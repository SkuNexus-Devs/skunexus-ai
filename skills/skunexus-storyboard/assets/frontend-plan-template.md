<!-- FE plan. Copy to .ai/<TICKET>/frontend-plan.md; fill from the storyboard, the contract snapshot, backend-plan.md and the FE code.
     Extra placeholders: <N>, <HASH_ARTIFACT>, <HASH_PLAN>, <PLAN_STATUS>. Standard placeholders: see SKILL.md. Delete the guidance comments once filled. -->
# Frontend Plan: <TICKET> — <Title>

> Status: Draft for the FE developer. The approach and the hours are theirs to confirm or replace (G4).
> Built from: contract v<N> (<DATE>) · prototype/artifact.md@<HASH_ARTIFACT> · backend-plan.md@<HASH_PLAN>
> Plan: backend-plan.md (<PLAN_STATUS>). Visual spec: the storyboard (`prototype/<SLUG>-storyboard.html`); each section below is one of its pages.
> Paths: <short aliases for the FE folders cited below, e.g. `OD/` = the client's order-details overlay; `@skunexus/<pkg>` = the installed version, from the client's package.json>

## The API the FE builds against
| What | Shape | Errors · permission | Source |
|---|---|---|---|
| <read: a GraphQL field or grid> | <fields and arguments> | <error shape; permission> | backend-plan T<n> |
| <write: a REST route> | <method, body → response> | <403 / 422 / …> | backend-plan T<n> |
<!-- Only what backend-plan.md's "Frontend-facing surface" and tasks give. A call the pages need that the plan lacks is a feedback.md entry, not a row. -->

## Approach
<!-- The one or two structural choices, with the alternative and why (e.g. a client page on the stock grid package vs a custom page; a wrapper outside the form state vs form fields). Cite installed code file:line. -->

## Pages

### s<n>.<m> · <page>: <state>
- **Cites:** <contract ids the step cites>
- **Components:** <what renders: stock component reused, overlay, new component; where SN places it>
- **API calls:** <reads and writes from the table above, and when>
- **Validation and messages:** <client-side checks and their text as the contract words it; the BE refusal as backstop>
- **FE items:**
  - **FE1** <what> · files: <`path`, **`new/path`**> · Part <n> · <low>–<high> h
<!-- One section per storyboard page, in scenario order. Every live step whose trigger is `user` has one. Cite an item defined earlier as "FE1 (above)". -->

### No FE work
- s<n>.<m>: <why: e.g. a system step whose email is rendered by the BE>

### Shared
- **FE<k>** Lint, format, build and a local walk-through against the BE branch · shared · <low>–<high> h

## FE hours per part
| Part | FE items | FE hours |
|---|---|---|
| Part 1 | FE1, FE2 | <low>–<high> |
| Part 2 | FE3 | <low>–<high> |
| shared | FE<k> | <low>–<high> |
| **total** | | **<low>–<high>** |
<!-- Live parts only, names as in workflows.md. The estimate copies this table and asks the developer how to split `shared`. -->

**Riskiest items:** <FE<n>: why the high end exists, with the evidence (file:line)>

**Basis:** <the FE developer's own figures for comparable pages (ticket, comment), and how this work compares>

**Not included** (implementation only): code review; stage verification with BE and QA; <rebases onto other tickets' FE branches>.

## Questions for the FE developer
1. <FE<n>: a technical choice, the options, the recommended one>
