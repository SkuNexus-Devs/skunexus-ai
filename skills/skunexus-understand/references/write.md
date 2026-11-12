# Write: the page, its reading order, the layers, the trace and the checks

You write `plan.json`, the fragments and `quiz.json`. The build writes everything else from git and from `plan.json`, so the page's code, file lists, counts and trace tables are never typed by a model.

**One word for readers.** The page calls each step of the change a **piece**: "The N pieces", "Files in this piece", "I've read this piece". Internally the name stays "chapter": `plan.json` `chapters[]`, the ids `ch-<n>` and the fragments `fragments/ch-<n>.html`. No reader-facing text, yours or the page's, says "chapter".

## 1. Page anatomy

The first screen tells the change; everything else sits one level deeper, behind a closed row or a "More on this" leaf. At most two levels of disclosure. Top to bottom:

| Part | What it shows | Fed by |
|---|---|---|
| **The bar** (sticky) | The ticket and title; the current section's name (a click goes back to the top); "Viewed n/N files"; the quiz pill ("Quiz 0/5", then "First try 4/5"); "Expand all" ↔ "Collapse all"; Options (font, code wrap, full width, keyboard shortcuts, "Reset reading progress", "Reset quiz") | the engine |
| **The file tree** (left, sticky) | Every changed file, folders first and compacted ("src/Inventory/Jobs"); per file its name (opens its diff in "All N files"), its piece badges as their own links ("① also ④"), a status mark with a text alternative, a Viewed tick. Generated files are hatched, with no badge. Drag-resizable, hideable. The filter box only above 20 files | `map.json` and the pieces' `files` |
| **h1 and the lead** | The heading, then the change in one sentence | `heading`, `glance` |
| **Start here** | A framed band under the lead: "Look at the map and what to carry · ~2 min → Read pieces ①–③ · ~4 min → Answer 5 questions · ~3 min · 0/5". Every step is a link; no step numbers | the build, from the map, the carry list, the main-flow pieces and the quiz |
| **The strip and the piece index** | One tile per changed file, width ∝ log(lines changed), coloured by family. A tile opens its file; hover, focus or a tap shows a card with the file link and its piece badges. The piece index under it is the strip's legend: badge · name · file count · "under Go deeper" for a hollow badge · Generated files · All N files | the build |
| **The map** (`#map`) | A framed section, h2 "The map": the change as a picture, every box a link | `plan.json` `map` (§18) |
| **To carry into the review** (`#carry`) | Tagged lines (`inherits`, `bypasses`, `ask`, `data`, `not here`), each with its own id and its pieces as badge links | `plan.json` `carry` tags, `open_questions`, `not_in_change` (§19) |
| **The N pieces** (`#pieces`) | The main-flow pieces (`read: must`), open, in `chapters[]` order. Each: a note (≤ ~120 words) on the left, the deciding hunk on the right, "More on this" under the note, "I've read this piece", "Next: ② … ↓" | `fragments/ch-<n>.html` (§4) |
| **Check yourself** (`#quiz`) | The final questions, open in the main flow, never folded, never after Go deeper | `quiz.json` (`quiz.md`) |
| **Go deeper** (`#deeper`) | Closed rows. Each row's summary is the exact heading of the section it opens | `plan.json` `deeper`, then the build's fixed rows |

**Inside Go deeper,** the build owns these headings. A reference to one uses its exact words and links to its id (§13):

| Id | Heading | Holds |
|---|---|---|
| `#asked` | What was asked | `asked.html` (§3) |
| `#problem` | The problem, and what happens now | `problem`, `problem_ref` and the `behaviour` table |
| `#background` | Background | `background.html` |
| `#intuition` | Intuition | `intuition.html` |
| `#trace` | The goals and their state | the trace (§7) |
| `#drift` | Where the code differs from earlier plans | `drift` entries with no `carry` tag (§9) |
| `#proven` | How it's proven | `proven.html` (§6) |
| `#look` | Where to look hardest | `hotspots` with no `carry` tag (§8) |
| `#ops` | Deploy and merge notes | `ops` entries with no `carry` tag (§9) |
| `#ch-<n>` | the badge and title of a deep piece | a `read: skim` piece: hollow badge |
| `#ch-mech` | Generated files | `mechanical` groups |
| `#files` | All N files | every changed file: each row expands in place to its whole diff, with sticky file headers (path, "+n −m", a 5-square diffstat, piece badges, Viewed) and "Explained in ① … · also ④ …" under it. Lockfiles and generated files link out instead of embedding. Search and filters only above 20 files |
| `#refs` | Sources | one entry per source a reader can open, grouped (§14 `origins`), then the Glossary and "About this page" (the Built-from line, base → head, files, lines) |

`deeper` orders the rows and groups sections into them (§14). "All N files" and "Sources" are always the last two rows.

**Behaviour everywhere** (the engine; nothing to author): every jump opens the target's closed ancestors and flashes it; Expand all leaves the file diffs and "Show N lines" closed; every external link opens a new tab with `rel=noopener`; every control's tooltip says what a click does.

**On a phone** the bar is one 48 px line (title or section, the quiz pill, "Files", Options), the tree is a drawer opened from "Files", a strip tile opens its card on the first tap, the map and Start here stack, a piece puts its note above its code, and every target is at least 44 px. Nothing scrolls sideways except code inside its figure. You author nothing for this; just keep labels short.

**Families** (the badge and strip colour) are derived, never authored: a `read: must` piece is `change`; a `read: skim` piece whose files are all tests is `tests`; any other `skim` piece is `harness`; a mechanical group's files are `gen` (hatched, no badge). A filled badge is a main-flow piece; a hollow one sits under Go deeper.

**Intent-only** (`plan.json` `stage: "intent-only"`): no tree, strip, piece index, pieces, "All N files", Viewed count or "Files" button. The main flow is the lead → Start here ("Look at the map and what to carry → Read what was asked → Answer N questions") → the map, drawn from the contract's workflow (§18) → the carry list → **What was asked, open, as an h2** → Check yourself → Go deeper (Background, Intuition, The goals and their state, Sources). You write `asked.html`, `background.html` and `intuition.html`; `chapters`, `mechanical` and `hotspots` are empty.

## 2. Reading order

The page's order is fixed (§1). You choose the order of the pieces.

1. **The main flow** is the pieces a reviewer must read to know the change (`read: must`), foundations first: the definitions others cite, then each consumer, then what enforces it, then wiring that changes behaviour (a binding swapped app-wide).
   - In an SN backend: migrations and entities, then commands, handlers, plugins and transitions, then controllers, GraphQL and queued jobs, then providers and config.
   - In a repo of skills or docs: the shared reference every file cites, then the first skill, then its checker script, then the next skill and its checker, then a changed neighbour skill.
2. **Under Go deeper** go the pieces a reader can trust or skim (`read: skim`): the tests piece, the test harness, routine wiring and the briefs. The tests are never a main-flow piece: the developer reads the proof only on demand.

- Each piece states why it sits where it does in `why_here`: "Comes after ① the hold because it writes that row." It is not shown on a main-flow piece; a deep piece shows it when `gist` is absent, and the fact-checker reads it.
- **No risk left last.** Files read late get less attention. When the foundations-first order puts a high-risk piece after low-risk ones, move it up unless a dependency forbids it. Its risk is on the carry list either way.
- Inside a piece, follow one request or command: entry, then effect.
- The order is a recommendation. The file tree, the strip and "All N files" are other ways through the same change.

## 3. What was asked: `asked.html`

A teaching summary, not a copy. It sits under Go deeper as the row "What was asked" (open in the main flow on an intent-only page). A reader who never opens `prd.md` must come away able to answer: what problem, what is in and out, what each group of criteria means in a concrete case, and why the main forks went the way they did. Paraphrase in plain words and let the ref chips carry the ids; the refs hold the verbatim text.

In this order, as `h3` sections, skipping any with no source:
1. **The problem and why:** 2–4 sentences from `prd.md` §1–2 (or `investigation.md` §1, or the fallback the ask came from, tagged). A Draft contract opens with a `risk` callout: "The contract is a draft (amending v2): this ask may still change."
2. **In and out of scope:** the goals as one short list. Then the **non-goals** under their own heading ("Not in this ticket"), one line each, cited, never folded into a toggle: a non-goal is what readers most often get wrong. Add `prd.md` §5 Scope fences and the plan's `Out of scope` where they say more. The same non-goals go in `plan.json` `not_in_change`, which puts them on the first screen as the carry list's "not here" line (§19).
3. **What must hold:** the criteria grouped in plain words, one short paragraph or list item per group (a requirement, or a workflow), with the criterion chips: "Placing an order holds its stock at once, and a second order can't take the same units <span class="ref" data-ref="R1.a">R1.a</span> <span class="ref" data-ref="R1.b">R1.b</span>." Mark an assumed criterion "(assumed)" and attach its `Q` chip. Skip retired ones.
4. **One workflow, walked:** one `workflows.md` scenario, the one that covers the most criteria, as a stepper with toy data: per step, the step chip (the build adds the "open in storyboard" link), the state before → after in a `table.toy` with changed cells marked, and the outcome in one line. When a storyboard exists, say "the storyboard draws these screens" once; never redraw them. With no `workflows.md`, walk the main criterion's case with toy data instead, cited to the criteria. With neither `workflows.md` nor criteria, point to the Intuition's walk in one line; never a second stepper.
5. **Decisions:** `decision` callouts, each "why A, not B", from `decisions.md`, Decided `Q` entries, rulings, or the PR body and commits when they name a choice. Name the rejected option where a source names it. One recorded only in a `feedback.md` **Proposed:** line is cited by its FB chip (the **Status:** line) plus your paraphrase, marked "(paraphrase)". With no recorded reason, write no "because".
6. **Assumptions:** a table of each `Q` marked Assumed (with no `prd.md`, the assumptions the PR body or Jira states): the assumption, its status ("Assumed: confirm with the PO", "Decided 2026-11-03"), and the criteria that rest on it.
7. **Open questions:** `prd.md` §7 entries still Open, every `feedback.md` entry whose **Status:** is open (cited `feedback.md FB<n>`), and deferred items with their one-line why. Each also goes to `plan.json` `open_questions`, tagged `(asked)` (§10), which puts it on the carry list. When `prd.md` says no question is open but `feedback.md` has open entries, list them anyway and add a `drift` entry: "prd.md says no question is open, but three feedback entries still are" (§9).
8. **Scope rulings:** each ruling that moved scope: what it settled, in your words, then "ruled" and its chip, e.g. "Cancelling a packed order stays out of this ticket (ruled <FB chip>)". Cite the ruling, never the discussion (`inputs.md` §6).

