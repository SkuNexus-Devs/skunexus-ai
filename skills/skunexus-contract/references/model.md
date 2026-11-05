# The contract model

The shared reference for `skunexus-contract`, `skunexus-storyboard` and `skunexus-backend-plan`'s parallel-drafting door. The other two read it by sibling path: `../skunexus-contract/references/model.md`. Every rule below traces to one principle: **one contract, many views**.

## Why

A storyboard is cheap to draw, but on its own it looks finished while it rests on guesses, so a picture can mislead the people who see it. Everything in this model exists so that no guess goes unseen: a draft can be shared early with its guesses marked, but nothing is priced, approved or built on a guess (§8, "Sharing").

- **Foundation: what a prototype needs before anyone else sees it.**
  - The evidence on disk: a fresh pull of the ticket.
  - The PO baseline: what the PO has already decided.
  - Stock pages captured from the app, not guessed.
  - Render-ready pages (§1): every element decided, assumed with a chip, or stock.
  - Parts in the PO's shape only.
  - Every guess visible: chipped on screen, or on the presenter sheet. A recorded triage of every guess that moves scope or price comes before anything is priced or approved, and before the "not reviewed" badge comes off (§8).
- **Why the investigation is heavier than on the regular route.** It is where the errors were caught, and it costs little next to the rest of a run:
  - the stock-page capture caught FFD-14's "next to the packing slip" line, which two panel reviewers repeated as written;
  - capture plus build is 6–10% of a measured run's tokens;
  - none of 28 regular-route PRDs on disk records a default for an open item, and drawing needs one for every element;
  - the PO has asked for the storyboard format on every FFD ticket since FFD-14, and changed FFD-14's scope by pointing at its storyboard.
- **Why unattended runs plus triage.** The run researches the ticket, captures the stock pages, drafts the contract with every guess marked, draws an internal storyboard and stops at a ranked decision list, with no plan and no hours. The developer then confirms or flips every guess that changes scope or price in a short, recorded triage. The triaged version is shared as a reviewed draft for discussion, with its open questions counted and no price; when a call comes before the triage, the draft is shared anyway, badged "not reviewed" (§8, "Sharing"). The PO and the FE developer see it together and answer a short list of plain questions, so polish questions can come up before the estimate rather than in QA, and the estimate follows their answers.
  - **What the evidence supports:** the PO values the format (6 of 6 FFD tickets asked for it), and it is cheap.
  - **What RL-47 showed** (pilot 1, 2026-11-05: attended, `storyboard-only`, shared untriaged an hour before the client call): the share was acted on in the call itself, with 8 contract decisions and a dated v2 and approval request; by the developer's estimate, a call without it would have covered 20–40% of the material, with approval weeks later. About 9 expectation items surfaced before QA, through the drawing rather than its chips. The cost was about 10 statements corrected in writing: half came from narration, and the decisions that moved were contract rules with no chip, which a triage would not have caught. Hence: share early, bind late (§8, "Sharing").
  - **What the pilots must still show:** that the unattended defaults hold (FFD-17: 1 of 2 reviewed overturned; RL-47, attended: 2 of 7 touched assumptions overturned); that the triage fits in 15–30 minutes; and that QA and UAT rounds shrink.

## 1. Contract, views, rules

**The contract** is the single source of truth for what the feature does. It is two files in `.ai/<TICKET>/`:

| Facet | File · section | Holds |
|---|---|---|
| Rules | `prd.md` §4 (`R` ids), §6 (lettered criteria `R.a`) | what must hold, each criterion falsifiable |
| Decisions and assumptions | `prd.md` §7 (`Q`, `J-` ids) | every open item decided, or assumed with evidence or an owner |
| Use cases | `workflows.md` scenarios (`s`) and steps (`s.M`) | actor, trigger, state before → after, outcome, cited ids, part |
| Parts | `workflows.md` "Parts" | the PO's priced scope; every step carries one |
| Provenance | `jira/`, `input/`, `research/`, `review/po-baseline.md` | evidence on disk, dated; the first pull is never overwritten |

`prd.md` keeps `skunexus-jira-prd`'s template, so every existing skill reads it unchanged. A ticket without `workflows.md` is a regular-route contract: rules and decisions only.

**Views** serve one audience each and add only binding:

