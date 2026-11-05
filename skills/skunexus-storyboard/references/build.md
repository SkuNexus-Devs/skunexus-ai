# Build: storyboard v1, v2 and stale rebuilds

Contents: §1 Three states · §2 Inputs and the run · §3 Render-ready prepass · §4 Format · §5 Anatomy (API call panels) · §6 Markers · §7 Parts · §8 Feedback · §9 Verify · §10 Rebuild stale · §11 Checklist

## §1 Three states

One single-file HTML page, built on `assets/storyboard-skeleton.html`, published as a private claude.ai artifact. It walks each `workflows.md` scenario, one recreated stock SN page per step, marks what is NEW or CHANGED against the captured stock pages, and carries the contract's ids and assumption chips. Readers: the PO (the flow, approval, the daily), the FE developer (each page, for the FE plan), the tech lead (fit with the platform), the developer (pairing it with the estimate).

| | v1: internal | v1.x: discussion | v2: approved |
|---|---|---|---|
| Built from | a `frozen` contract version | a `frozen` version; reviewed when a triage cut it (`run.md` has `triaged v<N>` with the `N` of its `BUILT_FROM`), else "not reviewed" | an `approved` version (G2), no `open` feedback |
| `STAGE` | `const STAGE='internal';` | `const STAGE='discussion';` | `const STAGE='approved';` |
| A gap in the contract (§3) | drawn with the simplest option, filed as a `CHOICE` entry, chipped `A('FB<n>')` | reviewed: **stops the build**, as in v2, no `A('FB<n>')` chip may remain; not reviewed: as in v1, the chips stay visible | **stops the build**: filed in `feedback.md`, nothing drawn until a ruling |
| Badge · version | "Internal draft v1" (fixes: v1.1, v1.2) | "Draft for discussion <DATE>" (before the triage: "Draft for discussion <DATE>, not reviewed"); the engine appends ": <N> assumptions open, not priced, not approved". The next minor of v1 (v1.1, v1.2 …) | "Draft v2", then v3, v3.1 … (`references/publish.md`) |
| Who sees it | the developer only | the PO and the FE developer together, when the developer shares it with no price and a presenter sheet (`references/publish.md` "Sharing v1.x") | the PO, when the developer shares it (G6, with the estimate) |
| Its job | find what the contract doesn't settle: FFD-13's nine drawing decisions and FFD-17's stale-page case came out of drawing | let the PO and the FE developer discuss a researched draft early, before the estimate | show the agreed scope, in parts |

Others see v1 only as v1.x. `check-storyboard.py` checks `STAGE='discussion'` with `--contract` on a page with a `BUILT_FROM` base and `prototype/sn-baseline.md`. With `run.md`'s `triaged v<N>` line for that version it is a reviewed share: every scope-bearing `Q` has a `Decided` line and no `A('FB<n>')` chip remains. Without it, it is an early share: the badge must say "not reviewed", and a missing `review/presenter-<DATE>.md` is a warning (model.md §8, "Sharing"). Any other `STAGE` value is an error; a page with no `STAGE` is legacy. The engine counts the open assumptions from the page's own `A()` chips that have a `QT` entry, so the count is never typed by hand.

**The bar:** an experienced SN user sees at a glance what is stock and what is new, and how the page will really look. On FFD-14 two things failed it: putting several dimensions on one page behind global toggles, and guessing the look from built CSS. One page per step on captured stock pages fixed both; build in that format from the first version.

## §2 Inputs and the run

The build agent reads, and only these:
- the contract snapshot it is built from: `review/prd-v<N>-<DATE>.md` (§4, §6, §7) and `review/workflows-v<N>-<DATE>.md`, never the live files;
- `prototype/sn-baseline.md` (`references/capture.md`);
- the skeleton (first build) or the current page (revision), and `feedback.md` for the next free `FB` id;
- not `prototype/screens/`: it holds local customer data and is large.

`BUILT_FROM` is `contract v<N> (<DATE>)` of that snapshot. Copy `assets/briefs/build-brief.md` to `prototype/BUILD-BRIEF.md`, fill it, and run one fresh `sn-worker` per version (10–20 min) in the background while other work continues. A text-only fix (a caption, a label) can be made directly in the main session, then checked as in §9.

