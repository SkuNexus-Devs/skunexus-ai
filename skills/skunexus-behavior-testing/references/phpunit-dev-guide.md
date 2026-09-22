# Writing a SkuNexus test — developer guide

**PHPUnit class syntax is the default in `skunexus-be-core`;** client repos author in Pest — their version
of this guide is `pest-dev-guide.md`, alongside this file. This doc says *what you type*; the full
convention with rationale — and the normative word on every rule here — is `phpunit-style-guide.md`,
alongside this file.

---

## 1. The default rule

> **One bus-level (or endpoint-level) test per behavior. Assert read-side state. Doubles only at external
> boundaries.**

Everything else in this guide is mechanics for that rule. If you remember one review question, make it:
*read the test name and body aloud — did you just hear the behavior contract?*

## 2. Where does my test go?

Two test styles appear in this guide:

- **GWT (Given/When/Then)** — the behavior-test style: *given* a world state, *when* one domain action
  runs, *then* the outcome is asserted through the read side. §3's grammar enforces it — every body line
  starts with `given`, `when`, or `assert` — so the test reads back as its own spec (`--testdox`).
- **AAA (Arrange–Act–Assert)** — the classic unit-test layout: build the inputs, call the code, assert
  the output. Three plain blocks, no vocabulary, no `given()` markers — for pure units, input → output
  already is the contract.

| You are testing… | Put it in | Extend | Style |
|---|---|---|---|
| a command's behavior (the normal case) | `tests/Feature/` | `SkuNexus\Core\Tests\TestCase` | GWT grammar (§3) |
| a GraphQL projection | `tests/Feature/GraphQL/` | `Feature\GraphQL\TestCase` | GWT grammar |
| a value object / pure algorithm | `tests/Unit/` | `PHPUnit\Framework\TestCase` (raw) | plain AAA, no ceremony |
| a multi-command business pipeline | `tests/Integrations/` | `Integrations\TestCase` | compose behavior traits |

Pure units get **no** GWT apparatus — input → output already is the contract (style guide §6). The
apparatus earns its keep where the world is wide.

## 3. The recipe — a new behavior test in 7 steps

Worked example to copy from: the annotated anatomy in `phpunit-style-guide.md` §2 and its copyable skeleton (§7).

1. **Write the scenarios in English first, as a committed skeleton.** Test names are the scenario titles;
   bodies hold the Given/When/Then sentence in `markTestIncomplete()` until implemented
   (style guide §8). The skeleton is runnable, reviewable, and self-deleting.

   ```php
   #[Test]
   public function put_away_is_rejected_when_the_product_was_never_received(): void
   {
       $this->markTestIncomplete(
           'Given a receiving cart with received coffee and tea,'
           . ' when a put-away asks for a product that was never received;'
           . ' then it is rejected and nothing is written.'
       );
   }
   ```

2. **Name every test as a falsifiable proposition.** `#[Test]` + snake_case, subject–verb–outcome:
   `put_away_moves_the_received_stock_into_the_put_away_location`. Banned words: *works, correctly,
   properly, successfully, should*.

3. **Put the shared Given in `setUp` — state only, in vocabulary sentences.** Never dispatch the command
   under test there, never assert there.

   ```php
   $this->warehouse = $this->aWarehouse();
   $this->cart      = $this->aReceivingCart($this->warehouse);
   $this->coffee    = $this->anActiveProduct(named: 'coffee');
   $this->receiveIntoCart($this->cart, $this->coffee, qty: 10, in: $this->warehouse);
   ```

4. **State the When once, as a private `when<DomainVerb>()` method** dispatching through `$this->bus()`.
   Dispatch only — it returns the result and never asserts. One When per test, visible in every body.

5. **Assert through the read-side, in domain language.** `assertPutAwayLocationHolds($warehouse, $coffee,
   qty: 10)` — never a bare `assertEquals` mismatch dump, never a spy on dispatched sub-commands. Positive
   state assertions only: `assertOrderRemainsInFulfillment(...)`, never `assertNotEquals(Closed, ...)`
   (which passes for every wrong state).

6. **Per-test variations are Given deltas, marked `given`.** Inline for one-off instances, named method
   when the delta states the rule in the test's name:

   ```php
   $this->given(fn () => $this->completeFulfillment($this->shipment));   // Form 1 — inline
   $this->givenThePutAwayAsksForAProductThatWasNeverReceived();          // Form 2 — named
   ```

7. **Exception outcomes use `assertThrows`, not `expectException`** — execution continues past the throw,
   so the guard's second clause ("…and nothing is written") lives in the same test:

   ```php
   $this->assertThrows(fn () => $this->whenCreatePutAway(), StockNotFoundException::class);
   $this->assertNoPutAwayFulfillmentExists($this->cart);
   ```

**The body grammar is total: every line in a test body starts with `given`, `when`, or `assert`.**
That is mechanically lintable, and it makes `--testdox` output read as the spec.

## 4. The vocabulary — where words live

Every noun in your scenarios is a builder; every Then is a domain assertion. They live in
**`tests/Behavior/`**, flat, per domain:

