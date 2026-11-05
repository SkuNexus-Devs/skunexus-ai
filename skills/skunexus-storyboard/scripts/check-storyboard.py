#!/usr/bin/env python3
"""Static checks for a storyboard page (skunexus-storyboard).

Usage: python3 -I check-storyboard.py <page.html> [--contract <TICKET_DIR | prd file>] [--forbid <regex> ...]
       python3 -I check-storyboard.py --selftest
--prd <file> is the same as --contract <file>; the ticket dir is the file's folder (its parent for prototype/ and review/).

Every page: node --check on the inline script (when node exists); every #id the script looks up exists; no hours or
other forbidden strings; every A('<key>') has a QT entry; with a contract, cited R ids and QT keys exist in prd.md
('Dev x' as a '(x)' line in section 7) and QT text not verbatim in section 7 is a warning. A legacy page (no
BUILT_FROM) gets these checks only.
A v2 page (const BUILT_FROM='contract v<N> (<DATE>)') adds, per model.md section 2-5:
  - every scenario and step carries its id ('s1', 's1.3'), deep links ('#s1.3', '#s1') reach a drawn step or a
    scenario with one (a NOT_DRAWN step is no target), PARTS covers every part the page uses;
  - with a contract, read at the version BUILT_FROM names (its review/ snapshots, else the live files): cited R, Q, J-,
    s, Part and FB ids are defined and not retired (s and Part need workflows.md, FB needs feedback.md; foreign ids
    such as 'FFD-14 R31' are skipped; a range 'R1.a-c' cites R1.a, R1.b and R1.c); an undefined id that appears only in
    the page's own text (fake data such as 'Part 77'), not in a news or index citation, an A() key, a part tag, a step
    or a link, is a warning; each step's p:[n] is its workflows.md part; every live step has a page unless
    NOT_DRAWN={'s2.3':'why'} lists it; PARTS keys, names and scopes match workflows.md "Parts";
  - stale pages through ../../skunexus-contract/scripts/check-contract.py --stale (skipped when not installed).
const STAGE (a page without it is legacy): 'internal' (v1), 'approved' (v2), or 'discussion' (v1.x, shared with the PO
and the FE developer), which needs --contract and prototype/sn-baseline.md. Reviewed (run.md has a History line
"- <DATE> triaged v<N>: …" for the BUILT_FROM version): a Decided line for every scope-bearing Q (it names a Part, has an
option tagged expansion, or is Assumed naming an owner but no Evidence:) and no A('FB<n>') chip. Not reviewed (no such
line, a share before the triage): the .draft badge says 'not reviewed', and a missing review/presenter-*.md is a
warning. Any other value is an error.
Prints summary counts. Exit 1 on any error.
"""
import argparse
import difflib
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile

# Hours must never appear on the artifact (user rule). Tuned so the engine and the FFD-14 page stay clean.
HOUR_PATTERNS = [
    r'(?i)\bhours?\b',
    r'(?i)(?<!<)\bhrs?\b',                                       # not the <hr> tag
    r'\b\d+(?:\.\d+)?\s*[–-]\s*\d+(?:\.\d+)?\s*h\b',          # 16–20 h, 16-20h
    r'(?<![\w)\]$])\+\d+(?:\.\d+)?\s*[–-]\s*\d+(?:\.\d+)?\b',  # +1–1.5 (not code like i+1-2)
    r'\b\d+(?:\.\d+)?\s?h(?:rs?)?\b',                            # 12h, 1.5 h, 3 hr, 2.5hrs
]
RID = r'(?<![\w$.#-])R\d+(?:\.[a-z]+)?(?![\w$(=-])'         # criterion letters [a-z]+ (model.md 2.1); not 'R12-B'


# ---------- a tiny JS scanner: strings, template literals, comments, balanced brackets ----------
def skip_str(s, i):
    q, i = s[i], i + 1
    while i < len(s):
        if s[i] == '\\':
            i += 2
        elif q == '`' and s.startswith('${', i):
            i = match(s, i + 1)
        elif s[i] == q:
            return i + 1
        else:
            i += 1
    raise ValueError('unterminated string at %d' % i)


def skip_comment(s, i):
    if s.startswith('/*', i):
        j = s.find('*/', i + 2)
        return len(s) if j < 0 else j + 2
    if s.startswith('//', i):
        j = s.find('\n', i)
        return len(s) if j < 0 else j
    return None


def match(s, i):
    """s[i] is an opener; return the index just after its closer."""
    depth = 0
    while i < len(s):
        c = s[i]
        if c in '\'"`':
            i = skip_str(s, i)
            continue
        j = skip_comment(s, i)
        if j is not None:
            i = j
            continue
        if c in '{[(':
            depth += 1
        elif c in '}])':
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise ValueError('unbalanced bracket')


def items(s, i):
    """Top-level comma-separated items inside the bracket opening at s[i]."""
    end, out, j = match(s, i), [], i + 1
    start = j
    while j < end - 1:
        c = s[j]
        if c in '\'"`':
            j = skip_str(s, j)
            continue
        k = skip_comment(s, j)
        if k is not None:
            j = k
            continue
        if c in '{[(':
            j = match(s, j)
            continue
        if c == ',':
            out.append(s[start:j])
            start = j + 1
        j += 1
    out.append(s[start:end - 1])
    return [x.strip() for x in out if x.strip()]


def strip_comments(s):
    out, i, last = [], 0, 0
    while i < len(s):
        if s[i] in '\'"`':
            i = skip_str(s, i)
            continue
        j = skip_comment(s, i)
        if j is not None:
            out.append(s[last:i])
            i = last = j
            continue
        i += 1
    out.append(s[last:])
    return ''.join(out)


def decl(js, name):
    m = re.search(r'\b(?:const|let|var)\s+%s\s*=\s*([{\[])' % name, js)
    return m.start(1) if m else None


def js_string(v):
    v = v.strip()
    if v[:1] in ('\'', '"') and skip_str(v, 0) == len(v):
        return re.sub(r'\\(.)', r'\1', v[1:-1])
    return None


def obj_entries(js, name):
    """{key: string value or None} for a top-level object literal const."""
    i = decl(js, name)
    if i is None:
        return None
    out = {}
    for it in items(js, i):
        m = re.match(r'''(?s)(?:'([^']*)'|"([^"]*)"|([\w$]+))\s*:\s*(.*)''', it)
        if m:
            out[m.group(1) or m.group(2) or m.group(3)] = js_string(m.group(4))
    return out


def norm(t):
    t = html.unescape(re.sub(r'<[^>]+>', '', t)).replace('**', '').replace('`', '')
    t = t.translate(str.maketrans('‘’“”', '\'\'""'))
    return re.sub(r'\s+', ' ', t).strip().lower()


def prd_section7(prd):
    m = re.search(r'(?mi)^(#{1,3})\s*(?:7\b|.*open questions).*$', prd)
    if not m:
        return ''
    rest = prd[m.end():]
    n = re.search(r'(?m)^#{1,%d}\s' % len(m.group(1)), rest)
    return rest[:n.start()] if n else rest



