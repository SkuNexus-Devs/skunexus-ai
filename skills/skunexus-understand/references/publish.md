# Publish: one local file, one URL, a version table

You publish; agents never do (they have no Artifact tool). The local file is the only publish source, so the developer keeps one link per `<KEY>` and every version can be traced to a head SHA and the sources it was built from. Publish once the check passes and the verify findings are applied. The artifact stays private: the developer decides whether a reviewer gets the link.

## First publish

1. `Artifact quickstart intent:"other", design_systems:false`. Its result counts as the `artifact-design` load.
2. Load the `artifact-capabilities` skill once: the Artifact tool requires it before any publish that passes `capabilities`.
3. `Artifact publish` with:
   - `file_path`: `<DIR>/explainer.html` (the publish file: no doctype; the artifact wraps it);
   - `icon: "book"`;
   - `title`: the page's `<title>`, i.e. `plan.json` `title` ("ABC-123 Stock Reservations"). It never changes between versions, and the stage never enters it;
   - `description`: one sentence, e.g. "Private page and quiz: what ABC-123 asked, built and proved, at abc1234." Intent-only: "Private page and quiz on what ABC-123 asks, before code.";
   - `label`: `Explainer @<sha7>`, plus ` · intent-only` on an intent-only page;
   - `capabilities`:
     ```json
     {"db": {"rules": [{"path": "results", "read": "self", "write": "self"},
                       {"path": "results/{self}", "read": "view", "write": "interact"}]},
      "user": {},
      "comments": {"composer_only": true}}
     ```
     Each viewer reads and writes only `results/<their id>`, and nobody else reads it, the owner included. You, reading through `ArtifactData` as the developer, see only the developer's own document. Comments open the host's composer on a section; the page builds no thread list of its own.
4. Create `<DIR>/artifact.md` (below).
5. **Read back once:** load `ArtifactData` (`ToolSearch` `select:ArtifactData`) and list the `results` collection of the new URL. An empty list with no error confirms the rules took. An error: tell the developer the page works, but the result must be pasted: Copy result, under the quiz.

Never share or pin the artifact. Pin it only if the developer asks.

## The Built-from line

Two forms of the same facts. **The page** shows them under Sources → "About this page", with no file names (a local path never reaches the page):

```
Built from: the head of ABC-123 (commit abc1234) against origin/dev (merge base 9f8e7d6) · contract v2 (Approved) · 3 local notes, not online · 2 online
```

**You** use the full form, in the hand-off and in `artifact.md`'s Inputs cell, from `map.json`, `plan.json` `contract` and the hashes in xd-data `meta.inputs`:

```
Built from: ABC-123@abc1234 vs origin/dev@9f8e7d6 · contract v2 (Approved) · prd.md@1a2b3c4d · decisions.md@5e6f7a8b · spec-from-tests.md@9c0d1e2f · storyboard: contract v2
```

- The head part is the `Scanned` cell of `artifact.md`. Intent-only, it records where the code stood.
- `contract v<N> (<status>)` appears only when `prd.md` has a `> Versions:` block (`inputs.md` §5); else `prd.md@hash8` alone identifies the ask.
- Each source in `plan.json` `sources` appears as `name@hash8` (`tr -d '\r' < <file> | sha256sum | cut -c1-8`); the page counts them only. A source that a ref quotes and whose origin has a `url` counts as online; every other is a local note.
- `storyboard: contract v<N>` appears when `prototype/artifact.md` exists; say so when it differs from the contract version.

So a later session can tell what the page was built from without opening it.

## Each later version

| Situation | Calls |
|---|---|
| A rebuild at a new head, a moved source, or a fix | Every rebuild is a full rebuild. `Artifact read url` (confirm the live page is the version `artifact.md` says) → publish the same `file_path`, or pass `url` from `artifact.md` in a new session. New `label` and `description`; no `icon`; omit `capabilities` to keep them. Add a row. The artifact keeps its own versions, so no local backup is made |
| An intent-only page gets code | The same URL: the page grows into a full one. The label drops ` · intent-only` |
| A new session | `artifact-design` and `artifact-capabilities` load once before the first publish. Without `url`, a publish creates a second artifact: always pass it |
| A text-only fix | Publish, then `Artifact read` with a `prompt` to confirm the string is live |
| Never | Republish from an `Artifact read` copy: it isn't byte-identical to the file you published |

