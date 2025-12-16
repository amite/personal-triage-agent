## How ChromaDB Fits Into Personal Triage Agent

The triage agent saves every generated draft to SQLite and mirrors the same content
into ChromaDB so you can run semantic search (e.g., follow-up prompts like “find my Q4
budget emails”). ChromaDB is configured with a persistent client (`chroma.PersistentClient`)
and a single `email_drafts` collection that stores embeddings for each draft.

### `utils/chromadb_manager.py`

- Initializes the `chroma.PersistentClient` in `data/chromadb` and calls
  `get_or_create_collection("email_drafts")` with the embedding function from
  `EmbeddingFactory`. If the stored embedding function changes, the collection is
  deleted and recreated so the schema stays consistent.
- Exposes helpers:
  - `get_collection()` returns the ready-made collection so tools and scripts can
    call methods like `count()` and `peek(limit=10)` when they need verification[^1].
  - `index_draft(content, metadata)` adds a document to ChromaDB with a metadata
    dictionary that captures `draft_id`, `subject`, `thread_id`, `timestamp`, and
    checkpoint context.
  - `search_drafts(query)` performs a semantic search and formats the results so
    callers only have to read the list of (metadata, document, distance) tuples.

### `utils/embedding_factory.py`

- Picks an embedding provider based on environment variables:
  - Default: local SentenceTransformer (`all-MiniLM-L6-v2`) with GPU/CPU auto-detection.
  - Optional: OpenAI embeddings when `EMBEDDING_PROVIDER=openai` and an API key is set.
- Each embedding function implements the interface Chroma expects (`name()`, `get_config()`),
  which is why we rely on Chroma’s own helpers under `chromadb.utils.embedding_functions`.
  The same model parameters feed into the `ChromaDBManager` so all added documents
  share the same vector space.

### Tools and Agents

- `tools/drafting_tool.py` creates the draft text, stores it in SQLite, and returns a
  dictionary with `success=True` and a `draft_id`. The `main.py` workflow inspects
  that result and runs `DraftIndexer.index_draft_by_id()`.
- `tools/draft_indexer.py` loads the draft body, merges metadata from `ArtifactsDB`
  and LangGraph checkpoints, then calls `ChromaDBManager.index_draft()`. If indexing
  fails, it logs the error but lets the workflow continue.
- `tools/search_drafts_tool.py` is the consumer: it creates a `ChromaDBManager`,
  calls `search_drafts()` with the user’s query, and formats the first few hits for
  display.
- `agents/llm_drafting_agent.py` and `agents/llm_triage_agent.py` orchestrate these
  tools. The triage agent routes user requests to `drafting_tool`, `reminder_tool`,
  or `search_drafts_tool` based on the parsed JSON response from the LLM.

### Workflow (`main.py`)

1. Request enters `run_task_manager()`, the graph dispatches to `tool_execution_node`.
2. If the selected tool is `drafting_tool`, the Drafting Agent returns `{"success": True, "draft_id": ...}`.
3. The new logging in `tool_execution_node` now traces the result and starts indexing:
   - Initializes `DraftIndexer` with the current `thread_id`.
   - Calls `index_draft_by_id()` and reports success/failure in the console (and the logs).
4. The `check_chromadb` script (`scripts/check_chromadb.py`) can be run manually or via
   `utils/nu-scripts/check-chromadb.nu` to compare `collection.count()` vs. SQLite and
   to peek at the top documents.
5. `tools/test_indexing.py` (`utils/nu-scripts/test-indexing.nu`) can rebuild the collection
   if you need to re-sync all drafts.

These pieces ensure the LLM-powered workflow stays in sync with the semantic memory layer.

## Helpful Documentation Links

- Chroma collection helpers (`count`, `peek`) for inspecting stored documents[^1].
- Python collection count reference[^2].
- Embedding function reference and requirements in Chroma[^3].

[^1]: https://docs.trychroma.com/docs/collections/manage-collections/
[^2]: https://docs.trychroma.com/reference/python/collection#count
[^3]: https://docs.trychroma.com/docs/embeddings/#using-the-embedding-functions

