<!-- Capture (~30 min). Copy to .ai/<TICKET>/prototype/CAPTURE-BRIEF.md, fill the placeholders and the page list,
then give one fresh `sn-scout` agent: "Read <path>/CAPTURE-BRIEF.md and do it." Extra placeholders: <PAGES>, <WRITES>,
<CONTRACT> (the frozen snapshots review/prd-v<N>-<DATE>.md and review/workflows-v<N>-<DATE>.md). Standard placeholders: see SKILL.md. -->

# Capture brief: stock SN pages for <TICKET>

You are the capture agent. Produce the "before" picture of every stock SkuNexus page the <TICKET> storyboard touches, as PII-free text in `<REPO>/.ai/<TICKET>/prototype/sn-baseline.md`, following `<SKILL>/assets/sn-baseline-template.md`. A separate build agent will draw the storyboard from your markdown alone, so the markdown must carry the layout, labels, actions and visual details it needs.

## Context hygiene (earlier capture agents crashed)
- Screenshots hold local customer data, and the build works from your text capture, never from images. Once an image is in your context every later call re-sends it. So:
  - `take_screenshot` and `take_snapshot` always get a `filePath` under `<REPO>/.ai/<TICKET>/prototype/screens/baseline/` (`NN-<slug>.png`, `NN-<slug>.snapshot.txt`). Never view a screenshot.
  - Never pull a whole snapshot into context: grep it, or slice it with `python3 -I`.
  - Read styles with `evaluate_script` (`getComputedStyle`, `innerText`, `getBoundingClientRect`), not by looking.
  - If a request fails after an image got into your context anyway, stop and report. Don't retry.
- **Append to `sn-baseline.md` after each page**, so progress survives a crash. Keep a `<!-- STATE <HH:MM>: done …; next … -->` line under its title until you finish, then delete it.

## Browser
- Load the tools first: `ToolSearch` with `select:mcp__chrome-devtools__list_pages,mcp__chrome-devtools__new_page,mcp__chrome-devtools__navigate_page,mcp__chrome-devtools__take_snapshot,mcp__chrome-devtools__take_screenshot,mcp__chrome-devtools__evaluate_script,mcp__chrome-devtools__click,mcp__chrome-devtools__close_page`. If `list_pages` fails, stop and report (no browser = no capture).
- Open your own tab (`new_page`) on `<LOCAL_APP_URL>`. Touch no other tab, especially not Jira, GitHub, Google or claude.ai. Close your tab at the end.
- The look source is the stock local app, not a client environment: client dev and stage sites carry overlays and are not a stock baseline.

## Pages, in workflow order
<PAGES>
<!-- The stock pages the live workflows.md steps visit, each with its step ids, as confirmed with the developer
     (references/capture.md step 1). e.g. 1. Orders grid · s1.1, s4.1  2. Order details: an open order with a kit line · s1.2, s1.3
     Skip pages a reusable baseline already covers (below). Give a page only a short "before" if the client doesn't use it today. -->

Reuse first: if another ticket on this machine already captured a page at the same core major version (`ls <REPO>/../skunexus-client-*/.ai/*/prototype/sn-baseline.md`, the sibling client repos), copy that section and note "copied from …" instead of recapturing. Global chrome and the visual system are core-wide and usually reusable.

## Per page, record
Path and tab title · the step ids it serves · an ASCII layout sketch · components and labels (cards, header actions and their variants, grid columns in order, row actions, fields, modals, verbatim toasts, empty states) · what the ticket's subject looks like today ("before"; it becomes the step's "Today in SN" line) · where <TICKET> would attach, as SN would place it, with the step id and the ids it cites in <CONTRACT>. Finish with the global chrome and the visual system, ending in the `:root { --sn-* }` token block.

Per page, prefer **one** `evaluate_script` that returns a compact JSON of everything this list needs (layout boxes, labels, grid columns in order, actions, computed styles). Save it as `screens/baseline/NN-<slug>.json` and grep it, rather than making many single reads: on FFD-35 capture took 266 turns, 114 of them small `evaluate_script` calls.

## Data and writes
- Record structure and value shapes only, never names, emails, addresses or phone numbers. The raw files stay local; only your markdown crosses into the artifact.
- Local writes: <WRITES>
  <!-- either "None: read-only. If a page state needs data you can't find, describe it from the code and any reused
  baseline section, marked 'drawn from code, not captured', and report it." or "Allowed on the local app and DB
  (<LOCAL_DB>) only, as the developer granted on <DATE>." -->
- When writes are allowed, log every change in the Data log table so it can be undone. Never run queued jobs or workers: some push to the client's external system (a queued shipment push once nearly reached a client's live store). List any job or statement you leave pending. Before the first write, check that no job can run: `grep -m1 '^QUEUE_CONNECTION=' <REPO>/.env` must not be `sync`, and no worker may be up (`pgrep -af 'queue:work|horizon'`; under Docker, `docker compose ps` shows no worker service running). If either check fails, make no writes: draw the state from code and report why.
- Never touch a remote DB, a client sandbox's admin UI or an external system. Learn submit behaviour from the code, not by clicking: open, inspect, cancel, never confirm.

## Reply (≤15 lines)
Pages captured (section numbers and step ids), pages skipped or reused and why, anything left pending in the local app, anything you couldn't capture, and any place where a stock page contradicts <CONTRACT> (id, section).
