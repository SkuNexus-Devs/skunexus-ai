#!/usr/bin/env python3
"""Mechanical contract check: prd.md, workflows.md, feedback.md, versions and view staleness.

Usage:
  python3 -I check-contract.py <TICKET_DIR | prd.md | snapshot | requirements-lite.md> [--prev <snapshot>]
  python3 -I check-contract.py --stale <view file>
  python3 -I check-contract.py --selftest

The model is ../references/model.md (§2 ids, §3 prd.md, §4 workflows.md, §5 versions, §6 feedback.md).
prd.md (check-prd.py's checks, unchanged in meaning): R ids in §4 run R1..Rmax with no gaps (retire, never
delete); no duplicate R/criterion ids; every live R has a criterion in §6 (not in a lite contract); no
criterion for an unknown R; no live criterion under a retired R; a full contract has a live R; criterion letters
run without holes (a … z, aa …); no placeholders or template comments;
every cited id resolves; every "(assumed, Qn)" marker names a §7 entry that states an assumption; an
"Assumed" §7 entry that names neither evidence nor a role to confirm it is a warning.
workflows.md (only when it exists; it defines the s and Part families): scenario, step and Parts tables;
trigger kinds; every live step has a live part and cites a live R or criterion; coverage both ways (every
live criterion, or in a lite contract every live requirement, is cited by a live step or listed under
"Not exercised" with a reason).
feedback.md (only when it exists; it defines the FB family): entry headings, types and statuses.
Versions (only under a header line that is exactly "> Versions:"; any other version header is legacy and
reported as information): line grammar; a snapshot per version; each line's changed/new/retired lists equal
the diff of its snapshot against the previous one; live edits since the newest snapshot are information in
a Draft and errors in an Approved contract; an id in a snapshot never disappears.
--prev <snapshot>: no R, criterion, Q/J, scenario, step or part of the older version disappeared.
--stale <view>: the view's stale ids against its "Built from" base (exit 0 current, 1 stale, 2 unreadable,
3 no base). run.md (model.md §8, only when it exists): each setting and value is known (workflow, mode, chain,
plan-fan-out; the workflow is one of the eight names), mode and chain agree with what the workflow fixes
(triage and re-pull fix nothing), and each History line reads "- <DATE> <setting> <old> → <new> (<who>)" or
"- <DATE> triaged v<N>: <n> items ruled (<who>)"; both are warnings. Every run prints the QA guard line
"open assumptions cited by live steps: <ids>": the §7 ids a live step cites that no entry marks Decided.
Lite = "> Status: Draft (lite)", or a legacy prototype/requirements-lite.md given as the path.
Not checked: ids written with another ticket's key ("FFD-14 R31", "FFD-14's R26"), every id on a line
whose bold lead names another ticket ("- **FFD-14 follow-up: …**"), and text in backticks (quoted text is
skipped only by the template-leftover check, as in check-prd.py). A criterion range cites every id in it:
"R1.a-c", "R1.a–R1.c", "R1.z-aa" (an unprefixed end after a spaced dash must be as long as the start).
The view hashes ("<file>@<hash>") are SHA-256 of the file with CRLF read as LF, first 8 hex.
Exit: 0 OK, 1 errors, 2 unreadable.
"""
import argparse
import hashlib
import os
import re
import sys
from datetime import date

# check-prd.py's patterns (unchanged).
ID = r'(?:R\d+(?:\.[a-z]+)?|Q\d+[a-z]?|J-\d+)'
R_DEF = re.compile(r'^\s*(?:[-*]\s+)?(~~)?\*\*(R\d+)\*\*(.*)$')
AC_DEF = re.compile(r'^\s*(?:[-*]\s+)?(~~)?\*\*(R\d+)\.([a-z]+)\*\*(.*)$')
Q_DEF = re.compile(r'^\s*(?:(?:[-*]|\d+\.)\s+|\|\s*|#{3,6}\s+)?(?:~~)?(?:\*\*)?(Q\d+[a-z]?|J-\d+)\b')
OTHER_LEAD = re.compile(r'^\s*(?:(?:[-*]|\d+\.)\s+)?(?:~~)?\*\*([A-Z][A-Z0-9]+-\d+)\b')
CODE_SPAN = re.compile(r'`[^`\n]*`')
QUOTED = re.compile(r'"[^"\n]*"|“[^”\n]*”')  # quoted literal text, e.g. an error message with "<uuid>" in it
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

# model.md §2.4 and §5.
FAMILY = {'R': r'R\d+(?:\.[a-z]+)?', 'Q': r'Q\d+[a-z]?|J-\d+', 's': r's\d+(?:\.\d+)?', 'Part': r'Part \d+',
          'FB': r'FB\d+'}
CONTRACT_ID = '(?:' + '|'.join(FAMILY.values()) + ')'
# Ids owned by another ticket or a research file: "FFD-14 R24", "FFD-14 Q1/R26/R31", "research R3", "research/R2-…".
EXTERNAL = re.compile(r"(?:\b[A-Z][A-Z0-9]+-\d+(?:'s)?|\b[Rr]esearch)\s+" + CONTRACT_ID +
                      r"(?:\s*(?:/|,|–|—|-|and|or|&|\+)\s*" + CONTRACT_ID + r")*|\bresearch/R\d+")
ANY_ID = re.compile(r'(?<![\w-])(' + CONTRACT_ID + r')(?![\w-])')
SNAP = re.compile(r'^(prd|workflows)-v(\d+(?:\.\d+)?)-(\d{4}-\d{2}-\d{2})\.md$')
VLINE = re.compile(r'^>\s*-\s+v(\d+(?:\.\d+)?)\s+(\S+)\s+(frozen|approved):\s*(.*?)\s*$')
LEGACY = re.compile(r'^>\s*(?:\*\*)?(?:Versions?\b|v\d+(?:\.\d+)?\s+\d{4}-|Changelog\b)', re.I)
TRIGGERS = {'user', 'system', 'schedule', 'integration'}
FB_TYPES = {'WRONG', 'CHOICE', 'SILENCE', 'CHANGE'}
FB_STATUS = re.compile(r'^(?:open\b|ruled v\d+(?:\.\d+)?\b|rejected v\d+(?:\.\d+)?:|withdrawn:)')
EVIDENCE = re.compile(r'evidence|confirm|owner|research|source|jira|input/|review/|§\s?\d|\.\w{1,4}:\d+|\.md\b', re.I)
# Criterion ranges (model.md §2): the same rule in check-plan.py and check-storyboard.py.
RANGE = re.compile(r'(?<![\w-])R(\d+)\.([a-z]+)(\s*)[–-](\s*)(R\1\.)?([a-z]+)(?![\w-])')
SEP = re.compile(r'^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)*\|?\s*$')
# run.md (model.md §8): each workflow and the (mode, chain) it fixes; each setting's values, the default first.
# "regular" is not a workflow: the regular route is skunexus-jira-prd, which writes no run.md.
WORKFLOWS = {'prd-storyboard-estimate': ('attended', 'whole'), 'prd-storyboard': ('attended', 'whole'),
             'lite-storyboard': ('lite', 'whole'), 'lite': ('lite', 'stage'), 'unattended': ('unattended', 'whole'),
             'storyboard-only': ('attended', 'stage'), 'triage': None, 're-pull': None}
SETTINGS = {'workflow': tuple(WORKFLOWS), 'mode': ('attended', 'unattended', 'lite'), 'chain': ('stage', 'whole'),
            'plan-fan-out': ('off', 'on')}
HISTORY = re.compile(r'^\s*[-*]\s+(\d{4}-\d{2}-\d{2})\s+(?:([\w-]+)\s+(\S+)\s+(?:→|->)\s+(\S+)|triaged v\d+(?:\.\d+)?: '
                     r'\d+ items? ruled)\s+\([^()]+\)\s*$')
DECIDED = re.compile(r'\bDecided\b')  # case-sensitive: an option tagged "[PO decided]" is still open


def cite_rx(fams):
    """Citation regex for the families whose defining file exists (R, Q always; s, Part, FB on demand)."""
    return re.compile(r'(?<![\w-])(' + '|'.join(FAMILY[f] for f in ('R', 'Q', *fams)) + r')(?![\w-])')


def lnum(s):
    n = 0
    for ch in s:
        n = n * 26 + ord(ch) - 96
    return n


def lstr(n):
    s = ''
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(97 + r) + s
    return s


def expand(text):
    """Write each criterion range out ('R1.a-c' -> 'R1.a, R1.b, R1.c'); a range that isn't one keeps its start."""
    def one(m):
        n, a, s1, s2, pre, b = m.groups()
        if (pre or len(b) == len(a) or not (s1 or s2) and len(b) <= 2) and lnum(b) >= lnum(a):
            return ', '.join(f'R{n}.{lstr(i)}' for i in range(lnum(a), lnum(b) + 1))
        return f'R{n}.{a} ' + m.group(0)[len(f'R{n}.{a}'):]
    return RANGE.sub(one, text)


def norm(text):
    return ' '.join(text.split())


def vkey(v):
    return tuple(int(x) for x in v.split('.'))


def sort_key(x):
    return [(0, int(t)) if t.isdigit() else (1, len(t), t) for t in re.split(r'(\d+)', x)]


def compact(ids):
    ids = sorted(ids, key=sort_key)
    return ', '.join(ids) if len(ids) <= 12 else ', '.join(ids[:12]) + f', … (+{len(ids) - 12})'


