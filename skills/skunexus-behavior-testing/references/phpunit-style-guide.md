# SN Test Style Guide — Given/When/Then

This document says *how*, and it is the normative reference for PHPUnit-syntax suites (core); the *why*
behind each rule travels with it. The practical on-ramp — a 7-step recipe, the surprises, how to run — is
`phpunit-dev-guide.md`, alongside this file; worked examples are §2 (anatomy) and §7 (copyable skeleton),
with shared vocabulary in the `tests/Behavior/` traits of the repo you are working in.

---

## 1. GWT vs Arrange/Act/Assert — same skeleton, different voice

They are the same three blocks. The difference is what language the blocks speak:

- **AAA** describes what the *code* does: construct objects, call a method, compare values.
- **GWT** describes what the *domain* does: a state of the world, an event, a promise.

The convention: **lay tests out as AAA, but name everything in GWT language.** The blocks are mechanical
(blank-line-separated, in order); the *words* inside them are domain sentences — builders are Givens
(`aReceivingCart()`), the dispatch is the When (`whenCreatePutAway()`), domain assertions are Thens
(`assertPutAwayLocationHolds()`). When the vocabulary is named right, the test reads as GWT without a
single `// GIVEN` comment. Don't annotate blocks with GWT comments in every test — that's the label-drift
problem in miniature; one comment over the shared Given in `setUp` is plenty.

Litmus test for which voice you're in: if the test says `assertSame(3, count($rows))`, it speaks AAA
(implementation); if it says `assertFulfillmentHasItems($f, count: 3)`, it speaks GWT (contract). Always
prefer the second — that's the whole §5 bet.

## 2. Anatomy of a test file

**One file = one behavior surface** — one command, one endpoint, or one pure algorithm. The file name is the
subject (`CreatePutAwayTest`); the test names are its promises; `--testdox` output of the file is its spec.

```
class CreatePutAwayTest extends TestCase
├── use ReceivingScenarioTrait, DomainAssertionsTrait   ← vocabulary, never inline plumbing
├── properties                                 ← the cast of the shared Given, domain-named
├── setUp()                                    ← the shared GIVEN, nothing else
├── #[Test] clause_one()                       ← (Given delta) + When + Then
├── #[Test] clause_two()
├── #[Test] guard_clause()
├── private whenCreatePutAway()                ← the WHEN, `when` + domain verb
└── private givenTheCartIsNotAReceivingCart()  ← Given deltas, `given` + precondition
```

## 3. Placement rules — what goes where

**`setUp` holds the shared Given, and only state.** Every test in the file must want all of it. No dispatch
of the command under test, no assertions, ever. One `// GIVEN …` headline on its first statement says what
the world is and carries the settings the scenarios lean on — `// GIVEN a sweep with a 60-minute grace window
and a 60-day age-out` — because "older than the age-out" is unfalsifiable to a reader who was never told the
age-out; the correspondence principle (§5.1) covers constants too. If only half the tests share a piece of
setup, that piece moves into those tests — or the file wants to be two files.

**Harness calls in the shared Given wear a vocabulary name.** `Carbon::setTestNow(...)`, `Queue::fake()` and
`$this->rebootHandlers([...])` are configuration, not sentences; `$this->theClockIsFixedAt($noon)` and
`$this->queuedJobsAreRecordedNotRun()` say what the world is. The boundary fake stays visible — only the
wording is domain — and a one-off fake inside a body still rides the inline marker
(`$this->given(fn () => Queue::fake())`, below).

**Given deltas open the test body, marked `given`.** A variation on the shared world is stated first, and
the *role marker is non-negotiable while the packaging is free* — two equivalent forms:

```php
// Form 1 — inline marker: one-off delta whose builder name IS the precondition
$this->given(fn () => $this->cart = $this->aPickingCart($this->warehouse));

// Form 2 — named method: the delta states a rule's condition, or is reused
#[Test]
public function put_away_is_rejected_when_the_cart_is_not_a_receiving_cart(): void
{
    $this->givenTheCartIsNotAReceivingCart();               // same words as the test name

    $this->assertThrows(
        fn () => $this->whenCreatePutAway(),                // same When as every other test
        InvalidCartDepartmentException::class,
    );
}

private function givenTheCartIsNotAReceivingCart(): void
{
    $this->cart = $this->aPickingCart($this->warehouse);    // vocabulary does the work
}
```

