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
`vendor/bin/pest`. Pest executes PHPUnit test classes natively, so PHPUnit suites
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
heading needs its context reassembled. A file that wants two groups wants two files (§8).
Pest's default output already prints the description list — no `--testdox` needed.

### 0.1 Installing Pest on a client repo that doesn't have it (one-time)

> Every command in this section is written host-style. In a repo that runs PHP only inside Docker, each one
> takes the runner prefix from the skill's Quick Reference ("Where PHP runs" — the repo's `CLAUDE.md` names
> it; e.g. `docker compose exec app composer require …`). Resolve it before the first command.

The knot: client repos pin `phpunit/phpunit` in `require-dev` (usually alongside
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
  test case object read off the proxy, then an ordinary `::` fetch. Better still, take the const as
  a parameter and pass `self::X` from the closure — then the function needs no shape at all.
- **The container is reached with `app()`, never `test()->app`.** `$app` is `protected` on Laravel's own
  `TestCase`, so the "make it public" cure that works for `bus()` is not available — it is not our class.
  Inside a file-level function use the helper: `app()->make(FooRepository::class)`. `test()->app` fails at
  runtime with `Cannot access protected property P\Tests\…::$app`, and it is the single most common breakage
  in a mechanical conversion.

## 3. Placement rules — what goes where

**`beforeEach` holds the shared Given, and only state.** Every test in the file must want all of it. No
dispatch of the command under test, no assertions, ever. Put the `// GIVEN …` headline comment on its first
statement, and let it carry the settings the scenarios lean on — `// GIVEN a sweep with a 60-minute grace
window and a 60-day age-out` — because "older than the age-out" is unfalsifiable to a reader who was never
told the age-out; the correspondence principle (§5.1) covers constants too. If only half the tests share a
piece of setup, that piece moves into those tests — or the file wants to be two files. `parent::setUp()` has
no Pest equivalent and no substitute; Pest chains the base class itself.

**Harness calls in the shared Given wear a vocabulary name.** `Carbon::setTestNow(...)`, `Queue::fake()` and
`rebootHandlers([...])` are configuration, not sentences; `$this->theClockIsFixedAt($noon)` and
`$this->queuedJobsAreRecordedNotRun()` say what the world is. The boundary fake stays visible — only the
wording is domain — and a one-off fake inside a body still rides the inline marker (`given(fn () =>
Queue::fake())`, below).

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
marks the step twice. A `given*`-named function is already marked; call it bare. A name that does **not**
start with `given` needs the wrapper.

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
`expect`, or `assert`.** That is mechanically checkable, and it makes the file read as its own spec:
*Given every line is accepted, when close, then the RMA is closed*.

**The When lives in the test body, always** — one line, calling the file's namespaced `when` + domain-verb
function (§4). Never in `beforeEach` (the body loses its verb, arrange-failures and contract-failures blur,
and the file goes rigid — no guard or variant test can exist once `beforeEach` has already acted).
**One When per test.** Two dispatches means one of them is really a Given (wrap it in `given(fn () => …)`) —
unless the sequence *is* the contract ("dispatching twice creates one fulfillment"), in which case the pair
is the When and stays inline.

**The `when*` function is a dispatch wrapper and nothing else** — one line, `return test()->bus()->handle(new
XCommand(…))->getValue();` (§2). Its arguments are built by `$this->` **at the call site**, so trait builders
stay private and the global stays trivial. It never asserts: it returns the result and the body states the
Then, so the clause stays visible in the test that owns it (the same leak as a `the*` helper that can fail,
§5.8). One per file; two is the ceiling (a `the*` reader a `when*` needs
is the only common second). Everything else goes through `$this`.

**The Then asserts one contract clause per statement.** Two shapes, both correct, chosen by what is being
read:

- **Entity reads → higher-order expectations, the preferred shape:**
  `expect($rma)->getState()->toBe(Closed::STATE)` reads subject → accessor → matcher ("the RMA's state is
  closed").
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

- **Guards name the rule, not the mechanics:** `'a pending rma cannot be force closed'` — the exception class
  is asserted in the body, not encoded in the description.
- **Builders:** indefinite article = creates (`aWarehouse()`, `anActiveProduct()`); definite article =
  retrieves what the seed guarantees (`theAdminUser()`); verb phrase = a Given-action (`receiveIntoCart(...)`).
  A builder with two or more parameters carries a one-line docblock stating what it makes — domain noun
  first, true of the body (`/** An order already imported from the shop, with the given number and
  created-at. */`): the call site shows arguments, not meaning, and a summary that promises what the builder
  doesn't do is worse than none.
- **Helper names open with the domain subject, never a vendor or proper noun** —
  `theCandidateLookupsAreRejected()`, not `shopifyRejectsTheCandidateLookups()`. Subject-first names read as
  sentences about the domain; vendor-first ones read as namespaces. Docblocks follow the same rule.
- **Thresholds and offsets are named readers derived from the consts** — `pastTheAgeOut()`,
  `justInsideTheGraceWindow()` — never arithmetic at the call site (`daysBefore(70)`). The name says which
  side of the rule the scenario sits on; the number lives once, beside the const it derives from.
- **The When helper: `when` + the imperative domain verb** (`whenCreatePutAway()`). This completes the
  morphological grammar — Given is marked by articles, Then by `expect`/`assert`, and without the prefix the
  When is the one unmarked verb, indistinguishable at the call site from a Given-action (`receiveIntoCart`
  arranges, `createPutAway` acts — same grammar). Derive it mechanically (`when` + verb phrase), don't
  hand-craft English (`whenPutAwayIsCreated`). Bonus: `grep '^function when'` lists every act in the suite.
- **Given deltas: marked `given`, inline, always** (§3). Vocabulary builders themselves stay unprefixed
  (article grammar) and do the actual work inside the closure.
- **Assertions:** `assert` + a domain proposition (`assertItemDestinedFor(...)`), failing with a domain
  sentence, never a bare matcher mismatch dump. Shape the name as the sentence's predicate and pass the
  subject last, PHPUnit's own expected-then-actual order: end on a copula
  (`assertHospitalIssueIs('withdrawn', $fulfillment)`) or a preposition (`assertNoAllocationsFor($product)`),
  and the call reads aloud as a sentence about its subject. The empty outcome gets its own word
  (`assertNoCandidatesDispatched()`, not `expect($dispatched)->toHaveCount(0)`) and a count lives in the name
  (`assertRepulledOnceFor()`, `assertRepulledTwiceFor()`) — a zero or an open comparator at the call site is
  the §5.8 leak in its most common form.
- **Traits carry a `Trait` suffix, file name matching** — `OrderRmaScenarioTrait`, `PutAwayAssertionsTrait`,
  `DomainAssertionsTrait` in `tests/Behavior/`; `uses(OrderRmaScenarioTrait::class);` reads as vocabulary.
  Team convention; rename any un-suffixed trait you touch.
- **Actors get distinguishable names.** `$coffee`/`$tea`, `$locationA`/`$locationB` — never
  `$product1`/`$product2`. Type-identical pairs are where silent transposition hides; distinct names make a
  swapped assertion visibly wrong. When a Then must say *which* — two stores, two cursors — the actors are
  properties set in the shared Given (`$this->store`, `$this->otherStore`), not locals assigned at the top of
  the test: the body names them and the Given owns them. And helpers take the domain number, never the
  transport id — `assertRepulledFor(936290)`, not `assertRepulledFor($gid)`; build the gid inside the helper.
  A body speaks in order numbers a reader can place, not in ids nobody can.

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
   department`), non-obvious constraints. A *why* note about a scenario sits directly above its `test()`
   call — never inside the body, where it reads as a step. Never restate the description in a comment above
   the test.
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
   reading a landed suite's descriptions back against their bodies, clause by clause.

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

   **The read-back.** The runner gives you the descriptions; the bodies you must read. Read each body's clauses
   back against its description: the mismatch is obvious in prose and near-invisible in a diff.

9. **Sibling tests with identical bodies are a red flag.** A matrix of one proposition is a dataset (§5.3);
   five *different* propositions sharing one body means the differentiator lives only in the descriptions.
   Surface it: a named `given*` delta taking the varying value (`givenTheShopReturned('shirt')`,
   `givenThePullWouldImport('shirt')`), with `beforeEach` naming the empty starting state — each body then
   says what makes it different.

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

/** WHEN — the contract's trigger, stated once. Dispatch only — the body asserts; args are built by $this-> at the call site. */
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
runner prints the scenario list before any code exists), reviewable (the spec is commit 1 of the PR), and
**self-deleting** — implementing a test replaces the sentence with the three role-marked lines that say the
same thing, so drift is impossible. Batching *titles* up front is writing the spec, not horizontal slicing —
implementation still proceeds one vertical slice at a time (red → green per scenario). Scenarios that
pre-exist in a PRD or plan flow into the skeleton whole: a Given/When/Then acceptance sentence becomes the
`markTestIncomplete` sentence, and the description is its *then* clause with its subject, in the §4 shape — the
same proposition in two lengths, never two propositions. They don't get duplicated into a second document.

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

*Enforcement: the review question — "read the test description and body aloud; did you hear the
behavior contract?" — plus the §6 metrics. Everything above is a default, not a straitjacket; deviate when
the contract itself demands it, and say why in a comment.*
