# The spec-readability pass — second pass over a landed suite

A landed, green suite renders a *faithful* spec that nobody can read: titles fine, every bullet a
100–300-char noun phrase. This pass fixes that **in the tests** — audit → apply → verify → iterate — and
hands the tool a change-request list for what only the extractor can fix. It is not an audit report; the
deliverable is a regenerated spec a PM reads without the tests, plus the suite that produced it.

Distilled from one landed connector suite (≈40 Feature + a handful of Unit tests, 18 defect classes, two
iterations); the numbers quoted below are that suite's, for scale.

**The pass is optional — offer it, never start it unasked.** After the first green `spec:extract` of a new
suite, or when a developer says the spec "needs a lot of improvement", run §1's measure block (two minutes,
read-only) and **ask** with `AskUserQuestion`, numbers in hand: "long bullets N, phrase dumps N, blank Thens N,
setting values stated: no. Run the readability pass now (≈K test files edited, suite must stay green), or
leave it?" Proceed only on a yes; "later" goes in the ticket's follow-ups. Skip the question when the metrics
already pass §7.

## 0. Baseline — before touching anything

```bash
T=$CLAUDE_JOB_DIR/tmp   # or any scratch dir; never /tmp on a shared box
S=~/.claude/skills/skunexus-spec-extract/scripts/spec-extract.phar
vendor/bin/pest tests/Feature/<Suite>Test.php tests/Unit/<Area> > $T/pest-0.txt 2>&1   # note "N passed (M assertions)"
php $S [--config=.ai/<TICKET>/spec-dialect.php] tests/Feature tests/Unit/<Area> --output=.ai/<TICKET>/spec-from-tests.md
cp .ai/<TICKET>/spec-from-tests.md $T/spec-before.md
```

Three facts the rest of the pass keys on: the **test count and assertion count** (the contract gate —
they must not move unless a fix deliberately adds a Then, and then you say so), the **scenario count per
section** (must not move), and the **before copy** (line numbers shift the moment anyone regenerates;
key every finding on the scenario *title*, not the line).

## 1. Measure — the metrics that say "machine transcript"

Run over the rendered spec. Zero `⚠` is necessary, nowhere near sufficient — the reference suite had 0 `⚠` and 86
unreadable bullets.

```bash
S=.ai/<TICKET>/spec-from-tests.md
grep -c '⚠' $S                                              # extractor gave up (RAW / NOTHING READ)
grep '^- ' $S | awk 'length>120' | wc -l                     # long bullets — the headline number
grep -c 'of number\|of days\|of minutes' $S                  # phrase dump: every arg with its param name
grep -cE 'exactly $| is $| at $'                             # blank Thens (empty array rendered as nothing)
grep -c 'ed at .* is .*ed at' $S; grep -ci 'shopifyed' $S    # a proper-noun helper prefix conjugated as a verb
grep -oE '\([^)]{60,}\)' $S | sort | uniq -c | sort -rn | head  # the same gloss repeated per sibling Given
grep -E '^\*\*(Then|And)\*\* an? .* of number' $S | wc -l     # a Then whose subject is its own Given, verbatim
grep -o '\b<domainword>\b' $S | wc -l                        # lowercase proper noun (initialism missing)
grep -c '^### [a-z]' $S                                      # lowercase headings
grep -c '^> ' $S                                             # rendered why-notes (should be > 0 if the tests have them)
```

Then two checks no grep does: **are the setting values anywhere?** ("older than the age-out" is
unfalsifiable if the age-out is never stated) and **can a reader tell sibling scenarios apart from their
bullets alone?** — the CLI/multi-actor scenarios and the pure-unit matrix are where they can't.

## 2. Three roles — taken separately, then reconciled

