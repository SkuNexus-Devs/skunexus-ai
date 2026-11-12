export const meta = {
  name: 'sn-prd-panel-review',
  description: 'PRD review panel: functional roles + simulated personas on a frozen PRD, cluster, adversarial verify, synthesize',
  whenToUse: 'Only when the user opted into a Workflow for the PRD panel; otherwise follow assets/briefs/panel-brief.md with parallel agents',
  phases: [
    { title: 'Panel', detail: 'functional roles and simulated personas: scored, evidenced findings' },
    { title: 'Cluster', detail: 'dedupe across reviewers and route to skeptics' },
    { title: 'Verify', detail: 'source-truth and code-truth skeptics try to refute' },
    { title: 'Synthesize', detail: 'panel-synthesis.md ordered by impact' },
  ],
}
// Stage: PRD review panel, Workflow variant of assets/briefs/panel-brief.md (same rules, same output files).
// Run with Workflow({ scriptPath: '<SKILL>/assets/panel-workflow.js', args }). Everything ticket-specific comes from args;
// relative paths resolve against args.ticketDir. Freeze the PRD first and queue PRD edits until the synthesis exists.
// Stub test (no agents): node <SKILL>/scripts/panel-workflow-selftest.mjs
//
// args = {
//   ticket: 'FFD-14', ticketDir: '/abs/repo/.ai/FFD-14', repo: '/abs/repo',
//   context: 'one paragraph: client, feature, deliverable, PO name',
//   brief: 'review/panel-BRIEF.md', frozenPrd: 'review/prd-v1-2026-10-25.md',
//   baseline: 'review/po-baseline.md', deviations: 'review/deviations.md',      // optional
//   prototypeQuestions: 'review/prototype-questions.md',                       // optional
//   consult: ['research/', 'review/baseline/', 'input/', 'jira/', '/abs/reference-repo'],  // optional
//   personas: [{ id: 'V4', name: '<PO name> (PO)', slug: 'po',
//                profilePath: '~/.claude/people/<po-slug>.md', focus: 'checklist from panel-brief.md' }],
//   roles: ['V1', 'V2', 'V3'],            // optional; ids pick the built-in roles below, or pass { id, name, slug, focus }.
//                                         // Default ['V1', 'V2'] (code facts, traceability); add 'V3' (big picture) when warranted; [] = none
//   done: ['review/panel/V1-code-facts.md'],  // resume only: complete reviewer files (ending in Confirmed OK) from an earlier run;
//                                         // then pass only the incomplete reviewers in roles / personas. roles is required
//                                         // with done ([] when V1-V3 are complete); with nothing left to run it skips to clustering
//   perClusterSkeptics: false,            // true = one skeptic per cluster and route (high stakes, slower)
// }

const A = args || {}
for (const k of ['ticket', 'ticketDir', 'repo', 'context', 'brief', 'frozenPrd']) {
  if (!A[k]) throw new Error(`panel-workflow: args.${k} is required`)
}
const DIR = A.ticketDir.replace(/\/$/, '')
const abs = p => (p.startsWith('/') || p.startsWith('~') ? p : `${DIR}/${p}`)
const BRIEF = abs(A.brief)
const PRD = abs(A.frozenPrd)
const BASELINE = A.baseline ? abs(A.baseline) : null
const DEVIATIONS = A.deviations ? abs(A.deviations) : null
const PROTO = A.prototypeQuestions ? abs(A.prototypeQuestions) : null
const CONSULT = (A.consult || []).map(abs)
const DONE = (A.done || []).map(abs)
const OUT = `${DIR}/review/panel`
const SYNTHESIS = `${DIR}/review/panel-synthesis.md`

