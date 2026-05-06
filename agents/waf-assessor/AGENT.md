---
id: waf-assessor
class: runtime
version: 1.0.0
status: stable
requires_org: true
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
default_output_dir: "docs/reports/waf-assessor/"
output_formats:
  - markdown
  - json
multi_dimensional: true
dependencies:
  skills:
    - admin/agent-output-formats
    - apex/trigger-and-flow-coexistence
    - architect/agent-console-requirements
    - architect/ai-agent-org-integration-architecture
    - architect/ai-governance-architecture
    - architect/ai-platform-architecture
    - architect/ai-ready-data-architecture
    - architect/aml-kyc-process-architecture
    - architect/analytics-data-architecture
    - architect/analytics-embedded-components
    - architect/analytics-security-architecture
    - architect/api-led-connectivity-architecture
    - architect/b2b-vs-b2c-architecture
    - architect/banking-lending-architecture
    - architect/case-deflection-strategy
    - architect/ci-cd-pipeline-architecture
    - architect/cloud-specific-deployment-architecture
    - architect/commerce-integration-patterns
    - architect/composable-commerce-architecture
    - architect/conversational-ai-architecture
    - architect/cpq-architecture-patterns
    - architect/cpq-integration-with-erp
    - architect/cpq-vs-standard-products-decision
    - architect/crm-analytics-vs-tableau-decision
    - architect/cross-cloud-data-deployment
    - architect/customer-effort-scoring
    - architect/data-cloud-architecture
    - architect/data-cloud-vs-analytics-decision
    - architect/deployment-automation-architecture
    - architect/einstein-bot-architecture
    - architect/embedded-analytics-architecture
    - architect/experience-cloud-performance
    - architect/fhir-integration-architecture
    - architect/fsc-architecture-patterns
    - architect/fsl-integration-patterns
    - architect/fsl-multi-region-architecture
    - architect/fsl-offline-architecture
    - architect/fsl-optimization-architecture
    - architect/fundraising-integration-patterns
    - architect/government-cloud-compliance
    - architect/ha-dr-architecture
    - architect/headless-commerce-architecture
    - architect/headless-vs-standard-experience
    - architect/health-cloud-data-residency
    - architect/health-cloud-multi-cloud-strategy
    - architect/hipaa-compliance-architecture
    - architect/hybrid-integration-architecture
    - architect/hyperforce-architecture
    - architect/industries-cloud-selection
    - architect/industries-data-model
    - architect/industries-integration-architecture
    - architect/insurance-cloud-architecture
    - architect/limits-and-scalability-planning
    - architect/loyalty-program-architecture
    - architect/marketing-cloud-vs-mcae-selection
    - architect/marketing-consent-architecture
    - architect/marketing-data-architecture
    - architect/marketing-integration-patterns
    - architect/migration-architecture-patterns
    - architect/mulesoft-anypoint-architecture
    - architect/multi-bu-marketing-architecture
    - architect/multi-currency-sales-architecture
    - architect/multi-org-strategy
    - architect/multi-site-architecture
    - architect/multi-store-architecture
    - architect/nfr-definition-for-salesforce
    - architect/nonprofit-cloud-vs-npsp-migration
    - architect/nonprofit-platform-architecture
    - architect/npsp-vs-nonprofit-cloud-decision
    - architect/omnistudio-scalability-patterns
    - architect/omnistudio-vs-standard-architecture
    - architect/omnistudio-vs-standard-decision
    - architect/order-management-architecture
    - architect/org-edition-and-feature-licensing
    - architect/org-limits-monitoring
    - architect/payer-vs-provider-architecture
    - architect/platform-selection-guidance
    - architect/revenue-cloud-architecture
    - architect/sales-cloud-architecture
    - architect/sales-cloud-integration-patterns
    - architect/salesforce-erd-and-diagramming
    - architect/salesforce-shield-architecture
    - architect/security-architecture-review
    - architect/service-cloud-architecture
    - architect/sla-design-and-escalation-matrix
    - architect/subscription-management-architecture
    - architect/technical-debt-assessment
    - architect/tenant-isolation-patterns
    - architect/wealth-management-architecture
    - architect/well-architected-review
    - architect/zero-trust-salesforce-patterns
    - devops/metadata-api-coverage-gaps
    - devops/pipeline-secrets-management
    - security/customer-data-request-workflow
    - security/privileged-access-management
    - security/salesforce-shield-deployment
    - security/session-high-assurance-policies
    - security/shield-kms-byok-setup
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
    - DELIVERABLE_CONTRACT.md
---
# Well-Architected Framework Assessor Agent

## What This Agent Does