Three readings, each in a distinct role, each written down **before** reconciling — a single blended read
misses what each role is for (the cold reader never opens the tests; the fix planner never trusts a
predicted render). They work well as three agents given the same brief, or as three deliberate passes by
one person. Brief for each: the domain in one paragraph, the file paths, and the doctrine pointers
(`pest-style-guide.md` §5.8 and §10, `skunexus-spec-extract/SKILL.md`, the repo's `CLAUDE.md`).

| Role | Reads | Must NOT | Produces |
|---|---|---|---|
| **Cold reader** — reads as a PM/PO, an FE dev, and the author in six months | the spec only | open the tests (stands-alone check) | sentences that don't parse (classified: harness plumbing / helper-name leakage / param dump / grammar), repetition metrics, tautological Thens, inconsistencies, missing information (values, undefined terms), structure, and **what already reads well** (the pattern to copy) |
| **Fidelity reviewer** — §5.8 promise ledger against source | spec + every test + vocabulary trait | edit | per scenario: dropped steps (count body statements vs bullets), title promises the Thens don't show (*every*, *exactly*, *the same way*, *again*, two-clause titles), Thens that hide the check (title restated; assertion inside a helper), harness Givens, existence-for-value; **verdict per defect: test-shape / vocabulary-name / extractor** |
| **Fix planner** — cheapest rung per defect, **measured** | everything + the phar in a scratch copy of the suite | predict a render — it runs the phar on a probe and quotes the output | per file, per method: exact new name or `#[TestDox]` string, ladder rung and why the cheaper rung fails, the rendered line after; extractor limitations separately, each with a repro |

Synthesis: rank by damage (occurrences × how much a reader loses), attach root cause and fix pointer to
each row, list **where the roles disagree and make the call** (see §5), and split out **what only
the tool can fix** (§8). Findings the three roles tend to miss, to add from experience: an assertion
inside a `when*` helper; a `times:`/count argument with no slot; a `When` that reads identically across
scenarios whose whole variable is its argument.

## 3. Apply — the ladder, and the order

Rungs (style guide §10, unchanged): **(1)** rename/reshape the helper so derived prose reads → **(2)**
`#[TestDox('{slot} …')]` at the definition → **(3)** a dialect word, evidence attached. Never contort a
test for the extractor; every rung-1 fix should make the *test* read better too — if it doesn't, you're
on the wrong rung.

Apply order — each step's names are referenced by the next:

1. `tests/Behavior/{Domain}ScenarioTrait.php` — builders, harness helpers, time readers, splits
2. `tests/Behavior/{Domain}AssertionsTrait.php` — slots, wrappers for the empty case, renamed slogans
3. `tests/Feature/*Test.php` — call sites, ids → properties, locals → `given()`, notes above `test()`, titles
4. `tests/Unit/**` and any fakes — `when*` per file, `given*` for the differentiators, sibling renames
5. `.ai/<TICKET>/spec-dialect.php` overlay → regenerate

Per file: edit → re-read the whole file (not the diff) → suite → grep every replaced name → render to
scratch → compare with the fix plan's measured preview and explain every other difference. Exact-count
replacements (assert the match count before writing) are what make a mechanical edit safe to gate.

## 4. Verify — a fresh-eyes verifier, adversarial

A verifier who did not write the fixes — a fresh agent, or you working from the rendered spec and the diff
rather than from memory of what you meant to change — regenerates the spec and checks, in this order:

1. **Defect table** — every row RESOLVED / PARTIAL / NOT with one quoted spec line; re-measure §1.
2. **Contract drift** — `git diff -- tests/` read for weakened Thens; assertion count vs baseline;
   collapsed fixture values (two offsets folded onto one reader — were either asserted?).
3. **Every `#[TestDox]` sentence is TRUE of its helper's body.** The reference run's first apply shipped
   *"a repull by IDs answered with the orders staged in Shopify"* on a fake that never reads the staged
   store. A wrong spec is worse than an ugly one; this check is the pass's most important line.
4. **Duplicated literals equal their source** — settings written into a Background TestDox vs the consts
   (and vs `config/` defaults).
5. **Orphans a green suite can't see** — return types no call site reads after a number-not-id change;
   sibling names not swept (`$gidsShopifyNoLongerReturns` after `theOrderVanishesFromShopify`); jargon
   left in the domain trait (`presenceNode`) when the boundary class is the fake.
6. **Style against `CLAUDE.md` and the style guide** — article grammar, `assert*` states the clause, one
   When per test, every arrange line marked, no unused imports, headings capitalised.
7. **Spot-read as a PM** — Background, first four scenarios, the multi-actor section, the unit sections.

Then a **cleanup pass** on its findings (same rules as §3), and the gate.

> **If you choose to split the work across agents** — a hint, not a requirement: the three §2 roles are
> independent reads and run well side by side; §3's apply splits cleanly by **disjoint file sets** (one
> agent on the Feature chain — scenario trait, assertions trait, Feature test — another on the Unit files and
> fakes); §4 wants a verifier who did not write the fixes, and a short cleanup role for its findings. What
> does not split: two writers on one file (in the reference run two helpers edited the same trait within
> minutes and nothing was lost only because both asserted match counts and ran the suite after each), and the
> apply order in §3 — the traits' new names are what the call sites reference.

