# AGENTS.md — Wiki Operating Contract

You are operating inside a structured **LLM-maintained knowledge wiki**. Raw sources are ingested, the wiki gets richer over time, and a chatbot serves answers from the compiled knowledge.

This file is the **portable agent contract** for the repo. It is host-agnostic and works across Claude Code, Codex, Cursor, and similar runtimes.

---

## Start Here

Before acting, decide which mode you are in.

### If working **with the wiki** (the default)
Read and follow:
1. `CLAUDE.md` — wiki schema, the three operations (ingest, query, lint), page conventions
2. `engine/boot.md` — supporting engine (state, logs, reflection)
3. `engine/runtimes/{runtime}.md` — runtime-specific modifiers (e.g., `claude-code.md`)

Triggered by `/ingest`, `/query`, `/lint`, or natural language.

### If working **on the engine**
Read and follow:
1. `engine/develop.md` — develop mode boot
2. `engine/runtimes/{runtime}.md`

Use this mode when refining protocols, changing repo structure, or updating the wiki frontend.

If uncertain, assume **wiki mode** first and orient before making changes.

---

## Source of Truth

When files disagree, lower tiers win — Tier 1 is most authoritative.

| Tier | Layer | Contents |
|------|-------|----------|
| 1 | **Wiki schema** | `CLAUDE.md` |
| 2 | **Wiki content** | `pages/`, `index.md`, `log.md` |
| 3 | **Raw sources** | `raw/approved/` (immutable, the source for wiki content) |
| 4 | **Engine protocols** | `engine/protocols/`, `engine/boot.md`, `engine/develop.md`, `engine/checkpoint.md` |
| 5 | **Orientation** | `README.md`, `engine/runtimes/*.md` |
| 6 | **State & working** | `engine/state.md`, `engine/memory.md`, `engine/log/`, `engine/reflections/` |

Higher-numbered tiers are informational or working surfaces.

---

## Judgment Guardrails

Default role: **orchestrator**. Do **not** offload system judgment:
- Which raw sources are worth ingesting
- Which pages a new source should touch
- When to split a page that has grown too large
- How to phrase the canonical name of an entity or concept
- Final synthesis on query answers
- What becomes truth in wiki pages

---

## Safety Boundaries

Ask before:
- Destructive changes (deleting or overwriting large bodies of work)
- Restructuring `pages/` section layout (renaming or moving section directories)
- Modifying immutable raw sources in `raw/approved/`
- Publishing externally

When editing system behavior:
- Preserve auditability
- Avoid hidden magic
- Prefer explicit files over implicit conventions

---

## Related Docs

- `CLAUDE.md` — wiki schema and conventions
- `engine/boot.md` / `engine/develop.md` — mode-specific boot
- `engine/checkpoint.md` — session shutdown procedure
- `engine/runtimes/*.md` — runtime-specific modifiers
- `.agents/skills/research-tools/SKILL.md` — repo-local research toolchain (Firecrawl, Perplexity, Reddit, etc.)
