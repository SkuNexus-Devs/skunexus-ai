<!-- Stage: PRD drafting in parallel sections, once the interview has decided §3 and §4. Copy to .ai/<TICKET>/review/drafting-BRIEF.md and fill it; the per-agent prompts and assembly steps at the end are for the orchestrator.
     Extra placeholders: <TICKET_SUMMARY>, <DECIDED_RANGE> (e.g. R1–R20), <INTERVIEW_DATE>, <STYLE_MODEL> (an approved PRD to copy conventions from, e.g. .ai/FFD-14/prd.md), <TERMS> (the PRD's fixed terms), <RELATED_SOURCES>, <EDGE_CASES> (for D1). Standard placeholders: see SKILL.md. -->
# <TICKET> PRD: drafting brief

## Artifact
`<REPO>/.ai/<TICKET>/prd.md`: the PRD for <TICKET> (<TICKET_SUMMARY>). Status Draft. §3 Goals/Non-Goals and §4 Requirements <DECIDED_RANGE> are **developer-decided** in the interview of <INTERVIEW_DATE>; §7 records each decision with its evidence.

**Do not reopen decided items.** Flag a problem with one only if it is factually wrong, contradictory, untestable or unsafe, and say which of the four.

## Audience
<DEVELOPER> (PRD owner) → <PO> (approves scope and estimate) → <TECH_LEAD> (reviews the design) → <FE_DEV> (sizes the frontend) → the backend-plan step, which cites R-ids and AC-ids.

## Sources of truth, highest first
1. The developer's decisions recorded in `prd.md` §7 and its Decision log.
2. Code in `<REPO>`: `app/`, `config/`, `patches/` (check before trusting vendor), `vendor/skunexus/*`, frontend `frontend-client/src`. Cite file:line.
3. Research already done (cite it, don't redo it): `research/*.md`, and `review/po-baseline.md` / `review/deviations.md` if present.
4. Ticket: `jira/description.md`, `jira/comment_*.md`, `jira-summary.md`, `input/`.
5. Related work: <RELATED_SOURCES>.

## Conventions (keep the PRD consistent with <STYLE_MODEL>)
| Item | Rule |
|---|---|
| Altitude | **What**, not how. No class names in §1–§6 except settings, permissions and statuses that users see. Implementation ideas go to Notes for Design |
| Terms | One term per concept, used everywhere: <TERMS> |
| §5 Scope of Changes | Bold surface name + outcome + R-ids in brackets |
| §6 Acceptance Criteria | Grouped by the §4 headings. One bullet per behaviour: `- **Rn.a** Given …, when …, then …`. Concrete values (order states, quantities, product codes). Happy path, edges and error paths, including concurrency ("exactly one succeeds"). Each falsifiable, with no implementation in it. Every requirement has ≥1 bullet; no bullet without a requirement |
| Other tickets' ids | Always with the ticket key: `FFD-14 R31`, `FFD-14's R26`. `check-prd.py` reads a bare id as this PRD's |
| Assumptions | Inline `(assumed, Qn)` in the requirement, plus a §7 line "Assumed: …" naming who confirms |
| §7 | At approval it holds only deliberately deferred items, each with a one-line reason and an owner, grouped by stakeholder (For <PO> / client · For <TECH_LEAD> · External inputs and follow-ups). Resolved items move into a **Decision log** table (`Id · Decision · R-ids · Evidence`), so the evidence trail survives |
| Notes for Design | Parked ideas and constraints for the backend plan, not decisions. One bold bullet per topic with its R-ids and file:line evidence |
| Spelling and tone | Match the file's spelling. Plain, short sentences; no marketing; no teammate quotes beyond what the ticket says |

## Drafting ownership
| Owner | Writes | Output file |
|---|---|---|
| D1 | §6 Acceptance Criteria for <DECIDED_RANGE> | `review/draft-6-acceptance.md` |
| D2 | §1 Summary, §2 Problem/Why, §5 Scope of Changes, the §7 rewrite (deferred items + Decision log), and a tidy of Notes for Design | `review/draft-1-2-5-7.md` |

Drafters write **only** their output file and never edit `prd.md`; the orchestrator assembles. Every draft ends with `## Notes for the orchestrator`: ambiguities, untestable requirements, contradictions between §3/§4 and §7, and design forks. Write your best version anyway and list the problem there, so forks come back up instead of being guessed.

## Hard rules
- Read-only everywhere except your own output file. No git. No Jira or Confluence writes (cloudId `https://skunexus.atlassian.net/`, `maxResults: 10` if you read). No calls to the client's systems. No live SkuNexus.
- Never Read PNG/JPEG files.
- `prd.md` may change while you work (the orchestrator answers questions in parallel). If it does, say so in your notes.

---

## Per-agent prompts (orchestrator)
Spawn D1 and D2 as `sn-writer` agents.

**D1.** "Read the shared brief first: `review/drafting-BRIEF.md`. You are D1. Write §6 for <DECIDED_RANGE> into `review/draft-6-acceptance.md`. Cover the happy path, edges and error paths for every requirement, including these edge cases: <EDGE_CASES>. Verify each behaviour you assert about existing core or connector behaviour against the research files or the code. If a requirement is ambiguous or untestable as written, still write your best bullet, and list the problem under '## Notes for the orchestrator'. Return ≤10 lines: AC count per requirement, and your notes."

**D2.** "Read the shared brief first: `review/drafting-BRIEF.md`. You are D2. Write §1, §2, §5, the §7 rewrite and the Notes for Design tidy into `review/draft-1-2-5-7.md`. Don't change any decision. If you find a contradiction between §3/§4 and §7, list it under '## Notes for the orchestrator'. Return ≤10 lines."

## Assembly (orchestrator)
1. **Before fan-out,** write the last confirmed interview batch into `prd.md`, so the drafters start from the settled state.
2. Wait for both completion notices.
3. Snapshot: `cp prd.md review/prd-pre-assembly.md`.
4. Splice each draft into its sections with a short Python script that replaces the section bodies between headings. Don't hand-merge.
5. Triage the "Notes for the orchestrator": fixes consistent with the decisions are applied at assembly; real gaps become `P1…Pn` and go to the developer. Ask them while the panel runs; the answers queue until the synthesis, because the panel reads a frozen snapshot.
6. Run `python3 -I <SKILL>/scripts/check-prd.py prd.md`.
7. Tell the panel's traceability auditor which §4 items changed after D1 started: ACs drafted against an older §4 are the usual misses.
