# Session Refiner Workflow

## How to Use This Skill

### Scenario 1: Manual Extraction (Quickest)

When you notice the conversation getting long and want to bridge quickly:

1. Ask Claude: "Use Session Refiner to create a summary for me"
2. Claude will analyze the conversation and generate a compact summary covering:
   - Active tasks (with [ ] checkboxes)
   - Key technical decisions made
   - Resolved bugs/issues
   - Important findings and notes
   - Essential code snippets (not full files)

3. Download the generated markdown summary
4. Start a fresh chat and paste the summary at the top
5. Continue with: "Here's my session summary from before. [paste summary]"

### Scenario 2: Script-Based Extraction (Most Thorough)

For super-long sessions, export conversation text and run the extraction script:

```bash
python extract_session_summary.py conversation.txt --output summary.md --max-tokens 5000
```

The script will:
- Parse TODOs, bug fixes, decisions, code references
- Generate a markdown summary
- Keep everything under your token budget

### When to Trigger This Skill

- **Token warning**: Claude warns the context window is getting full
- **Phase milestone**: You're finishing a major task and starting a new one
- **Long debugging session**: After several rounds of troubleshooting
- **Context reset needed**: Before moving to a different feature/component

## Summary Contents

### Active Tasks (Checkboxes)
```
- [ ] Fix authentication bug
- [ ] Add error handling to API
```

Tasks extracted from:
- Explicit TODOs, FIXMEs in code
- Unchecked items in [ ] lists
- Stated next steps

### Key Decisions
```
- **Using JWT for session tokens** (instead of server-side sessions)
- **PostgreSQL for persistence** (chosen for transaction support)
```

Helps you remember:
- Why certain architectural choices were made
- Alternative approaches that were rejected

### Resolved Issues
```
- Fixed import error in module X by adding __init__.py
- Resolved performance bottleneck by caching responses
```

Quick reference of what was already debugged.

### Code Snippets
Essential code references (not entire files):
- Critical function implementations
- Recently-changed patterns
- Important configuration

Excludes:
- Full file listings
- Boilerplate code
- Existing unchanged code

## Token Budget

A complete summary is designed to fit **2,000–5,000 tokens**, allowing you to:
- Paste it into a fresh chat (0 history tokens)
- Leave 195,000+ tokens for new work
- Reset context and cost

Compare to: Long conversations can consume 50,000+ tokens just in history.

## Tips

1. **Extract early and often**: Don't wait for context to fill. Refresh after major milestones.
2. **Review before pasting**: Skim the summary to ensure accuracy. Edit if needed.
3. **Add context**: If the summary feels incomplete, add a quick note in the markdown.
4. **Save originals**: Keep the full conversation in case you need to reference it later.

## Example Workflow

```
Session 1: Long debugging session (100k+ tokens used)
↓
Ask: "Session Refiner time"
↓
Receive: session-summary.md (3,500 tokens)
↓
Download & save
↓
Start fresh chat, paste summary (3,500 tokens used)
↓
Session 2: Continue with fresh context window
```

Savings: Avoided 100k tokens of history in Session 2, reset your budget.
