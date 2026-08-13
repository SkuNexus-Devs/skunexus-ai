---
name: skunexus-spec-extract
description: >-
  Use when you need the Given/When/Then behavior spec of a SkuNexus test suite — reading back what a
  test file actually asserts, producing .ai/<TICKET>/spec-from-tests.md for a ticket, comparing tests
  against a PRD, or reviewing a PR through its tests. Deterministic AST-based extractor (no LLM):
  renders each test as Given/When/Then prose from the tests/Behavior vocabulary. Do NOT use for:
  writing tests (skunexus-behavior-testing), driving new behavior test-first (skunexus-tdd-testing),
  running tests (composer test), planning or breaking down the work (skunexus-backend-plan),
  implementing production code (skunexus-backend-implement), writing the PR description that quotes
  the spec (skunexus-backend-pr), or QA testing steps (separate skill). Triggered by: gwt,
  given/when/then, behavior spec, spec from tests, spec:extract, spec-extract, what do these tests
  assert, spec vs PRD.
user-invocable: true
---

# spec-extract

Turns behavior tests into a Given/When/Then spec in Markdown. Deterministic — structure comes from `nikic/php-parser`, prose from the camelCase vocabulary, no LLM anywhere. **Never hand-edit the output**; fix the test names or re-run.

One self-contained file, `scripts/spec-extract.phar`. Needs PHP 8.2+ and nothing else — no `vendor/`, no `.env`, no booted app. Run it from anywhere inside the target repo.

```bash
# $S = scripts/spec-extract.phar inside this skill's folder, wherever it is installed
# (project .claude/skills/skunexus-spec-extract/ or global ~/.claude/skills/skunexus-spec-extract/)
S=~/.claude/skills/skunexus-spec-extract/scripts/spec-extract.phar

$S tests/Feature/OrderRMA --output=.ai/LO-58/spec-from-tests.md   # a directory, walked for *Test.php
$S tests/Feature/OrderRMA/CloseRmaTest.php            # one file, spec to stdout
$S 'tests/Unit/Domain/*/*Test.php' tests/Feature      # globs and several paths at once
$S --help
```

**The ticket artifact.** `.ai/<TICKET>/spec-from-tests.md` is a standing workflow artifact — regenerated at `skunexus-backend-implement` wrap-up and read by `skunexus-backend-pr`, `skunexus-backend-summary` and `skunexus-fe-handoff`.
It is a render, never hand-edited: prose that reads wrong is fixed in the test names and helpers, then the file is re-run.

## Arguments

| Argument | Effect |
|---|---|
| `<paths...>` | Files, directories (walked recursively for `*Test.php`), or globs. Globs are expanded by the tool, so quote them to keep the shell out of it — they are PHP `glob()`, one level per `*`, no `**`; pass a directory when you want recursion. Each path's matches are sorted; the order of the paths is kept. A path that matches nothing warns and is skipped |
| `--output=FILE` | Write the spec to `FILE` instead of stdout |
| `--dialect=NAME` | Vocabulary bundle to read by: `skunexus` (default) or `gwt` (the plain base, no SkuNexus initialisms) |
| `--config=FILE` | Overlay file merged over the dialect. Repeatable, applied left to right, last wins |
| `--selftest` | Run the renderer's internal checks and exit. Prints `selftest ok` |
| `--help`, `-h` | Usage summary |

Exit 0 on success; exit 1 for no paths given, nothing matched, an unknown dialect or option, or a missing overlay. **The spec goes to stdout, every message to stderr** — so `$S tests | less` and `$S tests > spec-from-tests.md` stay clean, and `2>/dev/null` silences the noise.

Which project a test belongs to is decided per file: the nearest ancestor directory holding `tests/Behavior/` or `artisan`. That is where `tests/Behavior/<Trait>.php` vocabulary is read from and what rendered paths are relative to — so one run can span several repos, and the current directory does not have to be the project root.

## Both syntaxes — `--mode`

The extractor reads **both** authoring syntaxes, so either is a first-class spec source:

