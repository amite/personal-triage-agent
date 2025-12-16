# Phase 2: ChromaDB Semantic Search - Technical Analysis

**Date:** 2025-12-16
**Status:** Planning phase analysis

## Executive Summary

Phase 2 integrates semantic search for email drafts using ChromaDB. The implementation:
- Adds 3 new modules (~290 lines of code)
- Modifies 5 existing files (~60 lines total)
- Introduces ChromaDB + Sentence Transformers dependencies
- Maintains backward compatibility
- Enables natural language queries over draft history

**Risk Level**: Low-to-Medium (well-isolated, additive changes)
**Complexity**: Medium (new dependency + checkpoint integration)
**Effort**: 4-6 hours (estimated)

---

## Codebase Integration Points

### 1. Draft Generation System

**Current Flow**:
```
DraftingTool.execute(content)
  ├─ Generate email body via LLM
  ├─ Create draft template
  └─ Save to inbox/drafts/draft_{TIMESTAMP}_{TOPIC}.txt
     └─ Return result: "✓ Email draft saved to {path}"
```

**Phase 2 Addition**:
```
After line 133 in main.py:tool_execution_node()
  ├─ Detect: tool_name == "drafting_tool" and "✓" in result
  ├─ Extract: file_path from result string
  ├─ Get: thread_id from workflow context
  └─ Index: DraftIndexer.index_draft_file(path, thread_id, checkpoint_id)
```

**Impact**: Minimal - 15 lines added, no changes to existing draft logic

### 2. Checkpoint System (Phase 1 Foundation)

**Current State**:
```
data/checkpoints.db
├─ checkpoints table: thread_id, checkpoint_ns, checkpoint_id, checkpoint (BLOB)
└─ writes table: thread_id, checkpoint_id, task_id, channel, value

Structure (AgentState):
├─ user_request: str (original query)
├─ task_queue: List[Dict] (remaining tasks)
├─ results: Dict[str, str] (tool execution outputs)
├─ llm_reasoning: List[str] (why tasks were identified)
├─ agent_thoughts: List[str] (execution trace)
└─ iteration: int (step counter)
```

**Phase 2 Usage**:
```
For each draft indexed:
├─ Read checkpoint (latest or by ID)
├─ Extract metadata:
│  ├─ user_request: Original user query
│  ├─ llm_reasoning: Reasoning from triage
│  ├─ thread_id: Session identifier
│  └─ iteration: Execution step
└─ Merge with draft file metadata:
   ├─ timestamp: From file
   ├─ subject: Extracted from draft
   ├─ body: Email content (embedded)
   └─ file_path: Disk location
```

**Impact**: Read-only access via new utility functions (utils/inspect_checkpoints.py)

### 3. Tool Registry & LLM Triage

**Current State** (`agents/llm_triage_agent.py`):
```python
AVAILABLE_TOOLS = {
    "reminder_tool": ReminderTool,
    "drafting_tool": DraftingTool,
    "search_tool": ExternalSearchTool
}
```

**Phase 2 Addition**:
```python
AVAILABLE_TOOLS = {
    # ... existing tools ...
    "search_drafts_tool": SearchDraftsTool  # NEW
}
```

**Impact**: 2-line change, tool cache auto-updates via `_build_tool_cache()`

---

## Architecture Deep-Dive

### Embedding Provider Strategy

**Why Factory Pattern?**
- Current: Single LLM provider (Ollama or GPT) via LLMFactory
- Need: Optional OpenAI embeddings for production
- Solution: Identical pattern = consistency + familiarity

**Provider Selection Flow**:
```
EmbeddingFactory.get_embedding_function()
├─ Check env: EMBEDDING_PROVIDER
├─ If "openai":
│  ├─ Get OPENAI_API_KEY
│  └─ Return OpenAIEmbeddingFunction(api_key)
│     └─ If key missing: fall back to SentenceTransformer + log warning
└─ Else (default "local"):
   └─ Return SentenceTransformerEmbeddingFunction()
      └─ Model: all-MiniLM-L6-v2 (384 dimensions)
```

