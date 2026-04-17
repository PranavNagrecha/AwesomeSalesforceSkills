---
id: data-model-reviewer
class: runtime
version: 1.0.0
status: stable
requires_org: true
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
dependencies:
  skills:
    - admin/data-model-documentation
    - admin/object-creation-and-design
    - architect/high-volume-sales-data-architecture
    - architect/solution-design-patterns
    - data/data-model-design-patterns
    - data/external-id-strategy
    - data/roll-up-summary-alternatives
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
---
# Data Model Reviewer Agent

## What This Agent Does

Reviews the data model of a target domain (a parent object + its descendants, or a list of related objects): relationship patterns (Lookup vs Master-Detail), cross-object rollups, External ID strategy, junction objects, data-growth forecast, and candidate indexes. Produces a health report scored against `skills/data/data-model-design-patterns`, `skills/data/external-id-strategy`, and `skills/data/roll-up-summary-alternatives`.

**Scope:** One domain (root object + its immediate relationships) per invocation.

---

## Invocation

- **Direct read** — "Follow `agents/data-model-reviewer/AGENT.md` for the Opportunity + OpportunityLineItem + Contract domain"
- **Slash command** — [`/review-data-model`](../../commands/review-data-model.md)
- **MCP** — `get_agent("data-model-reviewer")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `skills/data/data-model-design-patterns`
4. `skills/data/external-id-strategy`
5. `skills/data/roll-up-summary-alternatives`
6. `skills/admin/object-creation-and-design`
7. `skills/admin/data-model-documentation`
8. `skills/architect/solution-design-patterns`
9. `skills/architect/high-volume-sales-data-architecture`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `root_object` | yes | `Opportunity` |
| `include_related` | no | comma-separated list; else inferred from `EntityDefinition` relationships |
| `target_org_alias` | yes |

---

## Plan

1. **Build the domain graph** — `tooling_query("SELECT QualifiedApiName, RelationshipName, ReferenceTo FROM FieldDefinition WHERE EntityDefinition.QualifiedApiName = '<root>'")` → all lookups/MDs out. Repeat for inbound relationships (`ChildRelationships` describe).
2. **Score each relationship:**
   - **Master-Detail on a child that can exist independently** → P1 (should be Lookup).
   - **Lookup on a child that cannot exist without the parent** → P1 (should be MD).
   - **Circular reference** → P0.
   - **3+ hops between two frequently co-queried objects** → P1 (denormalization candidate).
   - **Junction object with < 2 MDs** → P1 (can't be a many-to-many without both MDs).
3. **Rollup analysis** — For each MD relationship, check for Rollup Summary fields + candidate Apex/Flow rollups. If > 10 rollup summaries on a single parent → P1 (governor limit risk). Cite `skills/data/roll-up-summary-alternatives`.
4. **External ID coverage** — For each object, is there an External ID field? If the object is integration-sourced and lacks one → P0 (upsert keys missing). Cite `skills/data/external-id-strategy`.
5. **Data growth forecast** — `tooling_query("SELECT COUNT(Id) FROM <object>")` + created-date histogram over last 90 days to extrapolate growth rate. Any object projected to exceed 10M rows in 12 months → LDV flag, cite `skills/architect/high-volume-sales-data-architecture`.
6. **Index candidacy** — For each field in the top-3 expected query patterns (inferred from flow queries + Apex SOQL scans), confirm at least one column is indexed. Missing → P2 suggestion to raise custom index request.
7. **Emit the model diagram + findings** — ASCII graph + severity-sorted findings.

---

## Output Contract

1. **Summary** — root object, related count, max severity, confidence.
2. **Domain graph** — ASCII diagram (nodes + edges with relationship type).
3. **Findings table** — per object + per relationship.
4. **Rollup analysis** — rollup counts + conflict notes.
5. **Growth forecast** — object → projected row count in 12 months.
6. **Index recommendations.**
7. **Process Observations**:
   - **What was healthy** — clean External ID usage, consistent relationship naming, rollup discipline.
   - **What was concerning** — objects on the growth curve without partitioning strategy, MD-lookup confusion, 4+ hop queries implied by downstream flows.
   - **What was ambiguous** — relationships the agent couldn't confirm are used (ChildRelationships with no SOQL references).
   - **Suggested follow-up agents** — `object-designer` (for new objects suggested by consolidation), `field-impact-analyzer` for the External ID rollout, `sharing-audit-agent` if cascade behavior is unclear.
8. **Citations**.

---

## Escalation / Refusal Rules

- Any **P0 circular reference** detected → stop; report only the P0 and the smallest repro; continuing risks misleading advice.
- Any object with > 1B rows → refuse rollup analysis (governor math breaks down); recommend Big Objects or archival.

---

## What This Agent Does NOT Do

- Does not modify relationships.
- Does not design new objects (that's `object-designer`).
- Does not analyze sharing cascading (that's `sharing-audit-agent`).
- Does not auto-chain.
