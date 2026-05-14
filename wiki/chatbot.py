"""
Chatbot module for the wiki.
Uses Claude Sonnet to answer questions with full context from the wiki markdown files.

Retrieval strategy ("full-context with focus"):
- Build an index of every wiki page.
- Score pages against the user's message using keyword overlap (+ alias expansion).
- Inject ALL pages into the system prompt at a condensed character cap,
  ordered by relevance, with the top-N matches expanded to a much higher cap.
- The page being viewed (if any) is also expanded.
- A 160K-char ceiling keeps total context bounded.

This trades cost-per-turn for recall: the model never has to "guess what exists"
because the page catalog and the actual page bodies are both in front of it.
"""

import os
import re
from pathlib import Path

import anthropic
import yaml

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 4096
MAX_CONVERSATION_TURNS = 10

# Full-context mode: load ALL wiki pages at condensed level, expand top matches.
WIKI_PAGE_CONDENSED_CHARS = 3000  # per-page cap for baseline context
WIKI_PAGE_FULL_CHARS = 20000      # per-page cap for top keyword matches
MAX_FULL_PAGES = 4                # how many pages get the full treatment
MAX_TOTAL_WIKI_CHARS = 160000     # hard ceiling on total wiki context

PAGES_DIR = Path(__file__).resolve().parent.parent / "pages"
INDEX_FILE = Path(__file__).resolve().parent.parent / "index.md"

# Domain-term aliases: map common misspellings, abbreviations, and brand names
# to canonical search terms so keyword matching doesn't fail on typos.
# Populate this per-project once the wiki has stable vocabulary. Bigrams are
# supported — e.g. "drug preclusion" -> "drug-preclusion-clause".
TERM_ALIASES = {
    # "mukuna": "mucuna",
    # "ldopa": "l-dopa levodopa",
}

SYSTEM_PROMPT = """You are the internal knowledge assistant for this wiki. This is a private, internal tool used by the project team. Answer directly and completely.

You have access to the project's structured research wiki. Each page has YAML frontmatter (title, section, sources, relations, created, updated) and a markdown body.

RULES:
- Be direct. Give the answer, then the reasoning. No disclaimers, no hedging, no boilerplate.
- Engage at the level of a scientifically literate collaborator.
- Give specific numbers, dates, and citations when the wiki has them.
- If asked about strategy, give your honest recommendation with reasoning.
- If asked about risks, be frank about what could go wrong and why.
- If you don't know something or the wiki doesn't cover it, say so — don't pad with generalities.
- Use **bold** for key terms and bullet points for lists.
- Reference page paths when citing claims (e.g., `pages/science/some-page.md`).
- The wiki is the source of truth. If your general training contradicts the wiki, defer to the wiki and flag the discrepancy.
- Convergent findings across multiple wiki pages carry more weight than single-source claims — surface this when relevant."""


def _parse_page(filepath):
    """Parse frontmatter and body from a wiki page."""
    text = filepath.read_text(encoding="utf-8")
    frontmatter = {}
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError:
                pass
            body = parts[2]
    return frontmatter, body


def _build_page_index():
    """Build a searchable index of all wiki pages."""
    index = []
    if not PAGES_DIR.exists():
        return index
    for section_dir in PAGES_DIR.iterdir():
        if not section_dir.is_dir():
            continue
        for md_file in section_dir.glob("*.md"):
            fm, body = _parse_page(md_file)
            title = fm.get("title", md_file.stem.replace("-", " ").title())
            index.append({
                "path": md_file,
                "section": section_dir.name,
                "title": title,
                "slug": md_file.stem,
                "body": body,
                "text_lower": (title + " " + body).lower(),
            })
    return index


