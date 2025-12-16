# Phase 2 Functional Testing Guide

**Purpose:** Manual testing procedures for Phase 2 semantic search functionality
**Target:** QA, developers, and product managers
**Scope:** Search drafts tool, indexing, ChromaDB integration, metadata correlation
**Duration:** 30-45 minutes for full test suite

---

## Pre-Test Setup

### Environment Requirements
- Python 3.12+
- `uv` package manager installed
- Dependencies installed: `uv sync`
- Optional: LLM provider (Ollama running OR OpenAI API key configured)

### Verify Installation
```bash
# Check dependencies
uv run python -c "import chromadb; import sentence_transformers; print('✓ Dependencies installed')"

# Check examples loaded
uv run python -c "from utils.example_loader import ExampleLoader; loader = ExampleLoader(); print(f'✓ {len(loader.examples)} examples loaded')"
```

### Initial State Check
```bash
# Clean ChromaDB for fresh testing (optional)
rm -rf data/chromadb/

# Verify CLI starts
timeout 3 uv run main.py || true
# Should see welcome banner and 29 examples listed
```

---

## Test Suite Overview

| Test | Duration | Difficulty | Purpose |
|------|----------|-----------|---------|
| **Smoke Test** | 2 min | Easy | Verify system starts without errors |
| **Test 1** | 5 min | Easy | Single search query on empty database |
| **Test 2** | 5 min | Easy | Draft creation triggers indexing |
| **Test 3** | 5 min | Medium | Draft search finds created draft |
| **Test 4** | 10 min | Medium | Multiple sequential searches |
| **Test 5** | 10 min | Medium | Complex multi-draft workflow |
| **Test 6** | 10 min | Hard | Semantic search quality test |
| **Persistence Test** | 5 min | Easy | Data survives across sessions |

**Total Time:** ~50 minutes for full suite

---

## Smoke Test (2 minutes)

### Objective
Verify the system starts without errors and CLI displays correctly.

### Steps

1. **Start CLI**
   ```bash
   uv run main.py
   ```

2. **Verify Output**
   - [ ] Welcome banner displays
   - [ ] LLM provider detected (GPT or Ollama)
   - [ ] 29 examples listed with complexity markers
   - [ ] "Enter your request" prompt appears

3. **Exit**
   ```
   Press Ctrl+C to exit
   ```

### Expected Result
✅ **PASS**: System starts cleanly, all 29 examples display with correct complexity colors (🟢🟡🔴)

---

## Test 1: Single Search Query (Empty Database)

### Objective
Verify search_drafts_tool handles queries gracefully when no drafts exist.

### Steps

1. **Run CLI**
   ```bash
   uv run main.py
   ```

2. **Select Example 14**
   ```
   > 14
   ```
   (Or press Enter, then input `14`)

3. **Verify Execution**
   - [ ] CLI shows "📚 Draft Search Agent" panel
   - [ ] Executing: "Search my drafts about budget approval..."
   - [ ] LLM triage identifies task: `search_drafts_tool`
   - [ ] Tool executes successfully

4. **Check Results**
   - [ ] Result displayed in summary table
   - [ ] Message: "No drafts found matching your search for: 'budget approval'"
   - [ ] No errors in console
   - [ ] Task marked as complete

### Expected Output
```
📚 Draft Search Agent
Executing: Search my drafts about budget approval...

[After execution]
No drafts found matching your search for: 'budget approval'
```

### Expected Result
✅ **PASS**: Tool executes without error, returns appropriate "no results" message

---

## Test 2: Draft Creation Triggers Indexing

### Objective
Verify that drafting_tool execution automatically triggers DraftIndexer.

### Steps

1. **Run CLI**
   ```bash
   uv run main.py
   ```

2. **Select Example 15**
   ```
   > 15
   ```
   Request: "Draft an email about Q4 financial planning and budgets, then search my drafts about budget"

3. **Verify Draft Creation**
   - [ ] "✉️ Drafting Agent" panel displays
   - [ ] Draft file created (check output for filename)
   - [ ] Result shows checkmark: "✓ Draft saved to..."

4. **Verify Indexing Happened**
   - [ ] No errors in console about indexing
   - [ ] (Optional) Check logs for "indexing" messages
   - [ ] ChromaDB collection should be created

