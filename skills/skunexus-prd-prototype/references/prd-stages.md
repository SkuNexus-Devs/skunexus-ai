# Stages 1–7: from ticket to approved PRD

Read the section for the stage you're entering. The PRD and `jira-summary.md` templates and the approval gate come from `skunexus-jira-prd` (`<SKILL>/../skunexus-jira-prd/`); this file adds the orchestration around them. Agent prompts live in `<SKILL>/assets/briefs/`.

Contents: §1 Intake · §2 Evidence triage · §3 PO baseline · §4 Interview · §5 Section drafting · §6 Deviation check + panel · §7 Rewrite + approval · §8 PRD conventions

## §1 Intake

**Goal:** every input on disk before anyone asks the developer anything.

1. Pull the **whole** ticket with the "Puller prompt (stages 1 and 12)" in `assets/briefs/reeval-brief.md`, target `jira/`. "Not just the summary" is the developer's standing request. Don't use `skunexus-jira-prd`'s fetch: it calls `getAccessibleAtlassianResources` and drops timestamps.
   - Layout (stages 3 and 12 read it): `jira/description.md`, `jira/comment_<author>_<date>.md`, `jira/inventory.md` (fields, changelog with timestamps, attachment list, last-updated), `jira/linked/`, `jira/attachments/`.
   - The puller obeys the repo `CLAUDE.md` Atlassian rules (cloudId, project key, maxResults), never writes, and never Reads images (OCR first).
   - A copy of the ticket in another ticket's `linked/` folder is a snapshot: pull fresh and diff against it.
2. Write `jira-summary.md` from the `skunexus-jira-prd` template, adding:
   - a "Connections to <related tickets>" section (sibling tickets in the same client folder, and precedent tickets the developer names, e.g. LO-58, DPP-202). For a precedent in another client's repo, read that repo's `.ai/<KEY>/` and code; if this repo's `CLAUDE.md` restricts Jira to one project key, ask before reading another project's Jira;
   - the ticket's **last-updated time**.
3. List `input/` and send the developer a **"please provide"** list before fanning out: call transcripts, Basecamp posts, attachments that failed to download. FFD-14 fanned out before the call transcript was in `input/`, and two agents had to be relaunched.
4. Write the `prd.md` skeleton (template from `skunexus-jira-prd`). Seed §7 with the open questions, the architecture-changing ones first. Skip this step for a storyboard-lite (SKILL.md): its `requirements-lite.md` owns the Qn.

**Gate:** the "please provide" list. Optional upfront-context questions can be asked while agents run.

## §2 Evidence triage

**Goal:** answer from evidence whatever evidence can answer, so the interview only settles real decisions.

