# Stages 10–11: backend plan and estimate

The plan's format, task shape and approval gate belong to `skunexus-backend-plan` (`<SKILL>/../skunexus-backend-plan/`, templates in its `assets/`). This file covers the orchestration around it:
- fixing the DAG (task dependency graph) shape and verified seams before fan-out;
- forked drafters;
- one correction round;
- scripted assembly and checks;
- an estimate the developer can post.

Contents: §1 Backend plan · §2 Estimate

## §1 Backend plan (stage 10)

**Inputs:** the approved PRD (a frozen Draft only with the developer's explicit OK, per `skunexus-backend-plan` Step 1; or the plan skill's inline spec), Notes for Design, the storyboard's drawing decisions, and the research and review files.

**Steps**
1. **Map** (optional but cheap). Copy `assets/briefs/map-brief.md` to `plan-parts/MAP-BRIEF.md` and run `sn-scout` mappers M1…Mn. Their job is retrieval, not design: exact, verified signatures with file:line, `patches/` before `vendor/`, and read-only sandbox probes where needed. Map files are persisted on purpose, unlike `skunexus-backend-plan` Step 2: drafters read them and they survive a pause.
2. **Design the DAG and the seams yourself** before any drafter starts, in `plan-parts/BRIEF.md` (from `assets/briefs/plan-brief.md`). The template ends with an "Orchestrator only" section: the spawn, correction, PAUSE and RESUME texts and the assembly commands. Keep that section for yourself and delete it from the copy drafters read.
   - **Wide and shallow.** Shared seams go in wave 1: event classes, locks, tables, permissions, base test vocabulary. Split long chains. Tasks with no edge between them react through events. A late re-wire on FFD-14 went from 7 waves to 4 and cost a full rework round.
   - **Every fixed seam carries its mechanism:** bus, dispatcher, lock, transaction hook, id type. Copy the mechanism from verified code.
     - Both FFD-14 and FFD-13 briefs specified Laravel `event()`. SN listeners register on SMST's `ListenerContainerInterface`, so those events would silently never fire.
     - The right call is `SMST\Commons\Design\Behavioral\EventBus\EventBusInterface->handle()` (e.g. `vendor/skunexus/rma/src/Domain/Definitions/Transitions/CloseTransitionHandler.php`).
   - **One owner** per seam, command and endpoint. A task calls only services from its `depends_on` tasks. Each write task binds its own permission and registers its own provider. Shared files (`routes/api.php`, `config/*`, provider lists, test traits) are append-only and re-read right before each edit.
   - **Check the brief against the house skills it invokes.** The FFD-13 brief asked for `describe()` groups, which `skunexus-behavior-testing` forbids.
3. **Fan out drafters** (A, B, …), each owning 2–5 tasks and writing `plan-parts/<Letter>-<slug>.md`. Spawn them as fresh `sn-worker` agents told to read PRD §4, §6 and Notes for Design first; don't fork (SKILL.md, "How to run every stage"). Each part ends with `#### Notes to orchestrator`:
   - seams that differ from the brief;
   - FE-surface lines;
   - open questions;
   - `decisions.md` candidates;
   - merge, split or re-wire suggestions.
   
   Drafters check each design fork against the R-ids it touches. A frozen stamp broke a requirement on FFD-13.
