#!/usr/bin/env python3
"""Assemble drafter part files into backend-plan.md and run the mechanical plan checks.

Usage: python3 -I assemble-plan-parts.py <ticket-dir> [--deps plan-parts/deps.json] [--check-only | --plan]
                                          [--forbid <regex> ...] [--stale <name> ...] | --selftest

Parts: <ticket-dir>/plan-parts/[A-Z]-*.md, split at `### T<n> ` headings; each part's
`#### Notes to orchestrator` goes to plan-parts/NOTES-collected.md.
deps.json (all keys optional): {"order": ["T1", ...], "deps": {"T2": ["T1", "T0 (tests only)"]},
"inserts": {"T8": "- [ ] step appended before the task's trailers"}}.
Checks: paused parts (a `PAUSED <DATE>` line), missing/extra/duplicate tasks (against `order`; without it, gaps
in the task numbering), unknown deps, cycles, waves + critical path, AC coverage
against prd.md §6, forbidden mechanisms, stale names. --check-only writes nothing. --plan runs the same
checks on the tasks of an assembled (and later edited) backend-plan.md instead of the parts. Exit 1 on errors.
"""
import argparse
import json
import re
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
AC = re.compile(r'\bR(\d+)\.([a-z])\b(?:\s*[–-]\s*(?:R\1\.)?([a-z])\b)?')


def task_num(t):
    return int(t[1:])


def dep_ids(text):
    return re.findall(r'\bT\d+\b', re.sub(r'\([^)]*\)', '', text))


def ac_ids(text):
    out = set()
    for n, a, b in AC.findall(text):
        out.update(f'R{n}.{chr(c)}' for c in range(ord(a), ord(b or a) + 1))
    return out


def read_parts(parts_dir, plan=None):
    tasks, owner, notes, errors = {}, {}, {}, []
    if plan:
        text = plan.read_text()
        start = re.search(r'(?m)^### T\d+ ', text)
        end = re.compile(r'(?m)^## ').search(text, start.end()) if start else None
        sources = [(plan.name, text[start.start():end.start() if end else None] if start else '')]
    else:
        sources = [(p.name, p.read_text()) for p in sorted(parts_dir.glob('*.md')) if re.match(r'^[A-Z]-.+\.md$', p.name)]
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
    """Text of each `**<label>...:**` trailer plus its continuation lines (to a blank line or the next ** / #)."""
    out, on = [], False
    for line in block.split('\n'):
        if line.startswith('**') or line.startswith('#') or not line.strip():
            on = line.startswith(f'**{label}')
        if on:
            out.append(line)
    return '\n'.join(out)


def prd_acs(prd):
    if not prd.exists():
        return None
    m = re.search(r'(?ms)^## (?:6\b|Acceptance).*?(?=^## |\Z)', prd.read_text())
    return re.findall(r'(?m)^\s*- \*\*(R\d+\.[a-z])\*\*', m.group(0)) if m else []