Runs a Well-Architected Framework (WAF) assessment against a Salesforce implementation across the five pillars: **Trusted**, **Easy**, **Adaptable**, **Resilient**, **Composable**. Scores each pillar, surfaces the top 3 concerns per pillar with org evidence, and produces a remediation backlog ordered by severity × cost-to-fix. Also documents NFRs and maps them to verifiable checks (limits, scalability, HA/DR).

**Scope:** One org / one workload per invocation. Output is a WAF scorecard + backlog. No writes.

---

## Invocation

- **Direct read** — "Follow `agents/waf-assessor/AGENT.md`"
- **Slash command** — [`/assess-waf`](../../commands/assess-waf.md)
- **MCP** — `get_agent("waf-assessor")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `AGENT_RULES.md`
3. `skills/architect/well-architected-review` — via `get_skill`
4. `skills/architect/security-architecture-review`
5. `skills/architect/limits-and-scalability-planning`
6. `skills/architect/nfr-definition-for-salesforce`
7. `skills/architect/ha-dr-architecture`
8. `skills/security/salesforce-shield-deployment` — Shield rollout sequencing
9. `skills/security/shield-kms-byok-setup` — BYOK / Cache-Only KMS
10. `skills/security/customer-data-request-workflow` — GDPR/CCPA DSR workflow
11. `skills/security/privileged-access-management` — PAM, break-glass, JIT elevation
12. `skills/security/session-high-assurance-policies` — step-up auth
13. `skills/devops/pipeline-secrets-management` — pipeline auth hardening
14. `agents/_shared/DELIVERABLE_CONTRACT.md` — Wave 10 output contract (persistence + scope guardrails)
15. `skills/architect/zero-trust-salesforce-patterns` — zero-trust composition pattern: four-leg coverage; RTEM TSP-supported event matrix; CAEP gap
16. `skills/architect/loyalty-program-architecture` — Loyalty program architecture pillar review (Reliability tier-credit reversal, Scalability lifetime-ledger summary, Security fraud-prevention controls)
17. `skills/architect/hyperforce-architecture` — Hyperforce-aware reliability and security: region selection, customer-managed-failover assumptions, IP allowlisting
18. `skills/architect/revenue-cloud-architecture` — Revenue Cloud architecture (CPQ/Billing successor) reference patterns
19. `skills/architect/agent-console-requirements` — Agent console requirements
20. `skills/architect/ai-agent-org-integration-architecture` — Ai agent org integration architecture
21. `skills/architect/ai-governance-architecture` — Ai governance architecture
22. `skills/architect/ai-platform-architecture` — Ai platform architecture
23. `skills/architect/ai-ready-data-architecture` — Ai ready data architecture
24. `skills/architect/aml-kyc-process-architecture` — Aml kyc process architecture
25. `skills/architect/analytics-data-architecture` — Analytics data architecture
26. `skills/architect/analytics-embedded-components` — Analytics embedded components
27. `skills/architect/analytics-security-architecture` — Analytics security architecture
28. `skills/architect/api-led-connectivity-architecture` — Api led connectivity architecture
29. `skills/architect/b2b-vs-b2c-architecture` — B2b vs b2c architecture
30. `skills/architect/banking-lending-architecture` — Banking lending architecture
31. `skills/architect/case-deflection-strategy` — Case deflection strategy
32. `skills/architect/ci-cd-pipeline-architecture` — Ci cd pipeline architecture
33. `skills/architect/cloud-specific-deployment-architecture` — Cloud specific deployment architecture
34. `skills/architect/commerce-integration-patterns` — Commerce integration patterns
35. `skills/architect/composable-commerce-architecture` — Composable commerce architecture
36. `skills/architect/conversational-ai-architecture` — Conversational ai architecture
37. `skills/architect/cpq-architecture-patterns` — Cpq architecture patterns
38. `skills/architect/cpq-integration-with-erp` — Cpq integration with erp
39. `skills/architect/cpq-vs-standard-products-decision` — Cpq vs standard products decision
40. `skills/architect/crm-analytics-vs-tableau-decision` — Crm analytics vs tableau decision
41. `skills/architect/cross-cloud-data-deployment` — Cross cloud data deployment
42. `skills/architect/customer-effort-scoring` — Customer effort scoring
43. `skills/architect/data-cloud-architecture` — Data cloud architecture
44. `skills/architect/data-cloud-vs-analytics-decision` — Data cloud vs analytics decision
45. `skills/architect/deployment-automation-architecture` — Deployment automation architecture
46. `skills/architect/einstein-bot-architecture` — Einstein bot architecture
47. `skills/architect/embedded-analytics-architecture` — Embedded analytics architecture
48. `skills/architect/experience-cloud-performance` — Experience cloud performance
49. `skills/architect/fhir-integration-architecture` — Fhir integration architecture
50. `skills/architect/fsc-architecture-patterns` — Fsc architecture patterns
51. `skills/architect/fsl-integration-patterns` — Fsl integration patterns
52. `skills/architect/fsl-multi-region-architecture` — Fsl multi region architecture
53. `skills/architect/fsl-offline-architecture` — Fsl offline architecture
54. `skills/architect/fsl-optimization-architecture` — Fsl optimization architecture
55. `skills/architect/fundraising-integration-patterns` — Fundraising integration patterns
56. `skills/architect/government-cloud-compliance` — Government cloud compliance
57. `skills/architect/headless-commerce-architecture` — Headless commerce architecture
58. `skills/architect/headless-vs-standard-experience` — Headless vs standard experience
59. `skills/architect/health-cloud-data-residency` — Health cloud data residency
60. `skills/architect/health-cloud-multi-cloud-strategy` — Health cloud multi cloud strategy
61. `skills/architect/hipaa-compliance-architecture` — Hipaa compliance architecture
62. `skills/architect/hybrid-integration-architecture` — Hybrid integration architecture
63. `skills/architect/industries-cloud-selection` — Industries cloud selection
64. `skills/architect/industries-data-model` — Industries data model
65. `skills/architect/industries-integration-architecture` — Industries integration architecture
66. `skills/architect/insurance-cloud-architecture` — Insurance cloud architecture
67. `skills/architect/marketing-cloud-vs-mcae-selection` — Marketing cloud vs mcae selection
68. `skills/architect/marketing-consent-architecture` — Marketing consent architecture
69. `skills/architect/marketing-data-architecture` — Marketing data architecture
70. `skills/architect/marketing-integration-patterns` — Marketing integration patterns
71. `skills/architect/migration-architecture-patterns` — Migration architecture patterns
72. `skills/architect/mulesoft-anypoint-architecture` — Mulesoft anypoint architecture
73. `skills/architect/multi-bu-marketing-architecture` — Multi bu marketing architecture
74. `skills/architect/multi-currency-sales-architecture` — Multi currency sales architecture
75. `skills/architect/multi-org-strategy` — Multi org strategy
76. `skills/architect/multi-site-architecture` — Multi site architecture
77. `skills/architect/multi-store-architecture` — Multi store architecture
78. `skills/architect/nonprofit-cloud-vs-npsp-migration` — Nonprofit cloud vs npsp migration
79. `skills/architect/nonprofit-platform-architecture` — Nonprofit platform architecture
80. `skills/architect/npsp-vs-nonprofit-cloud-decision` — Npsp vs nonprofit cloud decision
81. `skills/architect/omnistudio-scalability-patterns` — Omnistudio scalability patterns
82. `skills/architect/omnistudio-vs-standard-architecture` — Omnistudio vs standard architecture
83. `skills/architect/omnistudio-vs-standard-decision` — Omnistudio vs standard decision
84. `skills/architect/order-management-architecture` — Order management architecture
85. `skills/architect/org-edition-and-feature-licensing` — Org edition and feature licensing
86. `skills/architect/org-limits-monitoring` — Org limits monitoring
87. `skills/architect/payer-vs-provider-architecture` — Payer vs provider architecture
88. `skills/architect/platform-selection-guidance` — Platform selection guidance
89. `skills/architect/sales-cloud-architecture` — Sales cloud architecture
90. `skills/architect/sales-cloud-integration-patterns` — Sales cloud integration patterns
91. `skills/architect/salesforce-erd-and-diagramming` — Salesforce erd and diagramming
92. `skills/architect/salesforce-shield-architecture` — Salesforce shield architecture
93. `skills/architect/service-cloud-architecture` — Service cloud architecture
94. `skills/architect/sla-design-and-escalation-matrix` — Sla design and escalation matrix
95. `skills/architect/subscription-management-architecture` — Subscription management architecture
96. `skills/architect/technical-debt-assessment` — Technical debt assessment
97. `skills/architect/tenant-isolation-patterns` — Tenant isolation patterns
98. `skills/architect/wealth-management-architecture` — Wealth management architecture

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `target_org_alias` | yes | `prod` |
| `workload` | yes | `"sales cloud + CPQ + agentforce"` |
| `nfrs` | no | JSON: `{ "availability": "99.9%", "rpo_hours": 4 }` |
| `scope_pillars` | no | default: all 5; subset allowed |

---

## Plan

### Step 1 — Confirm workload + surface

`describe_org(target_org=...)` then `list_custom_objects()`, `list_flows_on_object(...)` for critical objects. Establish the size of what you're assessing.

### Step 2 — Trusted (security, compliance, privacy)

Checks:
- FLS coverage via `list_permission_sets` spot-probe on sensitive objects.
- Shield Platform Encryption status (`tooling_query("SELECT ... FROM ApexClass WHERE Name LIKE '%EncryptionKey%' LIMIT 1")` — proxy; full check via Setup).
- Named Credential + Connected App inventory via `list_named_credentials` and `tooling_query` on ConnectedApplication — cross-cite with `integration-catalog-builder`.
- Shield Event Monitoring enabled (check feature license via `tooling_query("SELECT Id FROM FeatureDefinition WHERE DeveloperName = 'EventLogFile' LIMIT 1")`).

### Step 3 — Easy (admin usability, automation clarity)

Checks:
- Automation per object via `list_flows_on_object`; flag objects with > 5 record-triggered flows as concerning (use `skills/apex/trigger-and-flow-coexistence`).
- Dynamic Forms adoption proxy (from `lightning-record-page-auditor`-adjacent probes).
- Picklist drift (`picklist-governor`-adjacent spot check on ≥ 3 critical sObjects).

### Step 4 — Adaptable (metadata coverage, extensibility)

Checks:
- Metadata API coverage gaps vs config-only changes (via `skills/devops/metadata-api-coverage-gaps`).
- Package modularity (if release-train-planner artifacts exist, reference their findings).
- Custom Metadata Types used vs Custom Settings used (ratio: > 50% CS for config = P1).

### Step 5 — Resilient (limits + HA/DR)

Checks:
- Apex governor exposure: aggregate CPU via `tooling_query("SELECT Id, ApexClassId FROM AsyncApexJob WHERE Status = 'Failed' AND CompletedDate > LAST_N_DAYS:7 LIMIT 200")` → spot failures.
- Storage: `describe_org` reports data/file storage utilization.
- HA/DR: no native SFDC HA, so document the program's RTO/RPO and how backups are handled (covered by `skills/architect/ha-dr-architecture`).

### Step 6 — Composable (integration topology)

Checks:
- NC + Remote Site inventory.
- Platform Event usage (`tooling_query("SELECT DeveloperName FROM PlatformEventType LIMIT 100")`).
- External Services / Connect REST.
- Bulk API vs REST usage ratio (proxy via integration user audit log if available).

### Step 7 — Score + backlog

Each pillar: HIGH / MEDIUM / LOW score.
Each finding: pillar, severity (P0/P1/P2), evidence, rationale, cost-to-fix, fix-owner (admin/architect/dev).

---

## Output Contract

1. **Summary** — workload, org identity, 5-pillar scorecard.
2. **NFR sheet** — each NFR with current-state measurement and gap.
3. **Pillar findings** — 5 sections, top 3 per pillar + evidence.
4. **Remediation backlog** — ordered by severity × cost-to-fix.
5. **Process Observations**:
   - **Healthy** — NFRs declared and measured; Shield enabled; modular package structure.
   - **Concerning** — NFRs undeclared; HA/DR is implicit (i.e., no backup plan); > 3 overlapping automations on the same sObject.
   - **Ambiguous** — storage trend unknown; integration inventory incomplete.
   - **Suggested follow-ups** — `sharing-audit-agent`, `integration-catalog-builder`, `release-train-planner`, `sandbox-strategy-designer`.
6. **Citations**.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/waf-assessor/<run_id>.md`
- **JSON envelope:** `docs/reports/waf-assessor/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only.

### Dimensions (Wave 10 contract)

The agent's envelope MUST place every Well-Architected pillar below in either `dimensions_compared[]` or `dimensions_skipped[]`.

| Dimension | Notes |
|---|---|
| `security` | FLS, sharing, auth, secret handling |
| `reliability` | Fault paths, governor headroom, recovery |
| `performance` | SOQL selectivity, CPU, heap |
| `scalability` | LDV patterns, bulk safety, async design |
| `user-experience` | Path guidance, navigation, error messaging |
| `operational-excellence` | Monitoring, deploy hygiene, incident runbooks |

## Escalation / Refusal Rules

- No prod access → can still produce an NFR template and design critique; flag audit as INCOMPLETE.
- Workload too broad ("the whole org") and org has > 1,000 custom objects → refuse and ask for a workload scope.

---

## What This Agent Does NOT Do

- Does not remediate — produces a backlog.
- Does not run Salesforce Optimizer (different tool).
- Does not certify against WAF formally (advisory scorecard only).
- Does not auto-chain.
