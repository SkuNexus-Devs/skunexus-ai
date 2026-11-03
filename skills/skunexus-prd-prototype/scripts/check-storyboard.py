#!/usr/bin/env python3
"""Static checks for a storyboard page (skunexus-prd-prototype, storyboard stage).

Usage: python3 -I check-storyboard.py <storyboard.html> [--prd <prd.md>] [--forbid <regex> ...]
       python3 -I check-storyboard.py --selftest
Checks: node --check on the inline script (when node exists); every #id the script looks up exists;
no hours or other forbidden strings; every A('<key>') has a QT entry; with --prd, every cited R-id and
QT key exists in the PRD ('Dev x' as a '(x)' line in section 7), and QT text not found verbatim in PRD section 7 is flagged (warning).
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
    r'(?i)\bhrs?\b',
    r'\b\d+(?:\.\d+)?\s*[–-]\s*\d+(?:\.\d+)?\s*h\b',          # 16–20 h, 16-20h
    r'(?<![\w)\]$])\+\d+(?:\.\d+)?\s*[–-]\s*\d+(?:\.\d+)?\b',  # +1–1.5 (not code like i+1-2)
    r'\b\d+(?:\.\d+)?\s?h(?:rs?)?\b',                            # 12h, 1.5 h, 3 hr, 2.5hrs
]
RID = r'(?<![\w$.#-])R\d+(?:\.[a-z])?(?![\w$(=])'


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


# ---------- the checks ----------
def check(text, prd=None, forbid=()):
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

    # 5. PRD cross-check
    cited = set(re.findall(RID, code)) | set(re.findall(RID, markup))
    if prd is not None:
        defs = set(re.findall(r'\*\*(R\d+(?:\.[a-z])?)\*\*', prd)) or set(re.findall(r'\bR\d+(?:\.[a-z])?\b', prd))
        for r_ in sorted(cited - defs, key=rid_key):
            err.append(('R-id', '%s is cited but not defined in the PRD' % r_))
        sec7 = prd_section7(prd)
        if not sec7:
            warn.append(('PRD', 'no section 7 (open questions) heading found'))
        for k, v in qt.items():
            q = re.fullmatch(r'Q\d+', k)
            d = re.fullmatch(r'Dev (\w+)', k)
            if (q or (not d and k in a_keys)) and not re.search(r'(?<![\w-])%s(?![\w-])' % re.escape(k), prd):
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
    info.append('R-ids cited: %d distinct%s' % (len(cited), (' (' + ', '.join(sorted(cited, key=rid_key)) + ')') if cited else ''))
    return err, warn, info


def rid_key(r):
    m = re.match(r'R(\d+)(?:\.(\w))?', r)
    return (int(m.group(1)), m.group(2) or '')


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
CLEAN = '''<title>T</title><div id="a"></div><p>Fake page</p><script>
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


def selftest():
    err, warn, info = check(CLEAN, PRD)
    assert not err, err
    assert any(k == 'stale' and "'Dev a'" in m for k, m in warn), warn
    assert not any(k == 'stale' and "'Q1'" in m for k, m in warn), warn
    assert any('1 scenarios (0 appendix), 1 steps (1), 1 index rows, 2 parts' in i for i in info), info
    assert any('P2 2' in i for i in info), info
    n = 0
    for kind, plant in PLANTS:
        if kind == 'syntax' and not shutil.which('node'):
            print('  skip: syntax plant (node not found)')
            continue
        if plant is None:
            e, _, _ = check(CLEAN, PRD, [r'\bFake\b'])
        else:
            e, _, _ = check(plant(CLEAN), PRD)
        assert any(k == kind for k, _ in e), (kind, e)
        n += 1
    print('selftest: OK (clean page passes; %d planted errors caught)' % n)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('html', nargs='?')
    ap.add_argument('--prd')
    ap.add_argument('--forbid', action='append', default=[], metavar='REGEX')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not a.html:
        ap.error('html path required')
    with open(a.html, encoding='utf-8') as f:
        text = f.read()
    prd = None
    if a.prd:
        with open(a.prd, encoding='utf-8') as f:
            prd = f.read()
    err, warn, info = check(text, prd, a.forbid)
    report(a.html, err, warn, info)
    return 1 if err else 0


if __name__ == '__main__':
    sys.exit(main())
