# Investigation: <TICKET-KEY> — <Title>

> Status: Draft  <!-- flip to "Approved" ONLY after the developer explicitly accepts -->
> Source: Jira <TICKET-KEY>  <!-- or: "described in chat (no ticket)" -->
> Verdict: pending  <!-- confirmed-bug | feature-change-request | works-as-designed | cannot-confirm-statically -->

## 1. Symptom
<!-- As PINNED DOWN IN THE INTERVIEW — not as the ticket phrased it. -->
**Expected:** <!-- and what grounds the expectation: docs, past behavior, spec, agreement -->
**Actual:** <!-- concrete, not "it doesn't work" -->
**Reproduction / anchor:** <!-- steps, or a concrete instance (order ID, timestamp, log line).
                                "unknown — see Open Questions" is honest; a vague anchor is not. -->
**Environment:** <!-- install/config/version context that matters; "n/a" if none -->

## 2. Verdict
<!-- One of: Confirmed bug | Feature change request | Works as designed | Cannot confirm statically.
     One short paragraph of justification. The evidence lives in §3 — don't repeat it here. -->

## 3. Analysis
<!-- The evidence trail. EVERY claim cites its source: `path/file.php:123`, a commit SHA, a doc passage,
     or a developer answer. Mark hypotheses explicitly as hypotheses until evidence promotes them.
     · Confirmed bug: the causal chain from trigger to symptom — the exact place behavior diverges
       from intent, and why each link holds.
     · Feature change request / works as designed: the traces showing current behavior is deliberate
       (introducing commit/ticket, recorded decisions, docs) and what the request would actually change.
     · Cannot confirm statically: the competing hypotheses, each with the discriminating check the
       developer can run (a query, a log to pull, a repro step) — precise enough to execute verbatim. -->

## 4. Proposed fix
<!-- CONFIRMED BUG ONLY — omit this section entirely for any other verdict.
     ONE recommended fix at "what to change, where" altitude: the files/classes/behavior to change and
     why that's the right layer — including what the fix could disturb (other call sites, side effects).
     List alternatives ONLY when a genuine fork exists (a credible alternative with real tradeoffs).
     NO task breakdown (the planning skill's job), NO code (the implementation skill's job).
     End with the complexity read and recommended route — the developer decides:
     · trivial → skunexus-backend-implement (direct road)
     · complex → skunexus-backend-plan first -->

## 5. Expected behavior after the fix
<!-- CONFIRMED BUG ONLY — omit for other verdicts. Testable acceptance bullets: the contract downstream
     skills trace to (the planning skill's tasks cite these IDs; the PR skill sources its before/after
     from here). Cover the fixed path AND the behavior that must NOT change.
     Each is a falsifiable proposition that can become a behavior-test name verbatim (naming rules:
     skunexus-behavior-testing); name where a regression test would live when it's obvious. -->
- **A1** …
- **A2** …

## 6. Open Questions
<!-- LIVE tracker during the hunt — add freely, clear as answered. Developer checks (queries, logs,
     repro runs) live here until their results come back as evidence. At approval, only deliberately-
     deferred items remain, each with a one-line "why". Empty is a good outcome. -->
- …