Choosing between them is not taste: **inline states an instance, a named method states the rule.** When the
mechanics and the precondition are the same words (`aPickingCart` used as "given a picking cart"), inline is
enough. When the test name references a *condition* ("…when the cart is not a receiving cart") of which the
builder is merely one instance — or the delta recurs across tests — name it, so the condition in the name and
in the body match. The inline marker is 3 lines on the base TestCase (`given(Closure $delta): void`); it
carries no string label (nothing to drift) and no value threading (state stays in properties).

With deltas marked, **the body grammar is total: every line in a test body starts with `given`, `when`, or
`assert`.** That is mechanically checkable, and it makes the file read as its own spec: *Given the cart is not a
receiving cart, when create put away, then rejected* — derived from names that cannot drift. (Anything else that must happen in a body — a
boundary fake like `Queue::fake()`, for instance — is arrange, and rides inside the inline marker:
`$this->given(fn () => Queue::fake());`.)

**The When lives in the test body, always** — one line, calling a private method named `when` + the domain
verb (see §4). That method is a dispatch wrapper and nothing else: it returns the result and never asserts —
a Then decided inside the When is a clause the test body no longer shows (the same leak as a `the*` helper
that can fail, §5.8).
Never in `setUp` (the body loses its verb, arrange-failures and contract-failures blur, and the file goes
rigid — no guard or variant test can exist once `setUp` has already acted). **One When per test.** Two
dispatches means one of them is really a Given (move it into a builder) — unless the sequence *is* the
contract ("dispatching twice creates one fulfillment"), in which case the pair is the When and stays inline.

**The Then asserts one contract clause through the read-side.** A clause is a sentence, not an assertion —
two assert lines that jointly state "the received stock is in the put-away location" belong together; a
second *sentence* belongs in a second test.

**Exception outcomes are Thens, asserted as Thens:** `assertThrows(fn () => $this->when...(), X::class)` —
Laravel-native, already on the base TestCase via `InteractsWithExceptionHandling`. Note `expectException` is
*not* a fourth role — it's a Then that PHPUnit forces to be declared before the When ("arm the trap, then
run"), which is why it breaks the grammar and why nothing after the When can execute under it.
`assertThrows` fixes both: the marker is `assert`, the When stays visible inside, and execution continues
after the throw — so a guard's second clause ("…and nothing was written") lives in the same test, which
`expectException` makes impossible. Use `expectException` only when `assertThrows` genuinely can't express
the case, and then nothing may follow the When.

## 4. Naming

**A test name is a proposition — something that is true or false.**
`put_away_moves_the_received_stock_into_the_put_away_location` is falsifiable;
`test_create_put_away_works` is not. Banned words: *works, correctly, properly, successfully, should* —
they carry no proposition. Present tense, subject–verb–outcome, `#[Test]` + snake_case.

- **Guards name the rule, not the mechanics:** `..._is_rejected_when_the_cart_is_not_a_receiving_cart`
  (the exception class is asserted in the body, not encoded in the name).
- **Builders:** indefinite article = creates (`aWarehouse()`, `anActiveProduct()`); definite article =
  retrieves what the seed guarantees (`theAdminUser()`); verb phrase = a Given-action
  (`receiveIntoCart(...)`). A builder with two or more parameters carries a one-line docblock stating what
  it makes — domain noun first, true of the body (`/** An order already imported from the shop, with the
  given number and created-at. */`): the call site shows arguments, not meaning, and a summary that promises
  what the builder doesn't do is worse than none.
- **Helper names open with the domain subject, never a vendor or proper noun** —
  `theCandidateLookupsAreRejected()`, not `shopifyRejectsTheCandidateLookups()`. Subject-first names read as
  sentences about the domain; vendor-first ones read as namespaces. Docblocks follow the same rule.
