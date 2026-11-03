#!/usr/bin/env python3
"""Mechanical PRD check (rewrite stage and before approval).

Usage:
  python3 -I check-prd.py <prd.md> [--prev <older-prd.md>] [--lite]
  python3 -I check-prd.py --selftest

Checks: R ids in §4 run R1..Rmax with no gaps (retire, never delete); no duplicate R/AC ids;
every live R has >=1 AC in §6; no AC for an unknown R; no live AC under a retired R; no
placeholders; every cited R/AC/Q/J id resolves; every inline "(assumed, Qn)" marker has a §7
entry; with --prev, no R/AC id of the older version disappeared. --lite (prototype/requirements-lite.md):
§6 is optional and a requirement needs no AC. Exit 1 on errors.
Not checked: ids written with another ticket's key ("FFD-14 R31", "FFD-14's R26"), and every id on a
line whose bold lead names another ticket ("- **FFD-14 follow-up: …**").
"""
import argparse
import re
import sys

ID = r'(?:R\d+(?:\.[a-z]+)?|Q\d+[a-z]?|J-\d+)'
R_DEF = re.compile(r'^\s*(?:[-*]\s+)?(~~)?\*\*(R\d+)\*\*(.*)$')
AC_DEF = re.compile(r'^\s*(?:[-*]\s+)?(~~)?\*\*(R\d+)\.([a-z]+)\*\*(.*)$')
Q_DEF = re.compile(r'^\s*(?:(?:[-*]|\d+\.)\s+|\|\s*|#{3,6}\s+)?(?:~~)?(?:\*\*)?(Q\d+[a-z]?|J-\d+)\b')
CITE = re.compile(r'(?<![\w-])(' + ID + r')(?![\w-])')
# Ids owned by another ticket or a research file: "FFD-14 R24", "FFD-14 Q1/R26/R31", "research R3", "research/R2-…".
EXTERNAL = re.compile(r"(?:\b[A-Z][A-Z0-9]+-\d+(?:'s)?|\b[Rr]esearch)\s+" + ID +
                      r"(?:\s*(?:/|,|–|—|-|and|or|&|\+)\s*" + ID + r")*|\bresearch/R\d+")
# A line led by another ticket's key is about that ticket ("- **FFD-14 follow-up: …** … R26 … R31").
OTHER_LEAD = re.compile(r'^\s*(?:(?:[-*]|\d+\.)\s+)?(?:~~)?\*\*([A-Z][A-Z0-9]+-\d+)\b')
CODE_SPAN = re.compile(r'`[^`\n]*`')
QUOTED = re.compile(r'"[^"\n]*"|“[^”\n]*”')  # quoted literal text, e.g. an error message with "<uuid>" in it
COMMENT = re.compile(r'<!--.*?-->', re.S)
ASSUMED = re.compile(r'\(([^()]*\b(?:assumed|confirm with)\b[^()]*)\)', re.I)
HTML_TAGS = {'br', 'b', 'i', 'em', 'strong', 'sub', 'sup', 'details', 'summary', 'code', 'kbd', 's', 'u',
             'p', 'div', 'span', 'a', 'img', 'hr', 'table', 'tr', 'td', 'th', 'ul', 'ol', 'li', 'pre',
             'small', 'mark', 'del', 'ins'}
PLACEHOLDERS = [
    (re.compile(r'\b(TBD|TODO|FIXME)\b'), 'placeholder {0}'),
    (re.compile(r'\?\?\?'), 'placeholder ???'),
    (re.compile(r'<(?:…|\.\.\.)>|<(/?)([A-Za-z_][^<>\n]{0,60})>'), 'template leftover {0}'),
    (re.compile(r'^\s*[-*]\s+(?:\*\*[^*]+\*\*\s*)?(?:…|\.\.\.)\s*$'), 'empty template item'),
    (re.compile(r'(?:^\s*[-*]\s+|\|\s*|:\s*)\(?pending\)?\s*(?:\||$)', re.I), 'bare "pending" placeholder'),
]


