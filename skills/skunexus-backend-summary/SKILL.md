---
name: skunexus-backend-summary
description: >-
  Produce (or drift-check and refresh) the per-ticket backend summary — `.ai/<TICKET>/backend-summary.md`,
  a current-state, feature-doc-style record of what the ticket implemented on the backend: business why,
  behavior, data model, backend map with file paths, decisions & gotchas — grounded in the real code of the
  ticket branch (diff vs the base branch scopes the work; prd.md/decisions.md/investigation.md supply the
  why, an interview fills the gaps). These summaries are the baseline the future bigger documentation will
  be built from. Runs on demand at any point — typically before PR creation for the initial draft, and again
  after changes to verify the document still matches the code. Use it whenever the developer wants the
  ticket's backend work summarized or documented: "write the backend summary", "summarize what PHG-418
  implemented", "document this ticket", "backend summary for this branch", "prepare the summary before the
  PR" — and to RE-CHECK an existing summary: "refresh the summary", "verify the summary still matches the
  code", "drift-check backend-summary.md", even in a fresh conversation. Do NOT trigger for: FE handoff
  notes (skunexus-fe-handoff), PR descriptions (skunexus-backend-pr), investigating bugs (skunexus-bug-hunt),
  or "how does X work" questions with no ticket work to document (skunexus-docs-c7).
---

# Backend work → per-ticket backend summary

Turn the backend work on a ticket into `.ai/<TICKET>/backend-summary.md`: a current-state description of
what the ticket implemented and why — **reviewed by the developer in their editor and done only on their
explicit approval**. It belongs to the engineering AI workflow but is not chained to a fixed position:
the developer invokes it on demand, typically once the implementation settles (before the PR) and again
after later changes to verify the document still tells the truth.

These summaries have an afterlife: they are the **baseline for the future bigger documentation** — the
per-feature docs that will one day be aggregated from them. That afterlife drives the two hardest rules:
describe the **current state only** (no changelog, no "was X, now Y" narration — git history owns that),
and keep the **why woven into the description** (a decision worth preserving lives in Decisions & gotchas,
not in a history section).

## The readers — and what that forces

