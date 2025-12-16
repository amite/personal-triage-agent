"""Semantic search tool for email drafts."""

import logging
from typing import List, Dict, Any

from utils.chromadb_manager import ChromaDBManager
from rich.console import Console
from rich.table import Table

logger = logging.getLogger(__name__)
console = Console()


class SearchDraftsTool:
    """Semantic search over historical email drafts."""

    description = (
        "Search historical email drafts by content. Use when user asks to find, "
        "search, or look up past drafts. Performs semantic search to find "
        "drafts related to the user's query."
    )

    def __init__(self):
        """Initialize search tool with ChromaDB manager."""
        self.chromadb = ChromaDBManager()

    @staticmethod
    def execute(content: str) -> str:
        """Execute semantic search over drafts.

        Args:
            content: Search query from user

        Returns:
            Formatted search results as string
        """
        tool = SearchDraftsTool()
        return tool._search_and_format(content)

    def _search_and_format(self, query: str) -> str:
        """Perform search and format results.

        Args:
            query: Search query

        Returns:
            Formatted results string
        """
        try:
            # Perform semantic search
            results = self.chromadb.search_drafts(query, n_results=5)

            if not results:
                return f"No drafts found matching your search for: '{query}'"

            # Format results
            return self._format_results(results, query)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return f"Error searching drafts: {e}"

    def _format_results(self, results: List[Dict[str, Any]], query: str) -> str:
        """Format search results for display.

        Args:
            results: List of search results
            query: Original search query

        Returns:
            Formatted string output
        """
        output_lines = [
            f"\n📧 Search Results for: '{query}'",
            f"Found {len(results)} matching drafts:\n",
        ]

        for i, result in enumerate(results, 1):
            metadata = result.get("metadata", {})
            document = result.get("document", "")
            distance = result.get("distance", 0)

            # Format result entry
            output_lines.append(f"{i}. {metadata.get('subject', 'Draft (no subject)')}")

            # Add metadata
            if metadata.get("timestamp"):
                output_lines.append(f"   📅 {metadata['timestamp']}")

            if metadata.get("file_path"):
                output_lines.append(f"   📄 {metadata['file_path']}")

            if metadata.get("user_request"):
                output_lines.append(f"   🎯 Request: {metadata['user_request'][:80]}...")

            # Add preview of content (first 150 chars)
            if document:
                preview = document[:150].replace("\n", " ")
                output_lines.append(f"   💬 Preview: {preview}...")

            # Add relevance score (lower distance = higher relevance)
            relevance = max(0, 100 - (distance * 100))
            output_lines.append(f"   ✅ Relevance: {relevance:.1f}%\n")

        return "\n".join(output_lines)
