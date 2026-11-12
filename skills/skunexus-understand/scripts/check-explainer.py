#!/usr/bin/env python3
"""Static checks for a ticket's understanding page (skunexus-understand).

Usage: python3 -I check-explainer.py <explainer-dir> [--forbid REGEX]... [--repo PATH]
       python3 -I check-explainer.py <explainer-dir> --blind     the quiz stems and options only (blind guesser input)
       python3 -I check-explainer.py <explainer-dir> --teach     the page text, scripts stripped, then the blind quiz
       python3 -I check-explainer.py <explainer-dir> --stale     exit 3 when the named head or the merge base moved;
                                                                  intent-only: when a why-source hash moved instead
       python3 -I check-explainer.py --selftest

Reads map.json, plan.json, quiz.json, fragments/*.html and the built explainer.html (+ explainer.local.html).
Every check is mechanical:
  plan       stage (intent-only: no chapters, mechanical, hotspots or mapped files), piece ids (plan.json chapters[],
             ch-<n>), read/risk/evidence vocabulary, a fragment per piece, tested needs review/tests-<head7>.txt that
             names <head7>; toy is text, a piece's checks a list of facts (one fact in two pieces warns); drift needs a note (needs_decision
             when it breaks prd.md), ops a what; a migration or config change with no ops warns; background.html and
             intuition.html always; asked.html when prd.md, workflows.md or investigation.md is a source, or a PR body
             or Jira copy (pr*.md, jira-*.md, *-jira.md, jira-summary.md) or a bug fix's notes (root-cause*.md,
             handoff*.md, investigation/*.md) is a plan source; proven.html when a test
             file changed, spec-from-tests.md is a source or review/tests-*.txt exists; every source exists and none is
             private (input/, meeting*, email*, panel, persona, simulated, logs/, *.log, a dump, a review/ folder
             except the page's own and the prd-v<N>-<DATE>.md and workflows-v<N>-<DATE>.md snapshots); no origin url
             (nor the storyboard's) carries a share token (?sk=, token=, key=, sig=, ...); contract and storyboard match prd.md's newest
             > Versions: line, its > Status: and prototype/artifact.md (unless that source moved since the build);
             a > Built from: header whose version differs from the newest row warns;
  trace      every prd.md criterion (the first of R<n>.<x>, AC<n>, R<n>; not in comments or Versions lines) and
             every investigation.md A<n> exactly once; another id warns, except goal.<slug> and s<n>.<m> with
             workflows.md; the state
             rules: tested needs proven + review/tests-<head7>.txt, built needs built + proven, untested needs built,
             not-built/non-goal/deferred need a note, drift a needs_decision drift entry; intent-only allows only
             not-built, non-goal and deferred;
  coverage   every map.json file in exactly one piece or mechanical group (fnmatch globs); a read-tier file in a
             mechanical group is an error (never down a tier);
  marker     every marker is an empty <pre data-hunk|data-code>; build resolves them and leaves a failed one in the
             page, where this check finds it;
  ref        a ref's text (>= 12 chars) occurs in its local src file after Markdown and quote normalisation (catches
             invented quotes); an FB<n> quotes only a **Status:** line of its own ### FB<n> entry; build reports a
             data-ref with no refs entry,
             and a dangling chip fails links;
  safety     fragments, tokenised by html.parser: no denylisted tag, on*=, style=, src=, javascript:/data: URL, unclosed
             trailing tag, links other than #id or the forge; unknown tags and classes warn. The page: no on*= at all;
  quiz       schema, each question's chapter resolves, checkpoints only in pieces, built_from = head, 3-5 finals (5 past 150
             read-tier lines, or intent-only past 8 criteria) and <= 12 in all; layer coverage of the finals: an
             intent kind (requirement|workflow|why|criterion) when an Asked source (a PR body or Jira copy too)
             exists, a test kind (ac-map is
             not one) when the Proven layer exists; intent-only: requirement|workflow|why only; no criterion or
             ac-map question on a drift that needs a decision; a why question's evidence names a recorded source (a
             decision, the PRD, a ruling, the PR text, answers.md, or a ref quoting a note in plan.json sources)
             or it warns; positions (spread <= 1, no run of
             3, no cycle; a valid sequence is printed), length with slack, a/an endings, all/none of the above,
             identical options, numeric options in order, reference-token parity, marker words, cue-follower scores
             <= N/4 + 1 (the message names the questions it alone gets right), one bold NOT at most; nothing of the
             key in the markup; asked.html's word count is printed (chips excluded); label: no commit SHA, file:line
             or line <n>, section sign, exit <n>|exit code or plan.json refs id (a whole token) in a stem or option;
             a stem with more than 3 code spans warns; past 4 main-flow pieces (read: must) and under 12 questions, a
             main-flow piece with no checkpoint warns (a checkpoint sits open at its piece's end, after More on this);
             a checkpoint on a skim piece (under Go deeper, its row closed) is an error;
  budget     soft, warnings only (visible words: outside <pre>, <details> and chips): a main-flow piece's note before
             <!--more--> <= 120 words; a gist <= 30 words; a fragment <= 450; asked.html <= 600 (<= 900 past 5 use
             cases); background.html <= 300; two questions with one option set warn;
  reader     the prose a reader meets (fragments minus <pre> and chips; plan.json glance, problem, the map's words,
             not_in_change, deeper summaries, hotspots why, drift and ops notes, open questions, piece titles, short
             names, why_here, gist and proof, glossary, mechanical intent, trace text and notes): a commit SHA or a
             name.ext:NN location is an error; a bare ref id (a refs key or R5, AC1, FB2, Q3, D4, T5, s1.2) warns,
             except in trace rows, code spans, tables and as an item's own "R5:" label; a glance (the lead) that tells
             the page's own history (rebuilt, round 2, this build, adds What was asked) is an error;
  contract   no doctype, a 2-4 word <title> in the first 8 KB, the viewport-fit-sides meta, script hosts and versions,
             Google Fonts only, ids [a-z0-9-]+ unique and not reserved, pre white-space, node --check on the engine;
  links      every href="#id" resolves;   size  warn > 4 MB, error > 15 MB, warn > 3,000 diff lines;
  leftover   no STATE comment, TODO, {{ or lorem outside code;   stale  xd-data meta.build = the inputs' hash now;
             a why-source whose hash differs from meta.inputs warns "why-source changed since build".
The page's shape (handoff §6), on the built page parsed as a tree; text is scanned per text node, never joined:
  shape      full: a file tree listing every file, a strip tile per file (data-f, data-fam) with a CSS min-width of
             >= 1rem, the piece index; intent-only: no tree, strip, index, files or pieces, and What was asked open in
             the main flow before Check yourself; no map (plan.json map) warns;
  quiz-place Check yourself (#quiz) in no <details>, after the last main-flow piece, before Go deeper; a link to it on
             the first screen (header.doc) besides the bar pill; no question (fieldset.q, final or checkpoint) under a
             closed <details>;
  badge      span.pb only; its number a piece's, its data-fam and hollow (.deep = read skim) the piece's; inside an <a>
             that lands on its piece (or inside it), its own piece's heading, or the summary of the row holding it;
             a.pref links a piece and holds its badge;   nest  no <a> inside an <a>;
  circled    no circled number (①..) in visible text or CSS content: a piece number shows only as its badge;
  label      visible text (not code, chips, title or aria; not the tree, files, strip or captions, which show repo
             paths) has no "chapter", "Ch n", "piece n", goal.<id> or name.ext:NN;
  section-ref  #map, #carry, #pieces ("The N pieces": two..twelve, digits past 12, "The piece"), #quiz and #deeper
             carry their headings; "the map", "what to carry", "To carry into the review", "Check yourself", "What was
             asked", "All N files" (N = the files) and "Read pieces" are links landing in the section they name (a
             section may name itself; code, chips, quiz stems and options, headings and summaries are exempt); each Go
             deeper row's summary is its heading's exact text;
  filter     no file-filter UI (#ftree-q, .tfil, .ftools, a search box) at or below xd-data meta.filter_at changed
             files (20 when absent); above it, the tree's #ftree-q;
  extlink    every external <a> has target="_blank" and rel with noopener;
  text-size  CSS outside @media print: no html/:root font size, no absolute unit (px, pt, ...), nothing under 1rem/1em/
             100% except the strip digits (a nav.strip selector); ponytail: the first size in a calc()/min() counts;
  root       the root budget replaces the must-path budget: the authored words above the pieces (h1, lead, the map,
             the carry list; closed <details>, <pre>, [hidden] and the file tree out; Start here, the strip, the piece
             index and the Next lines are generated, printed apart) <= ROOT_WORDS (480: the reference page has 402). The reading
             path (root, each main-flow piece, the quiz) is printed as information, never a gate;
  non-goal   each plan.json not_in_change text in a carry line, open, before Go deeper; a non-goal trace row with no
             not_in_change warns;
  trace-table  table.tt only at >= 4 trace rows or with a state other than tested; else p.trace-status;
  sources    no local path (.ai/, .tasks/, /home/, explainer/, review/) in visible text, title or aria (a changed
             file's own path is the repo's); no bare http(s) URL outside a link; each listed source (li#src-<origin>)
             cited by a chip and its "Cited in" linking each chip back; an origin with a url links it; no code, goal
             or non-goal entry and the per-reference store <ol hidden>; groups ordered Jira, GitHub, Shared pages,
             From the author, others, Glossary.
Quiz rules are adapted from no-leak-mcq (MIT, https://github.com/rquintino/claude-code-xtras): its word lists and the
logic of its marker-word and answer-key periodicity rules. Its significance tests are replaced by the exact score a
cue-follower gets on this quiz, capped at chance plus one question. Heuristic screening, not proof.
Exit 0 OK, 1 errors, 2 unreadable input, 3 stale (--stale).
"""
import argparse
import bisect
import copy
import glob
import html
import importlib.util
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter
from html.parser import HTMLParser


