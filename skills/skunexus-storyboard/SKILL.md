---
name: skunexus-storyboard
description: >-
  Build the PO-facing views of a SkuNexus (SN) ticket's contract: the clickable storyboard artifact (the "RMA
  mock-up" format, a private claude.ai artifact drawn on captured stock SN pages), the frontend plan
  (frontend-plan.md) and the hours estimate per part (estimate.md). Reads prd.md and workflows.md from
  .ai/TICKET/ (written by skunexus-contract) and backend-plan.md (skunexus-backend-plan). Use when the user asks
  for a mock-up, mockup, workflow artifact, storyboard or prototype for a ticket ("similar to the RMA one", "PRD
  and plan are done, just build the storyboard": workflow storyboard-only; a plain "/skunexus-storyboard TICKET"
  asks the same one workflow question as skunexus-contract), wants a storyboard revised, rebuilt after a contract change or a
  triage (the "Draft for discussion" v1.x), or republished, asks for an FE plan or the estimate for a ticket whose contract exists, or says "continue TICKET"
  for a ticket that already has contract files (workflows.md, feedback.md, research/ or review/po-baseline.md)
  when the first missing or stale artifact is a storyboard, FE plan or estimate; without contract files,
  "continue" belongs to the skill that owns the ticket's files. Do NOT trigger for: writing or changing
  requirements, use cases or parts (skunexus-contract or skunexus-jira-prd), the backend plan
  (skunexus-backend-plan), the as-built FE hand-off after implementation (skunexus-fe-handoff), or
  implementing code, or for a BE-only ticket or a data contract with no flow anyone walks (no storyboard: the regular route, skunexus-jira-prd); an integration whose flow another team walks gets a storyboard with API call panels.
argument-hint: "<TICKET> [workflow=<name>] [plan-fan-out=on]"
---

# SN storyboard, FE plan and estimate: the views the PO approves

This skill turns an SN ticket's contract into what the product owner (PO) needs to approve scope and price together (gate G6):
- **the storyboard:** one self-contained HTML page that walks each use case, one recreated stock SN page per step, marking what the ticket adds. The PO has asked for "the same" mock-up on every ticket since FFD-14;
- **`frontend-plan.md`:** each storyboard page bound to components, the plan's API calls, validation and FE hours;
- **`estimate.md`:** hours per part, in the PO's shape.

**Why.** A storyboard looks finished even when it rests on guesses, so what the PO sees must be built on the foundation `skunexus-contract` lays: evidence on disk, the PO baseline, stock pages captured rather than guessed, render-ready pages and parts in the PO's shape. Drawing is cheap (capture plus build is 6–10% of a run's tokens) and the capture catches errors a review panel misses. A storyboard has three states: v1 is internal; v1.x, "Draft for discussion", is shared with the PO and the FE developer together, after the developer's recorded triage or, when a call comes first, badged "not reviewed" with a presenter sheet, its open assumptions counted and no price; v2 goes out with the estimate. The evidence, and what pilots must still show: `../skunexus-contract/references/model.md` "Why".

**The model.** This skill needs `skunexus-contract` installed next to it, in the same skills folder. Read `../skunexus-contract/references/model.md` once per session: ids (§2), `workflows.md` (§4), the view header and the stale rule (§5), `feedback.md` (§6), gates (§7), the chain rule (§8) and how to run agents (§9). Each file here is a **view** of the contract. A view adds binding (pages, components, hours), never behaviour. **Drawing never decides:** anything the contract doesn't settle goes to `feedback.md` as `WRONG`, `CHOICE` or `SILENCE`, and comes back only through `skunexus-contract`'s rulings door. This skill never edits `prd.md` or `workflows.md`.

**Per-ticket values.** Resolve them once and record them in the memory note.