**Local Embeddings (Default)**:
- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Dimensions: 384
- Speed: ~10ms per document (GPU: <1ms)
- Quality: Good for draft search (optimized for semantic similarity)
- Cost: Zero (one-time ~90MB download)

**OpenAI Embeddings (Optional)**:
- Model: `text-embedding-3-small`
- Dimensions: 1536
- Speed: ~100ms per document (API latency)
- Quality: Excellent (SOTA embedding quality)
- Cost: $0.02 per 1M input tokens (~$0.001-0.01 per 100 drafts)

**Trade-off Decision**: Default local (low cost, acceptable quality) + production option (high quality, cost)

### ChromaDB Integration Points

**Why ChromaDB?**
- Vector DB designed for LLM applications
- Persistent storage (SQLite backend by default)
- Metadata filtering support
- Easy to swap (Pinecone, Weaviate, etc. later)
- No external service needed (local mode)

**Collection Schema**:
```
Collection: email_drafts
├─ Documents: Email body text (LLM-generated content)
├─ Embeddings: 384-dim or 1536-dim vectors (provider-dependent)
└─ Metadata per document:
   ├─ thread_id: Session UUID (searchable)
   ├─ timestamp: ISO 8601 string
   ├─ subject: Email subject line
   ├─ user_request: Original query (searchable)
   ├─ llm_reasoning: Why draft was created
   ├─ file_path: Disk location (for retrieval)
   ├─ tool_name: "drafting_tool" (for filtering)
   └─ iteration: Execution step number
```

**Storage Location**: `data/chromadb/`
- Auto-created by ChromaDB on first run
- Persistent across sessions
- Excludable from git via `.gitignore`

### Real-Time Indexing Design

**Why Hook in tool_execution_node?**

Current (without indexing):
```
tool_execution_node:
  1. Execute tool → Get result
  2. Update state["results"]
  3. Pop task from queue
  4. Return state
  ↓ (LangGraph creates checkpoint after node completes)
  Checkpoint written to checkpoints.db
```

With indexing (after line 133):
```
tool_execution_node:
  1. Execute tool → Get result
  2. Update state["results"]
  3. [NEW] If drafting_tool:
     ├─ Extract file_path from result
     ├─ Get thread_id from workflow config
     └─ Index draft (reading latest checkpoint context)
  4. Pop task from queue
  5. Return state
  ↓ (LangGraph creates new checkpoint)
```

**Timing Consideration**:
- Previous checkpoint exists (from triage/earlier tools)
- Current node hasn't been checkpointed yet
- Solution: Query latest checkpoint by thread_id
  - If recent (same iteration), use it
  - If stale, index with minimal metadata + log warning

**Latency Impact**:
- File read: ~1-2ms
- Checkpoint query: ~2-5ms
- Embedding: ~10-50ms (local) or ~100ms (OpenAI)
- ChromaDB write: ~5-10ms
- **Total**: ~20-70ms (local) or ~110-150ms (OpenAI)
- **Acceptable**: Yes (tool execution already 100-1000ms)

### Checkpoint Deserialization Challenge

**Problem**: Checkpoints stored as msgpack blobs

```python
# In checkpoints.db:
checkpoint BLOB = msgpack.packb(AgentState dict)
```

**Solution**: Use LangGraph's deserialization

```python
# Option 1: Use existing LangGraph utilities
from langgraph.checkpoint.base import ChannelVersions

# Option 2: Manual msgpack unpacking (if needed)
import msgpack
state_dict = msgpack.unpackb(checkpoint_blob)

# Option 3: Query via get_state() (most robust)
config = {"configurable": {"thread_id": thread_id}}
state = graph.get_state(config)  # LangGraph handles deserialization
```

