---
name: skunexus-prd-prototype
description: >-
  Run the SkuNexus (SN) ticket pipeline from any stage, picking up from what is on disk in .ai/TICKET/: Jira pull →
  evidence research → PO baseline → interview → PRD → review panel → rewrite and approval → stock-page capture →
  clickable storyboard artifact (the "RMA mock-up" format, a private claude.ai artifact) → backend plan → hours
  estimate → re-pull and diff. Orchestrates subagents. Use when the user asks for a mock-up, mockup or workflow
  artifact, storyboard or prototype for a ticket ("similar to the RMA one", "PRD and plan are done, just build the
  storyboard"), wants a PRD taken through PO baseline, panel, rewrite and estimate, says "orchestrate with subagents
  … estimate", wants a ticket re-pulled and diffed or the PRD and plan re-evaluated, or wants to continue, revise or
  republish a storyboard. Also use it to resume any ticket whose .ai/TICKET/ holds plan-parts/, prototype/ or
  review/panel/, even on "continue the plan". Not for a plain PRD interview (skunexus-jira-prd), planning alone
  (skunexus-backend-plan), or implementing code.
---

# SN ticket pipeline: PRD → storyboard → plan → estimate

This skill turns a SkuNexus client ticket into what the product owner (PO) needs to approve and price it:

- an approved product requirements document (PRD);
- a clickable storyboard artifact that shows, on recreated stock SN pages, what the ticket adds;
- a backend plan;
- an estimate the developer posts.

It started on FFD-14 (RMA). The PO asked for "the same" mock-up on later tickets, so the storyboard is the deliverable people notice. Everything else exists so the storyboard and the estimate rest on decided requirements.

Each stage writes files under `.ai/<TICKET>/` in the client repo, and each stage reads only files. That is what lets the pipeline **start at any stage**: a fresh session, or a user who already has a PRD and a plan, enters exactly where the disk says the work stands.

**Per-ticket values.** Resolve them once and record them in the memory note. Briefs list only their extra placeholders.

| Placeholder | Source |
|---|---|
| `<TICKET>`, `<DATE>` | The ticket key; today as YYYY-MM-DD |
| `<REPO>`, `<REPO_SLUG>` | The git root (`git rev-parse --show-toplevel`); the main checkout's `~/.claude/projects/` folder name: its path (`dirname "$(git rev-parse --path-format=absolute --git-common-dir)"`, the same as `<REPO>` outside a worktree) with every character other than a letter or digit replaced by `-` |
| `<CLIENT>`, `<PO>`, `<TECH_LEAD>`, `<FE_DEV>`, `<DEVELOPER>` | Projects and People tables in `~/.claude/CLAUDE.md` (the PO/PM is per project; `<DEVELOPER>` is "Me"); else ask the developer once and record the answers in the memory note |
| `<SANDBOX_CALL>` | A read-only script for the client's system named in the repo `CLAUDE.md` Commands section, if it exists on disk (with Docker PHP, use the repo's exec prefix), else "none: skip data probes" |
| `<LOCAL_APP_URL>`, `<LOCAL_DB>` | The repo's memory notes (FFD: `http://skunexus-ffd.test/`; PhpStorm connection `WSL`, schema `skunexus_dev_ffd`), else ask |
| `<SKILL>` | This skill's folder: the base directory Claude Code reports when the skill loads (normally `~/.claude/skills/skunexus-prd-prototype`). The sibling skills it uses sit next to it |
| `<VERSION>` | The PRD header's version, v1 if none (as in `review/prd-<VERSION>-<DATE>.md`); in the build brief, the storyboard's version; in `plan-parts/BRIEF.md` revision headers, the brief's revision (v2, v3…) |

## Step 0: find the entry stage

