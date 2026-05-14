# Checkpoint Protocol

> A checkpoint is the procedure for reaching a state where context can be cleared and work can resume cleanly.
>
> "Checkpoint," "shutdown," "save state," and "let's wrap up" all mean the same thing — run this procedure.

---

## Principles

- Do not let important state live only in conversation
- Keep audit artifacts in files
- Prefer durable markdown artifacts over implied memory

---

## The Procedure

Four steps, always in this order.

### 1. Update `state.md`

Record what's done, what's next, and anything the next boot needs to know.

- Prune completed items — state is not a history log
- State should read cleanly for cold-start orientation
- A new session reading only `state.md` should know exactly where to pick up

### 2. Append to today's session log

Write to `engine/log/YYYY-MM-DD.md`. Create the file if this is the first session of the day.

- Use `## Session — [focus]` headers
- Keep entries concise — what was done, key outcomes, anything notable
- The log is the history; state.md is the working surface

### 3. Commit all work

Stage and commit in logical conventional commit batches.

**Grouping:**

| Group | Example |
|-------|---------|
| Wiki content | `feat(wiki): ingest cohen-2022 paper into science + entities` |
| Engine changes | `refactor(engine): rewrite checkpoint protocol` |
| State/log bookkeeping | `chore(engine): update state and session log` |

**Rules:**
- Stage files specifically — never `git add .`
- One logical change per commit
- Review staged changes with `git diff --staged` before committing
- Do not ask the operator whether to commit — the work is done, commit it

### 4. Verify clean git state

Run `git status`. The working tree must be clean. If it isn't, something was missed — go back and commit it.

Checkpoint is not complete until git is clean.

---

## When to Checkpoint

- When the operator says "checkpoint," "shutdown," "save state," "let's wrap up," or similar
- After a wiki operation completes (ingest batch done, lint pass finished, substantial query answered)
- Before ending any session
- Proactively when significant work has accumulated and context is getting long

---

## Commit Conventions

Follow conventional commits:

```
<type>(<scope>): <description>

[optional body with details]
```

**Types:**
- `feat` — new pages, sources, capabilities
- `docs` — engine docs, protocols, logs
- `fix` — corrections to pages or engine behavior
- `refactor` — restructuring without behavior change
- `chore` — cleanup, bookkeeping, maintenance

**Scopes:**
- `wiki` — wiki content (pages, sources, index)
- `engine` — protocol/system changes
- `app` — Flask viewer / chatbot
- `log` — session logs

**Style:**
- Imperative mood: "add" not "added"
- Lowercase, no period, under 50 chars for description
- One logical change per commit

---

## What Checkpoint Is NOT

- Does **not** update `engine/memory.md` — only update memory when a cross-cutting pattern emerges
- Does **not** run reflect or tune — those are separate meta-protocols
- Does **not** require operator confirmation of what to commit — just commit the work that was done

---

## Anti-Patterns

- ❌ `git add . && git commit -m "updates"` — never do this
- ❌ Committing unfinished work without noting it — mark WIP in commit message if unavoidable
- ❌ Mixing engine changes and wiki content in one commit
- ❌ Forgetting to update state.md after committing
- ❌ Updating state/log but not committing — checkpoint isn't done until git is clean
- ❌ Asking the operator whether to commit — just do it, the work is done
