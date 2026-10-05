---
name: skunexus-backend-implement
description: >-
  Execute a backend implementation plan (.ai/<TICKET>/backend-plan.md, produced by skunexus-backend-plan) as
  working, developer-reviewed code — one task at a time or as a full multi-agent orchestration — keeping the
  plan's checkboxes and statuses, the PRD, and the decisions log truthful as code lands. Use it whenever the
  developer wants to implement, build, or execute planned backend work: "implement the plan for LO-58",
  "what should I pick up next", "let's do T3", "orchestrate the rest of the ticket", "continue the
  implementation" (resume works from disk, even in a fresh conversation). ALSO use it when there is no plan
  at all — for small, well-described changes ("just add X to endpoint Y, skip the ceremony") it implements
  directly and escalates to planning only if the change proves bigger than described — and when the
  developer comes back with changes to already-implemented work ("we need to change how X works", QA
  findings, relayed PR-review comments) to apply them to code and artifacts without re-litigating recorded
  decisions. Do NOT trigger for: producing the plan itself (skunexus-backend-plan), requirements interviews
  (skunexus-jira-prd), frontend implementation, or writing PR descriptions/testing steps
  (skunexus-backend-pr).
---

# Backend Plan → Working Code

Turn the approved task DAG in `.ai/<TICKET>/backend-plan.md` into working code on the ticket branch,
**explicitly reviewed by the developer** (who also runs environment verification themselves) — with the
ticket's artifacts still telling the truth when you're done. This is the execution step of the engineering
AI workflow: it follows `skunexus-jira-prd` (the contract) and `skunexus-backend-plan` (the task DAG), and
precedes the PR-description / FE-handoff / testing steps.

## Inputs — three doors

Everything lives under `.ai/<TICKET>/` in the current working repository:

```
.ai/<TICKET>/
├── prd.md            # the contract (may be absent — then the plan's Goal & Acceptance block is the contract)
├── investigation.md  # bug-route diagnosis (skunexus-bug-hunt): root cause, proposed fix, acceptance (may be absent)
├── backend-plan.md   # the task DAG — this skill checks its boxes, flips its statuses, amends its steps
└── decisions.md      # shared ADR-style log — this skill appends/supersedes as implementation decides things
```

Which door you're in is determined by what exists and what the developer asked for:

- **Door A — a plan exists**: implement it, task-by-task or orchestrated. The normal case.
- **Door B — no plan, a change described in the prompt**: implement directly without ceremony, or route to
  planning first — the developer chooses. On the bug route, the "description" may be an approved
  `.ai/<TICKET>/investigation.md` from `skunexus-bug-hunt` — a settled diagnosis to build on, not re-derive.
- **Door C — changes requested on implemented work**: the developer comes back (possibly in a fresh
  conversation) describing what needs to change — their own conclusions, QA findings, or relayed review
  feedback.

## Operating principles (read before doing anything)

These are the soul of the skill. The mechanics below serve them.

- **Tasks run against real code, not the plan's memory of it.** A task never starts until everything in its
  `depends_on` is `finished`. Before implementing, read the code those dependencies actually produced — the
  plan entry is the contract for *scope and approach*; the live code is the source of truth for *exact
  signatures*. The plan was grounded at planning time, but code moves; a signature copied from plan text
  instead of the file is how subtle breakage gets in. When a task touches platform machinery you don't
  already understand, build the mental model first (the `skunexus-docs-c7` skill), then read the code.

- **The tracker must stay truthful — and what "update" means depends on tense.** Check each `- [ ]` as the
  step lands (not in a batch at the end); a task's `Status` is derived from its boxes
  (`not_started`/`started`/`finished`). When reality diverges from what a step says, split by tense:
  - a **finished** task's entry is *history* — amend it only for **material** deviations (behavior, seam,
    scope) with a dated amendment note under the task; let micro-detail drift, the code is the signature
    truth anyway;
  - a **pending** task's entry is *instructions someone will execute* — if a change moves a seam or contract
    it references, updating it is **mandatory**. Walk the ripple through `depends_on` edges in both
    directions, exactly like the planning skill's review sweep, until the graph is consistent again.
  A checked box that lies, and a pending step that describes a dead design, are the two failure modes this
  principle exists to prevent. Updating the plan for a plain code fix that changes nothing a step asserts is
  churn — don't.