def sections(lines):
    """Map '4', '6', '7' to (start, end) line indexes of the level-2 heading's body."""
    heads = [(i, m.group(1)) for i, l in enumerate(lines) if (m := re.match(r'^##\s+(\S+)', l))]
    out = {}
    for n, (i, title) in enumerate(heads):
        key = title.rstrip('.')
        end = heads[n + 1][0] if n + 1 < len(heads) else len(lines)
        out.setdefault(key, (i + 1, end))
    return out


def strip_code(line):
    return CODE_SPAN.sub(lambda m: ' ' * len(m.group(0)), line)


def parse(path, lite=False):
    text = open(path, encoding='utf-8').read()
    lines = text.split('\n')
    sec = sections(lines)
    title = re.search(r'(?m)^#\s.*?\b([A-Z][A-Z0-9]+-\d+)\b', text)
    doc = {'path': path, 'lines': lines, 'sec': sec, 'errors': [], 'warnings': [],
           'R': {}, 'AC': {}, 'Q': {}, 'key': title.group(1) if title else None, 'lite': lite}
    for want in ('4', '7') if lite else ('4', '6', '7'):
        if want not in sec:
            doc['errors'].append(f'no "## {want}." section found; checks that need it are skipped')

    def body(key):
        a, b = sec.get(key, (0, 0))
        return range(a, b)

    for i in body('4'):
        if m := R_DEF.match(lines[i]):
            rid, rest = m.group(2), m.group(3)
            retired = bool(m.group(1)) or 'retired' in rest[:80].lower()
            if rid in doc['R']:
                doc['errors'].append(f'duplicate requirement {rid} (lines {doc["R"][rid]["line"]} and {i + 1})')
            else:
                doc['R'][rid] = {'line': i + 1, 'retired': retired}
    for i in body('6'):
        if m := AC_DEF.match(lines[i]):
            aid, rest = f'{m.group(2)}.{m.group(3)}', m.group(4)
            retired = bool(m.group(1)) or 'retired' in rest[:80].lower()
            if aid in doc['AC']:
                doc['errors'].append(f'duplicate AC {aid} (lines {doc["AC"][aid]["line"]} and {i + 1})')
            else:
                doc['AC'][aid] = {'line': i + 1, 'retired': retired, 'req': m.group(2)}
    for i in body('7'):
        if m := Q_DEF.match(lines[i]):
            doc['Q'].setdefault(m.group(1), {'line': i + 1, 'text': lines[i]})
    return doc


