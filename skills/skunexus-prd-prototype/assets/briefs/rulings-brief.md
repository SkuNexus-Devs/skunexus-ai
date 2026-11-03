<!-- Stage: PRD rewrite after the panel (rulings → editor → independent checker → fixer → mechanical pass). Copy to .ai/<TICKET>/review/rulings-BRIEF.md and fill the rulings from the developer's answers on the PD-list; the agent prompts at the end are for the orchestrator.
     Extra placeholders: <PREV_VERSION> (e.g. v1), <PREV_DATE>, <NEXT_R> (first new R id), <RULING> (the developer's instruction, verbatim), <KEPT_DECISIONS>, <ESTIMATE_SHAPE>, <PRD_TEMPLATE> (<SKILL>/../skunexus-jira-prd/assets/prd-template.md), <EDITOR_CALLS>. Standard placeholders: see SKILL.md. -->
# <TICKET> PRD <VERSION> rulings brief (developer rulings, <DATE>)

**Inputs:**
- `prd.md` (<PREV_VERSION>, backed up as `review/prd-<PREV_VERSION>-<PREV_DATE>.md`);
- `review/panel-synthesis.md`: panel decisions PD-n, questions Q-n, developer and tech-lead items I-n / J-n, edits E-n, the truth table;
- `review/po-baseline.md` and `review/deviations.md`, for context.

The developer's instruction: <RULING>

## Global rules
| Rule | Why |
|---|---|
| **Apply every E-n** with the panel's recommended text. Where an edit waits on a Q-n or J-n, use the default below, write it into the requirement as `(assumed, Qn)` (`Qn` = the PRD §7 id the panel Q-n maps to), and add a §7 line "Assumed: …; confirm with <PO> (Qn)" or "with <TECH_LEAD> (J-n)" | The developer approves with assumptions still open, so the PRD must say which parts are assumed |
| **Keep ids stable.** Never renumber or delete. A superseded requirement stays as `**Rn** (retired <DATE>: reason → see Rm)`, its ACs retired the same way. New requirements continue at <NEXT_R> with no gaps; new ACs take the next free letter | The plan, tests and estimate cite ids |
| **New ids are fixed here.** When a ruling adds a requirement, this brief gives its id and text ("use exactly these") | The editor must not invent requirements or mechanisms |
| **Requirements altitude.** Services, locks, hooks, endpoints and class names go to Notes for Design, condensed from I-n / J-n, not into R-text | Requirements say what, not how |
| **Interview decisions the panel didn't refute stay in scope:** <KEPT_DECISIONS> | The panel flags; the developer decides |
| A kept decision that contradicts a PO decision gets a §7 line: "Developer choice, confirm with <PO> (DV-n, PO-n)" | It is a confirm-or-change item for the PO, not a defect |
| **Status stays Draft.** Amending an Approved PRD sets `Status: Draft (amending approved v<N>, <DATE>)` | Approval and re-approval are the developer's explicit act |
| **Other tickets' ids carry their key:** `FFD-14 R31`, `FFD-14's R26`, never a bare `R31` | `check-prd.py` checks a bare id against this PRD |
| **Never quote personas** or name them as a source; "panel review <DATE>" is the only attribution | Simulated reviews are not people's opinions |
| **Keep the PO's estimate shape:** <ESTIMATE_SHAPE>. No options table or phase list the PO didn't ask for | Panels drift toward more structure |

## Defaults for waiting items
One bullet per item, grouped by area: `**Area (E-n, Q-n / J-n):** the default`. Every default listed here appears in the PRD as an assumption and in §7.
- …

## §7 rewrite
Title: "Open questions and assumptions". It opens with "The PRD stays Draft until these are confirmed." Groups, most consequential first:
1. **For <PO> / client** (client-facing wording goes through <PO>): one line per panel Q-n under the next free `Qn`, stating the assumption the PRD currently takes. Record the mapping (`panel Q-3 → Q21`) in the Decision log.
2. **For <TECH_LEAD>:** one line per J-n.
3. **External inputs and follow-ups:** client inputs still owed, the prototype refresh, research corrections.

## Header
Add a version line: `<VERSION> <DATE>: applied panel review (review/panel-synthesis.md) per review/rulings-BRIEF.md`. Keep the ticket's last-updated time in the header.

---

## Agent prompts (orchestrator)
Before the editor starts: the backup is the §6 snapshot `review/prd-<PREV_VERSION>-<PREV_DATE>.md`. Only when there was no panel freeze, `cp prd.md` to that name; never overwrite an existing snapshot. When the main context is heavy, delegate all three roles by default.

**Editor (1 `sn-writer` agent).** "Read in order: `review/rulings-BRIEF.md` (binding), `prd.md` (<PREV_VERSION>), `review/panel-synthesis.md`, `<PRD_TEMPLATE>`. Rewrite `prd.md` to <VERSION> per the brief.
- Write in 2–3 chunks: Write part 1, then Edit to append the rest (long single writes die on stream errors).
- Plain, specific, no marketing. One term per concept, used everywhere.
- One AC per cell of any status × action matrix; every matrix cell cites the AC that proves it.
- No persona attributions.
- Self-check: every <PREV_VERSION> id still present (live or retired); no placeholders; references resolve; each live R has an AC; §5 matches §4. Run `python3 -I <SKILL>/scripts/check-prd.py prd.md --prev review/prd-<PREV_VERSION>-<PREV_DATE>.md`.
- Return ≤30 lines: E-edits applied or deferred, new and retired ids, the assumption count, the check-prd result, and **every ambiguous call you made** (where the brief didn't settle it and you chose)."

**Checker (1 `sn-writer` agent, never the editor).** "You did not write this PRD, and your job is to find what's wrong. Check `prd.md` (<VERSION>) against `review/rulings-BRIEF.md` (binding), `review/prd-<PREV_VERSION>-<PREV_DATE>.md` and `review/panel-synthesis.md`; read `po-baseline.md` and `deviations.md` for context.
1. Brief compliance, rule by rule.
2. **A <PREV_VERSION> → <VERSION> diff, so no interview decision is silently lost or changed.**
3. E-edit coverage: each E-n applied or explicitly deferred.
4. Unified behaviour: matrix vs R-text vs ACs; each rule stated identically everywhere; terminology.
5. AC falsifiability; no implementation in ACs.
6. Altitude.
7. Code facts in Notes for Design (file:line).
8. A verdict on each of the editor's judgement calls: <EDITOR_CALLS>.

Write `review/prd-<VERSION>-check.md`: a header (what was checked, against what, counts `BLOCKING n · SHOULD-FIX n · NIT n`, a short verdict), then BLOCKING / SHOULD-FIX / NIT sections. Each item is `### CK-n · location · title` with **Problem**, **Evidence** (`prd:N`, `<PREV_VERSION>:N`, `syn:N`) and **Fix** as an exact old → new string; check that each old string occurs exactly once in `prd.md`. Then the judgement-call verdicts, then Confirmed OK. Read-only except that file. Return ≤20 lines." (FFD-14: the checker found 1 BLOCKING, an assumed default missing from §7, plus 9 SHOULD-FIX and 13 NIT that the editor's self-check had passed.)

**Fixer (1 `sn-scout` agent).** "Apply every item in `review/prd-<VERSION>-check.md` to `prd.md`, in file order. When an old string no longer matches, apply the fix by hand at the right place. Every new assumption goes into §7. Then run `python3 -I <SKILL>/scripts/check-prd.py prd.md --prev review/prd-<PREV_VERSION>-<PREV_DATE>.md`. Return: applied, applied by hand, not applied (and why)."

**Mechanical pass (orchestrator).** Run the same `check-prd.py` command yourself; it must exit 0. Fix the leftovers. Then give the developer a short list of **things that need your eye before approval**: every place the editor or fixer invented a mechanism or chose between options, each with its R-id (FFD-13: this list caught an invented mechanism that the developer replaced). **Gate: approval** ("approved" flips Status). Update the memory note.

## Variant: the synthesis is the instruction list (FFD-13)
When the orchestrator verified the findings itself and wrote `panel-synthesis.md` as decisions plus accepted findings, skip the rulings brief and run one editor:

"Read, in order: `review/drafting-BRIEF.md` (if present), `prd.md`, `review/panel-synthesis.md`. The synthesis is your **instruction list**; it overrides the reviewers wherever they differ. Read the reviews in `review/panel/` for the exact suggested text of each accepted finding. Keep R/AC ids stable: never renumber. Don't change any developer decision. If two instructions conflict, or a finding can't be applied cleanly, apply the closest faithful version and list it under 'Conflicts/unsure'. When done, run `python3 -I <SKILL>/scripts/check-prd.py prd.md`. Return only: the change summary (one line per finding id applied or skipped, grouped), the check results, and 'Conflicts/unsure'."

Then re-run `check-prd.py` yourself and list the things that need the developer's eye before approval.
