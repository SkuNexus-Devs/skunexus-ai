# Writing a SkuNexus test — developer guide (Pest syntax)

**Pest is the default test syntax in client repos.** `skunexus-be-core` stays on PHPUnit class syntax —
its version of this guide is `phpunit-dev-guide.md`, alongside this file. This doc says *what you type*;
the full convention with rationale — and the normative word on every rule here — is
`pest-style-guide.md`, alongside this file.

---

## 1. The default rule

> **One bus-level (or endpoint-level) test per behavior. Assert read-side state. Doubles only at external
> boundaries.**

Unchanged by Pest — Pest changes the *typing*, not the doctrine. If you remember one review question,
make it: *read the test description and body aloud — did you just hear the behavior contract?*

## 2. Where does my test go?

| You are testing… | Put it in | Vocabulary via | Style |
|---|---|---|---|
| a command's behavior (the normal case) | `tests/Feature/` | `uses({Domain}ScenarioTrait::class)` | GWT grammar (§3) |
| a GraphQL projection | `tests/Feature/GraphQL/` | `uses(...)` + the GraphQL base | GWT grammar |
| a value object / pure algorithm | `tests/Unit/` | nothing | plain AAA, no ceremony |
| a multi-command business pipeline | `tests/Integrations/` | compose scenario traits | GWT grammar |

The base `TestCase` is bound once in `tests/Pest.php` (`pest()->extend(Tests\TestCase::class)->in('Feature')`),
not per file. Scenario traits are **not** bound folder-wide — each file declares its own world with
`uses()`. Pure units get **no** GWT apparatus — input → output already is the contract; higher-order test
chains (`it('…')->get('/')->…`) are acceptable there and nowhere else.

## 3. The recipe — a new behavior test in 7 steps

Worked example to copy from: the annotated anatomy in `pest-style-guide.md` §2 and its copyable skeleton (§7).

1. **Write the scenarios in English first, as a committed skeleton.** The description is the scenario
   title; the body holds the Given/When/Then sentence until implemented. Runnable, reviewable,
   self-deleting.

   ```php
   test('a pending rma cannot be force closed', function () {
       $this->markTestIncomplete(
           'Given an approved RMA with unreceived units;'
           . ' when it is force closed without approval;'
           . ' then it is rejected and the state does not move.'
       );
   });
   ```

2. **Name every test as a falsifiable proposition** — lowercase, spaced, subject–verb–outcome:
   `test('force closing an approved rma closes it', …)`. Banned words: *works, correctly, properly,
   successfully, should*. In Pest the description **is** the spec sentence — already authored prose, so
   tests never need a `#[TestDox]` escape hatch; the name has to carry it. (Helper functions still take
   `#[TestDox]` — §9.)

