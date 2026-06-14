import logging
from pathlib import Path
from typing import List, Optional
from langchain_core.documents import Document
from src.chunkers.recursive__chunker import HybridRAGChunker
from src.vectorstores.chroma_db import LocalVectorDatabase
from src.embeddings.huggingface_embeddings import HuggingFaceEmbeddingEngine

logger = logging.getLogger(__name__)

BASE_DIR = Path.cwd().resolve()
DEFAULT_UPLOAD_DIR = BASE_DIR / "config" / "data" / "uploads"
DEFAULT_VECTOR_DIR = BASE_DIR / "config" / "data" / "vector_db"


class IngestionService:
    def __init__(
        self,
        upload_dir: Optional[Path] = None,
        vector_dir: Optional[Path] = None,
        collection_name: str = "documents",
        chunk_size: int = 900,
        chunk_overlap: int = 120,
    ):
        self.upload_dir = upload_dir or DEFAULT_UPLOAD_DIR
        self.vector_dir = vector_dir or DEFAULT_VECTOR_DIR
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.vector_dir.mkdir(parents=True, exist_ok=True)

        self.chunker = HybridRAGChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.vector_db = LocalVectorDatabase(db_path=str(self.vector_dir))
        self.embedding_engine = HuggingFaceEmbeddingEngine()
        self.collection_name = collection_name

    def ingest_pdf(self, pdf_path: str):
        """Chunk PDF, embed, and store vectors in database."""
        try:
            logger.info(f"Starting PDF ingestion: {pdf_path}")
            
            # Step 1: Chunk the PDF
            documents = self.chunker.chunk_pdf(
                pdf_path=pdf_path,
                extraction_mode="layout",
                pdf_mode="page",
            )
            
            if not documents:
                raise ValueError("No documents extracted from PDF")
            
            logger.info(f"Extracted {len(documents)} chunks from PDF")
            
            # Step 2: Extract text from documents
            chunk_texts = [doc.page_content for doc in documents]
            
            # Step 3: Generate embeddings
            logger.info("Computing embeddings...")
            embeddings = self.embedding_engine.get_embeddings(chunk_texts)
            
            if not embeddings or len(embeddings) != len(chunk_texts):
                raise ValueError(f"Embedding generation failed: expected {len(chunk_texts)} embeddings, got {len(embeddings)}")
            
            logger.info(f"Generated {len(embeddings)} embeddings")
            
            # Step 4: Save to vector store with embeddings
            source_file = Path(pdf_path).name
            self.vector_db.save_document_vector(
                collection_name=self.collection_name,
                chunks=chunk_texts,
                vectors=embeddings,
                source_file=source_file,
            )
            
            logger.info(f"Successfully ingested PDF with {len(documents)} documents")
            
            return {
                "status": "success",
                "collection_name": self.collection_name,
                "document_count": len(documents),
                "source": str(pdf_path),
            }
        except Exception as e:
            logger.error(f"PDF ingestion failed: {str(e)}")
            raise

    def ingest_web_url(self, url: str, strategy: str = "semantic"):
        """Chunk web content, embed, and store vectors in database."""
        url = str(url)
        try:
            logger.info(f"Starting web URL ingestion: {url}")
            
            # Step 1: Chunk the web content
            documents = self.chunker.chunk_web(url=url, strategy=strategy)
            
            if not documents:
                raise ValueError("No content extracted from URL")
            
            logger.info(f"Extracted {len(documents)} chunks from URL")
            
            # Step 2: Extract text from documents
            chunk_texts = [doc.page_content for doc in documents]
            
            # Step 3: Generate embeddings
            logger.info("Computing embeddings...")
            embeddings = self.embedding_engine.get_embeddings(chunk_texts)
            
            if not embeddings or len(embeddings) != len(chunk_texts):
                raise ValueError(f"Embedding generation failed: expected {len(chunk_texts)} embeddings, got {len(embeddings)}")
            
            logger.info(f"Generated {len(embeddings)} embeddings")
            
            # Step 4: Save to vector store with embeddings
            self.vector_db.save_document_vector(
                collection_name=self.collection_name,
                chunks=chunk_texts,
                vectors=embeddings,
                source_file=url,
            )
            
            logger.info(f"Successfully ingested URL with {len(documents)} documents")
            
            return {
                "status": "success",
                "collection_name": self.collection_name,
                "document_count": len(documents),
                "source": url,
            }
        except Exception as e:
            logger.error(f"URL ingestion failed: {str(e)}")
            raise

    def chunk_pdf(self, pdf_path: str):
        """Chunk PDF without storing (for preview/inspection)."""
        return self.chunker.chunk_pdf(
            pdf_path=pdf_path,
            extraction_mode="layout",
            pdf_mode="page",
        )

    def chunk_web(self, url: str, strategy: str = "semantic"):
        """Chunk web content without storing (for preview/inspection)."""
        return self.chunker.chunk_web(url=url, strategy=strategy)
