<!-- Stage 12: re-pull + diff + impact re-evaluation, before the daily, before posting an estimate, and whenever the ticket moved (offer it; don't run it unasked). Copy to .ai/<TICKET>/review/reeval-<DATE>/BRIEF.md; run the Puller prompt (orchestrator section) first, then fill <CHANGE_SUMMARY> from its diff. Stage 1 uses only the Puller prompt, with <PULL_DIR> = jira/.
     Extra placeholders: <PULL_DIR> (jira/ at stage 1, jira-<DATE>/ at stage 12), <PREV_PULL_DIR> (e.g. jira/), <PREV_PULL_TIME>, <CHANGE_SUMMARY>, <ARTIFACT_STATE> (status and counts of prd.md, backend-plan.md, decisions.md, estimate.md, prototype/artifact.md), <RELATED_TICKETS>, <A4_TOPIC>. Standard placeholders: see SKILL.md. -->
# <TICKET> re-evaluation brief (<DATE>)

<CHANGE_SUMMARY>

## Inputs, in order of authority for "what <PO> and the client now want"
1. `.ai/<TICKET>/jira-<DATE>/description.md` and its `comment_*.md`: the new ticket text, verbatim.
2. `.ai/<TICKET>/jira-diff-<DATE>.md`: the diff against `<PREV_PULL_DIR>` (pulled <PREV_PULL_TIME>).
3. `.ai/<TICKET>/jira-<DATE>/linked/`: newly linked tickets.

## What we have (the artifacts to re-evaluate)
<ARTIFACT_STATE>

Context: `research/`, `plan-parts/`, `input/`, related tickets' PRDs and decisions, the repo `CLAUDE.md`.

## Rules
- Read-only everywhere except your own output file in `.ai/<TICKET>/review/reeval-<DATE>/`. No Jira or Confluence writes (cloudId `https://skunexus.atlassian.net/`, `maxResults: 10` on any read). The client's systems only through `<SANDBOX_CALL>`, read-only: counts and value shapes, no PII. Never Read PNG/JPEG files.
- **Don't decide product questions.** For each item give: what the ticket now says (quoted, with its line), what we have (cite the R-, Q-, T- or D- id), a class, a proposed action, and who decides (developer / <PO> / client / <TECH_LEAD> / <FE_DEV>).
- Where the developer's interview decisions now conflict with <PO>'s text, say so. Those are **conversations for the daily, not silent edits.**

## Classes
| Class | Meaning |
|---|---|
| CONFIRMS | Already covered the same way |
| ANSWERS | Settles a deferred §7 item |
| CONTRADICTS | Conflicts with an approved decision or requirement |
| NEW-SCOPE | Not in the PRD, or currently a Non-Goal |
| REMOVES | Something we built in is no longer asked for |
| AMBIGUOUS | The ticket is unclear or contradicts itself |
| NO-IMPACT | Nothing to do |

## Output format
`ID · ticket ref (line) · as the ticket says · what we have (cite) · class · proposed action · decider · confidence`

End with a short **Top 5 for the daily**. Return ≤25 lines to the orchestrator.

## Analysts
| ID | Output file | Job |
|---|---|---|
| A1 | `A1-prd-impact.md` | Item by item over the new ticket text (background, requirements, open items, workflow, goal, and text that was removed) against `prd.md`. Then a "Proposed PRD changes" table (`RC-n · change · kind`) and a tally by class |
| A2 | `A2-plan-impact.md` | A verdict on every plan task (T-n) and `decisions.md` decision (D-n); new tasks sized in steps, as the plan counts them; a size-delta table (scope · steps · waves). Read-only data probes may settle a question (record codes and counts only) |
| A3 | `A3-cross-ticket.md` | Conflicts with sibling tickets (<RELATED_TICKETS>): which ticket owns each new ask, which approved PRD it would amend, and estimate deltas that belong to another ticket. Read-only Jira reads of related tickets are allowed |
| A4 (optional) | `A4-<A4_TOPIC>.md` | A deep-dive for <TECH_LEAD> on one new item that needs design: platform facts (what blocks or enables it, file:line), options (a)…(d) with step counts, a comparison and a recommendation. Facts and options only, no product decision. Write it in two parts (Write, then Edit to append) and finish both: FFD-13's A4 stopped at its part-2 marker, so its options were never written |

---

## Orchestrator

### Puller prompt (stages 1 and 12)
One `sn-scout` agent; at stage 12 it runs first. Stage 1 doesn't use skunexus-jira-prd's fetch: it calls getAccessibleAtlassianResources, drops timestamps and writes no `jira/` folder.

"Pull <TICKET> from Jira into `.ai/<TICKET>/<PULL_DIR>`. Follow the repo `CLAUDE.md` Atlassian rules: cloudId `https://skunexus.atlassian.net/` (never call getAccessibleAtlassianResources), its project key, `maxResults: 10` on every JQL and CQL search. Read-only: never write to Jira or Confluence. Layout:
- `description.md`: the description, verbatim;
- `comment_<author>_<date>.md`: one file per comment, verbatim, with its created and updated times;
- `inventory.md`: the fields (status, assignee, priority, estimates, time spent, links), the changelog with timestamps (`When · Who · Field · From → To`), the attachment list, and the issue's last-updated time with timezone; end it with **Not downloaded** (and why) and **Needs vision**;
- `linked/`: linked issues and Confluence pages, one file each. A linked ticket in a project key the repo `CLAUDE.md` doesn't allow: don't read it, list it under Not downloaded;
- `attachments/`: the downloaded attachments. Never Read an image: OCR it first (`tesseract <img> stdout --psm 11`) and list what OCR can't settle under Needs vision (no `tesseract`: list every image there).

If another ticket's folder holds a copy of <TICKET> (e.g. `.ai/<OTHER>/jira/linked/`), it is a snapshot: pull fresh anyway, and at stage 1 write the diff below against it. At stage 12 never overwrite `<PREV_PULL_DIR>` (it is the baseline) or `jira-summary.md`; write only the dated files. Stage 12 (or a snapshot): then write `.ai/<TICKET>/jira-diff-<DATE>.md`, facts only, with no interpretation against the PRD or plan:
- header: the baseline pull time and the new pull time (with timezone);
- **At a glance:** what changed, who changed it and when, line counts;
- **Changelog since the baseline:** `When · Who · Field · From → To`, plus edits the changelog doesn't show (a comment's `updated` time);
- **Description diff** (unified) and **Substantive changes, in plain language**;
- **New or edited comments**, verbatim;
- **Field changes:** status, assignee, approvals, time spent, links;
- **New linked content**, and **related tickets changed**;
- **Needs vision** and **Not downloaded**;
- the issue's last-updated time.

