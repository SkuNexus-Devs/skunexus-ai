<!-- Stage: PRD review panel (parallel-agents variant; for the Workflow-tool variant use assets/panel-workflow.js, only when the user opts into a workflow). Copy to .ai/<TICKET>/review/panel-BRIEF.md and fill it; the synthesis steps at the end are for the orchestrator. Pattern: ~/.claude/rules/multi-agent-perspective-review.md.
     Extra placeholders: <FROZEN_PRD> (review/prd-<VERSION>-<DATE>.md; <VERSION> = the PRD header's version, v1 if none), <PERSONAS> (rows picked from the panel table), <CLAIMS> (named code claims for V1), <PROTOTYPE_QUESTIONS> (or "none"), <RELATED_SOURCES>, <REPO_SLUG> (the repo's ~/.claude/projects/ folder name). Standard placeholders: see SKILL.md. -->
# <TICKET> PRD review panel brief

## The artifact is frozen
Every reviewer reads `<FROZEN_PRD>`, a copy of `prd.md` taken before fan-out, never the live `prd.md`. The orchestrator queues every PRD edit (gap answers, fixes) until the synthesis is written. On FFD-13 the PRD was edited while reviewers read it, and two of them reported reading a moving file.

## Inputs
- `<FROZEN_PRD>`.
- `review/po-baseline.md` (PO-n decisions, X-n contradictions, #n rows) and `review/deviations.md` (DV-n), when they exist.
- `research/*.md`, `review/baseline/B0–B2*.md`, `input/`, `jira/`.
- Code in `<REPO>` (check `patches/` before trusting vendor) and <RELATED_SOURCES>.
- Questions a prototype or storyboard builder raised: <PROTOTYPE_QUESTIONS>.

## The panel
Functional roles (they are not people) plus named personas (simulated). Use 4–6 reviewers: always V1, V2 and the simulated PO; add the tech lead, the FE developer (when there is UI), the BE reviewer, V3 big-picture or the developer as the ticket warrants (FFD-13 ran 5). IDs are `V1…Vn`.

| ID | Role | Checklist |
|---|---|---|
| V1 | **Code fact-checker** (red team) | Every statement about **existing** behaviour (core, connector, sibling tickets) must be true in code. Hunt especially for "nothing exists / no X" claims and for ACs that assert behaviour core doesn't have. Check these named claims: <CLAIMS>. file:line for each, `patches/` first |
| V2 | **Traceability auditor** | Every ticket ask maps to an R or a Non-Goal. R↔AC both ways. ACs drafted before a §4 amendment that now contradict or under-cover their R. Falsifiability. Decisions faithful to the interview (§7, Decision log, `review/prd-pre-assembly.md`). Recount every tally; resolve every cross-reference; run `python3 -I <SKILL>/scripts/check-prd.py <FROZEN_PRD>` |
| V3 | **Big-picture / unified behaviour** | Is behaviour one coherent product: manual vs automatic paths, two surfaces doing one job, limits × status × reopen, edits vs downstream artefacts (labels, documents)? Contradictions between R-ids. Terminology. A **truth table** for the interacting rules, with the undefined cells flagged. Answer each prototype question from PRD text, or mark it a gap |
| V<n> | Simulated **<PO>** (PO) | Does the PRD deliver what the PO agreed (their decisions = `po-baseline.md`)? Which DV-n they'd accept or reject. Scope vs the estimate shape they asked for. What the client will push back on. Client-facing wording. A paste-ready Jira answer if they asked a question in the ticket |
| V<n> | Simulated **<TECH_LEAD>** (tech lead) | Placement: client overlay vs core vs connector. Reuse of precedent tickets. Is any requirement really a general core issue that belongs in a Core bug report? Consistency with the connector decisions in the repo `CLAUDE.md`. Unsurfaced risks. An edge-case matrix |
| V<n> | Simulated **BE reviewer** (e.g. the usual first approver) | Data integrity, concurrency, idempotency; falsifiable ACs with negative paths; red-team every code claim in Notes for Design and in the research the PRD relies on |
| V<n> | Simulated **<FE_DEV>** (frontend) | Every FE surface and its sizing drivers: "everything they'd need before they could size it". The BE contract (reads, writes, error shapes, permissions). Prototype vs PRD. The real FE overlay and bundles in `frontend-client/` |
| V<n> | Simulated **<DEVELOPER>** (owner) | Implementability in this repo; estimate drivers and cut lines; over-specified "how". Read-only data probes via `<SANDBOX_CALL>` when a premise is data-shaped (FFD-14: probes found four core-option families and overturned three interview answers) |

This ticket's panel: <PERSONAS>

## Persona grounding (`~/.claude/rules/team-personas.md`)
- Read `~/.claude/people/<slug>.md` and use its role, **Review lens**, **Positions and decisions**, and the **10 most recent Observation-log entries**. If the file does not exist on this machine, treat it as a thin profile (below) and run the role from its checklist row.
- PO persona: their profile **plus** `review/po-baseline.md` as their decisions.
- Tech-lead persona: their profile plus `~/.claude/projects/<REPO_SLUG>/memory/skunexus-design-feedback.md` (if present).
- Developer persona: there is no profile. Use the "Me" section of `~/.claude/CLAUDE.md`, the repo `CLAUDE.md` style guide and the memory files in `~/.claude/projects/<REPO_SLUG>/memory/`, and say the profile is thin.
- **Thin profile:** say so in the review, lean on the documented role, and **ask** rather than predict on points the profile doesn't cover. Never invent opinions the person hasn't shown.
- Head the output "**Simulated <Name> review**". It is never the person's opinion: never quote it in the PRD or in anything sent to others, and write no profile entries from simulated content.

## Common rules (every reviewer)
- **Flag, don't decide.** Raise issues, risks, gaps and questions with options; never re-specify the PRD.
- **Evidence required:** file:line, a transcript timestamp, or a PO-/X-/DV-/R- id. A finding without evidence is marked `evidenced: no`, and its score is capped at 40.
- **Score 0–100:** 90+ blocks the estimate or architecture, or contradicts the PO with evidence · 70–89 likely changes a requirement · 50–69 worth fixing · under 50 a nit.
- **Cite DV-n, don't repeat them** ("agrees with DV-11"); add only what's new: a consequence, an edge case, a fix.
- Keep the estimate shape the PO asked for. Panels drift toward more structure (FFD-14: a five-part estimate was proposed and rejected).
- Read-only everywhere except your own output file. No Jira or Confluence writes (cloudId `https://skunexus.atlassian.net/`, `maxResults: 10` if you read). The client's systems only through `<SANDBOX_CALL>`, read-only: counts and value shapes, no PII. Never Read PNG/JPEG files.

**Before spawning,** create `review/panel/.gitignore` containing `*`: the persona files are working notes and never reach a commit.

**Spawn** (one agent per reviewer, all in one message; V2 as `sn-writer`, every other reviewer as `sn-judge`): "Read `review/panel-BRIEF.md`. You are <ID>, <role | Simulated <Name>>. Write `review/panel/<ID>-<slug>.md`."

## Finding format
Write `review/panel/<id>-<role>.md`, headed "Simulated <Name> review" (persona) or "<Role> review" (functional). Findings, most severe first:

`ID · location (section / R-id / AC-id) · type · as written · problem · evidence · suggested text · score · impact · owner · evidenced`

- **type:** fact / contradiction / edge-case / silent-assumption / missing / unified-behaviour / testability / feasibility / scope-cost / wording / question
- **impact:** architecture-estimate / po-confirm / developer-decision / editorial
- **owner:** developer / PO / tech-lead / FE

End with **Top 5** (finding ids) and **Confirmed OK** (what you checked and found right; it shows your coverage). Return to the orchestrator ≤20 lines: counts and your top 5, one line each.

---

## Synthesis (orchestrator)
1. **Wait** for every completion notice before reading the files. **Resume** (a session ended mid-panel): a reviewer file is complete when it ends with its Confirmed OK section; the planned list is "This ticket's panel" above, so a reviewer with no file at all is incomplete too. Re-run only the incomplete reviewers as fresh agents with this brief and the same frozen PRD (Workflow variant: pass only those in `args.roles` / `args.personas`, `roles: []` when V1–V3 are complete, and the complete files in `args.done`), then continue from step 2 over every file.
2. **Cluster:** dedupe across reviewers and keep the strongest evidence; every finding id lands in exactly one cluster; record where reviewers disagree. Route each cluster to the **source** skeptic (decided by baseline, transcript or Jira facts), the **code** skeptic, or **both**. Use one `sn-writer` agent for this, or do it yourself for fewer than ~60 findings.
3. **Filter:** verify a cluster if its max score is ≥ 50 or ≥ 2 reviewers raised it. Log the rest as skipped, each with a one-line reason; never drop one silently. Rank clusters raised independently by several reviewers first (FFD-13: one raised by three reviewers was decisive).
4. **Verify** with skeptics that wrote none of the findings:
   - source-truth: baseline, B0–B2, transcript, doc, Jira, and "is the PRD really saying this?";
   - code-truth: the repos and the research (code wins), file:line.

   Each returns per cluster: refuted yes/no · confidence H/M/L · reason · evidence · corrected claim. Status: confirmed / contested / refuted / unverified. When stakes are high, use one skeptic per cluster: two batch skeptics confirmed 58 of 58 on FFD-14, which may mean they were lenient. Code skeptics run as `sn-scout`: a second model family checking Opus reviewers is the mixed-jury upgrade (`multi-agent-perspective-review.md`, "Upgrades"); the source skeptic runs as `sn-judge`. Compare the refuted and narrowed counts with the previous ticket's (FFD-35: 2 refuted and 13 narrowed of 44).
5. **Synthesizer** (`sn-writer`) writes `review/panel-synthesis.md` in this order:
   1. counts (raw findings → clusters → confirmed / contested / refuted / skipped) and the 5 decisions that change the most;
   2. `PD-1…PD-n`: panel decisions that change architecture or estimate, each with options, a recommendation, evidence and the R-ids affected;
   3. `Q-1…Q-n` for <PO>, merged with the deviations questions, deduplicated, each tied to its PO-/X-/DV- ids; at the rewrite each takes the next free PRD §7 `Qn`, and the mapping is recorded (`panel Q-3 → Q21`);
   4. `I-n` items for the developer and `J-n` for the tech lead;
   5. `E-1…E-n` proposed PRD edits as concrete R-id changes (add / modify / retire), **not applied**;
   6. the unified-behaviour truth table, undefined cells marked;
   7. answers to the prototype questions (answered by the PRD / a gap / needs a decision);
   8. precedent relevance (what to reuse or avoid from reference tickets), if any;
   9. contested items, both sides, with the skeptics' corrections;
   10. refuted and skipped, one line each with the reason.

   Persona-derived content is labelled "simulated".
6. **Spot-check** the top items yourself in the primary sources. Zero refutations is unusually clean and can mean lenient skeptics; narrowed claims are a sign of real scrutiny.
7. **Gate:** bring the developer the PD-list. When they say "apply the recommended path", go to the rulings brief: the recommended defaults become `(assumed, Qn)` markers plus §7 lines. Don't re-interview item by item, and keep the PO's estimate shape.

**Lighter variant (FFD-13).** With about five reviewers and under ~100 findings, skip the clusterer and skeptics: verify every decision-changing claim in code yourself, ask the developer the resulting decisions, then write `panel-synthesis.md` as the editor's instruction list: the verified facts; a "Developer decisions on panel findings" table (`Id · Decision · Affects`); the findings accepted per reviewer ("apply as suggested, adjusted to the decisions"); and the deferred items with owners.

## Numbering legend
| Id | Meaning | Lives in |
|---|---|---|
| PO-n | PO decisions, in the PO's words | `po-baseline.md` |
| X-n | Contradictions or open items, as questions for the PO | `po-baseline.md` |
| #n | Baseline rows | `po-baseline.md` |
| DV-n | Deviations of the PRD from the baseline | `deviations.md` |
| V-n | Panel reviewers; findings are `V<n>-<k>` | `review/panel/` |
| P-n | Drafting gaps from the drafters' notes | `prd.md` Decision log |
| PD-n | Panel decisions that change architecture or estimate | `panel-synthesis.md` |
| Q-n | Questions for the PO; each becomes the next free PRD §7 `Qn` (mapping recorded) | `panel-synthesis.md`, then `prd.md` §7 |
| I-n / J-n | Developer / tech-lead items | `panel-synthesis.md`, then §7 and Notes for Design |
| E-n | Proposed PRD edits | `panel-synthesis.md` |
