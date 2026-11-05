# Door 7: version and staleness

**Goal:** every state that someone reads or approves is a numbered version with frozen snapshots, so views can say what they were built from and `--stale` can say what they must rebuild. Formats and rules: model.md §3 (version line), §5 (snapshots, staleness). Only this skill cuts versions.

**Done when:** the version line and its snapshots exist, `check-contract.py` exits 0, and `--stale` has been run over every view on disk.

## Cutting a version

**When** (model.md §5):
- **frozen:** before a panel, a storyboard build or a plan draft reads the contract. Edits queue until the readers finish.
- **approved:** on the developer's explicit yes (G2). Approving a frozen version unchanged reuses its number and snapshots: add a second line for the same `v<N>` and copy nothing. Any change since takes the next number.
- **amendment:** an approved contract changes. The status reads `Draft (amending approved v<N>, <DATE>)` until the yes, which cuts `v<N>.<M> approved`.

**How:**
1. Run `python3 -I <SKILL>/scripts/check-contract.py <T>`; it must exit 0 (the unversioned-change list is information in a Draft).
2. Add the line under the header's `> Versions:` (create the block, exactly `> Versions:`, right after `Source` if it is missing):
   `> - v<N>[.<M>] <DATE> <frozen|approved>: [<note>; ][changed <ids>; ][new <ids>; ][retired <ids>; ][from <FB ids>]`
   - The lists name the ids whose text changed, appeared or was retired since the previous snapshot, across both files; `check-contract.py` checks that they equal the diff. The first version has no previous snapshot and carries a note only (`v1 2026-11-02 frozen: unattended draft, 44 defaults`).
   - `from` names the `feedback.md` entries this version rules on.
   - For an approval, set `> Status: Approved` (the first word; keep any free text after it).
3. Snapshot both files, **after** the line is written, never overwriting one:
   ```bash
   cp <T>/prd.md <T>/review/prd-v<N>-<DATE>.md; cp <T>/workflows.md <T>/review/workflows-v<N>-<DATE>.md
   ```
   No `workflows.md` (a regular-route contract): the PRD snapshot alone. Only files named exactly `review/(prd|workflows)-v<N>[.<M>]-<DATE>.md` are snapshots; the newest is the highest version number, never the newest date.
4. Run the check again: a version line without its snapshot is an error.

Legacy version lines (`> Version: …`, `> v2 <DATE>: applied …`, dated changelog lines) stay as written; they are information only and the checks ignore them.

## Adoption

A `prd.md` that is `Approved` with no `> Versions:` block (approved in `skunexus-jira-prd`, or any regular-route PRD) is adopted before this skill changes anything in it:
1. Add `> Versions:` and `> - v1 <DATE> approved: adopted from <source>` (`skunexus-jira-prd interview`, `regular-route PRD of <date>`). Keep the legacy lines.
2. Snapshot it as `review/prd-v1-<DATE>.md`.
3. Then work as an amendment: `Draft (amending approved v1, <DATE>)`, and `v1.1 … approved` on the developer's yes.

## Unversioned changes

In an `Approved` contract, `check-contract.py` reports any id whose text differs from the newest snapshot: `unversioned change since v2: R4.c (new), R7.a (text): cut a version`. The usual cause is `skunexus-backend-plan` lettering criteria (its Step 3) or patching contained drift (its Step 5), which the developer confirmed in that thread.
- Show the developer the list in one line and ask; on yes, cut `v<N>.<M> <DATE> approved: from backend-plan Step 5; changed …; new …` with its snapshots.
- Step 5 adds criteria to `prd.md` only, so the check fails on coverage until each new criterion has a step. Before cutting, add the `workflows.md` step that exercises it (or a "Not exercised" line with the reason), then cut the version.
- A change the developer doesn't recognise is not versioned: file it as a `WRONG` entry (source `code`) and take it to door 6.

## Staleness

Run `--stale` over every view on disk and report one table: view · result · stale ids with their reasons · owner skill.
```bash
for v in <T>/backend-plan.md <T>/frontend-plan.md <T>/estimate.md <T>/prototype/*-storyboard.html; do
  [ -f "$v" ] && python3 -I <SKILL>/scripts/check-contract.py --stale "$v"; done
```
- Exit 0 current · 1 stale · 3 no base (counts as current; its owner adds the `Built from` header next time) · 2 unreadable.
- A view built from `vK` is stale on every id it cites that changed or was retired after `vK`, every id new since `vK` in its coverage scope, and every `<file>@<hash>` whose file changed (model.md §5). Snapshots are compared, never the live files: draft edits mark nothing stale until the next freeze.
- This skill never rebuilds a view. The owner skill rebuilds only the stale pages, tasks or rows: `skunexus-backend-plan` for the plan, `skunexus-storyboard` for the storyboard, the FE plan and the estimate.

## After an approval

G2 ends this skill's work: update the memory note and restart (model.md §8, "Restart after approval" and "State lives on disk"). The exception is the "just the storyboard" yes, which goes straight on to storyboard v2 (model.md §5, item 3).