5. **Verify Search Executes**
   - [ ] "📚 Draft Search Agent" panel displays
   - [ ] Search executes (not skipped)
   - [ ] Results show the draft we just created

### Expected Output
```
✉️ Drafting Agent
Executing: Draft an email about Q4 financial planning...
✓ Draft saved to inbox/drafts/draft_[timestamp].txt

[then]

📚 Draft Search Agent
Executing: Search my drafts about budget...
📧 Search Results for: 'budget'
Found 1 matching drafts:
  1. Subject: Q4 Financial Planning and Budgets
     📅 [timestamp]
     📄 inbox/drafts/draft_[timestamp].txt
     🎯 Request: Draft an email about Q4...
     💬 Preview: [first 150 chars of draft]
     ✅ Relevance: [score]%
```

### Expected Result
✅ **PASS**: Draft created → automatically indexed → search finds it

---

## Test 3: Verify Draft Metadata

### Objective
Confirm that indexed drafts contain complete metadata.

### Steps

1. **Run Previous Test (or Example 15)**
   - Follow steps from Test 2

2. **Verify Metadata in Results**
   Search results should include:
   - [ ] Subject line extracted correctly
   - [ ] Timestamp present and formatted
   - [ ] File path showing inbox/drafts/draft_*.txt
   - [ ] User request summary shown
   - [ ] Preview text present (first ~150 chars)
   - [ ] Relevance score calculated (0-100%)

3. **Check ChromaDB Directly (Optional)**
   ```bash
   ls -la data/chromadb/
   # Should see database files created
   ```

### Expected Result
✅ **PASS**: All metadata fields populated correctly in search results

---

## Test 4: Multiple Sequential Searches

### Objective
Verify multiple search queries work independently.

### Steps

1. **Run CLI**
   ```bash
   uv run main.py
   ```

2. **Select Example 16**
   ```
   > 16
   ```
   Request: "Search my drafts about project proposals, then search for drafts about client feedback"

3. **Verify First Search**
   - [ ] "📚 Draft Search Agent" executes
   - [ ] Query: "Search my drafts about project proposals"
   - [ ] Results returned (or "no drafts found")
   - [ ] No errors

4. **Verify Second Search**
   - [ ] Another "📚 Draft Search Agent" executes
   - [ ] Query: "Search for drafts about client feedback"
   - [ ] Results returned (or "no drafts found")
   - [ ] Both searches complete successfully

5. **Check Summary Table**
   - [ ] Shows 2 rows for search results
   - [ ] Both labeled "📚 Draft Search Tool"
   - [ ] Both have results displayed

### Expected Output
```
[First search completes]
Found X matching drafts: [or "No drafts found"]

[Second search completes]
Found Y matching drafts: [or "No drafts found"]

[Summary shows both]
1. 📚 Draft Search Tool  | Found X matching drafts...
2. 📚 Draft Search Tool  | Found Y matching drafts...
```

### Expected Result
✅ **PASS**: Multiple searches execute sequentially, each completes independently

---

## Test 5: Complex Multi-Draft Workflow

### Objective
Test creation of multiple drafts followed by semantic search.

### Steps

1. **Run CLI**
   ```bash
   uv run main.py
   ```

2. **Select Example 18**
   ```
   > 18
   ```
   Request: "Draft an email about the new product roadmap, draft a follow-up email about timeline expectations, and search my drafts about product strategy"

3. **Verify First Draft Creation**
   - [ ] "✉️ Drafting Agent" panel 1
   - [ ] Draft about "new product roadmap" created
   - [ ] Checkmark displayed

4. **Verify Second Draft Creation**
   - [ ] "✉️ Drafting Agent" panel 2
   - [ ] Draft about "timeline expectations" created
   - [ ] Checkmark displayed

5. **Verify Auto-Indexing**
   - [ ] Both drafts indexed automatically
   - [ ] No indexing errors in logs

6. **Verify Search Finds Both**
   - [ ] "📚 Draft Search Agent" executes
   - [ ] Query: "Search my drafts about product strategy"
   - [ ] Results show 2 drafts found
   - [ ] Both newly created drafts appear in results
   - [ ] Relevance scores calculated