1. Get the ticket key; ask for it if it's missing. Look at the folder:
   ```bash
   T=.ai/<TICKET>; ls $T $T/review $T/review/panel $T/prototype $T/plan-parts 2>/dev/null
   grep -m1 -i 'status' $T/prd.md $T/backend-plan.md 2>/dev/null; grep -c '<!-- TASKS -->' $T/backend-plan.md 2>/dev/null
   cat $T/prototype/artifact.md 2>/dev/null; grep -rl 'PAUSED' $T --include='*.md' --include='*.html'
   ```
   A `PAUSED` hit in a `*BRIEF.md` is a pause instruction, not a marker. Read the ticket's memory note: `~/.claude/projects/<REPO_SLUG>/memory/<ticket-lowercase>-<topic>.md`, indexed in that folder's `MEMORY.md` (e.g. `ffd-13-sif-hold-prd.md`). It records where the last session stopped. No note (another machine, or never written): the folder is the state; ask for anything only the note would hold (the artifact URL, the local app URL).
2. **Freshness.** Compare the newest `jira-*/`, the newest `review/reeval-*/` and the ticket's live last-updated time with the PRD's last version line (none: its approval or `Source` date, else the file's modified time). Get the live time with one read-only `getJiraIssue` (`fields: ["updated"]`) under the repo `CLAUDE.md` Atlassian rules, because `jira-summary.md` only holds the time of the last pull; without Atlassian, use that time and say so. If any is newer, say so before any stage that reads the PRD (6, 9, 10, 11) and offer stage 12 first.
3. **Older prototypes.** Any `prototype/*.html` with no `artifact.md` and no `prototype/BUILD-BRIEF.md` was made before this skill. A `*-storyboard.html` counts as stage 9 done; before any publish, or for a prototype in another format, follow `references/storyboard.md` §5. With a `BUILD-BRIEF.md` (or a memory note saying "built, not published") it is this skill's unpublished first build: run the check script, then First publish (§5). No URL in the memory note or `Artifact list` means it was never published: do a first publish, but ask the developer first if the PO may already hold a link to an earlier prototype.
4. Match the user's ask to a **target stage** (the table below) and work out which inputs it still lacks. Tell the user in two or three lines what exists, the target, and which earlier stages must run first, and why. Then start. Don't re-run a stage whose output exists unless the user asks; its files are the agreed state.

| # | Stage | Done when (on disk) | Minimum input | Gate | Reference |
|---|---|---|---|---|---|
| 1 | Intake | `jira/` (puller layout), `jira-summary.md` with the last-updated time | ticket key | The "please provide" list | `references/prd-stages.md` §1 |
| 2 | Evidence triage | `research/R*.md`; §7 questions carry evidence and a default | 1 | None; you verify every shaping claim yourself | §2 |
| 3 | PO baseline | `review/po-baseline.md` | 1, plus PO-written text (skip if the ticket is thin) | None; it feeds the option tags | §3 |
| 4 | Interview | `prd.md` §7 has a "Resolved <DATE>" line for every architecture-changing Q; no open Q in §3/§4 | 1 (2 and 3 first when they apply) | Each decision | §4 |
| 5 | Section drafting | every `prd.md` section filled | 4 | The real gaps P-n answered | §5 |
| 6 | Deviation check + panel | `review/panel-synthesis.md` | any PRD, frozen | Rulings on the PD-list | §6 |
| 7 | Rewrite + approval | `prd.md` `Status: Approved` | 6, or approval without a panel | Approval, after "things that need your eye"; then restart the session | §7 |
| 8 | Stock-page capture | `prototype/sn-baseline.md` covers the pages | a requirement source; the local app running | None (the page list is confirmed before capture) | `references/storyboard.md` §2 |
| 9 | Storyboard artifact | `prototype/<slug>-storyboard.html`, URL in `prototype/artifact.md` | a requirement source + 8 | The developer's reaction per version | §3–§6 |
| 10 | Backend plan | `backend-plan.md` with no `<!-- TASKS -->` line left | an approved PRD, a frozen Draft the developer accepts, or the plan skill's inline spec | Plan approval (`skunexus-backend-plan`) | `references/plan-estimate.md` §1 |
| 11 | Estimate | `estimate.md` | 10, plus base hours from the developer | The developer sets the base and posts | §2 |
| 12 | Re-pull + diff | `review/reeval-<DATE>/APPLY-BRIEF.md` applied (the PRD has a version line for <DATE>) | 1 | Top 5 taken to the daily | `assets/briefs/reeval-brief.md` |

**Common entries**
- **"Just the storyboard"** (the PRD exists, any status): after the freshness check, freeze the PRD as `review/prd-<VERSION>-<DATE>.md` unless it is frozen (`diff -q prd.md` against the newest `review/prd-v*-20*.md` shows no difference). Reuse or run the capture (8), then build (9). If `estimate.md` has parts, the storyboard shows them. If not, build a single-part storyboard; priced options the PRD names go in one appendix scenario labelled "priced option, not in base" (ask which, if more than two).
- **Storyboard with no PRD:** offer two routes and let the developer pick.
  - (a) Run stages 1–7 first. Recommend this when the PO also expects an estimate.
  - (b) A storyboard-lite. Run stage 1 steps 1–3 (pull, `jira-summary.md`, the "please provide" list; no `prd.md` skeleton, whose seeded Qn would collide with the lite file's), then write `prototype/requirements-lite.md` in the PRD formats so both scripts work (`check-prd.py --lite`, `check-storyboard.py --prd`): `## 4. Requirements` with `- **R<n>** …` (n = the ticket's own requirement number, noted "Req n in the ticket"), an optional `## 6. Acceptance Criteria`, and `## 7. Open Questions` with `- **Q<n>** …`, each with an "Assumed: <simplest default>" line. Pass it as `<REQ_SOURCE>` to the capture and build briefs, then run 8–9. If a PRD follows, seed its §7 from these Qn with the same ids.
- **"Republish" / a visual tweak** (the header, a label): edit the storyboard directly or through one build agent, run the check script, and publish to the URL in `artifact.md` (none: `references/storyboard.md` §5 first). No pipeline.
- **The PRD or the estimate changed:** re-sync the storyboard's `QT`/`PARTS` copies (`references/storyboard.md` §6) and republish. If the plan exists, list which tasks the change touches.
- **"The ticket changed"** or "before the daily": offer stage 12 rather than run it unasked. It writes only dated files (`jira-<DATE>/`, `jira-diff-<DATE>.md`, `review/reeval-<DATE>/`) and never rewrites `jira/` or `jira-summary.md`. Apply its result only through the developer's rulings: rulings → editor → checker on the PRD (an Approved PRD becomes `Status: Draft (amending approved v<N>, <DATE>)` until the developer re-approves), then re-sync the storyboard (`QT`/`PARTS`) and the `estimate.md` parts, and list the plan deltas. Never silent edits.
- **A stage half done:** resume it from its files; don't restart it.
  - Panel: a reviewer file is complete when it ends with its "Confirmed OK" section. Re-run only the incomplete reviewers (`panel-workflow.js`: pass only those in `args.roles`/`args.personas`, always with `roles` explicit (`[]` when V1–V3 are complete; the script refuses a resume without it rather than re-run V1 and V2), and list the complete files in `args.done` so the clusterer still includes their findings; with every file complete it goes straight to clustering), then synthesize.
  - Plan: `plan-parts/[A-Z]-*.md` exist and `backend-plan.md` is missing or still has `<!-- TASKS -->`: resume at `references/plan-estimate.md` §1 step 5.
  - A `PAUSED` marker: SendMessage the agent if it went idle under ~5 minutes ago; otherwise point a fresh agent of the same type at its file (see "Resume warm, restart cold").

**Sequencing 9 and 10.** Default: start 9, and start 10 when the build agent returns its "ambiguous to draw" list. Run them in parallel only when the developer is short of time; then send the list to the plan drafters as a correction round. Stage 10 needs an approved PRD, or the developer's explicit OK to plan on a frozen Draft (`skunexus-backend-plan` Step 1).

**Offer the storyboard** after PRD approval and with every estimate, if none exists. The PO has asked for one on every ticket since FFD-14.

## How to run every stage

These rules come from what went wrong on FFD-14 and FFD-13. Each reason is in the clause after it.

- **Orchestrate with subagents by default.** The developer asks for it every time. Raw dumps (Jira payloads, code maps, reviews) stay in agent files, out of the main context.
  - Write one shared brief file per fan-out from the templates in `assets/briefs/`, copied to the fixed names in the Assets table.
  - Give every agent the input paths, an output file it alone owns, and a reply cap (15 lines unless the brief sets another). For a long document (the PRD, the plan BRIEF, the maps), name the sections or R-ids the agent needs, so it reads those with `grep -n` and `sed -n`; only roles that review, rewrite or synthesize the whole document read it whole.
  - **Agent type per role.** Spawn every agent with one of these `subagent_type`s, never `general-purpose`. Each type (`~/.claude/agents/sn-*.md`) fixes the model, the effort and a lean tool list. A general-purpose agent starts at 58.7k tokens before reading anything and re-reads them on every turn; on FFD-35 that base was 20% of the run.
    - `sn-scout` (Sonnet): the puller, reference-implementation and data researchers, browser walkthroughs, the capture agent, code mappers, the plan compiler, fixers that apply exact edits (PRD and plan), the plan auditor, B2, the velocity probe, and the code skeptics (a mixed-family jury, per `multi-agent-perspective-review.md` "Upgrades").
    - `sn-worker` (Opus, effort high): plan drafters and design fixers, the plan's code fact-checkers, the storyboard builder (it keeps the CLAUDE.md files its browser checks rely on), R3.
    - `sn-writer` (Opus, effort high, no CLAUDE.md files): the document-only roles: D1, D2, the editor, the checker, V2, B0, B1, the baseline synthesizer, the deviation checker, the clusterer, the panel synthesizer, the estimate drafter. On FFD-40 these roles re-read 2.9M of starting context; skipping CLAUDE.md, the rules and memory takes ~11k tokens off each of their requests.
    - `sn-judge` (Opus, your session's effort): the plan architect, V1, V3 and the simulated personas, the simulated tech-lead plan review, the source skeptic. The interview stays with you.
    - If a type is missing (no `~/.claude/agents/sn-*.md` on this machine), say so and use `general-purpose`, with `model: "sonnet"` for the `sn-scout` roles.
  - Spawn fresh agents told which files to read; don't fork. A fork re-reads your whole context on every one of its turns: on FFD-35 that was ≥0.043M units per turn at the 430k median, against 0.036M per turn all-in for a fresh drafter. Fork only while your context is under ~100k tokens.
- **Restart the main session after PRD approval.** It is a step, not a fallback.
  - When: at the first moment after stage 7 when no agent is running, and again whenever the developer comes back after an hour or more. Background agents report only to the session that launched them, so never restart with agents in flight, and don't launch the next stage's agents first.
  - How: update the memory note (stage, files, open items, next step), then end your turn with "Start a new session now: `/skunexus-prd-prototype <TICKET>`. Step 0 resumes from disk." Start nothing else.
  - Why: the main session re-reads its whole context on every turn. On FFD-40 it mentioned a new session only "if your usage window runs out", then grew from 308k to 486k; restarting at 308k would have saved 1.9M of its 6.6M, the run's largest single item. FFD-35's single 23-hour session re-read a 433k median context on each of its 312 turns.
- **Wait for the completion notice** before reading an agent's file. A file can be on disk before the agent has finished writing it.
- **Verify what shapes a decision.** Check claims against the code (`patches/` before `vendor/`), the ticket or the PO's verbatim words before they reach the developer, even when two agents agree. A synthesizer once turned "please review LO-58" into "Build on LO-58".
- **Freeze before review.** Panels, storyboards and plan drafters read a dated snapshot. Edits queue until the synthesis, because reviewers who read a moving PRD report contradictions that aren't there.
- **Ids are permanent.** R, AC, Q, PD and E ids are never renumbered once cited; retire an id and take the next free one, because the storyboard, the plan and the panel all cite them.
  - Panel Q-n become the next free PRD §7 Qn at the rewrite; record the mapping (`panel Q-3 → Q21`).
  - Prefixes keep the families apart: panel decisions `PD-n`, re-eval changes `RC-n`, checker items `CK-n`.
  - Write another ticket's ids with its key (`FFD-14 R31`); `check-prd.py` skips them.
- **Gates belong to the developer.** Every stage ends at its Gate (the column above). Present decisions as lettered options, with the ticket-literal or PO-literal option first and each option tagged "PO decided" / "silence" / "expansion, cost S/M/L". End with `needs input: …`. Expect terse answers ("A", "yes to all"). After a panel, apply the recommended defaults as assumptions instead of re-interviewing item by item. This overrides `skunexus-jira-prd`'s ask-don't-assume rule at the developer's request; every default is marked `(assumed, Qn)` with a §7 line, so nothing is decided silently.
- **Say real durations up front:** capture ~30 min, a storyboard build 10–20 min, a panel ~45 min, drafters 3–9 min each. The developer plans around them. Name the two bursts before they start, plan drafting (~30% of a run's tokens) and the panel (~17%), so the developer can start them when nothing else needs the usage limit.
- **Resume warm, restart cold.** A subagent's prompt cache lives about 5 minutes; a SendMessage to an agent idle longer re-writes its whole context (on FFD-35, 27 such resumes re-wrote 9.7M tokens, 8% of the run).
  - SendMessage corrections, pauses and follow-ups only while the agent is busy or has been idle under ~5 minutes.
  - Otherwise start a fresh agent of the same type with the role's RESUME text, pointed at its brief and its own file. The `<!-- STATE … -->` line under the file's title carries what isn't in the deliverable yet, and the check scripts (`assemble-plan-parts.py --check-only`, `check-prd.py`, `check-storyboard.py`) catch dropped items.
  - Resume a cold agent only when it holds reasoning that isn't on disk and re-deriving it costs more than the re-write: a 400k agent costs ~0.5M to re-write and then re-reads 400k every turn, while a fresh one starts at ~100–150k.
  - After a usage-limit stop ("You've hit your 5-hour limit · resets …"), wait for the reset, then restart fresh instead of resuming: on FFD-35 six 330–460k agents resumed in the same minute and all hit the 5-hour limit again within 31 seconds.
  - On "pause": tell each agent to finish or stop within 1 minute and leave a marker line containing `PAUSED <DATE>` in its file. The build agent never publishes: it adds a "WIP — PAUSED <DATE>" badge, saves and stops, and you publish (`references/storyboard.md` §5). Update the memory note before you stop.
- **Write the project memory note at every phase boundary** (stage, files, open items, artifact URL, next step). A note that still says "paused" after a resume misleads the next session.
- **Use the Workflow tool only when the user opts in** ("use workflow"). When offering it, say what it adds: the long reviewer reports stay out of the main context, and dedupe and verify routing run as code. The panel has a ready script in `assets/panel-workflow.js` (it needs the `sn-*` agents installed); otherwise run the same panel as parallel Agent calls.

## Guardrails

| Rule | Why |
|---|---|
| No writes to Jira or Confluence, from you or any agent. The developer posts comments and estimates | Repo rule; the posted figures are the developer's |
| External systems are read-only: client sandboxes (via `<SANDBOX_CALL>`), client dev/stage admin UIs and remote DBs. Record counts and value shapes, never PII | They're live client systems |
| Local app/DB writes only when the developer grants them, with every change logged for undo. Never run queue jobs or workers | A queued job nearly pushed a shipment to the client's store |
| Keep images out of every context. Screenshots and snapshots go to `filePath` only; work from text. Visual judgement goes to a short-lived subagent that views at most 3 images. If an agent fails after an image got into its context, start a fresh agent and never resume the dead one. Ask the developer to give file paths, not pasted screenshots | Screenshots of the local app hold customer data, and once an image is in a context every later call re-sends it |
| Persona reviews are labelled "Simulated <Name> review", grounded in `~/.claude/people/`, and never quoted in anything sent to others. Write no profile entries from simulated content. `review/panel/` carries a `.gitignore` of `*`, so persona files never reach a commit | `~/.claude/rules/team-personas.md`; client repos commit selected `.ai/` files |
| No hours on the artifact. Hours live only in `estimate.md` | Developer rule; the artifact is shown to the PO and the client |
| Fake data only on the artifact. Raw captures stay in `prototype/screens/` and are never published | Local data holds customer records |
| Publish artifacts from the local file, never from an `Artifact read` copy | A read-back copy is not byte-identical to the file you published |

## Writing for the developer and the PO

- Lead with the answer, in tables and short prose; answer the question asked, and don't ask about effort (it's set).
- One term per concept. Define acronyms on first use. Cite sources by title and date ("the 2026-10-19 tech call", not "the call").
- PO-facing wording (questions, the artifact, estimate scope) is plain and free of internal ids, file names and counts. The developer may rewrite it; adopt their words verbatim.
- Questions for the PO are grouped for the developer to take to the daily. Never send them yourself.

## Assets

| File | Stage | Copy to (under `.ai/<TICKET>/`) | Use |
|---|---|---|---|
| `assets/briefs/research-brief.md` | 2 | `research/BRIEF.md` | Researchers with owned Q-ids |
| `assets/briefs/baseline-brief.md` | 3, 6 | `review/baseline-BRIEF.md` | PO baseline agents, synthesizer, deviation checker |
| `assets/briefs/drafting-brief.md` | 5 | `review/drafting-BRIEF.md` | Parallel PRD section drafters |
| `assets/briefs/panel-brief.md`, `assets/panel-workflow.js` | 6 | `review/panel-BRIEF.md` | Panel: functional roles + simulated personas; synthesis |
| `assets/briefs/rulings-brief.md` | 7, 12 | `review/rulings-BRIEF.md` | Rulings → editor → independent checker → fixer |
| `assets/briefs/capture-brief.md`, `assets/sn-baseline-template.md` | 8 | `prototype/CAPTURE-BRIEF.md`, `prototype/sn-baseline.md` | Stock-page capture |
| `assets/briefs/build-brief.md`, `assets/storyboard-skeleton.html` | 9 | `prototype/BUILD-BRIEF.md`, `prototype/<slug>-storyboard.html` | Storyboard build |
| `assets/briefs/map-brief.md`, `assets/briefs/plan-brief.md` | 10 | `plan-parts/MAP-BRIEF.md`, `plan-parts/BRIEF.md` | Code mappers; plan drafters |
| `assets/estimate-template.md` | 11 | `estimate.md` | Part · Hours · Scope estimate |
| `assets/briefs/reeval-brief.md` | 1, 12 | `review/reeval-<DATE>/BRIEF.md` (stage 12; stage 1 runs only its Puller prompt) | "Puller prompt (stages 1 and 12)"; impact analysts |
| `scripts/check-prd.py` | 5, 7, 12 | — | Mechanical PRD pass: ids, AC coverage, placeholders, assumptions |
| `scripts/check-storyboard.py` | 9 | — | Script syntax, ids, hours, QT/R-id drift |
| `scripts/assemble-plan-parts.py` | 10 | — | Assemble parts; cycles, waves, AC coverage, mechanism grep. `--check-only` checks `plan-parts/`; once the plan has been edited, check it with `--plan` (the parts go stale) |

Run scripts as `python3 -I <SKILL>/scripts/<name>.py …` (each one prints its usage with `-h`).

Related skills and rules, used rather than duplicated:
- `skunexus-jira-prd`: the `jira-summary.md` and PRD templates (`<SKILL>/../skunexus-jira-prd/assets/`) and the approval gate. Not its fetch: it calls `getAccessibleAtlassianResources`, which repo `CLAUDE.md` files may forbid, and writes no `jira/` folder.
- `skunexus-backend-plan`: plan and decisions templates.
- `artifact-design`: the page contract. The `Artifact quickstart` result counts as its load; the storyboard's Theme row overrides its dark-mode rule.
- `skunexus-behavior-testing`: test conventions that plan briefs must not contradict.
- `/chrome-devtools`: browser etiquette.
- `~/.claude/rules/multi-agent-perspective-review.md` (if present): the pattern behind the panel and the plan review. The briefs carry everything an agent needs from it.
