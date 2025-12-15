# Memory System Integration Plan - Phase 1: LangGraph Checkpointer

## Executive Summary

This plan implements Phase 1 of the memory system: integrating LangGraph's SqliteSaver checkpointer for automatic workflow state persistence. This is a minimal, incremental change that provides the foundation for future phases (ChromaDB semantic search and context-aware triage).

**Scope:** Phase 1 only - LangGraph checkpointer integration
**Effort:** ~30 lines of code across 3 files + utilities
**Risk:** Low - Native LangGraph feature with minimal changes
**Foundation:** Enables Phases 2-4 (ChromaDB, context enhancement, search)

## Current Architecture Analysis

### State Management (Ephemeral)
- **AgentState (TypedDict)**: user_request, task_queue, results, current_task, iteration, agent_thoughts, llm_reasoning
- **Lifecycle**: Single-request only - state destroyed after each invocation
- **No persistence**: Cross-session context not available

### Current Outputs
1. **ReminderTool**: Writes to `inbox/reminders/reminder_{timestamp}_{content}.txt`
2. **DraftingTool**: Writes to `inbox/drafts/draft_{timestamp}_{content}.txt` (LLM-generated)
3. **ExternalSearchTool**: Returns ephemeral strings (not persisted)

### Integration Points Identified
- AgentState extension for conversation history
- LangGraph checkpointer support (native SQLite integration)
- LLM prompt enhancement with historical context
- Tool execution logging points
- State initialization with previous context

## User Decisions

✅ **1. Memory Scope**: Phased approach (D) - All features rolled out incrementally
✅ **2. ChromaDB Scope**: High value content only - Email drafts and LLM-generated/user-generated content
✅ **3. Session Management**: Option C - No sessions (flat history, simplest)
✅ **4. Implementation**: Phased - Small incremental steps
✅ **5. Persistence**: LangGraph checkpointer (SqliteSaver) for workflow state

## Implementation Strategy

### Phased Rollout Plan

**Phase 1: LangGraph Checkpointer (Core Persistence)**
- Add LangGraph SqliteSaver for automatic workflow state persistence
- Enables crash recovery and state inspection
- Minimal code changes, maximum stability

**Phase 2: ChromaDB Semantic Search**
- Index email drafts (LLM-generated content)
- Add search functionality for draft retrieval
- Integrate with DraftingTool execution

**Phase 3: Context-Aware Triage**
- Feed relevant history to LLM triage agent
- Enhance prompts with previous task context
- Smart suggestions based on past behavior

**Phase 4: Historical Search & Reporting**
- Query interface for past requests and results
- CLI commands: "show history", "search drafts about X"
- Analytics and insights

---

## Phase 1 Implementation Plan: LangGraph Checkpointer

### Architecture Overview

```
User Request
     ↓
LangGraph Workflow with SqliteSaver
     ↓
[State automatically checkpointed at each node]
     ↓
Triage → Tool Execution → Finish
     ↓
Results displayed + State persisted to checkpoints.db
```

### What LangGraph Checkpointer Provides

1. **Automatic State Persistence**: Every node execution saves AgentState to SQLite
2. **Crash Recovery**: Resume from last checkpoint if execution fails
3. **State Inspection**: Query workflow history via `graph.get_state(thread_id)`
4. **Time Travel**: Replay or fork workflows from any checkpoint
5. **Thread-based History**: Each execution gets a unique thread_id (no session management needed)

### Benefits for This Project

- **Zero-config persistence**: Just add checkpointer to `graph.compile()`
- **Automatic logging**: All state transitions saved (user_request, task_queue, results, agent_thoughts, llm_reasoning)
- **Foundation for Phase 3**: Historical context retrieval built-in
- **Minimal code changes**: ~30 lines in main.py, 1 line in pyproject.toml, 1 line in .gitignore

## Quick Reference: Key Implementation Points

### Core Changes (3 files)

**1. main.py** (~25 lines added)
- Add imports: `sqlite3`, `SqliteSaver`, `uuid`
- New function: `get_checkpointer()` - initializes SqliteSaver with `data/checkpoints.db`
- Modify `build_graph()`: Add 3 lines to compile with checkpointer
- Modify `run_task_manager()`: Add thread_id parameter, generate UUID, pass config to invoke