- `--mode=pest` (**the default**) reads classless files: `test()` descriptions → scenario headings, `beforeEach` → Background, a marked `given` → Given steps, file-level `when*` functions → passive command prose, `expect()` families → Thens.
- `--mode=phpunit` reads `#[Test]` class methods.

A mixed repo is normal — Pest runs PHPUnit classes natively, and a converted suite extracts at parity with its PHPUnit original. Two Pest-only rules decide whether the prose reads: mark a Given **once** (`given(fn () => $this->…)` or a bare `givenX();`, never both nested), and pass a **directory** rather than a shell glob. Details in `skunexus-behavior-testing`'s style guide §3 and §10.5.

## What it reads

| Input | Becomes |
|---|---|
| `setUp()` statements | `**Background**` line; a `// GIVEN …` comment there becomes its headline |
| `#[Test]` methods | one `###` scenario per method, name read as English |
| `$this->givenX()` / `$this->whenY()` / `assert*` | `- **Given**` / `- **When**` / `- **Then**` steps; a step repeating the previous label reads `- **And**` |
| `whenX()` bodies dispatching `new SomethingCommand(...)` | passive prose (`the RMA is closed with reason X`) |
| trait methods from `tests/Behavior/` | argument labels and the `— by …` second-level detail |
| `#[TestDox('…')]` on a `#[Test]` method | that text, verbatim, as the scenario heading instead of the method name |
| `#[TestDox('…{param}…')]` on a given / when / assert helper | that sentence, verbatim, as the step — see below |
| `#[DataProvider]` string keys | `- **Where** the case is each of: …` |
| things a Given leaves behind | `(*the shipment*)`, referred to by that name in later steps |
| non-doc `//` comments on a method | note under the scenario heading |

Three `⚠` markers, each a prompt to fix the test rather than the markdown:

- `⚠ RAW — someCall(a, b)` — the call did not render as prose, so it stays as written. By design: the renderer does not know the argument roles and will not guess a sentence. Cure it with `#[TestDox]` below, or a clearer helper name
- `⚠ NOTHING READ — …` — every statement of that test fell outside the grammar, so the test body needs `given`/`when`/`assert` wrappers
- `⚠ NOT RUNNING — …` — `markTestSkipped` / `markTestIncomplete`: the scenario is documented but does not run

Quality depends on the test grammar: one When per test, body lines starting `given` / `when` / `assert`, method names that read as English. Bad prose = rename the test helper, not the extractor.

## `#[TestDox]` — writing the prose by hand

PHPUnit's own attribute is the override, and the sanctioned way to fix a line without renaming anything. It works on a test method (the heading) and on a `given` / `when` / `assert` helper (the step), and in both the text stands exactly as written — no derived name, no gloss, no passive or gerund conjugation on top:

```php
#[Test]
#[TestDox('Force closing an approved RMA closes it')]      // the scenario heading
public function force_close_closes(): void { … }

#[TestDox('{tote} holds {qty} of {item}')]                 // the step, slots filled from the call
protected function assertToteQtyFor($tote, $item, int $qty): void {}
```

`$this->assertToteQtyFor($this->cart, $this->item, 1)` then reads `- **Then** the cart holds 1 of the item`. Slot rules, all pinned by tests:

- each `{param}` takes the rendered argument the call passes for that parameter, PHP named arguments included
- a slot naming a parameter the helper does not have stays literal — `{nothere}`
- a slot the call left to a default renders as nothing, leaving a gap in the sentence
- slots read best when the call passes properties or objects (`$this->cart` → `the cart`). A bare literal is rendered with its parameter label — `'the blue tote'` in a `$tote` parameter becomes `tote “the blue tote”`, so `{tote} holds …` reads `tote “the blue tote” holds …`. For literal-heavy helpers, write the value into the sentence instead of slotting it

Precedence, the same on all three surfaces: **`#[TestDox]` first**, then the derived rules (passive dispatch for a When, the assertion families for a Then, the docblock gloss / `— by …` detail for a Given), then `⚠ RAW`. So the attribute silently outranks a docblock gloss on the same helper — if a helper has both, only the `#[TestDox]` text shows.

