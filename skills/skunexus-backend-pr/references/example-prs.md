# Liked PR examples — calibration references

Three real, developer-approved descriptions. Read them before drafting to internalize the shape
family, the depth, and the moves (annotations after each). Do not copy their sections blindly —
each shape fit *its* change; pick the shape yours has.

---

## Example 1 — new feature: "What & why / Changes" shape

**skunexus-client-phg #585** — title: `PHG-418: report partial-fulfillment orders ready for decision`

```markdown
## What & why

[PHG-418](https://skunexus.atlassian.net/browse/PHG-418) — orders decided with only partial stock
sit in `partial_fulfillment`, and the system never re-checks them when new inventory arrives, so
no one knows when the remaining units become fulfillable.

This is **not** the full Option 1 report from the ticket. After discussion we agreed on a
deliberately simplified, internal version: **we** run it on request and pass the resulting order
labels to the client. The client does not get access to it — hence the developer-only
authorization on the endpoint.

## Changes

Shared CQRS command + handler used by both entry points:
- `FindOrdersReadyForDecisionCommand` / `FindOrdersReadyForDecisionHandler` — pulls all
  `partial_fulfillment` orders, takes their undecided items
  (`DecisionItemsRepository::find()->toAvailableItems()`), computes `qtyAvailableToDecide` once
  per distinct product via the batch calculator, keeps orders where any undecided item's product
  has qty > 0, and returns an `[orderId => label]` map. Registered in `CommandsProvider`.
- `ProjectOrderRepository` — order DB access; order **label** is read from the `label` custom
  field (`order_custom_field_values` via `LabelDefinition::CODE`), not the `orders` table.

Two entry points:
- **Console command** `order-decision:report-ready-orders` — prints an Order ID / Label table.
- **Endpoint** `GET /api/phg/reports/orders-ready-for-decision` — restricted to
  `developer@skunexus.com` (resolved via `UserService`); other users are redirected to `/`.
  Returns a copy-paste-friendly, comma-separated `text/plain` list of labels.
```

**Why this works:**
- Opening = problem in one sentence, in domain terms (what hurts and why), before any code.
- The second paragraph is the **scoping note**: what this deliberately is *not*, and the decision
  that made it so — lifted from the kind of content `decisions.md`/`prd.md` record. It preempts
  the reviewer's "but the ticket said…" objection and *explains* a design choice (the developer-only
  auth) that would otherwise look arbitrary.
- `## Changes` is grouped by **seam** (shared command/handler, then the two entry points that
  consume it) — never a file list. Real names in backticks; behavior stated from the code
  ("label is read from the custom field, not the `orders` table" — a detail a reviewer would
  otherwise have to dig for).
- The real PR ended with a pointer at the one relevant commit because the branch carried dev-merge
  noise — reviewer orientation is a legitimate move.

---

## Example 2 — behavior change: "Current behavior / New behavior" shape

**skunexus-client-bb #369** — title: `BB-275: wait for queued transfer-cart-to-packing-station job
so 200 means the fulfillment is already on the packing station cart`

```markdown
## Current behavior

`POST /api/fulfillment/transfer-cart-to-packing-station` validates synchronously, then the handler
re-dispatches itself onto the single-worker `packing_station` queue and returns immediately — 200
means "validated and queued", not "transferred". FE redirects to the packing page on 200 and still
sees the old cart/tote until the worker finishes and the page is refreshed (the BB-275 report).

## New behavior

200 now means the transfer is complete — when the response arrives, the fulfillment is already on
the `<Packing Station>` cart.

    POST /api/fulfillment/transfer-cart-to-packing-station
    {
        "cart_id": "0b8649ec-b93d-42f4-bdc5-8cf7ab9be48d"
    }

Empty 200 response. Error responses are unchanged: 422 for a missing/invalid `cart_id`, and the
"Cannot transfer cart to Packing Station with invalid fulfillments: label (ID: …)" error when the
cart holds fulfillments not in pack state — both still returned immediately, before anything is
queued.

