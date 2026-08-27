---
name: skunexus-behavior-testing
description: >-
  Use when writing, converting, reshaping, naming, or placing any SkuNexus test — commands, plugins,
  transitions, vendor overrides, GraphQL fields, endpoints — or deciding test layer, data setup,
  assertions, or what to mock. Do NOT use for: driving new behavior test-first (that's
  skunexus-tdd-testing), debugging failing tests, QA testing steps (separate skill), planning or
  breaking down the work the tests cover (skunexus-backend-plan), writing the production code the
  tests exercise (skunexus-backend-implement), rendering a finished suite as a Given/When/Then spec
  (skunexus-spec-extract), or PR descriptions (skunexus-backend-pr). Triggered by: Feature test,
  PHPUnit, Pest, test(), expect(), uses(), beforeEach, bus->handle, Bus::fake, rebootHandlers,
  Given/When/Then, tests/Behavior, test naming, what to mock. ALSO use for the second pass over a landed
  suite whose rendered spec reads as machine transcript — "improve spec readability", "the spec-from-tests
  is unreadable", "the Given is missing the differentiator", "spec readability pass", "phrase dump", "TestDox
  slot" — which audits, FIXES the tests, verifies, and hands the extractor a change-request list.
user-invocable: true
---

# SN Behavior Testing

**Core principle, two halves:**

1. **Tests verify behavior through SN's public interfaces** — the command bus and HTTP/GraphQL endpoints — not handler internals or provider-array contents. The unit of testing in SN is the **command** (or endpoint), not the file. A test that survives an internal refactor was testing behavior; one that breaks was testing implementation.
2. **The contract must SCREAM.** The test is the only place a command's behavior contract exists in readable form — in `src/` it is scattered across Command, Handler, plugin chain, transition, and provider entry. A behavior-coupled test whose body is buried in plumbing has thrown away half its value. Name states the rule; body demonstrates it; nothing else is visible.

**Announce at start:** "I'm using the skunexus-behavior-testing skill to write/convert/reshape tests for `<behavior>`."

The enforcement question over everything below: **read the test name and body aloud — do they state the behavior contract?**

**Two syntaxes, one doctrine.** Pest is the default authoring syntax (client repos; `composer test` runs `vendor/bin/pest`). PHPUnit class syntax remains fully supported and is the default in core (`skunexus-be-core`) and any repo where Pest isn't installed. Detect by repo: `vendor/bin/pest` exists, or composer.json's `test` script runs pest → Pest; otherwise PHPUnit. Everything in this skill is syntax-neutral doctrine; only the shell differs.

| | PHPUnit (core) | Pest (client repos — default) |
|---|---|---|
| File shape | class extending `TestCase` | classless file — **`namespace` kept** (collision-proofs helpers/consts) |
| Vocabulary traits | `use {Domain}ScenarioTrait;` | `uses({Domain}ScenarioTrait::class);` |
| Shared Given | `setUp()` | `beforeEach(function () { … })` |
| Given delta | `$this->given(fn () => …)` or named private `given*()` | bare `given(fn () => …)` (3-line global in `tests/Pest.php`) |
| The When | private `when*()` method | one namespaced file-level `when*()` function via `test()->bus()` |
| Test declaration | `#[Test]` + `snake_case` method | `test('lowercase spaced proposition', function () { … })` |
| Entity-read Then | domain assertion / `assertSame` | `expect($x)->getAccessor()->toBe(…)` (higher-order) — one clause per sibling `expect()`, never `->and()` chains; domain assertions stay `$this->assert*` |
| Exception Then | `$this->assertThrows(fn, X::class)` | `expect(fn () => …)->toThrow(X::class)` (post-throw asserts follow as siblings) |
| File constants | `private const` | bare file-level `const` (namespaced); shared → trait constants |

`$this` inside `test()`/`beforeEach()` closures is class-scoped — private trait methods and protected base-`TestCase` methods stay reachable. Named file-level functions have no `$this` and use `test()` instead, which is why `bus()` is public. Pest runs PHPUnit classes natively (pilot: 77/77 green unmodified), so mixed trees are normal — never convert a suite as a prerequisite to anything. Repo has no Pest installed yet? The one-time setup — the phpunit/testbench knot, the patches workflow's `sebastian/diff` dependency, `tests/Pest.php` — is `references/pest-style-guide.md` §0.1; follow it, don't improvise the composer dance.

**The name is the contract; the body must prove exactly it — no more, no less.** Auditing a landed suite against its own names surfaced eight recurring leaks: a name promising a state while the body asserts `assertNotSame`; a noun the fixture never built; the deciding assertion hidden in a `the*` helper's `fail()`; a two-clause name with one clause proved; `assertArrayHasKey` standing in for a value; an unasserted qualifier ("…for the returned units"); "every" with one instance in the fixture; `assertGreaterThan(0, …)` where the Given fixed the number. Each reads correct in `--testdox` and passes review, which is why the check has to be explicit: the cures and the greps that catch them are the style guide §5.8 (`pest-style-guide.md` / `phpunit-style-guide.md`, matching the suite's syntax) — the promise ledger. Run it before renaming a test and before trusting someone else's suite.

**Source docs.** This skill is the authoring doctrine; the full convention, per syntax, is the two style guides shipped with it — `references/pest-style-guide.md` (Pest, the client-repo default) and `references/phpunit-style-guide.md` (PHPUnit, core). Each is self-contained and normative: the grammar, the naming and builder-article rules, the vocabulary graduation ladder, the promise ledger (§5.8), the extractor guidance (§10), and a copyable skeleton to start from.

## Overview — Why File-Level Testing Doesn't Fit SN

SN is a command-bus + provider-driven Laravel app. A "feature" is rarely one file — the smallest behavior-bearing change typically spans the Command class, the Handler, a `*CommandsProvider::COMMAND_HANDLERS` entry (without which the feature does not exist), and optionally `PLUGINS`, `*StateProvider::TRANSITIONS`, `*InterfaceProvider::SINGLETONS`, and a `*GraphQLProvider` listener.

