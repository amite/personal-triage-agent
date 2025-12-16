"""Indexes draft files with checkpoint metadata."""

import logging
import re
from pathlib import Path
from typing import Optional, Dict, Any

from utils.chromadb_manager import ChromaDBManager
from utils.inspect_checkpoints import get_checkpoint_state

logger = logging.getLogger(__name__)


class DraftIndexer:
    """Indexes email drafts with checkpoint metadata."""

    def __init__(self):
        """Initialize draft indexer with ChromaDB manager."""
        self.chromadb = ChromaDBManager()

    def index_draft_file(
        self, file_path: str, thread_id: str, checkpoint_id: Optional[str] = None
    ) -> bool:
        """Index a draft file with checkpoint metadata.

        Args:
            file_path: Path to draft file
            thread_id: Thread ID for checkpoint lookup
            checkpoint_id: Optional specific checkpoint ID

        Returns:
            True if successful, False otherwise
        """
        try:
            # Read draft file
            draft_path = Path(file_path)
            if not draft_path.exists():
                logger.error(f"Draft file not found: {file_path}")
                return False

            with open(draft_path, "r", encoding="utf-8") as f:
                draft_content = f.read()

            # Extract metadata from draft file
            file_metadata = self._extract_file_metadata(draft_content, file_path)

            # Get checkpoint context
            checkpoint_metadata = self._get_checkpoint_metadata(thread_id, checkpoint_id)

            # Merge metadata
            merged_metadata = {**file_metadata, **checkpoint_metadata}

            # Index in ChromaDB
            doc_id = self.chromadb.index_draft(draft_content, merged_metadata)
            if doc_id:
                logger.info(f"Successfully indexed draft: {file_path}")
                return True
            else:
                logger.error(f"Failed to index draft in ChromaDB: {file_path}")
                return False

        except Exception as e:
            logger.error(f"Exception while indexing draft {file_path}: {e}")
            return False

    def _extract_file_metadata(self, content: str, file_path: str) -> Dict[str, Any]:
        """Extract metadata from draft file.

        Args:
            content: Draft file content
            file_path: Path to draft file

        Returns:
            Metadata dictionary
        """
        metadata = {"file_path": file_path}

        # Extract timestamp from filename (format: draft_YYYYMMDD_HHMMSS_*.txt)
        match = re.search(r"draft_(\d{8})_(\d{6})", file_path)
        if match:
            date_str = match.group(1)
            time_str = match.group(2)
            # Format as ISO timestamp: YYYY-MM-DDTHH:MM:SS
            timestamp = (
                f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                f"T{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"
            )
            metadata["timestamp"] = timestamp

        # Extract subject line (first line that looks like "Subject: ...")
        lines = content.split("\n")
        for line in lines:
            if line.startswith("Subject:"):
                metadata["subject"] = line.replace("Subject:", "").strip()
                break

        return metadata

    def _get_checkpoint_metadata(self, thread_id: str, checkpoint_id: Optional[str] = None) -> Dict[str, Any]:
        """Get metadata from checkpoint.

        Args:
            thread_id: Thread ID
            checkpoint_id: Optional checkpoint ID

        Returns:
            Metadata dictionary from checkpoint
        """
        metadata = {"thread_id": thread_id}

        try:
            state = get_checkpoint_state(thread_id, checkpoint_id)
            if state:
                # Extract relevant fields from AgentState
                if "user_request" in state:
                    metadata["user_request"] = state["user_request"]

                if "llm_reasoning" in state and isinstance(state["llm_reasoning"], list):
                    # Combine all reasoning entries
                    metadata["llm_reasoning"] = " ".join(state["llm_reasoning"])

                if "iteration" in state:
                    metadata["iteration"] = state["iteration"]

                logger.debug(f"Retrieved checkpoint metadata for thread {thread_id}")
        except Exception as e:
            logger.warning(f"Failed to get checkpoint metadata: {e}")

        return metadata