| Placeholder | Source |
|---|---|
| `<TICKET>`, `<DATE>` | The ticket key; today as YYYY-MM-DD |
| `<REPO>` | The git root (`git rev-parse --show-toplevel`) |
| `<SKILL>` | This skill's folder (the base directory Claude Code reports when it loads); `skunexus-contract` sits next to it |
| `<CLIENT>`, `<PO>`, `<FE_DEV>`, `<DEVELOPER>` | The project and people tables in `~/.claude/CLAUDE.md`, if present; else ask the developer once and record the answers in the memory note |
| `<LOCAL_APP_URL>`, `<LOCAL_DB>` | The developer's stock local SN app and its local database, from the repo's memory notes (e.g. `http://<client>.test/`); else ask |
| `<SLUG>` | The storyboard's file stem, kept for every version (`prototype/<SLUG>-storyboard.html`) |
| `<VERSION>` | The storyboard's version: v1 is the discovery build, v2 the first PO-facing build (`references/publish.md`) |
| `<BUILT_FROM>` | `contract v<N> (<DATE>)`: the contract snapshot a view was built from (model.md §5) |
| `<CONTRACT_CHECK>` | `<SKILL>/../skunexus-contract/scripts/check-contract.py`. Missing: print `stale check skipped: skunexus-contract not installed` and go on |

## Step 0: find the door

1. Get the ticket key; ask if it's missing. Read the folder and the ticket's memory note (model.md §8; a pointer, never the source):
   ```bash
   T=.ai/<TICKET>; ls $T $T/review $T/prototype 2>/dev/null; sed -n '1,/^$/p' $T/prd.md
   ls $T/review | grep -E '^(prd|workflows)-v[0-9.]+-[0-9-]+\.md$'; grep -c 'Status:\*\* open' $T/feedback.md
   cat $T/prototype/artifact.md $T/run.md 2>/dev/null; grep -rl 'PAUSED' $T/prototype $T/*.md 2>/dev/null
   ```
   The newest snapshot is the highest version number, never the newest date. A `PAUSED` hit in a `*BRIEF.md` is a pause instruction, not a marker.
2. **Workflow** (model.md §8, "Workflows and settings"), first match wins: the arguments (`workflow=<name>`, `plan-fan-out=on`); a trigger phrase ("PRD and plan are done, just build the storyboard" is `storyboard-only`); the `workflow` row of `run.md`; otherwise the same one quick question as `skunexus-contract` (the menu A–F filtered by the disk, ending `needs input: …`). The steps before the drawing go to `skunexus-contract` by the chain rule. Echo the workflow in one line before any work ("Working with workflow `storyboard-only` (just the storyboard (PRD exists)): adoption + harden → storyboard v2. Attended; stops at each gate. Say "workflow <name>" to switch."). Write `run.md` on this skill's first write when it is missing; a switch appends its History line. `mode: lite` (C, D) builds v1 only, never v1.x or v2.
3. **Staleness.** For each view on disk (`prototype/<SLUG>-storyboard.html`, `frontend-plan.md`, `estimate.md`) run `python3 -I <CONTRACT_CHECK> --stale <view file>`. Exit 1 makes that view unfinished; exit 3 (no base, e.g. a storyboard built before this skill) counts as current.
4. Pick the door from the ask and the disk. Tell the developer in two or three lines what exists, the door, and what must come first. Don't redo a door whose output exists and is current unless asked.

