<!-- FE plan. Copy to .ai/<TICKET>/FE-PLAN-BRIEF.md, fill it, and give one fresh `sn-worker` agent:
"Read <path>/FE-PLAN-BRIEF.md and do it." Extra placeholders: <FE_SOURCES> (the client repo's FE folders and installed
@skunexus packages; any core FE checkout the developer named), <FE_BASIS> (the FE developer's posted figures the developer
pointed to), <PRD_SNAPSHOT>, <WORKFLOWS_SNAPSHOT>. Standard placeholders: see SKILL.md. -->

# FE plan brief: <TICKET>

You draft `<REPO>/.ai/<TICKET>/frontend-plan.md` from `<SKILL>/assets/frontend-plan-template.md`: each storyboard page bound to the FE work it needs, for the FE developer to confirm or replace. The rules are `<SKILL>/references/frontend-plan.md`; this brief is what you need from them.

## Read
1. The storyboard `prototype/<SLUG>-storyboard.html`: its `SC` (pages by step id, captions, chips) and `IX` (before/after rows). Read the data region with `grep -n`/`sed -n`; never open `prototype/screens/`.
2. The contract snapshot it was built from: `<PRD_SNAPSHOT>` and `<WORKFLOWS_SNAPSHOT>`.
3. `backend-plan.md`: "Frontend-facing surface (intended)" and the tasks it names.
4. FE code, read-only: <FE_SOURCES>. Cite file:line in the version the client installs.
5. Hours basis: <FE_BASIS>.

## Write
- One section per page, keyed by step id; every live step whose trigger is `user` has one. Items `FE<n>`, each with files, its step's Part and an hours range (implementation only).
- The FE hours per part table, live parts plus `shared` and `total`, summing correctly.
- The header's `Built from` line: the storyboard's `BUILT_FROM`, then `prototype/artifact.md@` and `backend-plan.md@` with `tr -d '\r' < <file> | sha256sum | cut -c1-8` taken when you start.
- Keep a `<!-- STATE <HH:MM>: done …; next … -->` line under the title while you work; delete it when done.

## Boundaries
- Binding only. If a page needs behaviour the contract doesn't settle, or an API the plan doesn't offer, append a `feedback.md` entry (re-read the file and take the next free `FB` id right before appending; never edit an entry):
  ```
  ### FB<n> · <WRONG|CHOICE|SILENCE> · FE plan · <DATE>
  - **Cites:** <step id, contract ids>
  - **What:** <the problem>
  - **Evidence:** <file:line>
  - **Proposed:** (A) … · (B) …
  - **Status:** open
  ```
  A technical choice that changes no behaviour goes under "Questions for the FE developer".
- Write only `frontend-plan.md` and appends to `feedback.md`. No local app or DB writes; no browser.

## Reply (≤15 lines)
Sections and items written; FE hours per part and total; the riskiest item; questions for the FE developer (count); `FB` ids filed, one line each.
