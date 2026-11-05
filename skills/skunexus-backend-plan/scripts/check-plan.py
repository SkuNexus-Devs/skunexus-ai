#!/usr/bin/env python3
"""Assemble drafter part files into backend-plan.md and run the mechanical plan checks.

Usage: python3 -I check-plan.py <ticket-dir> [--deps plan-parts/deps.json] [--check-only | --plan [--sizes]]
                                [--forbid <regex> ...] [--stale-name <name> ...] | --selftest

Parts: <ticket-dir>/plan-parts/[A-Z]-*.md, split at `### T<n> ` headings; each part's
`#### Notes to orchestrator` goes to plan-parts/NOTES-collected.md. The assembled tasks replace the one
`<!-- TASKS -->` line in backend-plan.md.
deps.json (all keys optional): {"order": ["T1", ...], "deps": {"T2": ["T1", "T0 (tests only)"]},
"inserts": {"T8": "- [ ] step appended before the task's trailers"}}.
Checks: paused parts (a `PAUSED <DATE>` line), missing/extra/duplicate tasks (against `order`; without it, gaps
in the task numbering), unknown deps, cycles, waves + critical path, criterion coverage against prd.md §6
(letters a … z, aa …; retired criteria need none; a requirement with no live criterion is cited as `Rn`; a range
cites every id in it: R1.a-c, R1.a–R1.c, R1.z-aa, and an unprefixed end after a spaced dash is as long as the start),
forbidden mechanisms, stale names (`--stale-name`, the names a revision renamed), and a task's `**Part:**`
line against workflows.md "Parts". With workflows.md, `Tests:` and `out-of-suite:` trailers may also cite scenarios
and steps (`s1`, `s1.2`): each live scenario needs a `Tests:` trailer citing `s<n>` (its scenario test) unless every
one of its live steps is out-of-suite (warnings, as is a cited `s` id that is not live). --check-only writes nothing. --plan runs the same checks on the tasks of an
assembled (and later edited) backend-plan.md, plus the contract's stale check when the plan has a
`> Built from:` line. --sizes (with --plan) prints plan characters per part for the estimate:
| Part | Tasks | Characters | How |. Exit 1 on errors, 2 when a file can't be read.
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

PLACEHOLDER = '<!-- TASKS -->'
NOTES = '#### Notes to orchestrator'
# SN listeners register on SMST's ListenerContainerInterface; Laravel-dispatched events never reach them.
DEFAULT_FORBID = [r'event\(new ', r'Illuminate\\Contracts\\Events\\Dispatcher', r'Event::dispatch']
TRAILER = re.compile(r'^\*\*(Out of scope|Sanity-check now|Tests)\b')
STEP = re.compile(r'^\s*- \[[ xX]\]')
PAUSED = re.compile(r'\bPAUSED \d{4}-\d{2}-\d{2}\b')
# Criterion ids, model.md §2: letters [a-z]+; ranges R1.a–R1.c and R1.a-c. The id edges and the range rule are the
# same as in check-contract.py and check-storyboard.py (copies, so this script stands alone).
AC = re.compile(r'(?<![\w-])R(\d+\.[a-z]+)(?![\w-])')
BARE_R = re.compile(r'(?<![\w-])R(\d+)(?![\w-]|\.[a-z])')
RANGE = re.compile(r'(?<![\w-])R(\d+)\.([a-z]+)(\s*)[–-](\s*)(R\1\.)?([a-z]+)(?![\w-])')
R_DEF = re.compile(r'^\s*(?:[-*]\s+)?(~~)?\*\*(R\d+)\*\*(.*)$')
AC_DEF = re.compile(r'^\s*(?:[-*]\s+)?(~~)?\*\*(R\d+)\.([a-z]+)\*\*(.*)$')
CONTRACT_ID = r"(?:R\d+(?:\.[a-z]+)?|Q\d+[a-z]?|J-\d+|s\d+(?:\.\d+)?|Part \d+|FB\d+)"
FOREIGN = re.compile(rf"(?:\b[A-Z][A-Z0-9]+-\d+(?:'s)?|\b[Rr]esearch)\s+{CONTRACT_ID}"
                     rf"(?:\s*(?:/|,|–|—|-|and|or|&|\+)\s*{CONTRACT_ID})*|\bresearch/R\d+")
# Only HTML comments are dropped: plans write trailer ids inside code spans (`out-of-suite: R10.a — …`).
COMMENT = re.compile(r'<!--.*?-->', re.S)
STEP_ID = re.compile(r'^(~~)?(s\d+\.\d+)(~~)?$')
PART_ID = re.compile(r'^(~~)?Part (\d+)(~~)?$')
S_ID = re.compile(r'(?<![\w-])(s\d+(?:\.\d+)?)(?![\w-]|\.\d)')
# The contract's stale check (model.md §5), called by sibling path; check-plan imports nothing from it.
CONTRACT_CHECK = Path(__file__).resolve().parent.parent.parent / 'skunexus-contract' / 'scripts' / 'check-contract.py'


def task_num(t):
    return int(t[1:])


def dep_ids(text):
    return re.findall(r'\bT\d+\b', re.sub(r'\([^)]*\)', '', text))


def lnum(s):
    n = 0
    for c in s:
        n = n * 26 + ord(c) - 96
    return n


def lstr(n):
    s = ''
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(97 + r) + s
    return s


def expand(text):
    """Write each criterion range out ('R1.a-c' -> 'R1.a, R1.b, R1.c'); a range that isn't one keeps its start,
    so "R6.a - needs" stays R6.a."""
    def one(m):
        n, a, s1, s2, pre, b = m.groups()
        if (pre or len(b) == len(a) or not (s1 or s2) and len(b) <= 2) and lnum(b) >= lnum(a):
            return ', '.join(f'R{n}.{lstr(i)}' for i in range(lnum(a), lnum(b) + 1))
        return f'R{n}.{a} ' + m.group(0)[len(f'R{n}.{a}'):]
    return RANGE.sub(one, text)


def cited(text):
    """Cited text without foreign ids and HTML comments (model.md §2.3-2.4), ranges written out."""
    return expand(FOREIGN.sub(' ', COMMENT.sub(' ', text)))


def ac_ids(text):
    return {f'R{x}' for x in AC.findall(cited(text))}


def bare_rs(text):
    return {f'R{n}' for n in BARE_R.findall(cited(text))}


def s_ids(text):
    return set(S_ID.findall(cited(text)))


def is_retired(lead, rest):
    return bool(lead) or 'retired' in rest[:80].lower()


def read_parts(parts_dir, plan=None):
    tasks, owner, notes, errors = {}, {}, {}, []
    if plan:
        text = plan.read_text(encoding='utf-8')
        start = re.search(r'(?m)^### T\d+ ', text)
        end = re.compile(r'(?m)^## ').search(text, start.end()) if start else None
        sources = [(plan.name, text[start.start():end.start() if end else None] if start else '')]
    else:
        sources = [(p.name, p.read_text(encoding='utf-8')) for p in sorted(parts_dir.glob('*.md')) if re.match(r'^[A-Z]-.+\.md$', p.name)]
    for name, text in sources:
        if PAUSED.search(text):
            errors.append(f'{name} is marked PAUSED: resume its drafter first')
        body, _, note = text.partition(NOTES)
        notes[name] = note.strip()
        for block in re.split(r'(?m)^(?=### T\d+ )', body):
            m = re.match(r'### (T\d+) ', block)
            if not m:
                continue
            t = m.group(1)
            if t in tasks:
                errors.append(f'{t} drafted twice: {owner[t]} and {name}')
            tasks[t], owner[t] = block.rstrip() + '\n', name
    return tasks, notes, errors


def insert_step(block, step):
    lines = block.rstrip('\n').split('\n')
    at = next((i for i, l in enumerate(lines) if TRAILER.match(l)), len(lines))
    while at > 0 and not lines[at - 1].strip():
        at -= 1
    lines.insert(at, step)
    return '\n'.join(lines) + '\n'


def waves_of(deps):
    """Kahn layering: wave = 1 + max(wave of deps). Returns (waves, cycle_members)."""
    level, left = {}, set(deps)
    while left:
        ready = sorted((t for t in left if all(d in level for d in deps[t])), key=task_num)
        if not ready:
            return None, sorted(left, key=task_num)
        for t in ready:
            level[t] = 1 + max((level[d] for d in deps[t]), default=0)
        left -= set(ready)
    waves = {}
    for t, w in level.items():
        waves.setdefault(w, []).append(t)
    return [sorted(waves[w], key=task_num) for w in sorted(waves)], []


def critical_path(waves, deps, steps):
    best = {}
    for wave in waves:
        for t in wave:
            prev = max(deps[t], key=lambda d: best[d][0], default=None)
            base = best[prev] if prev else (0, [])
            best[t] = (base[0] + steps[t], base[1] + [t])
    return max(best.values(), key=lambda v: v[0])


def trailer_text(block, label):
    """Text of each `**<label>...:**` line plus its continuation lines (to a blank line or the next ** / #)."""
    out, on = [], False
    for line in block.split('\n'):
        if line.startswith('**') or line.startswith('#') or not line.strip():
            on = line.startswith(f'**{label}')
        if on:
            out.append(line)
    return '\n'.join(out)


def section(text, heading):
    m = re.search(rf'(?ms)^## (?:{heading}).*?(?=^## |\Z)', text)
    return m.group(0) if m else ''


def read_prd(prd):
    """prd.md §4 and §6 -> (live criteria in order, retired criteria, {Rn: live criteria}, live Rn), or None."""
    if not prd.exists():
        return None
    text = prd.read_text(encoding='utf-8')
    live, retired, by_r = [], set(), {}
    for line in section(text, r'6\b|Acceptance').split('\n'):
        m = AC_DEF.match(line)
        if m:
            ac = f'{m.group(2)}.{m.group(3)}'
            if is_retired(m.group(1), m.group(4)):
                retired.add(ac)
            elif ac not in live:
                live.append(ac)
                by_r.setdefault(m.group(2), []).append(ac)
    reqs = []
    for line in section(text, r'4\b').split('\n'):
        m = R_DEF.match(line)
        if m and not is_retired(m.group(1), m.group(3)) and m.group(2) not in reqs:
            reqs.append(m.group(2))
    return live, retired, by_r, reqs


def cells(line):
    """A table row's cells, split as check-contract.py splits them (an escaped \\| stays in its cell), or None."""
    if not line.lstrip().startswith('|'):
        return None
    s = line.strip()[1:]
    s = s[:-1] if s.endswith('|') and not s.endswith('\\|') else s
    return [x.strip().replace('\\|', '|') for x in re.split(r'(?<!\\)\|', s)]


def row_retired(cs):
    return cs[0].startswith('~~') or any(c.lower().startswith(('(retired', 'retired')) for c in cs[1:])


def read_workflows(path):
    """workflows.md -> (live steps [(id, cited ids, part numbers)], {part number: live?}), or None."""
    if not path.exists():
        return None
    steps, parts, header = [], {}, []
    lines = path.read_text(encoding='utf-8').split('\n')
    for i, line in enumerate(lines):
        cs = cells(line)
        if cs is None:
            continue
        nxt = cells(lines[i + 1]) if i + 1 < len(lines) else None
        if nxt and all(re.fullmatch(r':?-+:?', c) for c in nxt if c):
            header = [c.lower() for c in cs]
            continue
        sm, pm = STEP_ID.match(cs[0]), PART_ID.match(cs[0])
        if sm and not row_retired(cs):
            col = {h: k for k, h in enumerate(header)}
            cite = cs[col['cites']] if 'cites' in col and col['cites'] < len(cs) else cs[-2]
            part = cs[col['part']] if 'part' in col and col['part'] < len(cs) else cs[-1]
            steps.append((sm.group(2), ac_ids(cite) | bare_rs(cite), re.findall(r'Part (\d+)', part)))
        elif pm and 'status' in header:
            parts[pm.group(2)] = not row_retired(cs)
    return steps, parts


def scenario_coverage(tasks, wf, report):
    """Each live scenario has a scenario test (a Tests: trailer citing s<n>) unless all its live steps are
    out-of-suite; `s1` in an out-of-suite line lists all of s1's steps. Returns warnings."""
    steps = [s for s, _, _ in wf[0]]
    scen = sorted({s.split('.')[0] for s in steps}, key=lambda x: int(x[1:]))
    tested = set().union(*(s_ids(trailer_text(b, 'Tests')) for b in tasks.values()))
    oos = set().union(*(s_ids(l) for b in tasks.values() for l in b.split('\n') if 'out-of-suite' in l.lower()))
    out = [f'{x} is cited in a trailer but is not a live scenario or step in workflows.md'
           for x in sorted((tested | oos) - set(steps) - set(scen), key=lambda x: [int(n) for n in x[1:].split('.')])]
    skipped = [s for s in scen if s not in tested and all(x in oos or s in oos for x in steps if x.split('.')[0] == s)]
    missing = [s for s in scen if s not in tested and s not in skipped]
    report.append(f'scenario coverage: {len(scen)} live · {len(scen) - len(skipped) - len(missing)} in Tests trailers'
                  f' · {len(skipped)} out-of-suite · {len(missing)} without a scenario test')
    return out + [f'scenario {s} has no scenario test: no Tests: trailer cites {s} (or list its steps out-of-suite)'
                  for s in missing]


def part_line(block):
    """The task's **Part:** line -> (its text, part numbers), or None. Reads "Part 2", "Parts 1 and 2", "Part 1, 3"."""
    m = re.search(r'(?m)^\*\*Part:\*\*(.*)$', block)
    if not m:
        return None
    runs = re.findall(r'\bParts?\s+(\d+(?:\s*(?:,|/|&|\+|and|or)\s*(?:Part\s+)?\d+)*)', m.group(1))
    return m.group(1).strip(), set(re.findall(r'\d+', ' '.join(runs)))


def task_parts(block, wf, prd):
    """(part numbers, how) for one task, per model.md §5: an explicit **Part:** line wins, else derived."""
    if (pl := part_line(block)) and pl[1]:
        return pl[1], 'explicit'
    by_r = prd[2] if prd else {}
    sat = re.search(r'(?m)^\*\*Satisfies:\*\*(.*)$', block)
    text = (sat.group(1) if sat else '') + '\n' + trailer_text(block, 'Tests')
    ids = ac_ids(text) | bare_rs(text)
    ids |= {ac for r in bare_rs(text) for ac in by_r.get(r, [])}
    found = set()
    for _, cites, parts in wf[0]:
        reach = cites | {ac for r in cites if '.' not in r for ac in by_r.get(r, [])}
        if ids & reach:
            found.update(parts)
    return found, 'derived'


def plan_sizes(text, tasks, wf, prd):
    """Plan characters per part. A task runs from `### T<n> ` to the next `### T` or `## ` (the estimate's measure)."""
    chars = {}
    for x in re.split(r'(?m)^(?=### T\d+ )', text):
        m = re.match(r'### (T\d+) ', x)
        if m:
            chars[m.group(1)] = len(x.split('\n## ')[0])
    rows, how_of = {}, {}
    for t in sorted(tasks, key=task_num):
        if wf is None:
            key, how = 'Part 1', 'no parts'
        else:
            parts, how = task_parts(tasks[t], wf, prd)
            key = 'shared' if len(parts) > 1 else f'Part {next(iter(parts))}' if parts else 'unassigned'
            how = 'shared' if key == 'shared' else 'unassigned' if key == 'unassigned' else how
        rows.setdefault(key, []).append(t)
        how_of.setdefault(key, set()).add(how)
    live_parts = [f'Part {p}' for p, live in sorted((wf[1] if wf else {'1': True}).items(), key=lambda kv: int(kv[0])) if live]
    order = live_parts + sorted((k for k in rows if k.startswith('Part ') and k not in live_parts),
                                key=lambda k: int(k[5:])) + ['shared', 'unassigned']
    table = ['| Part | Tasks | Characters | How |', '|---|---|---|---|']
    for k in order:
        ts = rows.get(k, [])
        table.append(f'| {k} | {", ".join(ts) or "—"} | {sum(chars.get(t, 0) for t in ts)} | '
                     f'{", ".join(sorted(how_of.get(k, []))) or "—"} |')
    total = sum(chars.get(t, 0) for t in tasks)
    table.append(f'| total | {len(tasks)} tasks | {total} | — |')
    table.append(f'Text outside tasks: {len(text) - sum(chars.values())} characters (unassigned).')
    return table


def stale_check(plan_path):
    """Run skunexus-contract's `--stale` on the plan (model.md §5). Returns (report lines, warnings)."""
    if not re.search(r'(?m)^> Built from:', plan_path.read_text(encoding='utf-8')):
        return ['stale check: no base (no `> Built from:` line), counts as current'], []
    if not CONTRACT_CHECK.exists():
        return ['stale check skipped: skunexus-contract not installed'], []
    r = subprocess.run([sys.executable, '-I', str(CONTRACT_CHECK), '--stale', str(plan_path)],
                       capture_output=True, text=True, encoding='utf-8')
    lines = [l for l in r.stdout.split('\n') if l.strip()]
    if r.returncode == 0:
        return ['stale check: current'], []
    if r.returncode == 3:
        return ['stale check: no base, counts as current'], []
    if r.returncode == 1:
        return ['stale check: stale'], [l for l in lines if l.startswith('stale ')] or ['plan is stale']
    return [], [f'stale check failed (exit {r.returncode}): {(lines or [r.stderr.strip()])[-1][:140]}']


def run(ticket, deps_path, check_only, forbid, stale_names, from_plan=False, sizes=False):
    errors, warnings, report = [], [], []
    parts_dir = ticket / 'plan-parts'
    plan_path = ticket / 'backend-plan.md'
    tasks, notes, dup = read_parts(parts_dir, plan_path if from_plan else None)
    errors += dup
    if not tasks:
        return [f'no tasks found in {"backend-plan.md" if from_plan else f"{parts_dir}/[A-Z]-*.md"}'], warnings, report
    cfg = json.loads(deps_path.read_text(encoding='utf-8')) if deps_path and deps_path.exists() and not from_plan else {}
    check_only = check_only or from_plan

    deps, dep_line = {}, {}
    for t, block in tasks.items():
        m = re.search(r'(?m)^\*\*Depends on:\*\*(.*)$', block)
        if not m:
            errors.append(f'{t}: no **Depends on:** line')
            continue
        given = cfg.get('deps', {}).get(t)
        line = (', '.join(given) if isinstance(given, list) else given) if given is not None else m.group(1).strip()
        dep_line[t] = line or 'none'
        deps[t] = dep_ids(line)
        tasks[t] = block[:m.start(1)] + ' ' + dep_line[t] + block[m.end(1):]
    for t in cfg.get('deps', {}):
        if t not in tasks:
            errors.append(f'deps.json lists {t}, which no part drafts')
    for t, ds in deps.items():
        for d in ds:
            if d not in tasks:
                errors.append(f'{t} depends on unknown {d}')
    for t, step in cfg.get('inserts', {}).items():
        if t in tasks:
            tasks[t] = insert_step(tasks[t], step)
        else:
            errors.append(f'insert for unknown {t}')
    if errors:
        return errors, warnings, report

    waves, cycle = waves_of(deps)
    if cycle:
        return [f'dependency cycle among: {" ".join(cycle)}'], warnings, report
    order = cfg.get('order') or [t for w in waves for t in w]
    missing = [t for t in tasks if t not in order]
    extra = [t for t in order if t not in tasks]
    if missing or extra:
        errors.append(f'order vs parts: not drafted={extra} not in order={missing}')
    if not cfg.get('order'):
        nums = sorted(map(task_num, tasks))
        gaps = [f'T{n}' for n in range(nums[0], nums[-1]) if n not in nums]
        if gaps:
            warnings.append(f'no task {" ".join(gaps)} in any part: undrafted? Put every DAG task in deps.json `order`')
    pos = {t: i for i, t in enumerate(order)}
    errors += [f'order puts {t} before its dependency {d}' for t in order if t in deps
               for d in deps[t] if d in pos and pos[d] > pos[t]]

    steps = {t: sum(1 for l in b.split('\n') if STEP.match(l)) for t, b in tasks.items()}
    report.append(f'{"plan" if from_plan else f"parts {len(notes)}"} · tasks {len(tasks)} · steps {sum(steps.values())}')
    report.append(f'waves {len(waves)} · peak width {max(map(len, waves))} · '
                  + ' · '.join(f'W{i} ({len(w)}): {" ".join(w)}' for i, w in enumerate(waves, 1)))
    total, path = critical_path(waves, deps, steps)
    sync = sum(max(steps[t] for t in w) for w in waves)
    report.append(f'critical path {total} steps: {" → ".join(f"{t}({steps[t]})" for t in path)}'
                  f' · wave-synchronous {sync} steps (largest task per wave, summed)')

    prd = read_prd(ticket / 'prd.md')
    # A `> Tests: none` plan (backend-plan Step 1) carries no trailers, so per-criterion coverage doesn't apply.
    tests_none = any(re.search(r'> Tests:\s*none\b', p.read_text(encoding='utf-8'))
                     for p in (plan_path, parts_dir / 'BRIEF.md') if p.exists())
    if tests_none:
        report.append('AC coverage: skipped (> Tests: none)')
    elif prd is None:
        report.append('AC coverage: skipped (no prd.md)')
    elif not prd[0]:
        warnings.append('AC coverage: no `- **Rn.x**` criteria found in prd.md §6')
    else:
        live, retired, by_r, reqs = prd
        bulletless = [r for r in reqs if r not in by_r]  # cited as `Rn` itself (lite, or no live criterion left)
        need = live + bulletless
        tested = set().union(*(ac_ids(t) | bare_rs(t) for t in (trailer_text(b, 'Tests') for b in tasks.values())))
        oos = set().union(*(ac_ids(l) | bare_rs(l) for b in tasks.values() for l in b.split('\n')
                            if 'out-of-suite' in l.lower()))
        uncovered = [a for a in need if a not in tested | oos]
        only_oos = [a for a in need if a in oos and a not in tested]
        report.append(f'AC coverage: {len(live)} live in prd.md §6'
                      + (f' + {len(bulletless)} requirements without criteria' if bulletless else '')
                      + (f' ({len(retired)} retired, not needed)' if retired else '')
                      + f' · {len(need) - len(uncovered) - len(only_oos)} in Tests trailers'
                      f' · {len(only_oos)} out-of-suite only · {len(uncovered)} uncovered')
        if uncovered:
            errors.append(f'uncovered AC: {", ".join(uncovered)}')
        key = lambda a: (int(re.match(r'R(\d+)', a).group(1)), a)
        acs_cited = {a for a in tested | oos if '.' in a}
        old = sorted(acs_cited & retired, key=key)
        if old:
            warnings.append(f'retired criteria still cited: {", ".join(old)}')
        unknown = sorted(acs_cited - set(live) - retired, key=key)
        if unknown:
            warnings.append(f'AC ids cited but not in prd.md §6: {", ".join(unknown)}')
        for t, b in tasks.items():
            bare = sorted(r for r in bare_rs(trailer_text(b, 'Tests')) if r in by_r)
            if bare:
                warnings.append(f'{t} Tests trailer cites bare {", ".join(bare)} (cite criterion ids)')

    for label, patterns in (('mechanism', DEFAULT_FORBID + forbid), ('stale name', [re.escape(s) for s in stale_names])):
        for t in order:
            for line in tasks.get(t, '').split('\n'):
                hit = next((p for p in patterns if re.search(p, line)), None)
                if hit:
                    errors.append(f'{label} /{hit}/ in {t}: {line.strip()[:140]}')

    wf = read_workflows(ticket / 'workflows.md')
    if wf is not None:
        for t, b in tasks.items():
            pl = part_line(b)
            if pl and not pl[1]:
                warnings.append(f'{t}: **Part:** "{pl[0][:40]}" names no "Part <n>": the part is derived instead')
            for p in sorted(pl[1], key=int) if pl else []:
                if p not in wf[1]:
                    errors.append(f'{t}: **Part:** Part {p} is not in workflows.md "Parts"')
                elif not wf[1][p]:
                    warnings.append(f'{t}: **Part:** Part {p} is retired in workflows.md')
        if not tests_none:
            warnings += scenario_coverage(tasks, wf, report)

    table = []
    if from_plan:
        lines, warns = stale_check(plan_path)
        report += lines
        warnings += warns
        if sizes:
            table = plan_sizes(plan_path.read_text(encoding='utf-8'), tasks, wf, prd)

    if not check_only and not errors:
        plan = plan_path.read_text(encoding='utf-8') if plan_path.exists() else ''
        if PLACEHOLDER not in plan:
            errors.append(f'{plan_path} has no {PLACEHOLDER} line; create it from the skunexus-backend-plan template '
                          f'with that line where the tasks go (refusing to write)')
        else:
            plan_path.write_text(plan.replace(PLACEHOLDER, '\n'.join(tasks[t].rstrip() + '\n' for t in order), 1), encoding='utf-8')
            (parts_dir / 'NOTES-collected.md').write_text('\n\n'.join(f'## {k}\n{v}' for k, v in notes.items()) + '\n', encoding='utf-8')
            report.append(f'wrote {plan_path} and {parts_dir / "NOTES-collected.md"}')
    return errors, warnings, report + ([''] + table if table else [])


def selftest():
    global CONTRACT_CHECK
    assert ac_ids('R6.a - needs a live worker') == {'R6.a'}
    assert ac_ids('R1.a-c, R2.z–R2.ab') == {'R1.a', 'R1.b', 'R1.c', 'R2.z', 'R2.aa', 'R2.ab'}
    assert ac_ids('FFD-14 R31.a, <!-- R9.a --> and `R4.b`') == {'R4.b'}
    assert ac_ids('R1.z-aa; R2.a - aa; R3.a-based') == {'R1.z', 'R1.aa', 'R2.a', 'R3.a'}
    assert ac_ids('ORD-R2.a, R12-B') == set() and bare_rs('SKU R12-B, R5.') == {'R5'}
    assert cells('| s1.1 | a \\| b | R1.a | Part 2 |') == ['s1.1', 'a | b', 'R1.a', 'Part 2']
    with tempfile.TemporaryDirectory() as d:
        ticket = Path(d)
        (ticket / 'plan-parts').mkdir()
        (ticket / 'prd.md').write_text('## 6. Acceptance Criteria\n- **R1.a** x\n- **R1.b** y\n- **R2.a** z\n## 7. Q\n', encoding='utf-8')
        (ticket / 'backend-plan.md').write_text('# Plan\n\n## Tasks\n<!-- TASKS -->\n', encoding='utf-8')
        (ticket / 'plan-parts' / 'A-one.md').write_text(
            '### T1 — a\n**Depends on:** none\n\n- [ ] step\n- [ ] step\n\n**Tests:** `t.php` — R1.a–R1.b\n'
            '\n#### Notes to orchestrator\nnote A\n', encoding='utf-8')
        (ticket / 'plan-parts' / 'B-two.md').write_text(
            '### T2 — b\n**Depends on:** T1 (tests only)\n\n- [ ] dispatch via `event(new X)`\n\n'
            '**Sanity-check now:** run it\n', encoding='utf-8')
        (ticket / 'plan-parts' / 'BRIEF.md').write_text('### T9 — not a part\n', encoding='utf-8')
        errors, _, report = run(ticket, None, True, [], [])
        assert any('uncovered AC: R2.a' in e for e in errors), errors
        assert any('mechanism /event\\(new / in T2' in e for e in errors), errors
        assert 'waves 2' in report[1] and 'critical path 3 steps' in report[2], report
        assert 'TASKS' in (ticket / 'backend-plan.md').read_text(encoding='utf-8')  # check-only wrote nothing
        (ticket / 'plan-parts' / 'BRIEF.md').write_text('### T9 — not a part\nPlan header: `> Tests: none — config only`\n', encoding='utf-8')
        errors, _, report = run(ticket, None, True, [], [])
        assert not any('uncovered AC' in e for e in errors) and '> Tests: none' in report[3], (errors, report)
        (ticket / 'plan-parts' / 'BRIEF.md').write_text('### T9 — not a part\n', encoding='utf-8')
        (ticket / 'plan-parts' / 'B-two.md').write_text(
            '### T2 — b\n**Depends on:** T1\n\n- [ ] dispatch via EventBusInterface\n\n'
            '**Sanity-check now:** out-of-suite: R2.a — MySQL only\n', encoding='utf-8')
        (ticket / 'plan-parts' / 'deps.json').write_text(json.dumps({'inserts': {'T1': '- [ ] inserted'}}), encoding='utf-8')
        errors, _, report = run(ticket, ticket / 'plan-parts' / 'deps.json', False, [], [])
        plan = (ticket / 'backend-plan.md').read_text(encoding='utf-8')
        assert not errors, errors
        assert plan.index('inserted') < plan.index('**Tests:**') < plan.index('### T2'), plan
        assert (ticket / 'plan-parts' / 'NOTES-collected.md').read_text(encoding='utf-8').startswith('## A-one.md\nnote A')
        (ticket / 'plan-parts' / 'deps.json').write_text(json.dumps({'deps': {'T1': ['T2']}}), encoding='utf-8')
        errors, _, _ = run(ticket, ticket / 'plan-parts' / 'deps.json', True, [], [])
        assert errors and 'cycle' in errors[0], errors
        errors, _, report = run(ticket, None, False, [], ['inserted'], from_plan=True)
        assert report[0].startswith('plan · tasks 2 · steps 4') and 'stale name' in errors[0], (report, errors)
        assert any('stale check: no base' in r for r in report), report
        (ticket / 'plan-parts' / 'deps.json').unlink()
        (ticket / 'plan-parts' / 'C-four.md').write_text(
            '### T4 — d\n> ASSEMBLY PAUSED 2026-10-28 14:05: done none; partial T4; next: steps\n**Depends on:** T1, T5\n', encoding='utf-8')
        errors, warnings, _ = run(ticket, None, True, [], [])
        assert any('C-four.md is marked PAUSED' in e for e in errors), errors
        assert any('T4 depends on unknown T5' in e for e in errors), errors
        (ticket / 'plan-parts' / 'C-four.md').write_text('### T4 — d\n**Depends on:** T1\n\n- [ ] step\n', encoding='utf-8')
        errors, warnings, _ = run(ticket, None, True, [], [])
        assert any('no task T3 in any part' in w for w in warnings), warnings
        (ticket / 'plan-parts' / 'deps.json').write_text(json.dumps({'order': ['T1', 'T2', 'T3', 'T4']}), encoding='utf-8')
        errors, _, _ = run(ticket, ticket / 'plan-parts' / 'deps.json', True, [], [])
        assert any("not drafted=['T3']" in e for e in errors), errors

    with tempfile.TemporaryDirectory() as d:  # v2: letters [a-z]+, retired criteria, bullet-less Rn, parts
        ticket = Path(d)
        (ticket / 'prd.md').write_text(
            '> Status: Approved\n## 4. Requirements\n- **R1** a\n- **R2** b\n- **R3** c, no criterion\n'
            '- **R4** (retired 2026-11-03: merged into R1 → see R1)\n## 6. Acceptance Criteria\n'
            '- **R1.a** x\n- **R1.z** x\n- **R1.aa** x\n- **R1.ab** x\n- **R2.a** y\n'
            '- **R2.b** (retired 2026-11-03: no longer true → see R2.a)\n- ~~**R2.c**~~ retired\n## 7. Q\n', encoding='utf-8')
        task = '### T{n} — t{n}\n**Status:** not_started\n**Depends on:** {dep}\n**Satisfies:** {sat}\n{part}\n- [ ] step\n\n{tests}\n'
        body = ''.join(task.format(n=n, dep=dep, sat=sat, part=part, tests=tests) for n, dep, sat, part, tests in (
            (1, 'none', 'R1', '', '**Tests:** `a.php` — R1.a, R1.z–R1.ab, FFD-14 R9.a'),
            (2, 'T1', 'R2', '', '**Tests:** `b.php` — R2.a, R2.b'),
            (3, 'T1', 'R1, R2', '', '**Tests:** `c.php` — R1.a, R2.a'),
            (4, 'none', 'R1', '**Part:** Part 2', ''),
            (5, 'none', 'R3', '', '**Sanity-check now:** out-of-suite: R3 — live worker')))
        (ticket / 'backend-plan.md').write_text(f'# Plan\n\n## Tasks\n\n{body}\n## Open Questions\n- none\n', encoding='utf-8')
        errors, warnings, report = run(ticket, None, True, [], [], from_plan=True, sizes=True)
        assert not errors, errors
        assert any('5 live in prd.md §6 + 1 requirements without criteria (2 retired' in r and '0 uncovered' in r
                   for r in report), report
        assert any('retired criteria still cited: R2.b' in w for w in warnings), warnings
        assert not any('not in prd.md' in w for w in warnings), warnings
        assert '| Part 1 | T1, T2, T3, T4, T5 | ' in '\n'.join(report) and 'no parts' in '\n'.join(report), report
        (ticket / 'backend-plan.md').write_text(
            (ticket / 'backend-plan.md').read_text(encoding='utf-8').replace('**Tests:** `c.php` — R1.a, R2.a', '**Tests:** `c.php` — R1.a'), encoding='utf-8')
        errors, _, _ = run(ticket, None, True, [], [], from_plan=True)
        assert errors == [], errors  # R2.a is still covered by T2
        (ticket / 'workflows.md').write_text(
            '# Workflows: X\n\n## s1. One\n| Step | Actor | Trigger | Before → after | Outcome | Cites | Part |\n'
            '|---|---|---|---|---|---|---|\n| s1.1 | user | user | a → b | ok \\| fine | R1.a, R1.z | Part 1 |\n'
            '| s1.2 | user | user | b → c | ok | R2 | Part 2 |\n'
            '| s1.3 | user | user | c → d | (retired 2026-11-03, v2: gone) | R3 | Part 1 |\n\n'
            '## Parts\n| Part | Name | Scope | PO\'s shape | Status |\n|---|---|---|---|---|\n'
            '| Part 1 | Base | The base. | base | live |\n| Part 2 | Extra | More. | priced | live |\n'
            '| Part 3 | Gone | Old. | priced | retired v2: merged into Part 1 |\n', encoding='utf-8')
        plan = (ticket / 'backend-plan.md').read_text(encoding='utf-8')
        (ticket / 'backend-plan.md').write_text(plan.replace('**Tests:** `c.php` — R1.a', '**Tests:** `c.php` — R1.a, R2.a'), encoding='utf-8')
        errors, warnings, report = run(ticket, None, True, [], [], from_plan=True, sizes=True)
        out = '\n'.join(report)
        assert not errors, errors
        for row in ('| Part 1 | T1 | ', '| Part 2 | T2, T4 | ', '| shared | T3 | ', '| unassigned | T5 | ', '| total | 5 tasks | '):
            assert row in out, (row, out)
        assert 'Part 3' not in out and 'derived, explicit |' in out, out
        # scenario coverage: s1 is live and no Tests trailer cites it; then a scenario test, then all out-of-suite
        assert any('scenario s1 has no scenario test' in w for w in warnings), warnings
        assert 'scenario coverage: 1 live · 0 in Tests trailers · 0 out-of-suite · 1 without' in out, out
        plan = (ticket / 'backend-plan.md').read_text(encoding='utf-8')
        (ticket / 'backend-plan.md').write_text(plan.replace('`a.php` — R1.a,', '`a.php` — s1 (s1.1, s1.2), R1.a,'), encoding='utf-8')
        _, warnings, report = run(ticket, None, True, [], [], from_plan=True)
        assert not any('scenario' in w for w in warnings) and any('1 in Tests trailers' in r for r in report), warnings
        oos = plan.replace('out-of-suite: R3 — live worker', 'out-of-suite: R3, s1.1 — live worker; `out-of-suite: s1.2 — UI only`')
        (ticket / 'backend-plan.md').write_text(oos.replace('R1.a, R1.z', 's9.1, R1.a, R1.z'), encoding='utf-8')
        _, warnings, report = run(ticket, None, True, [], [], from_plan=True)
        assert [w for w in warnings if 'scenario' in w] == ['s9.1 is cited in a trailer but is not a live scenario or step in '
                                                       'workflows.md'], warnings
        assert any('0 in Tests trailers · 1 out-of-suite · 0 without' in r for r in report), report
        (ticket / 'backend-plan.md').write_text(plan, encoding='utf-8')
        text = (ticket / 'backend-plan.md').read_text(encoding='utf-8')
        t1 = text[text.index('### T1 '):text.index('### T2 ')]
        assert f'| Part 1 | T1 | {len(t1)} | derived |' in out, out
        (ticket / 'backend-plan.md').write_text(text.replace('**Part:** Part 2', '**Part:** Part 4'), encoding='utf-8')
        errors, _, _ = run(ticket, None, True, [], [], from_plan=True)
        assert any('T4: **Part:** Part 4 is not in workflows.md' in e for e in errors), errors
        (ticket / 'backend-plan.md').write_text(text.replace('**Part:** Part 2', '**Part:** Parts 1 and 2'), encoding='utf-8')
        _, _, report = run(ticket, None, True, [], [], from_plan=True, sizes=True)
        assert '| shared | T3, T4 | ' in '\n'.join(report), report
        (ticket / 'backend-plan.md').write_text(text.replace('**Part:** Part 2', '**Part:** both'), encoding='utf-8')
        _, warnings, report = run(ticket, None, True, [], [], from_plan=True, sizes=True)
        assert any('T4: **Part:** "both" names no' in w for w in warnings), warnings
        assert '| Part 1 | T1, T4 | ' in '\n'.join(report), report
        # A non-UTF-8 locale reads and prints the plan ('→', '—'); a missing plan exits 2, not a traceback.
        env = {'LC_ALL': 'C', 'PYTHONCOERCECLOCALE': '0', 'PYTHONUTF8': '0', 'PATH': '/usr/bin:/bin'}
        r = subprocess.run([sys.executable, '-B', __file__, str(ticket), '--plan', '--sizes'], env=env,
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        assert r.returncode == 0 and 'Traceback' not in r.stderr, (r.returncode, r.stderr[-300:])
        r = subprocess.run([sys.executable, '-I', '-B', __file__, str(ticket / 'nope'), '--plan'],
                           capture_output=True, text=True, encoding='utf-8')
        assert r.returncode == 2 and 'cannot read' in r.stdout and 'Traceback' not in r.stderr, (r.stdout, r.stderr)
        (ticket / 'backend-plan.md').write_text('# Plan\n> Built from: contract v2 (2026-11-03)\n\n## Tasks\n' + body, encoding='utf-8')
        saved, CONTRACT_CHECK = CONTRACT_CHECK, ticket / 'missing' / 'check-contract.py'
        _, _, report = run(ticket, None, True, [], [], from_plan=True)
        assert 'stale check skipped: skunexus-contract not installed' in report, report
        CONTRACT_CHECK = ticket / 'fake-check-contract.py'
        CONTRACT_CHECK.write_text("print('stale R2.a: changed in v2.1'); print('result: stale'); raise SystemExit(1)\n", encoding='utf-8')
        _, warnings, report = run(ticket, None, True, [], [], from_plan=True)
        CONTRACT_CHECK = saved
        assert 'stale check: stale' in report and 'stale R2.a: changed in v2.1' in warnings, (report, warnings)
    print('selftest ok')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('ticket_dir', nargs='?')
    ap.add_argument('--deps', default='plan-parts/deps.json')
    ap.add_argument('--check-only', action='store_true')
    ap.add_argument('--plan', action='store_true', help='check backend-plan.md tasks instead of the parts')
    ap.add_argument('--sizes', action='store_true', help='with --plan: plan characters per part, for the estimate')
    ap.add_argument('--forbid', action='extend', nargs='+', default=[])
    ap.add_argument('--stale-name', action='extend', nargs='+', default=[], help='names a revision renamed')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.ticket_dir:
        ap.error('ticket_dir is required')
    if a.sizes and not a.plan:
        ap.error('--sizes needs --plan (it measures the assembled backend-plan.md)')
    ticket = Path(a.ticket_dir)
    deps = Path(a.deps)
    if not deps.is_absolute() and (ticket / deps).exists():
        deps = ticket / deps
    sys.stdout.reconfigure(errors='replace')  # a non-UTF-8 console shows '?' rather than crash on '→'
    try:
        errors, warnings, report = run(ticket, deps, a.check_only, a.forbid, a.stale_name, a.plan, a.sizes)
    except (OSError, UnicodeDecodeError, ValueError) as e:  # ValueError: a bad deps.json
        print(f'check-plan: cannot read: {e}')
        sys.exit(2)
    print('\n'.join(report + [f'WARN {w}' for w in warnings] + [f'ERROR {e}' for e in errors]))
    print(f'{"FAILED" if errors else "OK"}: {len(errors)} error(s), {len(warnings)} warning(s)'
          + (' (check-only, nothing written)' if a.check_only or a.plan else ''))
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
