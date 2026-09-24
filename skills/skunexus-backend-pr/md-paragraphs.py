#!/usr/bin/env python3
"""Re-flow markdown paragraphs: unwrap them into single lines, or wrap them to a column width.

Why this exists: GitHub renders markdown in two modes. In a `.md` file in a repository a single
newline inside a paragraph collapses to a space, but in a PR description, an issue body or a comment
GFM turns that newline into a `<br>`. So the same text that reads well wrapped in an editor renders
as ragged, hard-broken lines once it is posted.

The pipeline that follows from this: keep `.ai/<TICKET>/pr.md` wrapped, because that is the file you
review in your editor — and unwrap only the stream that goes to `gh pr create/edit --body-file`.

Left untouched in every mode: the leading `---` frontmatter block, headings, table rows, list item
markers, block quotes and the inside of fenced code blocks. Wrapped continuations of a list item are
joined onto (or re-indented under) the item they belong to.

Usage:
  md-paragraphs.py <file.md> --body            # frontmatter dropped + unwrapped -> stdout (for --body-file)
  md-paragraphs.py <file.md>                   # unwrapped, frontmatter kept -> stdout
  md-paragraphs.py <file.md> --wrap 110        # wrapped to 110 columns -> stdout
  md-paragraphs.py <file.md> --wrap 110 --write  # ... written back in place

Typical use with the PR skill:
  md-paragraphs.py .ai/PHG-446/pr.md --body | gh pr create --draft --base dev --title "<title>" --body-file -
"""

import argparse
import re
import sys
import textwrap
from pathlib import Path

BLOCK_LINE = re.compile(r'^(#{1,6} |\||>|---\s*$|\s*```)')
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

    A paragraph or list item arrives as a single already-joined string, so each mode only has to
    decide how to lay it out again.
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
            if kind == 'paragraph':
                pending = ('paragraph', payload + ' ' + stripped)
            else:
                indent, marker, text = payload
                pending = ('list-item', (indent, marker, text + ' ' + stripped))
            continue

        pending = ('paragraph', stripped)

    if pending:
        yield pending


def reflow(text: str, width: int = None) -> str:
    frontmatter, lines = split_frontmatter(text.split('\n'))
    out = list(frontmatter)

    for kind, payload in blocks(lines):
        if kind == 'verbatim':
            out.append(payload)
        elif kind == 'paragraph':
            out.append(textwrap.fill(payload, width=width) if width else payload)
        else:
            indent, marker, item = payload
            if width:
                out.extend(textwrap.fill(
                    item,
                    width=width,
                    initial_indent=indent + marker,
                    subsequent_indent=indent + ' ' * len(marker)
                ).split('\n'))
            else:
                out.append(indent + marker + item)

    return '\n'.join(out)


def drop_frontmatter(text: str) -> str:
    frontmatter, lines = split_frontmatter(text.split('\n'))
    return '\n'.join(lines).lstrip('\n') if frontmatter else text


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('file', help='markdown file to re-flow')
    parser.add_argument('--body', action='store_true', help='drop the frontmatter and unwrap (what goes to --body-file)')
    parser.add_argument('--wrap', type=int, metavar='COLS', help='wrap paragraphs to COLS columns instead of unwrapping')
    parser.add_argument('--write', action='store_true', help='write the result back into the file')
    args = parser.parse_args()

    if args.body and args.wrap:
        sys.exit('--body and --wrap are mutually exclusive: a posted body is never wrapped.')
    if args.body and args.write:
        sys.exit('--body writes to stdout only; pipe it into `gh pr create/edit --body-file -`.')

    path = Path(args.file)
    result = reflow(path.read_text(), args.wrap)

    if args.body:
        result = drop_frontmatter(result)

    if args.write:
        path.write_text(result if result.endswith('\n') else result + '\n')
        print(f'written: {path}', file=sys.stderr)
    else:
        print(result, end='' if result.endswith('\n') else '\n')


if __name__ == '__main__':
    main()