## 5. Disagreements you will have — and the calls the reference run made

| Question | Call | Why |
|---|---|---|
| Pure-unit files in the human spec: drop or shape? | **Shape** — a `when*` per file, arrangement in `given*` file functions | their titles were the clearest rule statement in the file and QA wants them; §6's "plain AAA" exemption stops earning its keep once the spec is a deliverable |
| Two fixture offsets both inside a window (30 min, 10 min) → one named reader? | **Collapse** | neither value asserted; one reader named for meaning beats two literals — but run the suite, don't take "unchanged" on faith |
| Fixture with 6 orders for "gapless history"? | **Cut to the minimum the proposition needs** (two adjacent numbers) | a literal count with no source is banned anyway; the suite's natural shape (3–4 Givens) shows the outliers |
| Dataset (`->with([...])`) to unify sibling scenarios? | **Only for a true data matrix** (same When, one varying value, Then differs by a value) | it renders a *Where* with case names, not Givens; siblings that differ in *which Then fires* stay separate propositions |
| Five scenarios with identical bodies, titles carry the difference — accept? | **No** (iteration 2) | "the Given is missing the differentiator" is exactly what a reader objects to; move the arrangement into `given*` functions so each body shows which lookup returned what |
| `{times}` slot for the count? | **No — a wrapper** (`assertRepulledTwiceFor`) + "once" in the default sentence | a defaulted slot renders as nothing, so the slot form lies on every default call |

## 6. The defect catalogue — symptom → cause → fix

Generalised from the 18 rows. **T** test shape · **V** vocabulary/TestDox · **X** extractor.

