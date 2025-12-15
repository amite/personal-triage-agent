"""
LLM Drafting Agent - Specialized agent for drafting tasks
"""

from agents.ollama_client import OllamaClient
from tools.drafting_tool import DraftingTool

class LLMDraftingAgent:
    """LLM-powered Drafting Agent"""

    def __init__(self):
        self.llm = OllamaClient()

    def execute(self, content: str) -> str:
        return DraftingTool.execute(content, self.llm)
