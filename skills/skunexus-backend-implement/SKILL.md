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
  per `skunexus-behavior-testing`. That exception is what closes the verify loop: a red test is a bug you
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

Confirm the **testing mode** in the same exchange — but only when the plan actually carries `Tests:` trailers.
**A plan with no `Tests:` trailers skips the dial entirely: don't raise it, don't write tests, run exactly as
today.** When trailers exist:

- **hybrid** (default) — each task's trailer is discharged post facto as part of that task. Default because
  it closes the verify loop at the smallest unit: the task that broke something is still the task in hand.
- **full post-facto** — tasks run untouched; one test pass after the last one.
- **full TDD** — tests lead the code; opt-in, and the slowest to steer.

The dial is **per run, not per developer or repo**: asked for each plan, re-confirmed on a resume from disk,
and changeable at any task boundary — nothing in the plan records the mode, so switching costs nothing;
trailers not yet discharged simply follow the new mode, and `**Tests (landed):**` ones stay landed.

Mode semantics:

- **hybrid:** after a task's steps land, discharge that task's trailer — load `skunexus-behavior-testing`
  (including its mandatory style-guide read) *before* writing test code, write the tests, run the file/group,
  put the real output in the task hand-off, and rewrite the trailer in the plan as `**Tests (landed):**`.
- **full post-facto:** tasks run exactly as today; after the last task, one pass discharges every trailer,
  grouped by test file, in its own commit(s) (`<TICKET>: behavior tests`), results reported at final review.
- **full TDD:** the trailer propositions become the skeleton titles; red → green per vertical slice per
  `skunexus-tdd-testing`, which owns the loop. It never edits the plan document.
- **Escape hatch (all modes):** a trailer that proves out-of-suite (the layer map puts it at HTTP level or
  cross-process) or simply wrong against the real code gets flagged in the hand-off with one line of why.
  Never grind on a test that doesn't make sense; never silently drop one.
- **Existing tests (all modes):** new tests follow `skunexus-behavior-testing`'s grammar even inside a file
  that already holds older-shaped tests; those are left alone unless the change broke them (dev guide §8 —
  repair, reshape or convert only what costs something; modernising is never a side effect). A touched file
  is rendered whole at wrap-up, so `⚠` markers on its pre-existing scenarios are that file's debt, not the
  ticket's.

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
   `Tests:` trailer is part of the task: once the steps land, discharge it and mark it `**Tests (landed):**`
   before handing off.
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

#### Mode 2 — orchestrate

You are the orchestrator: you schedule, review, track, and commit — subagents write the code.