## §3 Render-ready prepass (before any drawing)

Nothing is drawn unless each element is **decided** (contract text: a requirement, a criterion, a `Decided` §7 entry), **assumed** (a §7 entry in the `Assumed:` state, drawn with its chip) or **stock** (a captured page, unchanged). The build agent's first output is `prototype/page-plan-<VERSION>.md`, before any HTML:

| Step | Page · state | Element | Source |
|---|---|---|---|
| s1.3 | Order details: kit split, no serial | refusal toast naming the item | R4.b |
| s1.3 | | Serial field on the kit parent row | Q26 (assumed: chip) |
| s1.3 | | Cancel Order, Auto Decide Order | stock |
| s4.3 | Order details: page loaded before tagging | what the refusal says here | **gap** → FB4 (CHOICE in v1) |

- Every live step of the snapshot has rows; a retired step has none and is not drawn. A live step with nothing to show (a system step with no screen and no call to another system; a call gets an API call panel, §5) is listed in the page's `NOT_DRAWN` with its reason, e.g. `const NOT_DRAWN={'s2.3':'queued job, nothing on screen'};`; every other live step needs a page. Coverage is every live step, plus every assumed `Q` a drawn step cites (model.md §1).
- An element whose source is an id must match that id's text. An element no requirement asks for (a label, a placement) is a **proposal**: allowed when it adds no behaviour, labelled "proposal" in the caption. A confirmation, an extra state, a new rule or a message wording that decides something is behaviour: it is a gap. An "Are you sure?" step drawn before Create Fulfillment would be a gap, never a proposal.
- **v1:** each gap is drawn with the simplest option that contradicts nothing, filed as a `CHOICE` entry (the page chose; §8), and chipped `A('FB<n>')`. A `WRONG` the page can draw around is filed without a chip.
- **v1.x and v2:** any gap stops the build. The agent files every gap (§8), writes the page plan, and replies `STOPPED: <n> gaps` without drawing. You take the entries to `skunexus-contract`'s rulings door and rebuild from the version it cuts.

## §4 Format (fixed; the reasons are why)

| Decision | Choice | Why |
|---|---|---|
| Artifact type | Plain page: `Artifact quickstart intent:"other", design_systems:false` | `intent:"design"` leads to the Design canvas type, which doesn't allow script-built UI |
| Shape | Scenarios plus a before/after index | The PO follows the flow; the FE developer reads each page |
| Code | One file, vanilla JS, no libraries except the Inter font. Content lives in data (`SC`, `IX`, `QT`, `PARTS`, page builders) in the skeleton's TICKET CONTENT region | Revisions change data, not the engine |
| Theme | Light only, real `--sn-*` tokens | SN itself is light only; "respect what exists" beats a generic dark mode |
| Head | Stable `<title>` (`<CLIENT> <Feature> Prototype`), version badge in the page, `claude:viewport-fit-sides` meta, Inter link, no doctype or viewport meta | The artifact page contract; the title is the artifact's name |
| Ids | Scenario `id:'s<n>'` and step `id:'s<n>.<m>'` from `workflows.md`; step `p:[n]` its Part; a live step with no page in `NOT_DRAWN` with its reason; `BUILT_FROM` the snapshot's version | Ids are the join keys: the checks and `--stale` find pages by them |
| Deep links | `#s1.3` by step id (or scenario id), `#index`; every link in the page (`'#s1.3'`, `href="#s1.3"`, index `jump`) resolves to a drawn step or scenario | The PO deep-links steps in Jira comments; ids survive a retired step, positions don't |
| Data | Fake only, fixed `TODAY`, SN formats (7-digit ids, `MM/DD/YYYY hh:mm am`, plain-text statuses) | No real data from the local app |
| Contrast | Links `#0079a6`; navy text on cyan grid headers | Stock `#0ac1ef` on white is ~2.1:1 |
| Hours | None | The page goes to the PO and the client |

## §5 Anatomy

