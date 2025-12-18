---
name: langgraph
description: "LangGraph low-level agent orchestration. Build stateful, durable agents with graphs, persistence, streaming, and human-in-the-loop."
---

# LangGraph Development

> **Source:** https://github.com/langchain-ai/docs (src/oss/langgraph/)

LangGraph is the low-level orchestration framework for building stateful, long-running agents. It models workflows as graphs with nodes (functions) and edges (transitions). Use LangGraph when you need fine-grained control over agent behavior; use LangChain's `create_agent` for simpler use cases.

## Core Concepts

- **State**: Shared data structure representing the current snapshot
- **Nodes**: Functions that process state and return updates
- **Edges**: Determine which node runs next (conditional or fixed)

> "Nodes do the work, edges tell what to do next."

## Quick Start

```python
from langgraph.graph import StateGraph, MessagesState, START, END

def call_model(state: MessagesState):
    # Your LLM logic here
    return {"messages": [{"role": "ai", "content": "Hello!"}]}

graph = StateGraph(MessagesState)
graph.add_node("model", call_model)
graph.add_edge(START, "model")
graph.add_edge("model", END)

app = graph.compile()
result = app.invoke({"messages": [{"role": "user", "content": "Hi!"}]})
```

## State Definition

### Using TypedDict (Recommended)

```python
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph
from operator import add

class State(TypedDict):
    messages: Annotated[list, add]  # Reducer: append to list
    count: int                       # Overwrite on update

graph = StateGraph(State)
```

### Using MessagesState (Convenience)

```python
from langgraph.graph import StateGraph, MessagesState

# MessagesState has a pre-defined "messages" key with append reducer
graph = StateGraph(MessagesState)
```

## Adding Nodes

```python
def node_a(state: State) -> dict:
    """Nodes receive state and return updates."""
    return {"count": state["count"] + 1}

def node_b(state: State) -> dict:
    return {"messages": [{"role": "ai", "content": f"Count is {state['count']}"}]}

graph.add_node("a", node_a)
graph.add_node("b", node_b)
```

## Adding Edges

### Fixed Edges

```python
from langgraph.graph import START, END

graph.add_edge(START, "a")
graph.add_edge("a", "b")
graph.add_edge("b", END)
```

### Conditional Edges

```python
def router(state: State) -> str:
    """Return the name of the next node."""
    if state["count"] > 5:
        return "end_node"
    return "continue_node"

graph.add_conditional_edges(
    "a",
    router,
    {"end_node": END, "continue_node": "b"}
)
```

## Persistence (Checkpointing)

Enable durable execution with checkpointers:

```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
app = graph.compile(checkpointer=checkpointer)

# Each thread_id maintains separate state
config = {"configurable": {"thread_id": "user-123"}}
result = app.invoke({"messages": [...]}, config)

# Resume from checkpoint
result = app.invoke({"messages": [...]}, config)
```

### Production Checkpointers

```python
# PostgreSQL
from langgraph.checkpoint.postgres import PostgresSaver
checkpointer = PostgresSaver.from_conn_string("postgresql://...")

# SQLite
from langgraph.checkpoint.sqlite import SqliteSaver
checkpointer = SqliteSaver.from_conn_string("sqlite:///checkpoints.db")
```

## Streaming

```python
app = graph.compile()

# Stream node outputs
for chunk in app.stream({"messages": [...]}):
    print(chunk)

# Stream specific events
for event in app.stream({"messages": [...]}, stream_mode="updates"):
    print(event)

# Stream tokens from LLM
for event in app.stream({"messages": [...]}, stream_mode="messages"):
    print(event)
```

## Human-in-the-Loop

### Interrupts

```python
app = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=["sensitive_node"],  # Pause before this node
)

config = {"configurable": {"thread_id": "123"}}

# Run until interrupt
result = app.invoke({"messages": [...]}, config)

# Review state, then continue
result = app.invoke(None, config)  # Resume from checkpoint
```

### Dynamic Breakpoints

```python
from langgraph.errors import NodeInterrupt

def my_node(state: State):
    if needs_approval(state):
        raise NodeInterrupt("Approval required")
    return {"result": "processed"}
```

## Subgraphs

Compose complex workflows from smaller graphs:

```python
# Define inner graph
inner_graph = StateGraph(State)
inner_graph.add_node("inner_node", inner_fn)
inner_app = inner_graph.compile()

# Use as node in outer graph
outer_graph = StateGraph(State)
outer_graph.add_node("subgraph", inner_app)
outer_graph.add_edge(START, "subgraph")
```

## ReAct Agent Pattern

```python
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode

def call_model(state: MessagesState):
    response = model.invoke(state["messages"])
    return {"messages": [response]}

def should_continue(state: MessagesState) -> str:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END

graph = StateGraph(MessagesState)
graph.add_node("model", call_model)
graph.add_node("tools", ToolNode(tools))

graph.add_edge(START, "model")
graph.add_conditional_edges("model", should_continue, {"tools": "tools", END: END})
graph.add_edge("tools", "model")

app = graph.compile()
```

## Best Practices

1. **Use TypedDict for state** - Clear typing, good performance
2. **Define reducers explicitly** - Control how state updates are merged
3. **Use checkpointers in production** - Enable durability and recovery
4. **Keep nodes focused** - Single responsibility, easier testing
5. **Use conditional edges for branching** - Clean separation of routing logic
6. **Stream for long operations** - Better UX, visible progress

## When to Use LangGraph vs LangChain

| Use LangGraph when... | Use LangChain when... |
|----------------------|----------------------|
| Complex multi-step workflows | Simple agent loops |
| Custom state management | Default message-based state |
| Fine-grained streaming control | Basic streaming needs |
| Multiple conditional branches | Linear tool-calling flows |
| Heavy customization needed | Quick prototyping |

## Documentation Index

| Resource | When to Consult |
|----------|-----------------|
| [overview.md](resources/overview.md) | Getting started, core concepts |
| [quickstart.md](resources/quickstart.md) | First graph tutorial |
| [graph-api.md](resources/graph-api.md) | StateGraph, nodes, edges, state schemas |
| [functional-api.md](resources/functional-api.md) | Functional API alternative |
| [persistence.md](resources/persistence.md) | Checkpointers, durability |
| [memory.md](resources/memory.md) | Memory management patterns |
| [streaming.md](resources/streaming.md) | Stream modes, token streaming |
| [interrupts.md](resources/interrupts.md) | Human-in-the-loop, breakpoints |
| [durable-execution.md](resources/durable-execution.md) | Reliability, recovery |
| [use-subgraphs.md](resources/use-subgraphs.md) | Composing graphs |
| [thinking-in-langgraph.md](resources/thinking-in-langgraph.md) | Mental model, design patterns |
| [workflows-agents.md](resources/workflows-agents.md) | Workflow vs agent patterns |
| [deploy.md](resources/deploy.md) | Deployment options |
| [errors/](resources/errors/) | Error codes and troubleshooting |

## Syncing Documentation

```bash
cd skills/langgraph
bun run scripts/sync-docs.ts
```
