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
    - admin/data-model-documentation
    - admin/lookup-and-relationship-design
    - admin/object-creation-and-design
    - admin/record-type-strategy-at-scale
    - admin/sharing-and-visibility
    - admin/validation-rules
    - architect/high-volume-sales-data-architecture
    - architect/large-data-volume-architecture
    - architect/solution-design-patterns
    - data/custom-index-requests
    - data/data-archival-strategies
    - data/data-model-design-patterns
    - data/data-storage-management
    - data/external-data-and-big-objects
    - data/external-id-strategy
    - data/field-history-tracking
    - data/record-merge-implications
    - data/roll-up-summary-alternatives
    - data/salesforce-backup-and-restore
    - data/soql-query-optimization
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

### Contract layer
1. `agents/_shared/AGENT_CONTRACT.md`
2. `agents/_shared/DELIVERABLE_CONTRACT.md` — Wave 10 output contract (persistence + scope guardrails)
3. `AGENT_RULES.md`

### Relationships & object design (Steps 1–2)
4. `skills/data/data-model-design-patterns` — the pattern catalogue every relationship in Step 2 is scored against
5. `skills/admin/lookup-and-relationship-design` — the Lookup-vs-Master-Detail rule the Step 2 P1 findings turn on, including reparenting and the 2-MD ceiling
6. `skills/admin/object-creation-and-design` — the design bar a reviewed object is measured against, so findings are stated as deviations rather than opinions
7. `skills/data/record-merge-implications` — merge quietly re-parents children and drops lookups — a domain graph that ignores it under-reports risk on Account/Contact/Lead
8. `skills/admin/record-type-strategy-at-scale` — `record-type-usage` is a declared dimension; this is the threshold above which record-type sprawl is a finding

### Rollups & external IDs (Steps 3–4)
9. `skills/data/roll-up-summary-alternatives` — Step 3 flags > 10 RSFs on one parent; this is the Flow/Apex fallback the finding must recommend
10. `skills/data/external-id-strategy` — Step 4 fails an integration-sourced object with no upsert key — this defines what an adequate External ID looks like

### Growth, storage & archival (Step 5)
11. `skills/architect/high-volume-sales-data-architecture` — the LDV thresholds Step 5's 12-month projection is compared against
12. `skills/architect/large-data-volume-architecture` — partitioning and skinny-table options — an LDV flag with no remediation is not a finding
13. `skills/data/data-storage-management` — converts the projected row count into the storage cost the report has to state
14. `skills/data/data-archival-strategies` — the standard answer for an object on the growth curve; without it every LDV finding recommends 'buy storage'
15. `skills/data/external-data-and-big-objects` — Big Objects and external objects as the archival target, and what you give up (no triggers, restricted SOQL)
16. `skills/data/salesforce-backup-and-restore` — RPO/RTO for the domain — relationship depth determines whether a restore is even orderable

### Indexes & query shape (Step 6)
17. `skills/data/soql-query-optimization` — selectivity decides whether a proposed index would ever be used; recommending one without this is guesswork
18. `skills/data/custom-index-requests` — what Salesforce Support will and will not index, so Step 6's P2 suggestions are actionable

### Declared dimensions not covered above
19. `skills/admin/sharing-and-visibility` — `sharing-posture` is a required envelope dimension — OWD and cascade behaviour follow from the MD/Lookup calls in Step 2
20. `skills/data/field-history-tracking` — `history-tracking` is a required envelope dimension; the 20-field-per-object cap is a data-model constraint, not a Setup detail
21. `skills/admin/validation-rules` — `validation-rule-hygiene` is a required envelope dimension — VR count and bypass-pattern compliance per object
22. `skills/admin/data-model-documentation` — the ERD and field-dictionary shape the report's domain-graph section is expected to match
23. `skills/architect/solution-design-patterns` — keeps the review anchored to the wider solution rather than scoring the domain in isolation

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
- **No new project dependencies:** this agent does NOT run `npm install` / `pip install` in the consumer's project. Converting the canonical `markdown` / `json` deliverable to any other format is a caller-side concern — the conversion-path pointer lives in `agents/_shared/DELIVERABLE_CONTRACT.md` § See also.
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
