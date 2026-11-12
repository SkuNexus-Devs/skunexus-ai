#!/usr/bin/env python3
"""Map and build a ticket's understanding page (skunexus-understand): what was asked, built and proven.

Usage: python3 -I build-explainer.py map --base <ref> [--head <ref>] [--out <dir>] [--repo <path>] [--intent-only]
                                         [--ticket-dir <dir>]...
       python3 -I build-explainer.py build <explainer-dir> [--shell <path>] [--repo <path>] [--filter-at N]

The repo is --repo, else the git toplevel of the explainer dir (map: --out), else of the current directory.
Every diff is merge_base..head, where merge_base = git merge-base <base> <head> (the three-dot view).

map: triages every changed file into map.json (tier, kind, reason, +/-, blob, id "f-" + sha1(path)[:8]).
  Renames pair at 30% similarity; an added file whose basename matches a deleted one gets pred: [the deleted paths]
  (near-move candidates, not chosen). head_ref is a named ref: HEAD is stored as the branch name (detached: the SHA,
  with a warning). --out gets a .gitignore of "*" when it has none and is new or under .ai/. forge: the https URL of
  a GitHub origin (https, ssh://[:port], scp-style git@host:[/]Org/repo; .git and a trailing slash optional), else null.
  Intent-only (--intent-only, or no commits past the merge base): files [], intent_only true and a note. A diff
  whose commits net to nothing prints "nothing to explain" and writes nothing.
  The why-sources found in each ticket dir (--ticket-dir, repeatable; default the parent of --out) go to sources_found
  as repo-relative paths: the WHY_SOURCES names, pr*.md and jira-*.md, a bug fix's own notes (root-cause*.md,
  handoff*.md, hand-off*.md) and the *.md files of an investigation/ folder. From the first prd.md: contract {version,
  status, storyboard} (prototype/artifact.md: the newest row's Built from) and criteria; always present, else null, [].
  skip    generated, vendored or pipeline: linguist-generated/-vendored attributes, lockfiles, *.min.js|css, *.map,
          vendor/, node_modules/, snapshots, head files whose first 5 lines say @generated or DO NOT EDIT, .ai/;
  verify  mechanical: a pure rename, whitespace-only (not in indentation-sensitive files), a deleted file that is
          not code or test, binary, a mode-only change, a submodule pointer;
  read    everything else. The model may move a file up a tier (into a piece), never down.

build: reads map.json, plan.json, quiz.json (optional) and fragments/*.html, resolves the code markers
  <pre data-hunk="PATH:START-END">, <pre data-code="PATH:START-END"> and <pre data-code="PATH@base:START-END">
  from git (HTML-escaped, never retyped), fills the shell slots and writes explainer.html (the publish file, no
  doctype) and explainer.local.html (the same page with a doctype, for file://). A data-hunk hunk that runs past
  START-END is clipped to the range plus 3 context lines (its @@ header says "clipped"); @base on a renamed file
  reads the old path. A marker's data-notes="LINE:text|LINE:text" puts numbered line notes beside the figure, each
  LINE a line the figure shows (else an error); data-note="text" is a caption note. A figure over 30 lines folds
  under "Show N lines". xd-data meta.build hashes map, plan, quiz and fragments for the check's staleness test;
  meta.inputs holds {basename: hash8} per plan.json source (sha256 of the file without CR, as tr -d '\\r' | sha256sum):
  the page names those notes only by count, never by name or path.
  --filter-at N (default 20): the file tree's filter box and the files table's search and filters render only above
  N changed files; xd-data meta.filter_at records N.

  Pieces. plan.json chapters[] are the pieces (the page never says "chapter"; ids ch-<n>, fragments ch-<n>.html).
  Each gets a number (its plan order), a badge span.pb[data-fam] and a name (short, else title). read: must = the
  main flow (filled badge), skim = under Go deeper (hollow badge, .deep). Family, derived: must -> change; skim whose
  files are all tests -> tests; other skim -> harness; mechanical groups' files -> gen (hatched, no badge).
  A main-flow piece is two columns: the note (the fragment up to an optional <!--more-->, its code figures moved to
  the right) and the code; "More on this" holds the rest of the fragment, "Files in this piece" and the proof line
  (no leaf when all are empty); checkpoints (quiz final: false) follow it, open, never folded. A deep piece shows its whole fragment (a <!--more--> is ignored) under
  its gist. Every reference to a piece is its badge + name (a.pref); [name](#ch-2) in plan text and
  <a href="#ch-2">…</a> in a fragment become one.

  The page, top to bottom (intent-only: no strip, tree, pieces or files):
    header   h1 (heading, else title), p.lead (glance), nav.start#start "Start here": Look at the map [and what to
             carry] (or: Look at what to carry) -> Read pieces ①–④ (intent-only: Read what was asked) -> Answer N
             questions; each step only when its target exists. Then the strip of changed files and its legend, the
             piece index.
    tree     nav.ftree#ftree (TOC slot): the changed files, folders first; a drawer below 1100px.
    main     section.brief#overview: The map (section.mapframe#map) -> To carry into the review (h2#carry +
             ul.carry) -> [intent-only: What was asked, section#asked with an h2] -> "The N pieces" (h2#pieces:
             number words two … twelve, digits above; one piece: "The piece") with each main-flow piece; every
             block ends with a Next link. Then section#quiz "Check yourself" (open, never folded), then
             section.deeper#deeper "Go deeper": closed details.row, one per plan.json deeper group, then one per
             section no group holds, then "All N files", then "Sources" (with About this page).
  The map: plan.json map present -> rule-shaped (map.rule present: who asks -> the rule -> what happens, three
  columns) or flow-shaped (no map.rule: entries -> outcomes, two columns, div.map.two); absent -> no map, and Start
  here's first step is "Look at what to carry". Never invented: every box is an authored entry, rule or outcome.
  The goals: the table "The goals and their state" (section#trace) renders at >= 4 trace rows or when any row's
  state is not tested; otherwise a one-line p.trace-status ("2 goals: 2 tested") ends What was asked.
  Sources: one entry per origin a chip cites, grouped under h4s: Jira, GitHub, Shared pages, From the author, then
  any other group in first-seen order, then Glossary. A link only where the origin has a url (new tab, noopener);
  each entry ends "Cited in:" with a link to every chip that cites it. Per-ref previews live in a hidden
  ol.refs inside #refs. No local path (.ai/, .tasks/, explainer/, review/, sources/, absolute) reaches text, a
  title or aria: a hotspot, drift or ops path under one is dropped from the line.

plan.json (written by the orchestrator). Text fields are plain text with `code`, **bold**, [name](#ch-2) piece
links (badge + name) and [words](#asked) links to any other id the page renders. Every field is optional unless marked; an absent field renders nothing.
  {"title": "TOY-7 Shelf cap",                    the <title> and the bar's name, 2-4 words, the same on every rebuild
   "heading": "How the shelf stopped going below zero",   the h1; default: title
   "glance": "A take gives at most what the shelf holds.",   the lead sentence under the h1
   "ticket": "TOY-7", "branch": "toy-7",         the reading-progress storage key and the quiz's /skunexus-understand
                                                  command; About's Ticket and Branch rows
   "mode": "author|reviewer",                     default author; meta.mode and the stage default (the page's wording
                                                  is the same for every reader)
   "stage": "intent-only|full|reviewer",          default: intent-only when map.json says so, else reviewer when
                                                  mode is reviewer, else full
   "contract": {"version": "v2", "status": "Approved",
                "storyboard": {"url": "https://claude.ai/...", "built_from": "contract v2"}} | null,
                                                  About's Contract row; with a storyboard url (claude.ai only, else an
                                                  error), every s<n>[.<m>] chip gets an sb-link to <url>#<id>
   "sources": ["sources/notes.md"],               local notes the page was built from: hashed into meta.inputs,
                                                  counted in About: a source that a ref quotes (its src) and whose
                                                  origin has a url is online, any other is a local note ("1 local
                                                  note, not online · 2 online"); a path is absolute, else under the
                                                  repo, the explainer dir or its parent
   "chapters": [{"id": "ch-1",                    required, ch-[a-z0-9-]+ (else exit 2)
                 "title": "The shelf caps a take", the piece's heading
                 "short": "the cap",               its name in badge + name references; default: title
                 "read": "must|skim",              default must; anything else exits 2
                 "files": ["src/Shelf.php", "tests/*"],   globs (fnmatch) over map.json paths; a file's home piece is
                                                  the first that claims it; [] for a piece that shows hunks of
                                                  another piece's file (the index says "shares ①'s file")
                 "gist": "One sentence.",          a deep piece's line under its heading; default: why_here
                 "why_here": "…",
                 "proof": "Proven by the shelf test:",   the proof line's lead when a trace row it builds has proven
                                                  items; default "Proven by"; built but none proven: "No test proves
                                                  this piece."
                 "risk": "high|med|low"}],         the files table's Risk; default none
   "mechanical": [{"title": "Lockfile", "files": ["composer.lock"], "intent": "…", "check": "…"}],
                                                  the "Generated files" section (#ch-mech); its files are hatched
   "trace": [{"id": "R1", "text": "Never below zero", "built": ["ch-1", "file:src/Shelf.php:12"],
              "proven": ["file:tests/ShelfTest.php:2", "spec.cap"], "note": "…",
              "state": "tested|built|untested|not-built|drift|non-goal|deferred"}],
                                                  one row per goal; built/proven items are piece ids (a.pref) or ref
                                                  ids (chips); see "The goals" above for table vs status line
   "map": {"purpose": "Two places change; each feeds what the till returns.",   the line under "The map"
           "entries_h": "Who decides · changed to ask",   column headings; "a · b" puts b in a muted small;
           "rule_h": "The rule", "outcomes_h": "What happens",   defaults: Who decides (flow: What changed),
                                                  The rule, What happens
           "arrow": "ask", "so": "so",            the wire labels; arrow default ask (flow: then), so default so
           "entries": [{"label": "The till's sell", "sub": "records the shortfall", "kind": "changed|not asked",
                        "target": "ch-2"}],      kind default changed; "not asked" entries go to the quiet line
                                                  under the columns ("Two places don't ask ① the rule:"; flow:
                                                  "Two places stay out of it:")
           "rule": {"title": "A sale goes through when", "conditions": [{"text": "the shelf holds enough"},
                    {"text": "and it is not a refund", "exception": true}], "sub": "one new check",
                    "target": "ch-1", "new": true},   absent: flow-shaped; new (default true) marks the box "new"
           "outcomes": [{"label": "sells what is there", "sub": "never below zero", "goal": "R1",
                         "target": "ch-3"}]},     goal (optional): a trace id; the box shows its state and test count
                                                  (an unknown id is an error)
         Every target (entries, rule, outcomes) is a piece id (the box shows its badge), a carry line id
         (carry-<tag>-<n>: the n-th line with that tag, in carry order) or a section on the page (asked,
         background, intuition, proven, problem, trace, look, drift, ops, ch-mech, files, carry, quiz, deeper,
         refs); anything else is an error and the box renders unlinked.
   "hotspots": [{"at": "src/Till.php:7-9", "why": "The list only grows.", "carry": "inherits", "ref": "D2"}],
   "drift": [{"at": "src/Shelf.php:12", "note": "the plan said reject", "ref": "D2", "needs_decision": true,
              "carry": "bypasses"}],
   "ops": [{"what": "Migration", "files": ["database/migrations/*"], "note": "down() drops the table",
            "ref": "commit:abc1234", "label": "TOY-6", "carry": "data"}],
   "open_questions": ["(ch-2) Should a short sale warn the cashier?"],
   "not_in_change": ["Refunds", {"text": "Restocking", "ref": "ng.restock", "label": "TOY-9"}],
         The carry list ("To carry into the review"), in this order (which numbers carry-<tag>-<n>): hotspots with
         a carry tag; drift with a carry tag; every open question (tag ask; a "(ch-2|asked|background|intuition|
         proven) " prefix becomes a trailing link to that piece or section); ops with a carry tag; the non-goals
         joined into one "not here" line. Tags inherits, bypasses,
         ask, data and not here carry a tooltip; any other tag renders without one. Untagged hotspots go to "Where
         to look hardest" (#look), untagged drift to "Where the code differs from earlier plans" (#drift,
         needs_decision first, prefixed "Needs a decision:"), untagged ops to "Deploy and merge notes" (#ops).
         at is PATH:START[-END]: the file's name links its row in All N files (plain code text when the file is not
         in the change). ref (hotspots, drift, ops) is a chip; label (hotspots, ops; optional) replaces its text,
         e.g. another ticket's key.
   "problem": "Takes could push the count below zero.", "problem_ref": {"ref": "jira.ask", "label": "TOY-7"},
   "behaviour": {"intro": "…", "cols": ["What happens next", "Before", "After"],
                 "rows": [["A take of 5 from 2", "-3", "0"]]},
         "The problem, and what happens now" (#problem): the problem with its chip, then the before/after table
         (cols default as shown; a row whose Before and After differ marks After as changed)
   "deeper": [{"summary": "What was asked", "holds": ["asked", "problem", "background", "intuition", "trace",
               "drift"]}, {"piece": "ch-3", "holds": ["ch-3", "proven", "look"]}],
         Go deeper's rows, in order: each holds the named sections that exist (piece ids, asked, background,
         intuition, proven, problem, trace, look, drift, ops, ch-mech, files). Summary: with piece, that piece's
         badge + title; else summary; default: the heading of the first section it holds. A section no row
         holds gets its own row, after these.
   "refs": {"jira.ask": {"title": "The ask", "text": "a verbatim quote", "origin": "jira-1"}},
         a chip's preview (kind by id: R<n> Requirement, R<n>.<x>|AC<n> Criterion, D Decision, T Plan task,
         Q Assumption, A Acceptance, FB Ruling, s<n> Use case, s<n>.<m> Workflow step, spec.<slug> Test scenario,
         ng.<slug> Non-goal, goal.<slug> Goal, pr[.<slug>] PR body, jira[.<slug>] Jira, else Source). A cited ref
         needs an origin in origins (else an error). commit:<sha> refs take their title from git and, with a
         forge and no origin, a GitHub origin of their own; a sha not in the repo is an error.
   "origins": {"jira-1": {"group": "Jira", "label": "The ask (description)", "url": "https://…"},
               "notes-1": {"group": "From the author", "label": "The author's investigation"}},
         ids [A-Za-z0-9_-]+ (else exit 2); group default "Other"; label names the source in words (a role, never
         a person; a date when known); url only for a source a reader can open
   "glossary": [{"term": "take", "def": "Removing units from a shelf."}]}
  The build ignores any other key.
  Fragments: fragments/asked.html, background.html, intuition.html, proven.html and fragments/<piece id>.html. A
  chip is <span class="ref" data-ref="ID">text</span>; a file: ref (data-ref="file:PATH:LINE") needs no refs entry
  (the build quotes that line at head) and opens the file in All N files. A chip whose text is empty or just its id
  shows what the ref is: a file its basename, a test file line its test('…') name, a commit its subject, else the
  ref title (a pipeline id, R5 or FB23, in a muted span.rid after it).
  quiz.json: {"built_from": "abc1234", "questions": [{"id": "q1", "chapter": "ch-1|asked|…", "final": true,
  "kind": "predict", "stem": "…", "options": ["4 options"], "answer": 1, "feedback": ["4 lines"],
  "evidence": ["src/Shelf.php:12", "D2"]}]}: final questions render in Check yourself, the others at their piece's
  end; only stem and options reach the markup, the rest stays in xd-data for the engine.

Exit 0 OK, 1 errors (both files are still written, to inspect), 2 bad input (unreadable JSON, a bad chapters[] id or
read, a bad origins id, a git failure, a shell without its slots).
"""
import argparse
import datetime
import fnmatch
import hashlib
import html
import json
import math
import os
import re
import subprocess
import sys
from collections import Counter
from urllib.parse import quote

