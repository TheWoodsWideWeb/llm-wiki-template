---
name: research-tools
description: Use the repo-local Domain Engine research toolchain for web search, synthesis, scraping, social/community signal checks, and video/transcript discovery. Trigger when researching domains, hubs, parents, children, competitors, source credibility, or evidence gaps; when protocols need search/scrape/news/community inputs; or when an agent needs to run the local research scripts, know which environment variables they require, and choose the right research capability.
---

# Research Tools

Use this skill when Domain Engine work needs external research inputs.

This skill is the **repo-local research capability bundle**.

## Local script location

All research scripts live here:

```bash
.agents/skills/research-tools/scripts/
```

## Run pattern

Run from the repo root with `uv` pointing at the local tool project:

```bash
uv --directory .agents/skills/research-tools/scripts run <tool> [args]
```

Environment variables are loaded automatically from the repo root `.env` file via `python-dotenv`. No `--env-file` flag is needed.

## Available tools

### `google-search` — full Google search via SerpAPI
```bash
uv --directory .agents/skills/research-tools/scripts run google-search "longevity medicine" -n 5
uv --directory .agents/skills/research-tools/scripts run google-search "rapamycin dosing" -n 10 -t w
```

### `google-search-light` — lightweight Google search (proxy-based, no SerpAPI)
```bash
uv --directory .agents/skills/research-tools/scripts run google-search-light "longevity science" -n 5
```

### `google-news` — Google News via SerpAPI
```bash
uv --directory .agents/skills/research-tools/scripts run google-news "longevity medicine" -n 5
uv --directory .agents/skills/research-tools/scripts run google-news "aging research" -t w -n 3
```

### `google-trends` — Google Trends interest over time
```bash
uv --directory .agents/skills/research-tools/scripts run google-trends "longevity"
```

### `youtube-search` — YouTube search via SerpAPI
```bash
uv --directory .agents/skills/research-tools/scripts run youtube-search "longevity medicine" -n 5
uv --directory .agents/skills/research-tools/scripts run youtube-search "rapamycin" -t m -n 3
```

### `youtube-transcribe` — extract transcript from a YouTube video
```bash
uv --directory .agents/skills/research-tools/scripts run youtube-transcribe VIDEO_ID
uv --directory .agents/skills/research-tools/scripts run youtube-transcribe "https://youtube.com/watch?v=VIDEO_ID" -f json
```

### `web-scrape` — scrape or search URLs via Firecrawl
```bash
uv --directory .agents/skills/research-tools/scripts run web-scrape scrape https://example.com
uv --directory .agents/skills/research-tools/scripts run web-scrape search "longevity clinics"
```

### `x-search` — X/Twitter search and post reading via Grok
```bash
uv --directory .agents/skills/research-tools/scripts run x-search search "What are people saying about rapamycin?"
uv --directory .agents/skills/research-tools/scripts run x-search read POST_URL
```

### `reddit-search` — Reddit posts and comments via Oxylabs proxy
```bash
uv --directory .agents/skills/research-tools/scripts run reddit-search posts longevity -n 10
uv --directory .agents/skills/research-tools/scripts run reddit-search comments POST_URL
```

### `perplexity-search` — synthesized research via Perplexity Sonar Pro
```bash
uv --directory .agents/skills/research-tools/scripts run perplexity-search "rapamycin longevity evidence"
uv --directory .agents/skills/research-tools/scripts run perplexity-search "rapamycin longevity" --research
```

### `fear-greed` — Fear & Greed Index (no API key needed)
```bash
uv --directory .agents/skills/research-tools/scripts run fear-greed
```

### `word-count` — count readable words in an MDX article
```bash
uv --directory .agents/skills/research-tools/scripts run word-count /path/to/article.mdx
uv --directory .agents/skills/research-tools/scripts run word-count /path/to/article.mdx --wpm 240 --json
```
Counts readable text (prose + component content) excluding references, MDX syntax, citations, and URLs. Default 240 wpm. JSON output includes `wordCount` and `readingTime`. Used by Stage 9 of the content writing pipeline for canonical word count computation.

## Tool selection heuristics

### Start broad, then tighten
1. `perplexity-search` for orientation
2. `google-search` / `google-news` for targeted confirmation
3. `web-scrape` for direct source extraction
4. `reddit-search` / `x-search` / `youtube-search` for community and practitioner signal
5. `youtube-transcribe` only when the transcript itself matters

### Use the highest-authority source available
- prefer primary research, official organizations, original docs, and direct site extraction
- use synthesis tools to find sources, not to replace source reading when precision matters

### Match tool to task
- **landscape scan** → synthesis/search first
- **fact verification** → targeted search + direct extraction
- **competitor profiling** → search + map + scrape + social signal
- **source vetting** → direct scrape/map + targeted search for reputation/context

## Environment variables

Core research stack (set in repo root `.env`):
- `SERPAPI_API_KEY`
- `FIRECRAWL_API_KEY`
- `XAI_API_KEY`
- `PERPLEXITY_API_KEY`
- `OXY_USERNAME`
- `OXY_PASSWORD`

Optional:
- `OPENAI_API_KEY` — fallback workflows

## First-time setup

Run once from the scripts directory to install dependencies:

```bash
cd .agents/skills/research-tools/scripts && uv sync
```

## Fallback order

If the preferred capability is unavailable:
1. use another repo-local research capability that can answer the question
2. fall back from synthesis to direct search/scrape
3. note the missing capability explicitly in the output
4. do not invent unsupported confidence

## Scope boundary

This skill is for the research capability layer only.
Do not use it as a replacement for `AGENTS.md`, `README.md`, or runtime adapter docs.
