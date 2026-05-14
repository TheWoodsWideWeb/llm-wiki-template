# Protocol: Reflect

> Structured self-assessment at the end of a wiki session. Produces actionable observations about what worked, what didn't, and what could improve.

## Overview

- **Runs:** Operator-invoked at the end of a session
- **Produces:** Reflection file in `engine/reflections/` with findings across five dimensions
- **Unlocks:** Tune protocol — or accumulates for later tuning

## Purpose

Reflect is a meta-protocol. It doesn't produce wiki content — it produces observations about how the engine performed during a session. These observations feed into the Tune protocol (or accumulate for later tuning).

The goal state is "nothing to report." When sessions consistently run smoothly with no friction, the engine is dialed. Until then, every reflection makes the next session better.

## When to Run

- Manually invoked by the operator: "run reflection protocol" or `/reflect`
- Runs at the end of any session that involved real work (ingest, query, lint)
- Runs in the same session context — the agent that did the work is the one reflecting

## Inputs

- The conversation history of the current session
- The operation(s) that were executed
- The wiki state before and after (if relevant)

## Process

### Step 1: Review the Session

Walk through the full conversation. For each phase of work, note:
- What was the task?
- How did it go?
- Where did the operator intervene or correct course?
- Where did you hesitate, get stuck, or produce something that needed revision?
- Where did things flow smoothly?

### Step 2: Assess Each Dimension

Evaluate the session across these dimensions. For each, provide specific findings — not vague impressions. If a dimension has nothing to report, say so explicitly.

#### 1. Process Friction
Where did the workflow slow down, require workarounds, or break the expected flow?
- Unnecessary steps that could be eliminated
- Steps that were in the wrong order
- Manual work that could be automated or templated

#### 2. Instruction Gaps
Were protocol instructions (CLAUDE.md, boot.md, command files) ambiguous, incomplete, or wrong?
- Missing steps that had to be improvised
- Instructions that were confusing or contradictory
- Context that should have been injected but wasn't

#### 3. Tool & Capability Gaps
Did the agent need tools, access, or capabilities it didn't have?
- Missing research tools or data sources
- Output formats that were awkward to produce
- File operations that were cumbersome

#### 4. Output Quality
Did outputs match expectations? Where did they fall short?
- Page structure issues (frontmatter, cross-references, relations)
- Depth too shallow or too dense
- Accuracy or sourcing concerns
- Duplicates or orphans that slipped through

#### 5. What Worked Well
Patterns, decisions, and flows that should be protected and reinforced.
- Steps that felt natural and efficient
- Protocol instructions that were clear and helpful
- Anything the operator explicitly praised

### Step 3: Synthesize Findings

Produce a structured reflection file with:
- **Session summary** — one paragraph: what was done, what operation(s)
- **Findings** — organized by dimension, each finding with:
  - What happened (specific, concrete)
  - Where in the process (which protocol step, which conversation turn)
  - Impact (minor friction / significant slowdown / blocked progress / quality issue)
  - Suggested improvement (if obvious — Tune will formalize these)
- **Overall assessment** — one of:
  - ✅ **Clean session** — no significant friction, system worked as designed
  - ⚠️ **Minor friction** — some rough edges but nothing blocking
  - 🔧 **Tune recommended** — clear improvements identified, worth a Tune cycle
  - 🚨 **Significant issues** — process problems that should be addressed before next session

### Step 4: Write Reflection

Save to `engine/reflections/{YYYY-MM-DD}-{session-label}.md`. Create the `engine/reflections/` directory if it doesn't exist.

Session label should be descriptive: `ingest-batch-1`, `query-deep-dive`, `lint-cleanup`, etc.

## Output

A single reflection file in `engine/reflections/` with the structure above.

The operator decides whether to run the Tune protocol based on the overall assessment and findings.

## Rules

- Be honest and specific. Vague reflections are useless.
- Don't invent problems. If the session was clean, say so.
- Operator interventions are the strongest signal — every time the operator had to correct course, something in the system could be better.
- "What worked well" is just as important as problems — it protects good patterns from being broken by tuning.
- Even clean sessions produce a reflection file — it serves as a log entry. The file can be brief: session summary + "✅ Clean session — no significant friction."
- This protocol does NOT modify any engine files. It only produces a reflection.
