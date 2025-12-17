# Phase 2 Functional Testing Guide

**Purpose:** Manual testing procedures for Phase 2 semantic search functionality
**Target:** QA, developers, and product managers
**Scope:** Search drafts tool, indexing, ChromaDB integration, artifacts database, metadata correlation
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

# Check artifacts database module
uv run python -c "from utils.artifacts_db import ArtifactsDB; print('✓ Artifacts database module available')"
```

### Initial State Check
```bash
# Clean ChromaDB for fresh testing (optional)
rm -rf data/chromadb/

# Clean artifacts database for fresh testing (optional)
rm -f data/artifacts.db

# Verify CLI starts
timeout 3 uv run main.py || true
# Should see welcome banner and 29 examples listed
```

### Verify Database Setup
```bash
# Check artifacts database is created on first run
uv run python -c "from utils.artifacts_db import ArtifactsDB; db = ArtifactsDB(); print('✓ Artifacts database initialized')"

# Verify database schema
uv run python -c "import sqlite3; conn = sqlite3.connect('data/artifacts.db'); cursor = conn.cursor(); cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table'\"); tables = [row[0] for row in cursor.fetchall()]; print(f'✓ Tables: {tables}'); conn.close()"
# Should show: ['reminders', 'drafts']
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
| **Test 7** | 5 min | Easy | Artifacts database verification |
| **Test 8** | 5 min | Easy | Data persists across sessions |
| **Test 9** | 5 min | Easy | Backward compatibility check |
| **Test 10** | 5 min | Medium | Error handling & edge cases |

**Total Time:** ~60 minutes for full suite

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
   - [x ] Welcome banner displays
   - [x] LLM provider detected (GPT or Ollama)
   - [x] 29 examples listed with complexity markers
   - [x] "Enter your request" prompt appears

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
   - [x] CLI shows "📚 Draft Search Agent" panel
   - [x] Executing: "Search my drafts about budget approval..."
   - [x] LLM triage identifies task: `search_drafts_tool`
   - [x] Tool executes successfully

4. **Check Results**
   - [x] Result displayed in summary table
   - [x] Message: "No drafts found matching your search for: 'budget approval'"
   - [x] No errors in console
   - [x] Task marked as complete

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
   - [ ] Result shows checkmark: "✓ Email draft created (ID: [draft_id]): '[subject]'"
   - [ ] Draft ID is displayed in the result message

4. **Verify Database Record Created**
   - [ ] Artifacts database contains the draft record
   - [ ] Draft ID is valid (can be queried from database)
   - [ ] Thread ID is linked to the draft
   

5. **Verify Indexing Happened**
   - [ ] No errors in console about indexing
   - [ ] (Optional) Check logs for "indexing" messages
   - [ ] ChromaDB collection should be created
   
   **Query Commands:**

   
   # Check ChromaDB directory exists
   ls -la data/chromadb/
   # Should show database files (chroma.sqlite3, etc.)
   ```

6. **Verify Search Executes**
   - [ ] "📚 Draft Search Agent" panel displays
   - [ ] Search executes (not skipped)
   - [ ] Results show the draft we just created

### Expected Output
```
✉️ Drafting Agent
Executing: Draft an email about Q4 financial planning...
✓ Email draft created (ID: 1): 'Re: Q4 financial planning and budgets'

[then]

📚 Draft Search Agent
Executing: Search my drafts about budget...
📧 Search Results for: 'budget'
Found 1 matching drafts:
  1. Subject: Re: Q4 financial planning and budgets
     📅 [timestamp]
     🆔 Draft ID: 1
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
   - [ ] Draft ID displayed
   - [ ] User request summary shown
   - [ ] Preview text present (first ~150 chars)
   - [ ] Relevance score calculated (0-100%)

