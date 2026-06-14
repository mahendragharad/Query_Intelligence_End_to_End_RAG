from pathlib import Path
from src.chunkers.recursive__chunker import HybridRAGChunker
from src.vectorstores.vector_store_service_chroma import VectorStoreServiceChroma

BASE_DIR = Path.cwd().resolve()
vector_file_path = BASE_DIR / "config" / "data" / "LC_vector_db" 

class ChunkingAndEmbeddingService :

    def __init__(self) :
        self.chunker = HybridRAGChunker(chunk_size=900, chunk_overlap=120)

        self.vector_store = VectorStoreServiceChroma(
            collection_name = "documents",
            persist_directory=vector_file_path
        )
    
    def ingest_pdf(self, pdf_path) :
        chunks = self.chunker.chunk_pdf(
            pdf_path,
            extraction_mode="layout",
            pdf_mode="page",
        )

        db = self.vector_store.create(chunks)

        return db