| Door | When | Needs on disk | Gate | Reference |
|---|---|---|---|---|
| **v1** (discovery, internal) | the contract is frozen, not yet approved; or the developer asks for a first look | `prd.md`, `workflows.md`, a `frozen` version with both snapshots | none: internal; others see it only as v1.x | `references/capture.md`, `references/build.md` |
| **v1.x** (discussion) | the contract's triage cut a version ("triage X"), or a share comes before the triage (a call booked, the PO asks) | a `frozen` version (`BUILT_FROM` names it) and `prototype/sn-baseline.md`; reviewed: `run.md`'s `triaged v<N>` line with the same `N`, every scope-bearing `Q` `Decided`, no `A('FB<n>')` chip left; not reviewed: the badge says so | none: the developer shares it with the PO and the FE developer together, unpriced, with the presenter sheet; errata within 48 hours | `references/build.md` §1, `references/publish.md` "Sharing v1.x" |
| **v2** (PO-facing) | the contract is approved | `> Status: Approved` (G2), its version's snapshots, no `open` entry in `feedback.md` | G6, with the estimate | `references/capture.md`, `references/build.md` |
| **FE plan** | storyboard v2 is current | storyboard v2 + `prototype/artifact.md`; `backend-plan.md` with its Frontend-facing surface | G4 (FE developer) | `references/frontend-plan.md` |
| **estimate** | the plan and the FE plan exist | `backend-plan.md` (G3), `frontend-plan.md`, `skunexus-backend-plan`'s `check-plan.py` | G5 (developer), then G6 (PO) | `references/estimate.md` |
| **rebuild stale** | step 2 found a stale view | the view, its `Built from` version, the newest snapshot | the view's own gate | `references/build.md` "Rebuild stale" |
| **publish** | a build passed its checks; "republish", a visual tweak | the local HTML file | the developer shares v2+ with the PO | `references/publish.md` |

- **A BE-only ticket, or a data contract with no flow anyone walks, gets no storyboard** (model.md §8, routing): say so in one line: "No prototype needed: use `/skunexus-jira-prd <TICKET>`, the regular route." An integration whose flow another team walks gets one, with API call panels (`references/build.md`).
- **Missing contract pieces go back to `skunexus-contract`** (load it; chain rule): no `prd.md` (its evidence, interview-seed or lite door: "a quick storyboard, no PRD" is its lite door, then v1 here); no `workflows.md`, e.g. a regular-route PRD (its harden door); live files that differ from the newest snapshot (`diff -q --strip-trailing-cr` both; its version door freezes them); `open` feedback before v2 (its rulings door). This skill never cuts a version.
- **"Just the storyboard"** with an approved contract and no plan: v2 now, FE plan and estimate after `skunexus-backend-plan`. On an approved PRD with no `workflows.md`, the contract's harden door adopts it and adds the use cases only (rules unchanged), then v1 here; that amendment and the v1 review are approved in one message: one yes, no restart in between, then v2.
- **The PO reacts** (relayed by the developer): append a `CHANGE` entry, source `PO <DATE>` (model.md §6), and hand to the contract's rulings door. After G6 every change is an amendment there, and the estimate is revisited before the PO sees it again.
- **Older storyboards** (no `artifact.md`, or no `BUILT_FROM`): `references/publish.md` "Older storyboards". A republish or visual tweak works on them as they are; a rebuild re-keys them to `workflows.md` step ids first.
- **A door half done:** resume it from its files. `PAUSED` marker: resume its agent warm or restart it cold, per model.md §9.

**Chain.** v2 → FE plan → estimate. With `chain: whole`, go on to the next door instead of stopping; stop at G4 and G5, which are asked in one message with G3 when the plan is still open. After G5 (the developer posted): update the memory note and end the turn with "Start a new session now: `continue <TICKET>`". Otherwise end each door with one line offering the next.

## Roles

| Role | Agent type | Brief |
|---|---|---|
| Stock-page capture (~30 min, one per ticket, uses the one shared browser) | `sn-scout` | `assets/briefs/capture-brief.md` → `prototype/CAPTURE-BRIEF.md` |
| Storyboard build: v1, v2, rebuild (10–20 min, one fresh agent per version) | `sn-worker` | `assets/briefs/build-brief.md` → `prototype/BUILD-BRIEF.md` |
| FE plan drafter (one agent; reads the FE code) | `sn-worker` | `assets/briefs/frontend-plan-brief.md` → `FE-PLAN-BRIEF.md` |
| Estimate drafter | `sn-writer` | `assets/briefs/estimate-brief.md` → `ESTIMATE-BRIEF.md` |
| Velocity probe (read-only git measurement) | `sn-scout` | the probe prompt in `assets/estimate-template.md` "Basis" |
| Visual judgement (≤ 3 saved images, one narrow question, text reply) | `sn-scout` | inline: `references/build.md` "Verify" |

