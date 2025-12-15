# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**Personal Task Manager Triage** is a multi-agent LLM-powered CLI application built with LangGraph that autonomously analyzes complex user requests, breaks them into discrete tasks, and routes them to specialized agents for execution.

### Core Architecture

The system follows the **ReAct (Reasoning + Acting) pattern** with these key layers:

1. **LLM Providers** - Pluggable abstraction supporting multiple LLM backends
   - Ollama (default, local)
   - GPT-5-Mini (OpenAI)

2. **Triage Agent** - Dispatcher that analyzes user requests and identifies tasks using LLM reasoning
   - Uses Pydantic for structured JSON validation
   - Returns list of tasks with assigned tools and content

3. **Worker Agents & Tools** - Specialized handlers for specific task types
   - Scheduler Agent + ReminderTool
   - Drafting Agent (LLM-powered) + DraftingTool
   - Data Agent + ExternalSearchTool

4. **LangGraph Workflow** - Stateful orchestration of agent execution
   - Entry: Triage Node (task analysis)
   - Loop: Tool Execution Node (task processing)
   - Exit: Finish Node (result compilation)

### Data Flow

```
User Request
    ↓
Triage Agent (LLMTriageAgent.parse_request_with_llm)
    ↓ [Pydantic validates JSON → TaskResponse]
Task Queue (List[Dict[str, str]])
    ↓
LangGraph Workflow Loop:
    - Tool Execution Node (execute first task)
    - Route Decision (more tasks? → loop or finish)
    ↓
Finish Node (compile results)
    ↓
Results Display (CLI output via Rich)
```

---

## Key Recent Changes: JSON Parsing Refactoring

**Context**: The original `LLMTriageAgent.parse_request_with_llm()` had 150+ lines of complex JSON extraction logic (3 strategies + repair function). This was refactored to use Pydantic structured output validation.

### What Changed
- **File**: `agents/llm_triage_agent.py`
- **Code Reduction**: 367 → 250 lines (-32%), JSON parsing: 150 → 35 lines (-77%)
- **Key Changes**:
  - Replaced `TypedDict` with Pydantic `BaseModel` (TaskItem, TaskResponse)
  - Simplified `parse_request_with_llm()` from ~120 to ~20 lines
  - Removed `_attempt_json_repair()` method (35 lines of regex repairs)
  - Added lightweight `_fallback_extract_json()` method
- **Testing**: Verified with GPT-5-Mini—Pydantic validation succeeds consistently, fallback never triggered
- **Related Files**: `docs/JSON_PARSING_REFACTORING.md`, `CHANGES.md`, `TEST_RESULTS.md`

### Important Notes
- Pydantic validation is direct and automatic—cleaner than manual JSON extraction
- Fallback methods remain for robustness but are rarely needed
- All model validation rules are defined in TaskItem and TaskResponse models

---

## Development Workflow

### Setup & Installation

```bash
# Using uv (recommended)
uv sync

# Using pip
pip install -e .
```

### Running the Application

```bash
# Default (uses Ollama)
uv run main.py

# Using GPT-5-Mini (set env vars first)
export LLM_PROVIDER=gpt
export OPENAI_API_KEY=your-api-key
uv run main.py
```

### Configuring LLM Provider

**Ollama (Default)**:
- No configuration needed
- Requires `ollama serve` running locally
- Check connection: `curl http://localhost:11434/api/tags`

**GPT Provider**:
- Set environment variables:
  ```bash
  LLM_PROVIDER=gpt
  OPENAI_API_KEY=your-key
  ```
- Alternatively, programmatically:
  ```python
  from agents.llm_factory import LLMFactory
  client = LLMFactory.create_llm_client("gpt", api_key="key")
  ```

### Testing

The system is best tested interactively with `uv run main.py`:

```bash
# Run with example request (press Enter for default)
uv run main.py
> [press Enter to use example 1, or enter 1-3 to select]

# Run with custom request
uv run main.py
> I need to remind me to call John, draft an email, and search for weather
```

**To verify Pydantic parsing works**: Check logs for `INFO:agents.llm_triage_agent:Successfully parsed X tasks` (no warnings about fallback extraction).

---

## Architecture Details

### State Management (LangGraph AgentState)

