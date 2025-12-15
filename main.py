"""
Personal Task Manager Triage - A Multi-Agent Task Management System
Built with LangGraph using LLMs (Ollama) and the ReAct agent pattern
"""

import json
import re
from typing import TypedDict, List, Dict, Annotated, Literal, Optional, cast
from dataclasses import dataclass
from datetime import datetime
import requests

from langgraph.graph import StateGraph, END
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from rich.tree import Tree
from rich import print as rprint

# Initialize Rich console
console = Console()

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "llama3.1:8b-instruct-q4_K_M"  # You can change this to your preferred model


# ============================================================================
# OLLAMA CLIENT
# ============================================================================

class OllamaClient:
    """Client for interacting with Ollama API"""
    
    @staticmethod
    def generate(prompt: str, model: str = MODEL_NAME, temperature: float = 0.7) -> str:
        """Generate text using Ollama"""
        try:
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": temperature
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json()["response"]
        except requests.exceptions.ConnectionError:
            console.print("[bold red]Error: Cannot connect to Ollama. Make sure Ollama is running.[/bold red]")
            console.print("[yellow]Start Ollama with: ollama serve[/yellow]")
            raise
        except Exception as e:
            console.print(f"[bold red]Error generating response: {e}[/bold red]")
            raise


# ============================================================================
# STATE DEFINITION
# ============================================================================

class AgentState(TypedDict):
    user_request: str
    task_queue: List[Dict[str, str]]
    results: Dict[str, str]
    current_task: Dict[str, str]
    iteration: int
    agent_thoughts: List[str]
    llm_reasoning: List[str]


# ============================================================================
# TOOLS - Simulated External Functions
# ============================================================================

class ReminderTool:
    """Writes reminders to a persistent file"""

    name = "reminder_tool"
    description = "Sets a reminder for a specific task or event. Use this when the user wants to remember something or be reminded about an action."

    @staticmethod
    def execute(content: str) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        reminder_text = f"[{timestamp}] REMINDER: {content}\n"

        try:
            # Create inbox/reminders directory if it doesn't exist
            import os
            os.makedirs("inbox/reminders", exist_ok=True)

            # Create filename with timestamp
            safe_content = re.sub(r'[^\w\s-]', '', content[:30]).strip()
            filename = f"inbox/reminders/reminder_{file_timestamp}_{safe_content}.txt"

            with open(filename, "w") as f:
                f.write(reminder_text)
            return f"✓ Reminder saved to {filename}: '{content}'"
        except Exception as e:
            return f"✗ Failed to set reminder: {str(e)}"


class DraftingTool:
    """Generates and saves draft emails"""

    name = "drafting_tool"
    description = "Drafts an email based on the given topic or content. Use this when the user needs to write, compose, or draft an email or message."

    @staticmethod
    def execute(content: str, llm_client: Optional[OllamaClient] = None) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Use LLM to generate email body
        if llm_client:
            email_prompt = f"""Write a professional email about: {content}

Generate ONLY the email body (no subject line, no greeting, no signature). Keep it concise and professional, maximum 3-4 sentences.

Email body:"""

            try:
                email_body = llm_client.generate(email_prompt, temperature=0.7).strip()
            except:
                email_body = f"I wanted to reach out regarding {content}. Please let me know your thoughts at your earliest convenience."
        else:
            email_body = f"I wanted to reach out regarding {content}. Please let me know your thoughts at your earliest convenience."

        draft = f"""
{'='*60}
DRAFT EMAIL - {timestamp}
{'='*60}

Subject: Re: {content}

Dear Recipient,

{email_body}

Best regards,
[Your Name]

{'='*60}
"""

        try:
            # Create inbox/drafts directory if it doesn't exist
            import os
            os.makedirs("inbox/drafts", exist_ok=True)

            # Create filename with timestamp
            safe_content = re.sub(r'[^\w\s-]', '', content[:30]).strip()
            filename = f"inbox/drafts/draft_{file_timestamp}_{safe_content}.txt"

            with open(filename, "w") as f:
                f.write(draft)
            return f"✓ Email draft saved to {filename} about: '{content[:50]}...'"
        except Exception as e:
            return f"✗ Failed to save draft: {str(e)}"