A unit test that calls `(new XHandler($dep))($cmd)` skips `TransactionMiddleware`, `FirstCommandOnlyAclMiddleware`, `CustomFieldsGuardMiddleware`, every plugin registered against the command, and the deferred-resolution chain. It tests a fiction. If the code can't be invoked that way in production, tests must not pretend otherwise.

The right test unit is one of two things:

1. **`$this->bus()->handle(new XCommand([...]))`** — exercises the real composition (middleware, plugins, handler, sub-commands, events). `bus()` is the base-`TestCase` accessor (`tests/TestCase.php`); one accessor, never `app()`/`container()` variants.
2. **`$this->post('api/query', [...])`** or `$this->postJson('/api/...', [...])` — exercises the HTTP/GraphQL public surface end-to-end, mirroring what FE/integrators see.

## The Body Grammar — Summary

One file = one behavior surface (one command, one endpoint, one pure algorithm). The file name is the subject, the test names are its promises, the runner's description list of the file (`--testdox` in PHPUnit, default output in Pest) is its spec.

- **The grammar is total: every line in a test body starts with `given`, `when`, or a Then marker — `assert`, plus `expect` in Pest.** Mechanically lintable; documentation extraction becomes a name-splitter.
- **`setUp` / `beforeEach` holds the shared Given — state only.** Every test in the file must want all of it. Never dispatch the command under test there: the body loses its verb, arrange-failures blur with contract-failures, and no guard or variant test can exist once it has acted.
- **One When per test, one line** — a `when<DomainVerb>()` wrapper (private method in PHPUnit; one namespaced file-level function in Pest) wrapping the bus dispatch or POST. Given deltas open the body, marked `given` (inline closure or named method).
- **The Then asserts one contract clause through the read-side.** A clause is a sentence, not an assertion; a second sentence is a second test.
- **A test name is a falsifiable proposition** — `#[Test]` + snake_case, present tense, subject–verb–outcome (Pest: the `test('…')` description — same proposition, lowercase and spaced). Banned words: *works, correctly, properly, successfully, should*.
- **Actors get distinguishable names** — `$coffee`/`$tea`, never `$product1`/`$product2`; type-identical pairs are where silent transposition hides.
- **Pure unit tests (VOs, algorithms) skip the ceremony** — plain AAA, no `setUp`, no vocabulary; input → output already is the contract. The apparatus earns its keep in container-backed Feature tests.

**MANDATORY: before writing, converting, or renaming any test in `tests/Feature/`, `tests/Feature/GraphQL/`, or `tests/Integrations/`, read the style guide matching the repo's syntax — `references/pest-style-guide.md` (Pest, the default) or `references/phpunit-style-guide.md` (PHPUnit — core).** It holds the full grammar (Given-delta forms, `assertThrows` vs `expectException`), the naming and builder-article rules, readability rules and budgets, the promise ledger (§5.8 — name-vs-body audit and its greps), the graduation ladder, and the copyable skeleton. Do not reproduce those from memory.

**New to this convention?** Read `references/<syntax>-dev-guide.md` first — the 7-step recipe, the facts that surprise new authors, how to run, when to convert an old test; it is the on-ramp, and the matching style guide stays the mandatory normative read that wins on any conflict.

**Skip loading it** when writing a pure unit test (plain AAA, no ceremony) or when only running/diagnosing existing tests without editing their bodies.

## The Vocabulary — `tests/Behavior/`

The scenario vocabulary and domain assertions are the part of the system that matters and cannot be bought. It lives in a flat `tests/Behavior/`, two tiers plus base-class additions:

| Piece | Naming | Example |
|---|---|---|
| Scenario trait, per domain | `{Domain}ScenarioTrait` — article grammar: `a…()`/`an…()` **creates**, `the…()` **retrieves** what the seed guarantees, verb phrase = **Given-action** | `ReceivingScenarioTrait::aReceivingCart()`, `receiveIntoCart(...)` |
| Assertion trait, per domain | `{Domain}AssertionsTrait` — `assert` + the scenario's sentence, failing in domain language | `PutAwayAssertionsTrait::assertPutAwayLocationHolds()` |
| Shared assertions | `Behavior\DomainAssertionsTrait` — state propositions, cross-domain reads | `assertOrderIsInState()`, `assertFulfillmentAssignedTo()` |
| Base `TestCase` additions | `bus()` accessor (public in Pest repos so file-level `when*` functions reach it via `test()`) + the 3-line inline `given(Closure)` marker — `$this->given()` in PHPUnit, bare global `given()` from `tests/Pest.php` in Pest | `tests/TestCase.php`, `tests/Pest.php` |

Rules:

