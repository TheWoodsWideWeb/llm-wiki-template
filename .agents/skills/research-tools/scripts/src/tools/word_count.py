"""
word-count — Count readable words in an MDX article file.

Parses MDX content and extracts readable text (prose + component content),
excluding references, MDX tag syntax, citation brackets, URLs, and frontmatter.
Outputs word count and estimated reading time.

Usage:
    word-count <file> [--wpm 250] [--json]
"""

import argparse
import json
import re
import sys


def extract_readable_text(content: str) -> str:
    """Extract all human-readable text from an MDX article."""

    # Strip YAML frontmatter if present
    content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)

    # Split off references section
    parts = content.split('<ReferencesSection>')
    body = parts[0]

    # Extract quoted strings from JSX component props (10+ chars = likely content)
    jsx_strings = re.findall(r'"([^"]{10,})"', body)

    # Remove all MDX/JSX tags (self-closing and paired)
    clean = re.sub(r'<[^>]+/?>', '', body)

    # Remove JSX expression blocks { ... } but keep any text around them
    # Handle nested braces by removing innermost first, iterating
    for _ in range(5):
        prev = clean
        clean = re.sub(r'\{[^{}]*\}', ' ', clean)
        if clean == prev:
            break

    # Remove citation brackets [1], [2], etc.
    clean = re.sub(r'\[\d+\]', '', clean)

    # Remove markdown link syntax, keep link text
    clean = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', clean)

    # Remove markdown heading markers
    clean = re.sub(r'^#+\s*', '', clean, flags=re.MULTILINE)

    # Remove bold/italic markers
    clean = re.sub(r'\*{1,3}', '', clean)

    # Remove bullet markers
    clean = re.sub(r'^\s*[-*]\s+', '', clean, flags=re.MULTILINE)

    # Remove URLs
    clean = re.sub(r'https?://\S+', '', clean)

    # Add JSX component text content (deduplicated by first 5 words)
    seen = set()
    for line in clean.split('\n'):
        words = line.strip().split()[:5]
        if words:
            seen.add(' '.join(words))

    extra_text = []
    for s in jsx_strings:
        key = ' '.join(s.split()[:5])
        if key not in seen:
            seen.add(key)
            extra_text.append(s)

    combined = clean + '\n' + '\n'.join(extra_text)

    # Collapse whitespace
    combined = re.sub(r'\s+', ' ', combined).strip()

    return combined


def count_words(text: str) -> int:
    """Count words in cleaned text."""
    words = text.split()
    return len(words)


def main():
    parser = argparse.ArgumentParser(
        description='Count readable words in an MDX article file'
    )
    parser.add_argument('file', help='Path to the MDX file')
    parser.add_argument(
        '--wpm', type=int, default=240,
        help='Words per minute for reading time calculation (default: 240)'
    )
    parser.add_argument(
        '--json', action='store_true', dest='as_json',
        help='Output as JSON'
    )
    args = parser.parse_args()

    try:
        with open(args.file) as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: file not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    readable_text = extract_readable_text(content)
    wc = count_words(readable_text)
    reading_time = round(wc / args.wpm)
    reading_time = max(reading_time, 1)  # minimum 1 minute

    if args.as_json:
        print(json.dumps({
            'wordCount': wc,
            'readingTime': reading_time,
            'wordsPerMinute': args.wpm,
            'file': args.file,
        }, indent=2))
    else:
        print(f"Words:        {wc:,}")
        print(f"Reading time: {reading_time} min (at {args.wpm} wpm)")


if __name__ == '__main__':
    main()
