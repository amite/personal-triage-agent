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

## Embedding Function Consistency Fix (2025-12-16)

### Problem: Embedding Function Conflict

After the initial fix, a new issue was discovered during Phase 2 testing:
- ChromaDB collections cannot change their embedding function after creation
- If a collection was created with one embedding provider (e.g., `openai`) and the code later tries to use a different provider (e.g., `local`), ChromaDB raises a `ValueError`
- Error message: `"An embedding function already exists in the collection configuration, and a new one is provided"`

This caused indexing to fail when:
1. Collection was created with OpenAI embeddings (when `EMBEDDING_PROVIDER=openai`)
2. Later runs tried to use local embeddings (default `EMBEDDING_PROVIDER=local`)
3. ChromaDB rejected the mismatch, preventing draft indexing

### Solution: Automatic Collection Recreation

Updated `utils/chromadb_manager.py` to handle embedding function conflicts gracefully:

1. **Detection**: When `get_or_create_collection()` raises a `ValueError` due to embedding function mismatch
2. **Recovery**: Automatically delete the existing collection and recreate it with the current embedding function
3. **Consistency**: Ensures the collection always matches the current `EMBEDDING_PROVIDER` environment variable setting

**Implementation details:**
- Wrapped `get_or_create_collection()` in try/except to catch `ValueError`
- Check error message for "embedding function" and "already exists" keywords
- Delete existing collection using `client.delete_collection()`
- Recreate collection with current embedding function from `EmbeddingFactory.get_embedding_function()`
- Log warning message when recreation occurs

### Behavior

- **First run**: Collection created with current embedding provider
- **Provider change**: If `EMBEDDING_PROVIDER` changes, collection is automatically recreated on next initialization
- **Warning**: Previously indexed drafts are lost when collection is recreated (expected behavior, as embeddings are provider-specific)
- **Consistency**: Once recreated, collection uses the same embedding function consistently until provider changes

### Code Location

**File**: `utils/chromadb_manager.py`
**Method**: `ChromaDBManager._initialize()`
**Lines**: ~45-75

### Testing

Verified with Phase 2 Test 2:
- Draft creation works correctly
- Indexing no longer fails with embedding function conflicts
- Collection automatically uses current `EMBEDDING_PROVIDER` setting
- Warning logged when collection is recreated: `"Collection exists with different embedding function. Deleting and recreating to use current embedding provider."`

## Docs consulted
- Context7: `/chroma-core/chroma` embedding function docs (custom `EmbeddingFunction` via `__call__`)
- Runtime inspection in the project's `uv` environment confirmed ChromaDB `1.3.7` requires `name()` and `get_config()` methods on embedding functions used for persisted collections.
- Context7: OpenAI Python library documentation for Responses API structure and response parsing


