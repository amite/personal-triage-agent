"""
LLM Drafting Agent - Specialized agent for drafting tasks
"""

from typing import Optional, Dict, Any
from agents.llm_client_base import LLMClientBase
from agents.llm_factory import LLMFactory
from tools.drafting_tool import DraftingTool

class LLMDraftingAgent:
    """LLM-powered Drafting Agent"""

    def __init__(self, llm_client: Optional[LLMClientBase] = None):
        """
        Initialize the drafting agent
        
        Args:
            llm_client: Optional LLM client. If not provided, uses factory to create default client
        """
        self.llm = llm_client or LLMFactory.get_llm_client_from_env()

    def execute(
        self, 
        content: str,
        thread_id: Optional[str] = None,
        checkpoint_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute drafting with thread and checkpoint context.
        
        Args:
            content: Email topic or content
            thread_id: Optional thread ID for linking to execution
            checkpoint_id: Optional checkpoint ID
        
        Returns:
            Dictionary with success, draft_id, subject, and message
        """
        return DraftingTool.execute(
            content, 
            self.llm,
            thread_id=thread_id,
            checkpoint_id=checkpoint_id
        )
