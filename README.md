# LLM Wiki Template

A template for building a **persistent, LLM-maintained knowledge wiki** for any subject matter. Drop in research, run one command, get a structured, cross-linked, queryable knowledge base — with a Flask viewer and an AI chatbot built in.

> **What this is for:** You're researching something deep — a market, a regulatory landscape, a scientific topic, a competitive field, a domain you're going to operate in. You're accumulating papers, articles, Reddit threads, FDA letters, competitor pages, expert opinions. The pile gets too big to hold in your head and Notion gets messy. This template turns that pile into a wiki that **compounds**: every source ingested makes the next answer better, and the wiki itself is the source of truth — not your scratch notes or your conversation history with an LLM.

---

## What you get

- **A structured wiki** — markdown pages with typed YAML frontmatter, organized into auto-discovered sections (`pages/<section>/`). Cross-linked, with explicit relations (`deepens`, `supports`, `contradicts`, `supersedes`).
- **Three LLM-driven operations** — `/ingest` to turn raw sources into wiki pages, `/query` to ask questions of the wiki, `/lint` to audit health (contradictions, orphans, stale claims, missing cross-references).
- **A review gate** — raw sources land in `raw/staging/`, you approve them into `raw/approved/`, then ingest. Nothing enters the wiki without your sign-off.
- **A Flask frontend** — local web viewer with sidebar nav, full-text search, prose-friendly rendering, automatic citation linking (PMID, PMC, DOI, patent numbers), and a sources panel.
- **An AI chatbot** — Claude Sonnet 4.6, full-context retrieval (loads every page condensed + the top matches expanded), wiki-aware. Includes thread-persisting admin panel.
- **A research toolchain** — Firecrawl, Perplexity, SerpAPI, Reddit, YouTube transcripts, Grok — all pre-wired in `.agents/skills/research-tools/` for crawling and pulling sources into staging.
- **A small supporting engine** — session state, logs, reflection, tuning. The engine learns from each session and gets better.

## What this is NOT

- **Not a CMS, not a public site builder.** Internal tool. The chatbot system prompt explicitly says "internal use — answers from the wiki." You can deploy it, but it's designed for a small team.
- **Not a content production pipeline.** This template used to ship with a 21-protocol content-engine for producing publication-ready articles, images, SEO compliance, etc. That layer was stripped out. If you want to *produce* content from your wiki, that's a separate next step you can add or commission.
- **Not a SaaS replacement.** No DB, no multi-tenant, no user accounts (single admin password). It's a markdown repo with a small Flask wrapper.

---

## Quickstart

### 1. Clone and set up

```bash
git clone <your-repo-url> my-wiki
cd my-wiki

# Install Python deps (Flask + Anthropic SDK + markdown + yaml)
pip install -r requirements.txt

# Copy env template and fill in at least ANTHROPIC_API_KEY
cp .env.example .env
$EDITOR .env
```

If you'll use the research tools (`web-scrape`, etc.), also install [uv](https://github.com/astral-sh/uv) and run:

```bash
cd .agents/skills/research-tools/scripts && uv sync
```

### 2. Name your project

- Edit `CLAUDE.md` line 1: replace "Your Project Name" with the real one.
- Edit `engine/state.md` to describe your wiki's mandate.
- Set `WIKI_NAME` and `WIKI_TAGLINE` in `.env` (or leave defaults).
- Update `log.md` header.

### 3. Run the frontend

```bash
python -m wiki.app
```

Visit `http://localhost:5001`. It'll be empty — the wiki is fresh. The homepage will tell you what to do next.

### 4. Gather your first sources

Drop research files into `raw/staging/`. Tag them with a topic subdirectory:

```
raw/staging/
  science/    — papers, clinical trials, technical refs
  regulatory/ — FDA guidance, legal docs
  competitive/ — competitor pages, product listings
  community/  — Reddit threads, forum discussions
```

Add or rename topics to fit your subject matter.

You can:
- Paste markdown files directly
- Run `uv --directory .agents/skills/research-tools/scripts run web-scrape scrape <URL>` to pull a page via Firecrawl
- Run `uv --directory .agents/skills/research-tools/scripts run google-search "<query>"` to find sources

### 5. Review and approve

Skim what landed in `raw/staging/`. Move anything you want in the wiki to `raw/approved/<topic>/`:

```bash
mv raw/staging/science/some-paper.md raw/approved/science/
```

### 6. Ingest

Open Claude Code in this repo and run:

```
/ingest
```

The agent will:
- Read every un-ingested source in `raw/approved/`
- Create or update pages in `pages/` (entities, concepts, science, etc. — auto-discovered)
- Add cross-references between affected pages
- Update `index.md` and append to `log.md`

A single source typically touches 5-15 pages. The wiki compounds.

### 7. Query and lint

Once you have pages, you can:

