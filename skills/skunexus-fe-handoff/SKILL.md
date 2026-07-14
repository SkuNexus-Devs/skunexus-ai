---
name: skunexus-fe-handoff
description: >-
  Produce (or refresh) the FE handoff document for a ticket — `.ai/<TICKET>/fe-handoff.md`, a fully
  self-contained, human-readable map of everything the frontend implementation needs from the
  backend: GraphQL reads, REST write endpoints, auth/permissions, validation and error shapes,
  enums/states, and config-dependent behavior — presented in user-flow order with usage context,
  grounded in the real code of the ticket branch (prd.md/decisions.md supply the why). This is the
  FE-handoff step of the engineering AI workflow — it follows skunexus-backend-implement /
  skunexus-backend-pr. Use it whenever the developer wants handoff notes for the frontend team:
  "prepare the FE handoff", "write the handoff for PHG-418", "what does frontend need from this",
  "FE notes", "document the API for the FE team", "handoff doc" — or at the wrap-up of backend work
  when the feature has a frontend side to build. Also use it to UPDATE an existing fe-handoff.md
  after backend changes ("refresh the handoff", "the endpoint changed, update the handoff"). Do NOT
  trigger for: PR descriptions (skunexus-backend-pr), testing steps (separate skill), implementing
  or reviewing frontend code, or general API documentation unrelated to a ticket's FE handoff.
---

# Backend work → FE handoff

Turn the backend work on a ticket into `.ai/<TICKET>/fe-handoff.md`: the single document from
which the frontend can be built — **reviewed by the developer in their editor and done only on
their explicit approval**. This is the FE-handoff step of the engineering AI workflow: it follows
`skunexus-jira-prd` → `skunexus-backend-plan` → `skunexus-backend-implement` →
`skunexus-backend-pr`. It deliberately does NOT produce testing steps (separate downstream skill)
or restate the PR description — those serve reviewers; this serves builders.

## The reader — and what that forces

The handoff is read by an FE developer and/or an FE AI agent **who cannot open this repository**.
They will never see a controller, a FormRequest, or a GraphQL type class. Two consequences drive
everything:

- **Fully self-contained.** Every contract is inlined: complete example GraphQL operations with
  example responses, full request/response bodies for endpoints, whole enum value lists, exact
  error shapes. A backend file path or class name is dead weight to this reader — the document
  speaks only in HTTP, GraphQL, and feature language. If you catch yourself writing "see
  `OrderDecisionController`", inline what that class does to the wire instead.
- **Human-first, machine-friendly.** The document is ordered by the user's journey through the
  feature, not by API taxonomy. A human reads it top to bottom and understands the feature; an FE
  agent gets every fact it needs in the same pass. An alphabetical endpoint list satisfies neither
  — nobody knows *where* to use an endpoint from its signature alone, so every operation appears
  at the moment the flow needs it, with a sentence of context on what it powers.

## Sources of truth

Everything lives under `.ai/<TICKET>/` in the current working repository:

```
.ai/<TICKET>/
├── prd.md            # feature intent, scope, non-goals (may be absent)
├── decisions.md      # the WHY behind forks — scoping notes FE benefits from (may be absent)
├── backend-plan.md   # how the work was structured (may be absent)
├── pr*.md            # what shipped per PR round (may be absent)
└── fe-handoff.md     # THIS skill's deliverable — one per ticket, evolving across PR rounds
```