- **Header:** one row with the name, a short badge, tabs (Storyboards | Before / after index), the scope segments and "Legend ▾".
- **Part cards** in the body.
- **Scenario picker:** the `workflows.md` scenarios in order. A scenario is an end-to-end flow; a step is one page in one state. Shown as "Scenario 1, 2 …" by position; the ids live in the data and the links.
- **Step bar** with part badges; **stage:** a fake browser frame around the recreated SN page.
- **Caption panel:** "What's new here" bullets, each ending in the ids it shows (`R4.b`, `Q26`), one "Today in SN" line from `sn-baseline.md`, Prev / Next.
- **Advance:** highlighted in-page buttons also move to the next step.
- **Before / after index:** one row per stock page the flow uses (name, path, jump buttons by step id, a change list with ids, two panes "Stock SN today" | "<TICKET>"); a new screen gets one pane. Skip the "before" of a stock page the client doesn't use today.

One step is one recreated page in one state: sidebar with the active item, page header (History, H1, breadcrumb, user · role), cards, grids, modals and toasts as in `sn-baseline.md`. Only what that step needs; no global toggles. Put new things where SN would (a card header action, a new card, a grid column, a modal); don't invent layouts SN doesn't use.

### API call panels

A step whose trigger or effect is a call between SkuNexus and another system (an API call, a webhook, a sync, a details read) has no screen of its own. Draw the SN page the call starts from or lands on, and under it one dark panel per call: the other system left, SkuNexus right, the arrow from caller to callee, then the request and the response. The component is RL-47's Django ⇄ SkuNexus cards, look and colours unchanged (the skeleton's `apiPanel`, example step `s1.4`).
- **Data** (TICKET CONTENT): `SYS` names each other system, `{shop:{name:'Shop',bg:'#0c4b33',accent:'#44b78b'}}` (colours optional, default green; SkuNexus is always purple and cyan). Each call is one object, passed as `shell({…, api:[call]})`:
  `{from:'sn', to:'shop', kind:'event', event:'order.review_hold', part:1, req:{line:'POST https://<shop-host>/webhooks/skunexus', headers:[…], body:{…}, note}, res:{line:'200 OK'}, other:[['non-2xx','sent again','same event_id']], then, flag}`.
  `kind` is `call`, `event` or `read` (kicker: API call · Webhook · Details read); the status chip colours by code (2xx green, 4xx amber, 5xx red); `then` is what the other system does next, `flag` the orange "Watch out" note, `part` the part pill (hidden on a one-part page). `note`, `then`, `flag` and `other` are HTML.
- **One panel per call,** in call order. Error answers and retries of the same call go in `other`, not in a second panel.
- **Values come from the contract** (the `prd.md` and `workflows.md` snapshots), never invented. A field the contract leaves open keeps a placeholder value, and its column's `note` names it with its chip (the §7 `Q`, or in v1 the gap's `FB` id, §3): `` note:`<code>carrier</code> ${A('Q4')}` ``.
- **Draft gate:** until `STAGE='approved'`, every panel's top bar says "draft: confirm before coding against it". The other system's developers code against these panels, and only an approved (v2) contract is binding.
- Such a step is drawn, not listed in `NOT_DRAWN`: the call is what it shows.

## §6 Markers

| Marker | Look | Rule |
|---|---|---|
| (none) | Normal SN styling | Unmarked means stock |
| `NEW(...)` | Green outline + "NEW" tag + part chip | Even a page H1 can be NEW (a new screen) |
| `CHG(...)` | Amber outline + "CHANGED" tag | Stock behaviour removed or altered |
| `A('<key>')` | "Assumed · <key>" chip; hover shows the `QT` text and `BUILT_FROM` | Every drawn assumption. Key = the §7 id (`Q26`); a legacy drawing decision `(j)` is `A('Dev j')`; in v1 only, a gap's `FB` id |
| Proposal | Prose in the caption bullet ("wording is a proposal") | UI no requirement asks for, adding no behaviour |
| Part chips | P1 navy, P2 teal, P3 purple | Never reuse the NEW green or the CHANGED amber |

**One helper per id type**, so a grep audits the page: chips only through `A()`, ids only as the second item of a `news` or `changes` tuple, part tags only through `p:[n]`, `scoped()`, `pa()` or the part argument of `NEW`/`CHG`.

**`QT` and `PARTS` are copies, never paraphrases,** so drift is greppable. `QT[<Qn>]` = the `Assumed:` text of that §7 entry in the snapshot, verbatim; `QT['FB<n>']` = that entry's `What:` line, verbatim. A `Decided` entry gets no chip: its answer is now contract text. `PARTS` copies `workflows.md` "Parts" (§7).