def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def sha8(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read().replace(b'\r\n', b'\n')).hexdigest()[:8]  # CRLF read as LF (model.md §5)


def blank(rx, line):
    return rx.sub(lambda m: ' ' * len(m.group(0)), line)


# ---------------------------------------------------------------- prd.md (check-prd.py, extended)

def sections(lines):
    """Map '4', '6', '7' to (start, end) line indexes of the level-2 heading's body; also every heading's title."""
    heads = [(i, m.group(1), l) for i, l in enumerate(lines) if (m := re.match(r'^##\s+(\S+)', l))]
    out, titles = {}, []
    for n, (i, title, line) in enumerate(heads):
        end = heads[n + 1][0] if n + 1 < len(heads) else len(lines)
        out.setdefault(title.rstrip('.'), (i + 1, end))
        titles.append((i + 1, end, line))
    return out, titles


def block(lines, i, end, stops):
    """A definition's text: its line plus indented continuation lines, whitespace-normalised (model.md §5)."""
    out, j = [lines[i]], i + 1
    while j < end and lines[j].strip() and lines[j][:1] in ' \t' and not any(rx.match(lines[j]) for rx in stops):
        out.append(lines[j])
        j += 1
    return norm(' '.join(out))


def status_of(lines):
    for l in lines:
        if m := re.match(r'^>?\s*\**Status\**:\**\s*(.*)$', l, re.I):
            return m.group(1).strip()
    return ''