- **Every trait name ends in `Trait`, and its file matches** — `{Domain}ScenarioTrait`, `{Domain}AssertionsTrait`, shared `DomainAssertionsTrait`, `tests/Behavior/ReceivingScenarioTrait.php`. Team convention (POC review): a `use`/`uses()` line names traits, and the suffix is what tells a reader at a glance that the word came from vocabulary and not from a base class. Rename on sight; no un-suffixed trait survives a file you touch.
- **Vocabulary grows one word per test that needs it — never speculatively.** The wrong version of this system is a quarter spent building a DSL nobody asked for.
- **Graduation ladder:** file-private `given*`/`when*` wrappers never graduate (contract-specific one-liners over vocabulary); a builder moves into `{Domain}ScenarioTrait` when a **second file** needs it; an assertion moves into shared `DomainAssertionsTrait` when a **second domain** needs it. Every promotion is triggered by the second consumer arriving. **Pest amendment:** the bottom rung is the inline `given()` delta plus the file's namespaced `when*` function (never graduate); a NAMED compound builder graduates into `{Domain}ScenarioTrait` as soon as a Pest file needs it — PHP has no file-private named functions, so don't multiply namespaced globals. Keep file-level functions to ~1–2 per file; everything else routes through `$this`.
- **Builders go through the bus where it matters** — e.g. `anActiveProduct()` dispatches `CreateProductCommand` so plugins and custom-field hooks run and downstream commands see a production-indistinguishable product.
- **Domain gaps get exactly one named home.** Where setup has no domain command (no command sets a cart's department, none links received stock to a cart), the raw write lives inside ONE scenario builder with a `// DOMAIN GAP` comment naming the missing command — never inline in a test body, never copy-pasted per test. File the gap upstream (README §6.3).
- **A test file whose world spans domains composes several scenario traits.**
- **No labeled DSL.** The `given()` marker carries no string label (nothing to drift) and no value threading (state stays in properties). The runner's description list of proposition names is the documentation output; a runtime `given(fn, 'A Warehouse')` DSL is in-house Behat and declined.

### Fulfillment fixture — `aFulfillmentInState()`

Tests that exercise behavior on a fulfillment in a known state (guard checks, audit logs, GraphQL field reads) need a fixture. First built in a real implementation as `FulfillmentManagementTrait::aFulfillmentInState(StateClass::class)`; under this system it lands in `tests/Behavior/` as fulfillment scenario vocabulary (not yet in the working tree; land it with the first test that needs it). It inserts a `Fulfillment` Eloquent row directly with the requested state + the SHIPMENT workflow, seeds a parent order for the GraphQL-detail case, and returns a `FulfillmentId`.

**Direct insert is intentional** — building a fulfillment through `AddFulfillmentCommand` cascades into shipment, items, allocations, plugins, increment-id assignment, and several seeded reference tables. The fixture's purpose is to land a row in a state, not exercise the creation pipeline. For tests that *do* need a created-via-command fulfillment, build an order and `DecideOrder` to harvest the resulting fulfillment (see `tests/Behavior/OrderFulfillmentScenarioTrait.php`).

## Layer Map — Where the Test Goes, With What Tool

Placement is by what the test **needs** (README §6.1), enforced by base class — `tests/Unit` means *no container, no DB*; if a test needs `app()`, it is not a unit test:

| The test needs… | Put it in | Extend | What gets exercised |
|---|---|---|---|
| nothing but `new` and doubles (VOs, pure algorithms) | `tests/Unit/` | raw `PHPUnit\Framework\TestCase` | computation correctness |
| the container, the DB, a domain factory, or a bus dispatch | `tests/Feature/` | `SkuNexus\Core\Tests\TestCase` | middleware → plugins → handler → sub-commands → events |
| a GraphQL endpoint | `tests/Feature/GraphQL/` | `Feature\GraphQL\TestCase` (never the root one) | controller → schema → resolver → bus → DB; response shape |
| a multi-command business pipeline | `tests/Integrations/` | `Integrations\TestCase`, composing scenario traits | pull → decide → pick → pack → … end state |
| real HTTP middleware (auth, CSRF, throttle, CORS) | outside this suite — an HTTP-level test against the real kernel | — | Feature tests bypass middleware via global `WithoutMiddleware` |
| cross-process scenarios (live queue worker, real connector sandbox) | outside this suite — HTTP-level test against a deployed/dev environment | — | end-to-end with side systems |

In Pest repos the base classes bind folder-wide in `tests/Pest.php` (`pest()->extend(Tests\TestCase::class)->in('Feature')` etc.) instead of per-file `extends`; the table's base classes apply unchanged.

**Default: the in-suite Feature test** (either syntax). Faster (SQLite memory), per-test rollback, parallel-runner integrated, full access to the vocabulary, factories, `Queue::fake`, `rebootHandlers`. Leave the suite only when the table explicitly calls for it. Shared scenario helpers live in `tests/Behavior/` — no suite imports from another suite's namespace.

### Quick decision table — where does this test go?

| Adding/changing… | Test type | Fixture entry point |
|---|---|---|
| New command | Feature | `when<Verb>()` → `$this->bus()->handle(new XCommand(...))`; assert read-side |
| Plugin on existing command | Feature | dispatch upstream command; `Queue::fake()` + `QueuedCommandJob` if the follow-up is queued, read-side if sync |
| State transition | Feature | `aFulfillmentInState(...)` → dispatch transition command → `assertFulfillmentIsInState(...)` |
| Vendor handler override | Feature | dispatch core command, assert new behavior; do not `rebootHandlers` |
| Factory/interface override | Feature | dispatch consuming command, assert observable change |
| New GraphQL field/type | Feature (`graphQL()` helper) | `Feature\GraphQL\TestCase`; assert `errors` absent + explicit `sort` |
| New REST endpoint | Feature (`$this->postJson(...)`) | route + controller + bus end-to-end; assert status, then state |
| Field resolver (`config/fields.php`) | Feature | dispatch `Update*Command` with integration payload |
| Auth/CSRF/throttle behavior | HTTP integration, outside this suite | HTTP-level test against the real kernel |
| Cross-process scenario (real worker, connector sandbox) | HTTP integration, outside this suite | deployed/dev environment |
| Pure algorithm / value object | Unit (raw `PHPUnit\Framework\TestCase`) | direct call, plain AAA — no container, no ceremony |

## Before Writing a Test — Ask First

1. **Which public interface does this behavior cross?** Command bus (`$this->bus()->handle`), HTTP/GraphQL endpoint, or both? The answer picks the test entry point.
2. **Which vocabulary words are missing?** Every noun in the scenario is a builder, every Then a domain assertion. Check `{Domain}ScenarioTrait`/`{Domain}AssertionsTrait` first; build only the missing word, in the right tier.
3. **Will the assertion survive a refactor that splits or merges sub-commands?** If it breaks without observable behavior changing, the assertion is at the wrong level. Move it to entity state / response shape.
4. **What is the system boundary the test must NOT mock?** Default: nothing internal. Mock only external HTTP, time, randomness. If the impulse is to mock the bus, a repository, or a service owned by core, course-correct.
5. **Does this test need real HTTP middleware?** If yes (auth, CSRF, throttle), Feature tests bypass it via global `WithoutMiddleware` — that behavior needs an HTTP-level test against the real kernel, outside this suite. If no, Feature test is correct.

## Two Buses — The Distinction That Drives Test Design

SN runs on **two separate dispatchers**. Tests that confuse them silently pass while production fails.

| Dispatcher | Dispatch call | What runs | What faking sees |
|---|---|---|---|
| **SN command bus** | `$bus->handle(new SnCommand(...))` via `CommandHandlerContainerInterface` | all middleware + plugins + handler, synchronously | Nothing — neither `Bus::fake` nor `Queue::fake` intercepts it |
| **Laravel queue / job bus** | `QueuedCommandJob::dispatch(new SnCommand(...))` | pushes a `QueuedCommandJob` Laravel job; a worker later runs the SN command via `$bus->handle` | `Queue::fake()` (or `Bus::fake([QueuedCommandJob::class])`) intercepts the job |

Implications for assertions:

- **Sync sub-commands** dispatched inside a handler: **assert via the read-side**, not by faking the sub-command. The sub-command's plugins/hooks/middleware are part of the system under test; faking the handler skips them and (worse) crashes hooks that read `$result->getValue()` expecting a domain type.
- **Async follow-ups**: `Queue::fake()` + `Queue::assertPushed(QueuedCommandJob::class, fn ($job) => $job->command instanceof Cmd && ...)` — the job's `command` property holds the SN command instance for assertion predicates.
- `Illuminate\Support\Facades\Bus::fake([SnCommand::class])` only intercepts Laravel's job dispatcher. `Bus::assertDispatched(SnCommand::class)` will be empty even though the command ran on the SN bus.

## Test Patterns by Extension Point

Seven extension points, seven patterns. Each shows the public-interface assertion shape in the body grammar; `when*` helpers and vocabulary builders are implied per the style-guide skeleton. Examples are in Pest (the default); the PHPUnit shape is the same doctrine through the mapping table above — full PHPUnit examples live in `references/phpunit-style-guide.md`.

### Pattern 1 — New command

Dispatch through the real bus, assert via the read-side. No faking.

```php
test('doing x moves the entity to in progress', function () {
    $entity = $this->anEntityInState(Open::class);

    whenDoX($entity);   // namespaced file function: test()->bus()->handle(new DoXCommand($entity->getIdentifier(), ...))

    $this->assertEntityIsInState(new InProgress(), $entity);
});
```

If the handler queues an async follow-up, layer in `Queue::fake()` (Pattern 4) — but the primary assertion stays on the persisted state.

### Pattern 2 — Replace handler (vendor override)

Do **not** call `rebootHandlers`. Dispatch the core command through the real bus and assert the new behavior is observable — the test must prove the override actually wins via real provider order. If the test passes but production fails, the CommandsProvider is registered before core's — exactly the bug a unit test of the handler class would have missed.

### Pattern 3 — Replace factory/interface (`AdditionalInterfacesProvider`)

Same shape as Patterns 1–2. The Feature test that dispatches the consuming command exercises the real DI; if `provideWith()` is missing or the bootstrapper isn't loaded, the test fails at the observable layer.

### Pattern 4 — Plugin

The right test depends on **how the plugin dispatches its follow-up**:

**4a. Plugin uses `QueuedCommandJob::dispatch(...)`** (recommended for external pushes):

```php
given(fn () => Queue::fake());   // boundary fake = arrange, inline marker

whenTriggerX();

Queue::assertPushed(
    QueuedCommandJob::class,
    fn (QueuedCommandJob $job) => $job->command instanceof PushSomethingCommand
);
```

**4b. Plugin uses `$this->bus->handle(...)`** (sync sub-command on the SN bus): don't fake. Assert the *effect* the sub-command produces — Pattern 1's read-side discipline (`$this->assertAuditRowRecordedFor($this->entity)`). A temptation to spy on the sub-command means the assertion is at the wrong level.

External push commands default to `NoOpCommandHandler` in tests — that handles the "external API" boundary; combine with `Queue::fake()` only when the plugin queues via `QueuedCommandJob`.

### Pattern 5 — State transition

```php
$f = $this->aFulfillmentInState(Open::class);

whenTransitionTo(InFulfillment::class, $f);

$this->assertFulfillmentIsInState(new InFulfillment(), $f);
```

Side-effect commands dispatched by the transition handler follow Pattern 4's rule: `Queue::fake` if via `QueuedCommandJob`, read-side if sync. The rejection of an **illegal** transition is a guard test: `assertThrows` around the same When, plus a positive `assertFulfillmentIsInState` that the state did not move.

### Pattern 6 — GraphQL field/type extension

```php
$this->givenASeededWarehouse();

$data = $this->graphQL($this->cycleCountQuery());   // helper asserts `errors` is absent

expect(\Arr::get($data, 'warehouseQueries.warehouseGrid.rows.0.cycle_count'))->toBeNumeric();
```

Catches: field missing from entity, `SelectMutator` missing from provider, listener registered against the wrong event name, JOIN missing for cross-table fields. Two GraphQL house rules (README §6.5):

- **Always assert `errors` is absent** — the `graphQL()` helper on `Feature\GraphQL\TestCase` does it once for every test, turning opaque `false is not true` failures into the actual GraphQL error string.
- **Every grid query indexed by `rows.N` carries an explicit `sort`** — or resolve the expected model *from* the returned row. Row 0 == `Model::first()` is a SQLite insertion-order accident, not a contract.

### Pattern 7 — Field resolver (`config/fields.php`)

Feature test that pushes an integration-shaped payload through `UpdateOrderCommand`/`CreateOrderCommand` and asserts the custom field appears in the read model. The resolver class itself stays internal.

## Data Setup — the Decision Order

For the Given, in order of preference (README §6.3):

1. **A vocabulary builder** — if `{Domain}ScenarioTrait` already speaks the sentence, use it. If the word is missing and this test needs it, build it (right tier, on demand).
2. **Package Laravel factory.** `->create()` when a row just has to exist; `->createDomain([...])` + `$repository->add()` when the code under test consumes domain entities — **`createDomain()` does not persist**; persist via the repository. **Always pass the fields the assertion depends on** — never inherit a factory default.
3. **`*Faker` static class** (`create()` + `validParams()`, overrides last) for types with no model or package factory. Accept a time seed instead of calling `Carbon::now()`.
4. **A builder through the real write path** (bus dispatch inside a scenario trait) for multi-step aggregates — when the behavior depends on a write command's side effects (custom fields, decision plans, increment IDs). Slowest option; not for plain row existence.
5. **Seeders** only when the test genuinely asserts against the demo dataset — and then look values up **by name**, never by count or `inRandomOrder()`.
6. **Raw `\DB::table()` — never in a test body.** A write with no domain command is a **domain gap**: it lives in exactly one named scenario builder with a `// DOMAIN GAP` comment, and gets filed upstream.

No randomness in shared setup — fixed SKUs and quantities; select items by product/ID, never by array position.

## Assertions

- **Assert state, not just status.** Every write test gets a read-side read-back (repository / model / domain assertion). An `assertSuccessful()` after 40 lines of arrange asserts almost nothing.
- **State via value objects, positively:** `assertOrderIsInState(new Closed(), $order)` — re-reads through the production read path and compares via the state VO's own `equals()`.
- **Domain assertions fail in domain language** — "Expected order 42 to be 'closed', but it is 'in_fulfillment'." — never a bare `assertEquals` mismatch dump. `assertSame(3, count($rows))` speaks implementation; `assertFulfillmentHasItems($f, count: 3)` speaks contract.
- **Exception outcomes via `assertThrows`** — the marker stays `assert`, the When stays visible, and the guard's second clause ("…and nothing was written") is assertable after the throw. `expectException` forces the Then before the When and makes everything after the When unreachable; use it only when `assertThrows` genuinely can't express the case, and then nothing may follow the When. In Pest, `expect(fn () => …)->toThrow(X::class)` has the same properties (When visible, post-throw clauses assertable); `$this->assertThrows` remains valid inside Pest closures.
- **In Pest, one contract clause per `expect()` statement** — sibling `expect()` calls, never `->and()` chains. Higher-order accessor chains (`expect($rma)->getState()->toBe(…)`) are the preferred entity-read shape; domain assertions stay `$this->assert*` trait calls so failures speak domain language.
- **HTTP rejections are asserted as status + error body** — the frontend consumes JSON, not internal exception classes.
- **Timestamps through `assertEqualTime()`**, never raw equality.
- **Expectations read out of the DB, not hard-coded**, where the subject is a projection (GraphQL grids) — catches renamed fields and dropped resolvers without golden JSON.

### Raw DB reads — the reconciliation

Two rules that look like a conflict and aren't:

- **Behavior tests assert via the production read-side** (repository / model / GraphQL query) — never `DB::table(...)`. The read path production callers use is part of what's under test, and `CLAUDE.md` forbids raw `DB::` anyway.
- **Persistence tests** — where the repository is *itself the subject* and can't be its own oracle — may use a raw `\DB::table()` read as an **independent read oracle**. That is the only sanctioned raw-read site, and it is read-only.

## Test Infrastructure Quick Reference

- **Running the suite** — Pest repos: `composer test` = `vendor/bin/pest` (installing Pest hijacks `vendor/bin/phpunit`), `vendor/bin/pest --parallel` for the full suite; Pest's default output prints the description list — the `--testdox` equivalent, free. PHPUnit repos (core): `vendor/bin/paratest` for the full suite, `php artisan test --compact --filter=<name>` for one test, `--testdox` on a file renders its spec.
- **Every test method gets a brand-new database** (`:memory:` SQLite rebuilt per test). Cross-test setup is structurally impossible; state can never leak into another test.
- **Real migrations never run in tests.** A new migration is invisible until `php artisan dump:schema-for-testing --env=testing` — and the staleness guard is a 10-minute wall clock, so stale schema silently passes inside that window.
- **Testbench env hooks are inert.** The suite overrides `createApplication()` to boot the real repo app, so `defineEnvironment()`, `getPackageProviders()`, `testbench.yaml`, and `#[WithConfig]` silently no-op. Don't copy Testbench recipes from the docs. Pre-container config/provider injection goes through the `bootstrappingApplication()` hook.
- **`WithoutMiddleware` is global** — HTTP middleware (auth, CSRF, throttle) is bypassed in Feature tests; `loginAsAdmin()` proves nothing about authorization.
- **One container accessor:** `$this->app->make()` (or the `bus()` helper). Not `app()`, `app()->make()`, `container()`.
- **`$this->rebootHandlers([Cmd => Handler])`** — the *one* sanctioned spelling for a narrow handler override (never `$bus->setCommandHandler(...)` reached by hand). **`$this->rebuildHandlers([Cmd])`** re-makes from the container with current bindings.
- **Required seeds run automatically** — `FulfillmentCustomFieldsSeeder`, `PurchaseOrderCustomFieldsSeeder`, `PurchaseOrderItemCustomFieldsSeeder` in `setUp()`.

## Mocking / Faking Rules

Mock or fake at **system boundaries only**:

- External APIs — most `Push*` commands already default to `NoOpCommandHandler`; combine with `Queue::fake()` only when the producing plugin uses `QueuedCommandJob::dispatch`.
- Time / randomness — `Carbon::setTestNow(...)`, deterministic seeds.
- File system — sometimes; prefer real temp dirs.

Do **not** mock:

- The SN command bus or its middleware (`TransactionMiddleware`, `FirstCommandOnlyAclMiddleware`, `CustomFieldsGuardMiddleware`).
- Handlers, plugins, repositories, services, factories, resolvers, mutators owned by SN core or the client repo.
- Anything inside `SkuNexus\Core` namespace or `App\` overrides.
- The Eloquent layer — use real models on SQLite memory.

House rules for the doubles that remain (README §6.4):

- **One mocking framework: Mockery.** On a raw-PHPUnit class that mocks, add `use MockeryPHPUnitIntegration;` — without it Mockery expectations are never verified.
- **`->method(...)->with(...)` without `expects(...)` verifies nothing** — it reads like verification and isn't. Class-name strings passed to Mockery's `with()` compare identity, not type — use `Mockery::type()` or `withArgs()`.
- **Hand-written fakes implement the interface, never extend the real class** (an emptied constructor on an extended real class leaves typed properties unset and inherited methods crashing). When a fake exists, pair it with a **contract test** run against both implementations — that's how a fake stays honest.
- **At Feature/Integration depth, prefer no doubles at all** — the interesting behavior lives in middleware, plugins, and state machines, which mocks erase.

### Don't substitute handlers with shape-incompatible spies

`setCommandHandler($cmd, $spy)` swaps the handler, but **plugins and hooks around the command still run**, and they read `$result->getValue()` expecting a domain type. A spy that returns `SuccessResult` (whose `getValue()` returns `true`) will crash any hook that types the value as a domain object (e.g. `CustomFieldHookEventResolver`). If interception is unavoidable, the spy's return type and `getValue()` shape must match the production handler's. In almost all cases, the simpler answer is: **don't intercept; assert via the read-side.**

### The default that makes most tests trivially correct

For sync sub-commands inside a handler: dispatch the outer command through the real bus, then assert the persisted state via the public read API (repository / read-side query / GraphQL endpoint). Real handlers, real plugins, real hooks all run. The test asserts the *outcome* a production caller would observe.

## Red Flags — STOP and Course-Correct

| Thought | Course correction |
|---------|-------------------|
| "The body is 30 lines; I need a bigger test." | The body budget (~12 lines) is a smoke alarm: a vocabulary word is missing, or the file covers two surfaces. Extract the builder/assertion, don't grow the body. |
| "I'll add builders for the whole domain while I'm here." | Vocabulary grows one word per test that needs it. Speculative builders are the DSL-nobody-asked-for failure mode. |
| "The factory default happens to satisfy my assertion." | Correspondence principle: pin every field the assertion depends on in a visible Given line. A default satisfying a Then is a time bomb. |
| "This handler's logic is complex; I'll unit-test it." | Refactor for testability instead — extract a pure service/value object that can be unit-tested (plain AAA, no ceremony), leave the handler thin and tested through the bus. |
| "Test passes; I'll skip running the full suite." | Other tests share vocabulary, factories and seeders. Run the file's group at minimum. |
| "The name says it stays pending; asserting it isn't closed is the same thing." | It passes for Approved, Declined and any corrupt value. The name already told you which state to assert — assert that one, positively. |
| "The key is present; the value comes from the resolver, so presence is enough." | A renamed field, a null, or a wrong-but-non-empty value all pass. Assert the value the Given fixed. |
| "The helper fails with a good message — that *is* my assertion." | A `the*`/`a*` helper retrieves or creates; the moment it can fail, half the contract is invisible in the body. Rename it `assert*` and state the clause in the test. |
| "The spec has 0 `⚠`, so it's readable." | `⚠` measures where the extractor gave up, not where the reader does. Run the grep block in `spec-readability-pass.md` §1 — long bullets, phrase dumps, blank Thens. |
| "Five scenarios render the same body, but the titles tell them apart." | The Given is missing the differentiator. Move the arrangement into `given*` file functions with slots; probe the render in a scratch dir first. |
| "The plan says this TestDox will render as …" | A predicted render is a guess. Run the phar on a probe copy and quote the line. |

## NEVER Rules

**The one every other rule flows from:**

- **NEVER instantiate a handler directly in a test** — dispatch through `$bus->handle()`. Direct invocation skips the command-bus middleware and every plugin registered against the command.

### Dispatch and doubles — the composition stays real

- **NEVER mock the command bus or its middleware/plugins.** Mock only at system boundaries (external APIs, time, randomness).
- **NEVER use `rebootHandlers` / `rebuildHandlers` as a default.** Reserve for stubbing a non-NoOp external boundary or pinning an environment-varying handler; narrow the override or remove it. Wholesale rebooting defeats Feature-test fidelity.
- **NEVER use `Illuminate\Support\Facades\Bus::fake([SnCommand::class])` to assert SN sub-command dispatch.** Laravel's `Bus::fake` only intercepts the Illuminate Job dispatcher — `Bus::assertDispatched` will be empty even when the command ran. Use the read-side. The narrow exception: assertions on `QueuedCommandJob::class` via `Queue::fake()`.
- **NEVER swap a command's handler with a spy whose `getValue()` returns a non-domain value** when the command has plugins/hooks around it — see the SuccessResult trap above.
- **NEVER call `Queue::fake()` with no allow-list** when downstream test steps depend on real queue work running. Pass an allow-list scoped to the jobs the test cares about.
- **NEVER assume `HasEventStreamTrait` + `addEvent()` will propagate events when the handler is registered through `DeferredHandler`.** The `EventStreamPropagatorMiddleware` checks `$handler instanceof HasEventStreamInterface`, but `DeferredHandler` is the wrapper at that point and only implements `CommandHandlerInterface` — the check fails and events never reach the listener. Confirmed in a real implementation retrospective. Workaround: have the handler perform the side effect directly (e.g., write the audit row via an injected repo) instead of routing through a domain-event listener. If the listener-based shape is non-negotiable, the result type itself must implement `HasEventStreamInterface` or `EventStreamInterface` so the middleware's result-based checks fire — but direct write is simpler.

### The body — one act, one clause

- **NEVER dispatch the command under test in `setUp` / `beforeEach`.** They are the shared Given — state only. The When is one visible line in every test body.
- **NEVER assert on internal sub-command dispatch as the test's primary purpose.** If a refactor that splits or merges sub-commands breaks the test without changing observable behavior, the test was wrong. Assert the observable outcome instead.
- **NEVER inline a domain-gap raw write in a test body.** It lives in exactly one named scenario builder in `tests/Behavior/`, marked `// DOMAIN GAP`, and gets filed upstream.
- **NEVER hardcode entity IDs in test setup.** Use vocabulary builders / factories / seeded lookups by name. Hardcoded IDs break on DB refresh and on parallel runs.

### The name and its proof

- **NEVER name a test with *works / correctly / properly / successfully / should*.** A test name is a falsifiable proposition: `#[Test]` + snake_case, subject–verb–outcome, no `test_` prefix. (Pest: same rules on the `test('…')` description — lowercase, spaced, no banned words.)
- **NEVER assert a state negatively** (`assertNotEquals(Closed::STATE, ...)`) — it passes for every wrong state, including a buggy one. Assert the expected state positively via the value object's `equals()`. This leaks most often where the *name* already fixes the state (`..._stays_pending`): the name is the assertion you owe.
- **NEVER let a test name claim a noun, qualifier, quantifier or second clause the body doesn't assert.** "every line", "for the returned units", "a line of another RMA", "is already closed *and so* cannot be received" — if the fixture never builds it or no Then reads it, the name is a promise the suite doesn't keep, and the runner's description list publishes it as if it did. Build it and assert it, or rename the test to what is actually proved (style guide §5.8).
- **NEVER let existence stand in for a value.** `assertArrayHasKey`, `assertNotEmpty`, `assertGreaterThan(0, ...)` as a test's only Then pass for a renamed field, a null, and a wrong-but-nonzero number alike. Assert the value the Given fixed; if the expected value is unknowable, the Given is under-specified — fix the fixture, not the assertion.
- **NEVER put an assertion or `fail()` inside a `the*` / `a*` vocabulary helper.** Article-grammar words retrieve and create; one that can fail the test hides half the contract from the body and from the extracted spec. A helper that judges is named `assert*`, and the clause it decides is stated in the test.
- **NEVER verify side effects via raw DB reads in a behavior test** (`DB::table(...)`, raw SQL). Use the read-side production callers use. Sole exception: the independent oracle inside a *persistence* test.
- **NEVER assert "listener registered" or "class X exists in `PROVIDERS` array"** — a tautology against the literal. Assert the observable effect via bus dispatch or endpoint POST.

### The rendered spec

- **NEVER hand-edit `spec-from-tests.md`** — it is regenerated; fixes go in the tests or in a change request to the tool.
- **NEVER let a `#[TestDox]` say what the helper does not do** — verify every sentence against the body; a wrong spec is worse than an ugly one.
- **NEVER feed a `{slot}` a top-level local** — it inlines the local's whole assignment into the Then. Pass the domain number, a literal, or a `$this->` property.
- **NEVER assert inside a `when*` helper** — return the value and assert in the body, or the Then never renders and sibling scenarios silently differ.
- **NEVER leave a parameterised scenario builder without a `#[TestDox]`** — its derived prose is a parameter dump on every call.

### Pest-specific

- **NEVER drop the file's `namespace` in a Pest file.** It is what keeps `when*` functions and file consts from colliding across files — and duplicate global consts don't even crash: the second definition is silently ignored and the tests read another file's value.
- **NEVER chain a second contract clause with `->and()`.** Sibling `expect()` statements, one clause per line.
- **NEVER write higher-order *test* chains** (`it('…')->get('/')->…`) — a chain cannot carry a `given()` delta; the body grammar wins. (Higher-order *expectations* are encouraged; higher-order *tests* are banned.)
- **NEVER make scenario-trait vocabulary public (or global) to feed a file-level function.** Build arguments via `$this->` at the call site; the only sanctioned public members are `bus()` and the trait fixture properties a `when*` global genuinely reads via `test()`.
- **NEVER dispatch the command under test in `beforeEach`** — same rule as `setUp`.

### Placement and harness

- **NEVER skip `php artisan dump:schema-for-testing --env=testing` after adding a migration.** Stale schema silently passes tests until cache expiry (a 10-minute wall clock).
- **NEVER disable `WithoutMiddleware` globally to test auth/CSRF/throttle.** Middleware behavior needs an HTTP-level test against the real kernel, outside this suite (see "Before Writing a Test" #5).
- **NEVER default to HTTP-level tests against a running server** when the behavior doesn't need real HTTP middleware or a real cross-process worker. Feature tests are faster, isolated, and have stronger doubles.
- **NEVER tag a test `@group do-not-run` to skip a failure.** Either fix it, delete it, or document why it's quarantined in the file.

## When Things Go Wrong

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| `composer test` dies instantly with `InvalidPestCommand: Please run ./vendor/bin/pest` | Pest is installed and has hijacked `vendor/bin/phpunit` | Point the composer `test` script (and CI) at `vendor/bin/pest` |
| `Error: Using $this when not in object context` in a `when*` helper | The helper is a named file-level function — Pest binds `$this` only inside `test()`/`beforeEach()` closures | Use `test()` inside file-level functions; keep `$this->` for closures |
| Test passes locally, fails in CI | Schema dump stale; migration added recently | Run `php artisan dump:schema-for-testing --env=testing` |
| Test passes alone, fails in suite | Shared global state (config, container singletons, file locks) | Isolate setup in `setUp()` / `beforeEach()`; avoid mutating `config()` without restoring |
| Testbench recipe from the docs has no effect | `createApplication()` is overridden — `defineEnvironment()`, `getPackageProviders()`, `#[WithConfig]` are inert | Use `bootstrappingApplication()` for pre-container config/provider injection |
| `Bus::assertDispatched` fails despite handler clearly dispatching | Faked bus suppresses the *outer* command — handler never ran (or the dispatch is on the SN bus, which `Bus::fake` never sees) | Narrow `Bus::fake([...])` to follow-ups only; for SN-bus sub-commands, assert the read-side |
| Plugin assertion fails | Plugin not in `PLUGINS` const, or wrapped without `DeferredPlugin` | Check the relevant `*CommandsProvider` entry |
| GraphQL test returns `null` for new field | Field added to entity but no `SelectMutator` registered, or wrong `withMainSource()` | Verify `SelectMutator` registration and `withMainSource()` call |
| GraphQL assertion fails opaquely (`false is not true`) | Query returned `errors` that nothing asserted on | Use the `graphQL()` helper that asserts `errors` is absent and prints them |
| GraphQL `rows.0` assertion flaky / wrong model | No `sort` in the query — row 0 is insertion-order luck | Add an explicit `sort`, or resolve the expected model from the returned row |
| Override handler not called | The `CommandsProvider` registered before core's | Check provider order; CommandsProvider is last-wins |
| Test depends on time | Hardcoded "today's date" or relative arithmetic | `Carbon::setTestNow($fixed)` in `setUp` / `beforeEach` |
| Flaky on parallel runs | Test mutates a shared file or DB row outside its own transaction | Use factories per test; avoid `truncate` |
| A test fails three times in a row with the same error | Stop guessing | Stop retrying — read the full failure output, form one hypothesis at a time, and bisect the cause |

## The Test Is Also the Published Spec

`spec:extract` (the `skunexus-spec-extract` skill) deterministically renders any test file as Given/When/Then prose — the gwt.md a ticket attaches, the acceptance coverage check, the FE handoff quote. Its input language IS this skill's grammar: a test written per this doctrine extracts as readable English with **zero extra work**. Never contort a test for the extractor — when its output reads wrong, escalate cheapest-first, and notice the first rungs improve the test itself:

1. **Fix the name/shape.** A custom assertion whose phrase ends on a copula or closes on a preposition promotes its subject (`assertHospitalIssueIs` → "the fulfillment's hospital issue is 'withdrawn'"); one that can't renders a greppable `⚠ RAW —` marker instead of fake English.
2. **`#[TestDox('{param} …')]`** on the assertion helper or `given*`/`when*` wrapper — PHPUnit-native, inert at runtime, one line at the definition fixes every call site. Default is NO TestDox: right-reading derived prose needs no second source of truth.
3. **A dialect config word** — only for a domain word that inflects wrong in *every* suite ("unholded") or an acronym casing; never for one test's prose.

**One default changed by experience:** every scenario builder with two or more parameters carries a `#[TestDox]` from the start — derived prose for a parameterised builder dumps every argument with its parameter name (`an imported shopify order of number 936285, shopify created at settled long before the sweep`, ×127 in one suite). The measured rules for what a `{slot}` renders (a top-level local inlines its whole assignment; an empty array and a defaulted parameter render as nothing; a nested helper's own TestDox is ignored) and the sixteen-item first-pass checklist are the style guide §10.6–10.7 — read them before writing a builder or an assertion with slots.

Placement gotchas that silently eat prose: a `//` note goes ABOVE `#[Test]` (between attribute and `function` it vanishes); the class docblock goes after `namespace`; assertions inside closures/loops render `⚠ NOTHING READ` — which the body grammar bans anyway (the extractor is the lint). Read a new file back with `spec-extract <file>` next to `--testdox` before committing; `grep '⚠ RAW\|⚠ NOTHING READ'` over rendered specs is the suite's prose-debt metric — and if the read-back looks like machine transcript despite 0 `⚠`, **offer** the optional second pass (next section) rather than fixing ad hoc. Full guidance: the style guide §10.

**Status — the extractor reads both syntaxes.** `--mode` defaults to `pest` (`test()` → scenario, `beforeEach` → Background, bare `given()` or a bare `givenX()` call → Given, `when*` functions → passive command prose, `expect()` families → Thens, `#[TestDox]` on file-level helpers); `--mode=phpunit` reads `#[Test]` classes. A converted 40-file suite extracts at parity with its PHPUnit original, so either syntax is a first-class spec source. Two Pest-only rules that decide whether the prose reads: mark a Given **once** — `given(fn () => $this->…)` or a bare `givenX();`, never `given(fn () => givenX())` — and pass the extractor a **directory**, not a shell glob. Style guide §3 and §10.5.

## The Spec-Readability Pass — second pass over a landed suite

A green suite with `0 ⚠` can still render 86 unreadable bullets. **The pass is optional and the developer decides:** after the first render of a new suite, or when someone says the spec "needs a lot of improvement", run the two-minute measure block (reference §1, read-only) and **ask** with the numbers — `AskUserQuestion`: "long bullets N, phrase dumps N, blank Thens N, setting values stated: no. Run the readability pass now (≈K test files edited, suite stays green), or leave it?" Start only on a yes; "later" goes in the ticket's follow-ups. When it runs, `references/spec-readability-pass.md` is a **mandatory read first.** It is audit → **apply** → verify → iterate, not a report:

1. **Baseline** — suite counts (tests *and* assertions), scenario counts, a before-copy of the render.
2. **Measure** — the grep block: long bullets, phrase dumps, blank Thens, proper-noun verbs, repeated glosses, Then-repeats-Given, lowercase nouns/headings, why-notes rendered; then by eye: are the setting values anywhere, can sibling scenarios be told apart from their bullets.
3. **Three roles, written down separately, then reconciled** — a cold reader (spec only, as PM/PO and FE dev), a fidelity reviewer (§5.8 promise ledger against source, verdict test-shape / vocabulary / extractor per defect), a fix planner (cheapest rung, **every render measured on a probe**). Synthesise: rank by damage, make the disagreement calls.
4. **Apply** in order scenario trait → assertions trait → Feature test → Unit files → dialect overlay; re-read whole files, run the suite, grep every replaced name after each.
5. **Verify with a fresh-eyes verifier who didn't write the fixes** — defect table with quoted evidence, contract drift, **every TestDox sentence true of its body**, duplicated literals equal their consts, orphans (dead returns, unswept siblings, jargon left in the domain trait), style, PM spot-read. Then a cleanup pass.
6. **Gate** — same test count, assertion delta named, replaced names at zero, no duplicated methods, regenerated spec with the metrics in single digits.
7. **Deliver** — the regenerated spec, a `decisions.md` entry with the debt deliberately left (title-vs-body contract items are the developer's call), and `.ai/<TICKET>/spec-extract-requests.md` for the tool — **fix the tests now, don't wait for the tool.**
8. **Iterate** on the developer's review; the two recurring asks ("does it need N orders?", "the Given is missing the differentiator") have standard answers in the reference §9.

The generalised defect catalogue (symptom → cause → fix), the disagreement calls, the NEVER list and the diagnostics table are in the reference — as is a one-paragraph hint on how the roles map to agents if you choose to split the work (the three readings are independent; apply splits by disjoint file sets; the verifier didn't write the fixes).

## Related Skills

- **OPTIONAL COMPANION:** `skunexus-tdd-testing` — the process overlay for building new behavior test-first (when to write which test, in what order). Every test it drives is written per this skill.
- **OPTIONAL COMPANION:** `skunexus-spec-extract` — renders these tests as the published GWT spec; §10 of the style guide is the authoring guidance that keeps its output readable.
- **UPSTREAM:** invoked from the engineering workflow by `skunexus-backend-plan` (which names the test file and the propositions per task) and by `skunexus-backend-implement` (which writes and runs those tests as the tasks land).

This skill writes and runs the tests and stops there: it does not plan the work (`skunexus-backend-plan`), write the production code they exercise (`skunexus-backend-implement`), render them as the published spec (`skunexus-spec-extract`), or write QA testing steps (separate skill).