## §7 Parts

Parts are a contract facet (`workflows.md` "Parts"), so the storyboard shows them and never invents, merges or drops one.
- `PARTS` has one entry per **live** part, keyed by its number: `name` = Name and `scope` = Scope, verbatim; `q` = the "PO's shape" cell in brackets (`(base)`, `(priced separately)`); `short` = a one- or two-word label for the scope control. Part 1 is the base. One entry hides all scope UI.
- Each step's `p:[n]` is its `workflows.md` Part cell. A step whose part is not 1 also gets `pn` (its drawer name) and `hide` (its hidden-notice label). A scenario whose steps are all outside Part 1 is an appendix: it keeps its `workflows.md` id and carries `opt:1`. Its first page opens with the `optbanner` ("Priced option · not in base"), as in the skeleton's example.
- The set of `PARTS` keys equals the live parts exactly: a missing or extra key is a check error, and Name or Scope drift a warning.
- An element of another part inside a step (an email line on a base page) is tagged with that part (`NEW(html, inline, part, name)`, `scoped(...)`), and its caption bullet cites the ids of the step in that part whose behaviour it shows. Every element of a non-base part is tagged, because the drawer, badges and banner are built from the tags.
- The scope control is cumulative (`1 · Base` / `+2 · …` / `+3 · …`), the only switch on the page. Part cards carry "See what it adds (n)"; the "What Part N adds" drawer lists the page's own tags with Go to; badges ("P2·3") mark scenarios and steps; a banner with Highlight explains a scope change.
- A narrower scope hides elements behind a visible "… hidden: Part N not in scope" notice, never a silent gap. On FFD-14 hiding in place alone was invisible ("1 vs 1+2 looked the same"), and building the drawer from tags exposed two untagged elements.

## §8 Feedback: drawing never decides

Drawing against real stock pages finds contract problems; the storyboard reports them and fixes none. The build agent appends each one to `.ai/<TICKET>/feedback.md`, the one file outside `prototype/` it may touch, in model.md §6's shape:

```
### FB4 · CHOICE · storyboard v1 · 2026-11-03
- **Cites:** s4.3, R11.c, R1
- **What:** Drawn: a page loaded before the product was tagged shows no serial field; the refusal toast names the item.
- **Evidence:** prototype/sn-baseline.md §1; review/workflows-v1-2026-11-03.md (s4.3)
- **Proposed:** (A) refuse with the item message; a reload shows the field · (B) refuse with a "reload the page" message
- **Status:** open
```

| Type | When the drawing hits it |
|---|---|
| `WRONG` | the contract contradicts a stock page or another rule (FFD-14: a packet printed "next to the packing slip" that stock Packing never prints) |
| `CHOICE` | an element the contract leaves open (a label that decides something, a confirmation, a placement with behaviour); v1 drew the simplest option |
| `SILENCE` | a state or case the flow needs that nothing in the contract covers (FFD-17: a page loaded before its product was tagged). In v1, a silence the page must draw is filed as the `CHOICE` it drew, naming the silence in What |

- **Append only.** Create the file with `# Feedback: <TICKET>` if it is missing. Re-read it and take the next free `FB` id immediately before each append, because the contract's panel may be appending in the same phase. Never edit or renumber an entry, yours or anyone's; only the rulings door changes a status.
- **What** starts with "Drawn:" in v1 (what the page shows, for `QT`) and states the problem in v2. **Cites** names the step and the contract ids; **Evidence** a baseline section or a snapshot line; **Proposed** lettered options, the drawn or PO-literal one first.
- You, not the build agent, present the open entries to the developer and hand them to `skunexus-contract`'s rulings door. A ruled entry comes back as contract text or an assumed `Q` in a new version, and the next build drops its `FB` chip.

## §9 Verify (text only, always)

Images pulled into context killed a storyboard agent twice and the main session once.