3. **Header + shared Given.** Keep the `namespace` (one per file — it makes the file's `const` and `when*`
   function namespaced, so cross-file collisions are structurally impossible). `uses()` attaches the
   vocabulary. `beforeEach()` is state only, in vocabulary sentences, under a `// GIVEN` headline — never
   dispatch the command under test there, never assert there.

   ```php
   namespace Tests\Feature\PestOrderRMA\CloseRma;

   uses(OrderRmaScenarioTrait::class);

   const NEVER_ARRIVED = 'the remaining units never arrived';

   beforeEach(function () {
       // GIVEN an approved RMA whose 4 warehouse-bound units are still unreceived
       $this->order   = $this->anOrderWithADispatchedShipment();
       [$this->shirt] = $this->theShippedDecisionItemsOf($this->order);

       $this->rmaId = $this->anRmaFor($this->order, [
           $this->aReturnLine($this->shirt, quantity: 4, routing: RoutingAction::RETURN_TO_WAREHOUSE),
       ])->getRmaId();
   });
   ```

   `$this` inside `test()`/`beforeEach()` closures is class-scoped — **private** trait methods and
   **protected** base methods are reachable. File consts are bare `const`; consts and actors shared
   across files live on the scenario trait, as trait constants and typed properties.

   A **file-level function** has none of that: no `$this`, no `self`. A trait constant cannot be
   reached through the trait name (`OrderRmaScenarioTrait::QTY` is a fatal `Cannot access trait constant
   … directly`), so it is `test()->target::QTY` — or better, a parameter passed `self::QTY` from the
   closure. The container is `app()->make(X::class)`, never `test()->app` (`$app` is protected on
   Laravel's `TestCase` and is not ours to widen).

   An auxiliary base case becomes a **trait**: Pest binds one test case class per file and `Pest.php`
   already bound `Tests\TestCase`, so `class GraphQLTestCase extends TestCase` → `trait
   GraphQLTestCase` + `uses(GraphQLTestCase::class)`.

   A namespaced file must `use` the global classes it names — `RuntimeException::class` otherwise
   resolves into the file's own namespace, silently, and the failure reads *"To contain:
   Tests\Feature\…\RuntimeException"*.

4. **State the When once, as ONE file-level `when<DomainVerb>()` function.** Dispatch wrapper only —
   named functions have no `$this`, so they reach the app through `test()`. Arguments are built with
   `$this->` at the call site, which keeps the scenario trait private.

   ```php
   function whenClose(string $reason): ClosedOrderRma
   {
       return test()->bus()->handle(new CloseRmaCommand(test()->rmaId, $reason))->getValue();
   }
   ```

5. **Assert through the read side, in domain language.** Higher-order expectations are the preferred
   shape for entity reads — subject, accessor, matcher: it reads as "the RMA's state is closed". Domain
   assertions stay `$this->assert*` trait calls. **One clause per sibling `expect()` statement — never
   `->and()` chains.**

   ```php
   expect($closed)->getState()->toBe(Closed::STATE);
   expect($this->theRma($this->rmaId))->getState()->toBe(Closed::STATE);
   ```

   Positive state assertions only: `assertOrderRemainsInFulfillment(...)`, never
   `assertNotEquals(Closed, ...)` (which passes for every wrong state).

6. **Per-test variations are Given deltas, marked with the bare `given()` function** (a 3-line global in
   `tests/Pest.php`). The `fn () => $this->…` delta captures the test closure's `$this`, so trait
   privacy holds:

   ```php
   given(fn () => $this->acceptEveryLineOf($this->rmaId));
   given(fn () => whenClose(NEVER_ARRIVED));   // a prior When, used as Given
   givenTheRmaIsApproved();                    // a given*-NAMED function is already marked — bare
   ```

   Never wrap a value-returning builder in `given()` — it returns `void`. And **never mark a step
   twice**: `given(fn () => givenTheRmaIsApproved())` renders *"the RMA is is givened approved"*,
   because the inner `given` is read as the sentence's verb. The name or the wrapper, not both —
   and don't "fix" it by stripping the prefix, which promotes the next word to verb instead.
   The bare call is also the only shape whose body is read one hop, for the `— by …` detail.

7. **Exception outcomes use `expect(fn () => …)->toThrow()`** — execution continues past the throw, so
   the guard's second clause ("…and the state did not move") lives in the same test:

   ```php
   expect(fn () => whenClose(NEVER_ARRIVED))->toThrow(RmaNotApprovedException::class);

   expect($this->theRma($this->rmaId))->getState()->toBe(Pending::STATE);   // positive — 'not closed' passes for every wrong state
   ```

Endpoint tests keep `$this->postJson(...)` / `$response->assertStatus(422)` — the HTTP layer is the When
there, no wrapper needed.

**The body grammar is total: every line in a test body starts with `given`, `when`, `expect`, or
`$this->assert`.** That is mechanically lintable, and it makes the runner's own output read as the spec.

## 4. The vocabulary — where words live

Every noun in your scenarios is a builder; every Then is a domain assertion. They live in
**`tests/Behavior/`**, flat, per domain — traits, exactly as under PHPUnit:

| Piece | Naming | Landed example |
|---|---|---|
| Scenario trait, per domain | `{Domain}ScenarioTrait` — `a…()` creates, `the…()` retrieves, verb phrase = Given-action | `OrderRmaScenarioTrait::anRmaFor()`, `OrderFulfillmentScenarioTrait::anOrderInFulfillment()` |
| Assertion trait, per domain | `{Domain}AssertionsTrait` — `assert` + the scenario's sentence | `PutAwayAssertionsTrait::assertPutAwayLocationHolds()` |
| Shared assertions | `Behavior\DomainAssertionsTrait` — cross-domain state propositions | `assertOrderIsInState()` |
| Base `TestCase` | `bus()` accessor (**public** — the `when*` functions reach it via `test()`) | `tests/TestCase.php` |
| Auxiliary base case | a **trait**, attached with `uses()` — Pest allows one test case class per file | `trait GraphQLTestCase` |
| The `given()` marker | 3-line global `function given(Closure $delta): void { $delta(); }` | `tests/Pest.php` |

**The graduation ladder — nothing is created speculatively:**

```
inline given() deltas + the file's when* function      — never graduate (file-contract-specific)
  → {Domain}ScenarioTrait / {Domain}AssertionsTrait              — a NAMED compound builder graduates as soon as
                                                          ONE file needs it (PHP has no file-private
                                                          functions; keep file-level globals to ~1–2)
    → Behavior\DomainAssertionsTrait                        — an assertion moves up when a second DOMAIN needs it
```

That middle rung is the one Pest changed: PHPUnit's file-private compound builders had a class to hide
in; here they would be globals, so they go straight to the domain trait.

**Domain gaps get one named home.** Where a scenario needs a raw write because no command exists, the raw
write lives in exactly one vocabulary method with a `// DOMAIN GAP` comment — never copy-pasted per test.

## 5. Readability rules (the short list)

1. **Correspondence**: every value in a Then traces to a visible line in the Given/When (`quantity: 4` up
   top is why `4` below). Never let a factory default silently satisfy an assertion.
2. **Named arguments for literals**: `quantity: 4`, `routing: RoutingAction::RETURN_TO_WAREHOUSE`.
3. **One clause per `expect()` statement.** `->and()` chains fuse independent propositions into one
   failure — sibling statements name the clause that broke.
4. **No logic in test bodies**: no `if`, no `foreach` over assertions. Matrices → string-keyed
   `->with([...])`; the keys become part of the description.
5. **Budgets**: body ≤ ~12 lines, `beforeEach` ≤ ~10 vocabulary lines. Exceeding them means a vocabulary
   word is missing, not "split mechanically".
6. **Name your actors**: `$shirt`, `anActiveProduct(named: 'coffee')` — failures then speak the scenario,
   and swapped assertions are visibly wrong.
7. **Spec order**: happy paths first, then guards. Read the runner output before committing — if a
   sentence reads wrong, the description is wrong.

## 6. Five facts that surprise every new test author here

None of these changed under Pest.

1. **Every test gets a brand-new database.** Cross-test setup is impossible, ever.
2. **Real migrations never run in tests.** After adding a migration run
   `php artisan dump:schema-for-testing --env=testing` — the staleness window is a 10-minute wall clock.
3. **Testbench env hooks are inert.** We override `createApplication()`, so `defineEnvironment()`,
   `getPackageProviders()` and `#[WithConfig]` silently no-op. Use `bootstrappingCallbacks` instead.
4. **`Model::factory()->createDomain()` does not persist.** It returns a domain entity; you persist via
   the repository — or better, go through the bus so plugins and custom-field hooks run.
5. **`WithoutMiddleware` is global.** No HTTP test here proves anything about auth. Auth/CSRF/throttle
   coverage needs the ijhttp layer, not this suite.

### Three more that only bite in Pest

1. **`test()` is a proxy, not the test case.** It forwards to `->target`, so `public` members work and
   `protected` ones do not — hence `app()` over `test()->app`, and `test()->target::CONST` for a trait
   const (§3). List-assignment through it is safe: `[test()->a, test()->b] = …` lands on the case.
2. **A dynamic property must be created before it is read.** `test()->cart ??= …` throws *Undefined
   property* — `??=` reads first. Assign residual per-file state in `beforeEach`, or promote it to a
   typed property on the scenario trait.
3. **A converted file keeps its namespace, so it needs its imports.** Missing `use RuntimeException;`
   turns a global class into a namespaced one that never existed, with no error until the assertion
   fails strangely.

## 7. Running

```bash
# everything (composer test now runs vendor/bin/pest)
composer test

# everything, parallel
vendor/bin/pest --parallel

# one file / one test
vendor/bin/pest tests/Feature/PestOrderRMA/CloseRmaTest.php
vendor/bin/pest --filter='force closing an approved rma closes it'
```

Pest's default output already prints the scenario descriptions — the `--testdox` equivalent, free.

**`vendor/bin/phpunit` no longer runs.** Installing Pest hijacks that binary; it errors with
`InvalidPestCommand`. Use `vendor/bin/pest`.

No Pest in the repo yet? The one-time install recipe (composer order, `tests/Pest.php`, script changes) is
`pest-style-guide.md` §0.1.

## 8. When do I convert an OLD PHPUnit test to Pest?

**Pest executes PHPUnit test classes natively** — the LO pilot ran the untouched 77-test OrderRMA suite
green under the Pest runner before a single file was converted. So nothing is rewritten proactively, and
a mixed tree is a normal steady state, not a migration in progress. The trigger is the test costing you
something — same table as the PHPUnit guide:

| What just happened | What you do |
|---|---|
| A **mock-based handler test** failed because a constructor/collaborator changed (no behavior change) | **Convert**: write the same behavior as a bus-level Pest test with vocabulary; delete the mock test. Don't repair the mocks. |
| A **Feature test** failed on fixture fragility (seeder count, factory default, unsorted `rows.N`) and the fix forced you to understand the whole arrange block | **Reshape**: rewrite the Given with vocabulary builders that pin exactly what the assertions depend on. |
| A **Feature test** failed because you intentionally changed the behavior | That's the test doing its job — update it in the same PR; adopt Pest while you're in there if cheap. |
| A test never breaks | Never touch it. |

One-line repairs stay one-line repairs. Two mechanical notes if you do convert: `--filter` selectors bound
to old method names break (descriptions replace them), and typed fixture properties become dynamic
properties — promote the ones shared across files to typed properties on the scenario trait.

Versions: PHP 8.2 caps us at Pest 3, so `uses()` is the spelling (Pest 5 documents `pest()->use(...)`).
Syntax written now migrates forward with the official upgrade Rector sets.

## 9. Your tests are the spec — spec-extract

`spec-extract` renders a test file as Given/When/Then markdown (deterministic AST extraction, no LLM) —
the artifact QA reads, the FE handoff quotes, the spec-vs-PRD review diffs.

**The Pest grammar has shipped** — `--mode` defaults to `pest`, `--mode=phpunit` reads a class-syntax
tree, and a converted 40-file suite extracts at parity with its PHPUnit original. Pass the extractor a
**directory**, not a shell glob: `tests/**` is expanded by bash and feeds it `TestCase.php` and
`Pest.php`, which render as junk sections.

The attachment points it reads: `uses()` + `beforeEach()` → Background; `test('description')` → the
scenario heading; bare `given(fn)` **or** a bare `givenX()` call → a Given step (the named call also
yields a `— by …` detail from one hop into its body); `when*()` around `bus()->handle(new XCommand)` →
the When; `expect()` / `$this->assert*` → Then clauses; `->toThrow(X::class, MESSAGE)` → the rejection
plus its message; `->with([...])` string keys or `->with('name')` + `dataset('name', fn)` → the
**Where** step; `test()->target::CONST` → the constant's value.

What decides whether the output reads as English — none of it changes how Pest runs the test:

| Do | Because |
|---|---|
| keep the `when*` function one hop above `bus()->handle(...)` | two hops deep the spec reads the wrapper's name, not the command |
| keep assertions at top level — no loops/closures/`try` around them (§5.4 bans them anyway) | the extractor can't see inside; the scenario renders as unread |
| name custom assertions as sentences — end on a copula or a preposition (`assertHospitalIssueIs`, `assertNoAllocationsFor`) | the subject promotes: "the fulfillment's hospital issue is 'withdrawn'"; otherwise it renders raw |
| give `markTestSkipped(...)` its reason; name `->with([...])` cases with string keys | the reason renders as a not-running marker; the keys become the **Where** step |
| put `#[TestDox('{param} …')]` on a file-level `assert*`/`when*` helper whose derived prose reads wrong | legal PHP on functions, inert to Pest — the same override channel as on PHPUnit helper methods; test headings never need it (the description is already authored prose) |

A domain word that inflects wrong in *every* suite ("unholded") is a one-line dialect-config entry in the
extractor repo — file it there once, with the word and where it renders wrong. Never work around grammar
in the test, and never add a dialect word for one test's prose.
