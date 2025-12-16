import sys
import sqlite3
import json
from utils.artifacts_db import ArtifactsDB

# Parse arguments
output_json = '--json' in sys.argv
thread_id = None
if len(sys.argv) > 1:
    # Filter out --json flag and get thread_id
    args = [arg for arg in sys.argv[1:] if arg != '--json']
    thread_id = args[0] if args else None

# Run the database logic
db = ArtifactsDB()

if thread_id:
    # Filter by specific thread_id
    drafts = db.get_drafts_by_thread(thread_id)
    count_msg = f'✓ Found {len(drafts)} draft(s) for thread_id="{thread_id}"'
else:
    # List all drafts
    conn = sqlite3.connect(db.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM drafts ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    
    drafts = []
    for row in rows:
        draft = dict(row)
        if draft.get("tags"):
            draft["tags"] = json.loads(draft["tags"])
        drafts.append(draft)
    count_msg = f'✓ Found {len(drafts)} draft(s) total'

# Output results
if output_json:
    # Output as JSON for nu to parse
    print(json.dumps(drafts, default=str))
else:
    # Human-readable output
    print(count_msg)
    for d in drafts:
        print(f'  - ID {d["id"]}: {d["subject"]} (thread: {d["thread_id"]})')

