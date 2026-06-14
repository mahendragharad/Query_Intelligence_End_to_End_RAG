import os
import logging
from typing import List, Optional

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

logger = logging.getLogger(__name__)

class OllamaClient:
    """Local Ollama LLM client - fast, reliable, no API timeouts."""
    
    def __init__(
        self,
        model: str = "gemma3:4b",
        base_url: Optional[str] = None,
        timeout: int = 300,
    ):
        self.model = model
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.timeout = timeout
        self.available = False
        
        if not HAS_REQUESTS:
            logger.warning("The 'requests' library is not installed. Ollama client disabled.")
            return
        
        # Test connection to the local Ollama server
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                self.available = True
                logger.info(f"Ollama connected at {self.base_url} using model: {model}")
            else:
                logger.warning(f"Ollama server found but returned status {resp.status_code}")
        except Exception as e:
            logger.debug(f"Ollama server not reachable: {e}")

    def _format_prompt(self, query: str, context_chunks: List[dict]) -> str:
        """Helper to build the structured RAG prompt."""
        formatted_chunks = []
        for index, chunk in enumerate(context_chunks, start=1):
            source = chunk.get("source", "Unknown Document")
            text = chunk.get("text", "").strip()
            formatted_chunks.append(
                f"DOCUMENT CHUNK {index}\nSOURCE: {source}\nCONTENT:\n{text}\n" + ("=" * 40)
            )

        context_block = "\n".join(formatted_chunks)
        
        return f"""You are an expert AI Research Assistant.
Your job is to answer the user's question ONLY using the retrieved document context.

Instructions:
- Read every document carefully.
- Combine information from multiple chunks.
- Never invent facts.
- If information is unavailable, explicitly say so.

Response Format:
# Overview
# Detailed Explanation
# Important Points
# Conclusion

Retrieved Documents:
{context_block}

------------------------------------------------
User Question:
{query}

Generate a comprehensive answer."""

    def generate_answer(self, query: str, context_chunks: List[dict]) -> str:
        """Generates an answer using the local Ollama model via POST request."""
        if not self.available or not HAS_REQUESTS:
            logger.error("Ollama client is not available or requests is not installed.")
            return ""

        try:
            prompt = self._format_prompt(query, context_chunks)
            
            logger.info("=" * 40)
            logger.info(f"Ollama Call | Prompt Len: {len(prompt)} | Chunks: {len(context_chunks)}")
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "top_p": 0.9,
                    "num_predict": 1024,
                    "repeat_penalty": 1.1,
                },
            }

            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            answer = result.get("response", "").strip()

            logger.info(f"Generation successful. Answer length: {len(answer)}")
            return answer

        except requests.exceptions.Timeout:
            logger.error(f"Ollama request timed out after {self.timeout}s.")
            return "Error: The local model took too long to respond."
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error contacting Ollama: {e}")
            self.available = False  # Disable future calls if server is down
            return ""
            
        except Exception as e:
            logger.exception(f"An unexpected error occurred during generation: {e}")
            return ""