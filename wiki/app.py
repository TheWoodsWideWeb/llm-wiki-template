"""
Wiki — local knowledge base viewer.

Usage:
    python -m wiki.app                # http://localhost:5001
    python -m wiki.app --port 8080    # custom port

Sections are auto-discovered from subdirectories of pages/. The directory name
(snake-case) becomes the URL segment; the section label is the title-cased
version. Override labels in SECTION_LABEL_OVERRIDES if needed.
"""

import argparse
import os
import re
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import markdown
import yaml
from flask import (
    Flask, render_template, abort, request, jsonify,
    session, redirect, url_for,
)

from wiki.chatbot import chat as chatbot_chat
from wiki import chat_log

app = Flask(__name__)
app.secret_key = os.environ.get("WIKI_SECRET_KEY") or "wiki-admin-" + os.environ.get("USER", "local")
ADMIN_USERNAME = os.environ.get("WIKI_ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("WIKI_ADMIN_PASSWORD", "admin123")
WIKI_NAME = os.environ.get("WIKI_NAME", "Wiki")
WIKI_TAGLINE = os.environ.get("WIKI_TAGLINE", "Internal knowledge base")

REPO_ROOT = Path(__file__).resolve().parent.parent
PAGES_DIR = REPO_ROOT / "pages"
INDEX_FILE = REPO_ROOT / "index.md"
RAW_DIR = REPO_ROOT / "raw"
SCRATCH_DIR = REPO_ROOT / "engine" / "scratch"

# Override auto-generated labels here (otherwise: section_name.replace("-", " ").title()).
SECTION_LABEL_OVERRIDES = {
    "ip": "IP",
}


def section_label(name):
    return SECTION_LABEL_OVERRIDES.get(name, name.replace("-", " ").replace("_", " ").title())


def discover_sections():
    """Return a list of section directory names that exist under pages/."""
    if not PAGES_DIR.exists():
        return []
    return sorted(d.name for d in PAGES_DIR.iterdir() if d.is_dir() and not d.name.startswith("."))


# ----- Source resolution (frontmatter sources -> /source/<path>) ------------


_source_index_cache = {}


def _build_source_index():
    """Map source filenames and repo-relative paths to actual file paths."""
    if _source_index_cache and not app.debug:
        return _source_index_cache
    _source_index_cache.clear()

    for search_root in [RAW_DIR, SCRATCH_DIR]:
        if not search_root.exists():
            continue
        for f in search_root.rglob("*"):
            rel = str(f.relative_to(REPO_ROOT))
            _source_index_cache[rel] = f
            _source_index_cache[f.name] = f

    return _source_index_cache


def _resolve_source(source_name):
    """Resolve a frontmatter source name to a (Path, repo-relative-str) tuple or None."""
    idx = _build_source_index()

    path = idx.get(source_name)
    if path:
        return path, str(path.relative_to(REPO_ROOT))

    stem = source_name.replace(".md", "")
    path = idx.get(stem)
    if path:
        return path, str(path.relative_to(REPO_ROOT))

    return None


# ----- Page parsing ---------------------------------------------------------


def parse_page(filepath):
    """Parse a markdown wiki page, extracting YAML frontmatter and content."""
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


# ----- Markdown rendering: autolinkers + transforms ------------------------


def autolink_bare_urls(text):
    """Convert bare URLs in markdown body to clickable markdown links."""
    placeholders = []

    def stash(m):
        placeholders.append(m.group(0))
        return f"\x00X{len(placeholders) - 1}\x00"

    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", stash, text)
    text = re.sub(r"\[[^\]]*\]\([^)]+\)", stash, text)
    text = re.sub(r"<https?://[^>\s]+>", stash, text)
    text = re.sub(r"```.*?```", stash, text, flags=re.DOTALL)
    text = re.sub(r"`[^`]+`", stash, text)

    def linkify(m):
        url = m.group(0)
        trailing = ""
        while url and url[-1] in ".,;:!?)]}":
            trailing = url[-1] + trailing
            url = url[:-1]
        if not url:
            return m.group(0)
        return f"[{url}]({url}){trailing}"

    text = re.sub(r"https?://[^\s<>\[\]`|'\"]+", linkify, text)

    def restore(m):
        return placeholders[int(m.group(1))]

    text = re.sub(r"\x00X(\d+)\x00", restore, text)
    return text


def _patent_url(match):
    normalized = re.sub(r"[\s,/]", "", match.group(0))
    return f"https://patents.google.com/patent/{normalized}/en"


def _pmc_url(match):
    return f"https://pmc.ncbi.nlm.nih.gov/articles/PMC{match.group(1)}/"


def _pmid_url(match):
    return f"https://pubmed.ncbi.nlm.nih.gov/{match.group(1)}/"


def _doi_url(match):
    doi = match.group(1).rstrip(".,;:!?")
    return f"https://doi.org/{doi}"


# Order matters: more specific patterns first.
CITATION_PATTERNS = [
    (re.compile(r"\bUS\s*\d{1,2}(?:,\d{3}){2}\s*[AB]\d?\b"), _patent_url),
    (re.compile(r"\bUS\s*\d{11}\s*A\d\b"), _patent_url),
    (re.compile(r"\bUS\s*\d{4}/\d{7}\s*A\d\b"), _patent_url),
    (re.compile(r"\bWO\s*\d{4}/\d{5,6}\s*A\d?\b"), _patent_url),
    (re.compile(r"\bEP\s*\d{1,2}(?:,\d{3}){1,2}\s*[AB]\d?\b"), _patent_url),
    (re.compile(r"\bEP\s*\d{6,8}\s*[AB]\d?\b"), _patent_url),
    (re.compile(r"\bCA\s*\d{7}\s*[AB]\d?\b"), _patent_url),
    (re.compile(r"\bCN\s*\d{9}\s*[AB]\b"), _patent_url),
    (re.compile(r"\bPMC(\d{5,})\b"), _pmc_url),
    (re.compile(r"\bPMID[:\s]+(\d{5,})\b"), _pmid_url),
    (re.compile(r"\bdoi:\s*(10\.\d+/[^\s)]+)", re.IGNORECASE), _doi_url),
]


def autolink_citations(text):
    """Auto-link patent IDs, PMC, PMID, and DOI identifiers inline."""
    placeholders = []

    def stash(m):
        placeholders.append(m.group(0))
        return f"\x00C{len(placeholders) - 1}\x00"

    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", stash, text)
    text = re.sub(r"\[[^\]]*\]\([^)]+\)", stash, text)
    text = re.sub(r"<https?://[^>\s]+>", stash, text)
    text = re.sub(r"```.*?```", stash, text, flags=re.DOTALL)
    text = re.sub(r"`[^`]+`", stash, text)
    text = re.sub(r"https?://[^\s<>\[\]`|'\"]+", stash, text)

    for pattern, builder in CITATION_PATTERNS:
        def replace(match, _builder=builder):
            label = match.group(0)
            trailing = ""
            while label and label[-1] in ".,;:!?":
                trailing = label[-1] + trailing
                label = label[:-1]
            if not label:
                return match.group(0)
            link = f"[{label}]({_builder(match)})"
            placeholders.append(link)
            return f"\x00C{len(placeholders) - 1}\x00{trailing}"
        text = pattern.sub(replace, text)

    def restore(m):
        return placeholders[int(m.group(1))]

    text = re.sub(r"\x00C(\d+)\x00", restore, text)
    return text


def add_external_link_attrs(html):
    """Add target=_blank and rel=noopener to external http(s) links."""
    def rewrite(m):
        href = m.group(1)
        extra = m.group(2) or ""
        if "target=" in extra:
            return m.group(0)
        return f'<a href="{href}" target="_blank" rel="noopener noreferrer"{extra}>'

    return re.sub(r'<a href="(https?://[^"]+)"([^>]*)>', rewrite, html)


def extract_external_references(html):
    """Extract unique external URLs from rendered HTML in order of appearance."""
    urls = re.findall(r'href="(https?://[^"]+)"', html)
    seen = set()
    unique = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique.append(url)
    return unique


_slug_to_url_cache = {}


def _build_slug_lookup():
    """Map bare filenames (without .md) to wiki URLs for backtick-path conversion."""
    if _slug_to_url_cache and not app.debug:
        return _slug_to_url_cache
    _slug_to_url_cache.clear()
    if PAGES_DIR.exists():
        for section_dir in PAGES_DIR.iterdir():
            if not section_dir.is_dir() or section_dir.name.startswith("."):
                continue
            for md_file in section_dir.glob("*.md"):
                _slug_to_url_cache[md_file.stem] = f"/{section_dir.name}/{md_file.stem}"
    return _slug_to_url_cache


def _normalize_md_path_to_wiki_url(path):
    """Convert a relative .md path in the repo to a wiki URL.

    Returns None for absolute/external paths so the caller leaves them untouched.
    """
    if path.startswith(("http://", "https://", "#", "/", "mailto:")):
        return None

    fragment = ""
    if "#" in path:
        path, fragment = path.split("#", 1)
        fragment = "#" + fragment

    path = re.sub(r"^(\.\./)+", "", path)
    path = re.sub(r"\.md$", "", path)
    path = path.rstrip("/")

    if path.startswith("pages/"):
        return f"/{path[len('pages/'):]}{fragment}"

    if "/" not in path:
        lookup = _build_slug_lookup()
        if path in lookup:
            return f"{lookup[path]}{fragment}"

    return f"/{path}{fragment}"


def render_md(body):
    """Convert markdown to HTML with cross-link rewriting and autolinking."""

    # Pass 0: convert backtick-wrapped repo paths to proper markdown links.
    def _backtick_path_to_link(match):
        path = match.group(1)
        segments = [s for s in path.rstrip("/").split("/") if s and s != ".."]
        label_slug = segments[-1] if segments else path
        label = label_slug.replace(".md", "").replace("-", " ").title()
        return f"[{label}]({path})"

    body = re.sub(r"`(\.\.?/[\w./-]+(?:\.md)?/?)`", _backtick_path_to_link, body)
    body = re.sub(r"`((?:pages|engine|raw)/[\w./-]+(?:\.md)?/?)`", _backtick_path_to_link, body)
    body = re.sub(r"`([\w][\w-]+\.md)`", _backtick_path_to_link, body)

    # Pass 1: rewrite cross-reference markdown links — [Label](../entities/foo.md)
    def rewrite_link(match):
        label = match.group(1)
        path = match.group(2)
        url = _normalize_md_path_to_wiki_url(path)
        if url is None:
            return match.group(0)
        return f"[{label}]({url})"

    body = re.sub(r"\[([^\]]+)\]\(([^)]*\.md[^)]*)\)", rewrite_link, body)

    # Autolink citation identifiers (patents, PMC, PMID, DOI)
    body = autolink_citations(body)

    # Autolink bare URLs
    body = autolink_bare_urls(body)

    html = markdown.markdown(
        body,
        extensions=["tables", "fenced_code", "toc", "attr_list", "md_in_html"],
    )

    # External links -> new tab
    html = add_external_link_attrs(html)

    # Wrap tables for horizontal scroll on narrow viewports
    html = re.sub(r"(<table>)", r'<div class="table-wrapper">\1', html)
    html = re.sub(r"(</table>)", r"\1</div>", html)

    return html


# ----- Navigation -----------------------------------------------------------


def _collect_section_pages(section):
    section_dir = PAGES_DIR / section
    if not section_dir.is_dir():
        return []
    pages = []
    for md_file in sorted(section_dir.glob("*.md")):
        fm, _ = parse_page(md_file)
        title = fm.get("title", md_file.stem.replace("-", " ").title())
        pages.append({"slug": md_file.stem, "title": title, "url": f"/{section}/{md_file.stem}"})
    return pages


def get_nav():
    """Build a flat nav: {section_name: {label, pages: [...]}} sorted alphabetically."""
    nav = {}
    for section in discover_sections():
        pages = _collect_section_pages(section)
        if pages:
            nav[section] = {"label": section_label(section), "pages": pages}
    return nav


def count_pages():
    total = 0
    if not PAGES_DIR.exists():
        return 0
    for section_dir in PAGES_DIR.iterdir():
        if section_dir.is_dir() and not section_dir.name.startswith("."):
            total += len(list(section_dir.glob("*.md")))
    return total


@app.context_processor
def inject_nav():
    sections = discover_sections()
    return {
        "nav": get_nav(),
        "section_labels": {s: section_label(s) for s in sections},
        "wiki_name": WIKI_NAME,
        "wiki_tagline": WIKI_TAGLINE,
    }


# ----- Routes ---------------------------------------------------------------


@app.route("/")
def index():
    nav = get_nav()
    section_counts = {k: len(v["pages"]) for k, v in nav.items()}
    return render_template(
        "index.html",
        total_pages=count_pages(),
        section_counts=section_counts,
    )


@app.route("/all")
def all_pages():
    """All wiki pages across every section, sorted by `updated` frontmatter desc."""
    sort = (request.args.get("sort") or "recent").lower()
    section_filter = (request.args.get("section") or "").lower()
    sections = discover_sections()
    section_labels = {s: section_label(s) for s in sections}

    rows = []
    for sec in sections:
        if section_filter and section_filter != sec:
            continue
        section_dir = PAGES_DIR / sec
        for md_file in section_dir.glob("*.md"):
            fm, _ = parse_page(md_file)
            title = fm.get("title", md_file.stem.replace("-", " ").title())
            updated = str(fm.get("updated", "") or "")
            created = str(fm.get("created", "") or "")
            rows.append({
                "title": title,
                "section": sec,
                "section_label": section_labels[sec],
                "url": f"/{sec}/{md_file.stem}",
                "updated": updated,
                "created": created,
                "slug": md_file.stem,
            })

    if sort == "title":
        rows.sort(key=lambda r: r["title"].lower())
    elif sort == "section":
        rows.sort(key=lambda r: (r["section_label"], r["title"].lower()))
    elif sort == "oldest":
        rows.sort(key=lambda r: (r["updated"] or r["created"], r["title"].lower()))
    else:  # recent (default)
        rows.sort(key=lambda r: (r["updated"] or r["created"], r["title"].lower()), reverse=True)

    return render_template(
        "all.html",
        rows=rows,
        sort=sort,
        section_filter=section_filter,
        section_labels=section_labels,
        total=len(rows),
    )


@app.route("/search")
def search():
    query = request.args.get("q", "").strip().lower()
    if not query:
        return render_template("search.html", query="", results=[])

    sections = discover_sections()
    section_labels = {s: section_label(s) for s in sections}
    results = []
    for sec in sections:
        section_dir = PAGES_DIR / sec
        for md_file in sorted(section_dir.glob("*.md")):
            fm, body = parse_page(md_file)
            title = fm.get("title", md_file.stem.replace("-", " ").title())
            text = (title + " " + body).lower()
            if query in text:
                idx = text.find(query)
                start = max(0, idx - 80)
                end = min(len(text), idx + len(query) + 80)
                snippet = text[start:end].strip()
                if start > 0:
                    snippet = "..." + snippet
                if end < len(text):
                    snippet = snippet + "..."
                results.append({
                    "title": title,
                    "section": section_labels[sec],
                    "url": f"/{sec}/{md_file.stem}",
                    "snippet": snippet,
                })

    return render_template("search.html", query=query, results=results)


@app.route("/<section>/<slug>")
def page(section, slug):
    if section not in discover_sections():
        abort(404)

    filepath = PAGES_DIR / section / f"{slug}.md"
    if not filepath.exists():
        abort(404)

    fm, body = parse_page(filepath)
    title = fm.get("title", slug.replace("-", " ").title())
    raw_sources = fm.get("sources", [])
    created = fm.get("created", "")
    updated = fm.get("updated", "")

    sources = []
    for s in raw_sources:
        resolved = _resolve_source(s)
        if resolved:
            _, rel_path = resolved
            sources.append({"name": s, "url": f"/source/{rel_path}"})
        else:
            sources.append({"name": s, "url": None})

    html_content = render_md(body)
    references = extract_external_references(html_content)

    return render_template(
        "page.html",
        title=title,
        section=section,
        section_label=section_label(section),
        sources=sources,
        created=created,
        updated=updated,
        content=html_content,
        references=references,
    )


@app.route("/source/<path:filepath>")
def source(filepath):
    """Serve a raw source file or directory listing, rendered as HTML."""
    full_path = (REPO_ROOT / filepath).resolve()

    # Security: only allow files under raw/ or engine/scratch/
    allowed_roots = [str(RAW_DIR.resolve()), str(SCRATCH_DIR.resolve())]
    if not any(str(full_path).startswith(root) for root in allowed_roots):
        abort(404)

    if full_path.is_dir():
        files = sorted(f for f in full_path.iterdir() if f.is_file() or f.is_dir())
        entries = []
        for f in files:
            rel = str(f.relative_to(REPO_ROOT))
            entries.append({"name": f.name, "url": f"/source/{rel}", "is_dir": f.is_dir()})
        return render_template(
            "source.html",
            title=full_path.name,
            filepath=filepath,
            is_dir=True,
            entries=entries,
            content=None,
        )

    if not full_path.exists():
        abort(404)

    text = full_path.read_text(encoding="utf-8")
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            body = parts[2]

    html_content = render_md(body)

    return render_template(
        "source.html",
        title=full_path.stem.replace("-", " ").title(),
        filepath=filepath,
        is_dir=False,
        entries=None,
        content=html_content,
    )


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Chatbot endpoint. Accepts {message, history, page, thread_id} and returns {reply, thread_id}."""
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"ok": False, "error": "No message provided."})
    if len(message) > 4000:
        return jsonify({"ok": False, "error": "Message too long (max 4000 chars)."})

    history = data.get("history") or []
    page_path = (data.get("page") or "").strip()
    thread_id = (data.get("thread_id") or "").strip() or None

    clean_history = []
    for msg in history[-20:]:
        if isinstance(msg, dict) and msg.get("role") in ("user", "assistant") and msg.get("content"):
            clean_history.append({"role": msg["role"], "content": str(msg["content"])[:4000]})

    reply = chatbot_chat(message, clean_history, page_path)

    # Persist to chat log. Failures here never block the reply.
    try:
        thread_id = chat_log.append_qa(
            source="frontend",
            question=message,
            answer=reply,
            thread_id=thread_id,
            page=page_path or None,
        )
    except Exception as exc:  # pragma: no cover — logging must not break chat
        app.logger.warning("chat_log.append_qa failed: %s", exc)

    return jsonify({"ok": True, "reply": reply, "thread_id": thread_id})


# ----- Admin panel ----------------------------------------------------------


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin_login", next=request.path))
        return fn(*args, **kwargs)
    return wrapper


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["is_admin"] = True
            next_url = request.args.get("next") or url_for("admin_home")
            return redirect(next_url)
        error = "Invalid credentials."
    return render_template("admin_login.html", error=error)


@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    return redirect(url_for("admin_login"))


def _chat_path_to_url(path):
    """Resolve a repo-relative path to a wiki/source URL."""
    clean = path.rstrip("/")
    if clean.startswith(("engine/scratch/", "raw/")):
        return f"/source/{clean}"
    if clean.startswith("pages/"):
        stripped = re.sub(r"\.md$", "", clean[len("pages/"):])
        return f"/{stripped}"
    if "/" not in clean and clean.endswith(".md"):
        stem = clean[:-3]
        lookup = _build_slug_lookup()
        if stem in lookup:
            return lookup[stem]
    return None


_CHAT_PATH_RE = re.compile(r"`((?:engine|raw|pages)/[\w./-]+(?:\.md)?/?)`")
_CHAT_BARE_MD_RE = re.compile(r"`([\w][\w-]+\.md)`")


def _chat_backtick_to_link(match):
    path = match.group(1)
    url = _chat_path_to_url(path)
    if not url:
        return match.group(0)
    return f"[`{path}`]({url})"


def _render_chat_markdown(text):
    """Render a chat message as lightweight HTML with repo-path autolinking."""
    if not text:
        return ""
    text = _CHAT_PATH_RE.sub(_chat_backtick_to_link, text)
    text = _CHAT_BARE_MD_RE.sub(_chat_backtick_to_link, text)
    html = markdown.markdown(text, extensions=["tables", "fenced_code", "nl2br"])
    return add_external_link_attrs(html)


@app.route("/admin")
@admin_required
def admin_home():
    threads = chat_log.list_threads()
    source_filter = request.args.get("source", "").strip().lower()
    if source_filter in ("frontend", "backend"):
        threads = [t for t in threads if t["source"] == source_filter]
    counts = {"frontend": 0, "backend": 0}
    for t in chat_log.list_threads():
        counts[t["source"]] = counts.get(t["source"], 0) + 1

    rendered = []
    for t in threads:
        rendered.append({
            **t,
            "messages": [
                {**m, "html": _render_chat_markdown(m.get("content", ""))}
                for m in t.get("messages", [])
            ],
        })
    return render_template(
        "admin.html",
        threads=rendered,
        counts=counts,
        active_source=source_filter,
    )


@app.route("/admin/thread/<thread_id>/delete", methods=["POST"])
@admin_required
def admin_delete_thread(thread_id):
    chat_log.delete_thread(thread_id)
    return redirect(url_for("admin_home"))


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5001)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    print(f"Wiki running at http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=True)
