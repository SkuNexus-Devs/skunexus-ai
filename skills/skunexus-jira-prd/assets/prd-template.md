# PRD: <TICKET-KEY> — <Title>

> Status: Draft  <!-- flip to "Approved" ONLY after the developer explicitly accepts -->
> Source: Jira <TICKET-KEY>

## 1. Summary
<!-- 1–2 sentences: what is changing and why. Describe the change and its purpose — not "for whom." -->

## 2. Problem / Why
<!-- The underlying problem or motivation. Why this work matters / why now. This grounds the goals below. -->

## 3. Goals & Non-Goals
**Goals**
- <!-- desired outcomes, stated as results not tasks -->

**Non-Goals**
- <!-- explicitly out of scope, so the design skill and reviewers know the boundary -->

## 4. Requirements
<!-- Numbered, testable, unambiguous. Each is something the solution MUST satisfy. The downstream design skill cites these IDs, so keep them stable and atomic. -->
- **R1** …
- **R2** …

## 5. Scope of Changes
<!-- Product-scope only: which areas / components / surfaces are affected, stated as outcomes.
     NOT implementation steps — the downstream design skill breaks these into tasks. -->
- …

## 6. Acceptance Criteria
<!-- BDD-flavored, readable bullets (not strict Gherkin). Each ties back to a requirement — cite the Rn.
     Cover the main behaviors AND the important edge/error paths surfaced during the interview.
     These bullets flow downstream into test names: the backend plan cites them by ID in its per-task
     `Tests:` trailers and the implement skill names each test from the bullet's current wording — so keep
     each one falsifiable and tied to its Rn; this file stays the only copy of the sentence. -->
- Given …, when …, then …  (R1)

## 7. Open Questions
<!-- DURING the interview this is the LIVE tracker of unresolved ambiguities — add to it freely and clear items as they're answered.
     AT approval it should hold only items deliberately deferred, each with a one-line "why". Empty is a good outcome. -->
- …

<!-- ─────────────────────────────────────────────────────────────
     Notes for Design (OPTIONAL footer): include this section ONLY if the developer
     shared technical/approach ideas or scope-affecting constraints worth handing to the
     downstream design skill. These are parked ideas, NOT decisions. Omit the whole
     section if there are none — don't leave an empty heading.
     ───────────────────────────────────────────────────────────── -->
