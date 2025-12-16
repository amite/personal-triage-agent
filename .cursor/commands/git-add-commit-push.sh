#!/bin/bash
# Cursor command: Add, commit, and push untracked/modified changes

set -e

# Get the current branch name
CURRENT_BRANCH=$(git branch --show-current)

# Check if there are any changes (untracked, modified, or staged)
if [ -z "$(git status --porcelain)" ]; then
    echo "No changes to commit. Working directory is clean."
    exit 0
fi

# Show what will be committed
echo "Changes detected:"
git status --short

# Add all changes (untracked, modified, deleted)
git add -A

# Generate commit message with timestamp
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
COMMIT_MSG="Auto-commit: $(date +"%Y-%m-%d %H:%M:%S")"

# Count changes for better message
STAGED_COUNT=$(git diff --cached --numstat | wc -l)
if [ "$STAGED_COUNT" -gt 0 ]; then
    COMMIT_MSG="Update: $STAGED_COUNT file(s) changed - $TIMESTAMP"
fi

# Commit changes
git commit -m "$COMMIT_MSG"

# Push to remote (current branch)
echo "Pushing to origin/$CURRENT_BRANCH..."
git push origin "$CURRENT_BRANCH"

echo "✓ Successfully added, committed, and pushed changes to $CURRENT_BRANCH"