const ROLES = [
  { id: 'V1', slug: 'code-facts', name: 'Code fact-checker (red team, functional role)',
    focus: `Every statement in the PRD about EXISTING behaviour (SkuNexus core, the connector, sibling tickets, research it relies on) must be true in code.
- Hunt especially for "nothing exists / no X" claims and for ACs that assert behaviour core doesn't have.
- Check patches/ before trusting vendor/. Cite file:line for every verdict, and list the claims you confirmed.` },
  { id: 'V2', slug: 'traceability', agentType: 'sn-writer', name: 'Traceability auditor (functional role)',
    focus: `- Every ask in the ticket maps to an R or a Non-Goal.
- R <-> AC both ways: every live R has an AC; no AC proves an unknown R; ACs drafted before a §4 amendment that now contradict or under-cover it.
- AC falsifiability (concrete values, negative paths), decisions faithful to the interview (§7, Decision log).
- Recount every tally and resolve every cross-reference (R/AC/Q/D ids).` },
  { id: 'V3', slug: 'big-picture', name: 'Big-picture reviewer (unified behaviour, functional role)',
    focus: `The PRD as one coherent product.
- Is behaviour unified: manual vs automatic paths, two surfaces doing one job, limits x status x reopen, edits vs downstream artefacts?
- Contradictions between R-ids; terminology (one term per concept).
- Produce a TRUTH TABLE in your markdown for the interacting rules and flag the cells the PRD leaves undefined.
- If prototype questions were given, answer each from the PRD text or mark it a gap.` },
]
if (DONE.length && !Array.isArray(A.roles)) throw new Error('panel-workflow: on resume pass args.roles explicitly ([] when V1-V3 are complete); the default would re-run V1 and V2')
const REVIEWERS = [...(A.roles || ['V1', 'V2']).map(r => (typeof r === 'string' ? ROLES.find(x => x.id === r) : r)), ...(A.personas || [])]
if ((!REVIEWERS.length && !DONE.length) || REVIEWERS.some(r => !r)) throw new Error('panel-workflow: no reviewers and nothing in args.done, or an unknown role id (built-in: V1, V2, V3)')

const COMMON = `You are on the ${A.ticket} PRD review panel. ${A.context}
FIRST read the shared brief: ${BRIEF}. It defines the sources, persona grounding and the finding format.
Then read the FROZEN PRD snapshot ${PRD} (never the live prd.md, which may change).${BASELINE ? `
Read ${BASELINE} (PO baseline: PO-n decisions, X-n open items, facts the PO may not have had).` : ''}${DEVIATIONS ? `
Read ${DEVIATIONS} (DV-n deviations and the questions for the PO).` : ''}${PROTO ? `
Prototype questions to answer or route: ${PROTO}.` : ''}
Consult as needed: ${[...CONSULT, A.repo].join(', ')}. In the repo, check patches/ before vendor/; its CLAUDE.md holds the connector decisions.

RULES:
- FLAG, DON'T DECIDE. Raise issues, risks, gaps and questions with options; never re-specify the PRD.
- EVIDENCE REQUIRED. Every finding cites file:line, a transcript timestamp, or a PO-n/X-n/DV-n/R-n id. Without evidence set evidenced=false; its score is capped at 40.
- SCORE 0-100: 90+ blocks the estimate or architecture, or contradicts the PO with evidence; 70-89 likely changes a requirement; 50-69 worth fixing; under 50 a nit.
- Cite DV-n items, don't repeat them; add only what's new (a consequence, an edge case, a fix).
- Keep the estimate shape the PO asked for; don't propose more structure.
- Read-only everywhere except your own output file: no edits to prd.md, the baseline, profiles or code. No Jira, Confluence or client-system writes. Never Read PNG/JPEG files.
- Write your full review as markdown to your output file, headed "Simulated <Name> review" for a persona or "<Role> review" for a functional role, in the brief's finding format, ending with a Confirmed OK list.
- Then return the structured output: every finding (concise claim, at most 4 evidence strings), your top 5 finding ids, and a short confirmedOk list.`

