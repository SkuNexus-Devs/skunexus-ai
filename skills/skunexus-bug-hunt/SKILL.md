---
name: skunexus-bug-hunt
description: >-
  Investigate a bug-like ticket or a reported misbehavior down to a developer-approved, evidence-backed
  verdict — confirmed bug (with a proposed fix), feature change request in disguise, works as designed, or
  cannot-confirm-statically — via a relentless clarifying interview plus static code/docs/git investigation.
  This is the BUG entry point of the engineering AI workflow: it runs INSTEAD of skunexus-jira-prd when the
  work item is a defect report rather than a feature, and it hands off to the planning/implementation skills
  once the verdict is approved. Use it whenever the developer reports something broken, wrong, or regressed:
  "investigate PHG-456", "this looks like a bug", "X throws an error / returns the wrong value / stopped
  working", "orders are stuck in status Y", "QA found this", "why does X behave like this — it used to do Z",
  or when they describe an issue together with a suspected fix ("the bug is probably in <file>, we just need
  to…"). Trigger for bug-flavored Jira tickets AND for issues described directly in chat with no ticket at
  all. Also trigger to RESUME an existing investigation ("continue the investigation for PHG-456", any
  mention of an investigation.md draft), even in a fresh conversation. Do NOT trigger for: scoping a feature
  (skunexus-jira-prd), implementing an already-diagnosed and agreed fix (skunexus-backend-implement),
  planning an agreed fix (skunexus-backend-plan), or pure "how does X work" curiosity with nothing broken
  (skunexus-docs-c7).
---

# Bug report → Investigated verdict

Turn a bug-like ticket or a described misbehavior into `.ai/<TICKET>/investigation.md`: an evidence-backed
**verdict** plus — when it really is a bug — a **proposed fix** and the **acceptance** the fix will be
measured against, finalized **only after the developer explicitly approves it**. This is the bug entry point
of the engineering AI workflow: it runs *instead of* `skunexus-jira-prd` for defect reports, and the approved
investigation hands off to `skunexus-backend-implement` (trivial fix), `skunexus-backend-plan` (complex fix),
or back to the standard feature flow (`skunexus-jira-prd`) when the "bug" turns out to be a change request.

This skill **diagnoses and proposes — it never implements, and it never plans**.

## Inputs — two doors

- **Door 1 — a Jira ticket key** (e.g. `PHG-456`): fetch and distill the ticket in the background, then
  interview.
- **Door 2 — a described issue**: the developer explains the problem in chat, sometimes with a suspected fix.
  First ask whether a Jira ticket exists for it — if yes, offer to fetch it too (Door 1 applies on top); if
  no, ask for a short slug to name the folder (`.ai/<slug>/`).

All artifacts live under `.ai/<TICKET>/` (or `.ai/<slug>/`) **in the current working repository**:

```
.ai/<TICKET>/
├── jira-summary.md    # Door 1 only: the summarizer subagent's bug-focused distillation
└── investigation.md   # THE DELIVERABLE — the living investigation: starts Draft, ends Approved
```

## Operating principles (read before doing anything)

These are the soul of the skill. The mechanics below serve them.

- **Never guess, never infer — ask.** Better to ask too much than to assume once. A confident wrong diagnosis
  is the most expensive thing this skill can produce: it sends the fix skills at the wrong target and the
  real bug ships anyway. Any time you would assume a value, an expected behavior, an environment detail, or
  an intent — stop and ask the developer instead. This applies at every step, not just the intake interview.

- **The verdict is earned by evidence, not by plausibility.** Every claim in the investigation carries its
  source: a `path/file.php:123`, a commit SHA, a documentation passage, or a developer answer. Keep observed
  facts and hypotheses visibly separate — a hypothesis promoted to fact without evidence is guessing wearing
  a lab coat. And never force a verdict to look finished: when the evidence genuinely runs out at the static
  boundary, "cannot confirm statically" **is** the honest verdict, not a failure.

- **Static investigation only.** Read code, build the mental model through the `skunexus-docs-c7` skill, do
  git archaeology (`log`, `blame`). Do NOT run migrations, tinker, endpoints, or DB queries — environment
  truth belongs to the developer, the same honesty rule the implementation skill lives by. When a fact is
  only knowable at runtime (a config value on the install, what a row actually contains, whether the job
  ran), formulate the **exact check** for the developer to run — a query, a log to pull, a repro step —
  and treat their answer as evidence like any other.

- **Bug vs. not-a-bug is a judgment about intent — and intent leaves traces.** A defect is behavior that
  diverges from what the code was *built* to do; a change request asks to alter what it was built to do.
  You can't tell them apart from the symptom alone, so hunt for the intent: the commit and ticket that
  introduced the behavior, a recorded decision in a past ticket's `decisions.md`, the platform docs, the
  ticket history. "It surprised the reporter" is not evidence of a defect.

- **Backend-first, FE-aware.** The investigation targets the backend (domain logic, commands, API, GraphQL,
  DB, jobs). If the evidence shows the defect lives on the frontend side, don't refuse and don't go dark:
  say so, and document what the backend contract actually does (with evidence) so the FE side has something
  concrete to work against.

- **Diagnose and propose — at "what to change, where" altitude.** The proposed fix names the files, classes,
  and behavior to change and why that's the right layer. One recommended fix; alternatives only when a
  genuine fork exists (a credible alternative with real tradeoffs). No task breakdown — that's the planning
  skill's job. No code — that's the implementation skill's job.

- **Proportionality: the fast lane exists.** When the developer describes a trivial issue *and* its fix,
  your job shifts from hunting to **verification** — confirm their diagnosis against the real code instead
  of re-deriving it from scratch. Verification is not rubber-stamping (their fix is a hypothesis like any
  other), but it earns a short investigation, not the full ceremony.

- **The investigation is a gate, not a formality.** You do not finish until the developer has read
  `investigation.md` and explicitly approved it. Unresolved items don't get guessed — they become Open
  Questions or the fourth verdict.

## Workflow

### Step 0 — Resume check

If `.ai/<TICKET>/investigation.md` already exists, **default to continuing from disk — don't refetch or
re-hunt what's already established.** Re-read it (and `jira-summary.md` if present) and give a one-line state
recap (e.g. "investigation is a Draft, verdict pending, 2 open questions — one waiting on a log check from
you"). Then:

- **Verdict pending or Open Questions remain:** ask a light "anything new since last time — did you run the
  checks?", fold answers in as evidence, and continue the hunt from where it stopped.
- **Draft with a verdict:** the review gate (Step 5) is where you are — hand the document over for review.
- **Approved:** report the verdict and the recommended handoff, and stop — wait for the developer to say
  what's next. Don't re-investigate or re-approve on your own initiative.

Refetch the ticket only when the developer explicitly says it changed. If the folder doesn't exist, create
it and proceed to Step 1.

### Step 1 — Intake (two doors)

**Door 1 — ticket key.** Spawn a **general-purpose subagent** to fetch and distill the ticket. This runs in
its own context window on purpose: the raw Jira payload is noisy and would crowd out the investigation. Spawn
it with a prompt along these lines (fill in `<TICKET>` and the absolute repo path):

```
Fetch Jira ticket <TICKET> via the Atlassian MCP and write a distilled BUG summary to
<repo>/.ai/<TICKET>/jira-summary.md following the template at
<skill-dir>/assets/bug-summary-template.md. Steps:

1. Resolve the Atlassian cloudId (getAccessibleAtlassianResources).
2. Fetch the issue (getJiraIssue) requesting all fields and comments.
3. Distill for bug anatomy, from wherever it appears (description or comments): EXPECTED vs ACTUAL
   behavior; steps to reproduce; environment/config context (which install, env values, versions,
   relevant dates); error messages and stack traces VERBATIM (they are evidence — never paraphrase
   them); when it started / suspected trigger; substantive points from comments (workarounds tried,
   related tickets, agreements). EXCLUDE noise: assignee, reporter, priority, status, labels, sprint,
   story points, watchers, timestamps, "+1"/status-ping comments.
4. In "Flagged gaps", list what a developer would have to ask before investigating: missing
   reproduction, ambiguous expected behavior, unstated environment, contradictions between the
   description and the comments. Be specific.

Write the file. Then return ONLY: the ticket title, a 2–3 sentence gist of the reported misbehavior,
and the bulleted flagged gaps. Do not return the raw ticket.
```

While the subagent runs, don't sit idle: ask the developer for upfront context — when the problem started,
recent deploys or related changes, related tickets, their own suspicions, anything already tried. Optional,
but often the fastest evidence there is.

**Door 2 — described issue.** Ask whether a Jira ticket exists for this. If yes, offer to fetch it (run
Door 1 in parallel with the conversation). If no, ask for a short slug for the `.ai/<slug>/` folder. The
description itself is the intake — including any suspected fix, which routes to the fast lane (Step 3).

### Step 2 — Pin down the symptom (the interview)

Never start hunting from an ambiguous symptom — a hunt aimed at the wrong symptom produces a confident
diagnosis of the wrong thing. Before touching code, the interview must establish:

- **Expected behavior** — and *what grounds it*: docs, past behavior, a spec, an agreement? If the reporter
  can't say where the expectation comes from, that's itself a signal the verdict may be "change request".
- **Actual behavior** — concretely, not "it doesn't work".
- **An anchor** — reproduction steps, or at least one concrete instance: an order ID, a timestamp, a log
  line, an environment. Without an anchor, everything downstream is speculation.

Seed the question list from the summarizer's flagged gaps plus anything unclear in the upfront context. Ask
**one focused question at a time** for anything consequential — each answer sharpens the next question; batch
only trivial confirmations. Prefer concrete options ("A, B, or something else?") over open-ended prompts.

Create `investigation.md` now from `assets/investigation-template.md` (a living document) and keep the
working list in its **§6 Open Questions**, so progress survives a context clear. Fill §1 Symptom as answers
land — write it as *agreed in the interview*, not as the ticket phrased it.

### Step 3 — The hunt (static investigation)

- **Model first, then code.** Build the mental model through the `skunexus-docs-c7` skill before tracing —
  in SkuNexus, naming isn't the concept and dependencies aren't local, and bug hunts die on both. Then read
  the real code (client overlay and `vendor/skunexus`/`vendor/smst`/`vendor/wsnyc`) for what actually runs.
- **Trace the causal path.** From the symptom's entry point (route, command, job, resolver) through the code
  that actually executes — handlers, plugins, state transitions, listeners. You are looking for the exact
  place where behavior diverges from intent, not a plausible neighborhood.
- **Do the git archaeology.** `git blame` the suspect lines; find when the behavior appeared and which
  ticket/PR introduced it. A behavior introduced deliberately (commit referencing a ticket, a recorded
  decision in that ticket's `.ai/` artifacts if present) discriminates *works-as-designed* from *defect*
  better than any code reading.
- **Turn runtime gaps into developer checks.** Whatever you can't establish statically becomes a precise,
  executable ask ("run `SELECT … WHERE order_id = 4711`", "pull the queue log for June 3rd", "repro with
  config X off") tracked in Open Questions. Their answers come back as evidence.
- **Use subagents for broad sweeps.** "Find every call site of X across the overlays" is retrieval, not
  judgment — an Explore subagent on a cheaper model keeps the noise out of the investigation thread. Keep
  the reasoning about what the findings *mean* in this thread.
- **Keep `investigation.md` current as you go** — §3 Analysis grows with the evidence trail; it's the state
  that survives a context clear, and stale notes mislead the resumed session.

**The fast lane (developer described the fix).** Their diagnosis is a hypothesis to **verify, not accept**:
read the real code to confirm the root cause is what they say it is, and check the fix's completeness —
other call sites, side effects, behavior the change could disturb. If it checks out, write a short
investigation (symptom, verdict, brief evidence, their fix as the proposal) and go straight to Step 5. If it
doesn't, say exactly what doesn't hold and continue the normal hunt — that finding is evidence too.

### Step 4 — The verdict

Exactly one of four. Each has its own bar and its own follow-through in `investigation.md`:

| Verdict | It means | §3 Analysis must show | Then |
|---|---|---|---|
| **Confirmed bug** | Behavior diverges from what the code was built to do | The causal chain from trigger to symptom, each link cited | §4 proposed fix + §5 acceptance (`A1…An`) + complexity read |
| **Feature change request** | The code does what it was built to do; the ticket asks to change that | The traces proving current behavior is deliberate, and what the ask would actually change | No fix proposal; route to `skunexus-jira-prd` |
| **Works as designed** | Deliberate behavior, and the reporter's expectation was misplaced | The design intent with evidence (docs, commits, decisions) | Nothing proposed; the developer decides whether to escalate into a change request |
| **Cannot confirm statically** | The static boundary was reached with competing hypotheses alive | Each hypothesis + the discriminating check the developer can run | A waypoint, not an end: their results loop back into Step 3 |

For a **confirmed bug**, close the loop in the document: §4 names one recommended fix at "what to change,
where" altitude (real forks only — see the operating principle), plus an honest complexity read with the
recommended route — trivial → `skunexus-backend-implement` directly, complex → `skunexus-backend-plan`
first. Recommend; **the developer decides**. §5 states the expected behavior after the fix as testable
`A1…An` bullets — this is the acceptance contract downstream skills trace to.

### Step 5 — Review gate, then handoff

Tell the developer the draft is at `.ai/<TICKET>/investigation.md` and hand off — they review in their
editor, not via a chat walkthrough (the document is the deliverable; re-pasting it burns context). Iterate
on their feedback in the file. **Only on explicit approval**, flip `Status: Draft` → `Approved`.

Then state the handoff and **stop** — do not implement, plan, or start a PRD yourself:

| Approved verdict | Handoff |
|---|---|
| Confirmed bug, trivial fix | `skunexus-backend-implement` (direct road) — the approved investigation is the described change |
| Confirmed bug, complex fix | `skunexus-backend-plan` — tasks trace to the investigation's `A1…An` |
| Feature change request | `skunexus-jira-prd` (the standard feature flow) — the investigation is upfront context |
| Works as designed | Nothing to build; if the developer wants the behavior changed anyway, that's a change request → `skunexus-jira-prd` |
| Cannot confirm statically | The developer runs the listed checks; results reopen Step 3 (approval here just confirms the checks are the right ones) |

## The investigation structure

Always produce these sections, in this order (full template with per-section guidance:
`assets/investigation-template.md`). Keep the shape identical across tickets so downstream skills and human
readers always know where to look.

1. **Symptom** — expected vs. actual, reproduction/anchor, environment — *as agreed in the interview*.
2. **Verdict** — one of the four, one short paragraph of justification.
3. **Analysis** — the evidence trail; every claim cited; hypotheses marked as hypotheses.
4. **Proposed fix** — *confirmed bug only*: one recommended fix, real forks only, complexity + route.
5. **Expected behavior after the fix** — *confirmed bug only*: testable `A1…An` acceptance bullets.
6. **Open Questions** — live tracker during the hunt; at approval, only deliberately-deferred items remain.
