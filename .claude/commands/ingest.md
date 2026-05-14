Process approved raw sources into wiki pages. Follow the ingest operation defined in CLAUDE.md:

1. Read `index.md` to understand current wiki state
2. Read the source document(s) in `raw/approved/` that the operator specifies (or process all un-ingested sources)
3. For each source:
   - Write or update a source summary in the appropriate `pages/` section
   - Create or update entity pages in `pages/entities/` for every significant entity mentioned
   - Create or update concept pages in `pages/concepts/` for cross-cutting ideas
   - Add cross-reference links between all affected pages
4. Update `index.md` with any new pages (one-line summary each)
5. Append an ingest entry to `log.md`

A single source may touch 5-15 wiki pages. Link, don't duplicate — if a concept spans multiple sections, it gets ONE canonical page and other pages link to it. Use relative markdown links: `[Entity Name](../entities/entity-slug.md)`.

Every wiki page must have YAML frontmatter per the CLAUDE.md schema conventions.
