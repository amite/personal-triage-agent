"""
LLM Triage Agent - Main triage agent using ReAct pattern
"""

from typing import List, Dict, Tuple, Optional, TypedDict
import json
import re
import logging
from functools import lru_cache
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

class TaskResponse(TypedDict):
    """TypedDict for structured task response from LLM"""
    tasks: List[Dict[str, str]]
    reasoning: str

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
            JSONDecodeError: If LLM response contains invalid JSON
        """
        
        # Input validation
        if not request or not isinstance(request, str):
            logger.warning(f"Invalid request input: {request}")
            return self._fallback_parse(request)
        
        # Strip and normalize request
        request = request.strip()
        if not request:
            logger.warning("Empty request after stripping")
            return self._fallback_parse(request)
        
        # Use cached tool descriptions
        tool_descriptions = self._tool_cache

        prompt = f"""You are a task analysis expert. Analyze the following user request and break it down into discrete, actionable tasks.

User Request: "{request}"

Available Tools:
{tool_descriptions}

For each task you identify, specify:
1. Which tool should handle it (reminder_tool, drafting_tool, or search_tool)
2. The specific content/action for that task

IMPORTANT: Respond ONLY with valid JSON in this EXACT format. Do NOT include any additional text, explanations, or markdown formatting. Only return the JSON object:
{{
  "tasks": [
    {{"tool": "tool_name", "content": "task description"}},
    {{"tool": "tool_name", "content": "task description"}}
  ],
  "reasoning": "Your reasoning for why you identified these tasks and chose these tools"
}}

JSON Response:"""

        try:
            logger.info(f"Processing request: {request[:50]}...")
            response = self.llm.generate(prompt, temperature=0.3)
            logger.info(f"Full LLM response: {response}")

            # Extract JSON from response with better error handling
            # Try multiple approaches to find valid JSON
            json_str = None
            
            # Approach 1: Look for JSON that starts with { and ends with } - handle nested objects
            # Use a more sophisticated approach to find balanced braces
            json_str = None
            try:
                # Try to find the outermost JSON object
                brace_count = 0
                start_idx = response.find('{')
                if start_idx != -1:
                    for i, char in enumerate(response[start_idx:]):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                json_str = response[start_idx:start_idx+i+1]
                                break
            except Exception:
                pass
            
            # Approach 2: If that fails, try to find the first valid JSON object
            if not json_str:
                try:
                    # Try to find JSON by looking for the pattern we expect
                    json_pattern = r'\{["\']tasks["\']\s*:\s*\[.*?\]\s*,\s*["\']reasoning["\']\s*:\s*["\'].+?["\']\s*\}'
                    json_match = re.search(json_pattern, response, re.DOTALL)
                    if json_match:
                        json_str = json_match.group()
                except Exception:
                    pass
            
            # Approach 3: Try to parse the entire response as JSON
            if not json_str:
                try:
                    entire_response = json.loads(response)
                    if isinstance(entire_response, dict) and "tasks" in entire_response:
                        json_str = response
                except json.JSONDecodeError:
                    pass
            
            if json_str:
                try:
                    parsed = json.loads(json_str)
                    
                    # Validate parsed structure
                    if not isinstance(parsed, dict):
                        raise ValueError("LLM response is not a dictionary")
                    
                    tasks = parsed.get("tasks", [])
                    reasoning = parsed.get("reasoning", "No reasoning provided")
                    
                    # Validate tasks structure
                    if not isinstance(tasks, list):
                        tasks = []
                        logger.warning("Invalid tasks format in LLM response")
                    
                    # Ensure all tasks have required fields
                    validated_tasks = []
                    for task in tasks:
                        if isinstance(task, dict) and "tool" in task and "content" in task:
                            validated_tasks.append({
                                "tool": str(task["tool"]),
                                "content": str(task["content"])
                            })
                        else:
                            logger.warning(f"Invalid task format: {task}")
                    
                    logger.info(f"Successfully parsed {len(validated_tasks)} tasks")
                    return validated_tasks, str(reasoning)
                    
                except json.JSONDecodeError as json_err:
                    logger.error(f"JSON decode error: {json_err}")
                    logger.debug(f"Failed to parse JSON: {json_str}")
                    
                    # Attempt to repair the JSON
                    repaired_json = self._attempt_json_repair(json_str)
                    if repaired_json:
                        try:
                            parsed = json.loads(repaired_json)
                            logger.info("Successfully repaired JSON")
                            
                            # Validate parsed structure
                            if not isinstance(parsed, dict):
                                raise ValueError("LLM response is not a dictionary")
                            
                            tasks = parsed.get("tasks", [])
                            reasoning = parsed.get("reasoning", "No reasoning provided")
                            
                            # Validate tasks structure
                            if not isinstance(tasks, list):
                                tasks = []
                                logger.warning("Invalid tasks format in LLM response")
                            
                            # Ensure all tasks have required fields
                            validated_tasks = []
                            for task in tasks:
                                if isinstance(task, dict) and "tool" in task and "content" in task:
                                    validated_tasks.append({
                                        "tool": str(task["tool"]),
                                        "content": str(task["content"])
                                    })
                                else:
                                    logger.warning(f"Invalid task format: {task}")
                            
                            logger.info(f"Successfully parsed {len(validated_tasks)} tasks from repaired JSON")
                            return validated_tasks, str(reasoning)
                            
                        except Exception as repair_err:
                            logger.error(f"JSON repair failed: {repair_err}")
                            return self._fallback_parse(request)
                    else:
                        return self._fallback_parse(request)
            else:
                logger.warning("No JSON found in LLM response, using fallback")
                logger.debug(f"LLM response: {response}")
                return self._fallback_parse(request)

        except Exception as e:
            logger.error(f"LLM parsing failed, using fallback: {e}", exc_info=True)
            return self._fallback_parse(request)

    def _attempt_json_repair(self, json_str: str) -> Optional[str]:
        """Attempt to repair common JSON issues in LLM responses"""
        try:
            logger.debug(f"Attempting to repair JSON: {json_str}")
            
            # Fix common issues
            repaired = json_str.strip()
            
            # Remove trailing commas
            repaired = re.sub(r',\s*([}\]])\s*', r'\1', repaired)
            
            # Fix missing commas between array elements (the specific error we're seeing)
            repaired = re.sub(r'\}\s*\{', r'}, {', repaired)
            
            # Fix missing commas between array elements - more comprehensive
            repaired = re.sub(r'"\s*"', r'", "', repaired)
            
            # Fix missing commas in task arrays specifically
            repaired = re.sub(r'(\}\s*)(\})', r'\1,\2', repaired)
            
            # Fix missing quotes around keys
            repaired = re.sub(r'([{,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', repaired)
            
            # Fix single quotes to double quotes
            repaired = repaired.replace("'", '"')
            
            # Fix missing commas in arrays
            repaired = re.sub(r'"\s*"', r'", "', repaired)
            
            # Try to parse the repaired JSON
            json.loads(repaired)
            logger.debug(f"Successfully repaired JSON: {repaired}")
            return repaired
        except Exception as e:
            logger.debug(f"JSON repair failed: {e}")
            return None

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
