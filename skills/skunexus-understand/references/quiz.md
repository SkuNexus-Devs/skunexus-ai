# Quiz: questions, leak checks and the gate

The quiz is the verify layer. Reading alone makes it easy to believe you understood; a question you must answer before you see the key tests it. The threat it guards against is self-deception, not fraud: the key is in the page, and the only person a cheat fools is the reader.

## 1. `quiz.json`

```json
{"built_from": "abc1234",
 "questions": [
  {"id": "q1", "chapter": "ch-3", "final": true, "kind": "predict",
   "stem": "Product P has on_hand 10. Order #1001 (unpaid, placed 10:00) holds 4 and order #1002 (paid, placed 10:05) holds 3. The release job runs at 10:40 with a 30-minute window. How many units of P are available right after the run?",
   "options": ["3", "6", "7", "10"],
   "answer": 2,
   "feedback": [
     "That is the figure before the run. Order #1001 is unpaid and 40 minutes old, so the job gives its 4 units back.",
     "That releases the paid order and keeps the unpaid one: the job's filter is the other way round.",
     "Right: #1001's 4 units go back (unpaid, past 30 minutes) and #1002's 3 stay (paid). 10 − 3 = 7.",
     "Paid orders keep their hold until shipment. Only unpaid ones expire."],
   "evidence": ["src/Inventory/ReleaseExpiredReservations.php:41", "decisions.md D3"]}
 ]}
```

| Field | Rule |
|---|---|
| `built_from` | The head SHA (7 characters) the keys were verified at. Results bind to it |
| `id` | `q1`…`qN`, stable |
| `chapter` | Where the point is taught, so a miss can send the reader back: a piece id (`ch-3`), or `asked`, `background`, `intuition` or `proven`. A question on the ask is `asked`; a `test` question names the tests piece when one exists, else `proven`. After the pick the feedback says "It is decided in ③ the release job." (a piece), "See ④ the tests." (a `test` question on a piece) or "See What was asked." (a section) |
| `final` | `true`: in Check yourself. `false`: a checkpoint at the end of the piece `chapter` names (§2) |
| `kind` | One kind from §3 |
| `stem`, `options` | Plain text, `inline code` in backticks. No labels: no hash, ref id, `file:line`, section or exit code (§4). Exactly 4 options, rendered in this order |
| `answer` | 0–3 |
| `feedback` | 4 strings, about 2 sentences each. Each distractor's names the misconception behind it; the key's carries the why |
| `evidence` | At least one `file:line` at head, or an artifact id (`prd.md R3.a`, `workflows.md s1.2`, `feedback.md FB3`, `spec.<slug>`), proving the key |

## 2. Size and placement

**Placement** (the build does it; the check fails a page that breaks it):
- **Check yourself** (`#quiz`, an h2) sits open in the main flow, after the last main-flow piece (on an intent-only page, after What was asked) and before Go deeper. Never inside a closed row, never after Go deeper.
- **The first screen has an entry point** besides the bar's pill: Start here's last step, "Answer 5 questions · ~3 min", with its progress ("0/5").
- The last main-flow piece ends with "Next: Check yourself ↓".

**Size:**
- **Final questions:** 5, or 3 when the diff has ≤ 150 read-tier lines. Intent-only: 3–5, by the size of the ask (5 past about 8 criteria). The checker accepts 3–5.
- **Checkpoints** (`final: false`) only on a large change. With 4 main-flow pieces or fewer, the finals are the whole quiz (the check warns on a checkpoint). Past 4, each main-flow piece gets one checkpoint, 2 for a high-risk piece, while the total stays ≤ 12; past that, neighbouring pieces share one, and high-risk pieces keep theirs first. The check warns on a main-flow piece with none (while the quiz is under 12) and fails a piece with more than 2. A checkpoint renders at the end of its piece, after "More on this" and never inside it: no question is ever folded. Only a main-flow piece (`read: must`) takes checkpoints; a piece under Go deeper (`read: skim`) sits in a closed row, so the check fails a checkpoint there (make it a final). `asked.html` and `proven.html` get no checkpoints: their questions are finals.
- Every question counts toward the gate, and the checker and the agents treat them as one set.
- Checkpoints lean on `predict` and `where`. The finals lean on the layers, `impact`, `rollout` and a cross-piece `predict`.
- No two questions test the same fact; each piece's `checks` in `plan.json` name its checkpoint's fact up front (`write.md` §14). Never quiz a `next` callout: the participate layer stays ungraded. Never ask a `criterion` or `ac-map` question on a criterion with a `needs_decision` drift (`write.md` §9).