4. **One correction round, fed by two sources.** Budget for exactly one; drafters reading real code correct the brief (ids are uuid strings, new fields are custom fields, …).
   - As soon as every drafter returns, run the first `--check-only` assembly (step 5's command) and start the plan review (step 6) on the parts, in parallel with your own cross-part check. Merge all of them into one `## vN CORRECTIONS C1…` section in `plan-parts/BRIEF.md` (superseding, history visible).
   - **Mechanical items** (renamed test words, seams or classes; moved trailers): apply them yourself with one script over `plan-parts/[A-Z]-*.md`, then re-run the assembly with `--stale <old names>`.
   - **Design items:** SendMessage a drafter only if it went idle under ~5 minutes ago. For every other affected part, start one fresh `sn-worker` fixer with the RESUME text plus the Correction-round text (plan-brief, "Orchestrator only"); it applies the items that name its tasks to its part, in place, and reads only the parts and brief sections those items name (FFD-40's fixer read 102k chars of parts). Reworks take 1–3 min each, in parallel.
   - On FFD-35 three rounds through cold drafters (v2, addenda, v3) cost 17.1M of the drafting stage's 45.6M units. Most items were shared test-word names and one wrong mechanism; the test vocabulary registry and the name grep in the pre-fan-out check now catch those before fan-out.
5. **Assemble and check.** Before the first run without `--check-only`, create `backend-plan.md` from `skunexus-backend-plan`'s template with the body of its `## Tasks` section (the comment and the example T1/T2 blocks, up to the next `##` heading) replaced by one `<!-- TASKS -->` line; the script writes only into that marker. First `grep -l PAUSED plan-parts/[A-Z]-*.md`: resume those drafters (plan-brief RESUME); the script also refuses a part with a `PAUSED <DATE>` line. Write `plan-parts/deps.json` with `order` = every task id in the BRIEF's DAG table; the script finds an undrafted task only against `order`.
   ```bash
   python3 -I <SKILL>/scripts/assemble-plan-parts.py .ai/<TICKET> --check-only   # then without --check-only
   ```
   Add `deps` to `deps.json` if the parts' own `Depends on:` lines need overriding. The script checks:
   - missing or extra tasks (against `order` in deps.json; without it, only gaps in the task numbering);
   - parts still marked `PAUSED`;
   - cycles;
   - waves, peak width and the critical path in steps;
   - AC coverage: every PRD AC appears in a `Tests:` line or is marked out-of-suite (skipped for a `> Tests: none` plan);
   - the mechanism grep (Laravel events and the like);
   - stale names (the ones a revision renamed, passed with `--stale`).
   
   It refuses to write `backend-plan.md` while a check fails, so fix the parts first. After assembly, fill the plan's manifest and waves section from the script's report. After the plan has been assembled and edited (review changes, a re-pull), re-run the same checks on it with `--plan`.
   
   The script prints two critical-path figures: the longest dependency chain, and the wave-synchronous sum (largest task per wave, summed). The estimate's wall-clock uses the wave-synchronous sum.
   
   Then compile the FE-facing surface (every route with its permission) and the open questions by stakeholder from `NOTES-collected.md`. `decisions.md` takes only real forks.
6. **Plan review** (recommended): two code fact-checkers (`sn-worker`, one per half of the plan), a coverage and implementability auditor (`sn-scout`), and a simulated tech-lead review (`sn-judge`). Finding format: ID · location · type · as written · problem · evidence · suggested text; each file ends with a "Confirmed OK" list. Start it in step 4, on the parts at the first `--check-only` assembly, so its findings join the single correction round; after that round re-run only the assembly checks, not the reviewers. Each reviewer gets the parts (`plan-parts/[A-Z]-*.md`), the PRD and its checklist, and writes `plan-parts/review/<ID>-<role>.md`. **Gate:** the developer approves the plan per `skunexus-backend-plan`.

**Time:** say it up front. Drafters take 3–9 min each and reworks 1–3 min each. Assembly, checks and the estimate weren't timed on FFD-14; say so. "5 minutes" isn't realistic.

## §2 Estimate (stage 11)

**The developer sets the base.** Derive everything else proportionally and explain the rate. On FFD-14 the rate was 0.13–0.16 h per 1k plan characters, plus a small fixed cost for a new integration or a later phase. The developer then posts their own figures, which may differ: posted Jira hours are intentionally trimmed, so don't re-argue them.

Write `estimate.md` from `assets/estimate-template.md`:

| Rule | Why |
|---|---|
| Lead with a table **Part · Hours · Scope**, combination totals under it | The developer asked for exactly that |
| Keep the PO's estimate shape (e.g. with/without email + one priced option) | A panel-proposed five-part estimate was "too heavy" |
| Scope = 1–2 plain sentences per part saying what the client gets; no task ids, counts, file or mapping jargon | "Huge unreadable part list" and "too much assumed knowledge" were the developer's rejections |
| Figures = implementation incl. tests + review/rework. PR review, MySQL check, stage, QA, deploy and "FE, sized by the FE developer per page from the storyboard" go under "Not in these figures", **without hours** | Keeps the figure comparable across tickets |
| Separate agent DAG wall-clock from developer hours. Only implementation depends on orchestration; serial agents take ~3.7× the wall-clock | The developer asked which figures assume orchestrated subagents |
| Calibrate on a **measured** run, not a projection. One `sn-scout` agent reads the last comparable orchestrated ticket's git log, diff stats and commit times (TCM-150: 9.8 production lines per plan step, 1.69 code chars per plan char, ~2 min per critical-path step, review rework ~2 h). Re-measure after each new run | Projections missed by 2× |
| Mark it "Draft for the Jira estimate (not posted)" | Only the developer posts |
| When the developer rewrites the Scope column, adopt their words verbatim, then re-sync the storyboard's `PARTS` (`storyboard.md` §6) | The artifact and the estimate must say the same thing |

**With every estimate,** offer the storyboard if none exists (SKILL.md).

**Before posting:** offer stage 12 (re-pull and diff; it writes only dated files). The ticket may have moved since the PRD was approved.
