# ChromaDB embedding function interface fix (Example 14 crash)

## Summary
Example 14 (“Search my drafts about budget approval”) was crashing during ChromaDB initialization when using the OpenAI embedding provider. The root cause was a mismatch between ChromaDB’s expected embedding function interface (ChromaDB `1.3.7`) and our custom embedding wrappers.

We fixed this by switching `utils/embedding_factory.py` to return ChromaDB’s **built-in** embedding functions (`chromadb.utils.embedding_functions.*`) which implement the required persistence/config interface.

## Repro

```bash
cd /home/amite/code/python/personal-triage-agent
printf "14\n" | uv run main.py
```

### Observed errors (before fix)
- `Failed to initialize ChromaDB: 'OpenAIEmbeddingFunction' object has no attribute 'name'`
- After adding a string `name` attribute: `Error: 'str' object is not callable`

## Root cause
ChromaDB `1.3.7` expects embedding functions used with persistent collections to expose **methods**:
- `name()` (returns a stable provider identifier like `"openai"`)
- `get_config()` (returns a serializable config dict)

Our custom embedding wrappers in `utils/embedding_factory.py` only implemented `__call__`, and when we attempted to patch in `name` it was a string attribute rather than a callable `name()` method. That caused ChromaDB’s persistence layer to call `embedding_function.name()` and crash.

## Fix
### What changed
We updated `utils/embedding_factory.py` to return ChromaDB’s built-in embedding functions:
- `chromadb.utils.embedding_functions.OpenAIEmbeddingFunction(...)`
- `chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction(...)`

This avoids interface drift across Chroma versions and guarantees `name()` / `get_config()` are present and compatible.

### Environment variables supported
- `EMBEDDING_PROVIDER`: `openai` or `local` (default: `local`)
- `OPENAI_EMBEDDING_MODEL`: embedding model name (default: `text-embedding-3-small`)
- `LOCAL_EMBEDDING_MODEL`: local model name (default: `all-MiniLM-L6-v2`)
- `LOCAL_EMBEDDING_DEVICE`: `cpu`/`cuda` etc (default: `cpu`)

Note: For Chroma’s built-in OpenAI embedder, we pass `api_key_env_var="OPENAI_API_KEY"` to align with the existing app’s `.env`/runtime configuration.

## Verification

```bash
cd /home/amite/code/python/personal-triage-agent
printf "14\n" | uv run main.py
```

Expected outcome:
- App starts normally
- Example 14 runs `search_drafts_tool`
- No crash during ChromaDB init
- Output contains a “No drafts found …” message (when there are no matching drafts indexed)

## Docs consulted
- Context7: `/chroma-core/chroma` embedding function docs (custom `EmbeddingFunction` via `__call__`)
- Runtime inspection in the project’s `uv` environment confirmed ChromaDB `1.3.7` requires `name()` and `get_config()` methods on embedding functions used for persisted collections.


