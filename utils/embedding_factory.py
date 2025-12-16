"""Factory for creating embedding functions (local or OpenAI).

Note: ChromaDB expects embedding functions to conform to its internal interface,
including `name()` and `get_config()` methods for persistence/config tracking.
To avoid drift across Chroma versions, we prefer Chroma's built-in embedding
function implementations.
"""

import os
import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from chromadb.api.types import EmbeddingFunction

logger = logging.getLogger(__name__)


class EmbeddingFactory:
    """Factory for creating embedding functions."""

    @staticmethod
    def _detect_device() -> str:
        """Auto-detect the best available device for embeddings.
        
        Checks for CUDA (NVIDIA GPU), MPS (Apple Silicon), or falls back to CPU.
        
        Returns:
            Device string: 'cuda', 'mps', or 'cpu'
        """
        try:
            import torch
            
            if torch.cuda.is_available():
                logger.info("GPU (CUDA) detected - using GPU for embeddings")
                return "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                logger.info("Apple Silicon GPU (MPS) detected - using GPU for embeddings")
                return "mps"
            else:
                logger.info("No GPU detected - using CPU for embeddings")
                return "cpu"
        except ImportError:
            logger.debug("torch not available - using CPU for embeddings")
            return "cpu"
        except Exception as e:
            logger.warning(f"Error detecting GPU: {e} - falling back to CPU")
            return "cpu"

    @staticmethod
    def _get_device() -> str:
        """Get device for local embeddings from env var or auto-detect.
        
        Returns:
            Device string for embedding model
        """
        device = os.getenv("LOCAL_EMBEDDING_DEVICE")
        if device:
            logger.info(f"Using device from LOCAL_EMBEDDING_DEVICE env var: {device}")
            return device
        return EmbeddingFactory._detect_device()

    @staticmethod
    def _create_openai_embedding_function(model_name: str) -> Optional["EmbeddingFunction"]:
        """Create OpenAI embedding function if API key is available.
        
        Args:
            model_name: OpenAI embedding model name
            
        Returns:
            OpenAIEmbeddingFunction instance or None if API key missing
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not set, falling back to local embeddings")
            return None
        
        from chromadb.utils import embedding_functions as ef
        
        # Prefer Chroma's built-in OpenAI embedding function to match
        # required interface methods (name/get_config) for persistence.
        return ef.OpenAIEmbeddingFunction(
            api_key=api_key,
            model_name=model_name,
            api_key_env_var="OPENAI_API_KEY",
        )

    @staticmethod
    def _create_local_embedding_function(model_name: str, device: str) -> "EmbeddingFunction":
        """Create local sentence transformer embedding function.
        
        Args:
            model_name: Local embedding model name
            device: Device to use ('cpu', 'cuda', or 'mps')
            
        Returns:
            SentenceTransformerEmbeddingFunction instance
        """
        from chromadb.utils import embedding_functions as ef
        
        logger.info(f"Embedding config: model={model_name!r}, device={device!r}")
        return ef.SentenceTransformerEmbeddingFunction(
            model_name=model_name,
            device=device,
        )

    @staticmethod
    def get_embedding_function() -> "EmbeddingFunction":
        """Get embedding function based on EMBEDDING_PROVIDER env var.

        Environment variables:
            EMBEDDING_PROVIDER: 'local' (default) or 'openai'
            OPENAI_API_KEY: Required if EMBEDDING_PROVIDER=openai
            OPENAI_EMBEDDING_MODEL: OpenAI model name (default: 'text-embedding-3-small')
            LOCAL_EMBEDDING_MODEL: Local model name (default: 'all-MiniLM-L6-v2')
            LOCAL_EMBEDDING_DEVICE: Device override ('cpu', 'cuda', 'mps') or auto-detect

        Returns:
            Embedding function (callable)
        """
        provider = os.getenv("EMBEDDING_PROVIDER", "local").lower()
        
        # Try OpenAI provider if requested
        if provider == "openai":
            openai_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
            embedding_fn = EmbeddingFactory._create_openai_embedding_function(openai_model)
            if embedding_fn:
                return embedding_fn
            # Fall through to local if OpenAI fails
        
        # Default: Local sentence transformers
        local_model = os.getenv("LOCAL_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        device = EmbeddingFactory._get_device()
        return EmbeddingFactory._create_local_embedding_function(local_model, device)