| Rendered symptom | Cause | Fix |
|---|---|---|
| `an imported shopify order of number 936285, shopify created at settled long before the sweep` on every Given | V — parameterised builder with no TestDox: derived prose dumps every arg with its param name and the const's name spelled out | `#[TestDox('order #{number} already imported, created {shopifyCreatedAt}')]` on every builder with ≥2 params. Also deletes the per-call docblock gloss (TestDox outranks it) |
| **Then** whose subject is the whole Given phrase (`… of number 936290, shopify created at … is repulled`) | X+T — a `{slot}` fed a **top-level local** inlines the local's whole assignment | assertion takes the **domain number** (`assertRepulledFor(936290)`), the locals become `given(fn () => …)`; ids that must be passed become `$this->` properties (render by name) |
| `shopify created is shopifyed at …` / `rejects the lookups are shopifyed` | V+X — helper name starts with a proper noun; the extractor reads it as subject and passivises | rename so the clause starts with the domain subject (`theOrderVanishesFromShopify`, `theCandidateLookupsAreRejected`); file the initialism upstream |
| `the carbon set test now “…”` · `` `Queue` is faked `` · `reboot handlers with X: fake Y` in the Background | T — raw harness calls in `beforeEach` | named scenario helpers with TestDox (`theClockIsFixedAt`, `queuedRepullsAreRecordedNotRun`, `aRepullByIdsHandingBackEveryRequestedId`). Boundary fakes stay **visible** — only the wording changes |
| Background explains *why* settings are pinned, states no values | V — docblock instead of a sentence with the numbers | `#[TestDox('a sweep with a 60-minute grace window, a 60-day age-out and 2 failures before giving up')]` + a comment "values restated; keep in step with the consts" (a slot cannot read a const) |
| `created at days before the sweep of days 70` | X — TestDox ignored on a nested value helper | no-arg readers derived from the consts: `pastTheAgeOut()`, `justInsideTheAgeOut()`, `insideTheGraceWindow()` |
| `the sweep cursor stands at #936292` **and** `… at #112235` in one scenario, no actor named | V+T — assertion has no slot for *which* actor; ids are locals | `{store}` slot backed by `$this->store` / `$this->otherStore`; a §5.8 hole, not only prose |
| identical **When** across scenarios whose whole variable is the When's argument | V — slot-less TestDox on the `when*` | `#[TestDox('the sweep command runs for {store}')]`; introduce the odd value (unknown id) as a Given via a trait reader assigned bare |
| a Then missing that the sibling scenarios have (exit code, "no repull") | T — the assertion lives **inside** the `when*` helper, or was never written | `when*` returns the value; the body asserts it; add the sibling's Then |
| `**Then** the run repulls exactly ` (blank) | X — empty array renders as nothing | wrapper: `assertNoCandidatesDispatched()` → "the run repulls nothing"; `->toBeEmpty()` → "is empty"; file upstream |
| the only Then restates the title (`eligibility is decided by the pull's own filter…`) | V — a slogan TestDox on the assertion | say what is checked: `'the eligibility lookup carries {pullFilterTerm} and narrows by no created_at or updated_at window'` |
| "a single retry" / "again" render like a plain repull | V — `times:` has no slot; a defaulted slot renders nothing | "once" in the default sentence; `assert…TwiceFor()` wrapper → "a second time" |
| pure-unit scenarios with no **When**, the act rendered as a Given and re-inlined in the Then | T — plain AAA rendered as GWT | a `when*` per file; arrangement in `given*` file functions with slots; result on `$this->` |
| five scenarios, identical bodies, titles carry the difference | T — arrangement passed as `when*` arguments behind a slot-less TestDox | `givenShopifyReturned(name)`, `givenThePullWouldImport(name)`; Background `givenNeitherLookupHasReturnedAnything()` |
| same parenthetical gloss on every sibling Given | V — docblock rendered per call | falls out of the builder TestDox; move real information into the sentence |
| lowercase headings, mixed with sentence-cased ones | T — a description with any uppercase renders verbatim | capitalise those `test('…')` strings |
| four notations for one number in one scenario | V+X | one **rule**: number `#936290` unquoted (int slot, `#` in the sentence), name `“#936290”` quoted, count bare; 1-vs-N array label drift is upstream |
| the suite's best `//` *why* comments absent from the spec | X by design — in-body comments are dropped | move the note **above** the `test()` call; it renders as a blockquote under the heading |
| `number(s)`, `summaries … is` | X — printf plurals, no copula agreement | upstream; cosmetic |
| `Given the test` | X — `given(fn () => $this->x = CONST)` renders the closure's receiver | assign a trait reader bare: `$this->unknownStore = $this->anIntegrationIdNoStoreCarries();` |
| a 6-order fixture rendering six near-identical lines | T — a count with no source | the minimum the proposition needs; a range builder (`importedShopifyOrdersFrom(936291, to: 936294, …)`) where consecutive numbers matter |

## 7. The gate — what "done" means

- Suite green with the **same test count**; assertion count equal to baseline **or** each delta named
  (reference run: 102 → 103, one exit-code Then added to the scenario its siblings had).
- Every replaced name greps to **zero** across `tests/`; every new name's count matches intent.
- No duplicated method in any edited file (`grep -oE 'function \w+' f | sort | uniq -d`).
- Regenerated spec: same scenario count per section, `⚠` = 0, §1 metrics — long bullets to single digits
  (one-off informative glosses may remain), phrase dumps 0, blank Thens 0, proper-noun verbs 0,
  lowercase headings 0, setting values stated, why-notes rendered.
- Each remaining long bullet named as *acceptable gloss* or *debt*.
- `CLAUDE.md`: a green suite is not proof after a mechanical edit — the greps above are the proof.

