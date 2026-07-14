---
name: skunexus-jira-prd
description: >-
  Turn a Jira ticket into a developer-approved Product Requirements Document (PRD) by fetching and
  distilling the ticket, then running a relentless clarifying interview before writing the PRD. This is
  the FIRST step of the engineering AI workflow — it runs before any planning, design, or implementation
  skill. Use it whenever the user wants to start work on a Jira ticket, passes a ticket key (e.g. PROJ-123,
  ABC-1234) and wants to understand or scope it, or says things like "let's start TICKET-123", "write a PRD
  for this ticket", "spec out / scope / break down this ticket", "kick off the workflow for X", or "I need
  requirements for X". Trigger even when the user doesn't say the word "PRD" — if they're about to begin a
  ticket and haven't yet nailed down what to build, this skill comes first. Do NOT trigger for pure status
  questions about a ticket, or once a PRD already exists and the user wants design/implementation.
---

# Jira → PRD

Produce a Product Requirements Document for a Jira ticket that is **product-level** (what & why, not how),
captures a **shared, unambiguous understanding** between the AI and the developer, and is structured so the
**downstream AI planning/design skill** (and a human reviewer) can act on it directly.

The deliverable is `.ai/<TICKET>/prd.md`, finalized **only after the developer explicitly accepts it**.

## Inputs

The ticket key, e.g. `PROJ-123`. If the user invoked the skill without one, ask for the key before doing anything else.

All artifacts live under `.ai/<TICKET>/` **in the current working repository**:

```
.ai/<TICKET>/
├── jira-summary.md   # the summarizer subagent's distillation; seeds the interview (not a review gate)
└── prd.md            # the living PRD: starts as a skeleton, fills during the interview, ends Approved
```

## Operating principles (read before doing anything)

These are the soul of the skill. The mechanics below serve them.

- **Never infer or guess what the ticket means.** The entire point is to reach *common understanding*, not a
  plausible-sounding document. Any time you would assume a value, a boundary, a default, or an intent — stop and
  ask instead. A confident wrong assumption is the most expensive thing this skill can produce.
- **Surface the unstated; don't only clarify the stated.** Two kinds of gap become questions here. *Ambiguity* —
  the ticket says something unclearly — gets resolved. *Silence* — the ticket never addresses something a change
  of this kind must handle (an error path, an edge input, an affected surface, an interaction with existing
  behavior) — gets surfaced. Silence isn't a decision; it's usually just an omission, and the omissions nobody
  wrote down are the ones that bite in design and build. So reason actively about what a feature of *this shape*
  ought to cover, then flag where the context is quiet. Raising a gap is not filling it — you still ask, you
  never decide it yourself — which is the same anti-guessing rule applied to what's absent.
- **Interview relentlessly, but adaptively.** Ask one question at a time whenever the answer is genuinely
  ambiguous or consequential — it keeps each answer focused and lets the next question build on it. Batch only
  trivial, tightly-related confirmations. Prefer offering concrete options ("A, B, or something else?") over
  open-ended prompts; it's easier to react than to author.
- **Stay at the requirements altitude.** Probe *what* must be true and *why*, plus technical constraints that
  change scope or feasibility. Do not design the solution — that's the next skill's job. When the developer
  volunteers a "how" idea, capture it as a parked note (see Notes for Design) and steer back to the "what".
- **The PRD is a gate, not a formality.** You do not finish until the developer has read the PRD and explicitly
  approved it. Unresolved items don't get guessed — they become Open Questions.

## Workflow

### Step 0 — Resume check

If `.ai/<TICKET>/` already exists, **default to continuing from disk — do not refetch the ticket.** The two
files on disk are the complete state (this also covers resuming after a context clear): re-read them and give
the developer a one-line state recap (e.g. "summary exists, PRD is a draft with 3 open questions"). Then:

- **If §7 Open Questions still has items:** ask a single lightweight "anything new to fold in before I
  continue?" — then pick up the interview from the next open question. Fold any new context in as you would in
  Step 2; you don't need to re-run the full upfront-context routine.
- **If §7 Open Questions is empty:** there's nothing left to interview. Report the state and the PRD's status
  (Draft or Approved) and stop — wait for the developer to say what they want next (review it, add scope, hand
  off to design). Don't re-interview or re-approve on your own initiative.

**Refetch only when the developer explicitly asks** — e.g. they say the ticket changed since last time.
Refetching re-runs the summarizer (Step 1) and rewrites `jira-summary.md`, which costs a round-trip and can
clobber detail already folded into the PRD, so it's never your own initiative.

**If the folder exists but holds only bug-hunt artifacts** (an `investigation.md` and/or a bug-focused
`jira-summary.md`, no `prd.md`) — the ticket arrived via `skunexus-bug-hunt`'s "feature change request"
verdict. That's not a resume: treat the investigation as upfront context (Step 2 input) and run Step 1
normally — the bug summary doesn't cover requirements, so the summarizer still runs (it overwrites
`jira-summary.md`; the investigation file stays).

If the folder does not exist, create it and proceed to Step 1.

### Step 1 — Summarize the ticket (subagent, separate context)

Spawn a **general-purpose subagent** to fetch and distill the ticket. This runs in its own context window on
purpose: the raw Jira payload (JSON, every field, full comment threads) is noisy and would crowd out the
interview. The subagent returns only a clean distillation.

Spawn it with a prompt along these lines (fill in `<TICKET>` and the absolute repo path):