7. **Check Semantic Matching**
   - [ ] Drafts about "roadmap" and "timeline" found by "product strategy" query
   - [ ] Demonstrates semantic similarity (not just keyword matching)
   - [ ] Relevance scores reasonable (typically 70%+)

### Expected Output
```
✉️ Drafting Agent
Executing: Draft an email about the new product roadmap...
✓ Draft saved to inbox/drafts/draft_[timestamp1].txt

✉️ Drafting Agent
Executing: Draft a follow-up email about timeline expectations...
✓ Draft saved to inbox/drafts/draft_[timestamp2].txt

📚 Draft Search Agent
Executing: Search my drafts about product strategy...
📧 Search Results for: 'product strategy'
Found 2 matching drafts:
  1. Subject: New Product Roadmap Email
     ...
     ✅ Relevance: 85.2%

  2. Subject: Timeline Expectations Follow-up
     ...
     ✅ Relevance: 78.4%
```

### Expected Result
✅ **PASS**: 2 drafts created → auto-indexed → semantic search finds both with reasonable relevance scores

---

## Test 6: Semantic Search Quality

### Objective
Verify semantic search finds conceptually related content, not just keywords.

### Steps

1. **Run CLI**
   ```bash
   uv run main.py
   ```

2. **Select Example 17**
   ```
   > 17
   ```
   Request: "Search my drafts about quarterly financial performance review"

3. **Expected Behavior**
   - [ ] Search executes successfully
   - [ ] Query demonstrates semantic complexity: "quarterly financial performance review"
   - [ ] System searches for similar concepts

4. **If Results Exist (from previous tests)**
   - [ ] Look for relevance scores
   - [ ] Drafts don't need to contain exact keywords
   - [ ] Related content matches (e.g., "budget", "Q4", "financial planning")
   - [ ] Scoring makes sense (higher = more similar)

