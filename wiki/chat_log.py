"""
Chat log storage for the wiki admin panel.

Persists Q+A threads from two sources:
- frontend: questions asked via the wiki chat widget (/api/chat)
- backend: questions logged manually from a CLI via `python -m wiki.log_qa`

Storage: a single JSON file at wiki/chat_log.json. Schema:
{
  "threads": [
    {
      "id": "abc123",
      "source": "frontend" | "backend",
      "title": "First question, truncated to ~80 chars",
      "created": "2026-04-14T12:34:56",
      "updated": "2026-04-14T13:00:00",
      "page": "/section/slug"  (optional, frontend only),
      "messages": [
        {"role": "user", "content": "...", "ts": "..."},
        {"role": "assistant", "content": "...", "ts": "..."}
      ]
    }
  ]
}
"""

import json
import secrets
import threading
from datetime import datetime
from pathlib import Path

LOG_PATH = Path(__file__).resolve().parent / "chat_log.json"
_LOCK = threading.Lock()
TITLE_MAX = 80


def _now():
    return datetime.now().isoformat(timespec="seconds")


def _new_id():
    return secrets.token_urlsafe(9)


def _empty():
    return {"threads": []}


def _load():
    if not LOG_PATH.exists():
        return _empty()
    try:
        return json.loads(LOG_PATH.read_text(encoding="utf-8")) or _empty()
    except (json.JSONDecodeError, OSError):
        return _empty()


def _save(data):
    tmp = LOG_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(LOG_PATH)


def _title_from(question):
    q = (question or "").strip().replace("\n", " ")
    if len(q) <= TITLE_MAX:
        return q
    return q[: TITLE_MAX - 1].rstrip() + "…"


def append_qa(source, question, answer, thread_id=None, page=None):
    """Append a Q+A pair. Creates a new thread if thread_id is missing/unknown.

    Returns the thread_id of the affected thread.
    """
    if source not in ("frontend", "backend"):
        raise ValueError(f"source must be frontend or backend, got {source!r}")

    now = _now()
    with _LOCK:
        data = _load()
        thread = None
        if thread_id:
            for t in data["threads"]:
                if t["id"] == thread_id:
                    thread = t
                    break

        if thread is None:
            thread_id = _new_id()
            thread = {
                "id": thread_id,
                "source": source,
                "title": _title_from(question),
                "created": now,
                "updated": now,
                "messages": [],
            }
            if page:
                thread["page"] = page
            data["threads"].append(thread)

        thread["messages"].append({"role": "user", "content": question, "ts": now})
        thread["messages"].append({"role": "assistant", "content": answer, "ts": now})
        thread["updated"] = now
        if page and thread.get("page") != page:
            thread["page"] = page

        _save(data)
        return thread_id


def list_threads():
    """Return all threads, newest-updated first."""
    data = _load()
    return sorted(data["threads"], key=lambda t: t.get("updated", ""), reverse=True)


def get_thread(thread_id):
    data = _load()
    for t in data["threads"]:
        if t["id"] == thread_id:
            return t
    return None


def delete_thread(thread_id):
    with _LOCK:
        data = _load()
        data["threads"] = [t for t in data["threads"] if t["id"] != thread_id]
        _save(data)
