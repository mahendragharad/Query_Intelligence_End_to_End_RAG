import logging 
import torch
from langchain_community.embeddings import HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer, CrossEncoder

# Setup structured pipeline logging
logger = logging.getLogger("IngestionPipeline.EmbedAndStore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class HuggingFaceEmbeddingEngine :

    def __init__(self, embedding_model : str = "BAAI/bge-small-en-v1.5", rerank_model : str = "BAAI/bge-reranker-base") :
        self.device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"

        try : 
            logger.info(f"Loading step - 1 Bi-Encoder '{embedding_model}' on {self.device}")
            self.embed_model = SentenceTransformer(embedding_model, device=self.device)

            logger.info(f"Loading Stage-2 Cross Encoder '{rerank_model}' on {self.device}")        
            self.rerank_model = CrossEncoder(rerank_model, device=self.device)

        except Exception as e :
            logger.error(f"Failed to initiate neura network models: {e}")
            raise RuntimeError(f"ML engine Init Failure :{e}")
        
    
    def get_embeddings(self, text_chunks : list[str]) -> list[list[float]] :
        if not text_chunks :
            return []
        try : 
            vectors = self.embed_model.encode(text_chunks, batch_size=32, normalize_embeddings=True)
            return vectors.tolist()
        except Exception as e :
            logger.error(f"Error computing text vector spaces: {e}")
            raise