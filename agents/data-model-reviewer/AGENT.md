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
default_output_dir: "docs/reports/data-model-reviewer/"
output_formats:
  - markdown
  - json
multi_dimensional: true
dependencies:
  skills:
    - admin/agent-output-formats
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
    - DELIVERABLE_CONTRACT.md
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
10. `agents/_shared/DELIVERABLE_CONTRACT.md` — Wave 10 output contract (persistence + scope guardrails)

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

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/data-model-reviewer/<run_id>.md`
- **JSON envelope:** `docs/reports/data-model-reviewer/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only.

### Dimensions (Wave 10 contract)

The agent's envelope MUST place every dimension below in either `dimensions_compared[]` or `dimensions_skipped[]`.

| Dimension | Notes |
|---|---|
| `object-design` | Standard vs custom, record-type usage, fields |
| `relationships` | Lookup vs master-detail vs junction |
| `sharing-posture` | OWD + sharing rules + teams |
| `indexes` | Custom indexes, skinny tables, LDV markers |
| `history-tracking` | Field History + Audit Trail configuration |
| `external-id-coverage` | Upsert-ready external IDs per integration |
| `validation-rule-hygiene` | VR count, bypass pattern compliance |

## Escalation / Refusal Rules

- Any **P0 circular reference** detected → stop; report only the P0 and the smallest repro; continuing risks misleading advice.
- Any object with > 1B rows → refuse rollup analysis (governor math breaks down); recommend Big Objects or archival.

---

## What This Agent Does NOT Do

- Does not modify relationships.
- Does not design new objects (that's `object-designer`).
- Does not analyze sharing cascading (that's `sharing-audit-agent`).
- Does not auto-chain.
