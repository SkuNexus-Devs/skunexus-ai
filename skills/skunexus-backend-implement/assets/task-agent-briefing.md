# Task-agent briefing — fill every <…> slot, then spawn as a `general-purpose` agent

<!-- Orchestrator notes (do not include in the spawned prompt):
     · One task per agent. The task entry goes in VERBATIM — the plan wrote it to be executable alone;
       paraphrasing it re-introduces the ambiguity the planning skill spent its whole run removing.
     · "Dependency code to read" is how self-containment works at run time: the agent reads the real code
       its depends_on tasks produced, never another task's plan entry.
     · Keep the Rules and Report sections intact — the report is what you (the orchestrator) verify,
       record into backend-plan.md, and commit against. -->

You are implementing ONE task of an approved backend implementation plan in a SkuNexus client repository.

- **Repository:** <absolute repo path — the agent's own worktree when isolation is on; if `vendor/` is missing,
  run `composer install` there first — through the PHP runner below, like every other command>
- **Branch:** <branch> (already checked out — do not switch branches)
- **Ticket:** <TICKET> — <title>
- **Testing mode:** <hybrid | full post-facto>
- **PHP runner:** <exact prefix every `php` / `composer` / `vendor/bin/*` command takes — e.g. `docker compose
  exec app`, `sail`, or "host PHP" — resolved by the orchestrator; never run a host-style command without it>
- **Test baseline:** <"clean", or the tests already red before this run — copied from the plan's
  `> Test baseline` line. A red on this list is not yours>

## Your task (verbatim from `.ai/<TICKET>/backend-plan.md`)

<paste the FULL task entry: `### Tn — title`, the Status/Depends on/Satisfies header lines, every `- [ ]`
step, and the Out of scope / Sanity-check now / Tests trailers>

## Context (read-only)

- **Contract:** <`.ai/<TICKET>/prd.md`, or "inline — the plan's Goal & Acceptance, quoted here: …">. Your
  task satisfies: <quote the exact Rn/An requirement text>.
- **Binding decisions:** <paste the relevant `decisions.md` entries (or "none") — these record forks already
  settled with the developer; do not re-open them>.
- **Dependency code to read first:** <per depends_on task: the key files/classes it produced, from its
  report>. The live code — not any plan text — is the source of truth for exact signatures.
- If you hit platform machinery you don't understand, consult the `skunexus-docs-c7` skill (Context7 docs
  for the SkuNexus platform) before improvising.

## Rules

- Work the checkbox steps **in order**. The entry is this detailed on purpose — implement it, don't redesign
  it. If reality contradicts a step (a signature differs, a file moved, a named pattern doesn't exist), do
  the right thing in code and record the deviation in your report — never silently drift on scope or
  approach.
- The task's **Out of scope** line is binding. Do not fix, refactor, or "improve" code outside your task,
  even code that clearly deserves it — note it in your report instead.
- Match the surrounding code exactly: naming, structure, error handling, comment density (which in this
  codebase is *low*). Mirror the precedent files each step names.
- **Never reference artifact sections in code.** No `T3`, `D5`, `R19`, `OQ7`, "per the plan", or dated
  "verified …" notes in comments, docblocks, or names — that coupling is noise to a reader in the editor and
  rots when artifacts renumber. Comment only what the code cannot say itself, in plain domain language; put
  step rationale in your report, not the code.
- **Tests — per the Testing mode above.** In **full post-facto**, or when your task carries no `Tests:`
  trailer, the tests prohibition below stands as written. In **hybrid**: once your steps land, discharge the
  task's `Tests:` trailer: invoke the `skunexus-behavior-testing` skill first (the Skill tool — it names its
  own base directory), then read the style guide matching the repo's syntax under that directory
  (`references/pest-style-guide.md` for Pest, `references/phpunit-style-guide.md` for PHPUnit) BEFORE writing
  any test code. The trailer cites requirement IDs, not text: read each cited `Rn`/`An`'s **current** wording
  in the contract above and name the test from that sentence (subject–verb–outcome; a Given/When/Then
  sentence is the body's skeleton and its *then* clause is the name). Then run the file/group you wrote,
  through the PHP runner above. Never claim green without a run. A
  trailer that is out-of-suite (HTTP-level or cross-process per the layer map) or wrong against the real code
  gets flagged in your report, not ground on.
- **Shared test vocabulary is read-only for you.** Use the words already in `tests/Behavior/` freely, but
  never edit `{Domain}ScenarioTrait` / `{Domain}AssertionsTrait` / `DomainAssertionsTrait` — other agents are
  writing tests in this domain right now. A new word your test needs stays local to your test file (PHPUnit:
  a private `given*`/`assert*` method; Pest: an inline `given(fn)` delta or the namespaced file-level
  `givenX()` fallback — style guide §3, ladder §9) and goes in your report as a **vocabulary candidate** naming the trait
  it belongs in. The orchestrator graduates it after the run.
- **A red test is yours to act on, never to hide.** Classify it: (a) your implementation is wrong → fix it
  within your task's files and re-run, at most three red→fix rounds; (b) the test is wrong against the real
  code → flag it (the escape hatch above); (c) the requirement it cites looks wrong → a Contract flag, and
  stop on that trailer; (d) the failure is a fatal/parse/autoload error in a file outside your task's file
  set → a neighbouring agent is mid-edit, not your red: wait a moment, re-run once, then report it as
  `environment`; (e) the test is on the **Test baseline** above → it was red before you started: not yours,
  don't fix it, don't touch it, report it as `baseline`. Never make a test pass by weakening it — no deleted
  assertion, no `markTestSkipped`, no loosened expectation — and never touch another task's file to get
  green. Still red after that → return
  with the failure output verbatim and its class; the orchestrator re-runs on a settled tree and decides.
- New tests are written in the doctrine's grammar even when the file they join holds older-shaped tests.
  Leave those alone unless your change broke them (dev guide §8) — modernising them is out of scope.
- Do NOT: edit anything under `.ai/`, commit, write tests (except as the Testing mode above allows) or
  documentation (unless a step explicitly asks), or touch another task's files.
- Do NOT run environment verification (migrations, tinker, endpoints) — the developer runs those. Restate
  the task's **Sanity-check now** items in your report for them; don't execute them.

## Report (your final message — it is machine-consumed by the orchestrator, not shown to a human)

Return exactly these sections, in order:

1. **Steps** — one line per checkbox step, in order: `done` / `deviated` / `blocked`. For `deviated`: what
   you did instead and why. For `blocked`: what stopped you.
2. **Files** — every file created or edited (full paths).
3. **Test results** (hybrid only) — the exact command you ran (runner prefix included), the test names you
   wrote per cited requirement ID, pass/fail counts, any failure output verbatim with its class
   (`implementation` / `test wrong` / `contract` / `environment` / `baseline`) and the fix rounds spent, any
   trailer you flagged instead of writing, and your **vocabulary candidates** (local helper → the trait it
   belongs in), or "none".
4. **Sanity checks for the developer** — restate the task's `Sanity-check now` items (the developer runs
   them). Add any static/code-level confidence and known gaps. Do not run them or claim they passed.
5. **Decision candidates** — real forks you resolved whose rationale the code won't reveal (or "none").
6. **Contract flags** — anything suggesting a requirement is wrong, missing, or contradicted by reality
   (or "none").
