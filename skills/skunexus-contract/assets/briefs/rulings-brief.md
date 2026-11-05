<!-- Door 6 (rulings): apply the developer's rulings to the contract (editor → independent checker → fixer → mechanical pass). Copy to .ai/<TICKET>/review/rulings-BRIEF.md (after a re-pull: review/reeval-<DATE>/APPLY-BRIEF.md) and fill it from the developer's answers on the decision list; the agent prompts at the end are for the orchestrator.
     Extra placeholders: <PREV_VERSION> (the version being replaced, e.g. v1), <PREV_DATE>, <NEXT_VERSION> (e.g. v2, or v1.1 when amending an approved contract), <SYNTHESIS> (review/panel-synthesis.md, or review/reeval-<DATE>/SYNTHESIS.md), <RULING> (the developer's instruction, verbatim), <RULED_FB> (the FB ids this rewrite applies), <NEW_IDS> (every new R, criterion, Q, J-, step and part, with its text), <KEPT_DECISIONS>, <PARTS_SHAPE>, <PRD_TEMPLATE> (<SKILL>/../skunexus-jira-prd/assets/prd-template.md), <EDITOR_CALLS>. Standard placeholders: see the skill's SKILL.md. -->
# <TICKET> contract <NEXT_VERSION> rulings brief (developer rulings, <DATE>)

**Inputs:**
- `prd.md` and `workflows.md` (<PREV_VERSION>, frozen as `review/prd-<PREV_VERSION>-<PREV_DATE>.md` and `review/workflows-<PREV_VERSION>-<PREV_DATE>.md`);
- `feedback.md`: the entries ruled here, <RULED_FB>, each with its status line `ruled <NEXT_VERSION> (developer, option X) → <ids>`;
- `<SYNTHESIS>`: panel decisions PD-n, questions Q-n, developer and tech-lead items I-n / TL-n, edits E-n, the truth table (or, after a re-pull, the analysts' synthesis);
- `review/po-baseline.md` and `review/deviations.md`, for context.

The developer's instruction: <RULING>

## Global rules
| Rule | Why |
|---|---|
| **Apply every ruled entry** with the option the developer chose, and **every E-n** with the panel's recommended text. Where an edit waits on a Q-n or TL-n, use the default below, write it into the requirement as `(assumed, Qn)`, and add a §7 entry `Assumed: … Evidence: … Confirm with <PO>.` (or `with <TECH_LEAD>` under a `J-` id) | The developer approves with assumptions still open, so the contract must say which parts are assumed |
| **Each ruling lands in §7** as `Decided <DATE> (developer, option X): <answer> → <ids>`, under its existing `Q` or the new one fixed below. A `Q` is never deleted | Chips, citations and rulings point at it |
| **Keep ids stable.** Never renumber or delete. A superseded requirement stays as `- **Rn** (retired <DATE>, <NEXT_VERSION>: reason → see Rm)`; its criteria, steps (in the Outcome cell) and parts (in the Status cell) are retired the same way. New ids continue with no gaps | Views, tests and links cite them |
| **New ids are fixed here** (below): "use exactly these". The editor invents no requirement, step, part or mechanism | The editor must not decide |
| **Both files move together.** A changed or new criterion is cited by a step or listed under "Not exercised"; a retired one is cited by none. Every live step cites a live `R` or criterion and names a live part | Coverage reads both ways |
| **Requirements altitude.** Services, locks, hooks, endpoints and class names go to Notes for Design, condensed from I-n / TL-n, not into R-text | Requirements say what, not how |
| **Decisions the panel didn't refute stay in scope:** <KEPT_DECISIONS> | The panel flags; the developer decides |
| A kept decision that contradicts a PO decision gets a §7 entry: "Developer choice, confirm with <PO> (DV-n, PO-n)" | It is a confirm-or-change item for the PO, not a defect |
| **Status stays Draft.** An approved contract reads `Draft (amending approved v<N>, <DATE>)`. The version line is written at approval, not here | Approval is the developer's explicit act |
| **Other tickets' ids carry their key:** `FFD-14 R31`, `FFD-14's R26`, never a bare `R31` | A bare id is checked against this PRD |
| **Never quote personas** or name them as a source; "panel review <DATE>" is the only attribution | Simulated reviews are not people's opinions |
| **Keep the PO's parts:** <PARTS_SHAPE>. No part, options table or phase list the PO didn't ask for | Panels drift toward more structure |

## New ids (use exactly these)
<NEW_IDS>

## Defaults for waiting items
One bullet per item, grouped by area: `**Area (E-n, Q-n / TL-n):** the default`. Every default listed here appears in the contract as an assumption and in §7.
- …

## §7 shape
Groups, most consequential first: **For <PO> / client** (client-facing wording goes through <PO>) · **For <TECH_LEAD>** (`J-` entries) · **External inputs** (client inputs still owed, research corrections) · **Decision log** (every `Decided` entry, with the mappings `panel Q-3 → Q21`, `PD-2 → FB4 → Q26`). Each entry in one of the three states of the skill's `references/model.md` §3.

---

## Agent prompts (orchestrator)
Before the editor starts, the backup is the frozen snapshot of <PREV_VERSION>. Only when none exists, cut a frozen version first (door 7); never overwrite a snapshot. When the main context is heavy, delegate all three roles.

**Editor (1 `sn-writer` agent).** "Read in order: `review/rulings-BRIEF.md` (binding), `prd.md` and `workflows.md` (<PREV_VERSION>), the ruled `feedback.md` entries, `<SYNTHESIS>`, `<PRD_TEMPLATE>`. Rewrite both files per the brief.
- Write `prd.md` in 2–3 chunks: Write part 1, then Edit to append the rest (long single writes die on stream errors).
- Plain, specific, no marketing. One term per concept, used everywhere.
- One criterion per cell of any status × action matrix; every matrix cell cites the criterion that proves it.
- No persona attributions.
- Self-check: every <PREV_VERSION> id still present (live or retired); no placeholders; references resolve; each live R has a criterion; §5 matches §4; coverage both ways. Run `python3 -I <SKILL>/scripts/check-contract.py .ai/<TICKET> --prev review/prd-<PREV_VERSION>-<PREV_DATE>.md`.
- Return ≤30 lines: rulings and E-edits applied or deferred, new and retired ids, the assumption count, the check result, and **every ambiguous call you made** (where the brief didn't settle it and you chose)."

**Checker (1 `sn-writer` agent, never the editor).** "You did not write this contract, and your job is to find what's wrong. Check `prd.md` and `workflows.md` (<NEXT_VERSION>) against `review/rulings-BRIEF.md` (binding), the <PREV_VERSION> snapshots, the ruled `feedback.md` entries and `<SYNTHESIS>`; read `po-baseline.md` and `deviations.md` for context.
1. Brief compliance, rule by rule.
2. **A <PREV_VERSION> → <NEXT_VERSION> diff of both files, so no earlier decision is silently lost or changed.**
3. Ruling and E-edit coverage: each applied or explicitly deferred.
4. Unified behaviour: matrix vs R-text vs criteria vs step outcomes; each rule stated identically everywhere; terminology.
5. Criterion falsifiability; no implementation in criteria.
6. Altitude.
7. Code facts in Notes for Design (file:line).
8. A verdict on each of the editor's judgement calls: <EDITOR_CALLS>.

Write `review/prd-<NEXT_VERSION>-check.md`: a header (what was checked, against what, counts `BLOCKING n · SHOULD-FIX n · NIT n`, a short verdict), then BLOCKING / SHOULD-FIX / NIT sections. Each item is `### CK-n · location · title` with **Problem**, **Evidence** (`prd:N`, `wf:N`, `<PREV_VERSION>:N`, `syn:N`) and **Fix** as an exact old → new string; check that each old string occurs exactly once in its file. Then the judgement-call verdicts, then Confirmed OK. Read-only except that file. Return ≤20 lines." (FFD-14: the checker found 1 BLOCKING, an assumed default missing from §7, plus 9 SHOULD-FIX and 13 NIT that the editor's self-check had passed.)

**Fixer (1 `sn-scout` agent).** "Apply every item in `review/prd-<NEXT_VERSION>-check.md` to `prd.md` and `workflows.md`, in file order. When an old string no longer matches, apply the fix by hand at the right place. Every new assumption goes into §7. Then run `python3 -I <SKILL>/scripts/check-contract.py .ai/<TICKET> --prev review/prd-<PREV_VERSION>-<PREV_DATE>.md`. Return: applied, applied by hand, not applied (and why)."

**Mechanical pass (orchestrator).** Run the same check yourself; it must exit 0. Fix the leftovers. Then give the developer a short list of **things that need your eye before approval**: every place the editor or fixer invented a mechanism or chose between options, each with its ids (FFD-13: this list caught an invented mechanism that the developer replaced). **Gate: approval** (G2); door 7 writes the version line. Update the memory note.

## Variant: the synthesis is the instruction list (FFD-13)
When the orchestrator verified the findings itself and wrote the synthesis as decisions plus accepted findings, skip this brief and run one editor:

"Read, in order: `prd.md`, `workflows.md`, the ruled `feedback.md` entries, `review/panel-synthesis.md`. The synthesis and the rulings are your **instruction list**; they override the reviewers wherever they differ. Read the reviews in `review/panel/` for the exact suggested text of each accepted finding. Keep every id stable: never renumber or delete; retire instead. Don't change any developer decision. If two instructions conflict, or a finding can't be applied cleanly, apply the closest faithful version and list it under 'Conflicts/unsure'. When done, run `python3 -I <SKILL>/scripts/check-contract.py .ai/<TICKET> --prev review/prd-<PREV_VERSION>-<PREV_DATE>.md`. Return only: the change summary (one line per ruling or finding applied or skipped, grouped), the check result, and 'Conflicts/unsure'."

Then re-run the check yourself and list the things that need the developer's eye before approval.