A rebuild keeps the URL, so a reviewer's link always opens the newest version. The engine keeps a piece's "I've read this piece" tick only while its content is unchanged.

## `<DIR>/artifact.md`

```
# ABC-123 explainer artifact

- **URL:** <artifact URL> (private; the developer shares it)
- **File:** `.ai/ABC-123/explainer/explainer.html` · title "ABC-123 Stock Reservations"

| Scanned | Date | Label | Inputs | What changed | Checks | Quiz |
|---|---|---|---|---|---|---|
| ABC-123@9f8e7d6 vs origin/dev@9f8e7d6 | 2026-11-04 | Explainer @9f8e7d6 · intent-only | contract v1 (Approved), prd.md@0a1b2c3d, workflows.md@4e5f6a7b | first build: 12 criteria, all not built | light: check OK; blind 1/5; unclicked | first try 5/5 · 2026-11-04 |
| ABC-123@abc1234 vs origin/dev@9f8e7d6 | 2026-11-10 | Explainer @abc1234 | contract v2 (Approved), prd.md@1a2b3c4d, decisions.md@5e6f7a8b, spec-from-tests.md@9c0d1e2f | contract v1 → v2: R2.b changed, R1.c new (FB2); first code: 14 commits; 9 tested · 3 built | full: check OK; fact-check 41 ok, 2 fixed; blind 1/5; teach 5/5; clicked | not taken |
```

One row per published version; the newest is last.
- **Scanned:** `<head ref>@<head sha7> vs <base>@<merge-base sha7>`, the same as the page's Built-from line. `skunexus-backend-pr` compares this head with its HEAD.
- **Inputs:** the contract version and status, if any, then each source file as `name@hash8`, or `PR #482 body` and `jira` in reviewer mode.
- **What changed:** `first build` on the first row. Later: the line `inputs.md` §7 produces (contract and PRD deltas, new decisions and scenarios, commits since), then the trace counts that moved.
- **Checks:** the depth (`light` or `full`), then the check result, fact-check counts, blind hits per round (`blind 8/12 → 4/12`), teach score, and `clicked` or `unclicked`.
- **Quiz:** `not taken` until a result is read back; then one line, e.g. `first try 5/5 · 2026-11-10` or `first try 4/5; q3 cleared · 2026-11-10` (`references/quiz.md` §10).
- No Artifact tool: the URL reads "not published (no Artifact tool)".
- Built, with the publish left to someone else (the developer, an orchestrator): the URL reads "built, not yet published (<who> publishes from `explainer.html`)", and the Label cell holds the label that publish will set.

## Staleness

The page is stale when the head ref or the merge base moves, or when a source it was built from changed. In reviewer mode, re-fetch `origin/pr/<n>` first (`inputs.md` §1). Two git commands settle the head against the newest row:
```bash
git rev-parse --short <HEAD>
git rev-parse --short "$(git merge-base <BASE> <HEAD>)"
```
`check-explainer.py <DIR> --stale` does the same against the named ref and merge base in `map.json`, and exits 3 when stale. The default run (no flag) fails when `map.json`, `plan.json`, `quiz.json` or a fragment changed since `explainer.html` was built, and warns "why-source changed since build: prd.md@old → @new" for each source whose hash moved. The contract version and the storyboard are compared by hand (`inputs.md` §7). Never present a stale page as current; the hand-off says "built at `abc1234`, 3 commits behind" or "built from contract v2; the contract is now v3".

## The hand-off

