# Drafting the plan with subagents

Opt-in only (SKILL.md, Step 2): the developer asks to "orchestrate", "fan out" or work "in parallel", a calling skill hands the plan over with that ask, or `.ai/<TICKET>/run.md` says `plan-fan-out: on`. It replaces Steps 2–3 for that plan: the code maps are saved to `.ai/<TICKET>/plan-parts/`, subagents draft the tasks from one shared brief, and `scripts/check-plan.py` assembles and checks them into the same `backend-plan.md`. The plan's format, task shape and approval gate stay the skill's own: where this file seems to disagree with `SKILL.md` or `assets/backend-plan-template.md`, they win.

## The plan is a view of the contract

The contract is `prd.md` (rules: `R<n>` and lettered criteria `R<n>.<letters>`; decisions in §7), plus `workflows.md` when it exists (use cases: steps `s<n>.<m>`, each with a part). The plan is the system-side view of it, for the developer and the tech lead. Four rules follow; when `../skunexus-contract/references/model.md` exists, it is the full reference for all of them.

1. **The plan adds binding, never behaviour.** Its binding is mechanisms: which command, which event, synchronous or queued, which lock. What the feature does belongs to the contract.
2. **A question that changes behaviour is a contract question, never a task.** A drafter that finds the contract wrong or silent drafts the task as the contract reads today and raises it under its Notes; you file it (see "Contract questions"). On FFD-17 a refusal written into the queued decide job could never reach the user; the fix was a contract ruling (refuse before queueing), not a task tweak.
3. **Ids are the join keys.** Tasks cite criterion ids in `Satisfies:` and `Tests:` and never copy their text. Criterion letters run `a` … `z`, then `aa`. A retired id (`~~**R2.b**~~`, or "retired" right after it) needs no coverage and is never cited again; a foreign id carries its ticket key (`FFD-14 R31`).
4. **The plan has an owner and a gate:** the developer approves it (Step 6), and the tech lead reviews.

**Versioned contracts.** If the `prd.md` header has a `> Versions:` block, the plan is built from its newest version. Before the maps start, confirm `prd.md` (and `workflows.md`) still match the newest snapshot, `review/prd-v<N>-<DATE>.md` (`diff -q --strip-trailing-cr`). If they don't, the contract has edits that no version records: ask the developer to cut a version first, or to accept the risk explicitly. Then fill the template's `> Built from: contract v<N> (<DATE>)` line. A plan without that line has no base, which is fine for an unversioned contract. In a versioned contract, a Step 3 lettering or a Step 5 patch is an unversioned change: tell the developer that the contract needs a new version (`v<N>.<M>`, note `from backend-plan Step 5`) before the plan is approved.

**Parts.** When `workflows.md` exists, each task belongs to the part of the steps it serves. The brief's DAG table gives each task its Steps and its Part. A drafter adds `**Part:** Part <n>` to a task only when that cell names one part. Otherwise `check-plan.py` derives the part from the task's criteria, through the steps that cite them: a task that spans parts is `shared`, and a task with no step (a migration, a criterion under "Not exercised") is `unassigned`. With no `workflows.md`, no task carries a Part line.

## Contract questions

Either way, the affected task waits in the plan's Open Questions; it never encodes a guess.

- **Without `skunexus-contract`** (no `../skunexus-contract/references/model.md`): write no `feedback.md`. Raise the question with the developer under Step 5 in this thread; the answer is recorded where Step 5 records it.
- **With it installed:** file it in `.ai/<TICKET>/feedback.md` for the contract's rulings door, which decides; the contract then changes by a new version. One file per ticket, titled `# Feedback: <TICKET>`. Append; never edit an entry another source wrote. Take the next free `FB` number:

```
### FB3 · WRONG · BE plan draft · 2026-11-03
- **Cites:** R4.b
- **What:** R4.b's refusal sits inside the queued decide job, which never reaches the user.
- **Evidence:** research/R2-decisions.md:40; AutoDecideOrderHandler.php:43-45
- **Proposed:** (A) refuse before queueing, nothing created · (B) keep the job guard, add a notice
- **Status:** open
```

- **Type:** `WRONG` (the contract contradicts the code, the evidence or another rule) or `SILENCE` (it says nothing about a case the plan hit). A plan rarely needs `CHOICE` or `CHANGE`.
- **Source:** `BE plan draft` before the contract is approved, `BE plan` after.

## Per-ticket values

Resolve these once; the briefs list only their extra placeholders.

| Placeholder | Source |
|---|---|
| `<TICKET>`, `<DATE>` | The ticket key; today as YYYY-MM-DD |
| `<REPO>` | The git root (`git rev-parse --show-toplevel`) |
| `<SKILL>` | This skill's folder: the base directory Claude Code reports when the skill loads (normally `~/.claude/skills/skunexus-backend-plan`) |
| `<SANDBOX_CALL>` | A read-only script for the client's system named in the repo `CLAUDE.md` Commands section, if it exists on disk, else "none: skip data probes" |
| `<VERSION>` | In `plan-parts/BRIEF.md` revision headers, the brief's revision (v2, v3…) |

