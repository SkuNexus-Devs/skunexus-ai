# Capture: the stock pages, as text

**Goal:** a PII-free text picture of every stock SN page the storyboard draws, in `prototype/sn-baseline.md` (format: `assets/sn-baseline-template.md`). The build agent draws from this markdown alone, so it must carry layout, labels, actions and computed styles.

**Why it exists.** The bar is that an experienced SN user sees at a glance what is stock and what is new, and how the page will really look. On FFD-14 the look was first guessed from built CSS, and it failed that bar; captured stock pages fixed it. Capture once per ticket (usually for v1) and reuse it for every later version; recapture only the pages a new step visits.

## Steps

1. **Page list from the use cases.** Every live step of the frozen `workflows.md` snapshot is one page in one state. List the stock pages those steps visit, in workflow order, each with the step ids it serves (`Order details: open order with a kit line · s1.2, s1.3`). A step on a screen SN doesn't have yet needs no capture: the build draws it as a new screen. Show the list to the developer in a few lines and confirm it before capture. The scenarios are the contract's: this skill never invents or reorders a flow.
2. **Reuse first.** `ls <REPO>/../skunexus-client-*/.ai/*/prototype/sn-baseline.md` (sibling client repos). A section captured at the same core major version can be copied with a "copied from …" note. Global chrome and the visual system are core-wide and usually reusable. Capture only what's missing.
3. **Preflight the browser** before launching the agent: `ToolSearch` `select:mcp__chrome-devtools__list_pages`, then `list_pages`. If no browser answers, tell the developer: the build can still run on reused sections and code, and the storyboard is published marked "unclicked".
4. **Local writes** (creating a test order, driving one through pick and pack): ask the developer. A grant covers the local app and DB only; the brief forbids queue workers (after checking none can run) and requires an undo log. With no grant, the page state is drawn from code plus the reused baseline, marked "drawn from code, not captured" in `sn-baseline.md`.
5. Copy `assets/briefs/capture-brief.md` to `prototype/CAPTURE-BRIEF.md`, fill `<PAGES>` (step 1's list), `<WRITES>`, `<CONTRACT>` (the frozen snapshot paths) and the standard placeholders, and run **one** `sn-scout` capture agent (~30 min). Keep capture and build separate agents: a combined one died with too much in its context.

**The look source is the developer's stock local app** (`<LOCAL_APP_URL>`), not a client environment. Client dev and stage sites carry overlays, and `sn-baseline.md` wins over any other style reference.

## After the capture

- Read the agent's reply, not the baseline: pages captured, reused, pending and not captured. A page left pending in the local app (a queued job, an unconfirmed statement) goes to the developer at once.
- A stock page that contradicts the contract (a requirement places something the stock page doesn't have) is a `WRONG` entry in `feedback.md`, source `storyboard v1` or `v2`, citing the id and the baseline section. On FFD-14 a requirement printed a packet "next to the packing slip", which stock Packing never prints.
