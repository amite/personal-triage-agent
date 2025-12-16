"""
LLM Triage Agent - Main triage agent using ReAct pattern
"""

from typing import List, Dict, Tuple, Optional
import logging
from functools import lru_cache
from pydantic import BaseModel, Field
from agents.llm_client_base import LLMClientBase
from agents.llm_factory import LLMFactory
from tools.reminder_tool import ReminderTool
from tools.drafting_tool import DraftingTool
from tools.external_search_tool import ExternalSearchTool
from tools.search_drafts_tool import SearchDraftsTool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type aliases for better readability and maintainability
Task = Dict[str, str]
TaskList = List[Task]
ParseResult = Tuple[TaskList, str]

class TaskItem(BaseModel):
    """Structured task item from LLM"""
    tool: str = Field(description="Tool name: reminder_tool, drafting_tool, or search_tool")
    content: str = Field(description="Task content or description")

class TaskResponse(BaseModel):
    """Structured task response from LLM"""
    tasks: List[TaskItem] = Field(description="List of identified tasks")
    reasoning: str = Field(description="Reasoning for identified tasks")

# Tool registry
AVAILABLE_TOOLS = {
    "reminder_tool": ReminderTool,
    "drafting_tool": DraftingTool,
    "search_tool": ExternalSearchTool,
    "search_drafts_tool": SearchDraftsTool
}

class LLMTriageAgent:
    """
    LLM-powered Triage Agent using ReAct pattern
    Uses environment-configured LLM client (Ollama or GPT) to autonomously identify tasks and select tools
    """

    def __init__(self, llm_client: Optional[LLMClientBase] = None):
        """
        Initialize the triage agent
        
        Args:
            llm_client: Optional LLM client. If not provided, uses factory to create default client
        """
        self.llm = llm_client or LLMFactory.get_llm_client_from_env()
        self._tool_cache = self._build_tool_cache()

    def _build_tool_cache(self) -> str:
        """Build and cache tool descriptions for performance"""
        return "\n".join([
            f"- {name}: {tool.description}"
            for name, tool in AVAILABLE_TOOLS.items()
        ])

    @lru_cache(maxsize=100)
    def parse_request_with_llm(self, request: str) -> ParseResult:
        """Use LLM to parse request into discrete tasks and return tasks plus reasoning

        Args:
            request: User request string to parse

        Returns:
            ParseResult: Tuple containing (task_list, reasoning_string)

        Raises:
            ValueError: If request is empty or invalid
        """

        # Input validation
        if not request or not isinstance(request, str):
            raise ValueError(f"Invalid request input: {request}")
        
        request = request.strip()
        if not request:
            raise ValueError("Empty request after stripping")

        tool_descriptions = self._tool_cache
        prompt = f"""You are a task analysis expert. Analyze the following user request and break it down into discrete, actionable tasks.

User Request: "{request}"

Available Tools:
{tool_descriptions}

For each task you identify, specify which tool should handle it and what the task is.

Respond with JSON in this exact format:
{{
  "tasks": [
    {{"tool": "reminder_tool", "content": "task description"}},
    {{"tool": "drafting_tool", "content": "task description"}}
  ],
  "reasoning": "Your reasoning for these tasks"
}}"""

        try:
            logger.info(f"Processing request: {request[:50]}...")
            response = self.llm.generate(prompt, temperature=0.3)
            logger.info(f"LLM response: {response[:200]}...")

            # Try to parse response using Pydantic
            try:
                parsed = TaskResponse.model_validate_json(response)
                tasks = [{"tool": task.tool, "content": task.content} for task in parsed.tasks]
                logger.info(f"Successfully parsed {len(tasks)} tasks")
                return tasks, parsed.reasoning
            except Exception as e:
                logger.error(f"Pydantic parsing failed: {e}")
                raise ValueError(
                    f"LLM response could not be parsed as valid JSON. "
                    f"Expected format: {{'tasks': [{{'tool': '...', 'content': '...'}}], 'reasoning': '...'}}. "
                    f"Response received: {response[:500]}..."
                )

        except Exception as e:
            logger.error(f"LLM generation failed: {e}", exc_info=True)
            raise ValueError(f"LLM failed to process request: {e}. Please ensure your LLM provider is configured correctly and the API is accessible.")