const FINDINGS_SCHEMA = {
  type: 'object',
  properties: {
    reviewer: { type: 'string' },
    outputFile: { type: 'string' },
    findings: { type: 'array', items: { type: 'object', properties: {
      id: { type: 'string' },
      location: { type: 'string' },
      type: { type: 'string', enum: ['fact', 'contradiction', 'edge-case', 'silent-assumption', 'missing', 'unified-behaviour', 'testability', 'feasibility', 'scope-cost', 'wording', 'question'] },
      claim: { type: 'string' },
      evidence: { type: 'array', items: { type: 'string' } },
      suggestion: { type: 'string' },
      score: { type: 'number' },
      impact: { type: 'string', enum: ['architecture-estimate', 'po-confirm', 'developer-decision', 'editorial'] },
      owner: { type: 'string', enum: ['developer', 'PO', 'tech-lead', 'FE'] },
      evidenced: { type: 'boolean' },
    }, required: ['id', 'location', 'type', 'claim', 'evidence', 'suggestion', 'score', 'impact', 'owner', 'evidenced'] } },
    top5: { type: 'array', items: { type: 'string' } },
    confirmedOk: { type: 'array', items: { type: 'string' } },
  },
  required: ['reviewer', 'outputFile', 'findings', 'top5'],
}

const CLUSTER_SCHEMA = {
  type: 'object',
  properties: {
    clusters: { type: 'array', items: { type: 'object', properties: {
      key: { type: 'string' },
      title: { type: 'string' },
      memberIds: { type: 'array', items: { type: 'string' } },
      reviewers: { type: 'array', items: { type: 'string' } },
      maxScore: { type: 'number' },
      impact: { type: 'string' },
      owner: { type: 'string' },
      route: { type: 'string', enum: ['source', 'code', 'both'] },
      mergedClaim: { type: 'string' },
      mergedEvidence: { type: 'array', items: { type: 'string' } },
      suggestion: { type: 'string' },
      conflicts: { type: 'string' },
    }, required: ['key', 'title', 'memberIds', 'reviewers', 'maxScore', 'impact', 'owner', 'route', 'mergedClaim', 'mergedEvidence', 'suggestion'] } },
  },
  required: ['clusters'],
}

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    verdicts: { type: 'array', items: { type: 'object', properties: {
      key: { type: 'string' },
      refuted: { type: 'boolean' },
      confidence: { type: 'string', enum: ['H', 'M', 'L'] },
      reason: { type: 'string' },
      evidence: { type: 'array', items: { type: 'string' } },
      correctedClaim: { type: 'string' },
    }, required: ['key', 'refuted', 'confidence', 'reason', 'evidence'] } },
  },
  required: ['verdicts'],
}

if (REVIEWERS.length) phase('Panel')
const rawPanel = !REVIEWERS.length ? [] : await parallel(REVIEWERS.map(r => () => agent(
  `${COMMON}

YOUR ROLE: ${r.name}.${r.profilePath ? ` Profile: ${r.profilePath}. Ground the persona in its role, Review lens, Positions and decisions, and the 10 most recent Observation-log entries. If the profile is thin or missing, say so and lean on the documented role; ask rather than predict where it is silent; never invent opinions the person hasn't shown. This is a simulated review, never the person's opinion.` : ''}
${r.focus}

Output file: ${OUT}/${r.id}-${r.slug}.md (create the directory if missing). Prefix your finding ids with ${r.id}- (e.g. ${r.id}-1).`,
  { label: `panel:${r.slug}`, phase: 'Panel', schema: FINDINGS_SCHEMA, agentType: r.agentType || 'sn-judge' }
)))
const panel = rawPanel.filter(Boolean)
const missingReviewers = REVIEWERS.filter((r, i) => !rawPanel[i]).map(r => r.id)
if (missingReviewers.length) log(`WARNING: no review from ${missingReviewers.join(', ')}; the synthesis lists them`)
log(REVIEWERS.length ? `Panel returned ${panel.length}/${REVIEWERS.length} reviews, ${panel.reduce((s, r) => s + r.findings.length, 0)} findings` : `Every reviewer is in args.done (${DONE.length} files): skipping to clustering`)

