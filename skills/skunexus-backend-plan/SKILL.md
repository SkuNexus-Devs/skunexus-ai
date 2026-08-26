---
name: skunexus-backend-plan
description: >-
  Turn agreed requirements into a detailed, codebase-grounded BACKEND implementation plan — a DAG of
  independent, self-contained tasks an implementation agent can execute without stopping to ask for
  clarification. This is the planning step of the engineering AI workflow: it normally runs AFTER a PRD is
  approved (skunexus-jira-prd) and BEFORE implementation, but it does NOT require a PRD — for simpler changes
  it right-sizes the requirements itself (a lightweight inline spec). Use it whenever the developer wants to
  plan, break down, scope, or "turn into tasks" backend work, or says things like "plan the backend for
  TICKET-123", "break this into tasks", "create the implementation plan", "how should we build the backend
  for X", "skip the PRD, just plan this", or "make the build plan". Trigger even when they don't say
  "backend" if they're planning server-side work (API, domain/commands/handlers, DB/migrations, jobs,
  services, GraphQL). Also trigger to RESUME an in-progress plan — "continue the plan for TICKET-123",
  "let's finish reviewing the backend plan", or any mention of an existing backend-plan.md draft, even in a
  fresh conversation. Do NOT trigger for: a full product requirements interview when the ask is genuinely
  unclear (that's skunexus-jira-prd), planning the FRONTEND, or actually implementing the tasks.
---

# Requirements → Backend Implementation Plan

Produce a backend implementation plan that an AI implementation skill (and a human reviewer) can act on
**directly, without coming back to ask what was meant**. The plan is a **DAG of self-contained tasks**: each
runnable on its own, dependencies declared explicitly so independent tasks parallelize.

The deliverable is `.ai/<TICKET>/backend-plan.md`, finalized **only after the developer explicitly approves
it**. Depending on the change, one other file may be touched: `decisions.md` (durable rationale, created only
if earned).

## Inputs

A ticket key or short slug to name the working folder, and **agreed acceptance** — the requirements this plan
is built against. That acceptance can arrive at one of three weights (Step 1 picks the lightest that's safe):
a full `prd.md`, a lightweight `prd.md` captured here, or a 2–3 line inline Goal & Acceptance block in the
plan itself. If invoked with no key/slug and no PRD, ask what to build and how to name the folder.

Everything lives under `.ai/<TICKET>/` **in the current working repository**:

```
.ai/<TICKET>/
├── prd.md            # INPUT when it exists (full or lite) — the agreed contract tasks trace to. May be absent.
├── investigation.md  # INPUT on the bug route (skunexus-bug-hunt) — its "Expected behavior after the fix"
│                     # bullets (A1…An) are the agreed acceptance. May be absent.
├── backend-plan.md   # THE DELIVERABLE — the task DAG; starts Draft, ends Approved
└── decisions.md      # durable ADR-style rationale; SHARED across BE/FE; created ONLY when earned
```

## Operating principles (read before doing anything)

These are the soul of the skill. The mechanics below serve them.

- **Plan against agreed acceptance — never your own assumptions.** Every task exists to satisfy stated
  acceptance, and you decide *how* to meet it, not *what* it should be. The acceptance may be a full PRD, a
  lite spec, or an inline Goal & Acceptance block — but it is always *agreed*, and every task traces to it. A
  wrong plan run by an autonomous agent is the most expensive thing this skill can produce, so when you'd
  assume a value, a boundary, or an intent, ask instead. If you find the contract itself is missing or wrong,
  that's a contract question (Step 5) — never quietly fold new scope into the plan, or the plan and the
  contract it's supposed to satisfy drift apart.

- **Right-size everything to the change (proportionality).** Match the weight of the requirements *and* the
  plan to the weight of the work. A one-line change doesn't need a PRD, a manifest table, or a frontend-facing
  surface note; a multi-domain feature does. Over-structuring a trivial change is its own kind of slop —
  it buries the real work in ceremony and makes review cumbersome. Reach for the lightest form that still
  leaves an implementor unable to take a wrong turn.

- **Ground every task in the real codebase — map before you plan.** "Detailed enough that the implementor
  never has to ask" is only reachable when each task names *real* files, classes, methods, and the SkuNexus
  pattern it follows. A plan written from imagination is plausible and wrong. Build the mental model from the
  platform docs (the `skunexus-docs-c7` skill), then read the actual code for exact signatures and
  conventions. This research *is* the bulk of the skill's value — don't shortcut it to reach a tidy-looking
  document faster. (Scale it too: a tiny change needs a glance, not a survey.)

- **Tasks are nodes in a DAG: self-contained, independently runnable, explicitly wired.** An implementation
  agent picks up a *single* task and implements it directly in the codebase — so each task must stand on its
  own (its files, its approach, its boundary) and declare its dependencies (`depends_on`) rather than imply
  them. "Self-contained" means it needs no *other task's plan entry* to be understood — **not** that it ignores
  the repo: a task never starts until everything in its `depends_on` is complete and its code is available, and
  the implementor reads that real code for exact signatures (the live code, not the plan text, is the source
  of truth for signatures). That gate is the whole point of `depends_on`, and it's what makes parallelism safe —
  tasks run concurrently only when no dependency path connects them (the same execution wave). Dependencies
  form a *directed acyclic graph*: they may chain, but must never cycle (a cycle means nothing can start). Put
  the shared seams first — migrations, value objects, interfaces, API/GraphQL contracts become **foundational
  tasks** — so downstream work builds against one agreed seam instead of inventing conflicting ones.

- **Specify the "how" as atomic checkbox steps — implementation altitude, but you are planning, not coding.**
  A task body is a flat `- [ ]` list: **one action per step, verb-first, with the exact file path, class, and
  method named *in the step***. A step must be executable read alone — no "see the files above", no "same as
  T2", no step that mentions a concept without its concrete class/file/route. Steps read like "Create
  `app/Domain/X/Commands/Foo/FooHandler.php` extending `AbstractY`: validate Z, throw `ZException` — mirror
  `app/Domain/W/.../BarHandler.php`" — never paragraphs. Name the existing pattern to mirror inline, in the
  step it guides. Reserve literal code for contracts that must be precise (a method signature, a migration
  column, a response shape); don't paste whole implementations — that's the implementor's job. **Dense prose
  is the failure mode this skill must avoid**: a wall of text can't be scanned, can't be checked off, and
  buries the actions in rationale. A short parenthetical "why" on a step is fine; rationale that matters
  long-term goes to `decisions.md`.

- **The plan is a living tracker; the contract and the decisions log carry the durable "why".** Each task
  carries a `Status: [not_started|started|finished]` line and checkbox steps. The status is **derived from
  the checkboxes**: `not_started` (the default) while no step is checked, `started` the moment the first step
  is checked, `finished` only when every step is checked. The implementation skill (or a human) checks boxes
  and flips the status accordingly as work lands, so the plan is the one place to see where the ticket
  stands — including across amendments mid-implementation. Track *progress* there, but keep the other kinds
  of truth where they belong: *verification* truth lives in the acceptance criteria (PRD §6, or the inline
  Goal & Acceptance block); the *why* behind key technical choices lives in `decisions.md`. When
  implementation legitimately deviates from a step, amend the step (or add a dated amendment note under the
  task) rather than leaving a checked box that lies. At planning time, any status other than `not_started`
  must be backed by concrete evidence — a file path, class, or commit SHA noted in an **Existing work** line —
  never by the PRD's claim alone.

- **The plan is a gate, not a formality.** You finish only when the developer has reviewed and explicitly
  approved. Review the **shape** (the DAG) in-chat first; the *detail* review then happens in the document,
  not the chat — the developer reads `backend-plan.md` on their own and reports back issues (or approval).
  Don't re-paste task bodies into the conversation as a "walkthrough": the document is the deliverable, it's
  faster to read in an editor, and re-surfacing it just burns context. Process the reported issues per task,
  and treat every edit as potentially contagious: a change to one task can force changes in the tasks wired
  to it, so after each edit **sweep its DAG neighbours in both directions** — the tasks that depend on it and
  the tasks it depends on — and re-open whatever the ripple actually touches. Feedback on a late task that
  ripples back to an earlier one is normal, so re-open affected tasks freely. Approval is one global gate at
  the end, never per-task. Anything unresolved becomes an Open Question, not a guess.

## Workflow

### Step 0 — Resume check

If `.ai/<TICKET>/backend-plan.md` already exists, **default to continuing from disk — don't re-map the
codebase.** Re-read `prd.md` (if present), `backend-plan.md`, and `decisions.md`, then give a one-line state
recap (e.g. "plan is a Draft with 8 tasks, 2 Open Questions"). Then:

- **Draft (review in progress):** ask a light "anything new before I continue?" and pick up where you left
  off. After a context reset you *won't know* where the review stood — the plan file doesn't track it, so
  re-show the manifest and ask: is the developer still reading the document, or do they have issues to
  report / approval to give? Restarting the feedback loop costs nothing.
- **Approved:** report the state — including execution progress read from the task `Status` lines and
  checked boxes (e.g. "Approved; T1–T3 finished, T5 started, rest not_started") — and stop; wait for the
  developer to say what's next (revise, add a task, hand off to implementation). Don't re-plan or re-approve
  on your own initiative.

**Full re-maps are for when the developer asks or the contract has changed** — the plan on disk already
carries the grounded detail (that's why Step 3 drafts everything from the map), so a fresh context window
doesn't need to rebuild it. But the no-re-map default is about not *repeating* work, never a license to skip
grounding: when feedback means adding a task or reworking one whose surface you haven't seen in *this*
context window, do a targeted look at just that surface (a direct read, or one small subagent) instead of
editing from imagination. If the folder has a `prd.md` but no `backend-plan.md`, proceed to Step 1.

### Step 1 — Establish right-sized acceptance (the three doors)

The plan needs agreed acceptance to trace to. Reach it at the lightest weight that's safe:

- **An Approved `prd.md` already exists** → use it. Tasks will trace to its requirements (`R1…Rn`). Read any
  **Notes for Design** footer (parked ideas to weigh, not decisions) and `decisions.md` if present.
- **A `prd.md` exists but is `Draft`** → surface it and ask before proceeding. Planning against an unsettled
  spec risks rework when it moves. Proceed only if the developer *explicitly* accepts that risk.
- **An Approved `investigation.md` exists (the ticket came through `skunexus-bug-hunt`)** → use it. Its
  "Expected behavior after the fix" bullets (`A1…An`) are the agreed acceptance tasks trace to, and its
  root cause + proposed fix seed the technical approach — plan the fix, don't re-derive the diagnosis.
  A `Draft` investigation gets the same treatment as a Draft PRD: surface it and ask.
- **Neither exists** → judge the size of the change *with the developer* and pick a door:
  - **Substantial or genuinely ambiguous** → recommend the full PRD first (`skunexus-jira-prd`); planning on
    sand wastes the work. Hand off and stop.
  - **Moderate but well-understood** → run a **brief** scoping pass (not the relentless PRD interview): pin
    down a Summary, a short numbered **Requirements** list (`R1…Rn`) with testable acceptance, and explicit
    non-goals. Write it to `.ai/<TICKET>/prd.md` from the PRD skill's template
    (`../skunexus-jira-prd/assets/prd-template.md`; if that template isn't on disk, just write those
    sections by hand), with a marker line `> Source: lightweight scoping (no
    Jira PRD)`. Confirm it captures the intent, mark it `Approved`, then plan. Tasks trace to `R1…Rn`.
  - **Simple** → don't create a spec file at all. Capture a 2–3 line **Goal & Acceptance** block at the top
    of `backend-plan.md` itself (acceptance bullets `A1…An`). Tasks trace to `A1…An`. This block is the
    contract — it lives at requirement altitude, above the step-level detail that may drift.

The **anti-guessing rule applies in every door.** In a lite/inline door, if real ambiguity surfaces or the
scope balloons, *offer to escalate* to the full PRD rather than paper over it. If there's no Jira ticket at
all, ask for a short slug to name the `.ai/<slug>/` folder.

> **Downstream contract:** later skills (PR description, testing) read `prd.md` if it exists, else
> `investigation.md` (the bug route), else the plan's inline Goal & Acceptance plus the real diff — richest
> source available, one predictable lookup order.

### Step 2 — Map the codebase (subagents, separate context)

You cannot write grounded tasks without knowing the real code. Spawn **Explore/general-purpose subagent(s)**
to map the surfaces the requirements touch. This runs in separate context windows on purpose: the relevant
code is large and would crowd out the planning work, and mapping several areas in parallel is faster. Scale
it to the change — one subagent (or a direct look) for a small single-surface change; one per area, run
together, for a change spanning several domains.

First build the mental model with the **`skunexus-docs-c7`** skill (how the platform's pieces fit), then have
the subagents read the actual code for exact signatures.

Mapping is retrieval, not judgment — don't burn the planning-thread model on it. Spawn the subagents on a
cheaper model (`model: sonnet` is the sweet spot; `haiku` only for a narrow mechanical lookup like "list the
migrations touching table X"). A cheaper model discovers less on its own, so the briefing does more of the
work: give each subagent its area, what the requirements need from that area, and the pattern names your docs
pass established, and ask for structured findings back. Don't push below the tier that reliably returns
*exact, verified* signatures — a wrong signature in the map becomes a wrong task in the plan, the expensive
failure this whole skill exists to prevent.

Each subagent should map, for its area:

- **Domain module** — which `app/Domain/<Context>/` this touches, or whether a new context is warranted.
- **Command + Handler** — existing `Commands/<Name>/<Name>Handler.php` to mirror; handlers validate domain
  invariants, so note which invariants live where.
- **HTTP edge** — relevant `Http/Controllers/API` controllers and `Http/Requests/<Domain>/` FormRequests (and
  abstract base requests); how controllers catch domain exceptions and call `$e->render($request)`.
- **GraphQL** — any parallel resolver/type surface for the same capability.
- **Persistence** — `Model/`, `Repositories/`, and which `database/migrations` are relevant; current schema.
- **Domain primitives** — `Entities`, `ValueObjects`, `Factories`, `Collection`, `Specifications` in play.
- **Async & side effects** — `Jobs/` (queues), events/listeners, `Notifications/`, `Services/`.
- **Conventions to follow** — naming, structure, error handling, the validation split (FormRequest vs handler).
- **Exact signatures** of anything tasks will call, extend, or implement.
- **Scope-affecting constraints** — a needed migration, a breaking change, an external dependency.
- **Test terrain** — which syntax the repo uses (Pest if `vendor/bin/pest` exists or composer's `test` script
  runs pest, else PHPUnit), which `tests/Behavior/` vocabulary already exists (`{Domain}ScenarioTrait`
  builders, `{Domain}AssertionsTrait`), the existing test files nearest this area — so tasks name vocabulary to reuse
  instead of inventing it — and that the test database is `:memory:` SQLite (`phpunit.xml` / `tests/Pest.php`):
  a file-backed test DB would make the implement skill's parallel test runs collide, so name it here.

Have each subagent **return its structured findings** into the conversation, and draft the plan (Step 3)
directly from them — don't persist a separate map file. The useful content lands in the task bodies, and the
drafted plan is what survives a context clear. (If context clears mid-mapping on a large change, re-map.)

### Step 3 — Draft the full plan

Draft the **entire** plan into `.ai/<TICKET>/backend-plan.md` from `assets/backend-plan-template.md`. You
draft the whole thing before review (Step 4) because a DAG can't be judged piecemeal — the developer needs to
see the shape to react to it.

- **Foundational tasks first — but only *genuinely shared* seams.** A migration, value object, interface, or
  API/GraphQL contract earns its own foundational task when **two or more tasks depend on it** (or the contract
  must be locked before parallel work starts). A seam only one task uses belongs *inside* that task — don't
  extract it. Keep each foundational task **cohesive**: one seam with one nameable purpose ("`reservations`
  table + `Reservation` model"), never a batch-by-layer grab-bag ("all migrations", "all value objects"),
  which shatters a feature across tasks and is miserable to review. Ordering is by dependency; each task is
  still a logical unit of work you can name by its purpose.
- **Make each task self-contained.** Header lines first — `**Status:**` (`not_started` unless real prior
  work exists, evidenced in an **Existing work** line), `**Depends on:**`, `**Satisfies:** R2` (or `A2`) —
  then the flat `- [ ]` list of atomic steps with files/classes named inline (see the operating principle),
  then optional one-line `**Out of scope:**` / `**Sanity-check now:**` / `**Tests:**` trailers. Self-contained
  means independent of other tasks' *plan entries* — when a task builds on a dependency, point to what that
  dependency creates (the implementor reads its real code) rather than re-pasting its contract.
- **Name what proves each behavior-bearing task — the `Tests:` trailer.** It is what lets the implementor
  verify its own work instead of handing you a guess, so a task without one is a task nothing can check.
  A task qualifies when it adds or
  changes behavior per `skunexus-behavior-testing`'s quick decision table (new command, plugin on an existing
  command, state transition, vendor handler override, factory/interface override, GraphQL field/type, REST
  endpoint, field resolver); a pure migration, config-only, refactor or docs task doesn't and gets no trailer.
  Every qualifying task carries one line — `**Tests:** <test file path> — "<falsifiable proposition>", "<guard
  proposition>"` — the path placed per that skill's layer map — the subject is a command, an endpoint or a pure algorithm,
  so `tests/Feature/<Domain>/<Command>Test.php`, `tests/Feature/GraphQL/…`, `tests/Unit/…` or
  `tests/Integrations/…` as the map says, and often an **existing** file (a plugin, transition, override or
  resolver proves itself in the upstream command's file) — the propositions **quoted from the acceptance
  the task `Satisfies`** (`Rn` from the PRD, or `An` from the inline Goal & Acceptance), not re-invented.
  A task whose only proof is out-of-suite (auth/CSRF/throttle, a live worker, a connector sandbox) gets no
  trailer; its `Sanity-check now` line says so. The
  propositions are **not** checkbox steps (status stays derived from the steps alone), and a test is **never
  its own task** in the DAG — a red test task could never be `finished`. *When* the trailer is discharged is
  `skunexus-backend-implement`'s business (its testing mode decides), not the plan's.
- **Wire the DAG.** Each task's `depends_on`; then derive the **execution waves** (wave 1 = no deps; wave N =
  depends only on earlier waves) so parallelism is obvious to a human and an implementor.
- **Declare the Frontend-facing surface — the intended seam, not the handoff.** Name the public surface this
  DAG introduces — endpoints/resolvers and any FE-relied-on events, one line each with method + auth — so the
  developer can review the plan's public shape and a later FE-handoff step has an *intended* baseline to
  reconcile the real diff against. Stop at the surface: the full request/response/error shapes are the as-built
  handoff's job, produced post-implementation from the real code, not here. "None — backend-internal change"
  if there is none.
- **Scale the structure (proportionality).** A one- or two-task change collapses the manifest (a two-node DAG
  isn't worth a table), omits empty sections, and never spawns `decisions.md`. Don't impose a ten-task
  scaffold on a two-task change.

Then **self-review** before showing anything: is every requirement covered by ≥1 task? does every task trace
to one (or is it justified scaffolding)? is the graph acyclic? could an agent run each task from its own entry plus its
dependencies' real code, without reading another task's entry? is every step one atomic, verb-first action
naming its concrete file/class inline — no prose walls, no "see above", no placeholder ("add validation",
"handle errors") without the specific failure and exception named? does every qualifying task carry a
`Tests:` trailer naming a real test file plus its propositions? is every `Rn`/`An` covered by at least one
proposition across those trailers? Fix gaps now.

**Seed `decisions.md` only if planning produced a genuine decision** — apply the bar in "The decisions log"
below. If nothing clears it, don't create the file.

### Step 4 — Manifest-first review, then developer self-review of the document

1. **Present the manifest first** — the Task Manifest table (IDs, `depends_on`, `Satisfies`) and the execution
   waves. Ask the developer to react to the *structure*: a missing foundational task, a dependency that
   shouldn't exist, two tasks that should merge or split, wrong ordering. The tasks are *ordered* by
   dependency, but the `Satisfies` column lets you read the same table *by requirement* — scan it to confirm
   every `Rn`/`An` is covered. Structural ripples are cheap to fix here, before any detailed reading. (For a
   tiny collapsed plan, just present the one or two tasks.)
2. **Then hand the document over for self-review** — the developer reads `backend-plan.md` in their own
   editor; do NOT walk the task bodies through the chat (re-pasting the deliverable clutters the context
   window and is slower to read than the file itself). Name the handoff explicitly ("read the plan; come
   back with issues at any altitude, or approve") and, when it helps, point at the two or three tasks
   carrying the most design weight. Then wait.
3. **Process the reported feedback per task, then sweep the DAG for ripples.** For each issue: do a
   targeted look at the affected code surface if you haven't seen it in this context window (never edit from
   imagination), then apply the edit. **Changing a task isn't finished until you've swept the tasks it's
   wired to.** From each changed task, walk the `depends_on` edges in *both* directions — every task that
   depends on it (downstream: the contract, signatures, or seam it produces may have moved) and every task it
   depends on (upstream: it may now need something the dependency doesn't yet produce) — and decide, for
   each, whether it needs a matching edit. Follow the ripple transitively: a swept task that itself changes
   triggers a sweep of *its* neighbours, until the graph is consistent again. A change to a later task that
   ripples back to an earlier one is normal — nothing is locked, so nothing has to be un-locked.
4. **Re-surface every task you touched *or* reviewed, each with an explicit verdict.** Report both the tasks
   that changed ("changed — <what and why>") *and* the connected tasks you checked but left alone ("reviewed,
   no change needed — <why it still holds>"), so the developer can tell a deliberately-cleared task from an
   overlooked one — a silent sweep is indistinguishable from no sweep. Keep unresolved items in **Open
   Questions**. Loop (developer re-reads → reports → you fix) until the developer approves.

### Step 5 — Handle contract drift inline (whenever it arises)

If the developer pushes back on significant functionality or adds something that arguably belongs in the
contract, decide *with them, in this thread* what it is:

- **A product requirement / scope change?** → it belongs in the contract. If there's a `prd.md` and the change
  is **contained**, patch it directly (add/edit the `Rn`, add a one-line changelog note under the status),
  confirm, and carry on. If it's a **large rewrite**, spawn a subagent to apply it to `prd.md` so the planning
  thread isn't derailed. If the contract is an inline Goal & Acceptance block, edit it in place. **Never block
  planning** waiting on this.
- **A technical choice with a real fork?** → not a contract edit; it's a `decisions.md` entry (the contract
  stays at product altitude — *what/why*, not *how*).
- **Just a planning detail?** → handle it in the plan and move on.

### Step 6 — Approve

Single global gate. When the developer **explicitly approves**, flip `Status: Draft` → `Approved` and save.
Deliberately-deferred items stay in Open Questions, each with a one-line "why". Then **stop** — the plan is
ready for the implementation skill. Do not start coding.

## The backend plan structure

Always produce these sections, in this order (full template with per-section guidance:
`assets/backend-plan-template.md`). Keep the shape identical across tickets so the implementation skill and
human reviewers always know where to look — collapsing or omitting a section for a small change is fine, but
don't reorder.

1. **Goal & Acceptance** — *only when there's no `prd.md`* (the inline-spec door). Otherwise omitted; the
   contract is the PRD.
2. **Overview** — 2–4 sentences: the technical approach and which surfaces are touched. Not a task list.
3. **Task Manifest (the DAG)** — the table (ID, task, `depends_on`, `Satisfies`) + execution waves. *Reviewed
   first.* Collapsed for a one/two-task plan.
4. **Tasks** — detailed, in dependency order; each self-contained: `Status` / `Depends on` / `Satisfies`
   header lines, then flat `- [ ]` atomic steps (files/classes inline), then optional one-line
   `Out of scope` / `Sanity-check now` / `Tests` trailers (the last on every behavior-bearing task).
5. **Frontend-facing surface (intended)** — one line each for the public surface this DAG introduces
   (endpoints/resolvers/events): the intended seam a later FE-handoff step reconciles against, *not* the
   as-built handoff (full request/response/error shapes come post-implementation, from the real diff).
   "None — backend-internal change" if there is none.
6. **Open Questions** — live tracker during planning; only deliberately-deferred items at approval.

## The decisions log (`decisions.md`)

A durable, ADR-style record of the *why* behind key technical choices — the rationale the code can't reveal
and the contract shouldn't carry (it sits below product altitude). One **shared** file per ticket: this skill
seeds it, the implementation skill appends to it, the PR-description skill reads it. Template:
`assets/decisions-template.md`.

**Created only when a decision earns it.** Log an entry only when **all three** hold:

1. there was a **real fork** — a credible alternative was actually on the table;
2. the rationale is **not obvious** from the code or the contract; and
3. someone later would genuinely **ask "why was it done this way?"** — costly to reverse, surprising, or it
   deviates from convention.

Do **not** log naming, formatting, the obvious idiomatic Laravel choice, "added validation", routine file
placement, or anything that merely restates a requirement. A log's value is inversely proportional to its
noise — two real decisions get read; twenty trivial ones get skipped and bury the two that mattered. If
nothing clears the bar, the file should not exist. **Empty is the normal outcome.** When a decision is later
reversed, append a superseding entry ("D4 supersedes D2 because…") rather than editing — the change of mind
is itself worth keeping.