3. **Verify Database Record (Optional)**
   ```bash
   # Check draft exists in artifacts database
   uv run python -c "from utils.artifacts_db import ArtifactsDB; db = ArtifactsDB(); drafts = db.get_drafts_by_thread('unknown'); print(f'✓ Found {len(drafts)} draft(s) in database')"
   
   # Get specific draft with all metadata
   uv run python -c "
   from utils.artifacts_db import ArtifactsDB
   db = ArtifactsDB()
   drafts = db.get_drafts_by_thread('unknown')
   if drafts:
       d = drafts[0]
       print(f'✓ Draft ID {d[\"id\"]}:')
       print(f'  Subject: {d[\"subject\"]}')
       print(f'  Created: {d[\"created_at\"]}')
       print(f'  Status: {d[\"status\"]}')
       print(f'  Body preview: {d[\"body\"][:100]}...')
   "
   ```

4. **Check ChromaDB Directly (Optional)**
   ```bash
   # Check ChromaDB directory and files
   ls -la data/chromadb/
   # Should see database files created (chroma.sqlite3, etc.)
   
   # Check ChromaDB collection and document count
   uv run python -c "
   from utils.chromadb_manager import ChromaDBManager
   manager = ChromaDBManager()
   collection = manager.get_collection()
   if collection:
       count = manager.get_draft_count()
       print(f'✓ ChromaDB collection: email_drafts')
       print(f'  Total documents: {count}')
       
       # Get sample document IDs
       if count > 0:
           results = collection.get(limit=1)
           if results['ids']:
               print(f'  Sample document ID: {results[\"ids\"][0]}')
   else:
       print('✗ ChromaDB collection not initialized')
   "
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
✓ Email draft created (ID: 1): 'Re: the new product roadmap'

✉️ Drafting Agent
Executing: Draft a follow-up email about timeline expectations...
✓ Email draft created (ID: 2): 'Re: timeline expectations'

📚 Draft Search Agent
Executing: Search my drafts about product strategy...
📧 Search Results for: 'product strategy'
Found 2 matching drafts:
  1. Subject: Re: the new product roadmap
     🆔 Draft ID: 1
     ...
     ✅ Relevance: 85.2%

  2. Subject: Re: timeline expectations
     🆔 Draft ID: 2
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

## Test 7: Artifacts Database Verification

### Objective
Verify that artifacts (drafts and reminders) are properly stored in the SQLite database.

### Steps

1. **Run CLI and Create Artifacts**
   ```bash
   uv run main.py
   ```
   - Select Example 15 (creates a draft)
   - Note the draft ID from the output

2. **Verify Draft in Database**
   ```bash
   # Query database directly - list all drafts
   uv run python -c "
   from utils.artifacts_db import ArtifactsDB
   db = ArtifactsDB()
   drafts = db.get_drafts_by_thread('unknown')
   print(f'✓ Found {len(drafts)} draft(s) in database')
   for draft in drafts:
       print(f'  - ID {draft[\"id\"]}: {draft[\"subject\"]} (created: {draft[\"created_at\"]})')
   "
   
   # Get specific draft by ID (replace 1 with actual draft ID)
   uv run python -c "
   from utils.artifacts_db import ArtifactsDB
   db = ArtifactsDB()
   draft = db.get_draft(1)
   if draft:
       print(f'✓ Draft ID 1 details:')
       print(f'  Subject: {draft[\"subject\"]}')
       print(f'  Thread ID: {draft[\"thread_id\"]}')
       print(f'  Created: {draft[\"created_at\"]}')
       print(f'  Status: {draft[\"status\"]}')
       print(f'  Body length: {len(draft[\"body\"])} chars')
   else:
       print('✗ Draft ID 1 not found')
   "
   
   # Query using SQL directly for more control
   uv run python -c "
   import sqlite3
   conn = sqlite3.connect('data/artifacts.db')
   conn.row_factory = sqlite3.Row
   cursor = conn.cursor()
   cursor.execute('SELECT * FROM drafts ORDER BY created_at DESC LIMIT 5')
   drafts = cursor.fetchall()
   print(f'✓ Latest {len(drafts)} draft(s):')
   for d in drafts:
       print(f'  - ID {d[\"id\"]}: {d[\"subject\"]} (thread: {d[\"thread_id\"]}, created: {d[\"created_at\"]})')
   conn.close()
   "
   ```
   - [ ] Draft record exists in database
   - [ ] Draft ID matches what was displayed
   - [ ] Subject line is correct
   - [ ] Thread ID is set (even if "unknown")
   - [ ] Created timestamp is present

3. **Create Reminder and Verify**
   ```bash
   uv run main.py
   ```
   - Select Example 1 (or any with reminder_tool)
   - Note the reminder ID from the output

4. **Verify Reminder in Database**
   ```bash
   # List all reminders
   uv run python -c "
   from utils.artifacts_db import ArtifactsDB
   db = ArtifactsDB()
   reminders = db.get_reminders_by_thread('unknown')
   print(f'✓ Found {len(reminders)} reminder(s) in database')
   for reminder in reminders:
       print(f'  - ID {reminder[\"id\"]}: {reminder[\"content\"]} (status: {reminder[\"status\"]})')
   "
   
   # Get specific reminder by ID (replace 1 with actual reminder ID)
   uv run python -c "
   from utils.artifacts_db import ArtifactsDB
   db = ArtifactsDB()
   reminder = db.get_reminder(1)
   if reminder:
       print(f'✓ Reminder ID 1 details:')
       print(f'  Content: {reminder[\"content\"]}')
       print(f'  Status: {reminder[\"status\"]}')
       print(f'  Thread ID: {reminder[\"thread_id\"]}')
       print(f'  Created: {reminder[\"created_at\"]}')
       if reminder.get('due_date'):
           print(f'  Due: {reminder[\"due_date\"]}')
   else:
       print('✗ Reminder ID 1 not found')
   "
   ```
   - [ ] Reminder record exists in database
   - [ ] Reminder ID matches what was displayed
   - [ ] Content is correct
   - [ ] Status is "pending" (default)
   - [ ] Thread ID is set

5. **Verify Database Schema**
   ```bash
   uv run python -c "
   import sqlite3
   conn = sqlite3.connect('data/artifacts.db')
   cursor = conn.cursor()
   
   # Check tables exist
   cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")
   tables = [row[0] for row in cursor.fetchall()]
   print(f'✓ Tables: {tables}')
   assert 'drafts' in tables
   assert 'reminders' in tables
   
   # Check indexes exist
   cursor.execute(\"SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'\")
   indexes = [row[0] for row in cursor.fetchall()]
   print(f'✓ Indexes: {len(indexes)} found')
   
   conn.close()
   print('✓ Database schema verified')
   "
   ```
   - [ ] Both `drafts` and `reminders` tables exist
   - [ ] Indexes are created

### Expected Result
✅ **PASS**: All artifacts stored in database, schema correct, records queryable

---

## Test 8: Persistence Test

### Objective
Verify that indexed drafts persist across CLI sessions.

### Steps

1. **Run First Session**
   ```bash
   uv run main.py
   ```
   - Select Example 15 (creates and searches for draft)
   - Note the draft ID created (e.g., "✓ Email draft created (ID: 1)")
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
   - [ ] Artifacts database persisted data across sessions
   - [ ] Metadata intact

5. **Verify Database Persistence**
   ```bash
   # Check artifacts database exists and contains data
   ls -la data/artifacts.db
   # Should show database file

   # Query database directly - count all drafts
   uv run python -c "
   from utils.artifacts_db import ArtifactsDB
   db = ArtifactsDB()
   drafts = db.get_drafts_by_thread('unknown')
   print(f'✓ Found {len(drafts)} draft(s) in database')
   if drafts:
       print('  Latest drafts:')
       for d in drafts[:3]:
           print(f'    - ID {d[\"id\"]}: {d[\"subject\"]} ({d[\"created_at\"]})')
   "
   
   # Check database file size
   du -sh data/artifacts.db
   # Should show non-zero size
   
   # Verify specific draft from previous session still exists
   uv run python -c "
   from utils.artifacts_db import ArtifactsDB
   db = ArtifactsDB()
   # Replace 1 with the draft ID from session 1
   draft = db.get_draft(1)
   if draft:
       print(f'✓ Draft from session 1 still exists: ID {draft[\"id\"]} - {draft[\"subject\"]}')
   else:
       print('✗ Draft from session 1 not found')
   "
   ```
   - [ ] Database file exists
   - [ ] Contains draft records from previous session

6. **Verify ChromaDB Files**
   ```bash
   # Check ChromaDB directory exists
   ls -la data/chromadb/
   # Should show database files (chroma.sqlite3, etc.)

   # Check file sizes increased
   du -sh data/chromadb/
   # Should show non-zero size
   
   # Verify ChromaDB collection persisted and has documents
   uv run python -c "
   from utils.chromadb_manager import ChromaDBManager
   manager = ChromaDBManager()
   collection = manager.get_collection()
   if collection:
       count = manager.get_draft_count()
       print(f'✓ ChromaDB collection persisted: email_drafts')
       print(f'  Total indexed documents: {count}')
       
       # Get sample documents to verify data
       if count > 0:
           results = collection.get(limit=min(3, count))
           print(f'  Sample document IDs: {results[\"ids\"]}')
           if results.get('metadatas'):
               print(f'  Sample metadata:')
               for i, meta in enumerate(results['metadatas'][:2]):
                   print(f'    - {results[\"ids\"][i]}: draft_id={meta.get(\"draft_id\")}, subject={meta.get(\"subject\", \"N/A\")[:50]}')
   else:
       print('✗ ChromaDB collection not found')
   "
   ```
   - [ ] Directory exists
   - [ ] Contains database files
   - [ ] Files are not empty
   - [ ] Collection contains indexed documents from previous session

### Expected Output
```
[Session 1]
✓ Email draft created (ID: 1): 'Re: Q4 financial planning and budgets'

[Session 2, Example 14]
📧 Search Results for: 'budget approval'
Found 1 matching drafts:
  1. Subject: Re: Q4 financial planning and budgets
     📅 2025-12-16 12:05:30
     🆔 Draft ID: 1
     ✅ Relevance: 92.3%
```

### Expected Result
✅ **PASS**: Data persists across sessions, ChromaDB successfully stores and retrieves indexed drafts

---

## Test 9: Backward Compatibility Check

### Objective
Verify Phase 2 changes don't break existing Phase 1 functionality.

### Steps

1. **Test Reminder Tool**
   ```bash
   uv run main.py
   ```
   Select Example 1 (or any with reminder_tool)
   - [ ] Reminder tool executes
   - [ ] Result shows: "✓ Reminder created (ID: [id]): '[content]'"
   - [ ] Reminder record created in artifacts database
   - [ ] No errors related to Phase 2 components
   - [ ] Verify database: `uv run python -c "from utils.artifacts_db import ArtifactsDB; db = ArtifactsDB(); reminders = db.get_reminders_by_thread('unknown'); print(f'✓ Found {len(reminders)} reminder(s)')"`

2. **Test Drafting Tool (Without Search)**
   ```bash
   uv run main.py
   ```
   Select Example 2 (or 19-20 with single drafting_tool)
   - [ ] Draft created successfully
   - [ ] Result shows: "✓ Email draft created (ID: [id]): '[subject]'"
   - [ ] Draft record created in artifacts database
   - [ ] Auto-indexing happens silently (no visible errors)
   - [ ] Drafting completes as expected
   - [ ] Verify database: `uv run python -c "from utils.artifacts_db import ArtifactsDB; db = ArtifactsDB(); drafts = db.get_drafts_by_thread('unknown'); print(f'✓ Found {len(drafts)} draft(s)')"`

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

## Test 10: Error Handling & Edge Cases

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

2. **Database Connection Issues**
   ```bash
   # Test with database locked or missing
   chmod 000 data/artifacts.db 2>/dev/null || true
   uv run main.py
   > 15
   ```
   - [ ] Handles database errors gracefully
   - [ ] No unhandled exceptions
   - [ ] Error message helpful
   ```bash
   # Restore database access
   chmod 644 data/artifacts.db 2>/dev/null || true
   ```

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
# Check ChromaDB size
du -sh data/chromadb/
# Expected: < 50 MB for reasonable number of drafts

# Check artifacts database size
du -sh data/artifacts.db
# Expected: < 10 MB for reasonable number of artifacts
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
| Test 7: Artifacts Database | ✅ / ❌ | ___ min | |
| Test 8: Persistence | ✅ / ❌ | ___ min | |
| Test 9: Backward Compatibility | ✅ / ❌ | ___ min | |
| Test 10: Error Handling | ✅ / ❌ | ___ min | |

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

## Database Query Reference

### Quick Reference Commands

#### Artifacts Database (SQLite) Queries

**List all drafts:**
```bash
uv run python -c "
from utils.artifacts_db import ArtifactsDB
db = ArtifactsDB()
drafts = db.get_drafts_by_thread('unknown')
print(f'Total drafts: {len(drafts)}')
for d in drafts:
    print(f'  ID {d[\"id\"]}: {d[\"subject\"]} ({d[\"created_at\"]})')
"
```

**Get specific draft by ID:**
```bash
# Replace 1 with actual draft ID
uv run python -c "
from utils.artifacts_db import ArtifactsDB
db = ArtifactsDB()
draft = db.get_draft(1)
if draft:
    print(f'Draft ID {draft[\"id\"]}:')
    print(f'  Subject: {draft[\"subject\"]}')
    print(f'  Thread ID: {draft[\"thread_id\"]}')
    print(f'  Created: {draft[\"created_at\"]}')
    print(f'  Status: {draft[\"status\"]}')
    print(f'  Body length: {len(draft[\"body\"])} chars')
"
```

**List all reminders:**
```bash
uv run python -c "
from utils.artifacts_db import ArtifactsDB
db = ArtifactsDB()
reminders = db.get_reminders_by_thread('unknown')
print(f'Total reminders: {len(reminders)}')
for r in reminders:
    print(f'  ID {r[\"id\"]}: {r[\"content\"][:50]}... (status: {r[\"status\"]})')
"
```

**Get specific reminder by ID:**
```bash
# Replace 1 with actual reminder ID
uv run python -c "
from utils.artifacts_db import ArtifactsDB
db = ArtifactsDB()
reminder = db.get_reminder(1)
if reminder:
    print(f'Reminder ID {reminder[\"id\"]}:')
    print(f'  Content: {reminder[\"content\"]}')
    print(f'  Status: {reminder[\"status\"]}')
    print(f'  Thread ID: {reminder[\"thread_id\"]}')
"
```

**Direct SQL queries:**
```bash
# Count all drafts
uv run python -c "
import sqlite3
conn = sqlite3.connect('data/artifacts.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM drafts')
print(f'Total drafts: {cursor.fetchone()[0]}')
conn.close()
"

# Get drafts with full details
uv run python -c "
import sqlite3
conn = sqlite3.connect('data/artifacts.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute('SELECT id, subject, thread_id, created_at, status FROM drafts ORDER BY created_at DESC LIMIT 10')
for row in cursor.fetchall():
    print(f'ID {row[\"id\"]}: {row[\"subject\"]} (thread: {row[\"thread_id\"]}, {row[\"created_at\"]})')
conn.close()
"
```

#### ChromaDB Queries

**Check collection exists and get document count:**
```bash
uv run python -c "
from utils.chromadb_manager import ChromaDBManager
manager = ChromaDBManager()
collection = manager.get_collection()
if collection:
    count = manager.get_draft_count()
    print(f'✓ Collection: email_drafts')
    print(f'  Total documents: {count}')
else:
    print('✗ Collection not found')
"
```

**Get sample documents from ChromaDB:**
```bash
uv run python -c "
from utils.chromadb_manager import ChromaDBManager
manager = ChromaDBManager()
collection = manager.get_collection()
if collection:
    count = manager.get_draft_count()
    if count > 0:
        results = collection.get(limit=min(5, count))
        print(f'Sample documents ({len(results[\"ids\"])}):')
        for i, doc_id in enumerate(results['ids']):
            meta = results['metadatas'][i] if results.get('metadatas') else {}
            print(f'  - {doc_id}: draft_id={meta.get(\"draft_id\")}, subject={meta.get(\"subject\", \"N/A\")[:50]}')
    else:
        print('No documents in collection')
"
```

**Search ChromaDB directly (test semantic search):**
```bash
uv run python -c "
from utils.chromadb_manager import ChromaDBManager
manager = ChromaDBManager()
results = manager.search_drafts('budget approval', n_results=3)
print(f'Search results: {len(results)}')
for r in results:
    print(f'  - ID: {r[\"id\"]}')
    print(f'    Distance: {r[\"distance\"]:.4f}')
    if r.get('metadata'):
        print(f'    Draft ID: {r[\"metadata\"].get(\"draft_id\")}')
        print(f'    Subject: {r[\"metadata\"].get(\"subject\", \"N/A\")}')
"
```

**Check ChromaDB file structure:**
```bash
# List ChromaDB files
ls -la data/chromadb/

# Check file sizes
du -sh data/chromadb/*

# Check if collection database exists
ls -la data/chromadb/chroma.sqlite3
```

#### Combined Verification

**Verify draft exists in both databases:**
```bash
# Replace 1 with actual draft ID
uv run python -c "
from utils.artifacts_db import ArtifactsDB
from utils.chromadb_manager import ChromaDBManager

draft_id = 1

# Check artifacts database
db = ArtifactsDB()
draft = db.get_draft(draft_id)
if draft:
    print(f'✓ Draft {draft_id} in artifacts DB: {draft[\"subject\"]}')
else:
    print(f'✗ Draft {draft_id} NOT in artifacts DB')

# Check ChromaDB
manager = ChromaDBManager()
collection = manager.get_collection()
if collection:
    # Search for draft by metadata
    results = collection.get(where={'draft_id': str(draft_id)}, limit=1)
    if results['ids']:
        print(f'✓ Draft {draft_id} indexed in ChromaDB: {results[\"ids\"][0]}')
    else:
        print(f'✗ Draft {draft_id} NOT indexed in ChromaDB')
"
```

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
**Cause:** Indexing failed silently or database issue
**Solution:**
```bash
# Check if drafts exist in artifacts database
uv run python -c "
from utils.artifacts_db import ArtifactsDB
db = ArtifactsDB()
drafts = db.get_drafts_by_thread('unknown')
print(f'Drafts in artifacts DB: {len(drafts)}')
for d in drafts:
    print(f'  - ID {d[\"id\"]}: {d[\"subject\"]}')
"

# Check ChromaDB collection and document count
uv run python -c "
from utils.chromadb_manager import ChromaDBManager
manager = ChromaDBManager()
collection = manager.get_collection()
if collection:
    count = manager.get_draft_count()
    print(f'Documents in ChromaDB: {count}')
    if count > 0:
        # Get sample to verify indexing
        results = collection.get(limit=1)
        print(f'Sample document ID: {results[\"ids\"][0]}')
else:
    print('ChromaDB collection not initialized')
"

# Check ChromaDB directory
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

- [x] ✅ All 10 core tests pass
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
  - Artifacts Database: `utils/artifacts_db.py`
  - Examples: `data/examples.yaml`
  - Loader: `utils/example_loader.py`

---

**Last Updated:** 2025-12-16
**Phase:** 2 (Updated for Artifacts Database Migration)
**Status:** Ready for Testing