phase('Cluster')
const allFindings = panel.flatMap(r => r.findings.map(f => ({ ...f, reviewer: r.reviewer })))
const clustered = await agent(
  `You are the CLUSTERER for the ${A.ticket} PRD panel. Brief: ${BRIEF}.
Below are ALL panel findings as JSON. Group duplicates and near-duplicates (the same underlying issue, possibly under different R-ids or wording) into clusters.
For each cluster give:
- a short title and a merged claim that keeps the strongest evidence;
- memberIds and the distinct reviewers;
- maxScore: the highest member score, counting members with evidenced=false as at most 40;
- the dominant impact and owner;
- route: 'source' if PO, baseline, transcript or Jira facts decide it; 'code' if code or feasibility facts decide it; 'both' if both do;
- a merged suggestion;
- conflicts: where reviewers disagree.
Don't drop any finding: every member id appears in exactly one cluster. Don't judge truth; that is the next stage.${DONE.length ? `
Also read these complete reviewer files from an earlier run and cluster their findings too, ids as written there: ${DONE.join(', ')}.` : ''}

FINDINGS JSON:
${JSON.stringify(allFindings)}`,
  { label: 'cluster', phase: 'Cluster', schema: CLUSTER_SCHEMA, agentType: 'sn-writer' }
)
const clusters = clustered ? clustered.clusters : []
const clusteredIds = new Set(clusters.flatMap(c => c.memberIds))
const orphans = allFindings.filter(f => !clusteredIds.has(f.id)).map(f => f.id)
if (orphans.length) log(`WARNING: ${orphans.length} finding(s) missing from every cluster: ${orphans.join(', ')}`)
const toVerify = clusters.filter(c => c.maxScore >= 50 || c.reviewers.length >= 2)
const skipped = clusters.filter(c => !(c.maxScore >= 50 || c.reviewers.length >= 2))
log(`${clusters.length} clusters; verifying ${toVerify.length}; skipped ${skipped.length} (score < 50 and one reviewer), listed in the synthesis`)

phase('Verify')
const SKEPTICS = [
  { route: 'source', agentType: 'sn-judge', lens: `SOURCE-TRUTH skeptic. Try to REFUTE each claim against ${[BASELINE, DEVIATIONS].filter(Boolean).join(', ') || 'the PO\'s written decisions'}, the baseline analyses in ${DIR}/review/baseline/, the transcripts in ${DIR}/input/, the Jira export in ${DIR}/jira/, and the frozen PRD ${PRD} itself (is the PRD really saying what the claim says?).` },
  { route: 'code', agentType: 'sn-scout', lens: `CODE-TRUTH skeptic. Try to REFUTE each claim against code: ${A.repo} (app/, patches/ first, vendor/skunexus/, frontend-client/)${CONSULT.length ? `, plus ${CONSULT.join(', ')}` : ''}, and the frozen PRD ${PRD}. Research files are claims too; code wins. Cite file:line.` },
]
const skepticPrompt = (s, items) => `You are the ${s.lens}
Brief: ${BRIEF}. You did NOT write the PRD or these findings; your job is to refute them.
For each cluster:
- refuted=true if the evidence shows the claim is false, misreads the PRD or the baseline, or is already handled;
- refuted=false only if you checked and the claim holds. If you could not check it, say so in reason with confidence L.
Give a confidence, a reason, your own evidence (file:line, timestamp, or PO-/DV-/R- id), and correctedClaim when the claim is partly right. Read-only; never Read PNG/JPEG files.

CLUSTERS JSON:
${JSON.stringify(items.map(c => ({ key: c.key, title: c.title, claim: c.mergedClaim, evidence: c.mergedEvidence, suggestion: c.suggestion })))}`
const mineFor = s => toVerify.filter(c => c.route === s.route || c.route === 'both')
const units = A.perClusterSkeptics
  ? SKEPTICS.flatMap(s => mineFor(s).map(c => ({ s, items: [c], label: `verify:${s.route}:${c.key}` })))
  : SKEPTICS.filter(s => mineFor(s).length).map(s => ({ s, items: mineFor(s), label: `verify:${s.route}` }))
