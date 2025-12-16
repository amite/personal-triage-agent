# Cursor Commands

This directory contains custom Cursor commands for the project.

## Available Commands

### Git: Add, Commit & Push

**File**: `git-add-commit-push.sh`

**Description**: Automatically adds all untracked and modified files, commits them with a timestamped message, and pushes to the current branch.

**Usage**: 
- Run from Cursor's command palette (Cmd/Ctrl+Shift+P) and search for "Git: Add, Commit & Push"
- Or execute directly: `bash .cursor/commands/git-add-commit-push.sh`

**What it does**:
1. Checks for any changes (untracked, modified, or deleted files)
2. If changes exist, stages all files (`git add -A`)
3. Commits with a timestamped message
4. Pushes to the remote repository on the current branch

**Safety**: 
- Only runs if there are actual changes
- Shows what will be committed before proceeding
- Uses the current branch (won't push to wrong branch)

