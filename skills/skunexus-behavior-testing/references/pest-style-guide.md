# SN Test Style Guide — Given/When/Then (Pest syntax)

Pest is the default test syntax for **client repos**; PHPUnit class syntax stays the default in
`skunexus-be-core`. The doctrine is identical to `phpunit-style-guide.md` — same grammar, same naming, same
promise ledger — only the syntax shell differs; this file is self-contained and normative, so a Pest author
needs nothing else. The practical on-ramp — a 7-step recipe, the surprises, how to run — is
`pest-dev-guide.md`, alongside this file; worked references are §2 (anatomy) and §7 (copyable skeleton),
with shared vocabulary in the `tests/Behavior/` traits of the repo you are working in.

---

## 0. The idiom in one table

Every PHPUnit construct has exactly one Pest home. Nothing else is ratified; deviations below are declined,
not undiscovered.

| Tier | PHPUnit home | Pest home |
|---|---|---|
| Scenario builders + domain assertions | `{Domain}ScenarioTrait` / `{Domain}AssertionsTrait` traits | **the same traits, attached per file with `uses({Domain}ScenarioTrait::class);`** |
| Shared Given (state only) | `setUp()` | `beforeEach(function () { … })` |
| Given deltas | `$this->given(fn () => …)` / private `given*` method | **bare `given(fn () => $this->…)`** — one 3-line global in `tests/Pest.php`; a `given*`-**named** file-level function is already marked and is called **bare**, never wrapped (§3) |
| Compound file-local builders (`anApprovedWriteOffRma`) | private method | **graduate to `{Domain}ScenarioTrait`** — PHP has no file-private named function (§9) |
| The When | private `when<Verb>()` method | **one namespaced file-level `function when<Verb>()`**, body `test()->bus()->handle(…)` |
| Constants | `private const` | file-level `const X = '…'` (namespaced); shared across files → constant on the scenario trait, read `self::X` from a closure and **`test()->target::X`** from a file-level function (§2) |
| Typed fixture properties | `private Order $order` | shared actors → **typed properties on the scenario trait** (`public` if a `when*` global reads them via `test()`, else `protected`); residual per-file state stays dynamic, assigned in `beforeEach` |
| The container | `$this->app->make(X::class)` | `$this->app->…` in a closure; **`app()->make(X::class)`** in a file-level function — `test()->app` is unreachable (§2) |
| Data matrices | `#[DataProvider]` | `->with([...])` with string keys (per-file scoped), or `->with('name')` + a file-level `dataset('name', fn)` |
| Exception outcome | `assertThrows(fn, X::class)` | `expect(fn () => when…())->toThrow(X::class)` — and pass the message when the PHPUnit twin pinned one: `->toThrow(X::class, MESSAGE)` |

**Converted and new Pest files KEEP a `namespace`** — `Tests\Feature\PestOrderRMA\CloseRma`, i.e. the
directory namespace plus the file's own segment. This is not decoration: it is what makes the file-level
`when*` functions and `const`s collision-proof. Without it, duplicate global constants do not even error —
the second definition is *silently ignored* and the file reads another file's value. A namespace shared by a
whole folder re-creates the collision for same-named `when*` helpers; go one segment per file.

**A namespaced file must import the global classes it names.** `RuntimeException::class` inside
`namespace Tests\Feature\…\CancelGuards` resolves to `Tests\Feature\…\CancelGuards\RuntimeException` — no
parse error, just a class that does not exist, and a `toThrow` that fails with the baffling *"To contain:
Tests\Feature\…\CancelGuards\RuntimeException"*. Add `use RuntimeException;` (same for `Closure`,
`DateTimeImmutable`, `Throwable`) exactly as you would in production code. A converted file that lost the
import is the usual cause.

**Runner and coexistence.** Installing Pest hijacks `vendor/bin/phpunit`; `composer test` must run
`vendor/bin/pest`. Pest executes PHPUnit test classes natively (77/77 proven in the pilot), so PHPUnit suites
coexist untouched and **conversion is a style choice, never a prerequisite**. PHP 8.2 caps the project at
Pest 3, where `uses()` is the trait-attachment spelling (`pest()->extend()` in the current docs is the
Pest 5 API). `tests/Pest.php` binds the base class folder-wide
(`pest()->extend(Tests\TestCase::class)->in('Feature')`) — that is the base class, not vocabulary; folder-wide
*trait* binding (`->use(Trait)->in(…)`) is **declined**, per-file `uses()` keeps each file's world explicit.

**`describe()` / `it()` are declined — flat `test()` is the only shape.** `it('closes the order')` amputates
the subject, so the falsifiable proposition no longer exists on one line and the promise-ledger greps (§5.8)
stop seeing whole sentences. A group-scoped `beforeEach` re-blurs the shared Given the visible-`given()` rule
just fixed — arrange-failures and contract-failures merge again, for a subset of the file. And composed
headings (*closing a split order › closes when the last fulfillment completes*) don't travel: scenarios get
quoted standalone into PRD diffs, QA notes and FE handoffs, where a flat proposition survives whole and a
heading needs its context reassembled. A file that wants two groups wants two files (§8). The extractor still
*renders* `describe()` so foreign or converted files don't vanish — tolerance, not the idiom.
Pest's default output already prints the description list — no `--testdox` needed.

### 0.1 Installing Pest on a client repo that doesn't have it (one-time)

The knot, learned the hard way on LO: client repos pin `phpunit/phpunit` in `require-dev` (usually alongside
`orchestra/testbench`, which requires it and blocks its removal), and the patches workflow
(`symplify/vendor-patches` → `patches/bin/restore-oldfiles` in `post-cmd-common`) uses `sebastian/diff`
classes that were only present *transitively via PHPUnit* — so a naive remove/require dance breaks composer's
own post-install scripts halfway through. The order that works:

