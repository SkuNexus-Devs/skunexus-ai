---
name: skunexus-backend-pr
description: >-
  Draft the backend Pull Request title + description for the current ticket branch and — only after
  the developer explicitly approves the draft — push the branch and create a DRAFT PR on GitHub via
  gh (or edit the existing PR). Grounds every claim in the ticket's .ai/<TICKET>/ artifacts
  (prd.md, decisions.md, backend-plan.md) with the real diff as final authority; detects prior PR
  history for the branch/ticket and proposes describing only the delta. This is the PR step of the
  engineering AI workflow — it follows skunexus-backend-implement. Use it whenever the developer
  wants a PR drafted, opened, described, or re-described: "draft the PR", "write the PR
  description", "open a PR for PHG-418", "describe this branch", "update the PR description after
  the review changes", "redo the PR" — or at implementation wrap-up when the code is approved and
  needs a PR. Do NOT trigger for: FE handoff notes or testing steps (separate downstream skills),
  reviewing someone else's PR, or making code changes (that's skunexus-backend-implement).
---

# Branch → Draft PR

Turn the approved work on the ticket branch into a PR title + description a reviewer can trust —
**reviewed by the developer as `.ai/<TICKET>/pr.md` in their editor before anything reaches
GitHub**. On explicit approval (and only then), push the branch and open a **draft** PR, or edit
the existing one. This is the PR step of the engineering AI workflow: it follows
`skunexus-jira-prd` → `skunexus-backend-plan` → `skunexus-backend-implement`, and it deliberately
does NOT produce the FE handoff notes or the testing steps — those are separate downstream skills,
and writing them here would create two sources of truth.

## Inputs and the source-of-truth hierarchy

Everything lives under `.ai/<TICKET>/` in the current working repository:

```
.ai/<TICKET>/
├── prd.md            # the contract — requirements, scope, non-goals (may be absent)
├── investigation.md  # bug-route diagnosis (skunexus-bug-hunt) — symptom, root cause, acceptance (may be absent)
├── decisions.md      # ADR-style log — the WHY behind every real fork (may be absent)
├── backend-plan.md   # the task DAG — how the work was structured (may be absent)
└── pr.md             # THIS skill's deliverable (pr2.md, pr3.md for later PRs on the same ticket)
```

The hierarchy matters because the artifacts and the code answer different questions:

- **`prd.md` + `decisions.md` are the sources of truth for the *why*** — what problem this solves,
  what was deliberately scoped out, why approach A beat approach B. Scoping notes like "this is
  *not* the full report from the ticket — after discussion we agreed on a simplified internal
  version" come straight from these files; they are exactly what a reviewer needs and exactly what
  a diff can never tell you.
- **On the bug route, `investigation.md` is the primary why-source.** The bug-fix shape's `## Problem`
  comes from its Symptom + Analysis (real failing inputs, the root cause), and the before/after table from
  its "Expected behavior after the fix" bullets. Re-deriving the diagnosis from the diff wastes what the
  investigation already proved.
- **The codebase — the real diff — is the final authority on the *what*.** The artifacts describe
  intent at planning time; code moves. Every behavior, signature, route, and config key you name
  must be read from the diff and the surrounding real code, never copied from plan text. If the
  artifacts and the diff disagree, the diff wins — and the disagreement is worth surfacing to the
  developer, because it usually means an artifact went stale.

Any or all artifacts may be absent (a direct Door-B change leaves no trace but the diff). That's
fine — the fallback chain is: artifacts → the Jira ticket → `git log` commit messages → the
developer. What you must never do is invent the missing why: a plausible-sounding rationale that's
wrong misleads every future reader of the PR. When the why isn't inferable, **ask the developer
targeted questions before drafting** — only the specific gaps, e.g. "why the custom-field label
instead of the orders table?" — and fold the answers in.

When the diff touches platform machinery you don't already understand (command bus, plugins, state
machines, queues), build the mental model first via the `skunexus-docs-c7` skill and the real code.
A PR description that mis-explains a mechanism is worse than one that says less.

## Workflow

### Step 0 — Situate