- **Thresholds and offsets are named readers derived from the consts** — `pastTheAgeOut()`,
  `justInsideTheGraceWindow()` — never arithmetic at the call site (`daysBefore(70)`). The name says which
  side of the rule the scenario sits on; the number lives once, beside the const it derives from.
- **The When helper: `when` + the imperative domain verb** (`whenCreatePutAway()`). This completes the
  morphological grammar — Given is marked by articles, Then by `assert`, and without the prefix the When is
  the one unmarked verb, indistinguishable at the call site from a Given-action (`receiveIntoCart` arranges,
  `createPutAway` acts — same grammar). Derive it mechanically (`when` + verb phrase), don't hand-craft
  English (`whenPutAwayIsCreated`) — a rule that needs composing gets applied inconsistently. Bonus:
  `grep 'function when'` lists every act in the suite.
- **Per-test Given deltas: marked `given`, hybrid packaging** — inline `$this->given(fn () => ...)` for
  one-off instances, `given<Precondition>()` when the delta states a rule's condition or recurs (§3).
  Prefixes mark the *body*; position marks `setUp` — vocabulary builders themselves stay unprefixed
  (article grammar) and do the actual work inside either form.
- **Assertions:** `assert` + a domain proposition (`assertItemDestinedFor(...)`), failing with a domain
  sentence, never a bare `assertEquals` mismatch dump. Shape the name as the sentence's predicate and pass
  the subject last, PHPUnit's own expected-then-actual order: end on a copula
  (`assertHospitalIssueIs('withdrawn', $fulfillment)`) or a preposition (`assertNoAllocationsFor($product)`),
  and the call reads aloud as a sentence about its subject. The empty outcome gets its own word
  (`assertNoCandidatesDispatched()`, not `assertCount(0, …)`) and a count lives in the name
  (`assertRepulledOnceFor()`, `assertRepulledTwiceFor()`) — a zero or an open comparator at the call site is
  the §5.8 leak in its most common form.
- **Traits carry a `Trait` suffix, file name matching** — `ReceivingScenarioTrait`, `PutAwayAssertionsTrait`,
  `DomainAssertionsTrait` in `tests/Behavior/`. Team convention; rename any un-suffixed trait you touch.
- **Actors get distinguishable names.** `$coffee`/`$tea`, `$locationA`/`$locationB` — never `$product1`/`$product2`.
  Type-identical pairs are where silent transposition hides; distinct names make a swapped assertion
  visibly wrong. When a Then must say *which* — two stores, two cursors — the actors are properties set in
  the shared Given (`$this->store`, `$this->otherStore`), not locals assigned at the top of the test: the
  body names them and the Given owns them. And helpers take the domain number, never the transport id —
  `assertRepulledFor(936290)`, not `assertRepulledFor($gid)`; build the gid inside the helper. A body speaks
  in order numbers a reader can place, not in ids nobody can.

## 5. Readability rules

1. **The correspondence principle.** Every value in a Then traces to a visible line in the Given or When:
   `receiveIntoCart(..., qty: 10)` up top is *why* `assertPutAwayLocationHolds(..., qty: 10)` below.
   A number appearing only in the Then is a magic number; a factory default silently satisfying an
   assertion is a time bomb — pin every field an assertion depends on.
2. **Named arguments for literals.** `qty: 10`, `in: $warehouse`, `count: 3` — call sites label themselves.
3. **No logic in test bodies.** No `if` (a branching test tests two things or none), no `foreach` over
   assertions (a loop hides which iteration failed — unroll it into visible lines). Matrices go in a string-keyed
   `#[DataProvider]`; iteration may live *inside* a domain assertion, which reports the failing element.
4. **Budgets as smoke alarms.** Test body ≤ ~12 lines, `setUp` ≤ ~10 vocabulary lines. Exceeding them
   doesn't mean "split mechanically" — it means a vocabulary word is missing or the file covers two surfaces.
