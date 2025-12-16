# Artifacts Database Migration Plan

**Issue:** [#2 - Migrate tool artifacts from file storage to database](https://github.com/amite/personal-triage-agent/issues/2)  
**Status:** 📋 Planning  
**Priority:** High  
**Related:** Phase 2 (ChromaDB), Phase 3 (Context-Aware Triage)

---

## Executive Summary

Migrate tool outputs (reminders and drafts) from file-based storage (`inbox/reminders/`, `inbox/drafts/`) to a structured SQLite database (`artifacts.db`). This eliminates regex parsing, enables queryability, links artifacts to workflow executions, and enables future Phase 3+ features.

### Key Benefits

- ✅ **Eliminates regex parsing** - Structured return values instead of string parsing
- ✅ **Queryable** - SQL queries for drafts/reminders by date, status, thread_id
- ✅ **Linked to workflows** - Artifacts tied to `thread_id` and `checkpoint_id`
- ✅ **Updatable** - Mark drafts as sent, snooze reminders without file manipulation
- ✅ **Single source of truth** - Database as primary storage, files optional
- ✅ **Future-proof** - Enables Phase 3 context-aware triage and Phase 4 reporting

---

## Problem Statement

### Current Limitations

1. **File-based storage** (`inbox/reminders/`, `inbox/drafts/`)
   - No structured querying (can't find "all reminders from Dec 15")
   - Scattered data not linked to execution context
   - Hard to update state (mark draft as sent, snooze reminder)
   - Unindexed (full directory scan needed)
   - Can't answer "what artifacts were created during execution X?"

2. **Regex parsing required** (in `main.py` line 148)
   - Brittle: breaks if message format changes
   - Extracts file path from string: `"✓ Email draft saved to inbox/drafts/draft_20251216_143740_Draft an email to stakeholders.txt about: '...'"`
   - Error-prone: filename parsing, file I/O for indexing

3. **No workflow linkage**
   - Can't trace which checkpoint created which draft
   - Can't query artifacts by thread_id
   - No relationship between workflow state and tool outputs

---

## Proposed Solution

### Database Schema

Create `data/artifacts.db` with two tables:

#### Reminders Table

```sql
CREATE TABLE reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id TEXT NOT NULL,                    -- Link to execution
    checkpoint_id TEXT,                          -- Which checkpoint created this
    content TEXT NOT NULL,                      -- Reminder text
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    due_date TIMESTAMP,                         -- Optional due date
    status TEXT DEFAULT 'pending',              -- 'pending', 'snoozed', 'completed'
    snoozed_until TIMESTAMP,                    -- When to show again if snoozed
    FOREIGN KEY (thread_id) REFERENCES checkpoints(thread_id)
);

CREATE INDEX idx_reminders_thread_id ON reminders(thread_id);
CREATE INDEX idx_reminders_status ON reminders(status);
CREATE INDEX idx_reminders_created_at ON reminders(created_at);
```

#### Drafts Table

```sql
CREATE TABLE drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id TEXT NOT NULL,                    -- Link to execution
    checkpoint_id TEXT,                          -- Which checkpoint created this
    subject TEXT,                                -- Email subject line
    body TEXT NOT NULL,                          -- Full email body/content
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'draft',                -- 'draft', 'sent', 'archived'
    tags TEXT,                                   -- JSON array: ["budget", "client"]
    FOREIGN KEY (thread_id) REFERENCES checkpoints(thread_id)
);

CREATE INDEX idx_drafts_thread_id ON drafts(thread_id);
CREATE INDEX idx_drafts_status ON drafts(status);
CREATE INDEX idx_drafts_created_at ON drafts(created_at);
CREATE INDEX idx_drafts_subject ON drafts(subject);
```

---

## Implementation Strategy

### Phase 1: Dual-Write (Backward Compatible) ⚠️

**Goal:** Add database writes alongside existing file writes. No breaking changes.

#### Step 1.1: Create Artifacts Database Module

**File:** `utils/artifacts_db.py` (new)

```python
"""SQLite database for tool artifacts (reminders and drafts)."""

import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

class ArtifactsDB:
    """Manages artifacts database operations."""
    
    def __init__(self, db_path: str = "data/artifacts.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Reminders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT NOT NULL,
                checkpoint_id TEXT,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                due_date TIMESTAMP,
                status TEXT DEFAULT 'pending',
                snoozed_until TIMESTAMP
            )
        """)
        
        # Drafts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT NOT NULL,
                checkpoint_id TEXT,
                subject TEXT,
                body TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'draft',
                tags TEXT
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reminders_thread_id ON reminders(thread_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reminders_status ON reminders(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_drafts_thread_id ON drafts(thread_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_drafts_status ON drafts(status)")
        
        conn.commit()
        conn.close()
    
    def create_reminder(
        self, 
        thread_id: str, 
        content: str, 
        checkpoint_id: Optional[str] = None,
        due_date: Optional[datetime] = None
    ) -> int:
        """Create a reminder record.
        
        Returns:
            Reminder ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO reminders (thread_id, checkpoint_id, content, due_date)
            VALUES (?, ?, ?, ?)
        """, (thread_id, checkpoint_id, content, due_date))
        
        reminder_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return reminder_id
    
    def create_draft(
        self,
        thread_id: str,
        body: str,
        subject: Optional[str] = None,
        checkpoint_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> int:
        """Create a draft record.
        
        Returns:
            Draft ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        tags_json = json.dumps(tags) if tags else None
        
        cursor.execute("""
            INSERT INTO drafts (thread_id, checkpoint_id, subject, body, tags)
            VALUES (?, ?, ?, ?, ?)
        """, (thread_id, checkpoint_id, subject, body, tags_json))
        
        draft_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return draft_id
    
    def get_draft(self, draft_id: int) -> Optional[Dict[str, Any]]:
        """Get draft by ID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM drafts WHERE id = ?", (draft_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            draft = dict(row)
            if draft.get("tags"):
                draft["tags"] = json.loads(draft["tags"])
            return draft
        return None
    
    def get_reminders_by_thread(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get all reminders for a thread."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM reminders WHERE thread_id = ? ORDER BY created_at DESC", (thread_id,))
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_drafts_by_thread(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get all drafts for a thread."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM drafts WHERE thread_id = ? ORDER BY created_at DESC", (thread_id,))
        rows = cursor.fetchall()
        conn.close()
        
        drafts = []
        for row in rows:
            draft = dict(row)
            if draft.get("tags"):
                draft["tags"] = json.loads(draft["tags"])
            drafts.append(draft)
        return drafts
```

#### Step 1.2: Update ReminderTool

**File:** `tools/reminder_tool.py`

**Changes:**
- Add `artifacts_db` parameter or singleton access
- Write to database AND file (dual-write)
- Return structured data: `{"success": True, "reminder_id": id, "message": "..."}`

```python
@staticmethod
def execute(
    content: str, 
    thread_id: Optional[str] = None,
    checkpoint_id: Optional[str] = None
) -> dict:
    """Execute reminder tool with database storage."""
    from utils.artifacts_db import ArtifactsDB
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    reminder_text = f"[{timestamp}] REMINDER: {content}\n"
    
    # Create database record
    db = ArtifactsDB()
    reminder_id = db.create_reminder(
        thread_id=thread_id or "unknown",
        content=content,
        checkpoint_id=checkpoint_id
    )
    
    # Still write to file (backward compatibility)
    try:
        import os
        os.makedirs("inbox/reminders", exist_ok=True)
        safe_content = re.sub(r'[^\w\s-]', '', content[:30]).strip()
        filename = f"inbox/reminders/reminder_{file_timestamp}_{safe_content}.txt"
        with open(filename, "w") as f:
            f.write(reminder_text)
    except Exception as e:
        # Log but don't fail
        logging.warning(f"Failed to write reminder file: {e}")
    
    return {
        "success": True,
        "reminder_id": reminder_id,
        "message": f"✓ Reminder created (ID: {reminder_id}): '{content}'"
    }
```

#### Step 1.3: Update DraftingTool

**File:** `tools/drafting_tool.py`

**Changes:**
- Add `thread_id` and `checkpoint_id` parameters
- Write to database AND file (dual-write)
- Return structured data: `{"success": True, "draft_id": id, "subject": "...", "message": "..."}`

```python
@staticmethod
def execute(
    content: str, 
    llm_client: Optional[LLMClientBase] = None,
    thread_id: Optional[str] = None,
    checkpoint_id: Optional[str] = None
) -> dict:
    """Execute drafting tool with database storage."""
    from utils.artifacts_db import ArtifactsDB
    
    # Generate draft content (existing logic)
    email_body = generate_email_body(content, llm_client)
    subject = extract_subject(content)  # Extract from content or generate
    
    draft_body = format_draft_email(subject, email_body)
    
    # Create database record
    db = ArtifactsDB()
    draft_id = db.create_draft(
        thread_id=thread_id or "unknown",
        body=draft_body,
        subject=subject,
        checkpoint_id=checkpoint_id
    )
    
    # Still write to file (backward compatibility)
    try:
        import os
        os.makedirs("inbox/drafts", exist_ok=True)
        file_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_content = re.sub(r'[^\w\s-]', '', content[:30]).strip()
        filename = f"inbox/drafts/draft_{file_timestamp}_{safe_content}.txt"
        with open(filename, "w") as f:
            f.write(draft_body)
    except Exception as e:
        logging.warning(f"Failed to write draft file: {e}")
    
    return {
        "success": True,
        "draft_id": draft_id,
        "subject": subject,
        "message": f"✓ Email draft created (ID: {draft_id}): '{subject}'"
    }
```

#### Step 1.4: Update main.py - Remove Regex Parsing

**File:** `main.py` (lines 143-160)

**Before (regex parsing):**
```python
# Index draft if drafting_tool was executed
if tool_name == "drafting_tool" and "✓" in result:
    try:
        # Extract file path from result string
        file_match = regex.search(r"(inbox/drafts/draft_[^\.]+\.txt)", result)
        if file_match:
            file_path = file_match.group(1)
            indexer = DraftIndexer()
            indexer.index_draft_file(file_path, thread_id=state.get("thread_id"))
    except Exception as e:
        logging.warning(f"Draft indexing failed: {e}")
```

**After (structured data):**
```python
# Index draft if drafting_tool was executed
if tool_name == "drafting_tool" and isinstance(result, dict) and result.get("success"):
    try:
        draft_id = result["draft_id"]
        thread_id = state.get("thread_id", "unknown")
        checkpoint_id = state.get("current_checkpoint_id")  # If available
        
        indexer = DraftIndexer()
        indexer.index_draft_by_id(draft_id, thread_id=thread_id)
    except Exception as e:
        logging.warning(f"Draft indexing failed: {e}")
```

#### Step 1.5: Update DraftIndexer

**File:** `tools/draft_indexer.py`

**Add new method:**
```python
def index_draft_by_id(
    self, 
    draft_id: int, 
    thread_id: str, 
    checkpoint_id: Optional[str] = None
) -> bool:
    """Index a draft from database by ID.
    
    Args:
        draft_id: Draft ID from artifacts database
        thread_id: Thread ID for checkpoint lookup
        checkpoint_id: Optional specific checkpoint ID
    
    Returns:
        True if successful, False otherwise
    """
    try:
        from utils.artifacts_db import ArtifactsDB
        
        # Get draft from database
        db = ArtifactsDB()
        draft = db.get_draft(draft_id)
        
        if not draft:
            logger.error(f"Draft not found: {draft_id}")
            return False
        
        # Extract metadata
        metadata = {
            "draft_id": draft_id,
            "subject": draft.get("subject", ""),
            "timestamp": draft["created_at"],
            "thread_id": thread_id,
        }
        
        # Get checkpoint context
        checkpoint_metadata = self._get_checkpoint_metadata(thread_id, checkpoint_id)
        merged_metadata = {**metadata, **checkpoint_metadata}
        
        # Index in ChromaDB
        doc_id = self.chromadb.index_draft(draft["body"], merged_metadata)
        if doc_id:
            logger.info(f"Successfully indexed draft ID {draft_id}")
            return True
        else:
            logger.error(f"Failed to index draft ID {draft_id} in ChromaDB")
            return False
            
    except Exception as e:
        logger.error(f"Exception while indexing draft {draft_id}: {e}")
        return False
```

**Keep old method for backward compatibility:**
```python
def index_draft_file(...) -> bool:
    """Legacy method - kept for backward compatibility during migration."""
    # Existing implementation
```

#### Step 1.6: Update tool_execution_node to Pass thread_id

**File:** `main.py` (tool_execution_node)

**Changes:**
- Pass `thread_id` and `checkpoint_id` to tools
- Handle structured return values

```python
def tool_execution_node(state: AgentState) -> AgentState:
    # ... existing code ...
    
    thread_id = state.get("thread_id", "unknown")
    # Get current checkpoint_id if available from LangGraph state
    
    # Execute tool
    if tool_name == "drafting_tool":
        llm_agent = LLMDraftingAgent()
        result = llm_agent.execute(
            content, 
            thread_id=thread_id,
            checkpoint_id=current_checkpoint_id  # If available
        )
    elif tool_name == "reminder_tool":
        result = tool_class.execute(
            content,
            thread_id=thread_id,
            checkpoint_id=current_checkpoint_id
        )
    else:
        result = tool_class.execute(content)
    
    # Handle both string (legacy) and dict (new) return values
    if isinstance(result, dict):
        # New structured format
        display_result = result.get("message", str(result))
        state["results"][f"{tool_name}_{state['iteration']}"] = display_result
    else:
        # Legacy string format
        state["results"][f"{tool_name}_{state['iteration']}"] = result
    
    # ... rest of code ...
```

#### Step 1.7: Update LLMDraftingAgent

**File:** `agents/llm_drafting_agent.py`

**Changes:**
- Pass through `thread_id` and `checkpoint_id` parameters

```python
def execute(
    self, 
    content: str,
    thread_id: Optional[str] = None,
    checkpoint_id: Optional[str] = None
) -> dict:
    return DraftingTool.execute(
        content, 
        self.llm,
        thread_id=thread_id,
        checkpoint_id=checkpoint_id
    )
```

---

### Phase 2: Migration Complete ✅

**Goal:** Database becomes primary storage. Files optional/deprecated.

#### Step 2.1: Update Documentation

- Document new database schema
- Update tool documentation to show database storage
- Add migration guide for existing file-based artifacts

#### Step 2.2: Add Artifact Query Utilities

**File:** `utils/inspect_artifacts.py` (new)

```python
"""Inspect artifacts database."""

from utils.artifacts_db import ArtifactsDB
from rich.console import Console
from rich.table import Table

def show_artifacts_for_thread(thread_id: str):
    """Display all artifacts for a thread."""
    db = ArtifactsDB()
    
    reminders = db.get_reminders_by_thread(thread_id)
    drafts = db.get_drafts_by_thread(thread_id)
    
    # Display in rich table format
    # ...
```

#### Step 2.3: Update inspect_checkpoints.py

**File:** `utils/inspect_checkpoints.py`

**Add:**
- Show artifacts linked to each checkpoint
- Display draft/reminder counts per thread

---

### Phase 3: Cleanup 🧹

**Goal:** Remove file writing entirely (optional, user preference).

#### Step 3.1: Make File Writing Optional

Add configuration flag:
```python
WRITE_ARTIFACT_FILES = os.getenv("WRITE_ARTIFACT_FILES", "false").lower() == "true"
```

#### Step 3.2: Remove File Writing Code

- Remove file I/O from `DraftingTool` and `ReminderTool`
- Update documentation
- Add migration script for existing files → database

---

## Migration Checklist

### Phase 1: Dual-Write (Backward Compatible)

- [ ] Create `utils/artifacts_db.py` with schema
- [ ] Update `ReminderTool.execute()` to write to database + file
- [ ] Update `DraftingTool.execute()` to write to database + file
- [ ] Update `LLMDraftingAgent.execute()` to pass thread_id
- [ ] Update `main.py` tool_execution_node to pass thread_id/checkpoint_id
- [ ] Update `main.py` to use structured return values (remove regex)
- [ ] Add `DraftIndexer.index_draft_by_id()` method
- [ ] Update `main.py` indexing code to use draft_id
- [ ] Test: Verify database writes work
- [ ] Test: Verify file writes still work (backward compatibility)
- [ ] Test: Verify ChromaDB indexing works with database records
- [ ] Test: Verify search_drafts_tool still works

### Phase 2: Migration Complete

- [ ] Update documentation
- [ ] Create `utils/inspect_artifacts.py` utility
- [ ] Update `inspect_checkpoints.py` to show artifacts
- [ ] Add migration script for existing files → database
- [ ] Test: Verify all queries work
- [ ] Test: Verify artifact linking to checkpoints

### Phase 3: Cleanup (Optional)

- [ ] Add configuration flag for file writing
- [ ] Remove file writing code (or make optional)
- [ ] Update documentation
- [ ] Test: Verify system works without file writes

---

## Testing Strategy

### Unit Tests

1. **ArtifactsDB Tests**
   - Create reminder → verify in database
   - Create draft → verify in database
   - Query by thread_id → verify results
   - Update status → verify changes

2. **Tool Tests**
   - ReminderTool returns structured data
   - DraftingTool returns structured data
   - Both write to database AND file (Phase 1)

3. **Indexing Tests**
   - `index_draft_by_id()` retrieves from database
   - ChromaDB indexing works with database records
   - Metadata includes draft_id

### Integration Tests

1. **End-to-End Workflow**
   - Create draft → verify in database → verify indexed in ChromaDB
   - Create reminder → verify in database
   - Search drafts → verify finds database records

2. **Backward Compatibility**
   - Old file-based code still works
   - New database code works
   - Both coexist during Phase 1

### Manual Testing

1. Run example requests
2. Verify `data/artifacts.db` created
3. Query database directly: `SELECT * FROM drafts;`
4. Verify ChromaDB search finds database records
5. Verify files still created (Phase 1)

---

## Rollback Plan

If issues arise:

1. **Phase 1:** File writes still work, can disable database writes
2. **Phase 2:** Can re-enable file writes if needed
3. **Database:** Can export to files if needed

---

## Success Criteria

- ✅ `artifacts.db` created with reminders and drafts tables
- ✅ `ReminderTool` and `DraftingTool` write to database
- ✅ Artifacts linked to `thread_id` and `checkpoint_id`
- ✅ Regex parsing removed from `main.py`
- ✅ ChromaDB indexing works with database records
- ✅ File-based output still works (Phase 1)
- ✅ Tests verify database state matches expectations
- ✅ Inspection utility shows artifacts per thread

---

## Related Work

- **Phase 2 (ChromaDB):** Already uses database for semantic search
- **Phase 3 (Context-Aware Triage):** Will query artifacts database for history
- **Phase 4 (Historical Search):** Will use artifacts database for reporting

---

## Timeline Estimate

- **Phase 1:** 2-3 days (dual-write implementation)
- **Phase 2:** 1-2 days (documentation, utilities)
- **Phase 3:** 1 day (cleanup, optional)

**Total:** ~4-6 days

---

## Notes

- Database location: `data/artifacts.db` (alongside `checkpoints.db`)
- Thread ID comes from LangGraph state (already available)
- Checkpoint ID may need to be extracted from LangGraph state
- Consider adding foreign key constraints (if SQLite supports)
- Consider adding database migrations for schema changes

---

**Last Updated:** 2025-12-16  
**Status:** Ready for Implementation