def _build_module():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build-explainer.py')
    spec = importlib.util.spec_from_file_location('build_explainer', p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


B = _build_module()
BUILD = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build-explainer.py')
KINDS = {'predict', 'why', 'where', 'impact', 'edge', 'criterion', 'rollout', 'ac-map', 'requirement', 'workflow', 'test'}
INTENT = {'requirement', 'workflow', 'why', 'criterion'}
NOCODE = ('not-built', 'non-goal', 'deferred')
PRIVATE = re.compile(r'(?i)panel|persona|simulated|(^|/)(input/|meeting|email|logs?/)|\.log(\.\d+)?(\.gz)?$|(^|[/._-])dumps?([/._-]|$)')
TOKEN_Q = re.compile(r'(?i)[?&#;](sk|token|access_token|auth|key|api_?key|sig|signature|secret|password)=')   # a share token in a link
SNAPSHOT = re.compile(r'(^|/)review/(prd|workflows)-v\d+(\.\d+)*-\d{4}-\d{2}-\d{2}\.md$')
EVIDENCE = {'tested', 'covered', 'traced', 'inferred', 'assumed'}
VOCAB_TAGS = {'p', 'h3', 'h4', 'ul', 'ol', 'li', 'strong', 'em', 'code', 'a', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
              'figure', 'figcaption', 'details', 'summary', 'pre', 'span', 'aside', 'div', 'br'}
DENY_TAGS = {'script', 'style', 'iframe', 'object', 'embed', 'link', 'meta', 'base', 'form', 'input', 'textarea',
             'select', 'button', 'frame', 'frameset', 'template', 'applet', 'noscript', 'h1', 'h2', 'svg', 'math',
             'img', 'video', 'audio', 'source'}
VOCAB_CLASSES = {'callout', 'fig', 'flow', 'node', 'edge', 'ba', 'pane', 'cards', 'card', 'toy', 'chg', 'stepper',
                 'toggle', 'th', 'ref', 'file'}
CDN = ('https://cdnjs.cloudflare.com/', 'https://cdn.jsdelivr.net/npm/', 'https://unpkg.com/',
       'https://cdn.tailwindcss.com/', 'https://code.jquery.com/')
RESERVED = re.compile(r'^(settings|sidebar|customize|upgrade|downloads|comment-.*)$')
CSS_RULE = re.compile(r'([^{}]+)\{([^{}]*)\}')


# ---------- quiz: the lean port ----------
STOP = set("the a an is are was were in on at to for of and or not it its that this with from by as be has have had "
           "do does did what which how why when where who can could would should will than each other more most one "
           "so if into then there their they".split())
ABS = re.compile(r"\b(always|never|only|all|none|every|must|cannot|impossible|guaranteed|certainly|exclusively|purely)\b", re.I)
HEDGE = re.compile(r"\b(often|usually|typically|generally|may|might|can|sometimes|tends to|in most cases|primarily)\b", re.I)
REFTOK = re.compile(r"\b(?:AC|FB|R|D|T|Q|A)\d+(?:\.[a-z0-9]+)?\b|\bs\d+\.\d+\b"
                    r"|\b[\w/.-]+\.(?:php|py|js|ts|tsx|graphql|sql|md|ya?ml|json)\b")


def vis(o):                       # visible text: `x` renders as <code>x</code>, **x** as bold
    return o.replace('`', '').replace('**', '')


def words(t):
    return {w for w in re.findall(r"\w+", t.lower()) if w not in STOP and len(w) > 2}


def spec(o):                      # digits, parentheticals, dashes, slashes, code spans
    return (len(re.findall(r"\d+", o)) + len(re.findall(r"\(.*?\)", o)) + len(re.findall(r"[—–]", o))
            + o.count('/') + o.count('`') // 2)


def position_problems(seq):
    n, out = len(seq), []
    c = [seq.count(i) for i in range(4)]
    # ponytail: strict balance lets a slot-counter deduce the last answer at N = 8 or 12; the threat is unconscious
    # cue-following, not fraud. Upgrade: allow a spread of <= 2 for N >= 8.
    if max(c) - min(c) > 1:
        out.append("positions: counts per slot %s differ by more than 1" % c)
    if any(seq[i] == seq[i + 1] == seq[i + 2] for i in range(n - 2)):
        out.append("positions: a run of 3 or more")
    for w in range(2, min(5, n // 2 + 1)):            # no-leak-mcq rule 18: a repeated cycle
        reps = 3 if w == 2 else 2
        if any(seq[s:s + w * reps] == seq[s:s + w] * reps for s in range(n - w * reps + 1)):
            out.append("positions: repeated cycle of width %d" % w)
    return out


def valid_sequence(n, seed=0):
    rnd = random.Random(seed)
    while True:
        seq = [i % 4 for i in range(n)]
        rnd.shuffle(seq)
        if not position_problems(seq):
            return ''.join('abcd'[i] for i in seq)


def follow(qs, f, best=max, tol=0):   # expected score of "pick the option with the best f, ties at random"
    s, alone = 0.0, []                    # tol: lengths within 10% (or 2 chars) of the extreme look the same
    for q in qs:
        v = [f(q, o) for o in q['options']]
        b = best(v)
        top = [i for i, x in enumerate(v) if abs(x - b) <= max(tol * b, 2 if tol else 0)]
        s += (q['answer'] in top) / len(top)
        if top == [q['answer']]:
            alone.append(q['id'])
    return s, alone


CUES = {
    'longest': (lambda q, o: len(vis(o)), max, .1),
    'shortest': (lambda q, o: len(vis(o)), min, .1),
    'stem-echo': (lambda q, o: len(words(q['stem']) & words(o)), max),
    'most-specific': (lambda q, o: spec(o), max),
    'no-absolute': (lambda q, o: not ABS.search(o), max),
    'hedged': (lambda q, o: bool(HEDGE.search(o)), max),
    'convergence': (lambda q, o: sum(len(words(o) & words(p)) for p in q['options'] if p is not o), max),
}


def lean(qs):
    """qs in page order, schema already valid. -> list of messages."""
    errs, n = [], len(qs)
    for q in qs:
        o, a = q['options'], q['answer']
        if len({re.sub(r"\s+", " ", x.strip().lower()) for x in o}) < 4:
            errs.append("duplicate: %s has two identical options" % q['id'])
        if any(re.search(r"\b(all|none|both|neither) of (the|these) (above|options)\b", x, re.I) for x in o):
            errs.append("all-none: %s uses all/none of the above" % q['id'])
        if re.search(r"\s(a|an)\W*$", q['stem'].lower()):
            errs.append("article: %s stem ends with a/an" % q['id'])
        c = len(vis(o[a]))
        m = sum(len(vis(x)) for i, x in enumerate(o) if i != a) / 3
        if abs(c - m) > max(0.3 * m, 4):           # absolute slack keeps short numeric/identifier options sane
            errs.append("length: %s key is %.2fx the distractor mean" % (q['id'], c / m if m else float('inf')))
        refs = [i for i, x in enumerate(o) if REFTOK.search(x)]
        if len(refs) == 1:
            errs.append("ref: %s only option %s cites a reference" % (q['id'], 'abcd'[refs[0]]))
        nums = [x.strip() for x in o]
        if all(re.fullmatch(r"-?\d+(?:\.\d+)?", x) for x in nums):
            v = [float(x) for x in nums]
            if v != sorted(v) and v != sorted(v, reverse=True):
                errs.append("order: %s numeric options out of natural order" % q['id'])
    seq = [q['answer'] for q in qs]
    pp = position_problems(seq)
    if pp:
        errs += ["%s (keys %s; a valid sequence: %s)" % (p, ''.join('abcd'[i] for i in seq), valid_sequence(n)) for p in pp]
    cap = n / 4 + 1                                # a cue may beat blind chance by at most one question
    for name, (f, best, *tol) in CUES.items():
        s, alone = follow(qs, f, best, *tol)
        if s > cap + 1e-9:
            errs.append("cue: picking %s scores %.1f/%d (cap %.2f); it alone finds the key at %s"
                        % (name, s, n, cap, ', '.join(alone) or 'no single question'))
    cw, iw = Counter(), Counter()
    for q in qs:
        for i, x in enumerate(q['options']):
            (cw if i == q['answer'] else iw).update(w for w in re.findall(r"\w+", x.lower()) if w not in STOP and len(w) > 3)
    for w, k in cw.items():
        if (k >= 3 and not iw[w]) or (k >= 4 and k / (k + iw[w]) > .6):
            errs.append("marker: '%s' is in %d keys, %d distractors" % (w, k, iw[w]))
    return errs


SHA = re.compile(r'\b(?=[0-9a-f]*\d)(?=[0-9a-f]*[a-f])[0-9a-f]{7,40}\b', re.I)
LOC = r'\b[\w/.-]+\.[A-Za-z]\w{0,5}:\d+(?:-\d+)?\b'
LABELS = [  # (regex, what it names, the fix): labels a reader would have to recall, not understand
    (SHA, 'commit', 'describe the change instead (the commit belongs in evidence)'),
    (re.compile(LOC + r'|\blines? \d+\b', re.I), 'location',
     'name what the code does there (file:line belongs in evidence)'),
    (re.compile(r'§\s*\d[\w.]*'), 'section', 'name what the section says (the section belongs in feedback)'),
    (re.compile(r'\bexit(?: codes?\b|\s+\d+\b)', re.I), 'exit code', 'describe what the caller sees (the code belongs in feedback)'),
]


def labels(q, refs):
    """Stem and options only (feedback and evidence may cite labels). -> list of messages."""
    ids = [re.escape(k) for k in refs if not k.startswith(('file:', 'commit:'))]
    # whole tokens only: `skunexus-jira-prd`, docs/D1.md and the R1 of R1.a are not ref ids
    rx = LABELS + [(re.compile(r'(?<![\w./-])(?:%s)(?![\w/-]|\.[\w-])' % '|'.join(ids)), 'ref id',
                    'say what it means in plain words (the id belongs in evidence)')] * bool(ids)
    out = []
    for where, t in [('stem', q['stem'])] + [('option ' + 'abcd'[i], o) for i, o in enumerate(q['options'])]:
        for r, what, fix in rx:
            mo = r.search(t)
            if mo:
                out.append('label: %s %s names %s %s: %s' % (q['id'], where, what, mo.group(0), fix))
    return out


HISTORY = re.compile(r'(?i:\brebuil[dt]\b|\bround \d+\b|\bthis build\b)|\badds What was asked\b')
READER = (('hotspots', 'why'), ('hotspots', 'label'), ('drift', 'note'), ('ops', 'what'), ('ops', 'note'), ('ops', 'label'), ('open_questions', None),
          ('chapters', 'title'), ('chapters', 'short'), ('chapters', 'why_here'), ('chapters', 'gist'), ('chapters', 'proof'),
          ('glossary', 'term'), ('glossary', 'def'), ('mechanical', 'intent'), ('trace', 'text'), ('trace', 'note'),
          ('not_in_change', None), ('not_in_change', 'text'), ('deeper', 'summary'))


def plan_prose(plan):
    """[(where, text)]: the plan.json prose a reader meets (the lead, the problem, the map's words, the READER lists)."""
    out = [('plan.json %s' % k, plan[k]) for k in ('glance', 'problem') if isinstance(plan.get(k), str)]
    for key, f in READER:
        for i, x in enumerate(plan.get(key) or []):
            v = x.get(f) if f and isinstance(x, dict) else None if f else x
            if isinstance(v, str):
                out.append(('plan.json %s[%d]%s' % (key, i, '.' + f if f else ''), v))
    mp = plan.get('map') if isinstance(plan.get('map'), dict) else {}
    for k in ('purpose', 'entries_h', 'rule_h', 'outcomes_h', 'arrow', 'so'):
        if isinstance(mp.get(k), str):
            out.append(('plan.json map.%s' % k, mp[k]))
    for lst in ('entries', 'outcomes'):
        for i, e in enumerate(mp.get(lst) or []):
            for k in ('label', 'sub'):
                if isinstance(e, dict) and isinstance(e.get(k), str):
                    out.append(('plan.json map.%s[%d].%s' % (lst, i, k), e[k]))
    r = mp.get('rule') if isinstance(mp.get('rule'), dict) else {}
    out += [('plan.json map.rule.%s' % k, r[k]) for k in ('title', 'sub') if isinstance(r.get(k), str)]
    out += [('plan.json map.rule.conditions[%d]' % i, x['text']) for i, x in enumerate(r.get('conditions') or [])
            if isinstance(x, dict) and isinstance(x.get('text'), str)]
    return out


def reader(plan, frags, E, W):
    """Write for the reader, not the log: name the thing, never just its label. Chips, <pre>, evidence and the quiz
    are out of scope; ids are also fine in code spans and tables (toy data). A list item starts with \x01, so its
    own "R5:" label is allowed. -> [(where, text, text for the id scan or None)]"""
    texts = []
    for k, t in frags.items():
        t = re.sub(r'(?i)<li\b[^>]*>', '\x01', B.REFSPAN.sub(' ', re.sub(r'(?is)<pre\b.*?</pre>|<a\b[^>]*\bclass="ref\b[^>]*>.*?</a>', ' ', t)))
        texts.append(('fragments/%s.html' % k, plain(t), plain(re.sub(r'(?is)<code\b.*?</code>|<table\b.*?</table>', ' ', t))))
    for w, v in plan_prose(plan):
        texts.append((w, '\x01' + v, '\x01' + re.sub(r'`[^`]*`', ' ', v) if not w.startswith('plan.json trace') else None))
    keys = [re.escape(k) for k in plan.get('refs') or {} if not k.startswith(('file:', 'commit:'))]
    idrx = re.compile(r'(?<![\w./-])(?:%s)(?![\w/-]|\.[\w-])' % '|'.join([B.PIPE_ID] + keys))
    for where, t, tid in texts:
        for x in dict.fromkeys(SHA.findall(t)):
            E('reader', '%s names commit %s in prose: say what the commit did; the hash belongs in a chip or evidence' % (where, x))
        for x in dict.fromkeys(re.findall(LOC, t)):
            E('reader', '%s names %s in prose: move the location into a chip' % (where, x))
        mo = HISTORY.search(t) if where == 'plan.json glance' else None
        if mo:
            E('reader', '%s tells the page\'s own history (%r): describe the change and how to read the page; '
                        'rebuilds belong in artifact.md' % (where, mo.group(0)))
        bare = list(dict.fromkeys(mo.group(0) for mo in idrx.finditer(tid or '') if not (
            re.search(r'\x01\s*$', tid[:mo.start()]) and re.match(r'\s*[:—]', tid[mo.end():]))))
        if bare:
            W('reader', '%s: bare %s in prose: lead with what %s says; attach the id as a chip' % (where, ', '.join(bare), bare[0]))


def budget(ctx, chapters, ucs, W, info):
    """Soft prose budgets (write.md), warnings only. Visible words: outside <pre>, <details> and chips. The gate is the
    root budget (check_shape); the must path is information there, never a gate."""
    frags = ctx['frags']
    for i, c in enumerate(chapters):
        cid, raw = c.get('id'), frags.get(c.get('id')) or ''
        g = str(c.get('gist') or '').split()
        if len(g) > 30:
            W('budget', 'piece %d (%s): gist is %d words: one sentence of at most 30' % (i + 1, cid, len(g)))
        w = B.prose_words(raw)
        if w > 450:
            W('budget', 'fragments/%s.html: %d visible words: aim for 150-400' % (cid, w))
        if c.get('read', 'must') == 'must':
            v = B.prose_words(raw.partition('<!--more-->')[0])
            if v > 120:
                W('budget', 'piece %d (%s): %d words before <!--more-->: the visible note is at most ~120; the rest goes '
                            'under More on this' % (i + 1, cid, v))
    for k, cap, why in (('asked', 900 if ucs > 5 else 600, ' (%d use cases)' % ucs if ucs > 5 else ''), ('background', 300, '')):
        w = B.prose_words(frags.get(k)) if k in frags else 0
        if w > cap:
            W('budget', 'fragments/%s.html: %d visible words: at most %d%s; move detail into a details.toggle' % (k, w, cap, why))


# ---------- helpers ----------
def strip_bodies(page):
    """Markup with script and style bodies and comments removed (tags kept)."""
    page = re.sub(r'(?is)(<script\b[^>]*>).*?</script>', r'\1</script>', page)
    page = re.sub(r'(?is)(<style\b[^>]*>).*?</style>', r'\1</style>', page)
    return re.sub(r'(?s)<!--.*?-->', '', page)


def plain(markup):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', markup))).strip()


QUOTES = str.maketrans({'\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"', '\u2026': '...'})


def norm(t):
    """Markdown and typography out: [x](u) -> x, > prefixes, *_` marks, curly quotes, \u2026; whitespace collapsed."""
    t = re.sub(r'(?m)^[ \t]*>+', ' ', re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', t))
    return re.sub(r'\s+', ' ', re.sub(r'[*_`]', '', t.translate(QUOTES))).strip()


class Tags(HTMLParser):
    """Start tags as (tag, [(name, value)]): names lowercased, values unescaped, '/' splits attributes as browsers do."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []

    def handle_starttag(self, tag, attrs):
        self.out.append((tag, attrs))


def is_marker(t):
    return t[0] == 'pre' and any(k in ('data-hunk', 'data-code') for k, _ in t[1])


def tags(markup):
    p = Tags()
    p.feed(markup)
    p.close()
    return p.out


def xd_data(page):
    m = re.search(r'(?is)<script\b[^>]*\bid="xd-data"[^>]*>(.*?)</script>', page or '')
    return m and m.group(1)


def node_check(js):
    node = shutil.which('node')
    if not node:
        return None
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f:
        f.write(js)
    r = subprocess.run([node, '--check', f.name], capture_output=True, text=True)
    os.unlink(f.name)
    return '' if r.returncode == 0 else (r.stderr.strip().splitlines() or ['?'])[-1]


def load(d, repo=None):
    d = os.path.abspath(d)
    ctx = {'dir': d, 'repo': B.find_repo(d, repo), 'map': B.read_json(d, 'map.json'), 'plan': B.read_json(d, 'plan.json'),
           'quiz': B.read_json(d, 'quiz.json', need=False), 'frags': B.read_frags(d), 'page': None, 'local': None}
    for k, n in (('page', 'explainer.html'), ('local', 'explainer.local.html')):
        p = os.path.join(d, n)
        if os.path.exists(p):
            with open(p, encoding='utf-8') as fh:
                ctx[k] = fh.read()
    return ctx


# ---------- checks ----------
def moved(ctx):
    """[(name, hash at build, hash now)] for each why-source that changed since the build; None with no built page."""
    try:
        old = (json.loads(xd_data(ctx['page'] or '') or 'null') or {}).get('meta', {}).get('inputs')
    except (ValueError, AttributeError):
        old = None
    if not isinstance(old, dict):
        return None
    new = B.source_hashes(ctx['repo'], ctx['dir'], ctx['plan'].get('sources') or [])
    return [(k, old.get(k), new.get(k)) for k in dict.fromkeys(list(old) + list(new)) if old.get(k) != new.get(k)]


def private(ctx, s, p):
    """A path the page must never quote: input/, meeting*, email*, panel/persona/simulated, another skill's review/."""
    if p and os.path.abspath(p).startswith(ctx['dir'] + os.sep):
        return False                       # the page's own review/ and sources/
    rel = '/' + (os.path.relpath(p, ctx['repo']).replace(os.sep, '/') if p else s)
    own = '/explainer/review/' in rel                 # a page's own review/, also when checked from a copy
    return '/.ai/' in rel and bool(PRIVATE.search(rel) or ('/review/' in rel and not SNAPSHOT.search(rel) and not own))


def ran_at(ctx, h7):
    """review/tests-<h7>.txt exists and names h7 (its last line: at <h7> on <date>)."""
    p = os.path.join(ctx['dir'], 'review', 'tests-%s.txt' % h7)
    return os.path.isfile(p) and h7 in B.read_text(p)


def check(ctx, forbid=()):
    err, warn, info = [], [], []
    E = lambda k, m: err.append((k, m))       # noqa: E731
    W = lambda k, m: warn.append((k, m))      # noqa: E731
    m, plan, quiz, frags, page = ctx['map'], ctx['plan'], ctx['quiz'], ctx['frags'], ctx['page']
    src = B.Src(ctx['repo'], m)
    stage = B.stage_of(plan, m)
    nocode = stage == 'intent-only'
    chapters = plan.get('chapters') or []

    # plan: stage
    if stage not in B.STAGES:
        E('plan', 'stage %r is not %s' % (stage, '|'.join(B.STAGES)))
    if m.get('intent_only') and not nocode:
        E('plan', 'map.json is intent-only (no code): plan.json stage must be intent-only')
    if nocode:
        if m['files']:
            E('plan', 'stage intent-only, but map.json lists %d changed files: map with --intent-only, or stage full' % len(m['files']))
        for k in ('chapters', 'mechanical', 'hotspots'):
            if plan.get(k):
                E('plan', 'intent-only (no code yet): %s must be empty' % k)

    # plan: sources, private material, the layers they require
    found = {}
    for s_ in list(plan.get('sources') or []) + list(m.get('sources_found') or []):
        p = B.find_file(ctx['repo'], ctx['dir'], s_)
        if s_ in (plan.get('sources') or []) and not p:
            E('plan', 'source %s not found (looked in the repo, the explainer dir and its parent)' % s_)
        if s_ in (plan.get('sources') or []) and private(ctx, s_, p):
            E('plan', 'source %s is private material or a persona review: never quote it' % s_)
        name = 'prototype/artifact.md' if s_.endswith('prototype/artifact.md') else os.path.basename(s_)
        if p and name not in found:
            found[name] = p
    asked_why = sorted(set(found) & set(B.ASKED)) + sorted(
        {os.path.basename(s_) for s_ in plan.get('sources') or [] if B.ASK_SRC.fullmatch(os.path.basename(s_))
         or B.BUG_NOTES.fullmatch(os.path.basename(s_)) or '/investigation/' in '/' + s_})
    proven_why = ('a test file changed' if any(f['kind'] == 'test' for f in m['files']) else
                  'spec-from-tests.md is a source' if 'spec-from-tests.md' in found else
                  'review/tests-*.txt exists' if glob.glob(os.path.join(ctx['dir'], 'review', 'tests-*.txt')) else '')
    origins = plan.get('origins') if isinstance(plan.get('origins'), dict) else {}
    sb = (plan.get('contract') or {}).get('storyboard') if isinstance(plan.get('contract'), dict) else None
    for k, o in [('origins %s' % k, o) for k, o in origins.items()] + [('contract.storyboard', sb)]:
        mo = TOKEN_Q.search(str((o or {}).get('url') or '') if isinstance(o, dict) else '')
        if mo:
            E('sources', '%s: its url carries a share token (%s=): strip it from the query; the page links the plain URL' % (k, mo.group(1)))
    if asked_why and 'asked' not in frags:
        E('plan', 'fragments/asked.html is missing: %s %s' % (', '.join(asked_why), 'are sources' if len(asked_why) > 1 else 'is a source'))
    if proven_why and 'proven' not in frags:
        E('plan', 'fragments/proven.html is missing: %s' % proven_why)
    for k in ('background', 'intuition'):
        if k not in frags:
            E('plan', 'fragments/%s.html is missing: every page has a Background and an Intuition' % k)
    if 'asked' in frags:
        info.append('asked.html: %d words (chips excluded)' % len(plain(re.sub(r'(?is)<span\b[^>]*\bdata-ref\b[^>]*>.*?</span>', ' ', frags['asked'])).split()))
    ucs = len(re.findall(r'(?m)^#{2,4}[ \t]+s\d+\b', B.read_text(found['workflows.md']))) if 'workflows.md' in found else 0
    lay = {'stage': stage, 'intent': bool(asked_why or 'asked' in frags or set(found) & {'decisions.md', 'feedback.md', 'jira-summary.md'}),
           'test': bool(proven_why or 'proven' in frags), 'criteria': 0}
    info.append('layers: %s' % ', '.join(['asked'] * lay['intent'] + ['built'] * (not nocode) + ['proven'] * lay['test']))

    # plan
    ids = [c.get('id') for c in chapters]
    tests = 'review/tests-%s.txt' % m['head'][:7]
    ran = ran_at(ctx, m['head'][:7])
    if 'toy' in plan and not isinstance(plan['toy'], str):
        E('plan', 'toy: want one text block (the toy world every fragment and stem reuses)')
    facts = Counter()
    for c in chapters:
        ck = c.get('checks', [])
        if not isinstance(ck, list) or not all(isinstance(x, str) and x.strip() for x in ck):
            E('plan', '%s: checks: want a list of one-line facts' % c.get('id'))
        else:
            facts.update({norm(x).lower() for x in ck})
    for x, k in facts.items():
        if k > 1:
            W('plan', 'checks: %d pieces test the same fact %r: one question per fact' % (k, x))
    for c in chapters:
        cid = c.get('id')
        if not isinstance(cid, str) or not re.fullmatch(r'ch-[a-z0-9-]+', cid) or cid == 'ch-mech' or ids.count(cid) > 1:
            E('plan', 'chapters[] id %r: want a unique ch-<n> (not ch-mech)' % cid)
        if c.get('read', 'must') not in ('must', 'skim'):
            E('plan', '%s: read %r is not must|skim' % (cid, c.get('read')))
        if c.get('risk') not in ('high', 'med', 'low'):
            E('plan', '%s: risk %r is not high|med|low' % (cid, c.get('risk')))
        if c.get('evidence') not in EVIDENCE:
            E('plan', '%s: evidence %r is not %s' % (cid, c.get('evidence'), '|'.join(sorted(EVIDENCE))))
        elif c['evidence'] == 'tested' and not ran:
            E('plan', "%s: evidence tested needs %s naming %s (the developer's run at head); else covered" % (cid, tests, m['head'][:7]))
        if cid not in frags:
            E('plan', 'fragments/%s.html is missing' % cid)
    for g in plan.get('mechanical') or []:
        if not g.get('intent') or not g.get('check'):
            W('plan', 'mechanical group %r needs a one-line intent and a concrete check' % g.get('title'))
    for k in frags:
        if k not in ids and k not in ('asked', 'background', 'intuition', 'proven'):
            W('plan', 'fragments/%s.html belongs to no piece (plan.json chapters[])' % k)
    refs = plan.get('refs') or {}
    mv = moved(ctx)
    for k, old, new in mv or []:
        W('stale', 'why-source changed since build: %s@%s → %s' % (k, old or '(none)', '@' + new if new else 'gone'))
    still = lambda name: name not in {k for k, _, _ in mv or []}      # noqa: E731  (a moved source is the warning's job)
    prd = found.get('prd.md')
    prd_t = B.read_text(prd) if prd else ''
    pc = plan.get('contract')
    if prd and still('prd.md'):
        c = B.contract_of(prd_t)
        if c is None and pc:
            E('plan', 'contract: prd.md has no > Versions: lines, so plan.json contract is null')
        elif c and (not isinstance(pc, dict) or (pc.get('version'), pc.get('status')) != (c['version'], c['status'])):
            E('plan', 'contract %r: prd.md says {"version": "%s", "status": "%s"} (map.json contract has it)'
              % (pc and {k: pc.get(k) for k in ('version', 'status')}, c['version'], c['status']))
    if 'prototype/artifact.md' in found and isinstance(pc, dict) and still('artifact.md'):
        sbx, sbp = B.storyboard_of(B.read_text(found['prototype/artifact.md'])), pc.get('storyboard') or {}
        if (sbp.get('url'), sbp.get('built_from')) != (sbx['url'], sbx['built_from']):
            E('plan', 'contract.storyboard %r: prototype/artifact.md says %r' % (sbp or None, sbx))
    if 'prototype/artifact.md' in found:          # the newest row wins; a header that lags it is the storyboard's to fix
        t_ = B.read_text(found['prototype/artifact.md'])
        hv, rv = (re.search(r'\bv\d+(?:\.\d+)*', x or '') for x in ((B.SB_HEADER.search(t_) or [None, ''])[1], B.storyboard_of(t_)['built_from']))
        if hv and rv and hv.group(0) != rv.group(0):
            W('plan', 'prototype/artifact.md header says %s, newest row %s' % (hv.group(0), rv.group(0)))

    # trace: every criterion placed once, each state backed by its evidence
    trace = [r for r in plan.get('trace') or [] if isinstance(r, dict)]
    tids = [str(r.get('id')) for r in trace]
    need = {}
    if prd:
        label, crit = B.criteria(prd_t)
        lay['criteria'] = len(crit)
        need.update((i, 'prd.md') for i in crit)
        info.append('criteria: %d in prd.md%s' % (len(crit), ' (%s)' % label if label else ''))
    if 'investigation.md' in found:
        need.update((i, 'investigation.md') for i in re.findall(r'\bA\d+\b', B.read_text(found['investigation.md'])))
    for i, where in need.items():
        if i not in tids:
            E('trace', '%s (%s) has no trace row: place every criterion exactly once' % (i, where))
    for i, k in Counter(tids).items():
        if k > 1:
            E('trace', '%s has %d trace rows: exactly once' % (i, k))
        if prd and i not in need and not i.startswith('goal.') and not ('workflows.md' in found and re.fullmatch(r's\d+\.\d+', i)):
            W('trace', '%s is not a criterion in prd.md' % i)
    drift_refs = {str(d.get('ref')) for d in plan.get('drift') or [] if d.get('needs_decision')}
    for r in trace:
        rid, st = str(r.get('id')), r.get('state')
        built, proven = r.get('built') or [], r.get('proven') or []
        why = ('state %r is not %s' % (st, '|'.join(B.STATES)) if st not in B.STATES else
               'intent-only (no code yet): want not-built, non-goal or deferred' if nocode and st not in NOCODE else
               'tested needs a non-empty proven' if st == 'tested' and not proven else
               "tested needs %s naming %s (the developer's run at head); else built" % (tests, m['head'][:7])
               if st == 'tested' and not ran else
               'built needs a non-empty built and proven' if st == 'built' and not (built and proven) else
               'untested needs a non-empty built' if st == 'untested' and not built else
               '%s needs a note' % st if st in NOCODE and not str(r.get('note') or '').strip() else
               'drift needs a plan.json drift entry with ref %s and needs_decision true' % rid if st == 'drift' and rid not in drift_refs else '')
        if why:
            E('trace', '%s: %s' % (rid, why))
    if trace:
        info.append('trace: %d rows (%s)' % (len(trace), ', '.join('%d %s' % (k, st) for st, k in Counter(r.get('state') for r in trace).items())))
    for d in plan.get('drift') or []:
        if not d.get('note') or not isinstance(d.get('needs_decision', False), bool):
            E('plan', 'drift at %r: needs a note and needs_decision true|false' % d.get('at'))
        elif not d.get('needs_decision') and str((refs.get(str(d.get('ref'))) or {}).get('src')).endswith('prd.md'):
            E('plan', 'drift at %r breaks prd.md (%s): needs_decision must be true' % (d.get('at'), d['ref']))
    if any(not o.get('what') for o in plan.get('ops') or []):
        E('plan', 'every ops entry needs a what')
    if not plan.get('ops') and any(f['kind'] in ('migration', 'config') for f in m['files']):
        W('plan', 'a migration or config file changed but ops is empty: say how it deploys and rolls back')

    # 1. coverage
    owners, dead = B.assign(plan, m['files'])
    for f in m['files']:
        o = owners[f['path']]
        if not o:
            E('coverage', '%s is in no piece (plan.json chapters[]) or mechanical group' % f['path'])
        elif len(o) > 1:
            E('coverage', '%s is in %d owners: %s' % (f['path'], len(o), ', '.join(o)))
        elif f['tier'] == 'read' and o[0].startswith('ch-mech'):
            E('coverage', '%s is read-tier but sits in a mechanical group (never down a tier)' % f['path'])
    for o, g in dead:
        W('coverage', '%s: glob %r matches no changed file' % (o, g))
    info.append('coverage: %d files, %d pieces, %d mechanical groups' % (len(m['files']), len(chapters), len(plan.get('mechanical') or [])))

    # 2. markers: build resolves them and leaves a failed one in the page
    ftags, nmark = {k: tags(v) for k, v in frags.items()}, 0
    for name, t in frags.items():
        found = len(B.MARKER.findall(t))
        nmark += found
        if sum(map(is_marker, ftags[name])) != found:
            E('marker', 'fragments/%s.html: a code marker must be an empty <pre data-hunk|data-code="..."></pre>' % name)
    ptags = tags(strip_bodies(page)) if page is not None else []
    if any(map(is_marker, ptags)):
        E('marker', 'an unresolved code marker is left in explainer.html: see the build output')
    info.append('markers: %d' % nmark)

    # 3. refs
    for rid, r in refs.items():
        text, s = (r or {}).get('text', ''), (r or {}).get('src', '')
        if len(norm(text)) < 12:
            E('ref', '%s: the quote %r is under 12 characters: quote the sentence that says it' % (rid, text))
            continue
        if not s or re.match(r'https?://', s):
            continue
        p = B.find_file(ctx['repo'], ctx['dir'], s)
        if ('/' in s or p) and private(ctx, s, p):
            E('ref', '%s: src %s is private material or a persona review: never quote it' % (rid, s))
        if p is None:
            if '/' in s or re.search(r'\.\w{1,5}$', s):
                E('ref', '%s: src %s not found (looked in the repo, the explainer dir and its parent)' % (rid, s))
            continue
        body = B.read_text(p)
        if norm(text) not in norm(body):
            E('ref', '%s: its text is not found in %s (an invented or edited quote?)' % (rid, s))
        elif re.fullmatch(r'FB\d+', rid):
            blk = re.search(r'(?ms)^#+[ \t]+%s\b.*?(?=^#+[ \t]|\Z)' % rid, body)
            if not blk:
                E('ref', '%s: %s has no "### %s" entry' % (rid, s, rid))
            elif not any(norm(text) in norm(ln) for ln in blk.group(0).splitlines() if 'Status:' in ln):
                E('ref', '%s: quote only its **Status:** line, in its own entry (the ruling, not the discussion)' % rid)

    # 4. fragment safety: html.parser splits attributes as a browser does (on '/' too)
    forge = m.get('forge')
    for name, t in frags.items():
        where = 'fragments/%s.html' % name
        if re.search(r'<[A-Za-z][^>]*\Z', t):
            E('safety', '%s: an unclosed tag at the end (the build appends markup to it)' % where)
        for tag, at in ftags[name]:
            if tag in DENY_TAGS:
                E('safety', '%s: <%s> is not allowed' % (where, tag))
            elif tag not in VOCAB_TAGS:
                W('safety', '%s: <%s> is outside the fragment vocabulary' % (where, tag))
            for k, v in at:
                if k.startswith('on'):
                    E('safety', '%s: an event handler attribute %s=' % (where, k))
                elif k in ('style', 'src', 'srcdoc', 'formaction'):
                    E('safety', '%s: a %s= attribute' % (where, k))
                elif re.match(r'(javascript|vbscript|data):', re.sub(r'[\x00-\x20]+', '', v or '').lower()):
                    E('safety', '%s: a javascript: or data: URL in %s=' % (where, k))
                elif k == 'href' and v is not None and not v.startswith('#') and not (forge and v.startswith(forge + '/')):
                    E('safety', '%s: external href %s (only #id or the forge)' % (where, v))
                elif k == 'class':
                    for c in (v or '').split():
                        if c not in VOCAB_CLASSES:
                            W('safety', '%s: class %r is outside the vocabulary' % (where, c))

    # 5. quiz, then the prose a reader meets and its length
    check_quiz(ctx, src, E, W, info, lay)
    reader(plan, frags, E, W)
    budget(ctx, [] if nocode else chapters, ucs, W, info)

    # 6-8. the built page
    if page is None:
        E('contract', 'explainer.html is missing: run build-explainer.py build')
    else:
        check_page(page, ctx['local'], ptags, B.inputs_hash(m, plan, quiz, frags), E, W, info)
        check_shape(ctx, E, W, info)
    for rx in forbid:
        hay = [('explainer.html', page or ''), ('plan.json', json.dumps(plan, ensure_ascii=False)),
               ('quiz.json', json.dumps(quiz, ensure_ascii=False))] + [('fragments/%s.html' % k, v) for k, v in frags.items()]
        for n, h in hay:
            mo = re.search(rx, h)
            if mo:
                E('forbid', '%s: /%s/ matches %r' % (n, rx, mo.group(0)[:60]))
    return err, warn, info


def check_quiz(ctx, src, E, W, info, lay):
    plan, quiz, m, page = ctx['plan'], ctx['quiz'], ctx['map'], ctx['page']
    if not isinstance(quiz, dict) or not isinstance(quiz.get('questions'), list) or not quiz['questions']:
        E('quiz', 'schema: quiz.json needs a non-empty "questions" list')
        return
    qs = quiz['questions']
    bf = str(quiz.get('built_from', ''))
    if len(bf) < 7 or not m['head'].startswith(bf):
        E('quiz', 'built_from %r is not the map head %s: re-verify every key at head' % (bf, m['head'][:7]))
    chs = {c.get('id') for c in plan.get('chapters') or []}
    skim = {c.get('id') for c in plan.get('chapters') or [] if c.get('read', 'must') == 'skim'}
    cids = chs | ({'ch-mech'} if plan.get('mechanical') else set())
    cids |= {k for k in ('asked', 'background', 'intuition', 'proven') if k in ctx['frags']}
    bad, seen = [], set()
    for q in qs:
        qid = q.get('id')
        o, fb = q.get('options'), q.get('feedback')
        why = []
        if not isinstance(qid, str) or not re.fullmatch(r'[a-z0-9-]+', qid) or qid in seen:
            why.append('a unique id [a-z0-9-]+')
        seen.add(qid)
        if q.get('chapter') not in cids:
            why.append('chapter %r to resolve' % q.get('chapter'))
        if not isinstance(q.get('final'), bool):
            why.append('final true|false')
        elif not q['final'] and q.get('chapter') in cids - chs:
            why.append('final true (only a piece takes checkpoints; %s questions are finals)' % q.get('chapter'))
        elif not q['final'] and q.get('chapter') in skim:
            why.append('final true: a piece under Go deeper takes no checkpoint: its row is closed, so the question would be '
                       'folded; make it a final or move it to a main-flow piece')
        if q.get('kind') not in KINDS:
            why.append('kind in %s' % '|'.join(sorted(KINDS)))
        if not isinstance(q.get('stem'), str) or not q['stem'].strip():
            why.append('a stem')
        if not isinstance(o, list) or len(o) != 4 or not all(isinstance(x, str) and x.strip() for x in o):
            why.append('4 options')
        if not isinstance(q.get('answer'), int) or isinstance(q.get('answer'), bool) or q['answer'] not in range(4):
            why.append('answer 0-3')
        if not isinstance(fb, list) or len(fb) != 4 or not all(isinstance(x, str) and x.strip() for x in fb):
            why.append('4 feedback strings')
        if not isinstance(q.get('evidence'), list) or not q['evidence']:
            why.append('evidence (>= 1 place the key is proven)')
        if why:
            bad.append('%s needs %s' % (qid, ', '.join(why)))
    if bad:
        for b in bad:
            E('quiz', 'schema: ' + b)
        return                                   # a schema error stops the rest
    order = B.quiz_order(plan, quiz)
    n, finals = len(order), [q for q in order if q['final']]
    info.append('quiz: %d questions (%d final), keys %s' % (n, len(finals), ''.join('abcd'[q['answer']] for q in order)))
    if [q['id'] for q in order] != ['q%d' % i for i in range(1, n + 1)]:
        W('quiz', 'ids are not q1..q%d in page order (%s): the result line reads easier when they are' % (n, ' '.join(q['id'] for q in order)))
    sets = {}                 # a cross-question cue: the same four options under two stems
    for q in order:
        sets.setdefault(frozenset(re.sub(r'\s+', ' ', vis(o)).strip().lower() for o in q['options']), []).append(q['id'])
    for ids in sets.values():
        if len(ids) > 1:
            W('quiz', '%s share one option set: one answer may give the other away; vary the options' % ', '.join(ids))
    if n > 12:
        E('quiz', '%d questions: at most 12 (neighbouring pieces share a checkpoint)' % n)
    rl = m['totals']['by_tier']['read']['add'] + m['totals']['by_tier']['read']['del']
    big = lay['criteria'] > 8 if lay['stage'] == 'intent-only' else rl > 150
    if not 3 <= len(finals) <= 5 or (len(finals) < 5 and big):
        E('quiz', 'the final quiz has %d questions: want 5 (3-5 when read-tier lines <= 150, or intent-only with <= 8 '
                  'criteria; here %d lines, %d criteria)' % (len(finals), rl, lay['criteria']))
    if lay['intent'] and not any(q['kind'] in INTENT for q in finals):
        E('quiz', 'layer coverage: the Asked layer exists, but no final question is requirement|workflow|why|criterion')
    if lay['test'] and not any(q['kind'] == 'test' for q in finals):
        E('quiz', 'layer coverage: the Proven layer exists, but no final question is a test (ac-map is not one)')
    if lay['stage'] == 'intent-only':
        for q in order:
            if q['kind'] not in ('requirement', 'workflow', 'why'):
                E('quiz', '%s: kind %s in an intent-only quiz: requirement|workflow|why only (no code yet)' % (q['id'], q['kind']))
    chs = plan.get('chapters') or []
    num = {c.get('id'): 'piece %d (%s)' % (i + 1, c.get('id')) for i, c in enumerate(chs)}
    main = [c.get('id') for c in chs if c.get('read', 'must') == 'must']      # the relaxed rule: main-flow pieces only
    per = Counter(q['chapter'] for q in order if not q['final'])
    if len(main) <= 4 and per:
        W('quiz', 'a small change (<= 4 main-flow pieces) takes final questions only, not checkpoints')
    for d in plan.get('drift') or []:
        rx = r'(?<![\w.])%s(?!\.?\w)' % re.escape(str(d.get('ref')))
        for q in order:
            if d.get('needs_decision') and d.get('ref') and q['kind'] in ('criterion', 'ac-map') and re.search(rx, ' '.join([q['stem']] + q['evidence'])):
                E('quiz', '%s: a %s question on %s, a drift that needs a decision' % (q['id'], q['kind'], d['ref']))
    for c, k in per.items():
        if k > 2:
            E('quiz', '%s has %d checkpoints: at most 2' % (num.get(c, c), k))
    if len(main) > 4 and n < 12:
        for c in main:
            if not per.get(c):
                W('quiz', '%s has no checkpoint: past 4 main-flow pieces, each takes one or two, open at the piece\'s end' % num[c])
    for e in lean(order):
        E('quiz', e)
    for q in order:
        for e in labels(q, plan.get('refs') or {}):
            E('quiz', e)
        if q['stem'].count('`') // 2 > 3:
            W('quiz', '%s stem has %d code spans: reads like implementation trivia; name the behaviour in plain words'
                      % (q['id'], q['stem'].count('`') // 2))
    neg =[q['id'] for q in order if re.search(r'\*\*(NOT|EXCEPT)\*\*', q['stem'])]
    for q in order:
        if re.search(r'\b(NOT|EXCEPT)\b', re.sub(r'\*\*(NOT|EXCEPT)\*\*', '', q['stem'])):
            E('quiz', '%s: write a negation as **NOT** (bold)' % q['id'])
    if len(neg) > 1:
        E('quiz', 'negation stems %s: at most one' % ', '.join(neg))
    if len(finals) >= 3 and len({q['kind'] for q in finals}) < 3:
        W('quiz', 'the final questions span %d kinds: want >= 3' % len({q['kind'] for q in finals}))
    def at(s):
        p = B.find_file(ctx['repo'], ctx['dir'], str(s or ''))
        return os.path.realpath(p) if p else None
    notes = {at(s) for s in plan.get('sources') or [] if B.path_kind(str(s))[0] == 'docs'} - {None}
    refs = plan.get('refs') if isinstance(plan.get('refs'), dict) else {}

    def recorded(e):        # the evidence quotes a note in plan.json sources (by a ref id, or by the note's name)
        return any(at(refs[t].get('src') if isinstance(refs.get(t), dict) else t) in notes for t in str(e).split())
    for q in order:
        if q['kind'] == 'why' and not any(re.search(r'(?i)decisions|prd|pr\.md|\bPR\b|#\d+|\b(?:[DRQ]|FB)\d+|feedback|answers', e)
                                          or recorded(e) for e in q['evidence']):
            W('quiz', '%s: a why question needs a recorded source (decisions, PRD, ruling, PR text, or a note in plan.json sources)' % q['id'])
        for ev in q['evidence']:
            mo = re.match(r'^([^\s:]+\.[A-Za-z0-9]+):(\d+)(?:-(\d+))?$', str(ev))
            if mo and not ev.startswith('.ai/') and ('/' in mo.group(1) or mo.group(1) in src.files):
                ls = src.lines(mo.group(1))
                if ls is None:
                    E('quiz', '%s: evidence %s does not exist at head' % (q['id'], ev))
                elif not 1 <= int(mo.group(2)) <= int(mo.group(3) or mo.group(2)) <= len(ls):
                    E('quiz', '%s: evidence %s is outside the file (%d lines)' % (q['id'], ev, len(ls)))
    if page is None:
        return
    mk = strip_bodies(page)
    text = norm(plain(mk))
    for q in order:
        for i, f in enumerate(q['feedback']):
            if len(norm(f)) >= 24 and norm(f) in text:
                E('quiz', '%s: feedback %s is pre-rendered in the markup (JS adds it after the pick)' % (q['id'], 'abcd'[i]))
    sets = [tags(x) for x in re.findall(r'(?is)<fieldset\b.*?</fieldset>', mk)]
    have = {dict(t[0][1]).get('id') for t in sets}
    for q in order:
        if q['id'] not in have:
            E('quiz', '%s: no <fieldset class="q" id="%s"> in the page' % (q['id'], q['id']))
    for _, at in (x for t in sets for x in t):
        leak = [k for k, _ in at if (k.startswith('data-') and k != 'data-i') or k in ('aria-checked', 'aria-pressed', 'aria-selected')]
        leak += [c for k, v in at if k == 'class' for c in (v or '').split() if c in ('correct', 'key', 'right', 'wrong', 'answer')]
        if leak:
            E('quiz', 'the quiz markup carries %s: the key lives only in xd-data' % ', '.join(leak))


def check_page(page, local, ptags, inputs, E, W, info):
    if re.search(r'(?i)<!doctype', page):
        E('contract', 'the publish file has a doctype (the artifact wraps it)')
    if local is not None and not local.lstrip().lower().startswith('<!doctype html'):
        E('contract', 'explainer.local.html lacks <!doctype html>')
    mo = re.search(r'(?is)<title>(.*?)</title>', page[:8192])
    if not mo:
        E('contract', 'no <title> in the first 8 KB')
    elif not 2 <= len(html.unescape(mo.group(1)).split()) <= 4:
        E('contract', '<title> %r: want 2-4 words' % html.unescape(mo.group(1)))
    if not re.search(r'<meta\b[^>]*name="claude:viewport-fit-sides"', page):
        E('contract', 'the claude:viewport-fit-sides meta is missing')
    mk = strip_bodies(page)
    ids = []
    for tag, al in ptags:
        at = dict(al)
        for k, _ in al:
            if k.startswith('on'):      # the engine binds its handlers in script: the markup has none
                E('safety', 'the built page has an event handler attribute %s= on <%s>' % (k, tag))
        if tag == 'script' and 'src' in at:
            u = at['src']
            if not u.startswith(CDN):
                E('contract', 'script src %s is not on the allowlist hosts' % u)
            elif not re.search(r'[@/]v?\d+\.\d+\.\d+(?:[-+.][\w.]+)?(?:/|$)', u):
                E('contract', 'script src %s has no exact version' % u)
        if tag == 'link' and 'stylesheet' in (at.get('rel') or '').split() and not (at.get('href') or '').startswith('https://fonts.googleapis.com/'):
            E('contract', 'stylesheet %s is not Google Fonts' % at.get('href'))
        if 'id' in at:
            ids.append(at['id'])
    css = '\n'.join(re.findall(r'(?is)<style\b[^>]*>(.*?)</style>', page))
    for u in re.findall(r'@import\s+(?:url\()?["\']?([^"\')\s;]+)', css):
        if not u.startswith('https://fonts.googleapis.com/'):
            E('contract', 'stylesheet @import %s is not Google Fonts' % u)
    for i in sorted(set(ids)):
        if not re.fullmatch(r'[a-z0-9-]+', i):
            E('contract', 'id %r: want [a-z0-9-]+' % i)
        elif RESERVED.match(i):
            E('contract', 'id %r is reserved by the host' % i)
    for i, k in Counter(ids).items():
        if k > 1:
            E('contract', 'duplicate id %r (%d times)' % (i, k))
    # ponytail: a CSS rule whose selector list holds a bare `pre`, not a real cascade; enough for the fixed shell
    if '<pre' in mk and not any('pre' in [s.strip() for s in sel.split(',')] and re.search(r'white-space\s*:\s*pre(?:-wrap)?\b', body)
                                for sel, body in CSS_RULE.findall(css)):
        E('contract', 'no CSS rule gives pre white-space: pre or pre-wrap')
    js = '\n;\n'.join(b for a, b in re.findall(r'(?is)<script\b([^>]*)>(.*?)</script>', page)
                      if 'src=' not in a and not re.search(r'type="(?!text/javascript|module)[^"]*"', a))
    r = node_check(js) if js.strip() else None
    if r is None:
        info.append('node --check: skipped (%s)' % ('no engine script' if not js.strip() else 'node not found'))
    elif r:
        E('contract', 'node --check failed on the engine: %s' % r)
    else:
        info.append('node --check: OK')
    raw = xd_data(page)
    if raw is None:
        E('contract', 'no <script type="application/json" id="xd-data">')
    elif '</' in raw:
        E('contract', 'xd-data contains "</": escape it')
    else:
        try:
            if (json.loads(raw).get('meta') or {}).get('build') != inputs:
                E('stale', 'map.json, plan.json, quiz.json or a fragment changed since explainer.html was built: rebuild')
        except (ValueError, AttributeError) as e:
            E('contract', 'xd-data does not parse: %s' % e)
    have = set(ids)
    for _, al in ptags:
        h = dict(al).get('href') or ''
        if h.startswith('#') and len(h) > 1 and h[1:] not in have:
            E('links', 'href="%s" has no target' % h)
    size = len(page.encode('utf-8'))
    if size > 15 * 2 ** 20:
        E('size', 'explainer.html is %.1f MB: over 15 MB' % (size / 2 ** 20))
    elif size > 4 * 2 ** 20:
        W('size', 'explainer.html is %.1f MB: over 4 MB' % (size / 2 ** 20))
    nl = len(re.findall(r'<span class="l (?:add|del|ctx|hd)">', mk))
    if nl > 3000:
        W('size', '%d diff lines embedded: over 3,000' % nl)
    info.append('page: %.0f KB, %d diff lines, %d ids' % (size / 1024, nl, len(ids)))
    if re.search(r'<!--\s*STATE\b', page):
        E('leftover', 'a drafting STATE comment')
    prose = re.sub(r'(?is)<(pre|code|script|style)\b.*?</\1>', ' ', page)    # code, xd-data and the engine out
    for rx, what in ((r'\bTODO\b', 'TODO'), (r'\{\{', '{{'), (r'(?i)\blorem\b', 'lorem')):
        if re.search(rx, prose):
            E('leftover', '%s outside code' % what)


# ---------- the page as a tree: the shape checks (handoff §6) ----------
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}


class Node:
    __slots__ = ('tag', 'at', 'kids', 'up', 'text', 'i', 'e')

    def __init__(self, tag, at=None, up=None, text=None):
        self.tag, self.at, self.kids, self.up, self.text, self.i, self.e = tag, at or {}, [], up, text, 0, 0

    def cls(self):
        return (self.at.get('class') or '').split()

    def ups(self):
        n = self.up
        while n is not None:
            yield n
            n = n.up

    def has(self, other):          # other is self or inside it
        return self.i <= other.i <= self.e


class Dom(HTMLParser):
    """The page as a browser nests well-formed markup. ponytail: only <li> and <p> close implicitly; the build's markup is
    well-formed. nested: [(outer href, inner href)] for each <a> opened inside another (a browser splits them)."""

    def __init__(self, markup):
        super().__init__(convert_charrefs=True)
        self.root = self.cur = Node('#root')
        self.nested = []
        self.feed(markup)
        self.close()
        self.all, st = [], [self.root]
        while st:
            n = st.pop()
            n.i = len(self.all)
            self.all.append(n)
            st.extend(reversed(n.kids))
        for n in reversed(self.all):
            n.e = max([n.i] + [k.e for k in n.kids])
        self.byid = {}
        for n in self.all:
            if 'id' in n.at:
                self.byid.setdefault(n.at['id'], n)

    def handle_starttag(self, tag, attrs):
        if tag in ('li', 'p') and self.cur.tag == tag:
            self.cur = self.cur.up
        if tag == 'a':
            o = next((x for x in [self.cur] + list(self.cur.ups()) if x.tag == 'a'), None)
            if o is not None:
                self.nested.append((o.at.get('href'), dict(attrs).get('href')))
        n = Node(tag, {k: v or '' for k, v in attrs}, self.cur)
        self.cur.kids.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_endtag(self, tag):
        o = next((x for x in [self.cur] + list(self.cur.ups()) if x.tag == tag), None)
        if o is not None and o.up is not None:
            self.cur = o.up

    def handle_data(self, d):
        self.cur.kids.append(Node('#text', None, self.cur, d))

    def find(self, tag=None, cls=None, within=None):
        return [n for n in (self.all[within.i:within.e + 1] if within else self.all)
                if (tag is None or n.tag == tag) and (cls is None or cls in n.cls())]


class Txt:
    """A text node and what it sits in: script/style (skip), [hidden], a closed <details> (closed), <pre>/<code>/<kbd>
    (code), a chip (.ref, .cite, .rid, [data-ref]), a heading, a <summary>, the page chrome (the bar, its menu and the
    file tree), its nearest <a>."""
    __slots__ = ('n', 't', 'skip', 'hid', 'closed', 'code', 'chip', 'head', 'summ', 'chrome', 'link')


def text_nodes(dom):
    if getattr(dom, 'tx', None) is not None:
        return dom.tx
    out, st = [], [(dom.root, (False,) * 9 + (None,))]
    while st:
        n, f = st.pop()
        if n.tag == '#text':
            if n.text.strip():
                x = Txt()
                x.n, x.t = n, n.text
                x.skip, x.hid, x.closed, x.code, x.chip, x.head, x.summ, x.chrome, _, x.link = f
                out.append(x)
            continue
        for k in reversed(n.kids):
            g = list(f)
            g[0] |= k.tag in ('script', 'style', 'template', 'noscript')
            g[1] |= 'hidden' in k.at
            g[2] |= n.tag == 'details' and 'open' not in n.at and k.tag != 'summary'
            g[3] |= k.tag in ('pre', 'code', 'kbd', 'samp')
            kc = k.cls()
            g[4] |= bool({'ref', 'cite', 'rid'} & set(kc)) or 'data-ref' in k.at
            g[5] |= bool(re.fullmatch(r'h[1-6]', k.tag))
            g[6] |= k.tag == 'summary'
            g[7] |= k.at.get('id') in ('bar', 'xd-menu', 'ftree', 'xd-help', 'xd-pop')
            g[9] = k if k.tag == 'a' else g[9]
            st.append((k, tuple(g)))
    out.sort(key=lambda x: x.n.i)
    dom.tx, dom.txi = out, [x.n.i for x in out]
    return out


def text_of(dom, n, keep=lambda x: True, sep=' '):
    """The text inside n, its text nodes joined with sep."""
    tx, out = text_nodes(dom), []
    for x in tx[bisect.bisect_left(dom.txi, n.i):]:
        if x.n.i > n.e:
            break
        if keep(x):
            out.append(x.t)
    return sep.join(out)


def nwords(t):
    return len(re.findall(r'\S*\w\S*', t))


def norm_ws(t):
    return re.sub(r'\s+', ' ', t).strip()


def where(n):
    a = next((x for x in [n] + list(n.ups()) if x.at.get('id')), None)
    return '#' + a.at['id'] if a is not None else 'the page'


CIRCLED = re.compile('[①-⑳⓪-⓿❶-➓㉑-㉟㊱-㊿]')
TEXT_LABELS = [  # (pattern, what it is, the fix) for visible text; chips, code, title and aria are out of scope
    (re.compile(r'(?i)\bchapters?\b'), '"chapter"', 'the page says "piece"'),
    (re.compile(r'\bCh\.? ?\d'), '"Ch n"', 'cite a piece by its badge and name'),
    (re.compile(r'(?i)\bpiece \d'), '"piece n"', 'a piece number shows only as its badge'),
    (re.compile(r'(?<![\w-])goal\.\w'), 'a goal id', 'name the goal in words; the id belongs in a chip'),
    (re.compile(r'\.[A-Za-z]\w{0,5}:\d+\b'), 'a file:line label', 'name what the code does; the location belongs in a chip'),
]
LOCAL = re.compile(r'(?<![\w.-])(?:\.ai|\.tasks)/|/home/|(?<![\w./-])(?:explainer|review)/')
NUMW = ('one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve')
SRC_RANK = {'Jira': 0, 'GitHub': 1, 'Shared pages': 2, 'From the author': 3, 'Glossary': 9}
SIZE = re.compile(r'(?<![\w.#-])(\d*\.?\d+)(rem|em|px|pt|pc|cm|mm|in|q|%)(?![\w-])', re.I)
FILTER_AT = 20      # the build's --filter-at default; xd-data meta.filter_at wins when the build records it


def css_of(dom):
    """[(selector, declarations)] from every <style> (comments and @media print out: print sizes are the printer's)
    plus each style="" attribute."""
    css = re.sub(r'(?s)/\*.*?\*/', '', '\n'.join(k.text for n in dom.find('style') for k in n.kids if k.tag == '#text'))
    while True:
        mo = re.search(r'@media\s+print\b[^{]*\{', css)
        if not mo:
            break
        depth, j = 1, mo.end()
        while j < len(css) and depth:
            depth += {'{': 1, '}': -1}.get(css[j], 0)
            j += 1
        css = css[:mo.start()] + css[j:]
    return CSS_RULE.findall(css) + [('<%s style="">' % n.tag, n.at['style']) for n in dom.all if n.at.get('style')]


def font_sizes(body):
    """[(declaration, value, unit)] for each font-size and each font shorthand's size (its first number with a unit)."""
    out = []
    for prop, v in re.findall(r'(?:^|;)\s*(font-size|font)\s*:\s*([^;]+)', body, re.I):
        v = re.sub(r'var\([^)]*\)|!important', ' ', v)
        mo = SIZE.search(v)
        if mo:
            out.append((prop + ':' + v.strip(), float(mo.group(1)), mo.group(2).lower()))
        elif re.search(r'(?<![\w-])(?:xx-small|x-small|small|smaller)(?![\w-])', v):
            out.append((prop + ':' + v.strip(), 0.0, 'keyword'))
    return out


def registry(plan, m, nocode):
    """The pieces as the page must show them: {chapter id: {n, deep, fam, name}}. read must = main flow (filled badge),
    skim = under Go deeper (hollow); family: must = change, a skim piece whose files are all tests = tests, else harness."""
    chs = [] if nocode else [c for c in plan.get('chapters') or [] if isinstance(c, dict)]
    owners, _ = B.assign({'chapters': chs}, m['files'])
    kind = {f['path']: f['kind'] for f in m['files']}
    reg = {}
    for i, c in enumerate(chs):
        mine = [p for p, o in owners.items() if c.get('id') in o]
        deep = c.get('read', 'must') == 'skim'
        reg[c.get('id')] = {'n': i + 1, 'deep': deep, 'name': str(c.get('short') or c.get('title') or ''),
                            'fam': 'tests' if deep and mine and all(kind[p] == 'test' for p in mine) else 'harness' if deep else 'change'}
    return reg


def pc(reg, cid):
    return 'piece %d (%s)' % (reg[cid]['n'], cid) if cid in reg else repr(cid)


def check_shape(ctx, E, W, info):
    """The v10 page: quiz placement, badges, circled numbers, label patterns, section references, file filters,
    external links, text size, the root budget, non-goals, the trace table, Sources, and the three page shapes."""
    plan, m, page = ctx['plan'], ctx['map'], ctx['page']
    nocode = B.stage_of(plan, m) == 'intent-only'
    reg = registry(plan, m, nocode)
    bynum = {r['n']: k for k, r in reg.items()}
    main_pcs = [k for k, r in reg.items() if not r['deep']]
    nfiles = 0 if nocode else len(m['files'])
    try:
        meta = (json.loads(xd_data(page) or '{}') or {}).get('meta') or {}
    except ValueError:
        meta = {}
    dom = Dom(page)
    tx = text_nodes(dom)
    by = dom.byid
    shown = [x for x in tx if not x.skip]
    paths = sorted({p for f in m['files'] for p in (f['path'], f.get('old_path')) if p}, key=len, reverse=True)

    def target(a):                  # the element an in-page link lands on
        h = (a.at.get('href') or '') if a is not None else ''
        return by.get(h[1:]) if h.startswith('#') and len(h) > 1 else None

    def lands(a, ids):              # the link lands on one of ids, or inside one ("carry" also covers carry-<tag>-<n>)
        t = target(a)
        return t is not None and any(t is by.get(k) or (by.get(k) is not None and by[k].has(t)) or
                                     (k == 'carry' and any(str(u.at.get('id', '')).startswith('carry-') for u in [t] + list(t.ups())))
                                     for k in ids)

    def visible(n):                 # not in a closed <details>, not [hidden]
        return not any('hidden' in u.at for u in [n] + list(n.ups())) and not any(
            u.tag == 'details' and 'open' not in u.at and not (c.tag == 'summary') for c, u in zip([n] + list(n.ups()), n.ups()))

    navs = [by[k] for k in ('ftree', 'files') if k in by] + dom.find('nav', 'strip') + dom.find('figure', 'code') + dom.find('ul', 'flist')
    mark = [0] * (len(dom.all) + 1)
    for z in navs:
        mark[z.i] += 1
        mark[z.e + 1] -= 1
    innav, acc = [], 0
    for v in mark[:-1]:
        acc += v
        innav.append(acc > 0)
    in_nav = lambda n: innav[n.i]       # noqa: E731  (the tree, files, strip, captions and file lists show repo paths by design)
    head = next(iter(dom.find('header', 'doc')), None)
    ends = [by[k] for k in ('pieces', 'quiz', 'deeper') + (('asked',) if nocode else ()) if k in by]
    end = min((n.i for n in ends), default=len(dom.all))
    root = [x for x in shown if head is not None and head.i <= x.n.i < end and not (x.hid or x.closed or x.chrome)
            and not any(u.tag == 'pre' for u in x.n.ups())]

    # the three shapes: full (a strip, a tree, the piece index), no map, intent-only (no code parts at all)
    if head is None:
        E('shape', 'no <header class="doc">: the page has no h1, lead or Start here')
    if nocode:
        for sel, what in (('ftree', 'the file tree'), ('files', 'the files section'), ('pieces', 'the pieces')):
            if sel in by:
                E('shape', 'intent-only (no code): %s (#%s) must not render' % (what, sel))
        for tag, cl, what in (('nav', 'strip', 'the diff strip'), ('ol', 'pindex', 'the piece index')):
            if dom.find(tag, cl):
                E('shape', 'intent-only (no code): %s must not render' % what)
        if 'asked' in ctx['frags']:
            a = by.get('asked')
            if a is None or not visible(a) or ('quiz' in by and a.i > by['quiz'].i) or any(u.at.get('id') == 'deeper' for u in a.ups()):
                E('shape', 'intent-only: What was asked (#asked) sits open in the main flow, before Check yourself')
    elif nfiles:
        tiles = [n for s in dom.find('nav', 'strip') for n in s.kids if n.tag == 'a']
        rows = dom.find('li', 'fi')
        if 'ftree' not in by:
            E('shape', 'no file tree (#ftree) on a page with %d changed files' % nfiles)
        elif len({n.at.get('data-f') for n in rows}) != nfiles:
            E('shape', 'the file tree lists %d files, the change has %d' % (len({n.at.get('data-f') for n in rows}), nfiles))
        if len(tiles) != nfiles or any(not (n.at.get('data-f') and n.at.get('data-fam')) for n in tiles):
            E('shape', 'the diff strip has %d tiles for %d files (each a nav.strip > a with data-f and data-fam)' % (len(tiles), nfiles))
        elif not any(re.search(r'(^|,)\s*nav\.strip\s*>\s*a\s*(,|$)', s) and any(
                float(v) >= 1 for v in re.findall(r'min-width\s*:\s*(\d*\.?\d+)rem', b)) for s, b in css_of(dom)):
            E('shape', 'no CSS gives the strip tiles (nav.strip>a) a min-width of at least 1rem')
        if reg and not dom.find('ol', 'pindex'):
            E('shape', 'no piece index (ol.pindex) under the strip')
    if not nocode and reg and 'map' not in by:
        W('shape', 'no map (plan.json map): the first screen shows no picture of the change; draw it rule- or flow-shaped')
    elif 'map' not in by and nocode:
        W('shape', 'no map (plan.json map): draw the asked workflow as a flow-shaped map')

    # quiz placement: open in the main flow, after the last main-flow piece, before Go deeper; a first-screen link to it
    qs = (ctx['quiz'] or {}).get('questions') if isinstance(ctx['quiz'], dict) else None
    q = by.get('quiz')
    if qs and q is None:
        E('quiz-place', 'no Check yourself section (#quiz)')
    elif q is not None:
        if any(u.tag == 'details' for u in q.ups()):
            E('quiz-place', 'Check yourself (#quiz) is inside a <details>: it sits open in the main flow, never folded')
        if 'deeper' in by and (q.i > by['deeper'].i or by['deeper'].has(q)):
            E('quiz-place', 'Check yourself (#quiz) comes after Go deeper: it goes right after the pieces')
        late = [k for k in main_pcs if k in by and by[k].i > q.i]
        if late:
            E('quiz-place', 'Check yourself (#quiz) comes before %s: it goes after the last main-flow piece' % pc(reg, late[-1]))
        if not any(a.at.get('href') == '#quiz' and head is not None and head.i <= a.i < end and not any(
                u.at.get('id') in ('bar', 'xd-menu', 'ftree') for u in a.ups()) for a in dom.find('a')):
            E('quiz-place', 'the first screen has no link to Check yourself besides the bar pill: Start here ends with "Answer N questions"')
    for f in dom.find('fieldset', 'q'):     # every question, final or checkpoint, sits open
        if any(u.tag == 'details' and 'open' not in u.at for u in f.ups()):
            E('quiz-place', 'question %s in %s is inside a closed <details>: a question sits open (a checkpoint goes at its piece\'s '
                            'end, after More on this)' % (f.at.get('id'), where(f.up)))

    # badges: span.pb only, numbered as a piece, its family and depth; each one a link that lands in its piece
    for n in dom.all:
        c = n.cls()
        if 'pb' in c and n.tag != 'span':
            E('badge', '<%s class="pb"> in %s: the badge class is for piece badges (span.pb) only' % (n.tag, where(n)))
            continue
        if n.tag == 'a' and 'pref' in c:
            t = target(n)
            if t is None or (n.at.get('href') or '')[1:] not in reg:
                E('badge', 'a.pref in %s links to %s, not to a piece' % (where(n), n.at.get('href')))
            elif not any('pb' in k.cls() for k in dom.all[n.i:n.e + 1]):
                E('badge', 'a.pref to %s in %s has no badge: cite a piece as badge + name' % (pc(reg, n.at['href'][1:]), where(n)))
        if n.tag == 'a' and 'pbl' in c and 'pref' not in c:
            E('badge', 'a.pbl in %s: a bare badge link is a.pref.pbl' % where(n))
        if 'pb' not in c:
            continue
        t = norm_ws(text_of(dom, n))
        cid = bynum.get(int(t)) if t.isdigit() else None
        if cid is None:
            E('badge', 'a badge in %s reads %r: no piece has that number' % (where(n), t))
            continue
        r = reg[cid]
        if ('deep' in c) != r['deep'] or n.at.get('data-fam') != r['fam']:
            E('badge', 'badge %d in %s: %s, data-fam %r; want %s, data-fam %r' % (
                r['n'], where(n), 'hollow' if 'deep' in c else 'filled', n.at.get('data-fam'),
                'hollow (under Go deeper)' if r['deep'] else 'filled (main flow)', r['fam']))
        a = next((u for u in n.ups() if u.tag == 'a'), None)
        if a is not None:
            if not lands(a, [cid]):
                E('badge', 'badge %d in %s sits in a link to %s, not to its piece: make the badge its own link' % (r['n'], where(n), a.at.get('href')))
        elif not (any(re.fullmatch(r'h[1-6]', u.tag) for u in n.ups()) and cid in by and by[cid].has(n)) and not any(
                u.tag == 'summary' and u.up is not None and u.up.tag == 'details' and cid in by and u.up.has(by[cid]) for u in n.ups()):
            E('badge', 'badge %d in %s is not a link: make it <a class="pref pbl" href="#%s">' % (r['n'], where(n), cid))
    for outer, inner in dom.nested:
        E('nest', 'a link inside a link (%s inside %s): every badge and link is its own <a>' % (inner, outer))

    # circled numbers: only as badges (span.pb digits); titles and aria may spell ①
    for x in shown:
        mo = CIRCLED.search(x.t)
        if mo:
            E('circled', '%s: visible text %r uses a circled number: a piece number shows only as its badge' % (where(x.n), norm_ws(x.t)[:60]))
    rules = css_of(dom)
    for s, b in rules:
        if re.search(r'content\s*:[^;]*' + CIRCLED.pattern, b):
            E('circled', 'CSS %s puts a circled number in content: a piece number shows only as its badge' % s.strip()[:60])

    # visible text: no label a reader would have to decode (per text node, never joined)
    for x in shown:
        if x.hid or x.code or x.chip or in_nav(x.n):
            continue
        for rx, what, fix in TEXT_LABELS:
            mo = rx.search(x.t)
            if mo:
                E('label', '%s: visible text names %s (%r): %s' % (where(x.n), what, mo.group(0), fix))

    # section references: the words of the heading, as a link that lands there; Go-deeper rows named by their heading
    want_h = {'map': 'The map', 'carry': 'To carry into the review', 'quiz': 'Check yourself', 'deeper': 'Go deeper',
              'pieces': 'The piece' if len(main_pcs) == 1 else 'The %s pieces' % (NUMW[len(main_pcs) - 1] if len(main_pcs) <= 12 else len(main_pcs))}
    for k, want in want_h.items():
        n = by.get(k)
        h = n if n is not None and re.fullmatch(r'h[1-6]', n.tag) else next(
            (u for u in dom.all[n.i:n.e + 1] if re.fullmatch(r'h[1-6]', u.tag)), None) if n is not None else None
        if h is not None and norm_ws(text_of(dom, h)).rstrip('#').strip() != want:
            E('section-ref', '#%s is headed %r: want %r' % (k, norm_ws(text_of(dom, h)), want))
    phrases = [(r'\bthe map\b', ['map']), (r'\bwhat to carry\b', ['map', 'carry']), (r'\bTo carry into the review\b', ['carry']),
               (r'\bCheck yourself\b', ['quiz']), (r'\bWhat was asked\b', ['asked']), (r'\bAll (\d+) files\b', ['files']),
               (r'\bRead pieces?\b', list(reg))]
    for x in shown:      # not in code, chips, a question, a heading or a summary (checked against its heading below)
        if x.head or x.summ or x.hid or x.chrome or x.code or x.chip or any(u.tag == 'fieldset' for u in x.n.ups()):
            continue
        for rx, ids in phrases:
            for mo in re.finditer(rx, x.t, re.I if rx.startswith(r'\bthe map') or 'what to' in rx else 0):
                if any(k in by and by[k].has(x.n) for k in ids):
                    continue                    # a section may name itself
                if x.link is None:
                    E('section-ref', '%s: %r names a section but is not a link: link it to #%s (in a fragment, <a href="#%s">%s</a>)'
                      % (where(x.n), mo.group(0), ids[0] if ids else 'its piece', ids[0] if ids else 'ch-1', mo.group(0)))
                elif not lands(x.link, ids):
                    E('section-ref', '%s: %r links to %s, not to the section it names' % (where(x.n), mo.group(0), x.link.at.get('href')))
                elif mo.groups() and int(mo.group(1)) != nfiles:
                    E('section-ref', '%s: %r, but the change has %d files' % (where(x.n), mo.group(0), nfiles))
    if 'deeper' in by:
        for d in dom.find('details', 'row', by['deeper']):
            s = next((k for k in d.kids if k.tag == 'summary'), None)
            h = next((u for u in dom.all[d.i:d.e + 1] if re.fullmatch(r'h[1-6]', u.tag) and not (s is not None and s.has(u))), None)
            st, ht = (norm_ws(text_of(dom, z)) if z is not None else '' for z in (s, h))
            if st != ht.rstrip('#').strip():
                E('section-ref', 'Go deeper row %r opens a section headed %r: the row is named by its heading\'s exact words' % (st, ht))

    # file-filter UI only above the threshold
    thr = meta.get('filter_at') if isinstance(meta.get('filter_at'), int) else FILTER_AT
    fil = [n for n in dom.all if n.at.get('id') in ('ftree-q', 'ftree-hv') or {'tfil', 'tmenu', 'ftree-ext', 'ftools'} & set(n.cls())
           or (n.tag == 'input' and n.at.get('type') == 'search')]
    if fil and nfiles <= thr:
        E('filter', '%d changed files (threshold %d): no file-filter UI at or below it, found %s' % (
            nfiles, thr, ', '.join(sorted({'#' + n.at['id'] if n.at.get('id') else n.tag + '.' + '.'.join(n.cls()) for n in fil}))[:120]))
    if nfiles > thr and 'ftree-q' not in by:
        E('filter', '%d changed files, above %d: the file tree needs its filter box (#ftree-q)' % (nfiles, thr))

    # external links: a new tab, rel noopener
    bad = Counter(n.at.get('href') for n in dom.find('a') if re.match(r'(?i)(https?:)?//', n.at.get('href') or '')
                  and not (n.at.get('target') == '_blank' and 'noopener' in (n.at.get('rel') or '').split()))
    for h, k in bad.items():
        E('extlink', '<a href="%s">%s: an external link opens a new tab with target="_blank" rel="noopener"' % (h[:80], ' (%d times)' % k if k > 1 else ''))

    # text size: the browser's root size, rem only, nothing under 1rem but the strip digits
    for s, b in rules:
        sels = [z.strip() for z in s.split(',')]
        sz = font_sizes(b)
        if sz and any(re.fullmatch(r'(?:html|:root)(?:\[[^\]]*\]|:[\w-]+(?:\([^)]*\))?)*', z) for z in sels):
            E('text-size', 'CSS %s sets the root font size: follow the browser\'s own size' % s.strip()[:60])
            continue
        for decl, v, unit in sz:
            low = (unit in ('rem', 'em') and v < 1) or (unit == '%' and v < 100) or unit == 'keyword'
            if unit in ('px', 'pt', 'pc', 'cm', 'mm', 'in', 'q'):
                E('text-size', 'CSS %s{%s}: an absolute size ignores the browser\'s text size; use rem' % (s.strip()[:60], decl[:40]))
            elif low and not any('nav.strip' in z for z in sels):
                E('text-size', 'CSS %s{%s}: below 1rem; only the strip digits may be smaller' % (s.strip()[:60], decl[:40]))

    # the root budget: the authored words above the pieces (h1, lead, the map, the carry list), closed <details>, <pre>,
    # [hidden] and the file tree excluded; Start here, the strip, the piece index and the Next lines are generated, so they
    # are counted apart. Constant, whatever the change's size: depth (pieces, Go deeper) scales instead
    gen = ([by['start']] if 'start' in by else []) + dom.find('p', 'strip-h') + dom.find('nav', 'strip') + dom.find('ol', 'pindex') + dom.find('p', 'next')
    rw = sum(nwords(x.t) for x in root if not any(g.has(x.n) for g in gen))
    gw = sum(nwords(x.t) for x in root) - rw
    info.append('root: %d authored words above the pieces (budget %d) + %d generated (Start here, strip, piece index, Next lines)' % (rw, ROOT_WORDS, gw))
    if rw > ROOT_WORDS:
        E('root', 'the root has %d authored words above the pieces: at most %d. Shorten the lead, the map\'s words and the carry '
                  'lines, or move detail one level deeper (More on this, a Go deeper row)' % (rw, ROOT_WORDS))
    path = [('root', rw + gw)] + [(pc(reg, k), sum(nwords(x.t) for x in shown if by[k].has(x.n) and not (x.hid or x.closed)
                              and not any(u.tag == 'pre' for u in x.n.ups()))) for k in main_pcs if k in by]
    if q is not None:
        path.append(('Check yourself', sum(nwords(x.t) for x in shown if q.has(x.n) and not x.hid)))
    info.append('reading path (information): %s = %d words, about %d min' % (
        ' · '.join('%s %d' % p for p in path), sum(w for _, w in path), sum(B.minutes(w) for _, w in path)))

    # non-goals: on the first screen, as "not here" carry lines, never in a closed toggle
    ngs = [norm(vis(str((x.get('text') if isinstance(x, dict) else x) or ''))) for x in plan.get('not_in_change') or []]
    if ngs:
        lines = [n for n in dom.find('li') if n.at.get('id', '').startswith('carry-') and visible(n)
                 and ('deeper' not in by or n.i < by['deeper'].i)]
        seen = norm(' '.join(text_of(dom, n, sep='') for n in lines))
        for g in ngs:
            if g and g not in seen:
                E('non-goal', 'non-goal %r is not on the first screen: plan.json not_in_change renders as "not here" lines in To carry into the review' % g[:60])
    elif any(r.get('state') == 'non-goal' for r in plan.get('trace') or [] if isinstance(r, dict)):
        W('non-goal', 'a trace row is a non-goal, but plan.json not_in_change is empty: show non-goals on the first screen')

    # the trace table: at 4+ rows or with any state but tested; else a one-line status in What was asked
    trace = [r for r in plan.get('trace') or [] if isinstance(r, dict)]
    big = len(trace) >= 4 or any(r.get('state') != 'tested' for r in trace)
    table = dom.find('table', 'tt')
    if trace and not big and table:
        E('trace-table', '%d trace rows, all tested: no trace table; a one-line status (p.trace-status) in What was asked' % len(trace))
    elif trace and big and not table:
        E('trace-table', '%d trace rows%s: the page needs the trace table (table.tt)' % (
            len(trace), '' if len(trace) >= 4 else ' with a state other than tested'))
    elif trace and not big and not dom.find(None, 'trace-status'):
        E('trace-table', '%d trace rows, all tested: What was asked needs its one-line status (p.trace-status)' % len(trace))

    # Sources: no local path, no bare URL, each listed source cited and linked back, no code/goal/non-goal entries
    def scrub(s):           # a changed file's own path is the repo's, not a local note
        for p in paths:
            s = s.replace(p, ' ')
        return s
    for n in dom.all:
        if in_nav(n):
            continue
        for k, v in n.at.items():
            if (k == 'title' or k.startswith('aria-')) and LOCAL.search(scrub(v)):
                E('sources', '%s: a local path in %s=%r: name the source in words, or cite its online twin' % (where(n), k, v[:60]))
    for x in shown:
        if not x.code and LOCAL.search(scrub(x.t)) and not in_nav(x.n):
            E('sources', '%s: a local path in visible text %r: name the source in words, or cite its online twin' % (where(x.n), norm_ws(x.t)[:60]))
        if not x.code and x.link is None and re.search(r'https?://', x.t):
            E('sources', '%s: a bare URL in visible text %r: make it a link' % (where(x.n), norm_ws(x.t)[:60]))
    rs = by.get('refs')
    if rs is not None:
        unhidden = lambda n: not any('hidden' in u.at for u in [n] + list(n.ups()))      # noqa: E731  (Sources sits in a closed row)
        listed = [n for n in dom.find('li', within=rs) if n.at.get('id', '').startswith('src-') and unhidden(n)]
        chips = {}
        for n in dom.find('a'):
            if 'ref' in n.cls() and (n.at.get('href') or '').startswith('#src-'):
                chips.setdefault(n.at['href'][1:], []).append(n)
        origins = plan.get('origins') if isinstance(plan.get('origins'), dict) else {}
        for li in listed:
            sid, mine = li.at['id'], chips.get(li.at['id'], [])
            back = {(a.at.get('href') or '')[1:] for a in dom.find('a', 'cite', li)}
            if not mine:
                E('sources', '%s is listed, but no chip cites it: list only sources the page cites' % sid)
            for c in mine:
                if not c.at.get('id'):
                    E('sources', 'a chip citing %s in %s has no id, so "Cited in" cannot link back to it' % (sid, where(c)))
                elif c.at['id'] not in back:
                    E('sources', '%s: "Cited in" has no link to its chip in %s (#%s)' % (sid, where(c.up), c.at['id']))
            for b in back - {c.at.get('id') for c in mine}:
                E('sources', '%s: "Cited in" links #%s, which is not a chip citing it' % (sid, b))
            u = (origins.get(sid[4:]) or {}).get('url')
            if u and not any(a.at.get('href') == u for a in dom.find('a', within=li)):
                E('sources', '%s has a URL but no link to it: a source a reader can open is a real link' % sid)
        for n in dom.all[rs.i:rs.e + 1]:
            if not unhidden(n) or n.tag == '#text':
                continue
            dr = n.at.get('data-ref') or ''
            if dr.startswith(('file:', 'goal.', 'ng.')) or ('rk' in n.cls() and norm_ws(text_of(dom, n)) in ('Code', 'Goal', 'Non-goal')):
                E('sources', 'Sources lists a %s entry (%s): code, goals and non-goals are not sources' % (
                    'code' if dr.startswith('file:') else 'goal or non-goal', dr or norm_ws(text_of(dom, n))))
                break
        if any(n.tag == 'ol' and 'refs' in n.cls() and 'hidden' not in n.at for n in dom.all[rs.i:rs.e + 1]):
            E('sources', 'the per-reference store (ol.refs) is visible: it is the chip previews\' data, <ol hidden>')
        hs = [norm_ws(text_of(dom, n)) for n in dom.find('h4', within=rs) if unhidden(n)]
        rank = [SRC_RANK.get(h, 4) for h in hs]
        if rank != sorted(rank):
            E('sources', 'Sources groups are %s: want Jira, GitHub, Shared pages, From the author, other groups, Glossary' % ' · '.join(hs))


ROOT_WORDS = 480    # the root budget: the page the design settled on (a rule-shaped map of 6 boxes, 4 carry lines) has 402


# ---------- emitters ----------
def blind(plan, quiz):
    order = B.quiz_order(plan, quiz)
    out = ['%d questions. For each, pick one letter.' % len(order), '']
    for q in order:
        out.append('%s. %s' % (q['id'], q['stem']))
        out += ['   %s) %s' % ('ABCD'[k], o) for k, o in enumerate(q['options'])]
        out.append('')
    return '\n'.join(out)


class Text(HTMLParser):
    BLOCK = {'p', 'li', 'tr', 'dt', 'dd', 'figcaption', 'pre', 'summary', 'blockquote', 'div', 'section', 'aside',
             'header', 'table', 'ul', 'ol', 'dl', 'figure', 'details', 'br', 'label', 'nav'}
    SKIP = {'script', 'style', 'fieldset', 'button'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        elif self.skip:
            pass
        elif re.fullmatch(r'h[1-4]', tag):
            self.out.append('\n\n' + '#' * int(tag[1]) + ' ')
        elif tag in self.BLOCK:
            self.out.append('\n')
        elif tag in ('td', 'th'):
            self.out.append(' | ')

    def handle_endtag(self, tag):
        if tag in self.SKIP:
            self.skip = max(0, self.skip - 1)
        elif not self.skip and (tag in self.BLOCK or re.fullmatch(r'h[1-4]', tag)):
            self.out.append('\n')

    def handle_data(self, d):
        if not self.skip:
            self.out.append(d)


def teach(page, plan, quiz):
    t = Text()                                    # the document only: not the bar, menu or help chrome
    t.feed(''.join(re.findall(r'(?is)<header class="doc".*?</header>|<main\b.*?</main>', strip_bodies(page))) or page)
    body = re.sub(r'\n[ \t]*(?=\n)', '\n', ''.join(t.out))
    return re.sub(r'\n{3,}', '\n\n', body).strip() + '\n\n=== QUIZ (answer from the page above; cite the heading you used) ===\n\n' + blind(plan, quiz)


def stale(ctx):
    m, repo = ctx['map'], ctx['repo']
    if m.get('intent_only'):              # no code yet: the page binds to its sources, not to a moving base
        mv = moved(ctx)
        if mv is None:
            return 2, 'stale: explainer.html is missing or has no meta.inputs: build first'
        return ((3, 'stale: ' + '; '.join('%s@%s → %s' % (k, o or '(none)', '@' + n if n else 'gone') for k, o, n in mv)) if mv
                else (0, 'fresh: intent-only, every why-source as built'))
    head, base = B.rev(repo, m['head_ref']), B.rev(repo, m['base_ref'])
    if not head or not base:
        return 2, 'stale: cannot resolve %s' % (m['base_ref'] if head else m['head_ref'])
    mb = B.gits(repo, 'merge-base', base, head, ok=(0, 1)).strip()
    why = []
    if head != m['head']:
        n = B.gits(repo, 'rev-list', '--count', '%s..%s' % (m['head'], head), ok=(0, 128)).strip() or '?'
        why.append('%s moved %s -> %s (%s commits since)' % (m.get('head_ref'), m['head'][:7], head[:7], n))
    if mb != m['merge_base']:
        why.append('merge base moved %s -> %s' % (m['merge_base'][:7], mb[:7] or '?'))
    return (3, 'stale: ' + '; '.join(why)) if why else (0, 'fresh: built at %s' % m['head'][:7])


def report(d, err, warn, info):
    print('check-explainer: %s' % d)
    for i in info:
        print('  ' + i)
    for k, m in warn:
        print('  WARN  [%s] %s' % (k, m))
    for k, m in err:
        print('  ERROR [%s] %s' % (k, m))
    print('  result: %s' % ('FAIL (%d errors, %d warnings)' % (len(err), len(warn)) if err else 'OK (%d warnings)' % len(warn)))


# ---------- self-test: a synthetic shop change (orders reserve stock) ----------
MINI_SHELL = '''<title><!--XD:TITLE--></title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>:root{--bg:#fff;--fg:#111}body{background:var(--bg);color:var(--fg)}pre{white-space:pre;overflow-x:auto}nav.strip>a{min-width:1rem}</style>
<!--XD:HEADER--><div class="page"><!--XD:TOC--><main id="main"><!--XD:MAIN--></main></div>
<script type="application/json" id="xd-data">/*XD:DATA*/</script>
<script>(function(){'use strict';var d=JSON.parse(document.getElementById('xd-data').textContent);document.title+=' '+d.meta.head7;})();</script>
'''
PLACE = '''<?php

namespace Shop\\Orders;

final class PlaceOrder
{
    public function __construct(
        private OrderRepository $orders,
    ) {
    }

    public function handle(PlaceOrderCommand $command): Order
    {
        $order = Order::fromCart($command->cart);
        $this->orders->save($order);

        return $order;
    }

    public function describe(): string
    {
        return 'Places an order from a cart.';
    }

    public function name(): string
    {
        return 'place-order';
    }
}
'''
RESERVE = '''<?php

namespace Shop\\Inventory;

use Shop\\Orders\\Order;

final class ReserveStock
{
    public function __construct(private ReservationRepository $reservations, private StockLevel $stock)
    {
    }

    public function forOrder(Order $order): void
    {
        foreach ($order->lines() as $line) {
            $available = $this->stock->available($line->productId());
            $quantity = min($line->quantity(), $available);
            $this->reservations->hold($line->id(), $line->productId(), $quantity);
            if ($quantity < $line->quantity()) {
                $line->markBackordered($line->quantity() - $quantity);
            }
        }
    }
}
'''
MIGRATION = '''<?php

return new class extends Migration {
    public function up(Schema $schema): void
    {
        $schema->create('stock_reservation', function ($t) {
            $t->id();
            $t->foreignId('order_line_id')->unique();
            $t->foreignId('product_id');
            $t->integer('quantity');
        });
    }
};
'''
TEST = '''<?php

test('a short line is reserved in part and backordered', function () {
    $order = anOrder()->withLine(product: 'P', quantity: 5)->place();
    expect(reservedFor($order))->toBe(3);
});
'''
TOTALS = '<?php\r\n\r\nfinal class OrderTotals\r\n{\r\n    public function sum(array $lines): int\r\n    {\r\n        return array_sum($lines);\r\n    }\r\n}\r\n'
PRD = """# PRD: ABC-123 — Stock reservations

> Status: Approved

## 3. Goals & Non-Goals
**Non-Goals**
- No customer email when a hold is released.

## 6. Acceptance Criteria
- **R1.a** Given a placed order, then each line holds its stock at once.
- **R1.b** Given a line short of stock, then the rest of the line is backordered.
- **R2.a** Given an unpaid order past the window, then its hold is released.
"""
SPEC = """# Spec from tests: ABC-123

## tests/Inventory/ReserveStockTest.php

### A short line is reserved in part and backordered
- **Given** product P with 3 available
- **When** an order for 5 units is placed
- **Then** 3 units are held for it
"""
QUIZ = [  # synthetic items (R2 section 4), keys c a d b d
    ('predict', 'ch-1', 'Product P has 3 units available and an order line asks for 5. How many units does `ReserveStock::forOrder` hold?',
     ['0', '2', '3', '5'], 2, ['src/Inventory/ReserveStock.php:17']),
    ('why', 'ch-2', 'Why does this change reserve stock when the order is placed rather than when the payment is captured?',
     ['Payment confirmations arrive minutes late, and two checkouts in that gap could sell the same last unit.',
      'The payment gateway refuses to capture an order whose lines have no stock reservation attached yet.',
      'Reserving at capture time would need a second transaction that the order handler is not allowed to open.',
      'The warehouse picks unpaid orders early, so their units must already be held when the pick list is built.'], 0,
     ['decisions.md D1']),
    ('where', 'ch-1', 'The business wants a short line rejected instead of backordered. Where does that change belong?',
     ['In the stock_reservation migration, as a check on the quantity column of every row',
      'In the PlaceOrder handler, as a validation step that runs before the order is saved',
      'In the inventory config, as a flag that the order endpoint reads on every request',
      'In ReserveStock, inside the loop that decides how much of each line it can hold'], 3,
     ['src/Inventory/ReserveStock.php:19']),
    ('test', 'proven', 'Which behaviour of ABC-123 has code but no test, so the proof section lists it under Not tested?',
     ['Holding three units of a five-unit line when only three are available.',
      'Holding every unit of a line when the product has enough stock on hand.',
      'Releasing the hold of an unpaid order once its payment window closes.',
      'Backordering the units of a short line that the stock could not cover.'], 1,
     ['spec.short-line', 'prd.md R1.a']),
    ('edge', 'ch-2', 'A customer orders 5 units of a product with 3 available. What does the change do?',
     ['Rejects the whole order with a validation error before reserving anything.',
      'Reserves all 5 units and lets available stock fall to -2 until restock.',
      'Places the order unreserved and retries the reservation on every restock.',
      'Reserves 3 units and marks the other 2 units on that line as backordered.'], 3,
     ['src/Inventory/ReserveStock.php:20']),
]


def _w(root, rel, data):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'wb') as fh:
        fh.write(data if isinstance(data, bytes) else data.encode('utf-8'))


def _fixture(td):
    """A repo whose feature branch adds stock reservations; main moves on after the branch point."""
    repo = os.path.join(td, 'shop repo')
    os.makedirs(repo)
    g = lambda *a: B.git(repo, *a)              # noqa: E731
    g('init', '-q', '-b', 'main')
    for rel, data in (('src/Orders/PlaceOrder.php', PLACE), ('src/Orders/OrderTotals.php', TOTALS),
                      ('src/Inventory/Stock Level.php', '<?php\n\nfinal class StockLevel\n{\n}\n'),
                      ('src/Legacy/OldReserver.php', '<?php\n\nfinal class OldReserver\n{\n}\n'),
                      ('src/Orders/OrderProxy.php', '<?php\n// @generated by proxy-gen. DO NOT EDIT.\nclass OrderProxy {}\n'),
                      ('composer.lock', '{"content-hash": "aaa"}\n'), ('public/logo.png', b'\x89PNG\r\n\x1a\n\x00\x01'),
                      ('config/inventory.yml', 'inventory:\r\n  warehouse: main\r\n'),
                      ('config/release.yml', 'release:\n  window: 30\n  retries: 2\n')):
        _w(repo, rel, data)
    g('add', '-A')
    g('commit', '-qm', 'base')
    g('checkout', '-qb', 'feature')
    _w(repo, 'src/Orders/PlaceOrder.php', PLACE.replace(
        '        private OrderRepository $orders,\n', '        private OrderRepository $orders,\n        private ReserveStock $reserve,\n').replace(
        '        $this->orders->save($order);\n', '        $this->orders->save($order);\n        $this->reserve->forOrder($order);\n'))
    _w(repo, 'src/Orders/OrderTotals.php', TOTALS.replace('    ', '\t'))
    _w(repo, 'src/Inventory/ReserveStock.php', RESERVE)
    _w(repo, 'database/migrations/2026_11_10_000001_create_stock_reservations.php', MIGRATION)
    _w(repo, 'tests/Inventory/ReserveStockTest.php', TEST)
    _w(repo, 'src/Orders/OrderProxy.php', '<?php\n// @generated by proxy-gen. DO NOT EDIT.\nclass OrderProxy { public $x; }\n')
    _w(repo, 'composer.lock', '{"content-hash": "bbb"}\n')
    _w(repo, 'public/logo.png', b'\x89PNG\r\n\x1a\n\x00\x02')
    _w(repo, 'config/inventory.yml', 'inventory:\r\n  warehouse: main\r\n  release_window_minutes: 30\r\n')
    _w(repo, 'config/release.yml', 'release:\n  window: 30\nretries: 2\n')       # whitespace-only, yet a new key
    _w(repo, '.ai/ABC-123/prd.md', PRD)
    g('mv', 'src/Inventory/Stock Level.php', 'src/Inventory/StockLevel.php')
    g('rm', '-q', 'src/Legacy/OldReserver.php')
    g('add', '-A')
    g('commit', '-qm', 'ABC-123 reserve stock when an order is placed')
    g('checkout', '-q', 'main')
    _w(repo, 'CHANGELOG.md', '# Changes\n')
    g('add', '-A')
    g('commit', '-qm', 'changelog')
    g('checkout', '-q', 'feature')
    tk = os.path.join(repo, '.ai', 'ABC-123')
    _w(tk, 'spec-from-tests.md', SPEC)
    _w(tk, 'decisions.md', '# Decisions\n\n## D1: Reserve at placement\n> We reserve stock when the order is "placed", not when\n'
                           '> the payment is _captured_, because [payment confirmations](https://example.com) arrive minutes late.\n')
    for rel in ('backend-summary.md', 'pr.md', 'v2/pr2.md', 'explainer/sources/pr-7.md'):
        _w(tk, rel, '# %s\n\nReserve stock when an order is placed.\n' % rel)
    xd = os.path.join(tk, 'explainer')
    head7 = B.rev(repo, 'HEAD')[:7]
    plan = {'title': 'ABC-123 Stock Reservations', 'heading': 'How placing an order now reserves stock', 'ticket': 'ABC-123',
            'mode': 'author', 'stage': 'full', 'branch': 'feature', 'contract': None,
            'glance': 'Placing an order now holds stock for each line. A line short of stock holds what there is and backorders the rest.',
            'problem': 'Two checkouts could sell the same last unit.', 'problem_ref': {'label': 'decision', 'ref': 'D1'},
            'behaviour': {'cols': ['An order for 5 units of P, with 3 on hand', 'Before', 'After'],
                          'rows': [['The order is placed', 'Nothing held', '3 held, 2 backordered']]},
            'toy': 'Order #1001: one line of 5 units of product P, 3 available; it holds 3 and backorders 2.',
            'sources': ['.ai/ABC-123/prd.md', '.ai/ABC-123/decisions.md', '.ai/ABC-123/spec-from-tests.md'],
            'trace': [{'id': 'R1.a', 'text': 'A placed order holds its stock', 'built': ['ch-2', 'file:src/Orders/PlaceOrder.php:17'],
                       'proven': [], 'state': 'untested', 'note': ''},
                      {'id': 'R1.b', 'text': 'A short line is held in part, the rest backordered', 'built': ['ch-1'],
                       'proven': ['spec.short-line', 'file:tests/Inventory/ReserveStockTest.php:3'], 'state': 'tested'},
                      {'id': 'R2.a', 'text': 'Unpaid holds are released', 'built': [], 'proven': [], 'state': 'deferred',
                       'note': 'Deferred to ABC-124: the release job.'}],
            'drift': [{'at': 'src/Inventory/ReserveStock.php:19', 'note': 'The plan rejected short lines; the code backorders them.',
                       'ref': 'D1', 'needs_decision': False}],
            'ops': [{'what': 'migration', 'files': ['database/migrations/2026_11_10_000001_create_stock_reservations.php'],
                     'note': 'no `down()`: roll back by dropping `stock_reservation`'}],
            'hotspots': [{'at': 'src/Inventory/ReserveStock.php:15-21', 'why': 'the short-stock branch has one test'},
                         {'at': 'src/Orders/OrderTotals.php:5', 'why': 're-indented only'},
                         {'at': 'docs/none.md:1', 'why': 'not in the diff'},
                         {'at': 'src/Orders/PlaceOrder.php:17', 'why': 'An order saved by the nightly import never holds stock.', 'carry': 'bypasses',
                          'ref': 'D1'}],
            'not_in_change': [{'text': 'No customer email when a hold is released', 'ref': 'ng.email', 'label': 'non-goal'}],
            'map': {'purpose': 'Placing an order now asks one new rule how much stock each line holds.',
                    'entries_h': 'Who asks · changed to ask', 'rule_h': 'The rule they ask', 'outcomes_h': 'What the line does',
                    'arrow': 'ask', 'so': 'so',
                    'entries': [{'label': 'Placing an order', 'sub': 'after the order is saved', 'kind': 'changed', 'target': 'ch-2'},
                                {'label': 'The nightly import', 'sub': 'saves orders on its own', 'kind': 'not asked', 'target': 'carry-bypasses-1'}],
                    'rule': {'title': 'A line holds the stock there is', 'conditions': [{'text': 'one row per order line'},
                                                                                       {'text': 'never more than is available', 'exception': True}],
                             'sub': 'one new service', 'target': 'ch-1'},
                    'outcomes': [{'label': 'holds its stock', 'sub': 'a short line in part', 'target': 'ch-3', 'goal': 'R1.b'}]},
            'deeper': [{'summary': 'What was asked', 'holds': ['asked', 'problem', 'background', 'intuition', 'trace', 'drift']},
                       {'piece': 'ch-3', 'holds': ['ch-3', 'proven', 'look']},
                       {'summary': 'Deploy and merge notes', 'holds': ['ops']},
                       {'summary': 'Generated files', 'holds': ['ch-mech']}],
            'chapters': [
                {'id': 'ch-1', 'title': 'Reservations as data', 'short': 'the reservations', 'read': 'must', 'risk': 'med', 'evidence': 'covered',
                 'why_here': 'Everything else writes these rows.', 'checks': ['how many units a short line holds'],
                 'gist': 'One row per order line holds stock; a short line holds what there is and backorders the rest.',
                 'files': ['database/migrations/*', 'src/Inventory/ReserveStock.php']},
                {'id': 'ch-2', 'title': 'Placing an order reserves stock', 'short': 'placing an order', 'read': 'must', 'risk': 'high',
                 'evidence': 'inferred', 'files': ['src/Orders/PlaceOrder.php', 'config/inventory.yml', 'config/release.yml', 'src/Legacy/*']},
                {'id': 'ch-3', 'title': 'The tests and what they prove', 'short': 'the tests', 'read': 'skim', 'risk': 'low',
                 'evidence': 'tested', 'proof': 'Proven by the short-line test', 'files': ['tests/*']}],
            'mechanical': [{'title': 'Generated, moved and removed', 'intent': 'No behaviour change.',
                            'check': 'the lockfile hash, the rename and the re-indent change no logic',
                            'files': ['composer.lock', 'public/*', 'src/Inventory/StockLevel.php', '.ai/*',
                                      'src/Orders/OrderTotals.php', 'src/Orders/OrderProxy.php']}],
            'origins': {'prd': {'group': 'Jira', 'label': 'The ticket, with its acceptance criteria', 'url': 'https://tracker.example.com/browse/ABC-123'},
                        'pr': {'group': 'GitHub', 'label': 'Pull request #7 (its description)', 'url': 'https://forge.example.com/shop/pull/7'},
                        'decisions': {'group': 'From the author', 'label': "The author's decision log"},
                        'spec': {'group': 'From the author', 'label': "The author's test spec"}},
            'refs': {'D1': {'title': 'Reserve at placement', 'src': '.ai/ABC-123/decisions.md', 'origin': 'decisions',
                            'text': 'We reserve stock when the order is “placed”, not when the payment is captured'},
                     'R1.a': {'title': 'Holds at placement', 'src': '.ai/ABC-123/prd.md', 'origin': 'prd',
                              'text': 'Given a placed order, then each line holds its stock at once.'},
                     'R1.b': {'title': 'Short lines', 'src': '.ai/ABC-123/prd.md', 'origin': 'prd',
                              'text': 'Given a line short of stock, then the rest of the line is backordered.'},
                     'R2.a': {'title': 'Release', 'src': '.ai/ABC-123/prd.md', 'origin': 'prd',
                              'text': 'Given an unpaid order past the window, then its hold is released.'},
                     'ng.email': {'title': 'No email', 'src': '.ai/ABC-123/prd.md', 'origin': 'prd', 'text': 'No customer email when a hold is released.'},
                     'spec.short-line': {'title': 'Short line', 'src': '.ai/ABC-123/spec-from-tests.md', 'origin': 'spec',
                                         'text': 'A short line is reserved in part and backordered'},
                     'commit:' + head7: {'title': 'Commit ' + head7, 'src': '.ai/ABC-123/pr.md', 'origin': 'pr', 'text': 'Reserve stock when an order is placed.'}},
            'glossary': [{'term': 'available stock', 'def': 'on hand minus open reservations'}],
            'open_questions': ['(ch-1) Should a backordered line release its partial hold after a window?']}
    frags = {
        'asked': '<h3>The problem and why</h3><p>Two checkouts could sell the same last unit <span class="ref" data-ref="D1"></span>.</p>\n'
                 '<h3>Not in this ticket</h3><ul><li>No customer email on release <span class="ref" data-ref="ng.email">non-goal</span>.</li></ul>\n'
                 '<h3>What must hold</h3><p>Each line holds its stock <span class="ref" data-ref="R1.a"></span>; a short line holds what there '
                 'is <span class="ref" data-ref="R1.b"></span>.</p>\n<aside class="callout" data-kind="nongoal"><p>Releasing unpaid holds moved '
                 'to ABC-124 <span class="ref" data-ref="R2.a"></span>.</p></aside>\n',
        'proven': '<aside class="callout" data-kind="ran"><p>Ran at head: <code>composer test</code>, 1 passed.</p></aside>\n'
                  '<h3>A short line</h3><ul><li><span class="ref" data-ref="spec.short-line"></span>: 3 of 5 units held.</li></ul>\n'
                  '<aside class="callout" data-kind="risk"><p>Not tested: a full line <span class="ref" data-ref="R1.a"></span>.</p></aside>\n',
        'background': '<p>Before this change, placing an order did not touch stock.</p>\n'
                      '<pre data-code="src/Orders/PlaceOrder.php@base:12-18" data-note="before"></pre>\n',
        'intuition': '<figure><figcaption>Order #1001 (toy data)</figcaption><div class="fig toy"><table><thead><tr><th>product</th>'
                     '<th>available</th></tr></thead><tbody><tr><td>P</td><td class="chg">0</td></tr></tbody></table></div></figure>\n',
        'ch-1': '<p>A reservation row holds stock for one order line <span class="ref" data-ref="D1"></span>.</p>\n'
                '<pre data-hunk="database/migrations/2026_11_10_000001_create_stock_reservations.php:1-13"></pre>\n<!--more-->\n'
                '<pre data-code="src/Inventory/ReserveStock.php:1-5" data-note="the class"></pre>\n'
                '<pre data-code="src/Inventory/ReserveStock.php:13-23" data-note="the loop"></pre>\n'
                '<aside class="callout" data-kind="risk"><p>The short branch is <span class="ref" data-ref="file:src/Inventory/ReserveStock.php:19">'
                '</span>.</p></aside>\n<p>Prose may name the marker: <code>&lt;pre data-hunk="PATH:1-2"&gt;&lt;/pre&gt;</code>.</p>\n',
        'ch-2': '<p>The handler calls the new service after saving <span class="ref" data-ref="commit:%s">%s</span>.</p>\n' % (head7, head7) +
                '<pre data-hunk="src/Orders/PlaceOrder.php:5-20"></pre>\n<!--more-->\n'
                '<pre data-hunk="config/inventory.yml:1-3"></pre>\n<p>It writes the rows of <a href="#ch-1">the reservations</a>.</p>\n',
        'ch-3': '<p>One test holds a short line in part <span class="ref" data-ref="spec.short-line"></span>.</p>\n'
                '<pre data-hunk="tests/Inventory/ReserveStockTest.php:1-6"></pre>\n'}
    for k, v in frags.items():
        _w(xd, 'fragments/%s.html' % k, v)
    _w(xd, 'plan.json', json.dumps(plan, indent=1))
    qs = [{'id': 'q%d' % (i + 1), 'chapter': c, 'final': True, 'kind': k, 'stem': s, 'options': o, 'answer': a,
           'feedback': ['Option %s for question %d: the misconception it names, explained in two sentences.' % ('abcd'[j], i + 1)
                        for j in range(4)], 'evidence': ev}
          for i, (k, c, s, o, a, ev) in enumerate(QUIZ)]
    _w(xd, 'quiz.json', json.dumps({'built_from': head7, 'questions': qs}, indent=1))
    _w(xd, 'review/tests-%s.txt' % head7, '$ composer test -- --filter=ReserveStock\nTests: 1 passed\nat %s on 2026-11-10\n' % head7)
    return repo, xd


# ---------- self-test B: an intent-only contract ticket (no code, a storyboard, rulings) ----------
PRD_B = """# PRD: XYZ-9 — Lab kit returns

> Status: Approved
> Versions:
> - v1 2026-11-01 frozen: first draft
> - v2 2026-11-03 approved: changed R1.a; retired R1.b; new R9.z; from FB1

## 3. Goals & Non-Goals
**Non-Goals**
- No refund for a kit lost in the post.

## 6. Acceptance Criteria
- **R1.a** Given a returned kit, when the hub scans it, then its test moves to Received.
- **R1.b** Retired v2: merged into R1.a.
- **R2.a** Given a damaged kit, when the hub scans it, then the test is put on hold.
<!-- R3.a draft: a kit scanned twice is ignored -->

## 7. Open Questions
- **Q1** Who pays the return postage? Open.
"""
TICKET_B = {
    'prd.md': PRD_B,
    'review/prd-v1-2026-11-01.md': PRD_B.split('> - v2')[0] + PRD_B.split('FB1\n', 1)[1],
    'workflows.md': '# Workflows: XYZ-9\n\n## s1. A kit comes back\n| Step | Actor | Before → after |\n|---|---|---|\n'
                    '| s1.1 | Hub | kit Sent → Received |\n| s1.2 | Hub | test Waiting → Received |\n',
    'feedback.md': '# Feedback: XYZ-9\n\n### FB1 · CHOICE · storyboard v1 · 2026-11-02\n'
                   '- **What:** should a damaged kit fail the test at once?\n- **Status:** ruled v2 (developer, option B) → R2.a\n\n'
                   '### FB2 · SILENCE · panel P1-2 · 2026-11-02\n- **What:** who pays the return postage?\n- **Status:** open\n',
    'prototype/artifact.md': '# XYZ-9 storyboard artifact\n\n> Built from: contract v1 (2026-11-01)\n\n'
                             '- **URL:** https://claude.ai/artifact/abc123XYZ (private; the developer shares it)\n\n'
                             '| Version | Date | Label | Built from | Trigger | What changed |\n|---|---|---|---|---|---|\n'
                             '| v1 | 2026-11-01 | Storyboard v1 | contract v1 (2026-11-01) | first build | 1 scenario |\n'
                             '| v1.1 | 2026-11-02 | Storyboard v1.1 | contract v1 (2026-11-02) | labels | wording |\n'}
QUIZ_B = [  # keys c a b
    ('requirement', 'The PO asks whether XYZ-9 refunds a customer whose kit is lost in the post. What does the PRD say?',
     ['Covered: the hub scan of a returned kit triggers the refund.', 'Covered: a damaged kit is refunded while it is on hold.',
      'Out of scope: the PRD lists it among the non-goals.', 'Still open: the PO was asked, and no answer is recorded.'], 2,
     ['prd.md §3 Non-Goals']),
    ('workflow', 'Kit K-7 for test T-3 is Sent. The hub scans it at the door. What is the state right after the scan?',
     ['kit Received; test T-3 still Waiting for its own step', 'kit Received; test T-3 moved to Received with the kit',
      'kit Sent; test T-3 moved to Received by the scan', 'kit Sent; test T-3 put on hold until the hub checks'], 0,
     ['workflows.md s1.1']),
    ('why', 'Why does a damaged kit put its test on hold instead of failing the test at once?',
     ['The lab cannot open a damaged kit until the courier has signed it off.',
      'The PO ruled that the hub checks a damaged kit before the test fails.',
      'A failed test cannot be reopened, so the hub must never fail one early.',
      'The storyboard has no screen for failing a test from the hub scan.'], 1, ['feedback.md FB1']),
]


def _fixture_b(repo, mb):
    """Plan, fragments and quiz of XYZ-9 from its map.json mb (the sources are already on disk)."""
    xd = os.path.join(repo, '.ai', 'XYZ-9', 'explainer')
    src = lambda n: '.ai/XYZ-9/' + n             # noqa: E731
    plan = {'title': 'XYZ-9 Kit Returns', 'heading': 'What XYZ-9 asks: a scanned kit moves its test on', 'ticket': 'XYZ-9',
            'mode': 'author', 'stage': 'intent-only', 'contract': mb['contract'],
            'glance': 'No code yet. A hub scan moves a returned kit and its test on; a damaged kit puts its test on hold.',
            'map': {'purpose': 'What the ticket asks, as one walk: the hub scans a kit, and the test moves on.',
                    'entries_h': 'What the hub does', 'outcomes_h': 'What the test does', 'arrow': 'so',
                    'entries': [{'label': 'The hub scans a returned kit', 'sub': 'at the door', 'kind': 'changed', 'target': 'asked'}],
                    'outcomes': [{'label': 'its test moves to Received', 'sub': 'or on hold when the kit is damaged', 'target': 'asked'}]},
            'not_in_change': [{'text': 'No refund for a kit lost in the post', 'ref': 'ng.lost', 'label': 'non-goal'}],
            'deeper': [{'summary': 'Background', 'holds': ['background', 'intuition']}],
            'origins': {'prd': {'group': 'Jira', 'label': 'The ticket, with its PRD', 'url': 'https://tracker.example.com/browse/XYZ-9'},
                        'flows': {'group': 'From the author', 'label': "The author's workflow notes"},
                        'rulings': {'group': 'From the author', 'label': "The developer's rulings on the storyboard"}},
            'sources': [src(n) for n in ('prd.md', 'workflows.md', 'feedback.md', 'prototype/artifact.md', 'review/prd-v1-2026-11-01.md')],
            'trace': [{'id': 'R1.a', 'text': 'A scan moves the test to Received', 'state': 'not-built', 'note': 'no code yet'},
                      {'id': 'R1.b', 'text': 'Retired', 'state': 'non-goal', 'note': 'retired v2: merged into R1.a'},
                      {'id': 'R2.a', 'text': 'A damaged kit holds its test', 'state': 'deferred', 'note': 'no code yet; waits on Q1'},
                      {'id': 's1.1', 'text': 'The hub scans the kit', 'state': 'not-built', 'note': 'no code yet'}],
            'refs': {'R1.a': {'title': 'Scan', 'src': src('prd.md'), 'origin': 'prd',
                              'text': 'Given a returned kit, when the hub scans it, then its test moves to Received.'},
                     'R1.b': {'title': 'Retired', 'src': src('prd.md'), 'origin': 'prd', 'text': 'Retired v2: merged into R1.a.'},
                     'R2.a': {'title': 'Damaged', 'src': src('prd.md'), 'origin': 'prd',
                              'text': 'Given a damaged kit, when the hub scans it, then the test is put on hold.'},
                     's1.1': {'title': 'Hub scan', 'src': src('workflows.md'), 'origin': 'flows', 'text': 'Hub | kit Sent → Received'},
                     'FB1': {'title': 'Damaged kits', 'src': src('feedback.md'), 'origin': 'rulings', 'text': 'ruled v2 (developer, option B) → R2.a'},
                     'FB2': {'title': 'Postage', 'src': src('feedback.md'), 'origin': 'rulings', 'text': '**Status:** open'},
                     'ng.lost': {'title': 'Lost kits', 'src': src('prd.md'), 'origin': 'prd', 'text': 'No refund for a kit lost in the post.'},
                     'Q1': {'title': 'Postage', 'src': src('review/prd-v1-2026-11-01.md'), 'origin': 'prd', 'text': 'Who pays the return postage?'}},
            'open_questions': ['(asked) Who pays the return postage? Q1 is open (feedback.md FB2).'],
            'drift': [{'at': '.ai/XYZ-9/prototype/artifact.md', 'note': 'The storyboard was drawn from contract v1; the contract is now v2.',
                       'needs_decision': False},
                      {'at': 'src/Orders/PlaceOrder.php:14', 'note': 'Today an order is saved with no hold.', 'needs_decision': False}]}
    frags = {'asked': '<h3>Not in this ticket</h3><ul><li>No refund for a lost kit <span class="ref" data-ref="ng.lost">non-goal</span>.</li></ul>\n'
                      '<h3>What must hold</h3><p>A scan moves the test on <span class="ref" data-ref="R1.a"></span>.</p>\n'
                      '<ol class="stepper" data-title="Kit K-7 comes back (toy data)"><li><h3>The hub scans the kit</h3>'
                      '<p><span class="ref" data-ref="s1.1">s1.1</span></p><table class="toy"><tr><th>kit</th><th>state</th></tr>'
                      '<tr><td>K-7</td><td class="chg">Received</td></tr></table><p>The kit is in.</p></li></ol>\n'
                      '<p>ruled <span class="ref" data-ref="FB1">FB1</span>: a damaged kit holds its test <span class="ref" data-ref="R2.a"></span>.</p>\n'
                      '<p>Open: who pays the postage <span class="ref" data-ref="Q1"></span>.</p>\n',
             'background': '<p>Today the hub logs a returned kit by hand; an order is saved <span class="ref" '
                           'data-ref="file:src/Orders/PlaceOrder.php:15"></span>.</p>\n'
                           '<pre data-code="src/Orders/PlaceOrder.php@base:12-18" data-note="today"></pre>\n',
             'intuition': '<p>One kit, one scan, one test moved on.</p>\n'}
    for k, v in frags.items():
        _w(xd, 'fragments/%s.html' % k, v)
    _w(xd, 'plan.json', json.dumps(plan, indent=1, ensure_ascii=False))
    qs = [{'id': 'q%d' % (i + 1), 'chapter': 'asked', 'final': True, 'kind': k, 'stem': st, 'options': o, 'answer': a,
           'feedback': ['Option %s for question %d: the misconception it names, explained in two sentences.' % ('abcd'[j], i + 1)
                        for j in range(4)], 'evidence': ev}
          for i, (k, st, o, a, ev) in enumerate(QUIZ_B)]
    _w(xd, 'quiz.json', json.dumps({'built_from': mb['head'][:7], 'questions': qs}, indent=1, ensure_ascii=False))
    return xd


def _fixture_c(td):
    """A toy repo whose branch adds 80 files: 10 modules of 6 files, 12 tests, 8 config files (12 pieces)."""
    repo = os.path.join(td, 'big repo')
    os.makedirs(repo)
    g = lambda *a: B.git(repo, *a)              # noqa: E731
    g('init', '-q', '-b', 'main')
    _w(repo, 'README.md', '# Modules\n')
    g('add', '-A')
    g('commit', '-qm', 'base')
    g('checkout', '-qb', 'feature')
    for k in range(1, 11):
        for j in range(1, 7):
            _w(repo, 'src/Mod%02d/Part%d.php' % (k, j), '<?php\n\nfinal class Mod%02dPart%d\n{\n    public function run(): int\n    {\n'
                                                        '        return %d;\n    }\n}\n' % (k, j, k * 10 + j))
    for k in range(1, 13):
        _w(repo, 'tests/Mod%02dTest.php' % k, "<?php\n\ntest('module %d runs', function () {\n    expect(run(%d))->toBe(%d);\n});\n" % (k, k, k))
    for k in range(1, 9):
        _w(repo, 'config/mod%d.yml' % k, 'mod%d:\n  enabled: true\n  weight: %d\n' % (k, k))
    g('add', '-A')
    g('commit', '-qm', 'XYZ-80 split the modules')
    return repo, os.path.join(repo, '.ai', 'XYZ-80', 'explainer')


def _inputs_c(xd, head7):
    chs = [{'id': 'ch-%d' % k, 'title': 'Module %d returns its own number' % k, 'short': 'module %d' % k, 'read': 'must', 'risk': 'low',
            'evidence': 'covered', 'files': ['src/Mod%02d/*' % k]} for k in range(1, 11)]
    chs += [{'id': 'ch-11', 'title': 'The tests and what they prove', 'short': 'the tests', 'read': 'skim', 'risk': 'low',
             'evidence': 'covered', 'files': ['tests/*']},
            {'id': 'ch-12', 'title': 'The module switches', 'short': 'the switches', 'read': 'skim', 'risk': 'low',
             'evidence': 'covered', 'files': ['config/*']}]
    plan = {'title': 'XYZ-80 Module Split', 'heading': 'Ten modules, each returning its own number', 'ticket': 'XYZ-80',
            'mode': 'reviewer', 'stage': 'full', 'branch': 'feature', 'contract': None,
            'glance': 'One shared class became ten modules; each returns its own number and has a switch and a test.',
            'map': {'purpose': 'Two modules run, and a caller sees their number; the tests check each.',      # flow-shaped: no rule
                    'entries_h': 'What runs', 'outcomes_h': 'What a caller sees', 'arrow': 'returns',
                    'entries': [{'label': 'Module 2', 'sub': 'on every run', 'kind': 'changed', 'target': 'ch-2'},
                                {'label': 'Module 3', 'sub': 'on every run', 'kind': 'changed', 'target': 'ch-3'}],
                    'outcomes': [{'label': 'the number', 'sub': 'checked by one test per module', 'target': 'ch-11'}]},
            'not_in_change': ['How the modules load stays as it was'],
            'ops': [{'what': 'config', 'files': ['config/mod1.yml'], 'note': 'the switches ship on; no deploy step'}],
            'deeper': [{'piece': 'ch-11', 'holds': ['ch-11', 'proven']}, {'piece': 'ch-12', 'holds': ['ch-12', 'ops']},
                       {'summary': 'Background', 'holds': ['background', 'intuition']}],
            'chapters': chs, 'refs': {}, 'origins': {}}
    frags = {'ch-%d' % k: '<p>Module %d now returns its own number <span class="ref" data-ref="file:src/Mod%02d/Part1.php:7"></span>.</p>\n'
                          '<pre data-hunk="src/Mod%02d/Part1.php:1-9"></pre>\n<!--more-->\n<p>Its other five parts follow the same pattern.</p>\n'
                          % (k, k, k) for k in range(1, 11)}
    frags.update({'ch-11': '<p>One test per module.</p>\n<pre data-hunk="tests/Mod01Test.php:1-5"></pre>\n',
                  'ch-12': '<p>One switch per module.</p>\n<pre data-hunk="config/mod1.yml:1-3"></pre>\n',
                  'background': '<p>Before this change, the modules shared one class.</p>\n',
                  'intuition': '<p>Ten modules, one number each.</p>\n', 'proven': '<p>The tests ran at head: 12 passed.</p>\n'})
    for k, v in frags.items():
        _w(xd, 'fragments/%s.html' % k, v)
    _w(xd, 'plan.json', json.dumps(plan, indent=1))
    ev = [['src/Mod01/Part1.php:7'], ['decisions.md D1'], ['src/Mod01/Part1.php:7'], ['spec.short-line'], ['src/Mod02/Part1.php:7']]
    qs = [{'id': 'q%d' % (i + 1), 'chapter': c, 'final': True, 'kind': k, 'stem': s, 'options': o, 'answer': a,
           'feedback': ['Option %s for question %d: the misconception it names, explained in two sentences.' % ('abcd'[j], i + 1)
                        for j in range(4)], 'evidence': ev[i]}
          for i, (k, c, s, o, a, _) in enumerate(QUIZ)]
    _w(xd, 'quiz.json', json.dumps({'built_from': head7, 'questions': qs}, indent=1))


def _run(*args):
    r = subprocess.run([sys.executable, '-I'] + list(args), capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def _move_key(q, pos):
    a = q['answer']
    for k in ('options', 'feedback'):
        q[k][a], q[k][pos] = q[k][pos], q[k][a]
    q['answer'] = pos


def _rx(c, pat, repl):
    new = re.sub(pat, repl, c['page'], count=1, flags=re.S)
    assert new != c['page'], 'plant missed: %s' % pat
    c['page'] = new


def _move(c, pat, before):
    """Cut the first match of pat out of the page and put it before the first match of before."""
    mo = re.search(pat, c['page'], re.S)
    assert mo, 'plant missed: %s' % pat
    pg = c['page'][:mo.start()] + c['page'][mo.end():]
    at = re.search(before, pg).start()
    c['page'] = pg[:at] + mo.group(0) + pg[at:]


def _into(c, qid, after):
    """Cut question qid's fieldset and put it right after the first </summary> that follows the regex after."""
    mo = re.search(r'<fieldset class="q" id="%s">.*?</fieldset>' % qid, c['page'], re.S)
    pg = c['page'][:mo.start()] + c['page'][mo.end():]
    at = pg.index('</summary>', re.search(after, pg).start()) + len('</summary>')
    c['page'] = pg[:at] + mo.group(0) + pg[at:]


def _in_header(c, a, b):
    pg = c['page']
    i = pg.index('<header class="doc">')
    j = pg.index('</header>', i)
    assert a in pg[i:j], 'plant missed: %s' % a
    c['page'] = pg[:i] + pg[i:j].replace(a, b) + pg[j:]


QUIZ_SEC = r'<section class="sec" id="quiz">.*?</section>'


def _plants(ctx):
    """(key, needle, mutate(ctx)) per planted error; each must be caught."""
    Q = lambda c: c['quiz']['questions']        # noqa: E731
    F = lambda c, k, t: c['frags'].__setitem__(k, c['frags'][k] + t)   # noqa: E731
    P = lambda c, a, b: c.__setitem__('page', c['page'].replace(a, b, 1))   # noqa: E731
    I = lambda c, t: P(c, '</main>', t + '</main>')                     # noqa: E731, E741
    ch = lambda c, i: c['plan']['chapters'][i]   # noqa: E731
    T = lambda c: c['plan']['trace']            # noqa: E731
    return [
        ('plan', 'read', lambda c: ch(c, 0).__setitem__('read', 'maybe')),
        ('plan', 'missing', lambda c: c['frags'].pop('ch-2')),
        ('coverage', 'in no piece', lambda c: ch(c, 1)['files'].remove('config/inventory.yml')),
        ('coverage', 'owners', lambda c: ch(c, 0)['files'].append('composer.lock')),
        ('coverage', 'never down a tier', lambda c: (ch(c, 1)['files'].remove('src/Orders/PlaceOrder.php'),
                                                     c['plan']['mechanical'][0]['files'].append('src/Orders/PlaceOrder.php'))),
        ('marker', 'empty <pre', lambda c: F(c, 'ch-1', '<pre data-code="src/Inventory/ReserveStock.php:1-2">typed</pre>')),
        ('marker', 'unresolved', lambda c: P(c, '</main>', '<pre data-hunk="x.php:1-2"></pre></main>')),
        ('ref', 'invented', lambda c: c['plan']['refs']['D1'].__setitem__('text', 'We reserve stock when payment is captured')),
        ('ref', 'under 12', lambda c: c['plan']['refs']['D1'].__setitem__('text', 'We reserve')),
        ('plan', 'evidence tested needs', lambda c: (ch(c, 0).__setitem__('evidence', 'tested'), c.__setitem__('dir', c['dir'] + '-gone'))),
        ('plan', 'breaks prd.md', lambda c: (c['plan']['refs'].__setitem__('R1', {'src': '.ai/ABC-123/prd.md', 'text': 'A placed order holds its stock.'}),
                                             c['plan']['drift'][0].__setitem__('ref', 'R1'))),
        ('safety', '<script', lambda c: F(c, 'ch-1', '<script>alert(1)</script>')),
        ('safety', 'event handler', lambda c: F(c, 'ch-1', '<p onclick="go()">x</p>')),
        ('safety', 'event handler', lambda c: F(c, 'ch-1', "<p onmouseover='go()'>x</p>")),
        ('safety', 'style=', lambda c: F(c, 'ch-1', '<p style="color:red">x</p>')),
        ('safety', 'external href', lambda c: F(c, 'ch-1', '<a href="https://example.com/">x</a>')),
        ('safety', 'javascript:', lambda c: F(c, 'ch-1', '<a href="#x" title="javascript:go()">x</a>')),
        ('safety', '<iframe>', lambda c: F(c, 'ch-1', '<iframe></iframe>')),
        ('safety', 'onerror', lambda c: F(c, 'ch-1', '<img/src="x"/onerror="alert(1)">')),          # P6 F1: '/' splits attributes
        ('safety', 'ontoggle', lambda c: F(c, 'ch-1', '<details/open/ontoggle="alert(1)"><summary>x</summary></details>')),
        ('safety', 'unclosed', lambda c: F(c, 'ch-2', '<img src=x onerror=alert(1)')),               # the build appends a tag to it
        ('safety', 'javascript: or data:', lambda c: F(c, 'ch-1', '<a href="&#106;avascript:go()">x</a>')),
        ('safety', 'built page', lambda c: P(c, '</main>', '<p onclick="go()">x</p></main>')),
        ('quiz', 'schema', lambda c: Q(c)[0]['options'].pop()),
        ('quiz', 'schema', lambda c: Q(c)[1].__setitem__('chapter', 'ch-9')),
        ('quiz', 'built_from', lambda c: c['quiz'].__setitem__('built_from', '0000000')),
        ('quiz', 'want 5', lambda c: [Q(c).pop() for _ in range(3)]),
        ('quiz', 'want 5', lambda c: (Q(c).pop(), c['map']['totals']['by_tier']['read'].__setitem__('add', 151))),
        ('quiz', 'drift that needs a decision', lambda c: (c['plan']['drift'][0].__setitem__('needs_decision', True),
                                                           Q(c)[0].__setitem__('kind', 'criterion'), Q(c)[0]['evidence'].append('D1'))),
        ('quiz', 'positions', lambda c: (_move_key(Q(c)[2], 0), _move_key(Q(c)[3], 0))),
        ('quiz', 'length', lambda c: Q(c)[1]['options'].__setitem__(0, Q(c)[1]['options'][0] + ' This is what the decisions log records for the change.')),
        ('quiz', 'all-none', lambda c: Q(c)[2]['options'].__setitem__(0, 'None of the above, since the change adds no rule here.')),
        ('quiz', 'article', lambda c: Q(c)[3].__setitem__('stem', 'The release job reads its window from a')),
        ('quiz', 'duplicate', lambda c: Q(c)[4]['options'].__setitem__(0, Q(c)[4]['options'][1])),
        ('quiz', 'ref:', lambda c: Q(c)[1]['options'].__setitem__(0, Q(c)[1]['options'][0][:-1] + ' (D1).')),
        ('quiz', 'order', lambda c: Q(c)[0].__setitem__('options', ['0', '3', '2', '5'])),
        ('quiz', 'alone finds the key at q2, q3, q4, q5', lambda c: [q['options'].__setitem__(q['answer'], q['options'][q['answer']] + ' and the storefront totals stay right')
                                                     for q in Q(c)[1:]]),
        ('quiz', 'bold', lambda c: Q(c)[0].__setitem__('stem', 'Which value does NOT appear?')),
        ('quiz', 'pre-rendered', lambda c: P(c, '</main>', '<p>%s</p></main>' % Q(c)[0]['feedback'][2])),
        ('quiz', 'the key lives only', lambda c: P(c, 'class="opt" data-i="2"', 'class="opt correct" data-i="2"')),
        ('stale', 'rebuild', lambda c: Q(c)[0].__setitem__('stem', Q(c)[0]['stem'] + ' ')),
        ('stale', 'rebuild', lambda c: ch(c, 0).__setitem__('why_here', 'Edited after the build.')),
        ('contract', 'doctype', lambda c: c.__setitem__('page', '<!doctype html>' + c['page'])),
        ('contract', 'lacks <!doctype', lambda c: c.__setitem__('local', c['page'])),
        ('contract', '2-4 words', lambda c: P(c, '<title>ABC-123 Stock Reservations</title>', '<title>A title with far too many words</title>')),
        ('contract', 'viewport-fit-sides', lambda c: P(c, 'name="claude:viewport-fit-sides"', 'name="x"')),
        ('contract', 'allowlist', lambda c: P(c, '</main>', '</main><script src="https://example.com/x.js"></script>')),
        ('contract', 'exact version', lambda c: P(c, '</main>', '</main><script src="https://cdn.jsdelivr.net/npm/lib/x.js"></script>')),
        ('contract', 'Google Fonts', lambda c: P(c, '</main>', '</main><link rel="stylesheet" href="https://example.com/x.css">')),
        ('contract', 'reserved', lambda c: P(c, '</main>', '<div id="settings"></div></main>')),
        ('contract', 'duplicate id', lambda c: P(c, '</main>', '<div id="overview"></div></main>')),
        ('contract', '[a-z0-9-]+', lambda c: P(c, '</main>', '<div id="Bad_Id"></div></main>')),
        ('contract', 'white-space', lambda c: c.__setitem__('page', re.sub(r'white-space\s*:\s*pre(-wrap)?', 'color:red', c['page']))),
        ('contract', 'node --check', lambda c: c.__setitem__('page', c['page'] + '<script>if(</script>')),
        ('contract', 'escape it', lambda c: P(c, 'id="xd-data">{', 'id="xd-data">{"x":"</b>",')),
        ('links', 'no target', lambda c: P(c, '</main>', '<a href="#nowhere">x</a></main>')),
        ('size', '15 MB', lambda c: c.__setitem__('page', c['page'] + '<!--%s-->' % ('x' * (15 * 2 ** 20 + 1)))),
        ('leftover', 'TODO', lambda c: P(c, '</main>', '<p>TODO explain</p></main>')),
        ('leftover', 'STATE', lambda c: c.__setitem__('page', '<!-- STATE 10:00: drafting -->' + c['page'])),
        ('trace', 'R1.a (prd.md) has no trace row', lambda c: T(c).pop(0)),
        ('trace', 'trace rows: exactly once', lambda c: T(c).append(dict(T(c)[2]))),
        ('trace', "state 'done' is not", lambda c: T(c)[0].__setitem__('state', 'done')),
        ('trace', 'tested needs a non-empty proven', lambda c: T(c)[0].__setitem__('state', 'tested')),
        ('trace', 'tested needs review/tests-', lambda c: c.__setitem__('dir', c['dir'] + '-gone')),
        ('trace', 'built needs a non-empty built and proven', lambda c: T(c)[0].__setitem__('state', 'built')),
        ('trace', 'untested needs a non-empty built', lambda c: T(c)[0].__setitem__('built', [])),
        ('trace', 'deferred needs a note', lambda c: T(c)[2].__setitem__('note', ' ')),
        ('trace', 'drift needs a plan.json drift entry', lambda c: T(c)[0].__setitem__('state', 'drift')),
        ('plan', 'asked.html is missing: prd.md', lambda c: c['frags'].pop('asked')),
        ('plan', 'proven.html is missing: a test file changed', lambda c: c['frags'].pop('proven')),
        ('plan', 'not found', lambda c: c['plan']['sources'].append('.ai/ABC-123/nope.md')),
        ('plan', 'private material', lambda c: c['plan']['sources'].append('.ai/ABC-123/review/panel/p1.md')),
        ('plan', 'private material', lambda c: c['plan']['sources'].append('.ai/ABC-123/meeting-2026-11-01.md')),
        ('ref', 'private material', lambda c: c['plan']['refs']['D1'].__setitem__('src', '.ai/ABC-123/input/call.md')),
        ('plan', 'stage must be intent-only', lambda c: c['map'].__setitem__('intent_only', True)),
        ('plan', 'chapters must be empty', lambda c: c['plan'].__setitem__('stage', 'intent-only')),
        ('plan', "stage 'draft' is not", lambda c: c['plan'].__setitem__('stage', 'draft')),
        ('plan', 'contract: prd.md has no > Versions:', lambda c: c['plan'].__setitem__('contract', {'version': 'v1', 'status': 'Approved'})),
        ('quiz', 'Asked layer exists, but no final', lambda c: Q(c)[1].__setitem__('kind', 'predict')),
        ('quiz', 'Proven layer exists, but no final', lambda c: Q(c)[3].__setitem__('kind', 'ac-map')),
        ('quiz', 'only a piece takes checkpoints', lambda c: Q(c)[3].__setitem__('final', False)),
        ('quiz', 'a piece under Go deeper takes no checkpoint', lambda c: Q(c)[0].update(final=False, chapter='ch-3')),
        ('plan', 'asked.html is missing: pr-7.md is a source', lambda c: (                        # V3-c: an ask without a PRD
            c['plan'].__setitem__('sources', ['.ai/ABC-123/explainer/sources/pr-7.md']), c['map'].__setitem__('sources_found', []),
            c['frags'].pop('asked'))),
        ('quiz', 'Asked layer exists, but no final', lambda c: (
            c['plan'].__setitem__('sources', ['.ai/ABC-123/explainer/sources/jira-ABC-123.md']), c['map'].__setitem__('sources_found', []),
            c['frags'].pop('asked'), Q(c)[1].__setitem__('kind', 'predict'))),
        ('plan', 'background.html is missing', lambda c: c['frags'].pop('background')),
        ('plan', 'intuition.html is missing', lambda c: c['frags'].pop('intuition')),
        ('plan', 'toy: want one text block', lambda c: c['plan'].__setitem__('toy', ['TOY-1'])),
        ('plan', 'checks: want a list', lambda c: ch(c, 0).__setitem__('checks', 'one fact')),
        ('quiz', 'q1 stem names commit a1b2c3d: describe the change', lambda c: Q(c)[0].__setitem__('stem', 'After commit a1b2c3d, ' + Q(c)[0]['stem'])),
        ('quiz', 'q2 option a names location ReserveStock.php:17', lambda c: Q(c)[1]['options'].__setitem__(0, 'The guard at ReserveStock.php:17 is why.')),
        ('quiz', 'q3 stem names location line 19', lambda c: Q(c)[2].__setitem__('stem', 'The loop at line 19 must change. ' + Q(c)[2]['stem'])),
        ('quiz', 'q4 stem names section §7', lambda c: Q(c)[3].__setitem__('stem', 'As §7 lists, ' + Q(c)[3]['stem'])),
        ('quiz', 'q5 option a names exit code Exit 1', lambda c: Q(c)[4]['options'].__setitem__(0, 'Exit 1, listing the rows it skipped.')),
        ('quiz', 'q5 stem names ref id R1.b: say what', lambda c: Q(c)[4].__setitem__('stem', 'Under R1.b, ' + Q(c)[4]['stem'])),
        ('reader', 'glance names commit a1b2c3d in prose: say what', lambda c: c['plan'].__setitem__('glance', 'Since a1b2c3d, short lines backorder.')),
        ('reader', 'ch-2.html names commit a1b2c3d', lambda c: F(c, 'ch-2', '<p>Commit <code>a1b2c3d</code> wires it in.</p>')),
        ('reader', 'hotspots[0].why names ReserveStock.php:19 in prose: move the location into a chip',
         lambda c: c['plan']['hotspots'][0].__setitem__('why', 'the branch at `ReserveStock.php:19` has one test')),
        ('reader', 'map.entries[0].sub names ReserveStock.php:19', lambda c: c['plan']['map']['entries'][0].__setitem__('sub', 'at ReserveStock.php:19')),
        ('reader', "glance tells the page's own history ('Rebuilt')", lambda c: c['plan'].__setitem__('glance', 'Rebuilt at the same head.')),
        ('reader', "('adds What was asked')", lambda c: c['plan'].__setitem__('glance', 'This page adds What was asked.')),
        # the shape checks (handoff §6)
        ('quiz-place', 'inside a <details>', lambda c: _rx(c, '(%s)' % QUIZ_SEC, r'<details><summary>Quiz</summary>\1</details>')),
        ('quiz-place', 'comes after Go deeper', lambda c: _move(c, QUIZ_SEC, '</main>')),
        ('quiz-place', 'after the last main-flow piece', lambda c: _move(c, QUIZ_SEC, r'<h2[^>]*\bid="pieces"')),
        ('quiz-place', 'no link to Check yourself besides the bar pill', lambda c: _in_header(c, 'href="#quiz"', 'href="#deeper"')),
        ('quiz-place', 'question q1 in #ch-1 is inside a closed <details>', lambda c: _into(c, 'q1', r'<details class="leaf">')),
        ('quiz-place', 'question q4 in #deeper is inside a closed <details>', lambda c: _into(
            c, 'q4', r'<details class="row"><summary><span class="sm"><span class="pb deep"')),
        ('badge', 'badge 1 in #main is not a link', lambda c: I(c, '<p><span class="pb" data-fam="change">1</span> loose</p>')),
        ('badge', 'sits in a link to #ch-2, not to its piece', lambda c: I(c, '<p><a class="pref" href="#ch-2"><span class="pb" data-fam="change">1</span> x</a></p>')),
        ('badge', "reads '9': no piece has that number", lambda c: I(c, '<p><a class="pref pbl" href="#ch-1"><span class="pb" data-fam="change">9</span></a></p>')),
        ('badge', "want filled (main flow), data-fam 'change'", lambda c: P(c, '<span class="pb" data-fam="change">1</span>', '<span class="pb" data-fam="tests">1</span>')),
        ('badge', "hollow, data-fam 'change'", lambda c: P(c, '<span class="pb" data-fam="change">2</span>', '<span class="pb deep" data-fam="change">2</span>')),
        ('badge', 'the badge class is for piece badges', lambda c: I(c, '<p><b class="pb">1</b></p>')),
        ('badge', 'has no badge: cite a piece as badge + name', lambda c: I(c, '<p><a class="pref" href="#ch-1">the reservations</a></p>')),
        ('badge', 'not to a piece', lambda c: I(c, '<p><a class="pref" href="#quiz"><span class="pb" data-fam="change">1</span></a></p>')),
        ('nest', 'a link inside a link', lambda c: I(c, '<p><a href="#ch-1">the <a class="pref pbl" href="#ch-1"><span class="pb" data-fam="change">1</span></a></a></p>')),
        ('circled', 'uses a circled number', lambda c: I(c, '<p>Read \u2460 first.</p>')),
        ('circled', 'puts a circled number in content', lambda c: P(c, '</style>', '.x::before{content:"\u2461"}</style>')),
        ('label', 'names "chapter"', lambda c: I(c, '<p>See chapter 2.</p>')),
        ('label', 'names "Ch n"', lambda c: I(c, '<p>As Ch 2 says.</p>')),
        ('label', 'names "piece n"', lambda c: I(c, '<p>Read piece 2 first.</p>')),
        ('label', 'names a goal id', lambda c: I(c, '<p>It builds goal.hold today.</p>')),
        ('label', 'names a file:line label', lambda c: I(c, '<p>The branch at ReserveStock.php:19 decides.</p>')),
        ('section-ref', "'the map' names a section but is not a link", lambda c: I(c, '<p>Start with the map.</p>')),
        ('section-ref', "'All 99 files', but the change has 13 files", lambda c: I(c, '<p><a href="#files">All 99 files</a></p>')),
        ('section-ref', "'Check yourself' links to #deeper, not to the section it names", lambda c: I(c, '<p><a href="#deeper">Check yourself</a></p>')),
        ('section-ref', 'the row is named by its heading', lambda c: _rx(c, r'(<summary>(?:<span class="sm">)?)Generated files', r'\1Generated and moved files')),
        ('section-ref', "#pieces is headed 'The four pieces': want 'The two pieces'", lambda c: _rx(c, r'(\bid="pieces"[^>]*>)The two pieces', r'\1The four pieces')),
        ('filter', '13 changed files (threshold 20): no file-filter UI', lambda c: I(c, '<input type="search" id="ftree-q">')),
        ('extlink', 'opens a new tab', lambda c: I(c, '<p><a href="https://example.com/x">x</a></p>')),
        ('extlink', 'opens a new tab', lambda c: I(c, '<p><a href="https://example.com/y" target="_blank" rel="opener">y</a></p>')),
        ('text-size', 'below 1rem; only the strip digits', lambda c: P(c, '</style>', '.x{font-size:.8rem}</style>')),
        ('text-size', 'below 1rem; only the strip digits', lambda c: I(c, '<p style="font-size:90%">x</p>')),
        ('text-size', 'sets the root font size', lambda c: P(c, '</style>', 'html{font-size:12px}</style>')),
        ('text-size', 'an absolute size ignores', lambda c: P(c, '</style>', '.y{font:600 11px/1 serif}</style>')),
        ('root', 'authored words above the pieces: at most 480', lambda c: P(c, '<p class="lead">', '<p class="lead">' + 'word ' * 500)),
        ('non-goal', "'No customer email when a hold is released' is not on the first screen", lambda c: _rx(c, r'<li id="carry-not-here-1".*?</li>', '')),
        ('non-goal', 'is not on the first screen', lambda c: _rx(c, r'(<ul class="carry">.*?</ul>)', r'<details><summary>More</summary>\1</details>')),
        ('trace-table', '3 trace rows with a state other than tested: the page needs the trace table', lambda c: _rx(c, r'<table class="ft tt">.*?</table>', '')),
        ('trace-table', '3 trace rows, all tested: no trace table', lambda c: [r.update(state='tested', proven=['spec.short-line']) for r in T(c)]),
        ('sources', 'a local path in title', lambda c: I(c, '<p><span title=".ai/ABC-123/decisions.md">x</span></p>')),
        ('sources', 'a local path in aria-label', lambda c: I(c, '<p><a href="#refs" aria-label="see /home/dev/notes.md">x</a></p>')),
        ('sources', 'a local path in visible text', lambda c: I(c, '<p>From review/fact-check.md.</p>')),
        ('sources', 'a bare URL in visible text', lambda c: I(c, '<p>See https://example.com/x for more.</p>')),
        ('sources', 'src-zzz is listed, but no chip cites it', lambda c: P(c, '<ul class="srcs">', '<ul class="srcs"><li id="src-zzz"><span class="sl">A note</span></li>')),
        ('sources', '"Cited in" has no link to its chip', lambda c: _rx(c, r'<a class="cite"[^>]*>.*?</a>', '')),
        ('sources', 'the per-reference store (ol.refs) is visible', lambda c: P(c, '<ol class="refs" hidden>', '<ol class="refs">')),
        ('sources', 'code, goals and non-goals are not sources', lambda c: P(c, '<ol class="refs" hidden>', '<ol class="refs">')),
        ('sources', 'Sources groups are Glossary · Jira', lambda c: P(c, '<h4>Jira</h4>', '<h4>Glossary</h4><h4>Jira</h4>')),
        ('sources', 'src-prd has a URL but no link to it', lambda c: c['plan']['origins']['prd'].__setitem__('url', 'https://tracker.example.com/browse/ABC-9')),
        ('sources', 'origins pr: its url carries a share token (sk=)', lambda c: c['plan']['origins']['pr'].__setitem__('url', 'https://claude.ai/artifact/toy-1?sk=Zz9Yy8Xx7')),
        ('sources', 'origins prd: its url carries a share token (token=)', lambda c: c['plan']['origins']['prd'].__setitem__(
            'url', 'https://tracker.example.com/browse/ABC-123?focusedCommentId=10001&token=abc123')),
        ('plan', 'private material', lambda c: c['plan']['sources'].append('.ai/ABC-123/logs/worker.log')),
        ('plan', 'private material', lambda c: c['plan']['sources'].append('.ai/ABC-123/repro/db-dump.sql.gz')),
        ('shape', 'the file tree lists 12 files, the change has 13', lambda c: _rx(c, r'<li class="fi"[^>]*>.*?</li>', '')),
        ('shape', 'the diff strip has 12 tiles for 13 files', lambda c: _rx(c, r'(<nav class="strip"[^>]*>)<a [^>]*>.*?</a>', r'\1')),
        ('shape', 'min-width of at least 1rem', lambda c: P(c, 'nav.strip>a{min-width:1rem}', '')),
        ('shape', 'no piece index (ol.pindex)', lambda c: _rx(c, r'<ol class="pindex">.*?</ol>', '')),
    ]


def _plants_b():
    """Planted errors on the intent-only contract fixture B."""
    Q = lambda c: c['quiz']['questions']        # noqa: E731
    T = lambda c: c['plan']['trace']            # noqa: E731
    I = lambda c, t: c.__setitem__('page', c['page'].replace('</main>', t + '</main>', 1))    # noqa: E731, E741
    return [
        ('plan', 'prd.md says', lambda c: c['plan']['contract'].__setitem__('version', 'v1')),
        ('plan', 'prd.md says', lambda c: c['plan']['contract'].__setitem__('status', 'Draft')),
        ('plan', 'artifact.md says', lambda c: c['plan']['contract']['storyboard'].__setitem__('built_from', 'contract v2 (2026-11-03)')),
        ('trace', 'intent-only (no code yet): want', lambda c: T(c)[0].update(state='untested', built=['file:src/Orders/PlaceOrder.php:1'])),
        ('trace', 'R2.a (prd.md) has no trace row', lambda c: T(c).pop(2)),
        ('trace', 'non-goal needs a note', lambda c: T(c)[1].pop('note')),
        ('quiz', 'intent-only quiz', lambda c: Q(c)[0].__setitem__('kind', 'criterion')),
        ('quiz', 'only a piece takes checkpoints', lambda c: Q(c)[0].__setitem__('final', False)),
        ('plan', 'chapters must be empty', lambda c: c['plan'].__setitem__('chapters', [{'id': 'ch-1', 'files': []}])),
        ('plan', 'lists 1 changed files', lambda c: c['map']['files'].append({'path': 'x.php', 'kind': 'code', 'tier': 'read'})),
        ('ref', 'quote only its **Status:** line', lambda c: c['plan']['refs']['FB1'].__setitem__('text', 'should a damaged kit fail the test at once?')),
        ('plan', 'private material', lambda c: c['plan']['sources'].append('.ai/XYZ-9/review/cm7/decision-sheet.md')),
        ('ref', 'in its own entry', lambda c: c['plan']['refs']['FB1'].__setitem__('text', '**Status:** open')),     # FB2's line
        ('ref', 'has no "### FB9" entry', lambda c: c['plan']['refs'].__setitem__('FB9', dict(c['plan']['refs']['FB1']))),
        # the intent-only shape
        ('shape', 'intent-only (no code): the diff strip must not render', lambda c: I(c, '<nav class="strip"></nav>')),
        ('shape', 'intent-only (no code): the file tree (#ftree) must not render', lambda c: I(c, '<nav id="ftree"></nav>')),
        ('shape', 'What was asked (#asked) sits open in the main flow', lambda c: _rx(
            c, r'(<section class="sec" id="asked">.*?</section>)', r'<details><summary>What was asked</summary>\1</details>')),
        ('quiz-place', 'no link to Check yourself besides the bar pill', lambda c: _in_header(c, 'href="#quiz"', 'href="#deeper"')),
        ('non-goal', 'is not on the first screen', lambda c: _rx(c, r'<li id="carry-not-here-1".*?</li>', '')),
        ('trace-table', 'the page needs the trace table', lambda c: _rx(c, r'<table class="ft tt">.*?</table>', '')),
    ]


CAUGHT = Counter()      # planted errors caught, per check


def _caught(ctx, plants):
    n = 0
    for key, needle, plant in plants:
        if needle == 'node --check' and not shutil.which('node'):
            print('  skip: node --check plant (node not found)')
            continue
        c = copy.deepcopy(ctx)
        plant(c)
        e, _, _ = check(c, ())
        assert any(k == key and needle in msg for k, msg in e), (key, needle, e)
        CAUGHT[key] += 1
        n += 1
    return n


def selftest():
    os.environ.update({'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_AUTHOR_NAME': 'selftest',
                       'GIT_AUTHOR_EMAIL': 'selftest@example.com', 'GIT_COMMITTER_NAME': 'selftest',
                       'GIT_COMMITTER_EMAIL': 'selftest@example.com'})
    real = os.path.join(os.path.dirname(BUILD), '..', 'assets', 'explainer-shell.html')
    with tempfile.TemporaryDirectory() as td:
        repo, xd = _fixture(td)
        rc, out = _run(BUILD, 'map', '--base', 'main', '--out', xd)
        assert rc == 0, out
        m = B.read_json(xd, 'map.json')
        tiers = {f['path']: (f['tier'], f['reason']) for f in m['files']}
        want = {'composer.lock': ('skip', 'lockfile'), 'src/Orders/OrderProxy.php': ('skip', 'generated marker in the first 5 lines'),
                'public/logo.png': ('verify', 'binary'), 'src/Inventory/StockLevel.php': ('verify', 'pure rename'),
                'src/Legacy/OldReserver.php': ('read', 'deleted: say where the behaviour went'),            # D-f
                'src/Orders/OrderTotals.php': ('verify', 'whitespace-only'), 'config/release.yml': ('read', ''),  # S2
                '.ai/ABC-123/prd.md': ('skip', 'pipeline artifact: read as a why-source, not explained'),       # D-e
                'src/Orders/PlaceOrder.php': ('read', ''), 'config/inventory.yml': ('read', ''), 'src/Inventory/ReserveStock.php': ('read', ''),
                'tests/Inventory/ReserveStockTest.php': ('read', ''),
                'database/migrations/2026_11_10_000001_create_stock_reservations.php': ('read', '')}
        assert tiers == want, tiers                              # CHANGELOG.md is after the merge base: not in the map
        assert m['head_ref'] == 'feature', m['head_ref']         # D-g: never the literal HEAD
        assert open(os.path.join(xd, '.gitignore')).read() == '*\n'   # DF-B 14: an existing dir under .ai/ gets one
        fresh, plain_ = os.path.join(td, 'fresh', 'xd'), os.path.join(td, 'plain')
        rc, out = _run(BUILD, 'map', '--base', 'main', '--out', fresh, '--repo', repo)
        assert rc == 0 and open(os.path.join(fresh, '.gitignore')).read() == '*\n', out   # D-e
        os.makedirs(plain_)
        rc, out = _run(BUILD, 'map', '--base', 'main', '--out', plain_, '--repo', repo)
        assert rc == 0 and not os.path.exists(os.path.join(plain_, '.gitignore')), out    # an existing dir outside .ai/: left alone
        rc, out = _run(BUILD, 'map', '--base', 'feature', '--out', os.path.join(td, 'none'), '--repo', repo)   # base == head
        mn = B.read_json(os.path.join(td, 'none'), 'map.json')
        assert rc == 0 and mn['intent_only'] and mn['files'] == [] and 'no commits past' in mn['note'] and mn['sources_found'] == [], out
        assert mn['contract'] is None and mn['criteria'] == [] and 'asked: no prd.md, workflows.md or investigation.md' in out, out  # V3-d
        rc, out = _run(BUILD, 'map', '--intent-only', '--base', 'main', '--out', os.path.join(td, 'forced'), '--repo', repo,
                       '--ticket-dir', os.path.join(repo, '.ai', 'ABC-123'), '--ticket-dir', os.path.join(repo, '.ai', 'ABC-123', 'v2'))
        mf = B.read_json(os.path.join(td, 'forced'), 'map.json')
        assert rc == 0 and mf['intent_only'] and mf['files'] == [] and '13 changed files' in mf['note'], out
        assert mf['sources_found'] == ['.ai/ABC-123/%s' % n for n in ('prd.md', 'decisions.md', 'spec-from-tests.md', 'backend-summary.md',
                                                                       'pr.md', 'v2/pr2.md')], mf['sources_found']        # V3-d
        assert mf['criteria'] == ['R1.a', 'R1.b', 'R2.a'] and mf['contract'] is None and '3 criteria (R<n>.<x>)' in out, out
        assert m['sources_found'] == mf['sources_found'][:-1] and not m['intent_only'], m['sources_found']   # --out's parent is the ticket dir
        for rel in ('root-cause.md', 'handoff.md', 'fe-handoff.md', 'investigation/synthesis.md', 'investigation/notes-panel.md',
                    'investigation/raw.txt', 'logs/worker.log'):        # a bug fix's own notes are its ask
            _w(repo, '.ai/BUG-1/' + rel, '# toy\n')
        rc, out = _run(BUILD, 'map', '--intent-only', '--base', 'main', '--out', os.path.join(td, 'bug'), '--repo', repo,
                       '--ticket-dir', os.path.join(repo, '.ai', 'BUG-1'))
        mg = B.read_json(os.path.join(td, 'bug'), 'map.json')
        assert rc == 0 and mg['sources_found'] == ['.ai/BUG-1/%s' % n for n in ('fe-handoff.md', 'handoff.md', 'root-cause.md',
                                                                                'investigation/synthesis.md')], mg['sources_found']
        assert ("the ask is in the ticket's own notes, .ai/BUG-1/handoff.md, .ai/BUG-1/root-cause.md, .ai/BUG-1/investigation/: "
                'their numbered fix steps are goal.<slug> rows') in out and 'PR body, Jira or commits' not in out, out
        for r, want in (('git@github.com:/Example-Org/example-repo.git', 'https://github.com/Example-Org/example-repo'),
                        ('git@github.com:Org/repo', 'https://github.com/Org/repo'),                              # V3-e, DF-D D3
                        ('ssh://git@ssh.github.com:443/Org/repo.git', 'https://github.com/Org/repo'),
                        ('ssh://git@github.example.com/Org/repo.git/', 'https://github.example.com/Org/repo'),
                        ('https://x-access-token:t0k@github.com/Org/repo.git/\n', 'https://github.com/Org/repo'),
                        ('https://github.com/Org/repo/', 'https://github.com/Org/repo'),
                        ('https://gitlab.com/Org/repo.git', None), ('/srv/git/repo.git', None), ('', None)):
            assert B.forge_url(r) == want, (r, B.forge_url(r))
        fs = [{'path': 'old/check.py', 'status': 'D'}, {'path': 'new/check.py', 'status': 'A'}, {'path': 'new/other.py', 'status': 'A'}]
        B.near_moves(fs)                                                                     # DF-B 2
        assert fs[1]['pred'] == ['old/check.py'] and 'pred' not in fs[0] and 'pred' not in fs[2], fs
        kinds = {f['path']: f['kind'] for f in m['files']}
        assert kinds['tests/Inventory/ReserveStockTest.php'] == 'test' and kinds['config/inventory.yml'] == 'config', kinds
        assert kinds['database/migrations/2026_11_10_000001_create_stock_reservations.php'] == 'migration', kinds
        assert [f['old_path'] for f in m['files'] if f['status'] == 'R'] == ['src/Inventory/Stock Level.php'], m['files']
        shell = os.path.join(td, 'mini-shell.html')
        _w(td, 'mini-shell.html', MINI_SHELL)
        rc, out = _run(BUILD, 'build', xd, '--shell', shell)
        assert rc == 0, out
        ctx = load(xd)
        err, warn, info = check(ctx)
        assert not err, err
        pg = ctx['page']
        assert 'release_window_minutes: 30\n</span>' in pg and '\r' not in pg, 'CRLF hunk'
        assert re.search(r'<span class="old">src/Inventory/Stock Level\.php →</span>', pg), 'rename row'
        d = Dom(pg)
        by = d.byid
        at = [by[k].i for k in ('start', 'map', 'carry', 'pieces', 'ch-1', 'ch-2', 'quiz', 'deeper', 'asked', 'ch-3', 'ch-mech', 'files', 'refs')]
        assert at == sorted(at), 'the v10 order: Start here, the map, carry, the pieces, Check yourself, Go deeper'
        assert not any(u.tag == 'details' for u in by['ch-1'].ups()) and any(u.tag == 'details' for u in by['ch-3'].ups()), 'must open, skim deep'
        pbs = d.find('span', 'pb')
        assert {text_of(d, x) for x in pbs} == {'1', '2', '3'} and {text_of(d, x) for x in pbs if 'deep' in x.cls()} == {'3'}, 'badges'
        assert [n.at['href'] for n in d.find('a', 'pbl') if d.find('header', 'doc')[0].has(n)][:2] == ['#ch-1', '#ch-2'], 'Read pieces ①–②'
        assert {'carry-bypasses-1', 'carry-ask-1', 'carry-not-here-1'} <= set(by), 'carry lines'
        assert 'ftree-q' not in by and not d.find(None, 'tfil'), '13 files: no filter UI'
        assert d.find('table', 'tt') and any(x.startswith('root: ') for x in info), 'trace table, root info'
        assert all(n.at.get('target') == '_blank' for n in d.find('a') if n.at.get('href', '').startswith('http')), 'new tabs'
        assert [n.at['id'] for n in d.find('li', within=by['refs']) if n.at.get('id', '').startswith('src-')] == [
            'src-prd', 'src-pr', 'src-decisions', 'src-spec'], 'Sources by origin, grouped'
        assert not [x for k, x in warn if k in ('shape', 'budget')], warn
        assert any(x.startswith('reading path (information): root ') for x in info), info
        f8 = B.fid('src/Inventory/ReserveStock.php')[2:]
        assert 'href="#h-%s-13"' % f8 in pg or 'href="#%s"' % B.fid('src/Inventory/ReserveStock.php') in pg, 'hotspot links'
        meta = json.loads(xd_data(pg))['meta']
        assert meta['stage'] == 'full' and set(meta['inputs']) == {'prd.md', 'decisions.md', 'spec-from-tests.md'} and len(meta['build']) == 12, meta
        assert B.ref_kind('R1.a') == 'Criterion' and B.ref_kind('AC3') == 'Criterion' and B.ref_kind('R4') == 'Requirement', 'ref kinds'
        assert [B.ref_kind(x) for x in ('FB2', 's1', 's1.3', 'spec.x', 'ng.x', 'A3', 'pr.x', 'jira', 'goal.x', 'proof.x')] == [
            'Ruling', 'Use case', 'Workflow step', 'Test scenario', 'Non-goal', 'Acceptance', 'PR body', 'Jira', 'Goal', 'Source'], 'ref kinds'
        assert B.criteria('- **AC1** (R1) a\n- **AC2** (R2) b\n<!-- AC9 -->\n') == ('AC<n>', ['AC1', 'AC2']), 'AC ids'
        assert B.criteria('- **R1** a\n- **R2** b\n> - v2 2026-11-03 approved: new R9\n') == ('R<n>', ['R1', 'R2']), 'R ids'
        assert B.criteria(PRD_B) == ('R<n>.<x>', ['R1.a', 'R1.b', 'R2.a']) and B.criteria('no ids') == (None, []), 'criteria'
        assert B.contract_of('> - v1.9 2026-11-01 frozen: a\n> - v1.10 2026-11-01 frozen: b\n') == {'version': 'v1.10', 'status': 'Frozen'}
        assert B.contract_of(PRD) is None and B.contract_of(PRD_B) == {'version': 'v2', 'status': 'Approved'}, 'contract'
        src, n = B.Src(repo, m), 0
        for k, v, needle in (('data-code', 'src/Inventory/ReserveStock.php:1-999', 'outside the file'),
                             ('data-hunk', 'src/Nope.php:1-2', 'not in the diff'),
                             ('data-hunk', 'src/Orders/PlaceOrder.php:28-30', 'overlaps no hunk'),
                             ('data-code', 'src/Inventory/ReserveStock.php@base:1-2', 'does not exist at base'),
                             ('data-code', 'src/Inventory/StockLevel.php@base:1-3', '')):    # S5: a rename's base is its old path
            e = src.resolve({k: v})[2] or ''
            assert (needle in e) if needle else not e, (v, e)
            n += 1
        fig, lines, _ = src.resolve({'data-hunk': 'src/Inventory/ReserveStock.php:13-15'})   # S6: an added file is one hunk
        assert lines == 10 and '@@ -0,0 +10,9 @@ clipped' in fig, (lines, fig)
        errs = []
        B.render(src, ctx['plan'], ctx['quiz'], dict(ctx['frags'], **{'ch-2': ctx['frags']['ch-2'] + '<span class="ref" data-ref="D9"></span>'
                                                                      '<span class="ref" data-ref="file:src/Nope.php:3"></span>'}), MINI_SHELL, errs)
        assert any('no plan.json refs entry' in x for x in errs) and any('does not exist at head' in x for x in errs), errs
        c = copy.deepcopy(ctx)
        c['plan']['trace'].append({'id': 'goal.fast', 'text': 'Checkout stays fast', 'built': ['ch-2'], 'state': 'untested'})
        c['plan']['chapters'][1]['checks'] = ['How many units a **short line** holds']
        e, w, _ = check(c)
        assert not any('goal.fast' in x for _, x in e + w) and any('2 pieces test the same fact' in x for _, x in w), (e, w)
        assert not private(ctx, '.ai/X/explainer/review/tests-abc1234.txt', None) and private(ctx, '.ai/X/review/fact-check.md', None)
        assert private(ctx, '.ai/X/repro/db-dump/run.tsv', None) and not private(ctx, '.ai/X/dumpling-notes.md', None)
        assert not private(ctx, '.ai/X/catalog.md', None) and private(ctx, '.ai/X/logs/nginx/error.log.2.gz', None)
        c = copy.deepcopy(ctx)                       # a why's source: a ref quoting a note in plan.json sources counts as recorded
        _w(repo, '.ai/ABC-123/root-cause.md', '## Fix\n1. Hold the stock in the order transaction, so a retry cannot hold it twice.\n')
        c['plan']['sources'].append('.ai/ABC-123/root-cause.md')
        c['plan']['refs']['rc.fix'] = {'title': 'The fix', 'src': '.ai/ABC-123/root-cause.md', 'origin': 'decisions',
                                       'text': 'Hold the stock in the order transaction'}
        c['quiz']['questions'][0].update(kind='why', evidence=['rc.fix'])
        why = lambda c_: [x for _, x in check(c_)[1] if 'needs a recorded source' in x]      # noqa: E731
        assert not why(c), why(c)
        c['quiz']['questions'][0]['evidence'] = ['root-cause.md']                           # the note named directly
        assert not why(c), why(c)
        c['quiz']['questions'][0]['evidence'] = ['src/Inventory/ReserveStock.php:13']       # code is not a recorded why
        assert why(c) == ['q1: a why question needs a recorded source (decisions, PRD, ruling, PR text, or a note in plan.json sources)'], why(c)
        os.remove(os.path.join(repo, '.ai', 'ABC-123', 'root-cause.md'))
        c = copy.deepcopy(ctx)                       # a Jira comment link keeps its query; only a token fails
        c['plan']['origins']['prd']['url'] = 'https://tracker.example.com/browse/ABC-123?focusedCommentId=10001'
        assert not any('share token' in x for _, x in check(c)[0])
        assert '2 local notes, not online · 1 online' in pg, 'Built from counts the online sources'
        assert re.search(r'<li id="carry-bypasses-1">.*?data-ref="D1".*?</li>', pg), 'a hotspot ref is its chip'
        n += 5
        tf, h7 = os.path.join(xd, 'review', 'tests-%s.txt' % m['head'][:7]), m['head'][:7]     # V3-m: the run names the head
        keep = B.read_text(tf)
        _w(xd, 'review/tests-%s.txt' % h7, '$ composer test\nTests: 1 passed\n')
        assert any('R1.b: tested needs review/tests-%s.txt naming %s' % (h7, h7) in x for _, x in check(ctx)[0]), 'V3-m'
        _w(xd, 'review/tests-%s.txt' % h7, keep)
        n += 3
        c = copy.deepcopy(ctx)
        Q = c['quiz']['questions']
        Q[0]['chapter'], Q[1]['chapter'] = 'intuition', 'background'                        # S3
        c['plan'].pop('ops')
        e, w, _ = check(c)
        assert not [x for x in e if x[0] == 'quiz'] and any('ops is empty' in x for _, x in w), (e, w)   # D-h
        b = blind(ctx['plan'], ctx['quiz'])
        assert b.count('   A) ') == 5 and b.startswith('5 questions') and '\nq1. ' in b and 'feedback' not in b.lower() and 'Option a for' not in b, b
        t = teach(ctx['page'], ctx['plan'], ctx['quiz'])
        assert 'Reservations as data' in t and 'Font' not in t and 'Option a for' not in t and 'ReserveStock' in t, t[:400]
        n += _caught(ctx, _plants(ctx))
        c = copy.deepcopy(ctx)                       # what the shape checks let pass: the near misses of each plant
        c['page'] = c['page'].replace('</main>', '<p>Out of scope: a non-goal. The code, piece by piece '
                                      '<a class="pref pbl" href="#ch-1"><span class="pb" data-fam="change">1</span></a>.</p>'
                                      '<p><code>chapter 2 at ReserveStock.php:19</code> <span title="see chapter 2 or ① first">x</span> '
                                      '<a class="ref file" href="#ch-1" data-ref="file:src/Inventory/ReserveStock.php:19">ReserveStock.php:19</a> '
                                      '<a href="https://example.com/z" target="_blank" rel="noopener noreferrer">https://example.com/z</a></p>'
                                      '<style>@media print{body{font-size:10.5pt}} nav.strip>a span{font-size:.75rem} .z{font:600 1rem/1.4 serif}</style>'
                                      '<fieldset class="q" id="qz"><legend>Where is the map? Read pieces</legend><button class="opt">'
                                      'What was asked</button></fieldset><p><code>Check yourself</code> <a class="ref" href="#ref-d1" '
                                      'data-ref="D1">the map</a></p></main>', 1)
        e = check(c)[0]
        assert not [x for x in e if x[0] in ('label', 'circled', 'extlink', 'text-size', 'sources', 'badge', 'nest', 'section-ref',
                                             'quiz-place')], e
        n += 1
        c = copy.deepcopy(ctx)                       # S5: a hash in <pre>, a chip or the quiz evidence passes; a bare id warns
        c['frags']['ch-2'] += ('<pre>git show a1b2c3d</pre><p>It follows D1 <span class="ref" data-ref="commit:a1b2c3d">a1b2c3d</span>.</p>'
                               '<ul><li>D1: reserve at placement.</li></ul><p><code>D1</code></p><table class="toy"><tr><td>R1.a</td></tr></table>')
        c['quiz']['questions'][0].update(evidence_note='a1b2c3d added it at ReserveStock.php:19')
        c['plan']['trace'][0]['note'] = 'R1.b covers the rest'
        e, w, _ = check(c)
        assert not [x for k, x in e if k == 'reader'], e
        assert [x for k, x in w if k == 'reader'] == ['fragments/ch-2.html: bare D1 in prose: lead with what D1 says; attach the id as a chip'], w
        n += 4
        c = copy.deepcopy(ctx)                       # soft budgets warn and never fail; text under More on this is depth
        c['plan']['chapters'][0]['gist'] = ' '.join(['word'] * 31)
        c['frags']['ch-1'] = '<p>%s</p>' % ('word ' * 130) + c['frags']['ch-1']
        c['frags']['ch-2'] += '<p>%s</p>' % ('word ' * 1500)
        c['quiz']['questions'][4]['options'] = list(c['quiz']['questions'][3]['options'])
        e, w, i = check(c)
        bw = [x for k, x in w if k == 'budget']
        assert (any('piece 1 (ch-1): gist is 31 words' in x for x in bw) and any(x.startswith('fragments/ch-2.html: 15') for x in bw)
                and any('piece 1 (ch-1): 1' in x and 'before <!--more-->' in x for x in bw)
                and not any('piece 2 (ch-2):' in x and 'before <!--more-->' in x for x in bw)), bw
        assert any('q4, q5 share one option set' in x for _, x in w), w
        n += 5
        fp = {'id': 'q9', 'stem': 'At 10:00 ABC-123 runs `skunexus-jira-prd` on docs/D1.md for 1234567 acceded units.',
              'options': ['10:30', 'jira-sync', 'R1.a-notes', 'line items']}       # none is a label
        assert labels(fp, {'jira': {}, 'D1': {}, 'R1': {}, 'file:x.php:3': {}}) == [], labels(fp, {'jira': {}, 'D1': {}})
        c = copy.deepcopy(ctx)
        c['quiz']['questions'][0]['stem'] = '`a` `b` `c` `d` ' + c['quiz']['questions'][0]['stem']
        assert any('implementation trivia' in x for _, x in check(c)[1]), 'code-span warning'
        n += 2
        e, _, _ = check(ctx, ['Stock Reservations'])
        assert any(k == 'forbid' for k, _ in e), e
        assert _run(os.path.abspath(__file__), xd, '--forbid', '(')[0] == 2
        assert stale(ctx)[0] == 0
        B.git(repo, 'checkout', '-q', 'main')                # another branch checked out: the page is still fresh
        assert stale(ctx)[0] == 0
        B.git(repo, 'checkout', '-q', 'feature')
        assert stale(dict(ctx, map=dict(ctx['map'], base_ref='gone')))[0] == 2
        n += 3

        # no map: the build drops the section, Start here starts at the carry list, the check warns and passes
        xn = os.path.join(repo, '.ai', 'ABC-123', 'explainer-nomap')
        shutil.copytree(xd, xn)
        pn = B.read_json(xn, 'plan.json')
        pn.pop('map')
        _w(xn, 'plan.json', json.dumps(pn, indent=1))
        rc, out = _run(BUILD, 'build', xn, '--shell', shell)
        assert rc == 0, out
        e, w, _ = check(load(xn))
        assert not e and any(k == 'shape' and 'no map' in x for k, x in w) and 'id="map"' not in load(xn)['page'], (e, w)
        n += 1

        # a main-flow checkpoint renders open at its piece's end, after More on this: it passes the fold check
        xk = os.path.join(repo, '.ai', 'ABC-123', 'explainer-checkpoint')
        shutil.copytree(xd, xk)
        qk = B.read_json(xk, 'quiz.json')
        qk['questions'][0].update(final=False, chapter='ch-1')
        _w(xk, 'quiz.json', json.dumps(qk, indent=1))
        rc, out = _run(BUILD, 'build', xk, '--shell', shell)
        ck = load(xk)
        e = check(ck)[0]
        assert rc == 0 and 'id="q1"' in ck['page'] and not [x for x in e if x[0] in ('quiz-place', 'quiz')], (out, e)
        n += 1

        # later commits: the page goes stale
        _w(repo, 'src/Orders/PlaceOrder.php', PLACE + '// later\n')
        B.git(repo, 'commit', '-qam', 'later')
        assert stale(load(xd))[0] == 3
        n += 1

        # B: an intent-only contract ticket: no code, a versioned PRD, a storyboard built from an older contract
        for rel, data in TICKET_B.items():
            _w(repo, '.ai/XYZ-9/' + rel, data)
        rc, out = _run(BUILD, 'map', '--base', 'main', '--head', 'main', '--out', os.path.join(repo, '.ai', 'XYZ-9', 'explainer'))
        assert rc == 0 and 'contract v2 (Approved) · 3 criteria (R<n>.<x>)' in out and 'storyboard: built from contract v1 (2026-11-02)' in out, out
        xb = os.path.join(repo, '.ai', 'XYZ-9', 'explainer')
        mb = B.read_json(xb, 'map.json')
        assert mb['intent_only'] and mb['criteria'] == ['R1.a', 'R1.b', 'R2.a'] and mb['contract'] == {
            'version': 'v2', 'status': 'Approved', 'storyboard': {'url': 'https://claude.ai/artifact/abc123XYZ',
                                                                  'built_from': 'contract v1 (2026-11-02)'}}, mb
        assert mb['sources_found'] == ['.ai/XYZ-9/%s' % n for n in ('prd.md', 'workflows.md', 'feedback.md', 'prototype/artifact.md')]
        _fixture_b(repo, mb)
        rc, out = _run(BUILD, 'build', xb, '--shell', shell)
        assert rc == 0, out
        cb = load(xb)
        err, warn, info = check(cb)
        assert not err, err
        pg = cb['page']
        db = Dom(pg)
        assert not ({'ftree', 'files', 'pieces', 'ch-mech'} & set(db.byid)) and not db.find('nav', 'strip') and not db.find('ol', 'pindex'), 'no code parts'
        assert db.byid['map'].i < db.byid['carry'].i < db.byid['asked'].i < db.byid['quiz'].i < db.byid['deeper'].i, 'intent-only order'
        assert 'class="sb-link" href="https://claude.ai/artifact/abc123XYZ#s1.1" target="_blank" rel="noopener"' in pg, 'storyboard link'
        assert '<dt>Contract</dt><dd>v2 · Approved</dd>' in pg and not any('Base → Head' in x for x in re.findall(r'<dt>[^<]*</dt>', pg)), 'props'
        assert not re.search(r'href="#(files|code|ch-mech|f-[0-9a-f]{8})"', pg), 'V3-e: intent-only links'       # DF-D D6, D7
        assert not any('header says' in x for _, x in warn), warn
        assert 'Who pays the return postage?' in norm_ws(text_of(db, db.byid['carry-ask-1'])), 'the open question is a carry line'
        assert any(x == 'plan.json open_questions[0]: bare Q1, FB2 in prose: lead with what Q1 says; attach the id as a chip' for _, x in warn), warn
        assert list(B.source_hashes(repo, xb, ['.ai/ABC-123/prd.md', '.ai/XYZ-9/prd.md'])) == ['prd.md', '.ai/XYZ-9/prd.md'], 'DF-C 19'
        assert stale(cb) == (0, 'fresh: intent-only, every why-source as built'), stale(cb)
        n += _caught(cb, _plants_b())
        prd_b = os.path.join(repo, '.ai', 'XYZ-9', 'prd.md')       # a moved source: warned, stale, and 9 criteria want 5 finals
        _w(repo, '.ai/XYZ-9/prd.md', PRD_B + ''.join('- **R%d.a** Given more, then more.\n' % i for i in range(3, 9)))
        e, w, _ = check(load(xb))
        assert any(k == 'stale' and re.search(r'why-source changed since build: prd\.md@[0-9a-f]{8} → @[0-9a-f]{8}', x) for k, x in w), w
        assert any('want 5' in x for _, x in e) and any('R8.a (prd.md) has no trace row' in x for _, x in e), e
        assert not any('prd.md says' in x for _, x in e) and stale(load(xb))[0] == 3, e     # the warning covers the contract check
        _w(repo, '.ai/XYZ-9/prd.md', PRD_B)
        assert stale(load(xb))[0] == 0 and os.path.isfile(prd_b)
        _w(repo, '.ai/XYZ-9/prototype/artifact.md', TICKET_B['prototype/artifact.md'].replace('Built from: contract v1 (', 'Built from: contract v0.9 ('))
        w = check(load(xb))[1]                                                                  # V3-f: the newest row wins
        assert any('prototype/artifact.md header says v0.9, newest row v1' in x for _, x in w), w
        _w(repo, '.ai/XYZ-9/prototype/artifact.md', TICKET_B['prototype/artifact.md'])
        n += 5

        # C: a big diff, 80 files in 12 pieces, through the real build and shell
        if os.path.isfile(real) and '<!--XD:MAIN-->' in open(real, encoding='utf-8').read():
            repo_c, xc = _fixture_c(td)
            rc, out = _run(BUILD, 'map', '--base', 'main', '--out', xc, '--repo', repo_c)
            mc = B.read_json(xc, 'map.json')
            assert rc == 0 and len(mc['files']) == 80, out
            _inputs_c(xc, mc['head'][:7])
            t0 = time.time()
            rc, out = _run(BUILD, 'build', xc, '--shell', real)
            tb, t0 = time.time() - t0, time.time()
            assert rc == 0, out
            cc = load(xc)
            e, w, i = check(cc)
            tc = time.time() - t0
            assert not e, e
            dc = Dom(cc['page'])
            reg = registry(cc['plan'], mc, False)
            assert sorted({int(norm_ws(text_of(dc, x))) for x in dc.find('span', 'pb')}) == list(range(1, 13)), 'badges 1-12'
            prefs = dc.find('a', 'pref')
            assert prefs and all(norm_ws(text_of(dc, [y for y in dc.all[a.i:a.e + 1] if 'pb' in y.cls()][0])) == str(reg[a.at['href'][1:]]['n'])
                                 for a in prefs), 'every badge link targets its piece'
            assert 'ftree-q' in dc.byid, '80 files: the filter UI appears'
            tiles = [x for s in dc.find('nav', 'strip') for x in s.kids if x.tag == 'a']
            assert len(tiles) == 80 and all(x.at.get('data-f') and x.at.get('data-fam') for x in tiles), 'a strip tile per file'
            assert not [x for k, x in e if k == 'shape'], 'the strip tiles have their minimum width'
            assert {x.at.get('data-path') for x in dc.find('li', 'fi')} == {f['path'] for f in mc['files']}, 'the tree lists every file'
            assert norm_ws(text_of(dc, dc.byid['pieces'])).startswith('The ten pieces'), 'The N pieces'
            n += _caught(cc, [('filter', '80 changed files, above 20: the file tree needs its filter box', lambda c: _rx(
                c, r'<input [^>]*id="ftree-q"[^>]*>', ''))])
            print('  big diff: 80 files, 12 pieces: build %.1f s, check %.1f s (%.0f KB)' % (tb, tc, len(cc['page']) / 1024))
            for d_ in (xd, xb):
                rc, out = _run(BUILD, 'build', d_, '--shell', real)
                assert rc == 0, out
                err, warn, info = check(load(d_))
                assert not err, ('real shell', d_, err)
                print('  real shell: build and check pass, %s (%s)' % (os.path.basename(os.path.dirname(d_)),
                                                                     [i for i in info if i.startswith('page:')][0]))
        else:
            print('  skip: the real shell has no slots yet')
    print('  caught, per check: %s' % ' · '.join('%s %d' % kv for kv in sorted(CAUGHT.items())))
    print('selftest: OK (%d planted errors caught)' % n)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('dir', nargs='?')
    ap.add_argument('--forbid', action='append', default=[], metavar='REGEX',
                    help='a regex that must match nowhere in the page, plan.json, quiz.json or a fragment (a secret, '
                         'a share token, a name); repeatable: every one applies')
    ap.add_argument('--repo')
    g = ap.add_mutually_exclusive_group()
    g.add_argument('--blind', action='store_true')
    g.add_argument('--teach', action='store_true')
    g.add_argument('--stale', action='store_true')
    g.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not a.dir:
        ap.error('explainer dir required')
    try:
        for rx in a.forbid:
            re.compile(rx)
    except re.error as e:
        print('check-explainer: --forbid %r: %s' % (rx, e))
        return 2
    try:
        ctx = load(a.dir, a.repo)
        if a.stale:
            code, msg = stale(ctx)
            print(msg)
            return code
        if a.blind or a.teach:
            if not ctx['quiz']:
                raise B.Fail('quiz.json not found')
            if a.teach and ctx['page'] is None:
                raise B.Fail('explainer.html not found: build first')
            print(blind(ctx['plan'], ctx['quiz']) if a.blind else teach(ctx['page'], ctx['plan'], ctx['quiz']))
            return 0
        err, warn, info = check(ctx, a.forbid)
    except (B.Fail, OSError, UnicodeDecodeError, ValueError, KeyError) as e:
        print('check-explainer: %s: unreadable: %s' % (a.dir, e))
        return 2
    report(a.dir, err, warn, info)
    return 1 if err else 0


if __name__ == '__main__':
    sys.exit(main())
