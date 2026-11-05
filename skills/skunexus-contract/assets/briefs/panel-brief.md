<!-- Door 5 (harden): the discovery review panel, run as parallel agents. Copy to .ai/<TICKET>/review/panel-BRIEF.md and fill it; the synthesis steps at the end are for the orchestrator.
     Extra placeholders: <VERSION> (the frozen version, e.g. v1), <FROZEN_PRD> (review/prd-<VERSION>-<DATE>.md), <FROZEN_WORKFLOWS> (review/workflows-<VERSION>-<DATE>.md, or "none"), <PERSONAS> (rows picked from the panel table), <CLAIMS> (named code claims for V1), <VIEW_INPUTS> (the storyboard v1 file and the open feedback.md entries as of the freeze, or "none"), <RELATED_SOURCES>. Standard placeholders: see the skill's SKILL.md. -->
# <TICKET> contract review panel brief (<VERSION>)

## The contract is frozen
Every reviewer reads `<FROZEN_PRD>` and `<FROZEN_WORKFLOWS>`, copies taken before fan-out, never the live `prd.md` or `workflows.md`. The orchestrator queues every contract edit until the synthesis is written. On FFD-13 the PRD was edited while reviewers read it, and two of them reported reading a moving file.

## Inputs
- `<FROZEN_PRD>` and `<FROZEN_WORKFLOWS>`.
- `review/po-baseline.md` (PO-n decisions, X-n contradictions, #n rows) and `review/deviations.md` (DV-n), when they exist.
- `research/*.md`, `review/baseline/B0–B2*.md`, `input/`, `jira/`.
- Code in `<REPO>` (check `patches/` before trusting vendor) and <RELATED_SOURCES>.
- What the views found so far: <VIEW_INPUTS>. Cite a `feedback.md` entry by its id (`FB3`); don't repeat it.

## The panel
Functional roles (they are not people) plus named personas (simulated). Use 4–6 reviewers: always V1, V2 and the simulated PO; add the tech lead, the FE developer (when there is UI), the BE reviewer, V3 big-picture or the developer as the ticket warrants (FFD-13 ran 5). IDs are `V1…Vn`.

| ID | Role | Checklist |
|---|---|---|
| V1 | **Code fact-checker** (red team) | Every statement about **existing** behaviour (core, connector, sibling tickets) must be true in code, in the PRD and in the steps' Before → after. Hunt especially for "nothing exists / no X" claims and for criteria that assert behaviour core doesn't have. Check these named claims: <CLAIMS>. file:line for each, `patches/` first |
| V2 | **Traceability auditor** | Every ticket ask maps to an R or a Non-Goal. R↔criterion both ways. Criterion ↔ step both ways, and every "Not exercised" reason holds. Criteria drafted before a §4 amendment that now contradict or under-cover their R. Falsifiability. Decisions faithful to §7 and the Decision log (and `review/prd-pre-assembly.md` if present). Recount every tally; resolve every cross-reference; run `python3 -I <SKILL>/scripts/check-contract.py <FROZEN_PRD>` |
| V3 | **Big-picture / unified behaviour** | Is behaviour one coherent product: manual vs automatic paths, two surfaces doing one job, limits × status × reopen, edits vs downstream documents? Contradictions between R-ids, and between a step's outcome and its criteria. Terminology. A **truth table** for the interacting rules, with the undefined cells flagged. Answer each open storyboard entry from contract text, or mark it a gap |
| V<n> | Simulated **<PO>** (PO) | Does the contract deliver what the PO agreed (their decisions = `po-baseline.md`)? Which DV-n they'd accept or reject. Scope vs the parts they asked for. What the client will push back on. Client-facing wording, including each part's Scope. A paste-ready Jira answer if they asked a question in the ticket |
| V<n> | Simulated **<TECH_LEAD>** (tech lead) | Placement: client overlay vs core vs connector. Reuse of precedent tickets. Is any requirement really a general core issue that belongs in a Core bug report? Consistency with the connector decisions in the repo `CLAUDE.md`. Unsurfaced risks. An edge-case matrix |
| V<n> | Simulated **BE reviewer** | Data integrity, concurrency, idempotency; falsifiable criteria with negative paths; system, schedule and integration steps that can't happen as written; red-team every code claim in Notes for Design and in the research the contract relies on |
| V<n> | Simulated **<FE_DEV>** (frontend) | Every `user` step's surface and its sizing drivers: "everything they'd need before they could size it". The BE contract (reads, writes, error shapes, permissions). Storyboard vs contract. The real FE overlay and bundles in `frontend-client/` |
| V<n> | Simulated **<DEVELOPER>** (owner) | Implementability in this repo; cost drivers and cut lines; over-specified "how". Read-only data probes via `<SANDBOX_CALL>` when a premise is data-shaped (FFD-14: probes found four core-option families and overturned three interview answers) |

This ticket's panel: <PERSONAS>

## Persona grounding
- If `~/.claude/people/<slug>.md` exists, read it and use its role, **Review lens**, **Positions and decisions**, and the **10 most recent Observation-log entries**. If it doesn't exist on this machine, treat it as a thin profile (below) and run the role from its checklist row.
- PO persona: the profile (if any) **plus** `review/po-baseline.md` as their decisions.
- Developer persona: there is no profile. Use the "Me" section of `~/.claude/CLAUDE.md` (if present), the repo `CLAUDE.md` style guide and the repo's memory notes, and say the profile is thin.
- **Thin profile:** say so in the review, lean on the documented role, and **ask** rather than predict on points the profile doesn't cover. Never invent opinions the person hasn't shown.
- Head the output "**Simulated <Name> review**". It is never the person's opinion: never quote it in the contract or in anything sent to others, and write no profile entries from simulated content.

## Common rules (every reviewer)
- **Flag, don't decide.** Raise issues, risks, gaps and questions with options; never re-specify the contract.
- **Evidence required:** file:line, a transcript timestamp, or a PO-/X-/DV-/R-/s-/FB- id. A finding without evidence is marked `evidenced: no`, and its score is capped at 40.
- **Score 0–100:** 90+ blocks the estimate or architecture, or contradicts the PO with evidence · 70–89 likely changes a requirement · 50–69 worth fixing · under 50 a nit.
- **Cite DV-n and FB-n, don't repeat them** ("agrees with DV-11"); add only what's new: a consequence, an edge case, a fix.
- Keep the parts the PO asked for. Panels drift toward more structure (FFD-14: a five-part estimate was proposed and rejected).
- Read-only everywhere except your own output file. No Jira or Confluence writes (reads follow the repo `CLAUDE.md` Atlassian rules, cloudId `<JIRA_SITE>`, `maxResults: 10`). The client's systems only through `<SANDBOX_CALL>`, read-only: counts and value shapes, no PII. Never Read PNG/JPEG files.

**Before spawning,** create `review/panel/.gitignore` containing `*`: the persona files are working notes and never reach a commit.

**Spawn** (one agent per reviewer, all in one message; V2 as `sn-writer`, every other reviewer as `sn-judge`): "Read `review/panel-BRIEF.md`. You are <ID>, <role | Simulated <Name>>. Write `review/panel/<ID>-<slug>.md`."

## Finding format
Write `review/panel/<id>-<role>.md`, headed "Simulated <Name> review" (persona) or "<Role> review" (functional). Findings, most severe first:

`ID · location (section / R-id / criterion / step) · type · as written · problem · evidence · suggested text · score · impact · owner · evidenced`

- **type:** fact / contradiction / edge-case / silent-assumption / missing / unified-behaviour / testability / feasibility / scope-cost / wording / question
- **impact:** architecture-estimate / po-confirm / developer-decision / editorial
- **owner:** developer / PO / tech-lead / FE

End with **Top 5** (finding ids) and **Confirmed OK** (what you checked and found right; it shows your coverage, and a file without it counts as unfinished). Return to the orchestrator ≤20 lines: counts and your top 5, one line each.

---

## Synthesis (orchestrator)
1. **Wait** for every completion notice before reading the files. **Resume** (a session ended mid-panel): a reviewer file is complete when it ends with its Confirmed OK section; the planned list is "This ticket's panel" above, so a reviewer with no file at all is incomplete too. Re-run only the incomplete reviewers as fresh agents with this brief and the same frozen snapshots, then continue from step 2 over every file.
2. **Cluster:** dedupe across reviewers and keep the strongest evidence; every finding id lands in exactly one cluster; record where reviewers disagree. Route each cluster to the **source** skeptic (decided by baseline, transcript or Jira facts), the **code** skeptic, or **both**. Use one `sn-writer` agent for this, or do it yourself for fewer than ~60 findings.
3. **Filter:** verify a cluster if its max score is ≥ 50 or ≥ 2 reviewers raised it. Log the rest as skipped, each with a one-line reason; never drop one silently. Rank clusters raised independently by several reviewers first (FFD-13: one raised by three reviewers was decisive).
4. **Verify** with skeptics that wrote none of the findings:
   - source-truth (`sn-judge`): baseline, B0–B2, transcript, doc, Jira, and "is the contract really saying this?";
   - code-truth (`sn-scout`): the repos and the research (code wins), file:line. The code skeptics run on a different model family from the Opus reviewers on purpose: copies of one model share blind spots, so a mixed-family jury catches what they agree on wrongly.

   Each returns per cluster: refuted yes/no · confidence H/M/L · reason · evidence · corrected claim. Status: confirmed / contested / refuted / unverified. When stakes are high, use one skeptic per cluster: two batch skeptics confirmed 58 of 58 on FFD-14, which may mean they were lenient.
5. **Synthesizer** (`sn-writer`) writes `review/panel-synthesis.md` in this order:
   1. counts (raw findings → clusters → confirmed / contested / refuted / skipped) and the 5 decisions that change the most;
   2. `PD-1…PD-n`: panel decisions that change architecture, behaviour or scope, each with the type it would file as (`WRONG` / `CHOICE` / `SILENCE`), lettered options (the ticket- or PO-literal one first, tagged), a recommendation, evidence and the ids affected;
   3. `Q-1…Q-n` for <PO>, merged with the deviations questions, deduplicated, each tied to its PO-/X-/DV- ids; at the rulings each takes the next free §7 `Qn`;
   4. `I-n` items for the developer and `TL-n` items for the tech lead (not `J-n`: `J-` ids are the contract's own, §7 "For the tech lead");
   5. `E-1…E-n` proposed contract edits as concrete id changes (add / modify / retire), **not applied**;
   6. the unified-behaviour truth table, undefined cells marked;
   7. answers to the open storyboard entries (answered by the contract / a gap / needs a decision);
   8. precedent relevance (what to reuse or avoid from reference tickets), if any;
   9. contested items, both sides, with the skeptics' corrections;
   10. refuted and skipped, one line each with the reason;
   11. **Feedback entries:** one per `PD-n`, in the `feedback.md` entry format (`### FB? · <TYPE> · panel PD-n · <DATE>` with Cites, What, Evidence, Proposed, `Status: open`).

   Persona-derived content is labelled "simulated".
6. **Spot-check** the top items yourself in the primary sources. Zero refutations is unusually clean and can mean lenient skeptics; narrowed claims are a sign of real scrutiny.
7. **File** section 11 into `feedback.md` with the next free `FB` ids, once no other writer is running, and record the mapping (`PD-2 → FB4`) in the synthesis. Then go to the rulings door.

**Lighter variant (FFD-13).** With about five reviewers and under ~100 findings, skip the clusterer and skeptics: verify every decision-changing claim in code yourself, then write `panel-synthesis.md` as the editor's instruction list: the verified facts; the decisions as `PD-n` with options (filed as feedback, step 7); the findings accepted per reviewer ("apply as suggested, adjusted to the rulings"); and the deferred items with owners.

## Numbering legend (review-local ids; they reach the contract only through rulings)
| Id | Meaning | Lives in |
|---|---|---|
| PO-n | PO decisions, in the PO's words | `po-baseline.md` |
| X-n | Contradictions or open items, as questions for the PO | `po-baseline.md` |
| #n | Baseline rows | `po-baseline.md` |
| DV-n | Deviations of the contract from the baseline | `deviations.md` |
| V-n | Panel reviewers; findings are `V<n>-<k>` | `review/panel/` |
| P-n | Drafting gaps from the drafters' notes | the drafting triage |
| PD-n | Panel decisions; each becomes one `FB` entry (`PD-2 → FB4`) | `panel-synthesis.md`, then `feedback.md` |
| Q-n | Questions for the PO; each becomes the next free §7 `Qn` (`panel Q-3 → Q21`) | `panel-synthesis.md`, then `prd.md` §7 |
| I-n / TL-n | Developer / tech-lead items; each `TL-n` becomes the next free §7 `J-` id (`TL-2 → J-5`) | `panel-synthesis.md` |
| E-n | Proposed contract edits | `panel-synthesis.md` |
