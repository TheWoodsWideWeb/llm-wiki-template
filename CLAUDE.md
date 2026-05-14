# Your Project Name — LLM Wiki Schema

> Replace "Your Project Name" with the actual name of your knowledge base. Set the `WIKI_NAME` environment variable (or edit `wiki/app.py`) so the frontend matches.

A persistent, compounding knowledge wiki maintained by an LLM. Raw sources go in, structured knowledge comes out. The wiki gets richer with every source ingested and every question answered. Nothing is re-derived from scratch — knowledge is compiled once and kept current.

## Architecture

Three layers:

1. **Raw Sources** (`raw/`) — Immutable source documents. The LLM reads from them but never modifies them. Organized into `staging/` (awaiting review) and `approved/` (reviewed, ready for ingest).
2. **The Wiki** (`pages/`) — LLM-generated and LLM-maintained markdown pages. Summaries, entity pages, concept pages, explorations. The LLM owns this layer entirely. You read it; the LLM writes it.
3. **This Schema** (`CLAUDE.md`) — How the wiki is structured, what the conventions are, and what workflows to follow.

Two navigation files:
- `index.md` — Content catalog. Read this first on every session. Lists every page with a one-line summary, organized by section.
- `log.md` — Chronological append-only record of all activity (ingests, queries, lint passes).

Plus a small supporting engine in `engine/` for state tracking, session logs, reflection, and tuning. See `engine/boot.md`.

## Directory Structure

```
raw/
  staging/<topic>/       # Crawled/gathered, awaiting human review
  approved/<topic>/      # Human-reviewed, ready for ingest
pages/
  <section>/             # Each subdirectory becomes a navigable section
                         # Section names are up to you — common ones below
```

### Suggested Page Sections

`pages/` subdirectories are auto-discovered by the wiki frontend. Common starting sections:

- `entities/` — Specific things: organizations, people, products, compounds
- `concepts/` — Cross-cutting ideas: mechanisms, frameworks, principles
- `science/` — Research papers and scientific findings
- `regulatory/` — Compliance, rules, legal landscape
- `competitive/` — Market analysis, competitors
- `explorations/` — Filed query answers that compound

Add or remove sections to fit your domain. The wiki frontend will pick them up automatically.

### Topic Tags for Raw Sources

The defaults in `raw/staging/` and `raw/approved/` are:
- `science` — Papers, clinical trials, technical references
- `regulatory` — Rules, guidance, legal documents
- `competitive` — Competitor pages, product comparisons
- `community` — Forum threads, user discussions

Rename or extend these as needed for your subject matter.

## Three Operations

### Ingest

Process approved raw sources into wiki pages.

1. Read the source document in `raw/approved/`
2. Write or update a source summary in the appropriate `pages/` section
3. Create or update entity pages in `pages/entities/` for every significant entity mentioned
4. Create or update concept pages in `pages/concepts/` for cross-cutting ideas
5. Add cross-reference links between all affected pages
6. Add typed `relations` to frontmatter of all affected pages (especially `deepens`, `supports`, and any `contradicts` or `supersedes` discovered during ingest)
7. Update `index.md` with any new pages (one-line summary each)
8. Append an entry to `log.md`

A single source may touch 5-15 wiki pages. Link, don't duplicate — if a concept spans multiple sections, it gets ONE canonical page in `pages/concepts/` and other pages link to it.

Triggered by `/ingest`.

### Query

Answer questions using the wiki.

Every query produces two outputs: (a) the direct answer, and (b) updates to any wiki pages where the synthesis revealed new connections, contradictions, or gaps. The wiki should be richer after every interaction, not just after ingests.

1. Read `index.md` to find relevant pages
2. Read the relevant pages
3. Synthesize an answer with citations to specific wiki pages
4. Update any wiki pages where the query revealed missing cross-references, contradictions, stale claims, or new connections — including adding `relations` to frontmatter where appropriate
5. If the answer itself is substantial and reusable, file it as a new page in `pages/explorations/`
6. Append a query entry to `log.md`