- **Feedback lands at its altitude.** Whether it arrives during task review, at the end-of-run review, or
  as later follow-up changes, triage every piece of feedback to its destination *before* editing anything:

  | The feedback turns out to be… | It lands in… |
  |---|---|
  | A requirement change | `prd.md` — patch the `Rn`, one-line changelog note under the status (or edit the plan's inline Goal & Acceptance) |
  | …and that requirement's bullets (`Rn.x` / `An`) are cited by a `Tests:` trailer | The tests too — every landed trailer citing a moved bullet is re-discharged (a bare one stays bare unless the developer now wants it) against the new wording in the same change (name re-read from the contract, assertions re-checked, the landed line rewritten). A test still carrying the old sentence is a lie the suite publishes on every run |
  | A technical re-decision with a real fork | `decisions.md` — a dated **superseding** entry, provenance-tagged (e.g. "post-review change, 2026-07-20"); never edit the old entry |
  | Code should do something different from what a step says | The plan — amend the step / dated amendment note (tense rule above) |
  | A plain code fix within what the step already says | Code only — no artifact edit |

  The artifacts mirror *what was built and why*, not the conversation history.

- **One writer per artifact.** Subagents implement code; they never touch anything under `.ai/` and never
  commit. They return structured reports; the orchestrating thread is the sole writer of
  plan/PRD/decisions and the sole committer. This prevents concurrent-write corruption and keeps the
  judgment calls — what counts as a deviation, what earns a decision entry — in one place.

- **The developer runs environment verification, not you.** Do NOT run migrations, tinker, or hit endpoints
  to verify a task — the developer does that on their own. Never claim a task is "verified"; claim only what
  you can stand behind statically (code reads against real signatures, syntax, seam consistency). Instead of
  executing checks, **surface the task's `Sanity-check now` list to the developer** as the checks *they*
  should run, plus any code-level confidence and known gaps you want them to watch. The honest handoff is
  "here's what I built and how you can confirm it," never a green claim you didn't earn.
  **The one exception is the in-suite behavior tests — they are not "the environment."** They run on SQLite
  in memory, so you write them, run them, and report the real output: `vendor/bin/pest <file>` in Pest repos,
  `php artisan test --compact --filter=<name>` (or `vendor/bin/paratest` for the suite) in PHPUnit repos —
  per `skunexus-behavior-testing`, **through the repo's PHP runner**: many client repos run PHP only inside
  Docker, where every host-style command fails, so resolve the runner once before the first test command
  (`CLAUDE.md` first, then the compose file or a failing `php -v` — that skill's Quick Reference has the
  recipe) and prefix every `php` / `composer` / `vendor/bin/*` call with it for the rest of the run. That
  exception covers `php artisan dump:schema-for-testing --env=testing` too — it migrates and dumps only the
  SQLite test schema, never the environment's database, and it is mandatory after a migration (see "Schema
  dump" below). That exception is what closes the verify loop: a red test is a bug you
  caught yourself, so you fix it and keep going instead of handing the developer a guess and waiting. Nothing
  else moves: `Sanity-check now` items are still restated for the developer and never executed, and a passing
  test group is evidence for exactly what it asserted, never for anything you only checked statically.

- **Ceremony must be earned (proportionality).** A trivial, well-described change gets implemented directly
  with **no artifacts at all** — downstream skills already fall back gracefully (`prd.md` → the plan's Goal &
  Acceptance → the real diff). When direct work outgrows "trivial", surface it and recommend planning — but
  the developer decides, and "continue anyway" is a legitimate answer.

- **Code carries no artifact references, and comments stay sparse.** The plan/PRD/decisions are the *why*;
  the code is the *what*. NEVER cite artifact sections in code — no `T3`, `D5`, `R19`, `OQ7`, "per the plan",
  "verified 2026-…" in comments, docblocks, or names. That coupling is noise: it rots when artifacts renumber
  and means nothing to a reader in the editor. Comment only what the code cannot say itself (a non-obvious
  invariant, a subtle gotcha) in plain domain language, and match the surrounding files' comment density —
  which in this codebase is *low*. When a step's rationale feels worth preserving, it belongs in the plan
  amendment or a decision entry, not a code comment. This binds subagents too (put it in their briefing).

- **The developer gates completion.** Mode 1 gates per task; mode 2 and Door B gate once at the end; Door C
  gates on the processed changes. Code review happens in the developer's editor over the real diff — never
  a chat walkthrough of the code. Announce the handoff, summarize what to look at, then wait.

## Workflow

### Step 0 — Situate (every invocation, including resume)

Read what exists: `.ai/<TICKET>/backend-plan.md`, `prd.md`, `decisions.md`. Give a one-line state recap —
e.g. "Approved plan, 11 tasks: 3 finished, 1 started (T5, 4/9 steps), 7 not_started." Statuses and
checkboxes on disk are the *only* persistent execution state, so resume in a fresh conversation is just this
step again. Then check the ground you'd build on:

- Plan is **Approved** → Door A. Plan is **Draft** → stop; the planning gate hasn't been passed — hand back
  to `skunexus-backend-plan` to finish review.
- No plan, change described → Door B. Changes requested on work already implemented → Door C.
- Run `git status` / `git branch`: confirm with the developer which branch to work on and flag any unrelated
  uncommitted changes before writing code.

A `started` task inherited from a previous session deserves quick skepticism: verify its checked steps'
code actually exists before trusting them — a session that died mid-write may have left boxes that lie.

### Door A — implement the plan

Ask the developer to pick a mode (recommend one based on plan size and how much they want to steer):

- **Task-by-task** — you implement in this conversation, the developer reviews each task before the next
  starts. Best when they want to stay close to the work.
- **Orchestrate** — subagents implement everything remaining, the developer reviews once at the end. Best
  when the plan is settled and they want throughput.

At mode start, confirm the branch and the commit convention once: default is **commit per task** using the
repo's existing style (`<TICKET>: <summary>` — include the task id, e.g. `LO-58: T3 create-RMA command +
endpoint`). Per-task commits are what make the final review navigable and any task revertible.

Read the plan header's **`> Tests:`** line — the decision the planning step recorded; whether trailers happen
to exist is not the signal. **`> Tests: none — <why>`, or no such line (a plan written before it existed), skips the
dial entirely: don't raise it, don't write tests, no runner, no baseline, run exactly as a plan always
has.** When it reads `behavior`, confirm the **testing mode** in the same exchange:

- **hybrid** (default) — each task's trailer is discharged post facto as part of that task. Default because
  it closes the verify loop at the smallest unit: the task that broke something is still the task in hand.
- **full post-facto** — tasks run untouched; one test pass after the last one.
- **no tests** — the developer opts this run out: trailers stay bare, nothing below runs, a `T0 (tests only)`
  dependency is ignored (T0 stays `not_started`), and the wrap-up reports the bare trailers as untested
  rather than auditing them.

The dial is **per run, not per developer or repo**: asked for each plan, re-confirmed on a resume from disk,
and changeable at any task boundary — the header records the planning decision, not the run mode, so
switching costs nothing; trailers not yet discharged simply follow the new mode, and `**Tests (landed):**`
ones stay landed.

Two things happen once, at mode start, whenever the run writes tests (hybrid or full post-facto):

- **Resolve the PHP runner — and say it.** A container prefix (`docker compose exec <service> …`, `sail …`)
  or host PHP, per `skunexus-behavior-testing`'s Quick Reference — `CLAUDE.md` first. State what you
  resolved in the same exchange as branch, commit convention and mode, so the developer corrects it like any
  other checkpoint; the confirmed value is what every test command in this run, and every briefing, carries.
- **Baseline the suite.** Run the whole suite once *before the first task* and record what is already red
  as one line under the plan's status header — `> Test baseline (<date>, <command>): clean` or
  `…: 3 red — <test names>` (a list too long for one line goes to `.ai/<TICKET>/test-baseline.md`, the line
  pointing at it). It is what separates "I broke this" from "this was already broken" for every red in the
  run; without it neither you nor an agent can tell. Clean is the normal outcome. Re-baseline only when the
  tree moves underneath (a rebase the developer tells you about). Switching into a test-writing mode after
  tasks have landed: record it as `> Test baseline (<date>, late — after T1–T3)` and treat its reds as this
  run's until the developer says otherwise — a late baseline would otherwise launder your own regressions.

Mode semantics:

- **Discharging a trailer (all modes)** means: load `skunexus-behavior-testing` (including its mandatory
  style-guide read) *before* writing test code; read the **current** wording of each acceptance bullet the
  trailer cites in the contract (`prd.md` §6, `investigation.md`, or the plan's Goal & Acceptance) — one test
  per bullet at least, its name restating that bullet in the grammar's subject–verb–outcome shape (a
  Given/When/Then bullet is the body's skeleton and its *then* clause is the name). The contract leads and
  the test follows: the name comes from the bullet, never from what the code turned out to do. Write the
  tests; run the file/group; put the real output in the hand-off; then rewrite the trailer in the plan
  **with what actually landed**: `**Tests (landed):** <path> — R4.a "<test name>", R4.b "<test name>"`. A
  relabel alone would let the plan claim proof no test asserts; the real names are what the wrap-up coverage
  check reads.
- **hybrid:** after a task's steps land, discharge that task's trailer as part of the task.
- **full post-facto:** tasks run exactly as today; after the last task, one pass discharges every trailer,
  grouped by test file, in its own commit(s) (`<TICKET>: behavior tests`), results reported at final review.
- **When the test and the code disagree, the contract decides (all modes).** A test named from the bullet
  that fails against the code is one of two things: the implementation is wrong (fix it) or the bullet is
  wrong (a contract flag — the developer decides, never you). "The test is wrong" is only ever
  **mechanical** — wrong layer, wrong fixture, wrong entry point — and is fixed by rewriting the test, not by
  bending it toward what the code does.
- **Escape hatch (all modes):** a bullet whose proof turns out out-of-suite (the layer map puts it at HTTP
  level or cross-process), or a mechanical fault you can't resolve, is flagged with one line of why — in the
  hand-off **and** in the plan, as `**Tests (flagged):** <path> — R6.a: <why>`, so a resume from disk still
  sees it. A flag is an open question, not an outcome: each one needs a **developer decision before the run
  is done** — move the bullet to `out-of-suite` in the task's `Sanity-check now` line, rewrite the test, or
  patch the contract — and the trailer is rewritten to match. Never grind on a test that doesn't make sense;
  never silently drop one.
- **Schema dump after a migration (all modes).** Tests load the SQLite schema from a dump on disk
  (core's `tests/database/schema/sqlite-schema.sql` — `vendor/skunexus/core/…` in client repos),
  regenerated by the test bootstrap only once it's older than `INVALIDATE_SCHEMA_DUMP_AFTER` (600 s in
  core's `phpunit.xml`, the 60 s default in client repos) — so a task that adds a migration can test against
  the old schema and pass or fail for the wrong reason. Right after a migration step lands, run
  `php artisan dump:schema-for-testing --env=testing` through the runner, before any test.
- **Baseline reds (all modes):** a red that is in the baseline is not this run's — never fixed, never
  touched, reported as `baseline`. A red that is *not* in the baseline is yours until classified otherwise.
- **Existing tests (all modes):** new tests follow `skunexus-behavior-testing`'s grammar even inside a file
  that already holds older-shaped tests; those are left alone unless the change broke them (dev guide §8 —
  repair, reshape or convert only what costs something; modernising is never a side effect).

#### Mode 1 — task-by-task

Loop until the developer stops or the plan is done:

1. **Propose.** Compute the ready set: unfinished tasks whose `depends_on` are all `finished`. Recommend in
   this order — a `started` task first (finish WIP before opening new fronts), then the ready task that
   unblocks the most downstream work (count transitive dependents; prefer the critical path). One line of
   "why this one" per candidate; the developer picks. Never propose a task with an unfinished dependency —
   that's how a run soft-blocks itself.
2. **Implement in this thread.** Re-read the task entry; read the dependency code; work the checkbox list in
   order, checking each box as its step lands. Deviations follow the tense rule. Scope discipline: the
   entry's `Out of scope` line is binding — resist fixing adjacent code you pass. In **hybrid**, the task's
   `Tests:` trailer is part of the task: once the steps land (schema dump first if one was a migration),
   discharge it (the definition above — real test names into the landed line) before handing off.
3. **Do not run environment verification** (per the honesty principle): don't run migrations/tinker/endpoints
   — the in-suite tests of step 2 are not that. Restate the task's `Sanity-check now` items as the checks the
   developer should run, and note any code-level confidence or gaps.
4. **Hand off for review.** Summarize in chat: files touched, steps deviated (and why), the real output of
   the test run (hybrid) alongside the `Sanity-check now` items for the developer to run, any decision
   candidates. Then the developer reviews the diff in their editor. Process feedback through
   the triage table; if a fix moves a seam, ripple-sweep the pending tasks now, not later. Loop until they
   approve the task.
5. **Close out.** Commit (if agreed), confirm the task's boxes/status are truthful, append any earned
   decision, and go back to 1.
6. **Full post-facto only — the test pass, after the last task.** In-thread, one test file at a time:
   discharge every trailer (the definition above), commit as `<TICKET>: behavior tests`, then hand the pass
   off for review as its own step — the developer reviews the test diff like a task, feedback goes through
   the triage table, and only their approval moves on to the Wrap-up.

#### Mode 2 — orchestrate

You are the orchestrator: you schedule, review, track, and commit — subagents write the code.

1. **Preflight.** Re-read the whole plan. Surface anything that gates an autonomous run: an Open Question
   that blocks a task (deliberately-deferred ones usually don't), a `started` task with untrustworthy boxes,
   a dirty working tree, a missing test baseline when the run writes tests (the mode-start steps above: runner
   resolved, suite baselined into the plan header). Confirm branch + commit-per-task with the developer; this
   is their last checkpoint until the final review. Confirm **agent isolation** in the same breath — two
   valid shapes:
   - **shared tree** (default for small plans) — every agent edits the one checkout; the file-disjoint rule
     below is what keeps them apart, and a neighbour's half-written file can still fatal another agent's
     test run (reported as `environment`, settled by your re-run). The schema dump is shared too, and the
     test bootstrap regenerates it on its own once stale — so no instruction stops a parallel agent's run
     from loading a neighbour's half-written migration. The rule is scheduling instead: **in a shared tree,
     a task that adds a migration runs with nothing else in flight** (step 2). With several migration
     tasks, prefer worktrees.
   - **worktree per agent** — spawn with `isolation: worktree` (Claude Code creates a git worktree under
     `.claude/worktrees/`; PhpStorm sees it as its own root and branch). No shared tree, so no neighbour
     fatals, no file-set prediction needed, and the agent's own test run is trustworthy. Cost: a fresh
     worktree has only tracked files. Copy the main checkout's git-ignored files into it (`.env` above all —
     `APP_KEY` lives there and no `phpunit.xml` sets it — plus whatever else the app needs locally:
     `git -C <main> ls-files --others --ignored --exclude-standard`), except `vendor/`, which gets its own
     `composer install` (warm cache, well under a minute) per agent, never a copy or symlink (PHP resolves
     `__DIR__` through it and autoloads the *main* tree). Every command goes through
     the resolved runner **re-pointed at the worktree** — with Docker, `docker compose -f <main repo compose
     file> exec -w <container path of the worktree> <service> …`; the bare prefix runs in the main checkout
     and would install into, and test, the wrong tree while reporting green. The worktree must sit inside
     the mounted path (`.claude/worktrees/` under the repo does). Each worktree has its own schema dump, so an agent whose
     task adds a migration regenerates it itself, with no collision. Prefer it when tasks add migrations, when tasks
     touch shared registration points (providers, `routes/api.php`, config), when the plan is large enough
     that serialization would cost more than the installs, or whenever in-agent test results must be
     trusted as-is.
2. **Schedule continuously — dependency-ready AND file-disjoint.** Don't run rigid waves; launch a task the
   moment (a) its `depends_on` are all finished and (b) its predicted file set is disjoint from every
   in-flight task's. Predict file sets from the exact paths named in the task's steps, **plus the shared
   registration points this codebase funnels everything through** — provider classes, `routes/api.php`,
   `config/skunexus.php`, `config/app.php` — **plus, in hybrid, the test file the `Tests:` trailer names**.
   The domain's `tests/Behavior/` traits are deliberately **not** in the set: most tickets live in one
   domain, so claiming `{Domain}ScenarioTrait` per task would serialize the whole run. Instead, **agents in a
   parallel hybrid run never edit those traits** — they use the existing vocabulary freely and write any new
   word local to their own test file (a private `given*`/`assert*` method in PHPUnit; an inline `given(fn)`
   delta or the namespaced file-level `givenX()` fallback in Pest — style guide §3, ladder §8), reporting it as a
   **vocabulary candidate**. Record each candidate under the plan header as you record its task
   (`> Vocabulary candidates: givenX (tests/Feature/…/FooTest.php) → {Domain}ScenarioTrait; …`) — your
   context is not a resume-safe store. You graduate them into the traits yourself, serially, after the last
   task (step 7) — one writer, no interleaving, and the run's own tests prove the move. Two DAG-independent tasks that both "register the handler in
   the commands provider" WILL collide; that's overlap, so they serialize. When unsure whether two tasks
   overlap, serialize — lost parallelism is cheap, interleaved edits to one file are not. In a shared tree,
   a task whose steps add a migration also runs alone: the test bootstrap regenerates the shared schema dump
   on its own, so any parallel run could load the half-written migration.
3. **Assign models.** Default to the session model. Drop an agent to `sonnet` when the task entry is
   mechanical mirroring — a named precedent to copy, no "verify during implementation" branches, low blast
   radius (mail plumbing, permission config, a templated migration). Keep the session model for tasks that
   produce seams others consume, carry defensive branches or in-flight verification demands, or integrate
   across domains. A wrong cheap-model task costs more than the tokens it saved — when in doubt, don't
   downgrade.
4. **Brief and spawn.** Fill `assets/task-agent-briefing.md` per task — verbatim task entry, contract
   pointers, the dependency code to read, the prohibitions (no `.ai/` writes, no commits, no scope creep) —
   and spawn as a `general-purpose` agent. Launch independent tasks in parallel. State the testing mode, the
   resolved PHP runner and the test baseline in the briefing: in **hybrid** the agent discharges its own
   task's `Tests:` trailer (traits untouched, new words local — the rule in step 2); in **full post-facto**
   (or with no trailer) the briefing's no-tests prohibition stands.
5. **On each return, review before you record.** Read the agent's report against the actual diff of its
   predicted files; spot-check the seams other tasks will consume (statically — don't run migrations/tinker/
   endpoints; environment verification is the developer's). In hybrid, re-run the returned task's test
   file/group yourself rather than trusting the report — this serialized run on a settled tree is the
   authoritative one and the agent's own run is advisory, because parallel agents share one working tree:
   a neighbour's half-written provider can fatal an unrelated run, and while each test's database is
   `:memory:`, the schema dump it is loaded from is a shared file on disk. When the returned task added a
   migration, regenerate the dump first (`dump:schema-for-testing --env=testing` through the runner), then
   re-run. A task returned red routes by
   its class: `implementation` still red after the agent's three rounds → step 6; `test mechanics` → the
   flag goes into the plan as `**Tests (flagged):**` and onto the developer's decision list; `contract` →
   step 6's contract-flag path; `environment` → your re-run settles it; `baseline` → nothing, it was red
   before the run started (confirm against the plan's baseline line, not the agent's word). With **worktree isolation**, bring the task home first —
   `git -C <worktree> add -A && git -C <worktree> diff --cached | git apply --3way` onto the ticket branch,
   then remove the worktree — so the agent still never commits and you still commit once per task. With
   traits untouched and file sets disjoint the apply is clean; `--3way` is for the shared registration
   points the prediction covers but cannot guarantee — a conflict there is yours to resolve before the
   re-run, never the next agent's to trip over. Only then, as the single writer: check the boxes,
   flip the status, record amendments, append earned decisions, and commit. Then launch whatever just became eligible.
6. **Handle trouble without guessing.** A shallow or failed report → re-run the gaps on a stronger model or
   implement them in-thread; never patch blind over work you don't trust. An agent's contract flag (a
   requirement looks wrong or missing) → pause that task's dependent subtree only, keep independent tasks
   running, and put the question to the developer — the contract is never yours to guess.
7. **Final review.** In **full post-facto**, the test pass runs first — after the last task, before this
   review: in-thread, one domain at a time (one writer, so the graduation ladder applies as written). In **hybrid**, graduate the returned
   **vocabulary candidates** first — one serial pass per domain, yours or one cheap agent's, moving each
   local word into `{Domain}ScenarioTrait` / `{Domain}AssertionsTrait` per style guide §8 and re-running the
   groups that used it; a commit of its own (`<TICKET>: test vocabulary`); then delete the plan's
   `> Vocabulary candidates` line. Then the **Wrap-up** checks below —
   the full-suite run against the baseline and the trailer/coverage audit — and only then present the run
   report: per task one line (what landed, deviations), the full-suite result, the per-task `Sanity-check
   now` items for the developer to run, artifact updates, the commit list. Hand off — the developer reviews
   the whole branch in their editor, commit by commit. Triage their feedback; delegate mechanical fixes to
   cheap agents, keep judgment fixes in-thread. Approval ends the run.

### Door B — no plan: direct implementation

1. **Gauge, then let the developer choose the road.** From the prompt and a quick look at the touched code,
   say honestly what this change looks like, then offer: **implement directly now** (no artifacts — the diff
   is the record) or **plan first** (hand off to `skunexus-backend-plan`, which right-sizes the ceremony:
   inline Goal & Acceptance, lite PRD, or the full PRD interview). Recommend one; they decide.
2. **Direct road.** Build understanding before writing (docs skill + read the target code — with no plan,
   there is no pre-baked grounding to lean on). When an approved `investigation.md` exists, start from it:
   its root cause and proposed fix are the settled diagnosis (verify against the code you touch rather than
   re-hunting the bug), and its `A1…An` bullets are what the diff must satisfy. Implement in-thread, hand off for diff review (the developer
   runs any environment verification), fix on feedback. If a genuine decision surfaces — a real fork whose rationale the code won't reveal — offer
   to record it in `.ai/<TICKET>/decisions.md`; otherwise leave no trace but the diff. Trivial changes stay
   test-free by default. Offer a test — one line: the file and the proposition it would prove, plus, when the
   harness (`bus()` / `given()`) is missing, that adding it comes first as its own commit
   (`<TICKET>: test harness`) — when the
   change is behavior-bearing per `skunexus-behavior-testing`'s quick decision table (a new command, plugin,
   transition, override, GraphQL field, endpoint, resolver) or is a confirmed-bug fix off an approved
   `investigation.md` (a repro test, written after the fix). With an investigation, the proposition is an
   `An` bullet. **Without one there is no contract at all**: the proposition you show *is* the agreed
   behavior, so spell it out in full and treat the developer's yes as approval of that behavior, not only of
   writing a test. On a yes, before touching code: resolve the PHP runner (`CLAUDE.md` first) and say it,
   and run the touched test file/group once — the before-picture that tells your red from an old one. Then
   write the test after the change, run it through the runner, and report the real output.
3. **Escalate visibly when "trivial" stops being true.** Triggers: the change wants several independent
   tasks; a migration or shared seam that multiple edits build on; product-level ambiguity you'd have to
   guess; materially more surfaces than the prompt implied. Stop, summarize what you've learned (mapped
   surfaces, what's decided, what's open — this seeds the planning skill so nothing is re-discovered),
   recommend the hand-off, and **let the developer decide**. If they say continue, note the accepted risk in
   one line and carry on — their call, made informed, is the point.

### Door C — changes requested on implemented work

The developer describes what needs to change, in their own words — their conclusions after living with the
code, QA findings, or feedback they're relaying from a code review. If they point at a PR, pulling its
comments (`gh pr view --comments`) is a fine supplementary input, but the developer's framing is the
request; never require one.

1. **Gather.** Take the described changes; read the ticket's three artifacts — `decisions.md` especially: it
   exists precisely so later rounds don't re-litigate settled forks.
2. **Map before you edit.** Triage every requested change through the table and present the map — item →
   planned action (code fix / step amendment / decision supersede / PRD patch / push back) — to the
   developer. An item that contradicts a recorded decision gets flagged with the recorded rationale; the
   developer chooses: change course (→ dated **superseding** entry, provenance-tagged with where the change
   came from) or uphold (→ dated **addendum** on the entry, "re-raised \<date\>, upheld" — so the *next*
   round doesn't repeat it either; this is the versioning, no other mechanism needed). A change to *behavior*
   carries its tests: the map names the test files citing the moved requirement — the plan's trailers are the
   index; with no plan, or a plan without trailers, grep `tests/` for the touched command, endpoint or
   resolver class — they are updated in the same change (`skunexus-behavior-testing` — each name re-read
   from the moved requirement), and the touched groups are green before hand-off. When tests are in play,
   resolve and state the PHP runner first and run those groups once *before* the change, so a red after it
   is known to be yours.
3. **Apply.** Code fixes in-thread or delegated; artifact updates per the map and the tense rule;
   requirement-level changes patch `prd.md` with a changelog line.
4. **Report per item** — fixed / upheld with rationale / needs a developer call — then hand off for diff
   review and commit.

### Wrap-up

Before the final hand-off, when the run wrote tests (hybrid or full post-facto — in mode 1 this follows the
last task, or the test pass, in mode 2 it precedes the run report):

- **One full-suite run**, compared against the baseline. Until now only the touched file or group has ever
  run, so a change that broke another domain is still invisible. Every red not in the baseline is this run's
  — fix it (or classify and flag it) before handing off; a baseline red that turned green is worth a line.
  Report the real output.
- **No bare or flagged trailer left.** Every `**Tests:**` line now reads `(landed)` with its real test
  names. A bare one is an undischarged promise; a `(flagged)` one still waits on the developer's decision
  (out-of-suite / rewrite the test / patch the contract) — put each to them by ID, and the run isn't done
  until every flag is decided and its line rewritten.
- **Coverage still holds, per bullet** — the plan skill's self-review question, re-asked against what
  landed: every acceptance bullet (`Rn.x` or `An`, or a bullet-less `Rn`) is named by a landed test or recorded as out-of-suite in a
  `Sanity-check now` line. A bullet that lost its test is reported to the developer by ID, never left
  implied.

With **no tests** chosen for the run, none of this applies: the hand-off lists the bare trailers as untested,
by bullet ID, and stops there.

When the last task is approved: every `Status` reads `finished` and no box lies — the one exception is a
`T0 (tests only)` left `not_started` by a **no tests** run, reported as such in the hand-off; deviations are amended,
earned decisions appended, the PRD patched only where requirements actually moved.

Say what comes next in the workflow (`skunexus-backend-pr` for the PR description; FE handoff and testing
steps are their own downstream skills) and stop — don't write the PR description here.