class ExternalSearchTool:
    """Simulates external data lookup"""
    
    name = "search_tool"
    description = "Searches for information, looks up data, checks files, or retrieves external information. Use this for queries about stock prices, weather, file checks, or any factual lookup."
    
    @staticmethod
    def execute(query: str) -> str:
        query_lower = query.lower()
        
        if "stock" in query_lower and "google" in query_lower:
            return "✓ Google (GOOGL) stock price: $142.50 (Last updated: Today)"
        elif "stock" in query_lower:
            return f"✓ Stock information: Market data retrieved for '{query}'"
        elif "weather" in query_lower:
            return "✓ Weather: 72°F, Partly Cloudy, 10% chance of rain"
        elif "file" in query_lower or "document" in query_lower or "attach" in query_lower:
            return f"✓ File check: Found 3 relevant files ready for review"
        else:
            return f"✓ Search result: Information retrieved for '{query}'"


# ============================================================================
# TOOL REGISTRY
# ============================================================================

AVAILABLE_TOOLS = {
    "reminder_tool": ReminderTool,
    "drafting_tool": DraftingTool,
    "search_tool": ExternalSearchTool
}


# ============================================================================
# TRIAGE AGENT WITH LLM
# ============================================================================

class LLMTriageAgent:
    """
    LLM-powered Triage Agent using ReAct pattern
    Uses Ollama to autonomously identify tasks and select tools
    """
    
    def __init__(self):
        self.llm = OllamaClient()
    
    def parse_request_with_llm(self, request: str) -> tuple[List[Dict[str, str]], str]:
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
            console.print(f"[yellow]LLM parsing failed, using fallback: {e}[/yellow]")
            return self._fallback_parse(request)
    
    def _fallback_parse(self, request: str) -> tuple[List[Dict[str, str]], str]:
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


class LLMDraftingAgent:
    """LLM-powered Drafting Agent"""
    
    def __init__(self):
        self.llm = OllamaClient()
    
    def execute(self, content: str) -> str:
        return DraftingTool.execute(content, self.llm)


# ============================================================================
# GRAPH NODES
# ============================================================================

def triage_node(state: AgentState) -> AgentState:
    """Triage Agent Node - LLM-powered analysis and routing"""
    
    if state["iteration"] == 0:
        console.print(Panel.fit(
            "[bold cyan]🤖 LLM Triage Agent[/bold cyan]\n"
            "Analyzing request with AI...",
            border_style="cyan"
        ))
        
        agent = LLMTriageAgent()
        tasks, reasoning = agent.parse_request_with_llm(state["user_request"])
        
        state["task_queue"] = tasks
        state["iteration"] = 1
        state["llm_reasoning"].append(f"Triage: {reasoning}")
        state["agent_thoughts"].append(f"Identified {len(tasks)} tasks using LLM analysis")
        
        # Display LLM reasoning
        console.print(Panel(
            f"[bold]LLM Reasoning:[/bold]\n{reasoning}",
            title="💭 AI Analysis",
            border_style="blue"
        ))
        
        # Display identified tasks
        task_list = "\n".join([
            f"  {i+1}. [{task['tool']}] {task['content']}"
            for i, task in enumerate(tasks)
        ])
        console.print(Panel(
            f"[bold]Identified Tasks:[/bold]\n{task_list}",
            border_style="green"
        ))
    
    return state


def tool_execution_node(state: AgentState) -> AgentState:
    """Universal tool execution node"""
    
    if not state["task_queue"]:
        return state
    
    current_task = state["task_queue"][0]
    tool_name = current_task["tool"]
    content = current_task["content"]
    
    # Get tool and execute
    tool_class = AVAILABLE_TOOLS.get(tool_name)
    
    if not tool_class:
        result = f"✗ Unknown tool: {tool_name}"
    else:
        # Display execution
        tool_display_names = {
            "reminder_tool": "⏰ Scheduler Agent",
            "drafting_tool": "✉️  Drafting Agent", 
            "search_tool": "🔍 Data Agent"
        }
        
        display_name = tool_display_names.get(tool_name, tool_name)
        console.print(Panel.fit(
            f"[bold]{display_name}[/bold]\nExecuting: {content[:60]}...",
            border_style="green"
        ))
        
        # Execute tool
        if tool_name == "drafting_tool":
            llm_agent = LLMDraftingAgent()
            result = llm_agent.execute(content)
        else:
            result = tool_class.execute(content)
    
    # Update state
    state["results"][f"{tool_name}_{state['iteration']}"] = result
    state["task_queue"].pop(0)
    state["agent_thoughts"].append(f"Executed {tool_name}: {content[:50]}")
    state["iteration"] += 1
    
    return state


