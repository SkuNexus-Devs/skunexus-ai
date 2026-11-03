<!-- Stage: estimate, after backend-plan.md is assembled and passes assemble-plan-parts.py. Copy to .ai/<TICKET>/estimate.md; fill from the plan, the script's report and a measured velocity run. Ask the developer for the base hours first: they set the base, the add-ons are derived from it, and hours never go on the storyboard artifact.
     Extra placeholders: <PRD_STATUS>, <R_RANGE>, <PLAN_STATUS>, <N_TASKS>, <BASE_LOW>, <BASE_HIGH>, <RATE_LOW>, <RATE_HIGH>, <REF_TICKET>, <REF_REPO>. Standard placeholders: see SKILL.md. Delete the guidance comments once filled.
     When you present the estimate and no storyboard exists, offer one (the PO has asked for it on every ticket since FFD-14). -->
# <TICKET> — Estimate (backend)

> Draft for the Jira estimate (not posted). Based on `.ai/<TICKET>/prd.md` (<PRD_STATUS>, <R_RANGE>) and `.ai/<TICKET>/backend-plan.md` (<PLAN_STATUS> <DATE>, Tests: <behavior | none>, <N_TASKS> tasks).
> Backend only: the FE developer sizes the FE. The figures assume the PRD's §7 defaults; <Qn (topic), Qn (topic)> can still move them.
> Posted: not yet. The figures the developer posts in Jira are theirs and may differ from these; record them here (date, comment id) and don't re-argue them.

## Estimate: implementation incl. tests + review/rework

Each figure covers building the code with an orchestrated subagent run (automated tests included) plus the developer's review and rework of the result.

| Part | Hours | Scope |
|---|---|---|
| **1. <part name>** (base<, without …>) | **<BASE_LOW>–<BASE_HIGH>** | <1–2 plain sentences: what the client gets.> |
| **2. <part name>** (adds <the variant>) | **+<x>–<y>** | <1–2 plain sentences.> |
| **3. <part name>** (separately priced option, later phase) | **+<x>–<y>** | <1–2 plain sentences.> |
<!-- Keep the PO's estimate shape: the parts the ticket or PO asked for (FFD-14: base, with/without email, one priced option). Don't add parts a review panel proposes. One part: one row and no Totals table.
     Scope is for the PO or client: what they get, in plain words. No task ids, internal counts, file, mapping or field jargon, no feature lists. e.g. (FFD-14, Part 3): "Returned cores are put back into inventory as stock, instead of only being recorded as received."
     If the developer rewrites a Scope cell, re-read the file and keep their words verbatim; the storyboard's part cards copy this column. -->

**Totals:**

| Combination | Hours |
|---|---|
| Part 1 | <BASE_LOW>–<BASE_HIGH> |
| Parts 1 + 2 | <…> |
| Parts 1 + 3 | <…> |
| Parts 1 + 2 + 3 | <…> |

The low end assumes one review-and-rework pass. The high end allows a second pass, or <the integration most likely to need fixes>.

### How the figures are derived
- **The base is the developer's figure:** <BASE_LOW>–<BASE_HIGH> h for the <n> base tasks. Until they give it, leave the cell as `<ask the developer>` and offer the projection under "Agent wall-clock and projected code" as input.
- **Add-ons scale at the base's rate per plan size:** <BASE_LOW>–<BASE_HIGH> h ÷ <k>k base plan characters ≈ <RATE_LOW>–<RATE_HIGH> h per 1,000 plan characters. Plan characters measure size better than steps, because step size varies.
  - Part 2 (<task ids>, <k>k chars) comes to <x>–<y> h, plus a small fixed cost for <a new integration: its own mailer, faked-transport tests, template review>.
  - Part 3 (<task ids>, <k>k chars) comes to <x>–<y> h. A later phase adds its own run and review, and re-runs the suites it extends.
