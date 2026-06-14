from pathlib import Path 
from src.vectorstores.chroma_db import LocalVectorDatabase
from src.embeddings.huggingface_embeddings import logger

BASE_DIR = Path.cwd().resolve()
db_upload_directory = BASE_DIR / "config" / "data" / "vector_db"
pdf_upload_directory = BASE_DIR / "config" / "data" / "uploads" / "Neural-Network(Basics).pdf"

class Initiate_Retrieval :
    def __init__(self) :
        self.local_db_object = LocalVectorDatabase(db_upload_directory)
    
    def retrieve_candidates(self, collection_name : str, query_vector : list[float], pool_size : int = 10) -> list[str]:
        """Queries the native database matrix using a raw vector and flattens nested return arrays."""
        collection = self.local_db_object._get_collection(collection_name)

        try :
            results = collection.query(query_embeddings=[query_vector], n_results=pool_size)

            flat_results = []
            if results and results['documents'] :
                for i in range(len(results["documents"][0])) :
                    flat_results.append({
                        "id": results["ids"][0][i],
                        "text": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i]
                    })
            return flat_results
        except Exception as e:
            logger.error(f"Database query retrieval error: {e}")
            raise

    