def _extract_keywords(message):
    """Extract search keywords, expanding domain-term aliases (single + bigram)."""
    text = message.lower()
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "can", "shall", "about", "what", "which",
        "who", "how", "when", "where", "why", "this", "that", "these", "those",
        "and", "or", "but", "not", "with", "for", "from", "into", "to", "of",
        "in", "on", "at", "by", "it", "its", "my", "your", "our", "their",
        "me", "you", "we", "they", "i", "tell", "know", "think", "any",
        "much", "one", "per", "let", "want", "going", "just", "like",
    }
    words = re.findall(r"\b[a-z][a-z0-9-]+\b", text)
    keywords = [w for w in words if w not in stop_words and len(w) > 2]

    expanded = set(keywords)
    for word in keywords:
        if word in TERM_ALIASES:
            for alias_term in TERM_ALIASES[word].split():
                expanded.add(alias_term)
    # Bigrams
    for i in range(len(words) - 1):
        bigram = f"{words[i]} {words[i+1]}"
        if bigram in TERM_ALIASES:
            for alias_term in TERM_ALIASES[bigram].split():
                expanded.add(alias_term)
    return list(expanded)


def _load_page_catalog():
    """Load index.md as a compact page catalog so the model knows what exists."""
    if INDEX_FILE.exists():
        text = INDEX_FILE.read_text(encoding="utf-8")
        return text[:8000]
    return ""


def _fetch_context(message, page_path=None):
    """Build context: ALL wiki pages condensed + top-N expanded to full text."""
    index = _build_page_index()
    keywords = _extract_keywords(message)

    def score_entry(entry):
        s = 0
        text = entry["text_lower"]
        for kw in keywords:
            count = text.count(kw)
            if count > 0:
                s += count
                if kw in entry["title"].lower():
                    s += 5
        return s

    scored = [(score_entry(e), e) for e in index]
    scored.sort(key=lambda x: -x[0])

    # Top-N pages get full treatment
    full_page_paths = set()
    for score, entry in scored[:MAX_FULL_PAGES]:
        if score > 0:
            full_page_paths.add(str(entry["path"]))

    # If user is viewing a specific page, give that page full treatment too
    current_page_path = None
    if page_path and page_path.strip("/"):
        parts = page_path.strip("/").split("/")
        if len(parts) == 2:
            section, slug = parts
            for entry in index:
                if entry["section"] == section and entry["slug"] == slug:
                    full_page_paths.add(str(entry["path"]))
                    current_page_path = str(entry["path"])
                    break

    context_parts = []
    total_chars = 0

    catalog = _load_page_catalog()
    if catalog:
        context_parts.append(f"[Page Catalog — all wiki pages]\n{catalog}")
        total_chars += len(catalog)

    # All pages, ordered by relevance, condensed or full
    for _, entry in scored:
        if total_chars >= MAX_TOTAL_WIKI_CHARS:
            break
        path_str = str(entry["path"])
        is_full = path_str in full_page_paths
        cap = WIKI_PAGE_FULL_CHARS if is_full else WIKI_PAGE_CONDENSED_CHARS
        snippet = entry["body"][:cap]
        label = "FULL" if is_full else "condensed"
        if path_str == current_page_path:
            label = "CURRENT PAGE, FULL"
        header = f"[{entry['title']} ({entry['section']}, {label})]"
        part = f"{header}\n{snippet}"
        context_parts.append(part)
        total_chars += len(part)

    context_parts.append(
        f"Wiki stats: {len(index)} indexed pages across "
        f"{len(set(e['section'] for e in index))} sections."
    )
    return "\n\n---\n\n".join(context_parts)


def chat(message, history=None, page_path=None):
    """Send a message to Claude with wiki context. Returns the full response text."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return "The chatbot is not configured yet. Please set the ANTHROPIC_API_KEY environment variable."

    context = _fetch_context(message, page_path)

    system = SYSTEM_PROMPT
    if context:
        system += f"\n\nHere is relevant content from the wiki:\n\n{context}"

    messages = []
    if history:
        trimmed = history[-(MAX_CONVERSATION_TURNS * 2):]
        for msg in trimmed:
            messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": message})

    client = anthropic.Anthropic(api_key=api_key)

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system,
            messages=messages,
        )
        return response.content[0].text
    except anthropic.AuthenticationError:
        return "API key is invalid. Please check your ANTHROPIC_API_KEY."
    except anthropic.RateLimitError:
        return "The chatbot is temporarily busy. Please try again in a moment."
    except Exception:
        return "Sorry, something went wrong. Please try again later."