const verdictSets = (await parallel(units.map(u => () =>
  agent(skepticPrompt(u.s, u.items), { label: u.label, phase: 'Verify', schema: VERDICT_SCHEMA, agentType: u.s.agentType })
    .then(v => (v ? { route: u.s.route, verdicts: v.verdicts } : null))
))).filter(Boolean)

const verdictsByKey = {}
for (const vs of verdictSets) for (const v of vs.verdicts) (verdictsByKey[v.key] = verdictsByKey[v.key] || []).push({ ...v, route: vs.route })
const judged = toVerify.map(c => {
  const vs = verdictsByKey[c.key] || []
  const refutedCount = vs.filter(v => v.refuted).length
  const status = vs.length === 0 ? 'unverified' : refutedCount === vs.length ? 'refuted' : refutedCount > 0 ? 'contested' : 'confirmed'
  return { ...c, status, verdicts: vs }
})
const tally = s => judged.filter(j => j.status === s).length
log(`Verified: ${tally('confirmed')} confirmed, ${tally('contested')} contested, ${tally('refuted')} refuted, ${tally('unverified')} unverified`)
if (judged.length && !tally('refuted') && !tally('contested')) log('Zero refutations: possibly lenient skeptics. Spot-check the top items in the primary sources.')

phase('Synthesize')
const synthesis = await agent(
  `You are the SYNTHESIZER for the ${A.ticket} PRD panel. Brief: ${BRIEF}. Read the frozen PRD ${PRD}${BASELINE ? `, ${BASELINE}` : ''}${DEVIATIONS ? `, ${DEVIATIONS}` : ''}, and skim the panel files in ${OUT}/.
Below are the clustered findings with skeptic verdicts (status: confirmed / contested / refuted / unverified), the low-signal clusters that were skipped, reviewers that returned nothing, and findings missing from every cluster.

Write ${SYNTHESIS}. Lead with what most changes things, in this order:
1. Headline: counts (raw findings -> clusters -> confirmed / contested / refuted / unverified / skipped) and the 5 decisions that most change the architecture or estimate.
2. PD-1...PD-n, panel decisions that change architecture or estimate: options, recommended option, evidence, R-ids affected.
3. Q-1...Q-n, questions for the PO: merged with the deviations questions, deduplicated, each tied to PO-n / X-n / DV-n.
4. I-n items for the developer and J-n items for the tech lead.
5. E-1...E-n, proposed PRD edits: confirmed findings only, as concrete R-id changes (add / modify / retire, never renumber), NOT applied.
6. The unified-behaviour truth table from the big-picture review, undefined cells marked.
7. Answers to the prototype questions (answered by the PRD / a gap / needs a decision)${PROTO ? '' : ' (none were given: omit this section)'}.
8. Precedent relevance: what to reuse or avoid from reference tickets, if any reviewer raised it.
9. Contested items: both sides, and the skeptics' corrected claims.
10. Refuted and skipped: one line each, with why.

Label persona-derived content "simulated"; never present it as a real person's opinion, and never quote personas as sources. Keep the estimate shape the PO asked for. Write only that file.
Return (at most 40 lines): the headline counts, the top 5 decisions, the top questions for the PO, and the file path.

DATA JSON:
${JSON.stringify({
    judged,
    skipped: skipped.map(c => ({ key: c.key, title: c.title, reviewers: c.reviewers, maxScore: c.maxScore })),
    missingReviewers,
    earlierReviewFiles: DONE,
    orphanFindings: orphans,
    panelTop5: panel.map(r => ({ reviewer: r.reviewer, top5: r.top5, file: r.outputFile })),
  })}`,
  { label: 'synthesize', phase: 'Synthesize', agentType: 'sn-writer' }
)

return {
  counts: {
    reviews: panel.length,
    findings: allFindings.length,
    clusters: clusters.length,
    verified: toVerify.length,
    skipped: skipped.length,
    confirmed: tally('confirmed'),
    contested: tally('contested'),
    refuted: tally('refuted'),
    unverified: tally('unverified'),
    orphans: orphans.length,
  },
  synthesisFile: SYNTHESIS,
  synthesis,
}
