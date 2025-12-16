# Phase 2: ChromaDB Semantic Search - START HERE

> **Status**: 🟢 Planning Complete - Ready for Implementation
> **Created**: 2025-12-16
> **Estimated Duration**: 4-6 hours

---

## What is Phase 2?

Phase 2 adds **semantic search** for email drafts. Users can search their draft history naturally:

```
User: "Search my drafts about budget approval"
  ↓
AI routes to SearchDraftsTool
  ↓
Semantic search finds all budget-related drafts
  ↓
Display results with timestamps and preview
```

---

## Documentation Structure

All Phase 2 materials are in: `artifacts/wip/issues/phase-2-chromadb/`

### 1. **README.md** - Quick Overview
- Navigation guide
- Architecture highlights  
- Getting started checklist
- **Read this first** (5 min)

### 2. **status.md** - Completion Tracking
- 50+ item checklist
- File modification tracker
- Test result documentation
- **Update this as you code** (reference)

### 3. **progress.md** - Time Tracking
- Timeline of work
- Effort estimates per step
- Next-session preparation
- **Log your progress here** (logging)

### 4. **analysis.md** - Technical Deep-Dive
- Architecture rationale
- Integration points
- Error handling strategy
- Risk assessment
- **Refer to this for questions** (reference)

### 5. **Implementation Plan** - Detailed Code Guide
- Location: `/home/amite/.claude/plans/reactive-mixing-wolf.md`
- 515 lines of implementation detail
- Code templates and examples
- Data flow diagrams
- **Check this for implementation code** (reference)

---

## The 9 Implementation Steps

```
Step 1:  Dependencies & Setup (15 min)       ← START HERE
Step 2:  Embedding Factory (45 min)
Step 3:  ChromaDB Manager (60 min)
Step 4:  Checkpoint Context (30 min)
Step 5:  Draft Indexer (45 min)
Step 6:  Search Tool (30 min)
Step 7:  Workflow Integration (20 min)
Step 8:  Tool Registration (10 min)
Step 9:  Testing & Verification (90 min)     ← COMPREHENSIVE TESTING
                                              ─────────────────────
                                        Total: 4-6 hours
```

---

## Key Technical Decisions (Already Confirmed)

✅ **Embeddings**: Local Sentence Transformers (free) + OpenAI option  
✅ **Indexing**: Real-time (after draft creation)  
✅ **Interface**: Tool integration (natural language routing)  
✅ **Scope**: Email drafts only  

---

## How to Get Started

### Option A: Dive Right In (Recommended)
1. Read: `artifacts/wip/issues/phase-2-chromadb/README.md` (5 min)
2. Check: `/home/amite/.claude/plans/reactive-mixing-wolf.md` (10 min)
3. Start: Step 1 (Dependencies & Setup)
4. Follow: 9 steps in order
5. Track: Update `status.md` as you complete each step

### Option B: Deep Understanding First
1. Read: `artifacts/wip/issues/phase-2-chromadb/analysis.md` (20 min)
2. Review: `/home/amite/.claude/plans/reactive-mixing-wolf.md` (15 min)
3. Then follow Option A above

