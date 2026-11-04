# Publish: one local file, one URL, a version table

You publish; the build agent never does. The local file is the only publish source, so the PO keeps one link and every version is auditable. Publish storyboard v1 only when the developer asks (it is internal); publish v1.x and v2 and later once the checks pass. The artifact stays private until the developer shares the link: v1.x with the share post below, v2 and later usually with the estimate comment.

## Versions

| Change | Version | Badge |
|---|---|---|
| Discovery build from a frozen contract | v1; fixes v1.1, v1.2 | "Internal draft v1" |
| Rebuild after the developer's triage (`STAGE='discussion'`) | the next v1 minor (v1 → v1.1) | "Draft for discussion <DATE>", plus the engine's open-assumption count |
| First PO-facing build from an approved contract | v2 (a ticket that skipped discovery still starts at v2) | "Draft v2" |
| A rebuild from a new contract version, or a new scenario | next major (v2 → v3) | "Draft v3" |
| Text and chrome fixes | next minor (v3 → v3.1) | "Draft v3.1" |

The badge, the publish `label` ("Storyboard v3") and the `artifact.md` row carry the same number. The `<title>` never changes.

## `prototype/artifact.md`

```
# <TICKET> storyboard artifact

> Built from: contract v2 (2026-11-03)

- **URL:** <artifact URL> (private; the developer shares it)
- **File:** `prototype/<SLUG>-storyboard.html` · title "<TITLE>" · backups `<SLUG>-storyboard-v<N>.html`

| Version | Date | Label | Built from | Trigger | What changed |
|---|---|---|---|---|---|
| v2 | 2026-11-03 | Storyboard v2 | contract v2 (2026-11-03) | contract approved (G2) | 2 scenarios, 9 steps, 4 index rows; 2 parts; check OK; clicked through |
```

- **Built from** holds the page's `BUILT_FROM` exactly. A cell that doesn't start with `contract v` is legacy (no base): rows written before this skill (`review/prd-v2-2026-10-28.md`, `PRD v2 (2026-10-26)`) stay as written.
- The `> Built from:` line under the title equals the newest row's cell; update both at each publish. The FE plan names `artifact.md@<hash>`, so each new row marks the FE plan for a re-check.
- **What changed** is for the developer: scenarios × steps, index rows, parts, the `FB` ids filed, check and click-through results ("unclicked" when no browser answered). G6 is recorded here when the developer reports the PO's yes: `PO: <DATE> approved v<N> with the estimate`.

## Sharing v1.x

A v1.x page is shared with the PO and the FE developer at the same time, unpriced. Its `BUILT_FROM` names the version the triage cut, and `run.md` has `triaged v<N>` with that same `N`. Its `artifact.md` row's Trigger reads `triaged v<N>`. After `check-storyboard.py` passes, draft `review/share-<DATE>.md` for the developer to post (model.md §8, "Triage"):
- the v1.x link;
- a 3-line summary: what the ticket adds, what is still assumed, what happens next;
- at most about 7 lettered plain questions, each deep-linked to its step (`<URL>#s1.3`), with no ids or file names in the wording;
- a paste-ready "Open questions for the client" block;
- the date the estimate follows.

Cross-check any client summary the PO writes against the decision list. The PO's answers go in as `CHANGE` entries, source `PO <DATE>`, through `skunexus-contract`'s rulings door.

## Publishing

| Situation | Calls |
|---|---|
| First publish | `Artifact quickstart intent:"other", design_systems:false` (it counts as the `artifact-design` load) → `Artifact publish` with `file_path`, `icon:"layout"`, `title`, a one-sentence `description`, a `label`. Create `artifact.md` as above. Private; never share or pin it |
| No Artifact tool in this session | Stop after the checks. Give the developer the local file path and write `artifact.md` with "not published (no Artifact tool)" for the URL; they publish later from a session that has it |
| Each later version | Back up the previous file as `<SLUG>-storyboard-v<N>.html` (the build agent does this on a revision) → `Artifact read url` (confirm the live page is the expected version) → publish the same file path, or pass `url` from `artifact.md` in another session. New `label` and `description`, no `icon`. Add a row |
| `artifact-design` | A republish from a new session loads it once before the first publish. The storyboard's light-only theme overrides its dark-mode rule: never add dark tokens |
| Text-only fix | Publish, then `Artifact read` with a `prompt` to confirm the string is live |
| Pause | SendMessage the build agent: "STOP now: add the 'WIP — PAUSED <DATE>' badge and save; I'll publish." Publish as above if the developer wants the partial page live |
| Never | Republish from an `Artifact read` copy: it is not byte-identical to the file you published |

## Older storyboards

| Situation | What to do |
|---|---|
| `*-storyboard.html` with no `artifact.md` (built before this skill) | Find the URL in the ticket's memory note or with `Artifact list`, confirm it with `Artifact read`, then create `artifact.md` before publishing. Backfill only the versions the memory note records; don't invent history. Publishing without `url` from a new session would create a second artifact. No URL found: it was never published, so treat it as a first publish, asking first if the PO may already hold a link to an earlier prototype |
| A `BUILD-BRIEF.md` but no `artifact.md` (or a note "built, not published") | An unpublished first build: run the checks, then first publish |
| An older prototype in another format | Find its URL as above and ask whether the storyboard replaces it at the same URL (recommended: keeps the PO's link) or becomes a new artifact. Its drawing decisions `(a)`, `(b)` … in §7 stay as legacy `A('Dev a')` chips until a ruling turns them into `Q`s |
| No `BUILT_FROM` | No base: `--stale` counts it current. A republish or visual tweak keeps it as it is; the next rebuild re-keys it (`references/build.md` §10) |
