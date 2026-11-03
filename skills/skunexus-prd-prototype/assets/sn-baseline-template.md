<!-- Stage 8 (capture). Copy to .ai/<TICKET>/prototype/sn-baseline.md. The capture agent appends one section per
page as it goes, so progress survives a crash. Structure only: never names, emails, addresses or phone numbers.
Extra placeholders: <CORE_VERSION>, <ROLE>, <W>x<H>, <OTHER_TICKET>, <N>. Standard placeholders: see SKILL.md. -->

# SN baseline: stock SkuNexus pages (<CLIENT> local, core <CORE_VERSION>)

Captured <DATE> from `<LOCAL_APP_URL>` (developer's local app, user role <ROLE>), viewport <W>x<H>.
Purpose: the "before" picture for the <TICKET> storyboard. Structure only; no customer data recorded.
Raw a11y snapshots and screenshots: `screens/baseline/NN-*.snapshot.txt` / `*.png` (they contain customer data: keep local, never publish, never read the PNGs).
Reused sections: <none | "§7, §8 copied from .ai/<OTHER_TICKET>/prototype/sn-baseline.md (same core major)">

---

## Data log (local DB `<LOCAL_DB>` only; to undo)

Only when the developer granted local writes. One row per change, enough to undo it. List anything left pending (queued jobs, unconfirmed IDE statements) so the developer can clean it up.

| When | What | Ids |
|---|---|---|

---

## <N>. <Page name>: <state> (e.g. "Order details: open order with a core-option line")

- **Path:** `/<route>/<id-shape>` (tab title `<pattern>`).
- Files: `NN-<slug>.png`, `NN-<slug>.snapshot.txt`.
- Source: captured | "drawn from code, not captured" (no local-write grant for this state: built from <file:line> and the reused baseline).

```
+--------+-----------------------------------------------------------+
|SIDEBAR | [⟲History] <H1>                          <user> · <ROLE>    |
| 256px  | <breadcrumb>                                                |
|        | ┌ <Card title> ─────────────── [Action](variant) [Action] ┐ |
|        | │ <label> <value-shape> │ <label> <value-shape>            │ |
```

**Components and labels**
- Page header, cards (title, header actions with variant), grids (kind: main `<table>` grid or in-card div grid; columns in order; row actions), fields (label, control type), modals (title, fields, buttons), toasts (verbatim text), empty states.

**How <the thing the ticket changes> shows today (the "before")**
- What a user sees and can do today, in one or two lines per element. This becomes the step's "Today in SN" caption.

**Where <TICKET> attaches**
- Where each new or changed element would go, the way SN would place it (card header action, new card, grid column, modal), with the R-ids.

---

## <N+1>. Global chrome
Sidebar (width, colour, item list in order, active-item style), page header (History, H1, breadcrumb, user · role menu), floating widgets, toast region.

## <N+2>. Visual system
Font, colours, `.sn-button` variants and sizes, tags, cards, the two grid kinds, scan widgets, modal, tabs. End with the token block the storyboard uses:

```css
:root { --sn-font: 'Inter', sans-serif; --sn-primary: …; /* one line per token */ }
```
