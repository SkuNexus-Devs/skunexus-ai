# Task-agent briefing — fill every <…> slot, then spawn as a `general-purpose` agent

<!-- Orchestrator notes (do not include in the spawned prompt):
     · One task per agent. The task entry goes in VERBATIM — the plan wrote it to be executable alone;
       paraphrasing it re-introduces the ambiguity the planning skill spent its whole run removing.
     · "Dependency code to read" is how self-containment works at run time: the agent reads the real code
       its depends_on tasks produced, never another task's plan entry.
     · Keep the Rules and Report sections intact — the report is what you (the orchestrator) verify,
       record into backend-plan.md, and commit against. -->

You are implementing ONE task of an approved backend implementation plan in a SkuNexus client repository.

- **Repository:** <absolute repo path>
- **Branch:** <branch> (already checked out — do not switch branches)
- **Ticket:** <TICKET> — <title>

## Your task (verbatim from `.ai/<TICKET>/backend-plan.md`)

<paste the FULL task entry: `### Tn — title`, the Status/Depends on/Satisfies header lines, every `- [ ]`
step, and the Out of scope / Sanity-check now trailers>

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
- Do NOT: edit anything under `.ai/`, commit, write tests or documentation (unless a step explicitly asks),
  or touch another task's files.
- Do NOT run environment verification (migrations, tinker, endpoints) — the developer runs those. Restate
  the task's **Sanity-check now** items in your report for them; don't execute them.

## Report (your final message — it is machine-consumed by the orchestrator, not shown to a human)

Return exactly these five sections:

1. **Steps** — one line per checkbox step, in order: `done` / `deviated` / `blocked`. For `deviated`: what
   you did instead and why. For `blocked`: what stopped you.
2. **Files** — every file created or edited (full paths).
3. **Sanity checks for the developer** — restate the task's `Sanity-check now` items (the developer runs
   them). Add any static/code-level confidence and known gaps. Do not run them or claim they passed.
4. **Decision candidates** — real forks you resolved whose rationale the code won't reveal (or "none").
5. **Contract flags** — anything suggesting a requirement is wrong, missing, or contradicted by reality
   (or "none").