```
/query What are the main objections to [thing]?
/lint
```

Or hit the chatbot bubble in the bottom-right of the web frontend.

---

## How it stays useful over time

The wiki is **append-only and self-healing**:

- **Every query is allowed to update pages.** If asking a question reveals a missing cross-reference, a contradiction between two pages, or a stale claim, the `/query` operation fixes it on the way out. The wiki gets richer just from *using* it.
- **`/lint` keeps things tidy.** Periodic audits surface orphan pages, missing relations, contradictions, and gaps. You decide what to fix.
- **Reflections compound.** Run `/reflect` at the end of a substantial session — the agent writes a structured assessment of what worked and what didn't. Run `/tune` later to fold those observations back into the protocols. The system gets better at running itself.

---

## Architecture at a glance

```
my-wiki/
├── CLAUDE.md              ← wiki schema (start here)
├── AGENTS.md              ← portable agent contract for non-Claude runtimes
├── README.md              ← this file
├── log.md                 ← append-only activity log
├── index.md               ← page catalog (created on first ingest)
│
├── raw/                   ← immutable raw sources
│   ├── staging/<topic>/   ← awaiting review
│   └── approved/<topic>/  ← reviewed, ready to ingest
│
├── pages/                 ← the wiki itself (created on first ingest)
│   ├── entities/
│   ├── concepts/
│   ├── science/
│   └── ...                ← whatever sections you create
│
├── wiki/                  ← Flask viewer + chatbot
│   ├── app.py             ← routes, rendering, autolinks, admin panel
│   ├── chatbot.py         ← Sonnet 4.6, full-context retrieval
│   ├── chat_log.py        ← thread persistence
│   ├── log_qa.py          ← CLI to log backend Q+A pairs
│   ├── templates/         ← Jinja templates (Tailwind, Inter font, sage/amber palette)
│   └── static/
│
├── engine/                ← state, logs, reflection, tuning
│   ├── boot.md            ← orientation for wiki sessions
│   ├── develop.md         ← orientation for engine work
│   ├── checkpoint.md      ← session shutdown procedure
│   ├── state.md           ← what's in flight
│   ├── memory.md          ← residual operational calibration
│   ├── log/               ← daily session logs
│   ├── protocols/         ← reflect.md, tune.md
│   ├── reflections/       ← session reflections (created on first /reflect)
│   └── runtimes/          ← runtime-specific modifiers (claude-code.md)
│
├── .claude/
│   ├── commands/          ← slash commands: /ingest /query /lint /reflect /tune /checkpoint /sync /boot /dev
│   └── (no agents/)       ← single-orchestrator model; sub-agents dispatched ad-hoc
│
└── .agents/
    └── skills/
        └── research-tools/  ← Firecrawl, Perplexity, SerpAPI, Reddit, YouTube, etc.
```

---

## The chatbot, briefly

`wiki/chatbot.py`:

- **Model:** `claude-sonnet-4-6` (configurable — bump to Opus 4.7 if you want; ~5× more expensive per turn at this context size).
- **Retrieval strategy:** loads `index.md` as a page catalog, then every page in `pages/` (3000-char snippet each), then expands the top-4 keyword matches plus the current page to 20000 chars each. Total context ceiling 160K chars.
- **Why this works:** the model never has to "guess what exists." Recall is the bottleneck for wiki chatbots, and stuffing the whole wiki (at a sane char budget) is cheaper and more accurate than building a vector store for a few hundred pages.
- **Domain aliases:** `TERM_ALIASES` dict in `chatbot.py` lets you map common typos / abbreviations to canonical wiki terms. Empty by default — fill it once your vocabulary stabilizes.

The admin panel at `/admin` (default password `admin123`, override with `WIKI_ADMIN_PASSWORD`) archives every chat thread so you can review what the team is actually asking.

---

## Configuration reference

All optional, all via environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `ANTHROPIC_API_KEY` | (required) | Chatbot Claude API key |
| `WIKI_NAME` | `Wiki` | Displayed in header, page titles, admin |
| `WIKI_TAGLINE` | `Internal knowledge base` | Shown in chat widget header |
| `WIKI_ADMIN_USERNAME` | `admin` | Admin panel login |
| `WIKI_ADMIN_PASSWORD` | `admin123` | Admin panel password — **change this** |
| `WIKI_SECRET_KEY` | per-user dev value | Flask session secret |
| Research tool keys | (none) | See `.env.example` |

---

## Credits & lineage

This template descends from the [WellDopa](https://github.com/) internal wiki, with the content-production engine stripped out and the chatbot upgraded. The retrieval pattern, autolinkers, and admin panel are direct ports. The wiki schema (CLAUDE.md) is a fresh, simplified take on the LLM-maintained knowledge-base pattern.

## License

(Add your license here — MIT, Apache 2.0, or proprietary. The template ships without one so the choice is yours.)
