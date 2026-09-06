"""API endpoints for comprehensive mock test environment."""
import logging
from fastapi import APIRouter, Request, HTTPException, Query
from typing import Optional, List

from app.models.test_schemas import (
    CreateTestRequest, StartTestRequest, SubmitAnswerRequest, SubmitTestRequest,
    TestListResponse, TestMetadata, TestAttempt, TestResult, QuestionAttempt,
    UserTestPerformance, ExamType, DifficultyLevel, TestMode, LeaderboardResponse
)
from app.services.test_engine import TestEngine
from app.services.vector_store import VectorStoreService
from app.services.exam_templates import ExamTemplates

router = APIRouter()
logger = logging.getLogger(__name__)

# Global test engine instance
test_engine = TestEngine()


@router.get("/templates")
async def get_exam_templates(exam_type: Optional[ExamType] = Query(None)):
    """
    Get pre-configured exam templates with accurate patterns.
    
    Args:
        exam_type: Filter by exam type (optional)
    
    Returns:
        List of exam templates with template IDs
    """
    try:
        all_templates = ExamTemplates.get_all_templates()
        
        if exam_type:
            # Filter by exam type
            filtered = {
                tid: template for tid, template in all_templates.items()
                if template["exam_type"] == exam_type
            }
        else:
            filtered = all_templates
        
        # Format response with template IDs
        templates_list = [
            {
                "template_id": template_id,
                **template_data
            }
            for template_id, template_data in filtered.items()
        ]
        
        return {
            "templates": templates_list,
            "total": len(templates_list)
        }
    except Exception as e:
        logger.error(f"Failed to fetch templates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-from-template")