**2. pyproject.toml** (1 line)
- Add dependency: `langgraph-checkpoint-sqlite>=1.0.0`

**3. .gitignore** (1 line)
- Exclude `/data` directory

### New Utilities

**utils/inspect_checkpoints.py** - Database inspection tool
- Query checkpoint database
- Display thread summaries
- Foundation for Phase 2 indexing

### Database Location
```
data/checkpoints.db  # Auto-created, git-ignored, keeps root clean
```

### Thread ID Strategy
- Auto-generated UUID v4 per execution
- Displayed at end: "Session ID: abc123..."
- Optional parameter for future continuation support
- No session management (flat history)

---

## Implementation Status

### Completed
- ✅ Added `langgraph-checkpoint-sqlite>=1.0.0` to pyproject.toml
- ✅ Added imports: `sqlite3`, `SqliteSaver`, `uuid` to main.py
- ✅ Created `get_checkpointer()` function in main.py
- ✅ Modified `build_graph()` to use checkpointer
- ✅ Modified `run_task_manager()` with thread_id support
- ✅ Updated `.gitignore` to exclude `/data` directory
- ✅ Created `utils/inspect_checkpoints.py` utility

### In Progress
- 🔄 Testing checkpointer integration
- 🔄 Verifying database creation and state persistence

### Next Steps
1. Complete test run to verify:
   - `data/checkpoints.db` is created
   - Checkpoints are created at each node
   - State persists and can be queried
   - Thread IDs are displayed correctly
2. Document findings in completion report
3. Create entry in artifacts/completed/issues/ when verified

## Critical Files Modified

1. `/home/amite/code/python/personal-triage-agent/main.py`
   - Lines 9-10: Added imports
   - Line 18: Added SqliteSaver import
   - Lines 167-185: Added get_checkpointer() function
   - Lines 226-230: Modified build_graph() for checkpointer
   - Lines 369-429: Modified run_task_manager() with thread_id support

2. `/home/amite/code/python/personal-triage-agent/pyproject.toml`
   - Line 9: Added langgraph-checkpoint-sqlite dependency

3. `/home/amite/code/python/personal-triage-agent/.gitignore`
   - Lines 13-14: Added /data directory exclusion

4. `/home/amite/code/python/personal-triage-agent/utils/inspect_checkpoints.py`
   - New file created for database inspection

## Testing Plan

### Test 1: Database Creation
```bash
uv run main.py  # Run with example request
ls -la data/checkpoints.db  # Verify file exists
```

### Test 2: Checkpoint Inspection
```bash
python -m utils.inspect_checkpoints  # View database contents
```

### Test 3: State Retrieval
```python
# Verify state can be retrieved with thread_id
from main import build_graph
graph = build_graph()
config = {"configurable": {"thread_id": "known-thread-id"}}
state = graph.get_state(config)
```

## Phase 1 Success Criteria

- ✓ Application runs without errors after modifications
- ✓ `data/checkpoints.db` is created automatically
- ✓ Checkpoints are created after each node execution
- ✓ Thread IDs are generated and displayed
- ✓ State can be retrieved using `graph.get_state()`
- ✓ History can be retrieved using `graph.get_state_history()`
- ✓ Database inspection utility works
- ✓ No performance degradation
- ✓ Foundation ready for Phase 2 (ChromaDB integration)

## Notes for Future Phases

### Phase 2 Integration Points
- ChromaDB will index email drafts using SqliteSaver state history
- CheckpointSaver provides structured state access for embeddings
- Schema: Store thread_id + checkpoint_id + content in ChromaDB

### Phase 3 Integration Points
- Context-aware triage will query checkpointer history
- LLM prompts will be enhanced with similar past executions
- Checkpointer provides full access to previous request/result pairs

### API Surface for Future Use
```python
# Get all thread IDs
threads = utils.inspect_checkpoints.get_all_thread_ids()

# Get thread history
history = graph.get_state_history({"configurable": {"thread_id": thread_id}})

# Query specific checkpoint
state = graph.get_state({
    "configurable": {
        "thread_id": thread_id,
        "checkpoint_id": checkpoint_id
    }
})
```