## Roles

| Role | Agent type | Brief |
|---|---|---|
| Code mapper M1…Mn | `sn-scout` | `assets/briefs/map-brief.md` → `plan-parts/MAP-BRIEF.md` |
| Plan architect (optional, step 2) | `sn-judge` | `assets/briefs/plan-brief.md` → `plan-parts/BRIEF.md`, `plan-parts/ORCH-NOTES.md` |
| Plan drafter A, B, … | `sn-worker` | `assets/briefs/plan-brief.md` → `plan-parts/BRIEF.md` |
| Correction fixer | `sn-worker` | the same brief, RESUME + Correction-round texts |
| Plan review: code fact-checker (×2) | `sn-worker` (the second may be `sn-scout`) | the parts, the PRD, its checklist (step 6) |
| Plan review: coverage and implementability auditor | `sn-scout` | same |
| Plan review: simulated tech lead | `sn-judge` | same, plus the tech lead's documented role |

If an `sn-*` type isn't installed, say so and use `general-purpose`, with `model: "sonnet"` for the `sn-scout` roles.

## Inputs

The agreed acceptance per Step 1: an Approved `prd.md` (a Draft only with the developer's explicit OK), its Notes for Design, `workflows.md` when present, and the ticket's `research/` and `review/` files. Storyboard drawing decisions and review findings reach the plan only through the contract: a decision the PRD doesn't record yet is a contract question, not an input.

## Steps

Say the durations up front: mappers take a few minutes each, drafters 3–9 min each, reworks 1–3 min each. Plan drafting is a burst of parallel agents: start it early in a usage window.

1. **Map.** Copy `assets/briefs/map-brief.md` to `plan-parts/MAP-BRIEF.md`, fill its Areas table (3–6 areas, one being tests), and run one `sn-scout` mapper per area, in parallel. Mapping is retrieval, not design: exact, verified signatures with file:line, `patches/` before `vendor/`, the mechanism behind every event, lock and transaction, and read-only sandbox probes where needed. The map files are kept, unlike Step 2's: drafters read them, and they survive a pause.
2. **Design the DAG and the seams yourself** before any drafter starts, in `plan-parts/BRIEF.md` (from `assets/briefs/plan-brief.md`). This is the default. When the developer asks, or the ticket spans several domains, you may give this step and the brief's pre-fan-out check to one `sn-judge` plan architect: it reads the maps and writes `BRIEF.md` plus `plan-parts/ORCH-NOTES.md` (the Orchestrator-only section and its open design questions), which keeps the raw maps out of this session; you verify every fixed seam's file:line before the spawn (FFD-35). The brief ends with an "Orchestrator only" section: the pre-fan-out check, the spawn, correction, PAUSE and RESUME texts, and the assembly commands. Keep that section for yourself and delete it from the copy drafters read.
   - **Wide and shallow.** Shared seams go in wave 1: event classes, locks, tables, permissions, base test vocabulary. Split long chains. Tasks with no edge between them react through events. A late re-wire on FFD-14 went from 7 waves to 4 and cost a full rework round.
   - **Every fixed seam carries its mechanism:** bus, dispatcher, lock, transaction hook, id type, copied from verified code. SN listeners register on SMST's `ListenerContainerInterface`, so an event sent with Laravel's `event()` silently never fires. Dispatch through `SMST\Commons\Design\Behavioral\EventBus\EventBusInterface->handle()` (e.g. `vendor/skunexus/rma/src/Domain/Definitions/Transitions/CloseTransitionHandler.php`); `check-plan.py` fails on the Laravel forms.
   - **One owner** per seam, command and endpoint. A task calls only services from its `depends_on` tasks. Each write task binds its own permission and registers its own provider. Shared files (`routes/api.php`, `config/*`, provider lists, test traits) are append-only and re-read right before each edit.
   - **A test vocabulary registry,** one owner per trait, filled before fan-out (the brief's table).
   - **With `workflows.md`:** fill each task's Steps and Part cells, so every live step is served by a task or is FE-only.
   - **Check the brief against the house skills it invokes.** The FFD-13 brief asked for `describe()` groups, which `skunexus-behavior-testing` forbids.
3. **Fan out drafters** (A, B, …), each owning 2–5 tasks and writing `plan-parts/<Letter>-<slug>.md`. Spawn them as fresh `sn-worker` agents, all in one message, with the brief's Spawn text. Each part ends with `#### Notes to orchestrator`: seams that differ from the brief, FE-surface lines, open questions and contract questions, `decisions.md` candidates, and merge, split or re-wire suggestions. Drafters check each design fork against the R-ids it touches: a frozen stamp broke a requirement on FFD-13.
4. **One correction round, fed by two sources.** Budget for exactly one: drafters reading real code correct the brief (ids are uuid strings, new fields are custom fields, …).
   - As soon as every drafter returns, run the first `--check-only` assembly (step 5) and start the plan review (step 6) on the parts, in parallel with your own cross-part check. Merge them into one `## v<VERSION> CORRECTIONS C1…` section appended to `plan-parts/BRIEF.md` (superseding, history visible).
   - **Mechanical items** (renamed test words, seams or classes; moved trailers): apply them yourself with one script over `plan-parts/[A-Z]-*.md`, then re-run the assembly with `--stale-name <old names>`.
   - **Design items:** SendMessage a drafter only if it went idle under ~5 minutes ago. For every other affected part, start one fresh `sn-worker` fixer with the RESUME text plus the Correction-round text. It applies only the items that name its tasks, and reads only the parts and brief sections those items name.
   - **Contract questions** from the Notes go to the plan's Open Questions now, and to `feedback.md` only with `skunexus-contract` installed (see "Contract questions"), not into the corrections.
5. **Assemble and check.** Create `backend-plan.md` from `assets/backend-plan-template.md`, with the body of its `## Tasks` section (the comment and the example T1/T2 blocks, up to the next `##` heading) replaced by one `<!-- TASKS -->` line; the script writes only into that marker. First `grep -l PAUSED plan-parts/[A-Z]-*.md` and resume those drafters. Write `plan-parts/deps.json` with `order` = every task id in the brief's DAG table; the script finds an undrafted task only against `order` (`deps` and `inserts` are optional overrides).
   ```bash
   python3 -I <SKILL>/scripts/check-plan.py .ai/<TICKET> --check-only   # then without --check-only
   python3 -I <SKILL>/scripts/check-plan.py .ai/<TICKET> --plan          # after any later edit to the plan
   ```
   It refuses to write `backend-plan.md` while a check fails. The checks: missing, extra or duplicate tasks; parts still marked `PAUSED`; unknown dependencies and cycles; waves, peak width and the critical path; criterion coverage (every live criterion in a `Tests:` trailer or marked `out-of-suite`, a requirement with no live criterion cited as `Rn`; skipped for `> Tests: none`); the forbidden-mechanism grep (`--forbid` adds patterns); stale names (`--stale-name`); `**Part:**` lines against `workflows.md` "Parts". With `--plan` it also runs the contract's stale check (`../skunexus-contract/scripts/check-contract.py --stale`) when the plan has a `> Built from:` line, and says so when that skill isn't installed.
   - Fill the plan's manifest and waves from the report. It prints two critical-path figures: the longest dependency chain, and the wave-synchronous sum (the largest task per wave, summed), which is the one to use for agent wall-clock.
   - From `plan-parts/NOTES-collected.md`, compile the Frontend-facing surface (every route with its permission) and the open questions by who answers them. `decisions.md` takes only real forks (SKILL.md, "The decisions log").
   - For an estimate, `--plan --sizes` prints plan characters per part (`| Part | Tasks | Characters | How |`, plus `shared`, `unassigned` and `total` rows). A task runs from its `### T<n> ` heading to the next `### T` or `## `.
6. **Plan review** (recommended): two code fact-checkers (one per half of the plan), a coverage and implementability auditor, and a simulated tech-lead review, labelled "Simulated <Name> review" and grounded in that person's documented role. Start it in step 4, on the parts, so its findings join the single correction round; after that round re-run only the checks, not the reviewers. Each reviewer gets the parts, the PRD and its checklist, and writes `plan-parts/review/<ID>-<role>.md`: one finding per entry as `ID · location · type · as written · problem · evidence · suggested text`, ending with a "Confirmed OK" list. Run the second fact-checker as `sn-scout` (another model) when you can: copies of one model share blind spots. Verify every finding that changes a design against the code before you apply it. Then Step 4 of the skill: the manifest, the developer's read, and the gate.

## Resume and pause

- **A `plan-parts/` folder with no `backend-plan.md`, or a plan still holding `<!-- TASKS -->`,** is a draft in progress: read `BRIEF.md` (revisions included) and the parts, then resume at the first unfinished step. Step 1's answers, the `> Tests:` decision included, are in `BRIEF.md`'s Plan header line: reuse them, don't ask again. A part with a `> ASSEMBLY PAUSED` line or a `<!-- STATE … -->` line goes to a fresh drafter with the RESUME text.
- **Pause:** send the brief's PAUSE text to every running agent; each saves its file within a minute.
- **Resume warm, restart cold.** SendMessage a correction only to an agent that is busy or went idle under ~5 minutes ago; otherwise start a fresh agent of the same type on its brief and its own file. After a usage-limit stop, wait for the reset and restart fresh: on FFD-35, six large agents resumed in the same minute and all hit the limit again within 31 seconds.

## Running the agents

With `skunexus-contract` installed, its `references/model.md` §9 is the full rule set; the short rules here and under "Resume and pause" are kept in step with it for when it isn't.

- One shared brief per fan-out; every agent gets its input paths, an output file it alone owns, and a reply cap (15 lines unless the brief says otherwise).
- Fresh agents, not forks: a fork re-reads the whole parent context on every turn.
- Wait for each agent's completion notice before reading its file: a file can be on disk before the agent has finished it.
- Text only: agents never read images, and work from code and text files.
- Read-only outside the ticket folder: no git, Jira or Confluence writes; client sandboxes are read-only, recording codes, counts and value shapes, never personal data.