def literals(code):
    """The text of every string literal in comment-free JS."""
    out, i = [], 0
    while i < len(code):
        if code[i] in '\'"`':
            j = skip_str(code, i)
            out.append(code[i + 1:j - 1])
            i = j
        else:
            i += 1
    return out


def props(src):
    """{key: raw value} for the top-level properties of an object literal '{…}'."""
    out = {}
    if not src.startswith('{'):
        return out
    for it in items(src, 0):
        m = re.match(r'''(?s)(?:'([^']*)'|"([^"]*)"|([\w$]+))\s*:\s*(.*)''', it)
        if m:
            out[m.group(1) or m.group(2) or m.group(3)] = m.group(4).strip()
    return out


# ---------- the contract (model.md 2.4 patterns) ----------
R_DEF = r'^\s*(?:[-*]\s+)?(~~)?\*\*(R\d+(?:\.[a-z]+)?)\*\*(.*)$'
Q_DEF = r'^\s*(?:(?:[-*]|\d+\.)\s+|\|\s*|#{3,6}\s+)?(?:~~)?(?:\*\*)?(Q\d+[a-z]?|J-\d+)\b'
_ONE = r'(?:R\d+(?:\.[a-z]+)?|Q\d+[a-z]?|J-\d+|s\d+(?:\.\d+)?|Part \d+|FB\d+)'
FOREIGN = (r"(?:\b[A-Z][A-Z0-9]+-\d+(?:'s)?|\b[Rr]esearch)\s+%s(?:\s*(?:/|,|–|—|-|and|or|&|\+)\s*%s)*|\bresearch/R\d+"
           % (_ONE, _ONE))
QID = r'(?<![\w$.#-])(?:Q\d+[a-z]?|J-\d+)(?![\w$(=-])'
FBID = r'(?<![\w$.#-])FB\d+(?![\w$(=-])'
# Criterion ranges (model.md 2): the same rule as check-contract.py and check-plan.py.
RANGE = re.compile(r'(?<![\w-])R(\d+)\.([a-z]+)(\s*)[–-](\s*)(R\1\.)?([a-z]+)(?![\w-])')
STAGES = ('internal', 'discussion', 'approved')
BASE = r"contract v(\d+(?:\.\d+)?) \((\d{4}-\d{2}-\d{2})\)(?: · [\w./-]+@[0-9a-f]{8})*"


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
            return ', '.join('R%s.%s' % (n, lstr(i)) for i in range(lnum(a), lnum(b) + 1))
        return 'R%s.%s ' % (n, a) + m.group(0)[len('R%s.%s' % (n, a)):]
    return RANGE.sub(one, text)


def split_cells(line):
    """A table row's cells, split as check-contract.py splits them (an escaped \\| stays in its cell)."""
    s = line.strip()[1:]
    s = s[:-1] if s.endswith('|') and not s.endswith('\\|') else s
    return [x.strip().replace('\\|', '|') for x in re.split(r'(?<!\\)\|', s)]


def md_tables(text):
    """[(header cells lower-cased, [row cells])] for each pipe table."""
    out, cur = [], None
    for line in text.splitlines():
        if line.lstrip().startswith('|'):
            cells = split_cells(line)
            if cur is None:
                cur = ([c.lower() for c in cells], [])
                out.append(cur)
            elif not all(re.fullmatch(r':?-+:?', c) for c in cells if c):
                cur[1].append(cells)
        else:
            cur = None
    return out


def parse_contract(prd, wf=None, fb=None):
    """ids {id: live?}, step parts {s1.3: n}, part texts {n: (name, scope)}, feedback {FB1: (status, what)}."""
    c = {'ids': {}, 'step_part': {}, 'parts': {}, 'fb': {}, 'wf': wf is not None, 'has_fb': fb is not None, 'prd': prd}
    ids = c['ids']
    for line in prd.splitlines():
        m = re.match(R_DEF, line)
        if m:
            ids.setdefault(m.group(2), not (m.group(1) or 'retired' in m.group(3)[:80].lower()))
        elif re.match(Q_DEF, line):
            ids.setdefault(re.match(Q_DEF, line).group(1), True)   # a Q is never retired (model.md 2.1)
    for head, rows in md_tables(wf or ''):
        col = lambda r, k: r[head.index(k)] if k in head and head.index(k) < len(r) else ''
        for r in rows:
            first = re.sub(r'[~*`]', '', r[0]).strip()
            live = not (r[0].startswith('~~') or any(re.match(r'(?i)\(?retired', x) for x in r[1:]))
            if re.fullmatch(r's\d+(?:\.\d+)?|Part \d+', first):
                ids.setdefault(first, live)
            if re.fullmatch(r's\d+\.\d+', first):
                m = re.search(r'Part (\d+)', col(r, 'part'))
                c['step_part'].setdefault(first, int(m.group(1)) if m else None)
            elif first.startswith('Part '):
                c['parts'].setdefault(int(first[5:]), (col(r, 'name'), col(r, 'scope')))
    for chunk in re.split(r'(?m)^(?=#{2,4}\s*(?:~~)?FB\d+\b)', fb or ''):
        m = re.match(r'#{2,4}\s*(~~)?(FB\d+)\b(.*)', chunk)
        if m:
            st = re.search(r'\*\*Status:\*\*\s*(.*)', chunk)
            what = re.search(r'\*\*What:\*\*\s*(.*)', chunk)
            ids.setdefault(m.group(2), not (m.group(1) or 'retired' in m.group(3)[:80].lower()))
            c['fb'].setdefault(m.group(2), (st.group(1).strip() if st else '', what.group(1).strip() if what else ''))
    return c


def load_contract(path, base=None):
    """The contract at version base=(N, DATE): its review/ snapshots when present, else the live files."""
    if os.path.isdir(path):
        d, prd_p = path, os.path.join(path, 'prd.md')
    else:
        prd_p, d = path, os.path.dirname(os.path.abspath(path))
        if os.path.basename(d) in ('prototype', 'review'):
            d = os.path.dirname(d)
    used, warn = [], []

    def pick(name, live):
        if base:
            s = os.path.join(d, 'review', '%s-v%s-%s.md' % (name, base[0], base[1]))
            if os.path.isfile(s):
                return s
        return live if os.path.isfile(live) else None

    def read(p):
        if p is None:
            return None
        used.append(os.path.relpath(p, d))
        with open(p, encoding='utf-8') as f:
            return f.read()
    p = pick('prd', prd_p)
    if p is None:
        raise OSError('no prd file: %s' % prd_p)
    if base and p == prd_p:
        warn.append(('contract', 'no snapshot review/prd-v%s-%s.md: checked against the live files' % base))
    c = parse_contract(read(p), read(pick('workflows', os.path.join(d, 'workflows.md'))),
                       read(os.path.join(d, 'feedback.md') if os.path.isfile(os.path.join(d, 'feedback.md')) else None))
    c.update(dir=d, used=used, warn=warn)
    return c


