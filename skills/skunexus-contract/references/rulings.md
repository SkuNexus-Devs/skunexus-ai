# Door 6: rulings

**Goal:** every piece of feedback becomes one lettered decision for the developer (G1), the decisions reach the contract without losing any earlier one, and the developer approves the result (G2). This is the only door that changes a ruled contract's behaviour and the only one that changes a `feedback.md` entry's status (model.md §6).

**Done when:** no `feedback.md` entry is `open`, the panel synthesis (if any) is applied, `check-contract.py --prev` exits 0, and G1 and G2 are recorded (model.md §7).

**Inputs:** `feedback.md` (every source: storyboard, plan, panel, re-pull, PO, code, QA); `review/panel-synthesis.md` when unruled (its `Q-n`, `I-n`, `TL-n`, `E-n` items and truth table); `review/reeval-<DATE>/SYNTHESIS.md` after a re-pull.

## 1. The decision list

1. For each open entry, check the evidence that would change a rule: panel entries were verified by skeptics; for every other source, check it yourself in the code, the ticket or the PO's words.
2. Write `review/decision-list-<DATE>.md`, one item per open entry, ranked: parts, scope and price first; then platform and Core-vs-client items; then the questions only the PO can answer (at most about 7, marked `PO`); then the rest:
   `FB4 · WRONG · panel PD-2 · R4.b` · the question in one line · `(A) <ticket- or PO-literal> [PO decided] · (B) … [silence] · (C) … [expansion, S]` · recommended: B · evidence in one line.
   Then the panel's `Q-n` for the PO (grouped for the daily), `TL-n` for the tech lead (each becomes the next free `J-` entry), and the `E-n` edits as one "apply as suggested" item.
3. **Attended:** send the list in one message ending `needs input: …`. Expect "A", "yes to all", or a few corrections.
4. **Unattended:** don't wait. The recommended option of each item becomes an assumption (an `Assumed` §7 entry, "Confirm with the developer"), the entries stay `open`, and the run stops after step 3 below at a Draft with the decision list as its hand-back (model.md §8, stop points). Nothing goes to the PO.

## 2. G1: record the rulings

- **Fix the new ids first,** in the rulings brief: the next free `R`, criterion letters, `Q`, steps (`s<n>.<m>`) and parts. The editor uses exactly these.
- Set each entry's status: `ruled v<N> (developer, option X) → <ids>`, `rejected v<N>: <why>` or `withdrawn: <why>`. `v<N>` is the version this rewrite will cut: the next number, or `v<N>.<M>` when amending an approved contract.
- Each ruling lands in §7 as `Decided <DATE> (developer, option X): <answer> → <ids>`, under an existing `Q` or the next free one (`PD-2 → FB4 → Q26`). Each panel `Q-n` takes the next free `Q` (`panel Q-3 → Q21`, recorded in the Decision log).
- **Amending an approved contract** (any ruling after G2): set `> Status: Draft (amending approved v<N>, <DATE>)` before the editor starts. After the PO's approval (G6), say that the estimate must be revisited before the PO sees the change.

## 3. Rewrite: editor → checker → fixer

Copy `assets/briefs/rulings-brief.md` to `review/rulings-BRIEF.md` and fill it: the developer's instruction verbatim, the fixed ids, the defaults for waiting items, the decisions kept. The backup is the frozen snapshot the rewrite replaces (`review/prd-v<K>-<DATE>.md` and `review/workflows-v<K>-<DATE>.md`); only when none exists, cut one first (`references/versions.md`).

1. **Editor** (one `sn-writer`) rewrites `prd.md` and `workflows.md` and returns every ambiguous call it made.
2. **Checker** (one `sn-writer`, never the editor) works from the old → new diff, so no earlier decision is silently lost or changed, and writes `review/prd-v<N>-check.md`. FFD-14's checker found 1 BLOCKING, 9 SHOULD-FIX and 13 NIT items the editor's self-check had passed.
3. **Fixer** (one `sn-scout`) applies them in file order.
4. **Mechanical pass:** `python3 -I <SKILL>/scripts/check-contract.py <T> --prev review/prd-v<K>-<DATE>.md` must exit 0: no `R`, criterion, `Q`, step or part disappeared. Fix the leftovers yourself.

