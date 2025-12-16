"""Factory for creating embedding functions (local or OpenAI)."""

import os
import logging
from typing import List

logger = logging.getLogger(__name__)


class SentenceTransformerEmbeddingFunction:
    """Local embedding using sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize sentence transformer model.

        Args:
            model_name: Model name from Hugging Face
        """
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
            logger.info(f"Loaded local embedding model: {model_name}")
        except ImportError:
            logger.error("sentence-transformers not installed")
            raise

    def __call__(self, texts: List[str]) -> List[List[float]]:
        """Embed texts using sentence-transformers.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        return self.model.encode(texts).tolist()


class OpenAIEmbeddingFunction:
    """OpenAI embedding function (switchable for production)."""

    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        """Initialize OpenAI embedding client.

        Args:
            api_key: OpenAI API key
            model: Embedding model to use
        """
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
            self.model = model
            logger.info(f"Initialized OpenAI embeddings with model: {model}")
        except ImportError:
            logger.error("openai not installed")
            raise

    def __call__(self, texts: List[str]) -> List[List[float]]:
        """Embed texts using OpenAI.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        response = self.client.embeddings.create(input=texts, model=self.model)
        return [item.embedding for item in response.data]


class EmbeddingFactory:
    """Factory for creating embedding functions."""

    @staticmethod
    def get_embedding_function():
        """Get embedding function based on EMBEDDING_PROVIDER env var.

        Environment variables:
            EMBEDDING_PROVIDER: 'local' (default) or 'openai'
            OPENAI_API_KEY: Required if EMBEDDING_PROVIDER=openai

        Returns:
            Embedding function (callable)
        """
        provider = os.getenv("EMBEDDING_PROVIDER", "local").lower()

        if provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.warning(
                    "OPENAI_API_KEY not set, falling back to local embeddings"
                )
                return SentenceTransformerEmbeddingFunction()
            return OpenAIEmbeddingFunction(api_key=api_key)

        # Default: Local sentence transformers
        return SentenceTransformerEmbeddingFunction()
