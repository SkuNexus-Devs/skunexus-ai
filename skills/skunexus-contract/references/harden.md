# Door 5: harden

**Goal:** turn any `prd.md` into a contract the views can read: use cases and parts in `workflows.md`, a default for every deferred item, a passing check, a frozen version, and then the discovery panel. The panel flags; the developer decides.

**Done when:** `workflows.md` exists, `check-contract.py` exits 0, a `frozen` version is cut, and `review/panel-synthesis.md` exists with its items filed in `feedback.md` (or the developer skipped the panel).

## 1. Take the PRD as it is

Check these in order; each applies only when its condition holds.
- **Approved with no `> Versions:` block** (approved in `skunexus-jira-prd`, or any regular-route PRD): adopt it first (`references/versions.md`, "Adoption"), then set `> Status: Draft (amending approved v1, <DATE>)`. Everything below is an amendment.
- **A seed snapshot exists** (`review/prd-seed-<DATE>.md`): while §7 still carries the interview note and an entry is Open, the interview is unfinished and belongs to `skunexus-jira-prd` (model.md §8, row 2); go on only when it ended or the developer says it is over. Then run `python3 -I <SKILL>/scripts/check-contract.py <T> --prev review/prd-seed-<DATE>.md`. Restore every seeded `Q` it lists as missing, in the Decision log: `- **Q9** <question> Decided <DATE> (developer, interview): <answer> → R4, R4.b.` Find the answer in §3–§6; when you can't, say so and make it `Assumed` with "Confirm with the developer". Then delete the interview note at the top of §7.
- **Just the storyboard** (an approved PRD with no `workflows.md`, the developer wants the PO's storyboard): adopt it, write the use cases (§2), freeze, and skip the panel unless asked; storyboard v1 follows. The developer's yes on the v1 review also approves the amendment: one message, no restart before v2 (model.md §5, item 3).
- **`Draft (lite)`** with a full contract asked: see `references/lite.md`, "Later".
- **No research on disk** (a regular-route PRD): ground steps and defaults in the ticket, `jira-summary.md` and the code; say which ones have no evidence.

## 2. Use cases and parts

1. Copy `assets/workflows-template.md` to `workflows.md` (title and `Contract:` line filled) and `assets/briefs/workflows-brief.md` to `review/workflows-BRIEF.md`. Spawn the use-case drafter (`sn-writer`). It writes `workflows.md` and `review/workflows-notes.md`: the evidence for each step, and the steps it could not ground.
2. **Parts** follow the PO's priced shape when one is known: the ticket's phases or options, the baseline, an existing `estimate.md`, the developer's words. Otherwise there is one part, `Part 1`, `base`. Never add parts the PO didn't ask for: panels drift toward structure (FFD-14: a five-part estimate was proposed and rejected).
3. **Ungrounded steps and deferred items** (an Open §7 entry, or one `skunexus-jira-prd` deferred with a reason):
   - *attended:* send one message listing every ungrounded step (id, what it assumes, the proposed outcome) and every deferred item's proposed default, lettered as usual; "yes to all" or corrections. Ask nothing else.
   - *unattended:* make each one an `Assumed` §7 entry with the next free `Q` id, mark the step's Outcome cell `(assumed, Qn)` and add `Qn` to its Cites cell.
4. A step whose evidence contradicts a criterion is not fixed silently: write the step as the criterion says and file a `WRONG` entry in `feedback.md` (model.md §6) with source `harden <DATE>` and the evidence. The rulings door decides it.

## 3. Render-ready check, then freeze

- `python3 -I <SKILL>/scripts/check-contract.py <T>` exits 0: ids, markers, and coverage both ways (every live criterion cited by a live step or listed under "Not exercised"; every live step cites a live `R` or criterion; every `Part` named is in the Parts table).
- No §7 entry is still Open: each says `Assumed` or `Decided` (model.md §1, render-ready).
- Cut the next version `frozen` with its snapshots (`references/versions.md`). Every reader below reads the snapshots.

## 4. Discovery: panel ‖ storyboard v1

Discovery runs on the frozen version. In the chain, start both; in a one-stage ask, offer them. Say the panel takes ~45 min and is a burst. A plan draft joins only when the developer asks for one (hand `skunexus-backend-plan` the frozen Draft with their OK).

- **Storyboard v1:** load `skunexus-storyboard` (v1 door) once the panel agents are spawned. It writes its own problems to `feedback.md`.
- **Deviation check** (when `review/po-baseline.md` exists): the deviation checker in `review/baseline-BRIEF.md` classifies every `R`, Non-Goal and baseline row against the frozen snapshot into `review/deviations.md`. A deviation is a confirm-or-change item for the PO, not a defect. Run it before the panel; the panel cites its `DV-n` items.
- **Panel:** copy `assets/briefs/panel-brief.md` to `review/panel-BRIEF.md` and fill it. Create `review/panel/.gitignore` containing `*`. Pick 4–6 reviewers: always V1 (code fact-checker), V2 (traceability) and the simulated PO; then, as the ticket warrants, the tech lead, the FE developer (if there is UI), the BE reviewer, V3 (big picture) or the developer. FFD-14 ran 6, FFD-13 ran 5. Spawn them all in one message.
- **Resume a half-done panel:** a reviewer file is complete when it ends with its "Confirmed OK" section; a planned reviewer with no file is incomplete. Re-run only the incomplete ones, as fresh agents on the same frozen snapshot.

## 5. Synthesis

Follow the brief's "Synthesis" section: wait for every completion notice; cluster; verify every cluster with a top score ≥ 50 or raised by two reviewers (log the rest as skipped, with a reason); run the skeptics (the code skeptics on a second model family); write `review/panel-synthesis.md`; spot-check the top items yourself. Zero refutations is unusually clean and can mean lenient skeptics.

With about five reviewers and under ~100 findings, the lighter variant (FFD-13) skips the clusterer and skeptics: verify every decision-changing claim yourself and write the synthesis as decisions plus accepted findings. An unattended run uses this lighter variant by default and the full synthesis only on a large ticket (model.md §8, stop points): on FFD-14 the full panel repeated the one factual error on record, which the stock-page capture caught.

**File the panel's decisions.** Each `PD-n` becomes one `feedback.md` entry (model.md §6): type `WRONG`, `CHOICE` or `SILENCE` by its nature, source `panel PD-n`, its cited ids, evidence and lettered options. Append them yourself, numbered from the next free `FB` id, once no other writer is running (storyboard v1 finished or not started), and record the mapping in the synthesis (`PD-2 → FB4`). Panel `Q-n`, `I-n`, `TL-n` and `E-n` items stay in the synthesis; the rulings brief applies them.

**Next:** door 6 (rulings), G1.
