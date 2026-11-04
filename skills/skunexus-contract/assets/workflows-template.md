# Workflows: <TICKET-KEY> — <Title>

> Contract: versioned with prd.md (see its Versions line)

<!-- The use cases and parts of the contract (skunexus-contract, references/model.md §4). Replace every <…> and delete these comments.
     - Ids are permanent: never renumber or delete. Retire a step by writing "(retired <DATE>, v<N>: <why> → see s<n>.<m>)" in its Outcome cell; a new step takes the next free m in its scenario.
     - Actor is a role, never a person's name. Trigger is one of: user, system, schedule, integration.
     - Before → after is the entity's state; Outcome is what the actor sees. An outcome that contradicts a criterion is a WRONG entry in feedback.md, not a silent fix.
     - Cites lists the R ids and criteria the step exercises (at least one live R or criterion), plus any Q it relies on. An assumed outcome carries "(assumed, Qn)" and cites Qn.
     - Every step fills its Part cell; that cell is the only source of part membership. -->

## Scenarios
| Id | Scenario | Actors |
|---|---|---|
| s1 | <one end-to-end case, in the PO's words> | <roles> |

## s1. <Scenario name>
| Step | Actor | Trigger | Before → after | Outcome | Cites | Part |
|---|---|---|---|---|---|---|
| s1.1 | <role> | <user/system/schedule/integration> | <state> → <state> | <what the actor sees> | <R1, R1.a> | Part 1 |

## Parts
<!-- The PO's priced scope. Name and Scope are copied verbatim by the storyboard and the estimate.
     Scope: one or two plain sentences for the PO, no ids. PO's shape: base, priced separately, or the PO's own words.
     Status: live, or "retired v<N>: <why>". With no priced options, one part: Part 1, base. -->
| Part | Name | Scope | PO's shape | Status |
|---|---|---|---|---|
| Part 1 | <name> | <plain sentences> | base | live |

## Not exercised
<!-- Live criteria no user-visible step shows, each with its reason ("proved by a test, no step shows it"). Delete the heading if empty. -->
- <R1.b>: <reason>
