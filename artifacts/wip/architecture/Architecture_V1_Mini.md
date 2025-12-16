# Personal Task Manager Triage - Architecture Mini

**Version:** 1.0 (Mini)
**Date:** 2025-12-16
**Purpose:** Minimal context for chat agents

---

## System Overview

Multi-agent LLM-powered CLI that analyzes user requests, breaks them into tasks, and routes to specialized agents.

**Tech Stack:**
- LangGraph (workflow), Pydantic (validation), Ollama/GPT (LLMs), Rich (CLI), SQLite (state)

**Key Pattern:** ReAct (Reasoning + Acting)

---

## LangGraph Nodes

**3 Main Nodes** (`main.py`):

1. **`triage_node`** (lines 59-94)
   - Uses `LLMTriageAgent.parse_request_with_llm()`
   - Populates `task_queue` and `llm_reasoning`
   - Registered as `"triage"`

2. **`tool_execution_node`** (lines 96-138)
   - Pops task from queue, executes tool, stores result
   - Registered as `"tool_execution"`

3. **`finish_node`** (lines 140-146)
   - Final compilation
   - Registered as `"finish"`

**Graph Flow:**
```
START → triage → [has tasks?] → tool_execution → [more tasks?] → finish → END
```

---

## Data Flow

```
User Input → Triage Node (LLM analysis) → Task Queue → Tool Execution Loop → Finish → Output
```

**State Transitions:**
- **Initial**: `task_queue=[], results={}`
- **After Triage**: `task_queue=[{"tool": "X", "content": "Y"}, ...]`
- **After Tools**: `results={"tool_name_iteration": "result"}`
- **Final**: `task_queue=[], results={...}`

---

## AgentState Schema

```python
class AgentState(TypedDict):
    user_request: str
    task_queue: List[Dict[str, str]]  # [{"tool": "X", "content": "Y"}]
    results: Dict[str, str]           # {"tool_name_iteration": "result"}
    current_task: Dict[str, str]
    iteration: int
    agent_thoughts: List[str]
    llm_reasoning: List[str]
```

---

## Components

### Triage Agent (`agents/llm_triage_agent.py`)

**Method:** `parse_request_with_llm(request: str) -> (tasks, reasoning)`

**Parsing Strategy (3 levels):**
1. Pydantic validation (`TaskResponse.model_validate_json()`)
2. JSON extraction via brace matching
3. Rule-based regex (keywords: "remind", "draft", "search")

**Pydantic Models:**
```python
class TaskItem(BaseModel):
    tool: str      # "reminder_tool", "drafting_tool", "search_tool"
    content: str

class TaskResponse(BaseModel):
    tasks: List[TaskItem]
    reasoning: str
```

**Caching:** `@lru_cache(maxsize=100)`

### Tools

- **ReminderTool** (`tools/reminder_tool.py`): Creates `inbox/reminders/reminder_TIMESTAMP_*.txt`
- **DraftingTool** (`tools/drafting_tool.py`) + **LLMDraftingAgent** (`agents/llm_drafting_agent.py`): Generates email via LLM, saves to `inbox/drafts/draft_TIMESTAMP_*.txt`
- **ExternalSearchTool** (`tools/external_search_tool.py`): Mock search (placeholder)

### LLM Integration

**Provider Abstraction:**
- `LLMClientBase` (ABC) → `OllamaClient`, `GPTClient`
- `LLMFactory.get_llm_client_from_env()` reads `LLM_PROVIDER` env var

**Temperature:**
- Triage: 0.3 (consistency)
- Drafting: 0.7 (creativity)

**Flow:**
```
Agent → LLMFactory → LLMClientBase.generate() → [Ollama: localhost:11434 | GPT: OpenAI API] → Response → Pydantic validation
```

---

## State Persistence

- **LangGraph Checkpointer**: `SqliteSaver` → `data/checkpoints.db`
- **Thread ID**: Tracks sessions, enables resumption
- **Output Files**: `inbox/reminders/`, `inbox/drafts/`

---

## Design Patterns

1. **Strategy**: LLM providers (Ollama/GPT interchangeable)
2. **Factory**: `LLMFactory` creates clients
3. **ReAct**: Reasoning (triage) → Acting (tools)
4. **State Machine**: LangGraph workflow
5. **Repository**: Tool registry (`AVAILABLE_TOOLS` dict)

---

## Key File Locations

- **Main**: `main.py` (CLI, LangGraph workflow)
- **Agents**: `agents/llm_triage_agent.py`, `agents/llm_drafting_agent.py`
- **LLM**: `agents/llm_factory.py`, `agents/ollama_client.py`, `agents/gpt_client.py`
- **Tools**: `tools/reminder_tool.py`, `tools/drafting_tool.py`, `tools/external_search_tool.py`
- **State**: `data/checkpoints.db`
- **Output**: `inbox/reminders/`, `inbox/drafts/`

---

## Error Handling

**LLM Parsing (3-level fallback):**
1. Pydantic validation
2. JSON extraction (brace matching)
3. Rule-based regex

**LLM Connection:** Checked on startup, falls back to rule-based parsing on failure

---

## Extension Points

**Add Tool:**
1. Create class in `tools/`
2. Register in `AVAILABLE_TOOLS` (`agents/llm_triage_agent.py`)
3. Add execution logic in `tool_execution_node` if needed

**Add LLM Provider:**
1. Implement `LLMClientBase` in `agents/`
2. Update `LLMFactory.create_llm_client()`
3. Set `LLM_PROVIDER` env var

**Add State Field:**
1. Update `AgentState` TypedDict
2. Checkpointer auto-persists (no code changes)

---

### Layer Responsibilities

| Layer | Component | Responsibility |
|-------|-----------|---------------|
| **1. CLI Interface** | `main.py` | User interaction, input/output, display formatting |
| **2. Workflow Engine** | LangGraph StateGraph | State management, node execution, routing logic |
| **3. Agent Orchestration** | Triage/Worker Agents | Task analysis, tool selection, task execution |
| **4. LLM Abstraction** | Factory + Clients | Unified LLM interface, provider switching |
| **5. Persistence** | SqliteSaver + Files | State checkpointing, output storage |

**Last Updated:** 2025-12-16