def check(doc):
    lines, R, AC, Q = doc['lines'], doc['R'], doc['AC'], doc['Q']
    err, warn = doc['errors'], doc['warnings']

    nums = sorted(int(r[1:]) for r in R)
    for n in range(1, (nums[-1] if nums else 0) + 1):
        if f'R{n}' not in R:
            err.append(f'R{n} missing from §4 (a deleted id must stay, marked retired)')
    by_req = {}
    for aid, a in AC.items():
        by_req.setdefault(a['req'], []).append(aid)
        if a['req'] not in R:
            err.append(f'AC {aid} (line {a["line"]}) proves unknown requirement {a["req"]}')
        elif R[a['req']]['retired'] and not a['retired']:
            err.append(f'AC {aid} (line {a["line"]}) is live but {a["req"]} is retired')
    for rid, r in R.items():
        live_acs = [x for x in by_req.get(rid, []) if not AC[x]['retired']]
        if not r['retired'] and not live_acs and not doc['lite']:
            err.append(f'{rid} (line {r["line"]}) is live but has no AC in §6')
        letters = sorted(x.split('.')[1] for x in by_req.get(rid, []))
        if letters and all(len(c) == 1 for c in letters):
            gaps = [chr(c) for c in range(ord('a'), ord(letters[-1])) if chr(c) not in letters]
            if gaps:
                warn.append(f'{rid}: AC letters skip {", ".join(rid + "." + g for g in gaps)} (retire, never delete)')

    s7 = doc['sec'].get('7', (0, 0))
    s4 = doc['sec'].get('4', (0, 0))
    in_comment = False
    assumed_markers, assumed_ids = 0, set()
    for i, raw in enumerate(lines):
        # HTML comments are template leftovers; report once, then ignore their content.
        if in_comment or '<!--' in raw:
            if not in_comment:
                err.append(f'line {i + 1}: template comment left in the PRD')
            in_comment = '-->' not in raw.split('<!--')[-1] if '<!--' in raw else '-->' not in raw
            continue
        line = strip_code(raw)
        unquoted = QUOTED.sub(lambda m: ' ' * len(m.group(0)), line)
        for rx, msg in PLACEHOLDERS:
            for m in rx.finditer(unquoted if msg.startswith('template') else line):
                if msg.startswith('template') and m.group(2) and m.group(2).split()[0].lower() in HTML_TAGS:
                    continue
                if msg.startswith('template') and m.group(2) and m.group(2).startswith(('http', 'mailto')):
                    continue
                err.append(f'line {i + 1}: {msg.format(m.group(0).strip())}')
        visible = EXTERNAL.sub(lambda m: ' ' * len(m.group(0)), line)
        if (lead := OTHER_LEAD.match(raw)) and lead.group(1) != doc['key']:
            visible = ''
        is_q_def = s7[0] <= i < s7[1] and Q_DEF.match(raw)
        for m in CITE.finditer(visible):
            cid = m.group(1)
            if is_q_def and m.start() < 12 and cid == is_q_def.group(1):
                continue
            if cid.startswith('R') and '.' in cid:
                if cid not in AC:
                    err.append(f'line {i + 1}: cites {cid}, which is not an AC in §6')
            elif cid.startswith('R'):
                if cid not in R:
                    err.append(f'line {i + 1}: cites {cid}, which is not a requirement in §4')
            elif cid not in Q:
                err.append(f'line {i + 1}: cites {cid}, which has no entry in §7')
        if s4[0] <= i < s4[1]:
            for m in ASSUMED.finditer(visible):
                assumed_markers += 1
                ids = CITE.findall(m.group(1))
                qs = [x for x in ids if not x.startswith('R')]
                if not qs:
                    warn.append(f'line {i + 1}: assumption marker "({m.group(1)[:50]})" names no §7 id')
                for q in qs:
                    assumed_ids.add(q)
                    entry = Q.get(q)
                    if entry and not re.search(r'assum|confirm|default', entry['text'], re.I):
                        warn.append(f'line {i + 1}: {q} is assumed here, but its §7 entry (line {entry["line"]}) '
                                    f'states no assumption')
    doc['assumed_markers'], doc['assumed_ids'] = assumed_markers, assumed_ids
    a, b = s7
    doc['assumed_lines'] = sum(1 for l in lines[a:b] if re.search(r'\bAssumed\b', l))


def compare(doc, prev):
    for kind in ('R', 'AC'):
        gone = [x for x in prev[kind] if x not in doc[kind]]
        for x in sorted(gone, key=sort_key):
            doc['errors'].append(f'{x} existed in {prev["path"]} but is gone (retire it, never delete or renumber)')
        added = sorted((x for x in doc[kind] if x not in prev[kind]), key=sort_key)
        if added:
            doc['warnings'].append(f'new {kind} ids since prev ({len(added)}): {compact(added)}')


def sort_key(x):
    m = re.match(r'R(\d+)(?:\.([a-z]+))?', x)
    return (int(m.group(1)), len(m.group(2) or ''), m.group(2) or '')


def compact(ids):
    return ', '.join(ids) if len(ids) <= 12 else ', '.join(ids[:12]) + f', … (+{len(ids) - 12})'


