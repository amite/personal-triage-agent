"""
LLM Triage Agent - Main triage agent using ReAct pattern
"""

from typing import List, Dict, Tuple
import json
import re
from agents.ollama_client import OllamaClient
from tools.reminder_tool import ReminderTool
from tools.drafting_tool import DraftingTool
from tools.external_search_tool import ExternalSearchTool

# Tool registry
AVAILABLE_TOOLS = {
    "reminder_tool": ReminderTool,
    "drafting_tool": DraftingTool,
    "search_tool": ExternalSearchTool
}

class LLMTriageAgent:
    """
    LLM-powered Triage Agent using ReAct pattern
    Uses Ollama to autonomously identify tasks and select tools
    """

    def __init__(self):
        self.llm = OllamaClient()

    def parse_request_with_llm(self, request: str) -> Tuple[List[Dict[str, str]], str]:
        """Use LLM to parse request into discrete tasks and return tasks plus reasoning"""

        tool_descriptions = "\n".join([
            f"- {name}: {tool.description}"
            for name, tool in AVAILABLE_TOOLS.items()
        ])

        prompt = f"""You are a task analysis expert. Analyze the following user request and break it down into discrete, actionable tasks.

User Request: "{request}"

Available Tools:
{tool_descriptions}

For each task you identify, specify:
1. Which tool should handle it (reminder_tool, drafting_tool, or search_tool)
2. The specific content/action for that task

Respond in this EXACT JSON format (valid JSON only, no extra text):
{{
  "tasks": [
    {{"tool": "tool_name", "content": "task description"}},
    {{"tool": "tool_name", "content": "task description"}}
  ],
  "reasoning": "Your reasoning for why you identified these tasks and chose these tools"
}}

JSON Response:"""

        try:
            response = self.llm.generate(prompt, temperature=0.3)

            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                tasks = parsed.get("tasks", [])
                reasoning = parsed.get("reasoning", "No reasoning provided")
                return tasks, reasoning
            else:
                # Fallback parsing
                return self._fallback_parse(request)

        except Exception as e:
            print(f"[yellow]LLM parsing failed, using fallback: {e}[/yellow]")
            return self._fallback_parse(request)

    def _fallback_parse(self, request: str) -> Tuple[List[Dict[str, str]], str]:
        """Fallback parsing if LLM fails"""
        tasks = []
        reasoning = "Using rule-based fallback parsing"

        if "email" in request.lower() or "draft" in request.lower():
            match = re.search(r"(?:draft|write|email).*?(?:about|regarding)\s+([^.,]+)", request, re.IGNORECASE)
            if match:
                tasks.append({"tool": "drafting_tool", "content": match.group(1).strip()})

        if "remind" in request.lower():
            match = re.search(r"remind.*?to\s+([^.,]+)", request, re.IGNORECASE)
            if match:
                tasks.append({"tool": "reminder_tool", "content": match.group(1).strip()})

        if "search" in request.lower() or "stock" in request.lower() or "check" in request.lower():
            match = re.search(r"(?:search|check|look up|stock price).*?(?:for|of)\s+([^.,]+)", request, re.IGNORECASE)
            if match:
                tasks.append({"tool": "search_tool", "content": match.group(1).strip()})

        if not tasks:
            tasks.append({"tool": "search_tool", "content": request})

        return tasks, reasoning
