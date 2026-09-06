"""Comprehensive test engine for mock test environment."""
import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
import json

from app.models.test_schemas import (
    TestMetadata, QuestionModel, TestAttempt, TestAttemptConfig,
    QuestionAttempt, TestResult, UserTestPerformance, Leaderboard,
    TestMode, QuestionType, DifficultyLevel, Subject, ExamType
)
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class TestEngine:
    """Core engine for test creation, execution, and evaluation."""
    
    def __init__(self):
        self.llm_service = LLMService()
        # In production, this would be PostgreSQL
        self.tests_db: Dict[str, TestMetadata] = {}
        self.questions_db: Dict[str, List[QuestionModel]] = {}
        self.attempts_db: Dict[str, TestAttempt] = {}
        self.results_db: Dict[str, TestResult] = {}
        self.user_performance_db: Dict[str, UserTestPerformance] = {}
        
    # ============ Test Creation ============
    
    async def generate_test_from_document(
        self,
        name: str,
        description: str,
        exam_type: ExamType,
        subjects: List[Subject],
        duration_minutes: int,
        total_questions: int,
        difficulty_level: DifficultyLevel,
        content_chunks: List[str],
        topic_filter: Optional[str] = None,
        negative_marking: bool = True,
        user_id: str = "system"
    ) -> Tuple[TestMetadata, List[QuestionModel]]:
        """
        Generate a complete test from document content.
        
        Args:
            name: Test name
            description: Test description
            exam_type: Type of exam
            subjects: List of subjects covered
            duration_minutes: Test duration
            total_questions: Number of questions
            difficulty_level: Overall difficulty
            content_chunks: Content to generate questions from
            topic_filter: Optional topic filter
            negative_marking: Enable negative marking
            user_id: Creator user ID
            
        Returns:
            Tuple of (TestMetadata, List of Questions)
        """
        test_id = str(uuid.uuid4())
        
        # Generate questions using LLM
        questions = await self._generate_questions_from_content(
            test_id=test_id,
            content_chunks=content_chunks,
            num_questions=total_questions,
            subjects=subjects,
            difficulty_level=difficulty_level,
            topic_filter=topic_filter,
            exam_type=exam_type
        )
        
        # Calculate difficulty distribution
        difficulty_dist = {
            "easy": len([q for q in questions if q.difficulty == DifficultyLevel.EASY]),
            "medium": len([q for q in questions if q.difficulty == DifficultyLevel.MEDIUM]),
            "hard": len([q for q in questions if q.difficulty == DifficultyLevel.HARD]),
        }
        
        # Create test metadata
        test_metadata = TestMetadata(
            test_id=test_id,
            name=name,
            description=description,
            exam_type=exam_type,
            subjects=subjects,
            total_questions=len(questions),
            total_marks=float(len(questions)),  # 1 mark per question
            duration_minutes=duration_minutes,
            negative_marking=negative_marking,
            negative_marks_ratio=0.25,
            passing_percentage=33.0,
            difficulty_distribution=difficulty_dist,
            instructions=self._get_exam_instructions(exam_type),
            created_at=datetime.now(),
            created_by=user_id
        )
        
        # Store in database
        self.tests_db[test_id] = test_metadata
        self.questions_db[test_id] = questions
        
        logger.info(f"Created test {test_id} with {len(questions)} questions")
        return test_metadata, questions
    
    async def _generate_questions_from_content(
        self,
        test_id: str,
        content_chunks: List[str],
        num_questions: int,
        subjects: List[Subject],
        difficulty_level: DifficultyLevel,
        topic_filter: Optional[str],
        exam_type: ExamType
    ) -> List[QuestionModel]:
        """Generate questions using LLM."""
        
        # Combine content
        combined_content = "\n\n".join(content_chunks[:10])  # Limit for token size
        
        # Create prompt for question generation
        prompt = f"""Generate {num_questions} high-quality multiple choice questions for {exam_type.value.upper()} exam preparation.

Content to generate questions from:
{combined_content}

Requirements:
- Subjects: {', '.join([s.value for s in subjects])}
- Difficulty: {difficulty_level.value}
- Each question should have 4 options (A, B, C, D)
- Only ONE correct answer per question
- Include detailed explanation for each answer
{f'- Focus on topic: {topic_filter}' if topic_filter else ''}

Format your response as a JSON array of questions:
[
  {{
    "question": "Question text here?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "Option B",
    "difficulty": "medium",
    "subject": "indian_polity",
    "explanation": "Detailed explanation here",
    "topic_tags": ["constitution", "articles"]
  }},
  ...
]

Generate exactly {num_questions} questions."""

        try:
            response = await self.llm_service.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=8000
            )
            
            # Parse JSON response
            import re
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                questions_data = json.loads(json_match.group())
            else:
                raise ValueError("Could not parse questions from LLM response")
            
            # Convert to QuestionModel objects
            questions = []
            for idx, q_data in enumerate(questions_data[:num_questions]):
                question = QuestionModel(
                    question_id=str(uuid.uuid4()),
                    test_id=test_id,
                    question_text=q_data["question"],
                    question_type=QuestionType.MCQ_SINGLE,
                    subject=Subject(q_data.get("subject", subjects[0].value)),
                    difficulty=DifficultyLevel(q_data.get("difficulty", difficulty_level.value)),
                    marks=1.0,
                    negative_marks=0.25,
                    options=q_data["options"],
                    correct_answers=[q_data["correct_answer"]],
                    explanation=q_data.get("explanation", ""),
                    topic_tags=q_data.get("topic_tags", []),
                    times_attempted=0,
                    times_correct=0
                )
                questions.append(question)
            
            logger.info(f"Generated {len(questions)} questions from content")
            return questions
            
        except Exception as e:
            logger.error(f"Failed to generate questions: {e}")
            # Return fallback questions
            return self._get_fallback_questions(test_id, num_questions, subjects[0], difficulty_level)
    
    def _get_fallback_questions(
        self,
        test_id: str,
        num_questions: int,
        subject: Subject,
        difficulty: DifficultyLevel
    ) -> List[QuestionModel]:
        """Generate fallback questions if LLM fails."""
        questions = []
        for i in range(num_questions):
            question = QuestionModel(
                question_id=str(uuid.uuid4()),
                test_id=test_id,
                question_text=f"Sample question {i+1} for {subject.value}?",
                question_type=QuestionType.MCQ_SINGLE,
                subject=subject,
                difficulty=difficulty,
                marks=1.0,
                negative_marks=0.25,
                options=["Option A", "Option B", "Option C", "Option D"],
                correct_answers=["Option A"],
                explanation="This is a sample question for testing purposes.",
                topic_tags=["sample"],
                times_attempted=0,
                times_correct=0
            )
            questions.append(question)
        return questions
    
    def _get_exam_instructions(self, exam_type: ExamType) -> List[str]:
        """Get standard instructions for exam type."""
        base_instructions = [
            "Read each question carefully before answering",
            "Each question carries 1 mark",
            "Negative marking: -0.25 marks for wrong answers",
            "You can mark questions for review and return later",
            "Submit the test before time expires",
            "Do not refresh the page during the test",
        ]
        
        exam_specific = {
            ExamType.UPSC: [
                "This test simulates UPSC Prelims examination pattern",
                "Total duration matches actual exam timing",
            ],
            ExamType.MPSC: [
                "This test follows MPSC examination pattern",
                "Questions are in English (Hindi/Marathi versions coming soon)",
            ],
            ExamType.SSC: [
                "This test follows SSC CGL/CHSL pattern",
                "Focus on accuracy over speed",
            ],
        }
        
        return base_instructions + exam_specific.get(exam_type, [])
    
    # ============ Test Execution ============
    
    async def start_test(
        self,
        test_id: str,
        user_id: str,
        config: TestAttemptConfig
    ) -> TestAttempt:
        """Start a new test attempt."""
        
        if test_id not in self.tests_db:
            raise ValueError(f"Test {test_id} not found")
        
        test_metadata = self.tests_db[test_id]
        questions = self.questions_db[test_id]
        
        # Shuffle if requested
        if config.shuffle_questions:
            import random
            questions = random.sample(questions, len(questions))
        
        # Create attempt
        attempt_id = str(uuid.uuid4())
        attempt = TestAttempt(
            attempt_id=attempt_id,
            test_id=test_id,
            user_id=user_id,
            test_metadata=test_metadata,
            started_at=datetime.now(),
            time_remaining_seconds=test_metadata.duration_minutes * 60,
            questions_attempted=[],
            current_question_index=0,
            is_submitted=False,
            is_paused=False,
            mode=config.mode,
            config=config
        )
        
        # Initialize question attempts
        for question in questions:
            attempt.questions_attempted.append(
                QuestionAttempt(
                    question_id=question.question_id,
                    user_answer=None,
                    is_marked_for_review=False,
                    time_spent_seconds=0
                )
            )
        
        self.attempts_db[attempt_id] = attempt
        logger.info(f"Started test attempt {attempt_id} for user {user_id}")
        
        return attempt
    
    async def submit_answer(
        self,
        attempt_id: str,
        question_id: str,
        user_answer: Optional[List[str]],
        numeric_answer: Optional[float],
        is_marked_for_review: bool,
        time_spent_seconds: int
    ) -> QuestionAttempt:
        """Submit answer for a question."""
        
        if attempt_id not in self.attempts_db:
            raise ValueError(f"Attempt {attempt_id} not found")
        
        attempt = self.attempts_db[attempt_id]
        
        if attempt.is_submitted:
            raise ValueError("Cannot modify submitted test")
        
        # Find and update question attempt
        for q_attempt in attempt.questions_attempted:
            if q_attempt.question_id == question_id:
                q_attempt.user_answer = user_answer
                q_attempt.numeric_answer = numeric_answer
                q_attempt.is_marked_for_review = is_marked_for_review
                q_attempt.time_spent_seconds = time_spent_seconds
                q_attempt.answered_at = datetime.now()
                
                logger.info(f"Updated answer for question {question_id} in attempt {attempt_id}")
                return q_attempt
        
        raise ValueError(f"Question {question_id} not found in attempt")
    
    async def submit_test(
        self,
        attempt_id: str,
        user_id: str,
        force_submit: bool = False
    ) -> TestResult:
        """Submit and evaluate test."""
        
        if attempt_id not in self.attempts_db:
            raise ValueError(f"Attempt {attempt_id} not found")
        
        attempt = self.attempts_db[attempt_id]
        
        if attempt.user_id != user_id:
            raise ValueError("Unauthorized to submit this test")
        
        if attempt.is_submitted:
            # Return existing result
            return self.results_db.get(attempt_id)
        
        # Mark as submitted
        attempt.is_submitted = True
        attempt.submitted_at = datetime.now()
        
        # Calculate time taken
        time_taken = (attempt.submitted_at - attempt.started_at).total_seconds()
        
        # Evaluate test
        result = await self._evaluate_test(attempt, time_taken)
        
        # Store result
        self.results_db[attempt_id] = result
        
        # Update user performance
        await self._update_user_performance(user_id, result)
        
        logger.info(f"Test {attempt.test_id} submitted by {user_id}, score: {result.percentage}%")
        
        return result
    
    async def _evaluate_test(self, attempt: TestAttempt, time_taken_seconds: float) -> TestResult:
        """Evaluate test attempt and generate results."""
        
        questions = self.questions_db[attempt.test_id]
        test_meta = attempt.test_metadata
        
        # Create question lookup
        question_map = {q.question_id: q for q in questions}
        
        # Evaluate each question
        correct = 0
        incorrect = 0
        skipped = 0
        marks_obtained = 0.0
        
        subject_stats = {}
        difficulty_stats = {}
        question_results = []
        
        for q_attempt in attempt.questions_attempted:
            question = question_map.get(q_attempt.question_id)
            if not question:
                continue
            
            is_correct = False
            marks_for_question = 0.0
            
            if q_attempt.user_answer is None or len(q_attempt.user_answer) == 0:
                skipped += 1
                status = "skipped"
            else:
                # Check if answer is correct
                if question.question_type == QuestionType.MCQ_SINGLE:
                    is_correct = q_attempt.user_answer[0] in question.correct_answers
                elif question.question_type == QuestionType.MCQ_MULTIPLE:
                    is_correct = set(q_attempt.user_answer) == set(question.correct_answers)
                elif question.question_type == QuestionType.NUMERIC:
                    if q_attempt.numeric_answer is not None and question.correct_numeric_answer is not None:
                        tolerance = question.numeric_tolerance or 0.01
                        is_correct = abs(q_attempt.numeric_answer - question.correct_numeric_answer) <= tolerance
                
                if is_correct:
                    correct += 1
                    marks_for_question = question.marks
                    status = "correct"
                else:
                    incorrect += 1
                    marks_for_question = -question.negative_marks if test_meta.negative_marking else 0
                    status = "incorrect"
                
                marks_obtained += marks_for_question
            
            # Update subject stats
            subject_key = question.subject.value
            if subject_key not in subject_stats:
                subject_stats[subject_key] = {"correct": 0, "total": 0, "accuracy": 0.0}
            subject_stats[subject_key]["total"] += 1
            if is_correct:
                subject_stats[subject_key]["correct"] += 1
            
            # Update difficulty stats
            diff_key = question.difficulty.value
            if diff_key not in difficulty_stats:
                difficulty_stats[diff_key] = {"correct": 0, "total": 0, "accuracy": 0.0}
            difficulty_stats[diff_key]["total"] += 1
            if is_correct:
                difficulty_stats[diff_key]["correct"] += 1
            
            # Store question result
            question_results.append({
                "question_id": question.question_id,
                "question_text": question.question_text,
                "user_answer": q_attempt.user_answer,
                "correct_answer": question.correct_answers,
                "is_correct": is_correct,
                "status": status,
                "marks": marks_for_question,
                "time_spent": q_attempt.time_spent_seconds,
                "explanation": question.explanation,
                "subject": question.subject.value,
                "difficulty": question.difficulty.value
            })
        
        # Calculate accuracies
        for stats in subject_stats.values():
            stats["accuracy"] = (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0
        
        for stats in difficulty_stats.values():
            stats["accuracy"] = (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0
        
        # Calculate overall metrics
        attempted = correct + incorrect
        total_marks = test_meta.total_marks
        percentage = (marks_obtained / total_marks * 100) if total_marks > 0 else 0
        
        # Identify weak and strong topics
        weak_topics = [
            subject for subject, stats in subject_stats.items()
            if stats["accuracy"] < 50 and stats["total"] >= 3
        ]
        strong_topics = [
            subject for subject, stats in subject_stats.items()
            if stats["accuracy"] >= 75 and stats["total"] >= 3
        ]
        
        # Generate improvement suggestions
        suggestions = self._generate_suggestions(
            percentage, subject_stats, difficulty_stats, time_taken_seconds, test_meta.duration_minutes * 60
        )
        
        # Create result
        result = TestResult(
            attempt_id=attempt.attempt_id,
            test_id=attempt.test_id,
            user_id=attempt.user_id,
            total_questions=test_meta.total_questions,
            attempted=attempted,
            correct=correct,
            incorrect=incorrect,
            skipped=skipped,
            marks_obtained=marks_obtained,
            total_marks=total_marks,
            percentage=max(0, percentage),  # Don't show negative percentage
            subject_wise_analysis=subject_stats,
            difficulty_wise_analysis=difficulty_stats,
            total_time_taken_seconds=int(time_taken_seconds),
            average_time_per_question=time_taken_seconds / test_meta.total_questions,
            weak_topics=weak_topics,
            strong_topics=strong_topics,
            improvement_suggestions=suggestions,
            question_wise_results=question_results,
            submitted_at=attempt.submitted_at,
            evaluated_at=datetime.now(),
            total_test_takers=1  # Will be updated with actual data
        )
        
        return result
    
    def _generate_suggestions(
        self,
        percentage: float,
        subject_stats: Dict,
        difficulty_stats: Dict,
        time_taken: float,
        duration: float
    ) -> List[str]:
        """Generate personalized improvement suggestions."""
        suggestions = []
        
        if percentage < 40:
            suggestions.append("Focus on building fundamentals. Start with easier questions before attempting hard ones.")
        elif percentage < 60:
            suggestions.append("Good start! Work on accuracy before attempting more difficult questions.")
        elif percentage < 80:
            suggestions.append("You're doing well! Practice more to improve speed and accuracy.")
        else:
            suggestions.append("Excellent performance! Keep practicing to maintain consistency.")
        
        # Subject-specific suggestions
        weak_subjects = [s for s, stats in subject_stats.items() if stats["accuracy"] < 50]
        if weak_subjects:
            suggestions.append(f"Focus more on: {', '.join(weak_subjects)}")
        
        # Difficulty-specific suggestions
        if difficulty_stats.get("easy", {}).get("accuracy", 100) < 80:
            suggestions.append("Master easy questions first - they're scoring opportunities you shouldn't miss!")
        
        # Time management
        if time_taken < duration * 0.5:
            suggestions.append("You finished very quickly. Consider spending more time to improve accuracy.")
        elif time_taken > duration * 0.95:
            suggestions.append("Work on time management. Practice solving questions faster.")
        
        return suggestions
    
    async def _update_user_performance(self, user_id: str, result: TestResult):
        """Update user's overall performance metrics."""
        
        if user_id not in self.user_performance_db:
            self.user_performance_db[user_id] = UserTestPerformance(
                user_id=user_id,
                total_tests_taken=0,
                total_tests_completed=0,
                total_questions_attempted=0,
                overall_accuracy=0.0,
                average_score_percentage=0.0,
                subject_performance={},
                tests_by_exam_type={},
                improvement_trend=[],
                strongest_subjects=[],
                weakest_subjects=[],
                average_time_per_question=0.0,
                time_management_score=0.0,
                current_streak_days=0,
                longest_streak_days=0,
                updated_at=datetime.now()
            )
        
        perf = self.user_performance_db[user_id]
        perf.total_tests_completed += 1
        perf.total_questions_attempted += result.attempted
        
        # Update average score
        perf.average_score_percentage = (
            (perf.average_score_percentage * (perf.total_tests_completed - 1) + result.percentage) /
            perf.total_tests_completed
        )
        
        # Update overall accuracy
        perf.overall_accuracy = (
            (perf.overall_accuracy * (perf.total_questions_attempted - result.attempted) +
             (result.correct / result.attempted * 100 if result.attempted > 0 else 0) * result.attempted) /
            perf.total_questions_attempted
        )
        
        # Add to improvement trend
        perf.improvement_trend.append({
            "date": result.submitted_at.isoformat(),
            "score": result.percentage,
            "test_id": result.test_id
        })
        
        perf.updated_at = datetime.now()
        
        logger.info(f"Updated performance for user {user_id}")
    
    # ============ Retrieval Methods ============
    
    def get_test(self, test_id: str) -> Optional[TestMetadata]:
        """Get test metadata."""
        return self.tests_db.get(test_id)
    
    def get_test_questions(self, test_id: str) -> List[QuestionModel]:
        """Get all questions for a test."""
        return self.questions_db.get(test_id, [])
    
    def get_attempt(self, attempt_id: str) -> Optional[TestAttempt]:
        """Get test attempt."""
        return self.attempts_db.get(attempt_id)
    
    def get_result(self, attempt_id: str) -> Optional[TestResult]:
        """Get test result."""
        return self.results_db.get(attempt_id)
    
    def get_user_performance(self, user_id: str) -> Optional[UserTestPerformance]:
        """Get user's overall performance."""
        return self.user_performance_db.get(user_id)
    
    def list_tests(
        self,
        exam_type: Optional[ExamType] = None,
        difficulty: Optional[DifficultyLevel] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[TestMetadata], int]:
        """List available tests with filtering."""
        tests = list(self.tests_db.values())
        
        # Apply filters
        if exam_type:
            tests = [t for t in tests if t.exam_type == exam_type]
        if difficulty:
            tests = [t for t in tests if difficulty.value in t.difficulty_distribution]
        
        # Pagination
        total = len(tests)
        start = (page - 1) * page_size
        end = start + page_size
        
        return tests[start:end], total
