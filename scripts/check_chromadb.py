"""Check ChromaDB collection status and document count."""

import sqlite3
from utils.chromadb_manager import ChromaDBManager
from utils.artifacts_db import ArtifactsDB

# Initialize ChromaDB manager
manager = ChromaDBManager()
collection = manager.get_collection()

if collection:
    count = manager.get_draft_count()
    print(f'✓ ChromaDB collection exists: email_drafts')
    print(f'  Documents indexed: {count}')
    
    # Check database for comparison
    db = ArtifactsDB()
    conn = sqlite3.connect(db.db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM drafts')
    db_count = cursor.fetchone()[0]
    conn.close()
    
    print(f'  Drafts in database: {db_count}')
    
    if db_count > 0 and count == 0:
        print(f'\n⚠️  WARNING: {db_count} draft(s) exist in database but are not indexed in ChromaDB')
        print('   This suggests automatic indexing may not be working.')
        print('   Run indexing manually or check logs for indexing errors.')
    elif count > 0:
        # Show sample of indexed documents
        peek = collection.peek(limit=3)
        ids = peek.get('ids', [])
        metadatas = peek.get('metadatas', [])
        if ids:
            print(f'\n  Sample indexed documents: {len(ids)} shown')
            for i, doc_id in enumerate(ids[:3], 1):
                subject = 'No subject'
                try:
                    if metadatas and isinstance(metadatas, list) and i-1 < len(metadatas):
                        meta_item = metadatas[i-1]
                        if isinstance(meta_item, dict):
                            subject = meta_item.get('subject', 'No subject')
                except (IndexError, TypeError, AttributeError):
                    pass
                # Ensure doc_id is a string before slicing
                doc_id_str = str(doc_id) if doc_id else 'unknown'
                subject_str = str(subject) if subject else 'No subject'
                print(f'    {i}. ID: {doc_id_str[:20]}... | Subject: {subject_str[:50]}')
else:
    print('✗ ChromaDB collection not found')