Copy a brief into `.ai/<TICKET>/` under the name shown, fill its placeholders, and give the agent: "Read <path> and do it." Agent types, fresh agents, warm and cold resume, pause and the STATE line: model.md §9. Capture and build stay separate agents: a combined one died with too much in its context. The build agent never publishes; you publish (`references/publish.md`).

## Guardrails

| Rule | Why |
|---|---|
| No writes to Jira or Confluence. The developer posts estimates and shares links | The posted figures and the PO conversation are the developer's |
| Client sandboxes, client dev/stage sites and admin UIs, remote DBs: read-only. Record shapes and counts, never PII | They are live client systems |
| Local app/DB writes only when the developer grants them, logged for undo. Never run queue jobs or workers | A queued job nearly pushed a shipment to a client's live store |
| Images stay out of every context: screenshots and snapshots go to files, work is done from text, visual judgement goes to a short-lived agent viewing ≤ 3 images. An agent that fails after an image entered its context is replaced, never resumed. Ask the developer for file paths, not pasted screenshots | Screenshots of the local app hold customer data, the build works from the text baseline, and an image in a context is re-sent on every later call |
| No hours on the storyboard. FE hours live in `frontend-plan.md`, all hours in `estimate.md`, none in the contract or `feedback.md` | The storyboard goes to the PO and the client; hours are the developer's to post |
| Fake data only on the storyboard. Raw captures stay in `prototype/screens/` and are never published | The local app holds customer records |
| Publish from the local file, never from an `Artifact read` copy | A read-back copy is not byte-identical to the file you published |
| Views append to `feedback.md` and never edit an entry, `prd.md` or `workflows.md` | Behaviour moves only through the contract (model.md §6) |

## Writing for the developer and the PO

- Lead with the answer, in tables and short prose. One term per concept; define acronyms on first use; cite sources by title and date.
- PO-facing text (storyboard captions, part cards, estimate Scope) is plain and free of file names and counts. Part names and Scope are the contract's words, copied verbatim; to reword them, change `workflows.md` through `skunexus-contract`, then re-copy.
- Decisions for the developer come as lettered options, the PO-literal one first, each tagged `PO decided` / `silence` / `expansion, S/M/L`, ending with `needs input: …`. Expect terse answers ("A", "yes to all").

## Assets and scripts

| File | Door | Copy to (under `.ai/<TICKET>/`) |
|---|---|---|
| `assets/briefs/capture-brief.md`, `assets/sn-baseline-template.md` | v1, v2 | `prototype/CAPTURE-BRIEF.md`, `prototype/sn-baseline.md` |
| `assets/briefs/build-brief.md`, `assets/storyboard-skeleton.html` | v1, v2, rebuild | `prototype/BUILD-BRIEF.md`, `prototype/<SLUG>-storyboard.html` |
| `assets/briefs/frontend-plan-brief.md`, `assets/frontend-plan-template.md` | FE plan | `FE-PLAN-BRIEF.md`, `frontend-plan.md` |
| `assets/briefs/estimate-brief.md`, `assets/estimate-template.md` | estimate | `ESTIMATE-BRIEF.md`, `estimate.md` |
| `scripts/check-storyboard.py` | v1, v1.x, v2, rebuild, publish | — (script syntax, ids, hours, chips vs `QT`, `QT`/`PARTS` drift, step ids vs `workflows.md`, the `STAGE` rules) |
| `../skunexus-contract/scripts/check-contract.py --stale` | every door | — (stale ids per view) |
| `../skunexus-backend-plan/scripts/check-plan.py --plan --sizes` | estimate | — (plan characters per part) |

Run scripts as `python3 -I <path> …`; each prints its usage with `-h`.

Related skills, used rather than duplicated: `skunexus-contract` (the contract, versions, rulings), `skunexus-backend-plan` (the plan and its Frontend-facing surface), `artifact-design` (the page contract; the `Artifact quickstart` result counts as its load, and the storyboard's light-only theme overrides its dark-mode rule), `chrome-devtools` (browser etiquette).
