"""
renumber-refs — Renumber inline citations and reference list in an MDX file.

Scans the article body for [N] citations in order of first appearance,
builds a mapping from old numbers to new sequential numbers, applies
the mapping to both inline citations and the numbered reference list.

Usage:
    renumber-refs <file> [--dry-run] [--json]

Options:
    --dry-run   Show the mapping without modifying the file
    --json      Output mapping as JSON
"""

import argparse
import re
import sys
from pathlib import Path


def extract_body_and_refs(content: str) -> tuple[str, str, str]:
    """Split content into body, references section, and trailing content."""
    refs_start = content.find("<ReferencesSection>")
    refs_end = content.find("</ReferencesSection>")

    if refs_start == -1 or refs_end == -1:
        return content, "", ""

    body = content[:refs_start]
    refs_block = content[refs_start : refs_end + len("</ReferencesSection>")]
    trailing = content[refs_end + len("</ReferencesSection>") :]

    return body, refs_block, trailing


def find_citation_order(body: str) -> list[int]:
    """Find all [N] citations in body text, return unique numbers in order of first appearance."""
    # Match [N] but not inside URLs, link syntax, or JSX props
    # We want citations like [1], [2], not [Link] or [Read guide →]
    citations = re.findall(r"\[(\d+)\]", body)
    seen = set()
    ordered = []
    for c in citations:
        n = int(c)
        if n not in seen:
            seen.add(n)
            ordered.append(n)
    return ordered


def parse_references(refs_block: str) -> dict[int, str]:
    """Parse numbered references from the ReferencesSection block."""
    # Extract content between tags
    inner = re.search(
        r"<ReferencesSection>\s*(.*?)\s*</ReferencesSection>",
        refs_block,
        re.DOTALL,
    )
    if not inner:
        return {}

    refs = {}
    # Match lines starting with a number followed by a period
    for match in re.finditer(r"^(\d+)\.\s+(.+)$", inner.group(1), re.MULTILINE):
        num = int(match.group(1))
        text = match.group(2).strip()
        refs[num] = text

    return refs


def apply_renumbering(
    body: str, refs: dict[int, str], citation_order: list[int]
) -> tuple[str, str, dict[int, int]]:
    """Apply renumbering to body and references. Returns (new_body, new_refs_block, mapping)."""

    # Build old→new mapping
    mapping = {}
    for new_num, old_num in enumerate(citation_order, start=1):
        mapping[old_num] = new_num

    # Replace in body using temp markers to avoid collisions
    new_body = body
    for old_num in mapping:
        new_body = new_body.replace(f"[{old_num}]", f"[__REF_{old_num}__]")
    for old_num, new_num in mapping.items():
        new_body = new_body.replace(f"[__REF_{old_num}__]", f"[{new_num}]")

    # Build new reference list
    new_refs_lines = []
    for new_num in sorted(mapping.values()):
        # Find which old number maps to this new number
        old_num = next(k for k, v in mapping.items() if v == new_num)
        if old_num in refs:
            new_refs_lines.append(f"{new_num}. {refs[old_num]}")

    # Check for orphaned references (in ref list but never cited in body)
    orphaned = set(refs.keys()) - set(mapping.keys())

    new_refs_block = "<ReferencesSection>\n" + "\n".join(new_refs_lines) + "\n</ReferencesSection>"

    return new_body, new_refs_block, mapping, orphaned


def main():
    parser = argparse.ArgumentParser(
        description="Renumber inline citations and reference list in an MDX file"
    )
    parser.add_argument("file", help="Path to the MDX file")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show mapping without modifying the file",
    )
    parser.add_argument(
        "--json", action="store_true", help="Output mapping as JSON"
    )
    args = parser.parse_args()

    filepath = Path(args.file)
    if not filepath.exists():
        print(f"Error: {filepath} not found", file=sys.stderr)
        sys.exit(1)

    content = filepath.read_text(encoding="utf-8")
    body, refs_block, trailing = extract_body_and_refs(content)

    if not refs_block:
        print("No <ReferencesSection> found in file.", file=sys.stderr)
        sys.exit(1)

    citation_order = find_citation_order(body)
    refs = parse_references(refs_block)

    if not citation_order:
        print("No inline citations [N] found in body text.", file=sys.stderr)
        sys.exit(1)

    new_body, new_refs_block, mapping, orphaned = apply_renumbering(
        body, refs, citation_order
    )

    if args.json:
        import json

        result = {
            "mapping": {str(k): v for k, v in mapping.items()},
            "orphaned_references": sorted(orphaned),
            "total_citations": len(citation_order),
            "total_references": len(refs),
        }
        print(json.dumps(result, indent=2))
    else:
        # Summary output
        changes = [(k, v) for k, v in mapping.items() if k != v]
        if not changes and not orphaned:
            print("References are already in order. No changes needed.")
        else:
            if changes:
                print("Renumbering:")
                for old, new in sorted(mapping.items(), key=lambda x: x[1]):
                    marker = " *" if old != new else ""
                    print(f"  [{old}] → [{new}]{marker}")
            if orphaned:
                print(f"\nOrphaned references (in list but never cited): {sorted(orphaned)}")
                print("These will be removed from the reference list.")

    if not args.dry_run:
        new_content = new_body + new_refs_block + trailing
        filepath.write_text(new_content, encoding="utf-8")
        if not args.json:
            print(f"\nFile updated: {filepath}")


if __name__ == "__main__":
    main()