```bash
# 1. keep the patches workflow alive through the transition — sebastian/diff was only
#    installed via phpunit, and patches/bin runs on every composer install (all
#    environments), so it goes in `require`, not require-dev
composer require sebastian/diff

# 2. drop the direct pins that block Pest's phpunit ^11
composer why phpunit/phpunit                                # see what else pins it
composer remove --dev phpunit/phpunit orchestra/testbench   # --dev, or composer stops to ask; testbench only if present

# 3. install Pest (allow the plugin non-interactively first)
composer config allow-plugins.pestphp/pest-plugin true
composer require pestphp/pest --dev --with-all-dependencies

# 4. restore testbench — the SN test harness needs it; it now resolves against Pest's phpunit ^11
composer require --dev orchestra/testbench

# 5. scaffold, then delete the scaffold junk
./vendor/bin/pest --init
rm -f tests/Feature/ExampleTest.php tests/Unit/ExampleTest.php
```

A brand-new client repo with no test suite yet has no testbench to remove — steps 2/4 shrink to dropping the
`phpunit/phpunit` pin if present (and testbench still gets required in step 4). Do **not** install
`pest-plugin-drift` — the one-shot conversion experiments needed it; authoring doesn't.

Then three files by hand:

**`tests/Pest.php`** — replace the `--init` scaffold (the `toBeOne` expectation, the empty helper) with the
base-class binding and the `given()` marker; bind further folders (e.g. GraphQL) when the first test there
needs it:

```php
<?php

pest()->extend(Tests\TestCase::class)
    ->in('Feature');

/*
| given() is the Given-delta marker of the behavior grammar: it only invokes
| the closure, whose $this binding comes from the test closure that created
| it. PHPUnit-style classes keep the equivalent Tests\TestCase::given().
*/

function given(Closure $delta): void
{
    $delta();
}
```

**`composer.json`** — `"test": "vendor/bin/pest"` (`vendor/bin/phpunit` is hijacked and errors with
`InvalidPestCommand`); update any other script that calls `vendor/bin/phpunit` (coverage →
`vendor/bin/pest --coverage`).

**`tests/TestCase.php`** — `bus()` becomes `public` (file-level `when*` functions reach it via `test()`);
keep `$this->given()` on the class for PHPUnit-syntax files.

**An auxiliary base test case becomes a trait.** Pest gives a file exactly one test case class, and
`tests/Pest.php` already binds `Tests\TestCase` folder-wide — so a second base class has nowhere to stand.
`class GraphQLTestCase extends TestCase` becomes `trait GraphQLTestCase`, attached per file with
`uses(GraphQLTestCase::class)`; its `protected` helpers and consts stay reachable from every closure, and the
binding it used to inherit now comes from `Pest.php`. Keep the class's docblock reasoning with the trait — the
*why this base and not core's* is the part a reader needs and the syntax change hides.

Verify before writing or converting anything: `composer test` — the existing PHPUnit-syntax suites must run
green under the Pest runner (they will; Pest executes them natively).

## 1. GWT vs Arrange/Act/Assert — same skeleton, different voice

They are the same three blocks. The difference is what language the blocks speak:

- **AAA** describes what the *code* does: construct objects, call a function, compare values.
- **GWT** describes what the *domain* does: a state of the world, an event, a promise.

The convention: **lay tests out as AAA, but name everything in GWT language.** The blocks are mechanical
(blank-line-separated, in order); the *words* inside them are domain sentences — builders are Givens
(`aReceivingCart()`), the dispatch is the When (`whenCreatePutAway()`), domain assertions are Thens
(`assertPutAwayLocationHolds()`). When the vocabulary is named right, the test reads as GWT without a single
`// GIVEN` comment. Don't annotate blocks with GWT comments in every test — that's the label-drift problem in
miniature; one comment over the shared Given in `beforeEach` is plenty.

Litmus test for which voice you're in: if the test says `expect($rows)->toHaveCount(3)`, it speaks AAA
(implementation); if it says `$this->assertFulfillmentHasItems($f, count: 3)`, it speaks GWT (contract).
Always prefer the second — that's the whole §5 bet.

## 2. Anatomy of a test file

**One file = one behavior surface** — one command, one endpoint, or one pure algorithm. The file name is the
subject (`CloseRmaTest.php`); the `test()` descriptions are its promises; Pest's own output of the file is
its spec.

```
CloseRmaTest.php
├── namespace Tests\Feature\PestOrderRMA\CloseRma;   ← kept — makes consts/when* collision-proof
├── use …                                             ← imports
├── uses(OrderRmaScenarioTrait::class);                    ← vocabulary, never inline plumbing
├── const NEVER_ARRIVED = '…';                        ← file constants, namespaced
├── beforeEach(fn)                                    ← the shared GIVEN, state only
├── test('clause one', fn)                            ← (given delta) + When + Then
├── test('clause two', fn)
├── test('guard clause', fn)
└── function whenClose(…)                             ← the WHEN, at the bottom, dispatch only
```

The real thing (abridged):