## 8. Deliverables

1. `.ai/<TICKET>/spec-from-tests.md` regenerated — never hand-edited.
2. `.ai/<TICKET>/spec-dialect.php` if an initialism/dialect overlay was needed, and the regen command that
   uses it recorded in `decisions.md`.
3. A `decisions.md` entry: what the vocabulary now does by rule, what was deliberately left (the
   title-vs-body promises — "past the ceiling", "like a pocket" — are **contract** decisions for the
   developer, not prose fixes; list them, don't silently apply them).
4. `.ai/<TICKET>/spec-extract-requests.md` — the change requests to the tool, one per limitation:
   one table, columns `# · symptom · repro (probe shape) · renders · expected · workaround used`, header
   naming the phar version/date and the upstream repo (`SkuNexus-Devs/dev-ian-spec-extract`); a closing
   "nice-to-haves" line for slot forms the pass wished for. **Fix the tests now; don't wait for the tool** —
   every request must carry the rung-1/2 workaround already applied.
5. The audit + outcome (`spec-audit.md`) so the next reader sees before/after numbers.

## 9. Iterate — the review round

The developer reads the regenerated spec and points at a scenario. Two patterns recur:

- **"Does this really need N orders?"** — fixture-size question. Check the code for a real minimum
  (`hasRangeToScan` needed two numbers, not six); count Givens per test across the file to see the
  suite's natural shape; cut to the minimum, add a range builder only where consecutive numbers matter.
- **"The Given is missing the differentiator."** — the arrangement is hidden behind a slot-less `when*`
  or an accepted "titles carry it" call. Move it to `given*` file functions with slots; **probe the render
  in a scratch dir before editing** (`php $S $SCRATCH --output=…`) — a probe costs two minutes and
  replaces a paragraph of "it should render as".

## NEVER

- **NEVER hand-edit the rendered spec** — it is regenerated; fixes go in the tests or upstream.
- **NEVER let a `#[TestDox]` say what the helper does not do.** Verify every sentence against the body in
  the verify step; a wrong spec is worse than an ugly one.
- **NEVER feed a `{slot}` a top-level local** — pass the domain number, a literal, or a `$this->` property.
- **NEVER assert inside a `when*` helper** — return the value, assert in the body, or the Then is invisible.
- **NEVER have two writers on one file at once** — if work is split, split it by disjoint file sets, and
  re-run the gate if anyone else touched a file you were editing.
- **NEVER trust a predicted render** — the fix plan runs the phar on a probe and quotes the output.
- **NEVER apply a title-vs-body contract change silently** ("past the ceiling" with `CEILING` unasserted)
  — list it for the developer.
- **NEVER key findings on spec line numbers** — regeneration shifts them; use scenario titles.
- **NEVER treat 0 `⚠` as "readable"** — measure §1.

## Diagnostics

| You see in the spec | It means | Do |
|---|---|---|
| a bullet with `of <param> <value>, <param> at <value>` | parameterised builder without TestDox | §6 row 1 |
| a Then repeating a whole Given before its verb | slot fed a local | number-not-id; `given()` the builder |
| `is <noun>ed at` / `are <noun>ed` | proper-noun helper prefix | rename subject-first; initialism upstream |
| `Given the test` | `given(fn () => $this->x = …)` | bare trait-reader assignment |
| a Then ending in ` exactly ` / ` is ` | empty array | wrapper assertion (`…Nothing`, `toBeEmpty`) |
| two identical Whens in sibling scenarios | slot-less `when*` TestDox | `{actor}` slot, properties |
| the same `(gloss …)` on consecutive Givens | docblock rendered per call | builder TestDox |
| Background line that is a class name or method name | raw harness call | named helper + TestDox |
| sibling scenarios where only the title differs | arrangement hidden in the When's args | `given*` file functions |
| tests fail after `test()->list[] = $x` in a file-level `given*` | Pest `HigherOrderTapProxy` returns arrays by value | init in `beforeEach` via a named `given*`; write whole arrays back |
| line numbers in a role's report don't match the file | someone regenerated mid-pass | fine — key on titles |
