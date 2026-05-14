# Wiki Engine — Memory

> Residual calibration that complements the system files. Contains only cross-cutting operational context that has no natural enforcement point in a protocol or in CLAUDE.md. Updated manually as patterns emerge.

## Operational Patterns

### What to watch for during ingest
- A single source often touches 5-15 pages — keep cross-page state in working memory while ingesting, or you'll create duplicate canonical pages.
- Frontmatter `relations` are easy to forget. Add them while pages are fresh in mind, not on a sweep later.
- If the same concept keeps appearing as a one-liner in many pages, it probably wants its own page in `pages/concepts/`.

### What to watch for during query
- The query operation is allowed to update pages, not just answer. Use it. If synthesis surfaces a missing cross-reference or a contradiction, fix it on the way out.

## Runtime Notes

- **Claude Code:** Opus by default for orchestration. The wiki chatbot in `wiki/chatbot.py` uses Sonnet 4.6 by default (configurable).
- Skills auto-load `.env` via dotenv.
- Research tools run pattern: `uv --directory .agents/skills/research-tools/scripts run <tool> [args]`
- Firecrawl is wired up as `web-scrape` — use it to pull web sources into `raw/staging/`.
