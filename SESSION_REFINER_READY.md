# Session Refiner Skill - Ready to Use ✓

## What Was Created

Your **Session Refiner skill** has been successfully created in:
```
.claude/skills/session-refiner/
```

This skill automatically extracts key information from long conversations and generates compact markdown summaries to bridge sessions while saving 80,000+ tokens.

---

## File Structure

```
session-refiner/
├── SKILL.md                      # Main skill definition + usage guide
├── scripts/
│   └── extract_session_summary.py # Python extraction script (executable)
├── references/
│   └── workflow.md               # Detailed step-by-step instructions
└── assets/
    └── example-summary.md        # Real-world example output
```

---

## How to Use It (Right Now)

### Method 1: Ask Claude (Easiest)

In any Claude Code chat session, simply ask:

```
Use Session Refiner to create a summary
```

Claude will:
1. Scan your current conversation
2. Extract key decisions, tasks, bugs, and code snippets
3. Generate a markdown summary (2,000-5,000 tokens)
4. You download it

Then:
1. Start a fresh chat session
2. Paste the summary at the top
3. Continue with: "Here's my summary. Now I want to..."
4. You now have ~196,500 tokens available instead of running out

### Method 2: Run Script Locally

For maximum control, export your conversation to text and run:

```bash
python .claude/skills/session-refiner/scripts/extract_session_summary.py \
  conversation.txt \
  --output summary.md \
  --max-tokens 5000
```

---

## What Gets Extracted

| Type | Example | Source |
|------|---------|--------|
| **Tasks** | - [ ] Fix auth bug | TODOs, FIXMEs, checkboxes |
| **Decisions** | Decided to use JWT tokens | "Decided to...", "Using..." |
| **Resolved Bugs** | Fixed CORS error | "Fixed:", "Resolved:" |
| **Code References** | Auth middleware snippet | Triple-backtick blocks |
| **Key Findings** | 15-min token expiry needed | "Important:", "Note:" |

---

## Token Savings Example

**Without Session Refiner:**
- Session 1: Use 120,000 tokens debugging auth
- Session 2: Start with 120,000 tokens in history = only 80,000 new tokens available

**With Session Refiner:**
- Session 1: Use 120,000 tokens debugging auth
- Create summary: 3,500 tokens
- Session 2: Start with ONLY 3,500 tokens in history = 196,500 tokens available
- **Savings: 116,500 tokens!**

---

## When to Use

✓ After completing a major feature
✓ After resolving complex bugs (multi-round debugging)
✓ When switching between different projects/codebases
✓ When Claude warns "conversation is getting long"
✓ At the end of your work day
✓ When conversation exceeds 50,000 tokens

---

## Best Practices

1. **Use clear markers in your chat:**
   - `TODO:` for tasks
   - `Fixed:` for bug resolutions
   - `Decided to...` for decisions
   - `Note:` for findings

2. **Extract at good moments**
   - After finishing a module/feature
   - After debugging completes
   - NOT mid-task (you'll lose context)

3. **Review before pasting**
   - Skim the summary for accuracy
   - Add clarifying notes if needed
   - Delete irrelevant items

4. **Save originals**
   - Keep full conversations as backup
   - Useful for detailed reference later

---

## Files in the Skill

**SKILL.md** (6.3 KB)
- Complete usage instructions
- Two methods (Ask Claude vs. run script)
- Best practices and examples
- Metadata for skill triggering

**scripts/extract_session_summary.py** (8.4 KB)
- Executable Python script
- Parses conversations for key info
- Generates markdown summaries
- Supports `--output` and `--max-tokens` flags

**references/workflow.md** (3.3 KB)
- Step-by-step usage guide
- Detailed workflow explanation
- Token budget breakdown
- Tips and tricks

**assets/example-summary.md** (3.1 KB)
- Real-world example output
- Shows authentication system example
- Demonstrates all extraction types
- Template for your own summaries

---

## Quick Reference

| Action | Command |
|--------|---------|
| Ask Claude to create summary | "Use Session Refiner to create a summary" |
| Run extraction script | `python scripts/extract_session_summary.py conversation.txt` |
| Set output file | `--output my-summary.md` |
| Limit token count | `--max-tokens 3000` |
| Get script help | `--help` |

---

## Next Steps

1. **Try it on your next long session**
   - Chat as normal
   - When you notice the conversation getting long, ask: "Use Session Refiner to create a summary"

2. **Download the generated summary**
   - Review it for accuracy
   - Edit if needed

3. **Start a fresh chat**
   - Paste the summary at the top
   - Continue working with reset context window

4. **Enjoy the token savings!**
   - You'll have 100,000+ more tokens available

---

## Documentation Files

For comprehensive guides, see:
- [SKILL.md](.claude/skills/session-refiner/SKILL.md) - Complete reference
- [workflow.md](.claude/skills/session-refiner/references/workflow.md) - Detailed walkthrough
- [example-summary.md](.claude/skills/session-refiner/assets/example-summary.md) - Real-world example
- [SESSION_REFINER_GUIDE.txt](.claude/skills/SESSION-REFINER-GUIDE.txt) - Full comprehensive guide

---

## Status

✅ **Ready to use immediately**

Just ask Claude in any chat: `"Use Session Refiner to create a summary"`

---

*Created: 2025-12-18*
*Skill: Session Refiner v1.0*
*Purpose: Automatic token optimization for long sessions*
