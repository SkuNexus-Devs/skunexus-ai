#!/usr/bin/env python3
"""Unwrap markdown paragraphs into single lines, for posting as a GitHub PR description.

Why this exists: GitHub renders markdown in two modes. In a `.md` file in a repository a single
newline inside a paragraph collapses to a space, but in a PR description, an issue body or a comment
GFM turns that newline into a `<br>`. So the same text that reads well wrapped in an editor renders
as ragged, hard-broken lines once it is posted.

The pipeline that follows from this: keep `.ai/<TICKET>/pr.md` wrapped, because that is the file you
review in your editor — and unwrap only the stream that goes to `gh pr create/edit --body-file`.

Left untouched: the leading `---` frontmatter block, headings, table rows, list item markers, block
quotes and the inside of fenced code blocks. Wrapped continuations of a list item are joined onto the
item they belong to, and a paragraph keeps the indent of its first line — so a second paragraph
inside a list item stays inside that item.

Usage:
  md-paragraphs.py <file.md> --body            # frontmatter dropped + unwrapped -> stdout (for --body-file)
  md-paragraphs.py <file.md>                   # unwrapped, frontmatter kept -> stdout

Exits non-zero, printing nothing to stdout, when the file cannot be read or the body is empty.

Typical use with the PR skill — the script runs first and gh is called only if it succeeded:
  body="$(md-paragraphs.py .ai/PHG-446/pr.md --body)" && printf '%s\\n' "$body" | gh pr create --draft --base dev --title "<title>" --body-file -
"""

import argparse
import re
import sys
from pathlib import Path

BLOCK_LINE = re.compile(r'^(\s*(#{1,6} |\||>)|---\s*$|\s*```)')
LIST_ITEM = re.compile(r'^(\s*)([-*+] |\d+[.)] )')


def split_frontmatter(lines: list) -> tuple:
    """Return (frontmatter, rest); the leading `---` block is never re-flowed."""
    if not lines or lines[0].strip() != '---':
        return [], lines

    for index in range(1, len(lines)):
        if lines[index].strip() == '---':
            return lines[:index + 1], lines[index + 1:]

    return [], lines


def blocks(lines: list):
    """Yield (kind, payload) where kind is 'verbatim', 'paragraph' or 'list-item'.

    A paragraph arrives as (indent, joined text) and a list item as (indent, marker, joined text),
    so the caller only has to put the pieces back on one line.
    """
    pending = None
    in_fence = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith('```'):
            if pending:
                yield pending
                pending = None
            in_fence = not in_fence
            yield ('verbatim', line)
            continue

        if in_fence:
            yield ('verbatim', line)
            continue

        if not stripped:
            if pending:
                yield pending
                pending = None
            yield ('verbatim', line)
            continue

        list_match = LIST_ITEM.match(line)
        if list_match:
            if pending:
                yield pending
            pending = ('list-item', (list_match.group(1), list_match.group(2), stripped[len(list_match.group(2)):].strip()))
            continue

        if BLOCK_LINE.match(line):
            if pending:
                yield pending
                pending = None
            yield ('verbatim', line.rstrip())
            continue

        if pending:
            kind, payload = pending
            pending = (kind, payload[:-1] + (payload[-1] + ' ' + stripped,))
            continue

        indent = line[:len(line) - len(line.lstrip())]
        pending = ('paragraph', (indent, stripped))

    if pending:
        yield pending


def unwrap(text: str) -> str:
    frontmatter, lines = split_frontmatter(text.split('\n'))
    out = list(frontmatter)

    for kind, payload in blocks(lines):
        out.append(payload if kind == 'verbatim' else ''.join(payload))

    return '\n'.join(out)


def drop_frontmatter(text: str) -> str:
    frontmatter, lines = split_frontmatter(text.split('\n'))
    return '\n'.join(lines).lstrip('\n') if frontmatter else text


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('file', help='markdown file to unwrap')
    parser.add_argument('--body', action='store_true', help='drop the frontmatter and unwrap (what goes to --body-file)')
    args = parser.parse_args()

    result = unwrap(Path(args.file).read_text())

    if args.body:
        result = drop_frontmatter(result)

    if not result.strip():
        sys.exit(f'{args.file}: nothing to post, the body is empty.')

    print(result, end='' if result.endswith('\n') else '\n')


if __name__ == '__main__':
    main()
