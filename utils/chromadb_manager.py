"""Manages ChromaDB client and operations."""

import os
import logging
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.api.models.Collection import Collection

from utils.embedding_factory import EmbeddingFactory

logger = logging.getLogger(__name__)


class ChromaDBManager:
    """Manages ChromaDB client and email drafts collection."""

    def __init__(self, persist_directory: str = "data/chromadb"):
        """Initialize ChromaDB client with persistent storage.

        Args:
            persist_directory: Path to store ChromaDB data
        """
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None
        self._initialize()

    def _initialize(self):
        """Initialize ChromaDB client and collection.
        
        Note: If the collection exists with a different embedding function than currently
        configured, it will be deleted and recreated to ensure consistency with the
        current EMBEDDING_PROVIDER setting.
        """
        try:
            # Create persist directory if it doesn't exist
            os.makedirs(self.persist_directory, exist_ok=True)

            # Get embedding function from factory (based on EMBEDDING_PROVIDER env var)
            embedding_function = EmbeddingFactory.get_embedding_function()

            # Initialize ChromaDB with persistent storage
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            logger.info(f"Initialized ChromaDB client with path: {self.persist_directory}")

            # Try to get or create collection with current embedding function
            try:
                self.collection = self.client.get_or_create_collection(
                    name="email_drafts",
                    embedding_function=embedding_function,
                    metadata={"description": "Email drafts with semantic embeddings"},
                )
            except ValueError as e:
                error_msg = str(e).lower()
                # Check if error is due to embedding function mismatch
                if "embedding function" in error_msg and "already exists" in error_msg:
                    # Collection exists with different embedding function
                    # Delete and recreate to use current embedding function consistently
                    logger.warning(
                        "Collection exists with different embedding function. "
                        "Deleting and recreating to use current embedding provider."
                    )
                    try:
                        self.client.delete_collection(name="email_drafts")
                    except Exception as delete_error:
                        logger.warning(f"Error deleting collection (may not exist): {delete_error}")
                    
                    # Create new collection with current embedding function
                    self.collection = self.client.create_collection(
                        name="email_drafts",
                        embedding_function=embedding_function,
                        metadata={"description": "Email drafts with semantic embeddings"},
                    )
                    logger.info("Recreated email_drafts collection with current embedding function")
                else:
                    # Different error - re-raise
                    raise
            
            logger.info("Email drafts collection ready")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise

    def get_collection(self) -> Optional[Collection]:
        """Get the email_drafts collection.

        Returns:
            ChromaDB collection or None if initialization failed
        """
        return self.collection

    def index_draft(
        self, draft_content: str, metadata: Dict[str, Any]
    ) -> Optional[str]:
        """Index a draft in ChromaDB.

        Args:
            draft_content: Email body to embed and index
            metadata: Metadata dict with thread_id, timestamp, subject, etc.

        Returns:
            Document ID if successful, None otherwise
        """
        if not self.collection:
            logger.error("Collection not initialized")
            return None

        try:
            # Generate document ID from file path or use timestamp
            doc_id = metadata.get("file_path", "").replace("/", "_").replace(".", "_")
            if not doc_id:
                import time
                doc_id = f"draft_{int(time.time() * 1000)}"

            # Add document to collection
            self.collection.add(
                ids=[doc_id],
                documents=[draft_content],
                metadatas=[metadata],
            )
            logger.info(f"Indexed draft: {doc_id}")
            return doc_id
        except Exception as e:
            logger.error(f"Failed to index draft: {e}")
            return None

    def search_drafts(
        self, query: str, n_results: int = 5, filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Semantic search over drafts.

        Args:
            query: Search query (natural language)
            n_results: Number of results to return
            filters: Optional metadata filters

        Returns:
            List of matching drafts with metadata
        """
        if not self.collection:
            logger.error("Collection not initialized")
            return []

        try:
            # Perform semantic search
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=filters if filters else None,
            )

            # Format results
            formatted_results = []
            if results and results.get("ids") and results["ids"][0]:
                ids = results["ids"][0]
                documents = results.get("documents")
                metadatas = results.get("metadatas")
                distances = results.get("distances")
                
                for i, doc_id in enumerate(ids):
                    formatted_results.append(
                        {
                            "id": doc_id,
                            "document": documents[0][i] if documents and documents[0] else None,
                            "metadata": metadatas[0][i] if metadatas and metadatas[0] else None,
                            "distance": distances[0][i] if distances and distances[0] else None,
                        }
                    )
            logger.info(f"Search returned {len(formatted_results)} results for: {query}")
            return formatted_results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def get_draft_count(self) -> int:
        """Get total number of indexed drafts.

        Returns:
            Number of documents in collection
        """
        if not self.collection:
            return 0
        try:
            return self.collection.count()
        except Exception as e:
            logger.error(f"Failed to get draft count: {e}")
            return 0
