Health-check the wiki. Follow the lint operation defined in CLAUDE.md:

1. Read `index.md` and all wiki pages
2. Check for:
   - Contradictions between pages
   - Stale claims superseded by newer sources
   - Orphan pages with no inbound links
   - Important concepts mentioned but lacking their own page
   - Missing cross-references (first mention of an entity/concept with its own page should link to it)
   - Knowledge gaps that need new sources
   - Pages exceeding ~500 lines that should be split
   - Frontmatter issues (missing fields, wrong section tags, outdated dates)
3. Present findings organized by severity
4. Append a lint entry to `log.md`

Do not modify pages during lint — only report findings. The operator decides what to fix.