CONTRACT_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'skunexus-contract', 'scripts',
                               'check-contract.py')


def run_stale(view, script):
    """check-contract.py --stale (interface I2): (exit code, [(id, reason)], last line), or None when not installed."""
    if not os.path.isfile(script):
        return None
    r = subprocess.run([sys.executable, '-I', script, '--stale', view], capture_output=True, text=True, encoding='utf-8')
    out = r.stdout + r.stderr
    return r.returncode, re.findall(r'(?m)^stale (Part \d+|\S+): (.*)$', r.stdout), (out.strip().splitlines() or ['?'])[-1]


def nat(i):
    return [int(n) if n.isdigit() else n for n in re.split(r'(\d+)', i)]


def no_foreign(t):
    return expand(re.sub(FOREIGN, ' ', t))


# ---------- the checks ----------
def check(text, prd=None, forbid=(), contract=None, view=None, script=CONTRACT_SCRIPT):
    """contract: a ticket dir or prd file (read at the page's base version); prd: PRD text (selftest)."""
    err, warn, info = [], [], []
    scripts = re.findall(r'(?is)<script\b(?![^>]*\bsrc=)[^>]*>(.*?)</script>', text)
    js = '\n;\n'.join(scripts)
    if not scripts:
        err.append(('script', 'no inline <script> found'))
    markup = re.sub(r'(?is)<script\b.*?</script>|<style\b.*?</style>|<!--.*?-->', ' ', text)

    # 1. syntax
    node = shutil.which('node')
    if node and scripts:
        with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as f:
            f.write(js)
        r = subprocess.run([node, '--check', f.name], capture_output=True, text=True)
        os.unlink(f.name)
        if r.returncode:
            err.append(('syntax', 'node --check failed: ' + (r.stderr.strip().splitlines() or ['?'])[-1]))
        else:
            info.append('node --check: OK')
    else:
        warn.append(('syntax', 'node not found: syntax not checked'))

    try:
        code = strip_comments(js)
    except ValueError as e:
        err.append(('parse', str(e)))
        code = js

    # page version: a v2 page names its base (model.md 5); a legacy page gets the checks PR A ran
    bf = re.search(r'''\b(?:const|let|var)\s+BUILT_FROM\s*=\s*(['"`])(.*?)\1''', code)
    base = None
    if bf:
        m = re.fullmatch(BASE, bf.group(2))
        if m:
            base = (m.group(1), m.group(2))
        else:
            err.append(('BUILT_FROM', "BUILT_FROM='%s' is not 'contract v<N> (<DATE>)' [· <file>@<hash>]" % bf.group(2)))
    elif re.search(r'''\bid\s*:\s*['"]s\d+\.\d+['"]''', code):
        err.append(('BUILT_FROM', "the page has step ids (v2) but no const BUILT_FROM='contract v<N> (<DATE>)'"))
    v2 = bool(bf)
    c = None
    if contract is not None:
        c = load_contract(contract, base)
        prd = c['prd']
        warn += c['warn']
        info.append('contract: %s' % ', '.join(c['used']))
    info.append('page: %s' % ('v2, built from ' + bf.group(2) if v2 else 'legacy (no BUILT_FROM): no base, PR A checks only'))

    # 2. id lookups
    defined = set(re.findall(r'''\bid\s*=\s*["']([^"'$]+)["']''', text))
    prefixes = set(re.findall(r'''\bid\s*=\s*["']([\w-]*)\$\{''', text))
    refs = set()
    for sel in re.findall(r'''(?:\$\$?|querySelector(?:All)?|closest)\(\s*(['"`])(.*?)\1''', code):
        refs.update(re.findall(r'(?:^|[\s,>+~(])#([A-Za-z][\w-]*)', sel[1]))
    refs.update(re.findall(r'''getElementById\(\s*['"`]([\w-]+)''', code))
    for r_ in sorted(refs):
        ok = r_ in defined or (r_.endswith('-') and (r_ in prefixes or any(d.startswith(r_) for d in defined)))
        if not ok:
            err.append(('id', '#%s is looked up but no element has that id' % r_))
    info.append('ids: %d looked up, %d missing' % (len(refs), sum(1 for e in err if e[0] == 'id')))

    # 3. forbidden strings (hours + --forbid)
    hits = 0
    for pat in HOUR_PATTERNS + list(forbid):
        for m in re.finditer(pat, text):
            line = text.count('\n', 0, m.start()) + 1
            err.append(('forbidden', 'line %d: %r matches %s' % (line, m.group(0), pat)))
            hits += 1
    info.append('forbidden strings: %d hits (%d patterns)' % (hits, len(HOUR_PATTERNS) + len(forbid)))

    # 4. assumption chips vs QT
    qt = obj_entries(code, 'QT')
    a_calls = re.findall(r'''(?<![\w$.])A\(\s*(['"`])(.*?)\1\s*\)''', code)
    a_keys = {k for _, k in a_calls}
    data_q = set(re.findall(r'data-q="([^"$]+)"', text))
    if qt is None:
        if a_keys:
            err.append(('QT', 'A() is used but no QT object is declared'))
        qt = {}
    for k in sorted(a_keys - set(qt)):
        err.append(('QT', "A('%s') has no QT entry" % k))
    unused = sorted(set(qt) - a_keys - data_q)
    for k in unused:
        warn.append(('QT', "QT key '%s' is never used by A()" % k))

    # 5. PRD cross-check (a v2 page's ids are checked, retired-aware, in check_v2)
    cited = set(re.findall(RID, no_foreign(code))) | set(re.findall(RID, no_foreign(markup)))
    if prd is not None:
        if not v2:
            defs = set(re.findall(r'\*\*(R\d+(?:\.[a-z]+)?)\*\*', prd)) or set(re.findall(r'\bR\d+(?:\.[a-z]+)?\b', prd))
            for r_ in sorted(cited - defs, key=nat):
                err.append(('R-id', '%s is cited but not defined in the PRD' % r_))
        sec7 = prd_section7(prd)
        if not sec7:
            warn.append(('PRD', 'no section 7 (open questions) heading found'))
        for k, v in qt.items():
            q = re.fullmatch(r'Q\d+', k)
            d = re.fullmatch(r'Dev (\w+)', k)
            if v2 and re.fullmatch(r'Q\d+[a-z]?|J-\d+|FB\d+', k):
                pass                                  # existence: check_v2, against the contract's own files
            elif (q or (not d and k in a_keys)) and not re.search(r'(?<![\w-])%s(?![\w-])' % re.escape(k), prd):
                err.append(('Q-id', 'QT %s does not appear in the PRD' % k))
                continue
            if d and not re.search(r'\(%s\)' % re.escape(d.group(1)), sec7):
                err.append(('Q-id', "QT '%s': no (%s) developer decision in PRD section 7" % (k, d.group(1))))
                continue
            if not (q or d) or v is None or not sec7:
                continue
            pat = r'(?m)^\s*[-*]\s*(?:\*\*%s\*\*|\(%s\))(.*)$' % ((k, '\0') if q else ('\0', re.escape(d.group(1))))
            m = re.search(pat, sec7)
            line = norm(m.group(1)) if m else ''
            body = line.split('assumed:', 1)[-1].strip() if line else ''
            if norm(v) not in line:
                ratio = difflib.SequenceMatcher(None, norm(v), body).ratio() if body else 0
                warn.append(('stale', "QT '%s' text not verbatim in PRD section 7, possibly stale (re-copy); similarity %.2f" % (k, ratio)))

    # 6. summary counts
    sc_i, ix_i = decl(code, 'SC'), decl(code, 'IX')
    scn = items(code, sc_i) if sc_i is not None else []
    steps, appx, part_steps = [], 0, {}
    for s in scn:
        appx += bool(re.search(r'\bopt\s*:\s*(?!0\b|false\b)\w', s))
        m = re.search(r'\bsteps\s*:\s*\[', s)
        st = items(s, m.end() - 1) if m else []
        steps.append(len(st))
        for x in st:
            p = re.search(r'(?<![\w$.])p\s*:\s*\[([\d,\s]+)\]', x)
            low = min(int(n) for n in re.findall(r'\d+', p.group(1))) if p else 1
            if low > 1:
                part_steps[low] = part_steps.get(low, 0) + 1
    tags = {}
    for m in re.finditer(r'(?<![\w$.])(scoped|pa)\(\s*(\d+)', code):
        tags[int(m.group(2))] = tags.get(int(m.group(2)), 0) + 1
    calls = {'NEW': 0, 'CHG': 0}
    for m in re.finditer(r'(?<![\w$.])(?<!function )(NEW|CHG)\(', code):
        calls[m.group(1)] += 1
        args = items(code, m.end() - 1)
        if len(args) >= 3 and args[2].isdigit() and int(args[2]) > 1:
            tags[int(args[2])] = tags.get(int(args[2]), 0) + 1
    if ix_i is not None:
        ix_src = code[ix_i:match(code, ix_i)]
        lit = r"'(?:[^'\\]|\\.)*'"
        for n in re.findall(r'\bpart\s*:\s*(\d+)|\[\s*%s\s*,\s*%s\s*,\s*(\d+)\s*\]' % (lit, lit), ix_src):  # part: n, or a [text,'R-ids',n] change
            p = int(n[0] or n[1])
            if p > 1:
                tags[p] = tags.get(p, 0) + 1
    parts = obj_entries(code, 'PARTS') or {}
    info.append('counts: %d scenarios (%d appendix), %d steps (%s), %d index rows, %d parts' % (
        len(scn), appx, sum(steps), '/'.join(map(str, steps)) or '-', len(items(code, ix_i)) if ix_i is not None else 0, len(parts)))
    info.append('part tags (call sites): %s; whole steps: %s' % (
        ', '.join('P%d %d' % kv for kv in sorted(tags.items())) or 'none',
        ', '.join('P%d %d' % kv for kv in sorted(part_steps.items())) or 'none'))
    info.append('markers (call sites): NEW %d, CHG %d, Assumed %d (%d distinct of %d QT keys)' % (
        calls['NEW'], calls['CHG'], len(a_calls), len(a_keys), len(qt)))
    info.append('R-ids cited: %d distinct%s' % (len(cited), (' (' + ', '.join(sorted(cited, key=nat)) + ')') if cited else ''))

    check_stage(code, markup, base, a_keys, c, err, warn, info)
    if v2:
        used = set(tags) | set(part_steps) | {int(n) for n in re.findall(r'(?<![\w$.])(?:PT|chip)\(\s*(\d+)', code)}
        check_v2(code, markup, scn, qt, a_keys, used, c, view, script, err, warn, info)
    return err, warn, info


