# Stages 8–9: the storyboard artifact

Contents: §1 What it is and who reads it · §2 Capture (stage 8) · §3 Build (stage 9) · §4 Verify · §5 Publish · §6 Feedback loop and re-sync · §7 Checklist

## §1 What it is and who reads it

It is a single-file HTML storyboard, published as a private claude.ai artifact. It walks the PO through each workflow scenario, one recreated SN page per step. It marks what is NEW or CHANGED against the real stock pages, and it carries the PRD's R-ids and assumptions. The model is the FFD-14 RMA storyboard: `https://claude.ai/artifact/KTbbMs8UBtgTFCb6a17icC`, file `.ai/FFD-14/prototype/ffd-rma-storyboard.html` in the FFD client repo (on the author's machine; the skeleton's example content shows the same anatomy).

| Reader | Uses it for |
|---|---|
| PO | Following the flow; approval; the daily discussion. They asked for "the same" on later tickets after FFD-14 |
| FE developer | Sizing the FE per page |
| Tech lead | Checking it against the platform |
| Developer | Pairing it with the estimate comment: the artifact carries the scope, the Jira comment carries the hours |

**The bar:** an experienced SN user sees at a glance what is stock and what is new, and how the page will actually look. Two things failed that bar on FFD-14:
- v1/v2 put several dimensions on one page with global toggles;
- the look was guessed from built CSS.

The storyboard format on captured stock pages fixed both. Build it in that format from the first version.

## §2 Capture (stage 8)

**Goal:** a PII-free text picture of every stock page the storyboard draws, in `prototype/sn-baseline.md` (format: `assets/sn-baseline-template.md`).

0. **Scenarios first.** Draft 3–6 flows from the ticket's workflow or the requirement groups, each step a page in one state, and show them to the developer in 3–6 lines. The capture page list is the set of stock pages those steps visit; confirm it before capture.
1. **Reuse first.** `ls <REPO>/../skunexus-client-*/.ai/*/prototype/sn-baseline.md` (sibling client repos). A section captured at the same core major version can be copied with a "copied from …" note. On FFD, `.ai/FFD-14/prototype/sn-baseline.md` already covers:
   - §0 Orders grid;
   - §1 Order details (+ In Fulfillment);
   - §4 Receive Inventory (+ Customer Return);
   - §5 Fulfillment → Picking → Packing;
   - §7 global chrome;
   - §8 visual system and `--sn-*` tokens.
   
   Capture only what's missing.
2. **Preflight the browser** before launching the agent: `ToolSearch` `select:mcp__chrome-devtools-main__list_pages`, then `list_pages`. If no browser works, tell the developer; the build can still run on reused sections, marked "unclicked".
3. **Local writes** (creating test orders, driving one through pick/pack): ask the developer. A grant covers the local app and DB only. The capture brief forbids queue workers (after checking that none can run) and requires an undo log. With no grant, draw that page state from code plus the reused baseline, marked "drawn from code, not captured" in `sn-baseline.md`.
4. Copy `assets/briefs/capture-brief.md` to `prototype/CAPTURE-BRIEF.md`, fill in `<REQ_SOURCE>` (the frozen PRD snapshot or `prototype/requirements-lite.md`) and the page list in workflow order, and run **one** `sn-scout` capture agent (~30 min). Keep capture and build as separate agents: a combined one died with too much in its context.

The look source is the developer's **stock local app** (`<LOCAL_APP_URL>`), not a client environment. Client dev/stage sites carry overlays, and `sn-baseline.md` wins over any other style reference.

## §3 Build (stage 9)

**Inputs:**
- a frozen requirement source (`<REQ_SOURCE>`: a PRD snapshot, or `requirements-lite.md`);
- `sn-baseline.md`;
- the estimate parts, if any;
- the skeleton (`assets/storyboard-skeleton.html`).

Copy `assets/briefs/build-brief.md` to `prototype/BUILD-BRIEF.md`, fill it (scenarios, parts, changes for this version) and run one fresh build agent per version (10–20 min), in the background while other work continues. A small change (a header fix, a tooltip text) can be made directly in the main session.