```
Fetch Jira ticket <TICKET> via the Atlassian MCP and write a distilled summary to
<repo>/.ai/<TICKET>/jira-summary.md following the template at
<skill-dir>/assets/jira-summary-template.md. Steps:

1. Resolve the Atlassian cloudId (getAccessibleAtlassianResources).
2. Fetch the issue (getJiraIssue) requesting all fields and comments.
3. Resolve the IDs of the custom fields whose display names are exactly "Implementation Plan" and
   "Testing Steps" (use the issue/project field metadata or the field-name expansion). Read their values.
   If you cannot resolve a field, note that under "Flagged uncertainties" rather than guessing.
4. Distill into the template sections. INCLUDE: the essence of the description, the Implementation Plan
   field, the Testing Steps field, and only substantive points from comments (decisions, agreements,
   constraints, scope changes). EXCLUDE noise: assignee, reporter, priority, status, labels, sprint,
   story points, watchers, timestamps, "+1"/status-ping comments.
5. In "Flagged uncertainties", list everything ambiguous, contradictory, underspecified, or missing — the
   things a developer would have to ask about before building, including things a change like this would
   normally need to address that the ticket simply doesn't mention (error paths, edge inputs, affected
   surfaces, interactions with existing behavior). Be specific.

Write the file. Then return ONLY: the ticket title, a 2–3 sentence gist, and the bulleted list of
flagged uncertainties. Do not return the raw ticket.
```

### Step 2 — Prompt for upfront context (while the subagent works)

Don't sit idle while the subagent runs. Ask the developer, in your own words, whether there's anything they
want to share before you both dig in — for example: agreements or decisions made outside Jira, prior context on
this ticket, known constraints, or initial ideas on how they'd approach it. Make clear this is optional.

Hold their answer. Agreements/constraints will become Requirements or Non-Goals; "how" ideas become parked
Notes for Design. (Don't write `context.md` — the two-file model means this gets synthesized into the PRD.)

### Step 3 — The interview

This is the core of the skill. Goal: drive every consequential ambiguity to resolution so the PRD reflects
genuine shared understanding, not your best guess.

The summary from Step 1 is already saved to `jira-summary.md` — it's an input to the interview, not something
the developer has to sign off on. Orient them in a sentence if it helps ("I've read <TICKET> — it's about X; a
few things to pin down"), then go straight to questions. Any misread or stale detail in the summary surfaces
and gets corrected *through* the questions — resolving ambiguity is exactly what this step is for — so there's
no separate summary-review checkpoint.

**Seed the open-questions list** from the summarizer's flagged uncertainties plus anything unclear in the
upfront context. Create `prd.md` now from `assets/prd-template.md` (a living document), and keep the real
working list in its **§7 Open Questions** so progress survives a context clear.

Before working the list, **map the territory**: what does a change of this shape normally have to get right —
the surfaces it touches, the inputs it must handle, the existing behavior it could disturb? Read the context
against that map. Where the context is *vague*, you have an ambiguity to clarify; where it's *silent* on
something the map says matters, you have an omission to surface. Both feed the open-questions list — so the list
should grow beyond the summarizer's flags, not just confirm them. Keep this proportionate: a small, well-scoped
ticket warrants a short map; reserve deep edge-case hunting for changes where it actually changes the outcome.

**What to probe** (requirements altitude):
- Ambiguous or undefined terms, values, and boundaries ("recent" = how recent? which states count?).
- Scope edges — what's explicitly in and, just as important, explicitly out.
- Behavior on the unhappy paths: errors, empty states, permissions (when they apply), limits, concurrency.
- Acceptance: how will we know it's done and correct? Push until each requirement is testable.
- Scope-affecting technical constraints (a migration, an external dependency, a breaking change).
- Contradictions between the description, the Implementation Plan, the Testing Steps, and the comments.

**How to run it:**
- Work the list down adaptively — one focused question at a time for anything ambiguous; quick batched
  confirmations only for trivia. As answers land, **promote them into the PRD** (Requirements, Scope,
  Acceptance, Goals/Non-Goals) and clear the corresponding open question.
- When you'd otherwise assume something, ask. When the developer gives a "how", park it and return to "what".
- Keep going until the list is empty, then explicitly ask: *"Here's what I've still got open — anything I've
  missed or gotten wrong before I finalize?"* Don't proceed on your own judgment that it's "probably enough".

### Step 4 — Draft, review, accept

By now the PRD is largely written (you filled it live during the interview). Do a self-review pass first —
check for placeholders, contradictions, vague requirements, acceptance criteria not tied to a requirement, and
any §7 item that's actually unresolved. Then:

1. Present the full PRD to the developer for review.
2. Revise on their feedback — loop as many times as needed.
3. **Only when they explicitly accept**, flip `Status: Draft` → `Approved` and save the final `prd.md`.
   Anything they chose to defer stays in §7 Open Questions with a one-line reason.

Then stop. The PRD is ready for the downstream planning/design skill — do not start designing or implementing.

## The PRD structure

Always produce these sections, in this order (full template with per-section guidance:
`assets/prd-template.md`). Keep PRDs consistent across tickets so the downstream skill and human readers always
know where to look.

1. **Summary** — 1–2 sentences: what's changing and why (no audience framing).
2. **Problem / Why** — the underlying problem / motivation.
3. **Goals & Non-Goals** — desired outcomes + explicit out-of-scope.
4. **Requirements** — numbered R1, R2…, testable "shall" statements. *(Carries weight for the design skill.)*
5. **Scope of Changes** — product-scope: which areas/components are touched, as outcomes (not tasks).
6. **Acceptance Criteria** — BDD-flavored readable bullets, each tied to a requirement.
7. **Open Questions** — live tracker during the interview; only deliberately-deferred items at approval.

Plus an **optional "Notes for Design" footer** — include *only* when the developer shared technical/approach
ideas or scope-affecting constraints to hand off. Omit entirely when there are none.
