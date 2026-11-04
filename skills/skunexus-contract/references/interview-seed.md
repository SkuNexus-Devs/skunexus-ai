# Door 2: interview seed

**Goal:** the developer settles the real decisions in `skunexus-jira-prd`'s interview, starting from the evidence, with the options already in the PO's terms. This skill writes the seed; `skunexus-jira-prd` (unchanged) runs the interview, writes the PRD and asks for approval.

**Done when:** `prd.md` is seeded, `review/prd-seed-<DATE>.md` exists, and `skunexus-jira-prd` is loaded.

## Why a seed, and what can go wrong

- `skunexus-jira-prd` resumes from disk: with `prd.md` present and §7 holding items, its Step 0 picks up the interview from §7 and doesn't refetch the ticket. Without a `prd.md` it would run its own fetch (which calls `getAccessibleAtlassianResources` and rewrites `jira-summary.md`) and ignore `research/` and the baseline.
- Its rules differ from this pipeline's in three ways, so the seed carries the missing ones as text (the note below):
  - it has no "PO-literal option first" rule and no option tags; on FFD-14, untagged larger options were picked unknowingly 15 times;
  - its "never infer" rule re-asks every evidence-settled item, so those are batched as one confirmation;
  - it **clears** an answered §7 item. Cleared `Q` ids break the citations, chips and rulings that point at them, so the seed is snapshotted and the harden door restores every seeded `Q` that came back missing (model.md §3).

## Steps

1. Create `prd.md` from `<SKILL>/../skunexus-jira-prd/assets/prd-template.md`. Fill the title (`# PRD: <TICKET> — <Title>`), `> Status: Draft` and a `> Source:` line naming every input (`Jira <TICKET> (pulled <DATE>)`, each `input/` file by title and date, `research R1–Rn`, `review/po-baseline.md`). Leave §1–§6 as the template: the interview fills them.
2. Write §7 (heading kept as `## 7. Open Questions`) from the evidence door's notes, with the same `Q` ids:
   - **For the PO / client:** one entry per question in the Open shape, architecture-changing first:
     `- **Q3** <question> Options: (A) <ticket- or PO-literal> [PO decided] · (B) … [silence] · (C) … [expansion, M]. Evidence: research/R2-<slug>.md:40; po-baseline PO-4.` No `Recommended:`: on earlier tickets the developer overrode 9 of 11 evidence-backed recommendations.
   - Items the evidence settled: the Assumed shape, `- **Q7** <question> Assumed: <default>. Evidence: <file:line or quote>. Confirm with the developer.`
   - **For the tech lead:** `J-` entries the same way.
   - The researchers' `NEW-n` items take the next free `Q` ids.
3. Put the **interview note** (below) at the top of §7, under the heading.
4. Run `python3 -I <SKILL>/scripts/check-contract.py <T>`. Placeholders in §1–§6 are expected; fix anything in §7.
5. Snapshot the seed: `cp <T>/prd.md <T>/review/prd-seed-<DATE>.md`. It is not a version: no version line and no `review/prd-v*` name.
6. Update the memory note (model.md §8; next: the harden door after the interview).
7. Tell the developer in one line that the interview runs in `skunexus-jira-prd` and that "continue <TICKET>" comes back here when it ends. Then load `skunexus-jira-prd` for `<TICKET>`.

## The interview note (paste verbatim, fill the date)

```markdown
> **Interview note (seeded by skunexus-contract on <DATE>; the contract's harden door removes it).**
> The evidence is on disk: `jira/`, `jira-summary.md`, `input/`, `research/R*.md`, `review/po-baseline.md`. Cite it; don't refetch the ticket.
> 1. Open with "What the evidence settled (pending your confirmation)": every `Assumed` item below as one numbered list, answered with "yes to all" or corrections. Then "Must-haves the ticket doesn't mention".
> 2. Then one decision per turn, architecture-changing first: a short evidence paragraph or table, the lettered options as written here (the ticket- or PO-literal option first, each tagged `PO decided`, `silence` or `expansion, S/M/L`), presented neutrally (a recommendation only if asked), and a closing `needs input: …`.
> 3. In the first question, define every acronym and cite each source by title and date.
> 4. Prefer business agreements and known small limits over edge-case code. Record any option the developer invents word for word.
> 5. Keep every answered entry and its id: rewrite it as `Decided <DATE> (developer, option X): <answer> → <R ids>` instead of clearing it.
```

## After the interview

`skunexus-jira-prd` ends with a Draft or an `Approved` PRD and stops. "continue <TICKET>" opens door 5 (harden), which:
- adopts an `Approved` PRD that has no `> Versions:` block before changing it (`references/versions.md`, "Adoption");
- runs `check-contract.py <T> --prev review/prd-seed-<DATE>.md` and restores every seeded `Q` that came back missing, as `Decided` in the Decision log, citing where its answer landed;
- removes the interview note.
