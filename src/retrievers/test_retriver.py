import re
from pathlib import Path
from src.embeddings.huggingface_embeddings import logger
from models.web_base_model import URLRequest
from src.loaders.pdf_loader import FileStorageService
from src.chunkers.recursive__chunker import HybridRAGChunker
from src.vectorstores.chroma_db import LocalVectorDatabase
from src.retrievers.retriever import Initiate_Retrieval
from src.retrievers.reranking_retriever import PerformRetrieval_Reranking_Top_K
from src.embeddings.huggingface_embeddings import HuggingFaceEmbeddingEngine 
from src.vectorstores.vector_store_service_chroma import VectorStoreInitiate_With_LC_Croma

BASE_DIR = Path.cwd().resolve()
db_upload_directory = BASE_DIR / "config" / "data" / "vector_db"
pdf_upload_directory = BASE_DIR / "config" / "data" / "uploads" / "Neural-Network(Basics).pdf"

class Test_Retriever :
    def __init__(self, query) :
        self.query = query
        self.chunker = HybridRAGChunker(chunk_size=900, chunk_overlap=120)
        self.embedding_object = HuggingFaceEmbeddingEngine(embedding_model = "BAAI/bge-small-en-v1.5", rerank_model = "BAAI/bge-reranker-base")
        self.embedding_model = self.embedding_object.embed_model
        self.rerank_model = self.embedding_object.rerank_model
        self.vector_db = LocalVectorDatabase(db_path=db_upload_directory)
        self.filename = pdf_upload_directory.name
        self.collection_name="Knowledge_Base"
        self.initiate_retrieval_object = Initiate_Retrieval()
        self.get_top_chunks_obj = PerformRetrieval_Reranking_Top_K()
        self.vecterstor_LC = VectorStoreInitiate_With_LC_Croma(collection_name="Attention_You_Need")
    
    def collection_Retriever(self) :
        query = self.query

        logger.info("Perform Embedding on user query")
        query_vector = self.embedding_object.get_embeddings(query)

        logger.info("Fast retrieval stage - fetch a broad pool of candidate chunks (pool_size=10)")
        initial_candidates = self.initiate_retrieval_object.retrieve_candidates(
            collection_name="Knowledge_Base",
            query_vector=query_vector,
            pool_size=10
        )

        logger.info("Precision scoring stage - Re-rank candidates using Cross-Encoder and isolate the absolute best Top 3")
        top_chunks = self.get_top_chunks_obj.rerank_candidates(
            query,
            initial_candidates, 
            top_k=5
        )

        text = "\n".join(" ".join(chunk["text"]) for chunk in top_chunks)
    
        return text
    
    def Chroma_LC_Retriever(self) :
        get_db = self.vecterstor_LC.create_vector_store()
        db = get_db['DB']
        retriever = db.as_retriever(
            search_type = "similarity",
            search_kwargs={
                "k" : 10
            }
        )

        top_k_chunks = retriever.invoke(self.query)

        for clear_chunks in top_k_chunks :
            text = clear_chunks.page_content
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'\n\d+\n', '\n', text)
        
        return text
        

# let's test it 
retrieve_chunks = Test_Retriever()
print(retrieve_chunks.test_retriever())