### Option C: Quick Refresh
1. Check: `artifacts/wip/issues/phase-2-chromadb/progress.md` (current state)
2. Check: `artifacts/wip/issues/phase-2-chromadb/status.md` (what's done)
3. Resume where you left off

---

## Critical Files Overview

### To Create (4 new files, ~290 lines)
```
utils/embedding_factory.py           60 lines
utils/chromadb_manager.py           100 lines
tools/draft_indexer.py               80 lines
tools/search_drafts_tool.py           50 lines
```

### To Modify (5 existing files, ~60 lines changed)
```
main.py                              +15 lines (tool_execution_node)
agents/llm_triage_agent.py            +2 lines (AVAILABLE_TOOLS)
utils/inspect_checkpoints.py         +40 lines (helpers)
pyproject.toml                        +2 lines (dependencies)
.gitignore                            +1 line  (/data/chromadb)
```

---

## Quick Reference: Environment Variables

```bash
# Default: Local embeddings (no API key needed)
EMBEDDING_PROVIDER=local

# Production option: OpenAI embeddings (requires API key)
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

---

## Expected Behavior When Complete

### Current (without Phase 2)
```
User: "Draft email about budget"
  ↓
App creates inbox/drafts/draft_*.txt
  ✅ Done
```

### After Phase 2
```
User: "Draft email about budget"
  ↓
App creates inbox/drafts/draft_*.txt
  ↓
[NEW] Automatically indexed in ChromaDB
  ✓ With metadata (user request, timestamp, subject)
  ✓ Searchable instantly

User: "Search my drafts about budget"
  ↓
[NEW] SearchDraftsTool executes
  ↓
[NEW] Returns 3 matching drafts with previews
  ✓ Timestamp
  ✓ Subject
  ✓ Content snippet
  ✓ File path
```

---

## Success Looks Like

✅ Run: `uv run main.py`  
✅ Create a draft (e.g., "Draft email about quarterly budget")  
✅ Search: "Search my drafts about budget"  
✅ Result: Draft appears in search results with full metadata  

✅ Check: `sqlite3 data/chromadb/...` contains draft  
✅ Verify: Both embeddings and metadata stored correctly  

✅ Test: Works with local embeddings  
✅ Bonus: Can switch to OpenAI with `EMBEDDING_PROVIDER=openai`  

---

## Common Questions

**Q: Where do I start?**
A: Step 1 (Dependencies). Follow the 9 steps in order.

**Q: What if I get stuck?**
A: Check `analysis.md` for architecture, plan document for code examples.

**Q: How long does this take?**
A: 4-6 hours if you follow the steps. Breaks it down nicely.

**Q: Is backward compatibility guaranteed?**
A: Yes - all changes are additive, existing tools unchanged.

**Q: Can I switch embedding models later?**
A: Yes - just set `EMBEDDING_PROVIDER=openai` and restart.

**Q: What if indexing fails?**
A: Logged but doesn't crash - workflow continues, just logs warning.

---

## File Locations Summary

```
📋 PLANNING DOCUMENTS
/home/amite/.claude/plans/reactive-mixing-wolf.md
  └─ 515-line implementation plan with code examples

📁 ISSUE TRACKING
artifacts/wip/issues/phase-2-chromadb/
  ├─ README.md        (navigation guide)
  ├─ status.md        (completion checklist)
  ├─ progress.md      (time tracking)
  └─ analysis.md      (technical deep-dive)

📁 PHASE 1 REFERENCE (for context)
artifacts/wip/issues/phase-1-checkpointer/
  ├─ status.md        (Phase 1 completion)
  ├─ progress.md      (Phase 1 timeline)
  ├─ analysis.md      (Phase 1 architecture)
  └─ checkpointer-COMPLETE.md (summary)

🔄 PHASE 2 CODE LOCATIONS
Source Files to Create:
  utils/embedding_factory.py
  utils/chromadb_manager.py
  tools/draft_indexer.py
  tools/search_drafts_tool.py

Source Files to Modify:
  main.py
  agents/llm_triage_agent.py
  utils/inspect_checkpoints.py
  pyproject.toml
  .gitignore
```

---

## Next Action

**👉 Go to**: `artifacts/wip/issues/phase-2-chromadb/README.md`

**Then**:
1. Read the quick reference
2. Open `/home/amite/.claude/plans/reactive-mixing-wolf.md`
3. Start Step 1: Dependencies & Setup

---

## Quick Links

- [Phase 2 Issue Folder](artifacts/wip/issues/phase-2-chromadb/)
- [Implementation Plan](./home/amite/.claude/plans/reactive-mixing-wolf.md)
- [Phase 1 Reference](artifacts/wip/issues/phase-1-checkpointer/)
- [Project Overview](README.md)

---

**Status**: Ready to code  
**Quality**: Well-planned, architecturally sound  
**When**: Start whenever you're ready  
**Duration**: 4-6 hours  
**Complexity**: Medium (new dependency, checkpoint integration)

Good luck! 🚀