One message, in this order (`SKILL.md` step 13):
1. The link (or the local path) and the Built-from line.
2. **What changed** since the last version, when there is one: the `inputs.md` §7 line, naming the contract and PRD deltas by id: "contract v2 → v3: R2.b changed, R5.a new (FB7); decisions: D4 new; 2 new scenarios; 3 commits since abc1234."
3. The trace status line, then each criterion that is `not-built`, `untested` or `drift`, one line each, `drift` first.
4. The pieces (main flow and under Go deeper), generated files and files; hotspots.
5. Each drift (`needs_decision` first) and open question, one line each; the deploy and rollback notes.
6. Any instruction found in the sources (`inputs.md` §9).
7. The verify results: blind hits per round, and each question still hit after the last round with its tag (`quiz.md` §7).
8. The gate, in the page's own words: "Answer the 5 questions under Check yourself (Start here's last step) before you go on: your first pick on each is your first try. If you miss any, explain your misses to Claude: press Copy result under the quiz and paste it here, or tell me you're done and I'll read your result from the page; then explain, in your own words, why each answer is what it is." Without a published page: "… paste it here" only.
9. When the ticket has a PR, or one is coming: say that `skunexus-backend-pr` will put the page's PR header (below) on top of the PR body.

Intent-only, items 4 and 5's code parts drop out, and item 3 lists only the deferred and open rows.

## The PR header

A PR whose ticket has a published page opens with the page, and folds its regular description, the way the page itself folds tests and merge notes. `skunexus-backend-pr` writes the whole body (its Step 0.4); this is the block it puts on top. Fill it from the page as built:

```html
<p align="center">
  <a href="<URL>" target="_blank" rel="noopener">
    <img src="https://img.shields.io/badge/Open_in_Claude-<BADGE>-D97757?style=for-the-badge&amp;logo=claude&amp;logoColor=white&amp;labelColor=1F1F1E" alt="Open in Claude: <TITLE>" height="40">
  </a>
</p>

<p align="center">
  <b>Start here: <TITLE></b><br>
  A guided page for reviewing this PR: <THE MAP>, the <N> pieces of the change next to their code, all <F> changed files in place, and a <Q>-question check.<br>
  <sub>Opens in claude.ai · Ctrl/⌘-click to keep this tab</sub>
</p>

---

<details>
<summary><b>The regular PR description</b> (<SECTIONS>)</summary>

…the description skunexus-backend-pr drafted, unchanged…

</details>
```

- `<URL>`: `artifact.md`'s URL. `<TITLE>`: the page's `<title>` (`plan.json` `title`), e.g. "ABC-123 Stock Reservations".
- `<BADGE>`: the title in shields.io's path form, then the arrow: `-` → `--`, a space → `_`, then `_%E2%86%97` ("ABC--123_Stock_Reservations_%E2%86%97").
- `<THE MAP>`: what the map shows, in a few words ("the map of the three places that decide a reservation"); with no map, "what to carry into the review". `<N>`: the main-flow pieces; `<F>`: the changed files; `<Q>`: the final questions. Use the page's own words and counts. An intent-only page has no PR yet, so no header.
- `<SECTIONS>`: the folded description's own section names, in a few words ("problem, fix, tests, merge notes").
- The link goes to a private page: it opens for the people the developer has shared it with. Say so in the hand-off; the skill never shares it.
- GitHub serves the badge through its own image proxy (`camo.githubusercontent.com`). Right after a save, its editor may render the raw shields.io URL once, and the browser console reports a Content Security Policy block; a reload shows the badge. Nothing to fix. GitHub also drops `target` and `rel` from the link (it renders `rel="nofollow"`), so a plain click leaves the PR: that is why the header says "Ctrl/⌘-click to keep this tab".

## Reading the result back

- **From the page:** `ArtifactData` list on the `results` collection of the URL in `artifact.md`. You see only the developer's own document, keyed by their user id and holding `{<built_from>: {line, correct, total, at}}`. Use only the entry for the page's `built_from`. No entry: the quiz isn't finished yet, the developer used Reset quiz (it deletes this build's entry), or they viewed without write access; ask for the pasted line.
- **Pasted:** the developer pastes the result line (Copy result, under the quiz).
- **Then:** verify it against `quiz.json` and record one line in the Quiz cell (`references/quiz.md` §10). Never infer a pass.

## No Artifact tool

Skip the publish, write `artifact.md` with "not published (no Artifact tool)" as the URL, and continue with the hand-off and the gate (`SKILL.md` steps 13–14), using `<DIR>/explainer.local.html` (it opens from `file://`) and pasted result lines. The developer can publish later from a session that has the tool.
