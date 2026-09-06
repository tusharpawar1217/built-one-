"""LLM service for Gemini API integration."""
import logging
from typing import List, Dict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMService:
    """
    Wrapper for Gemini LLM with smart model selection.
    Uses Flash-8B by default, escalates to Pro for complex queries.
    """
    
    def __init__(self):
        """Initialize LLM service."""
        self.settings = settings
        
        # Initialize Flash model (cost-optimized)
        self.flash_model = ChatGoogleGenerativeAI(
            model=self.settings.gemini_model,
            google_api_key=self.settings.google_api_key,
            temperature=self.settings.gemini_temperature,
            max_output_tokens=self.settings.gemini_max_tokens
        )
        
        # Initialize Pro model (high-quality)
        self.pro_model = ChatGoogleGenerativeAI(
            model=self.settings.gemini_model_pro,
            google_api_key=self.settings.google_api_key,
            temperature=self.settings.gemini_temperature,
            max_output_tokens=self.settings.gemini_max_tokens
        )
        
        logger.info("LLM service initialized with Flash and Pro models")
    
    def format_context(self, retrieved_chunks: List[Dict]) -> str:
        """Format retrieved chunks into context string."""
        context_parts = []
        
        for idx, chunk in enumerate(retrieved_chunks, start=1):
            context_parts.append(
                f"[Source {idx}] (Document: {chunk['document_name']}, Page: {chunk['page_number']})\n"
                f"{chunk['content']}\n"
            )
        
        return "\n---\n".join(context_parts)
    
    async def generate_answer(
        self,
        query: str,
        context: str,
        conversation_history: Optional[List[Dict]] = None,
        use_pro: bool = False
    ) -> str:
        """
        Generate answer using retrieved context.
        
        Args:
            query: User query
            context: Retrieved and formatted context
            conversation_history: Previous messages
            use_pro: Force use of Pro model
        
        Returns:
            Generated answer
        """
        model = self.pro_model if use_pro else self.flash_model
        
        system_prompt = """You are an AI assistant helping students prepare for competitive government exams in India (UPSC, MPSC, SSC, Banking, Railways).

Your role:
- Answer questions accurately based on the provided context from the student's uploaded documents
- Cite specific page numbers when referencing information
- If the answer is not in the context, clearly state that
- Be concise but thorough
- Use simple language suitable for exam preparation

Important:
- Always cite sources with page numbers: "According to page X..."
- If information spans multiple pages, mention all relevant pages
- Don't make up information not present in the context"""

        user_prompt = f"""Context from documents:
{context}

Student Question: {query}

Provide a clear, accurate answer based on the context above. Always cite page numbers."""

        messages = [SystemMessage(content=system_prompt)]
        
        # Add conversation history if provided
        if conversation_history:
            for msg in conversation_history[-4:]:  # Last 4 messages for context
                if msg.get("role") == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg.get("role") == "assistant":
                    messages.append(AIMessage(content=msg["content"]))
        
        messages.append(HumanMessage(content=user_prompt))
        
        try:
            response = await model.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise
    
    async def classify_query_type(self, query: str) -> str:
        """
        Classify query type for routing.
        Returns: 'simple_qa', 'multi_page_synthesis', 'eligibility_check', 'quiz_generation'
        """
        system_prompt = """Classify the user query into one of these categories:
1. simple_qa - Direct factual question answerable from a few chunks
2. multi_page_synthesis - Requires understanding across multiple pages/sections (e.g., "summarize chapter 3", "explain the entire process")
3. eligibility_check - Questions about exam eligibility, qualifications, age limits
4. quiz_generation - Request to generate practice questions

Respond with only the category name."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Query: {query}")
        ]
        
        try:
            response = await self.flash_model.ainvoke(messages)
            query_type = response.content.strip().lower()
            
            # Validate response
            valid_types = ['simple_qa', 'multi_page_synthesis', 'eligibility_check', 'quiz_generation']
            if query_type not in valid_types:
                logger.warning(f"Invalid query type: {query_type}, defaulting to simple_qa")
                return 'simple_qa'
            
            return query_type
        except Exception as e:
            logger.error(f"Query classification failed: {e}, defaulting to simple_qa")
            return 'simple_qa'
    
    async def synthesize_chunks(self, chunks: List[str]) -> str:
        """
        Synthesize multiple chunks into coherent summary.
        Used for multi-page reasoning.
        """
        system_prompt = """Synthesize the following text excerpts into a coherent summary.
Maintain key facts, dates, and important details.
Organize information logically."""

        combined_text = "\n\n".join([f"Excerpt {i+1}:\n{chunk}" for i, chunk in enumerate(chunks)])
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=combined_text)
        ]
        
        try:
            response = await self.pro_model.ainvoke(messages)  # Use Pro for synthesis
            return response.content
        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            return "\n\n".join(chunks)  # Fallback to concatenation
