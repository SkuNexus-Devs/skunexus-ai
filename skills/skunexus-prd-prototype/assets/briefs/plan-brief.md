<!-- Stage: backend plan, step 2 (drafting brief, after the maps land). Copy to .ai/<TICKET>/plan-parts/BRIEF.md; fill every <…> from verified code and plan-parts/map-M*.md, then start one drafter per letter in the DAG table (see Spawn).
     Remove the last section ("Orchestrator only") from the copy and keep it for yourself. Before fan-out, run its pre-fan-out check.
     Extra placeholders: <PRD_STATUS>, <R_RANGE>, <N_AC> (acceptance bullet count), <DOMAIN_HOME>, <PROVIDER_HOME>, <PROVIDER_LIST>, <RELATED_PLANS> (other tickets' plans touching the same code, or "none"), <L> (drafter letter), <SLUG>. Standard placeholders: see SKILL.md. -->
# <TICKET> backend plan: shared drafting brief

Contract: `.ai/<TICKET>/prd.md` (**<PRD_STATUS>**; <R_RANGE>, acceptance bullets `Rn.x` in §6, Notes for Design).
Plan format: the `skunexus-backend-plan` skill, template `<SKILL>/../skunexus-backend-plan/assets/backend-plan-template.md`. This brief adds the orchestration rules only; where it seems to disagree with that template or with `skunexus-behavior-testing`, the skill wins: say so in your Notes.

Sources of truth, in order:
1. Real code: `<REPO>` plus `vendor/skunexus/*` and `vendor/smst/*`. Check `patches/` first, because a patched vendor class does not behave like its upstream source.
2. PRD §4 Requirements and §6 Acceptance Criteria.
3. The maps `plan-parts/map-M*.md`: <M1 = area, M2 = area, …>.
4. PRD Notes for Design, then `research/` and `review/`.
5. SN platform docs in `.ai/skunexus-docs/docs/`: the doc and section in your tasks' Docs column (start at `AI_ENTRY.md`; `glossary.md` for platform terms). Code wins on signatures.

Repo rules: `<REPO>/CLAUDE.md` (style guide, extension hierarchy, domain layout) and the repo's auto-memory notes on design feedback and plan DAG shape, if any.
Plan header: `> Tests: <behavior | none — why>`, decided with the developer per skunexus-backend-plan Step 1. For behavior: the repo's test runner, vocabulary in `tests/Behavior/`, layer map per `skunexus-behavior-testing`. <Harness: present (no T0) | missing (add T0 — test harness; every trailer-bearing task depends on `T0 (tests only)`)>.

## Output (each drafter)
Write ONLY your part file `.ai/<TICKET>/plan-parts/<L>-<SLUG>.md`, holding your `### Tn — title` task bodies in the template format:
- the header lines `**Status:** not_started`, `**Depends on:**` (ids from the DAG table; annotate a partial edge as `T19 (tests only)`), `**Satisfies:**`;
- a flat list of `- [ ]` atomic, verb-first steps naming exact paths, classes and methods inline, plus the existing file to mirror;
- optional one-line trailers `**Out of scope:**`, `**Sanity-check now:**`, `**Tests:**`.

| Rule | Why |
|---|---|
| `**Tests:** <test file path> — R3.a, R3.b …` cites the acceptance bullet ids assigned to your task, never a bare `Rn` and never the bullet text | One happy-path test must not mark a requirement's edge and error bullets as proved; the assembly script checks coverage per bullet |
| A bullet proved only outside the suite goes in `**Sanity-check now:**` as `out-of-suite: R3.c — <why>` (MySQL races, live carrier or connector sandbox, FE-only, DNS) | The coverage check counts it as covered, not missing |
| No prose walls, no "see Tn", no placeholders; literal code only for contracts (signatures, columns, setting names) | An implementation agent runs one task alone |
| Every migration task ends with the step that regenerates the test schema, if the repo has one (FFD: `php artisan dump:schema-for-testing --env=testing`) | Tests run on an SQLite dump |
| Each task registers its **own** provider class and names the provider list it appends to | Parallel agents never edit the same provider |
| Shared files are append-only, re-read right before each edit: <`routes/api.php`, `config/app.php`, `config/skunexus.php`, <PROVIDER_LIST>, the `*FieldsProvider` `SETTINGS_FIELDS`, `tests/Behavior/*Trait.php`> | Several agents write them in the same wave |
| Never change an existing method's signature in a shared trait or service; add a new public builder or method | Other tasks already call it |
| Test files follow `skunexus-behavior-testing`: flat `test()` only (no `describe()` or `it()`; two groups means two files), one file per behavior surface (command, endpoint, pure algorithm), lowercase falsifiable test names, new vocabulary as `{Domain}ScenarioTrait` / `{Domain}AssertionsTrait` in `tests/Behavior/`, and a test is never its own task | The FFD-13 brief asked for `describe()` groups, which that skill forbids, and the assembler had to split files |
| Check each design fork against every R-id it touches before choosing | FFD-13: a drafter froze a value at first import, which broke a later requirement |
| Dispatch and listen only through the mechanisms in "Mechanisms" below | See the event-bus row |

After the task bodies, add `#### Notes to orchestrator` covering:
1. seam names or signatures you NEED that differ from "Fixed seams" (with the file:line that proves it);
2. FE-facing surface lines: route or GraphQL field · method · permission;
3. open questions and `decisions.md` candidates (a real fork, non-obvious, someone would ask "why?");
4. merge, split or re-wire suggestions, and any bullet you think belongs to another task;
5. collision points with <RELATED_PLANS> in your files.

Reply in ≤15 lines. Do NOT edit any other file. Do NOT write code. Read-only on everything else; no git, Jira or DB writes.

## Global conventions
| Concern | Convention |
|---|---|
| Domain home | `<DOMAIN_HOME>` (`Commands/<Name>/<Name>Command.php` + `Handler.php`, `Services/`, `Repositories/`, `ValueObjects/`, `Events/`, `Listeners/`, `Plugins/`) |
| Providers | `<PROVIDER_HOME>`, each listed in `<PROVIDER_LIST>` |
| HTTP | Controllers `app/Http/Controllers/API/<Area>/`, FormRequests `app/Http/Requests/<Area>/`, routes `routes/api.php` |
| Ids | <uuid `string` everywhere | …> (verified: <file:line>) |
| Codes and keys | <e.g. compared case-insensitively, stored lower-cased> |
| Style | `<REPO>/CLAUDE.md` style guide (on FFD: `match`, early returns, promoted private constructor deps, `public const`, no "what" comments, collections own their logic, validate in `create()`) |

## Mechanisms (verified before fan-out; every task uses exactly these)
| Concern | Mechanism | Verified at |
|---|---|---|
| Events | Events implement `SMST\Commons\Design\Behavioral\EventBus\EventInterface`. Dispatch by injecting `SMST\Commons\Design\Behavioral\EventBus\EventBusInterface` and calling `->handle(new XEvent(…))`. Listeners go in the task's own `SMST\Commons\Laravel\ServiceProviders\AbstractEventListenerProvider::EVENT_LISTENERS` | `vendor/skunexus/rma/src/Domain/Definitions/Transitions/CloseTransitionHandler.php:23` (dispatch), `vendor/smst/commons/src/Laravel/ServiceProviders/AbstractEventListenerProvider.php:24-31` (registration) |
| Command bus | `SMST\Commons\Design\Behavioral\Command\CommandBusInterface::handle()`; nested commands run inside the outer command | <file:line> |
| Transactions | <e.g. core `SkuNexus\Core\Services\CommandBus\TransactionMiddleware` wraps each bus command; a synchronous listener commits with it; "after commit" = <mechanism>> | <file:line> |
| Locks | <e.g. order-row `lockForUpdate` in one named service> | <file:line> |
| Permissions | <how a command is bound to an ACL key; where the check runs> | <file:line> |
| New fields | <custom field vs column, and how it is read> | <file:line> |

Never use Laravel's `event()`, `Event::dispatch` or `Illuminate\Contracts\Events\Dispatcher`: SN listeners register on SMST's `ListenerContainerInterface`, so Laravel-dispatched events never reach them and the listener silently never runs. Both the FFD-14 and FFD-13 briefs made this mistake. The assembly script greps for these patterns and fails.

## Fixed seams (owner task → exact names; use exactly these)
One entry per seam that two or more tasks use. Copy each name, signature and mechanism from verified code or a map's §1; cite the source.
- **T<n> — <seam purpose>**
  - `<class FQCN>::<method>(<typed params>): <return>` — <what it does> — mechanism: <bus | EventBusInterface event | lock | transaction hook> — source: <file:line | map-M<n> §1>
  - Migration `<path>` creates `<table>`: <column: type, nullability, index/FK> …
  - Event `<class FQCN>(<typed promoted props>)`, dispatched by T<n> via `EventBusInterface->handle()`, listened to by T<n>, T<n>
  - Provider `<class FQCN>` appended to `<PROVIDER_LIST>`
  - Test vocabulary `tests/Behavior/<Domain>ScenarioTrait.php::<builder>(…)`

e.g. (FFD-14, after corrections): "**T1** — `RmaExited(string $rmaId, string $orderId, string $state)` fires on every exit including auto-complete; T6 and T14 listen."

## Test vocabulary registry (filled before fan-out; one word per purpose)
| Trait file | Owner task | Words (exact signatures) | Used by |
|---|---|---|---|
| `tests/Behavior/<Domain>ScenarioTrait.php` | T<n> | `<builder>(<typed params>): <return>`, … | T<n>, T<n> |

Only the owner task creates the file or adds its first words. A task that needs a word not listed here names it under its Notes as `proposed: <signature>`, uses that name, and the orchestrator settles it in the correction round. Grep this table and `tests/Behavior/` before proposing a word. On FFD-35 two correction rounds went on unowned and duplicate test words (`assertPurchaseOrderShipsTo` vs `assertShipsTo`, `assertOrderIsInState` vs `assertOrderStateIs`).

## DAG (ownership) and acceptance assignment
| ID | Task | depends_on | Satisfies | Drafter | Test file(s) | Bullets cited | Docs |
|---|---|---|---|---|---|---|---|
| T1 | <seam task> | none | <Rn, Rn (part)> | A | <tests/Feature/…Test.php> | <Rn.a, Rn.b; out-of-suite: Rn.c> | <`map-M2` §1; `domains/<cluster>/<domain>/spec.md` §Dependencies> |
| T2 | <…> | none | <…> | B | <…> | <…> | <…> |
| T<n> | <…> | T1, T2 | <…> | C | <…> | <…> | <…> |

Waves: **W1** = <…> (peak <n>) · **W2** = <…> · … Critical path: <largest task per wave, summed>.
Every one of the <N_AC> bullets in PRD §6 is assigned, cited or marked out-of-suite above. Drafters move a bullet only through "Notes to orchestrator".
Docs: the map sections (`map-M<n>` §) and the SN docs (`.ai/skunexus-docs/docs/`: domain specs, workflow docs, glossary entries) each task needs, chosen by the orchestrator. Drafters read those, not every map or the whole tree; on FFD-40 each drafter read 23–45k chars of maps and 14–32k of the PRD.

## Wide-DAG rules
| Rule | Why (FFD-14) |
|---|---|
| Wide and shallow: shared seams (event classes, locks, tables, base test vocabulary, permission plumbing) sit in wave 1 | A late re-wire went from 7 waves to 4 and cost a full rework round |
| Split long chains: a task whose output only one downstream task needs splits into storage + behaviour | Three splits cut the critical path |
| Tasks with no edge between them react through events defined in a wave-1 task, never by direct calls | Label voiding, auto labels and close holds all became listeners |
| No sink tasks: each write task binds its own permission and carries its own permission-denied test case | A wave-1 permission task replaced a final "bind everything" task |
| A task calls only services from its `depends_on` tasks | Implementation agents read only their dependencies' real code |
| One owner per seam, command and endpoint | Every cross-part conflict surfaced as duplicated commands or an endpoint nobody owned |

## Known constraints
- <transactions: e.g. the import is one DB transaction, so never queue a listener that must commit with it>
- <state machine: which transitions exist and which throw>
- <guards: e.g. the custom-field guard drops system writes unless they go through `emulateAlways`>
- <collisions with <RELATED_PLANS>: file → what they change; keep this ticket's edits additive>

## Revisions
Append revision sections here; never edit the text above, so drafters see what changed and why. A later section supersedes earlier text.
- `## v<VERSION> RE-WIRE (<DATE>, supersedes the DAG table above)`: the new DAG table, waves and moved seams.
- `## v<VERSION> CORRECTIONS (<DATE>; supersede anything above)`: numbered `C1 …`, one line each, naming the affected tasks. Corrections usually come from drafters reading real code (FFD-14: ids were uuid strings, not ints; new fields were custom fields, not columns; a marker was renamed).
- End every revision with the final wiring line (`T1 none · T5 T1,T3 · …`) and the waves.

## Orchestrator only (remove from the copy)
**Pre-fan-out check.** Every fixed seam has a verified mechanism with file:line, and the Events row is copied from code, not memory. Every §6 bullet appears in the DAG table (count = <N_AC>). The test rules match `skunexus-behavior-testing` and the step format matches the backend-plan template. Then grep every constant, method and class that the Mechanisms and Fixed-seams tables name in the file each one cites; a name missing from its cited file fails the check (on FFD-35 the DI row said `BINDINGS`, taken from the repo `CLAUDE.md`, while the cited `AbstractAdditionalInterfacesProvider` has only `SINGLETONS` and `INTERFACES`; seven drafters had to rework). Every test trait the DAG needs has a registry row with one owner, and every task has a Docs entry. Then tell the developer the realistic duration: drafters took 3–9 min each on FFD-14, a correction round 1–3 min, then assembly, checks and the estimate.

**Spawn** (one fresh `sn-worker` per drafter letter, all in one message; don't fork, see SKILL.md) with this in front of the text below: "In `.ai/<TICKET>/prd.md`, read only your tasks' R-ids (DAG `Satisfies`), their §6 bullets and the Notes for Design topics that cite them: find each with `grep -n '\*\*R<n>' prd.md` and print that block with `sed -n`. Open another R-id only when a design fork touches it. Read only the map sections and SN docs in your tasks' Docs column."
> You are drafter <L>. Read `.ai/<TICKET>/plan-parts/BRIEF.md` (all of it, including any revision sections) and write `.ai/<TICKET>/plan-parts/<L>-<SLUG>.md` with tasks <Tn, Tn>. Follow the Output rules, end with `#### Notes to orchestrator`, and reply in ≤15 lines.

**Correction round** (one round, per `references/plan-estimate.md` step 4: append the `## v<VERSION> CORRECTIONS` section and apply the mechanical items yourself by script first. Send this text only to drafters that went idle under ~5 minutes ago; for every other affected part, start a fresh `sn-worker` fixer with the RESUME text below followed by this text):
> CORRECTIONS v<VERSION>: read the `## v<VERSION> CORRECTIONS` section now appended to `.ai/<TICKET>/plan-parts/BRIEF.md`. Apply every item that touches your tasks to `plan-parts/<L>-<SLUG>.md` in place, keeping task ids. In `#### Notes to orchestrator`, add "Applied v<VERSION>: C…" and any new conflict. Reply in ≤10 lines: what changed, and anything you could not apply and why.

**PAUSE** (SendMessage to every running agent, start a 60 s timer, and write or update the ticket's memory note at the same time):
> PAUSE. You have at most 1 minute. Stop reading and save what you have to your file now. Put this line right under its title (or as its first line): `> ASSEMBLY PAUSED <DATE> <HH:MM>: done <ids>; partial <ids>; next: <one line>`. Reply in ≤5 lines with the same status. Start nothing new.

**RESUME** (SendMessage to the same agent only if it went idle under ~5 minutes ago; otherwise, or in a new session, start a fresh `sn-worker` with the Spawn text plus this text):
> RESUME. Re-read `.ai/<TICKET>/plan-parts/BRIEF.md`, including revision sections appended since the pause, and your own file. Delete the `> ASSEMBLY PAUSED` line, if any, and continue from its "next" item or your `<!-- STATE … -->` line. Reply in ≤15 lines when done.

**Assembly.** Write `plan-parts/deps.json` with `order` = every task id in the DAG table (the script finds an undrafted task only against it; `deps` and `inserts` are optional), then:
`python3 -I <SKILL>/scripts/assemble-plan-parts.py .ai/<TICKET> --check-only --stale <names a revision renamed>` (drop `--stale` when nothing was renamed)
Fix the parts (or send a correction round) until it passes. Then create `backend-plan.md` from the skunexus-backend-plan template, with one line `<!-- TASKS -->` where the task list goes, and run the script again without `--check-only`: it replaces that line with the tasks and writes `plan-parts/NOTES-collected.md`. Fill the Task Manifest and waves from its report; the plan is done when no `<!-- TASKS -->` is left. After later edits to the plan, re-check it with `--plan`. From the notes, compile the Frontend-facing surface (every route with its permission) and the open questions grouped by who answers them (tech lead, PO/client, FE developer, verify in implementation). `decisions.md` takes only real forks.
