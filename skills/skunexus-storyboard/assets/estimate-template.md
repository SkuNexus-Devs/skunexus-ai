<!-- Estimate, after backend-plan.md (G3) and frontend-plan.md. Copy to .ai/<TICKET>/estimate.md; fill from check-plan.py --sizes, the FE plan's
     "FE hours per part", workflows.md "Parts" and a measured velocity run. Ask the developer for the base hours first: they set the base, the other
     parts are derived from it, and hours never go on the storyboard.
     Extra placeholders: <N>, <HASH_PLAN>, <HASH_FE>, <BASE_LOW>, <BASE_HIGH>, <RATE_LOW>, <RATE_HIGH>, <REF_TICKET>, <REF_REPO>.
     Standard placeholders: see SKILL.md. Delete the guidance comments once filled. -->
# <TICKET> — Estimate

> Status: Draft for the Jira estimate (not posted)
> Built from: contract v<N> (<DATE>) · backend-plan.md@<HASH_PLAN> · frontend-plan.md@<HASH_FE>
> FE: <confirmed by the FE developer <DATE> | draft for the FE developer to confirm or replace>. The figures assume the contract's assumed defaults; <Qn (topic), Qn (topic)> can still move them.
> Posted: not yet. The figures the developer posts in Jira are theirs and may differ; record them here (date, comment id) and don't re-argue them.

## Estimate: implementation incl. tests + review and rework

Each figure covers building the code, BE with an orchestrated subagent run (automated tests included) and FE by the FE developer, plus review and rework of the result.

| Part | Hours | Scope |
|---|---|---|
| **1. <Name>** (<PO's shape>) | **<low>–<high>** | <Scope, verbatim from workflows.md> |
| **2. <Name>** (<PO's shape>) | **+<x>–<y>** | <Scope, verbatim> |
<!-- One row per live part of workflows.md "Parts", in its order; never add, merge or drop a part here. One part: one row and no Totals table.
     Name and Scope verbatim: the storyboard's part cards copy the same text. To reword them, change workflows.md through skunexus-contract. -->

**Totals:**

| Combination | Hours |
|---|---|
| Part 1 | <low>–<high> |
| Parts 1 + 2 | <…> |

The low end assumes one review-and-rework pass. The high end allows a second pass, or <the integration most likely to need fixes>.

### How the figures are derived

| Part | BE hours | FE hours | Plan characters (How) |
|---|---|---|---|
| Part 1 | <BASE_LOW>–<BASE_HIGH> | <from frontend-plan.md> | <k>k (<explicit / derived / no parts>) |
| Part 2 | <x>–<y> | <…> | <k>k |
| shared / unassigned | <split as the developer decided> | <FE shared row, split> | <k>k |

- **The BE base is the developer's figure:** <BASE_LOW>–<BASE_HIGH> h for Part 1's <k>k plan characters. Until they give it, leave the cell as `<ask the developer>` and offer the projection at the calibrated rate.
- **Other parts scale at the base's rate:** <BASE_LOW>–<BASE_HIGH> h ÷ <k>k ≈ <RATE_LOW>–<RATE_HIGH> h per 1,000 plan characters (`check-plan.py --plan --sizes`).
  - Part 2 (<task ids>, <k>k characters) comes to <x>–<y> h, plus a small fixed cost for <a new integration: its own mailer, faked-transport tests, template review>.
- **Shared and unassigned:** <k>k characters (<task ids, text outside tasks>), split <how the developer decided>.
- **FE:** per part from `frontend-plan.md` "FE hours per part"; its `shared` row split <how>.
- **Reuse discount:** <none | what a precedent ticket's code saves and why>.

### Not in these figures
- PR and code review
- MySQL check of the concurrency criteria: <Rn.x, Rn.x> (the suite runs on SQLite with a sync queue)
- Stage verification: <the flows that need real systems: carrier labels, connector pulls and pushes, …>
- QA support and fixes
- Deploy: <settings, migrations, one-off runs>
- <Part-specific prerequisites, e.g. the sending-domain DNS setup; the client's lead time is a dependency>
<!-- No hours on these lines: they depend on review, QA and release, not on the plan. -->

## Agent wall-clock and projected code (BE)
Only the implementation run depends on orchestration; the developer hours above barely change with it, because review and rework scale with the code, not with how it was produced.

| | Part 1 | Part 2 |
|---|---|---|
| Plan text | <k>k chars | <k>k chars |
| Critical path | <s> steps, <w> waves, peak <p> agents | <runs in wave n beside Part 1> |
| Agent wall-clock | ~<h> h | <adds no time> |
| Production code | ~<low>–<high> lines | <…> |
| Test code (final behavioural suite) | ~<low>–<high> lines | <…> |

- **Wall-clock** = the critical path (largest task per wave, summed: `check-plan.py`'s wave-synchronous figure) × <min> min per critical-path step, plus ~20% when <n>+ agents share files.
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
     Velocity probe, one `sn-scout`, read-only: "In <REF_REPO>, measure the orchestrated run of <REF_TICKET>: git log --reverse --date=iso and git diff --numstat for <base>..<branch>; production vs test lines (skip lock and generated files); implementation span (one commit per task) vs review-rework span; from .ai/<REF_TICKET>/backend-plan.md: tasks, steps, characters, waves, peak width. Compute lines per step, code chars per plan char, minutes per critical-path step. Reply in ≤15 lines."
     Fallback when nothing newer is measured, and say so: TCM-150 (2026-10): 14 tasks, 58 steps, 55k chars, 5 waves; 566 production + 1,170 test lines (2.07×); ~55 min implementation, ~2 h rework; 9.8 lines per step, 1.69 code chars per plan char, ~2 min per critical-path step. -->