```php
namespace Tests\Feature\PestOrderRMA\CloseRma;

use App\Domain\OrderRMA\Commands\CloseRma\CloseRmaCommand;
use App\Domain\OrderRMA\Exceptions\RmaNotApprovedException;
use App\Domain\OrderRMA\Values\ClosedOrderRma;
use SkuNexus\RMA\Domain\Values\States\Closed;
use Tests\Behavior\OrderRmaScenarioTrait;

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

test('force closing an approved rma closes it', function () {
    given(fn () => $this->acceptEveryLineOf($this->rmaId));

    $closed = whenClose(NEVER_ARRIVED);

    expect($closed)->getState()->toBe(Closed::STATE);
    expect($this->theRma($this->rmaId))->getState()->toBe(Closed::STATE);
});

test('a pending rma cannot be force closed', function () {
    expect(fn () => whenClose(NEVER_ARRIVED))->toThrow(RmaNotApprovedException::class);
});

function whenClose(string $reason): ClosedOrderRma
{
    return test()->bus()->handle(new CloseRmaCommand(test()->rmaId, $reason))->getValue();
}
```

**Where `$this` reaches and where it doesn't** — the one Pest fact that decides every placement below:

| Inside… | Binding | Reaches |
|---|---|---|
| `test()` / `beforeEach()` closures | class-scoped `$this` | **private** scenario-trait methods, **protected** base-`TestCase` methods, trait constants via `self::X`, dynamic properties |
| a named file-level `function` | no `$this` at all | only `test()->…` — so `bus()` is **public** on `tests/TestCase.php`, and any property a `when*` reads is public |

That asymmetry is the whole reason the idiom keeps file-level functions to ~1–2 per file and routes
everything else through `$this`: privacy survives everywhere except inside a top-level `function`.

Two consequences of the second row that a whole suite conversion found the hard way:

- **A trait constant has no name a file-level function can spell.** There is no `self` in a function, and PHP
  forbids reaching a trait constant through the trait: `HospitalScenarioTrait::ITEM_QTY` is a fatal
  `Cannot access trait constant … directly`. The one working shape is **`test()->target::ITEM_QTY`** — the
  test case object read off the proxy, then an ordinary `::` fetch. spec-extract folds that back to `self::X`
  and renders the value, so the step still reads "4 units" and not "the test". Better still, take the const as
  a parameter and pass `self::X` from the closure — then the function needs no shape at all.
- **The container is reached with `app()`, never `test()->app`.** `$app` is `protected` on Laravel's own
  `TestCase`, so the "make it public" cure that works for `bus()` is not available — it is not our class.
  Inside a file-level function use the helper: `app()->make(FooRepository::class)`. `test()->app` fails at
  runtime with `Cannot access protected property P\Tests\…::$app`, and it is the single most common breakage
  in a mechanical conversion.

## 3. Placement rules — what goes where

**`beforeEach` holds the shared Given, and only state.** Every test in the file must want all of it. No
dispatch of the command under test, no assertions, ever. Put the `// GIVEN …` headline comment on its first
statement (the extractor reads it there and nowhere else). If only half the tests share a piece of setup,
that piece moves into those tests — or the file wants to be two files. `parent::setUp()` has no Pest
equivalent and no substitute; Pest chains the base class itself.

**Given deltas open the test body, marked `given`.** One packaging, not two:

```php
given(fn () => $this->acceptEveryLineOf($this->rmaId));   // a delta over the shared world
given(fn () => Queue::fake());                            // a boundary fake is arrange, so it rides here too
given(fn () => whenClose(NEVER_ARRIVED));                 // a prior act as precondition — legal, and reads right
givenTheRmaIsApproved();                                  // a given*-NAMED function: already marked, so called bare
```

`given()` is a bare global in `tests/Pest.php` — `function given(Closure $delta): void { $delta(); }`. The
closure captures the test's `$this` at creation, so trait privacy is intact and nothing is threaded: state
stays in properties, and the marker carries no string label (nothing to drift). PHPUnit files keep
`$this->given(...)`; the two coexist without conflict.

**One marker per step — the name or the wrapper, never both.** `given(fn () => givenTheRmaIsApproved())`
marks the step twice, and the cost is not cosmetic: prose extraction reads the inner call's leading `given` as
the sentence's verb, so it renders *"the RMA is **is givened** approved"*. A `given*`-named function is
already marked; call it bare. A name that does **not** start with `given` needs the wrapper. Stripping the
prefix to keep the wrapper is the wrong repair — the next word becomes the verb, and
`given(fn () => everyUnitOfTheItemIsInATote())` reads *"unit of the item is is everyed in a tote"*.

The bare call earns something extra: it is the **only** shape whose body is read. The extractor follows a bare
`given*` call one hop and renders the first vocabulary call inside it as a second-level detail — `a bay that
cannot cover the shortage — by a hospital item short of six units`. Inside a `given(fn () => …)` wrapper that
hop is invisible and the detail is lost.

**The PHPUnit "named private `given*` method" form does not dissolve in Pest — it graduates or goes global.**
There is no file-private named function, so a delta that *states a rule's condition* and recurs
**graduates into `{Domain}ScenarioTrait` as a builder whose name states the condition** (`aPickingCart()`,
`anRmaWithNoApprovedLines()`), called as `given(fn () => $this->aPickingCart())`. That is still the preferred
home. When the delta is genuinely file-local and too big to inline, the ratified fallback is a namespaced
file-level `function givenX(): void` called bare — the shape a mechanical conversion produces, and the shape
that reads best. A genuinely one-off delta stays inline. The rule the PHPUnit form protected still holds: when
the test name references a *condition* of which the builder is one instance, the name in the body and the name
in the test must be the same words — which is also why such a helper is never inlined away: inlining deletes
the name, and the name was the sentence.

With deltas marked, **the body grammar is total: every line in a test body starts with `given`, `when`,
`expect`, or `assert`.** That is mechanically checkable, and it makes spec extraction a name-splitter:
*Given every line is accepted, when close, then the RMA is closed*.

