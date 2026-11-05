<!-- Estimate. Copy to .ai/<TICKET>/ESTIMATE-BRIEF.md, fill it, and give one fresh `sn-writer` agent:
"Read <path>/ESTIMATE-BRIEF.md and do it." Extra placeholders: <SIZES> (the check-plan.py --plan --sizes table, pasted),
<BASE> (the developer's Part 1 BE hours, or "not given yet"), <SPLIT> (how the developer splits shared and unassigned),
<BASIS> (the velocity probe's reply, or "fallback"), <WORKFLOWS_SNAPSHOT>. Standard placeholders: see SKILL.md. -->

# Estimate brief: <TICKET>

You write `<REPO>/.ai/<TICKET>/estimate.md` from `<SKILL>/assets/estimate-template.md`. The rules are `<SKILL>/references/estimate.md` "BE hours", "FE hours" and "Rules"; read those sections.

## Inputs
- Parts: `<WORKFLOWS_SNAPSHOT>` "Parts", live rows only. Name and Scope verbatim; the PO's shape as the qualifier. Never add, merge or drop a part.
- BE size per part: <SIZES>
- BE base: <BASE>. Every other part scales at the base's rate (base hours ÷ Part 1's characters), plus the small fixed costs the template names. With no base yet, show the projection at the calibrated rate and leave the base cell as `<ask the developer>`.
- Shared and unassigned: <SPLIT>
- FE: `frontend-plan.md` "FE hours per part" and its Status line.
- Plan facts for the wall-clock table: `backend-plan.md` manifest and waves; `check-plan.py`'s critical-path figures.
- Velocity basis: <BASIS>

## Boundaries
- Write only `estimate.md`. Hours go nowhere else. Header `Status: Draft for the Jira estimate (not posted)`; the `Built from` line as the template shows, hashes from `tr -d '\r' < <file> | sha256sum | cut -c1-8`.
- A part that looks wrongly shaped is a question for the developer in your reply, never a change here.

## Reply (≤10 lines)
Part · Hours lines; BE and FE totals; the rate used and its basis; open items the developer must give (base, split, FE confirmation).
