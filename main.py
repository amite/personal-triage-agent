"""
Personal Task Manager Triage - A Multi-Agent Task Management System
Built with LangGraph using LLMs (Ollama/GPT) and the ReAct agent pattern
"""

import json
import re
import os
import sqlite3
import uuid
from typing import TypedDict, List, Dict, Annotated, Literal, Optional, cast
from dataclasses import dataclass
from datetime import datetime
import requests
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from rich.tree import Tree
from rich import print as rprint

# Load environment variables
load_dotenv()

# Initialize Rich console
console = Console()

# Import agents and tools
from agents.llm_triage_agent import LLMTriageAgent, AVAILABLE_TOOLS
from agents.llm_drafting_agent import LLMDraftingAgent
from agents.ollama_client import OllamaClient, OLLAMA_BASE_URL, MODEL_NAME
from tools.reminder_tool import ReminderTool
from tools.drafting_tool import DraftingTool
from tools.external_search_tool import ExternalSearchTool

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
# CHECKPOINTER INITIALIZATION
# ============================================================================

def get_checkpointer() -> SqliteSaver:
    """
    Initialize and return a SqliteSaver checkpointer.

    The database file is stored in the data/ directory to keep the root clean.
    This provides automatic state persistence for all graph executions.

    Returns:
        SqliteSaver: Configured checkpointer instance
    """
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    # Connect to SQLite database
    db_path = "data/checkpoints.db"
    conn = sqlite3.connect(db_path, check_same_thread=False)

    # Create and return checkpointer
    return SqliteSaver(conn)

# ============================================================================
# GRAPH CONSTRUCTION
# ============================================================================

def build_graph():
    """Construct the LangGraph workflow with automatic state persistence"""

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

    # Initialize checkpointer for state persistence
    checkpointer = get_checkpointer()

    # Compile with checkpointer enabled
    return workflow.compile(checkpointer=checkpointer)

# ============================================================================
# DISPLAY FUNCTIONS
# ============================================================================

def display_welcome():
    """Display welcome banner"""
    welcome_text = """
    # 🤖 Personal Task Manager Triage (LLM-Powered)

    **Multi-Agent System using LLMs (Ollama/GPT), LangGraph & ReAct Pattern**

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

def check_llm_connection():
    """Check if the configured LLM provider is available"""
    provider = os.environ.get("LLM_PROVIDER", "ollama").lower()
    
    if provider == "ollama":
        return check_ollama_connection()
    elif provider == "gpt":
        # For GPT, just check if API key is available
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key and api_key.strip():
            console.print(f"[green]✓ GPT client configured with API key[/green]")
            return True
        else:
            console.print("[bold red]✗ OpenAI API key not configured[/bold red]")
            console.print("[yellow]Set OPENAI_API_KEY in your .env file[/yellow]")
            return False
    else:
        console.print(f"[bold red]✗ Unknown LLM provider: {provider}[/bold red]")
        return False

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

def run_task_manager(user_request: str, thread_id: Optional[str] = None) -> AgentState:
    """
    Execute the task manager with given request

    Args:
        user_request: The user's task request
        thread_id: Optional thread ID for persistence. If None, generates a new one.
                  Use existing ID to continue a previous conversation.

    Returns:
        Final agent state after execution
    """

    # Generate or use provided thread ID
    if thread_id is None:
        thread_id = str(uuid.uuid4())
        console.print(f"[dim]Starting new session: {thread_id[:8]}...[/dim]")
    else:
        console.print(f"[dim]Continuing session: {thread_id[:8]}...[/dim]")

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

    # Configuration with thread ID for persistence
    config = {"configurable": {"thread_id": thread_id}}

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]🤖 Executing LLM-powered workflow...", total=None)

        # Invoke with config containing thread_id
        final_state = cast(AgentState, graph.invoke(initial_state, config=config))

        progress.update(task, completed=True)

    # Display results
    console.print()
    display_execution_tree(final_state)
    console.print()
    display_summary(final_state)

    # Display thread ID for future reference
    console.print(f"\n[dim]Session ID: {thread_id}[/dim]")

    return final_state

def main():
    """Main CLI entry point"""
    display_welcome()

    # Check LLM connection based on configured provider
    if not check_llm_connection():
        provider = os.environ.get("LLM_PROVIDER", "ollama").lower()
        if provider == "ollama":
            console.print("\n[bold red]Please start Ollama before running this application.[/bold red]")
        elif provider == "gpt":
            console.print("\n[bold red]Please configure OpenAI API key before running this application.[/bold red]")
        else:
            console.print(f"\n[bold red]Please configure {provider} before running this application.[/bold red]")
        return

    console.print()

    # Example requests
    example_requests = [
        "I need to prepare for the meeting tomorrow, remind me to check the attached files, and draft an email to the client about the new deadline. Also, search for the current stock price of Google.",
        "Remind me to call John at 3pm, draft an email about the quarterly report, and look up the weather forecast.",
        "Set a reminder to submit the proposal, search for recent AI developments, and write an email about project updates.",
        "I have a presentation next Friday. Remind me to review the slides two days before, draft a follow-up email to attendees, and search for the latest market trends in our industry.",
        "Help me organize my week: set a reminder to complete the budget review, draft an email requesting budget approval from finance, and look up competitor pricing updates.",
        "I'm switching projects next month. Remind me to archive old files, draft a transition email to the team, and search for best practices in project handoffs.",
        "Conference preparation: remind me to book hotel accommodation, draft an email to the conference organizers with my attendance confirmation, and search for the event schedule and keynote speakers.",
        "End of quarter tasks: set a reminder for quarterly performance reviews, draft an email summarizing team achievements, and search for Q4 industry benchmarks.",
        "Client onboarding: remind me to send the welcome package, draft an introductory email outlining our service roadmap, and search for similar case studies to share.",
        "Research sprint: remind me to consolidate findings, draft an email with research methodology summary, and search for recent publications on natural language processing.",
        "Team communication: set a reminder to conduct one-on-ones with three team members, draft an announcement about new remote work policy, and search for employee engagement best practices.",
        "Personal development: remind me to register for the online course, draft an email to my manager about skill development goals, and search for Python machine learning certifications.",
        "Vendor management: remind me to review contracts with current vendors, draft an email requesting quote updates, and search for new tools in project management software."
    ]

    console.print("\n[bold cyan]📋 Example Requests:[/bold cyan]")
    for i, req in enumerate(example_requests, 1):
        console.print(f"  {i}. {req[:80]}...")

    console.print("\n[bold green]💬 Enter your request (or press Enter for example 1, or enter 1-3 to select an example):[/bold green]")
    user_input = input("> ").strip()

    if not user_input:
        user_input = example_requests[0]
        console.print(f"[dim]Using example: {user_input}[/dim]\n")
    elif user_input.isdigit():
        example_index = int(user_input) - 1
        if 0 <= example_index < len(example_requests):
            selected_example = example_requests[example_index]
            console.print(f"[dim]Using example {user_input}: {selected_example}[/dim]\n")
            user_input = selected_example

    # Run the task manager
    try:
        run_task_manager(user_input)
        console.print("\n[bold green]✓ Task processing complete![/bold green]")
        console.print("[dim]Check inbox/reminders/ and inbox/drafts/ for saved outputs.[/dim]\n")
    except Exception as e:
        console.print(f"\n[bold red]Error: {e}[/bold red]")

if __name__ == "__main__":
    main()