5. **Comments only for what code can't say:** domain gaps (`// DOMAIN GAP: no command sets a cart's
   department`), non-obvious constraints. A *why* note about a scenario sits directly above its `#[Test]`
   line — never inside the body, where it reads as a step, and never between the attribute and `function`,
   where it is easy to miss. Never restate the method name in a docblock.
6. **File reads as the spec, in spec order.** Happy-path clauses first, then guards and edge cases. Before
   committing, run `--testdox` on the file: if a sentence reads wrong, the name is wrong.
7. **Audit the code against the prose scenarios** (when scenarios exist — e.g. the GWT sentences of a
   §8 skeleton). Line them up word by word: every prose clause must own a code word (a missing
   assertion hides here), assertions mirror prose word order (`assertPutAwayLocationHolds`, not
   `assertStockInPutAwayLocation`), builder parameters speak prose not structure (`label: 'a'`, never
   `['location' => 'a']`), actors are named in the data so failures speak the scenario
   (`anActiveProduct(named: 'coffee')` → "Expected 10 of coffee…", not a faker SKU) — and one dialect per
   noun: if the prose says "shelf" and the code says "location", one of them is wrong; pick the ubiquitous
   term and use it on both sides.
8. **Audit the name against the body — the promise ledger.** §5.7 audits prose → code; this audits
   name → code, and it is where a *landed* suite leaks: a name that reads correct makes a weak body
   invisible in review, and `--testdox` then publishes the promise as if it were proved. Read the name
   as a sentence and make every word earn an assertion — each noun exists in the fixture, each
   qualifier is asserted, each quantifier is exercised, each clause has a Then. The eight modes below
   were all found by reading a landed suite's names back against their bodies, clause by clause.

   | The name promises… | …the body proves | Cure |
   |---|---|---|
   | a state — `..._stays_pending` | `assertNotSame(Closed::STATE, …)`, true of every wrong state | assert the named state positively through the state VO |
   | a relationship — "a line of *another* RMA" | a random unknown id | build the noun the name names, or rename to what the fixture built ("an unknown line") |
   | one proposition | two — the deciding half is a `fail()` inside a `the*` read helper | assertions live in the body; a helper that can fail is named `assert*` and its clause is visible in the test |
   | two clauses — "is already closed **and so** cannot be received" | the second clause only | assert both, or split into two tests |
   | a value — "reports the customer and the order date" | `assertArrayHasKey(...)` — a renamed resolver returning null passes | assert the value against the Given's known input |
   | a scope — "a put-away **for the returned units**" | that *a* put-away exists | assert the qualifier (quantity, product, destination) or drop it from the name |
   | a quantifier — "**every** line pending" | one line in the fixture | the fixture carries ≥2 and the assertion covers the set, or the name drops to the singular |
   | an exact outcome | `assertGreaterThan(0, …)` where the Given fixed the number | assert the number — open comparators are smoke tests, not contracts |

   **The cheap greps** (run over a file before committing, and over a suite you are reviewing):
   `assertNot(Same|Equals)\(.*STATE` · a test whose only assertion is
   `assertArrayHasKey|assertNotEmpty|assertGreaterThan` · `fail\(` in a method not named `assert*` ·
   a name containing `every|all|each|both` in a file whose `setUp` builds one actor.

   **The read-back.** `--testdox` gives you the names; the bodies you must read. Read each body's clauses
   back against its name: the mismatch is obvious in prose and near-invisible in a diff.

9. **Sibling tests with identical bodies are a red flag.** A matrix of one proposition is a data provider
   (§5.3); five *different* propositions sharing one body means the differentiator lives only in the names.
   Surface it: a named `given*` delta taking the varying value (`givenTheShopReturned('shirt')`,
   `givenThePullWouldImport('shirt')`), with `setUp` naming the empty starting state — each body then says
   what makes it different.

## 6. Where plain AAA (no ceremony) is correct

Pure unit tests — value objects, algorithms — skip the whole apparatus: no `setUp`,
no vocabulary, arrange inline, because input → output already *is* the contract in one breath:

