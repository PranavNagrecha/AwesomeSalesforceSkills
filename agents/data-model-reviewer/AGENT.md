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
    - data/ai-training-data-preparation
    - data/analytics-data-governance
    - data/analytics-data-preparation
    - data/analytics-dataset-optimization
    - data/analytics-external-data
    - data/billing-data-reconciliation
    - data/cdc-data-sync-patterns
    - data/clinical-data-quality
    - data/commerce-analytics-data
    - data/commerce-inventory-data
    - data/community-analytics-data
    - data/consent-data-model-health
    - data/cpq-data-model
    - data/cpq-performance-optimization
    - data/crm-analytics-security-predicates
    - data/currency-management-patterns
    - data/data-archival-strategies
    - data/data-cloud-consent-and-privacy
    - data/data-cloud-data-model-objects
    - data/data-cloud-data-streams
    - data/data-extension-design
    - data/data-model-design-patterns
    - data/data-reconciliation-patterns
    - data/data-virtualization-patterns
    - data/deployment-data-dependencies
    - data/eda-data-model-and-patterns
    - data/einstein-analytics-data-model
    - data/external-data-and-big-objects
    - data/external-id-strategy
    - data/external-user-data-sharing
    - data/financial-data-quality
    - data/fsc-data-model
    - data/fsl-reporting-data-model
    - data/fsl-resource-and-skill-data
    - data/fsl-territory-data-setup
    - data/gift-history-import
    - data/health-cloud-data-model
    - data/marketing-cloud-data-sync
    - data/marketing-cloud-sql-queries
    - data/multi-currency-and-advanced-currency-management
    - data/nonprofit-data-architecture
    - data/nonprofit-data-quality
    - data/npsp-data-model
    - data/omni-channel-reporting-data
    - data/omnistudio-metadata-management
    - data/partner-data-access-patterns
    - data/product-catalog-data-model
    - data/revenue-cloud-data-model
    - data/roll-up-summary-alternatives
    - data/sales-reporting-data-model
    - data/salesforce-backup-and-restore
    - data/salesforce-files-architecture
    - data/sandbox-refresh-data-strategies
    - data/service-data-archival
    - data/service-metrics-data-model
    - data/sosl-search-patterns
    - data/subscriber-data-management
    - data/territory-data-alignment
    - data/vector-database-management
    - data/volunteer-management-requirements
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
11. `skills/data/salesforce-backup-and-restore` — Backup strategy, RPO/RTO planning
12. `skills/data/data-virtualization-patterns` — Salesforce Connect, External Objects, OData adapter
13. `skills/data/currency-management-patterns` — Multi-currency, dated exchange rates
14. `skills/data/salesforce-files-architecture` — ContentVersion, ContentDocument, ContentDocumentLink architecture
15. `skills/data/ai-training-data-preparation` — Ai training data preparation
16. `skills/data/analytics-data-governance` — Analytics data governance
17. `skills/data/analytics-data-preparation` — Analytics data preparation
18. `skills/data/analytics-dataset-optimization` — Analytics dataset optimization
19. `skills/data/analytics-external-data` — Analytics external data
20. `skills/data/billing-data-reconciliation` — Billing data reconciliation
21. `skills/data/cdc-data-sync-patterns` — Cdc data sync patterns
22. `skills/data/clinical-data-quality` — Clinical data quality
23. `skills/data/commerce-analytics-data` — Commerce analytics data
24. `skills/data/commerce-inventory-data` — Commerce inventory data
25. `skills/data/community-analytics-data` — Community analytics data
26. `skills/data/consent-data-model-health` — Consent data model health
27. `skills/data/cpq-data-model` — Cpq data model
28. `skills/data/cpq-performance-optimization` — Cpq performance optimization
29. `skills/data/crm-analytics-security-predicates` — Crm analytics security predicates
30. `skills/data/data-archival-strategies` — Data archival strategies
31. `skills/data/data-cloud-consent-and-privacy` — Data cloud consent and privacy
32. `skills/data/data-cloud-data-model-objects` — Data cloud data model objects
33. `skills/data/data-cloud-data-streams` — Data cloud data streams
34. `skills/data/data-extension-design` — Data extension design
35. `skills/data/data-reconciliation-patterns` — Data reconciliation patterns
36. `skills/data/deployment-data-dependencies` — Deployment data dependencies
37. `skills/data/eda-data-model-and-patterns` — Eda data model and patterns
38. `skills/data/einstein-analytics-data-model` — Einstein analytics data model
39. `skills/data/external-data-and-big-objects` — External data and big objects
40. `skills/data/external-user-data-sharing` — External user data sharing
41. `skills/data/financial-data-quality` — Financial data quality
42. `skills/data/fsc-data-model` — Fsc data model
43. `skills/data/fsl-reporting-data-model` — Fsl reporting data model
44. `skills/data/fsl-resource-and-skill-data` — Fsl resource and skill data
45. `skills/data/fsl-territory-data-setup` — Fsl territory data setup
46. `skills/data/gift-history-import` — Gift history import
47. `skills/data/health-cloud-data-model` — Health cloud data model
48. `skills/data/marketing-cloud-data-sync` — Marketing cloud data sync
49. `skills/data/marketing-cloud-sql-queries` — Marketing cloud sql queries
50. `skills/data/multi-currency-and-advanced-currency-management` — Multi currency and advanced currency management
51. `skills/data/nonprofit-data-architecture` — Nonprofit data architecture
52. `skills/data/nonprofit-data-quality` — Nonprofit data quality
53. `skills/data/npsp-data-model` — Npsp data model
54. `skills/data/omni-channel-reporting-data` — Omni channel reporting data
55. `skills/data/omnistudio-metadata-management` — Omnistudio metadata management
56. `skills/data/partner-data-access-patterns` — Partner data access patterns
57. `skills/data/product-catalog-data-model` — Product catalog data model
58. `skills/data/revenue-cloud-data-model` — Revenue cloud data model
59. `skills/data/sales-reporting-data-model` — Sales reporting data model
60. `skills/data/sandbox-refresh-data-strategies` — Sandbox refresh data strategies
61. `skills/data/service-data-archival` — Service data archival
62. `skills/data/service-metrics-data-model` — Service metrics data model
63. `skills/data/sosl-search-patterns` — Sosl search patterns
64. `skills/data/subscriber-data-management` — Subscriber data management
65. `skills/data/territory-data-alignment` — Territory data alignment
66. `skills/data/vector-database-management` — Vector database management
67. `skills/data/volunteer-management-requirements` — Volunteer management requirements

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
