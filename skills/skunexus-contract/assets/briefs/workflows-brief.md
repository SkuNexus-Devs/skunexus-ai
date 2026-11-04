<!-- Door 5 (harden) and door 4 (lite): the use-case drafter writes workflows.md from the PRD and the evidence. Copy to .ai/<TICKET>/review/workflows-BRIEF.md and fill it; the last section is for the orchestrator.
     Extra placeholders: <PRD> (prd.md, or the frozen snapshot it was drafted from), <PARTS_SHAPE> (the PO's priced shape if known: parts, names and one-line scope, with where it comes from; else "one part, base"), <SCENARIO_HINTS> (flows the ticket, the call or the baseline describes, with their locations), <LITE> ("yes" for a lite contract: steps cite requirements, §6 may be empty). Standard placeholders: see the skill's SKILL.md. -->
# <TICKET> use cases: drafting brief

## Your job
Write `.ai/<TICKET>/workflows.md`, the use-case facet of the contract: scenarios → steps, each with an actor, a trigger, the entity's state before → after, what the actor sees, the ids it exercises, and its part. Start from the template already copied there and follow its comments. Also write `.ai/<TICKET>/review/workflows-notes.md` (below). Nothing else.

A step **restates** the contract; it never adds behaviour. If a flow needs behaviour the PRD doesn't state, don't invent it: write the simplest outcome the PRD allows, and list the step as ungrounded in your notes.

## Inputs, highest authority first
1. `<PRD>`: §4 requirements, §6 criteria, §7 decisions and assumptions, Non-Goals.
2. `review/po-baseline.md` (the PO's own flows and words), `jira/description.md`, `input/` (transcripts): <SCENARIO_HINTS>.
3. `research/*.md` and the code in `<REPO>` for how today's pages and jobs behave (stock behaviour), with file:line.

## Rules
- **Scenarios:** 3–6 end-to-end cases the PO would recognise, each 2–7 steps, named in the PO's words. Cover the main path, the refusals and errors the criteria define, and every non-user trigger (system, schedule, integration) the requirements touch.
- **Step ids** `s<n>.<m>`, numbered in order inside each scenario. **Actor** is a role (warehouse user, permitted user, the integration, system), never a person's name. **Trigger** is exactly one of `user`, `system`, `schedule`, `integration`.
- **Before → after** names the entity's state (`order Open, undecided → unchanged`); **Outcome** is what the actor sees or what happens, in one plain clause.
- **Cites:** every `R` and criterion the step exercises (at least one live `R` or criterion), plus any `Q` it relies on. Bare ids are this PRD's; another ticket's ids carry its key and don't count.
- **Coverage, both ways:** every live criterion (with `<LITE>` = yes: every live requirement) is cited by at least one step, or listed under "Not exercised" with its reason (e.g. "proved by a test; no step shows it"). Retired ids are never cited.
- **Parts:** <PARTS_SHAPE>. Every step fills its Part cell. Scope is one or two plain sentences for the PO, with no ids. Never invent a part.
- **Contradictions:** a step whose evidence contradicts a criterion is written as the criterion says, and listed in your notes as a contradiction with the evidence.
- Read-only everywhere except your two files. No Jira, Confluence or client-system writes. Never Read PNG/JPEG files.

## `review/workflows-notes.md`
1. **Grounding:** one line per step, `s1.3 · evidence (file:line, PO-n, call m:ss, or "PRD only")`.
2. **Ungrounded steps:** `s<n>.<m> · what it assumes · the proposed outcome · who should confirm`.
3. **Contradictions:** `s<n>.<m> · criterion · evidence`.
4. **Coverage:** counts of live criteria cited, listed under Not exercised, and steps per scenario.

Return ≤15 lines: scenario and step counts, the ungrounded and contradiction counts, and anything you could not place.

---

## Orchestrator
- Spawn one `sn-writer`: "Read `review/workflows-BRIEF.md` and follow it. You are the use-case drafter."
- After the completion notice, run `python3 -I <SKILL>/scripts/check-contract.py .ai/<TICKET>` and fix the coverage errors it reports (a missing citation is usually a missing step or a "Not exercised" line).
- Ungrounded steps and contradictions go to the developer in one message (attended) or become `Assumed` entries and `WRONG` feedback (unattended): `references/harden.md` §2.
