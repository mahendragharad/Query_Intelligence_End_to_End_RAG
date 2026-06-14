from pathlib import Path
import chromadb
from src.embeddings.huggingface_embeddings import logger

BASE_DIR = Path.cwd().resolve()
upload_directory = BASE_DIR / "config" / "data" / "uploads"

class LocalVectorDatabase :
    """Enterprise wrapper handling persistent on-disk raw chunk storage and retrieval mappings."""
    def __init__(self, db_path : str = "") :
        Path(db_path).mkdir(parents=True, exist_ok=True)
        logger.info(f"Binding persistent database client to storage target: {db_path}")
        self.client = chromadb.PersistentClient(path=db_path)

    def _get_collection(self, collection_name:str) :
        return self.client.get_or_create_collection(
            name = collection_name,
            metadata={"hnsw:space" : "cosine"}
        )

    def save_document_vector(self, collection_name: str, chunks: list[str], vectors: list[list[float]], source_file: str):
        """Ingests structured document vectors along with tracing metadata into disk storage."""
        if not chunks or not vectors:
            return []

        collection = self._get_collection(collection_name)
        ids = [f"{source_file}_chunk{i}" for i in range(len(chunks))]
        metadata = [{"source": source_file} for _ in range(len(chunks))]

        try:
            logger.info(f"Executing batch upsert of {len(chunks)} vectors into collection '{collection_name}'...")
            collection.upsert(ids=ids, embeddings=vectors, documents=chunks, metadatas=metadata)
            logger.info("Storage persistence array synchronization complete.")
        except Exception as e:
            logger.error(f"Database write execution error: {e}")
            raise

    def query_collection(self, collection_name: str, query_embeddings: list[list[float]], n_results: int = 10) -> dict:
        collection = self._get_collection(collection_name)
        return collection.query(query_embeddings=query_embeddings, n_results=n_results)

    def retrieve_candidates(self, collection_name: str, query_vector: list[float], pool_size: int = 10) -> list[dict]:
        results = self.query_collection(collection_name, [query_vector], n_results=pool_size)
        candidates = []
        if not results or not results.get("documents"):
            return candidates

        for idx in range(len(results["documents"][0])):
            candidates.append(
                {
                    "id": results["ids"][0][idx],
                    "text": results["documents"][0][idx],
                    "metadata": results["metadatas"][0][idx],
                    "distance": results["distances"][0][idx],
                }
            )
        return candidates
