"""Quiz generation endpoints."""
import logging
import uuid
from fastapi import APIRouter, Request, HTTPException
from typing import Optional

from app.models.schemas import QuizRequest, QuizResponse, QuizQuestion
from app.services.quiz_generator import QuizGenerator
from app.services.vector_store import VectorStoreService
from app.config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()


@router.post("/generate", response_model=QuizResponse)
async def generate_quiz(
    request: Request,
    quiz_request: QuizRequest
):
    """
    Generate quiz questions from uploaded document content.
    
    Args:
        quiz_request: Quiz generation parameters
    
    Returns:
        Generated quiz with questions
    """
    try:
        # Get vector store
        vector_store = request.app.state.vector_store
        embedding_service = request.app.state.embedding_service
        
        # Get relevant chunks for the topic
        if quiz_request.topic:
            # Generate embedding for topic
            topic_embedding = await embedding_service.embed_query(quiz_request.topic)
            
            # Search for relevant chunks
            search_results = await vector_store.search(
                query_embedding=topic_embedding,
                user_id=quiz_request.user_id,
                document_ids=[quiz_request.document_id],
                top_k=10
            )
            
            content_chunks = [result["content"] for result in search_results]
        else:
            # Get random chunks from the document
            # For now, just get top chunks by searching for generic query
            generic_embedding = await embedding_service.embed_query("exam preparation content")
            
            search_results = await vector_store.search(
                query_embedding=generic_embedding,
                user_id=quiz_request.user_id,
                document_ids=[quiz_request.document_id],
                top_k=10
            )
            
            content_chunks = [result["content"] for result in search_results]
        
        if not content_chunks:
            raise HTTPException(status_code=404, detail="No content found in document")
        
        # Generate quiz
        quiz_generator = QuizGenerator()
        questions = await quiz_generator.generate_questions(
            content_chunks=content_chunks,
            topic=quiz_request.topic,
            num_questions=quiz_request.num_questions,
            difficulty=quiz_request.difficulty
        )
        
        # Create quiz response
        quiz_id = str(uuid.uuid4())
        estimated_time = len(questions) * 2  # 2 minutes per question
        
        response = QuizResponse(
            quiz_id=quiz_id,
            questions=questions,
            total_questions=len(questions),
            estimated_time_minutes=estimated_time
        )
        
        logger.info(f"Generated quiz with {len(questions)} questions for user {quiz_request.user_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quiz generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Quiz generation failed: {str(e)}")


@router.post("/generate-topic", response_model=QuizResponse)
async def generate_quiz_by_topic(
    request: Request,
    topic: str,
    user_id: str,
    num_questions: int = 5,
    difficulty: Optional[str] = None
):
    """
    Generate quiz questions on a specific topic using LLM knowledge.
    Useful when user wants to practice without uploading documents.
    
    Args:
        topic: Topic name (e.g., "Indian History", "Mathematics")
        user_id: User making request
        num_questions: Number of questions (default: 5)
        difficulty: Difficulty level (easy/medium/hard)
    
    Returns:
        Generated quiz
    """
    try:
        quiz_generator = QuizGenerator()
        
        questions = await quiz_generator.generate_from_topic(
            topic=topic,
            num_questions=num_questions,
            difficulty=difficulty
        )
        
        quiz_id = str(uuid.uuid4())
        estimated_time = len(questions) * 2
        
        response = QuizResponse(
            quiz_id=quiz_id,
            questions=questions,
            total_questions=len(questions),
            estimated_time_minutes=estimated_time
        )
        
        logger.info(f"Generated topic-based quiz on '{topic}' for user {user_id}")
        return response
        
    except Exception as e:
        logger.error(f"Topic quiz generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
