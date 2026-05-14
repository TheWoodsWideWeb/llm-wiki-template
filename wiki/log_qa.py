"""
Manual Q+A logger — pushes a question/answer pair into the chat log as a
`backend` entry, so terminal sessions can be archived alongside frontend
chats in the admin panel.

Usage:
    python -m wiki.log_qa \\
        --question "What is concept X?" \\
        --answer "Concept X is..." \\
        [--thread-id abc123] \\

    # Read question/answer from files (recommended for long content):
    python -m wiki.log_qa --question-file q.txt --answer-file a.md

    # List existing threads (to find an ID to append to):
    python -m wiki.log_qa --list

    # Show a thread's full transcript:
    python -m wiki.log_qa --show abc123

If --thread-id is omitted, a new thread is created.
"""

import argparse
import sys
from pathlib import Path

from wiki.chat_log import append_qa, list_threads, get_thread


def _read(path_or_none):
    if not path_or_none:
        return None
    return Path(path_or_none).read_text(encoding="utf-8")


def _cmd_list():
    threads = list_threads()
    if not threads:
        print("(no threads logged)")
        return
    for t in threads:
        src = t["source"].upper().ljust(8)
        print(f"{t['id']}  {src}  {t['updated']}  {t['title']}")


def _cmd_show(thread_id):
    t = get_thread(thread_id)
    if not t:
        print(f"Thread {thread_id!r} not found.", file=sys.stderr)
        sys.exit(1)
    print(f"# {t['title']}")
    print(f"id: {t['id']}  source: {t['source']}  created: {t['created']}  updated: {t['updated']}")
    if t.get("page"):
        print(f"page: {t['page']}")
    print()
    for msg in t["messages"]:
        role = msg["role"].upper()
        print(f"--- {role} ({msg.get('ts','')}) ---")
        print(msg["content"])
        print()


def main():
    parser = argparse.ArgumentParser(description="Log a Q+A pair to the wiki chat log.")
    parser.add_argument("--list", action="store_true", help="list existing threads and exit")
    parser.add_argument("--show", metavar="THREAD_ID", help="print a thread and exit")
    parser.add_argument("--thread-id", help="append to an existing thread (else creates new)")
    parser.add_argument("--question", help="question text (inline)")
    parser.add_argument("--answer", help="answer text (inline)")
    parser.add_argument("--question-file", help="read question from a file")
    parser.add_argument("--answer-file", help="read answer from a file")
    args = parser.parse_args()

    if args.list:
        _cmd_list()
        return

    if args.show:
        _cmd_show(args.show)
        return

    question = args.question or _read(args.question_file)
    answer = args.answer or _read(args.answer_file)

    if not question or not answer:
        parser.error("must provide both --question and --answer (or their --*-file variants)")

    thread_id = append_qa(
        source="backend",
        question=question,
        answer=answer,
        thread_id=args.thread_id,
    )
    print(thread_id)


if __name__ == "__main__":
    main()