**Layer coverage** (the check errors when it fails). The finals cover every layer the page has:
- at least 1 intent question (`requirement`, `workflow`, `why` or `criterion`) when any Asked source exists, a PR body or Jira copy in `plan.json` `sources` included;
- at least 1 `test` question when the Proven layer exists (`proven.html`). An `ac-map` question doesn't count: it starts from a test, while a `test` question starts from the behaviour and asks for its proof.

Fill the rest in this order, while slots remain: 1 `predict`; 1 `why` when a recorded decision exists; 1 `impact` or `edge`; at least 3 kinds in all. With 3 finals on a small diff, that is `predict`, one intent question and one `test` question. An intent-only quiz skips this order: see the next paragraph.

**An intent-only quiz** (no code yet) uses intent kinds only: `requirement`, `workflow` and `why`. A `criterion` question reads the code against the PRD, so before code exists, ask a criterion's meaning as a `requirement`. Build the questions from the criteria, the workflow steps' before → after, the rulings and the decisions, so that a reader who passes could plan the ticket: e.g. 5 finals of 2 `requirement` (one of them a non-goal), 2 `workflow` and 1 `why`. Every `chapter` is `asked`, `background` or `intuition`, and every `evidence` is an artifact id.

## 3. The kinds

| Kind | It tests | The key comes from | Good distractors | Watch for |
|---|---|---|---|---|
| `predict` | Running the new logic in your head on toy data | the code at head; `spec-from-tests.md` scenarios | the pre-change result, an inverted filter, a boundary misread | every input in the stem; small numbers; numeric options in natural order (ascending or descending) |
| `why` | Why this approach beat the alternative | a `decisions.md` entry, a Decided `Q`, a ruling, `prd.md`, the PR body, or a ticket note in `plan.json` `sources` (a root-cause note's rejected alternative) | the rejected alternatives; plausible reasons nobody recorded | **with no recorded source, ask no why question** |
| `where` | Where a future change belongs | the code structure at head | real neighbouring files, classes and config | invented names are free eliminations; keep the options one shape ("In X, as Y") |
| `impact` | What an invariant protects | the code, and which test turns red | failures of neighbouring invariants | a generic-knowledge key: rewrite it to this change's consequence |
| `edge` | Behaviour at a boundary | the code and the tests | reject, overflow, silent truncation | cover both sides of the boundary across the quiz |
| `criterion` | Whether the code meets one stated requirement, in a case the requirement speaks to | `prd.md` §6, read against the code | outcomes the requirement might suggest but the code doesn't produce | the key is what the code does. If that breaks the criterion, it is a `needs_decision` drift (`write.md` §9), and the quiz asks no question on that criterion |
| `requirement` | What was asked: a goal, a non-goal, or what a criterion means in a concrete case | `prd.md` §3, §4, §6 and §7; `feedback.md` rulings; `investigation.md` §5 | a neighbouring criterion, a non-goal presented as covered, an open question presented as decided | a toy case in the stem, never the criterion's wording; the key is what the contract says, not what the code does |
| `workflow` | A contract step's state before → after, or what the actor sees | `workflows.md` step rows | the state one step earlier or later, another scenario's outcome, a plausible side effect the step doesn't have | every input in the stem; state options in a natural order; the key is the step's row, re-read |
| `test` | Which scenario proves a behaviour, what ran, or what is not tested | `spec-from-tests.md`, the `Tests (landed)` lines, the run, the trace | a scenario that proves a neighbouring criterion, a test that exists but didn't run, a behaviour that is built but untested | the key must be on `proven.html` or the trace; no file paths or line numbers as options; scenario headings are fine |
| `rollout` | What happens at deploy to existing rows and in-flight work | migrations, `decisions.md`, `backend-plan.md` | "a backfill exists", "the job sweeps old rows", "it fails hard" | ask only when the change touches persisted state or jobs |
| `ac-map` | Which requirement a piece of evidence proves | `prd.md` criteria; the acceptance coverage in `spec-from-tests.md` | neighbouring criteria | describe the test's setup, never echo the criterion's text; each option names a criterion in plain words, never by id, in the PRD's order |

A change to what consumers see (an API, a GraphQL field, an event) is asked as a `predict` ("what does the field return after this change?") or an `impact`.

**One example per kind,** all from one synthetic shop ticket, ABC-123: *reserve stock when the order is placed; a scheduled job releases unpaid holds after a window.* Its toy PRD has R1 (placing an order holds its quantity), R2 (an order larger than available stock is backordered), R3 (an unpaid order releases its hold when the window closes), R4 (a paid order keeps its hold until shipment), the non-goal "no customer email when a hold is released", and the open question Q2 (should a backorder hold incoming stock?). `*` marks the key. In this order, the keys run C A D B D C B A C D B, which passes the position checks.

1. **predict:** the JSON example in §1. Options 3 / 6 / **7\*** / 10. Each distractor is a misconception: 3, nothing was released; 6, the paid order was released instead; 10, both were released.
2. **why:** "Why does this change reserve stock when the order is placed rather than when the payment is captured?"
   - **A\*** Payment confirmations arrive minutes late, and two checkouts in that gap could sell the same last unit.
   - B: The payment gateway refuses to capture an order whose lines have no stock reservation attached yet.
   - C: Reserving at capture time would need a second transaction that the order handler is not allowed to open.
   - D: The warehouse picks unpaid orders early, so their units must already be held when the pick list is built.
   - The feedback cites `decisions.md D2`. All four options are reasons of the same length and shape.
3. **where:** "The business wants unpaid holds to expire after 45 minutes instead of 30. Where does that change belong?"
   - A: In the ReserveStock handler, as an expiry timestamp written onto every new reservation row.
   - B: In the stock_reservation migration, as the default value of a new expires_at column.
   - C: In the order placement endpoint, as a request parameter that the checkout page sends.
   - **D\*** In the release window setting of the inventory config, which the scheduled job loads on each run.
4. **impact:** "A later refactor drops the database's unique key on a reservation's order line. What goes wrong first?"
   - A: The release job can no longer match holds to orders, so it deletes the holds of paid orders.
   - **B\*** A retried reservation message holds the same line twice, so available stock looks lower than it is.
   - C: Two lines for the same product now share one reservation row, so the second line's quantity is lost.
   - D: Available stock is summed per order line instead of per product, so the storefront totals drift.
5. **edge:** "A customer orders 5 units of a product with 3 available. What does the change do?"
   - A: Rejects the whole order with a validation error before reserving anything.
   - B: Reserves all 5 units and lets available stock fall to −2 until restock.
   - C: Places the order unreserved and retries the reservation on every restock.
   - **D\*** Reserves 3 units and marks the other 2 units on that line as backordered.
6. **ac-map:** "A test sets on_hand to 5, places an order for 3 that nobody pays, runs the job 31 minutes later and asserts that all 5 units are available again. Which acceptance criterion is it evidence for?"
   - A: Placing an order lowers available stock by the ordered quantity.
   - B: An order larger than available stock is placed with a backorder.
   - **C\*** An order still unpaid when the window closes releases its stock.
   - D: A paid order keeps its units held until the shipment is created.
   - The feedback names each id (R1 to R4); the options never do.
7. **rollout:** "Orders placed before this deploy have no reservation rows. What happens to them after the deploy?"
   - A: A migration backfills a hold for every unpaid order, starting from its placement time.
   - **B\*** They hold no stock, so available stock stays overstated until those orders ship.
   - C: The release job treats them as expired on its first run and cancels those unpaid orders.
   - D: Shipping refuses them until someone re-places the order so that a reservation exists.
   - The feedback cites the decision that accepts the gap. Naming `decisions.md` inside option B alone would be a reference leak.
8. **criterion:** "The PRD says an order still unpaid when the 30-minute window closes releases its stock. Order #1004 is placed at 10:00 and paid at 10:29. The job runs at 10:31. What does the change do with its hold?"
   - **A\*** Keeps it until the order's shipment is created.
   - B: Releases it at 10:31 and leaves the order open.
   - C: Releases it at 10:31 and cancels the order.
   - D: Keeps it one more run, then releases it at 11:01.
   - The feedback cites the job's paid-order filter and R3. Options that echo "releases" from the stem point away from the key.
9. **requirement:** "The PO asks whether ABC-123 emails the customer when an unpaid order's hold is released. What does the PRD say?"
   - A: Covered: the release job sends it when it releases the hold.
   - B: Covered: the order confirmation already warns about it.
   - **C\*** Out of scope: the PRD lists it among the non-goals.
   - D: Still open: the PO was asked, and no answer is recorded.
   - No option names an id. The feedback quotes the non-goal line, cites R3 and R1, and says the open question Q2 is about backorders. A is the misconception "the release step must tell someone".
10. **workflow:** "Order #1003 (2 × MUG-1, placed 10:00) is still unpaid when the release job runs at 10:31; the window is 30 minutes. MUG-1 shows available 8 before the run. What is the state after it?"
    - A: available 8; the order stays open and the hold waits one more run.
    - B: available 8; the order is cancelled and the hold moves to backorder.
    - C: available 10; the order is cancelled and its hold is deleted with it.
    - **D\*** available 10; the order stays open and unpaid; its hold is released.
    - The options run in the natural order of the leading number. The feedback cites the s1.2 row's before → after. C is the commonest misreading: releasing the stock does not cancel the order.
11. **test:** "Which behaviour does ABC-123 build that no test proves, so the page lists it under Not tested?"
    - A: Refusing a second order that wants units already held for #1003.
    - **B\*** Skipping an order that was cancelled before the release job runs.
    - C: Writing the hold in the same transaction as the order it belongs to.
    - D: Leaving available stock unchanged for an order line of quantity 0.
    - Every option is a behaviour of the same size, and none restates another question's key: in one quiz, an option that states another key is a cross-question leak. The feedback names the trace row (R3.b, `untested`) and, for each distractor, the scenario that proves it. The variant "which scenario proves that an unpaid order releases its hold?" lists real scenario headings from `spec-from-tests.md` as options.

## 4. Authoring rules

> **Ask about the thing, never its label.** A quiz tests understanding (behaviour, why, impact, risk, where to change), never recall. In stems and options, never require recall of:
> - commit hashes, line numbers or `file:line`;
> - the ticket's ref ids (R4.b, D2, FB12, Q21, s1.7, T3);
> - menu letters, door, step or section numbers (§7);
> - exit codes, exact message text, constant or variable names, the internal names of checks;
> - other tickets' keys.
>
> Name the thing in plain words: "the change that lets a storyboard go out before the triage", "the criterion that a reservation expires after 30 minutes". Labels belong in `feedback` and `evidence`, which show after the pick.

Two clarifications:
- Toy-world ids that the stem itself defines (order #1003, TOY-8) are scenario data, not recall. Plain words are still preferred.
- Real domain vocabulary a developer must use is allowed: an event or status name in an integration contract, an endpoint.

**Before and after: a label** (synthetic, ABC-123). The label version: "What does the release job exit with, since commit a1b2c3d, when a hold is locked?"
- A: Exit 0, with a warning in the log.
- B: Exit 1, listing the locked hold.
- **C\*** Exit 2, so the next run retries it.
- D: Exit 3, and the order is cancelled.

A teammate who knows exactly how the job behaves, but not the hash or the number, fails it. The rewrite names the situation and asks for the behaviour; the commit and the exit code move to the feedback and the evidence:

"Order #1007's hold is locked by a checkout that is still running when the release job reaches it. What happens?"
- A: The job stops at that hold and reports the whole run as failed.
- B: The job waits for the lock, then releases that hold in the same run.
- **C\*** The job skips that hold, finishes the run, and releases it next run.
- D: The job releases that hold anyway, so the checkout fails on its write.

**The key is knowable only from this ticket.** The blind guesser is a strong reasoner, not only a cue counter. On one real run it scored 10 of 12 without the page, while a reader with the page scored 12 of 12. Few of its hits came from a cue: the stems described each situation so fully that a smart outsider could reason out the rule behind the key. After the label rule, three rules come before all the others:
- **The stem gives the situation, never the rule.** Name the inputs, the toy values and the moment, then ask for the outcome. Leave out every sentence that states the rule or its purpose, and every name that carries it: a job called `releaseUnpaidHolds` tells the reader which holds it releases. The page teaches the rule; the stem must not.
- **Every distractor is a rule a reasonable engineer could have chosen.** Prefer the recorded rejected alternatives: the other option of a `decisions.md` entry, the plan's alternatives, a `feedback.md` **Proposed:** option that was not ruled. A distractor that contradicts the stem, or that no sane design would pick, is a free elimination.
- **The key is the ticket's own choice among those rules.** When the situation admits only one sensible outcome, the question tests reasoning, not the ticket: move it to a fork the ticket decided, or drop it.
- **Not every key agrees with the headline rule.** When every question turns on one rule ("a view adds binding, never behaviour"), each stem teaches the guesser that rule, and the guesser then picks whichever option agrees with it. Include at least one question whose key is a case where the rule does not apply (an exception the ticket records, a boundary, a path it leaves alone), with distractors that agree with the rule. Two questions never share one option set (the check warns): the second gives the first away.

**The outsider self-test,** on every question, before the checker: read only the stem and the four options, as a smart engineer who never saw this ticket. Can you pick the key? If yes, rewrite: take the rule out of the stem, or swap the weak distractors for rejected alternatives. The blind guesser (§7) then tests what you missed.

**The teammate self-test,** beside it: would a teammate who understood this change, but memorised none of its labels, answer this? If not, rewrite it in plain words. The two tests pull against each other: beating the blind guesser must come from plausible alternative designs as distractors, never from piling on specifics or labels, which shut out the teammate along with the outsider.

**Before and after: a leak** (synthetic, ABC-123). The leaky version:

"ABC-123 holds stock the moment an order is placed, so two checkouts can't sell the same last unit. Order #1005 takes the last LAMP-2 at 10:00 and is paid at 10:02. Order #1006 asks for one LAMP-2 at 10:01. What happens to #1006?"
- **A\*** It is placed as a backorder, and #1005 keeps the unit.
- B: It takes the unit, and #1005 is backordered at 10:02.
- C: It is placed in full, and available stock falls to −1.
- D: It takes the unit, and #1005 is cancelled at 10:01.

Why it leaks: the first sentence states the rule and its purpose. B and D give the unit to the later order, against "the moment an order is placed"; C is the double sale the stem says the change prevents. Only A survives a careful reading, with no knowledge of ABC-123. No cue points at A, so the checker can pass it.

The rewrite:

"Order #1005 takes the last LAMP-2 at 10:00 and is paid at 10:02. Order #1006 asks for one LAMP-2 at 10:01. What happens to #1006 at 10:01?"
- **A\*** It is placed as a backorder, and #1005 keeps the unit.
- B: It is placed with no hold, and the first to pay gets the unit.
- C: It is refused as out of stock, and #1005 keeps the unit.
- D: It is placed in full, and available stock falls to −1.

The rule left the stem; the page teaches it. Each option is now a design a shop could ship: B holds at payment capture, the alternative `decisions.md` D2 rejected; C refuses where R2 chose a backorder; D is the behaviour before this change. Only D2 and R2 give the key, so a reader must know ABC-123 to pick it. The feedback cites both.

The rules below keep the surface clean:
- **Options are bare claims** of equal granularity and the same grammatical shape. The "because" goes in the feedback, never in the option: a reason makes the key long, and length is the commonest leak.
- **Ordered option sets keep their natural order:** numbers, ids, states, times. Pick the distractor values so that the key lands in its slot (§5).
- **Only real identifiers.** A distractor naming a class or file that doesn't exist is a free elimination for anyone who knows the codebase. Use real neighbours.
- **A `why` question needs a recorded source** (a PRD, a decision, a Decided `Q`, a ruling, the PR text, or a note in `plan.json` `sources`, cited in `evidence` by a ref that quotes it). With none, ask no why question.
- **Every key's evidence is re-read** at `built_from`, or in its source file for an intent key. A wrong key is the worst failure, because it teaches the bug.
- **At most one negation stem,** with the word written `**NOT**` so it renders bold.
- **No trivia and no gotchas:** no file counts or author names, and no labels (the first rule of this section). Medium difficulty: a reader of the page gets it; a skimmer doesn't.
- **Concrete scenarios:** toy values from `plan.json` `toy` (`write.md` §13), every input in the stem, and the question asks for an outcome, not a definition. A stem that needs another history names another record or ticket ("a different order, #1004, …", "a different ticket, TOY-8, …"); it never gives a toy record a second history.
- **Distractors are real misconceptions:** the pre-change behaviour, an inverted rule, the wrong layer ("the resolver filters it" when middleware does), a real element in the wrong role, a naive default ("runs in the same transaction" when the follow-up is queued), a rejected alternative from `decisions.md`. No throwaways, no absolutes ("always", "never").
- **Parity:** inline code in all options or in none; a reference token (a file path, or a toy id the stem defines) in no option or in at least two. The ticket's own ref ids appear in none (the label rule).
- **No generic-knowledge keys.** If an engineer can pick the key without this change ("dropping a unique key allows duplicates"), rewrite it around this change's consequence, or make the textbook answer a distractor where the change chose otherwise for a recorded reason.
- **Never** "all of the above" or "none of the above", and never a stem ending in "a" or "an".
- **Every key must be teachable from the page.** If the page doesn't say it, add it to the section or drop the question. An intent key is taught in `asked.html`, a `test` key in `proven.html` or the trace.

## 5. Positions

Positions are fixed, balanced and authored: the options render in the order you write them, with no shuffle at runtime. The checker, the blind agent, the learner and anyone discussing "q3, option B" then all see the same order.
- The key positions across the whole set: counts differ by at most 1, no run of 3 equal positions, no repeating cycle.
- The sequence runs in page order: each piece's checkpoints in piece order, then the finals.
- Choose the sequence before writing the questions (for fan-out, give each piece writer its slots), or take the valid sequence the checker prints when positions fail.
- Known ceiling: with N = 8 or 12 and strict balance, someone counting the revealed slots can deduce the last key. That is accepted, because the threat is unconscious cue-following, not counting.

## 6. The checker

`python3 -I <SKILL>/scripts/check-explainer.py <DIR>` checks the quiz with the rest of the page. Its quiz rules are adapted from no-leak-mcq (MIT). It replaces statistical tests, which say nothing at 5–12 questions, with the exact score a reader following one cue would get on this quiz. Its output says "heuristic screening, not proof": a pass doesn't prove the quiz is clean, which is why the blind guesser follows.

Each failure message names its rule: schema (a missing field, an unresolved `chapter` or `kind`, `built_from` not the head, 3–5 finals, at most 12 in all), positions, length, article, all/none, duplicate, numeric order, negation, reference parity, marker word, cue score, label, and the coverage warning. §4 has the rule behind each. Four fixes are not obvious:
- **label** (in a stem or option: a commit SHA, a `file:line` or "line n", a `§` number, "exit n" or "exit code", or an id from `plan.json` `refs` as a whole token): say what the thing is or does in plain words, and move the label to the feedback or the evidence. A stem with more than 3 code spans warns: it reads like implementation trivia. Menu letters, step numbers and message text the checker can't see; the teammate self-test (§4) catches them.
- **positions:** re-slot the keys to the sequence the checker prints. For ordered options, change the distractor values instead of the order.
- **length** (the key differs from the distractors' mean by more than 30%, with 4 characters of slack): move the reason into the feedback, and bring all four options to the same granularity.
- **cue score** (always picking the longest, the shortest, the stem echo, the most specific, the one without an absolute, the hedged one, or the one sharing the most words beats chance by more than one question, cap N/4 + 1): in the questions where that cue lands on the key (the message names them), change the surface: length, stem words, code spans, numbers, hedges, shared words.

Two emitters feed the agent checks:
- `check-explainer.py <DIR> --blind`: the stems, numbered by id (`q1.`), and the lettered options only. No kinds, `chapter` fields, keys or feedback.
- `check-explainer.py <DIR> --teach`: the page's text with scripts and styles stripped. It ends with the quiz's stems and options, with no key or feedback.

## 7. The blind guesser

It answers the quiz without the page. If it scores well, the quiz leaks, asks general knowledge, or states its rules in the stems.
- **Agent:** the blind guesser of `SKILL.md` "Roles", one call for all the questions together, so cross-question cues show. A strong guesser is the point; a weak one under-reports leaks. A fresh agent each round: one that saw round 1 remembers its picks.
- **Input:** `python3 -I <SKILL>/scripts/check-explainer.py <DIR> --blind > <DIR>/review/blind.txt`. The prompt names that one file and the agent reads nothing else. Never paste the quiz into a brief: a rebuild would leave a stale copy behind.
- **Prompt:** section B of `assets/briefs/verify-brief.md`. Save the reply as `<DIR>/review/blind.md` (round 2: `blind-2.md`).
- **Set threshold:** hits stay below N/2: at most 1 of 3, 2 of 5, 3 of 8, 5 of 12.
- **Each hit's tag** (the reply gives one) decides the fix, when the protocol below calls for one:
  - `cue` (length, a word from the stem, the only code span, a position pattern) → remove that cue;
  - `stem`, `plausible` or `general` (the stem's wording gives the rule, the key is the only sensible design, or textbook knowledge picks it) → rewrite the question by §4: the situation only in the stem, and distractors from the recorded rejected alternatives;
  - `guess` → leave it. Guessing alone reaches N/2 about 10% of the time at N = 5 or 8.

**The protocol: blind first, two rounds at most.**
1. Run the outsider self-test (§4) and the check, then blind round 1, before the teachability reader. A teach run on a quiz that leaks is wasted.
2. On a fail, rewrite only the hits tagged `cue`, `stem`, `plausible` or `general`; leave the misses and the `guess` hits alone (if every hit is `guess`, rewrite nothing). Re-run the check, then round 2 with a fresh guesser on the new `--blind` output.
3. Stop after round 2, pass or fail. Report the hits that remain, honestly, in the hand-off and the Checks cell of `artifact.md`: "blind 8/12 → 6/12 after 2 rounds; q2, q5 and q9 still reasoned out from the stem". Never run a third round, and never report a failing set as a pass.

## 8. The teachability reader

It answers the quiz from the page alone, at `full` depth. If it can't, the page doesn't teach what the quiz asks, or a key is wrong. It must pass the intent and `test` questions as well as the code ones: a miss there is a gap in `asked.html`, `proven.html` or the trace.
- **Agent:** the teachability reader of `SKILL.md` "Roles".
- **Input:** `python3 -I <SKILL>/scripts/check-explainer.py <DIR> --teach > <DIR>/review/teach.txt`. The agent reads that one file.
- **Prompt:** section C of `assets/briefs/verify-brief.md`. Save the reply as `<DIR>/review/teach.md`.
- **Threshold:** N/N. Triage each miss as one of:
  - a gap in the page → fix the section;
  - two defensible options → fix the question;
  - a wrong key → re-read the code at head, or the source for an intent key, and fix the key. If the code itself looks wrong, that is an open question for the author, never a quiz trick.
- A cited heading that differs from the section the question's `chapter` names means the link is wrong: fix `chapter`.
- A question the reader tags `label` (it needed an id, a hash, a number or an exit code, not understanding) → rewrite it in plain words (§4), even when the reader got it right.

**Reading the two results together:**

| Blind | Teach | Meaning |
|---|---|---|
| low | N/N | The quiz measures what the page teaches |
| high | any | A leak, or a general-knowledge question |
| any | below N/N | A gap in the page, or a wrong key |

Re-runs after edits: `write.md` §16 step 6.

## 9. The gate

**Pass:** every question right on the first pick (the **first try**), or each first-try miss cleared by explaining it to Claude. The rule: don't build on the ask, send the code on, or review someone else's, until you pass. "First try n/N" is the score's name everywhere: on the page, in the result line, in `artifact.md` and in your hand-off.

### On the page

The engine does all of this; nothing to author. Quoted text is the page's own wording.
- **The quiz's intro:** "5 questions. Pick one answer each: only your first pick counts." (with checkpoints: "7 questions in all (5 here, 2 at piece ends)"), then "Your first picks are saved privately for you; nobody else can read them."
- **A pick** locks the question, marks "✓ Correct", "✓ The answer" and "✗ Your pick", and shows "Correct." or "Not quite.", where it is decided ("It is decided in ③ the release job.", "See ④ the tests.", "See What was asked."), the pick's feedback, "The answer is c. …" on a miss, a closed "Why not the others?" and a closed "Evidence". Re-clicking never counts. First picks persist in that browser, keyed by `built_from` and the questions.
- **The counters:** the bar's pill reads "Quiz 2/5" until every question has a first pick, then "First try 4/5" (its tooltip: "Go to the quiz · First try 4/5 · explain your misses to Claude" when any missed). Start here's last step reads "Answer 5 questions · ~3 min" with "2/5", then "First try" with "4/5" and "· explain your misses to Claude".
- **The result line** (Copy result, under the quiz): `understand quiz abc1234: first try 4/5 · q1 c ✓ · q2 a ✓ · q3 b ✗ (key d) · q4 b ✓ · q5 c ✓`.
- **After every question has a first pick,** a box under the questions, the same for every reader whatever `plan.json` `mode` says:
  - with misses, the heading "Explain your misses to Claude", then: "First try 4/5. To clear it, paste your result [Copy result] into a Claude Code session running `/skunexus-understand ABC-123` and explain, in your own words, why the answer to q3 is what it is. Claude checks each explanation against the code." (several misses: "To clear them, …, why each of the 2 answers is what it is."); then "Re-read first: ③ the release job (q3)" (with more misses, "③ the release job (q3) · What was asked (q1)"), one link per piece or row the missed questions' `chapter` names; and, only where the page can save results, "Your result is also saved privately for you on this page, so Claude can read it without the paste.";
  - with none missed, "Done: you’ve checked your understanding of this change", then "First try 5/5. Go deeper ↓".
- **The saved result.** On the published page, once every question has a first pick, the page writes `{<built_from>: {line, correct, total, at}}` to `results/<viewer id>`, which only that viewer can read, the owner included. A view-only visitor can't write, so their picks stay in the browser. A local `file://` page saves nothing.

### Practice and the two resets

Each erases one kind of progress, says so in its tooltip, and shows its effect on the page (never only to a screen reader):

| Control | Where | Erases | Keeps |
|---|---|---|---|
| **Practice reset** | Under the quiz. Its hint, beside it and in its tooltip: "Practice reset: hides your answers so you can try again. Your first try (4/5) stays your score; reloading the page shows it again. To erase your first try, use Options → Reset quiz." | Nothing stored: it hides the answers for a practice round. A banner says "Practice round: your first try, 4/5, is still your score. Answers here are for practice and aren’t saved.", counts "practice: 1/5 answered", and offers "Show my first try". A question with no first pick yet still counts as the first try | The first try, the saved result, everything else |
| **Reset quiz** | Options; two clicks within 3 seconds ("Click again to erase your quiz answers and first-try result (Viewed files and read ticks are kept)") | This build's first picks and result, the "result saved" flag, and the saved result's entry for this build (read the doc, drop the `<built_from>` key, write the rest back, or delete the doc when nothing is left) | Viewed files, "I've read this piece" ticks, the layout |
| **Reset reading progress** | Options; two clicks ("Click again to reset") | The "I've read this piece" ticks and the Viewed marks | The quiz answers, the first try and the saved result, the layout |

**The pending-wipe flag.** Reset quiz stores `wipe:<built_from>:<questions>` in the browser before it touches the saved result, and clears it only once the wipe succeeds. A reset clicked before the page's saved-result store is ready (or one that fails) keeps the flag, and the next load that reaches the store wipes the entry then, unless a new complete first try has been taken since: its own write replaces the entry, and the flag is dropped.

### Clearing a miss

The developer comes back to you in a Claude Code session running `/skunexus-understand <KEY>` (or this one), with the result pasted, or asks you to read it: then list `results` with `ArtifactData` (`publish.md` "Reading the result back").
1. Name the question and the piece or row it was decided in. Ask the developer to explain, in their own words, why the key is right and why their pick isn't. Seeing the key already is fine: explaining the mechanism is the test.
2. Re-read the question's evidence at head, then grade on substance, not phrasing, against the feedback and the evidence.
3. Cleared: the explanation states the mechanism, or for an intent question the rule and its reason, not just the answer. Not cleared: point to the piece or the section (and, for you, the `file:line` or the artifact id), and ask one follow-up on the gap. After two tries, say "not cleared yet: re-read <the piece or section, by its badge and name or heading>" and stop.
4. Record a clear only when you witnessed it.

**Reviewer use.** The same page serves a reviewer, as an optional self-check before opening the diff, with the same wording. Their misses point at an unclear section, a surprising design or a gap in the proof; raising them as PR comments is their call. Nobody sees another viewer's picks or result, so the author never grades a reviewer and a reviewer is never primed. A reviewer who wants an independent page runs this skill on the PR in reviewer mode.

## 10. Recording the result

- **Read it** from `ArtifactData` (list the `results` collection of the published page; you see only the developer's own document) or from a result line the developer pastes. `references/publish.md` "Reading the result back" has the calls.
- **Verify it:** its SHA equals the page's `built_from`; each pick checks against `quiz.json`'s `answer`; the count matches.
- **Record one line** in the Quiz cell of `artifact.md`'s row for that head: `first try 5/5 · 2026-11-10`, or `first try 4/5; q3 cleared · 2026-11-10`. A row with no result reads `not taken`.
- **Stale:** `skunexus-backend-pr` Step 0.4 quotes the newest row's Quiz cell and marks it stale when that row's head (its `Scanned` cell) is not the branch's HEAD. In your own hand-off, say "passed at `abc1234`, 3 commits since".
- **Never infer a pass** and never write a result you weren't given. It is a self-report, and nothing needs to make it more than that: no hashes, no completion codes.
- **Only the developer's own result** goes in the file.
