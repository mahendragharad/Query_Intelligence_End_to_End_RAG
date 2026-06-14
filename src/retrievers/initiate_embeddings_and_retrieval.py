from pathlib import Path
from src.embeddings.huggingface_embeddings import logger
from models.web_base_model import URLRequest
from src.loaders.pdf_loader import FileStorageService
from src.chunkers.recursive__chunker import HybridRAGChunker
from src.vectorstores.chroma_db import LocalVectorDatabase
from src.retrievers.retriever import Initiate_Retrieval
from src.retrievers.reranking_retriever import PerformRetrieval_Reranking_Top_K
from src.embeddings.huggingface_embeddings import HuggingFaceEmbeddingEngine

BASE_DIR = Path.cwd().resolve()
db_upload_directory = BASE_DIR / "config" / "data" / "vector_db"
pdf_upload_directory = BASE_DIR / "config" / "data" / "uploads" / "Neural-Network(Basics).pdf"

class Initiate_Top_Chunk_Retrieval :
    def __init__(self, file_path : str, db_path : str) :
        self.file_path = file_path
        self.db_path = db_path
        self.chunker = HybridRAGChunker(chunk_size=900, chunk_overlap=120)
        self.embedding_object = HuggingFaceEmbeddingEngine(embedding_model = "BAAI/bge-small-en-v1.5", rerank_model = "BAAI/bge-reranker-base")
        self.embedding_model = self.embedding_object.embed_model
        self.rerank_model = self.embedding_object.rerank_model
        self.vector_db = LocalVectorDatabase(db_path=db_upload_directory)
        self.filename = pdf_upload_directory.name
        self.collection_name="Knowledge_Base"
        self.initiate_retrieval_object = Initiate_Retrieval()
        self.get_top_chunks_obj = PerformRetrieval_Reranking_Top_K()

    def Initiate_Top_K_Chunk_Retrieval(self) :
        """Initiate the chunking from the uploaded document"""
        try : 
            logger.info("Performing chunking")
            chunks = self.chunker.chunk_pdf(self.file_path, extraction_mode="layout", pdf_mode="page")
            cleaned_chunks = [chunk.page_content for chunk in chunks]

            print(cleaned_chunks)

            logger.info("Decoding chunks into vector")
            chunked_vector = self.embedding_object.get_embeddings(cleaned_chunks)

            logger.info("Saving chunks into the local vector db")
            self.vector_db.save_document_vector(self.collection_name, cleaned_chunks, chunked_vector,self.filename)

            return {
                "Status" : "Vector Store Created",
                "Chunk Length" : len(chunked_vector)
            }
        
        except Exception as e :
            raise e


# Create the vector DB 
Initiate_pipeline = Initiate_Top_Chunk_Retrieval(pdf_upload_directory, db_upload_directory)
print(Initiate_pipeline.Initiate_Top_K_Chunk_Retrieval())
        