Length: 300–600 visible words (outside toggles; chip labels don't count; the check warns over 600). A contract with more than 5 use cases may run to 900, with the per-workflow detail inside `details.toggle`. Skip "What must hold" when the trace has only `goal.` rows (no PRD): "The goals and their state" already lists them. Over 700 words in all on an intent-only page means `full` verification (§16). Toy data comes from `plan.json` `toy` (§13).

```html
<h3>Not in this ticket</h3>
<ul><li>No customer email when a hold is released <span class="ref" data-ref="ng.email">non-goal</span>.</li></ul>
<h3>One order, walked</h3>
<ol class="stepper" data-title="Unpaid web order #1001 (toy data)">
  <li><h4>The customer places the order</h4>
    <p><span class="ref" data-ref="s1.1">s1.1</span></p>
    <table class="toy"><tr><th>MUG-1</th><th>available</th><th>order #1001</th></tr>
      <tr><td>before</td><td>10</td><td>none</td></tr><tr><td>after</td><td class="chg">8</td><td class="chg">placed, unpaid</td></tr></table>
    <p>The order holds 2 units at once.</p></li>
</ol>
```
A non-goal has no id of its own: give it a slug ref (`ng.<slug>`) whose `text` quotes the `prd.md` §3 line, the PR body's or Jira's fence, or a hand-off's out-of-scope item. The walk sits under its own `h3`, so its steps are `h4`.

## 4. Pieces

A piece is one coherent step of the change: its contract, its implementation and its tests together. Directories are evidence, not rules.

- **Seed the pieces,** first match wins:
  1. the tasks in `backend-plan.md`: the waves and `depends_on` give the build order. Merge tiny tasks; split a task over the budget;
  2. the commits, when they tell a clean story: task-aligned subjects such as `ABC-123: T3 …`, no "wip" or "fix review", and no commit holding more than about two pieces' budget;
  3. a two-pass split: first write one line per `read`-tier file saying what it does in this change, then cluster the lines into behaviour units (a command, its handler, its provider entry, plugins, transitions, GraphQL and tests).
- **Budget:** about 400 changed `read`-tier lines per main-flow piece, a soft target, not a rule. A file is never split, so a big single file is its own piece; point the hotspots inside it. Badges run ① to ⑫ and beyond, but a reader holds about 4–6 main-flow pieces at once: on a large diff, put the tests, harness and wiring under Go deeper rather than add main-flow pieces.
- **Small diffs:** about 5 files or fewer, or a single concern, get one walkthrough piece (`ch-1`). The page keeps its other parts; Start here reads "Read piece ①".
- **`read: must` or `skim`.** `must` is the main flow (filled badge). `skim` is under Go deeper (hollow badge): the tests and what they prove, the harness, renamed call sites, boilerplate DTOs. A skim piece can be a short paragraph and its file list.
- **Deletions and moves.** A deleted `code` or `test` file is `read`-tier: say where its behaviour went, in a piece (it may be `skim`). `map` pairs a moved and edited file at 30% similarity and records its `old_path`; read that pair as an edit, never as a new file. A near-move `map` didn't pair (an added file whose basename matches a deleted one; `map.json` lists the candidates in its `pred`, unchosen) is also read as an edit: put both files in the same piece, and name the pair in the piece brief's moves. A folder deleted whole (a retired skill or module) may instead get one skim piece that names each deleted file's successor and the piece that holds it; that satisfies the near-move rule.
- **Generated files last.** `skip` and `verify` files go into `mechanical` groups by reason, shown under the row "Generated files": one line of intent and one check a reader can run or trust, e.g. "Rename only, 0 content lines" or "`composer.lock`: only the scheduler package and its two dependencies changed". A `read`-tier file never goes into a mechanical group; the check fails if it does.
- **Coverage:** every file in `map.json` matches exactly one piece's `files` or one group's `files` (globs allowed). The check fails on a file in none or in two. A file whose code another piece also shows gets that piece as "also ④" in the tree and in "All N files".
- **A piece that owns no file.** One file can hold two ideas, and a file is never split. Give the second idea its own piece with `files: []`, and show that file's hunks in it. The file stays in its home piece; this piece is its "also ②", and the piece index says "shares ①'s file" (each home piece's badge, then "file" or "files" by count) instead of a count. The piece has no "Files in this piece"; its proof line still comes from the trace rows it builds.
- **After a re-map,** compare each file's `status`, `tier` and `old_path` with the previous `map.json` (keep a copy before you re-run `map`). A pair can turn into a move, and a deleted file can move up to `read` and out of a mechanical glob. Re-check every piece whose files changed, its prose, callouts and `evidence_note`, and re-fill its brief.

### The shape of a main-flow piece

The fragment has two parts, split by a line holding only `<!--more-->`:

| Part | Where it shows | What goes in it |
|---|---|---|
| **The note** (before `<!--more-->`) | The left column, open | At most ~120 visible words: what this code does in the change, in plain words. Then the **deciding hunk** first: the one `data-hunk` marker (two at most) that decides the piece. Its `data-notes` line notes tie short remarks to its lines (§12). The build moves these figures to the right column |
| **More on this** (after `<!--more-->`) | A closed leaf at the bottom of the note | The rest at the note's width: the scenario (§5), the walkthrough beyond the deciding hunk, callouts, the toy-data example, the invariant. Its code figures join the right column while the leaf is open |

The build adds the rest of the piece: the h3 (badge and `title`); "Files in this piece (n)" and the proof line ("Proven by …" from the trace, or "No test proves this piece."), both inside "More on this"; then the piece's checkpoint questions, if any, visible after "More on this" (a question is never folded); then "I've read this piece" and "Next: ② … ↓" (the last piece's goes to "Check yourself").

A main-flow fragment without `<!--more-->` shows whole as its note, and its "More on this" holds only the files and the proof line (no leaf at all when it has neither): only for a piece that fits in ~120 words. A **deep piece** (`read: skim`) shows its whole fragment under its own heading, with `gist` (else `why_here`) as one line under the title; a `<!--more-->` there is ignored.

```html
<p>The job runs every minute and picks the holds whose order is still unpaid when the window ends. It deletes them, so the units count as available again at once <span class="ref" data-ref="D3">D3</span>.</p>
<pre data-hunk="src/Inventory/ReleaseExpiredReservations.php:38-52" data-notes="41:unpaid orders only|44:older than the window|50:one delete per run"></pre>
<!--more-->
<p><strong>What it must do:</strong> release an unpaid order's hold once the window closes <span class="ref" data-ref="spec.release-unpaid-after-window">the release test</span>.</p>
<p>In the toy shop, order #1001 is never paid. At 10:31 the job releases its 2 units: available 5 → 7. Order #1002 is paid and keeps its 3.</p>
<pre data-code="config/inventory.php:8-10" data-note="the window the job reads"></pre>
<aside class="callout" data-kind="question"><p>An order paid at exactly 10:30:00 is released by the 10:30 run. Is the boundary meant to be inclusive?</p></aside>
<p>A paid order's hold is never released by the job.</p>
```

`plan.json` gives each piece a `short` name, used after its badge in every reference ("③ the release job"), and an optional `proof` line (§14).

## 5. Tests in a piece

Under "More on this", open with what the piece must do, then show how:
1. the scenario: a Given/When/Then from `spec-from-tests.md`, cited as `spec.<slug>` (`inputs.md` §6), or else one line of test intent taken from the test names;
2. the rest of the production hunks, with prose;
3. the test hunks, or nothing: "Files in this piece" lists the test files, and the proof line names the tests.

Don't make a tests-first piece in the main flow. Readers who read tests first find more test defects and fewer production ones. The whole proof, by criterion, is in `proven.html`, which usually sits in the same Go-deeper row as the tests piece.

## 6. How it's proven: `proven.html`

The proof, organised by what it proves. Quote the `spec-from-tests.md` render; never write a Given/When/Then of your own, and never render tests: `skunexus-spec-extract` does that.

In this order, as `h3` sections:
1. **Scenarios by criterion:** group by requirement; with no criteria, by `goal.<slug>` row, else by test file or script. Per criterion: its chip, then each scenario that proves it, with its `spec.<slug>` chip and its Given/When/Then as a short `ul` (toy values as the render gives them). The `Tests (landed)` lines give the mapping; with no render, use the test name and its `file:` ref. A criterion whose piece already shows the scenario gets one line and a link to that piece.
2. **What ran:** one line. "Ran at this head: `composer test -- --filter=Reserve`, 41 passed, 0 failed" (from `<DIR>/review/tests-<sha7>.txt`, format in §8), or "Not run here: the tests exist, and nobody ran them at this head."
3. **Not tested:** one `risk` callout listing every built criterion with no test, every `Tests (flagged)` item with its why, and every `⚠ NOT RUNNING` scenario. Say "none" when there are none: that is a finding too. Untested paths live here and on "The goals and their state", never on the carry list.
4. **Known reds:** from the baseline line or `test-baseline.md`, one line each: "Red before this change: `ReleaseTest` 'a paid order keeps its hold' (baseline 2026-11-08)." A test the run shows red that the baseline doesn't list goes here too, marked "new red at this head". Say "none" when there are none, and "no baseline recorded" when there is no baseline.
5. **Manual testing steps:** Jira's Testing Steps, as a short `ol` in your words, cited `jira.steps`. Skip when the field is empty.

At most 2 code markers (`data-code` on a key assertion); the test hunks live in their pieces. Length: 150–400 visible words. "What ran" lives here only: a piece never restates it.

## 7. The trace

`plan.json` `trace` has one row per criterion. The build shows it in three places:
- **the map's outcomes:** each outcome names a trace row in `goal` and shows its state and test count ("tested, 2 tests");
- **each piece's proof line:** the `proven` refs of every row whose `built` names the piece ("Proven by …"), or "No test proves this piece." when it builds rows and none is proven;
- **"The goals and their state"** (`#trace`, under Go deeper): a table (Goal, Built, Proven, State) only when there are 4 or more rows or any row is not `tested`; otherwise one status line at the end of What was asked ("2 goals: 2 tested").

```json
"trace": [
  {"id": "R3.a", "text": "An unpaid order releases its hold when the window closes",
   "built": ["ch-3", "file:src/Inventory/ReleaseExpiredReservations.php:41"],
   "proven": ["spec.release-unpaid-after-window", "file:tests/Inventory/ReleaseTest.php:22"],
   "state": "tested", "note": ""},
  {"id": "R2.a", "text": "An order larger than available stock is backordered",
   "built": ["ch-2"], "proven": [], "state": "untested", "note": "No test reaches the backorder branch."},
  {"id": "R5.a", "text": "Holds expire on a per-warehouse window",
   "built": [], "proven": [], "state": "non-goal", "note": "Retired v2: merged into R3.a."}
]
```

- **Which ids:** every criterion in `prd.md` (`R<n>.<x>`; in an older PRD `AC<n>`; with no criteria at all, the requirements `R<n>`). With `investigation.md`, its `A<n>` items; with only the plan's inline block, its `A<n>` items. Workflow steps `s<n>.<m>` may be added as optional rows. With only a PR body, Jira or the ticket's own notes as the ask (a bug fix's root-cause note or hand-off, `inputs.md` §3), there are no criterion rows: `trace` may hold one `goal.<slug>` row per goal they state (a note's numbered fix step is one goal; a `goal.<slug>` ref quotes it), else it is `[]`. Never invent a criterion from prose. Each id **exactly once**: the check errors on a missing criterion and warns on an id that isn't in `prd.md`.
- **`text`:** a short paraphrase. A verbatim excerpt of the criterion is in `refs`.
- **`built`:** piece ids and `file:PATH:LINE` refs at head. Take them from the plan's `Satisfies`, the piece's files and the code; a piece writer proposes them (§15).
- **`proven`:** `spec.<slug>` refs and `file:tests/…:LINE` refs. Take them from the `Tests (landed)` lines and `spec-from-tests.md`. A `⚠ NOT RUNNING` scenario never counts.
- **`note`:** plain text; `[name](#ch-2)` cites a piece (badge and name).

| State | Means | Needs |
|---|---|---|
| `tested` | A test proves it and ran green at this head | a non-empty `proven`, and `<DIR>/review/tests-<sha7>.txt` showing those tests pass |
| `built` | Code and a test exist; the test wasn't run here (or ran red: say so in `note`) | a non-empty `built` and a non-empty `proven` |
| `untested` | Code exists; no test proves it | a non-empty `built` |
| `not-built` | No code for it yet | a `note` |
| `drift` | The code does something other than the criterion says | a matching `plan.json` `drift` entry, `needs_decision: true` (§9) |
| `non-goal` | The ticket deliberately doesn't do it, or the criterion was retired | a `note` (e.g. "retired v2: merged into R3") |
| `deferred` | Planned for a later PR or ticket, or waiting on an open question | a `note` naming where it went |

- **Intent-only:** every row is `not-built`, `non-goal` or `deferred`, and the note says "no code yet" (on an Analysis ticket that will get none: "Analysis ticket: no code"). After the plan, name the task: "no code yet; planned in T3". A criterion met by a document, not code (a fit review, a proposal), is `not-built` with the note "Analysis deliverable: <doc>"; the page doesn't judge the document. A build criterion that waits on an approval is `deferred`, its note naming the gate.
- **The status line** counts rows by state: "14 criteria: 9 tested · 3 built · 1 not built · 1 non-goal".
- Never upgrade a state the evidence doesn't give: a test that exists is `built`, not `tested`, until a run at this head shows it green.

## 8. Evidence, risk, tier and hotspots

Three separate axes per piece. Never show a confidence number or a percentage: model confidence is overconfident, and a closed vocabulary with a reason is honest.

| Evidence state | Means | Backed by (`evidence_note`) |
|---|---|---|
| `tested` | A test ran and passed at `<HEAD>` | the developer's run, saved as `review/tests-<sha7>.txt` (format below). Running tests is the developer's call: ask once. With nobody to ask, don't run them; the state is `covered` |
| `covered` | A test exists that exercises it, not run here | the test file and name |
| `traced` | Traced to a recorded why (a PRD criterion, a decision, the PR body, a commit, `answers.md`), no test | the ref ids |
| `inferred` | Read from the changed text only, code or prose | "read from the diff" |
| `assumed` | Not checked: framework behaviour, an external system, config on a server | what was assumed |

- **`review/tests-<sha7>.txt`:** each command run on its own line, prefixed `$ `, followed by that command's final output lines; the last line is `at <sha7> on <YYYY-MM-DD>`. The check confirms only that the file exists and names the head SHA, so tie each `tested` piece's `evidence_note` to a command in it.
  ```
  $ composer test -- --filter=Reserve
  Tests: 41 passed, 0 failed
  at abc1234 on 2026-11-10
  ```
- A piece's **main claims** are its scenario and the invariant it ends with; its state is the weakest state among them. A side claim carries its own tag ("(inferred from code)") and doesn't lower the piece. The state must agree with the trace rows the piece builds: a piece whose criteria are all `untested` is not `covered`. The evidence state is not shown on the page; the fact-checker reads it.
- A claim that a named test backs gets a faded `verified` callout (labelled "Backed by a test") naming the test, unless the piece's proof line already names it. Faded means lower priority, not settled: the reader still judges the test.
- **Risk** is the blast radius: `high` for data loss, money, stock, state transitions, external pushes, migrations on big tables or backward-compatibility breaks; `med` or `low` otherwise. It shows in the Risk column of "All N files".
- **Tier** comes from `map.json`: `read`, `verify` or `skip`.
- **Hotspots: at most 7** line ranges where a human is most likely to need a change, each with a one-line reason: an untested branch, an inferred contract, a concurrency or migration edge, a deviation from the PRD, a drift. Each is fact-checked. A hotspot with a `carry` tag goes on the carry list (§19); the rest are listed under "Where to look hardest" in Go deeper. Each line leads with its reason, then the file's name, which opens the file in "All N files". In prose, use that heading; the page never says "hotspot 2".

## 9. Drift, deploy and rollback

A drift is a place where a plan, a decision, a PRD criterion, a contract step or a PR body says one thing and the code does another. For an author whose agents wrote much of the branch, this is the most useful part of the page.

- Look for drift in: the plan's task steps and `Out of scope`, `decisions.md`, the PRD's §6 criteria, the `workflows.md` steps' before → after, statements in `backend-summary.md`, a posted `pr.md` or a PR body older than the head (`inputs.md` §4).
- Each drift is a `drift` callout in its piece and one `plan.json` `drift` entry, `{at, note, ref, needs_decision}`. `at` may be a file the diff leaves unchanged (the plan named a file the code doesn't touch): give its line at head. All N files has no row for it, so the page shows its name as plain code text, not a link. The build lists it under "Where the code differs from earlier plans" in Go deeper, `needs_decision` first; with a `carry` tag it goes on the carry list instead. A drift that no decision records is also an open question (§10): its callout may end with that question and then counts as the question's callout.
- **Between two artifacts** (a storyboard built from an older contract, a plan that predates the contract, `prd.md` against `feedback.md`): `at` is the artifact's repo-relative path with no line, `needs_decision: false`. This is the only drift an intent-only page has; its callout sits in `asked.html`. A local path never reaches the page, so the build drops such an `at` from the line: name both artifacts in words in the `note` ("the storyboard was drawn from the contract's first version").
- State both sides, each with its chip, and no verdict: "**Plan said** the window comes from config. **Code does** use a 30-minute constant." The plan task's chip follows the first half, a `file:` chip the second (markup in §12). Against a plan or a decision, which side is right is the developer's call.
- **Against a PRD criterion or a contract step,** set `needs_decision: true`, and the trace row's state is `drift`. The contract is the baseline, so the gap stays open until the code is fixed or the contract changes through its owning skill. The quiz asks no `criterion` question on that criterion.
- List each drift in the hand-off, `needs_decision` first. Never fix an artifact or the code from this skill.

**Deploy and rollback.** `plan.json` `ops`, `[{what, files, note, ref?, label?, carry?}]`, one entry per deploy or merge concern: a migration and whether it reverses (`down()`); new env or config keys and whether `.env.example` changed; scheduled jobs, queues and listeners, and where they are registered; backfills and what existing rows hold; feature flags; merge conflicts and which side to keep; in a repo of skills or docs, installs to re-link and artifacts that in-flight work already wrote in the old shape. The build lists them under "Deploy and merge notes" in Go deeper; an entry about existing data a reviewer must keep in mind may carry `"carry": "data"` instead. The check warns when `map.json` has a `migration` or `config` file and `ops` is empty. A wiring claim cites its registration line; if that line isn't in the diff, the claim becomes an open question.

## 10. Open questions

`plan.json` `open_questions`: plain strings, each starting with a tag for where it belongs (`(ch-3) …`, `(asked) …`, `(proven) …`, `(background) …`, `(intuition) …`). Every one becomes an `ask` line on the carry list (§19). The build strips the tag and ends the line with a link: a piece's badge and name, or the section's heading. The words after the tag are plain, for the author: no tag, hash, `file:line` or bare id inside them (§13). Each also appears as a `question` callout in that fragment, without the tag. They come from:
- a why no source gives: "Unknown: ask the author. Why is the window 30 minutes?";
- a "this looks wrong" moment, phrased as a question with its evidence: "An order paid at exactly 10:30:00 is released by the 10:30 run. Is the boundary meant to be inclusive?";
- a drift that no decision records;
- a `prd.md` §7 entry still Open, or an open `feedback.md` entry, even when `prd.md` says none is open (§3 item 7).

An answered question moves to `answers.md` (`inputs.md` §4). In author mode the rest feed `skunexus-backend-pr` Step 1. In reviewer mode they are the reviewer's list for the author.

## 11. The participate layer

Ungated material that builds a model of the ticket, so the reader can have the next idea.
- **Glossary:** one name per concept, with a one-line definition and a code location (or, intent-only, the `prd.md` or `workflows.md` id). Use exactly these names everywhere: piece titles and short names, the map's boxes, prose, quiz stems, open questions. A term not in the glossary isn't used for a concept of the ticket. It shows under "Sources".
- **`next` callouts:** at most one per piece, mostly in Intuition and the last piece. An extension seam ("a second warehouse needs one more row in `stock_location` and nothing in the job"), what the change makes easy or hard, what you might try next. They are never quizzed.

## 12. The fragment vocabulary

Fragments are HTML snippets with no `<html>`, `<head>` or `<body>`. Only these tags and classes are allowed. The check rejects scripts, event attributes, `style=`, `javascript:`, iframes and external links, and warns on unknown classes.

`p, h3, h4, ul, ol, li, strong, em, code, br, a[href^="#"], table/thead/tbody/tr/th/td, figure, figcaption, details, details.toggle, summary, pre[data-hunk|data-code], span.ref[data-ref], aside.callout[data-kind], div.fig.flow|ba|cards|toy with their parts div.node, div.edge, div.pane, div.card, ol.stepper, span.chg, td.chg`, and the `<!--more-->` line (§4).

Headings inside a fragment start at `h3` and skip no level; the build owns `h1` and `h2`, and a piece's own `h3`. A pane, card or stepper-step heading directly under the section is an `h3`; it is an `h4` only when it sits under an `h3` of your own.

**Code markers.** The build replaces each one with the real lines from git, escaped, with a caption, a GitHub link and a Copy button. The caption's file name opens that file in "All N files"; "GitHub ↗" is a separate link that opens a new tab. Over 30 lines, the code folds under "Show N lines". Never put code inside the `<pre>`.
```html
<pre data-hunk="src/Inventory/ReserveStock.php:30-58" data-note="the hold is written in the order's transaction"></pre>
<pre data-hunk="src/Inventory/ReleaseExpiredReservations.php:38-52" data-notes="41:unpaid orders only|44:older than the window"></pre>
<pre data-code="src/Inventory/AvailableQty.php:12-20"></pre>
<pre data-code="src/Inventory/AvailableQty.php@base:12-18"></pre>
```
- `data-hunk` is the diff of head lines 30–58 (its range must overlap a changed hunk; a hunk larger than the range, on any file, is clipped to the range plus 3 context lines and its header says `clipped`); `data-code` is head-side lines with no `+`/`−`; `@base` takes the lines from the merge base (a renamed file's old path), for a "before" pane. For an unpaired near-move, the before pane is `data-code="OLD_PATH@base:…"`. An intent-only page has no diff: use `@base` markers only.
- `data-note`: one short remark in the caption.
- `data-notes="LINE:text|LINE:text"`: line notes. Each LINE is a line number the figure shows (head side; base side for an `@base` excerpt or a deleted file), and each text is a few plain words (backticks allowed). The build puts a numbered marker on that line and the note beside the code. A LINE the figure doesn't show is a build error.
- Embed at most about 6 hunks per piece, one or two before `<!--more-->`; the rest stay in "Files in this piece".

**Refs, piece links and callouts.**
```html
<p>Checkout now holds stock when the order is placed <span class="ref" data-ref="D2">D2</span>, not when payment arrives.</p>
<p>The job deletes the row <a href="#ch-1">the hold</a> wrote.</p>
<aside class="callout" data-kind="drift"><p><strong>Plan said</strong> the window comes from config <span class="ref" data-ref="T4">T4</span>. <strong>Code does</strong> use a 30-minute constant <span class="ref" data-ref="file:src/Inventory/ReleaseExpiredReservations.php:18">ReleaseExpiredReservations.php</span>.</p></aside>
<aside class="callout" data-kind="verified"><p><code>ReserveStockTest</code> "a retried message reserves once" backs the unique key.</p></aside>
```
- A link to a piece, `<a href="#ch-1">…</a>` (exactly that: no other attribute, plain text inside), renders as that piece's badge and `short` name, whatever text you wrote: the one way to cite a piece. Its own number, its own link.
- A link to a section uses the section's heading words: `<a href="#asked">What was asked</a>` (§1 lists them).
- A `file:` chip names the file and opens it in "All N files"; its preview quotes the line.

Callout kinds: `concept` (a definition), `edge` (a boundary case), `risk`, `decision` (why A, not B; cites a `D` or `Q` ref), `drift`, `verified` (faded, "Backed by a test"; names the test), `question` (ask the author), `next` (a participate prompt), `fact` (a quiet side note with no label), and in the Asked and Proven sections `nongoal` ("Not in scope"), `ran` ("What ran": the test run and its result) and `nocode` (intent-only: no code yet). The shell prints the label from `data-kind`; don't write it. Ration them: about 3 per piece, and none in a note before `<!--more-->` except a `fact`.

**Diagrams.** Use one only where it carries more than prose. Each sits in a `figure` with a caption; values are toy data.
```html
<figure><figcaption>Placing order #1001 (toy data)</figcaption><div class="fig flow">
  <div class="node"><strong>Checkout</strong>POST /orders</div><div class="edge">{sku: MUG-1, qty: 2}</div>
  <div class="node"><strong>ReserveStock</strong>writes one hold</div><div class="edge">hold 1001/1</div>
  <div class="node"><strong>availableQty</strong>10 − 2 = 8</div>
</div></figure>
<figure><figcaption>availableQty, before and after</figcaption><div class="fig ba">
  <div class="pane"><h3>Before</h3><pre data-code="src/Inventory/AvailableQty.php@base:12-18"></pre></div>
  <div class="pane"><h3>After</h3><pre data-code="src/Inventory/AvailableQty.php:12-20"></pre></div>
</div></figure>
<figure><figcaption>MUG-1 after order #1001 (toy data)</figcaption><div class="fig toy"><table class="toy">
  <thead><tr><th>sku</th><th>on_hand</th><th>held</th><th>available</th></tr></thead>
  <tbody><tr><td>MUG-1</td><td>10</td><td class="chg">2</td><td class="chg">8</td></tr></tbody>
</table></div></figure>
```
`.flow` alternates `div.node` (a bold name, then what it does) and `div.edge` (the example payload). `.ba` is two `div.pane`, each a heading and the same kind of content. `.cards` is a row of `div.card`, each a heading and one line. `.toy` holds a `table.toy`, with changed cells marked `td.chg` (or `span.chg` inline). Diagrams go under "More on this", never in the note.

**Stepper.** At most one per piece (and one in `asked.html`), 3–12 steps, toy data only, every step cited. Each `<li>` holds a heading, a `<p>` with the code-location or step ref, a `<table class="toy">` with the state after the step, and a one-line note.
```html
<ol class="stepper" data-title="Releasing order #1001 (toy data)">
  <li><h3>The job selects expired holds</h3>
    <p><span class="ref" data-ref="file:src/Inventory/ReleaseExpiredReservations.php:40">ReleaseExpiredReservations.php</span></p>
    <table class="toy"><tr><th>order</th><th>paid</th><th>placed</th></tr><tr><td>#1001</td><td>no</td><td>10:00</td></tr></table>
    <p>At 10:31 the hold is 31 minutes old and unpaid, so it is selected.</p></li>
</ol>
```
Long background or side material goes in `<details class="toggle"><summary>…</summary>…</details>`, closed by default. Non-goals never go in one.

## 13. Writing style

- **Classic style.** The reader is an intelligent peer, and you show them something true. State it plainly; no hedging and no "we will see".
- **Concrete before abstract.** The toy example comes first, then the rule it shows.
- **Toy data:** small numbers and invented names (order #1001, `MUG-1`, on_hand 10), all from `plan.json` `toy` (below). Never data from a client database.
- **Before/after with the result on the same line:** "on_hand 10, holds 4 + 3 → available 3".
- **Short sentences, one idea per paragraph.** No em-dash asides, no "worth noting", "simply" or "it's important to".
- **Name real things** in `<code>`: classes, methods, tables, config keys, queue names.
- **Each piece:** the note says what the deciding hunk does; "More on this" gives the scenario, then prose → code marker → consequence, and ends with the invariant the piece establishes ("the hold and the order commit together or not at all").
- **Explain what the diff can't show:** the why, the flow across files, the invariant. Don't narrate a hunk line by line: a line note says what one line does, in a few words.
- **Teach the ask in the reader's words:** a criterion becomes a case with toy values, not a restated sentence.
- **Heading (`heading`):** the change as a short narrative, e.g. "Checkout now holds the last unit when the order is placed". Never the PR title.

### The first screen: lead, Start here, the map, the carry list

These replace any summary or overview. The lead (`glance`) says the change in one sentence; the map shows it; the carry list holds what a reviewer must keep in mind; Start here sends the reader through the pieces to the quiz. Nothing else sits at the root: the tests, the harness, deploy and merge notes, the files, the trace and the sources live under Go deeper, and so do the untested paths.

### One wording per thing

Every word the page uses for itself is a contract:
- **Words the check fails in visible text** (code spans and chips aside): "chapter" in any form (in a repo whose files use the word, put it in `code`), "Ch 2", "piece 2", a goal id (`goal.x`), a `name.ext:NN` location.
- **A piece is cited by badge and name,** never "piece 2", "the second piece" or "chapter 2": a link `<a href="#ch-2">` in a fragment, `[the release job](#ch-3)` in a `plan.json` text field. Circled numbers belong to pieces only: no ① for steps, headings or quiz numbers.
- **A reference to a section is a link that uses that section's heading words:** "see <a href="#asked">What was asked</a>". The check fails these phrases anywhere in the page's text unless they are a link to their section (or sit inside it): "the map", "what to carry", "To carry into the review", "Check yourself", "What was asked", "All N files" (with the right N), "Read piece(s)". In a fragment write the `<a>`; in a `plan.json` text field (the lead, the map's words, carry lines, notes, open questions) write `[What was asked](#asked)`. Avoid "the map" as a common noun too ("the lookup table", not "the map of codes"). Never "above", "below" or "the appendix" without the link.
- **One name per counter and per action,** as the page says them: piece, the N pieces, Start here, The map, To carry into the review, Check yourself, Go deeper, What was asked, Sources, All N files, Generated files, More on this, Files in this piece, I've read this piece, Viewed n/N files, First try n/N, Practice reset, Reset quiz, Reset reading progress, Explain your misses to Claude.
- **An instruction says where and how.** Never assume the reader knows the skill's workflow: not "in chat" but "in a Claude Code session running `/skunexus-understand ABC-123`"; not "run the tests" but "run `composer test -- --filter=Release` in the repo root".
- **A file name opens that file** in "All N files"; GitHub is always a separate "↗" link.

### Lengths and the size rule

**The root is constant; depth scales.** The first screen stays the same size whatever the diff: a bigger change adds pieces, Go-deeper rows and files, not root words. The check counts the **authored** words above the pieces (the h1, the lead, the map, the carry list), with closed sections, code and the file tree left out, and fails past **480**. Start here, the strip, the piece index and the Next lines are generated and counted apart. A rule-shaped map of 6 boxes with 4 carry lines sits near 400.

The other lengths count visible words: outside code, closed toggles and chips. They are targets; the check warns (never fails) on a main-flow note over 120, a piece over 450, a gist over 30, What was asked over 600 (900) and Background over 300:
- **the lead:** one sentence, at most about 35 words;
- **a piece's note:** at most ~120 words before `<!--more-->`; the whole piece 150–450;
- **a deep piece:** 150–400, plus a `gist` of at most 30 words;
- **a carry line:** one sentence; the list as short as the review needs (it counts toward the first screen);
- **the map's purpose:** one sentence; box labels 2–5 words, subs one short line;
- What was asked 300–600 (900 past 5 use cases, §3); Background at most 300 plus its closed deep layer; Intuition 200–400; How it's proven 150–400.

The check also prints the reading path's words (the root, each main-flow piece, Check yourself) and its minutes, as information only: it is not a gate.

**Thresholds the build applies** (nothing to author):
- **file filters:** the tree's filter box and the files table's search and filters appear only above 20 changed files (`build --filter-at <N>`, default 20);
- **the trace table:** only at 4 or more trace rows, or when any row is not `tested`; otherwise one status line in What was asked.

### Less text: what goes where

- **Open in the main flow:** the lead, the map, the carry list (the non-goals included), each main-flow piece's note and deciding hunk, the quiz.
- **Under "More on this":** the scenario, the rest of the walkthrough, the toy example, callouts, the invariant, the files and the proof line.
- **Under Go deeper:** What was asked, the problem and the before/after table, Background, Intuition, the trace, drift, the deep pieces, How it's proven, Where to look hardest, deploy and merge notes, Generated files, All N files, Sources.
- **In a closed `details.toggle`:** the deep layer of Background, per-workflow detail past the first walk, a second example, long tables, edge cases already covered by a test, the "why not" of a rejected option when a decision callout names it.
- **Say each thing once.**
  - Skip "What must hold" in `asked.html` when the trace has only `goal.` rows: "The goals and their state" lists them.
  - Background shows the base state only; the code paths that change belong to the pieces.
  - No `verified` callout when the piece's proof line already names that test.
  - "What ran" lives only in `proven.html`.
  - A fragment never repeats the `gist`: the build renders it on a deep piece.

### Write for the reader, not the log

A reader getting up to speed knows none of the ticket's labels. **Name the thing, never just its label.** This is the quiz's rule (`quiz.md` §4) applied to every text a reader sees: the fragments, and in `plan.json` the lead, the map's words, carry lines, hotspot reasons, drift and ops notes, open questions, piece titles and short names, the glossary, trace texts, the `behaviour` table, `not_in_change` and mechanical intents.
- **A commit** is named by what it did: "the PR's last commit, which fixes the release window at 30 minutes", or "the commit that retired the old job". Its hash appears only in a ref chip's preview, `evidence` or `evidence_note`.
- **A location** (`file:line`) never sits in a sentence. Name the file, class or rule in words and attach a `file:` chip; the chip's preview carries the path, the line and the quoted code.
- **An id** (R5, FB23, Q19, s1.5, D2, T3, AC4) never stands alone as the subject. Lead with what it means ("the open ruling on whether a store sets its own window") and attach the id as a chip. A trace row, or a list item that is the id's own entry, is fine. A plain-text `plan.json` field can't hold a chip, so leave the id out there: the fragment that covers the point carries the chip; a drift's or an op's id goes in its `ref`, a non-goal's in its `ref`.
- **Another ticket's key** never sits in a sentence: "the ticket that added backorders", with the key in a chip (`label`).
- **Never the page's own history:** rebuilds, rounds, what this version added ("Rebuilt at the same head: adds What was asked"). That belongs in `artifact.md` and the hand-off.
- **Open questions** are phrased for the author in plain words. Their text carries no "(ch-3)" or "(asked)" prefix: the leading tag of a `plan.json` entry is routing, and the build strips it and renders the link (§10).

One carry line from the toy ticket ABC-123, before and after:

> **Before:** "Since 4e7a9c2, `ReleaseExpiredReservations.php:18` releases unpaid holds after a fixed 30 minutes, and FB12 is open."
>
> **After:** "The release window is a fixed 30 minutes; whether a store may set its own is still an open ruling."

The piece that covers the point carries the labels as chips:
```html
<p>The release job now waits a fixed 30 minutes <span class="ref" data-ref="file:src/Inventory/ReleaseExpiredReservations.php:18">ReleaseExpiredReservations.php</span>. Whether a store may set its own window is still an open ruling <span class="ref" data-ref="FB12">FB12</span>.</p>
```

### One toy world: `plan.json` `toy`

A reader who meets order #1001 unpaid in the Intuition and paid in a quiz stem learns nothing and starts to doubt the page. So the page has one toy world, written once, in `plan.json` `toy`: a short text block naming each toy record, its values, and the history the page walks.
```json
"toy": "MUG-1: on_hand 10. Order #1001: 2 × MUG-1, placed 10:00, never paid. Order #1002: 3 × MUG-1, placed 10:05, paid 10:06. Window 30 min; the release job runs at 10:31 and releases #1001's hold: available 5 → 7. Contract v1 → v2: v2 decides Q2, changes s1.2, adds R1.c."
```
- Write it before the Intuition. Every fragment, every map box and every quiz stem uses its names and values; add a value to `toy` before any section uses it.
- A question or callout that needs another history names another record: "a different order, #1004, …", or for a ticket world, "a different ticket, TOY-8, …". Never give a toy record a second history.
- Re-read the toy's claims against their sources before fan-out: the piece brief copies `toy` verbatim, so one wrong value spreads to every piece.
- The fact-checker checks every fragment and stem against it (verify brief item 13).

## 14. `plan.json`

You own it. The build and the check read it. A toy example (ABC-123, reserve stock at placement; a job releases unpaid holds after 30 minutes):

```json
{
  "title": "ABC-123 Stock Reservations",
  "heading": "Checkout now holds the last unit when the order is placed",
  "glance": "Checkout holds an order's stock the moment it is placed. A job gives an unpaid order's units back after 30 minutes; a paid order keeps them until it ships.",
  "ticket": "ABC-123", "mode": "author", "stage": "full", "branch": "ABC-123",
  "contract": {"version": "v2", "status": "Approved",
               "storyboard": {"url": "https://claude.ai/…", "built_from": "contract v2 (2026-11-03)"}},
  "toy": "MUG-1: on_hand 10. Order #1001: 2 × MUG-1, placed 10:00, never paid. Order #1002: 3 × MUG-1, placed 10:05, paid 10:06. …",
  "problem": "Two checkouts a minute apart could both sell the last unit, because stock was held only when the payment arrived.",
  "problem_ref": {"ref": "jira.oversell"},
  "behaviour": {"cols": ["Next, for one unit of MUG-1", "Before", "After"],
                "rows": [["A second checkout asks for it", "Sold twice", "Backordered"],
                         ["The first order is never paid", "Stays sold", "Back in stock after 30 minutes"],
                         ["The first order is paid", "Held", "Held"]]},
  "map": {"purpose": "Two places decide whether a unit is free. Each now asks one rule. Read it in order: who decides, the rule they ask, what the unit does.",
          "entries_h": "Who decides · changed to ask", "rule_h": "The rule they ask", "outcomes_h": "What the unit does",
          "entries": [
            {"label": "Checkout", "sub": "places an order · holds each line at once", "kind": "changed", "target": "ch-2"},
            {"label": "The release job", "sub": "every minute · gives unpaid holds back", "kind": "changed", "target": "ch-3"},
            {"label": "A manual stock count", "sub": "still writes on_hand directly", "kind": "not asked", "target": "carry-bypasses-1"}],
          "rule": {"title": "A unit stays held while", "target": "ch-1",
                   "conditions": [{"text": "an order line holds it"}, {"text": "its order is paid"},
                                  {"text": "or the hold is under 30 minutes old"},
                                  {"text": "a cancelled order holds nothing", "exception": true}],
                   "sub": "one hold row per order line, unique by line"},
          "outcomes": [
            {"label": "stays held", "sub": "until the order ships", "goal": "R1.a", "target": "ch-4"},
            {"label": "comes back to stock", "sub": "30 minutes after an unpaid order", "goal": "R3.a", "target": "ch-4"}]},
  "not_in_change": [{"text": "No customer email when a hold is released", "ref": "ng.email"}],
  "hotspots": [
    {"at": "src/Inventory/AvailableQty.php:12-20", "carry": "inherits",
     "why": "Every caller of `availableQty` now subtracts holds, the storefront's stock badge included."},
    {"carry": "bypasses", "why": "A manual stock count writes `on_hand` directly and ignores holds (inferred from code)."},
    {"at": "src/Inventory/ReleaseExpiredReservations.php:40-52",
     "why": "Untested boundary: an order paid exactly at the end of the window."}
  ],
  "chapters": [
    {"id": "ch-1", "title": "A hold per order line", "short": "the hold",
     "why_here": "Every later piece reads or writes this row.",
     "files": ["database/migrations/*_create_stock_reservation.php", "src/Inventory/Reservation.php"],
     "gist": "Each order line holds its units in one row, so a retried message cannot hold them twice.",
     "read": "must", "risk": "med", "evidence": "covered",
     "evidence_note": "ReservationTest covers the unique key; not run here.",
     "proof": "Proven by the reservation test:",
     "checks": ["A retried reserve message for the same order line writes one hold, not two."]},
    {"id": "ch-4", "title": "The tests and what they prove", "short": "the tests",
     "why_here": "After the code it proves: one test per path.", "files": ["tests/Inventory/*"],
     "gist": "One test per path: placing, releasing, and a paid order kept.",
     "read": "skim", "risk": "low", "evidence": "covered", "evidence_note": "Read from the test files; not run here."}
  ],
  "deeper": [
    {"summary": "What was asked", "holds": ["asked", "problem", "background", "intuition", "trace", "drift"]},
    {"piece": "ch-4", "holds": ["ch-4", "proven", "look"]},
    {"piece": "ch-5", "holds": ["ch-5", "ops"]},
    {"summary": "Generated files", "holds": ["ch-mech"]}
  ],
  "mechanical": [
    {"title": "Lockfile", "files": ["composer.lock"],
     "intent": "One package added for the scheduler.",
     "check": "Only the scheduler package and its two dependencies change in `composer.lock`."}
  ],
  "trace": [
    {"id": "R1.a", "text": "Placing an order holds its quantity at once",
     "built": ["ch-1", "ch-2"], "proven": ["spec.reserve-on-place"], "state": "built", "note": ""}
  ],
  "refs": {
    "D2": {"title": "Reserve at placement", "src": ".ai/ABC-123/decisions.md", "origin": "author-decisions",
           "text": "Reserve stock when the order is placed, not when payment is captured."},
    "jira.oversell": {"title": "The oversell report", "src": ".ai/ABC-123/explainer/sources/jira-ABC-123.md",
                      "origin": "jira-desc", "text": "Two customers bought the last MUG-1 within a minute."}
  },
  "origins": {
    "jira-desc": {"group": "Jira", "label": "The ticket's description",
                  "url": "https://example.atlassian.net/browse/ABC-123"},
    "jira-window": {"group": "Jira", "label": "The product owner's answer on the window (comment, 2026-11-03)",
                    "url": "https://example.atlassian.net/browse/ABC-123?focusedCommentId=10001"},
    "pr-482": {"group": "GitHub", "label": "PR #482: this change (its description)",
               "url": "https://github.com/acme/shop/pull/482"},
    "page-rootcause": {"group": "Shared pages", "label": "The oversell root-cause page",
                       "url": "https://claude.ai/artifact/toy-0001"},
    "author-decisions": {"group": "From the author", "label": "The author's decision log"}
  },
  "glossary": [
    {"term": "hold", "def": "A `stock_reservation` row: units of one product kept for one order line."}
  ],
  "open_questions": [
    "(ch-3) An order paid at exactly 10:30:00 is released by the 10:30 run. Is the boundary meant to be inclusive?"
  ],
  "drift": [
    {"at": "src/Inventory/ReleaseExpiredReservations.php:18", "ref": "T4", "needs_decision": false,
     "note": "Plan said the window comes from config; the code uses a 30-minute constant."}
  ],
  "ops": [
    {"what": "Migration: create stock_reservation", "files": ["database/migrations/*_create_stock_reservation.php"],
     "note": "Reversible: down() drops the table."},
    {"what": "Orders placed before the deploy hold nothing", "files": [], "carry": "data",
     "note": "They have no hold rows, so available stock stays overstated until they ship."}
  ],
  "sources": [".ai/ABC-123/prd.md", ".ai/ABC-123/workflows.md", ".ai/ABC-123/decisions.md",
              ".ai/ABC-123/backend-plan.md", ".ai/ABC-123/spec-from-tests.md"]
}
```

The example shows two of its five pieces: `ch-2` and `ch-3` (main flow) and `ch-5` (the scheduler wiring, `skim`) have the same fields, and `refs` holds every other id it cites (`ng.email`, `spec.reserve-on-place`, `T4`). An origin that no chip cites, like `pr-482` here, is not listed.

Text fields are plain text: `inline code` in backticks, `**bold**` in double asterisks, `[name](#ch-2)` for a piece (it renders as the piece's badge and name), `[words](#id)` for any other section or carry line the page renders (`#asked`, `#map`, `#carry-ask-1`; the check fails a link with no target). Fields not listed below are ignored by the build.

**The page's words**

| Field | Rule | When absent |
|---|---|---|
| `title` | The `<title>` and the artifact's name: 2–4 words, the key plus a subject. The same on every rebuild; the check enforces the word count | required |
| `heading` | The `<h1>`: the change as a short narrative (§13) | `title` |
| `glance` | The lead under the h1: the change in one plain sentence, what it does and for whom, no ids or labels | no lead under the h1 |
| `ticket`, `mode`, `branch` | `<KEY>`; `author` or `reviewer`; the head branch, if any. The page's wording is the same in both modes | `mode`: `author` |
| `stage` | `intent-only`, `full` or `reviewer` (`inputs.md` §2) | from `map.json` and `mode` |
| `contract` | `{version, status, storyboard}` (`inputs.md` §5), or `null` when `prd.md` has no `> Versions:` block. `storyboard` is `{url, built_from}` or absent | none shown |
| `toy` | The one toy world, as a short text block (§13). Not rendered; the piece brief copies it and the fact-checker checks against it | — |

**Under Go deeper: the problem and the before/after**

| Field | Rule | When absent |
|---|---|---|
| `problem` | 1–3 sentences: why the ticket exists, in plain words | no problem paragraph |
| `problem_ref` | `{ref, label?}`: a chip after the problem. `ref` is a `refs` id; `label`, when set, replaces the chip's text (e.g. another ticket's key, shown only in the chip) | no chip |
| `behaviour` | `{cols, rows, intro?}`: the before/after table. `rows` are `[situation, before, after]`, 2–5 of them, each a situation a reader can picture; an `after` that differs from its `before` is marked changed. `cols` are the three headings (default "What happens next", "Before", "After"); `intro`, one optional line above the table | no table. With neither `problem` nor `behaviour`, no "The problem, and what happens now" section |

**The first screen**

| Field | Rule | When absent |
|---|---|---|
| `map` | The map (§18): `purpose`, `entries_h`, `entries[]`, `rule_h`, `rule`, `arrow`, `so`, `outcomes_h`, `outcomes[]` | no map section; Start here's first step reads "Look at what to carry"; the check warns |
| `not_in_change[]` | The non-goals, each a string or `{text, ref, label?}`: one "not here" line on the carry list, items joined by " · ", each with its chip. Every `prd.md` non-goal belongs here, short, and also in `asked.html` | no "not here" line |
| `hotspots[].carry`, `drift[].carry`, `ops[].carry` | A carry tag (§19): `inherits`, `bypasses`, `ask`, `data` or `not here`. The entry moves from its Go-deeper section to the carry list. A carry hotspot may omit `at`; then its `ref` backs the line | the entry stays in Go deeper |
| `open_questions[]` | Tagged strings (§10); every one is an `ask` line on the carry list | no `ask` lines |

**Pieces and rows**

| Field | Rule | When absent |
|---|---|---|
| `chapters[]` | The pieces, in reading order. `id` is `ch-1`, `ch-2`… (`ch-[a-z0-9-]+`; never `ch-mech`); its fragment is `fragments/<id>.html`. `files` are paths or globs. `read` is `must` (main flow, filled badge) or `skim` (under Go deeper, hollow badge). `risk` is `high`, `med` or `low`; `evidence` is one state from §8, and `evidence_note` says what backs it (not rendered; the fact-checker reads it). Optional `checks`: the one fact the piece's checkpoint tests, so two questions never test the same fact. Empty when intent-only | — |
| `chapters[].title` | The piece's heading after its badge: what the piece does, a short phrase ("The release job gives unpaid holds back") | — |
| `chapters[].short` | The piece's name in every reference, after its badge: 1–3 words, lower case unless a proper name ("the release job") | `title` |
| `chapters[].proof` | The words before the proof chips at the piece's end ("Proven by the release test:") | "Proven by" |
| `chapters[].gist` | One plain sentence of at most 30 words, shown under a deep piece's heading; no hash, id or `file:line` | `why_here` |
| `chapters[].why_here` | Why the piece sits where it does (§2) | — |
| `deeper[]` | The Go-deeper rows, in order: `{summary?, holds[], piece?}`. `holds` lists the sections the row opens, first the one whose heading the row repeats: `asked`, `problem`, `background`, `intuition`, `trace`, `drift`, `proven`, `look`, `ops`, `ch-mech`, or a deep piece's id. With `piece` (a deep piece's id, also listed first in `holds`), the row's summary is that piece's badge and title. Else it is `summary`, which must equal the first held section's heading (§1); leave it out and the build uses that heading. Never hold `files` or `refs`: "All N files" and "Sources" are always the last rows. On an intent-only page, never hold `asked`: it sits in the main flow | each section gets its own row, named by its heading (pieces first, in their order) |
| `mechanical[]` | `title`, `files`, `intent` (one line), `check` (one concrete line), shown under "Generated files". Empty when intent-only | no Generated files row |

**Evidence and sources**

| Field | Rule | When absent |
|---|---|---|
| `trace[]` | One row per criterion: `id`, `text`, `built`, `proven`, `state`, `note` (§7) | no trace section, no outcome states |
| `hotspots[]` | At most 7, most important first: `at` (`PATH:START-END` at head), `why` (one line, rendered before the file's name), optional `ref` and `label` (a chip after the line, as on an op: the source that backs it; `label` replaces the chip's text), optional `carry`. Empty when intent-only | no "Where to look hardest" |
| `drift[]` | `at` (`PATH:LINE` or `PATH:START-END` at head, an unchanged file included (§9); between two artifacts, the artifact's path), `note` (both sides, one line), `ref` (the plan, decision, criterion or step id), `needs_decision` (`true` against a PRD criterion or a contract step), optional `carry` (§9) | — |
| `ops[]` | `what`, `files`, `note`, optional `ref` and `label` (a chip after the note; `label` replaces the chip's text), optional `carry` (§9) | — |
| `refs` | Every id a fragment, a trace row or a field above cites, except `file:PATH:LINE` refs, which need no entry: the build quotes that line at head. Each entry has `title`, `src` (a repo-relative path, a URL, or `commit <sha7>`), `text` (the verbatim quote; a marked paraphrase only for a PR or Jira comment) and `origin` (an `origins` id: where a reader opens it). The build names the kind from the id prefix (`R4` requirement, `R4.b` or `AC3` criterion, `D`, `T`, `Q`, `A`, `FB`, `s1.3`, `spec.<slug>` test scenario, `ng.<slug>` non-goal, `goal.<slug>` goal stated by a PR body, Jira or the ticket's own notes); any other id, such as `pr.<slug>`, `jira.<slug>`, `commit:` or `ans.<slug>`, shows as a source. `text` is any contiguous excerpt of `src`, at least 12 characters, with no personal names. A `commit:<sha>` ref takes its title from git and, with a GitHub remote and no `origin`, a GitHub origin of its own. Provenance rules: `inputs.md` §6 | — |
| `origins` | `{id: {group, label, url?}}`: the Sources list, one entry per origin a chip cites (below). Ids are `[A-Za-z0-9_-]+` (else the build exits 2) | a cited ref with no known `origin` is a build error; a `group` left out is "Other" |
| `glossary[]` | `term`, `def` (one line), shown under Sources | no Glossary |
| `sources[]` | Each source file read, as a repo-relative path. The build hashes each into the page data; the page names them only by count, split by whether a reader can open them: a source that a ref quotes (its `src`) and whose origin has a `url` is online, any other is a local note ("1 local note, not online · 2 online") | — |

`summary` and `reading` are no longer rendered: the lead, Start here and the map replace them. An older plan's are ignored.

### `origins`: the Sources list

The Sources row lists only what a reader can open, one entry per origin, grouped under h4s in this order: **Jira**, **GitHub**, **Shared pages**, **From the author**, then any other group, then the Glossary. Each entry ends with "Cited in:" links back to every chip that cites it. Code (`file:`) chips are never listed: they open the file instead.
- **`group`:** where it lives. `Jira` (a ticket field or comment), `GitHub` (a PR, its description or comments, a commit, a file at the head), `Shared pages` (a published page, below), `From the author` (a note that exists only on the author's machine).
- **`label`:** the reader-facing name, by what it is: "The product owner's decision on the window (comment, 2026-11-03)", "PR #482: this change (its description)", "The oversell root-cause page". A role, never a person's name; a date when the source has one. **Never a path.**
- **`url`:** only for a source a reader can open: a Jira comment's `focusedCommentId` link, a PR, a commit, a published page. The build makes it a link that opens a new tab. A "From the author" entry has no `url`.
- **A local note cites its online twin.** Before you file a note under "From the author", look for the place it came from or went to: the Jira comment it quotes, the PR description it drafted, or a page it was published as. A note published as a claude.ai page is a **Shared pages** entry with that page's link: grep the ticket folder for `claude.ai/artifact` and `claude.ai/code/artifact` (an `artifact.md`, a handoff or a README line records the URL). Only a note with no online twin stays "From the author", named in words.
- `refs[].src` keeps the local path, so the check can confirm the quote; `refs[].origin` says where a reader opens it. The page never shows the path: not in text, not in a tooltip, not in a label.

## 15. Fan-out

In this thread by default. Offer fan-out for a large diff, saying the real durations: piece writers run in parallel, about 5–10 minutes each; the fact-check takes about 5–10 minutes; the blind and teach checks 1–3 minutes each. Run it only on the developer's yes. Agent types: `SKILL.md` "Roles". An intent-only page never fans out.

1. **First, yourself:**
   - `map.json`; the complete `plan.json` (pieces with their `short` names, files, order and `read`; `glance`; the map; the carry tags; `not_in_change`; `deeper`; the trace rows with their ids and texts; the refs, origins, glossary, open questions and drift known so far); `asked.html`, `background.html` and `intuition.html`, because they need the whole picture.
   - The key sequence for every quiz question, in page order: each piece's checkpoints in piece order, then the finals. Write it by hand to the rules in `quiz.md` §5 (for 12: `cadbdcbacabd`), so each writer gets its slots. The checker prints a valid sequence only when positions fail.
   - The near-move pairs `map` didn't pair (`map.json` `pred`, §4), for the briefs.
   - `plan.json` `toy` (§13), re-read against its sources: every brief copies it.
   - Each piece's `checks`: the one fact its checkpoint tests, all different across pieces and the finals you plan.
   - **The pre-fan-out check:** `check-explainer.py <DIR>` (with any `--forbid`). Before the fragments exist it exits 1, and the expected errors are only these: one `fragments/ch-<n>.html is missing` per piece, a missing `proven.html` when the Proven layer exists, the quiz schema error, and `explainer.html is missing`. Fix any other error (plan, coverage, trace, marker, ref, origin, safety, forbid) before you spawn. A passing ref check prints no line.
2. **One brief per piece.** Copy `<SKILL>/assets/briefs/piece-brief.md` to `<DIR>/briefs/ch-<n>-brief.md` and fill its placeholders. Writers reuse a ref id when `refs` already quotes the same text, and name new ids in the namespaces `pr.<slug>`, `jira.<slug>`, `spec.<slug>`, `ng.<slug>` and `goal.<slug>`, each with an `origin`.
3. **Spawn** one fresh piece writer per piece, all in one message: "Read `<DIR>/briefs/ch-<n>-brief.md` and do it."
4. **Each writer owns two files,** `fragments/ch-<n>.html` and `quiz-parts/ch-<n>.json`, keeps a `<!-- STATE HH:MM … -->` line at the top of its fragment until done, and replies in at most 15 lines.
5. **Wait for each completion notice** before reading a writer's files. Resume a stopped writer with SendMessage while it has been idle under about 5 minutes; after that, start a fresh one pointed at its brief and its own files.
6. **Merge:** the checkpoint questions from `quiz-parts/` into `quiz.json`; their `refs`, `origins`, `open_questions`, `drift` and `proposals` (evidence state, gist, proof line, hotspots and their carry tags, glossary terms, ops, trace, map boxes) into `plan.json`, keeping one name per concept. Dedupe refs by text: two ids with the same `src` and `text` become one. One id with two texts from two writers: rename one and fix the fragment that cites it. Add each toy value a writer reports to `toy`, and check it against the rest. A trace proposal adds to a row's `built` and `proven`; you set the state, from the whole row. A proposed map box joins the map only with the code marker or chip it names. Then write `proven.html` and the final questions yourself, build and check; the check fails on a STATE comment left in a fragment.

## 16. Verification

The depth is `light` or `full`, stated in step 3's echo and recorded in `artifact.md`'s Checks cell, so a resume reads it instead of guessing.
- **`light`** (the default when the diff has ≤ 400 read-tier changed lines and ≤ 4 pieces, and for an intent-only page with at most 8 criteria and an `asked.html` of at most 700 words): steps 1, 2, the blind guesser, 5 and 6.
- **`full`** (otherwise, or when the developer asks): every step. On an intent-only page the fact-checker covers `asked.html` and `background.html` (the verify brief says which items).

In this order:
1. **The check** (free, deterministic): `check-explainer.py <DIR>`. Fix every error.
2. **Key verification** (you): re-read each quiz key's `evidence` at `<HEAD>`, or in its source file for an intent question. A wrong key teaches the bug. Run the outsider self-test on every question (`quiz.md` §4). Re-read each trace row's state against its rule (§7), and each map box and carry line against the marker or chip behind it (§18, §19).
3. **Fact-check** (`full`): copy `<SKILL>/assets/briefs/verify-brief.md` to `<DIR>/briefs/verify-brief.md`, fill it, and give a fresh fact-checker: "Read `<DIR>/briefs/verify-brief.md` and do section A." It checks the pieces against the code, the map and the carry list against the pieces, `asked.html` against the Asked sources, `proven.html` and the trace against the tests, and the Sources against their origins, and writes `review/fact-check.md`. Let it finish, and apply its quiz rows (step 5), before the first blind round: a stem or key it corrects after the blind rounds can't be re-run blind under the two-round cap.
4. **Blind guesser,** before the teach reader, two rounds at most (`quiz.md` §7); then (`full`) the **teachability reader:** sections B and C of the same brief (`quiz.md` §8). Re-fill the brief from the asset on every rebuild.
5. **Apply.** Re-check every `wrong` verdict against its source yourself before changing anything: reviewers can be wrong too, and evidence settles it, not a vote. An `unverifiable` claim is reworded as inferred (and the piece's state lowered), or dropped.
6. **Re-run what the edit touched:** a quiz edit → the check, and a blind round if the two-round cap allows (else name the edited questions as not re-run blind in the hand-off); a page edit → the teach reader (`full`); a changed claim → the fact-checker on those ids only (SendMessage while it is warm).

## 17. Click-through (optional)

Text only, with the `chrome-devtools` MCP server. Load the tools with `ToolSearch` `select:mcp__chrome-devtools__new_page,mcp__chrome-devtools__evaluate_script,mcp__chrome-devtools__list_console_messages,mcp__chrome-devtools__emulate,mcp__chrome-devtools__take_snapshot,mcp__chrome-devtools__close_page`.
- Open a new tab on `file://<abs path>/explainer.local.html` (WSL with Chrome on Windows: `file://wsl.localhost/$WSL_DISTRO_NAME<abs path>`).
- Size with `emulate` (`viewport` `1440x900x1`, `1280x800x1`, `390x844x3,mobile,touch`), never by resizing a shared window.
- In `evaluate_script`, collect: `document.compatMode` is `CSS1Compat`; every `a[href^="#"]` target exists; no `pre[data-hunk]` or `pre[data-code]` is left empty; no `a a` nesting; `document.documentElement.scrollWidth <= visualViewport.width` at each size, collapsed and after "Expand all". Compare with `visualViewport.width`, never `innerWidth`: on a phone one unbreakable string widens the layout viewport, so `innerWidth` grows with the page and the test passes falsely.
- Count words as a reader sees them: exclude `details:not([open]) > :not(summary)`, and scan text node by node (joined text makes false hits). Text checks miss CSS `::before` content.
- The first screen: the top of `#start` is within `innerHeight` at 1440 and 390. Repeat with `document.documentElement.style.fontSize` at `12px` and `20px` (browsers' small and large defaults): a regular `main h3` stays larger than the body text, and nothing visible is smaller than 1rem except the strip's digits.
- On the phone size: "Files" opens the tree drawer and Esc closes it; a strip tile's first tap opens its card without navigating.
- A local `file://` page has no runtime: the saved result and Reset quiz's wipe of it work only on the published page.
- A published page: opening a new tab on its claude.ai URL drops it from the server's targets. Use a tab that is already open on it, take a snapshot, and pass a uid from inside the "User-generated artifact content" frame as `evaluate_script`'s `args`, so the script runs inside the frame.
- `list_console_messages`: no errors.
- Snapshots go to files under `<DIR>/review/` (`filePath`), and you grep them. Never take or view a screenshot: images bloat the context; work from text.
- **Never click a quiz option, Practice reset or either reset in Options.** The first pick is stored in that browser and locks the question for the developer.
- Never follow a storyboard link or a Shared pages link: they open other artifacts.
- Close your tab. No browser, or it times out: rely on the check and report "unclicked".

## 18. The map

The map shows the change as a picture on the first screen. It is per-ticket authoring, and the most expensive part of the plan: write it after the pieces are settled.

**Never invent a box.** Every box links to a piece, a carry line or a named section, and every word in it is backed by a code marker or a chip in that target. A box you can't back is a box you leave out.

### Three shapes

| Shape | When | Columns |
|---|---|---|
| **Rule-shaped** (`map.rule` set) | The change is one rule that several places now ask: entry points → a rule with conditions → outcomes | 3: who decides (entries) → the rule → what happens (outcomes), joined by the `arrow` and `so` connectors |
| **Flow-shaped** (`map.rule` absent) | No single rule: a flow, or a set of changed entry points each leading somewhere ("what changed, where") | 2: entries → outcomes, joined by the `arrow` connector |
| **No map** (`map` absent) | Nothing a picture would add: a one-file fix, a rename sweep | none: Start here's first step reads "Look at what to carry", and the check warns |

On an intent-only page, draw the map from the contract's workflow: the actors or entry points the workflow names → the rule the contract states (rule-shaped), or straight to the outcomes (flow-shaped) → the outcomes, each tied to a criterion in `goal`. With no pieces, a box targets a section (`asked`, `background`, `intuition`, `trace`) or a carry line.

### Fields

| Field | Rule | Default |
|---|---|---|
| `purpose` | One sentence under the h2: what the picture shows and how to read it, in order. Direction-neutral (the map stacks on a phone): "Read it in order: who decides, the rule they ask, what the unit does", never "left to right" | none |
| `entries_h`, `rule_h`, `outcomes_h` | The column headings. Text after " · " shows as a small sub-heading ("Who decides · changed to ask") | "Who decides" (flow-shaped: "What changed"), "The rule", "What happens" |
| `entries[]` | `{label, sub, kind, target}`. `kind: "changed"` (a box in the first column) or `"not asked"` (a place that goes around the change, listed under the columns: "One place doesn't ask ① the hold:" on a rule-shaped map, "Two places stay out of it:" on a flow-shaped one). Point a "not asked" entry at its carry line (`carry-<tag>-<n>`, §19), so the line "… in To carry into the review ↓" appears | — |
| `rule` | `{title, conditions[], sub, target, new?}`: the rule's name ("A unit stays held while"), its conditions as `{text, exception?}` chips (an `exception: true` chip is the case where the rule doesn't apply), one `sub` line, and its target. `new: false` drops the "new" mark when the rule existed before this change | absent: the flow shape. `new`: `true` |
| `arrow`, `so` | The connector words: entries → rule (or entries → outcomes on a flow-shaped map), rule → outcomes | "ask" (flow-shaped: "then"), "so" |
| `outcomes[]` | `{label, sub, goal?, target}`: what happens, tied to a trace row in `goal` (the build adds its state and test count, "tested, 2 tests"), and its target | `goal`: no state tag. A `goal` that is no trace id is a build error |

**Targets.** Every box's `target` is a piece id (the box shows its badge and the whole box is the link), a carry line id (`carry-<tag>-<n>`), or a section the page renders (`asked`, `background`, `intuition`, `proven`, `problem`, `trace`, `look`, `drift`, `ops`, `ch-mech`, `files`, `carry`, `quiz`, `deeper`, `refs`). Prefer a piece: the map is the way into the pieces. Any other target is a build error.

Labels are 2–5 words in the glossary's names; a `sub` is one short line. Box text is plain: no ids, hashes or `file:line`. The legend under the map lists only what the map shows (a filled or hollow badge, "new", the "tested" tag, the dashed "doesn't ask the rule" or "stays out of it").

A flow-shaped map, for a different toy ticket (TOY-8: the product import gains a dry run):
```json
"map": {"purpose": "Two commands changed. Read each from the command to what it now does.",
        "entries_h": "What changed", "outcomes_h": "What it does now", "arrow": "now",
        "entries": [
          {"label": "The import command", "sub": "gains a dry-run option", "kind": "changed", "target": "ch-1"},
          {"label": "The import report", "sub": "lists what a run would write", "kind": "changed", "target": "ch-2"}],
        "outcomes": [
          {"label": "nothing is written", "sub": "on a dry run", "goal": "goal.dry-run", "target": "ch-1"},
          {"label": "the report shows every row", "sub": "with its planned change", "goal": "goal.report", "target": "ch-3"}]}
```

## 19. To carry into the review

The carry list (`#carry`, an h2 "To carry into the review") holds what a reviewer must keep in mind that no single piece shows: a consequence that reaches beyond the diff, a path around the change, a question for the author, existing data, and what the change leaves out. Each line is one tagged sentence ending in its pieces as badge links.

| Tag | Means (the page's own tooltip) | From |
|---|---|---|
| `inherits` | Other code gets this behaviour too | a hotspot or drift with `carry: "inherits"` |
| `bypasses` | A path that goes around the change | a hotspot or drift with `carry: "bypasses"` |
| `ask` | A question for the author | every `open_questions` entry, and any entry with `carry: "ask"` |
| `data` | Existing data the change leaves as it is | an `ops` entry (or hotspot) with `carry: "data"` |
| `not here` | Not part of this change | `not_in_change`: one line holding every non-goal |

- **Order and ids.** Lines render in this order: hotspots, drift, open questions, ops, then the "not here" line. Each line's id is `carry-<tag>-<n>`, numbered per tag in that order (`carry-bypasses-1`, `carry-ask-2`, `carry-not-here-1`). A map's "not asked" entry targets one of these ids.
- **What stays off it:** untested paths and deploy notes. They live in Go deeper ("How it's proven", "Deploy and merge notes"); the carry list is for the review, not the release.
- **Keep it short.** One sentence a line; the list counts toward the first screen's budget (§13).
- **Every line is backed:** a hotspot's `at` or `ref`, a drift's or an op's `ref`, a chip, or the words "(inferred from code)". A line about code outside the diff has no `at`: give its hotspot a `ref`, the note that says so, and the build renders it as the line's chip.
- The list ends with "Next: ① … ↓" to the first piece.
