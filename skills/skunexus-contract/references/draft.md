# Door 3: draft with defaults

**Goal:** a complete Draft `prd.md` with no interview: every open item decided or assumed, each assumption with its evidence or the role who confirms it. Used unattended ("I'm away: run FFD-17 without stopping") or when the developer says "draft it with defaults". FFD-17 ran this way: 44 defaults, each citing evidence or naming who confirms, and its panel found none that contradicted a PO decision.

**Done when:** `prd.md` is a Draft with every section filled, every §7 entry `Assumed` or `Decided`, and `check-contract.py` OK. The status stays Draft; only the developer approves (G2).

**Needs:** door 1's outputs. With no research, say so: every default then names an owner instead of evidence.

## The default rule

For each `Q` from the evidence door, take, in this order:
1. the option the PO decided (a `PO-n` in `review/po-baseline.md`, or the ticket text);
2. otherwise the researcher's proposed default;
3. never an `expansion` option, unless the evidence makes it the only workable one (then say why in the entry).

Write it into the requirement as `(assumed, Qn)` and into §7 as `- **Qn** <question> Assumed: <default>. Evidence: <file:line or quote>. Confirm with <role>.` A contradiction with a PO decision you keep on purpose gets `(Developer choice, confirm with the PO: Qn.)`.

## Steps

1. **Skeleton.** Create `prd.md` from `<SKILL>/../skunexus-jira-prd/assets/prd-template.md`: title, `> Status: Draft`, `> Source:` naming every input.
2. **§3 and §4 yourself.** Goals, Non-Goals (each with its provenance and the `Q` it depends on) and requirements `R1…Rn`, from the baseline's `PO-n` decisions, the ticket and the defaults above. This is the step the interview would have done; keep it in the main session, because every later section is built on it. Write §7 with every `Q` (the evidence door's ids, `NEW-n` items as the next free ids) in the Assumed or Decided shape.
3. **Drafters** (`assets/briefs/drafting-brief.md` → `review/drafting-BRIEF.md`, both `sn-writer`, in one message): D1 writes §6 criteria; D2 writes §1, §2, §5, the §7 tidy with the Decision log, and Notes for Design. They write only their own files.
4. **Assembly.** Wait for both completion notices. `cp prd.md review/prd-pre-assembly.md`, then splice each draft into its sections with a short Python script that replaces the section bodies between headings; don't hand-merge.
5. **Triage** each draft's "Notes for the orchestrator": fixes consistent with the decisions are applied now; real gaps become new `Q` entries with a default by the rule above (unattended), or a short list `P1…Pn` for the developer (attended), asked while the next door runs.
6. Run `python3 -I <SKILL>/scripts/check-contract.py <T>` until it exits 0. A criterion drafted before a late §4 change is re-checked against its requirement.
7. **Next:** door 5 (harden), which writes `workflows.md`. It runs after assembly, not alongside the drafters, because steps cite the criterion letters D1 assigns.

## PRD conventions

`prd.md` keeps `skunexus-jira-prd`'s template and section numbers, so every existing skill reads it unchanged. On top of it (the FFD-14 model):

| Convention | Form |
|---|---|
| Header | `> Status:` first, `> Source:` (every input), then the `> Versions:` block once a version is cut (model.md §3); a references legend; the ticket's last-updated time |
| §1 Summary | What changes and why, in 1–2 sentences |
| Non-Goals | Each with its provenance ("(PO, doc comment <DATE>)") and the `Q` it depends on |
| Terms table | Top of §4: `Term \| Meaning in this PRD \| In <CLIENT>'s words`, each term pointing to its `R` id |
| Requirements | `- **Rn** … shall …` under bold subheads; one product rule each; no implementation |
| Criteria | `- **Rn.a** Given …, when …, then …`, grouped by the §4 headings, with concrete values, negative paths and concurrency ("exactly one succeeds"); each falsifiable; every requirement has one, none without a requirement |
| Assumptions | Inline `(assumed, Qn)` or `(Developer choice, confirm with the PO: Qn.)`, each with a matching §7 `Assumed:` entry |
| Lifecycle matrix | Rows = actions, columns = statuses; every cell cites the criterion that proves it |
| §7 | Grouped: For the PO / client · For the tech lead (`J-`) · External inputs · Decision log (`Id · Decision · R ids · Evidence`). Entry states as in model.md §3 |
| Notes for Design | Parked ideas and constraints for the plan, not decisions: one bold bullet per topic with its `R` ids and file:line evidence |
| Altitude | What, not how: no class names in §1–§6 except settings, permissions and statuses users see |
| Wording | Plain, specific, no marketing; one term per concept; no persona attributions |
| Other tickets' ids | Key adjacent: `FFD-14 R31`, `FFD-14's R26`. A bare id is checked against this PRD |