def q_entries(prd):
    """{Q or J- id: all its entries' text, continuation lines included} (model.md 3: a Q may also sit in the log)."""
    out, cur = {}, None
    for line in prd.splitlines():
        m = re.match(Q_DEF, line)
        if m:
            cur = m.group(1)
            out[cur] = out.get(cur, '') + '\n' + line
        elif cur and line[:1] in ' \t' and line.strip():
            out[cur] += ' ' + line.strip()
        else:
            cur = None
    return out


def check_stage(code, markup, base, a_keys, c, err, warn, info):
    """const STAGE: 'discussion' (v1.x, shared): reviewed once the BUILT_FROM version is triaged, else badged
    'not reviewed' with a presenter sheet (model.md 8, "Sharing")."""
    m = re.search(r'''\b(?:const|let|var)\s+STAGE\s*=\s*(['"`])(.*?)\1''', code)
    if not m:
        return
    stage = m.group(2)
    info.append('stage: %s' % stage)
    if stage not in STAGES:
        err.append(('STAGE', "STAGE='%s' is not one of %s" % (stage, ', '.join(STAGES))))
        return
    if stage != 'discussion':
        return
    if base is None or c is None:
        err.append(('STAGE', "STAGE='discussion' needs a BUILT_FROM base and --contract <TICKET_DIR> to be checked"))
        return
    run = os.path.join(c['dir'], 'run.md')
    runs = open(run, encoding='utf-8').read() if os.path.isfile(run) else ''
    if not os.path.isfile(os.path.join(c['dir'], 'prototype', 'sn-baseline.md')):
        err.append(('STAGE', 'discussion: no prototype/sn-baseline.md (stock pages captured, not guessed)'))
    if not re.search(r'(?m)^\s*[-*]\s+\d{4}-\d{2}-\d{2}\s+triaged v%s:' % re.escape(base[0]), runs):
        info.append('share: not reviewed (run.md has no triaged v%s line)' % base[0])
        badge = re.search(r'<[^>]*\bid=["\']badge["\'][^>]*>([^<]*)<', markup)
        if not badge or 'not reviewed' not in badge.group(1):
            err.append(('STAGE', "discussion: not triaged, so the .draft badge must say 'not reviewed' "
                                 "(or triage v%s first)" % base[0]))
        rev = os.path.join(c['dir'], 'review')
        if not any(f.startswith('presenter-') for f in (os.listdir(rev) if os.path.isdir(rev) else ())):
            warn.append(('STAGE', 'discussion: no review/presenter-<DATE>.md for the person presenting it'))
        return
    for q, text in sorted(q_entries(c['prd']).items(), key=lambda kv: nat(kv[0])):
        scope = (re.search(r'\bParts? \d+', text) or re.search(r'\bexpansion\b', text, re.I)
                 or re.search(r'\bAssumed\b', text) and not re.search(r'(?i)\bEvidence:', text)
                 and re.search(r'(?i)\bconfirm with\b|\bowner\b', text))
        if scope and not re.search(r'\bDecided\b', text):
            err.append(('STAGE', 'discussion: scope-bearing %s has no Decided line (rule it in triage)' % q))
    for k in sorted((k for k in a_keys if re.fullmatch(r'FB\d+', k)), key=nat):
        err.append(('STAGE', "discussion: A('%s') is a v1 CHOICE chip: rule it, or re-key it to a plain question" % k))


