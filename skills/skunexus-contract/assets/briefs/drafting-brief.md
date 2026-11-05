<!-- Door 3 (draft with defaults): parallel section drafters, once §3, §4 and §7 hold every decision or default. Copy to .ai/<TICKET>/review/drafting-BRIEF.md and fill it; the per-agent prompts and assembly steps at the end are for the orchestrator.
     Extra placeholders: <TICKET_SUMMARY>, <DECIDED_RANGE> (e.g. R1–R20), <STYLE_MODEL> (an approved PRD to copy conventions from, if the repo has one), <TERMS> (the PRD's fixed terms), <RELATED_SOURCES>, <EDGE_CASES> (for D1). Standard placeholders: see the skill's SKILL.md. -->
# <TICKET> PRD: drafting brief

## Artifact
`<REPO>/.ai/<TICKET>/prd.md`: the PRD for <TICKET> (<TICKET_SUMMARY>). Status Draft. §3 Goals/Non-Goals and §4 Requirements <DECIDED_RANGE> are settled: each open item is either decided or carries a default marked `(assumed, Qn)`, and §7 records it with its evidence or the role who confirms it.

**Do not reopen settled items.** Flag a problem with one only if it is factually wrong, contradictory, untestable or unsafe, and say which of the four. **Leave nothing open:** where your section needs a choice §3, §4 and §7 don't make, write the simplest default consistent with them, mark it `(assumed, Q?)`, and list it under your Notes so the orchestrator gives it a `Q` id.

## Audience
<DEVELOPER> (contract owner) → <PO> (approves scope and estimate) → <TECH_LEAD> (reviews the design) → <FE_DEV> (sizes the frontend) → the backend plan and the storyboard, which cite R-ids and criterion ids.

## Sources of truth, highest first
1. The decisions and defaults recorded in `prd.md` §7 and its Decision log.
2. Code in `<REPO>`: `app/`, `config/`, `patches/` (check before trusting vendor), `vendor/skunexus/*`, frontend `frontend-client/src`. Cite file:line.
3. Research already done (cite it, don't redo it): `research/*.md`, and `review/po-baseline.md` if present.
4. Ticket: `jira/description.md`, `jira/comment_*.md`, `jira-summary.md`, `input/`.
5. Related work: <RELATED_SOURCES>.

## Conventions (keep the PRD consistent with <STYLE_MODEL>)
| Item | Rule |
|---|---|
| Altitude | **What**, not how. No class names in §1–§6 except settings, permissions and statuses that users see. Implementation ideas go to Notes for Design |
| Terms | One term per concept, used everywhere: <TERMS> |
| §5 Scope of Changes | Bold surface name + outcome + R-ids in brackets |
| §6 Acceptance Criteria | Grouped by the §4 headings. One bullet per behaviour: `- **Rn.a** Given …, when …, then …`, letters a…z then aa. Concrete values (order states, quantities, product codes). Happy path, edges and error paths, including concurrency ("exactly one succeeds"). Each falsifiable, with no implementation in it. Every requirement has ≥1 bullet; no bullet without a requirement |
| Other tickets' ids | Always with the ticket key: `FFD-14 R31`, `FFD-14's R26`. A bare id is read as this PRD's |
| Assumptions | Inline `(assumed, Qn)` in the requirement, plus a §7 entry `Assumed: … Evidence: … Confirm with <role>.` |
| §7 | Grouped: For <PO> / client · For <TECH_LEAD> (`J-n`) · External inputs. A `Q` is never deleted: decided items move into a **Decision log** (`Id · Decision · R-ids · Evidence`) with their ids |
| Notes for Design | Parked ideas and constraints for the backend plan, not decisions. One bold bullet per topic with its R-ids and file:line evidence |
| Spelling and tone | Match the file's spelling. Plain, short sentences; no marketing; no teammate quotes beyond what the ticket says |

## Drafting ownership
| Owner | Writes | Output file |
|---|---|---|
| D1 | §6 Acceptance Criteria for <DECIDED_RANGE> | `review/draft-6-acceptance.md` |
| D2 | §1 Summary, §2 Problem/Why, §5 Scope of Changes, the §7 tidy (groups + Decision log), and Notes for Design | `review/draft-1-2-5-7.md` |

Drafters write **only** their output file and never edit `prd.md`; the orchestrator assembles. Every draft ends with `## Notes for the orchestrator`: ambiguities, untestable requirements, contradictions between §3/§4 and §7, design forks, and every new default you assumed. Write your best version anyway and list the problem there, so forks come back up instead of being guessed.

## Hard rules
- Read-only everywhere except your own output file. No git. No Jira or Confluence writes (reads follow the repo `CLAUDE.md` Atlassian rules, cloudId `<JIRA_SITE>`, `maxResults: 10`). No calls to the client's systems. No live SkuNexus.
- Never Read PNG/JPEG files.
- `prd.md` may change while you work. If it does, say so in your notes.

---

## Per-agent prompts (orchestrator)
Spawn D1 and D2 as `sn-writer` agents, in one message.

**D1.** "Read the shared brief first: `review/drafting-BRIEF.md`. You are D1. Write §6 for <DECIDED_RANGE> into `review/draft-6-acceptance.md`. Cover the happy path, edges and error paths for every requirement, including these edge cases: <EDGE_CASES>. Verify each behaviour you assert about existing core or connector behaviour against the research files or the code. If a requirement is ambiguous or untestable as written, still write your best bullet, and list the problem under '## Notes for the orchestrator'. Return ≤10 lines: criterion count per requirement, and your notes."

**D2.** "Read the shared brief first: `review/drafting-BRIEF.md`. You are D2. Write §1, §2, §5, the §7 tidy and Notes for Design into `review/draft-1-2-5-7.md`. Don't change any decision or default, and don't delete any `Q`. If you find a contradiction between §3/§4 and §7, list it under '## Notes for the orchestrator'. Return ≤10 lines."

## Assembly (orchestrator)
1. **Before fan-out,** §3, §4 and §7 are final in `prd.md`, so the drafters start from the settled state.
2. Wait for both completion notices.
3. Snapshot: `cp prd.md review/prd-pre-assembly.md` (not a version snapshot).
4. Splice each draft into its sections with a short Python script that replaces the section bodies between headings. Don't hand-merge.
5. Triage the "Notes for the orchestrator": fixes consistent with the decisions are applied now; each new default gets the next free `Q` id and its §7 entry; real gaps become `P1…Pn` for the developer (attended) or `Assumed` entries (unattended).
6. Run `python3 -I <SKILL>/scripts/check-contract.py .ai/<TICKET>` until it exits 0.
7. Tell the panel's traceability auditor (door 5) which §4 items changed after D1 started: criteria drafted against an older §4 are the usual misses.