```php
#[Test]
public function greatest_of_equal_values_is_that_value(): void
{
    $this->assertSame(5, Qty::greatest(new Qty(5), new Qty(5))->getValue());
}
```

Forcing GWT ceremony onto these is noise in the other direction. The apparatus earns its keep exactly where
the world is wide — container-backed Feature tests of cross-domain commands.

## 7. The copyable skeleton

```php
class <Command>Test extends TestCase
{
    use <Domain>ScenarioTrait;
    use DomainAssertionsTrait;

    // the cast — domain nouns, distinguishable names
    private WarehouseInterface $warehouse;

    protected function setUp(): void
    {
        parent::setUp();
        // GIVEN, shared by every test in this file
        $this->warehouse = $this->aWarehouse();
        // ... vocabulary sentences only
    }

    #[Test]
    public function <subject_verb_outcome — a falsifiable proposition>(): void
    {
        // optional Given delta — either form:
        // $this->given(fn () => ...);  or  $this->given<Precondition>();

        $result = $this->when<DomainVerb>();          // WHEN — one line, one act

        $this-><assertDomainProposition>(...);    // THEN — one clause, read-side
    }

    /** WHEN — the contract's trigger, stated once. Dispatch only — the body asserts. */
    private function when<DomainVerb>(): <DomainResult>
    {
        return $this->bus()->handle(new <Command>(...))->getValue();
    }
}
```

---

## 8. Scenario-first, without extra files — the skeleton form

Writing the scenarios in English *before* the test code is the discipline; a standing `.scenarios.md` per
test file is not — it would be a parallel English artifact that can drift, the same disease as labeled DSLs
(standalone `.scenarios.md` files are demo material, not a required deliverable). The exercise's native
home is **the test file itself, committed first as a skeleton**:

```php
#[Test]
public function split_order_closes_when_its_last_fulfillment_completes(): void
{
    $this->markTestIncomplete(
        'Given the order is split across shipment and pickup,'
        . ' and the shipment has already completed;'
        . ' when the pickup completes; then the order is closed.'
    );
}
```

Names are the scenario titles (already propositions, §4); each body carries its GWT sentence until
implemented. The skeleton is runnable (`--testdox` renders the scenario list before any code exists),
reviewable (the spec is commit 1 of the PR), and **self-deleting** — implementing a test replaces the
sentence with the three role-marked lines that say the same thing, so drift is impossible. Batching *titles*
up front is writing the spec, not horizontal slicing — implementation still proceeds one vertical slice at a
time (red → green per scenario). Scenarios that pre-exist in a PRD or plan flow into the skeleton whole: a
Given/When/Then acceptance sentence becomes the `markTestIncomplete` sentence, and the name is its *then*
clause with its subject, in the §4 shape — the same proposition in two lengths, never two propositions. They
don't get duplicated into a second document next to the test.

## 9. Who shares what — the vocabulary graduation ladder

Scenario and assertion traits are **per domain, shared by every test file in that domain** — `tests/Behavior/`
is flat, and `ReceivingScenarioTrait` serves `CreatePutAwayTest`, `CancelPutAwayTest`, and every future receiving
test (killing exactly the copy-paste the suite has today). A test file whose world spans domains composes
several scenario traits. Only the `given*`/`when*` wrappers stay file-private: they name preconditions and
acts relative to *this file's* setUp and contract, and they're one-liners over vocabulary — redeclaring them
is cheaper than coupling files.

```
file-private given*/when* wrappers            — never graduate (file-contract-specific)
  → {Domain}ScenarioTrait / {Domain}AssertionsTrait     — a word moves in when a second FILE needs it
    → Behavior\DomainAssertionsTrait               — an assertion moves up when a second DOMAIN needs it
```

Nothing is created speculatively at any tier — every promotion is triggered by the second consumer arriving.

---

*Enforcement: the review question — "read the test name and body aloud; did you hear the
behavior contract?" — plus the §6 metrics. Everything above is a default, not a straitjacket; deviate when
the contract itself demands it, and say why in a comment.*