```python
class AgentState(TypedDict):
    user_request: str                # Original user input
    task_queue: List[Dict[str, str]] # Tasks: [{"tool": "...", "content": "..."}]
    results: Dict[str, str]          # Tool execution results
    current_task: Dict[str, str]     # Current task being processed
    iteration: int                   # Loop counter
    agent_thoughts: List[str]        # Execution log
    llm_reasoning: List[str]         # LLM reasoning traces
```

### LLM Provider Architecture (Strategy Pattern)

```
LLMClientBase (abstract)
  ├── OllamaClient (local model)
  ├── GPTClient (OpenAI API)

LLMFactory (factory)
  └── get_llm_client_from_env() → LLMClientBase
```

Each client implements `generate(prompt: str, temperature: float) -> str`. The factory handles environment-based client selection.

### Triage Agent (Task Parsing)

```
Input: user_request (str)
  ↓
Pydantic Validation:
  1. TaskResponse.model_validate_json(llm_response)
  2. Returns: (List[Task], reasoning: str)

Fallbacks (if Pydantic fails):
  1. _fallback_extract_json() → brace matching + Pydantic re-validation
  2. _fallback_parse() → rule-based pattern matching
```

**Key Models** (in `agents/llm_triage_agent.py`):
- `TaskItem`: Individual task with tool and content
- `TaskResponse`: Complete response with tasks list and reasoning
- Tool Registry: Maps tool names to tool classes (ReminderTool, DraftingTool, ExternalSearchTool)

### LangGraph Workflow (main.py)

Nodes:
- **triage_node**: Parses request, populates task_queue, displays reasoning
- **tool_execution_node**: Executes current task, updates results, removes from queue
- **finish_node**: Compiles final results for display

Conditional Edges:
- **route_after_triage**: Has tasks? → tool_execution : finish
- **route_after_tool**: More tasks? → triage : finish

---

## Important Patterns & Conventions

### Tool Execution

All tools inherit from a base interface and implement `execute(content: str) -> str`:

```python
class MyTool:
    description = "What this tool does"
    @staticmethod
    def execute(content: str) -> str:
        return "result"
```

Tools are registered in `LLMTriageAgent.AVAILABLE_TOOLS` dict.

### LLM Response Format

The triage agent expects LLM to return JSON:

```json
{
  "tasks": [
    {"tool": "reminder_tool", "content": "..."},
    {"tool": "drafting_tool", "content": "..."}
  ],
  "reasoning": "Why these tasks were identified"
}
```

Pydantic validates this structure automatically. The prompt in `parse_request_with_llm()` shows the expected format.

### Agent-to-LLM Interface

- **LLMTriageAgent**: Uses `LLMClientBase.generate()` to get JSON-formatted task list
- **LLMDraftingAgent**: Uses same interface for email drafting
- Both handle Pydantic validation and fallback parsing

---

## File Structure

```
agents/
  llm_triage_agent.py      # Main triage dispatcher, task parsing (Pydantic models)
  llm_drafting_agent.py    # LLM-powered email drafting
  llm_client_base.py       # Abstract base for LLM clients
  llm_factory.py           # Factory for creating LLM clients
  ollama_client.py         # Ollama implementation
  gpt_client.py            # GPT-5-Mini implementation

tools/
  reminder_tool.py         # Saves reminders to file
  drafting_tool.py         # Saves drafts to file
  external_search_tool.py  # Simulates data lookup

main.py                    # LangGraph workflow, CLI interface
pyproject.toml            # Project config, dependencies

docs/
  LLM_PROVIDER_SETUP.md    # Guide for configuring Ollama/GPT
  JSON_PARSING_REFACTORING.md  # Details on Pydantic refactoring
  REFACTORING_COMPARISON.md    # Before/after code comparison
  build_graph_explanation.md   # LangGraph workflow details
```

---

## Common Development Tasks

### Adding a New Tool

1. Create tool class in `tools/new_tool.py`:
   ```python
   class NewTool:
       description = "What this tool does"
       @staticmethod
       def execute(content: str) -> str:
           return "result"
   ```

2. Register in `agents/llm_triage_agent.py` AVAILABLE_TOOLS dict:
   ```python
   AVAILABLE_TOOLS = {
       "new_tool": NewTool,
       ...
   }
   ```

