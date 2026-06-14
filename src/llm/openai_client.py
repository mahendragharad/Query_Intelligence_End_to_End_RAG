import os
import logging
from typing import List

from openai import OpenAI

logger = logging.getLogger(__name__)


class NVIDIAOpenAIClient:
    """NVIDIA-hosted OpenAI-compatible API client."""
    
    def __init__(
        self,
        model: str = "nvidia/nemotron-3-ultra-550b-a55b",
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int = 100,
    ):
        self.model = model
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://integrate.api.nvidia.com/v1")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.timeout = timeout

        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set; NVIDIA client will not be available")
            self.client = None
            return

        logger.info(f"Initializing NVIDIA OpenAI client for model {self.model}")
        try:
            self.client = OpenAI(base_url=self.base_url, api_key=self.api_key, timeout=timeout)
        except Exception as e:
            logger.error(f"Failed to initialize NVIDIA client: {e}")
            self.client = None


    def build_prompt(query: str, context_chunks: List[dict]) -> str:
        """
        Build a structured RAG prompt from retrieved chunks.

        Args:
            query: User question
            context_chunks: Retrieved document chunks

        Returns:
            Formatted prompt string
        """

        if not context_chunks:
            return f"""
        
        Question:
        {query}

        No context was retrieved.
        If you cannot answer confidently, state that the information is unavailable.
        """

        formatted_chunks = []

        for index, chunk in enumerate(context_chunks, start=1):

            source = chunk.get("source", "Unknown Source")
            page = chunk.get("page", "N/A")
            text = chunk.get("text", "").strip()

            formatted_chunks.append(
                f"""
            ==================================================
            DOCUMENT CHUNK {index}

            Source : {source}
            Page   : {page}

            {text}
            ==================================================
            """
            )

            context = "\n".join(formatted_chunks)

            prompt = f"""
            You are an expert AI Research Assistant.

            Your task is to answer the user's question ONLY using the information provided
            inside the retrieved document chunks.

            Instructions:

            1. Read every context chunk carefully.
            2. Combine information from multiple chunks whenever possible.
            3. Do NOT invent facts.
            4. If the answer is partially available, clearly mention what is available.
            5. If the answer is not present, respond:
            "The provided documents do not contain enough information to answer this question."

            Formatting Rules:

            - Use Markdown.
            - Use headings.
            - Use bullet points.
            - Use numbered lists when appropriate.
            - Explain concepts clearly.
            - Avoid repeating the same information.
            - Generate a detailed answer instead of a one-line summary.

            ====================================================================

            RETRIEVED DOCUMENTS

            {context}

            ====================================================================

            USER QUESTION

            {query}

            ====================================================================

            Generate a comprehensive answer.
            """

        return prompt

    def generate_answer(self, query: str, context_chunks: List[dict]) -> str:

        if not self.client:
            logger.warning("LLM client unavailable")
            return ""

        try:

            prompt = self.build_prompt(query, context_chunks)

            logger.info("=" * 80)
            logger.info(f"Prompt Length : {len(prompt)} characters")
            logger.info(f"Retrieved Chunks : {len(context_chunks)}")
            logger.info("=" * 80)

            response = self.client.chat.completions.create(

                model=self.model,

                messages=[
                    {
                        "role": "system",
                        "content": """
                        You are an intelligent document assistant.

                        Use ONLY the supplied document context.

                        Always produce well-structured answers using:

                        - Headings
                        - Bullet points
                        - Tables when appropriate
                        - Explanations

                        Never hallucinate information.

                        If information is unavailable, explicitly say so.
                        """
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

                temperature=0.2,
                max_tokens=1200,

            )

            answer = response.choices[0].message.content.strip()

            logger.info("Answer generated successfully.")

            return answer

        except Exception as e:

            logger.exception(f"Answer generation failed: {e}")

            return ""