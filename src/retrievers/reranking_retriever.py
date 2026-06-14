from src.embeddings.huggingface_embeddings import HuggingFaceEmbeddingEngine, logger

class PerformRetrieval_Reranking_Top_K:
    def __init__(self):
        self.model_object = HuggingFaceEmbeddingEngine()
        self.rerank_model = self.model_object.rerank_model

    def rerank_candidates(self, query: str, candidate_chunks: list[dict], top_k: int = 3) -> list[dict]:
        """Performs precise side-by-side semantic scoring to return the definitive top_k chunks."""
        if not candidate_chunks:
            return []

        try:
            pairs = [[query, chunk['text']] for chunk in candidate_chunks]
            scores = self.rerank_model.predict(pairs)

            for idx, score in enumerate(scores):
                candidate_chunks[idx]['rerank_score'] = float(score)
            
            candidate_chunks.sort(key=lambda x: x['rerank_score'], reverse=True)
            return candidate_chunks[:top_k]

        except Exception as e:
            logger.error(f"Error executing Cross-Encoder Re-Ranking: {e}")
            # Return original chunks sorted by distance if reranking fails
            return sorted(candidate_chunks, key=lambda x: x.get('distance', 0))[:top_k]