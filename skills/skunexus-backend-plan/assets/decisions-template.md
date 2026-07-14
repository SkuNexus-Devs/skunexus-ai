# Decisions: <TICKET-KEY> — <Title>

> Durable, ADR-style log of the *why* behind key technical choices for this ticket.
> SHARED across backend & frontend, planning & implementation. Seeded by the planning skills,
> appended by the implementation skills, read by the PR-description skill.
> APPEND, don't rewrite — supersede an old entry rather than editing it, so the change of mind survives.

<!-- ─────────────────────────────────────────────────────────────
     LOG AN ENTRY ONLY IF ALL THREE HOLD:
       1. there was a REAL FORK — a credible alternative was actually on the table;
       2. the rationale is NOT OBVIOUS from the code or the contract; and
       3. someone later would genuinely ASK "why was it done this way?" — costly to reverse,
          surprising, or it deviates from convention.
     DO NOT log: naming, formatting, the obvious idiomatic Laravel choice, "added validation",
     routine file placement, or anything that merely restates a requirement.
     If nothing clears the bar, THIS FILE SHOULD NOT EXIST. Empty is the normal outcome.
     ───────────────────────────────────────────────────────────── -->

## D1 — <short decision title>
- **Area:** backend | frontend | cross-cutting
- **Decided:** <YYYY-MM-DD>
- **Decision:** <!-- what was chosen -->
- **Alternative(s) rejected:** <!-- the fork — what we deliberately did NOT do -->
- **Why:** <!-- the rationale the code won't reveal -->
- **Consequences / affected:** <!-- what this constrains or implies downstream; requirement IDs or tasks touched -->

<!-- Reversal example:
## D4 — Switch reservation to a queued job
- ...
- **Supersedes:** D2 — because load testing showed the synchronous path blocked checkout under contention.
-->
