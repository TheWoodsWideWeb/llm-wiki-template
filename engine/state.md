# Wiki Engine — State

> Working state: what we're doing now, what's next, unfinished work. Items flow through — they arrive when work starts and leave when it lands.

## Mandate

Define your wiki's mandate here. One or two sentences on the subject matter and the goal.

## Current Focus

**Fresh start.** No wiki pages yet, no raw sources gathered.

### What exists now
- **0 wiki pages** — empty `pages/` will be created on first ingest
- **0 raw sources** — `raw/staging/` and `raw/approved/` exist but are empty
- **Wiki frontend** — Flask app + chatbot ready to run (`python -m wiki.app`)

### Three priority gates
1. **Define wiki scope** — Edit this file and `CLAUDE.md` to name the project and describe the subject matter
2. **Begin raw source collection** — Gather initial sources into `raw/staging/<topic>/`
3. **First ingest cycle** — Move reviewed sources to `raw/approved/` and run `/ingest`

## In Review

Nothing currently in review.

## Queue

### Next session
1. Update project name and tagline (CLAUDE.md, `WIKI_NAME` env var)
2. Gather first sources for your subject matter
3. Run first `/ingest` to populate wiki pages

### Operator decisions needed
1. **Project scope** — What subject matter will this wiki cover?
2. **Section structure** — Are the default raw-source topic tags (community, competitive, regulatory, science) appropriate, or do they need to be renamed?
3. **Page section names** — `pages/` subdirectories are auto-discovered. Decide what sections make sense (entities, concepts, etc.) and create the first ones on first ingest.

## Human Notes

- Project name: (set me)