- Copy `assets/briefs/research-brief.md` to `research/BRIEF.md`. Give each researcher (R1…Rn) its own Q-ids, and one narrow researcher per external reference (another client's implementation, the core package, the sandbox data).
  - Run reference-implementation and data researchers as `sn-scout`; a researcher that judges this client's own baseline (FFD-35 R3) as `sn-worker`.
  - A browser walkthrough of another client's app is the costliest agent type (FFD-35 R2: 292 turns, 6% of the run). Give it a fixed page list tied to Q-ids. Grant a write walkthrough only for a named decision the code can't settle, as a separate fresh agent. Put any per-click guard into one `evaluate_script` helper that guards, clicks and reads in one call.
- Data probes are read-only. Run client CSVs and the client sandbox (`<SANDBOX_CALL>`), and record counts and value shapes. One read-only probe showed a requirement's premise false in 261 of 261 shipped orders.
- The main agent reads only the description and the PO's own documents. Agents read the rest.
- Verify every claim that will shape a requirement yourself, even when two agents agree. Fold each answer into §7 as **evidence → proposed default → who decides**.

## §3 PO baseline

**Goal:** know what the PO actually decided, as distinct from what Claude drafted or the developer chose. The PO's own desired-state doc and description are a stronger signal than a meeting transcript. Alternatives can still be argued, but against a clear baseline.

**When:** before the interview, whenever the PO wrote a desired-state doc or a substantial description. Skip it for a thin ticket and say so. Running it after the interview (FFD-14) overturned the premises of eight requirements the next day and cost a full rewrite.

**How:** copy `assets/briefs/baseline-brief.md` to `review/baseline-BRIEF.md`:
- B0 reads the transcript only. With no transcript, skip B0.
- B1 builds the delta across call, doc, description and comments (without a transcript: description, PO doc and comments), including a sequencing table and authorship tells.
- B2 covers prior client context.
- A synthesizer writes `review/po-baseline.md` from B0–B2 and the primary sources, **not from `prd.md`**.

Then check the top PO quotes against the source verbatim, and re-check any paraphrase that shapes a decision.

**Output:** PO decisions in their own words (PO-n), contradictions as questions with options (X-n), the silences, and "facts the PO may not have had".

## §4 Interview

**Goal:** settle only the real decisions, with each option carrying the PO's position and the data.

| Rule | Why |
|---|---|
| One decision per turn: a short evidence paragraph or table, lettered options, a closing `needs input: …`. Batch trivia as numbered confirmations ("answer 'yes to all' or correct any") | Numbered text questions worked. A 4-question tool batch was rejected with "clarify" |
| Ticket- or PO-literal option first, then the options neutrally | The developer follows the ticket text and the PO's stated assumptions. Evidence-backed recommendations were overridden 9 times out of 11 |
| Tag each option: "PO decided X" / "silence" / "expansion, cost S/M/L" | Untagged larger options were picked unknowingly (15 expansions on FFD-14) |
| Define every acronym and cite each source by title and date in question 1 | "Which 10/19 call?" and "what is SIF?" each cost a round trip |
| Accept business agreements and known small limits over edge-case code ("a few seconds' window", "go-live agreement instead of a switch") | The developer prefers them |
| Capture options the developer invents, word for word | Several requirements came from them |
| Write each answer into `prd.md` at once: "Resolved <DATE> (developer, option B): …" plus the R-ids. Park any "how" in Notes for Design | Progress survives a context clear |

## §5 Section drafting

**Goal:** draft the remaining sections in parallel once §3/§4 are decided.

1. Write the last confirmed answers into `prd.md` first.
2. Copy `assets/briefs/drafting-brief.md` to `review/drafting-BRIEF.md`, with an ownership table: typically D1 = §6 ACs, D2 = §1, §2, §5, the §7 rewrite, the Decision log and Notes for Design. Drafters write only their own file and never `prd.md`.
3. Snapshot `review/prd-pre-assembly.md` and splice the drafts in with a script.
4. Triage each drafter's "Notes for the orchestrator" into fixes consistent with the decisions (apply them) and real gaps (P1…Pn). Ask about the gaps while the panel runs.
5. Run `scripts/check-prd.py prd.md`. Any AC drafted before a late §4 change must be re-checked against its R.

**Gate:** the real gaps P-n answered.

## §6 Deviation check + panel

**Goal:** surface edge cases, silent assumptions, contradictions and false code claims before anything is estimated. The panel flags; the developer decides. Pattern: `~/.claude/rules/multi-agent-perspective-review.md`.

1. **Freeze** `prd.md` as `review/prd-<VERSION>-<DATE>.md` (the header's version, v1 if none) and queue edits until the synthesis.
2. **Deviation check** (when a baseline exists): classify every R, Non-Goal and baseline row into `review/deviations.md` (`review/baseline-BRIEF.md`, deviation checker). A deviation is a confirm-or-change item for the PO, not a defect.
3. **Panel** (copy `assets/briefs/panel-brief.md` to `review/panel-BRIEF.md`, or use `assets/panel-workflow.js` if the user opted into a workflow). Each reviewer gets one perspective. Pick 4–6:
   - always the code fact-checker (red team; hunts "nothing exists" claims), the traceability auditor (R↔AC both ways, recounts) and the simulated PO (the PO/PM from the project table in `~/.claude/CLAUDE.md`);
   - then, as the ticket warrants: the tech lead, the FE developer (if there is UI), the backend reviewer, a big-picture reviewer (unified behaviour, a truth table), and the developer (no profile; use the "Me" section of `~/.claude/CLAUDE.md` and the repo style guide). Personas come from `~/.claude/people/`. FFD-14 ran 6, FFD-13 ran 5.

   Hand the panel any storyboard drawing questions and the storyboard file as inputs. The FE persona cites it for FE-contract gaps.

   **Resume:** a reviewer file is complete when it ends with its "Confirmed OK" section. Re-run only the incomplete reviewers: pass only those in the workflow's `args.roles`/`args.personas` (always pass `roles`, `[]` when V1–V3 are complete), and list the complete reviewer files in `args.done` so the clusterer still includes their findings. With every file complete, the workflow goes straight to clustering.
4. **Synthesis:**
   - cluster the findings;
   - verify each cluster where the top score is ≥ 50 or two reviewers raised it, and log the rest as skipped with a reason;
   - run source and code skeptics;
   - write `review/panel-synthesis.md` in the order the brief gives.
   
   Spot-check the top claims yourself. Zero refutations can mean lenient skeptics.
5. **Gate:** bring the developer the decision list (PD-n) and the developer and tech-lead items (I-n/J-n). Apply the recommended defaults for the rest as assumptions; don't re-interview.

**Pitfall:** panels drift toward more structure (a five-part estimate was rejected). Keep the PO's estimate shape.

## §7 Rewrite + approval

**Goal:** apply the rulings without losing any interview decision, and prove it mechanically. When the main context is heavy, delegate.

1. The §6 snapshot `review/prd-<VERSION>-<DATE>.md` is the backup of the version being replaced. Copy `assets/briefs/rulings-brief.md` to `review/rulings-BRIEF.md` and fill it:
   - apply every E-n;
   - give each panel Q-n the next free §7 Qn (record the mapping, `panel Q-3 → Q21`) and write each Qn/J-n default into its requirement, with a §7 line "Assumed: confirm with <PO> (Qn)";
   - keep ids stable and requirements at product altitude;
   - mark PO contradictions "developer choice, confirm with <PO>";
   - the status stays Draft.
2. **Editor** (one agent) writes `prd.md` in 2–3 chunks and returns the ambiguous calls it made.
3. **Checker** (never the author) works from a v-old → v-new diff, so no interview decision is lost. It returns BLOCKING / SHOULD-FIX / NIT items, each as an exact old → new string.
4. **Fixer** applies them in file order.
5. Run `scripts/check-prd.py prd.md --prev review/prd-<VERSION>-<DATE>.md` (the §6 snapshot).
6. **Gate:** give the developer the "things that need your eye" list (editor judgement calls, invented mechanisms). That list caught an invented requirement mechanism on FFD-13. Flip `Status: Approved` only on the developer's explicit approval. Pragmatic approval with §7 assumptions still open is fine. In the same message, offer the storyboard alongside the plan if none exists (sequencing: SKILL.md); the PO has asked for one on every ticket since FFD-14. After approval, update the memory note and restart the session before any stage 8–11 agent starts (SKILL.md, "Restart the main session after PRD approval").

**After approval the ticket can still move.** The PO rewrote FFD-13 the day after approval. Stage 12 handles it. Conflicts with recorded decisions go to the daily, never into silent edits. Amending an Approved PRD sets `Status: Draft (amending approved v<N>, <DATE>)` until the developer re-approves.

## §8 PRD conventions (the FFD-14 model)

| Convention | Form |
|---|---|
| Header | `Status:` · `Source:` (every input file) · version line ("v2 <DATE>: applied panel review per review/rulings-BRIEF.md") · references legend · ticket last-updated time |
| §1 Summary | Per the template: what changes and why, in 1–2 sentences. Name the deliverables (plan, estimate, mock-up) in the header's references line |
| Non-Goals | Each carries its provenance ("(<PO>, doc comment <DATE>)") and the Q-n it depends on |
| Terms table | Top of §4: `Term \| Meaning in this PRD \| In <CLIENT>'s words`, each term pointing to its R-id |
| Requirements | `- **Rn** … shall …` under bold subheads; one product rule each; no implementation |
| ACs | `- **Rn.a** Given …, when …, then …` with concrete numbers, negative paths and concurrency ("exactly one succeeds") |
| Assumptions | Inline `(assumed, Qn)` / `(Developer choice, confirm with <PO>: Qn.)`, each with a matching §7 "Assumed: …" line |
| Lifecycle matrix | Rows = actions, columns = statuses, every cell cites the AC that proves it |
| Notes for Design | Parked ideas and constraints for the plan, not decisions: one bold bullet per topic with I-/J- id, R-ids and file:line |
| §7 | Grouped by stakeholder: For <PO>/<CLIENT> (client-facing wording goes through the PO) · For the tech lead (J-n) · External inputs and follow-ups (incl. the storyboard status and drawing decisions (a), (b)…). At approval §7 holds only deferred items, plus a Decision log |
| Wording | Plain, specific, no marketing; one term per concept; no persona attributions; persona content never quoted |
| Other tickets' ids | Key adjacent: `FFD-14 R31`, `FFD-14 R31.a`. `check-prd.py` skips them; a bare id is checked against this PRD |
