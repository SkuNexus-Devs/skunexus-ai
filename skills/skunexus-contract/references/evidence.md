# Door 1: evidence

**Goal:** every input on disk, dated, before anyone drafts a rule or asks the developer a question. Evidence is the provenance facet of the contract (model.md §1): it is what makes resumes, unattended runs, panels and re-pull diffs possible.

**Done when:** `jira/` (the puller layout), `jira-summary.md` with the ticket's last-updated time, `research/R*.md`, and `review/po-baseline.md`, or the developer skipped the baseline and you said so.

## 1. Pull the whole ticket

1. Run the "Puller prompt" in `assets/briefs/reeval-brief.md` with `<PULL_DIR>` = `jira/` (one `sn-scout` agent). "Not just the summary" is the developer's standing request. Don't use `skunexus-jira-prd`'s fetch: it calls `getAccessibleAtlassianResources` and drops timestamps.
   - Layout: `jira/description.md`, `jira/comment_<author>_<date>.md`, `jira/inventory.md` (fields, changelog with timestamps, attachment list, last-updated), `jira/linked/`, `jira/attachments/`.
   - A copy of the ticket in another ticket's `linked/` folder is a snapshot: pull fresh and diff against it.
   - `jira/` is the first pull and is never overwritten. Later pulls go to `jira-<DATE>/` (door 6).
2. Write `jira-summary.md` from `<SKILL>/../skunexus-jira-prd/assets/jira-summary-template.md`, adding:
   - a "Connections to <related tickets>" section: sibling tickets in the same client folder and precedent tickets the developer names. For a precedent in another client's repo, read that repo's `.ai/<KEY>/` and code. If this repo's `CLAUDE.md` limits Jira to one project key, ask before reading another project's Jira;
   - the ticket's last-updated time.
3. List `input/` and send the developer one **"please provide"** list before fanning out: call transcripts, Basecamp posts, attachments that failed to download. FFD-14 fanned out before the call transcript was in `input/`, and two agents had to be relaunched. Optional context questions can be asked while agents run.

**Gate:** none, but wait for the answer to the "please provide" list (or "nothing more") before step 2.

## 2. The question list

Write the open questions into `research/BRIEF.md` (from `assets/briefs/research-brief.md`), not into a `prd.md`: a `prd.md` on disk would tell `skunexus-jira-prd` and the ownership table that the PRD exists.

- Sources: the summary's flagged uncertainties, the ticket's own questions, and the gaps a feature of this shape must handle (error paths, edge inputs, affected surfaces, permissions, interaction with existing behaviour).
- Number them `Q1…Qn`, architecture-changing first. **These ids are final**: door 2, 3 or 4 carries them into `prd.md` §7 unchanged.

## 3. Research and PO baseline (one message, in parallel)

- **Researchers** (`assets/briefs/research-brief.md`): each owns a set of `Q` ids. Run one narrow researcher per external reference (another client's implementation, the core package, the sandbox data). Reference and data researchers are `sn-scout`; a researcher who judges this client's own baseline is `sn-worker`.
  - A browser walkthrough of another client's app is the costliest kind of agent. Give it a fixed page list tied to `Q` ids. Grant a write walkthrough only for a named decision the code can't settle, as a separate fresh agent.
  - Data probes are read-only: client CSVs and `<SANDBOX_CALL>`, counts and value shapes only. One probe showed a requirement's premise false in 261 of 261 shipped orders.
- **PO baseline** (`assets/briefs/baseline-brief.md`): run it whenever the PO wrote a desired-state doc or a substantial description; skip it for a thin ticket and say so. B0 reads the transcript only (skip it with no transcript); B1 builds the delta; B2 the prior context; the synthesizer writes `review/po-baseline.md` from the sources, **never from `prd.md`**. Running the baseline after the interview (FFD-14) overturned eight requirements the next day.
- You read only the description and the PO's own documents. Agents read the rest.

## 4. Verify and hand on

- Wait for each completion notice before reading an agent's file.
- Check every claim that will shape a requirement yourself, in the primary source, even when two agents agree (FFD-13: "two agents made the permission claim, so I'll check the ACL config myself"). Grep the exact text of the top PO quotes; re-read the PO's words for every paraphrase that shapes a decision; recount data claims.
- For each `Q`, note **evidence → proposed default → who decides**, and tag each option `PO decided` / `silence` / `expansion, S/M/L`, the ticket- or PO-literal option first. Doors 2, 3 and 4 write these into §7; the tags are what keep scope at what the PO asked (15 unchosen expansions on FFD-14 before tagging).
- Collect the researchers' `NEW-n` items (gaps nobody raised): each becomes the next free `Q` when §7 is written.

**Next door:** attended (workflow `prd-storyboard-estimate` or `prd-storyboard`) → door 2 (interview seed); unattended (workflow `unattended`) or "draft it with defaults" → door 3; a lite workflow (`lite-storyboard`, `lite`) → door 4.