def check_v2(code, markup, scn, qt, a_keys, used, c, view, script, err, warn, info):
    # the page's own shape (interface I1): scenario and step ids, deep links, parts
    scen, step_src, step_low = set(), {}, {}
    for s in scn:
        P = props(s)
        sid = js_string(P.get('id') or "''") or ''
        if not re.fullmatch(r's\d+', sid):
            err.append(('step-id', "scenario %s needs id:'s<n>', its workflows.md id" % (P.get('name') or '?')[:40]))
        scen.add(sid)
        st = P.get('steps', '')
        for x in (items(st, 0) if st.startswith('[') else []):
            X = props(x)
            xid = js_string(X.get('id') or "''") or ''
            if not re.fullmatch(r's\d+\.\d+', xid) or xid.split('.')[0] != sid:
                err.append(('step-id', "step %s in %s needs id:'%s.<m>', its workflows.md id" % (
                    (X.get('t') or '?')[:40], sid or '?', sid or 's<n>')))
                continue
            if xid in step_src:
                err.append(('step-id', '%s is drawn twice' % xid))
                continue
            step_src[xid] = x
            nums = [int(n) for n in re.findall(r'\d+', X.get('p', ''))] or [1]
            step_low[xid] = min(nums)
            used.update(nums)
    nd = obj_entries(code, 'NOT_DRAWN') or {}
    ni = decl(code, 'NOT_DRAWN')
    no_nd = code[:ni] + code[match(code, ni):] if ni is not None else code   # its keys are not links
    links = {t.lstrip('#') for t in literals(no_nd) if re.fullmatch(r'#?s\d+(?:\.\d+)?', t)}
    links |= set(re.findall(r'''href=["']#(s\d+(?:\.\d+)?)["']''', markup))
    links -= set(re.findall(r'''\bid\s*:\s*['"](s\d+(?:\.\d+)?)['"]''', code))   # a page's own id is not a link
    drawn_scen = {x.split('.')[0] for x in step_src}            # '#s1' opens scenario s1's first drawn step
    for r_ in sorted(links - drawn_scen - set(step_src), key=nat):
        err.append(('link', "'%s' is linked but no page draws it%s" % (r_, ' (NOT_DRAWN)' if r_ in nd else '')))
    for r_ in sorted(set(nd) & set(step_src), key=nat):
        warn.append(('coverage', '%s is drawn and also listed in NOT_DRAWN' % r_))
    pi = decl(code, 'PARTS')
    parts = {}
    for it in (items(code, pi) if pi is not None else []):
        m = re.match(r'''(?s)['"]?(\d+)['"]?\s*:\s*(.*)''', it)
        if m:
            parts[int(m.group(1))] = props(m.group(2).strip())
    for p in sorted(used - set(parts)):
        err.append(('part', 'Part %d is used on the page but PARTS has no %d' % (p, p)))
    text = no_foreign(code) + '\n' + no_foreign(markup)
    page_ids = {x: set(re.findall('|'.join((RID, QID, FBID)), no_foreign(src))) | {x, 'Part %d' % step_low[x]}
                for x, src in step_src.items()}
    info.append('steps drawn: %d (%s); not drawn: %d%s' % (
        len(step_src), ', '.join(sorted(step_src, key=nat)) or '-', len(nd),
        ' (%s)' % ', '.join(sorted(nd, key=nat)) if nd else ''))

    # the contract, at the page's base version
    if c is None:
        info.append('contract: none given (--contract <TICKET_DIR>): ids not resolved')
    else:
        ids = c['ids']
        skip = lambda i: (re.match(r's\d|Part ', i) and not c['wf']) or (i.startswith('FB') and not c['has_fb'])
        lit = r"'(?:[^'\\\n]|\\.)*'" + '|' + r'"(?:[^"\\\n]|\\.)*"'
        cites = ' '.join(js_string(m.group(1)) or '' for m in re.finditer(     # news/changes: ['label','R1, R2.a'(,n)]
            r'\[\s*(?:%s)\s*,\s*(%s)\s*(?:,\s*\d+\s*)?\]' % (lit, lit), code))
        cites = no_foreign(cites)
        strong = (set(re.findall(RID, cites)) | set(re.findall(QID, cites)) | set(re.findall(FBID, cites))
                  | {k for k in a_keys | set(qt) if re.fullmatch(r'Q\d+[a-z]?|J-\d+|FB\d+', k)}
                  | {'Part %d' % p for p in used} | (scen - {''}) | set(step_src) | links)
        loose = (set(re.findall(RID, text)) | set(re.findall(QID, text)) | set(re.findall(FBID, text))
                 | {'Part ' + n for n in re.findall(r'\bPart (\d+)\b', text)})
        for i in sorted((strong | loose) - set(nd), key=nat):
            if skip(i):
                continue
            if i not in ids and i not in strong:   # page text only: fake data ('Part 77') or a citation to fix
                warn.append(('contract', '%s appears in the page text but is not defined in %s: fake data, or a '
                             'citation to fix' % (i, ', '.join(c['used']))))
            elif i not in ids:
                err.append(('contract', '%s is cited but not defined in %s' % (i, ', '.join(c['used']))))
            elif not ids[i]:
                err.append(('retired', '%s is retired: a new citation cites its successor' % i))
        if c['wf']:
            for x, low in sorted(step_low.items()):
                want = c['step_part'].get(x)
                if ids.get(x) and want and low != want:
                    err.append(('part', '%s is Part %d in workflows.md; the page draws it as p:[%d]' % (x, want, low)))
            live = {i for i, ok in ids.items() if ok and re.fullmatch(r's\d+\.\d+', i)}
            for i in sorted(live - set(step_src) - set(nd), key=nat):
                err.append(('coverage', 'live step %s has no page: draw it, or list it in NOT_DRAWN with a reason' % i))
            for i in sorted(nd, key=nat):
                if i not in ids:
                    err.append(('contract', 'NOT_DRAWN %s is not a step in %s' % (i, ', '.join(c['used']))))
                elif not ids[i]:
                    warn.append(('coverage', 'NOT_DRAWN %s is retired: a retired step needs no entry' % i))
            live_parts = {n for n in c['parts'] if ids.get('Part %d' % n)}
            for n in sorted(live_parts - set(parts)):
                err.append(('part', 'PARTS lacks Part %d (%s), a live part in workflows.md' % (n, c['parts'][n][0])))
            for n in sorted(set(parts) - live_parts):
                err.append(('part', 'PARTS has Part %d, which is not a live part in workflows.md' % n))
            for n in sorted(set(parts) & live_parts):
                for k, want in zip(('name', 'scope'), c['parts'][n]):
                    got = js_string(parts[n].get(k) or "''")
                    if got is not None and norm(got) != norm(want):
                        warn.append(('drift', 'PARTS %d %s not verbatim from workflows.md Parts, possibly stale (re-copy): %r'
                                     % (n, k, want[:60])))
            info.append('workflows: %d live steps, %d drawn, %d not drawn; %d live parts' % (
                len(live), len(live & set(step_src)), len(live & set(nd)), len(live_parts)))
        for k in sorted(a_keys & set(c['fb']), key=nat):
            status, what = c['fb'][k]
            if not status.lower().startswith('open'):
                warn.append(('FB', "A('%s') rests on a feedback entry that is '%s': re-key the chip to its ruling" % (k, status[:60])))
            if qt.get(k) and what and norm(qt[k]) not in norm(what):
                warn.append(('stale', "QT '%s' text not verbatim from its feedback.md What line, possibly stale (re-copy)" % k))

    # stale pages: check-contract.py --stale (interface I2), mapped back to the steps that cite each id
    if view is None:
        return
    r = run_stale(view, script)
    if r is None:
        info.append('stale check skipped: skunexus-contract not installed')
        return
    rc, stale, last = r
    if rc == 0:
        info.append('stale check: current')
    elif rc == 3:
        info.append('stale check: no base')
    elif rc == 1:
        # ponytail: maps by the step's own source; an id cited only inside a shared helper or the index shows as
        # "outside the steps". Expand helper calls if rebuilds miss pages.
        for i, why in stale:
            pages = sorted((x for x, s in page_ids.items() if i in s), key=nat)
            err.append(('stale', '%s: %s; pages: %s' % (
                i, why, ', '.join(pages) or 'none drawn (new, or cited outside the steps: index or shared helpers)')))
        if not stale:
            err.append(('stale', last))
    else:
        err.append(('stale', 'check-contract.py --stale could not read the page: %s' % last))