5. **Verify Semantic Matching**
   - [ ] Not keyword-based (wouldn't find "quarterly" specifically)
   - [ ] Meaning-based (finds financial/performance related content)
   - [ ] Relevance scores reflect conceptual similarity

### Expected Output
```
📚 Draft Search Agent
Executing: Search my drafts about quarterly financial performance review...
📧 Search Results for: 'quarterly financial performance review'
Found X matching drafts:
  1. Subject: Q4 Financial Planning...
     ✅ Relevance: 82.1%  [Despite different exact words, found because semantically related]

  2. Subject: Budget Approval Request...
     ✅ Relevance: 71.5%  [Financial topic match]
```

### Expected Result
✅ **PASS**: Semantic search finds related content, demonstrates meaning-based matching

---

## Test 7: Persistence Test

### Objective
Verify that indexed drafts persist across CLI sessions.

### Steps

1. **Run First Session**
   ```bash
   uv run main.py
   ```
   - Select Example 15 (creates and searches for draft)
   - Note the draft created (e.g., draft_20251216_120530.txt)
   - Exit CLI

2. **Run Second Session**
   ```bash
   uv run main.py
   ```

3. **Select Example 14 (Different search)**
   ```
   > 14
   ```
   Request: "Search my drafts about budget approval"

4. **Verify Persistence**
   - [ ] Draft from first session is STILL found
   - [ ] Results show the draft we created in session 1
   - [ ] ChromaDB persisted data across sessions
   - [ ] Metadata intact

5. **Verify ChromaDB Files**
   ```bash
   ls -la data/chromadb/
   # Should show database files

   # Check file sizes increased
   du -sh data/chromadb/
   ```
   - [ ] Directory exists
   - [ ] Contains database files
   - [ ] Files are not empty

### Expected Output
```
[Session 1]
✓ Draft saved to inbox/drafts/draft_20251216_120530.txt

[Session 2, Example 14]
📧 Search Results for: 'budget approval'
Found 1 matching drafts:
  1. Subject: Q4 Financial Planning and Budgets
     📅 2025-12-16 12:05:30
     📄 inbox/drafts/draft_20251216_120530.txt
     ✅ Relevance: 92.3%
```

### Expected Result
✅ **PASS**: Data persists across sessions, ChromaDB successfully stores and retrieves indexed drafts

---

## Test 8: Backward Compatibility Check

### Objective
Verify Phase 2 changes don't break existing Phase 1 functionality.

### Steps

1. **Test Reminder Tool**
   ```bash
   uv run main.py
   ```
   Select Example 1 (or any with reminder_tool)
   - [ ] Reminder tool executes
   - [ ] File created in inbox/reminders/
   - [ ] No errors related to Phase 2 components

2. **Test Drafting Tool (Without Search)**
   ```bash
   uv run main.py
   ```
   Select Example 2 (or 19-20 with single drafting_tool)
   - [ ] Draft created successfully
   - [ ] Auto-indexing happens silently (no visible errors)
   - [ ] Drafting completes as expected

3. **Test External Search Tool**
   ```bash
   uv run main.py
   ```
   Select Example 3 (or any with search_tool)
   - [ ] External search executes
   - [ ] Results returned
   - [ ] Phase 2 components don't interfere

4. **Test Multi-Tool Workflow**
   ```bash
   uv run main.py
   ```
   Select Example 1 (multi-tool example)
   - [ ] All tools execute in sequence
   - [ ] No Phase 2 errors blocking flow
   - [ ] Workflow completes normally

### Expected Result
✅ **PASS**: All Phase 1 tools work unchanged, Phase 2 integration doesn't introduce errors

---

## Test 9: Error Handling & Edge Cases

### Objective
Verify graceful handling of errors and edge cases.

### Steps

1. **Search with Empty Results**
   ```bash
   uv run main.py
   > 14
   ```
   (Search for something that won't match any existing drafts)
   - [ ] No error displayed
   - [ ] Graceful "No drafts found" message
   - [ ] CLI continues normally

2. **Corrupted/Missing Draft File**
   ```bash
   # Create a search query that references a non-existent draft
   uv run main.py
   > 14
   ```
   - [ ] Search handles gracefully
   - [ ] No unhandled exceptions
   - [ ] Error logged (check console)

3. **Network Issues (OpenAI embeddings)**
   ```bash
   # If using OpenAI embeddings
   export EMBEDDING_PROVIDER=openai
   # Disconnect network or use invalid API key
   uv run main.py
   > 14
   ```
   - [ ] Falls back gracefully
   - [ ] Error message helpful
   - [ ] Or fails with clear message

4. **ChromaDB Directory Issues**
   ```bash
   # Remove read permissions from /data/chromadb/
   chmod 000 data/chromadb/
   uv run main.py
   > 14
   ```
   - [ ] Handles permission error gracefully
   - [ ] Helpful error message
   ```bash
   # Restore permissions
   chmod 755 data/chromadb/
   ```

### Expected Result
✅ **PASS**: All errors handled gracefully with informative messages, no crashes

---

## Configuration Testing

### Test Embedding Provider Switching

#### Local Embeddings (Default)
```bash
unset EMBEDDING_PROVIDER
uv run main.py
> 15
```
- [ ] Uses sentence-transformers
- [ ] Search works
- [ ] No external API calls

#### OpenAI Embeddings
```bash
export EMBEDDING_PROVIDER=openai
export OPENAI_API_KEY=your-api-key
uv run main.py
> 15
```
- [ ] Uses OpenAI embeddings
- [ ] Search works with OpenAI vectors
- [ ] Relevance scores may differ slightly

### Expected Result
✅ **PASS**: Both embedding providers work correctly

---

## Performance Checks

### Check Indexing Speed
```bash
# Run Example 15 and note time
uv run main.py
> 15
# Measure: Time from "✉️ Drafting Agent" start to "✓ Draft saved"
# Expected: <2 seconds for indexing after draft creation
```

### Check Search Speed
```bash
# Run Example 14 and note time
uv run main.py
> 14
# Measure: Time from "📚 Draft Search Agent" start to results displayed
# Expected: <1 second for search query
```

### Check Disk Usage
```bash
du -sh data/chromadb/
# Expected: < 50 MB for reasonable number of drafts
```

---

## Test Results Template

### Test Execution Summary

| Test | Status | Duration | Notes |
|------|--------|----------|-------|
| Smoke Test | ✅ / ❌ | ___ min | |
| Test 1: Empty Search | ✅ / ❌ | ___ min | |
| Test 2: Draft Creation + Indexing | ✅ / ❌ | ___ min | |
| Test 3: Draft Metadata | ✅ / ❌ | ___ min | |
| Test 4: Multiple Searches | ✅ / ❌ | ___ min | |
| Test 5: Complex Workflow | ✅ / ❌ | ___ min | |
| Test 6: Semantic Search | ✅ / ❌ | ___ min | |
| Test 7: Persistence | ✅ / ❌ | ___ min | |
| Test 8: Backward Compatibility | ✅ / ❌ | ___ min | |
| Test 9: Error Handling | ✅ / ❌ | ___ min | |

### Issues Found

| Issue | Severity | Impact | Reproduction | Resolution |
|-------|----------|--------|--------------|------------|
| | | | | |

### Overall Result

- **Total Tests Run:** __
- **Passed:** __ ✅
- **Failed:** __ ❌
- **Blockers:** None / ___
- **Recommendation:** **PASS** / **FAIL** / **CONDITIONAL**

---

## Troubleshooting Common Issues

### Issue: "No examples loaded"
**Cause:** data/examples.yaml missing or malformed
**Solution:**
```bash
# Verify file exists
ls -la data/examples.yaml

# Check YAML syntax
uv run python -c "from utils.example_loader import ExampleLoader; ExampleLoader()"
```

### Issue: "ModuleNotFoundError: chromadb"
**Cause:** Dependencies not installed
**Solution:**
```bash
uv sync
```

### Issue: "Circular import error"
**Cause:** Old tools/__init__.py configuration
**Solution:**
```bash
# Verify tools/__init__.py has lazy imports
cat tools/__init__.py
# Should NOT have: from .search_drafts_tool import SearchDraftsTool
```

### Issue: Search returns no results even after creating drafts
**Cause:** Indexing failed silently
**Solution:**
```bash
# Check if drafts created
ls -la inbox/drafts/

# Check ChromaDB created
ls -la data/chromadb/

# Check console logs for indexing errors
```

### Issue: "Draft Search Agent" doesn't appear
**Cause:** LLM not recognizing search_drafts_tool
**Solution:**
```bash
# Verify tool registered
uv run python -c "from agents.llm_triage_agent import AVAILABLE_TOOLS; print('search_drafts_tool' in AVAILABLE_TOOLS)"
# Should print: True
```

---

## Success Criteria

Phase 2 is considered **PASS** if:

- [x] ✅ All 9 core tests pass
- [x] ✅ Semantic search finds relevant drafts
- [x] ✅ Auto-indexing works without errors
- [x] ✅ Data persists across sessions
- [x] ✅ Backward compatibility maintained
- [x] ✅ No crashes or unhandled exceptions
- [x] ✅ Metadata correctly captured and displayed
- [x] ✅ Configuration switching works (if applicable)

Phase 2 is considered **CONDITIONAL** if:

- ⚠️ Most tests pass but minor issues found
- ⚠️ Performance slightly below targets
- ⚠️ Edge cases not fully handled

Phase 2 is considered **FAIL** if:

- ❌ Search doesn't find created drafts
- ❌ Indexing fails systematically
- ❌ Core Phase 1 tools broken
- ❌ Crashes or unhandled exceptions
- ❌ Data not persisting

---

## Next Steps After Testing

1. **Document any issues** found during testing
2. **Note performance metrics** (indexing speed, search speed, disk usage)
3. **Record environment details** (LLM provider, embedding provider, OS)
4. **Create issues** for any bugs found
5. **Schedule Phase 3 planning** if Phase 2 passes

---

## Additional Resources

- **Implementation Details:** COMPLETION_SUMMARY.md
- **Architecture Overview:** status.md
- **Code Reference:**
  - Search Tool: `tools/search_drafts_tool.py`
  - ChromaDB Manager: `utils/chromadb_manager.py`
  - Indexer: `tools/draft_indexer.py`
  - Examples: `data/examples.yaml`
  - Loader: `utils/example_loader.py`

---

**Last Updated:** 2025-12-16
**Phase:** 2
**Status:** Ready for Testing