In BE, the controller now runs the command twice: `bus->handle($command)` performs the validation
pass (the handler returns right after validation), then
`QueuedCommandJob::runAndWait($command->forExecution())` dispatches the execute pass to the
`packing_station` queue and polls until the job is gone. The wait has to live in the controller,
not the handler: every `bus->handle()` runs inside a DB transaction (core `TransactionMiddleware`),
so a handler-side dispatch-and-wait would insert the job row inside the open transaction — the
worker could never see it and the request would wait until PHP timeout, rolling the job back. From
the controller the dispatch happens after the validation transaction commits. Transfers still
execute one at a time through the single-worker `packing_station` queue (the BB-189 race fix) —
only the response timing changed.

The command's flag is renamed to match its actual meaning:
`$runningInQueue`/`isRunningInQueue()`/`forQueue()` → `$validationOnly` (default
`true`)/`isValidationOnly()`/`forExecution()` — the flag distinguishes the validation pass from
the execute pass; the queue is the controller's business.
```

**Why this works:**
- The title states the *meaning* of the change, not the mechanics.
- "Current behavior" describes what 200 *meant* and the user-visible consequence — the semantics,
  not the old code.
- "New behavior" leads with the contract (concrete request example, what error responses did
  **not** change — reviewers verify against negatives too), then the mechanics.
- The controller-vs-handler paragraph is the depth benchmark: it explains a constraint the diff
  cannot show (`TransactionMiddleware` would strand the job row inside the open transaction) and
  what deliberately did *not* change (the single-worker serialization from BB-189). That's the
  "why a reviewer would trip on" bar.
- A rename gets one sentence with its reason — proportionate depth.
- The real PR also carried a `## For FE` section. **That is now produced by a separate skill —
  never write one.**

---

## Example 3 — follow-up round: delta-only description

**PHG-77 round 2** (`pr2.md`, following a merged round-1 fix) — abridged:

```markdown
## Problem

After the first round of fixes (switching `str_ireplace` → `preg_replace` with `(?<!\w)` / `(?!\w)`
lookarounds), three more real-world inputs were found where the replacement still misbehaves:

| Input          | Expected        | Actual before this PR | Cause                                       |
|----------------|-----------------|-----------------------|---------------------------------------------|
| `PO44 Main St` | `Box44 Main St` | unchanged             | `(?!\w)` rejects digits, but a digit after `PO` is a valid P.O. Box pattern |
| `P.O.Box 99`   | `Box 99`        | `BoxBox 99`           | No template covered `P.O.Box`; only the shorter `P.O.` prefix matched |
| `P O Box 77`   | `Box 77`        | unchanged             | No template covered `P O Box`               |

Cases 2 and 3 were also broken under the original implementation; they are pre-existing gaps that
surfaced once we started looking. Case 1 is a regression introduced by the previous PR's tighter
boundary check.

## Fix

Two surgical changes.

### 1. Boundary check uses letters, not word characters

Replaced every `\w` in the regex with `\p{L}` (Unicode letter class) and added the `u` modifier.
**Why:** the original bug was `PO` matching inside real *words* like `Popple`. Words are runs of
letters; digits and punctuation are not — `PO44` is `PO` followed by an address number, not a word
continuation. `\w` (letters + digits + underscore) was too broad; `\p{L}` matches the actual
semantic boundary we want.

### 2. Added three missing template variants

(`P.O.Box`, `P O Box`, `POBox` in `config/skunexus.php` defaults.)

**Note for reviewers:** customers that override `ORDER_ADDRESS_PO_BOX_TEMPLATES` via env will need
their env value updated separately — only the defaults are changed here.

## Behavior summary

| Input          | Before this PR | After this PR   |
|----------------|----------------|-----------------|
| `PO44 Main St` | `PO44 Main St` | `Box44 Main St` |
| …              | …              | …               |
```

**Why this works:**
- **One clause** ("After the first round of fixes…") anchors the reader to round 1; everything
  else is only the new work. Re-explaining the merged round would bury what this reviewer must
  actually judge.
- It classifies each new failure honestly: which are pre-existing gaps vs a **regression the
  previous round introduced** — that honesty is what makes the description trustworthy.
- The env-override callout is the canonical **env/config reviewer note**: the diff changes a
  default; the description says who is *not* covered by the diff.
- Fresh before/after table scoped to this round's inputs.
