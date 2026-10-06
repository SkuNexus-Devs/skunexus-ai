---
name: skunexus-tdd-testing
description: >-
  Use when driving new SkuNexus behavior test-first — a new command, plugin, transition, endpoint, or
  GraphQL field — and deciding what to test in what order. Do NOT use for: how to write, convert, name,
  or place a test (that is skunexus-behavior-testing), debugging failing tests, QA testing steps
  (separate skill), turning requirements into the task breakdown this loop implements
  (skunexus-backend-plan), executing planned work that is not being driven test-first
  (skunexus-backend-implement), rendering the finished tests as a spec (skunexus-spec-extract), or PR
  descriptions (skunexus-backend-pr). Triggered by: TDD, red-green-refactor, test-first, scenario
  skeleton, markTestIncomplete, tracer bullet, vertical slice, spec before code.
user-invocable: true
---

# TDD in SN

**Core principle:** The unit of TDD in SN is the **command** (or endpoint), not the file — and propositions come before code. The contract (`prd.md` §6 → `investigation.md` → the plan's Goal & Acceptance) leads; the skeleton is its acceptance bullets restated as test titles; implementation proceeds one vertical slice at a time.

**Announce at start:** "I'm using the skunexus-tdd-testing skill to drive `<behavior>` test-first."

**How you reach it:** inside the workflow, pick **full TDD** once when `skunexus-backend-implement` asks for the testing mode — it loads this skill per task itself; you never invoke it task by task. Outside a plan, say *test-first* / *TDD this* and it triggers on the phrasing; `/skunexus-tdd-testing` is only for when it didn't. It never competes with `skunexus-behavior-testing` — it loads it.

**Violating the letter of this rule is violating the spirit of this rule.**

## The Iron Law

```
NO IMPLEMENTATION WITHOUT A WATCHED RED — NO NEXT BODY UNTIL THIS ONE IS GREEN
```

A test whose failing run was never watched proves nothing about the implementation that follows; a second body written before green describes imagined behavior.

Every test this loop drives is **written per `skunexus-behavior-testing`** — grammar, naming, vocabulary, placement, data setup, assertions, and mocking rules all live there. Load it before writing the first test body. This skill owns only the *order*: what gets tested, when. That includes the syntax: Pest where the repo has it, PHPUnit class syntax otherwise — that skill's detection rule decides.

## The Loop

### Step 0 — Proposition skeleton (in the test file)

Before any test code, commit one runnable placeholder per acceptance bullet the task cites — never a standing `.md` beside the test (the form is the style guide's §8):

```php
test('split order closes when its last fulfillment completes', function () {
    $this->markTestIncomplete('R4.a');   // no contract file: the approved Given/When/Then sentence instead
});
```

(PHPUnit — core: the same in a `#[Test]` snake_case method.)

- Test descriptions (Pest) / method names (PHPUnit) restate the cited bullets as falsifiable propositions (naming rules: `skunexus-behavior-testing`). The body **cites the bullet ID, never copies its text** — the sentence stays in the contract.
- **No contract file** (a standalone "TDD this"): state each proposition as a Given/When/Then sentence and get the developer's yes before committing the skeleton — that sentence *is* the agreed behavior, so it goes in the placeholder.
- The runner renders the proposition list before any code exists (Pest prints descriptions by default; `--testdox` in PHPUnit); the skeleton is the first commit of the loop, reviewable as the proof list.
- The skeleton is **self-deleting**: implementing a test replaces the placeholder with the role-marked body that proves the bullet, so nothing is left to drift.
- **Batching titles up front is not horizontal slicing.** Bodies and implementations still go one slice at a time.

### RED — implement the next skeleton body, watch it fail

Replace one `markTestIncomplete` with a real body. Two valid red states:

1. **Wiring missing** — the Command class does not exist, or the provider entry is absent. Wiring counts as part of "implementation"; "code doesn't exist" is a valid red, not a broken test.
2. **Behavior missing** — everything dispatches, but the observable outcome does not happen yet.

Expect first REDs to also surface **plan-vs-codebase mismatches** — wrong interface, wrong method name, wrong constructor shape. Corrections made to the test's assumptions before any implementation exists are the loop paying for itself.

### GREEN — minimum to pass

Create Command + Handler + provider entry; implement just enough handler logic to satisfy the assertion. Resist adding the next behavior in the same change.

### REFACTOR — only on green

- Extract sub-commands (handler doing two things → split).
- Push cross-cutting side effects into a plugin.
- Extract repositories/factories, moving the binding to the interface provider.
- **Vocabulary graduation** — promote test helpers that earned reuse; the ladder and mechanics live in `skunexus-behavior-testing`.

Tests stay green through all of it because the command/endpoint-level contract is unchanged.

## Vertical Slicing

A slice is **one command (or one endpoint), all its files, end-to-end** — then the next. The horizontal anti-pattern is especially tempting in SN because the wiring boilerplate feels batchable: batched provider entries silently miss plugins, transitions, and listeners, and batched test bodies describe imagined behavior that cannot catch the omissions.

```
WRONG (horizontal):  body1, body2, body3 → impl1, impl2, impl3
RIGHT (vertical):    titles as skeleton → body1 → impl1 → body2 → impl2 → …
```

## Tracer Bullet — the First Slice of Any New Feature

The first skeleton scenario to implement is a **tracer**: minimal assertion, maximal coverage of the composition.

```php
test('doing x moves the entity to in progress', function () {
    $entity = $this->anEntityInState(Open::class);

    whenDoX($entity);   // namespaced file-level function → test()->bus()->handle(new DoXCommand(…))

    $this->assertEntityIsInState(new InProgress(), $entity);
});
```

Progression: run RED (Command class missing — fatal) → create Command + Handler skeletons + provider entry → run RED again (handler empty, state unchanged) → add minimum logic → GREEN.

One tracer proves: provider order is correct, the command is dispatchable, no middleware rejects it, the handler runs, DI resolves. Every later test builds on that proven path — a later failure points at the new behavior, not the wiring. Skipping the tracer means debugging multiple unknowns when the third or fourth test fails.

## Before Each RED — Ask First

1. **Can the scenario be stated as one Given/When/Then sentence?** If not, the behavior is not understood yet — no code until it can be. With a contract that sentence is the cited bullet (and a bullet that can't be stated this way is a contract question); without one it is the developer-approved placeholder.
2. **What is the *one* observable outcome?** State change, queued follow-up, response shape — name one. A second sentence of outcome is a second test.
3. **Is wiring allowed to be the red?** For a new command/field/plugin, "Command class missing" and "provider entry missing" are both valid reds — don't conflate "code doesn't exist" with "test is wrong."
4. **Is the slice vertical?** One command (or endpoint), all its wiring, end-to-end — not one layer across many commands.

## Red Flags — STOP and Course-Correct

| Thought | Course correction |
|---------|-------------------|
| "I'll batch-write 8 command test bodies, implement after." | Horizontal slice. Batch the skeleton *titles*, then one body → one implementation → repeat. |
| "I'll skip the test for wiring — I can see it works." | Provider-order and missing-listener bugs are the dominant SN failure mode; the tracer catches them, visual inspection doesn't. |
| "While it's green I'll add the next behavior too." | GREEN is minimum-to-pass. The next behavior is the next slice's red. |
| "I'll keep the scenarios in a `.md` next to the test file." | The contract already has them; the test file holds a `markTestIncomplete` skeleton citing their IDs — runnable, reviewable, self-deleting. |

## When Things Go Wrong

| Situation | Action |
|-----------|--------|
| The first RED fails with a different error than expected (wrong interface, method name, signature) | A plan-vs-codebase mismatch is surfacing — the loop's documented early payoff. Correct the test's assumptions first; implement only once the red fails for the *stated* reason. |
| GREEN is unreachable without touching a second command | The slice was two slices. Split the scenario into two skeleton titles and re-slice vertically. |
| Mid-slice, the scenario sentence turns out to be wrong | If the title restates a cited PRD/plan acceptance bullet, this is a contract flag: the PRD (or inline acceptance) moves first, then the title — never a silent rename that lets the test outrun its contract. If the sentence was this loop's own, edit the title and GWT sentence, re-run RED, then implement against the corrected proposition. |
| A later test fails and no tracer was ever written | Multiple unknowns are entangled (new code? wiring? middleware?). Write the tracer now to re-prove the path, then debug the behavior on top of it. |

## NEVER Rules

- **NEVER write the full set of test *bodies* for a feature before implementing any of it.** Horizontal slicing produces tests of imagined behavior. Skeleton titles with `markTestIncomplete` placeholders may be batched; bodies go one vertical slice at a time: red → green → next.
- **NEVER refactor on red.** Sub-command extraction, plugin extraction, and vocabulary graduation happen only once the slice is green — otherwise there is no safety net proving the contract survived.

## Related Skills

- **REQUIRED:** `skunexus-behavior-testing` — every test this loop drives is written per that skill: body grammar, naming, vocabulary system, layer placement, data setup, assertions, mocking rules, test infrastructure.
- **UPSTREAM:** runs on request inside `skunexus-backend-implement`, when the developer asks to drive a task test-first; the acceptance bullets the plan's `Tests:` trailer cites become the skeleton titles — cited by ID, never copied or re-invented here. The loop never edits the plan; `skunexus-backend-implement` rewrites the trailer as landed once it closes.

This skill owns the *order* of testing work and stops there: it does not decide how a test is written (`skunexus-behavior-testing`), break requirements into tasks (`skunexus-backend-plan`), execute planned work that is not test-first (`skunexus-backend-implement`), or write QA testing steps (separate skill).
