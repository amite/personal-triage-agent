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
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reminders_created_at ON reminders(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_drafts_thread_id ON drafts(thread_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_drafts_status ON drafts(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_drafts_created_at ON drafts(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_drafts_subject ON drafts(subject)")
        
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
        
        Args:
            thread_id: Thread ID linking to execution
            content: Reminder text content
            checkpoint_id: Optional checkpoint ID
            due_date: Optional due date for reminder
        
        Returns:
            Reminder ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        due_date_str = due_date.isoformat() if due_date else None
        
        cursor.execute("""
            INSERT INTO reminders (thread_id, checkpoint_id, content, due_date)
            VALUES (?, ?, ?, ?)
        """, (thread_id, checkpoint_id, content, due_date_str))
        
        reminder_id = cursor.lastrowid
        if reminder_id is None:
            raise ValueError("Failed to create reminder: no ID returned")
        
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
        
        Args:
            thread_id: Thread ID linking to execution
            body: Full email body/content
            subject: Optional email subject line
            checkpoint_id: Optional checkpoint ID
            tags: Optional list of tags
        
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
        if draft_id is None:
            raise ValueError("Failed to create draft: no ID returned")
        
        conn.commit()
        conn.close()
        return draft_id
    
    def get_draft(self, draft_id: int) -> Optional[Dict[str, Any]]:
        """Get draft by ID.
        
        Args:
            draft_id: Draft ID
        
        Returns:
            Draft dictionary or None if not found
        """
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
    
    def get_reminder(self, reminder_id: int) -> Optional[Dict[str, Any]]:
        """Get reminder by ID.
        
        Args:
            reminder_id: Reminder ID
        
        Returns:
            Reminder dictionary or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM reminders WHERE id = ?", (reminder_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_reminders_by_thread(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get all reminders for a thread.
        
        Args:
            thread_id: Thread ID
        
        Returns:
            List of reminder dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM reminders WHERE thread_id = ? ORDER BY created_at DESC", (thread_id,))
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_drafts_by_thread(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get all drafts for a thread.
        
        Args:
            thread_id: Thread ID
        
        Returns:
            List of draft dictionaries
        """
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

