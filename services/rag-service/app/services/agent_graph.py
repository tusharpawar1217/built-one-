"""LangGraph agent for query orchestration."""
import logging
from typing import Dict, List, Any, TypedDict, Annotated
from langgraph.graph import StateGraph, END
# ToolExecutor has been removed in newer langgraph versions

from app.models.schemas import QueryType, Citation

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State passed between graph nodes."""
    # Input
    query: str
    user_id: str
    document_ids: List[str]
    conversation_history: List[Dict]
    
    # Processing
    query_type: str
    query_embedding: List[float]
    retrieved_chunks: List[Dict]
    reranked_chunks: List[Dict]
    
    # Output
    answer: str
    citations: List[Citation]
    model_used: str
    processing_steps: List[str]


class QueryAgent:
    """
    LangGraph-based agent for intelligent query processing.
    
    Flow:
    1. Classify query type
    2. Route to appropriate handler:
       - Simple Q&A: retrieve → rerank → answer
       - Multi-page synthesis: metadata filter → map-reduce → synthesize
       - Eligibility check: structured extraction
       - Quiz generation: topic extraction → question generation
    """
    
    def __init__(
        self,
        embedding_service,
        vector_store,
        reranker_service,
        llm_service
    ):
        """Initialize agent with required services."""
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.reranker_service = reranker_service
        self.llm_service = llm_service
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Construct the LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("classify", self._classify_node)
        workflow.add_node("embed_query", self._embed_query_node)
        workflow.add_node("retrieve", self._retrieve_node)
        workflow.add_node("rerank", self._rerank_node)
        workflow.add_node("simple_qa", self._simple_qa_node)
        workflow.add_node("multi_page_synthesis", self._multi_page_synthesis_node)
        
        # Define edges
        workflow.set_entry_point("classify")
        
        # After classification, always embed query
        workflow.add_edge("classify", "embed_query")
        
        # After embedding, retrieve chunks
        workflow.add_edge("embed_query", "retrieve")
        
        # After retrieval, rerank
        workflow.add_edge("retrieve", "rerank")
        
        # After reranking, route based on query type
        workflow.add_conditional_edges(
            "rerank",
            self._route_by_query_type,
            {
                "simple_qa": "simple_qa",
                "multi_page_synthesis": "multi_page_synthesis",
                "eligibility_check": "simple_qa",  # Use simple QA for now
                "quiz_generation": "simple_qa"  # Phase 2
            }
        )
        
        # All processing nodes end
        workflow.add_edge("simple_qa", END)
        workflow.add_edge("multi_page_synthesis", END)
        
        return workflow.compile()
    
    async def _classify_node(self, state: AgentState) -> AgentState:
        """Node: Classify query type."""
        logger.info("Node: Classify query type")
        
        query_type = await self.llm_service.classify_query_type(state["query"])
        
        state["query_type"] = query_type
        state["processing_steps"] = state.get("processing_steps", [])
        state["processing_steps"].append(f"Classified as: {query_type}")
        
        logger.info(f"Query classified as: {query_type}")
        return state
    
    async def _embed_query_node(self, state: AgentState) -> AgentState:
        """Node: Generate query embedding."""
        logger.info("Node: Generate query embedding")
        
        query_embedding = await self.embedding_service.embed_query(state["query"])
        
        state["query_embedding"] = query_embedding
        state["processing_steps"].append("Generated query embedding")
        
        return state
    
    async def _retrieve_node(self, state: AgentState) -> AgentState:
        """Node: Retrieve relevant chunks from vector store."""
        logger.info("Node: Retrieve chunks")
        
        from app.config import get_settings
        settings = get_settings()
        
        retrieved_chunks = await self.vector_store.search(
            query_embedding=state["query_embedding"],
            user_id=state["user_id"],
            document_ids=state["document_ids"],
            top_k=settings.top_k_retrieval
        )
        
        state["retrieved_chunks"] = retrieved_chunks
        state["processing_steps"].append(f"Retrieved {len(retrieved_chunks)} chunks")
        
        logger.info(f"Retrieved {len(retrieved_chunks)} chunks")
        return state
    
    async def _rerank_node(self, state: AgentState) -> AgentState:
        """Node: Rerank retrieved chunks."""
        logger.info("Node: Rerank chunks")
        
        reranked_chunks = self.reranker_service.rerank(
            query=state["query"],
            search_results=state["retrieved_chunks"]
        )
        
        state["reranked_chunks"] = reranked_chunks
        state["processing_steps"].append(f"Reranked to top {len(reranked_chunks)}")
        
        logger.info(f"Reranked to {len(reranked_chunks)} chunks")
        return state
    
    def _route_by_query_type(self, state: AgentState) -> str:
        """Conditional edge: Route to appropriate handler."""
        return state["query_type"]
    
    async def _simple_qa_node(self, state: AgentState) -> AgentState:
        """Node: Simple Q&A with retrieved context."""
        logger.info("Node: Simple Q&A")
        
        # Format context
        context = self.llm_service.format_context(state["reranked_chunks"])
        
        # Generate answer
        answer = await self.llm_service.generate_answer(
            query=state["query"],
            context=context,
            conversation_history=state.get("conversation_history"),
            use_pro=False  # Use Flash for simple Q&A
        )
        
        # Create citations
        citations = []
        for chunk in state["reranked_chunks"]:
            citations.append(Citation(
                document_id=chunk["document_id"],
                document_name=chunk["document_name"],
                page_number=chunk["page_number"],
                chunk_text=chunk["content"][:200] + "...",  # Preview
                relevance_score=chunk.get("rerank_score", chunk["score"])
            ))
        
        state["answer"] = answer
        state["citations"] = citations
        state["model_used"] = "gemini-flash-8b"
        state["processing_steps"].append("Generated answer with Flash model")
        
        return state
    
    async def _multi_page_synthesis_node(self, state: AgentState) -> AgentState:
        """Node: Multi-page synthesis with map-reduce."""
        logger.info("Node: Multi-page synthesis")
        
        chunks = state["reranked_chunks"]
        
        # If many chunks, do map-reduce
        if len(chunks) > 5:
            # Map: Summarize each chunk
            chunk_summaries = []
            for chunk in chunks[:10]:  # Limit to 10 chunks
                summary = await self.llm_service.synthesize_chunks([chunk["content"]])
                chunk_summaries.append(summary)
            
            # Reduce: Combine summaries
            context = "\n\n".join(chunk_summaries)
        else:
            context = self.llm_service.format_context(chunks)
        
        # Generate comprehensive answer with Pro model
        answer = await self.llm_service.generate_answer(
            query=state["query"],
            context=context,
            conversation_history=state.get("conversation_history"),
            use_pro=True  # Use Pro for complex synthesis
        )
        
        # Create citations
        citations = []
        for chunk in chunks:
            citations.append(Citation(
                document_id=chunk["document_id"],
                document_name=chunk["document_name"],
                page_number=chunk["page_number"],
                chunk_text=chunk["content"][:200] + "...",
                relevance_score=chunk.get("rerank_score", chunk["score"])
            ))
        
        state["answer"] = answer
        state["citations"] = citations
        state["model_used"] = "gemini-pro"
        state["processing_steps"].append("Synthesized multi-page answer with Pro model")
        
        return state
    
    async def process_query(
        self,
        query: str,
        user_id: str,
        document_ids: List[str],
        conversation_history: List[Dict] = None
    ) -> AgentState:
        """
        Process a user query through the agent graph.
        
        Args:
            query: User question
            user_id: User identifier
            document_ids: Documents to search
            conversation_history: Previous conversation
        
        Returns:
            Final agent state with answer and citations
        """
        initial_state = AgentState(
            query=query,
            user_id=user_id,
            document_ids=document_ids,
            conversation_history=conversation_history or [],
            query_type="",
            query_embedding=[],
            retrieved_chunks=[],
            reranked_chunks=[],
            answer="",
            citations=[],
            model_used="",
            processing_steps=[]
        )
        
        logger.info(f"Processing query: {query}")
        
        # Run the graph
        final_state = await self.graph.ainvoke(initial_state)
        
        logger.info(f"Query processed. Steps: {final_state['processing_steps']}")
        
        return final_state