def run(ticket, deps_path, check_only, forbid, stale, from_plan=False):
    errors, warnings, report = [], [], []
    parts_dir = ticket / 'plan-parts'
    tasks, notes, dup = read_parts(parts_dir, ticket / 'backend-plan.md' if from_plan else None)
    errors += dup
    if not tasks:
        return [f'no tasks found in {"backend-plan.md" if from_plan else f"{parts_dir}/[A-Z]-*.md"}'], warnings, report
    cfg = json.loads(deps_path.read_text()) if deps_path and deps_path.exists() and not from_plan else {}
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

    acs = prd_acs(ticket / 'prd.md')
    # A `> Tests: none` plan (backend-plan Step 1) carries no trailers, so per-bullet coverage doesn't apply.
    tests_none = any(re.search(r'> Tests:\s*none\b', p.read_text())
                     for p in (ticket / 'backend-plan.md', parts_dir / 'BRIEF.md') if p.exists())
    if tests_none:
        report.append('AC coverage: skipped (> Tests: none)')
    elif acs is None:
        report.append('AC coverage: skipped (no prd.md)')
    elif not acs:
        warnings.append('AC coverage: no `- **Rn.x**` bullets found in prd.md §6')
    else:
        tested = set().union(*(ac_ids(trailer_text(b, 'Tests')) for b in tasks.values()))
        oos = set().union(*(ac_ids(l) for b in tasks.values() for l in b.split('\n') if 'out-of-suite' in l.lower()))
        uncovered = [a for a in acs if a not in tested | oos]
        only_oos = [a for a in acs if a in oos and a not in tested]
        report.append(f'AC coverage: {len(acs)} in prd.md §6 · {len(acs) - len(uncovered) - len(only_oos)} in Tests trailers'
                      f' · {len(only_oos)} out-of-suite only · {len(uncovered)} uncovered')
        if uncovered:
            errors.append(f'uncovered AC: {", ".join(uncovered)}')
        unknown = sorted((tested | oos) - set(acs), key=lambda a: (int(a[1:a.index('.')]), a))
        if unknown and acs:
            warnings.append(f'AC ids cited but not in prd.md §6: {", ".join(unknown)}')
        for t, b in tasks.items():
            bare = re.findall(r'\bR\d+\b(?!\.[a-z])', trailer_text(b, 'Tests'))
            if bare:
                warnings.append(f'{t} Tests trailer cites bare {", ".join(sorted(set(bare)))} (cite bullet ids)')

    for label, patterns in (('mechanism', DEFAULT_FORBID + forbid), ('stale name', [re.escape(s) for s in stale])):
        for t in order:
            for line in tasks.get(t, '').split('\n'):
                hit = next((p for p in patterns if re.search(p, line)), None)
                if hit:
                    errors.append(f'{label} /{hit}/ in {t}: {line.strip()[:140]}')

    if not check_only and not errors:
        plan_path = ticket / 'backend-plan.md'
        plan = plan_path.read_text() if plan_path.exists() else ''
        if PLACEHOLDER not in plan:
            errors.append(f'{plan_path} has no {PLACEHOLDER} line; create it from the skunexus-backend-plan template '
                          f'with that line where the tasks go (refusing to write)')
        else:
            plan_path.write_text(plan.replace(PLACEHOLDER, '\n'.join(tasks[t].rstrip() + '\n' for t in order), 1))
            (parts_dir / 'NOTES-collected.md').write_text('\n\n'.join(f'## {k}\n{v}' for k, v in notes.items()) + '\n')
            report.append(f'wrote {plan_path} and {parts_dir / "NOTES-collected.md"}')
    return errors, warnings, report


