# Backend Plan: <TICKET-KEY> — <Title>

> Status: Draft  <!-- flip to "Approved" ONLY after the developer explicitly accepts -->
> Contract: .ai/<TICKET-KEY>/prd.md   <!-- or: "inline (see Goal & Acceptance below)" when there's no PRD -->
> Scope: Backend only. See "Frontend-facing surface (intended)" for the public seam; the as-built FE handoff (exact request/response/error shapes) is a later step, produced post-implementation from the real diff.

<!-- ─────────────────────────────────────────────────────────────
     Goal & Acceptance — INCLUDE ONLY when there is no prd.md (the inline-spec door).
     This block is the contract: it lives at requirement altitude, above the step-level
     detail that may drift. Omit the whole section when a prd.md exists.
     ───────────────────────────────────────────────────────────── -->
## Goal & Acceptance
**Goal:** <!-- 1–2 sentences: what's changing and why. -->
**Non-goals:** <!-- explicit out-of-scope, so tasks don't sprawl. -->
**Acceptance:**
- **A1** <!-- testable "shall" statement; tasks trace to these IDs -->
- **A2** …

## Overview
<!-- 2–4 sentences: the technical approach in brief — which domain(s)/surfaces are touched and the shape of
     the solution. NOT a task list. -->

## Task Manifest (the DAG)
<!-- The dependency graph at a glance — REVIEW THIS FIRST. `depends_on` wires the graph (must be acyclic).
     Tasks with no dependency path between them run in parallel.
     PROPORTIONALITY: for a one- or two-task change, drop this table and just list the task(s) below — a
     two-node graph isn't worth a manifest. -->

| ID | Task | depends_on | Satisfies |
|----|------|------------|-----------|
| T1 | …    | none       | R1 / A1   |
| T2 | …    | T1         | R2, R3    |

**Execution waves** (derived from `depends_on` — what can run in parallel):
- **Wave 1** (no deps): T1, …
- **Wave 2** (after wave 1): T2, …

## Tasks
<!-- Detailed, in dependency order. Each task is SELF-CONTAINED: an implementation agent picks up ONE task and
     must not have to read another task's ENTRY (or ask a question) to proceed. It DOES read the real code its
     depends_on tasks have already produced — those run first, so their code is available and is the source of
     truth for exact signatures.
     STEP FORMAT — this is what makes the plan usable:
     · one atomic action per `- [ ]` step, verb-first, checkable in isolation;
     · the exact file path / class / method named IN the step (no separate Files list to cross-reference);
     · the SkuNexus pattern to mirror cited inline, in the step it guides (a real existing file);
     · no placeholders ("add validation", "handle errors") — name the specific check and the exception;
     · no cross-references ("see T2", "as above") — repeat the content;
     · literal code only for contracts that MUST be exact (a signature, a migration column, a response shape);
     · a short parenthetical "why" is fine; longer rationale goes to decisions.md, not the step. -->

### T1 — <title>
**Status:** not_started  <!-- not_started|started|finished — DERIVED from the checkboxes below: not_started
                              while no step is checked, started once the first step is checked, finished only
                              when every step is checked. The implementation skill checks boxes and flips this
                              as work lands; the plan is the live progress tracker for the ticket -->
**Depends on:** none
**Satisfies:** R1  <!-- requirement IDs: Rn from the PRD, or An from the inline Goal & Acceptance.
                        Traceability is durable — it's how the PR/testing skills map back. -->
<!-- **Existing work:** ONLY when Status is started|finished at planning time — the concrete evidence (file
     paths, classes, commit SHAs) and, for started, what's left. Never carry a status on the PRD's word
     alone. Omit the line entirely for not_started. -->

- [ ] <atomic step: create/edit `<exact path>` — what it contains (class, extends, key constants/signature); pattern to mirror>
- [ ] <atomic step>
- [ ] …

**Out of scope:** <one line — the boundary; which task owns what's excluded>  <!-- omit if nothing to say -->
**Sanity-check now:** <one line — how the implementor confirms this works in the moment; non-durable, the
testing-steps skill derives from acceptance criteria + merged code, not from here>  <!-- optional -->

### T2 — …
<!-- repeat -->

## Frontend-facing surface (intended)
<!-- The public seam this DAG introduces — the INTENDED baseline a later FE-handoff step reconciles the real
     diff against, NOT the as-built handoff. One line per item: name + method/verb + auth. Stop at the seam:
     exact request/response/error shapes are the post-implementation handoff's job, derived from the real
     code — pinning them down here just guarantees they rot as implementation drifts. -->
- **Endpoints / resolvers:** <!-- one line each: REST route or GraphQL field; method; auth/permission -->
- **Events the FE relies on:** <!-- one line each, if any -->
<!-- If the change has no frontend-facing surface, replace this whole list with:
     None — backend-internal change. -->

## Open Questions
<!-- LIVE tracker during planning — add freely, clear as answered. AT approval, only deliberately-deferred
     items remain, each with a one-line "why". Empty is a good outcome. -->
- …