Return ≤15 lines."

**After the re-pull:** read the new description yourself, write <CHANGE_SUMMARY> into this brief, and launch A1–A3 (and A4 if a new item needs design) in parallel.

**After the analysts**
1. Wait for every completion notice.
2. Write `review/reeval-<DATE>/SYNTHESIS.md`:
   - inputs, and the analyses with one line of counts each;
   - **What changed in the ticket (substance):** scope that grows (Non-Goals pulled in), questions it settles, what it confirms, what's ambiguous, what was removed, new deliverables, new references;
   - **Verified facts that shape the answers:** check every decision-shaping claim in code or data yourself; where analysts disagree, take the more conservative reading;
   - **Size impact** (`scope · steps · waves`);
   - **For the daily:** numbered items, each with the question, who answers it, the options and the recommended answer.
3. **Gate:** the developer answers the daily list (often "yes to all"). Then write `review/reeval-<DATE>/APPLY-BRIEF.md` from `assets/briefs/rulings-brief.md`: keep its Global rules and Header sections; Inputs = `prd.md`, `review/reeval-<DATE>/SYNTHESIS.md`, `jira-diff-<DATE>.md`; then the decisions; the **fixed new ids and their text** ("use exactly these"), continuing from the last id with no gaps; and the daily-dependent items, flagged "pending daily (<DATE>)" with an owner.
4. Apply it through the rulings route: run the Editor, Checker and Fixer prompts of `rulings-brief.md` with `review/reeval-<DATE>/APPLY-BRIEF.md` in place of `review/rulings-BRIEF.md` and `review/reeval-<DATE>/SYNTHESIS.md` in place of `review/panel-synthesis.md`, then `python3 -I <SKILL>/scripts/check-prd.py prd.md --prev <backup>`. An Approved PRD becomes `Status: Draft (amending approved v<N>, <DATE>)` until the developer re-approves; its version line reads `<VERSION> <DATE>: applied review/reeval-<DATE>/APPLY-BRIEF.md`. Then re-sync the storyboard (`QT`, `PARTS`; `storyboard.md` §6) and the `estimate.md` parts whose scope or size moved, and list the plan deltas (tasks added, changed, retired) for the developer. Never edit silently.
5. Put the ticket's last-updated time in the PRD header, and update the memory note.