def selftest():
    with tempfile.TemporaryDirectory() as d:
        ticket = Path(d)
        (ticket / 'plan-parts').mkdir()
        (ticket / 'prd.md').write_text('## 6. Acceptance Criteria\n- **R1.a** x\n- **R1.b** y\n- **R2.a** z\n## 7. Q\n')
        (ticket / 'backend-plan.md').write_text('# Plan\n\n## Tasks\n<!-- TASKS -->\n')
        (ticket / 'plan-parts' / 'A-one.md').write_text(
            '### T1 — a\n**Depends on:** none\n\n- [ ] step\n- [ ] step\n\n**Tests:** `t.php` — R1.a–R1.b\n'
            '\n#### Notes to orchestrator\nnote A\n')
        (ticket / 'plan-parts' / 'B-two.md').write_text(
            '### T2 — b\n**Depends on:** T1 (tests only)\n\n- [ ] dispatch via `event(new X)`\n\n'
            '**Sanity-check now:** run it\n')
        (ticket / 'plan-parts' / 'BRIEF.md').write_text('### T9 — not a part\n')
        errors, _, report = run(ticket, None, True, [], [])
        assert any('uncovered AC: R2.a' in e for e in errors), errors
        assert any('mechanism /event\\(new / in T2' in e for e in errors), errors
        assert 'waves 2' in report[1] and 'critical path 3 steps' in report[2], report
        assert 'TASKS' in (ticket / 'backend-plan.md').read_text()  # check-only wrote nothing
        (ticket / 'plan-parts' / 'BRIEF.md').write_text('### T9 — not a part\nPlan header: `> Tests: none — config only`\n')
        errors, _, report = run(ticket, None, True, [], [])
        assert not any('uncovered AC' in e for e in errors) and '> Tests: none' in report[3], (errors, report)
        (ticket / 'plan-parts' / 'BRIEF.md').write_text('### T9 — not a part\n')
        (ticket / 'plan-parts' / 'B-two.md').write_text(
            '### T2 — b\n**Depends on:** T1\n\n- [ ] dispatch via EventBusInterface\n\n'
            '**Sanity-check now:** out-of-suite: R2.a — MySQL only\n')
        (ticket / 'plan-parts' / 'deps.json').write_text(json.dumps({'inserts': {'T1': '- [ ] inserted'}}))
        errors, _, report = run(ticket, ticket / 'plan-parts' / 'deps.json', False, [], [])
        plan = (ticket / 'backend-plan.md').read_text()
        assert not errors, errors
        assert plan.index('inserted') < plan.index('**Tests:**') < plan.index('### T2'), plan
        assert (ticket / 'plan-parts' / 'NOTES-collected.md').read_text().startswith('## A-one.md\nnote A')
        (ticket / 'plan-parts' / 'deps.json').write_text(json.dumps({'deps': {'T1': ['T2']}}))
        errors, _, _ = run(ticket, ticket / 'plan-parts' / 'deps.json', True, [], [])
        assert errors and 'cycle' in errors[0], errors
        errors, _, report = run(ticket, None, False, [], ['inserted'], from_plan=True)
        assert report[0].startswith('plan · tasks 2 · steps 4') and 'stale name' in errors[0], (report, errors)
        (ticket / 'plan-parts' / 'deps.json').unlink()
        (ticket / 'plan-parts' / 'C-four.md').write_text(
            '### T4 — d\n> ASSEMBLY PAUSED 2026-10-28 14:05: done none; partial T4; next: steps\n**Depends on:** T1, T5\n')
        errors, warnings, _ = run(ticket, None, True, [], [])
        assert any('C-four.md is marked PAUSED' in e for e in errors), errors
        assert any('T4 depends on unknown T5' in e for e in errors), errors
        (ticket / 'plan-parts' / 'C-four.md').write_text('### T4 — d\n**Depends on:** T1\n\n- [ ] step\n')
        errors, warnings, _ = run(ticket, None, True, [], [])
        assert any('no task T3 in any part' in w for w in warnings), warnings
        (ticket / 'plan-parts' / 'deps.json').write_text(json.dumps({'order': ['T1', 'T2', 'T3', 'T4']}))
        errors, _, _ = run(ticket, ticket / 'plan-parts' / 'deps.json', True, [], [])
        assert any("not drafted=['T3']" in e for e in errors), errors
    print('selftest ok')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('ticket_dir', nargs='?')
    ap.add_argument('--deps', default='plan-parts/deps.json')
    ap.add_argument('--check-only', action='store_true')
    ap.add_argument('--plan', action='store_true', help='check backend-plan.md tasks instead of the parts')
    ap.add_argument('--forbid', action='extend', nargs='+', default=[])
    ap.add_argument('--stale', action='extend', nargs='+', default=[])
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.ticket_dir:
        ap.error('ticket_dir is required')
    ticket = Path(a.ticket_dir)
    deps = Path(a.deps)
    if not deps.is_absolute() and (ticket / deps).exists():
        deps = ticket / deps
    errors, warnings, report = run(ticket, deps, a.check_only, a.forbid, a.stale, a.plan)
    print('\n'.join(report + [f'WARN {w}' for w in warnings] + [f'ERROR {e}' for e in errors]))
    print(f'{"FAILED" if errors else "OK"}: {len(errors)} error(s), {len(warnings)} warning(s)'
          + (' (check-only, nothing written)' if a.check_only or a.plan else ''))
    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
