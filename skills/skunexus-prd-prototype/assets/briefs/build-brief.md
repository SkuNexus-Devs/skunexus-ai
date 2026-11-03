<!-- Stage 9 (storyboard build, 10–20 min). Copy to .ai/<TICKET>/prototype/BUILD-BRIEF.md for each version, fill it, and give one
fresh `sn-worker` agent: "Read <path>/BUILD-BRIEF.md and do it." Extra placeholders: <SLUG>, <TITLE>, <REQ_SOURCE>, <PARTS>,
<CHANGES>, <SCENARIOS>. Standard placeholders: see SKILL.md. -->

# Build brief: <TICKET> storyboard <VERSION>

You are the build agent. Build (or revise) the storyboard: a single-file HTML page, published as a private claude.ai artifact, that walks the product owner (PO) through each workflow scenario, one recreated SkuNexus page per step, and makes it obvious at a glance what is stock SN and what <TICKET> adds. The PO reads the flow, the FE developer sizes the work per page, and the tech lead checks it; it is discussed on the daily and drives approval and the estimate.

## Read only these (keep your context lean)
1. `<REPO>/.ai/<TICKET>/prototype/sn-baseline.md`: the "before". The pages you draw must look like these.
2. The requirement source, frozen: <REQ_SOURCE>
   <!-- e.g. "`.ai/<TICKET>/review/prd-v2-<DATE>.md` §4, §5 and the §7 'Assumed' lines" or, without a PRD,
   "`.ai/<TICKET>/prototype/requirements-lite.md` (PRD-shaped: §4 `R<n>` = the ticket's Req n, §7 `Q<n>` with
   'Assumed:' lines)". -->
3. `<SKILL>/assets/storyboard-skeleton.html`: the engine. Copy it on a first build; on a revision, edit the current file.
4. Optional: the previous version (`<REPO>/.ai/<TICKET>/prototype/<SLUG>-storyboard.html`) for snippets.

Don't open `prototype/screens/` (snapshots and screenshots): they hold local customer data and are large.

## What to build
- **File:** `<REPO>/.ai/<TICKET>/prototype/<SLUG>-storyboard.html`. On a revision, first back up the current file as `<SLUG>-storyboard-v<previous>.html`.
- **Edit only the TICKET CONTENT region** of the skeleton (fake data, `PARTS`, `QT`, page builders, `SC`, `IX`, nav), plus the `<title>` (`<TITLE>`, never changes between versions), the `.pname` text (same as the title) and the `.draft` badge (`Draft <VERSION>`); set `TICKET`, `HOST`, `USER`, `QT_SRC` (the requirement source and version, e.g. 'PRD v2 §7') and `TODAY`. Leave the ENGINE region alone; if it genuinely needs a fix, make it and say so in your reply.
- **Scenarios:** <SCENARIOS>
  <!-- The scenario list the developer confirmed before capture: 3–6 end-to-end user flows of 2–7 steps, from the
  ticket's workflow or the requirement groups; who does what, in order. Optional parts go in an appendix scenario
  clearly labelled "priced option, not in base". -->
