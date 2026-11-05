---
name: skunexus-contract
description: >-
  Build and own the contract of a SkuNexus (SN) client ticket in .ai/TICKET/: prd.md (rules and decisions, in
  skunexus-jira-prd's template) plus workflows.md (use cases and the PO's priced parts). It grounds them in evidence
  on disk, hardens them with a review panel, changes them only through rulings on feedback.md, and versions them so
  every view knows when it is stale. Runs as a named workflow; a plain "/skunexus-contract FFD-17" asks one question
  to pick it. Use when the developer asks for "PRD, storyboard and estimate for FFD-40" (workflow
  prd-storyboard-estimate: this skill first, then skunexus-backend-plan and skunexus-storyboard, chained); "I'm away:
  run FFD-17 without stopping" (workflow unattended: a draft with defaults); "a quick storyboard, no PRD" (workflow
  lite-storyboard: a lite contract, then skunexus-storyboard); "re-pull FFD-14 and diff it" (re-pull); "triage
  FFD-17" (triage: rule the scope-bearing guesses of a stopped unattended run, then a storyboard draft for discussion); "rule on the feedback", "freeze / approve the contract", "what is stale"; or, for
  a ticket that already has contract files (workflows.md, feedback.md, research/ or review/po-baseline.md), "the
  ticket changed" or "continue FFD-40" when the first missing or unfinished artifact is the evidence, prd.md,
  workflows.md, the review panel or an open feedback.md entry (without them, these belong to the skill that owns
  the ticket's files). Do NOT trigger for a plain "let's start PHG-439", "write a PRD for X" or a PRD interview on
  its own (skunexus-jira-prd does it; this skill only seeds that interview inside a chain), for planning or "plan it, fan out to subagents" (skunexus-backend-plan), for drawing,
  republishing, the FE plan or the estimate (skunexus-storyboard), or for implementing code.
argument-hint: "<TICKET> [workflow=<name>] [plan-fan-out=on]"
---

# SN ticket contract: evidence → prd.md + workflows.md → rulings → versions

**Two front doors, chosen by one question: must the PO see and price it before it is built?** Yes: `/skunexus-contract <TICKET>`, this skill: it owns `run.md`, asks the workflow question, and drives the chain, calling `skunexus-jira-prd` for the interview, `skunexus-backend-plan` for the plan and `skunexus-storyboard` for the drawing, each at its turn. No: `/skunexus-jira-prd <TICKET>`, the regular route, unchanged.

The contract is the single source of truth for what a ticket's feature does: `prd.md` (rules in §4 and §6, decisions in §7) and `workflows.md` (use cases and parts), backed by evidence on disk. Every other output (storyboard, BE plan, FE plan, estimate, code) is a **view** that adds binding, never behaviour. This skill writes and changes the contract; it never plans or draws. The model behind it (ids, file formats, versions, staleness, gates, the chain rule and workflows, running agents) is `references/model.md`; read the section a step names.

**Why.** A storyboard looks finished even when it rests on guesses, so nothing is shared, priced or built on a guess nobody can see. This skill lays the foundation first: the evidence on disk, the PO baseline, every open item decided or marked as an assumption, and parts in the PO's shape. That investigation is where errors were caught (the stock-page capture caught one the panel repeated), and the storyboard it feeds is 6–10% of a run's tokens. An unattended run stops at an internal draft and a ranked decision list; only a version the developer has triaged is shared, as a draft for discussion. The evidence, and what pilots must still show: model.md "Why".

**Per-ticket values.** Resolve them once and record them in the memory note. Briefs list only their extra placeholders.

| Placeholder | Source |
|---|---|
| `<TICKET>`, `<DATE>` | The ticket key; today as YYYY-MM-DD |
| `<T>` | `.ai/<TICKET>/` in the client repo |
| `<REPO>`, `<REPO_SLUG>` | The git root (`git rev-parse --show-toplevel`); the main checkout's `~/.claude/projects/` folder name: `dirname "$(git rev-parse --path-format=absolute --git-common-dir)"` with every character other than a letter or digit replaced by `-` |
| `<CLIENT>`, `<PO>`, `<TECH_LEAD>`, `<FE_DEV>`, `<DEVELOPER>` | The Projects and People tables in `~/.claude/CLAUDE.md` (the PO is per project; `<DEVELOPER>` is "Me"); else ask the developer once |
| `<JIRA_SITE>` | The cloudId in the repo `CLAUDE.md` Atlassian rules; else ask the developer once for the Jira site URL (it works as a cloudId) and record it in the memory note |
| `<SANDBOX_CALL>` | A read-only script for the client's system named in the repo `CLAUDE.md` Commands section, if it exists on disk; else "none: skip data probes" |
| `<SKILL>` | This skill's folder, as Claude Code reports it on load. Sibling skills sit next to it |

## Step 0: pick the door

1. Get the ticket key (ask if it's missing) and read the disk:
   ```bash
   T=.ai/<TICKET>; ls $T $T/review $T/research $T/prototype 2>/dev/null; ls $T/review/prd-seed-*.md 2>/dev/null
   grep -m1 -i 'status' $T/prd.md 2>/dev/null; grep -A20 '^> Versions:$' $T/prd.md 2>/dev/null | grep '^> - v'
   grep -c '^- \*\*Status:\*\* open' $T/feedback.md 2>/dev/null; grep -rl 'PAUSED' $T --include='*.md' --include='*.html'
   cat $T/run.md 2>/dev/null; python3 -I <SKILL>/scripts/check-contract.py $T
   ```
   A `PAUSED` hit in a `*BRIEF.md` is a pause instruction, not a marker. Read the memory note (model.md §8 defines it): it points, the disk decides.
2. **Workflow** (model.md §8, "Workflows and settings"), first match wins: the arguments (`workflow=<name>`, `plan-fan-out=on`); a trigger phrase; the `workflow` row of `run.md`; otherwise one quick question: the lettered menu A–F filtered by the disk, plus `triage` and `re-pull` when they apply, ending `needs input: …` ("B" is enough). A ticket that needs no prototype (the developer says so, or it is BE-only or integration) gets one line, "No prototype needed: use `/skunexus-jira-prd <TICKET>`, the regular route.", and nothing is written. Then echo it in one line before any work ("Working with workflow `unattended` (unattended draft, then triage): evidence → draft → harden → storyboard v1 → decision list. Unattended; stops at the decision list. Say "workflow <name>" to switch."). Write `run.md` (`workflow` first, then the `mode` and `chain` it fixes) on this skill's first write for the ticket; a switch appends its History line. "let's start X" is not a workflow: hand it to `skunexus-jira-prd`.
3. **Freshness.** Compare the newest `jira-*/` pull and the ticket's live last-updated time with the PRD's last version line (none: its `Source` date). Get the live time with one read-only `getJiraIssue` (`fields: ["updated"]`) under the repo `CLAUDE.md` Atlassian rules, with `<JIRA_SITE>` as the cloudId; without Atlassian, use `jira-summary.md`'s time and say so. If the ticket is newer, say so and offer the re-pull (door 6) before anything reads the contract.
4. **Ownership.** No contract files (model.md §8): name the skill that owns the ticket's files in one line and stop. Otherwise walk §8's table: the first missing or unfinished artifact names its owner. Row 2 during an unfinished seeded interview belongs to `skunexus-jira-prd`, rows 6–9 to `skunexus-backend-plan` or `skunexus-storyboard`: load that skill with `chain: whole`, otherwise name it in one line and stop.
5. Match the ask and the disk to a door. Tell the developer in two or three lines what exists, the door, and what must run first. Don't redo a door whose output exists unless asked: its files are the agreed state.

| # | Door | Opens when | Done when | Reference |
|---|---|---|---|---|
| 1 | Evidence | A new ticket (no `jira/`), or research or a PO baseline is asked for | `jira/`, `jira-summary.md`, `research/R*.md`, `review/po-baseline.md` (or skipped, and said) | `references/evidence.md` |
| 2 | Interview seed | No `prd.md`, attended, and the developer will rule on the decisions (the attended default) | `prd.md` seeded, `review/prd-seed-<DATE>.md`, `skunexus-jira-prd` loaded | `references/interview-seed.md` |
| 3 | Draft with defaults | No `prd.md`, and "I'm away" or "draft it with defaults" | `prd.md` Draft, every open item decided or `(assumed, Qn)`; check OK | `references/draft.md` |
| 4 | Lite | "A quick storyboard, no PRD" | `prd.md` `Draft (lite)`, `workflows.md`, v1 frozen | `references/lite.md` |
| 5 | Harden | `prd.md` exists without `workflows.md` or a `frozen` version: a seeded interview ended (§7 has no interview note with an Open entry, or the developer says it is over), a regular-route PRD, "just the storyboard" on an approved PRD, a lite contract going full | `workflows.md`; check OK; a `frozen` version; the panel synthesis, or the developer skipped the panel | `references/harden.md` |
| 6 | Rulings | Open `feedback.md` entries or an unruled panel synthesis; "re-pull X and diff it", "the ticket changed"; "triage X" (scoped to the triage set) | None open; G1 and G2 recorded (triage: its set ruled, a `frozen` version, the `triaged` History line) | `references/rulings.md` |
| 7 | Version and staleness | An approval to record; an `unversioned change` error; "what is stale" | The version line and its snapshots; `--stale` run per view | `references/versions.md` |

**Modes** (`mode` in `run.md`, fixed by the workflow; stop points and routing in model.md §8). *Attended* (A, B, F) stops at every gate. *Unattended* (E, "I'm away") runs evidence → draft → harden with the lighter panel → storyboard v1 → rulings, applies the recommended options as assumptions, and stops at a Draft with a ranked `review/decision-list-<DATE>.md`: no plan, no estimate, no hours, nothing approved, nothing sent to the PO. *Lite* (C, D) stops after storyboard v1 or the lite contract, internal only. "Triage X" is the follow-up workflow `triage`, not a mode: the developer's later pass through door 6 on a stopped run. A BE-only or integration ticket gets no storyboard.

**The whole chain** (`chain: whole`; workflow `prd-storyboard-estimate`): evidence → seed (attended) or draft (unattended) → harden → discovery (panel ‖ storyboard v1) → rulings → G2 → restart → `skunexus-backend-plan` → `skunexus-storyboard` (v2, FE plan, estimate). `skunexus-jira-prd` stops when its interview ends; "continue <TICKET>" brings the chain back here.

## Rules for every door

Model.md §9 (running agents) applies in full. On top of it:

- **Behaviour moves only through rulings.** Views, the panel and re-pulls file `feedback.md` entries (model.md §6). Only the rulings door decides them and changes their status. An edit outside a ruling is an unversioned change (model.md §5).
- **Freeze before readers.** A panel, a storyboard build or a plan draft reads a `frozen` version's snapshots, never the live files. Edits queue until the readers finish, because reviewers who read a moving file report contradictions that aren't there (FFD-13).
- **Ids are permanent** (model.md §2): never renumber or delete; retire and take the next free id. A `Q` is never deleted: it ends `Decided`. Another ticket's ids carry its key (`FFD-14 R31`).
- **Gates belong to named people** (model.md §7). Present decisions as one lettered list: the ticket- or PO-literal option first, each option tagged `PO decided` / `silence` / `expansion, S/M/L`, a recommendation, and a closing `needs input: …`. Expect terse answers ("A", "yes to all"). Only the developer's explicit yes sets `Approved`.
- **Restart after G2,** and keep the memory note current (model.md §8).

## Roles

The interview stays with the main session (`skunexus-jira-prd`). Every other role is an agent:

| Role | Agent type | Brief |
|---|---|---|
| Puller (intake and re-pull) | `sn-scout` | `assets/briefs/reeval-brief.md`, "Puller prompt" |
| Researchers R1…Rn; a researcher judging this client's own baseline | `sn-scout`; `sn-worker` | `assets/briefs/research-brief.md` |
| B0, B1, baseline synthesizer, deviation checker; B2 | `sn-writer`; `sn-scout` | `assets/briefs/baseline-brief.md` |
| Section drafters D1, D2 | `sn-writer` | `assets/briefs/drafting-brief.md` |
| Use-case drafter | `sn-writer` | `assets/briefs/workflows-brief.md` |
| Panel: V1, V3, simulated personas; V2 | `sn-judge`; `sn-writer` | `assets/briefs/panel-brief.md` |
| Clusterer, panel synthesizer | `sn-writer` | `assets/briefs/panel-brief.md` |
| Source skeptic; code skeptics (a second model family) | `sn-judge`; `sn-scout` | `assets/briefs/panel-brief.md` |
| Editor, checker; fixer | `sn-writer`; `sn-scout` | `assets/briefs/rulings-brief.md` |
| Re-pull analysts A1, A3; A2, A4 (code) | `sn-writer`; `sn-worker` | `assets/briefs/reeval-brief.md` |

## Hand-offs

- **Interview:** `skunexus-jira-prd`, unchanged, interviews from the seeded `prd.md`; its Step 0 resumes from §7 (door 2).
- **Planning:** `skunexus-backend-plan` reads the approved contract, or a frozen Draft the developer accepts. `plan-fan-out: on` in `run.md` opens that skill's parallel-drafting door.
- **Drawing, FE plan, estimate:** `skunexus-storyboard`: v1 during discovery once a version is frozen; v2, the FE plan and the estimate after G2.
- **Chain rule** (model.md §8): with `chain: whole`, load the next owner instead of stopping, except at a gate (attended) or at the workflow's stop point. With `chain: stage`, end with one line offering it.

## Guardrails

| Rule | Why |
|---|---|
| No writes to Jira or Confluence, by you or any agent; the developer posts | Repo rule; posted words and figures are the developer's |
| Client sandboxes, client admin UIs and remote DBs are read-only (`<SANDBOX_CALL>`); record counts and value shapes, never PII | They are live client systems |
| Local app and DB writes only when the developer grants them, logged for undo; never run queue jobs or workers | A queued job nearly pushed a shipment to a client's store |
| No images in any context: screenshots go to files, OCR comes first, and visual judgement goes to a short-lived agent that views at most 3 images | Screenshots hold customer data, and an image in a context is re-sent on every later call |
| Persona reviews are labelled "Simulated <Name> review", kept under `review/panel/` (with a `.gitignore` of `*`), and never quoted in the contract or anything sent to others; no profile entries from simulated content | They are not the person's opinion; client repos commit selected `.ai/` files |
| `jira/` and `jira-summary.md` are never overwritten; a re-pull writes dated files | The diff needs its baseline |

## Writing for the developer and the PO

- Lead with the answer, in tables and short prose. Answer the question asked; don't ask about effort.
- One term per concept. Define acronyms on first use. Cite sources by title and date ("the 2026-10-19 tech call", not "the call").
- PO-facing text (questions, the Parts Scope) is plain, with no internal ids, file names or counts. Adopt the developer's rewrites verbatim.
- Questions for the PO are grouped for the developer to take to the daily. Never send them yourself.

## Assets and scripts

| File | Door | Copy to (under `<T>`) |
|---|---|---|
| `assets/briefs/research-brief.md` | 1 | `research/BRIEF.md` |
| `assets/briefs/baseline-brief.md` | 1, 5 | `review/baseline-BRIEF.md` |
| `assets/briefs/drafting-brief.md` | 3 | `review/drafting-BRIEF.md` |
| `assets/workflows-template.md`, `assets/briefs/workflows-brief.md` | 4, 5 | `workflows.md`, `review/workflows-BRIEF.md` |
| `assets/briefs/panel-brief.md` | 5 | `review/panel-BRIEF.md` |
| `assets/briefs/rulings-brief.md` | 6 | `review/rulings-BRIEF.md` (after a re-pull: `review/reeval-<DATE>/APPLY-BRIEF.md`) |
| `assets/briefs/reeval-brief.md` | 1 (Puller prompt only), 6 | `review/reeval-<DATE>/BRIEF.md` |
| `scripts/check-contract.py` | every door | — |

Run the check as `python3 -I <SKILL>/scripts/check-contract.py <T>`, with `--prev <snapshot>` (nothing disappeared) or `--stale <view file>` (what a view must rebuild); `-h` prints the usage. Exit codes are in model.md §5.

Related skills, used rather than duplicated: `skunexus-jira-prd` (`<SKILL>/../skunexus-jira-prd/assets/prd-template.md` and `jira-summary-template.md`, and the interview; not its fetch, which calls `getAccessibleAtlassianResources` and writes no `jira/`), `skunexus-backend-plan`, `skunexus-storyboard`, and `skunexus-behavior-testing` (criteria become test names).