**The When lives in the test body, always** — one line, calling the file's namespaced `when` + domain-verb
function (§4). Never in `beforeEach` (the body loses its verb, arrange-failures and contract-failures blur,
and the file goes rigid — no guard or variant test can exist once `beforeEach` has already acted).
**One When per test.** Two dispatches means one of them is really a Given (wrap it in `given(fn () => …)`) —
unless the sequence *is* the contract ("dispatching twice creates one fulfillment"), in which case the pair
is the When and stays inline.

**The `when*` function is a dispatch wrapper and nothing else** — one line, `return test()->bus()->handle(new
XCommand(…))->getValue();` (§2). Its arguments are built by `$this->` **at the call site**, so trait builders
stay private and the global stays trivial. One per file; two is the ceiling (a `the*` reader a `when*` needs
is the only common second). Everything else goes through `$this`.

**The Then asserts one contract clause per statement.** Two shapes, both correct, chosen by what is being
read:

- **Entity reads → higher-order expectations, the preferred shape:**
  `expect($rma)->getState()->toBe(Closed::STATE)` reads subject → accessor → matcher ("the RMA's state is
  closed") and gives the extractor a mechanical rendering.
- **Domain propositions → the trait's `$this->assert*` calls, unchanged.** They fail in domain language
  ("Expected order 42 to be 'closed', but it is 'in_fulfillment'"). **Do not rewrite them into `expect()`
  chains** — a bare matcher mismatch dump is a downgrade.

**One clause per `expect()` statement — sibling `expect()` calls, NEVER `->and()` chains.** A clause is a
sentence, not an assertion: two lines that jointly state "the received stock is in the put-away location"
belong together; a second *sentence* belongs in a second test. `->and()` fuses distinct clauses into one
statement and one failure line, which is exactly what the doctrine is buying its way out of.

**Exception outcomes are Thens, asserted as Thens:**
`expect(fn () => whenClose(NEVER_ARRIVED))->toThrow(RmaNotApprovedException::class)` — the Pest-native
equivalent of `assertThrows`. The When stays visible inside the closure and **execution continues after the
throw**, so a guard's second clause ("…and the state did not move") is a sibling `expect()`/`assert*` in the
same test. `$this->assertThrows(...)` remains valid if preferred. Never `expectException` — it forces the
Then before the When and makes everything after the When unreachable.

**HTTP endpoint tests are unchanged inside Pest closures:** `$this->postJson('/api/…', [])` then
`$response->assertStatus(422)`. Assert status + error body; the frontend consumes JSON, not exception classes.

## 4. Naming

**A test description is a proposition — something that is true or false.**
`test('put away moves the received stock into the put away location', …)` is falsifiable;
`test('create put away works', …)` is not. Banned words: *works, correctly, properly, successfully, should* —
they carry no proposition. Present tense, subject–verb–outcome, lowercase and spaced (the mechanical mapping
from the PHPUnit snake_case name: replace `_` with a space, drop nothing else).

- **Lowercase is the default and it matters downstream.** An all-lowercase description is sentence-cased and
  initialism-corrected by the extractor ("rma" → "RMA"); a description containing *any* uppercase is treated
  as authored prose and rendered verbatim. Use mixed case only when you mean to override the casing.
- **Guards name the rule, not the mechanics:** `'a pending rma cannot be force closed'` — the exception class
  is asserted in the body, not encoded in the description.
- **Builders:** indefinite article = creates (`aWarehouse()`, `anActiveProduct()`); definite article =
  retrieves what the seed guarantees (`theAdminUser()`); verb phrase = a Given-action (`receiveIntoCart(...)`).
- **The When helper: `when` + the imperative domain verb** (`whenCreatePutAway()`). This completes the
  morphological grammar — Given is marked by articles, Then by `expect`/`assert`, and without the prefix the
  When is the one unmarked verb, indistinguishable at the call site from a Given-action (`receiveIntoCart`
  arranges, `createPutAway` acts — same grammar). Derive it mechanically (`when` + verb phrase), don't
  hand-craft English (`whenPutAwayIsCreated`). Bonus: `grep '^function when'` lists every act in the suite.
- **Given deltas: marked `given`, inline, always** (§3). Vocabulary builders themselves stay unprefixed
  (article grammar) and do the actual work inside the closure.
- **Assertions:** `assert` + a domain proposition (`assertItemDestinedFor(...)`), failing with a domain
  sentence, never a bare matcher mismatch dump.
- **Traits carry a `Trait` suffix, file name matching** — `OrderRmaScenarioTrait`, `PutAwayAssertionsTrait`,
  `DomainAssertionsTrait` in `tests/Behavior/`; `uses(OrderRmaScenarioTrait::class);` reads as vocabulary.
  Team convention; rename any un-suffixed trait you touch.
- **Actors get distinguishable names.** `$coffee`/`$tea`, `$locationA`/`$locationB` — never
  `$product1`/`$product2`. Type-identical pairs are where silent transposition hides; distinct names make a
  swapped assertion visibly wrong.

## 5. Readability rules

1. **The correspondence principle.** Every value in a Then traces to a visible line in the Given or When:
   `aReturnLine(..., quantity: 4)` up top is *why* `expect($line)->getQuantity()->toBe(4)` below. A number
   appearing only in the Then is a magic number; a factory default silently satisfying an assertion is a time
   bomb — pin every field an assertion depends on.
2. **Named arguments for literals.** `quantity: 4`, `in: $warehouse`, `count: 3` — call sites label
   themselves, in `when*` calls and builders alike.
3. **No logic in test bodies.** No `if` (a branching test tests two things or none), no `foreach` over
   assertions (a loop hides which iteration failed — and Pest's `->each` modifier is the same sin with
   nicer syntax). Matrices go in a string-keyed dataset: `test('…', function (string $state) { … })
   ->with(['pending' => [Pending::STATE], 'declined' => [Declined::STATE]]);` — name the cases; the keys are
   the prose. Iteration may live *inside* a domain assertion, which reports the failing element.
4. **Budgets as smoke alarms.** Test body ≤ ~12 lines, `beforeEach` ≤ ~10 vocabulary lines, file-level
   functions ≤ 2. Exceeding them doesn't mean "split mechanically" — it means a vocabulary word is missing or
   the file covers two surfaces.
5. **Comments only for what code can't say:** domain gaps (`// DOMAIN GAP: no command sets a cart's
   department`), non-obvious constraints. Never restate the description in a comment above the test.
6. **File reads as the spec, in spec order.** Happy-path clauses first, then guards and edge cases. Before
   committing, run the file (`vendor/bin/pest path/to/File.php`) — the default output *is* the description
   list; if a sentence reads wrong, the description is wrong.
7. **Audit the code against the prose scenarios** (when scenarios exist — e.g. the GWT sentences of a §8
   skeleton). Line them up word by word: every prose clause must own a code word (a missing assertion hides
   here), assertions mirror prose word order (`assertPutAwayLocationHolds`, not
   `assertStockInPutAwayLocation`), builder parameters speak prose not structure (`label: 'a'`, never
   `['location' => 'a']`), actors are named in the data so failures speak the scenario
   (`anActiveProduct(named: 'coffee')` → "Expected 10 of coffee…", not a faker SKU) — and one dialect per
   noun: if the prose says "shelf" and the code says "location", one of them is wrong; pick the ubiquitous
   term and use it on both sides.
8. **Audit the description against the body — the promise ledger.** §5.7 audits prose → code; this audits
   name → code, and it is where a *landed* suite leaks: a description that reads correct makes a weak body
   invisible in review, and the runner then publishes the promise as if it were proved. Read the description
   as a sentence and make every word earn an assertion — each noun exists in the fixture, each qualifier is
   asserted, each quantifier is exercised, each clause has a Then. The eight modes below were all found by
   rendering a landed suite's spec and reading its clauses back against its names.

   | The description promises… | …the body proves | Cure |
   |---|---|---|
   | a state — `'…stays pending'` | `expect(...)->not->toBe(Closed::STATE)`, true of every wrong state | assert the named state positively through the state VO |
   | a relationship — "a line of *another* RMA" | a random unknown id | build the noun the description names, or rename to what the fixture built ("an unknown line") |
   | one proposition | two — the deciding half is a `test()->fail()` inside a `the*` read helper | assertions live in the body; a helper that can fail is named `assert*` and its clause is visible in the test |
   | two clauses — "is already closed **and so** cannot be received" | the second clause only | assert both, or split into two tests |
   | a value — "reports the customer and the order date" | `->toHaveKey(...)` — a renamed resolver returning null passes | assert the value against the Given's known input |
   | a scope — "a put-away **for the returned units**" | that *a* put-away exists | assert the qualifier (quantity, product, destination) or drop it from the description |
   | a quantifier — "**every** line pending" | one line in the fixture | the fixture carries ≥2 and the assertion covers the set, or the description drops to the singular |
   | an exact outcome | `->toBeGreaterThan(0)` where the Given fixed the number | assert the number — open comparators are smoke tests, not contracts |

   **The cheap greps** (run over a file before committing, and over a suite you are reviewing):
   `not->toBe\(.*STATE` (a negative standing in for a positive state assert) · a test whose only Then is
   `toHaveKey|not->toBeEmpty|toBeGreaterThan` · `fail\(` in a function not named `assert*` ·
   a description containing `every|all|each|both` in a file whose `beforeEach` builds one actor.

   **The read-back.** The runner gives you the descriptions; the bodies you must read. Render the file's spec
   (§10.5) and check each clause against its description: the mismatch is obvious in prose and near-invisible
   in a diff.

## 6. Where plain AAA (no ceremony) is correct

Pure unit tests — value objects, algorithms — skip the whole apparatus: no `beforeEach`, no `uses()`, no
vocabulary, arrange inline, because input → output already *is* the contract in one breath:

```php
test('greatest of equal values is that value', function () {
    expect(Qty::greatest(new Qty(5), new Qty(5))->getValue())->toBe(5);
});
```

Forcing GWT ceremony onto these is noise in the other direction, and existing raw-PHPUnit unit classes are
fine exactly as they are — Pest runs them. The apparatus earns its keep exactly where the world is wide:
container-backed Feature tests of cross-domain commands.

## 7. The copyable skeleton

```php
<?php

namespace Tests\Feature\<Domain>\<Command>;

use Tests\Behavior\<Domain>ScenarioTrait;

uses(<Domain>ScenarioTrait::class);

const <SHARED_LITERAL> = '…';        // namespaced; if a second file needs it, it becomes a trait const

beforeEach(function () {
    // GIVEN <the shared world, in one sentence>
    $this->warehouse = $this->aWarehouse();
    // ... vocabulary sentences only — no dispatch of the command under test, no assertions
});

test('<subject verb outcome — a lowercase, falsifiable proposition>', function () {
    given(fn () => $this-><aPrecondition>());          // optional GIVEN delta

    $result = when<DomainVerb>(...);                   // WHEN — one line, one act

    expect($result)-><getAccessor>()->toBe(<expected>);   // THEN — one clause, read-side
    $this->assert<DomainProposition>(...);                // THEN — domain language failures
});

test('<the guard, named as the rule>', function () {
    expect(fn () => when<DomainVerb>(...))->toThrow(<Exception>::class);

    $this->assert<StateDidNotMove>(...);               // the guard's second clause, still reachable
});

/** WHEN — the contract's trigger, stated once. Args are built by $this-> at the call site. */
function when<DomainVerb>(...): <DomainResult>
{
    return test()->bus()->handle(new <Command>(...))->getValue();
}
```

---

## 8. Scenario-first, without extra files — the skeleton form

Writing the scenarios in English *before* the test code is the discipline; a standing `.scenarios.md` per
test file is not — it would be a parallel English artifact that can drift, the same disease as labeled DSLs.
The exercise's native home is **the test file itself, committed first as a skeleton**:

```php
test('split order closes when its last fulfillment completes', function () {
    $this->markTestIncomplete(
        'Given the order is split across shipment and pickup,'
        . ' and the shipment has already completed;'
        . ' when the pickup completes; then the order is closed.'
    );
});
```

`markTestIncomplete` works unchanged inside a Pest closure. Descriptions are the scenario titles (already
propositions, §4); each body carries its GWT sentence until implemented. The skeleton is runnable (the
runner renders the scenario list before any code exists), reviewable (the spec is commit 1 of the PR), and
**self-deleting** — implementing a test replaces the sentence with the three role-marked lines that say the
same thing, so drift is impossible. Batching *titles* up front is writing the spec, not horizontal slicing —
implementation still proceeds one vertical slice at a time (red → green per scenario). Scenarios that
pre-exist in a PRD or plan flow into skeleton descriptions; they don't get duplicated into a second document.

## 9. Who shares what — the vocabulary graduation ladder (Pest amendment)

Scenario and assertion traits are **per domain, shared by every test file in that domain** — `tests/Behavior/`
is flat, and `OrderRmaScenarioTrait` serves all nine RMA files. A test file whose world spans domains composes
several scenario traits with one `uses(A::class, B::class)`.

Pest removes one rung the PHPUnit ladder relied on: **PHP has no file-private named functions**, so anything
that would have been a private helper is either an inline closure or a namespaced global. The ladder becomes:

```
inline given(fn) deltas + the file's namespaced when* function   — never graduate (file-contract-specific)
  → {Domain}ScenarioTrait / {Domain}AssertionsTrait   — a NAMED compound builder graduates as soon as ONE Pest file
                                              needs it; a word moves in when a second FILE needs it
    → Behavior\DomainAssertionsTrait             — an assertion moves up when a second DOMAIN needs it
```

The amendment is only at the bottom: a **named** compound builder (`anApprovedWriteOffRma()`,
`anRmaWithNoApprovedLines()`) graduates to `{Domain}ScenarioTrait` on first need rather than on the second
consumer — it is domain vocabulary anyway, and the alternative is multiplying namespaced globals. Keep
file-level functions to ~1–2 per file (the `when*`, occasionally one `the*` reader a `when*` needs);
everything else routes through `$this`. Anonymous one-off deltas never graduate — they stay inside
`given(fn () => …)`.

A trait method a `when*` global reaches via `test()->` must be `public`; everything a test closure calls can
stay `private`. Prefer arranging the call so the trait method is reached from the closure (`$this->`), not
from the global.

Nothing is created speculatively at any tier — every promotion is triggered by a real consumer.

---

## 10. The test is also the published spec — writing for spec-extract

**Status: the Pest grammar has shipped.** The extractor reads both syntaxes — `--mode` defaults to `pest`,
`--mode=phpunit` for a class-syntax tree. A 40-file Pest suite extracts at full parity with its PHPUnit
original: same scenario count, same Background, same steps, the difference down to the one test that was
deliberately renamed. So a converted suite is a first-class spec source, and nothing below is speculative
shaping.

What the Pest grammar will read, and therefore what to write:

| You write | The spec shows |
|---|---|
| `test('force closing an approved rma closes it', …)` | a scenario heading, sentence-cased with dialect initialisms — "Force closing an approved RMA closes it" |
| a description containing **any** uppercase | rendered **verbatim** — the authored-prose channel (`closes an OrderRMA` is never mangled) |
| `beforeEach(fn)` with `// GIVEN …` on its first statement | the **Background**, under that headline |
| `uses({Domain}ScenarioTrait::class)` | the vocabulary the step prose is resolved against |
| bare `given(fn () => $this->…)` | a **Given** step |
| a bare `givenX();` call to a file-level `given*` function | a **Given** step, plus a `— by …` detail read one hop into its body |
| a file-level `when*` function wrapping `test()->bus()->handle(new XCommand(…))` | passive command prose — "the RMA is closed with reason 'never arrived'" |
| `test()->target::ITEM_QTY` in a step's arguments | the constant's **value** — "4 units", folded back to `self::X` |
| `expect($rma)->getState()->toBe(X)` | a **Then**, read subject → accessor → matcher |
| `expect(fn () => when…())->toThrow(X::class)` | the attempt, then "it is rejected — …" |
| `expect(fn () => when…())->toThrow(X::class, MESSAGE)` | the same, plus "and the rejection message contains …" |
| `$this->assert*` trait calls | Thens, exactly as in PHPUnit suites |
| `->with(['pending' => […]])`, or `->with('name')` + `dataset('name', fn)` | a **Where** step listing the case names |
| a file docblock after `namespace`; a `//` note above a `test()` call | the file blockquote; the scenario note |

### 10.1 Free rides — and the placement gotchas that silently eat them

- The `// GIVEN` comment is read on `beforeEach`'s **first statement** and nowhere else.
- The file docblock belongs **after** `namespace` (above it, php-parser hands it to the namespace node).
- `markTestSkipped('the ACL check is missing')` renders `⚠ NOT RUNNING — the ACL check is missing`; the
  argless call renders only a default.
- **Keep `when*` wrappers one hop above the dispatch.** One wrapper deep, the spec reads the command; two
  deep, it falls back to the wrapper's own name.
- **Assertions inside closures, loops, or `each` chains are invisible** — the scenario renders
  `⚠ NOTHING READ`. §5.3 bans body logic anyway; the extractor is the lint that makes the ban visible.
  (`given(fn () => …)` and `expect(fn () => …)->toThrow()` are recognized shapes, not "logic".)

### 10.2 Custom assertions and expectations — shape the name so the subject promotes

A custom `assert*` helper's subject (the **last** variable argument) promotes into the phrase whenever the
name can host it: a phrase ending on a copula (`assertHospitalIssueIs`) or closing on a preposition with one
argument (`assertNoAllocationsFor`) reads as "the fulfillment's hospital issue is 'withdrawn'". A name that
can't host its subject renders as marked call syntax — `⚠ RAW — tote qty for(the cart, the item, 1)` —
honest, greppable, ugly. Higher-order `expect()` chains promote their subject for free, which is one reason
they are the preferred entity-read shape. An `expect()` matcher outside the recognized set falls to
`⚠ RAW` rather than an invented sentence.

Custom `expect()->extend('toHoldQty', …)` expectations (Pest's sanctioned home for a helper that judges) are
a **phase-2** move, not yet in any suite and not yet read by the grammar. Until then, domain assertions stay
`assert*` trait methods. Whichever form, the rule holds: a helper that can fail is named for the judgment it
makes, and its clause is visible in the test.

### 10.3 `#[TestDox]` — the one-line override, used sparingly

`#[TestDox('…')]` on a **file-level Pest helper function** is legal PHP, inert to Pest, and is the same
prose-override channel it is on a PHPUnit helper method. Three homes, in descending order of warrant:

1. **On an assertion helper** whose derived prose is `⚠ RAW`: `#[TestDox('{tote} holds {qty} of {item}')]` —
   `{param}` slots fill from the call's arguments by parameter name; one line at the definition fixes every
   call site.
2. **On a `when*` function** whose derived sentence reads wrong: the template replaces the derived prose
   verbatim (write the finished sentence — it is not passivised for you).
3. **On a test** — unnecessary in Pest: the `test()` description *is* authored prose (§4). Use mixed case in
   the description instead of reaching for an attribute.

Default: **no TestDox on `when*` and `assert*` helpers whose derived English reads** — there an attribute
is a second source of truth that can drift. **Default: TestDox on every scenario builder with two or more
parameters** — derived prose for a parameterised builder dumps every argument with its parameter name and
the constant's *name* spelled out (`an imported shopify order of number 936285, shopify created at settled
long before the sweep`, 127 times in one suite), and the docblock gloss renders on every call. One
`#[TestDox('order #{number} already imported, created {shopifyCreatedAt}')]` at the definition fixes all
of them and retires the gloss (the attribute outranks the docblock). Slots must name real parameters — a
typo'd `{slot}` leaks into the spec verbatim — and every sentence must be **true of the body**: a TestDox
that claims a link the fake does not have is a wrong spec, which is worse than an ugly one.

### 10.4 Dialect words — last resort, evidence required

When a DOMAIN word inflects wrong in every suite ("unholded", "reshiped") or an acronym renders lowercase
("sku urls"), the fix is one entry in the extractor's dialect config (irregular participle/gerund,
initialism), filed once in the spec-extract repo
(https://github.com/SkuNexus-Devs/dev-ian-spec-extract) — not a TestDox per call site. One word per
demonstrated, recurring need; generic English/PHP words belong to the base dialect, SN domain words to the SN
dialect. Never add a dialect word to fix one test's prose — that's TestDox's job; never TestDox around
grammar — that's the dialect's job.

### 10.5 The read-back and the debt greps

Before committing a new test file, render it and read it as the reviewer will:

```bash
spec-extract tests/Feature/PestOrderRMA/CloseRmaTest.php   # one file, spec to stdout
spec-extract tests --output=.ai/<TICKET>/spec-from-tests.md # the suite: pass the DIRECTORY
spec-extract tests-orig --mode=phpunit                     # a class-syntax tree needs the flag
```

**Pass a directory, not a shell glob.** `tests/**` is expanded by bash before the tool sees it, and a
directory argument is walked for `*Test.php` while an explicitly named *file* is read whatever it is called —
so `tests/**` feeds it `TestCase.php`, `GraphQLTestCase.php` and `Pest.php`, which render as junk sections
(`TestCase.php`'s `setUp()` becomes a Background full of raw PHP). With `shopt -s globstar` it is worse: every
file *and* its parent directory get passed, so scenarios are read twice. If you really want a glob, quote it
so the tool expands it (`'tests/Feature/Hospital/*/*Test.php'` — PHP `glob()`, one level per `*`, no `**`).

Then the two debt greps over the rendered spec, both of which should trend to zero suite-wide: `⚠ RAW` (an
assertion wanting a copula-shaped name or a TestDox) and `⚠ NOTHING READ` (a body the grammar cannot see —
almost always logic in the body). `⚠ NOT RUNNING` is not debt; it's a skip doing its job. Read the §5.8
ledger by eye alongside it — the promise audit is the part no tool does.

### 10.6 What a `{slot}` renders — measured, not documented

Probed against the packed phar with scratch files — re-probe when the phar changes. These decide which
rung fixes a line; the ones marked ↑ are extractor limitations to file upstream (the readability pass's
`spec-extract-requests.md` deliverable is where they are listed, with repro and workaround).

| The slot is fed… | Renders as |
|---|---|
| an `int` literal | bare `936285` (a quantity-named param gets its unit: `$qty` → `7 units`) |
| a `string` literal or `string` const | `<param label> “value”` — `$orderName` → `order name “#936290”`; a numeric-looking string loses the label ↑ |
| an array of **1** | `<param label> “#936290”` — label kept ↑ |
| an array of **2+** | `“#1”, “#2” and “#3”` — label dropped ↑ |
| an empty array | **nothing** — the sentence ends `exactly ` ↑ → wrap: `assertNoCandidatesDispatched()` → "repulls nothing" |
| a parameter left to its default | **nothing** ↑ → never slot an optional; a `times:` count needs a wrapper (`…TwiceFor`) with "once" in the default sentence |
| a constant via a default (`int $x = self::X`) | nothing ↑ → write the value into the sentence, comment "keep in step with the const" |
| `$this->prop` | the property name as English — `$this->otherStore` → `the other store` |
| a **local assigned at test top level** | the **whole assigned expression, inlined** ↑ — the cause of every "Then that repeats its Given" |
| a nested value helper carrying its own `#[TestDox]` | the attribute is **ignored**; the helper's derived name renders (`of days 70`) ↑ → no-arg readers named for meaning |
| `given(fn () => $this->prop = CONST)` | `Given the test` ↑ → assign a trait reader bare: `$this->unknownStore = $this->anIntegrationIdNoStoreCarries();` |
| a Background step opening with a proper noun | first character lowercased after TestDox ↑ → start with the article or the domain noun |
| a docblock gloss opening with a proper noun | lowercased, initialisms not applied ↑ → reword |
| a raw harness call in `beforeEach` (`Carbon::setTestNow`, `rebootHandlers([...])`) | invented prose (`the carbon set test now “…”`) instead of `⚠ RAW` ↑ → a named scenario helper with TestDox |
| a helper whose name **starts with a proper noun** (`shopifyRejects…`) | read as the subject and passivised — `rejects … are shopifyed` ↑ → subject-first name (`theCandidateLookupsAreRejected`) |

### 10.7 Authoring rules that keep the render readable — the first-pass checklist

Each of these was a defect class in a landed suite; writing to them costs nothing and saves the second pass
(`spec-readability-pass.md`).

1. **Every builder with ≥2 params carries a `#[TestDox]`** with the domain noun first: `order #{number} …`,
   never `an imported shopify order of number …`. Where a gloss carried information, it goes *in* the sentence.
2. **Helpers take the domain number, not the transport id.** `assertRepulledFor(936290)`, not
   `assertRepulledFor($gid)`; the gid is built inside (`orderGid()`), so no local ever holds it. Then the
   builders return `void` — a `: string` nobody reads is an orphan a green suite can't see.
3. **Actors are properties, never locals**, when an assertion or a `when*` needs to say *which*:
   `$this->store`, `$this->otherStore`, `$this->unknownStore`, with a `{store}` slot on `assertCursorAt`
   and on `whenTheSweepCommandRunsFor`. Two cursors asserted with no store named is a §5.8 hole, not prose.
4. **Harness calls are named scenario helpers** — `theClockIsFixedAt(…)`, `queuedRepullsAreRecordedNotRun()`,
   `aRepullByIdsHandingBackEveryRequestedId()`. Boundary fakes stay visible; only the wording is domain.
5. **Setting values are in the Background sentence** — `a sweep with a 60-minute grace window, a 60-day
   age-out and 2 failures before giving up` — with a comment that they restate the consts. "Older than the
   age-out" is unfalsifiable to a reader who is never told the age-out.
6. **Time offsets are named readers derived from the consts** — `pastTheAgeOut()`, `justInsideTheAgeOut()`,
   `insideTheGraceWindow()` — not `daysBeforeTheSweep(70)` at the call site.
7. **A `when*` never asserts.** It returns the exit code / result; the body asserts it, so the Then renders
   and every sibling scenario shows the same Then.
8. **Counts are in the sentence** — "is repulled once" in the default, `assert…TwiceFor()` → "a second
   time". A slot-less count is a title promise ("a single retry", "again") the spec cannot show.
9. **The empty case has its own word** — `assertNoCandidatesDispatched()`, `toBeEmpty()`.
10. **An assertion's TestDox names the observable, not the rule** — `the eligibility lookup carries
    {pullFilterTerm} and narrows by no created_at or updated_at window`, never a restatement of the title.
11. **Helper names start with the domain subject**, never with a proper noun (`shopify…`); docblocks and
    Background TestDoxes don't open with one either.
12. **`//` *why* notes go above `test()`**, not in the body — they are the suite's best content and only
    render there.
13. **Descriptions that contain any uppercase (`Shopify`) start with a capital** — they render verbatim.
14. **Pure unit tests whose scenarios differ only in arrangement** put the arrangement in `given*` file
    functions with slots (`givenShopifyReturned(name)`, `givenThePullWouldImport(name)`), a `beforeEach`
    that names the empty starting state, and a no-arg `when*` reading `$this` — otherwise five scenarios
    render identical bodies. **Pest gotcha:** `test()` is a `HigherOrderTapProxy` whose `__get` returns
    arrays by value — `test()->list[] = $x` appends to a copy and `test()->prop ?? []` misfires (no
    `__isset`); write whole arrays: `test()->list = [...test()->list, $x]`.
15. **Fixtures hold the minimum the proposition needs** — "gapless history" is two adjacent numbers, not
    six; where consecutive numbers matter, a range builder (`importedShopifyOrdersFrom(936291, to: 936294, …)`)
    renders one line.
16. **Probe before you promise.** Render a scratch copy with the phar and quote the line; a "should render
    as" in a plan is a guess.

---

*Enforcement: the review question — "read the test description and body aloud; did you hear the
behavior contract?" — plus the §6 metrics. Everything above is a default, not a straitjacket; deviate when
the contract itself demands it, and say why in a comment.*
