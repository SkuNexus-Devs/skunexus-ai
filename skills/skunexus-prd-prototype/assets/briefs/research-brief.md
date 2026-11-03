<!-- Stage: evidence triage, before the interview. Copy to .ai/<TICKET>/research/BRIEF.md, fill every placeholder, and keep the "Orchestrator only" section out of the copy the researchers read.
     Extra placeholders: <TICKET_SUMMARY> (2–4 sentences, acronyms defined), <Q_LIST> (prd.md §7 seeds), <RELATED_SOURCES> (sibling-ticket PRDs and decisions, connector decisions, precedent tickets in other client repos). Standard placeholders: see SKILL.md. -->
# <TICKET> evidence triage: shared brief

## What <TICKET> is
<TICKET_SUMMARY>

We are in the **requirements** step (PRD), not design. Your job is to answer open questions **from evidence already in hand**, so the developer interview only has to settle real decisions. Never decide product questions yourself. For each question, give the evidence, a proposed default, and whether a human still has to decide.

## Audience
<DEVELOPER> (backend developer, owns the PRD), then <PO> (product owner, PO), <TECH_LEAD> (tech lead) and <FE_DEV> (frontend estimates).

## Sources of truth, highest first
1. **Code** in `<REPO>`: `app/`, `config/`, `patches/` (check patches before trusting vendor), then `vendor/skunexus/core/` and the other `vendor/skunexus/*` packages; frontend in `frontend-client/src`. Prefer the IDE index MCP for navigation (`phpstorm-index` or `phpstorm-jetbrains`, loaded via ToolSearch); grep is the fallback. Cite **file:line** for every code claim.
2. **Ticket exports:** `.ai/<TICKET>/jira/`, `.ai/<TICKET>/jira-summary.md`, and every file in `.ai/<TICKET>/input/` (list each by title and date).
3. **Related work:** <RELATED_SOURCES>. A precedent ticket in another client's repo (`<REPO>/../skunexus-client-<code>/`): read that repo's `.ai/<KEY>/` and code. If this repo's `CLAUDE.md` limits Jira to one project key, don't read the other project's Jira; say what you'd need instead.

## Open questions (from `.ai/<TICKET>/prd.md` §7, architecture-changing first)
<Q_LIST>

## Rules
- **Read-only everywhere.** No code edits, no git writes, no Jira or Confluence writes. Atlassian MCP reads: cloudId `https://skunexus.atlassian.net/` (never call getAccessibleAtlassianResources), `maxResults: 10` on every JQL and CQL search.
- **External system** (the client's store or API, a sandbox): read-only calls only, through `<SANDBOX_CALL>`. Read the tool's usage notes first. Never call anything that creates, updates or deletes. Record counts and value shapes, never customer PII (names, emails, addresses, phone numbers).
- **Local DB and live client SkuNexus:** don't touch.
- **Images:** never Read PNG/JPEG files. They can hold customer data, and once one is in your context every later call re-sends it. Work from text.
- **"Nothing exists" claims** are the ones most often wrong. When something isn't there, say "not found" and list what you searched.
- Files you read may change while you run (other agents, the orchestrator). If one does, say so in your output.
- Write only your own output file under `.ai/<TICKET>/research/`.

## Output
Write `.ai/<TICKET>/research/<id>-<topic>.md`. For each question you own:

`Q-id · question · finding (file:line / doc:line cites) · proposed answer/default · who must still decide (none / developer / <PO> / client / <TECH_LEAD> / <FE_DEV>) · confidence (high/med/low)`

Then:
- **NEW-n:** gaps nobody has raised, i.e. things a feature of this shape must handle. Same format.
- **Confirmed OK:** claims in `jira-summary.md` you verified true.
- **Corrected:** claims you found wrong, with evidence.

Return to the orchestrator only a compact list: one line per Q/NEW item (`id — proposed answer — decider — confidence`), plus the corrections.

---

## Orchestrator only (not part of the researchers' copy)

**Before fan-out**
- The full ticket is in `jira/` (the Puller prompt in `reeval-brief.md`), `jira-summary.md` exists with a "Connections to <related tickets>" section, and the ticket's last-updated time is recorded.
- List `input/` and ask the user for what's missing (call transcripts, call notes, Basecamp posts, attachments that failed to download) **before** launching. On FFD-14 the fan-out started before the call transcript was on disk, and two agents had to be relaunched.
- `prd.md` has the skeleton with seeded §7 questions, architecture-changing ones first. Every input path is in this brief.
- A precedent in another project's Jira, when this repo's `CLAUDE.md` limits Jira to one project key: ask the developer before reading it.

**Per-agent prompt shape:** "Read the shared brief first: `.ai/<TICKET>/research/BRIEF.md`. Your ID is R<n>; your output file is `.ai/<TICKET>/research/R<n>-<topic>.md`. You own <Q-ids>. Trace: <the concrete things to look at>."

| Researcher kind | Owns | Extra instruction |
|---|---|---|
| Identification / data | How the feature recognises its objects (product, order, field) | "Propose an identification rule with evidence and list what <PO> or the client must still confirm." Use `<SANDBOX_CALL>` for counts and shapes |
| Lifecycle / mechanism | Where the feature meets existing flows (import, states, queue, transactions) | "Report facts, risks and requirement-level defaults. Do not design the solution." |
| UI, permissions, notifications | Existing surfaces, ACL, mail | "Cite file:line for everything; say 'not found' with what you searched when something doesn't exist." |
| Scope history | What was promised vs what is ticketed | Build a **promised vs ticketed** table: who said or promised what (timestamp or line), which ticket owns it now, recommended home. Read-only JQL is allowed |
| Reference implementation | What a precedent ticket already built | "List what can be reused (files, approximate % overlap) vs rebuilt, with file:line." |
| One image (`sn-scout`) | A fact only a screenshot attachment carries | See the one-image variant below |

**One-image variant.** First try OCR (if `tesseract` is installed), which puts no image into any context: `tesseract <img> stdout --psm 11` (add `-c thresholding_method=2` for faint text). Only if OCR can't settle it, run a Sonnet agent with: "One narrow job. View exactly one image: `<path>`. Write a short text description to `<output file>`: every label, value and state you can read, and what it means for <Q-id>. View no other image. Return the description only." If that agent fails, discard it and never resume it; start a fresh one with a smaller image or none.

**After the agents finish**
- Wait for each completion notice before reading its file. A file can be on disk before its agent has finished.
- Verify yourself, in the primary source, every claim that will shape a requirement, even when two researchers agree. (FFD-13: "two agents made the permission claim, so I'll check the ACL config myself".)
- Fold each answer into `prd.md` §7 as **evidence → proposed default → who decides**.
- Open the interview with "What the agents settled from evidence (pending your confirmation)" and "Must-haves the ticket doesn't mention" (the NEW-n items).