LOCKFILES = {'composer.lock', 'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'Gemfile.lock', 'poetry.lock'}
CODE_DIRS = {'src', 'app', 'lib', 'Classes', 'Model', 'Domain'}
TIERS = ('read', 'verify', 'skip')
INDENTED = re.compile(r'\.(ya?ml|py|neon|haml|pug|slim|sass|mk)$|(^|/)Makefile$')   # whitespace carries meaning
# ponytail: a lower threshold pairs moved+edited files; it may mis-pair tiny files. Raise it if that shows up.
RENAMES = '-M30%'
WHY_SOURCES = ('prd.md', 'workflows.md', 'decisions.md', 'investigation.md', 'spec-from-tests.md', 'backend-plan.md',
               'feedback.md', 'jira-summary.md', 'test-baseline.md', 'backend-summary.md', 'fe-handoff.md',
               'prototype/artifact.md')
ASKED = ('prd.md', 'workflows.md', 'investigation.md')
ASK_SRC = re.compile(r'pr(?:[-_]?\d+|[-_][\w.-]+)?\.md|jira-[\w.-]+\.md|[\w.-]+-jira\.md')   # a PR body or a Jira copy (not prd.md)
BUG_NOTES = re.compile(r'(root-?cause|hand-?off)[\w.-]*\.md')   # a bug fix's own notes (not fe-handoff.md): its ask with no prd.md


class Fail(Exception):
    """Bad input: exit 2."""


# ---------- git ----------
def git(repo, *args, data=None, ok=(0,)):
    """Run git in repo and return stdout bytes. Pathspecs are literal, so '[id].tsx' or 'a b.php' are plain paths."""
    r = subprocess.run(['git', '--literal-pathspecs', '-C', repo, '-c', 'core.quotepath=off'] + list(args),
                       input=data, capture_output=True)
    if r.returncode not in ok:
        raise Fail('git %s: %s' % (' '.join(args[:3]), r.stderr.decode('utf-8', 'replace').strip()))
    return r.stdout


def gits(repo, *args, **kw):
    return git(repo, *args, **kw).decode('utf-8', 'replace')


def find_repo(start=None, explicit=None):
    cands = [explicit] if explicit else [start, os.getcwd()]
    for d in cands:
        if not d:
            continue
        d = os.path.abspath(d)
        while not os.path.isdir(d) and os.path.dirname(d) != d:   # --out may not exist yet
            d = os.path.dirname(d)
        r = subprocess.run(['git', '-C', d, 'rev-parse', '--show-toplevel'], capture_output=True, text=True)
        if r.returncode == 0:
            return r.stdout.strip()
    raise Fail('not inside a git repository: %s (pass --repo)' % (explicit or start))


def rev(repo, ref):
    return gits(repo, 'rev-parse', '--verify', '--quiet', ref + '^{commit}', ok=(0, 1, 128)).strip()


FORGE = re.compile(r'(?:(?:https?|ssh|git)://(?:[^@/\s]+@)?([^/:\s]+)(?::\d+)?/+|(?:[^@/\s]+@)?([^/:\s]+):/*)'
                   r'([^/\s]+)/([^/\s]+?)(?:\.git)?/*$')


def forge_url(remote):
    """A GitHub remote (https, ssh://[:port], scp-style with or without a leading slash) -> https://<host>/<o>/<r>."""
    m = FORGE.match(remote.strip())
    host = m and (m.group(1) or m.group(2)).lower()
    # ponytail: GitHub link formats only (compare, blob#L); a GitLab or Bitbucket origin gets no forge. Add theirs when one shows up.
    if not host or 'github' not in host:
        return None
    return 'https://%s/%s/%s' % ('github.com' if host == 'ssh.github.com' else host, m.group(3), m.group(4))


def blob(repo, rev_, path):
    """Bytes of path at rev, or None when it does not exist there."""
    r = subprocess.run(['git', '-C', repo, 'cat-file', 'blob', '%s:%s' % (rev_, path)], capture_output=True)
    return r.stdout if r.returncode == 0 else None


# ponytail: non-UTF-8 paths and contents are decoded with 'replace'; such a path will not round-trip to git.
def text_lines(data):
    """Bytes -> lines without their EOL (LF or CRLF). A trailing newline adds no empty line."""
    t = data.decode('utf-8', 'replace')
    ls = t.split('\n')
    if ls and ls[-1] == '':
        ls.pop()
    return [x[:-1] if x.endswith('\r') else x for x in ls]


def fid(path):
    return 'f-' + hashlib.sha1(path.encode('utf-8')).hexdigest()[:8]


# ---------- map ----------
def parse_raw(out):
    """git diff --raw -z -M --no-abbrev -> [{path, old_path, status, score, blob}]."""
    t, i, files = out.decode('utf-8', 'replace').split('\0'), 0, []
    while i < len(t):
        if not t[i].startswith(':'):
            i += 1
            continue
        meta = t[i][1:].split(' ')
        st = meta[4]
        p1 = t[i + 1]
        if st[0] in 'RC':
            p2, i = t[i + 2], i + 3
        else:
            p2, i = None, i + 2
        files.append({'path': p2 or p1, 'old_path': p1 if p2 else None, 'status': st[0],
                      'score': int(st[1:]) if st[1:].isdigit() else None, 'submodule': '160000' in meta[:2],
                      'blob': None if set(meta[3]) == {'0'} else meta[3]})
    return files


def parse_numstat(out):
    """git diff --numstat -z -> {path: (add, del)}, (None, None) for binary."""
    t, i, res = out.decode('utf-8', 'replace').split('\0'), 0, {}
    while i < len(t):
        if not t[i]:
            i += 1
            continue
        a, d, p = t[i].split('\t', 2)
        if p == '':                      # rename: the next two tokens are old and new path
            p, i = t[i + 2], i + 3
        else:
            i += 1
        res[p] = (None, None) if a == '-' else (int(a), int(d))
    return res


def check_attr(repo, head, paths):
    """{path: set of set attrs} for linguist-generated / linguist-vendored."""
    if not paths:
        return {}
    data = '\0'.join(paths).encode('utf-8', 'replace') + b'\0'
    args = ['check-attr', '-z', '--stdin', 'linguist-generated', 'linguist-vendored']
    try:
        out = git(repo, *(args[:1] + ['--source', head] + args[1:]), data=data)
    except Fail:
        # ponytail: git < 2.40 has no --source, so .gitattributes come from the working tree, not head
        out = git(repo, *args, data=data)
    t, res = out.decode('utf-8', 'replace').split('\0'), {}
    for k in range(0, len(t) - 2, 3):
        if t[k + 2] not in ('unspecified', 'unset', 'false'):
            res.setdefault(t[k], set()).add(t[k + 1])
    return res


def heads5(repo, shas):
    """{blob sha: first 5 lines as text} via one cat-file --batch."""
    # ponytail: reads whole blobs to see 5 lines; fine for normal PRs, slow on gigabyte-sized generated files
    if not shas:
        return {}
    out, res, i = git(repo, 'cat-file', '--batch', data=''.join(s + '\n' for s in shas).encode()), {}, 0
    while i < len(out):
        j = out.index(b'\n', i)
        hdr = out[i:j].decode().split()
        if len(hdr) < 3:                  # '<sha> missing'
            i = j + 1
            continue
        size = int(hdr[2])
        body = out[j + 1:j + 1 + size]
        res[hdr[0]] = '\n'.join(body.decode('utf-8', 'replace').split('\n')[:5])
        i = j + 1 + size + 1
    return res


def path_kind(p):
    """(kind, reason): a reason means the path alone puts the file in the skip tier."""
    segs = p.split('/')
    dirs, base = segs[:-1], segs[-1]
    if '.ai' in dirs:
        return 'docs', 'pipeline artifact: read as a why-source, not explained'
    if 'vendor' in dirs or 'node_modules' in dirs:
        return 'vendor', 'vendored'
    if base in LOCKFILES:
        return 'generated', 'lockfile'
    if re.search(r'\.min\.(js|css)$|\.map$', base):
        return 'generated', 'minified or source map'
    if '__snapshots__' in dirs or base.endswith('.snap'):
        return 'generated', 'snapshot'
    if (any(re.fullmatch(r'tests?', d, re.I) for d in dirs) or base.endswith('Test.php')
            or re.search(r'\.(test|spec)\.\w+$', base)):
        return 'test', ''
    if 'migrations' in dirs:
        return 'migration', ''
    if re.search(r'\.(md|rst|adoc|txt)$', base, re.I) or (dirs and dirs[0] in ('docs', 'doc')):
        return 'docs', ''
    if ('config' in dirs or base.startswith('.env')
            or (re.search(r'\.(ya?ml|json|ini|xml|neon|toml|dist)$', base) and not (dirs and dirs[0] in CODE_DIRS))):
        return 'config', ''
    return 'code', ''


def triage(f, attrs, head5, ws_only):
    """(tier, kind, reason) for one file. Deterministic: the model may only move a file up."""
    kind, why = path_kind(f['path'])
    if why:
        return 'skip', kind, why
    if 'linguist-vendored' in attrs:
        return 'skip', 'vendor', 'vendored'
    if 'linguist-generated' in attrs:
        return 'skip', 'generated', 'linguist-generated'
    if head5 and re.search(r'@generated|DO NOT EDIT', head5):
        return 'skip', 'generated', 'generated marker in the first 5 lines'
    if f['status'] == 'D':   # deleted behaviour is read: the chapter says where it went
        return ('read', kind, 'deleted: say where the behaviour went') if kind in ('code', 'test') else ('verify', kind, 'deleted file')
    if f['submodule']:
        return 'verify', kind, 'submodule pointer'
    if f['binary']:
        return 'verify', kind, 'binary'
    if f['status'] == 'R' and f['score'] == 100 and f['add'] == f['del'] == 0:
        return 'verify', kind, 'pure rename'
    if ws_only and not INDENTED.search(f['path']):
        return 'verify', kind, 'whitespace-only'
    if f['add'] == f['del'] == 0:
        return 'verify', kind, 'empty new file' if f['status'] == 'A' else 'mode or type change only'
    return 'read', kind, ''


def near_moves(files):
    """An added file whose basename matches a deleted one gets pred: the deleted paths (candidates, not chosen)."""
    # ponytail: basename match only, no similarity score; add a difflib ratio when candidates get ambiguous.
    gone, name = {}, lambda f: f['path'].rsplit('/', 1)[-1]
    for f in files:
        if f['status'] == 'D':
            gone.setdefault(name(f), []).append(f['path'])
    for f in files:
        if f['status'] == 'A' and name(f) in gone:
            f['pred'] = gone[name(f)]


def make_map(repo, base, head='HEAD', intent_only=False):
    head_sha, base_tip = rev(repo, head), rev(repo, base)
    if not head_sha or not base_tip:
        raise Fail('cannot resolve %s' % (head if not head_sha else base))
    mb = gits(repo, 'merge-base', base_tip, head_sha).strip()
    if not mb:
        raise Fail('no merge base between %s and %s' % (base, head))
    if head == 'HEAD':     # a named ref keeps its meaning after a checkout; detached: the SHA
        head = gits(repo, 'symbolic-ref', '-q', '--short', 'HEAD', ok=(0, 1)).strip() or head_sha
    common = ['diff', '-z', RENAMES, '--no-color', '--no-ext-diff', '--no-textconv', mb, head_sha]
    num = parse_numstat(git(repo, *common[:1] + ['--numstat'] + common[1:])) if mb != head_sha else {}
    note = None
    if intent_only or mb == head_sha:     # no code yet: the page covers what was asked
        note = ('intent-only: no commits past the merge base' if mb == head_sha else
                'intent-only: %d changed files at head are not explained' % len(num))
        files, ws = [], {}
    else:
        files = parse_raw(git(repo, *common[:1] + ['--raw', '--no-abbrev'] + common[1:]))
        ws = parse_numstat(git(repo, *common[:1] + ['--numstat', '-w'] + common[1:]))
    for f in files:
        f['add'], f['del'] = num.get(f['path'], (0, 0))
        f['binary'] = f['add'] is None
    near_moves(files)
    attrs = check_attr(repo, head_sha, [f['path'] for f in files])
    h5 = heads5(repo, sorted({f['blob'] for f in files if f['blob'] and not f['binary']}))
    tot = {'files': 0, 'add': 0, 'del': 0, 'by_tier': {t: {'files': 0, 'add': 0, 'del': 0} for t in TIERS}}
    for f in sorted(files, key=lambda f: f['path']):
        ws_only = not f['binary'] and (f['add'] or f['del']) and ws.get(f['path'], (0, 0)) == (0, 0)
        f['tier'], f['kind'], f['reason'] = triage(f, attrs.get(f['path'], ()), h5.get(f['blob']), ws_only)
        f['id'] = fid(f['path'])
        for k in (tot, tot['by_tier'][f['tier']]):
            k['files'] += 1
            k['add'] += f['add'] or 0
            k['del'] += f['del'] or 0
    r = subprocess.run(['git', '-C', repo, 'remote', 'get-url', 'origin'], capture_output=True, text=True)
    forge = forge_url(r.stdout) if r.returncode == 0 else None
    name = forge.split('/', 3)[3] if forge else os.path.basename(repo)
    order = ['id', 'path', 'old_path', 'status', 'score', 'add', 'del', 'binary', 'tier', 'kind', 'reason', 'blob', 'pred']
    res = {'generated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
           'repo': name, 'forge': forge, 'base_ref': base, 'head_ref': head,
           'base_tip': base_tip, 'merge_base': mb, 'head': head_sha, 'intent_only': note is not None, 'totals': tot,
           'files': [{k: f[k] for k in order if k in f} for f in sorted(files, key=lambda f: f['path'])]}
    if note:
        res['note'] = note
    return res


# ---------- the Asked layer: ids, the contract version, the storyboard ----------
CRITERIA = (('R<n>.<x>', r'\bR\d+\.[a-z0-9]+\b'), ('AC<n>', r'\bAC\d+\b'), ('R<n>', r'\bR\d+\b'))
VERSION_LINE = r'(?m)^[ \t]*>[ \t]*-[ \t]*(v\d+(?:\.\d+)*)[ \t]+\S+[ \t]+(\w+)'
SB_URL = re.compile(r'https://claude\.ai/[\w./-]+')
SB_HEADER = re.compile(r'(?m)^>[ \t]*Built from:[ \t]*(.+?)[ \t]*$')


def criteria(t):
    """prd.md text -> (format, ids in natural order): the first of R<n>.<x>, AC<n>, R<n> that occurs. Ids only in
    HTML comments or in the > Versions: lines are history, not the ask."""
    t = re.sub(r'(?m)^[ \t]*>[ \t]*-[ \t]*v\d.*$', '', re.sub(r'(?s)<!--.*?-->', '', t))
    for label, rx in CRITERIA:
        ids = sorted(set(re.findall(rx, t)), key=lambda i: [int(x) if x.isdigit() else x for x in re.split(r'(\d+)', i)])
        if ids:
            return label, ids
    return None, []


def contract_of(t):
    """prd.md text -> {version, status} or None (no > Versions: lines). The version is the highest number, never the
    newest date; the status is the first word of > Status:, else that line's word."""
    vs = re.findall(VERSION_LINE, t)
    if not vs:
        return None
    ver, word = max(vs, key=lambda v: tuple(int(x) for x in v[0][1:].split('.')))
    st = re.search(r'(?m)^[ \t]*>[ \t]*Status:[ \t]*(\w+)', t)
    return {'version': ver, 'status': st.group(1) if st else word.capitalize()}


def storyboard_of(t):
    """prototype/artifact.md text -> {url, built_from}: the **URL:** line (claude.ai only, else None) and the Built
    from cell of the table's last (newest) row, else the > Built from: line."""
    u = re.search(r'\*\*URL:\*\*\s*(%s)' % SB_URL.pattern, t)
    rows = [[c.strip() for c in ln.strip().strip('|').split('|')] for ln in t.splitlines() if ln.lstrip().startswith('|')]
    hdr = next((r for r in rows if 'Built from' in r), None)
    body = [r for r in rows[rows.index(hdr) + 1:] if not re.fullmatch(r'[-: ]*', ''.join(r))] if hdr else []
    k = hdr.index('Built from') if hdr else 0
    bf = body[-1][k] if body and len(body[-1]) > k else None
    if not bf:
        mo = SB_HEADER.search(t)
        bf = mo and mo.group(1)
    return {'url': u.group(1) if u else None, 'built_from': bf}


def read_text(p):
    with open(p, encoding='utf-8', errors='replace') as fh:
        return fh.read()


def asked_facts(m, repo, tdirs):
    """Fill map.json sources_found, contract and criteria from the ticket dirs; -> the echo lines."""
    m['sources_found'], m['contract'], m['criteria'], prd, sb = [], None, [], None, None
    for td in tdirs:
        ls = sorted(os.listdir(td)) if os.path.isdir(td) else []
        names = [n for n in WHY_SOURCES if os.path.isfile(os.path.join(td, n))]
        names += [n for n in ls if (ASK_SRC.fullmatch(n) or BUG_NOTES.fullmatch(n)) and n not in names and os.path.isfile(os.path.join(td, n))]
        inv = os.path.join(td, 'investigation')
        names += ['investigation/' + n for n in (sorted(os.listdir(inv)) if os.path.isdir(inv) else [])
                  if n.endswith('.md') and not re.search(r'(?i)panel|persona|simulated', n) and os.path.isfile(os.path.join(inv, n))]
        m['sources_found'] += [os.path.relpath(os.path.join(td, n), repo).replace(os.sep, '/') for n in names]
        prd = prd or ('prd.md' in names and os.path.join(td, 'prd.md'))
        sb = sb or ('prototype/artifact.md' in names and os.path.join(td, 'prototype', 'artifact.md'))
    out = ['sources: %s' % (', '.join(m['sources_found']) or 'none in %s' % ', '.join(tdirs))]
    if prd:
        t = read_text(prd)
        label, m['criteria'] = criteria(t)
        m['contract'] = contract_of(t)
        c = m['contract']
        out.append('asked: %s · %d criteria%s' % ('contract %s (%s)' % (c['version'], c['status']) if c else 'no contract versions',
                                                 len(m['criteria']), ' (%s)' % label if label else ''))
    elif not any(os.path.basename(s) in ASKED for s in m['sources_found']):
        notes = list(dict.fromkeys(re.sub(r'/investigation/.*', '/investigation/', s) for s in m['sources_found']
                                   if BUG_NOTES.fullmatch(os.path.basename(s)) or '/investigation/' in '/' + s))
        out.append('asked: no prd.md, workflows.md or investigation.md (contract null, criteria []): %s' % (
            'the ask is in the ticket\'s own notes, %s: their numbered fix steps are goal.<slug> rows, their out-of-scope '
            'list not_in_change' % ', '.join(notes) if notes else 'the ask is in the PR body, Jira or commits'))
    if sb:
        s = storyboard_of(read_text(sb))
        if m.get('contract'):
            m['contract']['storyboard'] = s
        out.append('storyboard: built from %s · %s' % (s['built_from'] or '?', s['url'] or 'no claude.ai URL'))
    return out


def cmd_map(a):
    repo = find_repo(a.out, a.repo)
    m = make_map(repo, a.base, a.head, a.intent_only)
    if not m['files'] and not m['intent_only']:
        print('map: nothing to explain: %s..%s has no changes' % (m['merge_base'][:7], m['head'][:7]))
        return 0
    echo = asked_facts(m, repo, [os.path.abspath(t) for t in a.ticket_dir or [os.path.join(a.out, '..')]])
    new, gi = not os.path.isdir(a.out), os.path.join(a.out, '.gitignore')
    if new:
        os.makedirs(a.out)
    # ponytail: an existing dir gets one only under .ai/, so a bare --out . never ignores a whole repo
    if not os.path.exists(gi) and (new or '.ai' in os.path.abspath(a.out).split(os.sep)):
        with open(gi, 'w') as fh:
            fh.write('*\n')
    if not gits(repo, 'rev-parse', '--symbolic-full-name', m['head_ref'], ok=(0, 128)).strip():
        print("map: warning: %s is no named ref (detached): --stale can't track it" % m['head_ref'], file=sys.stderr)
    p = os.path.join(a.out, 'map.json')
    with open(p, 'w', encoding='utf-8') as fh:
        json.dump(m, fh, indent=1, ensure_ascii=False)
        fh.write('\n')
    t = m['totals']
    print('map: %s  %s..%s  %s' % (p, m['merge_base'][:7], m['head'][:7], m.get('note') or '%d files  +%d -%d' % (t['files'], t['add'], t['del'])))
    for k in TIERS if not m['intent_only'] else ():
        b = t['by_tier'][k]
        print('  %-6s %4d files  +%d -%d' % (k, b['files'], b['add'], b['del']))
    for x in echo:
        print('  ' + x)
    return 0


# ---------- build: shared with check-explainer.py ----------
MORE = '<!--more-->'      # in a main-flow piece's fragment: the visible note ends here; the rest opens under "More on this"
MARKER = re.compile(r'<pre\b([^>]*?\bdata-(?:hunk|code)\s*=\s*"[^"]*"[^>]*)>\s*</pre>', re.I)
ATTR = re.compile(r'([\w:-]+)\s*=\s*"([^"]*)"')
REFSPAN = re.compile(r'<span\b([^>]*?\bdata-ref\s*=\s*"([^"]*)"[^>]*)>(.*?)</span>', re.S | re.I)
SPEC = re.compile(r'^(.+?)(@base|@head)?:(\d+)(?:-(\d+))?$')
HUNK = re.compile(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@')
LANG = {'php': ('PHP', 'php'), 'js': ('JavaScript', 'javascript'), 'mjs': ('JavaScript', 'javascript'),
        'ts': ('TypeScript', 'typescript'), 'tsx': ('TSX', 'tsx'), 'jsx': ('JSX', 'jsx'), 'py': ('Python', 'python'),
        'sql': ('SQL', 'sql'), 'json': ('JSON', 'json'), 'yml': ('YAML', 'yaml'), 'yaml': ('YAML', 'yaml'),
        'xml': ('XML', 'markup'), 'html': ('HTML', 'markup'), 'twig': ('Twig', 'twig'), 'css': ('CSS', 'css'),
        'scss': ('SCSS', 'scss'), 'sh': ('Shell', 'bash'), 'graphql': ('GraphQL', 'graphql'),
        'gql': ('GraphQL', 'graphql'), 'md': ('Markdown', 'markdown'), 'neon': ('NEON', 'yaml'), 'ini': ('INI', 'ini')}
RISK = {'none': 0, 'low': 1, 'med': 2, 'high': 3}
REF_KIND = [(r'file:', 'Code'), (r'R\d+\.[a-z0-9]+$|AC\d+$', 'Criterion'), (r'R\d+$', 'Requirement'), (r'D\d', 'Decision'),
            (r'T\d', 'Plan task'), (r'Q\d', 'Assumption'), (r'A\d', 'Acceptance'), (r'FB\d', 'Ruling'),
            (r's\d+\.\d', 'Workflow step'), (r's\d+$', 'Use case'), (r'spec\.', 'Test scenario'), (r'ng\.', 'Non-goal'),
            (r'goal\.', 'Goal'), (r'pr(\.|$)', 'PR body'), (r'jira(\.|$)', 'Jira')]
STATES = {'drift': 'Drift', 'not-built': 'Not built', 'untested': 'Built, no test', 'built': 'Built, test not run',
          'tested': 'Tested', 'deferred': 'Deferred', 'non-goal': 'Non-goal'}     # in sort order: gaps first
STAGES = ('intent-only', 'full', 'reviewer')     # the checker validates plan.stage against these
PIPE_ID = r'(?:R\d+(?:\.[a-z0-9]+)?|AC\d+|FB\d+|Q\d+|D\d+|T\d+|s\d+\.\d+)'     # the ids a reader meets again (trace, storyboard)
OQ_AT = re.compile(r'^\s*\((ch-[a-z0-9-]+|asked|background|intuition|proven)\)\s*')   # an open question's "(ch-2) " prefix


def attrs_of(tag_inner):
    return {k.lower(): html.unescape(v) for k, v in ATTR.findall(tag_inner)}


def ref_id(rid):
    return 'ref-' + re.sub(r'[^a-z0-9]+', '-', rid.lower()).strip('-')


def ref_kind(rid):
    return next((k for rx, k in REF_KIND if re.match(rx, rid)), 'Source')


def stage_of(plan, m):
    return plan.get('stage') or ('intent-only' if m.get('intent_only') else 'reviewer' if plan.get('mode') == 'reviewer' else 'full')


def find_file(repo, d, s):
    """A source or ref path: absolute, else under the repo, the explainer dir or its parent; None when absent."""
    cands = [s] if os.path.isabs(s) else [os.path.join(b, s) for b in (repo, d, os.path.dirname(d))]
    return next((c for c in cands if os.path.isfile(c)), None)


def source_hashes(repo, d, sources):
    """{basename: hash8} per existing source, in plan order: sha256 without CR = tr -d '\\r' < f | sha256sum | cut -c1-8."""
    out = {}
    for s in sources:
        p = find_file(repo, d, s)
        if p:
            k = os.path.basename(s)
            with open(p, 'rb') as fh:            # a second source with the same basename keys on its plan path
                out[k if k not in out else s] = hashlib.sha256(fh.read().replace(b'\r', b'')).hexdigest()[:8]
    return out


def online_sources(repo, d, plan):
    """How many plan.json sources a reader can open online: a ref quotes the file (src) and its origin has a url."""
    def at(s):
        p = find_file(repo, d, s)
        return os.path.realpath(p) if p else None
    origins = plan.get('origins') if isinstance(plan.get('origins'), dict) else {}
    on = {at(r['src']) for r in (plan.get('refs') or {}).values()
          if isinstance(r, dict) and r.get('src') and (origins.get(r.get('origin')) or {}).get('url')} - {None}
    return sum(1 for s in plan.get('sources') or [] if at(s) in on)


def inline(t):
    """Plan/quiz text -> HTML: escaped, `code` -> <code>, **bold** -> <strong>."""
    out = []
    for i, part in enumerate(re.split(r'`([^`]*)`', t or '')):
        e = html.escape(part)
        if not i % 2:   # [name](#ch-2) cites a piece (becomes badge + name); [words](#asked) links any section the page renders
            e = re.sub(r'\[([^\]]+)\]\(#(ch-[a-z0-9-]+)\)', r'<a href="#\2" data-p>\1</a>', e)
            e = re.sub(r'\[([^\]]+)\]\(#([a-z][a-z0-9-]*)\)', r'<a href="#\2">\1</a>', e)
        out.append('<code>%s</code>' % e if i % 2 else re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', e))
    return ''.join(out)


def prose_words(markup):
    """Words a reader meets without opening anything: not inside <pre> (code) or <details> (closed toggles), no chips."""
    keep, depth = [], 0
    for tok in re.split(r'(?i)(</?(?:details|pre)\b[^>]*>)', markup or ''):
        if re.match(r'(?i)<(details|pre)\b', tok):
            depth += 1
        elif re.match(r'(?i)</(details|pre)\b', tok):
            depth = max(depth - 1, 0)
        elif not depth:
            keep.append(tok)
    return len(html.unescape(re.sub(r'<[^>]+>', ' ', REFSPAN.sub(' ', ''.join(keep)))).split())


def minutes(words):
    return max(1, -(-words // 200))


def must_path(plan, frags, chapters, overview):
    """The must path, [(section id, label, words)]: the overview (rendered), What was asked, the Intuition and the
    main-flow pieces (fragment + gist). Not used by the build: check-explainer.py reports it as information."""
    out = [('overview', 'Overview', prose_words(overview))]
    out += [(k, t, prose_words(frags[k])) for k, t in (('asked', 'What was asked'), ('intuition', 'Intuition')) if k in frags]
    for i, c in enumerate(chapters):
        if c.get('read', 'must') == 'must':
            out.append((c.get('id'), 'piece %d' % (i + 1),
                        prose_words(frags.get(c.get('id')) or '') + len(str(c.get('gist') or c.get('why_here') or '').split())))
    return out


def assign(plan, files):
    """({path: [owner, ...]}, [(owner, glob) matching nothing]). Owners: chapter ids and 'ch-mech:<n>'."""
    owners, dead = {f['path']: [] for f in files}, []
    groups = [(c.get('id'), c.get('files') or []) for c in plan.get('chapters') or []]
    groups += [('ch-mech:%d' % (i + 1), g.get('files') or []) for i, g in enumerate(plan.get('mechanical') or [])]
    for label, globs in groups:
        for g in globs:
            hit = [p for p in owners if p == g or fnmatch.fnmatchcase(p, g)]
            if not hit:
                dead.append((label, g))
            for p in hit:
                if label not in owners[p]:
                    owners[p].append(label)
    return owners, dead


def quiz_order(plan, quiz):
    """Questions in page order: each chapter's checkpoints (final: false), then the final quiz."""
    qs = list((quiz or {}).get('questions') or [])
    out = []
    for c in plan.get('chapters') or []:
        out += [q for q in qs if not q.get('final') and q.get('chapter') == c.get('id')]
    out += [q for q in qs if q.get('final')]
    return out + [q for q in qs if not any(q is o for o in out)]   # stray checkpoints: last, so none is lost


def clip(h, side, lo, hi):
    """(header, lines) of hunk h cut to the lines whose side line number is in lo..hi; a cut hunk gets a recounted
    header that says so. An added file is one hunk: without this, every marker on it embeds the whole file."""
    b, n, out, keep = h['bs'], h['hs'], [], False
    first = None
    for x in h['lines']:
        if x[0] != '\\':                        # "\ No newline" follows the line before it
            keep = lo <= (b if side == 'base' else n) <= hi
        if keep:
            first = first or (b, n)
            out.append(x)
        b += x[0] in ' -'
        n += x[0] in ' +'
    if not out or len(out) == len(h['lines']):
        return h['hdr'], h['lines']
    return '@@ -%d,%d +%d,%d @@ clipped' % (first[0], sum(x[0] in ' -' for x in out), first[1],
                                             sum(x[0] in ' +' for x in out)), out


class Src:
    """Lines, hunks, links and code figures for one map.json."""

    def __init__(self, repo, m):
        self.repo, self.m = repo, m
        self.files = {f['path']: f for f in m['files']}
        self.cache, self.ids, self.first, self.figs = {}, set(), {}, {}    # figs: {path: [(start, end, id)]} at head
        self.diff_lines = 0

    def lines(self, path, side='head'):
        k = (side, path)
        if k not in self.cache:
            data = blob(self.repo, self.m['head'] if side == 'head' else self.m['merge_base'], path)
            self.cache[k] = None if data is None or b'\0' in data[:8000] else text_lines(data)
        return self.cache[k]

    def hunks(self, path):
        k = ('hunks', path)
        if k not in self.cache:
            f = self.files[path]
            out = git(self.repo, 'diff', '-U3', RENAMES, '--no-color', '--no-ext-diff', '--no-textconv',
                      self.m['merge_base'], self.m['head'], '--', *([f['old_path'], path] if f['old_path'] else [path]))
            hs, cur = [], None
            for ln in text_lines(out):
                h = HUNK.match(ln)
                if h:
                    cur = {'hdr': ln, 'bs': int(h.group(1)), 'bn': int(h.group(2) or 1),
                           'hs': int(h.group(3)), 'hn': int(h.group(4) or 1), 'lines': []}
                    hs.append(cur)
                elif cur is not None and ln and ln[0] in ' +-\\':
                    cur['lines'].append(ln)
            self.cache[k] = hs
        return self.cache[k]

    def compare(self, path):
        """The forge compare view anchored on path (GitHub: #diff-<sha256(path)>), or None without a forge."""
        fg = self.m.get('forge')
        return fg and '%s/compare/%s...%s#diff-%s' % (fg, self.m['merge_base'], self.m['head'],
                                                     hashlib.sha256(path.encode()).hexdigest())

    def link(self, path, side, s, e, diff=False):
        """The forge URL of path's lines, or None without a forge (the caller renders plain text)."""
        fg = self.m.get('forge')
        if not fg:
            return None
        if diff:
            return '%s%s%d' % (self.compare(path), 'L' if side == 'base' else 'R', s)
        return '%s/blob/%s/%s#L%d-L%d' % (fg, self.m['head'] if side == 'head' else self.m['merge_base'], quote(path), s, e)

    def resolve(self, a, register=True):
        """a: marker attributes. -> (figure html or None, lines embedded, error or None). register=False: a Files-row
        diff, which no file ref or Files link should point at."""
        kind = 'hunk' if 'data-hunk' in a else 'code'
        spec = a.get('data-' + kind, '')
        m = SPEC.match(spec)
        if not m:
            return None, 0, 'data-%s="%s": want PATH:START-END' % (kind, spec)
        path, s = m.group(1), int(m.group(3))
        e, side = int(m.group(4) or s), (m.group(2) or '@head')[1:]
        f = self.files.get(path)
        if kind == 'hunk':
            if m.group(2):
                return None, 0, 'data-hunk="%s": @side is for data-code' % spec
            if not f:
                return None, 0, 'data-hunk="%s": %s is not in the diff' % (spec, path)
            if f['binary']:
                return None, 0, 'data-hunk="%s": binary file, no hunks' % spec
            side = 'base' if f['status'] == 'D' else 'head'   # a deleted file has no head side: its range is base lines
        elif side == 'base' and f and f['old_path']:
            path = f['old_path']                              # a renamed file's base lines live at its old path
        ls = self.lines(path, side)
        if ls is None:
            return None, 0, '%s="%s": %s does not exist at %s (or is binary)' % ('data-' + kind, spec, path, side)
        if not 1 <= s <= e <= len(ls):
            return None, 0, '%s="%s": outside the file (%d lines at %s)' % ('data-' + kind, spec, len(ls), side)
        ext = path.rsplit('.', 1)[-1].lower() if '.' in path.rsplit('/', 1)[-1] else ''
        lang, prism = LANG.get(ext, ('', ''))
        if kind == 'hunk':
            key = 'hs' if side == 'head' else 'bs'
            sel = [h for h in self.hunks(path)
                   if s <= h[key] + max(h['hn' if side == 'head' else 'bn'], 1) - 1 and h[key] <= e]
            if not sel:
                return None, 0, 'data-hunk="%s": overlaps no hunk' % spec
            body, lns = [], []                # lns: each rendered line's number on `side` (None: a header or the other side)
            for h in sel:
                hdr, ls_ = clip(h, side, s - 3, e + 3)
                hm = HUNK.match(hdr)
                b_, n_ = int(hm.group(1)), int(hm.group(3))
                body.append(('hd', hdr))
                lns.append(None)
                for x in ls_:
                    body.append(({'+': 'add', '-': 'del'}.get(x[0], 'ctx'), x))
                    mine = x[0] in (' -' if side == 'base' else ' +')
                    lns.append((b_ if side == 'base' else n_) if mine else None)
                    b_ += x[0] in ' -'
                    n_ += x[0] in ' +'
            add, dele = sum(k == 'add' for k, _ in body), sum(k == 'del' for k, _ in body)
            code = '<code class="language-diff%s diff-highlight">%s</code>' % (
                '-' + prism if prism else '', ''.join('<span class="l %s">%s\n</span>' % (k, html.escape(t)) for k, t in body))
            stat = ' <span class="stat"><span class="plus">+%d</span> <span class="minus">−%d</span></span>' % (add, dele)
            href, dside, n = self.link(path, side, s, e, True), 'diff', len(body)
            self.diff_lines += n
        else:
            body = ls[s - 1:e]
            code = '<code class="language-%s">%s</code>' % (prism or 'none', html.escape('\n'.join(body)))
            stat, href, dside, n = '', self.link(path, side, s, e), side, len(body)
            lns = list(range(s, e + 1))
        fig = 'h-%s-%d' % (fid(path)[2:], s)
        k = 2
        while fig in self.ids:
            fig, k = 'h-%s-%d-%d' % (fid(path)[2:], s, k), k + 1
        self.ids.add(fig)
        if register:
            self.first.setdefault(path, fig)
        if register and (kind == 'hunk' or side == 'head'):          # an @base excerpt counts lines on the other side
            self.figs.setdefault(path, []).append((s, e, fig))
        notes = []                                    # data-notes="LINE:text|LINE:text", each tied to a rendered line
        for k_, part in enumerate(x for x in (a.get('data-notes') or '').split('|') if x.strip()):
            mo = re.match(r'\s*(\d+)\s*:\s*(.+)', part, re.S)
            if not mo or int(mo.group(1)) not in lns:
                return None, 0, 'data-notes on %s: %r is not LINE:text on a shown line' % (spec, part)
            notes.append((lns.index(int(mo.group(1))), int(mo.group(1)), mo.group(2).strip()))
        pre = '<pre>%s%s</pre>' % (code, ''.join('<i class="lmark" style="--i:%d" aria-hidden="true">%d</i>' % (i, k_ + 1)
                                                  for k_, (i, _, _) in enumerate(notes)))
        if n > 30:
            pre = '<details class="toggle more"><summary>Show %d lines</summary>%s</details>' % (n, pre)
        dr, _, bn = path.rpartition('/')             # the folder muted, the file bold; a line breaks only after a slash
        loc = '%s<b>%s</b> lines %d–%d' % ('<span class="dir">%s/<wbr></span>' % html.escape(dr).replace('/', '/<wbr>') if dr else '',
                                    html.escape(bn), s, e)
        # the caption's file name opens the file in All N files (not in a file's own diff); GitHub is its own link, new tab
        inpage = register and f is not None
        cap = '%s%s%s%s%s <button type="button" class="copy" title="Copy this code">Copy</button>' % (
            '<a class="ref file loc" href="#%s" title="Open %s in All %d files">%s</a>' % (f['id'], html.escape(bn), len(self.files), loc)
            if inpage else '<span class="loc">%s</span>' % loc,
            ' <a class="gh" href="%s" target="_blank" rel="noopener" title="Open these lines on GitHub, in a new tab">GitHub ↗</a>' % html.escape(href) if href else '',
            ' <span class="note">%s</span>' % html.escape(a['data-note']) if a.get('data-note') else '',
            ' <span class="lang">%s</span>' % lang if lang else '', stat)
        out = '<figure class="code" id="%s" data-side="%s"><figcaption>%s</figcaption>%s</figure>' % (fig, dside, cap, pre)
        if notes:
            out = '<div class="noted"><ol class="lnotes">%s</ol>%s</div>' % (''.join(
                '<li style="--i:%d" title="line %d">%s</li>' % (i, ln, inline(t)) for i, ln, t in notes), out)
        return out, n, None

    def file_ref(self, rid):
        """'file:PATH:LINE[-END]' -> (path, start, end, [lines]) or an error string."""
        m = SPEC.match(rid[5:])
        if not m or m.group(2):
            return 'want file:PATH:LINE'
        path, s = m.group(1), int(m.group(3))
        e, ls = int(m.group(4) or s), self.lines(m.group(1))
        if ls is None:
            return '%s does not exist at head' % path
        if not 1 <= s <= e <= len(ls):
            return '%s:%d-%d is outside the file (%d lines at head)' % (path, s, e, len(ls))
        return path, s, e, ls[s - 1:min(e, s + 4)]


def files_list(src, paths, reasons=False):
    out = []
    for p in paths:
        f = src.files[p]
        out.append('<li><a class="ref file" href="#%s">%s</a> %s%s</li>' % (
            f['id'], html.escape(p), pm(f), ' · ' + html.escape(f['reason']) if reasons and f['reason'] else ''))
    return '<ul class="flist">%s</ul>' % ''.join(out)


def pm(f):
    if f.get('binary'):
        return '<span class="plus">bin</span>'
    return '<span class="plus">+%d</span> <span class="minus">−%d</span>' % (f['add'] or 0, f['del'] or 0)


def fieldset(q):
    """Stem and options only, in the authored order: the key, feedback, chapter and evidence stay in xd-data."""
    opts = ''.join('<button type="button" class="opt" data-i="%d">%s</button>' % (i, inline(o))
                   for i, o in enumerate(q.get('options') or []))
    qid = html.escape(str(q.get('id')))
    return ('<fieldset class="q" id="%s"><legend><span class="qn">%s</span> %s</legend><div class="opts">%s</div></fieldset>'
            % (qid, qid, inline(q.get('stem')), opts))


def read_json(d, name, need=True):
    p = os.path.join(d, name)
    if not os.path.exists(p):
        if need:
            raise Fail('%s not found' % p)
        return None
    try:
        with open(p, encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError) as e:
        raise Fail('%s: %s' % (p, e))


def read_frags(d):
    fd, res = os.path.join(d, 'fragments'), {}
    if os.path.isdir(fd):
        for n in sorted(os.listdir(fd)):
            if n.endswith('.html'):
                with open(os.path.join(fd, n), encoding='utf-8') as fh:
                    res[n[:-5]] = fh.read()
    return res


def inputs_hash(m, plan, quiz, frags):
    """What the page was built from, as check-explainer.py re-reads it: a changed input means a stale page."""
    return hashlib.sha256(json.dumps([m, plan, quiz, frags], sort_keys=True).encode()).hexdigest()[:12]


FILTER_AT = 20     # GitHub's rule of thumb: file-filter UI (tree box, table search and filters) only above ~20 files
VIEWED_TIP = 'Marks the file as looked at, to track your progress. It stays in this browser and is sent nowhere.'
ST_NAME = {'A': 'added', 'D': 'deleted', 'R': 'renamed'}      # anything else (M, C, T) reads as modified
# the heading of each section a Go deeper row can hold (a row's default summary; Sources' "Cited in" names)
TITLES = {'asked': 'What was asked', 'background': 'Background', 'intuition': 'Intuition', 'proven': "How it's proven",
          'problem': 'The problem, and what happens now', 'trace': 'The goals and their state', 'look': 'Where to look hardest',
          'drift': 'Where the code differs from earlier plans', 'ops': 'Deploy and merge notes', 'ch-mech': 'Generated files',
          'carry': 'To carry into the review'}
# the Sources groups, in this order, then any other authored group, then the Glossary
SRC_GROUPS = ('Jira', 'GitHub', 'Shared pages', 'From the author')
# a path only the page builder's checkout has: never shown on the page (not in text, a title or aria)
LOCAL = re.compile(r'(?:^|/)\.(?:ai|tasks)/|^(?:explainer|review|sources)/|^(?:/|~|[A-Za-z]:[\\/])')
CARRY_TIP = {'inherits': 'Other code gets this behaviour too', 'bypasses': 'A path that goes around the change',     # each carry tag's meaning
             'ask': 'A question for the author', 'not here': 'Not part of this change', 'data': 'Existing data the change leaves as it is'}


def dstat(a, d):
    """GitHub's 5-square diffstat: one square a line up to 5 lines, else shares of 5 (each side that changed keeps one)."""
    t = a + d
    g = a if t <= 5 else min(4, max(1, round(5 * a / t))) if a and d else 5 * bool(a)
    r = d if t <= 5 else 5 - g
    return '<span class="dst" aria-hidden="true">%s</span>' % ''.join('<i class="%s"></i>' % c for c in 'a' * g + 'd' * r + 'n' * (5 - g - r))


def file_tree(files, piece_cell, owners, reg, total, filter_at):
    """GitHub's file tree: folders first, then files, by name; single-child folder chains in one row; each file a link
    to its row in the Files table, its status mark, its piece badges (none for generated files) and a Viewed tick."""
    root = {}
    for f in files:
        node = root
        for part in f['path'].split('/')[:-1]:
            node = node.setdefault(part + '/', {})
        node[f['path'].rsplit('/', 1)[-1]] = [f]      # a file is a list, a folder a dict
    esc = html.escape

    def li(name, x, at, dp):
        if isinstance(x, dict):
            while len(x) == 1 and isinstance(next(iter(x.values())), dict):     # merge a single-child folder chain
                k, x = next(iter(x.items()))
                name += k
            return ('<li class="fo" style="--d:%d"><details open><summary title="%s"><i class="chev" aria-hidden="true"></i>'
                    '<i class="fol" aria-hidden="true"></i><span class="nm">%s</span></summary><ul>%s</ul></details></li>') % (
                dp, esc(at + name), esc(name.rstrip('/')), level(x, at + name, dp + 1))
        x = x[0]
        own = owners[x['path']]
        home = own[0].split(':')[0] if own else ''
        gen = home not in reg
        marks = '<i class="sw" title="generated"></i>' if gen else piece_cell(x['path'], home)     # each badge its own link, beside the file's
        st = ST_NAME.get(x['status'], 'modified')
        return ('<li class="fi" style="--d:%d" data-f="%s" data-path="%s" data-ext="%s"%s><a href="#%s" title="%s · open its diff"><i class="ic" aria-hidden="true"></i>'
                '<span class="nm">%s</span></a><span class="bs">%s</span><span class="vt" role="img" aria-label="viewed" title="viewed">✓</span>'
                '<span class="fst" data-st="%s" role="img" aria-label="%s" title="%s"></span></li>') % (
            dp, x['id'], esc(x['path']), esc(os.path.splitext(name)[1]), ' data-gen' if gen else '', x['id'], esc(x['path']), esc(name),
            marks, x['status'], st, st)

    def level(node, at, dp=1):
        keys = sorted(node, key=lambda k: (not isinstance(node[k], dict), k.lower()))
        return ''.join(li(k, node[k], at, dp) for k in keys)
    fil = ''
    if len(files) > filter_at:
        ext = Counter(os.path.splitext(f['path'].rsplit('/', 1)[-1])[1] for f in files)
        fil = ('<div class="tfil"><input type="search" id="ftree-q" placeholder="Filter files…" autocomplete="off" aria-label="Filter files by name">'
               '<details class="tmenu"><summary>File filter</summary><div class="tmenu-b"><p>File extensions</p>%s'
               '<label><input type="checkbox" id="ftree-hv"> Hide viewed files</label></div></details></div>') % ''.join(
            '<label><input type="checkbox" class="ftree-ext" value="%s" checked> %s (%d)</label>' % (esc(e), esc(e) or 'no extension', n)
            for e, n in sorted(ext.items()))
    # the drawer (below 1100px, where titles are never seen) spells out the marks its rows use; CSS hides it on the desktop sidebar
    sts = {ST_NAME.get(f['status'], 'modified'): f['status'] for f in files}
    leg = ''.join('<span><span class="fst" data-st="%s" aria-hidden="true"></span>%s</span>' % (c, n)
                  for n, c in sorted(sts.items(), key=lambda kv: ['modified', 'added', 'deleted', 'renamed'].index(kv[0])))
    leg += '<span><span class="vt" aria-hidden="true">✓</span>viewed</span>'
    if any(owners[f['path']][0].split(':')[0] not in reg if owners[f['path']] else True for f in files):
        leg += '<span><i class="sw" aria-hidden="true"></i>generated</span>'
    return ('<nav class="ftree" id="ftree" aria-label="Changed files"><div class="ftree-h"><span>Viewed <span id="ftree-v">0</span>/%d file%s</span>'
            '<button type="button" class="tbtn" data-act="tree" title="Hide the file tree; the bar gets a button to show it again">Hide file tree</button></div>'
            '<p class="tleg">%s</p>%s<ul class="tree">%s</ul></nav>') % (total, '' if total == 1 else 's', leg, fil, level(root, ''))


def render(src, plan, quiz, frags, shell, errs, build='', inputs=None, filter_at=FILTER_AT, online=0):
    """Fill the shell. errs collects unresolved markers and refs. build: the page-inputs hash; inputs: source hashes;
    online: how many of those sources a reader can open online."""
    m, inputs = src.m, inputs or {}
    head7, base7 = m['head'][:7], m['merge_base'][:7]
    stage = stage_of(plan, m)
    nocode = stage == 'intent-only'
    files = [] if nocode else m['files']
    owners, _ = assign(plan, files)
    chapters = [] if nocode else plan.get('chapters') or []    # the check names any it finds on an intent-only plan
    for c in chapters:      # both land in attributes unescaped
        if not re.fullmatch(r'ch-[a-z0-9-]+', str(c.get('id'))) or c.get('read', 'must') not in ('must', 'skim'):
            raise Fail('plan.json chapters[] %r: want id ch-[a-z0-9-]+ and read must|skim' % c.get('id'))
    origins = {k: dict(v or {}) for k, v in (plan.get('origins') or {}).items()}
    for k in origins:       # an origin id lands in ids, hrefs and a comment slot
        if not re.fullmatch(r'[A-Za-z0-9_-]+', str(k)):
            raise Fail('plan.json origins %r: want an id of letters, digits, _ and -' % k)
        origins[k]['group'] = origins[k].get('group') or 'Other'
    cnum = {c.get('id'): str(i + 1) for i, c in enumerate(chapters)}
    esc = html.escape

    # One piece registry (number, name, family, depth) behind every badge and every reference to a piece.
    # Family is the badge's colour: a must piece is the change; a skim piece is tests when all its files are tests, else
    # harness. Depth is read: must is the main flow (filled badge), skim sits under Go deeper (hollow badge).
    def family(c):
        if c.get('read', 'must') == 'must':
            return 'change'
        mine = [p for p in owners if c.get('id') in owners[p]]
        return 'tests' if mine and all(src.files[p]['kind'] == 'test' for p in mine) else 'harness'
    reg = {c.get('id'): {'n': i + 1, 'title': str(c.get('title') or ''), 'name': str(c.get('short') or c.get('title') or ''),
                         'fam': family(c), 'deep': c.get('read', 'must') == 'skim'} for i, c in enumerate(chapters)}

    def badge(cid):
        r = reg[cid]
        return '<span class="pb%s" data-fam="%s">%d</span>' % (' deep' if r['deep'] else '', r['fam'], r['n'])

    def pref(cid):      # the one way to cite a piece: badge + its name
        return '<a class="pref" href="#%s" title="Go to %s">%s %s</a>' % (cid, esc(circ(cid) + ' ' + reg[cid]['name']), badge(cid), inline(reg[cid]['name']))

    def circ(cid):      # ② : a piece's number as text (titles, aria-labels); the page shows the badge
        return chr(0x245F + reg[cid]['n'])

    def blink(cid):     # a bare badge that is its own link to its own piece
        return '<a class="pref pbl" href="#%s" title="Go to %s" aria-label="%s">%s</a>' % (
            cid, esc(circ(cid) + ' ' + reg[cid]['name']), esc(circ(cid) + ' ' + reg[cid]['name']), badge(cid))

    def pieces_cited(t):    # inline()'s [name](#ch-2) becomes the piece's badge link
        return re.sub(r'<a href="#(ch-[a-z0-9-]+)" data-p>[^<]*</a>', lambda mo: pref(mo.group(1)) if mo.group(1) in reg else mo.group(0), t)

    def code_label(rid):
        """A file ref's visible name: a test's own description (test('…') on that line), else the file's basename."""
        fr = src.file_ref(rid)
        if not isinstance(fr, str):
            mo = re.search(r'''\b(?:it|test)\(\s*(['"])(.+?)\1''', fr[3][0])
            if mo:
                return esc(mo.group(2))
        return esc(re.sub(r':\d+(?:-\d+)?$', '', rid[5:]).rsplit('/', 1)[-1])
    order = quiz_order(plan, quiz)
    trace = [r for r in plan.get('trace') or [] if isinstance(r, dict)]
    contract = plan.get('contract') if isinstance(plan.get('contract'), dict) else None
    sb = contract.get('storyboard') if contract and isinstance(contract.get('storyboard'), dict) else None
    sb_url = (sb or {}).get('url')
    if sb_url and not SB_URL.fullmatch(str(sb_url)):
        errs.append('plan.json contract.storyboard.url %r: want https://claude.ai/...' % sb_url)
        sb_url = None
    sb_v = re.search(r'contract v\d+(?:\.\d+)*', str((sb or {}).get('built_from') or ''))
    used, cites = {}, {}
    refs = {k: dict(v or {}) for k, v in (plan.get('refs') or {}).items()}
    # origins: where a reader opens a ref (a Jira comment, a GitHub page, a shared page) or whose words it is (no link);
    # a local path never shows
    for rid, r in refs.items():      # a commit is named by what it did: its subject line, never "Commit <sha>"
        if rid.startswith('commit:'):
            full = rev(src.repo, rid[7:])
            if full:
                r['title'] = gits(src.repo, 'log', '-1', '--format=%s', full).strip()
                if m.get('forge') and not r.get('origin'):
                    r['origin'] = 'commit-' + full[:7]
                    origins.setdefault(r['origin'], {'group': 'GitHub', 'label': 'Commit %s: %s' % (full[:7], r['title']),
                                                     'url': '%s/commit/%s' % (m['forge'], full)})
            else:
                errs.append('plan.json refs %s: not a commit in %s' % (rid, src.repo))

    def sb_link(rid):      # rid matches s<n>[.<m>], so it is safe in the attribute
        if not sb_url or not re.fullmatch(r's\d+(?:\.\d+)?', rid):
            return ''
        return ('<a class="sb-link" href="%s#%s" target="_blank" rel="noopener" aria-label="Open %s in the storyboard">↗</a>'
                % (html.escape(sb_url), rid, rid))

    def chip(rid, label, where):
        used.setdefault(rid, where)
        label = label or (code_label(rid) if rid.startswith('file:') else html.escape(rid))
        if rid.startswith('file:'):     # a file opens in All N files; its source entry stays the hover preview
            p = re.sub(r':\d+(?:-\d+)?$', '', rid[5:])
            if p in rows:
                return '<a class="ref file" href="#%s" data-ref="%s" title="Open %s in All %d files">%s</a>' % (
                    fid(p), html.escape(rid), html.escape(p.rsplit('/', 1)[-1]), len(rows), label)
            return '<span class="ref file" data-ref="%s">%s</span>' % (html.escape(rid), label)     # not in the change: a preview, no target
        cites.setdefault(rid, []).append(('cite-%s-%d' % (ref_id(rid)[4:], len(cites[rid]) + 1), where))     # Sources links back here
        o = (refs.get(rid) or {}).get('origin')
        return '<a class="ref" id="%s" href="#%s" data-ref="%s">%s</a>%s' % (
            cites[rid][-1][0], 'src-' + o if o in origins else ref_id(rid), html.escape(rid), label, sb_link(rid))

    def label(rid, text):
        """A fragment chip's text: the author's words; when empty or just the id, what the ref is (a file's basename;
        else its title, a pipeline id muted after it). The preview carries the id, path:line or hash."""
        t, bare = html.unescape(re.sub(r'<[^>]+>', '', text)).strip(), rid.split(':', 1)[-1]
        if t not in ('', rid, bare, bare.rsplit('/', 1)[-1]):
            return text
        if rid.startswith('file:'):
            return html.escape(re.sub(r':\d+(?:-\d+)?$', '', bare).rsplit('/', 1)[-1])
        title = (refs.get(rid) or {}).get('title')
        if not title:
            return text
        return inline(title) + (' <span class="rid">%s</span>' % html.escape(rid) if re.fullmatch(PIPE_ID, rid) else '')

    def chips(items, where):
        out = [pref(x) if x in cnum else chip(x, '', where)
               for x in (str(i) for i in items or [])]
        return ' '.join(out) or '<span class="none">none</span>'

    rows = {f['path'] for f in files}               # the Files rows this page renders (none on intent-only)

    def at_link(at):
        """A hotspot or drift `at`, after its sentence: the file's basename linking the code figure covering its lines,
        else its Files row, else plain text; the full path:lines in the title."""
        mo = SPEC.match(at or '')
        p = mo.group(1) if mo and not mo.group(2) else None
        base = html.escape((mo.group(1) if mo else at or '').rsplit('/', 1)[-1])
        if p not in rows:
            return ' <code>%s</code>' % base if at and not LOCAL.search(at) else ''
        ln = 'lines %s–%s' % (mo.group(3), mo.group(4)) if mo.group(4) else 'line ' + mo.group(3)     # one rule: a file name opens that file
        return ' <a class="ref file" href="#%s" title="Open %s in All %d files (%s)">%s</a>' % (fid(p), base, len(rows), ln, base)

    def frag(name):
        t = frags.get(name)
        return None if t is None else fragtext(name, t)

    def fragtext(name, t):
        def mk(mo):
            h, _, err = src.resolve(attrs_of(mo.group(1)))
            if err:
                errs.append('%s: %s' % (name, err))
                return mo.group(0)
            return h
        def ref(mo):
            rid = html.unescape(mo.group(2))
            return chip(rid, label(rid, mo.group(3).strip()), name)
        t = re.sub(r'<a href="#(ch-[a-z0-9-]+)">[^<]*</a>', lambda mo: pref(mo.group(1)) if mo.group(1) in reg else mo.group(0), t)
        return REFSPAN.sub(ref, MARKER.sub(mk, t))

    # pieces first: figures register the first hunk per file for the Files table
    chsec, hashes, rungmin = {}, [], {}
    for c in chapters:
        cid = c.get('id')
        deep = reg[cid]['deep']
        mine = [f['path'] for f in files if cid in owners[f['path']]]
        raw = frags.get(cid)
        if raw is None:
            errs.append('fragments/%s.html is missing' % cid)
            raw = ''
        if not deep:
            # a main-flow piece: the note and its deciding hunks; after MORE (optional) the rest, under "More on this"
            rr, _, rest_raw = raw.partition(MORE)
            figs = ''.join(fragtext(cid, mo.group(0)) for mo in MARKER.finditer(rr))
            lnotes = ''.join(re.findall(r'<ol class="lnotes">.*?</ol>', figs, re.S))
            figs = re.sub(r'<ol class="lnotes">.*?</ol>', '', figs, flags=re.S)
            note, rest = fragtext(cid, MARKER.sub('', rr)), fragtext(cid, rest_raw)
            body = note + figs + rest
            rungmin[cid] = minutes(prose_words(rr))
        else:
            body = fragtext(cid, raw.replace(MORE, ''))      # a piece under Go deeper shows its whole fragment
        gist = c.get('gist') or c.get('why_here')
        sat = [r for r in trace if cid in (r.get('built') or [])]
        prov = list(dict.fromkeys(str(p) for r in sat for p in r.get('proven') or []))
        pchips = [chip(p, '', cid) for p in prov]
        proof = ('<p class="proof">%s %s</p>' % (inline(c.get('proof') or 'Proven by'), ' '.join(pchips)) if pchips else
                 '<p class="proof">No test proves this piece.</p>' if sat else '')
        checks = ''.join(fieldset(q) for q in order if not q.get('final') and q.get('chapter') == cid)
        inner = ('%s<p class="flist-h">Files in this piece (%d)</p>%s%s'
                 % (body, len(mine), files_list(src, mine), '<div class="checks">%s</div>' % checks if checks else ''))
        hsh = hashlib.sha256(inner.encode()).hexdigest()[:12]      # the proof line and gist stay outside: a new test unreads nothing
        hashes.append({'id': cid, 'hash': hsh})
        if not deep:
            # "More on this" closes the note column (the rest of the fragment, Files in this piece and the proof line;
            # no leaf when all are empty); its code figures join the code column, shown only while it is open.
            # Checkpoints follow the leaf, open: a quiz question is never folded.
            fig_re = re.compile(r'(?s)<figure class="code".*?</figure>')
            more_figs, rest_text = ''.join(fig_re.findall(rest)), fig_re.sub('', rest)
            leaf = rest_text + ('<p class="flist-h">Files in this piece (%d)</p>%s' % (len(mine), files_list(src, mine)) if mine else '') + proof
            chsec[cid] = ('<section class="ch piece" id="%s" data-hash="%s" data-read="%s"><div class="hunk"><div class="note"><h3>%s %s</h3>'
                          '%s%s%s%s</div><div class="figs">%s%s</div></div>'
                          '<label class="read"><input type="checkbox" class="read-ch" id="read-%s"> I\'ve read this piece</label></section>' % (
                              cid, hsh, html.escape(c.get('read', 'must')), badge(cid), inline(c.get('title')), note, lnotes,
                              '<details class="leaf"><summary title="Show the rest of this piece">More on this</summary>%s</details>' % leaf
                              if leaf.strip() else '', '<div class="checks">%s</div>' % checks if checks else '',
                              figs, '<div class="more-figs">%s</div>' % more_figs if more_figs else '', cid))
            continue
        chsec[cid] = ('<section class="ch" id="%s" data-hash="%s" data-read="%s"><header class="ch-head"><h3>%s %s</h3>'
                      '%s</header>%s%s<label class="read"><input type="checkbox" class="read-ch" id="read-%s">'
                      ' I\'ve read this piece</label></section>' % (cid, hsh, html.escape(c.get('read', 'must')), badge(cid),
                                                                    inline(c.get('title')), '<p class="gist">%s</p>' % inline(gist) if gist else '',
                                                                    inner, proof, cid))
    mech = [] if nocode else plan.get('mechanical') or []
    if mech:
        groups, mall = [], []
        for i, g in enumerate(mech):
            mine = [f['path'] for f in files if 'ch-mech:%d' % (i + 1) in owners[f['path']]]
            mall += mine
            groups.append('<div class="mgroup"><h4>%s · %d files</h4>%s%s<p class="flist-h">Files (%d)</p>%s</div>'
                          % (inline(g.get('title')), len(mine), '<p>%s</p>' % inline(g['intent']) if g.get('intent') else '',
                             '<p class="how">How to check: %s</p>' % inline(g['check']) if g.get('check') else '',
                             len(mine), files_list(src, mine, True)))
        a = sum(src.files[p]['add'] or 0 for p in mall)
        d = sum(src.files[p]['del'] or 0 for p in mall)
        inner = '<p>These files need a check, not a read: generated, vendored, moved, deleted, binary or whitespace-only.</p>' + ''.join(groups)
        hsh = hashlib.sha256(inner.encode()).hexdigest()[:12]
        hashes.append({'id': 'ch-mech', 'hash': hsh})
        chsec['ch-mech'] = ('<section class="ch" id="ch-mech" data-hash="%s" data-read="mechanical"><header class="ch-head"><h3>'
                       'Generated files</h3><p class="gist"><span class="plus">+%d</span> <span class="minus">−%d</span> · %d files</p></header>%s'
                       '<label class="read"><input type="checkbox" class="read-ch" id="read-ch-mech"> I\'ve checked these files</label></section>'
                       % (hsh, a, d, len(mall), inner))

    # the layer fragments, after the pieces (the Files table links each file's first piece figure)
    layer = {n: frag(n) for n in ('asked', 'background', 'intuition', 'proven')}

    # level 0 is the change as a picture; every other section sits in a closed Go deeper row that opens in place
    t = m['totals']
    drift = ['<li>%s%s%s%s</li>' % ('<strong>Needs a decision:</strong> ' if d.get('needs_decision') else '', inline(d.get('note')),
                                   at_link(d.get('at')), ' ' + chip(d['ref'], label(d['ref'], ''), 'drift') if d.get('ref') else '')
             for d in sorted(plan.get('drift') or [], key=lambda d: not d.get('needs_decision')) if not d.get('carry')]
    def refchip(x, where):      # an item's own chip; `label` shows a ticket key only in the chip
        return ' ' + chip(x['ref'], esc(x['label']) if x.get('label') else label(x['ref'], ''), where) if isinstance(x, dict) and x.get('ref') else ''
    hot = ['<li>%s%s%s</li>' % (inline(h.get('why')), at_link(h.get('at')), refchip(h, 'look')) for h in plan.get('hotspots') or [] if not h.get('carry')]
    ops = ['<li><strong>%s</strong> %s %s%s</li>' % (inline(o.get('what')), ' '.join(
        '<a class="ref file" href="#%s">%s</a>' % (fid(p), html.escape(p)) if p in rows else '<code>%s</code>' % html.escape(p)
        for p in o.get('files') or [] if not LOCAL.search(p)), inline(o.get('note')), refchip(o, 'ops')) for o in plan.get('ops') or [] if not o.get('carry')]
    go = {k: TITLES[k] for k in ('asked', 'background', 'intuition', 'proven') if layer[k] is not None}

    def oq(x):          # "(ch-2) text" -> "text ② core's recompute"; "(asked) text" -> "text What was asked"; no section, no link
        mo = OQ_AT.match(x or '')
        k = mo.group(1) if mo else None
        return inline(x[mo.end():] if mo else x) + (' ' + pref(k) if k in reg else ' <a href="#%s">%s</a>' % (k, esc(go[k])) if k in go else '')

    def sec(sid, title, body, h='h3'):      # a section inside a Go deeper row is an h3; only the page's blocks are h2
        return '<section class="sec" id="%s"><%s>%s</%s>%s</section>' % (sid, h, title, h, body)

    def row(summary, body):
        return '<details class="row"><summary>%s</summary>%s</details>' % (summary, body)

    part = dict(chsec)
    for k in go:
        part[k] = sec(k, TITLES[k], layer[k])
    tested = all(str(r.get('state')) == 'tested' for r in trace)
    if trace and tested and len(trace) < 4:
        # a few goals, all tested: no table, one status line at the end of What was asked
        line = '<p class="trace-status">%d goal%s: <span class="state" data-state="tested">%d tested</span></p>' % (
            len(trace), '' if len(trace) == 1 else 's', len(trace))
        if 'asked' in part:
            part['asked'] = part['asked'][:-len('</section>')] + line + '</section>'
        else:
            part['trace'] = sec('trace', TITLES['trace'], line)
    elif trace:
        trs = ''.join(
            '<tr id="trace-%s" data-id="%s" data-state="%s" data-proven="%d"><td class="c">%s</td><td class="chips">%s</td>'
            '<td class="chips">%s</td><td><span class="state" data-state="%s">%s</span>%s</td></tr>' % (
                ref_id(str(r.get('id')))[4:], html.escape(str(r.get('id'))), html.escape(str(r.get('state'))), len(r.get('proven') or []),
                inline(r.get('text')), chips(r.get('built'), 'trace'), chips(r.get('proven'), 'trace'),
                html.escape(str(r.get('state'))), html.escape(STATES.get(str(r.get('state')), str(r.get('state')))),
                ' <span class="tnote">%s</span>' % inline(r['note']) if r.get('note') else '') for r in trace)
        part['trace'] = sec('trace', TITLES['trace'], '<p>One row per goal: the pieces and code that build it, the tests that '
                            'prove it, and its state.</p>'
                            '<div class="tablebox"><table class="ft tt"><thead><tr><th><button type="button" data-sort="id">Goal</button></th>'
                            '<th>Built</th><th><button type="button" data-sort="proven">Proven</button></th>'
                            '<th><button type="button" data-sort="state">State</button></th></tr></thead><tbody>%s</tbody></table></div>' % trs)
    tree = ''
    if not nocode:
        # ponytail: no roll-up rows per folder or kind; a flat table sorts 5k rows fine. Add roll-ups past that.
        # a file's Piece cell is its home badge, then "also" every other piece whose figures show code from it
        figpath = {fg: p for p, xs in src.figs.items() for _, _, fg in xs}
        shows = {cid: {figpath[x] for x in re.findall(r'<figure class="code" id="([^"]+)"', chsec.get(cid, '')) if x in figpath}
                 for cid in reg}

        def piece_cell(path, home):
            if home == 'ch-mech':
                return '<a href="#ch-mech">generated</a>'
            if home not in reg:
                return '–'
            also = [c for c in reg if c != home and path in shows[c]]

            # a bare badge links to its piece; its name ("② core's recompute") is the label, the digit alone says too little
            return blink(home) + ''.join(' <span class="also">also %s</span>' % blink(c) for c in also)
        # every changed file reads in place: its whole diff (a hunk marker over the whole file, resolved from git)
        # under its row, then the pieces that explain it; generated and vendored files are never embedded
        def file_diff(f, home):
            p, side = f['path'], 'base' if f['status'] == 'D' else 'head'
            ls = None if f['binary'] else src.lines(p if side == 'head' or not f['old_path'] else f['old_path'], side)
            cmpl = src.compare(p)
            gh = ' · <a href="%s">view on GitHub ↗</a>' % esc(cmpl) if cmpl else ''
            if f['tier'] == 'skip':
                why = '%s regenerated' % f['reason'] if f['reason'] == 'lockfile' else f['reason'] or f['kind']
                return '<p class="fgen">Generated (%s), %s%s</p>' % (esc(why), pm(f), gh)
            if ls is None:
                return '<p class="fgen">Binary file%s</p>' % gh
            if not ls:
                return '<p class="fgen">empty file</p>'
            if not src.hunks(p):        # a pure rename or a mode change: no line changed, nothing to embed
                return '<p class="fgen">No line changes (%s)%s</p>' % (esc(f['reason'] or 'no hunks'), gh)
            out, _, err = src.resolve({'data-hunk': '%s:1-%d' % (p, len(ls)), 'data-note': 'whole diff'}, register=False)
            if err:
                errs.append('files: %s' % err)
                return ''
            also = [c for c in reg if c != home and p in shows[c]]
            go_ = ('<p class="fgo">Explained in %s%s</p>' % (pref(home), ''.join(' · also %s' % pref(c) for c in also))
                   if home in reg else '')
            return out + go_
        frows = []
        for f in files:
            own = owners[f['path']]
            cid = own[0].split(':')[0] if own else ''
            c = next((x for x in chapters if x.get('id') == cid), {})
            rk = c.get('risk', 'none') if cid != 'ch-mech' else 'none'
            d, b = f['path'].rsplit('/', 1) if '/' in f['path'] else ('', f['path'])
            frows.append(
                '<tr id="%s" data-path="%s" data-ch="%s" data-kind="%s" data-tier="%s" data-risk="%d" data-add="%d" data-del="%d" data-chg="%d" data-st="%s" data-h="%s">'
                '<td class="p"><span class="st">%s</span> %s'
                '<button type="button" class="fx" aria-expanded="false" aria-controls="fd-%s">%s%s</button></td><td>%s</td><td class="k">%s</td><td><span class="risk" data-risk="%d">%s</span></td>%s'
                '<td class="vw"><label title="%s"><input type="checkbox" class="read-f" id="read-%s" aria-label="Viewed: %s"> Viewed</label></td></tr>' % (
                    f['id'], html.escape(f['path']), cid, f['kind'], f['tier'], RISK.get(rk, 0), f['add'] or 0, f['del'] or 0,
                    (f['add'] or 0) + (f['del'] or 0), f['status'], f['blob'] or m['head'], f['status'],
                    '<span class="old">%s →</span> ' % html.escape(f['old_path']) if f['old_path'] else '', f['id'][2:],
                    '<span class="dir">%s/</span>' % html.escape(d) if d else '', html.escape(b),
                    piece_cell(f['path'], cid), f['kind'], RISK.get(rk, 0), rk,
                    '<td class="n">bin</td>' if f['binary'] else
                    '<td class="n"><span class="plus">+%d</span> <span class="minus">−%d</span> %s</td>' % (f['add'], f['del'], dstat(f['add'], f['del'])),
                    VIEWED_TIP, f['id'], html.escape(f['path'])) +
                '<tr class="fd"><td colspan="6"><details class="fdx" id="fd-%s"><summary>%s</summary><div class="fdw">%s</div></details></td></tr>' % (
                    f['id'][2:], html.escape(f['path']), file_diff(f, cid)))
        part['files'] = sec('files', 'All %d files' % t['files'], '<p>%d files, <span class="plus">+%d</span> <span class="minus">−%d</span>: %d pieces%s. '
                            '%d files to read, %d to check, %d generated or vendored.</p>' % (
                                t['files'], t['add'], t['del'], len(chapters), ' and the generated files' if mech else '',
                                t['by_tier']['read']['files'], t['by_tier']['verify']['files'], t['by_tier']['skip']['files'])
                            + '<div class="tablebox"><table class="ft"><thead><tr>'
                            '<th><button type="button" data-sort="path">File</button></th><th><button type="button" data-sort="ch">Piece</button></th>'
                            '<th class="k">Kind</th><th><button type="button" data-sort="risk">Risk</button></th>'
                            '<th class="n"><button type="button" data-sort="chg">Changes</button></th><th>Viewed</th></tr></thead><tbody>%s</tbody></table></div>' % ''.join(frows))
        tree = file_tree(files, piece_cell, owners, reg, t['files'], filter_at)
    finals = [q for q in order if q.get('final')]
    quiz_sec = sec('quiz', 'Check yourself', '<p>%d question%s%s. Pick one answer each: only your first pick counts.</p><p class="quiz-note">'
                   'Your first picks are saved privately for you; nobody else can read them.</p>%s' % (
                       len(order), '' if len(order) == 1 else 's', ' in all (%d here, %d at piece ends)' % (len(finals), len(order) - len(finals))
                       if len(finals) < len(order) else '', ''.join(fieldset(q) for q in finals)), 'h2')

    # the main flow: the map → the carry list → the main-flow pieces, open (intent-only: What was asked) → the quiz → the
    # closed Go deeper rows
    b = []
    pb = []
    if plan.get('problem'):
        pb.append('<p>%s%s</p>' % (inline(plan['problem']), refchip(plan.get('problem_ref'), 'problem')))
    bh = plan.get('behaviour') or {}
    if bh.get('rows'):
        pb.append('%s<table class="bt"><thead><tr>%s</tr></thead><tbody>%s</tbody></table>' % (
            '<p class="how">%s</p>' % inline(bh['intro']) if bh.get('intro') else '',
            ''.join('<th>%s</th>' % inline(x) for x in bh.get('cols') or ('What happens next', 'Before', 'After')),
            ''.join('<tr><td>%s</td><td>%s</td><td%s>%s</td></tr>' % (inline(r[0]), inline(r[1]), ' class="chg"' if r[1] != r[2] else '', inline(r[2]))
                    for r in bh['rows'])))
    if pb:
        part['problem'] = sec('problem', 'The problem, and what happens now', ''.join(pb))
    if hot:
        part['look'] = sec('look', 'Where to look hardest', '<ol>%s</ol>' % ''.join(hot))
    if drift:
        part['drift'] = sec('drift', 'Where the code differs from earlier plans', '<div class="drift-list"><ul>%s</ul></div>' % ''.join(drift))
    if ops:
        part['ops'] = sec('ops', 'Deploy and merge notes', '<div class="ops-list"><ul>%s</ul></div>' % ''.join(ops))

    # the picture: authored plan.json map; goal tags and their state come from the trace
    mp = plan.get('map') if isinstance(plan.get('map'), dict) else None
    trow = {str(r.get('id')): (i + 1, r) for i, r in enumerate(trace)}

    ngs = [x.get('text') if isinstance(x, dict) else x for x in plan.get('not_in_change') or []]
    ngline = ' · '.join(inline(x) + refchip(y, 'carry') for x, y in zip(ngs, plan.get('not_in_change') or []))

    # the carry list: tagged facts from hotspots, drift, open questions, ops and the non-goals; untagged ones stay in Go deeper.
    # each line has an id (carry-<tag>-<n>), so a map box can land on it
    ctags = Counter()

    def tagged(tag, body):
        ctags[tag] += 1
        tip = CARRY_TIP.get(tag)
        return '<li id="carry-%s-%d"><b class="tag" data-tag="%s"%s>%s</b> %s</li>' % (
            re.sub(r'[^a-z0-9]+', '-', tag.lower()).strip('-'), ctags[tag], esc(tag), ' title="%s"' % esc(tip) if tip else '', esc(tag), body)
    carry = ([tagged(h['carry'], inline(h.get('why')) + at_link(h.get('at')) + refchip(h, 'carry')) for h in plan.get('hotspots') or [] if h.get('carry')]
             + [tagged(d['carry'], inline(d.get('note')) + at_link(d.get('at')) + (' ' + chip(d['ref'], label(d['ref'], ''), 'carry') if d.get('ref') else ''))
                for d in plan.get('drift') or [] if d.get('carry')]
             + [tagged('ask', oq(x)) for x in plan.get('open_questions') or []]
             + [tagged(o['carry'], '%s. %s%s' % (inline(o.get('what')), inline(o.get('note')), refchip(o, 'carry')))
                for o in plan.get('ops') or [] if o.get('carry')]
             + ([tagged('not here', ngline)] if ngline else []))
    carry_ids = set(re.findall(r'<li id="(carry-[a-z0-9-]+)"', ''.join(carry)))
    how = [c for c in chapters if not reg[c.get('id')]['deep']]       # the main-flow pieces, in plan order
    asked_main = nocode and 'asked' in part         # intent-only: What was asked opens in the main flow

    def nextline(href, inner):      # every block ends by naming where the path goes next
        return '<p class="next"><a href="#%s">Next: %s ↓</a></p>' % (href, inner)

    def piece_next(cid):
        return nextline(cid, '%s %s' % (badge(cid), inline(reg[cid]['title'])))

    def read_next():                # where reading starts after the map and the carry list
        if how:
            return piece_next(how[0].get('id'))
        if asked_main:
            return nextline('asked', TITLES['asked'])
        return nextline('quiz', 'Check yourself') if order else ''

    # "The map": a framed section (header, columns joined by wires, the places left out, a legend), named "The map"
    # everywhere; plan.json map supplies the words. Rule-shaped (map.rule): who asks → the rule → what happens.
    # Flow-shaped (no map.rule): entries → outcomes. Every box links to a piece (and shows its badge), a carry line or a
    # section the page renders; the build invents no box.
    targets = {k: TITLES.get(k, k) for k in part if k not in reg}
    targets.update(quiz='Check yourself', deeper='Go deeper', refs='Sources', **({'carry': TITLES['carry']} if carry else {}))
    if 'files' in part:
        targets['files'] = 'All %d files' % t['files']

    def dest(k):        # (title, badge) of a box's target, or None
        if k in reg:
            return 'Go to %s' % (circ(k) + ' ' + reg[k]['name']), badge(k)
        if k in carry_ids:
            return 'Go to its line in To carry into the review', ''
        return ('Go to %s' % targets[k], '') if k in targets else None

    def box(x, where, cls, inner):
        k = str(x.get('target') or '')
        d = dest(k)
        if not d:
            errs.append('plan.json map %s %r: target %r is not a piece, a carry line (%s) or a section on this page' % (
                where, x.get('label') or x.get('title'), k, ', '.join(sorted(carry_ids)) or 'none'))
            return '<div class="%s">%s</div>' % (cls, inner)
        return '<a class="%s" href="#%s" title="%s">%s%s</a>' % (cls, k, esc(d[0]), d[1], inner)

    def colh(t):
        t, _, sub = str(t).partition(' · ')
        return '<h3>%s%s</h3>' % (inline(t), ' <small>· %s</small>' % inline(sub) if sub else '')
    mapsec = ''
    if mp:
        ents = mp.get('entries') or []
        askers = [e for e in ents if e.get('kind') != 'not asked']
        skips = [e for e in ents if e.get('kind') == 'not asked']
        r_ = mp.get('rule') if isinstance(mp.get('rule'), dict) else None
        new = bool(r_) and r_.get('new', True) is not False
        tagged_states = set()

        def outcome(o):
            gk = o.get('goal')
            g = trow.get(str(gk)) if gk is not None else None
            if gk is not None and not g:
                errs.append('plan.json map outcome %r: goal is not a trace id' % gk)
            if g:
                tagged_states.add(str(g[1].get('state')))
            tag = ('<span class="gtag" data-state="%s">%s, %d test%s</span>' % (
                esc(str(g[1].get('state'))), STATES.get(str(g[1].get('state')), str(g[1].get('state'))).lower(),
                len(g[1].get('proven') or []), '' if len(g[1].get('proven') or []) == 1 else 's')) if g else ''
            return box(o, 'outcome', 'box out', '<b>%s</b> %s %s' % (inline(o.get('label')), inline(o.get('sub')), tag))

        def skip(e):
            k = str(e.get('target') or '')
            d = dest(k)
            if not d:
                errs.append('plan.json map entry %r: a "not asked" target must be a carry line (%s), a piece or a section on '
                            'this page' % (e.get('label'), ', '.join(sorted(carry_ids)) or 'none'))
                return '<span class="skip"><b>%s</b> %s</span>' % (inline(e.get('label')), inline(e.get('sub')))
            return '<a class="skip" href="#%s" title="%s"><b>%s</b> %s</a>' % (k, esc(d[0]), inline(e.get('label')), inline(e.get('sub')))
        ent_h = colh(mp.get('entries_h') or ('Who decides' if r_ else 'What changed'))
        ent = ''.join(box(e, 'entry', 'box asker', '<b>%s</b><small>%s</small>' % (inline(e.get('label')), inline(e.get('sub'))))
                      for e in askers)
        out_h, outs = colh(mp.get('outcomes_h') or 'What happens'), ''.join(outcome(o) for o in mp.get('outcomes') or [])
        if r_:
            rk = str(r_.get('target') or '')
            conds = ''.join('<li%s>%s</li>' % (' class="ex"' if x.get('exception') else '', inline(x.get('text')))
                            for x in r_.get('conditions') or [])
            grid = ('<div class="map"><div class="col">%s%s</div><div class="wire bus" aria-hidden="true"><em>%s</em><span></span></div>'
                    '<div class="col">%s%s</div><div class="wire plain" aria-hidden="true"><em>%s</em><span></span></div>'
                    '<div class="col">%s%s</div></div>' % (
                        ent_h, ent, esc(mp.get('arrow') or 'ask'),
                        colh(mp.get('rule_h') or 'The rule'), box(r_, 'rule', 'box rule', '<b>%s%s</b><ul class="cond">%s</ul>%s' % (
                            inline(r_.get('title')), '<i class="new">new</i>' if new else '', conds,
                            '<small>%s</small>' % inline(r_.get('sub')) if r_.get('sub') else '')),
                        esc(mp.get('so') or 'so'), out_h, outs))
            num = {1: 'One place doesn\'t', 2: 'Two places don\'t', 3: 'Three places don\'t'}.get(len(skips), '%d places don\'t' % len(skips))
            skip_h = '%s ask %s' % (num, pref(rk) if rk in reg else 'the rule')
        else:
            grid = ('<div class="map two"><div class="col">%s%s</div><div class="wire bus" aria-hidden="true"><em>%s</em><span></span></div>'
                    '<div class="col">%s%s</div></div>' % (ent_h, ent, esc(mp.get('arrow') or 'then'), out_h, outs))
            skip_h = {1: 'One place stays', 2: 'Two places stay', 3: 'Three places stay'}.get(len(skips), '%d places stay' % len(skips)) + ' out of it'
        both = {1: 'it is', 2: 'both are'}.get(len(skips), 'all are')
        shown = re.findall(r'<a class="box[^"]*" href="#(ch-[a-z0-9-]+)"', grid)
        fill = next((c for c in reg if c in shown and not reg[c]['deep']), None)
        hollow = next((c for c in reg if c in shown and reg[c]['deep']), None)
        legend = ''.join(x for x in (
            '<span>%s a piece: click to read it</span>' % blink(fill) if fill else '',
            '<span>%s a piece under Go deeper</span>' % blink(hollow) if hollow else '',
            '<span><b class="new">new</b> added by this change</span>' if new else '',
            '<span><span class="gtag" data-state="tested">tested</span> a test proves it</span>' if 'tested' in tagged_states else '',
            '<span><i class="sw-dash" aria-hidden="true"></i> %s</span>' % ('doesn\'t ask the rule' if r_ else 'stays out of it') if skips else ''))
        mapsec = (
            '<section class="mapframe" id="map" aria-labelledby="map-h"><header><h2 id="map-h">The map</h2>%s</header>%s%s%s</section>' % (
                '<p>%s</p>' % inline(mp['purpose']) if mp.get('purpose') else '', grid,
                '<p class="skips"><b>%s:</b> %s%s</p>' % (skip_h, ' '.join(skip(e) for e in skips),
                                                         ' <a class="to" href="#carry">%s in To carry into the review ↓</a>' % both
                                                         if all(str(e.get('target')) in carry_ids for e in skips) else '') if skips else '',
                '<p class="legend">%s</p>' % legend if legend else ''))
        b.append(mapsec + (nextline('carry', TITLES['carry']) if carry else read_next()))
    if carry:
        b.append('<h2 class="blk" id="carry">To carry into the review</h2><ul class="carry">%s</ul>%s' % (''.join(carry), read_next()))
    if asked_main:
        head = sec('asked', TITLES['asked'], '')[:-len('</section>')]
        b.append(part.pop('asked').replace(head, '<section class="sec" id="asked"><h2 class="blk">%s</h2>' % TITLES['asked'], 1)[:-len('</section>')]
                 + (nextline('quiz', 'Check yourself') if order else '') + '</section>')
    if how:
        for i, c in enumerate(how):     # a piece ends with the next piece, the last with the quiz
            nx = piece_next(how[i + 1].get('id')) if i + 1 < len(how) else nextline('quiz', 'Check yourself') if order else ''
            part[c.get('id')] = part[c.get('id')][:-len('</section>')] + nx + '</section>'
        nw = ('one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve')
        b.append('<h2 class="blk" id="pieces">%s</h2>%s' % (
            'The piece' if len(how) == 1 else 'The %s pieces' % (nw[len(how) - 1] if len(how) <= len(nw) else len(how)),
            ''.join(part.pop(c.get('id')) for c in how)))

    def part_title(k):      # a section's heading, as the summary of the row that holds it
        if k in reg:
            return '%s %s' % (badge(k), inline(reg[k]['title']))
        return 'All %d files' % t['files'] if k == 'files' else esc(TITLES.get(k, k))

    # go deeper (level 1): the plan's groups, then whatever no group holds, then All N files
    deeper = []
    for g in plan.get('deeper') or []:
        held = [k for k in g.get('holds') or [] if k in part]
        pc = g.get('piece') if g.get('piece') in reg else None      # a piece's row is named by its badge and title
        if held:
            deeper.append(row('<span class="sm">%s</span>' % (part_title(pc) if pc else inline(g['summary']) if g.get('summary')
                                                              else part_title(held[0])), ''.join(part.pop(k) for k in held)))
    files_sec = part.pop('files', None)
    for k in list(part):        # nothing is lost: a section no group holds gets its own row
        deeper.append(row('<span class="sm">%s</span>' % part_title(k), part.pop(k)))
    if files_sec:
        deeper.append(row('<span class="sm">%s</span>' % part_title('files'), files_sec))

    for rid, where in used.items():
        if not rid.startswith('file:') and rid not in refs:
            errs.append('%s: data-ref="%s" has no plan.json refs entry' % (where, rid))
    lis = []        # the previews' store (hidden): one entry per ref, its origin named in words, never its local path
    for rid, r in refs.items():
        o = origins.get(r.get('origin'))
        if cites.get(rid) and not o:
            errs.append('plan.json refs %s: cited, but its origin %r is not in plan.json origins' % (rid, r.get('origin')))
        lis.append('<li id="%s" data-ref="%s"%s><span class="rk">%s</span> <b>%s</b>%s<blockquote>%s</blockquote><span class="src">%s</span></li>' % (
            ref_id(rid), html.escape(rid), ' data-entry="src-%s"' % r['origin'] if o else '', ref_kind(rid),
            inline(r.get('title')) or html.escape(rid), sb_link(rid), html.escape(r.get('text', '')),
            '%s · %s' % (esc(o.get('group')), inline(o.get('label'))) if o else ''))
    for rid in sorted(x for x in used if x.startswith('file:')):
        fr = src.file_ref(rid)
        if isinstance(fr, str):
            errs.append('%s: data-ref="%s": %s' % (used[rid], rid, fr))
            continue
        p, s, e, ls = fr
        lk, at_ = src.link(p, 'head', s, e), '%s at %s' % (html.escape(p), head7)
        lis.append('<li id="%s" data-ref="%s"><span class="rk">Code</span> <b>%s</b><blockquote><code>%s</code></blockquote><span class="src">%s</span></li>' % (
            ref_id(rid), html.escape(rid), html.escape(p) + (' lines %d–%d' % (s, e) if e != s else ' line %d' % s), html.escape('\n'.join(x.strip() for x in ls)),
            '<a href="%s">%s ↗</a>' % (html.escape(lk), at_) if lk else at_))
    gl = ''.join('<dt>%s</dt><dd>%s</dd>' % (inline(g.get('term')), inline(g.get('def'))) for g in plan.get('glossary') or [])
    # the listed sources: one entry per origin a chip cites, grouped; each ends with the places that cite it
    cited_by = {}
    for rid, r in refs.items():
        if r.get('origin') in origins and cites.get(rid):
            cited_by.setdefault(r['origin'], []).extend(cites[rid])
    groups = []
    for g in dict.fromkeys(SRC_GROUPS + tuple(o['group'] for o in origins.values())):
        note = '<p class="src-note">Notes that are not online, so they have no link.</p>' if g == 'From the author' else ''
        ents = ['<li id="src-%s">%s <span class="cited">Cited in: <!--XD:CITES:%s--></span></li>' % (
            k, '<a href="%s">%s ↗</a>' % (esc(o['url']), inline(o.get('label'))) if o.get('url') else '<span class="sl">%s</span>' % inline(o.get('label')), k)
            for k, o in origins.items() if o.get('group') == g and k in cited_by]
        if ents:
            groups.append('<h4>%s</h4>%s<ul class="srcs">%s</ul>' % (g, note, ''.join(ents)))
    refs_sec = sec('refs', 'Sources', '%s<ol class="refs" hidden>%s</ol>%s' % (
        ''.join(groups), ''.join(lis), '<h4>Glossary</h4><dl class="gloss">%s</dl>' % gl if gl else ''))

    def cited_in(main, k):      # in page order; a place that cites twice gets one named link, then numbered ones
        at = {}
        for cid_, where in sorted(cited_by[k], key=lambda x: main.find('id="%s"' % x[0])):
            at.setdefault(where, []).append(cid_)
        out = []
        for where, ids in at.items():
            nm = '%s %s' % (badge(where), inline(reg[where]['name'])) if where in reg else esc(TITLES.get(where, where))
            tn = circ(where) + ' ' + reg[where]['name'] if where in reg else TITLES.get(where, where)
            out.append('<a class="cite" href="#%s" title="Go to where %s cites this">%s</a>' % (ids[0], esc(tn), nm) + ''.join(
                '<a class="cite n" href="#%s" title="Go to where %s cites this (%d)" aria-label="%s, citation %d">%d</a>' % (
                    x, esc(tn), i, esc(tn), i, i) for i, x in enumerate(ids[1:], 2)))
        return ' · '.join(out)

    # About this page: the last row (built-from, hashes, base → head)
    now = datetime.datetime.now(datetime.timezone.utc)
    st = Counter(f['status'] for f in files)
    na = nd = 0                                       # five cells split +/-, each side at least one when present
    if t['add'] + t['del']:
        na = min(max(round(5 * t['add'] / (t['add'] + t['del'])), 1 if t['add'] else 0), 4 if t['del'] else 5)
        nd = 5 - na
    bar = '<i class="a"></i>' * na + '<i class="d"></i>' * nd + '<i></i>' * (5 - na - nd)
    ticket = plan.get('ticket') or ''
    compare = '%s/compare/%s...%s' % (m['forge'], m['merge_base'], m['head']) if m.get('forge') else None
    stage_dd = {'intent-only': 'Intent only: no code yet', 'reviewer': 'Reviewer: built to review the PR'}.get(
        stage, 'Full: ' + ', '.join(['asked'] * (layer['asked'] is not None) + ['built'] + ['proven'] * (layer['proven'] is not None)))
    bf = ['the head of <code>%s</code> (commit <code>%s</code>) against <code>%s</code> (merge base <code>%s</code>)'
          % (esc(m['head_ref']), head7, esc(m['base_ref']), base7)]
    if contract:
        bf.append('<code>contract %s (%s)</code>' % (esc(str(contract.get('version'))), esc(str(contract.get('status')))))
    if inputs:      # sources are named by count; their names and hashes stay in the page data (meta.inputs)
        loc = len(inputs) - online
        bf += ['%d local note%s, not online' % (loc, '' if loc == 1 else 's')] * bool(loc) + ['%d online' % online] * bool(online)
    props = [('Ticket', esc(ticket)) if ticket else None,
             ('Repository', ('<a href="%s">%s ↗</a>' % (esc(m['forge']), esc(m['repo']))) if m.get('forge') else esc(m['repo'])),
             ('Stage', stage_dd),
             ('Contract', '%s · %s' % (esc(str(contract.get('version'))), esc(str(contract.get('status'))))) if contract else None,
             ('Branch', '<code>%s</code>' % esc(plan['branch'])) if plan.get('branch') else None]
    if not nocode:
        props += [('Base → Head', ('<a href="%s">' % esc(compare) if compare else '') + '<code>%s</code> → <code>%s</code>' % (base7, head7) + (' ↗</a>' if compare else '')),
                  ('Files', '<a href="#files">%d (%s)</a>' % (t['files'], ' · '.join('%d %s' % (st[k], k) for k in 'AMDRCT' if k in st))),
                  ('Lines', '<span class="plus">+%d</span> <span class="minus">−%d</span> <span class="sizebar" aria-hidden="true">%s</span>' % (t['add'], t['del'], bar))]
    props += [('Built from', ' · '.join(bf)),
              ('Generated', '<time datetime="%s" data-rel>%s</time>' % (now.isoformat(timespec='seconds'), now.strftime('%Y-%m-%d %H:%M UTC')))]
    deeper.append(row('<span class="sm">Sources</span>', refs_sec + '<div class="about-b"><h3>About this page</h3>%s<dl class="props">%s</dl></div>' % (
        '' if nocode else '<p>This page explains the change; it does not review it. It embeds selected hunks; '
                          '<a href="#files">All %d files</a> lists every change.</p>' % t['files'],
        ''.join('<div><dt>%s</dt><dd>%s</dd></div>' % p for p in props if p))))

    # the diff weight strip, one tile per file (width ∝ log(lines changed)), each a link to its home piece and numbered
    # with it (the shell hides a digit on a tile under 13 px); colour = the piece's family; generated files are hatched.
    # Its legend is the piece index: every piece, its file count, where it sits; then the generated files and all files.
    def home(f):
        own = owners[f['path']]
        return own[0].split(':')[0] if own else ''
    strip = ''
    if files:
        gen = [f for f in files if home(f) not in reg]
        tiles = []
        for cid, fs in [(c.get('id'), [f for f in files if home(f) == c.get('id')]) for c in chapters] + [('ch-mech', gen)]:
            for f in fs:      # a tile is a file: a click opens it in All N files; the shell's hover card adds its piece
                tiles.append('<a href="#%s" data-f="%s" data-fam="%s" style="flex-grow:%.2f" aria-label="%s: open its diff in All %d files">%s</a>' % (
                    f['id'], f['id'], reg[cid]['fam'] if cid in reg else 'gen',
                    max(math.log1p((f['add'] or 0) + (f['del'] or 0)), .3), esc(f['path'].rsplit('/', 1)[-1]), t['files'],
                    '<span>%d</span>' % reg[cid]['n'] if cid in reg else ''))

        def nfiles(cid):        # a piece that owns no file shows another's: "shares ①'s file", each badge its own link
            n = sum(1 for f in files if home(f) == cid)
            sh = [f for f in files if f['path'] in shows[cid]] if not n else []
            hs = list(dict.fromkeys(home(f) for f in sh if home(f) in reg))
            if hs:
                return 'shares %s\'s file%s' % (' and '.join(blink(h) for h in hs), '' if len(sh) == 1 else 's')
            return '%d file%s' % (n, '' if n == 1 else 's')
        idx = ['<li data-ch="%s"><a href="#%s" title="Go to %s">%s <span class="long">%s</span><span class="short">%s</span></a> <small>%s%s</small></li>' % (
            cid, cid, esc(circ(cid) + ' ' + r['name']), badge(cid), inline(r['title']), inline(r['name']), nfiles(cid),
            ' · under Go deeper' if r['deep'] else '') for cid, r in reg.items()]
        if gen:
            why = Counter('lockfile' if f['reason'] == 'lockfile' else 'empty file' if f['reason'] == 'empty new file' else 'generated' for f in gen)
            idx.append('<li><a href="#%s" title="Go to Generated files"><i class="sw"></i> Generated files</a> <small>%s</small></li>' % (
                'ch-mech' if mech else 'files', ' + '.join(('%d %ss' % (n, k) if n > 1 else k) for k, n in why.items())))
        idx.append('<li class="all"><a href="#files" title="Open All %d files">All %d files</a></li>' % (t['files'], t['files']))
        strip = ('<p class="strip-h"><b>The %d files, by size.</b> <span class="hv">A tile opens its file; hover or focus it for the file and its piece.</span>'
                 '<span class="tp">Tap a tile for its file and its piece.</span></p>'
                 '<nav class="strip" aria-label="The %d files, by size">%s</nav><ol class="pindex">%s</ol>' % (t['files'], t['files'], ''.join(tiles), ''.join(idx)))
    # "Start here": a framed band under the lead, linked steps, no step numbers (circled numbers are pieces');
    # minutes are estimates: the map and the carry list's words, the pieces' visible notes, ~0.6 min per question
    steps = []
    if mapsec or carry:
        glance = minutes(prose_words(mapsec + ''.join(carry)))
        steps.append('<a class="step" href="#%s"><span class="st">Look at %s</span> <small>· %s%d min</small></a>' % (
            'map' if mapsec else 'carry', 'the map and what to carry' if mapsec and carry else 'the map' if mapsec else 'what to carry',
            '~' if glance > 1 else '', glance))
    if how:
        a_, z_ = how[0].get('id'), how[-1].get('id')
        steps.append('<span class="step"><a class="step-a" href="#%s">Read piece%s</a> %s <small>· ~%d min</small></span>' % (
            a_, 's' if len(how) > 1 else '', '%s–%s' % (blink(a_), blink(z_)) if len(how) > 1 else blink(a_), sum(rungmin.values())))
    elif asked_main:
        n_ = minutes(prose_words(layer['asked']))
        steps.append('<a class="step" href="#asked"><span class="st">Read what was asked</span> <small>· %s%d min</small></a>' % (
            '~' if n_ > 1 else '', n_))
    if order:
        steps.append('<a class="go path-q" href="#quiz"><span class="go-t">Answer %d question%s <small>· ~%d min</small></span><i class="path-prog">0/%d</i></a>' % (
            len(order), '' if len(order) == 1 else 's', max(1, round(len(order) * 0.6)), len(order)))
    start = ('<nav class="start" id="start" aria-label="Start here"><b class="lbl">Start here</b>%s</nav>' % (
        '<span class="arr" aria-hidden="true">→</span>'.join(steps)) if steps else '')
    header = '<header class="doc"><h1>%s</h1>%s%s%s</header>' % (
        inline(plan.get('heading') or plan.get('title')), '<p class="lead">%s</p>' % inline(plan['glance']) if plan.get('glance') else '', start, strip)
    sections = ['<section class="sec brief" id="overview">%s</section>' % ''.join(b), quiz_sec,
                '<section class="sec deeper" id="deeper"><h2 class="lbl">Go deeper</h2>%s</section>' % ''.join(deeper)]
    data = {'meta': {'repo': m['repo'], 'ticket': ticket, 'head': m['head'], 'head7': head7, 'base': m['merge_base'], 'base7': base7,
                     'generated': now.isoformat(timespec='seconds'), 'mode': plan.get('mode', 'author'), 'stage': stage,
                     'forge': m.get('forge'), 'contract': contract, 'inputs': inputs, 'build': build, 'filter_at': filter_at},
            'chapters': hashes, 'quiz': quiz,
            # the piece registry and the row names, for the quiz's "decided in"; figures by file, for evidence links
            'pieces': reg, 'rows': dict(go, files='All %d files' % t['files'] if not nocode else 'Files'),
            'figs': {p: [[a_, b_, fg] for a_, b_, fg in xs] for p, xs in src.figs.items()}}
    main = ''.join(sections)

    def finish(t):      # cited pieces become badge links; every external link opens a new tab
        return re.sub(r'<a (?![^>]*\btarget=)([^>]*\bhref="https?:)', r'<a target="_blank" rel="noopener" \1', pieces_cited(t))
    slots = {'TITLE': esc(plan.get('title') or ''), 'HEADER': finish(header),
             'TOC': finish(tree),      # the file tree (files only); the page has no section outline
             'MAIN': finish(re.sub(r'<!--XD:CITES:([\w-]+)-->', lambda mo: cited_in(main, mo.group(1)), main)),
             'DATA': json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')}
    missing = [k for k in slots if ('/*XD:DATA*/' if k == 'DATA' else '<!--XD:%s-->' % k) not in shell]
    if missing:
        raise Fail('shell lacks slot(s): %s' % ', '.join(missing))
    return re.sub(r'<!--XD:(TITLE|HEADER|TOC|MAIN)-->|/\*XD:(DATA)\*/', lambda mo: slots[mo.group(1) or mo.group(2)], shell)


LOCAL_HEAD = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
              '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n')


def cmd_build(a):
    d = os.path.abspath(a.dir)
    repo = find_repo(d, a.repo)
    m, plan, quiz, frags = read_json(d, 'map.json'), read_json(d, 'plan.json'), read_json(d, 'quiz.json', need=False), read_frags(d)
    build = inputs_hash(m, plan, quiz, frags)
    quiz = quiz or {'built_from': m['head'][:7], 'questions': []}
    try:
        with open(a.shell, encoding='utf-8') as fh:
            shell = fh.read()
    except OSError as e:
        raise Fail('shell: %s' % e)
    src, errs = Src(repo, m), []
    page = render(src, plan, quiz, frags, shell, errs, build, source_hashes(repo, d, plan.get('sources') or []), a.filter_at,
                  online_sources(repo, d, plan))
    for name, text in (('explainer.html', page), ('explainer.local.html', LOCAL_HEAD + page)):
        with open(os.path.join(d, name), 'w', encoding='utf-8') as fh:
            fh.write(text)
    owners, _ = assign(plan, m['files'])
    print('build: %s  %.0f KB  %s  %d code figures, %d diff lines embedded  %d pieces  %d trace rows  %d questions  %d files (%d unassigned)' % (
        os.path.join(d, 'explainer.html'), len(page.encode()) / 1024, stage_of(plan, m), len(src.ids), src.diff_lines,
        len(plan.get('chapters') or []), len(plan.get('trace') or []), len(quiz.get('questions') or []), len(m['files']),
        sum(not o for o in owners.values())))
    for e in errs:
        print('  ERROR %s' % e)
    return 1 if errs else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest='cmd')
    m = sub.add_parser('map', help='triage the changed files into map.json')
    m.add_argument('--base', help='required unless --intent-only (then it defaults to --head)')
    m.add_argument('--head', default='HEAD')
    m.add_argument('--out', default='.')
    m.add_argument('--repo')
    m.add_argument('--intent-only', action='store_true', help='no code yet: map no files')
    m.add_argument('--ticket-dir', action='append', help='a .ai/<TICKET>/ dir to list why-sources from, repeatable '
                                                        '(default: the parent of --out)')
    b = sub.add_parser('build', help='plan + fragments + quiz + map -> explainer.html')
    b.add_argument('dir')
    b.add_argument('--shell', default=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   '..', 'assets', 'explainer-shell.html'))
    b.add_argument('--repo')
    b.add_argument('--filter-at', type=int, default=FILTER_AT, help='file-filter UI (the tree\'s filter box, the files table\'s search and filters) only above this many '
                   'changed files (default %(default)s)')
    a = ap.parse_args(argv)
    if not a.cmd:
        ap.print_help()
        return 2
    if a.cmd == 'map' and not a.base:
        if not a.intent_only:
            ap.error('map: --base is required (or pass --intent-only)')
        a.base = a.head
    try:
        return cmd_map(a) if a.cmd == 'map' else cmd_build(a)
    except Fail as e:
        print('build-explainer: %s' % e, file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
