<!-- Storyboard build (10–20 min). Copy to .ai/<TICKET>/prototype/BUILD-BRIEF.md for each version, fill it, and give one
fresh `sn-worker` agent: "Read <path>/BUILD-BRIEF.md and do it." Extra placeholders: <KIND> (v1 discovery | v1.x discussion | v2 PO-facing), <STAGE> (internal | discussion | approved),
<SLUG>, <TITLE>, <PRD_SNAPSHOT>, <WORKFLOWS_SNAPSHOT>, <CHANGES>. Standard placeholders: see SKILL.md. -->

# Build brief: <TICKET> storyboard <VERSION> (<KIND>)

You are the build agent. Build (or revise) the storyboard: a single-file HTML page, published later as a private claude.ai artifact, that walks each use case of the <TICKET> contract, one recreated stock SkuNexus page per step, and makes it obvious at a glance what is stock SN and what <TICKET> adds. The PO reads the flow, the FE developer plans the work per page, the tech lead checks it against the platform. The full rules are `<SKILL>/references/build.md`; this brief is what you need from them.

## Read only these (keep your context lean)
1. The contract snapshot, never the live files: `<PRD_SNAPSHOT>` (§4 requirements, §6 criteria, §7 decisions and assumptions) and `<WORKFLOWS_SNAPSHOT>` (scenarios, steps, Parts). `BUILT_FROM` = `<BUILT_FROM>`.
2. `<REPO>/.ai/<TICKET>/prototype/sn-baseline.md`: the "before". The pages you draw must look like these.
3. `<SKILL>/assets/storyboard-skeleton.html`: the engine. Copy it on a first build; on a revision, edit the current file.
4. `<REPO>/.ai/<TICKET>/feedback.md`, only for the next free `FB` id and entries already filed.
5. Optional: the previous version (`prototype/<SLUG>-storyboard.html`) for snippets.

Don't open `prototype/screens/`: it holds local customer data and is large.

## First: the render-ready page plan (before any HTML)
Write `prototype/page-plan-<VERSION>.md`: one row per element of every live step, `| Step | Page · state | Element | Source |`, where Source is an id whose text the element matches (decided), an assumed §7 id (drawn with its chip), `stock`, or **gap**. A label or placement that adds no behaviour is a proposal, not a gap; a confirmation, an extra state, a rule or a message that decides something is a gap.
- <KIND> = v1: draw each gap with the simplest option that contradicts nothing, file it as a `CHOICE` entry (below) and chip it `A('FB<n>')`.
- <KIND> = v1.x or v2: if there is any gap, file every gap, finish the page plan, draw nothing, and reply `STOPPED: <n> gaps`.