def finish_node(state: AgentState) -> AgentState:
    """Final compilation node"""
    console.print(Panel.fit(
        "[bold blue]📊 Compilation Agent[/bold blue]\nGenerating final summary...",
        border_style="blue"
    ))
    return state


# ============================================================================
# ROUTING LOGIC
# ============================================================================

def route_after_triage(state: AgentState) -> str:
    """Route from triage to tool execution or finish"""
    if state["task_queue"]:
        return "tool_execution"
    return "finish"


def route_after_tool(state: AgentState) -> str:
    """Route from tool execution back to triage or finish"""
    if state["task_queue"]:
        return "triage"
    return "finish"


# ============================================================================
# GRAPH CONSTRUCTION
# ============================================================================

def build_graph():
    """Construct the LangGraph workflow"""
    
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("triage", triage_node)
    workflow.add_node("tool_execution", tool_execution_node)
    workflow.add_node("finish", finish_node)
    
    # Set entry point
    workflow.set_entry_point("triage")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "triage",
        route_after_triage,
        {
            "tool_execution": "tool_execution",
            "finish": "finish"
        }
    )
    
    workflow.add_conditional_edges(
        "tool_execution",
        route_after_tool,
        {
            "triage": "triage",
            "finish": "finish"
        }
    )
    
    # Finish ends the graph
    workflow.add_edge("finish", END)
    
    return workflow.compile()


# ============================================================================
# DISPLAY FUNCTIONS
# ============================================================================

def display_welcome():
    """Display welcome banner"""
    welcome_text = """
    # 🤖 Personal Task Manager Triage (LLM-Powered)
    
    **Multi-Agent System using Ollama, LangGraph & ReAct Pattern**
    
    This system uses Large Language Models to autonomously analyze requests,
    identify patterns, and select the right tools for task execution.
    
    **Features:**
    - 🧠 LLM-powered task analysis
    - 🎯 Autonomous tool selection
    - 🔄 ReAct reasoning pattern
    - 📊 Beautiful CLI interface
    """
    
    console.print(Panel(
        Markdown(welcome_text),
        border_style="bold blue",
        padding=(1, 2)
    ))


def display_execution_tree(state: AgentState):
    """Display execution flow as a tree"""
    tree = Tree("🎯 [bold]Execution Flow[/bold]")
    
    triage_branch = tree.add("🤖 LLM Triage Agent")
    triage_branch.add(f"Analyzed and identified {len(state['results'])} tasks")
    
    for key, result in state["results"].items():
        tool_name = key.rsplit("_", 1)[0]
        
        if tool_name == "drafting_tool":
            branch = tree.add("✉️  Drafting Agent (LLM)")
        elif tool_name == "reminder_tool":
            branch = tree.add("⏰ Scheduler Agent")
        else:
            branch = tree.add("🔍 Data Agent")
        
        branch.add(result)
    
    console.print(Panel(tree, title="Agent Execution Tree", border_style="green"))