Three audiences, all of whom **can open this repository** (unlike fe-handoff's reader):

- **Team developers** — a colleague (or the author in six months) who wants to know what the ticket did
  without re-reading the diff. File paths, class names, and table names are helpful here, not dead weight —
  cite them.
- **The future documentation effort** — a human or agent aggregating these summaries into feature docs
  long after the ticket's context evaporated. The document must stand alone: feature language first,
  implementation detail second, nothing that requires having been there.
- **Future Claude sessions** — an agent about to touch this customization who needs to understand it
  before changing it. Precision matters more than prose: exact config keys, exact permission names, exact
  state values.

**Backend only.** Domain logic, commands and handlers, API endpoints, GraphQL types, DB, jobs, config,
permissions. The frontend is out of scope entirely — `fe-handoff.md` is the FE-facing document; do not
duplicate or summarize it here.

## Sources of truth

```
.ai/<TICKET>/
├── prd.md              # business intent, scope (may be absent)
├── decisions.md        # the WHY behind forks (may be absent)
├── investigation.md    # bugfix tickets: root cause + verdict (may be absent)
└── backend-summary.md  # THIS skill's deliverable — starts Draft, ends Approved
```

- **The code on the ticket branch is the only authority on the what.** Every behavior, field, rule, and
  path in the document is read from the real code — never from artifact text, which describes intent at
  writing time. When code and artifacts disagree, the code wins, **silently**: document the actual
  behavior and move on — this skill does not audit artifacts for staleness.
- **Artifacts answer the why.** `prd.md` and `decisions.md` give business intent and deliberate scoping;
  `investigation.md` gives a bugfix's root cause and the behavior contract the fix satisfies. Use them
  for What & why and Decisions & gotchas.
- **The diff scopes the work; it is not a source.** The merge-base diff against the base branch tells you
  *which* code to read — then read that code in full on the branch, including untouched neighbors needed
  to describe behavior honestly.
- **The developer fills what nothing else can.** When the why isn't recoverable from artifacts or code,
  **interview — never guess.** A plausible-sounding invented why is worse than no document: it gets
  aggregated into the real documentation later and nobody re-checks it. The document does not ship with
  an unexplained why; ask until it's explained.

Build missing mental models via the `skunexus-docs-c7` skill before writing about platform machinery you
don't fully understand — in SkuNexus, naming isn't the concept and dependencies aren't local.

## Operating principles

- **The ticket's work is the star; core is context, explicitly labeled.** Readers must never mistake
  core-provided behavior for this ticket's work or vice versa. Where core behavior is needed to understand
  the feature, include it under an explicit label — "context from core" in the heading or an inline
  "(core, unchanged)". This keeps the future aggregation into customization docs clean.
- **Current state only.** Describe how it works now. If a non-obvious decision shaped the current form,
  preserve the why in Decisions & gotchas — never as a change narrative.
- **Depth scales with the surface.** A one-endpoint ticket gets a page; a full feature gets the works.
  Omit sections that genuinely have nothing (a ticket with no schema change has no Data model section) —
  but never pad, and never invent sections outside the template.
- **Pending work lives in the document.** Open TODOs — QA pass pending, follow-up cleanup, an open
  business decision — go in the Pending section with an *as of YYYY-MM-DD* date, so the next reader sees
  them on `git pull`. Resolved items are removed, not struck through.
- **No Jira write-backs.** Like the rest of the pipeline, nothing is posted anywhere; the deliverable is
  the file.

## Workflow

### Step 0 — Situate

1. **Identify the ticket and branch.** Branch name is normally the ticket key. For work with no ticket,
   ask for a short slug and use `.ai/<slug>/` (pipeline convention).
2. **Check for an existing `backend-summary.md`.** If one exists, this run is a **drift check** — jump to
   Drift-check mode below. Don't silently overwrite: the file may be hand-edited or already Approved.
3. **Propose the diff base and confirm.** Compute the natural base (normally the merge-base with `dev`),
   state it — "scoping PHG-433 as `git diff origin/dev...HEAD`, 14 files" — and **ask the developer to
   confirm before scanning**. Stacked branches, already-merged work, and hotfix-off-master setups all
   break the default silently; the developer knows which situation this is.

### Step 1 — Scope from the diff, read the code

From the confirmed diff, list the backend surface the ticket touched: migrations, domain objects, commands
and handlers, routes/controllers/FormRequests, GraphQL types, jobs/console commands, providers, config and
`.env` keys, permission entries. Then **read the touched code in full on the branch** — plus whatever
adjacent code is needed to describe behavior truthfully (the plugin's target command, the state machine a
transition hooks into). Broad retrieval sweeps ("every call site of X across the overlays") go to an
Explore subagent; the judgment about what findings mean stays here.

### Step 2 — Recover the why

Read `prd.md`, `decisions.md`, and `investigation.md` where present. Map each piece of implemented surface
to its intent. Whatever remains unexplained — why this feature exists, why this shape and not the obvious
one, why this edge case is handled this way — goes to the developer as **focused interview questions**,
one consequential question at a time, concrete options over open-ended prompts. Batch only trivial
confirmations. Do not draft an invented why while waiting; the section stays unwritten until the answer
lands.

### Step 3 — Write `.ai/<TICKET>/backend-summary.md`

Always this shape — identical across tickets, so readers and future aggregation always know where to look:

```markdown
# <TICKET>: <Title>

Status: Draft
Scanned: <TICKET>@<short-sha> vs <base>@<short-sha>

## What & why
<Business intent and the problem solved, in feature language — from prd.md / decisions.md /
investigation.md or the interview. For a bugfix: what was broken, what correct means now.>

## Behavior
<Rules, triggers, flows, edge cases — how it works now. Feature language first; a reader who
never opens the code should understand the feature from this section alone. Core-provided
behavior needed for understanding appears here explicitly labeled as core context.>

## Data model
<Tables, columns, custom fields (with codes), migrations — with types, nullability, FKs and
their cascade behavior. Omit the section if the ticket touched no schema.>

## Backend map
<Where everything lives, with file paths: domain entities/VOs, commands + handlers, plugins and
what they attach to, endpoints (method + path + FormRequest + command), GraphQL types, jobs and
schedules, providers, config/env keys with defaults, permissions and what they gate.>

## Decisions & gotchas
<The non-obvious, each with its why: shapes that look wrong but are deliberate, constraints
inherited from core, scoping decisions ("no bulk endpoint — decided against"), traps for the
next developer.>

## Relations
<Other tickets/features this touches or builds on — other .ai/<T>/ docs, core features it
plugs into, sibling customizations.>

## Pending
<Open TODOs as of YYYY-MM-DD — QA pending, follow-up cleanup, open business decision. Omit the
section entirely when nothing is pending.>
```

Style:

- Real names in backticks: routes, classes, config keys, permission names, enum/state values. Paths as
  `app/Domain/.../File.php` — clickable and greppable.
- Tables for field lists, endpoint maps, and config keys; prose for behavior and why.
- **API depth is adaptive.** Default: signature + purpose + key validation rules + gating permission per
  endpoint — `fe-handoff.md` remains the payload reference, link it in Relations. Only when **no
  `fe-handoff.md` exists** for the ticket, inline full ready-to-use request/response examples so the
  summary is self-sufficient.
- English, like every pipeline artifact.

### Step 4 — The review gate

Tell the developer the draft is at `.ai/<TICKET>/backend-summary.md` and hand off — they review in their
editor, not via a chat walkthrough. Iterate on feedback in the file. The summary is **done only on
explicit approval** — then flip `Status: Draft` → `Approved`. That's the end of this skill's job; nothing
is handed downstream automatically.

## Drift-check mode (existing summary)

The `Scanned:` line records what code state the document last described. On a rerun:

1. **Re-derive the facts.** Diff from the recorded scan baseline to the current branch state; re-read the
   code behind every affected claim in the document.
2. **Present the discrepancies first.** Before touching the file, show the developer what no longer holds
   — "doc says the job runs hourly, code now schedules it every 5 minutes", "endpoint gained a `reason`
   field", "doc has no mention of the new permission" — and what you intend to change.
3. **Update facts only.** Correct what the code contradicts, add surface the diff introduced, remove what
   was deleted. **Never restructure or reword prose that is still accurate** — the file may be
   hand-edited, and a gratuitous rewrite destroys the developer's diff.
4. **Record the new scan baseline.** Update `Scanned:`. Any substantive change flips `Status:` back to
   `Draft` for re-approval; a clean drift check ("nothing diverged") changes nothing and says so.
