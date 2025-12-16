import sys
from utils.artifacts_db import ArtifactsDB

# 1. Get the draft_id from command-line arguments
try:
    draft_id = int(sys.argv[1])
except (IndexError, ValueError):
    print("Error: Please provide a valid integer draft ID.")
    sys.exit(1)

# 2. Run the database logic
db = ArtifactsDB()
draft = db.get_draft(draft_id)

# 3. Print the result
draft_id_str = str(draft_id)

if draft:
    print("✓ Draft ID {} found: {}"
          .format(draft_id_str, draft["subject"]))
    print("  Thread ID: {}".format(draft["thread_id"]))
    print("  Created: {}".format(draft["created_at"]))
else:
    print("✗ Draft ID {} not found".format(draft_id_str))