def display_summary(state: AgentState):
    """Display final action summary"""
    
    # Create summary table
    table = Table(title="📊 Action Summary", border_style="blue", show_header=True)
    table.add_column("Step", style="cyan", no_wrap=True, width=6)
    table.add_column("Tool", style="magenta", width=20)
    table.add_column("Result", style="green")
    
    step = 1
    for key, result in state["results"].items():
        tool_name = key.rsplit("_", 1)[0]
        
        tool_display = {
            "drafting_tool": "✉️  Drafting Tool",
            "reminder_tool": "⏰ Reminder Tool",
            "search_tool": "🔍 Search Tool"
        }.get(tool_name, tool_name)
        
        table.add_row(str(step), tool_display, result)
        step += 1
    
    console.print(table)
    
    # Display LLM reasoning
    if state["llm_reasoning"]:
        console.print("\n[bold yellow]🧠 LLM Reasoning Process:[/bold yellow]")
        for reasoning in state["llm_reasoning"]:
            console.print(f"  💭 {reasoning}")
    
    # Display agent thoughts
    if state["agent_thoughts"]:
        console.print("\n[bold cyan]🔄 Execution Log:[/bold cyan]")
        for thought in state["agent_thoughts"]:
            console.print(f"  → {thought}")


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def check_ollama_connection():
    """Check if Ollama is running and accessible"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        response.raise_for_status()
        
        models = response.json().get("models", [])
        model_names = [m["name"] for m in models]
        
        console.print(f"[green]✓ Connected to Ollama[/green]")
        console.print(f"[dim]Available models: {', '.join(model_names) if model_names else 'None'}[/dim]")
        
        if MODEL_NAME not in model_names and f"{MODEL_NAME}:latest" not in model_names:
            console.print(f"[yellow]⚠ Model '{MODEL_NAME}' not found. Available models: {model_names}[/yellow]")
            console.print(f"[yellow]Pull it with: ollama pull {MODEL_NAME}[/yellow]")
            return False
        
        return True
        
    except requests.exceptions.ConnectionError:
        console.print("[bold red]✗ Cannot connect to Ollama[/bold red]")
        console.print("[yellow]Make sure Ollama is running:[/yellow]")
        console.print("[yellow]  1. Start Ollama: ollama serve[/yellow]")
        console.print(f"[yellow]  2. Pull model: ollama pull {MODEL_NAME}[/yellow]")
        return False
    except Exception as e:
        console.print(f"[bold red]Error checking Ollama: {e}[/bold red]")
        return False


def run_task_manager(user_request: str):
    """Execute the task manager with given request"""
    
    # Initialize state
    initial_state: AgentState = {
        "user_request": user_request,
        "task_queue": [],
        "results": {},
        "current_task": {},
        "iteration": 0,
        "agent_thoughts": [],
        "llm_reasoning": []
    }
    
    # Build and execute graph
    console.print(f"\n[bold]📝 Processing request:[/bold] {user_request}\n")
    
    graph = build_graph()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]🤖 Executing LLM-powered workflow...", total=None)
        
        final_state = cast(AgentState, graph.invoke(initial_state))
        
        progress.update(task, completed=True)
    
    # Display results
    console.print()
    display_execution_tree(final_state)
    console.print()
    display_summary(final_state)
    
    return final_state


def main():
    """Main CLI entry point"""
    display_welcome()
    
    # Check Ollama connection
    if not check_ollama_connection():
        console.print("\n[bold red]Please start Ollama before running this application.[/bold red]")
        return
    
    console.print()
    
    # Example requests
    example_requests = [
        "I need to prepare for the meeting tomorrow, remind me to check the attached files, and draft an email to the client about the new deadline. Also, search for the current stock price of Google.",
        "Remind me to call John at 3pm, draft an email about the quarterly report, and look up the weather forecast.",
        "Set a reminder to submit the proposal, search for recent AI developments, and write an email about project updates."
    ]
    
    console.print("\n[bold cyan]📋 Example Requests:[/bold cyan]")
    for i, req in enumerate(example_requests, 1):
        console.print(f"  {i}. {req[:80]}...")
    
    console.print("\n[bold green]💬 Enter your request (or press Enter for example 1):[/bold green]")
    user_input = input("> ").strip()
    
    if not user_input:
        user_input = example_requests[0]
        console.print(f"[dim]Using example: {user_input}[/dim]\n")
    
    # Run the task manager
    try:
        run_task_manager(user_input)
        console.print("\n[bold green]✓ Task processing complete![/bold green]")
        console.print("[dim]Check inbox/reminders/ and inbox/drafts/ for saved outputs.[/dim]\n")
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]")


if __name__ == "__main__":
    main()