Put it on the behavior trait method, where every test that calls it gets the fix at once. It is inert to PHPUnit there: `#[TestDox]` targets classes and methods, but PHPUnit only reads it on test classes and test methods, so on a helper it changes no test behavior and warns about nothing. `#[TestDox]` on a test method is the escape hatch for a scenario name that will not read as English no matter how the method is spelled.

This is the cure for `⚠ RAW` — the marker means "the renderer refused to guess; a human should write this line":

```bash
grep -rn '⚠ RAW' .ai/*/spec-from-tests.md      # every line still waiting for prose
grep -rc '⚠ RAW' .ai/*/spec-from-tests.md      # a per-suite quality number to drive toward zero
```

## Vocabulary overlays

An overlay is a PHP file returning a partial vocabulary. Handy for one-off casing without touching the dialect:

```php
<?php return ['initialisms' => ['rma' => 'Return Auth'], 'non_verbs' => ['hospital']];
```

Keys: `initialisms`, `navigators`, `qualifiers`, `http_verbs`, `gerunds`, `participles` (word ⇒ reading maps) and `prepositions`, `ordinals`, `read_verbs`, `transparent_hops`, `invisible_hops`, `passthrough_calls`, `quantity_params`, `layer_prefixes`, `non_verbs`, `state_consts`, `identifier_consts`, `class_suffixes`, `field_suffixes`, `compounds` (word lists). Maps merge per entry, lists union in base order, `ordinals` is positional so a layer replaces it whole, and an unknown key fails the run loud.

## Source, and changing it

The phar is built from https://github.com/SkuNexus-Devs/dev-ian-spec-extract — a Laravel app that exists to develop this tool. Plan changes there, not against the phar.

- `app/Spec/*` — all the work: `Parse/TestFileParser` (structure), `SpecComposer` (the markdown), `CommandProse` / `AssertionProse` / `ExpressionRenderer` / `EnglishGrammar` / `VocabularyIndex` (the prose), `Cli` (one run, framework-free)
- `app/Console/Commands/SpecExtractCommand.php` — thin adapter, so `php artisan spec:extract` and the phar share `Cli`
- `config/spec/gwt.php`, `config/spec/skunexus.php` — the dialects
- `tests/` — 334 tests; `tests/Fixtures/corpus` + `tests/Fixtures/expected` are 15 byte-exact goldens from real BB/LO suites. Any prose change shows up there first, and a deliberate change means re-blessing the golden
- `.ai/spec-extract/` — why it is shaped this way: `design.md` (the class map, the config/dialect scheme, §6.1b on the `#[TestDox]` escape hatch), `decisions.md` (D1 per-file roots, D2 frozen-oracle goldens, D3 no guessed prose — `⚠ RAW` instead), `findings.md` (the stage-3 backlog). Read these before proposing a prose change; most "bugs" are pinned decisions
- `bin/build-phar.php` — the packer: `app/Spec`, `config/spec`, php-parser, `Illuminate\Support\Str` and doctrine/inflector, with a class map read out of the packed files. It refuses to finish if the packed phar cannot pass its own `--selftest`, and keeps the phar it replaced in `bin/previous/spec-extract.phar.N`

```bash
git clone git@github.com:SkuNexus-Devs/dev-ian-spec-extract.git && cd dev-ian-spec-extract
composer install
composer test                                        # 334 tests, goldens included
composer phar                                        # rebuild bin/spec-extract.phar
cp bin/spec-extract.phar <this skill's folder>/scripts/   # refresh this skill
```

## Related skills

- `skunexus-behavior-testing` — the grammar this extractor reads; its style guides §10 (`pest-style-guide.md` / `phpunit-style-guide.md`) are the authoring guidance that keeps this output readable. Write tests per that skill and the spec comes out right.

This skill renders existing tests as a spec and stops there: it does not write them (`skunexus-behavior-testing`), drive them test-first (`skunexus-tdd-testing`), run them (`composer test`), or turn the spec into a PR description (`skunexus-backend-pr`) or QA testing steps (separate skill).
