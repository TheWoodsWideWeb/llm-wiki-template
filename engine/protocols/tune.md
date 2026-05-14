# Protocol: Tune

> Self-improve the engine based on reflections and session analysis. Proposes and applies changes with operator approval.

## Overview

- **Runs:** Operator-invoked (`/tune`), typically after reviewing reflections
- **Produces:** Approved modifications to engine files
- **Unlocks:** Improved engine behavior for subsequent sessions

## Purpose

Tune is the action layer of the self-improvement flywheel. It reads reflections, analyzes session conversations, and produces categorized recommendations for engine improvements. Nothing is applied without operator approval.

Tune operates in develop mode context — it modifies engine files (protocols, boot configuration, CLAUDE.md, slash command definitions). It's the bridge between "we noticed friction" and "we fixed it."

## When to Run

- Manually invoked by the operator: `/tune` or "run tune protocol"
- Typically follows a Reflect run, but can also be triggered independently
- Runs in a develop.md session — not in the same session as Reflect. The operator invokes Tune after reviewing the reflection output.
- Because Tune modifies engine files, it needs develop.md context
- Can process one reflection or accumulated reflections across sessions

## Inputs

- The full conversation from the work session (primary source of truth)
- Any reflection file(s) from the Reflect protocol in `engine/reflections/`
- Current engine state: `boot.md`, `develop.md`, `state.md`, `memory.md`, `CLAUDE.md`, `engine/protocols/`, `engine/runtimes/`, `.claude/commands/`

## Process

### Step 1: Gather Context

1. Read the most recent reflection(s) in `engine/reflections/`. If no reflection files exist, work from the conversation history only — the conversation is the primary source of truth regardless.
2. Review the work session conversation — look for:
   - Operator corrections or redirections
   - Moments where the agent improvised (indicates missing instructions)
   - Output revisions (indicates quality gaps)
   - Anything the reflection might have missed

### Step 2: Identify Improvements

For each issue found, define:
- **What:** The specific change needed
- **Where:** Which file(s) to modify
- **Why:** What problem this solves (link to reflection finding or conversation evidence)
- **Risk tier:** Safe / Structural / Breaking

### Step 3: Categorize by Risk

#### ✅ Safe Changes (low risk, additive)
Changes that clarify, extend, or improve without altering process flow:
- Clarifying ambiguous language in protocols
- Adding missing context references or file paths
- Adding examples or edge case notes
- Fixing typos or outdated references
- Updating `memory.md` with cross-cutting patterns

#### ⚠️ Structural Changes (medium risk, process modification)
Changes that modify how a protocol works or add new capabilities:
- Adding new steps to existing protocols
- Changing the order of operations within a protocol
- New protocol sections or sub-sections
- New entries in CLAUDE.md (e.g., adding a new operation or section type)
- New slash commands

#### 🚨 Breaking Changes (high risk, architectural)
Changes that alter fundamental assumptions:
- Changing the wiki schema (frontmatter format, relation types, section structure)
- Changing the three-operation model (ingest / query / lint)
- Modifying folder structure conventions
- Redefining how `index.md` or `log.md` work

### Step 4: Present Recommendations

Present all recommendations to the operator, grouped by risk tier. For each:

```
### [Risk Tier Emoji] Change Title

**What:** One-line description
**Where:** `engine/path/to/file.md` (section or line range)
**Why:** Evidence from reflection/conversation
**Change:** The specific edit (show before/after for clarity when helpful)
```

Wait for operator approval before proceeding. The operator may:
- Approve all
- Approve selectively (by tier or individually)
- Request modifications to proposed changes
- Reject and discuss

### Step 5: Apply Approved Changes

Make the approved changes to engine files. For each change:
1. Edit the file
2. Verify the edit doesn't break coherence with related files
3. Note what was changed

### Step 6: Document

- Update `state.md` with what was tuned
- The session log captures the full detail (run `/checkpoint` after)

## Output

- Modified engine files (protocols, boot.md, develop.md, CLAUDE.md, command files, etc.)
- Updated `state.md` reflecting the tune

## Rules

- **Nothing auto-applies.** All changes require operator approval, regardless of risk tier.
- **Show your work.** Every recommendation needs evidence — a reflection finding or a conversation moment.
- **Don't over-tune.** If a protocol worked fine, leave it alone. Tune addresses real friction, not theoretical improvements.
- **Coherence check.** After any protocol edit, mentally trace related protocols to ensure changes don't create conflicts.
- **One session's friction is a data point. Three sessions' friction is a pattern.** Wait for patterns on structural changes.
- **Protect what works.** If Reflect flagged "what worked well," make sure Tune changes don't break those patterns.
