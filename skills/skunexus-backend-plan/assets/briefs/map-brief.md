<!-- Parallel drafting, step 1 (codebase mapping, before the drafting brief; see references/parallel-drafting.md). Copy to .ai/<TICKET>/plan-parts/MAP-BRIEF.md; fill the placeholders and the Areas table (3–6 areas, one per mapper).
     Spawn one `sn-scout` agent per Areas row, in parallel, with: "Read .ai/<TICKET>/plan-parts/MAP-BRIEF.md and map area M<n>." Mapping is retrieval, so it doesn't need the planning model. The map files are kept on purpose, unlike the skill's Step 2: drafters read them and they survive a pause.
     Extra placeholders: <PRD_STATUS> (e.g. "Approved 2026-10-27", or "contract v2 (2026-11-03)" when it has versions), <R_RANGE> (e.g. R1–R22), <RELATED_PLANS> (other tickets' plans touching the same code, or "none"). Standard placeholders: see references/parallel-drafting.md. -->
# <TICKET> backend plan: codebase mapping brief

Contract: `.ai/<TICKET>/prd.md` (**<PRD_STATUS>**; <R_RANGE>, acceptance bullets `Rn.x` in §6, Notes for Design at the end). When `.ai/<TICKET>/workflows.md` exists, it holds the use cases: steps `s<n>.<m>` with actor, trigger, state before → after, the ids they cite and their part. Before mapping, read only your Areas row's R-ids in §4, their §6 bullets and the Notes for Design topics that cite them: find each with `grep -n '\*\*R<n>' prd.md` and print that block with `sed -n` (a row marked `all` reads §4 whole). With `workflows.md`, also read the step rows that cite your R-ids (`grep -n 'R<n>\b' workflows.md`): they say which trigger reaches your seam and what the actor must see.
Repo: `<REPO>` (Laravel, PHP, `skunexus/core`). Read the repo `CLAUDE.md` first: extension hierarchy, domain layout, style guide, recorded decisions.
Related plans: <RELATED_PLANS>. Note every place where one of them touches the same file, class or method.
Research already done (cite it; don't redo it): `.ai/<TICKET>/research/R*.md`, `.ai/<TICKET>/review/*.md` (verified code facts with file:line, where present).

## Areas
| ID | Area | Requirements it serves | Questions to answer |
|---|---|---|---|
| M1 | <e.g. order pull, hold, auto-decide> | <R-ids; step ids when workflows.md exists> | <e.g. where does the pull commit; which hook fires after the order is stored> |
| M2 | <…> | <…> | <…> |
| M<n> | Tests: harness and terrain | all | <which syntax; does the harness exist; nearest test files> |

e.g. (FFD-13): M1 order pull, hold, D5, auto-decide · M2 product data, category lookup · M3 ACL, routes, custom field, guard, record storage · M4 tests · M5 FE seam.

## Your job
Map **your area only**. Mapping is retrieval, not design: report what exists, with **exact, verified signatures** (namespace, class, method, parameter and return types) and file:line. A wrong signature becomes a wrong task, so verify each one by reading the file, not from memory or docs.
- Check `patches/` (and `patches.json`) before trusting a `vendor/` file: a patched class does not behave like the upstream source.
- Where the PRD needs something that doesn't exist, say "not found", list what you searched, and name the nearest existing pattern to mirror.
- **Record the mechanism, not only the name.** For every event, dispatch, lock, transaction boundary, permission check and id type in your area, write down how it works at file:line: how listeners are registered and how events are dispatched, which lock API is used, which middleware wraps the command in a transaction, whether ids are uuid strings or ints. The drafting brief copies these into its fixed seams; on FFD-14 and FFD-13 a seam named without its mechanism led both plans to the wrong event bus.
- If an IDE navigation MCP is available (ToolSearch), use it; otherwise grep.
- Optional, read-only sandbox probes: `<SANDBOX_CALL>` (from the repo root). Read its tool folder and safety note first. Only read/list/load functions; never call anything that creates, updates, deletes or assigns.

Write your findings to `.ai/<TICKET>/plan-parts/map-M<n>.md` with these sections:
1. **Seams.** The classes and methods your area's requirements hook into: exact signature, file:line, what each does today, and its mechanism (see above).
2. **Patterns to mirror.** One existing client or core file per kind of change (command + handler, plugin, provider, migration, setting, custom field, route, GraphQL field, listener, test), with the provider list it is registered in.
3. **Constraints.** Invariants, transactions, ACL, ordering, what throws, and where a related plan touches the same file.
4. **Gaps and options.** What the PRD needs that has no seam, with 1–3 options and a recommendation. Plan-relevant only. Where the code contradicts what the contract asks (for example, a check inside a queued job can never reach the user), say so with file:line: that is a contract question, not a design choice.
5. **Test terrain.** The nearest existing test file, the `tests/Behavior/` vocabulary traits and builders to reuse, how the subject is driven (bus command, REST endpoint, GraphQL), and whether the harness exists (`bus()` / `given()` in `tests/TestCase.php`, global `given()` in `tests/Pest.php`). A missing harness becomes a `T0` task.

Return to the orchestrator in ≤25 lines: your recommendation per gap, every verified mechanism, and any finding that changes the PRD's assumptions (cite the R-ids).

## Hard rules
- Read-only everywhere except your own `map-M<n>.md`. No git writes, no Jira or Confluence writes, no local DB writes.
- Sandbox: record codes, counts and value shapes, never names, emails or addresses. Delete raw dumps when done.
- Never Read PNG or JPEG files (an image in your context is re-sent on every later call; work from text).