| Check | How |
|---|---|
| Static | `python3 -I <SKILL>/scripts/check-storyboard.py <html> --contract .ai/<TICKET>` (exit 2: unreadable): script syntax, id lookups, hour strings, `A()` keys vs `QT`, cited ids, step ids vs live steps and `NOT_DRAWN`, deep links, `QT`/`PARTS` drift, `PARTS` keys vs live parts, `BUILT_FROM`. A page with `BUILT_FROM` is checked against the snapshots it names; newer versions reach it only through `--stale` |
| Stale | `python3 -I <CONTRACT_CHECK> --stale <html>`: `result: current` right after a build |
| Click-through | Own tab via `new_page` (`file://<abs path>#s1.1`; WSL with Chrome on Windows: `file://wsl.localhost/$WSL_DISTRO_NAME<abs path>#s1.1`). In `evaluate_script`, click every step, `[data-go]`, scope segment, drawer "Go to" and index jump, and open `#<id>` for every step id; read toasts, rows and errors into a log |
| Layout | `getBoundingClientRect` boxes, `innerWidth`, `scrollWidth` at 1920, `1280x800x1`, `390x844x1`; no sideways scroll at phone width; the header stays one row |
| Console | `list_console_messages` with `types:["error","warn"]` |
| Counts | Steps per scenario equal the snapshot's live steps; index rows; drawer items equal the DOM tags per part |
| No browser, or `chrome-devtools` doesn't answer | The check script only; publish with "unclicked" in the `artifact.md` row |

Snapshots go to `filePath` under `prototype/screens/` and are grepped. Visual judgement the text can't settle (crowding, alignment) goes to one short-lived `sn-scout` that views at most 3 saved screenshots, answers one narrow question in text and is discarded. Ask the developer to describe a visual problem or give a file path rather than paste a screenshot.

## §10 Rebuild stale

A contract version marks the storyboard stale by id (model.md §5). The rebuild touches only the stale pages:
1. `python3 -I <CONTRACT_CHECK> --stale prototype/<SLUG>-storyboard.html` lists each stale id with its reason.
2. Map ids to pages: a step whose id, cited ids, chips or part are listed is redrawn; a new live step gets a new page; a retired step's page and its index jumps are removed; a changed `Assumed:` text is re-copied into `QT`; a changed part is re-copied into `PARTS` and its tags checked.
3. One fresh build agent with that list as `<CHANGES>` (§2); it re-runs §3 for those steps only. `BUILT_FROM` becomes the new version. A rebuild bumps the major version (`references/publish.md`), except the triage rebuild, which is the next v1 minor with `STAGE='discussion'`.
4. Grep the page for the old wording of every changed text, then §9.

The FE plan and the estimate name `prototype/artifact.md@<hash>`, so a new storyboard version marks them stale in turn; rebuild their affected sections and rows next (chain).

**Pre-skill storyboards** (no `BUILT_FROM`, positional `#s1-2` links, `QT` copied from a PRD): they have no base and count as current. Their first rebuild re-keys every scenario and step to `workflows.md` ids and adds `BUILT_FROM`. Their `QT` texts were often condensed: list only drift warnings below ~0.8 similarity, or, with the developer's OK, re-copy every `QT` verbatim once as a minor version. On FFD-14 a stale tooltip contradicted the updated PRD and estimate.

## §11 Checklist (the developer's rules)

- [ ] Built by a background `sn-worker` from one frozen or approved snapshot; `BUILT_FROM` names it; `STAGE` and the badge match the state (§1).
- [ ] Render-ready page plan written before any drawing; v1 gaps chipped `A('FB<n>')`, v2 stopped on any gap.
- [ ] One page per live step, keyed by its step id; no global toggles; stock vs added obvious; pages look like the captured ones.
- [ ] Caption per step: "What's new here" with ids, one "Today in SN" line; extra UI marked "proposal".
- [ ] Nothing decided by drawing: every problem is a `feedback.md` entry.
- [ ] `QT` and `PARTS` copied verbatim; parts from `workflows.md`, tagged, with visible hidden notices.
- [ ] Before / after index; "before" panes only for stock pages the client uses.
- [ ] Header in one row; legend in a dropdown; descriptive cards in the body.
- [ ] No hours; fake data only; text-only verification.
- [ ] Same URL for every version; stable `<title>`; version badge; publish `label`; backups `*-v<N>.html`.
- [ ] On "pause": the build agent sets the "WIP — PAUSED <DATE>" badge, saves and stops; you publish.