- **Artifacts answer the why**: what the feature is for, what was deliberately scoped out ("no
  bulk endpoint — decided against in review"), which flow the PRD actually describes. Scoping
  notes matter to FE: they prevent the frontend from waiting for surface that will never exist.
- **The code is the final authority on the what.** Every route, field, rule, enum value, and
  permission you write must be read from the real code on the ticket branch — never copied from
  plan text, which describes intent at planning time. If artifacts and code disagree, the code
  wins; surface the disagreement to the developer, because it usually means an artifact went
  stale.

Fallback chain when artifacts are absent: the Jira ticket → `git log` → the developer. Never
invent a why or a contract detail — a wrong fact here propagates unchecked, because the reader has
no code to check it against. When something isn't derivable, **ask the developer targeted
questions before drafting**.

## Where the FE-facing surface lives

The platform split you are mapping (verify specifics in code; build missing mental models via the
`skunexus-docs-c7` skill before writing about machinery you don't understand):

- **Reads are GraphQL.** The schema is code-first and query-only — no mutations. Grids
  (`XxxGrid`), detail views (`XxxDetails`), collections, query namespaces (`XxxQueries`), and
  status/enum entities are GraphQL types. Field shaping (aliases, custom-value fields, full-text
  search, access-scoping filters, CSV export) happens per type — read the actual type classes to
  get real field names, types, and filters.
- **Writes are REST.** Route → controller → FormRequest (`rules()` is the validation contract,
  `toCommand()` names the command) → command bus. The FormRequest gives you the exact request
  fields and validation table; the handler and its response give you the success shape and side
  effects.
- **Permissions attach to commands.** The command→permission map lives in `config/skunexus.php`
  under `permissions`; the ACL check runs on the outermost command for HTTP requests. The GraphQL
  read layer does not enforce per-query permissions — authenticated users can query exposed types,
  subject to scoping filters (warehouse access, vendor segregation). Report the *effective*
  behavior per operation: which permission gates the write, what an unauthorized caller receives,
  and what scoping silently filters from reads.
- **Config/env changes behavior.** `config/*` keys and `.env` entries that alter FE-visible
  behavior (toggles, limits, allow-lists) — FE needs to know both states, not the key name.

## Workflow

### Step 0 — Situate

1. **Identify the ticket and branch.** Branch name is normally the ticket key. Collect the
   merge-base diff (`git diff origin/dev...HEAD`) for what this ticket added or changed. The
   handoff runs after backend implementation is complete — if the plan shows unimplemented tasks
   that affect the FE surface, say so and confirm with the developer before describing a moving
   target.
2. **Check for an existing `fe-handoff.md`.** If one exists, **ask the developer: full rewrite,
   or rescan-and-update?** (Semantics of update mode below.) Don't silently overwrite — the file
   may have been hand-edited or already shared with FE.
3. **Establish scope.** The handoff covers **everything the FE flow needs** — including
   pre-existing endpoints and GraphQL types the feature reuses — with what's new or changed in
   this ticket clearly flagged. The diff tells you what's new; the PRD and the code tell you what
   the flow touches beyond the diff.
4. **Recap and confirm.** One short recap — "branch PHG-418, decision endpoint + grid type are
   new, the flow also reuses the existing order details query; no existing handoff" — then confirm
   scope with the developer before writing.

### Step 1 — Reconstruct the user flow

From `prd.md` (or the ticket, or the developer), lay out the feature as the user experiences it:
what loads first, what each interaction triggers, what happens after. Each step will own the
operations it uses. Features that aren't journey-shaped (a pure export, a webhook) still get a
logical order — trigger → processing → result. If the flow is ambiguous, ask the developer; they
know the feature, and a wrong flow order makes every subsequent section confusing.

### Step 2 — Derive every contract from code

For each operation the flow touches, read the real code and extract:

- **Reads**: the GraphQL type's actual fields (name, type, nullability), available filters,
  sorting, pagination; then write a complete example query *as FE would send it* and a realistic
  example response. Example values come from the code and config (real status strings, real
  formats) — plausible-looking invented data is the failure mode to avoid.
- **Writes**: method + path, a complete example request, the field-by-field validation table from
  the FormRequest rules, the success response, and each error the FE must handle — the 422 shape
  with a real example, the 403 (and which permission causes it), 404, business-rule rejections.
- **Side effects FE must reflect**: status transitions, rows appearing/disappearing from grids,
  counters changing — the things FE re-fetches or updates optimistically.
- **Enums and states**: full value lists with meaning, and which transitions the UI can trigger.
- **Auth/permissions and scoping** per operation, as effective behavior.
- **Config-dependent behavior**: what FE sees in each config state.

Flag every operation: **NEW** (this ticket introduced it), **CHANGED** (what exactly changed —
FE may have existing code against the old shape), or existing/unmarked.

### Step 3 — Write `.ai/<TICKET>/fe-handoff.md`

```markdown
---
ticket: PHG-418
scanned: PHG-418@<short-sha> vs dev@<short-sha>
status: draft
---

# <Feature name> — FE handoff

<One short paragraph: what the feature does for the user, from prd.md. Orientation, not a spec.>

## The flow at a glance
<Numbered journey. Each step names the user action and the operations it uses, linking to the
sections below. This is the table of contents that carries meaning.>

## 1. <Flow step — e.g., "Operator opens the decision grid">
<A sentence of context: what happens here, what FE calls and why.>
### Read: `orderDecisionGrid` — **NEW**
<inline example query, example response, fields/filters worth explaining, auth & scoping>
### Write: `PUT /order/{id}/decision` — **NEW**
<example request, validation table, success response, error responses, side effects>

## 2. <next step> …

## Reference
<GraphQL endpoint + auth mechanics stated once; enum/status tables; config-dependent behavior;
an operations index table: operation, kind, NEW/CHANGED/existing, flow step it belongs to.>
```

Style:

- Real names in backticks: fields, routes, GraphQL types, enum values, config keys.
- Tables for validation rules, enum values, and the operations index; prose for flow and context.
- **Depth scales with the surface.** A one-endpoint change gets a one-step flow and a page; a
  full feature gets the works. No padding, no invented sections.
- Honest scoping notes from `decisions.md` — what FE should *not* wait for.
- **Never include**: UI/UX prescriptions (FE owns their design — say what an operation powers,
  not how to render it), testing steps, backend internals (commands, handlers, plugins, class
  names) — describe their wire-visible effects instead.

### Step 4 — The review gate

Tell the developer the draft is at `.ai/<TICKET>/fe-handoff.md` and hand off — they review in
their editor, not in a chat walkthrough. Iterate on feedback in the file. The handoff is **done
only on explicit approval** — then flip `status:` to `approved`. Delivery to the FE team is the
developer's job; this skill's job ends at the approved file.

## Update mode (existing handoff, developer chose rescan-and-update)

The scan baseline in the frontmatter (`scanned:`) tells you what code state the document last
described — diff from there to now. Then **update facts only**:

- Correct only content the code now contradicts: a changed field, a new validation rule, a
  removed enum value, a different error shape. Update the flag on operations that changed
  (**CHANGED** with what changed).
- Add new surface where the flow demands it; mark removed surface as removed rather than silently
  deleting sections FE may have built against.
- **Never restructure or rewrite prose that is still accurate** — the document may be hand-edited
  and already in FE hands; gratuitous rewording destroys their diff.
- Record the new scan baseline in the frontmatter and flip `status:` back to `draft` until the
  developer re-approves.