- **One step = one recreated SN page in one state:** sidebar with the active item, page header (History, H1, breadcrumb, user · role), cards, grids, modals and toasts as in `sn-baseline.md`. Keep each step uncluttered: only what that step needs. No global toggles; one page state per step.
- **Put new things where SN would:** card header actions, a new card, a grid column, a modal. Don't invent layouts SN doesn't use.
- **Markers** (fixed legend): unmarked = existing SN · `NEW(...)` green outline + tag · `CHG(...)` amber outline + tag for stock behaviour that is removed or altered · `A('Qn')` "Assumed · Qn" chip whose hover text is the §7 assumption. The key is the id §7 uses for that item: `Qn`, `Dev a` for developer decision (a), or the PRD's own decision id; the chip shows the key (`Dev a` renders as "dev (a)") · UI that no requirement asks for is labelled "proposal" in the caption.
- **Open questions are never answered by drawing.** Draw the stated default (§7 "Assumed:") and mark it `A('Qn')`. If there is no default, draw the simplest option, mark it, and list it under "ambiguous to draw".
- **Caption per step:** "What's new here" bullets, each ending in its R-ids, plus one "Today in SN" line taken from `sn-baseline.md`.
- **Before/after index tab:** one row per stock SN page the flow uses: name, path, jump buttons to the steps, a change list with R-ids, and two panes "STOCK SN TODAY" | "<TICKET>". New screens get one pane. Skip the "before" for stock pages the client doesn't use today.
- **Scope parts:** <PARTS>
  <!-- "None (single part)": the skeleton hides the scope UI. Also when there is no estimate.md yet; then the options
  the PRD prices go in one appendix scenario labelled "priced option, not in base" (more than two: ask the
  developer which). Or the estimate's parts, e.g. "1 · Base, +2 · Email,
  +3 · Core inventory (separately priced option, later phase)", with each part's scope text copied verbatim from
  the Scope column of `.ai/<TICKET>/estimate.md` (the developer may have rewritten it: use their words verbatim). -->
  Tag every element of a non-base part with its part (`NEW(html, inline, part, name)` / `scoped(...)`) so the drawer, badges and banner, which are built from the tags, show what each part adds. A narrower scope must leave a visible "… hidden: Part N not in scope" notice, never a silent gap.
- **QT and PARTS are copies:** `QT` texts come verbatim from §7 of the requirement source; `PARTS` scope texts from `estimate.md`. Copy them, don't paraphrase, so later drift is greppable.
- **Data:** fake only: invented customers, plausible SKUs, a fixed `TODAY`. SN formats: 7-digit zero-padded ids (`0000118`), dates `MM/DD/YYYY hh:mm am`, statuses as plain text.
- **No hours anywhere** on the artifact. Hours live only in `estimate.md`.
- Changes for this version: <CHANGES>
  <!-- the developer's request in their own words, plus the orchestrator's list; "first build" for v1. -->

## Verify (text only)
- Run `python3 -I <SKILL>/scripts/check-storyboard.py <file> --prd <the REQ_SOURCE file>` and fix every error.
- Browser click-through if available: `ToolSearch` `select:` the `mcp__chrome-devtools__` tools `list_pages,new_page,evaluate_script,list_console_messages,emulate,take_snapshot,close_page`. Open a NEW tab on `file://<abs path>#s1-1` (WSL with Chrome on Windows: `file://wsl.localhost/$WSL_DISTRO_NAME<abs path>#s1-1`); in `evaluate_script` click every step, `[data-go]` control, scope segment, drawer "Go to" and index jump, and collect errors and a text log; check `list_console_messages` (errors, warnings); check `documentElement.scrollWidth <= innerWidth` at 1920, `1280x800x1` and `390x844x1`. Snapshots go to `filePath` under `prototype/screens/` and are grepped.
- **Never take or view a screenshot.** Screenshots hold local customer data, the page is drawn from the text baseline, and once an image is in your context every later call re-sends it. If a request fails after an image got in, stop and report.
- No browser, or `chrome-devtools` times out? Rely on the check script and report "unclicked".

## Publishing and boundaries
- Never publish: the orchestrator publishes from the local file.
- Edit only `prototype/`. Never touch `prd.md` or `estimate.md`; the orchestrator owns them.
- If the orchestrator sends "STOP now": set the `.draft` badge to "WIP — PAUSED <DATE>", save, report what is done and what isn't, and stop. The orchestrator publishes.

## Reply (≤15 lines)
File path, lines and size; scenarios × steps; index rows; distinct R-ids cited; check-script and browser results; and **"anything ambiguous to draw"**: every place the requirements didn't say what to draw, or where drawing against the stock pages showed a requirement is wrong (e.g. it mentions something the stock page doesn't have).