**Format decisions** (fixed; the reasons are why they're fixed)

| Decision | Choice | Why |
|---|---|---|
| Artifact type | Plain page: `Artifact quickstart intent:"other", design_systems:false` | `intent:"design"` leads to the Design canvas type, which doesn't allow script-built UI |
| Shape | Scenarios plus a before/after index | Serves the PO (the flow) and the FE developer (per page) |
| Code | One file, vanilla JS, no libraries except the Inter font. Content lives in data (`SC`, `IX`, `QT`, `PARTS`, page builders) in the skeleton's TICKET CONTENT region | Revisions change data, not the engine |
| Theme | Light only, real `--sn-*` tokens | SN itself is light only; "respect what exists" beats the generic dark-mode contract |
| Head | Stable `<title>` (`<CLIENT> <Feature> Prototype`), version badge in the page, `claude:viewport-fit-sides` meta, Inter link, no doctype or viewport meta | Artifact page contract; the title is the artifact's name |
| Data | Fake only, fixed `TODAY`, SN formats (7-digit ids, `MM/DD/YYYY hh:mm am`, plain-text statuses) | No real data from the local app |
| Contrast | Links `#0079a6`; navy text on cyan grid headers | Stock `#0ac1ef` on white is ~2.1:1 |
| Deep links | `#s1-1` … , `#sx-1`, `#index` | The PO deep-links steps in Jira comments |
| Hours | None | Developer rule |

**Anatomy:**
- **Header:** one row with name, a short badge ("Draft v2"), tabs (Storyboards | Before/after index), the scope segments, and "Legend ▾".
- **Part cards** sit in the body.
- **Scenario picker:** 3–6 scenarios of 2–7 steps. A scenario is an end-to-end user flow; a step is one page in one state.
- **Step bar** with part badges.
- **Stage:** a fake browser frame around the recreated SN page.
- **Caption panel:** "What's new here" bullets with R-ids, one "Today in SN" line, and Prev/Next.
- **Advance:** highlighted in-page buttons also move to the next step.

**Markers**

| Marker | Look | Rule |
|---|---|---|
| (none) | Normal SN styling | Unmarked means stock |
| `NEW(...)` | Green outline + "NEW" tag + part chip | Even a page H1 can be NEW (a new screen) |
| `CHG(...)` | Amber outline + "CHANGED" tag | Stock behaviour removed or altered |
| `A('<key>')` | "Assumed · <key>" chip showing the key (`Dev a` renders as "dev (a)"); hover shows the PRD §7 text | Every drawn default of an open question. The key is the id PRD §7 uses for that item: `Qn`, `Dev a`, or the PRD's own decision ids |
| Proposal | Prose in the caption bullet ("wording is a proposal") | UI no requirement asks for |
| Part chips | P1 navy, P2 teal, P3 purple | Never reuse the NEW green or the CHANGED amber |

**Scope parts** (only when the estimate has parts; with no `estimate.md`, build a single part and put priced options the PRD names in one appendix scenario labelled "priced option, not in base", asking which if more than two):
- a joined, cumulative segment control (`1 · Base` / `+2 · …` / `+3 · …`), the only switch on the page;
- part cards with "See what it adds (n)";
- a "What Part N adds" drawer, built from the page's own `data-part` tags, with Go to;
- "P2·3" badges on scenarios and steps;
- a scope banner with Highlight.

A narrower scope hides elements behind a visible notice. On FFD-14, hiding in place alone was invisible ("1 vs 1+2 looked the same"), and building the drawer from tags exposed two untagged elements.

## §4 Verify

Text only, always. Images pulled into context killed a storyboard agent twice and the main session once.

| Check | How |
|---|---|
| Static | `python3 -I <SKILL>/scripts/check-storyboard.py <html> --prd <the frozen REQ_SOURCE>`: script syntax, id references, forbidden hour strings, `A()` keys vs `QT`, R-ids and Q-ids vs the PRD, `QT` texts that drifted from §7 |
| Click-through | Own tab via `new_page` (`file://<abs path>#s1-1`; WSL with Chrome on Windows: `file://wsl.localhost/$WSL_DISTRO_NAME<abs path>#s1-1`). In `evaluate_script`, click every step, `[data-go]`, scope segment, drawer "Go to" and index jump; read toasts, rows and errors into a log |
| Layout | `getBoundingClientRect` boxes, `innerWidth`, `scrollWidth` at 1920, `1280x800x1`, `390x844x1`; no sideways scroll at phone width; the header stays one row |
| Console | `list_console_messages` with `types:["error","warn"]` |
| Counts | Steps and index rows per scope; drawer items equal to the DOM tags per part |
| No browser, or `chrome-devtools-main` doesn't answer | The check script only; publish with the badge "unclicked" |

Visual judgement the text can't settle (crowding, alignment) goes to one short-lived subagent that views at most 3 saved screenshots and returns text. Ask the developer to describe a visual problem, or give a file path, rather than paste a screenshot.

## §5 Publish

| Situation | Calls |
|---|---|
| First publish | `Artifact quickstart intent:"other", design_systems:false` (it counts as the `artifact-design` load) → `Artifact publish` with `file_path`, `icon:"layout"`, `title`, a one-sentence `description`, a `label` ("Storyboard v1"). Create `prototype/artifact.md` with the URL and a version table (version · date · label · PRD snapshot it was built from · trigger · what changed). Private; never share or pin it |
| No Artifact tool in this session | Stop after the check script and the click-through. Give the developer the local file path and write `artifact.md` with "not published (no Artifact tool)" in the URL column; they publish later from a session that has it |
| Each later version | Back up `<slug>-storyboard-v<N>.html` → `Artifact read url` (confirm the live page is the expected version) → publish the same file path, or pass `url` from `artifact.md` in another session. New `label` and `description`, no `icon`. Add a row to `artifact.md` |
| No `artifact.md` (a storyboard made before this skill, e.g. FFD-14) | Find the URL in the ticket's memory note or with `Artifact list`, confirm it with `Artifact read`, then create `artifact.md` before publishing. Backfill only the versions the memory note records; don't invent history. Publishing without `url` from a new session would create a second artifact. If no URL is found, it was never published: treat it as a first publish, asking the developer first if the PO may already hold a link to an earlier prototype |
| An older prototype in another format, no `artifact.md` (e.g. FFD-13's `ffd-sif-prototype.html`) | Find its URL as above and ask whether the storyboard replaces it at the same URL (recommended: keeps the PO's link) or becomes a new artifact. Carry its drawing decisions (a), (b)… from PRD §7 |
| Version numbers | A rebuild or a new scenario bumps the major (v3 → v4). Text and chrome fixes bump the minor (v3.2 → v3.3). Badge, `label` and the `artifact.md` row all carry the same number |
| `artifact-design` | A republish from a new session loads it once before the first publish (on a first publish the quickstart counts). The Theme row overrides its dark-mode rule: never add dark tokens |
| Pause | SendMessage to the build agent: "STOP now: add the 'WIP — PAUSED <DATE>' badge and save; I'll publish." The build agent never publishes. You publish as above; a first publish creates `artifact.md` |
| Text-only fix | Publish, then `Artifact read` with a `prompt` to confirm the string is live |
| Never | Republish from an `Artifact read` copy. A read-back copy is not byte-identical to the file you published |

The in-page badge carries the version the reader sees ("Draft — PRD v2", "Draft v3"). The `<title>` never changes. Remind the developer that the artifact is private until they share the link; they post it themselves, usually with the estimate comment.

## §6 Feedback loop and re-sync

Drawing against real stock pages finds PRD bugs. The build agent **returns** "anything ambiguous to draw". The orchestrator, never the build agent, takes those items to the PRD:

- A requirement that is factually wrong against the stock page goes to the developer as a correction. On FFD-14, a requirement printed a packet "next to the packing slip" that stock Packing never prints.
- Open drawing choices become developer decisions (a), (b)… in PRD §7 "Developer decisions for the plan", with the option the storyboard assumes. If the PRD is Approved, show the developer the proposed dated lines and add them only on their yes; a line that changes what an R requires goes through the amend path (`Status: Draft (amending approved v<N>, <DATE>)`). Don't change R text without their OK. If `backend-plan.md` exists, list the tasks each drawing decision touches.
- Before a panel: the drawing questions and the storyboard file go to the panel as inputs (`prd-stages.md` §6).

**Re-sync rule:** `QT` copies PRD §7 and `PARTS` copies the estimate's Scope column. After any edit to either:
1. Diff the source against the page first. If nothing differs, say so and ask before republishing.
2. Re-copy the changed texts.
3. Run `check-storyboard.py --prd prd.md`. Use the current PRD, not the build snapshot, because the point is to see drift. It flags `QT` text that no longer matches §7, and stale tooltips it reports outside the change you were asked for go to the developer as a list rather than being fixed silently. On a pre-skill storyboard the `QT` texts were condensed: list only warnings below ~0.8 similarity, or, with the developer's OK, re-copy every `QT` verbatim once as a minor version.
4. Grep the HTML for the old wording.

On FFD-14, a stale tooltip contradicted the updated PRD and estimate.

## §7 Checklist (the developer's rules)

- [ ] Built by a background `sn-worker` agent while other work continues; corrections relayed with SendMessage while it is warm (idle under ~5 min), otherwise a fresh build agent.
- [ ] Built from a frozen requirement version; ids emitted through helpers so a grep finds stale ones.
- [ ] Storyboard format from the first version, on captured stock pages; plus a before/after index.
- [ ] One page state per step, no global toggles; stock vs added obvious; pages look like the real ones.
- [ ] Caption per step: "What's new here" with R-ids, plus one "Today in SN" line.
- [ ] Open questions never answered by drawing: "Assumed · Qn" carries the PRD default; extra UI marked "proposal".
- [ ] "Before" panes only for stock pages the client uses.
- [ ] Estimate parts visible and scopable; part text = the estimate's Scope column, in the developer's words; optional parts labelled "separately priced option".
- [ ] A scope change shows its difference (drawer, badges, banner, hidden-item notices), derived from the page's own tags.
- [ ] Header in one row; legend in a dropdown; descriptive cards in the body.
- [ ] No hours (`check-storyboard.py` greps for them); fake data only.
- [ ] Text-only verification; no screenshots in any context.
- [ ] Same URL for every version; stable `<title>`; version badge; publish `label`; backups `*-vN.html`.
- [ ] "Anything ambiguous to draw" returned and taken into the PRD by the orchestrator.
- [ ] On "pause": the build agent adds a "WIP — PAUSED <DATE>" badge, saves and stops; the orchestrator publishes.