3. Prompt instructions in `parse_request_with_llm()` will automatically include it.

### Debugging LLM Responses

```python
# In agents/llm_triage_agent.py, the parse_request_with_llm method logs:
logger.info(f"LLM response: {response[:200]}...")  # Raw response
logger.info(f"Successfully parsed {len(tasks)} tasks")  # On success

# Check logs for:
# - Pydantic parsing success: "Successfully parsed X tasks"
# - Fallback extraction: "Extracted X tasks from malformed JSON"
# - Rule-based fallback: "Fallback parser generated X tasks"
```

### Testing LLM Provider Switching

```python
# In Python:
from agents.llm_factory import LLMFactory

# Use Ollama
ollama = LLMFactory.create_llm_client("ollama")
response = ollama.generate("test prompt")

# Use GPT
gpt = LLMFactory.create_llm_client("gpt", api_key="key")
response = gpt.generate("test prompt")
```

### Modifying Prompt Instructions

The triage prompt is in `LLMTriageAgent.parse_request_with_llm()`. Key sections:
1. Task analysis description
2. Tool descriptions (auto-generated from AVAILABLE_TOOLS)
3. Expected JSON format example
4. Temperature setting (currently 0.3 for consistency)

---

## Key Dependencies

- **langgraph**: Workflow orchestration and state management
- **pydantic**: Structured output validation (recent addition for JSON parsing)
- **rich**: Beautiful CLI output with panels, tables, trees
- **python-dotenv**: Environment variable management
- **requests**: HTTP calls (Ollama API, external data)
- **ollama**: Ollama client library (optional if using Ollama)
- **openai**: OpenAI API client (required for GPT provider)

---

## Documentation References

- **[CHANGES.md](CHANGES.md)** - Detailed JSON parsing refactoring breakdown
- **[TEST_RESULTS.md](TEST_RESULTS.md)** - Test execution results with GPT-5-Mini
- **[VERIFICATION_COMPLETE.md](VERIFICATION_COMPLETE.md)** - Production readiness verification
- **[docs/JSON_PARSING_REFACTORING.md](docs/JSON_PARSING_REFACTORING.md)** - Technical implementation details
- **[docs/LLM_PROVIDER_SETUP.md](docs/LLM_PROVIDER_SETUP.md)** - Provider configuration guide
- **[docs/build_graph_explanation.md](docs/build_graph_explanation.md)** - LangGraph workflow detailed explanation

---

## Known Gotchas & Important Notes

1. **Pydantic JSON Validation**: The `TaskResponse.model_validate_json()` expects valid JSON. GPT-5-Mini consistently produces well-formed JSON, but older models might need fallback extraction.

2. **Tool Execution**: The `tool_execution_node` in main.py has special handling for `drafting_tool` (uses LLMDraftingAgent) vs other tools (uses static execute method).

3. **Temperature Setting**: Currently set to 0.3 in both triage and drafting agents for consistency. Adjust if LLM responses become too repetitive or too creative.

4. **Ollama Model**: Check `agents/ollama_client.py` for MODEL_NAME constant—must match an installed Ollama model.

5. **Task Queue Format**: Tasks are stored as `List[Dict[str, str]]` with keys "tool" and "content". The tool name must exist in AVAILABLE_TOOLS.

---

## Testing & Verification

The refactored Pydantic parser has been verified with:
- Complex multi-task requests (4+ tasks)
- Multi-tool requests (reminder + drafting + search)
- Both Ollama and GPT-5-Mini providers

All tests show direct Pydantic validation succeeding without fallback, confirming the refactoring is production-ready.

---

## Project Organization & Documentation

This project uses a structured approach to organizing materials, work tracking, and documentation:

### docs/ - Learning Materials & Architecture

The `docs/` directory contains educational materials and technical guides:
- **Architecture & Design**: `build_graph_explanation.md` (LangGraph workflow details)
- **Setup Guides**: `LLM_PROVIDER_SETUP.md` (Ollama/GPT configuration)
- **Technical References**: How-to guides, integration docs, best practices

**Add here**: Materials that explain how the system works, setup instructions, and learning references.

### artifacts/completed/issues/ - Completed Work Documentation

