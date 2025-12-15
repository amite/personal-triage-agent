"""
LLM Drafting Agent - Specialized agent for drafting tasks
"""

from typing import Optional
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

    def execute(self, content: str) -> str:
        return DraftingTool.execute(content, self.llm)
