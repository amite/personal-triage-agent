"""
LLM Triage Agent - Main triage agent using ReAct pattern
"""

from typing import List, Dict, Tuple, Optional
import re
import logging
from functools import lru_cache
from pydantic import BaseModel, Field
from agents.llm_client_base import LLMClientBase
from agents.llm_factory import LLMFactory
from tools.reminder_tool import ReminderTool
from tools.drafting_tool import DraftingTool
from tools.external_search_tool import ExternalSearchTool

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
    "search_tool": ExternalSearchTool
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
            logger.warning(f"Invalid request input: {request}")
            return self._fallback_parse(request)

        request = request.strip()
        if not request:
            logger.warning("Empty request after stripping")
            return self._fallback_parse(request)

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
                logger.warning(f"Pydantic parsing failed: {e}, attempting fallback extraction")
                return self._fallback_extract_json(response, request)

        except Exception as e:
            logger.error(f"LLM generation failed: {e}", exc_info=True)
            return self._fallback_parse(request)

    def _fallback_extract_json(self, response: str, request: str) -> ParseResult:
        """Simple fallback JSON extraction from LLM response

        Args:
            response: Raw LLM response
            request: Original user request (for fallback parsing)

        Returns:
            ParseResult: Tuple containing (task_list, reasoning_string)
        """
        try:
            # Try simple brace matching
            start = response.find('{')
            if start == -1:
                logger.warning("No JSON object found in response")
                return self._fallback_parse(request)

            brace_count = 0
            for i, char in enumerate(response[start:]):
                brace_count += (char == '{') - (char == '}')
                if brace_count == 0:
                    json_str = response[start:start+i+1]
                    parsed = TaskResponse.model_validate_json(json_str)
                    tasks = [{"tool": task.tool, "content": task.content} for task in parsed.tasks]
                    logger.info(f"Extracted {len(tasks)} tasks from malformed JSON")
                    return tasks, parsed.reasoning

            logger.warning("Could not extract valid JSON from response")
            return self._fallback_parse(request)

        except Exception as e:
            logger.warning(f"JSON extraction failed: {e}")
            return self._fallback_parse(request)

    def _fallback_parse(self, request: str) -> ParseResult:
        """Fallback parsing if LLM fails
        
        Uses rule-based parsing to extract tasks from user requests.
        Handles various edge cases and provides structured fallback.
        
        Args:
            request: User request string to parse
            
        Returns:
            ParseResult: Tuple containing (task_list, reasoning_string)
        """
        if not request or not isinstance(request, str):
            logger.warning("Invalid request in fallback parser")
            return [], "Invalid request format"
        
        try:
            tasks = []
            reasoning = "Using rule-based fallback parsing"
            request_lower = request.lower().strip()

            # Email/draft detection with improved regex
            if "email" in request_lower or "draft" in request_lower:
                try:
                    match = re.search(
                        r"(?:draft|write|compose|create|email).*?(?:about|regarding|for|topic)\s+([^.,;]+)",
                        request,
                        re.IGNORECASE
                    )
                    if match:
                        content = match.group(1).strip()
                        if content:  # Only add if content is not empty
                            tasks.append({"tool": "drafting_tool", "content": content})
                except re.error as re_err:
                    logger.error(f"Regex error in draft parsing: {re_err}")

            # Reminder detection with improved regex
            if "remind" in request_lower:
                try:
                    match = re.search(
                        r"remind(?:\s+me)?\s+(?:to|about|that)\s+([^.,;]+)",
                        request,
                        re.IGNORECASE
                    )
                    if match:
                        content = match.group(1).strip()
                        if content:
                            tasks.append({"tool": "reminder_tool", "content": content})
                except re.error as re_err:
                    logger.error(f"Regex error in reminder parsing: {re_err}")

            # Search detection with improved regex and more keywords
            search_keywords = ["search", "stock", "check", "look up", "find", "research", "query"]
            if any(keyword in request_lower for keyword in search_keywords):
                try:
                    # More comprehensive search pattern
                    pattern = r"(?:search|check|look\s+up|find|research|query|stock\s+price|market\s+data).*?(?:for|about|on|regarding)\s+([^.,;]+)"
                    match = re.search(pattern, request, re.IGNORECASE)
                    if match:
                        content = match.group(1).strip()
                        if content:
                            tasks.append({"tool": "search_tool", "content": content})
                except re.error as re_err:
                    logger.error(f"Regex error in search parsing: {re_err}")

            # If no specific tasks found, use generic search
            if not tasks:
                # Extract meaningful content from request
                if len(request.split()) > 3:  # If request has more than 3 words
                    content = " ".join(request.split()[:10])  # Take first 10 words
                    tasks.append({"tool": "search_tool", "content": content})
                else:
                    tasks.append({"tool": "search_tool", "content": request})

            # Remove duplicate tasks
            seen_tasks = set()
            unique_tasks = []
            for task in tasks:
                task_key = (task["tool"], task["content"])
                if task_key not in seen_tasks:
                    seen_tasks.add(task_key)
                    unique_tasks.append(task)

            logger.info(f"Fallback parser generated {len(unique_tasks)} tasks")
            return unique_tasks, reasoning

        except Exception as e:
            logger.error(f"Fallback parsing failed: {e}", exc_info=True)
            # Ultimate fallback - return empty tasks with error reasoning
            return [], f"Parsing failed: {str(e)}"
