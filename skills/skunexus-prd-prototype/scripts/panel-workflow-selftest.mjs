// Stub test for assets/panel-workflow.js: runs it with fake agents (no Workflow tool, no model calls).
// Usage: node <SKILL>/scripts/panel-workflow-selftest.mjs [path/to/panel-workflow.js]
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import assert from 'node:assert/strict'

const path = process.argv[2] || fileURLToPath(new URL('../assets/panel-workflow.js', import.meta.url))
const body = readFileSync(path, 'utf8').replace(/^export const meta/m, 'const meta')
const AsyncFunction = (async () => {}).constructor
const workflow = new AsyncFunction('args', 'phase', 'parallel', 'agent', 'log', body)

async function run(extra) {
  const calls = { phases: [], labels: [], prompts: {} }
  const args = { ticket: 'TK-1', ticketDir: '/t/.ai/TK-1', repo: '/t', context: 'c', brief: 'review/panel-BRIEF.md',
                 frozenPrd: 'review/prd-v1-2026-10-28.md', ...extra }
  const agent = async (prompt, o) => {
    calls.labels.push(o.label); calls.prompts[o.label] = prompt
    if (o.label.startsWith('panel:')) return { reviewer: o.label, outputFile: 'f', findings: [], top5: [] }
    return o.label === 'cluster' ? { clusters: [] } : 'synthesis'
  }
  const result = await workflow(args, p => calls.phases.push(p), fns => Promise.all(fns.map(f => f())), agent, () => {})
  return { calls, result }
}

const done = ['review/panel/V1-code-facts.md', 'review/panel/V2-traceability.md']
const all = await run({ roles: [], done })
assert.ok(!all.calls.phases.includes('Panel') && !all.calls.labels.some(l => l.startsWith('panel:')), 'all done: no reviewer re-run')
assert.ok(all.calls.prompts.cluster.includes('/t/.ai/TK-1/review/panel/V2-traceability.md'), 'all done: clusterer reads args.done')
await assert.rejects(run({ done }), /roles explicitly/, 'resume without roles must throw')
await assert.rejects(run({ roles: [] }), /no reviewers/, 'nothing to run must throw')
await assert.rejects(run({ roles: ['V9'] }), /unknown role id/, 'unknown role must throw')
const fresh = await run({})
assert.deepEqual(fresh.calls.labels.filter(l => l.startsWith('panel:')), ['panel:code-facts', 'panel:traceability'], 'default roles V1, V2')
const part = await run({ roles: ['V3'], done })
assert.deepEqual(part.calls.labels.filter(l => l.startsWith('panel:')), ['panel:big-picture'], 'resume runs only the given roles')
console.log('selftest ok')