def report(doc, prev_path=None):
    R, AC = doc['R'], doc['AC']
    r_ret = sum(r['retired'] for r in R.values())
    ac_ret = sum(a['retired'] for a in AC.values())
    qn = sum(1 for q in doc['Q'] if q.startswith('Q'))
    jn = len(doc['Q']) - qn
    print(f'check-prd: {doc["path"]}' + (f'  (prev: {prev_path})' if prev_path else ''))
    print(f'  R {len(R) - r_ret} live / {r_ret} retired · AC {len(AC) - ac_ret} live / {ac_ret} retired · '
          f'§7 ids Q {qn} / J {jn} · §4 assumption markers {doc["assumed_markers"]} '
          f'({len(doc["assumed_ids"])} ids) · §7 "Assumed" lines {doc["assumed_lines"]}')
    for label, items in (('ERROR', doc['errors']), ('warn', doc['warnings'])):
        for x in dict.fromkeys(items):
            print(f'  {label}: {x}')
    ne, nw = len(set(doc['errors'])), len(set(doc['warnings']))
    print(f'  result: {"FAIL" if ne else "OK"} ({ne} errors, {nw} warnings)')
    return 1 if doc['errors'] else 0


def run(path, prev_path=None, lite=False):
    doc = parse(path, lite)
    check(doc)
    if prev_path:
        compare(doc, parse(prev_path))
    return doc


def selftest():
    import os
    import tempfile
    good = """# PRD: TK-1 — x
> Status: Draft
## 4. Requirements
- **R1** The system shall do A (assumed, Q1).
- **R2** (retired 2026-10-26: merged into R3)
- **R3** The system shall do B.
## 6. Acceptance Criteria
- **R1.a** Given A, when x, then y.
- **R2.a** (retired 2026-10-26, see R3.a)
- **R3.a** Given B, then R1.a still holds.
## 7. Open questions and assumptions
- **Q1** Is A right? Assumed: yes. FFD-14 R31/R31.a and FFD-14's R26 differ.
- **FFD-14 follow-up.** Its Q9 gives no line, and R31 offers none.
- **TK-1 note.** R1 holds.
"""
    bad = good.replace('- **R3.a** Given B, then R1.a still holds.\n', '- **R4.a** Given TBD, then R9.\n') \
              .replace('(assumed, Q1)', '(assumed, Q2)').replace('R1 holds', 'R8 holds')
    prev = good.replace('## 7.', '- **R1.b** old.\n## 7.', 1)
    with tempfile.TemporaryDirectory() as d:
        paths = {}
        for name, body in (('good', good), ('bad', bad), ('prev', prev)):
            paths[name] = os.path.join(d, name + '.md')
            open(paths[name], 'w').write(body)
        g = run(paths['good'])
        assert not g['errors'], g['errors']
        assert (len(g['R']), sum(r['retired'] for r in g['R'].values())) == (3, 1)
        b = run(paths['bad'])
        joined = '\n'.join(b['errors'])
        for needle in ('unknown requirement R4', 'R3 (line', 'placeholder TBD', 'cites R9', 'cites Q2', 'cites R8'):
            assert needle in joined, (needle, joined)
        p = run(paths['good'], paths['prev'])
        assert any('R1.b existed' in e for e in p['errors']), p['errors']
        lite = os.path.join(d, 'lite.md')
        open(lite, 'w').write('# Requirements (lite): TK-2\n## 4. Requirements\n- **R1** Req 1 in the ticket (assumed, Q1).\n'
                              '- **R2** Req 2 in the ticket.\n## 7. Open Questions\n- **Q1** Which? Assumed: the simplest.\n')
        assert not run(lite, lite=True)['errors'], run(lite, lite=True)['errors']
        assert any('no "## 6."' in e for e in run(lite)['errors'])
    print('selftest: OK')
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('prd', nargs='?')
    ap.add_argument('--prev')
    ap.add_argument('--lite', action='store_true', help='requirements-lite.md: §6 optional, no AC per R needed')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.prd:
        ap.error('prd path required')
    try:
        return report(run(a.prd, a.prev, a.lite), a.prev)
    except OSError as e:
        print(f'check-prd: cannot read: {e}')
        return 2


if __name__ == '__main__':
    sys.exit(main())