1. **Identify the ticket and branch.** The branch name is normally the ticket key (`PHG-418`).
   If it isn't recognizable, ask. Confirm the base branch — default `dev` — and that the working
   tree is clean enough to describe (uncommitted work you'd be describing? flag it).
2. **Collect the change.** `git diff origin/<base>...HEAD` (three-dot: merge-base diff, so dev
   merge-commits on the branch don't pollute it) plus `git log --oneline origin/<base>..HEAD` for
   the narrative. Read the artifacts that exist.
3. **Detect PR history** — this determines what "the right description" even means:
   - open PR on this branch: `gh pr list --head <branch> --state all --json number,state,title,url,body`
   - earlier PRs on the ticket: `gh pr list --search "<TICKET> in:title" --state all ...`
   - local rounds: existing `pr*.md` files under `.ai/<TICKET>/`
4. **Recap and propose.** One short recap — "branch PHG-418, 9 commits ahead of dev, PRD + decisions
   present, PR #585 already open (description last matched the code 6 commits ago)" — then propose
   the scope and **ask; the developer confirms or redirects before you draft**:
   - **No PR history** → propose a full description of the branch vs base.
   - **Open PR exists** → compare its current description against the current diff; propose
     precisely what to re-describe ("the endpoint section is stale — response format changed;
     the new console command is undescribed") and what still holds. The updated description must
     read as a coherent description of the PR's *current* state — not a changelog of edits.
   - **No open PR, but an earlier PR on this ticket was merged** → propose a delta-only
     description: this PR describes only the new work, with a one-line reference to the earlier
     round (see the round-2 example in `references/example-prs.md`). Re-explaining already-merged
     work buries what the reviewer actually needs to look at.

### Step 1 — Understand the change

Read the diff against the real files, not in isolation — hunks lie about behavior when you can't
see the surrounding code. From the artifacts, pull the problem framing, scope decisions, and any
recorded fork rationale. Then sweep for the elements that, **when present in the diff, must appear
in the description** (the judgment of "applies here" is yours; looking for them is not optional):

- **Env / config changes** — new `.env.example` entries, changed `config/*` defaults, anything an
  existing installation must update separately. These get an explicit reviewer callout (e.g.
  "customers that override `ORDER_ADDRESS_PO_BOX_TEMPLATES` via env need their value updated —
  only the defaults change here").
- **Migrations / schema changes** — what they create or alter, and anything destructive, slow on
  large tables, or order-dependent.
- **Exercisable behavior** — a bug fix gets a before/after table of real inputs; an endpoint
  change gets a request/response example; a contract change states what error responses did NOT
  change. Concrete examples are what reviewers actually verify against.

If any why-gap remains after artifacts + Jira + commits, ask the developer now — targeted
questions, then draft once.

### Step 2 — Draft `.ai/<TICKET>/pr.md`

File-to-PR mapping is 1:1: `pr.md` is the ticket's first PR, `pr2.md` the second, and so on.
Updating an open PR's description means updating *its* file, not starting a new one. Format:

```markdown
---
title: "PHG-418: report partial-fulfillment orders ready for decision"
base: dev
pr: (filled with the URL once posted)
status: draft
---

<the description body, exactly as it will appear on GitHub>
```

Everything below the closing `---` is posted verbatim — so the developer reviews precisely what
GitHub will show, title included, in their editor's markdown preview.

**Title**: `<TICKET>: <lowercase imperative summary of the outcome>`. State what the change
*means*, not its mechanics — "wait for queued transfer job so 200 means the fulfillment is already
on the packing station cart" beats "add QueuedCommandJob::runAndWait to controller".

**Body — adaptive shapes.** There is a blessed family, not a fixed form; pick the shape the change
actually has and drop what doesn't apply (a brand-new feature has no "Current behavior" — nothing
existed). The shapes, with full annotated examples in `references/example-prs.md`:

| The change is… | Shape |
|---|---|
| A behavior change to something that already works | `## Current behavior` → `## New behavior` — contract examples inline, then the mechanics and their why |
| A new feature / new capability | `## What & why` (problem + scope framing) → `## Changes` grouped by component or seam — never by file |
| A bug fix | `## Problem` (real failing inputs, ideally a table) → `## Fix` (each non-obvious part with its why) → before/after summary table |

Mixing is fine when the change genuinely mixes; inventing sections to look complete is not.

**Depth scales with the change.** Every non-obvious decision a reviewer would trip on gets its
why — the liked examples explain *why the wait lives in the controller and not the handler*
(transaction middleware) and *why `\p{L}` instead of `\w`* (words are runs of letters; digits
aren't word continuations). That depth, when the change carries it. A config-default tweak gets
three lines. No padding either way.

**Style** (calibrate against `references/example-prs.md`):
- Name real things in backticks: classes, routes, commands, config keys, queue names.
- Dense technical prose for reviewers who know the platform; tables and fenced code where they
  carry the information better than prose.
- Honest scoping notes — what this deliberately is *not* — sourced from `decisions.md`/`prd.md`.
- Reviewer orientation when the branch is noisy (dev merged in): it's fine to point at the
  commits that matter.
- **Never include**: FE handoff notes (`## For FE` — separate skill), testing steps (separate
  skill), deployment/release runbooks. Env/config *callouts* stay (reviewers must know); deploy
  *instructions* don't.
- **`pr.md` itself stays wrapped** — it is the file the developer reads in their editor. The
  unwrapping happens on the way out (Step 4), because GFM turns every single newline in a GitHub text
  field into a `<br>`, so a wrapped body renders as ragged, broken lines. Write the file for reading;
  post the body unwrapped.

### Step 3 — The review gate

Tell the developer the draft is at `.ai/<TICKET>/pr.md` and hand off — they review in their
editor, not in a chat walkthrough. Iterate on feedback in the file. **Nothing reaches GitHub
until they explicitly approve** — "looks good, post it" or equivalent. Silence, or approval of
the *code*, is not approval of the PR.

### Step 4 — Post to GitHub

On approval (approval to post covers the push):

1. Push the branch if it isn't on the remote: `git push -u origin <branch>`.
2. **Extract the body unwrapped** with `md-paragraphs.py`, which sits in this skill's own directory
   (the base directory you were given when this skill loaded). `--body` does both halves — drops the
   metadata block and joins every wrapped paragraph into one line, leaving headings, table rows, list
   items, quotes and fenced blocks alone:
   `python3 <skill-dir>/md-paragraphs.py .ai/<TICKET>/pr.md --body > <scratchpad>/pr-body.md`.
   Do it even when the draft looks unwrapped; a body posted with wrapped prose renders a `<br>` at every
   newline and has to be reposted. Never unwrap `pr.md` in place — that is the developer's reading copy.
   Then:
   - new PR: `gh pr create --draft --base <base> --title "<title>" --body-file <file>`
   - existing PR: `gh pr edit <number> --title "<title>" --body-file <file>` — editing never
     changes the PR's draft/ready state, and neither do you (`gh pr ready` is the developer's call).
3. Set nothing else — no assignees, reviewers, or labels; those stay manual.
4. Write the PR URL into the file's `pr:` field and flip `status:` to `posted`, so the file
   remains the local record of what went out.

Then stop: report the URL and note that FE handoff notes and testing steps are the next,
separate skills — don't write them here.