| View | File | Audience | Binding it adds | Owner · gate | Coverage scope (rule 3) |
|---|---|---|---|---|---|
| Storyboard | `prototype/<slug>-storyboard.html`, `prototype/artifact.md` | PO, client | pages, states, the parts switch | developer · G6 | every live step; every assumed `Q` a drawn step cites |
| BE plan | `backend-plan.md` | developer, tech lead | commands, events, sync or queued | developer, tech lead reviews · G3 | every live criterion |
| FE plan | `frontend-plan.md` | FE developer | components, API calls, validation, FE hours | FE developer · G4 | every live step whose trigger is `user` |
| Estimate | `estimate.md` | PO | hours per part | developer · G5 | every live part |
| Code and tests | the PR | tech lead | code; tests named after their criterion, one scenario test per live scenario with backend effects | developer · G7 | every live criterion and every such scenario (backend-plan's `Tests:` trailers) |
| QA steps, FE hand-off, backend summary | their skills' files | QA, FE developer, team | steps, API per journey step, map of shipped code | their skills · G8 / none | unchanged skills; they read `prd.md` as today |

**The four rules of views.**
1. A view adds binding (pages, mechanisms, hours), never behaviour. A view that needs behaviour the contract lacks files feedback (§6); it does not invent it.
2. Behaviour reaches another view only through the contract: feedback → rulings → a new contract version. Views never pass behaviour to each other.
3. Permanent ids are the join keys. Coverage reads both ways, and a contract change marks views stale by id (§5).
4. Each view has an owner and a gate (§7). Drafts have no gate.

**Render-ready.** Nothing is drawn or built unless each element is *decided* (contract text), *assumed* (a `Q` with a visible chip) or *stock* (a captured page, unchanged). The two storyboards treat a gap differently:
- **Storyboard v1** (discovery, internal) draws the simplest option, files a `CHOICE` entry in `feedback.md`, and marks the element with a chip keyed by that entry's id (`A('FB3')`). Finding these is v1's job: FFD-13's nine drawing decisions came out of this fallback.
- **Storyboard v2** (PO-facing) and every other view stop. The element goes to `feedback.md` and waits for a ruling.

**Phases.** discovery (storyboard v1 ‖ panel; a plan draft only when asked) → rulings (G1, G2) → sizing (BE plan ‖ storyboard v2 → FE plan → estimate) → PO gate (G6) → build (G7) → verify (G8). Feedback costs more at each phase: a ruling, then a re-estimate, an amendment the PO re-approves, a code change, a bug.

## 2. Ids

### 2.1 Contract ids (permanent)

| Id | Example | Defined in | Notes |
|---|---|---|---|
| `R<n>` | `R4` | `prd.md` §4, `- **R4** …` | requirement |
| `R<n>.<letters>` | `R4.b`, `R4.aa` | `prd.md` §6, `- **R4.b** …` | criterion; letters `[a-z]+` in every script (a … z, then aa) |
| `Q<n>[a-z]?` | `Q26`, `Q3b` | `prd.md` §7 | question, assumption or decision |
| `J-<n>` | `J-4` | `prd.md` §7 "For the tech lead" | question for the tech lead |
| `s<n>` | `s4` | `workflows.md` scenario table | scenario |
| `s<n>.<m>` | `s1.3` | `workflows.md` step table | step; a storyboard page is keyed by it |
| `Part <n>` | `Part 2` | `workflows.md` "Parts" | priced scope |
| `FB<n>` | `FB7` | `feedback.md` | feedback entry (not `F<n>`: FE plans and review files already use it) |
| `(<letter>)` | `(j)` | `prd.md` §7 | legacy drawing decision (PR A runs). New drawing problems become `FB` entries, and a ruling gives them a `Q` |

- **Never renumber, never delete.** Retire the id and take the next free one, because views, tests and links cite them. Gaps never appear: `R1 … Rmax` is complete, and criterion letters run without holes.
- **Retirement form:** `- **R2** (retired 2026-11-03, v2: merged into R3 → see R3)`, or the whole line struck through as `~~…~~`. The same form applies to criteria, steps (`s1.4` row: `(retired …)` in the Outcome cell), parts and feedback. A `Q` is never retired: it ends as `Decided` (§3).
- **Next free id.** A new criterion takes the next letter under its requirement; a new step takes the next `m` in its scenario.

### 2.2 Ids that are not contract ids

- **View-local:** `T<n>` BE plan tasks; `FE<n>` FE plan items; `D<n>` entries in `decisions.md` (backend-plan's design log); `A<n>` acceptance items of backend-plan's inline Goal & Acceptance block (no `prd.md`). Views cite contract ids. The contract cites a view-local id only as evidence (`backend-plan T11`), never as a rule.
- **Review-local:** ids that live inside one review or research file: `PO-n`, `X-n`, `#n`, `DV-n`, `V<n>-<k>`, `P-n`, `PD-n`, panel `Q-n` (with hyphen), panel tech-lead items `TL-n` (PR A wrote them `J-n`, which collides with the contract's `J-<n>`), `I-n`, `E-n`, `RC-n`, `CK-n`, `NEW-n`, `C-n`. They reach the contract only through rulings, which record the mapping: `panel Q-3 → Q21`, `PD-2 → FB4 → Q26`.
- **Research files** are cited as `research/R2-<slug>.md` or `research R2`, never as a bare `R2`, which would read as a requirement.
- **Role labels are not ids.** Brief roles (drafters D1/D2, analysts A1–A4, researchers R1…Rn, B0/B1, V1–V3) never appear as bare tokens in contract files. A writing rule, not checked: older contracts mention "drafts D1/D2" in their headers.

### 2.3 Foreign ids

Another ticket's ids carry its key: `FFD-14 R31`, `FFD-14's R26`, `FFD-14 Q1/R26`. A line whose bold lead names another ticket (`- **FFD-14 follow-up: …**`) is about that ticket. Every check skips both forms.

### 2.4 Patterns the scripts share

```
CONTRACT_ID = R\d+(?:\.[a-z]+)?|Q\d+[a-z]?|J-\d+|s\d+(?:\.\d+)?|Part \d+|FB\d+
R_DEF       = ^\s*(?:[-*]\s+)?(~~)?\*\*(R\d+)\*\*(.*)$                    # §4
AC_DEF      = ^\s*(?:[-*]\s+)?(~~)?\*\*(R\d+)\.([a-z]+)\*\*(.*)$          # §6
Q_DEF       = ^\s*(?:(?:[-*]|\d+\.)\s+|\|\s*|#{3,6}\s+)?(?:~~)?(?:\*\*)?(Q\d+[a-z]?|J-\d+)\b   # §7
RETIRED     = leading ~~, or "retired" within the first 80 characters after the id;
              in a table row: the id cell struck through, or a cell starting "(retired" or "retired"
FOREIGN     = (?:\b[A-Z][A-Z0-9]+-\d+(?:'s)?|\b[Rr]esearch)\s+<ID>(?:\s*(?:/|,|–|—|-|and|or|&|\+)\s*<ID>)*|\bresearch/R\d+
```

In contract files, text inside backticks and HTML comments is not a citation; quoted text still is (only the placeholder check skips it). In a plan, the ids in its trailers (`Satisfies:`, `Tests:`, `out-of-suite:`) count even inside backticks, because plans write them that way; with `workflows.md`, a scenario counts as tested only when a `Tests:` trailer cites `s<n>` (a step id alone does not), `out-of-suite: s<n> — <why>` covers a whole scenario, and `out-of-suite: s1.2 — UI only` covers one step. `check-contract.py` keeps the PRD checks unchanged. Every script (`check-contract.py`, `check-storyboard.py`, `check-plan.py`, `--stale`) checks a family only when the file that defines it exists: `s` and `Part` need `workflows.md`, `FB` needs `feedback.md`. So a regular-route PRD that mentions "Part 2" in prose raises no error.

## 3. `prd.md`: header, §7, markers

**Header** (blockquote lines right under the title, `Status` first: older tools read the first `status` match):

```
# PRD: FFD-17 — Tuner serial number at decision

> Status: Approved
> Source: Jira FFD-17 (pulled 2026-11-01, re-pulled 2026-11-04) · input/meeting.md · research R1–R4 · review/po-baseline.md
> Versions:
> - v1 2026-11-02 frozen: unattended draft, 44 defaults
> - v2 2026-11-03 approved: changed R4.b; new Q26, R1.g; from FB1, FB2
> - v2.1 2026-11-04 approved: changed Q12, Part 1; retired Part 2; from FB4
```

- **Status:** the first word after `Status:` is `Draft` or `Approved`; the rest is free text (older PRDs write `Approved v2 (2026-10-28, developer)`), except two markers the checks read: `(lite)`, a lite contract (§6 optional, a requirement needs no criterion), and `(amending approved v<N>, <DATE>)`. Only the developer's explicit yes sets `Approved` (G2).
- **Version line grammar:** `> - v<N>[.<M>] <YYYY-MM-DD> <frozen|approved>: [<note>; ][changed <ids>; ][new <ids>; ][retired <ids>; ][from <FB ids>]`. The first version's line carries a note only. The ids cover both files; `from` names the feedback the version rules on. §5 says when a version is cut.
- **Legacy headers.** The version checks (§5) run only when the header has a line that is exactly `> Versions:`, followed by `> - v…` bullets. Every other shape (`> Version: …`, `> v2 <DATE>: applied …`, a one-line `> Versions: v1 … v2 …`, dated `Changelog` lines) is legacy: reported once as information, never an error.
- **Adoption.** A `prd.md` that is `Approved` with no `> Versions:` block (approved in `skunexus-jira-prd`, or any regular-route PRD) is adopted before the contract changes it. Cut `v1 <DATE> approved: adopted from <source>` with its snapshot, then work as an amendment (§5, item 3). Legacy version lines stay as written.
- `Source` names every input, so a reader can tell what the contract was built from.

**§7.** The heading stays `## 7. …` (the scripts key on the number). It has up to four groups, each optional:
1. **For the PO / client:** `Q` entries.
2. **For the tech lead:** `J-` entries.
3. **External inputs:** waiting on someone outside the team.
4. **Decision log:** every `Q` and `J-` that is decided.

Group headings are not checked: older PRDs use their own, and some keep the Decision log as `## 8.`. Each entry starts with its id and one of three states:

| State | Shape | Render-ready? |
|---|---|---|
| Open | `- **Q9** <question> Options: (A) <PO-literal> [PO decided] · (B) … [silence] · (C) … [expansion, M]. Evidence: …` | no |
| Assumed | `- **Q9** <question> Assumed: <default>. Evidence: <file:line or quote>. Confirm with <role>.` | yes, with a chip |
| Decided | `- **Q9** <question> Decided 2026-11-03 (developer, option B): <answer> → R4.b, s1.3.` | yes |

- **A `Q` is never deleted.** An answered question moves to the Decision log with its id, because chips, `QT`, citations and rulings point at it. `skunexus-jira-prd` clears answered items. So the contract saves a seed snapshot, `review/prd-seed-<DATE>.md` (not a version), before it hands over the interview, and its harden door restores every seeded `Q` that came back missing as `Decided`, citing where the answer landed. `check-contract.py --prev <seed snapshot>` lists them.
- **Inline markers** in §4 and §6, and in a `workflows.md` step's Outcome cell (with the `Q` also in its Cites cell): `(assumed, Q9)` or `(Developer choice, confirm with the PO: Q9.)`. Every marker names a §7 id whose entry says `Assumed` (or `confirm` / `default`). An `Assumed` entry should name its evidence or the role who confirms it; `check-contract.py` warns when it names neither (a warning, so PRDs written before this rule still pass).
- **Lettered options:** the ticket-literal or PO-literal option comes first, each tagged `PO decided`, `silence` or `expansion, S/M/L`.

## 4. `workflows.md`: use cases and parts

```
# Workflows: FFD-17 — Tuner serial number at decision

> Contract: versioned with prd.md (see its Versions line)

## Scenarios
| Id | Scenario | Actors |
|---|---|---|
| s1 | Jellybuilt-tuned Hydra (a vendor tune) | integration, warehouse user, system |

## s1. Jellybuilt-tuned Hydra (a vendor tune)
| Step | Actor | Trigger | Before → after | Outcome | Cites | Part |
|---|---|---|---|---|---|---|
| s1.1 | integration | integration | — → order Open, undecided | the order-create auto-decide skips it quietly | R10, R10.a, R1 | Part 1 |
| s1.3 | warehouse user | user | kit split, no serial → unchanged | Create Fulfillment refused, naming the item | R4, R4.b, Q26 | Part 1 |

## Parts
| Part | Name | Scope | PO's shape | Status |
|---|---|---|---|---|
| Part 1 | Tuner serial workflow | Serial capture at decision, the refusal without one, the quiet auto-decide skip and the vendor PO email. | base | live |
| Part 2 | PO email branding | The FFD logo and reply address on vendor PO emails. | priced separately | retired v2.1: merged into Part 1 (Q12) |

## Not exercised
- R21.b: email subject carries no environment label; proved by a test, no user step shows it.
```

- **Trigger** is one of `user`, `system`, `schedule`, `integration`. **Actor** is a role, never a person's name.
- **Before → after** is the entity's state. **Outcome** is what the actor sees. A step whose outcome contradicts a criterion is a `WRONG` entry, not a silent fix.
- **Every step row fills its Part cell;** that cell is the only source of part membership. The Parts table's Scope is one or two plain sentences for the PO, with no ids. The estimate prices parts, the storyboard shows them, and both copy Name and Scope verbatim.
- **Coverage, both ways** (`check-contract.py`):
  - every live criterion, and every live requirement with no live criterion (in a lite contract, every live requirement), is cited by at least one live step, or is listed under "Not exercised" with a reason;
  - every live step cites at least one live `R` or criterion;
  - every cited id resolves;
  - every `Part` a step names is in the Parts table.

## 5. Versions, snapshots, staleness

**When a version is cut** (by the contract skill only):
1. **Freeze for readers:** before a panel, a storyboard build or a plan draft reads the contract. The version is `v<N> … frozen`; edits queue until the readers finish, because reviewers who read a moving file report contradictions that aren't there (FFD-13).
2. **Approval (G2):** `v<N> … approved`. Approving a frozen version unchanged reuses its number and snapshot (a second line for the same `v<N>`); any change takes the next number.
3. **Amendment of an approved contract:** status `Draft (amending approved v<N>, <DATE>)`, then `v<N>.<M> … approved` on the developer's yes. The estimate is revisited before the PO sees it. **Just the storyboard** (an approved PRD with no `workflows.md`): adoption plus a workflows-only amendment (rules unchanged) is approved in the same message as the storyboard v1 review: one yes, and no restart before v2. An entry v1 files that would change a rule takes the rulings door as usual.

**Snapshots.** Cutting a version copies both files, never to be edited again: `review/prd-v<N>-<DATE>.md` and `review/workflows-v<N>-<DATE>.md`. A version line without its snapshot is an error (a `workflows` snapshot is required once an earlier version had one). An id that was in the newest snapshot and is gone from the live files is an error in any status: retire, never delete. A snapshot is exactly a file matching `^review/(prd|workflows)-v(\d+(?:\.\d+)?)-(\d{4}-\d{2}-\d{2})\.md$`; other `review/prd-v*` files (briefs, checks, pre-edit copies) are not snapshots. The newest is the highest version number, never by date or file time.

**Unversioned changes.** `check-contract.py` compares each id's text (its definition line plus indented continuation lines, or its table row; whitespace-normalised; the first definition wins) in the live files against the newest snapshot. In a Draft this is information: the next version lists the changes. In an `Approved` contract it is an error, `unversioned change since v2: R4.c (new), R7.a (text): cut a version`. This catches every direct edit, including `skunexus-backend-plan`'s Step 3 lettering and Step 5 contained patches, which the developer confirmed in that thread. The contract's version door turns them into `v<N>.<M> approved` with the note `from backend-plan Step 5`. `check-contract.py` also checks that a version line's `changed` / `new` / `retired` lists equal the diff between its snapshot and the previous one.

**View header.** Every view file carries one line under its title:

```
> Built from: contract v2 (2026-11-03) · backend-plan.md@3f2a9c1e · frontend-plan.md@77d0e1aa
```

- The contract part names the snapshot it read: `review/prd-v2-2026-11-03.md`, plus `review/workflows-v2-2026-11-03.md` when that exists.
- `<file>@<hash>` names another view it read. The hash is the first 8 hex characters of the SHA-256 of the file at build time, with CRLF read as LF (`tr -d '\r' < <file> | sha256sum | cut -c1-8`), so a git checkout that rewrites line endings changes nothing. The estimate names the plan and the FE plan; the FE plan names the storyboard's `artifact.md` and `backend-plan.md`.
- In the storyboard the string is one line of the page, `const BUILT_FROM='contract v2 (2026-11-03)';`, and it fills the `Built from` column of `prototype/artifact.md`'s version table. A cell that does not start with `contract v` is legacy (no base). Scenario objects carry `id:'s1'`, step objects `id:'s1.3'` and their part as `p:[1]`; deep links are `#s1.3`. A live step that is deliberately not drawn is listed in `const NOT_DRAWN={'s2.3':'<reason>'};`. An appendix (priced-option) scenario keeps its `workflows.md` id and `opt:1`; all its steps sit outside Part 1. A CHOICE chip `A('FB3')` shows that entry's **What:** line verbatim. A page is checked against the snapshots its `BUILT_FROM` names; later versions reach it only through `--stale`.

**Stale rule.** Staleness compares `vK`'s snapshot with the newest snapshot, never the live files, so draft edits mark nothing stale until the next freeze. A view built from `vK` is stale on:
- every id it cites whose text changed, or that was retired, after `vK`;
- every id new after `vK` that falls in its coverage scope (§1 table);
- every `<file>@<hash>` whose file has changed since.

A rebuild touches only the stale pages, tasks or rows.

**No base.** A view with no `Built from` line (a regular-route plan, a legacy storyboard) has no base: `--stale` says so and the view counts as current. Its owner adds the header the next time it writes the view. Dates are never a base: FFD-17 cut v1, v2 and v2.1 on one day.

### Script interfaces other skills call

| Command | Does | Exit |
|---|---|---|
| `python3 -I check-contract.py <TICKET_DIR>` | checks `prd.md` (+ `workflows.md`, `feedback.md` when present): the PRD checks (ids run without gaps, every live requirement has a criterion, citations resolve, no placeholders, assumption markers), coverage both ways, versions and snapshots, unversioned changes | 0 OK · 1 errors · 2 unreadable |
| `… --prev <snapshot>` | no `R`, criterion, `Q`, step or part disappeared since that snapshot | same |
| `python3 -I check-contract.py <file>` | one file: a snapshot, or a legacy `prototype/requirements-lite.md` (read as lite) | same |
| `… --stale <view file>` | the view's stale ids, each with its reason (`changed in v2`, `new in v2.1`, `backend-plan.md changed`) | 0 current · 1 stale · 2 unreadable · 3 no base (counts as current) |
| `… --selftest` | built-in fixtures | 0 OK |
| `python3 -I check-plan.py <TICKET_DIR> --plan --sizes` | plan characters per part, for the estimate (a task runs from `### T<n> ` to the next `### T` or `## `) | 0 OK · 1 errors |

**A task's part.** A `**Part:** Part 2` line in the task wins. Otherwise `check-plan.py` derives it from the criteria the task cites in `Satisfies:` (an `R<n>` stands for its live criteria) and `Tests:`, through the steps that cite them. A task whose criteria span parts is `shared`. Text outside tasks, and tasks with no part (a migration, a criterion under "Not exercised"), are `unassigned`, each with its size. The estimate door asks the developer how to split `shared` and `unassigned`, and records the split in `estimate.md`, never in the plan. FE hours that span parts are split the same way. Hours appear only in `frontend-plan.md` and `estimate.md`, never on the storyboard.

## 6. `feedback.md`: the only way behaviour moves

One file per ticket. Every view and every source appends to it; only the contract's rulings door reads it to decide, and only the rulings door changes an entry's status. Where `skunexus-contract` is not installed, `skunexus-backend-plan`'s Step 5 rules on the plan's entries with the developer.

```
# Feedback: FFD-17

### FB3 · WRONG · BE plan draft · 2026-11-03
- **Cites:** R4.b
- **What:** R4.b's refusal sits inside the queued decide job, which never reaches the user.
- **Evidence:** research/R2-decisions.md:40; AutoDecideOrderHandler.php:43-45
- **Proposed:** (A) refuse before queueing, nothing created · (B) keep the job guard, add a notice
- **Status:** ruled v2 (developer, option A) → R4.b changed, Q26 new
```

| Type | Means | Typical source |
|---|---|---|
| `WRONG` | the contract says something the evidence, the code or another rule contradicts | plan, panel, code, QA |
| `CHOICE` | a view needs a decision the contract does not make, and drew or assumed the simplest option | storyboard v1, FE plan |
| `SILENCE` | the contract says nothing about a case a view hit | storyboard, plan, QA |
| `CHANGE` | the outside world moved: a re-pulled ticket, the PO's reaction, a new constraint | re-pull diff, PO, coding surprise |

- **Sources:** `harden <DATE>` (the contract's own findings), `storyboard v1`, `storyboard v2`, `BE plan draft`, `BE plan`, `FE plan`, `estimate`, `panel`, `re-pull <DATE>`, `PO <DATE>`, `code`, `QA`.
- **Status:** `open` · `ruled v<N> (<who>, option X) → <ids>` · `rejected v<N>: <why>` · `withdrawn: <why>`.
- **A view never edits the contract,** and never edits another source's entry. A panel's decision items (`PD-n`) and a re-pull's changes (`RC-n`) enter as `FB` entries, with the review-local id in the source (`panel PD-2`). Re-pull classes: ANSWERS, CONTRADICTS, NEW-SCOPE, REMOVES and AMBIGUOUS enter as `CHANGE` with the class in the source (`re-pull 2026-11-04 · CONTRADICTS`); CONFIRMS and NO-IMPACT file nothing.

## 7. Gates

A gate is a named role's explicit yes before anything downstream builds on the artifact. Silence is not approval, and a draft has no gate. Each yes is recorded with its date and who gave it.

| Gate | Owner | Yes means | Recorded in |
|---|---|---|---|
| G1 | developer | the decision list is ruled | §7 `Decided …` entries and `feedback.md` statuses |
| G2 | developer | the contract is approved | `> Status: Approved` + the version line |
| G3 | developer; tech lead reviews | the BE plan is approved | `backend-plan.md` status |
| G4 | FE developer | the FE plan is confirmed or replaced | `frontend-plan.md` `> Status: Confirmed <DATE> (FE developer)` |
| G5 | developer | the estimate is posted (the developer sets the base; posted hours are theirs, never re-argued) | `estimate.md` `> Posted <DATE>: …` |
| G6 | PO | scope and price, together | `estimate.md` `> PO: <DATE> …` and `prototype/artifact.md` |
| G7 | tech lead | the PR is merged | GitHub |
| G8 | QA | testing passes | Jira |

G3–G5 can be asked in one message. Present decisions as lettered options, the PO-literal one first, each tagged as in §3, and end with `needs input: …`. Expect terse answers ("A", "yes to all").

**An assumed chip never becomes an expected result** (the hand-over guard). Every §7 id that a live step cites is `Decided` before the testing steps are written, or it goes into their prerequisites as "assumed, confirm with the PO", never into a step's expected result. `check-contract.py` prints `open assumptions cited by live steps: <ids>` on every run: every §7 id a live step cites with no `Decided` entry, Open as well as `Assumed` (only an entry whose state is `Decided …` counts; an option tag such as `[PO decided]` does not); at G5 and G6 the estimate states them as its assumptions. A page that still carries an `A()` chip gets an estimate, not a build. The QA-steps view reads `prd.md` with no stale check, so this rule sits at the hand-over.

## 8. Chain rule, ownership, workflows and settings

**Ownership.** The table applies only to a ticket that already has contract files (`workflows.md`, `feedback.md`, `research/` or `review/po-baseline.md`). Without them, "continue <TICKET>" and "the ticket changed" belong to the skill that owns the ticket's files (`skunexus-jira-prd`, `skunexus-backend-plan`, `skunexus-backend-implement`). With them, "continue <TICKET>" goes to the skill that owns the first missing or unfinished artifact, in this order:

| # | Artifact | Owner | Done when |
|---|---|---|---|
| 1 | `jira/`, `input/`, `research/`, `review/po-baseline.md` | contract, evidence door | the baseline exists, or the developer skipped it |
| 2 | `prd.md` | contract (draft or lite door) or `skunexus-jira-prd` (seeded interview) | `prd.md` exists, and no seeded interview is unfinished. While §7 still carries the interview note and any entry is Open, the owner is `skunexus-jira-prd` (its Step 0 resumes from §7), not the harden door; when the developer says the interview is over, go to row 3 |
| 3 | `workflows.md` + a frozen version | contract, harden door | `check-contract.py` OK; a `frozen` version exists |
| 4 | discovery views | storyboard (v1) ‖ contract (panel) | the panel synthesis and storyboard v1 exist, or the developer skipped them |
| 5 | `feedback.md` open entries | contract, rulings door | none open; G1 and G2 recorded |
| 6 | `backend-plan.md` | `skunexus-backend-plan` | G3 |
| 7 | storyboard v2 | storyboard | built from the current version |
| 8 | `frontend-plan.md` | storyboard, FE plan door | G4 |
| 9 | `estimate.md` | storyboard, estimate door | G5, then G6 |

A stale view counts as unfinished: `check-contract.py --stale` decides. A view with no base counts as current.

**Chain rule.** With `chain: whole` (below), a skill that finishes loads the next owner instead of stopping. It still stops at a gate (attended) or at the workflow's stop point (below). With `chain: stage` it ends with one line offering the next skill.

**Restart after approval.** Each approval that ends a skill's work (G2, G3, G5) is followed by a restart (the one exception is the "just the storyboard" yes, §5 item 3). Restart also when the developer comes back after an hour or more: the session's cache is cold, so its next turn re-writes the whole context. Update the memory note, then end the turn with "Start a new session now: `continue <TICKET>`". The main session re-reads its whole context on every turn: on FFD-40 it grew from 308k to 486k after the PRD approval, and restarting at 308k would have saved 1.9M of its 6.6M. Never restart with agents in flight.

### Workflows and settings

**Two front doors, chosen by one question: must the PO see and price it before it is built?** Yes: `/skunexus-contract <TICKET>`, which owns `run.md`, asks the workflow question (A–F) and drives the chain, calling `skunexus-jira-prd` for the (seeded) interview, `skunexus-backend-plan` for the plan and `skunexus-storyboard` for the drawing, each at its turn. No: `/skunexus-jira-prd <TICKET>` ("let's start PHG-418"), the regular route, unchanged.

A run's behaviour depends on a named **workflow**, never on the tone of an ask. A workflow is a preset: a route through the doors, a stop point, and the `mode` and `chain` it fixes. `plan-fan-out` is not a workflow: it stays a separate switch on top of any workflow that reaches the BE plan. The workflow is picked in Step 0 of `skunexus-contract` and `skunexus-storyboard`, echoed before anything runs, and recorded as the first row of `run.md`.

| Letter | Workflow (`workflow=`) | Label in the question | Route | Stops at | Fixes |
|---|---|---|---|---|---|
| A | `prd-storyboard-estimate` | PRD + storyboard + estimate | evidence → seeded interview (`skunexus-jira-prd`) → harden + panel → rulings (G1, G2) → BE plan (G3) → storyboard v2 → FE plan (G4) → estimate (G5) | the estimate posted; scope and price go to the PO together (G6) | attended, whole |
| B | `prd-storyboard` | PRD + storyboard | evidence → seeded interview → harden + panel → rulings (G1, G2) → storyboard v2; no BE plan (only A passes G3) | storyboard v2 shared for scope (no hours) | attended, whole |
| C | `lite-storyboard` | lite + storyboard | lite contract → storyboard v1 | storyboard v1, internal only | lite, whole |
| D | `lite` | lite only | lite `prd.md` + `workflows.md` | the lite contract | lite, stage |
| E | `unattended` | unattended draft, then triage | evidence → draft with defaults → harden (lighter panel) → storyboard v1 + ranked decision list | the decision list; shared after `triage`, or before it badged "not reviewed" | unattended, whole |
| F | `storyboard-only` | just the storyboard (PRD exists) | adoption + harden (one approval) → storyboard v2; the estimate too when a plan exists | storyboard v2 | attended, stage |
| — | `triage` | (follow-up, offered only after E has stopped) | rulings on the triage set → v1.x "Draft for discussion" | the discussion draft and the drafted share | keeps `mode` |
| — | `re-pull` | (offered only when `jira/` exists) | re-pull → diff → rulings | the ruled contract | keeps `mode` |

- "let's start X" stays with `skunexus-jira-prd`: no workflow, and nothing is written to `run.md`. `/skunexus-jira-prd <TICKET>` is the regular route's front door; its closing line offers `skunexus-contract` when the PO must see and price the feature first, and the contract then adopts the approved PRD (workflow B or F).
- **No prototype needed** (the developer says so, or the ticket is BE-only or a data contract with no flow anyone walks): `skunexus-contract` says so in one line, "No prototype needed: use `/skunexus-jira-prd <TICKET>`, the regular route.", and writes nothing. The regular route is not a menu option.
- A plain `/skunexus-storyboard <TICKET>` with no `run.md` asks the same question (the same menu) and hands the steps before the drawing to `skunexus-contract` by the chain rule.
- "continue X" resumes the workflow recorded in `run.md`: echo it, then go to the next owner (the ownership table above).
- `triage` and `re-pull` are follow-ups: picking one switches the `workflow` row and keeps `mode` and `chain` as they are.

**Step 0** (both skills), first match wins:
1. **Arguments:** `/skunexus-contract FFD-17 workflow=unattended`, also `plan-fan-out=on`. Echo, don't ask.
2. **A trigger phrase** (the table below) selects a workflow. Echo, don't ask.
3. **`run.md` exists:** echo the recorded workflow and continue. A `run.md` with no `workflow` row counts as missing it: ask the question and keep its History.
4. **Otherwise** (a plain `/skunexus-contract FFD-17`): one quick question.

A workflow from 1 or 2 that differs from `run.md` is a switch: write it with its History line. An ask that matches two rows gets the question, never a guess from tone.

**The question.** One message: one line on what the choices cost the developer, then one lettered list of the menu workflows, A–D first, then E and F, then the follow-ups `triage` and `re-pull` when they apply, ending with `needs input: …`. One answer is enough ("B"). The list is filtered by the disk:
- F only when `prd.md` exists;
- `re-pull` only when `jira/` exists, `triage` only when an `unattended` run has stopped (its `review/decision-list-<DATE>.md` exists);
- an approved `prd.md` makes A and B start by adopting it (the harden door) instead of the interview.

```
FFD-17: which workflow? A and B interview you and wait at every gate; C and D ask nothing and stay internal; E asks nothing now and needs a 15–30 min triage later; F asks one approval.
(A) PRD + storyboard + estimate: stops when the estimate is posted; scope and price go to the PO together
(B) PRD + storyboard: stops at storyboard v2, shared for scope (no hours)
(C) lite + storyboard: stops at storyboard v1, internal only
(D) lite only: stops at the lite contract
(E) unattended draft, then triage: stops at a ranked decision list; shared after the triage, or before it badged "not reviewed"
(F) just the storyboard (PRD exists): stops at storyboard v2
needs input: one letter
```

**The echo,** always one line, before any work: the workflow, its label, its route shortened, the mode and where it stops, and how to switch.

> Working with workflow `prd-storyboard` (PRD + storyboard): evidence → interview → contract → storyboard v2. Attended; stops at each gate. Say "workflow <name>" to switch.

**The file: `.ai/<TICKET>/run.md`,** written on the first write after the echo.

```
# Run settings: FFD-17

| Setting | Value | Since | Set by |
|---|---|---|---|
| workflow | unattended | 2026-11-03 | developer: "I'm away: run FFD-17 without stopping" |
| mode | unattended | 2026-11-03 | the workflow |
| chain | whole | 2026-11-03 | the workflow |
| plan-fan-out | off | default | |

## History
- 2026-11-04 workflow unattended → triage (developer)
- 2026-11-04 triaged v2: 9 items ruled (developer)
```

- **Written** by the first of the two skills to write anything for the ticket, on that first write: `workflow` first, then the `mode` and `chain` it fixes.
- **Changed** only by the developer's explicit words ("workflow <name>", a trigger phrase, an argument). A switch updates the rows and appends a History line, exactly `- <YYYY-MM-DD> <setting> <old> → <new> (<who>)`, e.g. `- 2026-11-04 workflow unattended → triage (developer)` or `- 2026-11-05 plan-fan-out off → on (developer)`. A triage appends `- <YYYY-MM-DD> triaged v<N>: <n> items ruled (<who>)`, where `v<N>` is the frozen version the triage cut: the version in the v1.x page's `BUILT_FROM`. These are the only two forms.
- **`mode` and `chain` follow the workflow;** to change them, switch the workflow.
- **A resume never changes it.** The memory note points to it and never copies it. `check-contract.py` warns on an unknown setting, value or workflow name, on a `mode` or `chain` that contradicts what the workflow fixes, and on a malformed History line.

| Setting | Values (default first) | Meaning |
|---|---|---|
| `workflow` | the eight names above, no default | the preset; the first row |
| `mode` | `attended` · `unattended` · `lite` | fixed by the workflow. **attended:** the interview runs (seeded into `skunexus-jira-prd`) and every gate waits for the developer. **unattended:** no interview; research and the lighter panel give every open item a default with evidence or an owner; no gate is passed; the run ends at its stop point. **lite:** defaults only, no research or panel; internal only and never shared |
| `chain` | `stage` · `whole` | fixed by the workflow. **stage:** finish this skill and end with one line offering the next. **whole:** load the next owner (the table above) until a gate (attended) or the workflow's stop point |
| `plan-fan-out` | `off` · `on` | `skunexus-backend-plan`'s parallel-drafting door, on top of any workflow. Never switched on by plan size |

**Triggers** (the skills' descriptions mirror this table):

| The developer says | Workflow | Skill · door |
|---|---|---|
| "PRD, storyboard and estimate for X" | `prd-storyboard-estimate` (A) | contract · evidence |
| "I'm away: run X without stopping" / "unattended" | `unattended` (E) | contract · evidence → draft |
| "a quick storyboard, no PRD" | `lite-storyboard` (C) | contract · lite → storyboard v1 |
| "PRD and plan are done, just build the storyboard" | `storyboard-only` (F) | storyboard (the contract's harden door first when `workflows.md` is missing) |
| "re-pull X and diff it" | `re-pull` | contract · rulings (re-pull) |
| "triage X" | `triage` | contract · rulings, scoped to the triage set → storyboard rebuild as v1.x "Draft for discussion"; appends the `triaged` History line |
| "plan it, fan out to subagents" | unchanged; `plan-fan-out` on | backend-plan · parallel door |
| "continue X" | the one recorded in `run.md` | the owner of the first missing artifact (the table above) |
| "let's start X" | none (no `run.md` is written) | `skunexus-jira-prd` (unchanged) |

**What each mode builds.** The workflow's stop point ends the route; inside it, the mode decides what runs and where it waits.

| Mode | Builds, in order | Stops | The PO receives |
|---|---|---|---|
| attended | the ownership order above (`prd-storyboard` skips row 6, the BE plan) | at every gate | `prd-storyboard-estimate`: storyboard v2 with the estimate, at G6; `prd-storyboard`, `storyboard-only`: storyboard v2 for scope, no hours |
| unattended | 1. evidence: a fresh pull and the PO baseline · 2. a Draft with a default per question · 3. harden with the lighter panel (the full panel on a large ticket) · 4. `workflows.md` and a frozen version · 5. the capture and storyboard v1 (internal, chipped) · 6. `review/decision-list-<DATE>.md`, ranked: parts, scope and price; then platform and Core-vs-client items; then the PO-owned questions (at most about 7, marked); then the rest | after 6, with no BE plan, FE plan, estimate or hours: plan drafting is the largest share of a run, and the first overturned scope default makes it stale | nothing from the run itself; silence is not approval (§7) |
| lite | a lite contract, v1 frozen, storyboard v1 (`lite-storyboard`) | after storyboard v1, or after the lite contract (`lite`) | nothing: lite is internal only |

**Triage** ("triage X"): a later, attended pass by the developer on a stopped run, through the rulings door. It is the follow-up workflow `triage`, not a mode: it keeps `mode` and `chain` and changes nothing a run does before its stop.
- **The triage set:** every scope-bearing `Q` (it names a `Part`, is tagged `expansion`, or is `Assumed` naming an owner but no `Evidence:`) and every v1 `CHOICE` chip on a drawn page. Each is ruled, or a chip is re-keyed to a plain `Q`; a cosmetic label becomes caption "proposal" text. The 15–30 minutes this takes is assumed, not measured.
- **Then:** the rulings door cuts a `frozen` version, `run.md` gets its `triaged v<N>` line, and the storyboard is rebuilt from that version as v1.x, "Draft for discussion" (`skunexus-storyboard` `references/build.md` §1). `N` in `triaged v<N>` must equal the version in the v1.x page's `BUILT_FROM`. For a reviewed share, `check-storyboard.py` needs `--contract`, a `BUILT_FROM` base and `prototype/sn-baseline.md`, and, for that version, `run.md`'s `triaged v<N>` line, a `Decided` line on every scope-bearing `Q` and no `A('FB<n>')` chip left. Without the `triaged` line it is an early share (below).
- **The share:** after the rebuild, the developer posts the v1.x link, a 3-line summary, at most about 7 lettered plain questions each deep-linked to its step, a paste-ready "Open questions for the client" block, and the date the estimate follows. The skill drafts it as `review/share-<DATE>.md`; the developer posts it. The PO and the FE developer get the link at the same time.

**Sharing: early and labelled; binding only at v2.** A booked call or the PO's ask outranks the triage: the drawing exists to be discussed, and waiting costs weeks ("Why", RL-47).
- **Before the triage:** rebuild as v1.x with `STAGE='discussion'` and the badge "Draft for discussion <DATE>, not reviewed". Its `A('FB<n>')` chips stay, so its guesses stay visible. The flip takes minutes, so it never delays the call. `check-storyboard.py` requires the badge and warns without a presenter sheet.
- **A presenter sheet with every v1.x share** (`review/presenter-<DATE>.md`, `skunexus-storyboard` `references/publish.md`): the live path of about 15 steps, the open assumptions by step, the assumed contract rules that have no chip, the steps not drawn, and one rule for whoever presents: not drawn or not on the card, say "not drawn yet, noted" and write it down; never narrate behaviour the contract doesn't hold.
- **Errata within 48 hours:** every statement from the call that the contract contradicts becomes a `WRONG` entry and every client decision a `CHANGE` entry (source `call <DATE>`); the rulings door applies them and drafts `review/errata-<DATE>.md` for the developer to send (`references/rulings.md`).
- **The hard gate is binding, not sharing:** nothing is priced (G5), approved to build (G6) or coded against, by the client's developers too, before an approved (G2) contract and its v2. Below `STAGE='approved'`, an API call panel says "draft: confirm before coding against it" (`skunexus-storyboard` `references/build.md`).

**Routing by ticket kind.**

| Ticket kind | Route |
|---|---|
| UI change, small or medium, with a clear ask (the FFD-27 kind) | `unattended` → `triage` → v1.x share |
| UI change with Core-vs-client, concurrency or entry-path decisions | the same, with those items ruled in the triage; if they can't be ruled within its time box, `prd-storyboard-estimate` |
| Integration whose flow another team walks: calls, webhooks, syncs (the RL-47 kind) | this skill, with API call panels on the integration steps (`skunexus-storyboard` `references/build.md`): RL-47's client team worked through its 56 steps in one call |
| BE-only, or a data contract with no flow anyone walks | the regular route, not this skill: `skunexus-jira-prd` → `skunexus-backend-plan`, no storyboard |
| "A quick look" | `lite-storyboard` or `lite`, internal only, never shared |

Full attended (`prd-storyboard-estimate`) is required when any one of these holds: the first share must carry an estimate, because the PO will price options in front of the client; after the triage, more than about 7 PO-owned questions remain, or scope-bearing items remain unruled after the 30-minute box; the ticket is large.

**State lives on disk.** Every door decides from the files. The project memory note is a pointer, never the source. This is its one definition; the skills cite it.
- **File:** `~/.claude/projects/<REPO_SLUG>/memory/<ticket-lowercase>-<topic>.md` (`<REPO_SLUG>`: `skunexus-contract` SKILL.md).
- **Written** at every door or phase boundary, after an approval and before a pause.
- **Records:** stage; a pointer to `run.md` (never a copy of its settings); files; open items (open entries, `Assumed` items, stale views); artifact URL; the Jira site URL when the repo `CLAUDE.md` gives no cloudId; next step.
- A note that still says "paused" after a resume misleads the next session.

## 9. Running agents

These rules apply to every package that fans out. Each one keeps the clause that explains it.

- **Orchestrate by default.** Raw dumps (Jira payloads, code maps, reviews) stay in agent files, out of the main context. One shared brief file per fan-out; every agent gets its input paths, an output file it alone owns, and a reply cap (15 lines unless the brief says otherwise).
- **Agent types.** Spawn `sn-scout` (Sonnet: retrieval, capture, mappers, exact-edit fixers, code skeptics), `sn-worker` (Opus: plan drafters, fact-checkers, the storyboard builder), `sn-writer` (Opus, no CLAUDE.md files: document-only roles), `sn-judge` (the session's model: the backend-plan door's optional plan architect, red team, simulated personas). Never `general-purpose`: it starts at ~59k tokens and re-reads them every turn. If a type is missing, say so and use `general-purpose`, with `model: "sonnet"` for scout roles.
- **Fresh agents, not forks.** A fork re-reads the whole parent context on every turn. Fork only while that context is under ~100k tokens.
- **Wait for the completion notice** before reading an agent's file: a file can be on disk before the agent has finished it.
- **Verify what shapes a decision** against the code (`patches/` before `vendor/`), the ticket or the PO's own words before the developer sees it, even when two agents agree. A synthesizer once turned "please review LO-58" into "Build on LO-58".
- **Say real durations up front:** capture ~30 min, a storyboard build 10–20 min, a panel ~45 min, plan drafters 3–9 min each. Name the bursts (plan drafting, the panel) before they start, so the developer can start them early in a usage window.
- **Resume warm, restart cold.** A subagent's prompt cache lives about 5 minutes.
  - SendMessage corrections only while the agent is busy or has been idle under ~5 minutes.
  - Otherwise start a fresh agent of the same type, pointed at its brief and its own file. The `<!-- STATE … -->` line under the file's title carries what isn't in the deliverable yet, and the check scripts catch dropped items.
  - Resume a cold agent only when it holds reasoning that isn't on disk and re-deriving it costs more than the re-write: a 400k agent costs ~0.5M to re-write and then re-reads 400k every turn, while a fresh one starts at ~100–150k.
  - After a usage-limit stop, wait for the reset and restart fresh. On FFD-35, six large agents resumed in the same minute and all hit the limit again within 31 seconds.
- **Pause.** On "pause", tell each agent to finish or stop within a minute and leave `PAUSED <DATE>` in its file. Update the memory note before you stop.
- **Text only.** Screenshots and snapshots go to files; agents work from text. Visual judgement goes to a short-lived agent that views at most 3 images. An agent that fails after an image entered its context is replaced, never resumed.
- **Read-only outside.** No writes to Jira or Confluence; client sandboxes and admin UIs are read-only; local app and DB writes only when the developer grants them, logged for undo. Never run queue jobs or workers.

## 10. Review findings

Every reviewer, in a panel, a plan review or a check, writes findings in one shape:
- **Each finding:** `ID · location · type · as written · problem · evidence · suggested text`.
- **End of the file:** a "Confirmed OK" list, which shows what was covered.
- **Verify before applying:** findings that change a rule or a decision are re-checked against the primary source before they reach the developer. Reviewers contradict each other, so settle conflicts with evidence, never by vote.
- **Code skeptics are a mixed-model jury:** they run as `sn-scout`, on a different model from the Opus reviewers and drafters whose claims they test, because copies of one model share blind spots.
- **Persona reviews** are labelled "Simulated <Name> review", grounded in the person's profile or documented role facts, kept under `review/panel/` (git-ignored), and never quoted in anything sent to others.