When the main context is heavy, delegate all three roles. The variant where the synthesis is the instruction list (FFD-13) runs one editor; it is in the brief.

## 4. G2: approval

Give the developer a short list of **things that need your eye**: every place the editor or fixer invented a mechanism or chose between options, each with its ids. On FFD-13 this list caught an invented mechanism the developer replaced. Then ask for approval. Approving with `Assumed` items still open is fine; silence is not approval.

On the explicit yes, door 7 cuts `v<N> <DATE> approved: …` with its snapshots, sets `> Status: Approved`, runs `--stale` over the views, and restarts the session. In the same message, offer the next skill (chain rule): the plan, and the storyboard if none exists.

## Triage ("triage X")

A later, attended pass on a stopped unattended run, so that a version can be shared as a draft for discussion (model.md §8, "Triage"). `run.md` switches its `workflow` row to `triage` (with its History line) and keeps `mode` and `chain`.

1. **The triage set:** from the decision list, every scope-bearing `Q` (it names a `Part`, is tagged `expansion`, or is `Assumed` naming an owner but no `Evidence:`) and every `CHOICE` entry storyboard v1 chipped on a drawn page (`A('FB<n>')`). Send them as one lettered list, as in §1 step 3; the rest stay `Assumed`.
2. **Rule** as in §2: a chip's entry is ruled into contract text or an assumed `Q`, or re-keyed to a plain `Q` for the PO; a cosmetic label becomes caption "proposal" text.
3. **Rewrite** as in §3, then cut the next version `frozen` (`references/versions.md`; the status stays Draft, no G2), and append `- <DATE> triaged v<N>: <n> items ruled (developer)` to `run.md`'s History. `v<N>` is that frozen version, the one the v1.x page's `BUILT_FROM` will name; `check-storyboard.py` matches them.
4. **Next:** `skunexus-storyboard` rebuilds the storyboard from that version as v1.x, "Draft for discussion", and drafts the share (model.md §8). The developer posts it.

## Re-pull and diff

**When:** the ticket moved (Step 0's freshness check), before the daily, before an estimate is posted. Offer it; run it only when asked ("re-pull FFD-14 and diff it").

1. Copy `assets/briefs/reeval-brief.md` to `review/reeval-<DATE>/BRIEF.md`. Run its Puller prompt with `<PULL_DIR>` = `jira-<DATE>/`, diffed against the newest earlier pull. It writes only dated files and never touches `jira/` or `jira-summary.md`.
2. Read the new description yourself, write the change summary into the brief, and launch the analysts A1–A3 (A4 when a new item needs design) in one message.
3. Write `review/reeval-<DATE>/SYNTHESIS.md` (the brief's "After the analysts"): verify every decision-shaping claim; where analysts disagree, take the more conservative reading.
4. **File the changes:** each `ANSWERS`, `CONTRADICTS`, `NEW-SCOPE`, `REMOVES` or `AMBIGUOUS` item becomes a `CHANGE` entry with the class in its source (`re-pull <DATE> · CONTRADICTS`); `CONFIRMS` and `NO-IMPACT` file nothing.
5. Rule on them as above (§1–§4), with `review/reeval-<DATE>/APPLY-BRIEF.md` from the rulings brief and the synthesis in place of the panel synthesis. A conflict with a recorded decision goes to the daily, never into a silent edit.
6. Put the ticket's last-updated time in the PRD's `Source` line and update the memory note. The views go stale by id; door 7 lists them. Never edit a view's copies (`QT`, `PARTS`, plan tasks) from here.

After approval the ticket can still move: the PO rewrote FFD-13 the day after its approval.

## Other sources

The developer reports a PO reaction, a coding surprise or a QA result: file it as a `feedback.md` entry (source `PO <DATE>`, `code` or `QA`, typed per model.md §6) and rule on it as above. After G6, every such ruling is an amendment the PO re-approves.
