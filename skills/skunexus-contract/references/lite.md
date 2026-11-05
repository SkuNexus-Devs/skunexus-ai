# Door 4: lite

**Goal:** enough contract for a first storyboard, fast: the ticket's asks as requirements, every question given its simplest default, and the use cases. No research, no PO baseline, no panel. Offer it when the developer asks for "a quick storyboard, no PRD"; if the PO will also expect an estimate, recommend the full route (doors 1–6) instead and let the developer pick.

**Done when:** `prd.md` with `> Status: Draft (lite)`, `workflows.md`, `check-contract.py` OK, and `v1 … frozen`.

## Steps

1. **Pull only:** door 1 step 1 (puller, `jira-summary.md`, the "please provide" list). Skip the question list, research and baseline.
2. **`prd.md`** from `<SKILL>/../skunexus-jira-prd/assets/prd-template.md`:
   - header `> Status: Draft (lite)` and `> Source: Jira <TICKET> (pulled <DATE>)` plus any `input/` file;
   - §4: one `- **Rn** …` per ask, in ticket order; when the ticket numbers its asks, note "(ticket Req n)";
   - §6: optional. A lite contract needs no criterion per requirement (model.md §3);
   - §7: one entry per open question, each `Assumed: <the simplest default>. Evidence: <ticket line>. Confirm with <role>.`, and `(assumed, Qn)` in the requirement it shapes.
3. **`workflows.md`** from `assets/workflows-template.md`: the ticket's flows as scenarios and steps, each step citing at least one `R`; every live requirement cited by a step or listed under "Not exercised". One part (`Part 1`, the ticket's title, `base`) unless the ticket or the developer names priced options.
4. Run `python3 -I <SKILL>/scripts/check-contract.py <T>` until it exits 0.
5. **Freeze:** cut `v1 <DATE> frozen: lite` with its two snapshots (`references/versions.md`).
6. **Next:** workflow `lite-storyboard` loads `skunexus-storyboard`, v1 door, with the frozen version; workflow `lite` stops here and offers it in one line (model.md §8).

## Later

- **A full contract follows** on the same `prd.md`: set the status to `Draft`, keep every id, and run door 1 (its question list starts after the lite `Q` ids), then door 3 or door 2 seeded from the lite entries, then door 5. Each lite `Q` keeps its id.
- **A legacy lite file** (`prototype/requirements-lite.md`, from runs before this skill) stays where it is. Check it with `check-contract.py <T>/prototype/requirements-lite.md`; a contract that follows copies its `R` and `Q` ids into `prd.md` unchanged.