Triggered by `/query`. The wiki chatbot at `/api/chat` is a lightweight version of this same operation, scoped to a single answer.

### Lint

Health-check the wiki periodically.

Look for: contradictions between pages (check all `contradicts` relations first), stale claims superseded by newer sources (check all `supersedes` relations for unresolved targets), orphan pages with no inbound links, important concepts mentioned but lacking their own page, missing cross-references, missing or incomplete `relations` in frontmatter, knowledge gaps that need new sources.

Triggered by `/lint`. Lint only reports — it doesn't modify pages.

## Page Conventions

### Frontmatter

Every wiki page starts with YAML frontmatter:

```yaml
---
title: Page Title
section: <your-section-name>   # matches the pages/<section>/ subdirectory
sources: [list of raw source filenames that informed this page]
relations:
  - type: deepens | supports | contradicts | supersedes | related-to
    target: relative/path/to/other-page.md
    note: optional — brief explanation, especially for contradicts/supersedes
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

### Relation Types

| Type | Meaning | Lint behavior |
|------|---------|---------------|
| `deepens` | This page explores a subtopic of the target | Detects orphan hierarchies, aids depth navigation |
| `supports` | This page provides evidence for claims on the target | Maps the evidence chain across science -> claims |
| `contradicts` | This page disagrees with the target on a specific point | Lint flags unresolved contradictions automatically |
| `supersedes` | This page has newer/better information than the target | Lint checks whether the superseded page has been updated |
| `related-to` | Generic topical connection not covered by the above | Fallback — prefer a typed relation when one fits |

Relations are optional on existing pages — add them incrementally as pages are touched during ingests, queries, and lint fixes. No bulk migration required. The `note` field is encouraged for `contradicts` and `supersedes` to explain the specific disagreement or what changed.

### Cross-References

Use relative markdown links: `[Entity Name](../entities/entity-slug.md)`. The Flask viewer rewrites these to clean URLs (`/entities/entity-slug`). Always link on first mention of an entity or concept that has its own page.

### One Page, One Topic

Each page covers one entity, one concept, or one exploration. If a page grows beyond ~500 lines, split it.

## Review Gate

Raw sources flow through a gate before ingest:

1. **Gather** — Research tools crawl and dump into `raw/staging/<topic>/`. Use `web-scrape` (Firecrawl) from `.agents/skills/research-tools/` to pull web sources.
2. **Review** — Human scans staging. Approves or rejects.
3. **Approve** — Accepted sources move to `raw/approved/<topic>/`
4. **Ingest** — LLM processes approved sources into wiki pages via `/ingest`

Nothing enters the wiki without passing through `approved/`.

## The Wiki Frontend

A Flask app in `wiki/` serves the wiki for browsing and provides a chatbot at `/api/chat` powered by Claude Sonnet 4.6.

Run it:
```bash
python -m wiki.app                # http://localhost:5001
python -m wiki.app --port 8080    # custom port
```

Required environment variable: `ANTHROPIC_API_KEY` (for the chatbot).

Optional: `WIKI_NAME`, `WIKI_TAGLINE`, `WIKI_ADMIN_USERNAME`, `WIKI_ADMIN_PASSWORD`, `WIKI_SECRET_KEY`.

The admin panel at `/admin` archives every chat thread (frontend widget + backend CLI via `python -m wiki.log_qa`) so you can review what the team is asking and how the chatbot is answering.

## Meta Protocols

- `/reflect` — End-of-session self-assessment. Produces a reflection file in `engine/reflections/`.
- `/tune` — Engine self-improvement from reflections. Runs in develop mode, modifies engine files with operator approval.
- `/checkpoint` — Session shutdown (update state, append log, commit, verify clean git).
- `/sync` — Sync working branch with main.

These improve the engine over time. Use `/reflect` at the end of substantial sessions; run `/tune` periodically to fold accumulated learnings into the protocols.