1. **Preflight.** Re-read the whole plan. Surface anything that gates an autonomous run: an Open Question
   that blocks a task (deliberately-deferred ones usually don't), a `started` task with untrustworthy boxes,
   a dirty working tree. Confirm branch + commit-per-task with the developer; this is their last checkpoint
   until the final review. Confirm **agent isolation** in the same breath — two valid shapes:
   - **shared tree** (default for small plans) — every agent edits the one checkout; the file-disjoint rule
     below is what keeps them apart, and a neighbour's half-written file can still fatal another agent's
     test run (reported as `environment`, settled by your re-run).
   - **worktree per agent** — spawn with `isolation: worktree` (Claude Code creates a git worktree under
     `.claude/worktrees/`; PhpStorm sees it as its own root and branch). No shared tree, so no neighbour
     fatals, no file-set prediction needed, and the agent's own test run is trustworthy. Cost: `vendor/`
     is not in a fresh worktree — `composer install` (warm cache, well under a minute) per agent, never a
     symlink (PHP resolves `__DIR__` through it and autoloads the *main* tree). Prefer it when tasks
     touch shared registration points (providers, `routes/api.php`, config), when the plan is large enough
     that serialization would cost more than the installs, or whenever in-agent test results must be
     trusted as-is.
2. **Schedule continuously — dependency-ready AND file-disjoint.** Don't run rigid waves; launch a task the
   moment (a) its `depends_on` are all finished and (b) its predicted file set is disjoint from every
   in-flight task's. Predict file sets from the exact paths named in the task's steps, **plus the shared
   registration points this codebase funnels everything through** — provider classes, `routes/api.php`,
   `config/skunexus.php`, `config/app.php`. Two DAG-independent tasks that both "register the handler in
   the commands provider" WILL collide; that's overlap, so they serialize. When unsure whether two tasks
   overlap, serialize — lost parallelism is cheap, interleaved edits to one file are not.
3. **Assign models.** Default to the session model. Drop an agent to `sonnet` when the task entry is
   mechanical mirroring — a named precedent to copy, no "verify during implementation" branches, low blast
   radius (mail plumbing, permission config, a templated migration). Keep the session model for tasks that
   produce seams others consume, carry defensive branches or in-flight verification demands, or integrate
   across domains. A wrong cheap-model task costs more than the tokens it saved — when in doubt, don't
   downgrade.
4. **Brief and spawn.** Fill `assets/task-agent-briefing.md` per task — verbatim task entry, contract
   pointers, the dependency code to read, the prohibitions (no `.ai/` writes, no commits, no scope creep) —
   and spawn as a `general-purpose` agent. Launch independent tasks in parallel. State the testing mode in
   the briefing: in **hybrid** the agent discharges its own task's `Tests:` trailer; in **full post-facto**
   (or with no trailer) the briefing's no-tests prohibition stands.
5. **On each return, review before you record.** Read the agent's report against the actual diff of its
   predicted files; spot-check the seams other tasks will consume (statically — don't run migrations/tinker/
   endpoints; environment verification is the developer's). In hybrid, re-run the returned task's test
   file/group yourself rather than trusting the report — this serialized run on a settled tree is the
   authoritative one and the agent's own run is advisory, because parallel agents share one working tree
   and a neighbour's half-written provider can fatal an unrelated run (the DB never interferes: `:memory:`
   SQLite is per process, which is what `--parallel` relies on every day). A task returned red routes by
   its class: `implementation` still red after the agent's three rounds → step 6; `test wrong` → the flag
   stays in the hand-off; `contract` → step 6's contract-flag path; `environment` → your re-run settles it.
   With **worktree isolation**, bring the task home first — `git -C <worktree> add -A && git -C <worktree>
   diff --cached | git apply` onto the ticket branch, then remove the worktree — so the agent still never
   commits and you still commit once per task. Only then, as the single writer: check the boxes,
   flip the status, record amendments, append earned decisions, and commit. Then launch whatever just became eligible.
6. **Handle trouble without guessing.** A shallow or failed report → re-run the gaps on a stronger model or
   implement them in-thread; never patch blind over work you don't trust. An agent's contract flag (a
   requirement looks wrong or missing) → pause that task's dependent subtree only, keep independent tasks
   running, and put the question to the developer — the contract is never yours to guess.
7. **Final review.** In **full post-facto**, the test pass runs first — after the last task, before this
   review: orchestrator-run, or one test-authoring agent per domain when the surface is large. Run all
   touched test groups and report the real output. Present the run report: per task one line (what landed,
   deviations), the per-task `Sanity-check now` items for the developer to run, artifact updates, the commit list. Hand off — the developer reviews the whole branch in their
   editor, commit by commit. Triage their feedback; delegate mechanical fixes to cheap agents, keep
   judgment fixes in-thread. Approval ends the run.

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
   test-free by default. Offer a test — one line: the file and the proposition a `Tests:` trailer would have
   carried — when the change is behavior-bearing per `skunexus-behavior-testing`'s quick decision table (a
   new command, plugin, transition, override, GraphQL field, endpoint, resolver) or is a confirmed-bug fix
   off an approved `investigation.md` (a repro test). Write it only if the developer says yes; then run it
   and report the real output.
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
   carries its tests: the map names the test files whose propositions move with it, they are updated in the
   same change (`skunexus-behavior-testing` — the name is the contract), and the touched groups are green
   before hand-off.
3. **Apply.** Code fixes in-thread or delegated; artifact updates per the map and the tense rule;
   requirement-level changes patch `prd.md` with a changelog line.
4. **Report per item** — fixed / upheld with rationale / needs a developer call — then hand off for diff
   review and commit.

### Wrap-up

When the last task is approved: every `Status` reads `finished` and no box lies; deviations are amended,
earned decisions appended, the PRD patched only where requirements actually moved.

When the ticket landed tests, regenerate `.ai/<TICKET>/spec-from-tests.md` with the `skunexus-spec-extract`
skill — a standing artifact, always regenerated, never hand-edited. Its input is **every test file the branch
added or changed** (`git diff --name-only <base>...HEAD -- '*Test.php'`), each rendered whole: a ticket that
adds one test here and two there gets all three files' current contract, never a diff of test lines. It reads
both syntaxes (`--mode` defaults to `pest`); a run that renders 0 scenarios means the tests fell outside the
grammar, which is a signal to fix them — never a reason to hand-write the file. Say so in chat.

Then run the **acceptance coverage check**: read that spec against the acceptance criteria in the existing
lookup order (`prd.md` → `investigation.md` → the plan's inline Goal & Acceptance) and report two lists —
`Rn`/`An` with no scenario, and scenarios that map to no acceptance id. The PRD is the spec and the tests
are its proof; the two never stay divergent, so every line of both lists resolves before hand-off:

- an `Rn` with no scenario gets one line of why — proven out-of-suite (layer map), covered by another
  requirement's scenario, or an accepted gap. Thin coverage is the developer's to accept, **not a gate** —
  but the acceptance is recorded (plan or `decisions.md`), never silent.
- a scenario with no `Rn` is behavior nobody asked for: either the PRD gains the line (patch + changelog,
  as Door C does) or the test goes. Never a test that quietly outruns its contract.

Say what comes next in the workflow (`skunexus-backend-pr` for the PR description; FE handoff and testing
steps are their own downstream skills) and stop — don't write the PR description here.