## What to build
- **File:** `<REPO>/.ai/<TICKET>/prototype/<SLUG>-storyboard.html`. On a revision, first back up the current file as `<SLUG>-storyboard-v<previous>.html`.
- **Edit only the TICKET CONTENT region** (fake data, `PARTS`, `QT`, page builders, `SC`, `IX`, nav), plus the `<title>` (`<TITLE>`, never changes between versions), the `.pname` text (same as the title) and the `.draft` badge (v1: `Internal draft <VERSION>`; v1.x: `Draft for discussion <DATE>`, the engine appends the open-assumption count; v2 on: `Draft <VERSION>`); set `STAGE` (`'<STAGE>'`), `TICKET`, `HOST`, `USER`, `BUILT_FROM` and `TODAY`. A v1.x page keeps no `A('FB<n>')` chip: every one was ruled in the triage. Leave the ENGINE region alone; if it genuinely needs a fix, make it and say so in your reply.
- **Scenarios and steps = `<WORKFLOWS_SNAPSHOT>`,** in its order: scenario `id:'s<n>'`, step `id:'s<n>.<m>'`, step `p:[n]` its Part cell. Every live step is one page, except one listed in `NOT_DRAWN` with its reason (`const NOT_DRAWN={'s2.3':'<why>'};`, in TICKET CONTENT); a retired step is not drawn. A scenario whose steps are all outside Part 1 keeps its id and gets `opt:1` (an appendix). Never add, merge or reorder a step. Every deep link (`'#s1.3'`, `href="#s1.3"`, `jump`) must resolve to a drawn step or scenario.
- **One step = one recreated SN page in one state:** sidebar with the active item, page header (History, H1, breadcrumb, user · role), cards, grids, modals and toasts as in `sn-baseline.md`. Only what that step needs; no global toggles. Put new things where SN would (card header action, new card, grid column, modal); don't invent layouts SN doesn't use.
- **Integration steps** (a call, webhook, sync or details read between SkuNexus and another system): draw the SN page the call starts from or lands on, with one API call panel per call under it, `shell({…, api:[call]})`, `SYS` and the call shape as in the skeleton's step `s1.4` (`<SKILL>/references/build.md` §5 "API call panels"). Payload values come from the snapshot, never invented; an open field gets its `A()` chip in the column `note`.
- **Markers:** unmarked = existing SN · `NEW(...)` green outline + tag · `CHG(...)` amber outline + tag for stock behaviour removed or altered · `A('<key>')` chip, key = the §7 id (`Q26`; a legacy drawing decision (j) is `Dev j`; in v1 a gap's `FB<n>`) · UI no requirement asks for is labelled "proposal" in the caption.
- **Caption per step:** "What's new here" bullets, each ending in the ids it shows (the second item of the tuple), plus one "Today in SN" line from `sn-baseline.md`.
- **Before / after index tab:** one row per stock SN page the flow uses: name, path, `jump` = the step ids that show it, a change list with ids, and two panes "Stock SN today" | "<TICKET>". New screens get one pane. Skip the "before" for stock pages the client doesn't use today.
- **Parts = `<WORKFLOWS_SNAPSHOT>` "Parts", live rows only:** `PARTS[n] = {name: Name, scope: Scope (both verbatim), q: '(' + PO's shape + ')', short: a one- or two-word label}`. One part hides the scope UI. Tag every element of a non-base part with its part (`NEW(html, inline, part, name)` / `scoped(...)`); a step not in Part 1 also gets `pn` and `hide`. A narrower scope must leave a visible "… hidden: Part N not in scope" notice, never a silent gap.
- **`QT` and `PARTS` are copies:** `QT[Qn]` = that §7 entry's `Assumed:` text verbatim (a `Decided` entry gets no chip); `QT['FB<n>']` = the entry's What line verbatim. Copy, don't paraphrase, so drift is greppable.
- **Data:** fake only: invented customers, plausible SKUs, a fixed `TODAY`. SN formats: 7-digit zero-padded ids (`0000118`), dates `MM/DD/YYYY hh:mm am`, statuses as plain text.
- **No hours anywhere** on the page.
- Changes for this version: <CHANGES>
  <!-- "first build" for v1; for v2, "rebuild from contract v<N>"; for a stale rebuild, the stale ids and the pages they map to
       (references/build.md §10); plus the developer's request in their own words. -->

## feedback.md (append only)
Each gap, and each place where a stock page or another rule contradicts the contract, is one entry, appended to `<REPO>/.ai/<TICKET>/feedback.md` (create it with `# Feedback: <TICKET>` if missing). Re-read the file and take the next free `FB` id right before each append; never edit any existing entry.
```
### FB<n> · <WRONG|CHOICE|SILENCE> · storyboard <v1|v2> · <DATE>
- **Cites:** <step id, contract ids>
- **What:** <v1 CHOICE: "Drawn: <what the page shows>"; otherwise the problem in one or two sentences>
- **Evidence:** <sn-baseline.md section, or snapshot file and line>
- **Proposed:** (A) <the drawn or PO-literal option> · (B) <…>
- **Status:** open
```

## Verify (text only)
- `python3 -I <SKILL>/scripts/check-storyboard.py <file> --contract <REPO>/.ai/<TICKET>`; fix every error.
- Browser click-through if available: `ToolSearch` `select:` the `mcp__chrome-devtools__` tools `list_pages,new_page,evaluate_script,list_console_messages,emulate,take_snapshot,close_page`. Open a NEW tab on `file://<abs path>#s1.1` (WSL with Chrome on Windows: `file://wsl.localhost/$WSL_DISTRO_NAME<abs path>#s1.1`); in `evaluate_script` click every step, `[data-go]` control, scope segment, drawer "Go to" and index jump, open `#<id>` for every step id, and collect errors and a text log; check `list_console_messages` (errors, warnings); check `documentElement.scrollWidth <= innerWidth` at 1920, `1280x800x1` and `390x844x1`. Snapshots go to `filePath` under `prototype/screens/` and are grepped. Close your tab.
- **Never take or view a screenshot.** Screenshots hold local customer data, the page is drawn from the text baseline, and once an image is in your context every later call re-sends it. If a request fails after an image got in, stop and report.
- No browser, or `chrome-devtools` times out? Rely on the check script and report "unclicked".

## Boundaries
- Never publish: the orchestrator publishes from the local file.
- Write only under `prototype/`, plus appends to `feedback.md`. Never touch `prd.md`, `workflows.md`, the snapshots, `frontend-plan.md` or `estimate.md`.
- If the orchestrator sends "STOP now": set the `.draft` badge to "WIP — PAUSED <DATE>", save, report what is done and what isn't, and stop.

## Reply (≤15 lines)
File path, lines and size; scenarios × steps (and any live step not drawn, with why); index rows; distinct ids cited; chips by key; check-script and browser results; the `FB` ids you filed, by type, one line each; or `STOPPED: <n> gaps` with their ids.