def report(path, err, warn, info):
    print('check-storyboard: %s' % path)
    for i in info:
        print('  ' + i)
    for k, m in warn:
        print('  WARN  [%s] %s' % (k, m))
    for k, m in err:
        print('  ERROR [%s] %s' % (k, m))
    print('  result: %s' % ('FAIL (%d errors, %d warnings)' % (len(err), len(warn)) if err else 'OK (%d warnings)' % len(warn)))


# ---------- self-test ----------
# A legacy page (PR A's fixture, unchanged) and its PRD.
CLEAN = '''<title>T</title><div id="a"></div><p>Fake page</p><hr><script>
'use strict';
const QT={
  Q1:'Only open orders can be held.',
  'Dev a':'The reason list is fixed.',
  'D-R1':'Holds are manual.'
};
const PARTS={1:{name:'Base'},2:{name:'Option'}};
function A(q){return q;} function NEW(h,i,p,n){return h;} function scoped(p,w,h){return h;}
/* comments are ignored: A('Q42') R77 */
const SC=[{id:'s1',name:'x',steps:[{t:'a',page:()=>NEW('x',0,2,'n')+A('Q1')+A('Dev a')+A('D-R1')+document.querySelector('#a'),news:[['b','R1, R2.a']],today:'t'}]}];
const IX=[{name:'p',changes:[['c','R1',2]]}];
</script>'''
PRD = '''# PRD
## 4. Requirements
- **R1** Hold an order.
## 6. Acceptance Criteria
- **R2.a** Given x, then y.
## 7. Open questions and assumptions
- **Q1** Holds. Assumed: only open orders can be held.
- (a) Reason list? Assumed: the reason list is fixed in code.
- **D-R1** Holds are manual.
'''
PLANTS = [
    ('id', lambda h: h.replace("querySelector('#a')", "querySelector('#nope')")),
    ('forbidden', lambda h: h.replace('Fake page', 'Fake page, 16–20 h')),
    ('forbidden', lambda h: h.replace('Fake page', 'Fake page: 3 hours')),
    ('QT', lambda h: h.replace("A('Dev a')", "A('Dev a')+A('Q9')")),
    ('R-id', lambda h: h.replace("'R1, R2.a'", "'R1, R99'")),
    ('Q-id', lambda h: h.replace("Q1:'Only", "Q7:'x',\n  Q1:'Only")),
    ('Q-id', lambda h: h.replace("Q1:'Only", "'PD-9':'x',\n  Q1:'Only").replace("A('D-R1')", "A('D-R1')+A('PD-9')")),
    ('forbidden', None),
    ('syntax', lambda h: h.replace("'use strict';", "'use strict'; const = ;")),
]