| Piece | Naming | Landed example |
|---|---|---|
| Scenario trait, per domain | `{Domain}ScenarioTrait` — `a…()` creates, `the…()` retrieves, verb phrase = Given-action | `ReceivingScenarioTrait::aReceivingCart()`, `OrderFulfillmentScenarioTrait::anOrderInFulfillment()` |
| Assertion trait, per domain | `{Domain}AssertionsTrait` — `assert` + the scenario's sentence | `PutAwayAssertionsTrait::assertPutAwayLocationHolds()`, `OrderAssertionsTrait::assertOrderIsClosed()` |
| Shared assertions | `Behavior\DomainAssertionsTrait` — cross-domain state propositions | `assertOrderIsInState()`, `assertFulfillmentAssignedTo()` |
| Base `TestCase` | `bus()` accessor + the 3-line inline `given(Closure)` marker | `tests/TestCase.php` |

**The graduation ladder — nothing is created speculatively:**

```
file-private given*/when* wrappers            — never graduate (file-contract-specific)
  → {Domain}ScenarioTrait / {Domain}AssertionsTrait     — a word moves in when a second FILE needs it
    → Behavior\DomainAssertionsTrait               — an assertion moves up when a second DOMAIN needs it
```

Vocabulary grows **one word per test that needs it**. The wrong version of this project is a quarter
spent building a DSL nobody asked for.

**Domain gaps get one named home.** Where a scenario needs a raw write because no command exists (e.g. no
command sets a cart's department), the raw write lives in exactly one vocabulary method with a
`// DOMAIN GAP` comment — never copy-pasted per test. See `ReceivingScenarioTrait::aCartInDepartment()` and
`receiveIntoCart()`.

## 5. Readability rules (the short list)

1. **Correspondence**: every value in a Then traces to a visible line in the Given/When
   (`qty: 10` up top is why `qty: 10` below). Never let a factory default silently satisfy an assertion.
2. **Named arguments for literals**: `qty: 10`, `in: $warehouse`.
3. **No logic in test bodies**: no `if`, no `foreach` over assertions. Matrices → string-keyed
   `#[DataProvider]`.
4. **Budgets**: body ≤ ~12 lines, `setUp` ≤ ~10 vocabulary lines. Exceeding them means a vocabulary word
   is missing, not "split mechanically".
5. **Name your actors**: `$coffee`/`$tea`, `anActiveProduct(named: 'coffee')` — failures then speak the
   scenario ("Expected 10 of coffee…"), and swapped assertions are visibly wrong.
6. **Spec order**: happy paths first, then guards. Run `--testdox` on the file before committing — if a
   sentence reads wrong, the name is wrong.
7. **The shared Given reads as a world.** Its `// GIVEN` headline carries the settings the scenarios lean
   on, and harness calls there wear a vocabulary name (`theClockIsFixedAt($noon)`, not
   `Carbon::setTestNow($noon)`).

## 6. Five facts that surprise every new test author here

1. **Every test method gets a brand-new database.** Cross-test setup is impossible, ever.
2. **Real migrations never run in tests.** After adding a migration run
   `php artisan dump:schema-for-testing --env=testing` — the staleness window is a 10-minute wall clock.
3. **Testbench env hooks are inert.** We override `createApplication()`, so `defineEnvironment()`,
   `getPackageProviders()` and `#[WithConfig]` silently no-op. Use `bootstrappingCallbacks` instead.
4. **`Model::factory()->createDomain()` does not persist.** It returns a domain entity; you persist via the
   repository — or better, go through the bus so plugins and custom-field hooks run.
5. **`WithoutMiddleware` is global.** No HTTP test here proves anything about auth. Auth/CSRF/throttle
   coverage needs the ijhttp layer, not this suite.

## 7. Running

> Every command in this section is written host-style. In a repo that runs PHP only inside Docker, each one
> takes the runner prefix from the skill's Quick Reference ("Where PHP runs" — the repo's `CLAUDE.md` names
> it; e.g. `docker compose exec app vendor/bin/paratest`). Resolve it before the first command.

```bash
# the new suite alone (fast: full behavior coverage of two commands in ~3 s)
vendor/bin/phpunit --testsuite Behavior

# as a browsable spec document
vendor/bin/phpunit --testsuite Behavior --testdox

# everything, parallel
vendor/bin/paratest
```

## 8. When do I convert an OLD test to this system?

Nothing is rewritten proactively. The trigger is the test costing you something — and the move differs by
what broke:

| What just happened | What you do |
|---|---|
| A **mock-based handler test** failed because a constructor/collaborator changed (no behavior change) | **Convert**: write the same behavior as a bus-level test with vocabulary; delete the mock test. Don't repair the mocks. |
| A **Feature test** failed on fixture fragility (seeder count, factory default, unsorted `rows.N`) and the fix forced you to understand the whole arrange block | **Reshape**: rewrite the Given with vocabulary builders that pin exactly what the assertions depend on. |
| A **Feature test** failed because you intentionally changed the behavior | That's the test doing its job — update it in the same PR; adopt the grammar while you're in there if cheap. |
| A test never breaks | Never touch it. |

One-line repairs stay one-line repairs. The conversion pays for itself only when the repair bill arrives.