def parse(path, lite=False, text=None):
    text = read(path) if text is None else text
    lines = text.split('\n')
    sec, titles = sections(lines)
    title = re.search(r'(?m)^#\s.*?\b([A-Z][A-Z0-9]+-\d+)\b', text)
    status = status_of(lines[:40])
    lite = lite or bool(re.match(r'Draft\b.*\(lite\)', status))
    doc = {'path': path, 'lines': lines, 'sec': sec, 'errors': [], 'warnings': [], 'status': status,
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
                doc['R'][rid] = {'line': i + 1, 'retired': retired, 'text': block(lines, i, sec['4'][1], [R_DEF])}
    for i in body('6'):
        if m := AC_DEF.match(lines[i]):
            aid, rest = f'{m.group(2)}.{m.group(3)}', m.group(4)
            retired = bool(m.group(1)) or 'retired' in rest[:80].lower()
            if aid in doc['AC']:
                doc['errors'].append(f'duplicate AC {aid} (lines {doc["AC"][aid]["line"]} and {i + 1})')
            else:
                doc['AC'][aid] = {'line': i + 1, 'retired': retired, 'req': m.group(2),
                                  'text': block(lines, i, sec['6'][1], [AC_DEF])}
    # §7, plus a Decision log kept as its own section ("## 8. Decision log", model.md §3).
    q_ranges = [sec['7']] if '7' in sec else []
    q_ranges += [(a, b) for a, b, l in titles if re.search(r'decision', l, re.I)
                 and not re.match(r'^##\s+[1-7]\b', l)]
    doc['q_ranges'] = q_ranges
    for a, b in q_ranges:
        for i in range(a, b):
            if m := Q_DEF.match(lines[i]):
                doc['Q'].setdefault(m.group(1), {'line': i + 1, 'text': lines[i], 'retired': False,
                                                 'block': block(lines, i, b, [Q_DEF])})
    return doc


def scan(doc, cite, resolve, prd=True):
    """check-prd.py's line pass: template comments, placeholders, citations; in prd.md also §4 markers."""
    lines, Q = doc['lines'], doc.get('Q', {})
    err, warn = doc['errors'], doc['warnings']
    where = '' if prd else os.path.basename(doc['path']) + ' '
    s7 = doc['sec'].get('7', (0, 0)) if prd else (0, 0)
    s4 = doc['sec'].get('4', (0, 0)) if prd else (0, 0)
    in_comment = False
    assumed_markers, assumed_ids = 0, set()
    for i, raw in enumerate(lines):
        # HTML comments are template leftovers; report once, then ignore their content.
        if in_comment or '<!--' in raw:
            if not in_comment:
                err.append(f'{where}line {i + 1}: template comment left in the {"PRD" if prd else "file"}')
            in_comment = '-->' not in raw.split('<!--')[-1] if '<!--' in raw else '-->' not in raw
            continue
        line = blank(CODE_SPAN, raw)
        unquoted = blank(QUOTED, line)
        for rx, msg in PLACEHOLDERS:
            for m in rx.finditer(unquoted if msg.startswith('template') else line):
                if msg.startswith('template') and m.group(2) and m.group(2).split()[0].lower() in HTML_TAGS:
                    continue
                if msg.startswith('template') and m.group(2) and m.group(2).startswith(('http', 'mailto')):
                    continue
                err.append(f'{where}line {i + 1}: {msg.format(m.group(0).strip())}')
        visible = blank(EXTERNAL, line)
        if (lead := OTHER_LEAD.match(raw)) and lead.group(1) != doc['key']:
            visible = ''
        is_q_def = s7[0] <= i < s7[1] and Q_DEF.match(raw)
        for m in cite.finditer(expand(visible)):
            cid = m.group(1)
            if is_q_def and m.start() < 12 and cid == is_q_def.group(1):
                continue
            if problem := resolve(cid):
                err.append(f'{where}line {i + 1}: {problem}')
        if s4[0] <= i < s4[1]:
            for m in ASSUMED.finditer(visible):
                assumed_markers += 1
                qs = [x for x in cite.findall(m.group(1)) if x.startswith(('Q', 'J-'))]
                if not qs:
                    warn.append(f'line {i + 1}: assumption marker "({m.group(1)[:50]})" names no §7 id')
                for q in qs:
                    assumed_ids.add(q)
                    entry = Q.get(q)
                    if entry and not re.search(r'assum|confirm|default', entry['text'], re.I):
                        warn.append(f'line {i + 1}: {q} is assumed here, but its §7 entry (line {entry["line"]}) '
                                    f'states no assumption')
    return assumed_markers, assumed_ids


def check_prd(doc):
    """check-prd.py's structural checks, plus the "Assumed names evidence or a role" warning (model.md §3)."""
    R, AC, Q = doc['R'], doc['AC'], doc['Q']
    err, warn = doc['errors'], doc['warnings']
    nums = sorted(int(r[1:]) for r in R)
    if '4' in doc['sec'] and not doc['lite'] and not any(not r['retired'] for r in R.values()):
        err.append('no live requirement in §4 (a contract states at least one "- **R1** …")')
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
        letters = {x.split('.')[1] for x in by_req.get(rid, [])}
        if gaps := [lstr(n) for n in range(1, max(map(lnum, letters), default=0)) if lstr(n) not in letters]:
            warn.append(f'{rid}: AC letters skip {compact(rid + "." + g for g in gaps)} (retire, never delete)')
    for qid, q in Q.items():
        if re.search(r'\bAssumed\b', q['block']) and not EVIDENCE.search(q['block']):
            warn.append(f'{qid} (line {q["line"]}) is Assumed but names neither its evidence nor who confirms it')
    a, b = doc['sec'].get('7', (0, 0))
    doc['assumed_lines'] = sum(1 for l in doc['lines'][a:b] if re.search(r'\bAssumed\b', l))


# ---------------------------------------------------------------- workflows.md (model.md §4)

def cells(line):
    s = line.strip()
    s = s[1:] if s.startswith('|') else s
    s = s[:-1] if s.endswith('|') and not s.endswith('\\|') else s
    return [x.strip().replace('\\|', '|') for x in re.split(r'(?<!\\)\|', s)]


def tables(lines, a, b):
    """[(header cells lowercased, [(line index, cells)])] for each markdown table in lines[a:b]."""
    out, i = [], a
    while i < b:
        if lines[i].lstrip().startswith('|') and i + 1 < b and SEP.match(lines[i + 1]):
            head, rows = [x.lower() for x in cells(lines[i])], []
            i += 2
            while i < b and lines[i].lstrip().startswith('|'):
                rows.append((i, cells(lines[i])))
                i += 1
            out.append((head, rows))
        else:
            i += 1
    return out


def bare(cell):
    return cell.replace('~~', '').replace('**', '').strip()


def row_retired(cl):
    return cl[0].startswith('~~') or any(x.lower().startswith(('(retired', 'retired')) for x in cl)


def col(head, name):
    return next((n for n, h in enumerate(head) if h.startswith(name)), None)


def parse_wf(path, text=None):
    text = read(path) if text is None else text
    lines = text.split('\n')
    sec, titles = sections(lines)
    key = re.search(r'(?m)^#\s.*?\b([A-Z][A-Z0-9]+-\d+)\b', text)
    wf = {'path': path, 'lines': lines, 'sec': {}, 'errors': [], 'warnings': [], 'key': key.group(1) if key else None,
          'scen': {}, 'steps': {}, 'parts': {}, 'notex': {}, 'has': set()}
    err = wf['errors']

    def add(kind, ident, entry, i):
        if ident in wf[kind]:
            err.append(f'workflows.md line {i + 1}: duplicate {ident} (first on line {wf[kind][ident]["line"]})')
        else:
            wf[kind][ident] = entry

    for a, b, head_line in titles:
        title = re.sub(r'^##\s+', '', head_line).strip()
        low = title.lower()
        if low.startswith('scenarios'):
            wf['has'].add('scenarios')
            for head, rows in tables(lines, a, b):
                for i, cl in rows:
                    if re.fullmatch(r's\d+', sid := bare(cl[0])):
                        add('scen', sid, {'line': i + 1, 'retired': row_retired(cl), 'text': norm(lines[i])}, i)
        elif low.startswith('parts'):
            wf['has'].add('parts')
            for head, rows in tables(lines, a, b):
                sc, st = col(head, 'scope'), col(head, 'status')
                for i, cl in rows:
                    if re.fullmatch(r'Part \d+', pid := bare(cl[0])):
                        add('parts', pid, {'line': i + 1, 'retired': row_retired(cl), 'text': norm(lines[i]),
                                           'scope': cl[sc] if sc is not None and sc < len(cl) else '',
                                           'status': cl[st] if st is not None and st < len(cl) else ''}, i)
        elif low.startswith('not exercised'):
            wf['has'].add('notex')
            for i in range(a, b):
                if not re.match(r'^\s*[-*]\s', lines[i]):
                    continue
                m = re.match(r'^\s*[-*]\s+(?:~~)?(?:\*\*)?(R\d+(?:\.[a-z]+)?)(?:\*\*)?\s*(?:[:—–]|\s-\s)\s*(.*)$', lines[i])
                if not m:
                    err.append(f'workflows.md line {i + 1}: a "Not exercised" item reads "- R<n>.<x>: <reason>"')
                elif not m.group(2).strip():
                    err.append(f'workflows.md line {i + 1}: "Not exercised" {m.group(1)} gives no reason')
                else:
                    wf['notex'].setdefault(m.group(1), {'line': i + 1})
        elif m := re.match(r'(s\d+)\b\.?', title):
            sid = m.group(1)
            wf['sec'].setdefault(sid, a)
            for head, rows in tables(lines, a, b):
                c = {k: col(head, k) for k in ('trigger', 'cites', 'part')}
                for k, n in c.items():
                    if n is None:
                        err.append(f'workflows.md line {a}: the step table under "## {sid}." has no {k.title()} column')
                for i, cl in rows:
                    if not re.fullmatch(r's\d+\.\d+', stid := bare(cl[0])):
                        continue
                    get = (lambda k: bare(cl[c[k]]) if c[k] is not None and c[k] < len(cl) else '')
                    add('steps', stid, {'line': i + 1, 'retired': row_retired(cl), 'text': norm(lines[i]),
                                        'section': sid, 'trigger': get('trigger').lower(), 'part': get('part'),
                                        'cites': set(ANY_ID.findall(expand(blank(EXTERNAL, get('cites')))))}, i)
    return wf


def check_wf(c):
    """Format and coverage both ways (model.md §4)."""
    wf, prd = c['wf'], c['prd']
    err, warn = wf['errors'], wf['warnings']
    for want, name in (('scenarios', 'Scenarios'), ('parts', 'Parts')):
        if want not in wf['has']:
            err.append(f'workflows.md: no "## {name}" section')
    for kind, rx in (('scen', r's(\d+)'), ('parts', r'Part (\d+)')):
        nums = {int(re.fullmatch(rx, x).group(1)) for x in wf[kind]}
        if nums and (gaps := [n for n in range(1, max(nums)) if n not in nums]):
            warn.append(f'workflows.md: {kind.replace("scen", "scenario")} numbers skip {gaps} (retire, never delete)')
    live_R = {r for r, v in prd['R'].items() if not v['retired']}
    live_AC = {a for a, v in prd['AC'].items() if not v['retired']}
    by_scen = {}
    for sid, st in wf['steps'].items():
        scen, n = sid.split('.')
        by_scen.setdefault(scen, []).append(int(n))
        where = f'workflows.md line {st["line"]}: step {sid}'
        if scen != st['section']:
            err.append(f'{where} sits under "## {st["section"]}." (a step belongs to its own scenario)')
        if scen not in wf['scen']:
            err.append(f'{where} belongs to {scen}, which is not in the Scenarios table')
        if st['retired']:
            continue
        if scen in wf['scen'] and wf['scen'][scen]['retired']:
            err.append(f'{where} is live but scenario {scen} is retired')
        if st['trigger'] not in TRIGGERS:
            err.append(f'{where}: trigger "{st["trigger"]}" is not one of {", ".join(sorted(TRIGGERS))}')
        if not re.fullmatch(r'Part \d+', st['part']):
            err.append(f'{where}: the Part cell reads "{st["part"]}", not one "Part <n>" (every step carries one)')
        elif st['part'] not in wf['parts']:
            err.append(f'{where}: {st["part"]} is not in the Parts table')
        elif wf['parts'][st['part']]['retired']:
            err.append(f'{where} is live but {st["part"]} is retired')
        if not st['cites'] & (live_R | live_AC):
            err.append(f'{where} cites no live requirement or criterion')
        if dead := sorted(x for x in st['cites'] if x in prd['R'] and x not in live_R
                          or x in prd['AC'] and x not in live_AC):
            warn.append(f'{where} cites retired {", ".join(dead)}')
    for scen, ns in by_scen.items():
        if gaps := [n for n in range(1, max(ns)) if n not in ns]:
            warn.append(f'workflows.md: {scen} step numbers skip {", ".join(f"{scen}.{n}" for n in gaps)} '
                        f'(retire, never delete)')
    for sid, s in wf['scen'].items():
        if not s['retired'] and not any(not st['retired'] for x, st in wf['steps'].items() if x.split('.')[0] == sid):
            err.append(f'workflows.md line {s["line"]}: scenario {sid} is live but has no live step')
    used = {st['part'] for st in wf['steps'].values() if not st['retired']}
    for pid, p in wf['parts'].items():
        if ids := ANY_ID.findall(expand(blank(EXTERNAL, p['scope']))):
            warn.append(f'workflows.md line {p["line"]}: {pid} Scope names ids ({", ".join(ids)}); '
                        f'Scope is plain sentences for the PO')
        if not p['retired'] and p['status'] and p['status'].lower() != 'live':
            warn.append(f'workflows.md line {p["line"]}: {pid} Status "{p["status"]}" is neither "live" nor "retired …"')
        if not p['retired'] and pid not in used:
            warn.append(f'workflows.md line {p["line"]}: {pid} is live but no live step carries it')
    # Coverage: every live criterion (lite: every live requirement) is exercised or listed as not exercised.
    cited = set().union(*(st['cites'] for st in wf['steps'].values() if not st['retired']))
    with_ac = {a.split('.')[0] for a in live_AC}
    need = {x: x in cited for x in live_R if prd['lite'] or x not in with_ac}
    if not prd['lite']:
        need.update((a, a in cited) for a in live_AC)
    for x, ok in sorted(need.items(), key=lambda kv: sort_key(kv[0])):
        if not ok and x not in wf['notex']:
            err.append(f'{x} is live but no live step cites it and it is not under "Not exercised"')
    for x, n in wf['notex'].items():
        where = f'workflows.md line {n["line"]}: "Not exercised" {x}'
        if x not in prd['R'] and x not in prd['AC']:
            continue  # the citation pass reports it
        if x not in live_R and x not in live_AC:
            warn.append(f'{where} is retired')
        elif x in cited:
            warn.append(f'{where} is cited by a live step')


# ---------------------------------------------------------------- feedback.md (model.md §6)

def parse_fb(path, text=None):
    text = read(path) if text is None else text
    lines = text.split('\n')
    fb = {'path': path, 'lines': lines, 'errors': [], 'warnings': [], 'entries': {}}
    cur = None
    for i, l in enumerate(lines):
        if l.startswith('### ') or l.startswith('## '):
            cur = None
            if not (m := re.match(r'^###\s+(~~)?(FB\d+)\b(.*)$', l)):
                continue
            parts = [x.strip() for x in m.group(3).replace('~~', '').split('·')]
            parts = parts[1:] if parts and not parts[0] else parts
            cur = {'line': i + 1, 'retired': bool(m.group(1)), 'type': parts[0] if parts else '',
                   'date': parts[-1] if len(parts) >= 3 else '', 'fields': {}}
            if m.group(2) in fb['entries']:
                fb['errors'].append(f'feedback.md line {i + 1}: duplicate {m.group(2)}')
                cur = None
                continue
            fb['entries'][m.group(2)] = cur
        elif cur is not None and (m := re.match(r'^\s*[-*]\s+\*\*([A-Za-z ]+):\*\*\s*(.*)$', l)):
            cur['fields'].setdefault(m.group(1).strip().lower(), (i + 1, m.group(2).strip()))
    return fb


def check_fb(c, resolve, cite):
    fb = c['fb']
    err, warn = fb['errors'], fb['warnings']
    nums = sorted(int(x[2:]) for x in fb['entries'])
    if nums and (gaps := [n for n in range(1, nums[-1]) if n not in nums]):
        warn.append(f'feedback.md: FB numbers skip {", ".join(f"FB{n}" for n in gaps)} (withdraw, never delete)')
    for fid, e in fb['entries'].items():
        where = f'feedback.md line {e["line"]}: {fid}'
        if e['type'] not in FB_TYPES:
            err.append(f'{where}: type "{e["type"]}" is not one of {", ".join(sorted(FB_TYPES))}')
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', e['date']):
            err.append(f'{where}: the heading reads "### {fid} · <TYPE> · <source> · <YYYY-MM-DD>"')
        for f in ('what', 'status'):
            if f not in e['fields']:
                err.append(f'{where} has no **{f.title()}:** line')
        if 'cites' not in e['fields'] and e['type'] != 'CHANGE':
            warn.append(f'{where} has no **Cites:** line')
        if 'status' in e['fields'] and not FB_STATUS.match(e['fields']['status'][1]):
            err.append(f'feedback.md line {e["fields"]["status"][0]}: {fid} status "{e["fields"]["status"][1][:40]}" '
                       f'is not open · ruled v<N> (…) → <ids> · rejected v<N>: … · withdrawn: …')
        for f in ('cites', 'status'):
            if f in e['fields']:
                n, val = e['fields'][f]
                val = val.split('→', 1)[1] if f == 'status' and '→' in val else ('' if f == 'status' else val)
                for cid in cite.findall(expand(blank(EXTERNAL, blank(CODE_SPAN, val)))):
                    if problem := resolve(cid):
                        err.append(f'feedback.md line {n}: {problem}')


# ---------------------------------------------------------------- ids, snapshots, diffs (model.md §5)

def defs(prd, wf=None):
    """id -> {text, retired, kind, ...}: the text that versions and staleness compare."""
    out = {}
    for kind in ('R', 'AC', 'Q'):
        for k, v in prd[kind].items():
            out[k] = {'text': v['block'] if kind == 'Q' else v['text'], 'retired': v['retired'], 'kind': kind}
    for kind in ('scen', 'steps', 'parts') if wf else ():
        for k, v in wf[kind].items():
            out[k] = {'text': v['text'], 'retired': v['retired'], 'kind': kind,
                      'trigger': v.get('trigger'), 'cites': v.get('cites', set())}
    return out


def diff(old, new):
    """id -> 'new' | 'text' | 'retired' | 'gone'."""
    out = {}
    for k, v in new.items():
        if k not in old:
            out[k] = 'new'
        elif v['retired'] and not old[k]['retired']:
            out[k] = 'retired'
        elif v['text'] != old[k]['text']:
            out[k] = 'text'
    out.update((k, 'gone') for k in old if k not in new)
    return out


def snapshots(tdir):
    """version -> {'prd': {date: path}, 'workflows': {date: path}} from the strict snapshot names only."""
    out, rd = {}, os.path.join(tdir, 'review')
    for f in sorted(os.listdir(rd)) if os.path.isdir(rd) else ():
        if m := SNAP.match(f):
            out.setdefault(m.group(2), {'prd': {}, 'workflows': {}})[m.group(1)][m.group(3)] = os.path.join(rd, f)
    return out


def snap_defs(snaps, v, d=None):
    s = snaps.get(v, {'prd': {}, 'workflows': {}})
    d = d or max(s['prd'], default=None)
    if d not in s['prd']:
        return None
    w = s['workflows'].get(d)
    return defs(parse(s['prd'][d]), parse_wf(w) if w else None)


KEYS = ('changed', 'new', 'retired', 'from')


def clauses(rest, n, err):
    """'[note; ]changed …; new …; retired …; from …' -> {key: set(ids)} (model.md §3)."""
    lists, order = {}, -1
    for cl in (x.strip() for x in rest.split(';')):
        m = re.match(r'^(changed|new|retired|from)\s+(.+)$', cl)
        items = [x.strip() for x in m.group(2).split(',')] if m else []
        rx = FAMILY['FB'] if m and m.group(1) == 'from' else CONTRACT_ID
        good = [x for x in items if re.fullmatch(rx, x)]
        if not m or (order < 0 and not good):
            if order >= 0 and cl:
                err.append(f'line {n}: version clause "{cl[:40]}" follows the id lists (note first, then '
                           f'changed; new; retired; from)')
            continue
        if KEYS.index(m.group(1)) <= order:
            err.append(f'line {n}: version clause "{m.group(1)}" is repeated or out of order (changed; new; retired; from)')
        order = KEYS.index(m.group(1))
        if bad := [x for x in items if x not in good]:
            err.append(f'line {n}: "{m.group(1)}" lists {", ".join(bad)}, which are not contract ids')
        lists.setdefault(m.group(1), set()).update(good)
    return lists


def check_versions(c):
    p, err, tdir = c['prd'], c['errors'], c['dir']
    lines = p['lines']
    end = next((i for i, l in enumerate(lines) if l.startswith('## ')), len(lines))
    strict = next((i for i in range(end) if lines[i].rstrip() == '> Versions:'), None)
    legacy = [i for i in range(end) if i != strict and LEGACY.match(lines[i])]
    if legacy:
        c['info'].append(f'line {legacy[0] + 1}: legacy version header: information only, never checked')
    c['vinfo'] = 'legacy header only (information only)' if legacy else 'none'
    if strict is None:
        return
    vl, j, bad = [], strict + 1, 0
    while j < end and re.match(r'^>\s*-\s', lines[j]):
        m = VLINE.match(lines[j])
        try:
            m and date.fromisoformat(m.group(2))
        except ValueError:
            m = None
        if not m:
            bad += 1
            err.append(f'line {j + 1}: version line does not read "> - v<N>[.<M>] <YYYY-MM-DD> <frozen|approved>: …"')
        else:
            vl.append({'v': m.group(1), 'date': m.group(2), 'kind': m.group(3), 'line': j + 1,
                       'lists': clauses(m.group(4), j + 1, err)})
        j += 1
    if not vl:
        bad or err.append(f'line {strict + 1}: "> Versions:" has no "> - v…" lines')
        return
    snaps = snapshots(tdir)
    distinct, lists = [], {}
    for e in vl:
        if distinct and vkey(e['v']) < vkey(distinct[-1]['v']):
            err.append(f'line {e["line"]}: v{e["v"]} comes after v{distinct[-1]["v"]} (versions only go up)')
            continue
        for k, ids in e['lists'].items():
            lists.setdefault(e['v'], {}).setdefault(k, set()).update(ids)
        if distinct and e['v'] == distinct[-1]['v']:
            continue  # approving a frozen version unchanged reuses its number and snapshot
        distinct.append(e)
        s = snaps.get(e['v'], {'prd': {}, 'workflows': {}})
        if e['date'] not in s['prd']:
            err.append(f'line {e["line"]}: v{e["v"]} has no snapshot review/prd-v{e["v"]}-{e["date"]}.md')
        if c['wf'] and e['date'] not in s['workflows'] and any(
                x['date'] in snaps.get(x['v'], {'workflows': {}})['workflows'] for x in distinct[:-1]):
            err.append(f'line {e["line"]}: v{e["v"]} has no snapshot review/workflows-v{e["v"]}-{e["date"]}.md')
    c['vinfo'] = f'{len(vl)} lines, v{distinct[0]["v"]} … v{distinct[-1]["v"]}'
    # Each version line's lists equal the diff between its snapshot and the previous one.
    for a, b in zip(distinct, distinct[1:]):
        old, new = snap_defs(snaps, a['v'], a['date']), snap_defs(snaps, b['v'], b['date'])
        if old is None or new is None:
            continue
        d = diff(old, new)
        if gone := [k for k, v in d.items() if v == 'gone']:
            err.append(f'line {b["line"]}: v{b["v"]}\'s snapshot drops {compact(gone)} (retire, never delete)')
        for k, kind in (('changed', 'text'), ('new', 'new'), ('retired', 'retired')):
            want = {x for x, v in d.items() if v == kind}
            listed = lists.get(b['v'], {}).get(k, set())
            if missing := want - listed:
                err.append(f'line {b["line"]}: v{b["v"]} does not list {k} {compact(missing)} '
                           f'(its snapshot differs from v{a["v"]})')
            if extra := listed - want:
                err.append(f'line {b["line"]}: v{b["v"]} lists {k} {compact(extra)}, but its snapshot shows no '
                           f'such change from v{a["v"]}')
    if c['fb']:
        for e in vl:
            if bad := e['lists'].get('from', set()) - set(c['fb']['entries']):
                err.append(f'line {e["line"]}: v{e["v"]} is from {compact(bad)}, not in feedback.md')
        for fid, e in c['fb']['entries'].items():
            st = e['fields'].get('status', (0, ''))[1]
            if (m := re.match(r'ruled v(\d+(?:\.\d+)?)', st)) and m.group(1) in {x['v'] for x in vl} \
                    and fid not in lists.get(m.group(1), {}).get('from', set()):
                c['warnings'].append(f'{fid} is ruled v{m.group(1)}, but the v{m.group(1)} line does not list it '
                                     f'under "from"')
    # Unversioned changes: live files against the newest snapshot.
    if not snaps:
        return
    newest = max(snaps, key=vkey)
    old = snap_defs(snaps, newest)
    if old is None:
        return
    d = diff(old, defs(p, c['wf']))
    if gone := [k for k, v in d.items() if v == 'gone']:
        err.append(f'{compact(gone)} existed in v{newest}\'s snapshot but gone (retire it, never delete or renumber)')
    if changes := sorted((k for k, v in d.items() if v != 'gone'), key=sort_key):
        msg = (f'unversioned change since v{newest}: ' + ', '.join(f'{k} ({d[k]})' for k in changes[:12]) +
               (f', … (+{len(changes) - 12})' if len(changes) > 12 else '') + ': cut a version')
        (err if p['status'].split()[:1] == ['Approved'] else c['info']).append(msg)


# ---------------------------------------------------------------- run.md and the QA guard (model.md §8, §7)

def check_run(c):
    """run.md, when it exists: known settings and values, mode and chain as the workflow fixes them, and History
    lines in their two forms. Warnings only."""
    path = os.path.join(c['dir'], 'run.md')
    if not os.path.isfile(path):
        return
    lines, warn, seen = read(path).split('\n'), c['warnings'], {}
    for head, rows in tables(lines, 0, len(lines)):
        s, v = col(head, 'setting'), col(head, 'value')
        for i, cl in rows if s is not None and v is not None else ():
            name, val = (bare(cl[n]).strip('`') if n < len(cl) else '' for n in (s, v))
            if name not in SETTINGS:
                warn.append(f'run.md line {i + 1}: unknown setting "{name}" (settings: {", ".join(SETTINGS)})')
            elif val not in SETTINGS[name]:
                warn.append(f'run.md line {i + 1}: {name} "{val}" is not one of {", ".join(SETTINGS[name])}')
            else:
                seen[name] = (val, i)
    for n, (name, want) in enumerate(zip(('mode', 'chain'), WORKFLOWS.get(seen.get('workflow', ('',))[0]) or ())):
        if name in seen and seen[name][0] != want:
            warn.append(f'run.md line {seen[name][1] + 1}: {name} "{seen[name][0]}" contradicts workflow '
                        f'{seen["workflow"][0]}, which fixes {name} {want}')
    for a, b, head in sections(lines)[1]:
        for i in range(a, b) if re.match(r'^##\s+History\b', head, re.I) else ():
            if not re.match(r'^\s*[-*]\s', lines[i]):
                continue
            m = HISTORY.match(lines[i])
            if not m or m.group(2) and (m.group(2) not in SETTINGS or {m.group(3), m.group(4)} - set(SETTINGS[m.group(2)])):
                warn.append(f'run.md line {i + 1}: History line does not read "- <YYYY-MM-DD> <setting> <old> → <new> '
                            f'(<who>)" or "- <YYYY-MM-DD> triaged v<N>: <n> items ruled (<who>)"')
    c['run'] = ' · '.join(f'{k} {seen[k][0]}' if k in seen else f'{k} none' if k == 'workflow' else
                          f'{k} {v[0]} (default)' for k, v in SETTINGS.items())


def open_cited(c):
    """The QA guard: §7 ids a live step cites that no entry marks Decided (an assumed chip never becomes an
    expected result). Empty without workflows.md."""
    p = c['prd']
    if not c['wf']:
        return []
    decided = {m.group(1) for a, b in p['q_ranges'] for i in range(a, b)
               if (m := Q_DEF.match(p['lines'][i])) and DECIDED.search(block(p['lines'], i, b, [Q_DEF]))}
    cited = set().union(*(st['cites'] for st in c['wf']['steps'].values() if not st['retired']))
    return sorted((x for x in cited if x in p['Q'] and x not in decided), key=sort_key)


# ---------------------------------------------------------------- the contract

def load(target, lite=False):
    target = os.path.normpath(target)
    base, d = os.path.basename(target), os.path.dirname(target)
    wf_path, mode = None, 'file'
    if os.path.isdir(target) or base == 'prd.md':
        tdir = target if os.path.isdir(target) else d
        prd_path, wf_path, mode = os.path.join(tdir, 'prd.md'), os.path.join(tdir, 'workflows.md'), 'ticket'
    elif m := SNAP.match(base):
        prd_path = os.path.join(d, f'prd-v{m.group(2)}-{m.group(3)}.md')
        wf_path = os.path.join(d, f'workflows-v{m.group(2)}-{m.group(3)}.md')
        tdir = os.path.dirname(d) if os.path.basename(d) == 'review' else d
    else:
        prd_path, lite = target, lite or base == 'requirements-lite.md'
        tdir = os.path.dirname(d) if os.path.basename(d) in ('prototype', 'review') else d
    fb_path = os.path.join(tdir, 'feedback.md')
    return {'target': target, 'dir': tdir, 'mode': mode, 'prd': parse(prd_path, lite),
            'wf': parse_wf(wf_path) if wf_path and os.path.isfile(wf_path) else None,
            'fb': parse_fb(fb_path) if os.path.isfile(fb_path) else None,
            'errors': [], 'warnings': [], 'info': [], 'vinfo': 'not checked (single file)'}


def resolver(c):
    p, wf, fb = c['prd'], c['wf'], c['fb']

    def resolve(cid):
        if cid.startswith('R') and '.' in cid:
            return None if cid in p['AC'] else f'cites {cid}, which is not an AC in §6'
        if cid.startswith('R'):
            return None if cid in p['R'] else f'cites {cid}, which is not a requirement in §4'
        if cid.startswith(('Q', 'J-')):
            return None if cid in p['Q'] else f'cites {cid}, which has no entry in §7'
        if cid.startswith('FB'):
            return None if cid in fb['entries'] else f'cites {cid}, which is not an entry in feedback.md'
        if cid.startswith('Part'):
            return None if cid in wf['parts'] else f"cites {cid}, which is not in workflows.md's Parts table"
        if '.' in cid:
            return None if cid in wf['steps'] else f'cites {cid}, which is not a step in workflows.md'
        return None if cid in wf['scen'] else f'cites {cid}, which is not a scenario in workflows.md'
    return resolve


def compare(c, prev_path):
    """--prev: nothing of the older version disappeared (R, criteria, Q/J, scenarios, steps, parts)."""
    m = SNAP.match(os.path.basename(prev_path))
    pwf = os.path.join(os.path.dirname(prev_path), f'workflows-v{m.group(2)}-{m.group(3)}.md') if m else None
    old = defs(parse(prev_path), parse_wf(pwf) if pwf and os.path.isfile(pwf) else None)
    cur = defs(c['prd'], c['wf'])
    why = {'Q': 'a Q is never deleted: restore it as Decided, citing where the answer landed'}
    for x in sorted((x for x in old if x not in cur), key=sort_key):
        c['errors'].append(f'{x} existed in {prev_path} but is gone ({why.get(old[x]["kind"], "retire it, never delete or renumber")})')
    label = {'R': 'R', 'AC': 'AC', 'Q': 'Q/J', 'scen': 'scenario', 'steps': 'step', 'parts': 'part'}
    for kind, name in label.items():
        if added := [x for x in cur if x not in old and cur[x]['kind'] == kind]:
            c['warnings'].append(f'new {name} ids since prev ({len(added)}): {compact(added)}')


def run(target, prev_path=None, lite=False):
    c = load(target, lite)
    fams = (['s', 'Part'] if c['wf'] else []) + (['FB'] if c['fb'] else [])
    cite, resolve = cite_rx(fams), resolver(c)
    check_prd(c['prd'])
    c['assumed_markers'], c['assumed_ids'] = scan(c['prd'], cite, resolve)
    if c['wf']:
        scan(c['wf'], cite, resolve, prd=False)
        check_wf(c)
    if c['fb']:
        check_fb(c, resolve, cite)
    if c['mode'] == 'ticket':
        check_versions(c)
        check_run(c)
    c['open_cited'] = open_cited(c)
    if prev_path:
        compare(c, prev_path)
    return c


def collect(c, kind):
    return list(dict.fromkeys(c['prd'][kind] + (c['wf'][kind] if c['wf'] else []) +
                              (c['fb'][kind] if c['fb'] else []) + c[kind]))


def report(c, prev_path=None):
    p = c['prd']
    R, AC = p['R'], p['AC']
    r_ret, ac_ret = sum(r['retired'] for r in R.values()), sum(a['retired'] for a in AC.values())
    qn = sum(1 for q in p['Q'] if q.startswith('Q'))
    print(f'check-contract: {c["target"]}' + (f'  (prev: {prev_path})' if prev_path else ''))
    print(f'  R {len(R) - r_ret} live / {r_ret} retired · AC {len(AC) - ac_ret} live / {ac_ret} retired · '
          f'§7 ids Q {qn} / J {len(p["Q"]) - qn} · §4 assumption markers {c["assumed_markers"]} '
          f'({len(c["assumed_ids"])} ids) · §7 "Assumed" lines {p["assumed_lines"]}' + (' · lite' if p['lite'] else ''))
    if w := c['wf']:
        def lr(k):
            n = sum(x['retired'] for x in w[k].values())
            return f'{len(w[k]) - n} live / {n} retired'
        print(f'  workflows.md: scenarios {lr("scen")} · steps {lr("steps")} · parts {lr("parts")} · '
              f'not exercised {len(w["notex"])}')
    else:
        print('  workflows.md: none (s and Part ids not checked)')
    if f := c['fb']:
        n_open = sum(1 for e in f['entries'].values() if e['fields'].get('status', (0, ''))[1].startswith('open'))
        print(f'  feedback.md: FB {len(f["entries"])} ({n_open} open)')
    print(f'  versions: {c["vinfo"]}')
    if c.get('run'):
        print(f'  run.md: {c["run"]}')
    print(f'  open assumptions cited by live steps: {", ".join(c["open_cited"])}'.rstrip())
    errors, warnings = collect(c, 'errors'), collect(c, 'warnings')
    for label, items in (('ERROR', errors), ('warn', warnings), ('info', c['info'])):
        for x in dict.fromkeys(items):
            print(f'  {label}: {x}')
    print(f'  result: {"FAIL" if errors else "OK"} ({len(errors)} errors, {len(warnings)} warnings)')
    return 1 if errors else 0


# ---------------------------------------------------------------- --stale <view> (model.md §5, interface I2)

def built_from(text):
    if m := re.search(r"\bBUILT_FROM\s*=\s*(['\"`])(.*?)\1", text):
        return m.group(2)
    if m := re.search(r'(?m)^>\s*Built from:\s*(.+?)\s*$', text):
        return m.group(1)
    lines = text.split('\n')
    for head, rows in tables(lines, 0, len(lines)):
        if (n := col(head, 'built from')) is not None and rows:
            return rows[-1][1][n] if n < len(rows[-1][1]) else ''
    return None


def view_kind(view):
    base, parent = os.path.basename(view), os.path.basename(os.path.dirname(os.path.abspath(view)))
    if parent == 'prototype' and (base.endswith(('.html', '.htm')) or base == 'artifact.md'):
        return 'storyboard'
    return {'backend-plan.md': 'plan', 'frontend-plan.md': 'fe', 'estimate.md': 'estimate'}.get(base)


def in_scope(kind, x, newest):
    """Coverage scope per view (model.md §1 table): a new id here makes the view stale."""
    v = newest[x]
    if v['retired']:
        return False
    if kind == 'storyboard':
        return v['kind'] == 'steps' or v['kind'] == 'Q' and re.search(r'\bAssumed\b', v['text']) and any(
            x in s.get('cites', ()) for s in newest.values() if s['kind'] == 'steps' and not s['retired'])
    return {'plan': v['kind'] == 'AC', 'fe': v['kind'] == 'steps' and v.get('trigger') == 'user',
            'estimate': v['kind'] == 'parts'}.get(kind, False)


def stale(view):
    try:
        text = read(view)
    except (OSError, UnicodeDecodeError) as e:
        print(f'check-contract: cannot read: {e}')
        print('result: unreadable')
        return 2
    value = built_from(text)
    m = re.match(r'contract v(\d+(?:\.\d+)?) \((\d{4}-\d{2}-\d{2})\)', (value or '').strip().strip('`').strip())
    if not m:
        print(f'stale check: {view} has no "Built from: contract v…" base' + (f' ("{value[:40]}")' if value else ''))
        print('result: no base')
        return 3
    k, kdate = m.groups()
    d = os.path.dirname(os.path.abspath(view))
    tdir = os.path.dirname(d) if os.path.basename(d) == 'prototype' else d
    if not os.path.isfile(os.path.join(tdir, 'prd.md')):  # a template or a copy outside a ticket folder
        print(f'stale check: no contract (prd.md) next to {view}')
        print('result: no base')
        return 3
    snaps = snapshots(tdir)
    try:
        base = snap_defs(snaps, k, kdate)
        if base is None:
            raise OSError(f'no snapshot review/prd-v{k}-{kdate}.md for the base "contract v{k} ({kdate})"')
        chain = [(k, base)] + [(v, snap_defs(snaps, v)) for v in sorted(snaps, key=vkey) if vkey(v) > vkey(k)]
        chain = [(v, x) for v, x in chain if x is not None]
    except (OSError, UnicodeDecodeError) as e:
        print(f'check-contract: cannot read: {e}')
        print('result: unreadable')
        return 2
    events = {}
    for (_, a), (v, b) in zip(chain, chain[1:]):
        for x, kind in diff(a, b).items():
            events.setdefault(x, ({'text': 'changed', 'new': 'new', 'retired': 'retired', 'gone': 'gone'}[kind], v))
    newest = chain[-1][1]
    key = re.search(r'(?m)^#\s.*?\b([A-Z][A-Z0-9]+-\d+)\b', text)
    cited = set()
    for line in text.split('\n'):
        if (lead := OTHER_LEAD.match(line)) and (not key or lead.group(1) != key.group(1)):
            continue
        cited.update(ANY_ID.findall(expand(blank(EXTERNAL, line))))
    out = {}
    for x, (ev, v) in events.items():
        if x in cited and x in base and ev != 'new':
            out[x] = f'{ev} in v{v}'
        elif ev == 'new' and x in newest and in_scope(view_kind(view), x, newest):
            out[x] = f'new in v{v}'
    lines = [f'stale {x}: {r}' for x, r in sorted(out.items(), key=lambda kv: sort_key(kv[0]))]
    for name, h in re.findall(r'([\w./-]+)@([0-9a-f]{8})\b', value):
        path = next((p for p in (os.path.join(tdir, name), os.path.join(d, name)) if os.path.isfile(p)), None)
        if path is None:
            lines.append(f'stale {name}: {name} missing')
        elif sha8(path) != h:
            lines.append(f'stale {name}: {name} changed')
    for l in lines:
        print(l)
    print(f'result: {"stale" if lines else "current"}')
    return 1 if lines else 0


# ---------------------------------------------------------------- selftest

PRD1 = """# PRD: TK-1 — x

> Status: Draft
> Source: Jira TK-1 · research R1–R2
> Versions:
> - v1 2026-11-02 frozen: first draft

## 4. Requirements
- **R1** The system shall do A (assumed, Q1).
- **R2** (retired 2026-10-26: merged into R3)
- **R3** The system shall do B.

## 6. Acceptance Criteria
- **R1.a** Given A, when x, then y.
- **R2.a** (retired 2026-10-26, see R3.a)
- **R3.a** Given B, then R1.a still holds.
- **R3.b** The email subject carries no label.

## 7. Open questions and assumptions
- **Q1** Is A right? Assumed: yes. Evidence: jira/TK-1.md:3. FFD-14 R31/R31.a and FFD-14's R26 differ.
- **Q2** Which colour? Decided 2026-11-02 (developer, option A): blue → R1.a, s1.1.
- **FFD-14 follow-up.** Its Q9 gives no line, and R31 offers none.
"""
WF1 = """# Workflows: TK-1 — x

> Contract: versioned with prd.md (see its Versions line)

## Scenarios
| Id | Scenario | Actors |
|---|---|---|
| s1 | Happy path | warehouse user, system |

## s1. Happy path
| Step | Actor | Trigger | Before → after | Outcome | Cites | Part |
|---|---|---|---|---|---|---|
| s1.1 | warehouse user | user | — → open | sees A | R1, R1.a, Q1 | Part 1 |
| s1.2 | system | system | open → done | B happens | R3, R3.a | Part 1 |

## Parts
| Part | Name | Scope | PO's shape | Status |
|---|---|---|---|---|
| Part 1 | Base | Does A and B. | base | live |

## Not exercised
- R3.b: no user step shows it; proved by a test.
"""
V2_LINE = '> - v2 2026-11-03 approved: changed R1.a; new R1.b, s1.3; retired R3.b; from FB1'
PRD2 = (PRD1.replace('> Status: Draft', '> Status: Approved')
        .replace('frozen: first draft\n', 'frozen: first draft\n' + V2_LINE + '\n')
        .replace('when x, then y.', 'when x, then z.')
        .replace('- **R2.a**', '- **R1.b** Given A twice, then one z.\n- **R2.a**')
        .replace('- **R3.b** The email', '- **R3.b** (retired 2026-11-03: dropped) The email'))
WF2 = (WF1.replace('| Part 1 |\n\n## Parts', '| Part 1 |\n| s1.3 | warehouse user | user | open → open | sees one z '
                   '| R1.b | Part 1 |\n\n## Parts')
       .replace('\n## Not exercised\n- R3.b: no user step shows it; proved by a test.\n', ''))
FB = """# Feedback: TK-1

### FB1 · WRONG · BE plan draft · 2026-11-02
- **Cites:** R1.a
- **What:** R1.a's y is wrong.
- **Evidence:** research/R2-x.md:4
- **Proposed:** (A) z · (B) keep y
- **Status:** ruled v2 (developer, option A) → R1.a changed, R1.b new
"""


def selftest():
    import io
    import tempfile
    from contextlib import redirect_stdout

    def write(path, body):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(body)

    def ticket(root, name, prd, wf=None, fb=None, snaps=()):
        d = os.path.join(root, name)
        write(os.path.join(d, 'prd.md'), prd)
        wf and write(os.path.join(d, 'workflows.md'), wf)
        fb and write(os.path.join(d, 'feedback.md'), fb)
        for v, dt, p, w in snaps:
            write(os.path.join(d, 'review', f'prd-v{v}-{dt}.md'), p)
            w and write(os.path.join(d, 'review', f'workflows-v{v}-{dt}.md'), w)
        return d

    def errs(c):
        return '\n'.join(collect(c, 'errors'))

    def has(c, *needles, kind='errors'):
        text = '\n'.join(collect(c, kind) if kind != 'info' else c['info'])
        for n in needles:
            assert n in text, (n, text)

    def quiet(fn, *a):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = fn(*a)
        return rc, buf.getvalue()

    V = [('1', '2026-11-02', PRD1, WF1), ('2', '2026-11-03', PRD2, WF2)]
    with tempfile.TemporaryDirectory() as root:
        # 1. check-prd.py's own fixtures, unchanged in meaning (one file in place of the ticket dir).
        good = PRD1.replace('> Versions:\n> - v1 2026-11-02 frozen: first draft\n', '').replace(', s1.1.', '.') + \
            '- **TK-1 note.** R1 holds; Part 2 and FB3 are prose here (no workflows.md, no feedback.md).\n'
        bad = good.replace('- **R3.a** Given B, then R1.a still holds.\n', '- **R4.a** Given TBD, then R9.\n') \
                  .replace('- **R3.b** The email subject carries no label.\n', '') \
                  .replace('(assumed, Q1)', '(assumed, Q3)').replace('R1 holds', 'R8 holds')
        prev = good.replace('## 7.', '- **R1.b** old.\n## 7.', 1)
        for n, body in (('good', good), ('bad', bad), ('prev', prev)):
            write(os.path.join(root, 'one', n + '.md'), body)
        one = lambda n: os.path.join(root, 'one', n + '.md')
        g = run(one('good'))
        assert not errs(g), errs(g)
        assert (len(g['prd']['R']), sum(r['retired'] for r in g['prd']['R'].values())) == (3, 1)
        has(run(one('bad')), 'unknown requirement R4', 'R3 (line', 'placeholder TBD', 'cites R9', 'cites Q3', 'cites R8')
        has(run(one('good'), one('prev')), 'R1.b existed')
        lite_body = ('# Requirements (lite): TK-2\n## 4. Requirements\n- **R1** Req 1 in the ticket (assumed, Q1).\n'
                     '- **R2** Req 2 in the ticket.\n## 7. Open Questions\n- **Q1** Which? Assumed: the simplest. '
                     'Confirm with the PO.\n')
        write(os.path.join(root, 'lite', 'prototype', 'requirements-lite.md'), lite_body)
        assert not errs(run(os.path.join(root, 'lite', 'prototype', 'requirements-lite.md')))
        write(os.path.join(root, 'lite', 'other.md'), lite_body)
        has(run(os.path.join(root, 'lite', 'other.md')), 'no "## 6."')
        write(os.path.join(root, 'lite2', 'other.md'), lite_body.replace('TK-2\n', 'TK-2\n> Status: Draft (lite)\n'))
        assert run(os.path.join(root, 'lite2', 'other.md'))['prd']['lite']
        assert not errs(run(os.path.join(root, 'lite2', 'other.md')))
        # Assumed with neither evidence nor a role: a warning only.
        write(os.path.join(root, 'ev', 'prd.md'), good.replace('Evidence: jira/TK-1.md:3. ', ''))
        c = run(os.path.join(root, 'ev'))
        assert not errs(c), errs(c)
        has(c, 'Q1 (line', 'names neither', kind='warnings')
        # T13: ranges cite every id in them; letter holes past z; quoted ids are cited; an empty skeleton fails.
        assert expand('R1.a-c, R2.z–R2.ab; R3.z-aa; R6.a - needs') == 'R1.a, R1.b, R1.c, R2.z, R2.aa, R2.ab; ' \
            'R3.z, R3.aa; R6.a  - needs', expand('R1.a-c, R2.z–R2.ab; R3.z-aa; R6.a - needs')
        assert ANY_ID.findall(expand('Satisfies: R1.a-c')) == ['R1.a', 'R1.b', 'R1.c']
        write(os.path.join(root, 'rng', 'prd.md'), good.replace('Given B, then R1.a still holds.', 'Given B, R1.a-c.'))
        has(run(os.path.join(root, 'rng')), 'cites R1.b', 'cites R1.c')
        write(os.path.join(root, 'gap', 'prd.md'), good.replace('- **R2.a**', '- **R1.z** z.\n- **R1.aa** aa.\n- **R2.a**'))
        has(run(os.path.join(root, 'gap')), 'R1: AC letters skip R1.b, R1.c', kind='warnings')
        write(os.path.join(root, 'quo', 'prd.md'), good.replace('Given B, then', 'Given "R97" and `R98`, then'))
        assert 'cites R97' in errs(run(os.path.join(root, 'quo'))) and 'R98' not in errs(run(os.path.join(root, 'quo')))
        write(os.path.join(root, 'empty', 'prd.md'), '# PRD: TK-3\n\n## 4. Requirements\n\n## 6. AC\n\n## 7. Q\n')
        has(run(os.path.join(root, 'empty')), 'no live requirement in §4')

        # 2. A versioned ticket at v2, current: no errors, by dir, by prd.md and by snapshot path.
        t = ticket(root, 'v2', PRD2, WF2, FB, V)
        for target in (t, os.path.join(t, 'prd.md'), os.path.join(t, 'review', 'prd-v2-2026-11-03.md')):
            c = run(target)
            assert not errs(c) and not c['info'], (target, errs(c), c['info'])
        assert c['wf'] and run(t)['vinfo'].startswith('2 lines')
        # --prev: nothing disappeared since v1 (good); Q2 and s1.2 deleted (bad).
        c = run(t, os.path.join(t, 'review', 'prd-v1-2026-11-02.md'))
        assert not errs(c), errs(c)
        has(c, 'new AC ids since prev (1): R1.b', 'new step ids since prev (1): s1.3', kind='warnings')
        t = ticket(root, 'prev', PRD2.replace('- **Q2**', 'Q-two'), WF2.replace('| s1.2 |', '| x |'), FB, V)
        has(run(t, os.path.join(t, 'review', 'prd-v1-2026-11-02.md')), 'Q2 existed in', 'a Q is never deleted',
            's1.2 existed in')
        # Unversioned changes: an error when Approved, information in a Draft.
        edited = PRD2.replace('then R1.a still holds', 'then R1.a holds')
        has(run(ticket(root, 'unv', edited, WF2, FB, V)), 'unversioned change since v2: R3.a (text): cut a version')
        c = run(ticket(root, 'unv2', edited.replace('Status: Approved', 'Status: Draft'), WF2, FB, V))
        assert not errs(c), errs(c)
        has(c, 'unversioned change since v2: R3.a (text)', kind='info')
        # Version-line lists must equal the snapshot diffs.
        wrong = PRD2.replace(V2_LINE, '> - v2 2026-11-03 approved: changed R1.a, R3.a; new R1.b; from FB1')
        has(run(ticket(root, 'lists', wrong, WF2, FB, [V[0], ('2', '2026-11-03', wrong, WF2)])),
            'v2 does not list new s1.3', 'v2 lists changed R3.a', 'v2 does not list retired R3.b')
        # Grammar, missing snapshot, order, unknown "from".
        bad_v = PRD2.replace(V2_LINE, V2_LINE + '\n> - v3 2026-11-04 frozen: next\n> - v4 2026-13-01 approved: x\n'
                             '> - v2.1 2026-11-04 approved: new R1.b; changed R1.a\n> - v5 2026-11-05 approved: from FB9')
        has(run(ticket(root, 'gram', bad_v, WF2, FB, V)), 'v3 has no snapshot review/prd-v3-2026-11-04.md',
            'version line does not read', 'v2.1 comes after v3', 'is from FB9, not in feedback.md')
        c = run(ticket(root, 'cap', PRD2.replace(V2_LINE, '> - v2 2026-11-03 Approved: x').replace(
            '> - v1 2026-11-02 frozen: first draft', '> - v1 2026-11-02 Frozen: first draft'), WF2, FB, V))
        assert errs(c).count('version line does not read') == 2 and 'has no "> - v' not in errs(c), errs(c)
        has(run(ticket(root, 'order', PRD2.replace(V2_LINE, V2_LINE + '\n> - v3 2026-11-04 frozen: new R1.b; changed R1.a'),
                       WF2, FB, V)), 'repeated or out of order')
        # Legacy headers: information only, never an error (even with snapshots that differ).
        legacy = PRD2.replace('> Versions:\n> - v1 2026-11-02 frozen: first draft\n' + V2_LINE + '\n',
                              '> Version: v2 2026-11-03: applied the rulings\n').replace('then R1.a still', 'then R1.a now')
        c = run(ticket(root, 'legacy', legacy, WF2, FB, V))
        assert not errs(c), errs(c)
        has(c, 'legacy version header', kind='info')

        # 3. workflows.md format and coverage.
        plain = PRD1.replace('> Versions:\n> - v1 2026-11-02 frozen: first draft\n', '')
        assert not errs(run(ticket(root, 'wf-good', plain, WF1)))
        bad_wf = (WF1.replace('| user | — → open', '| click | — → open')
                  .replace('| R3, R3.a | Part 1 |', '| R3, R3.a | |')
                  .replace('| Part 1 | Base |', '| Part 1 | Base |')
                  + '\n## s2. Other\n| Step | Actor | Trigger | Before → after | Outcome | Cites | Part |\n'
                    '|---|---|---|---|---|---|---|\n| s2.1 | system | system | a → b | c | Q1 | Part 1 |\n'
                    '| s1.3 | system | system | a → b | c | R1.a | Part 3 |\n')
        has(run(ticket(root, 'wf-bad', plain, bad_wf)), 'trigger "click"', 'the Part cell reads ""',
            'step s2.1 belongs to s2, which is not in the Scenarios table', 'step s2.1 cites no live requirement',
            'step s1.3 sits under "## s2."', 'Part 3 is not in the Parts table', 'cites Part 3', 'cites s2,')
        retired_part = WF1.replace('| base | live |', '| base | live |\n| Part 2 | Old | Gone. | add-on | retired v2: merged |') \
                          .replace('| R3, R3.a | Part 1 |', '| R3, R3.a | Part 2 |')
        has(run(ticket(root, 'wf-ret', plain, retired_part)), 'step s1.2 is live but Part 2 is retired')
        has(run(ticket(root, 'cov', plain, WF1.replace('- R3.b: no user step shows it; proved by a test.', ''))),
            'R3.b is live but no live step cites it')
        has(run(ticket(root, 'cov2', plain, WF1.replace('- R3.b: no user step shows it; proved by a test.', '- R3.b:'))), 'gives no reason')
        lite_wf = WF1.replace('| R1, R1.a, Q1 |', '| R1, Q1 |').replace('| R3, R3.a |', '| R3 |')
        lite_prd = plain.replace('Status: Draft', 'Status: Draft (lite)')
        assert not errs(run(ticket(root, 'cov-lite', lite_prd, lite_wf)))
        has(run(ticket(root, 'cov-full', plain, lite_wf)), 'R1.a is live but no live step cites it')
        # Families only when their file exists: "Part 2" and "FB3" in prose resolve only against those files.
        prose = plain + '- **TK-1 note.** Part 2 and FB3 are prose.\n'
        assert not errs(run(ticket(root, 'fam0', prose)))
        has(run(ticket(root, 'fam1', prose, WF1, FB)), 'cites Part 2', 'cites FB3')

        # 3b. The QA guard: a live step cites assumed Q1 (listed) and decided Q2 (not); none without workflows.md.
        c = run(ticket(root, 'qa', plain, WF1.replace('| R1, R1.a, Q1 |', '| R1, R1.a, Q1, Q2 |')))
        assert c['open_cited'] == ['Q1'] and run(one('good'))['open_cited'] == [], c['open_cited']
        rc, out = quiet(report, c)
        assert '  open assumptions cited by live steps: Q1\n' in out, out
        assert '  open assumptions cited by live steps:\n' in quiet(report, run(one('good')))[1]
        # run.md: known settings and values pass; an unknown setting, a bad value and a bad History line warn.
        t = ticket(root, 'run', plain, WF1)
        good_run = ('# Run settings: TK-1\n\n| Setting | Value | Since | Set by |\n|---|---|---|---|\n'
                    '| mode | unattended | 2026-11-03 | developer |\n| `chain` | whole | 2026-11-03 | same |\n\n'
                    '## History\n- 2026-11-03 mode attended → unattended (developer)\n'
                    '- 2026-11-04 triaged v1: 6 items ruled (developer)\n')
        write(os.path.join(t, 'run.md'), good_run)
        c = run(t)
        assert not errs(c) and not c['warnings'] and c['run'] == \
            'workflow none · mode unattended · chain whole · plan-fan-out off (default)', \
            (errs(c), c['warnings'], c.get('run'))
        write(os.path.join(t, 'run.md'), good_run.replace('| whole |', '| all |') +
              '- 2026-11-04 triaged 6 items\n- 2026-11-04 mode attended → triage (developer)\n')
        c = run(t)
        assert not errs(c) and len(c['warnings']) == 3, (errs(c), c['warnings'])
        has(c, 'run.md line 6: chain "all" is not one of stage, whole', 'run.md line 11: History line does not read',
            'run.md line 12: History line', kind='warnings')
        write(os.path.join(t, 'run.md'), good_run.replace('| mode |', '| triage |'))
        has(run(t), 'unknown setting "triage"', kind='warnings')
        # Workflows: the eight names, mode and chain as the workflow fixes them, a workflow History line.
        wf_run = good_run.replace('| mode |', '| workflow | unattended | 2026-11-03 | developer |\n| mode |') + \
            '- 2026-11-04 workflow unattended → triage (developer)\n'
        write(os.path.join(t, 'run.md'), wf_run)
        c = run(t)
        assert not c['warnings'] and c['run'].startswith('workflow unattended · mode unattended'), (c['warnings'], c['run'])
        for name in ('triage', 're-pull'):  # follow-ups keep mode and chain
            write(os.path.join(t, 'run.md'), wf_run.replace('| workflow | unattended |', f'| workflow | {name} |'))
            assert not run(t)['warnings'], (name, run(t)['warnings'])
        write(os.path.join(t, 'run.md'), wf_run.replace('| workflow | unattended |', '| workflow | lite-storyboard |'))
        c = run(t)
        assert len(c['warnings']) == 1, c['warnings']
        has(c, 'run.md line 6: mode "unattended" contradicts workflow lite-storyboard, which fixes mode lite', kind='warnings')
        write(os.path.join(t, 'run.md'), wf_run.replace('| workflow | unattended |', '| workflow | storyboard-only |')
              .replace('| mode | unattended |', '| mode | attended |'))
        has(run(t), 'chain "whole" contradicts workflow storyboard-only, which fixes chain stage', kind='warnings')
        write(os.path.join(t, 'run.md'), wf_run.replace('| workflow | unattended |', '| workflow | regular |')
              .replace('→ triage (developer)', '→ full (developer)'))
        c = run(t)
        assert len(c['warnings']) == 2, c['warnings']
        has(c, 'run.md line 5: workflow "regular" is not one of prd-storyboard-estimate', 'run.md line 12: History line',
            kind='warnings')

        # 4. feedback.md format.
        bad_fb = FB + ('\n### FB2 · BUG · panel PD-2 · 2026-11-03\n- **Cites:** R9\n- **Status:** done\n'
                       '\n### FB4 · CHANGE · re-pull 2026-11-04 · CONTRADICTS\n- **What:** x\n- **Status:** open\n')
        has(run(ticket(root, 'fb', plain, WF1, bad_fb)), 'type "BUG"', 'FB2 has no **What:**', 'status "done"',
            'feedback.md line 11: cites R9', 'FB4: the heading reads')
        has(run(ticket(root, 'fb', plain, WF1, bad_fb)), 'FB numbers skip FB3', kind='warnings')

        # 5. --stale <view>, interface I2: the three reasons, current, no base, unreadable.
        t = ticket(root, 'st', PRD2, WF2, FB, V)
        write(os.path.join(t, 'frontend-plan.md'), '# FE plan\n\n> Built from: contract v1 (2026-11-02)\n\ns1.1\n')
        h = sha8(os.path.join(t, 'frontend-plan.md'))
        views = {
            'prototype/sb.html': ("const BUILT_FROM='contract v1 (2026-11-02)';\nconst S={id:'s1.1',c:['R1.a','R3.b']};\n"
                                  "// FFD-14 R1.a is foreign\n", 1,
                                  ['stale R1.a: changed in v2', 'stale R3.b: retired in v2', 'stale s1.3: new in v2']),
            'backend-plan.md': (f'# Plan\n\n> Built from: contract v2 (2026-11-03) · frontend-plan.md@{h}\n\nR1.a R3.b\n',
                                0, ['result: current']),
            'estimate.md': ('# Estimate\n\n> Built from: contract v1 (2026-11-02)\n\nPart 1\n', 0, ['result: current']),
            'frontend-plan.md': (None, 1, ['stale s1.3: new in v2']),
            'prototype/artifact.md': ('# Artifact\n\n| Version | Built from |\n|---|---|\n| v1 | `review/prd-v1.md` |\n'
                                      '| v2 | contract v2 (2026-11-03) |\n', 0, ['result: current']),
            'plan-old.md': ('# Plan\n\n> Built from: contract v1 (2026-11-02) · frontend-plan.md@00000000\n', 1,
                            ['stale frontend-plan.md: frontend-plan.md changed']),
            'notes.md': ('# Notes\n\nR1.a\n', 3, ['result: no base']),
            'prototype/old.html': ("const QT_SRC='PRD v2 §7';\n", 3, ['result: no base']),
            'gone.md': ('# x\n\n> Built from: contract v9 (2026-11-09)\n', 2, ['cannot read']),
        }
        for rel, (body, rc_want, needles) in views.items():
            body and write(os.path.join(t, rel), body)
            rc, out = quiet(stale, os.path.join(t, rel))
            assert rc == rc_want and all(n in out for n in needles), (rel, rc, out)
            assert 'R1.a' not in out or rel != 'prototype/sb.html' or out.count('R1.a') == 1
        crlf = os.path.join(t, 'frontend-crlf.md')  # a CRLF checkout of the same file hashes the same
        with open(crlf, 'wb') as f:
            f.write(open(os.path.join(t, 'frontend-plan.md'), 'rb').read().replace(b'\n', b'\r\n'))
        assert sha8(crlf) == h
        rng = os.path.join(t, 'range-plan.md')  # a range cites each id in it: 'R1.a-b' cites R1.a, which changed in v2
        write(rng, '# Plan\n\n> Built from: contract v1 (2026-11-02)\n\n**Satisfies:** R1.a-b\n')
        rc, out = quiet(stale, rng)
        assert rc == 1 and 'stale R1.a: changed in v2' in out, out
        bp = os.path.join(t, 'backend-plan.md')  # rebuilt-from-v1 plan: new criteria are in its scope
        write(bp, '# Plan\n\n> Built from: contract v1 (2026-11-02)\n\nR1.a\n')
        rc, out = quiet(stale, bp)
        assert rc == 1 and 'stale R1.a: changed in v2' in out and 'stale R1.b: new in v2' in out, out
        assert quiet(stale, os.path.join(t, 'missing.md'))[0] == 2
        lone = os.path.join(root, 'no-ticket', 'skeleton.html')  # a template: a base, but no contract beside it
        write(lone, "const BUILT_FROM='contract v1 (2026-01-15)';\n")
        rc, out = quiet(stale, lone)
        assert rc == 3 and 'no contract' in out, (rc, out)
    print('selftest: OK')
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('target', nargs='?', help='ticket dir, prd.md, a snapshot, or a legacy requirements-lite.md')
    ap.add_argument('--prev', help='an older snapshot: nothing in it may disappear')
    ap.add_argument('--stale', metavar='VIEW', help='list the view\'s stale ids (exit 0 current, 1 stale, 2 unreadable, 3 no base)')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.stale:
        return stale(a.stale)
    if not a.target:
        ap.error('a ticket dir or file is required')
    try:
        return report(run(a.target, a.prev), a.prev)
    except (OSError, UnicodeDecodeError) as e:
        print(f'check-contract: cannot read: {e}')
        return 2


if __name__ == '__main__':
    sys.exit(main())