- **Reuse discount:** <none | what a precedent ticket's code saves (files, approximate % overlap) and why>.
<!-- Plan characters for a set of tasks:
     python3 -I -c "import re,sys; b=re.split(r'(?m)^(?=### T\d+ )', open(sys.argv[1]).read()); print(sum(len(x.split('\n## ')[0]) for x in b if re.match(r'### (%s) ' % '|'.join(sys.argv[2:]), x)))" .ai/<TICKET>/backend-plan.md T11 T21
     FFD-14: 16–20 h for ~125k chars of base tasks ≈ 0.13–0.16 h per 1k chars. -->

### Not in these figures
- FE, sized by the FE developer per page from the storyboard
- PR and code review
- MySQL check of the concurrency acceptance bullets: <Rn.x, Rn.x> (the suite runs on SQLite with a sync queue)
- Stage verification: <the flows that need real systems: carrier labels, connector pulls and pushes, …>
- QA support and fixes
- Deploy: <settings, migrations, one-off runs>
- <Part-specific prerequisites, e.g. with email only: the sending-domain DNS setup; the client's lead time is a dependency>
<!-- No hours on these lines: they depend on review, QA and release, not on the plan. -->

## Agent wall-clock and projected code
Only the implementation run depends on orchestration; the developer hours above barely change with it, because review and rework scale with the code, not with how it was produced.

| | Part 1 | Part 2 | Part 3 |
|---|---|---|---|
| Plan text | <k>k chars | <k>k chars | <k>k chars |
| Critical path | <s> steps, <w> waves, peak <p> agents | <runs in wave n beside Part 1> | <s> steps |
| Agent wall-clock | ~<h> h | <adds no time> | ~<m> min, as a separate run |
| Production code | ~<low>–<high> lines | <…> | <…> |
| Test code (final behavioral suite) | ~<low>–<high> lines | <…> | <…> |

- **Wall-clock** = the critical path (largest task per wave, summed: the script's "wave-synchronous" figure) × <min> min per critical-path step, plus ~20% when <n>+ agents share files.
- **Serial run:** one agent working through all <total> steps in order would take about <total ÷ critical>× longer (FFD-14: 255 vs 68 steps, ~3.7×).
- **Production lines:** high end = steps × <lines> lines per step; low end from plan characters × <ratio> code chars per plan char. Test lines = production × <test ratio>.

## Basis: <REF_TICKET> measured velocity (with tests)
Measured on `<REF_REPO>`, branch `<branch>`, base `<sha>`, <n> commits.

| Metric | <REF_TICKET> |
|---|---|
| Plan | <tasks> tasks, <steps> steps, <k>k chars, <w> waves, peak <p> agents |
| Diff | <prod> production lines, <test> test lines (<ratio>×) |
| Implementation | ~<min> min wall-clock (<date>, one commit per task) |
| Review rework | ~<h> h, first to last commit (<date>) |
| Ratios | <lines> production lines per step; <ratio> code chars per plan char; ~<min> min per critical-path step |

This basis is one run, <its size relative to this plan>. Its rework time is the span between the first and last commit, not logged effort. Re-measure after this ticket's run.
<!-- Measure the last comparable orchestrated run with Tests: behavior; don't reuse an earlier projection, and don't calibrate a tested plan on a run without tests (FFD-6 had none: 32 lines per step).
     One `sn-scout` subagent, read-only (TCM-150's took 38 s): "In <REF_REPO>, measure the orchestrated run of <REF_TICKET>: git log --reverse --date=iso and git diff --numstat for <base>..<branch>; production vs test lines (skip lock and generated files); implementation span (one commit per task) vs review-rework span; from .ai/<REF_TICKET>/backend-plan.md: tasks, steps, characters, waves, peak width. Compute lines per step, code chars per plan char, minutes per critical-path step. Reply in ≤15 lines."
     Fallback when nothing newer is measured, and say so: TCM-150 (2026-10): 14 tasks, 58 steps, 55k chars, 5 waves; 566 production + 1,170 test lines (2.07×); ~55 min implementation, ~2 h rework; 9.8 lines per step, 1.69 code chars per plan char, ~2 min per critical-path step. -->
