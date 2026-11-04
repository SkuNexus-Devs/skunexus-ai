# Estimate: hours per part, in the PO's shape

`estimate.md` is the PO's price view of the contract: each live part → BE hours + FE hours. Owner: the developer, gate G5 (they set the base and post it; posted hours are theirs and never re-argued). Then G6: the PO approves scope (the shared storyboard) and price (the posted estimate) together.

## When and inputs

After `backend-plan.md` is approved (G3) and `frontend-plan.md` exists. G3, G4 and G5 can be asked in one message.
- **Parts:** `workflows.md` "Parts" of the contract version the views were built from: live parts only, Name and Scope verbatim, the PO's shape as the qualifier. The parts are the PO's priced scope: never add, merge or split one here. A panel-proposed five-part estimate was rejected as "too heavy" on FFD-14; a part that should change goes to `feedback.md` (source `estimate`) and the contract.
- **BE size per part:** `python3 -I <SKILL>/../skunexus-backend-plan/scripts/check-plan.py .ai/<TICKET> --plan --sizes` prints `| Part | Tasks | Characters | How |`, one row per part plus `shared`, `unassigned` and `total`. A task's part is its `**Part:**` line, else derived from the criteria it covers (model.md §5). With no parts every task is `Part 1`.
- **FE hours per part:** the "FE hours per part" table of `frontend-plan.md`, with its status (G4 confirmed, replaced, or still a draft).
- **Rate:** a measured velocity basis (below).

## BE hours

1. **The developer sets the base.** Ask for Part 1's BE hours first. Until they give one, offer the projection: Part 1's characters × the calibrated rate. On FFD-14 the rate came out at 0.13–0.16 h per 1,000 plan characters (16–20 h for ~125k characters of base tasks); on FFD-40, Part 1's 72.8k characters gave 9.5–11.7 h at that rate, and the developer proposed 11–15 h.
2. **Every other part scales at the base's rate:** base hours ÷ Part 1's characters = h per 1,000 characters; a part's BE hours = its characters × that rate, plus a small fixed cost where the plan adds a new integration (its own mailer, faked-transport tests, a template review) or a later phase (its own run and review).
3. **`shared` and `unassigned`** characters (tasks spanning parts, migrations, text outside tasks): ask the developer how to split them, and record the split in `estimate.md`'s derivation, never in the plan.
4. **Calibrate on a measured run, not a projection**: projections missed by 2×. One `sn-scout` velocity probe measures the last comparable orchestrated run (its prompt is in `assets/estimate-template.md` "Basis"); re-measure after each new run. Plan characters measure size better than steps, because step size varies.

## FE hours

Copied from `frontend-plan.md` per part, never re-derived. Until the FE developer confirms (G4), the estimate says "FE: draft for the FE developer to confirm or replace". The FE plan's `shared` row is split with the developer, like the BE one.

## Rules

| Rule | Why |
|---|---|
| Lead with **Part · Hours · Scope**, Hours = BE + FE; the BE/FE split and the combination totals under it | The developer asked for exactly that |
| Part names and Scope copied verbatim from `workflows.md`; Scope is 1–2 plain sentences, no ids, counts, files or mapping jargon | The storyboard's part cards copy the same text; "too much assumed knowledge" was the developer's rejection |
| Figures = implementation incl. tests + review and rework, BE and FE. PR review, MySQL checks, stage verification, QA support and deploy go under "Not in these figures", without hours | Keeps the figure comparable across tickets |
| Agent wall-clock kept apart from developer hours; only implementation depends on orchestration (serial agents take ~3.7× the wall-clock) | The developer asked which figures assume orchestrated subagents |
| Header `> Status: Draft for the Jira estimate (not posted)` until G5; the developer posts, then `> Posted <DATE>: <their figures, comment id>` | Only the developer posts; posted hours are intentionally trimmed and never re-argued |
| Hours live here and in `frontend-plan.md` (FE) only: never on the storyboard, in the contract or in `feedback.md` | The storyboard goes to the PO and the client |

**Header.** `> Built from: contract v<N> (<DATE>) · backend-plan.md@<hash> · frontend-plan.md@<hash>` (`tr -d '\r' < <file> | sha256sum | cut -c1-8` when you start; model.md §5). G6 is recorded as `> PO: <DATE> approved <parts> at <figures>` when the developer reports it.

**Open assumptions.** The estimate lists, as its assumptions, the ids `check-contract.py` prints as `open assumptions cited by live steps` (model.md §7): a page that still carries an `A()` chip is estimated, not built.

**Before posting,** offer `skunexus-contract`'s re-pull and diff: the ticket may have moved since the contract was approved.

**After G6** a scope change is an amendment in the contract; the estimate is revisited from the new version before the PO sees it again (FFD-17: Part 2 merged into the base after storyboard v1, and the estimate was redone).

## Run and stale

Copy `assets/briefs/estimate-brief.md` to `.ai/<TICKET>/ESTIMATE-BRIEF.md` and run one `sn-writer`, or write it yourself when the figures are few. Present the result with the G5 question (and G3, G4 if still open) in one message. After G5: update the memory note and end the turn with "Start a new session now: `continue <TICKET>`".

`python3 -I <CONTRACT_CHECK> --stale estimate.md` marks the estimate stale when a part changes or the plan or the FE plan file changed; redo only the affected rows and totals, and refresh the header.
