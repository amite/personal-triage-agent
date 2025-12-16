"""Factory for creating embedding functions (local or OpenAI).

Note: ChromaDB expects embedding functions to conform to its internal interface,
including `name()` and `get_config()` methods for persistence/config tracking.
To avoid drift across Chroma versions, we prefer Chroma's built-in embedding
function implementations.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

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
        openai_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        local_model = os.getenv("LOCAL_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        local_device = os.getenv("LOCAL_EMBEDDING_DEVICE", "cpu")

        if provider == "openai":
            api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.warning(
                    "OPENAI_API_KEY not set, falling back to local embeddings"
                )
                provider = "local"
            else:
                from chromadb.utils import embedding_functions as ef

                # Prefer Chroma's built-in OpenAI embedding function to match
                # required interface methods (name/get_config) for persistence.
                return ef.OpenAIEmbeddingFunction(
                    api_key=api_key,
                    model_name=openai_model,
                    api_key_env_var="OPENAI_API_KEY",
                )

        # Default: Local sentence transformers (via Chroma's built-in wrapper)
        from chromadb.utils import embedding_functions as ef

        return ef.SentenceTransformerEmbeddingFunction(
            model_name=local_model,
            device=local_device,
        )