# A v2 ticket: contract v1 frozen in review/, a live draft edit after it, and a v2 page built from v1.
V2_PRD = '''# PRD: TKT-1 — Review hold

> Status: Approved
> Versions:
> - v1 2026-11-03 approved: first version

## 4. Requirements
- **R1** Hold an order for review.
- **R2** (retired 2026-11-03, v1: merged into R1 → see R1)
- **R3** Release a hold.

## 6. Acceptance Criteria
- **R1.a** Given an open order, when it is held, then it shows Held for review.
- **R1.aa** Given a held order, when the hold is saved, then the customer is emailed.
- **R3.a** Given a held order, when Release is clicked, then the hold clears.

## 7. Open Questions
- **Q1** Which orders? Assumed: only open orders can be held. Evidence: the ticket. Confirm with the PO.
'''
V2_WF = '''# Workflows: TKT-1 — Review hold

## Scenarios
| Id | Scenario | Actors |
|---|---|---|
| s1 | Hold an order | warehouse user |
| s2 | Release it | warehouse user, system |

## s1. Hold an order
| Step | Actor | Trigger | Before → after | Outcome | Cites | Part |
|---|---|---|---|---|---|---|
| s1.1 | warehouse user | user | Open → Open | sees Hold for review | R1 | Part 1 |
| s1.2 | warehouse user | user | Open → Held | the order shows Held for review | R1.a, Q1 | Part 1 |
| s1.3 | warehouse user | user | — | (retired 2026-11-03, v1: merged into s1.2) | R1 | Part 1 |

## s2. Release it
| Step | Actor | Trigger | Before → after | Outcome | Cites | Part |
|---|---|---|---|---|---|---|
| s2.1 | warehouse user | user | Held → Open | the hold clears | R3, R3.a | Part 1 |
| s2.2 | system | system | Held → Held | the customer is emailed | R1.aa | Part 2 |
| s2.3 | system | schedule | Held → Held | a nightly digest | R3 | Part 1 |

## Parts
| Part | Name | Scope | PO's shape | Status |
|---|---|---|---|---|
| Part 1 | Review hold | Hold orders for review and release them. | base | live |
| Part 2 | Customer notice | Email the customer when an order is held. | priced separately | live |
| Part 3 | Branding | The logo on the email. | priced separately | retired v1: dropped |
'''
V2_FB = '''# Feedback: TKT-1

### FB1 · CHOICE · storyboard v1 · 2026-11-03
- **Cites:** R1
- **What:** The Hold for review button sits in the Order Details header.
- **Status:** open
'''
V2_PAGE = '''<title>T</title><div id="a"></div><p>Fake page</p><script>
'use strict';
const BUILT_FROM='contract v1 (2026-11-03)';
const PARTS={
  1:{name:'Review hold',short:'Base',q:'(base)',scope:'Hold orders for review and release them.'},
  2:{name:'Customer notice',short:'Notice',q:'(priced separately)',scope:'Email the customer when an order is held.'}
};
const QT={Q1:'only open orders can be held.',FB1:'The Hold for review button sits in the Order Details header.'};
const NOT_DRAWN={'s2.3':'a nightly job; nothing on screen'};
function A(q){return q;} function NEW(h,i,p,n){return h;}
const SC=[
{id:'s1',name:'Hold an order',steps:[
 {id:'s1.1',t:'Order details',page:()=>NEW('x',1)+A('FB1')+document.querySelector('#a'),news:[['Hold for review','R1']]},
 {id:'s1.2',t:'Held',page:()=>'y'+A('Q1'),news:[['Held tag','R1.a; as FFD-14 R31 and R40']]}]},
{id:'s2',name:'Release it',steps:[
 {id:'s2.1',t:'Released',page:()=>'z',news:[['Release','R3, R3.a']]},
 {id:'s2.2',t:'Customer notice',p:[2],page:()=>NEW('n',0,2),news:[['Email','R1.aa']]}]}];
const IX=[{name:'Order details',jump:['s1.2','#s2.1'],changes:[['Hold for review','R1']]}];
</script>'''
V2_PLANTS = [
    ('contract', lambda h: h.replace("['Email','R1.aa']", "['Email','R1.ab']")),
    ('contract', lambda h: h.replace("A('Q1')", "A('Q7')").replace('{Q1:', '{Q7:')),
    ('contract', lambda h: h.replace("A('FB1')", "A('FB2')").replace(',FB1:', ',FB2:')),
    ('retired', lambda h: h.replace("['Hold for review','R1']]}", "['Hold for review','R2']]}")),
    ('retired', lambda h: h.replace("id:'s1.1'", "id:'s1.3'")),
    ('coverage', lambda h: h.replace("id:'s1.1'", "id:'s1.3'")),
    ('coverage', lambda h: h.replace("'s2.3':'a nightly job; nothing on screen'", '')),
    ('part', lambda h: h.replace("p:[2],", '')),
    ('part', lambda h: h.replace("  2:{name:'Customer notice'", "  3:{name:'Branding',short:'B',q:'',scope:'x'},\n  2:{name:'Customer notice'")),
    ('part', lambda h: h.replace("NEW('n',0,2)", "NEW('n',0,4)")),
    ('step-id', lambda h: h.replace("id:'s2.1'", "id:'s1.4'")),
    ('step-id', lambda h: h.replace("{id:'s2',", '{')),
    ('link', lambda h: h.replace("'#s2.1'", "'#s2.9'")),
    ('link', lambda h: h.replace("'#s2.1'", "'#s2.3'")),                   # a NOT_DRAWN step is no target
    ('link', lambda h: h.replace("'#s2.1'", "'#s3'")),
    ('contract', lambda h: h.replace("'R3, R3.a'", "'R3, R3.a-b'")),         # a range cites R3.b
    ('BUILT_FROM', lambda h: h.replace("'contract v1 (2026-11-03)'", "'PRD v1'")),
    ('BUILT_FROM', lambda h: h.replace("const BUILT_FROM='contract v1 (2026-11-03)';", '')),
]


