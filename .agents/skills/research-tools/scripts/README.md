# System Tools — Data Acquisition Layer

Standalone CLI tools for data acquisition. These can be called from any agent or script.

## Installation

```bash
cd .agents/skills/research-tools/scripts
uv sync
```

## Available Tools

### Search & Research

| Tool | API | Description |
|------|-----|-------------|
| `google-search` | SERP API | Full Google search with knowledge graph, answer boxes |
| `google-search-light` | SERP API | Organic results only (faster, cheaper) |
| `google-news` | SERP API | Google News search |
| `google-trends` | SERP API | Google Trends data (timeseries, related queries) |
| `youtube-search` | SERP API | YouTube video search |
| `youtube-transcribe` | ytscrape | Get YouTube transcripts (uses Oxylabs proxy) |
| `web-scrape` | Firecrawl | Scrape URLs or search+scrape |
| `x-search` | Grok 4.1 | X/Twitter search with DeepSearch |
| `reddit-search` | Reddit JSON | Search Reddit or get subreddit posts |
| `perplexity-search` | Sonar Pro | Synthesized research with citations |

## Usage

All tools output JSON to stdout. Run with `uv run <tool>`:

```bash
# Google Search
uv run google-search "longevity medicine" -n 5
uv run google-search "rapamycin news" -t w  # Past week

# Google Light (organic only)
uv run google-search-light "senolytics research" -n 10

# Google News
uv run google-news "longevity startup funding"

# Google Trends
uv run google-trends "rapamycin" --date "today 12-m"
uv run google-trends "rapamycin,metformin" --type RELATED_QUERIES

# YouTube Search
uv run youtube-search "Peter Attia longevity"

# YouTube Transcribe (uses Oxylabs proxy)
uv run youtube-transcribe dQw4w9WgXcQ
uv run youtube-transcribe "https://youtube.com/watch?v=xxx" -f json

# Web Scrape
uv run web-scrape scrape "https://example.com"
uv run web-scrape search "longevity clinics" -n 5 --scrape

# X/Twitter Search
uv run x-search search "What are people saying about rapamycin?"
uv run x-search read "https://x.com/user/status/123"

# Reddit
uv run reddit-search posts longevity -s hot -n 10
uv run reddit-search search "NAD+ supplementation" -r longevity

# Perplexity
uv run perplexity-search "What is rapamycin?"
uv run perplexity-search "Latest longevity research" --research
```

## Environment Variables

| Variable | Required For | Description |
|----------|--------------|-------------|
| `SERPAPI_API_KEY` | google-*, youtube-search | SERP API key |
| `FIRECRAWL_API_KEY` | web-scrape | Firecrawl API key |
| `XAI_API_KEY` | x-search | xAI/Grok API key |
| `PERPLEXITY_API_KEY` | perplexity-search | Perplexity API key |
| `OXY_USERNAME` | youtube-transcribe | Oxylabs proxy username |
| `OXY_PASSWORD` | youtube-transcribe | Oxylabs proxy password |
| `OPENAI_API_KEY` | youtube-transcribe | For Whisper fallback (optional) |

## Output Format

All tools return consistent JSON:

```json
{
  "success": true,
  "data": { ... },
  "source": "tool-name",
  "timestamp": "2026-02-07T00:00:00.000Z"
}
```

On error:

```json
{
  "success": false,
  "error": "Error message",
  "timestamp": "2026-02-07T00:00:00.000Z"
}
```

## Proxy Configuration

YouTube transcription uses Oxylabs residential proxy to avoid IP blocks. The proxy URL is built from `OXY_USERNAME` and `OXY_PASSWORD`:

```
http://{OXY_USERNAME}:{OXY_PASSWORD}@pr.oxylabs.io:7777
```

**Always use the proxy for any YouTube scraping to avoid IP bans.**

## Adding New Tools

1. Create `src/tools/<tool_name>.py`
2. Add entry point in `pyproject.toml` under `[project.scripts]`
3. Use `common.py` helpers for consistent output
4. Run `uv sync` to update

## Testing

```bash
# Test individual tools
uv run google-search "test" -n 1
uv run youtube-search "test"
uv run reddit-search posts longevity -n 1

# Quick sanity check
uv run google-search "hello" -n 1 | jq '.success'
```
