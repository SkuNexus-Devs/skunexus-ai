# FE plan: each storyboard page bound to FE work

`frontend-plan.md` is the FE developer's view of the contract (model.md §1): each storyboard page → its components, the backend plan's API calls, validation, the riskiest items and FE hours. It adds binding, never behaviour. Owner: the FE developer, gate G4 (they confirm it or replace it). On FFD-40 and FFD-17 the FE plan was written ad hoc "for the FE developer to confirm or replace"; this door makes that the rule.

## When

After storyboard v2 is current and `backend-plan.md` has its "Frontend-facing surface" (the plan need not be approved yet; if it isn't, the header says so and the plan's hash will mark this file for a re-check). Before the estimate, which reads its FE hours per part.

## Inputs

- the storyboard page and `prototype/artifact.md`: the visual spec, one section per page;
- the contract snapshot named by the page's `BUILT_FROM` (§4, §6, §7, `workflows.md`): what each step must do;
- `backend-plan.md`: the "Frontend-facing surface" and the tasks it names, for the routes, permissions and error shapes; the FE plan calls the plan's API, never invents one;
- the FE code: the client repo's FE overlays and the installed `@skunexus/*` packages (their versions from the client's `package.json`), plus any core FE checkout the developer names. Every claim about a package cites file:line in the installed version;
- the FE developer's own past figures (posted estimate comments the developer points to), for the hours basis.

## Shape (`assets/frontend-plan-template.md`)

- **Header:** `> Status: Draft for the FE developer` until G4; `> Built from: contract v<N> (<DATE>) · prototype/artifact.md@<hash> · backend-plan.md@<hash>`; the paths legend.
- **The API the FE builds against:** one row per read or write the pages use: shape, errors, permission, source task (`backend-plan T6`).
- **Approach:** the one or two structural choices (a client page on a stock package, a wrapper, a client copy of a package), with the alternative and why.
- **Pages: one section per storyboard page, keyed by step id** (`### s1.3 · Order details: no serial, Create Fulfillment`). Every live step whose trigger is `user` gets a section (model.md §1 coverage); a step with another trigger gets one only when the FE shows something for it, and otherwise one line under "No FE work". Each section: Cites · Components · API calls · Validation and messages · FE items.
- **FE items `FE<n>`**, numbered across the file, each defined once under the first page that needs it (later pages cite it): what, files (new ones bold), the part, hours as a range. Work no page owns (lint and build, a walk-through, a shared helper) goes under "Shared", part `shared`.
- **FE hours per part:** `| Part | FE items | FE hours |`, one row per live part plus `shared` and `total`. An item's part is its step's `workflows.md` Part. The estimate copies this table.
- **Riskiest items:** the one or two places the high end exists for, with the evidence.
- **Basis and not included:** the FE developer's comparable figures; implementation only (no review, stage verification or QA support).
- **Questions for the FE developer:** technical choices only, numbered, each naming its `FE<n>`.

## Rules

- **Binding only.** A page that needs behaviour the contract lacks (a message the contract doesn't word, a state no step has, an API the plan doesn't offer) is a `feedback.md` entry, source `FE plan` (model.md §6), not an FE item. A technical choice that changes no behaviour (which package hook, a client copy or a core prop) is a question for the FE developer.
- **Ids.** FE items are `FE<n>`, never `F<n>` or `FB<n>`. Sections cite step ids and contract ids; the plan's tasks are cited as `backend-plan T5`.
- **Hours** live here (FE, the FE developer's to confirm) and in `estimate.md`, never on the storyboard or in the contract.
- **G4.** The developer relays the FE developer's answer. Confirmed: `> Status: Confirmed <DATE> (FE developer)`. Replaced: `> Status: Replaced <DATE> (FE developer)` and their figures go into the FE hours table, with the draft's kept below under "Draft figures". Never ask the FE developer directly and never post for them.
- **Stale.** `python3 -I <CONTRACT_CHECK> --stale frontend-plan.md`: rewrite only the sections whose step ids are listed, the API rows when `backend-plan.md` changed, and the hours table rows those touch; then refresh the header's version and hashes. A rewrite that changes any section or hours row sets the status back to `> Status: Draft for the FE developer (re-check: contract v<N>)` and G4 is asked again; a hash-only refresh, such as after a republish, keeps it.

## Run

Copy `assets/briefs/frontend-plan-brief.md` to `.ai/<TICKET>/FE-PLAN-BRIEF.md`, fill it, and run one `sn-worker` (it reads FE code). It writes `frontend-plan.md` and appends any behaviour gaps to `feedback.md`. Check its reply: every `user` step has a section, the hours table sums, every API call names a plan task. Then the estimate door; G4 is asked together with G3 and G5.

The hash in the header is the first 8 hex characters of the file's SHA-256 at build time: `tr -d '\r' < prototype/artifact.md | sha256sum | cut -c1-8` (CRLF read as LF, model.md §5).
