# Runtime Modifier — Claude Code

## Core operating model

Every Claude Code session is the orchestrator. The main thread holds context, runs the three wiki operations (`/ingest`, `/query`, `/lint`), and makes judgment calls. Substantial side work can be dispatched to sub-agents via the Task tool when it helps protect the main context.

**Why:** Wiki sessions are mostly read-heavy and accretive — a single source can touch 5-15 pages, and the orchestrator needs the cross-page state in working memory. Dispatch is the exception, not the rule.

## Model assignments

- **Opus** is the default for all orchestration: ingest, query, lint, reflect, tune.
- **Sonnet** is fine for genuinely trivial tasks: quick file lookups, simple transformations.
- **Haiku 4.5** powers the wiki chatbot by default (configurable in `wiki/chatbot.py`).
- Never use a faster model as a substitute for judgment-heavy work.

## When to dispatch a sub-agent

- A batch of source files needs to be summarized into raw-source descriptions before ingest. Dispatch one agent per source, parallel.
- The lint pass surfaces a backlog of fix candidates and you want them researched without polluting the main thread.
- A query requires deep external research that would otherwise pull dozens of pages into context.

The default is: don't dispatch. The wiki workflow is small and direct.

## Dispatch contracts

Every dispatch should include:
- Exact task and scope boundary
- Input files to read
- Output file/location to write
- Quality bar and constraints
- What not to change

Keep prompts narrow and file-scoped. Use explicit handoff contracts, not open-ended instructions.

## What the orchestrator owns

- Cross-page state during ingest (so the same concept doesn't get a second canonical home)
- Synthesis of query answers
- Final judgment on lint findings — what to fix, what to defer, what to ignore
- Frontmatter and cross-reference correctness
- Updating `index.md` and `log.md`

## What the orchestrator does not do

- Web scraping of large batches of sources — dispatch one agent per URL via `web-scrape` (see `.agents/skills/research-tools/`)
- Reading dozens of unrelated pages just to compute statistics — script it or dispatch

Most wiki sessions never dispatch anything. That's the right baseline.
