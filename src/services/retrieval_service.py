import logging
from typing import List
from src.embeddings.huggingface_embeddings import HuggingFaceEmbeddingEngine
from src.llm.openai_client import NVIDIAOpenAIClient
from src.llm.ollama_client import OllamaClient
from src.vectorstores.chroma_db import LocalVectorDatabase
from src.retrievers.reranking_retriever import PerformRetrieval_Reranking_Top_K

logger = logging.getLogger(__name__)


class RetrievalService:
    def __init__(
        self,
        db_path: str,
        collection_name: str = "documents",
        rerank_top_k: int = 3,
        use_ollama_first: bool = True,
    ):
        self.collection_name = collection_name
        self.vector_db = LocalVectorDatabase(db_path=db_path)
        self.embedding_engine = HuggingFaceEmbeddingEngine()
        self.reranker = PerformRetrieval_Reranking_Top_K()
        self.rerank_top_k = rerank_top_k
        
        # Initialize LLM clients with Ollama as primary, NVIDIA as fallback
        self.ollama_client = OllamaClient() if use_ollama_first else None
        self.nvidia_client = NVIDIAOpenAIClient(timeout=100)

    def _get_answer(self, query: str, context_chunks: List[dict]) -> str:
        """Try Ollama first for speed, fallback to NVIDIA if unavailable."""
        # Try Ollama (local, fast, no timeout issues)
        if self.ollama_client and self.ollama_client.available:
            logger.info("Attempting Ollama for answer generation")
            try:
                answer = self.ollama_client.generate_answer(query, context_chunks)
                if answer:
                    return answer
                logger.warning("Ollama returned no answer or crashed; falling back to NVIDIA.")
            except Exception as e:
                logger.warning(f"Ollama failed: {e}")
                logger.warning("Falling back to NVIDIA after Ollama failure.")
        
        # Fallback to NVIDIA
        logger.info("Attempting NVIDIA API for answer generation")
        try:
            if self.nvidia_client and self.nvidia_client.client:
                answer = self.nvidia_client.generate_answer(query, context_chunks)
                if answer:
                    return answer
        except Exception as e:
            logger.warning(f"NVIDIA failed: {e}")
        
        # Last resort: return first chunk summary
        logger.warning("Both LLM clients failed, returning chunk summary")
        if context_chunks:
            return f"Based on the search results: {context_chunks[0].get('text', '')}..."
        return ""

    def query(self, query: str, top_k: int = 3) -> List[dict]:
        """Query the vector store and return top-k ranked results."""
        try:
            logger.info(f"Processing query: {query}")
            
            # Step 1: Embed the query
            query_embeddings = self.embedding_engine.get_embeddings([query])
            if not query_embeddings or len(query_embeddings) == 0:
                raise ValueError("Failed to generate embedding for query")
            
            query_vector = query_embeddings[0]
            logger.info(f"Query embedded successfully")
            
            # Step 2: Retrieve candidate chunks (use broader pool for reranking)
            pool_size = max(top_k * 3, 10)
            logger.info(f"Retrieving {pool_size} candidate chunks...")
            candidate_chunks = self.vector_db.retrieve_candidates(
                collection_name=self.collection_name,
                query_vector=query_vector,
                pool_size=pool_size,
            )
            
            if not candidate_chunks:
                logger.warning("No candidate chunks retrieved from vector store")
                return []
            
            logger.info(f"Retrieved {len(candidate_chunks)} candidates")
            
            # Step 3: Rerank candidates
            logger.info(f"Reranking with top_k={top_k}...")
            reranked = self.reranker.rerank_candidates(query, candidate_chunks, top_k=top_k)
            logger.info(f"Reranking complete, returned {len(reranked)} results")
            
            return reranked
            
        except Exception as e:
            logger.error(f"Query failed: {str(e)}")
            raise

    def generate_answer(self, query: str, top_k: int = 3) -> dict:
        """Generate contextual answer from retrieved chunks with fast, reliable LLM."""
        results = self.query(query, top_k=top_k)
        if not results:
            return {
                "query": query,
                "answer": "",
                "context": [],
                "message": "No relevant documents were found to answer the query.",
            }

        logger.info(f"Generating answer for query with {len(results)} context chunks")
        answer_text = self._get_answer(query, results)
        
        return {
            "query": query,
            "answer": answer_text,
            "context": results,
            "collection_name": self.collection_name,
            "result_count": len(results),
        }
