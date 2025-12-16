"""Test draft indexing manually with verbose logging."""

import logging
import sys

# Set up verbose logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

import sqlite3
from utils.artifacts_db import ArtifactsDB
from tools.draft_indexer import DraftIndexer
from utils.chromadb_manager import ChromaDBManager

def main():
    # Get all drafts from database
    db = ArtifactsDB()
    conn = sqlite3.connect(db.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM drafts ORDER BY created_at DESC")
    rows = cursor.fetchall()
    drafts = [dict(row) for row in rows]
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"Found {len(drafts)} draft(s) in database")
    print(f"{'='*60}\n")
    
    if not drafts:
        print("No drafts found. Create a draft first using the main application.")
        return
    
    # Check current ChromaDB state
    manager = ChromaDBManager()
    initial_count = manager.get_draft_count()
    print(f"ChromaDB documents before indexing: {initial_count}\n")
    
    # Index each draft
    indexer = DraftIndexer()
    
    for draft in drafts:
        draft_id = draft['id']
        subject = draft['subject'][:50]
        
        print(f"\n--- Indexing Draft ID: {draft_id} ---")
        print(f"Subject: {subject}")
        
        success = indexer.index_draft_by_id(
            draft_id=draft_id,
            thread_id=draft.get('thread_id', 'test-thread'),
            checkpoint_id=None
        )
        
        if success:
            print(f"✓ Successfully indexed draft {draft_id}")
        else:
            print(f"✗ Failed to index draft {draft_id}")
    
    # Check final ChromaDB state
    final_count = manager.get_draft_count()
    print(f"\n{'='*60}")
    print(f"ChromaDB documents after indexing: {final_count}")
    print(f"Documents added: {final_count - initial_count}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()