**Recommendation**: Use Option 3 (graph.get_state) in production
- Leverages existing LangGraph code
- Handles version compatibility
- Most reliable

**Risk**: If LangGraph internal format changes
- Mitigation: Add version check, fallback to minimal metadata

---

## Data Flow Architecture

### End-to-End Sequence

```
User Query: "Draft email about Q4 budget"
│
├─ Triage Node
│  ├─ LLM analyzes: "Need to draft email"
│  └─ Checkpoint A: task_queue = [{"tool": "drafting_tool", "content": "..."}]
│
├─ Tool Execution Node
│  ├─ DraftingTool.execute()
│  │  ├─ LLM generates email body
│  │  └─ Saves: inbox/drafts/draft_20251216_120000_Q4_budget.txt
│  │  └─ Returns: "✓ Email draft saved to inbox/drafts/draft_..."
│  │
│  ├─ Update state["results"]["drafting_tool_1"] = result
│  │
│  ├─ [NEW] DraftIndexer.index_draft_file()
│  │  ├─ Read draft file → Extract body, subject, timestamp
│  │  ├─ Get latest checkpoint → Extract user_request, llm_reasoning
│  │  ├─ Merge metadata:
│  │  │  ├─ Draft content (file-based)
│  │  │  ├─ Checkpoint context (database)
│  │  │  └─ Execution metadata (state + environment)
│  │  └─ ChromaDBManager.index_draft(body, metadata)
│  │     ├─ Embed text via EmbeddingFactory
│  │     ├─ Store in ChromaDB with metadata
│  │     └─ Return doc ID
│  │
│  └─ Checkpoint B: results updated, draft indexed
│
├─ Finish Node
│  └─ Checkpoint C: Final state compiled
│
└─ [Later] Search: "Find drafts about budget"
   ├─ User says: "Search my drafts about budget"
   ├─ Triage recognizes: "search_drafts_tool"
   ├─ SearchDraftsTool.execute("budget")
   │  ├─ ChromaDBManager.search_drafts("budget", n_results=5)
   │  │  ├─ Embed query: "budget" (same provider as documents)
   │  │  ├─ Cosine similarity search in ChromaDB
   │  │  └─ Return: [doc1, doc2, ...] + metadata
   │  ├─ Format results (Rich table: timestamp, subject, snippet)
   │  └─ Return: Formatted string with file paths
   └─ Display: "Found 3 drafts about budget"
```

---

## Dependency Analysis

### New Dependencies

| Dependency | Version | Size | Purpose | Risk |
|------------|---------|------|---------|------|
| chromadb | >=0.4.24 | ~5MB | Vector DB | Low |
| sentence-transformers | >=2.0.0 | ~90MB | Embeddings | Low |

**Model Download**:
- `all-MiniLM-L6-v2` downloads on first use (~50MB)
- Cached in `~/.cache/huggingface/`
- One-time download

**Total Installation Impact**:
- Disk: ~150MB (code + cached model)
- Memory: ~200MB (model loaded in RAM when needed)
- Build time: ~2-3 minutes (first sync)

**Existing Dependencies Used**:
- `openai>=1.0.0` (already present for GPT provider)

### Compatibility Considerations

**Python Version**: 3.10+ (same as existing project)
**OS Support**: Linux, macOS, Windows (all fully supported)
**LangGraph Version**: No version constraints needed (read-only use of checkpoints)

---

## Error Handling Strategy

### Scenario 1: Draft File Not Found
**Cause**: File deleted between execution and indexing
**Handling**:
```python
try:
    with open(file_path) as f:
        content = f.read()
except FileNotFoundError:
    logger.error(f"Draft file not found: {file_path}")
    # Skip indexing, return early
    return False
```

### Scenario 2: Checkpoint Deserialization Fails
**Cause**: msgpack format corrupted or incompatible version
**Handling**:
```python
try:
    state = checkpoint.get_state(config)
except Exception as e:
    logger.warning(f"Checkpoint deserialization failed: {e}, using defaults")
    metadata = {"thread_id": thread_id}  # Minimal metadata
```