The `artifacts/completed/issues/` directory stores finalized documentation for closed issues:
- **Issue Resolution Reports**: Problem → Solution → Results
- **Implementation Docs**: Changes made, rationale, metrics
- **Test Results**: Verification & validation evidence
- **Examples**: `JSON_PARSING_REFACTORING.md`, `TEST_RESULTS.md`, `CHANGES.md`

**Add here**: When an issue is resolved, move final documentation here with test results and verification.

**Naming**: Use descriptive filenames like `FEATURE_NAME_*.md` or `ISSUE_TYPE_*.md`.

### artifacts/wip/issues/ - Work In Progress Tracking

The `artifacts/wip/issues/` directory tracks active work with one folder per issue:
```
artifacts/wip/issues/ISSUE_ID/
  ├── status.md        # Current status, blockers, next steps
  ├── analysis.md      # Investigation notes & root cause
  └── progress.md      # Daily/hourly work progress tracking
```

**Add here**: When starting work on an issue, create a folder with these three tracking files.

**Update**: Keep status.md and progress.md current as work progresses.

**Move**: When issue is complete, move finalized docs to artifacts/completed/issues/.

### artifacts/wip/plans/ - Project Planning

The `artifacts/wip/plans/` directory contains phase plans and roadmaps:
- **Phase Plans**: `phase-1.md`, `phase-2.md` - Objectives, work items, success criteria
- **Roadmap**: `roadmap.md` - Overall timeline and feature priorities
- **Quarterly Plans**: Sprint or quarterly planning documents

**Add here**: Create phase plans before starting major work, update as project progresses.

### Workflow Summary

1. **Plan** → Create/update files in `artifacts/wip/plans/`
2. **Start Work** → Create folder in `artifacts/wip/issues/ISSUE_ID/` with tracking files
3. **Track Progress** → Update `status.md` and `progress.md` regularly
4. **Complete** → Finalize documentation and move to `artifacts/completed/issues/`
5. **Share Learning** → Add architecture insights to `docs/` if relevant

### Best Practices

✅ **DO**:
- Use descriptive filenames indicating issue/feature clearly
- Link between related documents with markdown links
- Keep work-in-progress files updated daily
- Document decisions and rationale, not just what was done
- Include metrics (lines changed, test results, performance impact)
- Archive completed work to keep wip/ focused on current activities
- Keep project root clean (no clutter)

❌ **DON'T**:
- Mix issue tracking and planning documents
- Leave stale status files in wip/
- Skip implementation details that future maintainers need
- Duplicate content across docs (link instead)
- Ignore formatting and consistency
- Leave incomplete documentation in wip/
- **Clutter project root with scripts, docs, or generated files**

### Keeping Project Root Clean

The project root should contain only essential files for development and documentation:

**✅ Essential files in root**:
- `main.py` - Application entry point
- `pyproject.toml` - Project configuration
- `README.md` - Project overview
- `CLAUDE.md` - Claude Code guidance (this file)
- `.env.example` - Environment template
- `.gitignore` - Git configuration
- Standard files: `LICENSE`, `setup.py` (if needed)

**📁 Proper locations for everything else**:
- **Documentation**: `docs/` directory
  - Architecture guides: `docs/build_graph_explanation.md`
  - Setup guides: `docs/LLM_PROVIDER_SETUP.md`

- **Completed issue docs**: `artifacts/completed/issues/` directory
  - Implementation details: `artifacts/completed/issues/JSON_PARSING_REFACTORING.md`
  - Test results: `artifacts/completed/issues/TEST_RESULTS.md`

- **Work in progress**: `artifacts/wip/issues/` directory
  - Per-issue tracking: `artifacts/wip/issues/ISSUE_ID/status.md`

- **Plans & phases**: `artifacts/wip/plans/` directory
  - Phase plans: `artifacts/wip/plans/phase-1.md`
  - Roadmap: `artifacts/wip/plans/roadmap.md`

- **Source code**: `agents/`, `tools/` directories
  - Agent implementations, tool definitions, LLM clients

- **Temporary files**: `.gitignore` them (no root clutter)
  - Generated files, caches, temporary outputs

**Rule**: If a file would clutter the root and doesn't need to be there, it belongs in a subdirectory.