def selftest():
    # legacy page: PR A's checks, unchanged
    err, warn, info = check(CLEAN, PRD)
    assert not err, err
    assert any(k == 'stale' and "'Dev a'" in m for k, m in warn), warn
    assert not any(k == 'stale' and "'Q1'" in m for k, m in warn), warn
    assert any('1 scenarios (0 appendix), 1 steps (1), 1 index rows, 2 parts' in i for i in info), info
    assert any('P2 2' in i for i in info), info
    assert any('legacy' in i for i in info), info
    n = 0
    for kind, plant in PLANTS:
        if kind == 'syntax' and not shutil.which('node'):
            print('  skip: syntax plant (node not found)')
            continue
        e, _, _ = check(CLEAN, PRD, [r'\bFake\b']) if plant is None else check(plant(CLEAN), PRD)
        assert any(k == kind for k, _ in e), (kind, e)
        n += 1

    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, 'review'))
        os.makedirs(os.path.join(d, 'prototype'))
        for name, body in (('prd.md', V2_PRD), ('review/prd-v1-2026-11-03.md', V2_PRD), ('workflows.md', V2_WF),
                           ('review/workflows-v1-2026-11-03.md', V2_WF), ('feedback.md', V2_FB)):
            with open(os.path.join(d, name), 'w', encoding='utf-8') as f:
                f.write(body)
        # a draft edit after v1: a new live step; the page is checked against v1, so it is not missing a page
        row = next(x for x in V2_WF.splitlines() if x.startswith('| s2.3 '))
        with open(os.path.join(d, 'workflows.md'), 'w', encoding='utf-8') as f:
            f.write(V2_WF.replace(row, row + '\n' + row.replace('s2.3', 's2.4')))
        view = os.path.join(d, 'prototype', 'tkt-1-storyboard.html')
        with open(view, 'w', encoding='utf-8') as f:
            f.write(V2_PAGE)
        none = os.path.join(d, 'no-such', 'check-contract.py')
        err, warn, info = check(V2_PAGE, contract=d, view=view, script=none)
        assert not err, err
        assert not warn, warn
        assert 'stale check skipped: skunexus-contract not installed' in info, info
        assert any('5 live steps, 4 drawn, 1 not drawn; 2 live parts' in i for i in info), info
        for kind, plant in V2_PLANTS:
            e, _, _ = check(plant(V2_PAGE), contract=d, view=view, script=none)
            assert any(k == kind for k, _ in e), (kind, e)
            n += 1
        # T13: '#s1' reaches scenario s1; fake data ('Part 77', 'R12-B', 'Q9') in page text is a warning only;
        # a backticked BUILT_FROM is a base; an escaped pipe in a Parts Scope is read as '|'
        page = V2_PAGE.replace("'#s2.1'", "'#s1'").replace("page:()=>'z'", "page:()=>'<td>Part 77</td> SKU R12-B Q9'")
        e, w, _ = check(page, contract=d)
        assert not e and sorted(m.split()[0] for k, m in w if k == 'contract') == ['Part', 'Q9'], (e, w)
        page = V2_PAGE.replace("const BUILT_FROM='contract v1 (2026-11-03)'", 'const BUILT_FROM=`contract v1 (2026-11-03)`')
        e, w, i = check(page, contract=d)
        assert not e and not w and any(x.startswith('page: v2') for x in i), (e, w, i)
        for name in ('workflows.md', 'review/workflows-v1-2026-11-03.md'):
            with open(os.path.join(d, name), 'w', encoding='utf-8') as f:
                f.write(V2_WF.replace('Hold orders for review and release', 'Hold orders for review \\| release'))
        e, w, _ = check(V2_PAGE.replace('Hold orders for review and release', 'Hold orders for review | release'), contract=d)
        assert not e and not w, (e, w)
        for name in ('workflows.md', 'review/workflows-v1-2026-11-03.md'):
            with open(os.path.join(d, name), 'w', encoding='utf-8') as f:
                f.write(V2_WF)
        n += 3
        # drift and a ruled feedback entry are warnings
        _, w, _ = check(V2_PAGE.replace("name:'Customer notice'", "name:'Notice'"), contract=d)
        assert any(k == 'drift' for k, _ in w), w
        with open(os.path.join(d, 'feedback.md'), 'w', encoding='utf-8') as f:
            f.write(V2_FB.replace('**Status:** open', '**Status:** ruled v2 (developer, option A) → Q2'))
        _, w, _ = check(V2_PAGE, contract=d)
        assert any(k == 'FB' for k, _ in w), w
        # interface I2: a stale id maps to the pages that cite it; exit 3 is no base
        stub = os.path.join(d, 'check-contract.py')
        with open(stub, 'w', encoding='utf-8') as f:
            f.write("import sys\nprint('stale R1.a: changed in v2\\nstale s2.4: new in v2\\nresult: stale')\nsys.exit(1)\n")
        e, _, _ = check(V2_PAGE, contract=d, view=view, script=stub)
        assert ('stale', 'R1.a: changed in v2; pages: s1.2') in e, e
        assert any(k == 'stale' and m.startswith('s2.4: new in v2; pages: none drawn') for k, m in e), e
        with open(stub, 'w', encoding='utf-8') as f:
            f.write("import sys\nprint('result: no base')\nsys.exit(3)\n")
        e, _, i = check(V2_PAGE, contract=d, view=view, script=stub)
        assert not any(k == 'stale' for k, _ in e) and 'stale check: no base' in i, (e, i)
        n += 3
        # STAGE: internal and approved pass; an unknown value fails; discussion needs the triage record, the
        # baseline, every scope-bearing Q decided and no FB chip
        e, _, i = check(V2_PAGE.replace("'use strict';", "'use strict'; const STAGE='internal';"), contract=d)
        assert not e and 'stage: internal' in i, e
        disc = V2_PAGE.replace("'use strict';", "'use strict'; const STAGE='discussion';").replace("+A('FB1')", '')
        disc = disc.replace(",FB1:'The Hold for review button sits in the Order Details header.'", '')
        e, _, _ = check(disc, contract=d)
        assert sorted(m.split(':')[1].split()[0] for k, m in e if k == 'STAGE') == ['no', 'not'], e
        with open(os.path.join(d, 'run.md'), 'w', encoding='utf-8') as f:
            f.write('# Run settings: TKT-1\n\n## History\n- 2026-11-04 triaged v1: 3 items ruled (developer)\n')
        with open(os.path.join(d, 'prototype', 'sn-baseline.md'), 'w', encoding='utf-8') as f:
            f.write('# Baseline\n')
        e, _, i = check(disc, contract=d)
        assert not e and 'stage: discussion' in i, e
        # a share before the triage: badged 'not reviewed', its FB chip stays, a presenter sheet is expected
        early = V2_PAGE.replace("'use strict';", "'use strict'; const STAGE='discussion';").replace(
            '<title>T</title>', '<title>T</title><span class="draft" id="badge">Draft for discussion 2026-11-05, not reviewed</span>')
        with open(os.path.join(d, 'run.md'), 'w', encoding='utf-8') as f:
            f.write('# Run settings: TKT-1\n\n## History\n')
        e, w, i = check(early, contract=d)
        assert not [m for k, m in e if k == 'STAGE'] and any('presenter' in m for k, m in w), (e, w)
        assert 'share: not reviewed (run.md has no triaged v1 line)' in i, i
        sheet = os.path.join(d, 'review', 'presenter-2026-11-05.md')
        with open(sheet, 'w', encoding='utf-8') as f:
            f.write('# Presenter sheet\n')
        e, w, _ = check(early, contract=d)
        assert not [m for k, m in e if k == 'STAGE'] and not any('presenter' in m for k, m in w), (e, w)
        e, _, _ = check(early.replace(', not reviewed', ''), contract=d)
        assert any(k == 'STAGE' and "must say 'not reviewed'" in m for k, m in e), e
        os.remove(sheet)
        with open(os.path.join(d, 'run.md'), 'w', encoding='utf-8') as f:
            f.write('# Run settings: TKT-1\n\n## History\n- 2026-11-04 triaged v1: 3 items ruled (developer)\n')
        n += 3
        snap = os.path.join(d, 'review', 'prd-v1-2026-11-03.md')
        plants = [
            ('STAGE=', lambda h: h.replace("STAGE='discussion'", "STAGE='triage'"), None),
            ('needs a BUILT_FROM', lambda h: h, 'no contract'),
            ('not reviewed', lambda h: h.replace("contract v1 (2026-11-03)", "contract v2 (2026-11-03)"), None),
            ("A('FB1')", lambda h: h.replace("A('Q1')", "A('Q1')+A('FB1')"), None),
            ('scope-bearing Q2', lambda h: h, '- **Q2** Email too? Options: (A) no [PO decided] · (B) yes [expansion, M].\n'),
            ('scope-bearing Q3', lambda h: h, '- **Q3** Which list? Assumed: the short one.\n  Confirm with the PO.\n'),
            ('scope-bearing Q4', lambda h: h, '- **Q4** Notice? Assumed: in Part 2. Evidence: the ticket.\n'),
        ]
        for needle, plant, extra in plants:
            if extra and extra != 'no contract':
                with open(snap, 'w', encoding='utf-8') as f:
                    f.write(V2_PRD + extra)
            e, _, _ = check(plant(disc), contract=None if extra == 'no contract' else d)
            assert any(k == 'STAGE' and needle in m for k, m in e), (needle, e)
            n += 1
        with open(snap, 'w', encoding='utf-8') as f:   # decided in the log: no longer blocks
            f.write(V2_PRD + '- **Q4** Notice? Assumed: in Part 2.\n\n## 8. Decision log\n- **Q4** Decided 2026-11-04 '
                    '(developer, option A): in Part 2.\n')
        e, _, _ = check(disc, contract=d)
        assert not e, e
    print('selftest: OK (legacy and v2 pages pass; %d planted errors caught)' % n)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('html', nargs='?')
    ap.add_argument('--contract', metavar='TICKET_DIR|PRD', help='the ticket dir, or a prd file (a legacy requirements-lite.md)')
    ap.add_argument('--prd', metavar='PRD', help='same as --contract <PRD>')
    ap.add_argument('--forbid', action='append', default=[], metavar='REGEX')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not a.html:
        ap.error('html path required')
    try:
        with open(a.html, encoding='utf-8') as f:
            text = f.read()
        err, warn, info = check(text, None, a.forbid, a.contract or a.prd, a.html)
    except (OSError, UnicodeDecodeError, ValueError) as e:
        print('check-storyboard: %s: unreadable: %s' % (a.html, e))
        return 2
    report(a.html, err, warn, info)
    return 1 if err else 0


if __name__ == '__main__':
    sys.exit(main())
