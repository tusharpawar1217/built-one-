"""Quiz generation from document content."""
import logging
import json
from typing import List, Dict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage

from app.config import get_settings
from app.models.schemas import QuizQuestion

logger = logging.getLogger(__name__)
settings = get_settings()


class QuizGenerator:
    """
    Generate practice quiz questions from uploaded content.
    Supports multiple difficulty levels and question types.
    """
    
    def __init__(self):
        """Initialize quiz generator."""
        self.settings = settings
        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,  # Flash is sufficient for quiz gen
            google_api_key=settings.google_api_key,
            temperature=0.7  # Some creativity for varied questions
        )
    
    async def generate_questions(
        self,
        content_chunks: List[str],
        topic: Optional[str] = None,
        num_questions: int = 5,
        difficulty: Optional[str] = None
    ) -> List[QuizQuestion]:
        """
        Generate quiz questions from content.
        
        Args:
            content_chunks: List of text chunks to generate questions from
            topic: Optional topic filter
            num_questions: Number of questions to generate
            difficulty: Optional difficulty level (easy, medium, hard)
        
        Returns:
            List of quiz questions with options and explanations
        """
        # Combine chunks (limit to reasonable size)
        combined_content = "\n\n".join(content_chunks[:5])  # Max 5 chunks
        
        difficulty_instruction = ""
        if difficulty:
            difficulty_instruction = f"Generate {difficulty} difficulty questions."
        
        topic_instruction = ""
        if topic:
            topic_instruction = f"Focus on the topic: {topic}"
        
        system_prompt = """You are an expert at creating multiple-choice questions for competitive exam preparation.

Your task:
1. Read the provided content carefully
2. Generate high-quality MCQ questions that test understanding
3. Provide 4 options (A, B, C, D) for each question
4. Mark the correct answer
5. Provide a clear explanation for the correct answer
6. Questions should test concepts, not just memorization

Format each question as JSON:
{
  "question": "Question text?",
  "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
  "correct_answer": "A",
  "difficulty": "medium",
  "explanation": "Explanation of why this is correct",
  "source_reference": "Brief reference to where this info came from"
}

Return an array of such question objects."""

        user_prompt = f"""Generate {num_questions} multiple-choice questions from this content:

{combined_content[:6000]}

{difficulty_instruction}
{topic_instruction}

Return only a valid JSON array of question objects."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        try:
            response = await self.llm.ainvoke(messages)
            
            # Parse JSON response
            # Handle markdown code blocks if present
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]  # Remove ```json
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            questions_data = json.loads(content)
            
            # Convert to QuizQuestion objects
            questions = []
            for idx, q_data in enumerate(questions_data[:num_questions]):
                question = QuizQuestion(
                    question=q_data.get("question", ""),
                    options=q_data.get("options", []),
                    correct_answer=q_data.get("correct_answer", "A"),
                    difficulty=q_data.get("difficulty", difficulty or "medium"),
                    explanation=q_data.get("explanation", ""),
                    source_page=idx + 1  # Placeholder, should track actual page
                )
                questions.append(question)
            
            logger.info(f"Generated {len(questions)} quiz questions")
            return questions
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse quiz JSON: {e}")
            logger.error(f"Response content: {response.content}")
            raise ValueError("Failed to generate valid quiz questions")
        
        except Exception as e:
            logger.error(f"Quiz generation failed: {e}")
            raise
    
    async def generate_from_topic(
        self,
        topic: str,
        num_questions: int = 5,
        difficulty: Optional[str] = None
    ) -> List[QuizQuestion]:
        """
        Generate questions on a specific topic without content.
        Uses LLM's knowledge (for general topics).
        """
        difficulty_str = difficulty or "medium"
        
        system_prompt = """You are an expert at creating multiple-choice questions for competitive exam preparation in India (UPSC, MPSC, SSC, Banking, Railways).

Create high-quality MCQ questions on the given topic.
Format as JSON array with structure:
{
  "question": "Question text?",
  "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
  "correct_answer": "A",
  "difficulty": "medium",
  "explanation": "Explanation"
}"""

        user_prompt = f"""Generate {num_questions} {difficulty_str} difficulty multiple-choice questions on the topic: {topic}

Focus on concepts tested in Indian competitive exams.
Return only valid JSON array."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        try:
            response = await self.llm.ainvoke(messages)
            
            # Parse response
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:-3] if content.endswith("```") else content[7:]
            elif content.startswith("```"):
                content = content[3:-3] if content.endswith("```") else content[3:]
            content = content.strip()
            
            questions_data = json.loads(content)
            
            questions = []
            for q_data in questions_data[:num_questions]:
                question = QuizQuestion(
                    question=q_data.get("question", ""),
                    options=q_data.get("options", []),
                    correct_answer=q_data.get("correct_answer", "A"),
                    difficulty=q_data.get("difficulty", difficulty_str),
                    explanation=q_data.get("explanation", ""),
                    source_page=0  # No source page for generated questions
                )
                questions.append(question)
            
            logger.info(f"Generated {len(questions)} questions on topic: {topic}")
            return questions
        
        except Exception as e:
            logger.error(f"Topic-based quiz generation failed: {e}")
            raise
