# Wiki Engine — Development Mode

> Boot file for working ON the engine itself: refining protocols, tuning the system, making structural changes to how the wiki operates.

## On Boot (Development Mode)

1. Read `engine/state.md` — current mandate, focus, in-flight work, queue
2. Read `engine/memory.md` — residual calibration context from prior sessions
3. Read the most recent log file in `engine/log/` (optionally the one before it if more context is useful)
4. If the runtime is known, read `engine/runtimes/{runtime}.md`
5. Present orientation using this template:
   1. Mode (develop) and runtime
   2. Active mandate
   3. Current focus (from state.md)
   4. Items in review or blocked
   5. Next 2-4 actions
   6. Any decisions needed from the operator

   Keep it to 5-10 lines. Lead with what matters most.

## What You're Working On

The wiki engine is a small, opinionated system for maintaining a structured knowledge wiki via an LLM agent. The wiki layer (`CLAUDE.md`, `raw/`, `pages/`, `index.md`, `log.md`) is the product; the engine layer (`engine/`) is the supporting machinery.

### Key Files
| File | Purpose |
|------|---------|
| `CLAUDE.md` | Wiki schema, conventions, the three operations (ingest, query, lint) |
| `engine/state.md` | Where we are, what's next, open questions |
| `engine/memory.md` | Residual operational calibration — cross-cutting patterns |
| `engine/boot.md` | Boot file for wiki-content sessions |
| `engine/checkpoint.md` | Session shutdown procedure |
| `engine/log/YYYY-MM-DD.md` | Session logs |
| `engine/protocols/reflect.md` | End-of-session self-assessment |
| `engine/protocols/tune.md` | Engine self-improvement based on reflections |
| `engine/runtimes/*.md` | Runtime-specific modifiers (e.g., claude-code.md) |
| `wiki/` | Flask viewer + chatbot for the wiki |

## How to Work in Development Mode

- **Changing a protocol:** Read the protocol, understand its inputs/outputs/constraints, make targeted edits. Check that changes don't break coherence with related files.
- **Adding a protocol:** Define purpose, when to run, inputs, process, outputs. Add to `boot.md`'s protocol table.
- **Tuning behavior:** Run the tune protocol against accumulated reflections.

## Session Shutdown

Run `engine/checkpoint.md`. "Checkpoint," "shutdown," "save state," and "let's wrap up" all mean the same thing.

## Rules

- Don't modify wiki content from development mode — use the wiki operations (`/ingest`, `/query`, `/lint`) instead
- Keep protocols coherent with each other — changes can cascade
- `state.md` is your scratchpad — write to it aggressively, read it on boot
- Keep runtime-specific quirks in `engine/runtimes/*.md`, not in core protocols