async def create_test_from_template(
    request: Request,
    template_id: str = Query(...),
    user_id: str = Query(...),
    source_document_ids: Optional[List[str]] = Query(None)
):
    """
    Create a test from pre-configured template.
    
    Args:
        template_id: Template identifier (e.g., upsc_prelims_gs1)
        user_id: User creating the test
        source_document_ids: Optional documents to generate questions from
    
    Returns:
        Created test metadata
    """
    try:
        template = ExamTemplates.get_template(template_id)
        
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        vector_store = request.app.state.vector_store
        embedding_service = request.app.state.embedding_service
        
        # Get content from documents if provided
        content_chunks = []
        if source_document_ids:
            for doc_id in source_document_ids:
                query_embedding = await embedding_service.embed_query("exam preparation content")
                search_results = await vector_store.search(
                    query_embedding=query_embedding,
                    user_id=user_id,
                    document_ids=[doc_id],
                    top_k=30
                )
                content_chunks.extend([result["content"] for result in search_results])
        
        if not content_chunks:
            # Generate from template subjects/topics
            subjects_str = ", ".join([s["name"] for s in template.get("sections", [])])
            content_chunks = [f"Generate questions on: {subjects_str}"]
        
        # Extract subjects from template sections
        from app.models.test_schemas import Subject
        all_subjects = []
        for section in template.get("sections", []):
            all_subjects.extend(section.get("subjects", []))
        
        # Remove duplicates
        unique_subjects = list(set(all_subjects))
        
        # Generate test
        test_metadata, questions = await test_engine.generate_test_from_document(
            name=template["name"],
            description=template["description"],
            exam_type=template["exam_type"],
            subjects=unique_subjects,
            duration_minutes=template["duration_minutes"],
            total_questions=template["total_questions"],
            difficulty_level=DifficultyLevel.MEDIUM,  # Use template default
            content_chunks=content_chunks,
            topic_filter=None,
            negative_marking=template["negative_marking"],
            user_id=user_id
        )
        
        # Update with template-specific details
        test_metadata.negative_marks_ratio = template.get("negative_marks_ratio", 0.25)
        test_metadata.instructions = template.get("instructions", [])
        
        logger.info(f"Created test from template {template_id}: {test_metadata.test_id}")
        return test_metadata
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Template test creation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create", response_model=TestMetadata)
async def create_test(
    request: Request,
    test_request: CreateTestRequest
):
    """
    Create a new mock test from documents or generate from topics.
    
    Args:
        test_request: Test creation parameters
    
    Returns:
        Created test metadata
    """
    try:
        vector_store = request.app.state.vector_store
        embedding_service = request.app.state.embedding_service
        
        # Get content from documents if provided
        content_chunks = []
        if test_request.source_document_ids:
            for doc_id in test_request.source_document_ids:
                # Search for content from document
                query_embedding = await embedding_service.embed_query(
                    test_request.topic_filter or "exam preparation content"
                )
                
                search_results = await vector_store.search(
                    query_embedding=query_embedding,
                    user_id=test_request.user_id,
                    document_ids=[doc_id],
                    top_k=20
                )
                
                content_chunks.extend([result["content"] for result in search_results])
        
        if not content_chunks:
            # Generate generic questions if no documents provided
            content_chunks = [f"Generate questions on {test_request.topic_filter or 'general topics'}"]
        
        # Generate test
        test_metadata, questions = await test_engine.generate_test_from_document(
            name=test_request.name,
            description=test_request.description,
            exam_type=test_request.exam_type,
            subjects=test_request.subjects,
            duration_minutes=test_request.duration_minutes,
            total_questions=test_request.total_questions,
            difficulty_level=test_request.difficulty_level,
            content_chunks=content_chunks,
            topic_filter=test_request.topic_filter,
            negative_marking=test_request.negative_marking,
            user_id=test_request.user_id
        )
        
        logger.info(f"Created test {test_metadata.test_id} with {len(questions)} questions")
        return test_metadata
        
    except Exception as e:
        logger.error(f"Test creation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=TestListResponse)
async def list_tests(
    exam_type: Optional[ExamType] = Query(None),
    difficulty: Optional[DifficultyLevel] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    List available mock tests with optional filtering.
    
    Args:
        exam_type: Filter by exam type
        difficulty: Filter by difficulty level
        page: Page number
        page_size: Items per page
    
    Returns:
        List of tests with pagination
    """
    try:
        tests, total = test_engine.list_tests(
            exam_type=exam_type,
            difficulty=difficulty,
            page=page,
            page_size=page_size
        )
        
        return TestListResponse(
            tests=tests,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Test listing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{test_id}", response_model=TestMetadata)
async def get_test(test_id: str):
    """
    Get detailed information about a specific test.
    
    Args:
        test_id: Test ID
    
    Returns:
        Test metadata
    """
    test = test_engine.get_test(test_id)
    
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    return test


@router.get("/{test_id}/preview")
async def preview_test(test_id: str, num_questions: int = Query(3, ge=1, le=10)):
    """
    Preview a few questions from the test before starting.
    
    Args:
        test_id: Test ID
        num_questions: Number of questions to preview
    
    Returns:
        Sample questions (without answers)
    """
    test = test_engine.get_test(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    questions = test_engine.get_test_questions(test_id)
    
    # Return preview without answers
    preview_questions = []
    for q in questions[:num_questions]:
        preview_questions.append({
            "question_id": q.question_id,
            "question_text": q.question_text,
            "question_type": q.question_type,
            "options": q.options,
            "marks": q.marks,
            "difficulty": q.difficulty,
            "subject": q.subject
        })
    
    return {
        "test_id": test_id,
        "test_name": test.name,
        "total_questions": test.total_questions,
        "preview_questions": preview_questions
    }


@router.post("/start", response_model=TestAttempt)
async def start_test(test_request: StartTestRequest):
    """
    Start a new test attempt.
    
    Args:
        test_request: Test start configuration
    
    Returns:
        Test attempt with questions
    """
    try:
        from app.models.test_schemas import TestAttemptConfig
        
        config = TestAttemptConfig(
            test_id=test_request.test_id,
            user_id=test_request.user_id,
            mode=test_request.mode,
            enable_calculator=test_request.enable_calculator,
            shuffle_questions=test_request.shuffle_questions
        )
        
        attempt = await test_engine.start_test(
            test_id=test_request.test_id,
            user_id=test_request.user_id,
            config=config
        )
        
        return attempt
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start test: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/attempt/{attempt_id}", response_model=TestAttempt)
async def get_attempt(attempt_id: str, user_id: str = Query(...)):
    """
    Get current test attempt progress.
    
    Args:
        attempt_id: Attempt ID
        user_id: User ID for authorization
    
    Returns:
        Test attempt with current progress
    """
    attempt = test_engine.get_attempt(attempt_id)
    
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    
    if attempt.user_id != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    return attempt


@router.get("/attempt/{attempt_id}/questions")
async def get_attempt_questions(
    attempt_id: str,
    user_id: str = Query(...),
    include_answers: bool = Query(False)
):
    """
    Get questions for an active test attempt.
    
    Args:
        attempt_id: Attempt ID
        user_id: User ID
        include_answers: Include correct answers (only for practice mode)
    
    Returns:
        List of questions
    """
    attempt = test_engine.get_attempt(attempt_id)
    
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    
    if attempt.user_id != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    questions = test_engine.get_test_questions(attempt.test_id)
    
    # Format questions
    formatted_questions = []
    for q in questions:
        question_data = {
            "question_id": q.question_id,
            "question_text": q.question_text,
            "question_type": q.question_type,
            "options": q.options,
            "marks": q.marks,
            "difficulty": q.difficulty,
            "subject": q.subject,
            "topic_tags": q.topic_tags
        }
        
        # Include answers only in practice mode or after submission
        if include_answers and (attempt.mode == TestMode.PRACTICE or attempt.is_submitted):
            question_data["correct_answers"] = q.correct_answers
            question_data["explanation"] = q.explanation
        
        formatted_questions.append(question_data)
    
    return {
        "attempt_id": attempt_id,
        "questions": formatted_questions,
        "total_questions": len(formatted_questions)
    }


@router.post("/attempt/{attempt_id}/answer", response_model=QuestionAttempt)
async def submit_answer(attempt_id: str, answer_request: SubmitAnswerRequest):
    """
    Submit answer for a question during test.
    
    Args:
        attempt_id: Attempt ID
        answer_request: Answer submission
    
    Returns:
        Updated question attempt
    """
    try:
        if answer_request.attempt_id != attempt_id:
            raise HTTPException(status_code=400, detail="Attempt ID mismatch")
        
        question_attempt = await test_engine.submit_answer(
            attempt_id=attempt_id,
            question_id=answer_request.question_id,
            user_answer=answer_request.user_answer,
            numeric_answer=answer_request.numeric_answer,
            is_marked_for_review=answer_request.is_marked_for_review,
            time_spent_seconds=answer_request.time_spent_seconds
        )
        
        return question_attempt
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to submit answer: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/attempt/{attempt_id}/submit", response_model=TestResult)
async def submit_test(attempt_id: str, submit_request: SubmitTestRequest):
    """
    Submit and evaluate the complete test.
    
    Args:
        attempt_id: Attempt ID
        submit_request: Submission request
    
    Returns:
        Detailed test results
    """
    try:
        if submit_request.attempt_id != attempt_id:
            raise HTTPException(status_code=400, detail="Attempt ID mismatch")
        
        result = await test_engine.submit_test(
            attempt_id=attempt_id,
            user_id=submit_request.user_id,
            force_submit=submit_request.force_submit
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to submit test: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/result/{attempt_id}", response_model=TestResult)
async def get_result(attempt_id: str, user_id: str = Query(...)):
    """
    Get detailed test results.
    
    Args:
        attempt_id: Attempt ID
        user_id: User ID for authorization
    
    Returns:
        Complete test results with analysis
    """
    result = test_engine.get_result(attempt_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    if result.user_id != user_id:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    return result


@router.get("/user/{user_id}/performance", response_model=UserTestPerformance)
async def get_user_performance(user_id: str):
    """
    Get user's overall test performance analytics.
    
    Args:
        user_id: User ID
    
    Returns:
        Performance metrics and analytics
    """
    performance = test_engine.get_user_performance(user_id)
    
    if not performance:
        raise HTTPException(status_code=404, detail="No performance data found")
    
    return performance


@router.get("/user/{user_id}/history")
async def get_test_history(
    user_id: str,
    exam_type: Optional[ExamType] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    Get user's test history.
    
    Args:
        user_id: User ID
        exam_type: Filter by exam type
        page: Page number
        page_size: Items per page
    
    Returns:
        List of past test attempts with results
    """
    # This would query database in production
    # For now, return placeholder
    return {
        "user_id": user_id,
        "test_attempts": [],
        "total": 0,
        "page": page,
        "page_size": page_size
    }


@router.get("/{test_id}/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    test_id: str,
    period: str = Query("all_time", regex="^(all_time|monthly|weekly|daily)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """
    Get leaderboard for a test.
    
    Args:
        test_id: Test ID
        period: Time period (all_time, monthly, weekly, daily)
        page: Page number
        page_size: Items per page
    
    Returns:
        Leaderboard with rankings
    """
    test = test_engine.get_test(test_id)
    
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    # Placeholder leaderboard
    from datetime import datetime
    from app.models.test_schemas import Leaderboard
    
    leaderboard = Leaderboard(
        test_id=test_id,
        period=period,
        entries=[],
        generated_at=datetime.now()
    )
    
    return LeaderboardResponse(
        test_id=test_id,
        test_name=test.name,
        leaderboard=leaderboard,
        user_rank=None,
        user_score=None
    )


@router.get("/stats/overview")
async def get_platform_stats():
    """
    Get overall platform statistics.
    
    Returns:
        Platform-wide statistics
    """
    return {
        "total_tests": len(test_engine.tests_db),
        "total_attempts": len(test_engine.attempts_db),
        "total_users": len(test_engine.user_performance_db),
        "popular_exams": {
            "MPSC": 45,
            "UPSC": 30,
            "SSC": 20,
            "Banking": 5
        },
        "average_score": 65.5,
        "total_questions_attempted": sum(
            perf.total_questions_attempted 
            for perf in test_engine.user_performance_db.values()
        )
    }