### Scenario 3: Embedding Generation Fails
**Cause**: OpenAI API timeout or model download fails (Sentence Transformers)
**Handling**:
```python
try:
    embeddings = embedding_function([text])
except Exception as e:
    logger.error(f"Embedding failed: {e}")
    raise  # Fail explicitly (better than silent skip)
```

### Scenario 4: ChromaDB Write Fails
**Cause**: Disk full, permission denied, or corruption
**Handling**:
```python
try:
    doc_id = collection.add(
        documents=[body],
        metadatas=[metadata],
        ids=[unique_id]
    )
except Exception as e:
    logger.error(f"ChromaDB index failed: {e}")
    # Don't crash workflow - log and continue
```

---

## Testing Strategy

### Unit Tests (Per Component)

1. **EmbeddingFactory**
   - Test local provider (default)
   - Test OpenAI provider (if API key available)
   - Test fallback behavior (missing key)

2. **ChromaDBManager**
   - Test collection creation
   - Test document indexing
   - Test search results
   - Test metadata filtering

3. **DraftIndexer**
   - Test draft file parsing
   - Test checkpoint context lookup
   - Test metadata merging
   - Test error handling

4. **SearchDraftsTool**
   - Test query parsing
   - Test result formatting
   - Test empty results
   - Test special characters in queries

### Integration Tests

1. **Full Workflow**
   - Create draft via UI
   - Verify indexing completes
   - Query indexed draft
   - Verify result accuracy

2. **Backward Compatibility**
   - Run without search_drafts_tool
   - Drafting still works
   - No new errors in logs

3. **Checkpoint Correlation**
   - Verify thread_id matches
   - Verify user_request preserved
   - Verify timestamp accuracy

4. **Provider Switching**
   - Switch to OpenAI (if available)
   - Re-index and search
   - Verify results still relevant

### Performance Tests

1. **Indexing Latency**
   - Measure with local embeddings (target: <100ms)
   - Measure with OpenAI (target: <200ms)

2. **Search Latency**
   - Query 10 drafts (target: <50ms)
   - Query 100 drafts (target: <100ms)

3. **Storage Usage**
   - Measure per draft (target: <500KB per document)
   - Estimate growth rate

---

## Future Enhancement Opportunities

### Phase 2.5: Reminders Indexing
- Add reminders to ChromaDB (separate collection)
- Lower priority (simple text, low semantic value)
- Could enable: "Find all reminders about budget"

### Phase 3: Context-Aware Triage
- Use search results to enhance LLM prompts
- "Similar drafts found: [titles]"
- Enables: "Draft something similar to past email about..."

### Phase 4: Historical Analytics
- Search + analyze trends
- "Most common draft topics"
- "Time spent on different draft types"

### Phase 2.5 Alternative: Query Expansion
- When user searches "budget," also try "expense," "spending"
- Uses LLM to generate similar queries
- Improves recall for vague searches

---

## Production Deployment Checklist

- [ ] Load test with 1000+ drafted emails
- [ ] Measure OpenAI API costs (if using)
- [ ] Plan for ChromaDB migration if switching backends
- [ ] Document embedding provider switching process
- [ ] Set up monitoring for indexing failures
- [ ] Plan for reindexing strategy (version changes, etc.)

---

## Conclusion

Phase 2 adds semantic search with:
- **Minimal risk**: Isolated changes, backward compatible
- **Clean architecture**: Factory pattern for flexibility
- **Production-ready**: Supports local and OpenAI embeddings
- **Well-integrated**: Leverages Phase 1 checkpoints
- **Reasonable effort**: 4-6 hours estimated

The implementation follows established patterns (LLMFactory, tool registration) and maintains code quality standards. Checkpoint integration provides rich context for search, and real-time indexing ensures consistency.

Ready for implementation.
