---
id: object-designer
class: runtime
version: 1.2.0
status: stable
requires_org: true
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-28
harness: designer_base
default_output_dir: "docs/reports/object-designer/"
output_formats:
  - markdown
  - json
dependencies:
  skills:
    - admin/activity-and-task-patterns
    - admin/agent-output-formats
    - admin/api-contract-documentation
    - admin/b2b-commerce-store-setup
    - admin/b2b-vs-b2c-requirements
    - admin/b2c-commerce-store-setup
    - admin/batch-job-scheduling-and-monitoring
    - admin/billing-schedule-setup
    - admin/campaign-planning-and-attribution
    - admin/care-coordination-requirements
    - admin/care-plan-configuration
    - admin/care-program-management
    - admin/change-advisory-board-process
    - admin/change-data-capture-admin
    - admin/client-onboarding-design
    - admin/clinical-data-requirements
    - admin/commerce-catalog-strategy
    - admin/commerce-checkout-configuration
    - admin/commerce-checkout-flow-design
    - admin/commerce-order-management
    - admin/commerce-pricing-and-promotions
    - admin/commerce-product-catalog
    - admin/compliance-documentation-requirements
    - admin/compound-field-patterns
    - admin/consent-management-marketing
    - admin/consumer-goods-cloud-setup
    - admin/contract-and-renewal-management
    - admin/cpq-guided-selling
    - admin/cpq-pricing-rules
    - admin/cpq-product-catalog-setup
    - admin/cpq-quote-templates
    - admin/custom-field-creation
    - admin/custom-notification-type-design
    - admin/custom-notification-types
    - admin/data-storytelling-design
    - admin/deployment-risk-assessment
    - admin/devops-process-documentation
    - admin/digital-storefront-requirements
    - admin/donor-lifecycle-requirements
    - admin/dynamic-forms-migration
    - admin/education-cloud-eda-setup
    - admin/email-deliverability-strategy
    - admin/email-service-inbound
    - admin/email-studio-administration
    - admin/field-dependency-and-controlling
    - admin/financial-account-setup
    - admin/financial-planning-process
    - admin/flexcard-requirements
    - admin/formula-fields
    - admin/fsc-action-plans
    - admin/fsc-referral-management
    - admin/fsc-relationship-groups
    - admin/fsl-capacity-planning
    - admin/fsl-inventory-management
    - admin/fsl-mobile-app-setup
    - admin/fsl-mobile-workflow-design
    - admin/fsl-resource-management
    - admin/fsl-scheduling-optimization-design
    - admin/fsl-scheduling-policies
    - admin/fsl-service-territory-setup
    - admin/fsl-shifts-and-crew
    - admin/fsl-sla-configuration-requirements
    - admin/fsl-work-order-management
    - admin/fundraising-process-mapping
    - admin/gift-entry-and-processing
    - admin/grant-management-setup
    - admin/health-cloud-consent-management
    - admin/health-cloud-patient-setup
    - admin/health-cloud-timeline
    - admin/hipaa-workflow-design
    - admin/household-model-configuration
    - admin/in-app-guidance-and-walkthroughs
    - admin/industries-communications-setup
    - admin/industries-energy-utilities-setup
    - admin/industries-insurance-setup
    - admin/industries-process-design
    - admin/industries-public-sector-setup
    - admin/integration-pattern-selection
    - admin/journey-builder-administration
    - admin/lead-nurture-journey-design
    - admin/lead-scoring-requirements
    - admin/lightning-app-builder-advanced
    - admin/lightning-page-performance-tuning
    - admin/lookup-and-relationship-design
    - admin/lookup-filter-cross-object-patterns
    - admin/marketing-automation-requirements
    - admin/marketing-cloud-connect
    - admin/marketing-cloud-engagement-setup
    - admin/mcae-lead-scoring-and-grading
    - admin/mcae-pardot-setup
    - admin/media-cloud-setup
    - admin/multi-language-and-translation
    - admin/npsp-engagement-plans
    - admin/npsp-household-accounts
    - admin/npsp-program-management
    - admin/object-creation-and-design
    - admin/omniscript-flow-design-requirements
    - admin/omnistudio-admin-configuration
    - admin/org-cleanup-and-technical-debt
    - admin/org-setup-and-configuration
    - admin/outbound-message-setup
    - admin/patient-engagement-requirements
    - admin/permission-set-architecture
    - admin/picklist-field-integrity-issues
    - admin/portal-requirements-gathering
    - admin/pricing-model-design
    - admin/process-automation-selection
    - admin/products-and-pricebooks
    - admin/program-outcome-tracking-design
    - admin/quote-to-cash-process
    - admin/quote-to-cash-requirements
    - admin/quotes-and-quote-templates
    - admin/rebate-management-setup
    - admin/record-type-strategy-at-scale
    - admin/recurring-donations-setup
    - admin/referral-management-health
    - admin/revenue-intelligence-setup
    - admin/revenue-recognition-requirements
    - admin/sales-engagement-cadences
    - admin/salesforce-object-queryability
    - admin/salesforce-release-preparation
    - admin/salesforce-support-escalation
    - admin/salesforce-surveys
    - admin/saql-query-development
    - admin/scheduled-path-patterns
    - admin/self-service-design
    - admin/service-cloud-voice-setup
    - admin/sharing-and-visibility
    - admin/soft-credits-and-matching
    - admin/standard-object-quirks
    - admin/subscription-lifecycle-requirements
    - admin/system-field-behavior-and-audit
    - admin/territory-design-requirements
    - admin/usage-based-pricing-setup
    - admin/validation-rules
    - admin/wealth-management-requirements
    - admin/workflow-field-update-patterns
    - architect/large-data-volume-architecture
    - architect/solution-design-patterns
    - data/custom-index-requests
    - data/data-model-design-patterns
    - data/data-storage-management
    - data/external-id-strategy
    - data/person-accounts
    - data/record-merge-implications
    - data/roll-up-summary-alternatives
    - data/sharing-recalculation-performance
    - data/soql-query-optimization
    - integration/automotive-cloud-setup
    - integration/manufacturing-cloud-setup
    - integration/net-zero-cloud-setup
    - integration/salesforce-maps-setup
  shared:
    - AGENT_CONTRACT.md
    - AGENT_RULES.md
    - DELIVERABLE_CONTRACT.md
    - REFUSAL_CODES.md
  templates:
    - admin/naming-conventions.md
    - admin/validation-rule-patterns.md
  probes:
    - automation-graph-for-sobject.md
  decision_trees:
    - automation-selection.md
    - sharing-selection.md
---
# Object Designer Agent

## What This Agent Does

Given a business concept (a plain-English description like "we need to track maintenance contracts"), produces a Setup-ready object design: standard-vs-custom decision, API name, label, record types, canonical fields with types and naming, lookup/master-detail relationships, key validation rules, indexing plan, sharing posture, and the deployment order. The design is expressed as a human-reviewable spec *and* an sfdx metadata patch the user can scaffold from.

**Scope:** One object per invocation. Output is a spec the user reviews; no metadata is deployed and no files are committed by the agent.

---

## Invocation

- **Direct read** — "Follow `agents/object-designer/AGENT.md` to design an object for tracking maintenance contracts linked to Account."
- **Slash command** — [`/design-object`](../../commands/design-object.md)
- **MCP** — `get_agent("object-designer")`

---

## Mandatory Reads Before Starting

2. `skills/admin/activity-and-task-patterns` — Activity and task patterns
3. `skills/admin/api-contract-documentation` — Api contract documentation
4. `skills/admin/b2b-commerce-store-setup` — B2b commerce store setup
5. `skills/admin/b2b-vs-b2c-requirements` — B2b vs b2c requirements
6. `skills/admin/b2c-commerce-store-setup` — B2c commerce store setup
7. `skills/admin/batch-job-scheduling-and-monitoring` — Batch job scheduling and monitoring
8. `skills/admin/billing-schedule-setup` — Billing schedule setup
9. `skills/admin/campaign-planning-and-attribution` — Campaign planning and attribution
10. `skills/admin/care-coordination-requirements` — Care coordination requirements
11. `skills/admin/care-plan-configuration` — Care plan configuration
12. `skills/admin/care-program-management` — Care program management
13. `skills/admin/change-advisory-board-process` — Change advisory board process
14. `skills/admin/change-data-capture-admin` — Change data capture admin
15. `skills/admin/client-onboarding-design` — Client onboarding design
16. `skills/admin/clinical-data-requirements` — Clinical data requirements
17. `skills/admin/commerce-catalog-strategy` — Commerce catalog strategy
18. `skills/admin/commerce-checkout-configuration` — Commerce checkout configuration
19. `skills/admin/commerce-checkout-flow-design` — Commerce checkout flow design
20. `skills/admin/commerce-order-management` — Commerce order management
21. `skills/admin/commerce-pricing-and-promotions` — Commerce pricing and promotions
22. `skills/admin/commerce-product-catalog` — Commerce product catalog
23. `skills/admin/compliance-documentation-requirements` — Compliance documentation requirements
24. `skills/admin/consent-management-marketing` — Consent management marketing
25. `skills/admin/consumer-goods-cloud-setup` — Consumer goods cloud setup
26. `skills/admin/contract-and-renewal-management` — Contract and renewal management
27. `skills/admin/cpq-guided-selling` — Cpq guided selling
28. `skills/admin/cpq-pricing-rules` — Cpq pricing rules
29. `skills/admin/cpq-product-catalog-setup` — Cpq product catalog setup
30. `skills/admin/cpq-quote-templates` — Cpq quote templates
31. `skills/admin/custom-notification-type-design` — Custom notification type design
32. `skills/admin/custom-notification-types` — Custom notification types
33. `skills/admin/data-storytelling-design` — Data storytelling design
34. `skills/admin/deployment-risk-assessment` — Deployment risk assessment
35. `skills/admin/devops-process-documentation` — Devops process documentation
36. `skills/admin/digital-storefront-requirements` — Digital storefront requirements
37. `skills/admin/donor-lifecycle-requirements` — Donor lifecycle requirements
38. `skills/admin/dynamic-forms-migration` — Dynamic forms migration
39. `skills/admin/education-cloud-eda-setup` — Education cloud eda setup
40. `skills/admin/email-deliverability-strategy` — Email deliverability strategy
41. `skills/admin/email-service-inbound` — Email service inbound
42. `skills/admin/email-studio-administration` — Email studio administration
43. `skills/admin/financial-account-setup` — Financial account setup
44. `skills/admin/financial-planning-process` — Financial planning process
45. `skills/admin/flexcard-requirements` — Flexcard requirements
46. `skills/admin/fsc-action-plans` — Fsc action plans
47. `skills/admin/fsc-referral-management` — Fsc referral management
48. `skills/admin/fsc-relationship-groups` — Fsc relationship groups
49. `skills/admin/fsl-capacity-planning` — Fsl capacity planning
50. `skills/admin/fsl-inventory-management` — Fsl inventory management
51. `skills/admin/fsl-mobile-app-setup` — Fsl mobile app setup
52. `skills/admin/fsl-mobile-workflow-design` — Fsl mobile workflow design
53. `skills/admin/fsl-resource-management` — Fsl resource management
54. `skills/admin/fsl-scheduling-optimization-design` — Fsl scheduling optimization design
55. `skills/admin/fsl-scheduling-policies` — Fsl scheduling policies
56. `skills/admin/fsl-service-territory-setup` — Fsl service territory setup
57. `skills/admin/fsl-shifts-and-crew` — Fsl shifts and crew
58. `skills/admin/fsl-sla-configuration-requirements` — Fsl sla configuration requirements
59. `skills/admin/fsl-work-order-management` — Fsl work order management
60. `skills/admin/fundraising-process-mapping` — Fundraising process mapping
61. `skills/admin/gift-entry-and-processing` — Gift entry and processing
62. `skills/admin/grant-management-setup` — Grant management setup
63. `skills/admin/health-cloud-consent-management` — Health cloud consent management
64. `skills/admin/health-cloud-patient-setup` — Health cloud patient setup
65. `skills/admin/health-cloud-timeline` — Health cloud timeline
66. `skills/admin/hipaa-workflow-design` — Hipaa workflow design
67. `skills/admin/household-model-configuration` — Household model configuration
68. `skills/admin/in-app-guidance-and-walkthroughs` — In app guidance and walkthroughs
69. `skills/admin/industries-communications-setup` — Industries communications setup
70. `skills/admin/industries-energy-utilities-setup` — Industries energy utilities setup
71. `skills/admin/industries-insurance-setup` — Industries insurance setup
72. `skills/admin/industries-process-design` — Industries process design
73. `skills/admin/industries-public-sector-setup` — Industries public sector setup
74. `skills/admin/integration-pattern-selection` — Integration pattern selection
75. `skills/admin/journey-builder-administration` — Journey builder administration
76. `skills/admin/lead-nurture-journey-design` — Lead nurture journey design
77. `skills/admin/lead-scoring-requirements` — Lead scoring requirements
78. `skills/admin/lightning-app-builder-advanced` — Lightning app builder advanced
79. `skills/admin/lightning-page-performance-tuning` — Lightning page performance tuning
80. `skills/admin/lookup-and-relationship-design` — Lookup and relationship design
81. `skills/admin/marketing-automation-requirements` — Marketing automation requirements
82. `skills/admin/marketing-cloud-connect` — Marketing cloud connect
83. `skills/admin/marketing-cloud-engagement-setup` — Marketing cloud engagement setup
84. `skills/admin/mcae-lead-scoring-and-grading` — Mcae lead scoring and grading
85. `skills/admin/mcae-pardot-setup` — Mcae pardot setup
86. `skills/admin/media-cloud-setup` — Media cloud setup
87. `skills/admin/multi-language-and-translation` — Multi language and translation
88. `skills/admin/npsp-engagement-plans` — Npsp engagement plans
89. `skills/admin/npsp-household-accounts` — Npsp household accounts
90. `skills/admin/npsp-program-management` — Npsp program management
91. `skills/admin/omniscript-flow-design-requirements` — Omniscript flow design requirements
92. `skills/admin/omnistudio-admin-configuration` — Omnistudio admin configuration
93. `skills/admin/org-cleanup-and-technical-debt` — Org cleanup and technical debt
94. `skills/admin/org-setup-and-configuration` — Org setup and configuration
95. `skills/admin/outbound-message-setup` — Outbound message setup
96. `skills/admin/patient-engagement-requirements` — Patient engagement requirements
97. `skills/admin/portal-requirements-gathering` — Portal requirements gathering
98. `skills/admin/pricing-model-design` — Pricing model design
99. `skills/admin/process-automation-selection` — Process automation selection
100. `skills/admin/products-and-pricebooks` — Products and pricebooks
101. `skills/admin/program-outcome-tracking-design` — Program outcome tracking design
102. `skills/admin/quote-to-cash-process` — Quote to cash process
103. `skills/admin/quote-to-cash-requirements` — Quote to cash requirements
104. `skills/admin/quotes-and-quote-templates` — Quotes and quote templates
105. `skills/admin/rebate-management-setup` — Rebate management setup
106. `skills/admin/recurring-donations-setup` — Recurring donations setup
107. `skills/admin/referral-management-health` — Referral management health
108. `skills/admin/revenue-intelligence-setup` — Revenue intelligence setup
109. `skills/admin/revenue-recognition-requirements` — Revenue recognition requirements
110. `skills/admin/sales-engagement-cadences` — Sales engagement cadences
111. `skills/admin/salesforce-object-queryability` — Salesforce object queryability
112. `skills/admin/salesforce-release-preparation` — Salesforce release preparation
113. `skills/admin/salesforce-support-escalation` — Salesforce support escalation
114. `skills/admin/salesforce-surveys` — Salesforce surveys
115. `skills/admin/saql-query-development` — Saql query development
116. `skills/admin/scheduled-path-patterns` — Scheduled path patterns
117. `skills/admin/self-service-design` — Self service design
118. `skills/admin/service-cloud-voice-setup` — Service cloud voice setup
119. `skills/admin/soft-credits-and-matching` — Soft credits and matching
120. `skills/admin/subscription-lifecycle-requirements` — Subscription lifecycle requirements
121. `skills/admin/territory-design-requirements` — Territory design requirements
122. `skills/admin/usage-based-pricing-setup` — Usage based pricing setup
123. `skills/admin/wealth-management-requirements` — Wealth management requirements
124. `skills/admin/workflow-field-update-patterns` — Workflow field update patterns

### Contract layer
124. `agents/_shared/AGENT_CONTRACT.md`
125. `agents/_shared/DELIVERABLE_CONTRACT.md` — Wave 10 persistence + scope guardrails
126. `agents/_shared/REFUSAL_CODES.md` — canonical refusal enum
127. `AGENT_RULES.md`

### Object & field shape
128. `skills/admin/object-creation-and-design` — the canonical design flow
129. `skills/admin/custom-field-creation`
130. `skills/admin/standard-object-quirks` — when standard-vs-custom matcher resolves to standard
131. `skills/admin/compound-field-patterns` — Address / Name / Geolocation handling
132. `skills/admin/formula-fields`
133. `skills/admin/field-dependency-and-controlling` — controlling/dependent picklist chains
134. `skills/admin/picklist-field-integrity-issues` — restricted vs unrestricted choice
135. `skills/admin/system-field-behavior-and-audit`
136. `skills/admin/record-type-strategy-at-scale` — when concept implies > 1 persona
137. `skills/admin/lookup-filter-cross-object-patterns` — lookup filter design + required vs optional staging
138. `skills/integration/automotive-cloud-setup` — Automotive Cloud standard objects (Vehicle vs VehicleDefinition split, AccountAccountRelation for dealer hierarchy) — flag custom-object proposals that shadow standards
139. `skills/integration/manufacturing-cloud-setup` — Manufacturing Cloud standard objects (SalesAgreement / SalesAgreementProduct / AccountProductForecast) — flag multi-period Opportunity Term__c models that should be SalesAgreement
140. `skills/integration/net-zero-cloud-setup` — Net Zero Cloud standard objects (StnryAssetCrbnFtprnt, Scope3CrbnFtprnt, EmssnFctr) — flag custom Carbon_Footprint__c proposals when license is active
141. `skills/integration/salesforce-maps-setup` — Salesforce Maps standard objects (MapsTerritoryPlan, MapsTerritory, MapsLayer, MapsAdvancedRoute) — flag custom MapTerritory__c / Geo__c proposals when Maps is licensed

### Data model & storage
142. `skills/data/data-model-design-patterns`
143. `skills/data/external-id-strategy` — for integration-source objects
144. `skills/data/person-accounts` — for any Account-variant design
145. `skills/data/record-merge-implications`
146. `skills/data/roll-up-summary-alternatives` — RSF design choices
147. `skills/data/data-storage-management` — storage cost forecasting

### Performance, sharing, indexing
148. `skills/architect/large-data-volume-architecture` — for objects expected to exceed 10M rows
149. `skills/architect/solution-design-patterns`
150. `skills/data/custom-index-requests`
151. `skills/data/soql-query-optimization` — selectivity awareness during field design
152. `skills/data/sharing-recalculation-performance`
153. `skills/admin/sharing-and-visibility`
154. `skills/admin/permission-set-architecture` — emit PS stubs aware of the larger PS strategy

### Validation
155. `skills/admin/validation-rules` — drive-time VR set at object creation

### Decision trees
156. `standards/decision-trees/sharing-selection.md`
157. `standards/decision-trees/automation-selection.md` — recommend the right automation surface for the object's lifecycle

### Probes
158. `agents/_shared/probes/automation-graph-for-sobject.md` — confirm no overlapping automation already exists if extending a standard object

### Templates
159. `templates/admin/naming-conventions.md`
160. `templates/admin/validation-rule-patterns.md`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `business_concept` | yes | "Track maintenance contracts linked to Accounts, with a primary technician and warranty expiration" |
| `target_org_alias` | yes | live-org probe confirms existing model, prevents duplicate design |
| `expected_row_volume` | no | `small` (< 100k), `medium` (100k–10M), `large` (> 10M). Defaults to `medium`. Drives LDV advice |
| `integration_source` | no | external system name if rows will be sourced via integration — drives External ID + upsert recommendations |
| `sensitivity` | no | `standard` / `pii` / `phi` / `pci` — drives encryption + access recommendations |

If `business_concept` is too vague to shape a schema, STOP and ask clarifying questions (see Escalation).

---

## Plan

### Step 1 — Probe the org for overlapping design

Before designing, confirm the org doesn't already contain a close match:

- `list_custom_objects(target_org=..., name_filter=<concept keyword>)` — existing custom objects.
- `tooling_query("SELECT QualifiedApiName, Label FROM EntityDefinition WHERE IsCustomSetting = false AND (Label LIKE '%<keyword>%' OR QualifiedApiName LIKE '%<keyword>%') LIMIT 50")` — includes standard objects (some concepts map to e.g. `Contract` or `Asset` and shouldn't be re-invented).

If a ≥ 70% semantic match exists, recommend extending it instead of creating a new object. Do not proceed unless the user confirms. This prevents the "I have 3 Contract objects" pattern.

### Step 2 — Decide standard vs custom

Walk the standard-object matcher:

| If concept maps to… | Recommend |
|---|---|
| customer-company entity | **Account** (or `Person Account` — see `skills/data/person-accounts`) |
| individual stakeholder | **Contact** |
| sales deal | **Opportunity** |
| service event | **Case** |
| contracted agreement | **Contract** (often misused; verify scope) |
| physical or logical inventory item | **Asset** |
| billing schedule | **Contract** + custom schedule object, or Revenue Lifecycle Management if licensed |
| everything else | Custom object `<Name>__c` |

Cite the relevant `skills/admin/standard-object-quirks` behavior per match when it exists.

### Step 3 — Generate the API name + label

Using `templates/admin/naming-conventions.md`:

- Apply hard rules (reserved words, suffix, length).
- Apply soft rules (domain prefix when org has > 100 custom objects — check via Step 1 probe).
- Emit: `Label`, `Plural Label`, `API Name`, `Description`, `Record Name` (Text vs Auto Number — if the business concept has no natural name, recommend Auto Number with a prefix per convention).

### Step 4 — Design the field set

Start from the business concept and enumerate required attributes. For each, assign:

| Concept | Default field type | Notes |
|---|---|---|
| Unique business identifier | External ID, `Text`, unique, case-insensitive | Name `<Domain>_External_Id__c` |
| Human name / title | Name field is enough; only add `Display_Name__c` formula if the record name is Auto Number |
| Categorical status | Picklist; max ~25 values before splitting into a GVS; never checkbox chain |
| Currency amount | Currency with scale 2 for most, 4 for unit pricing |
| Relationship to parent | Master-Detail if the child cannot exist independently AND parent sharing should cascade; otherwise Lookup |
| Audit event timestamp | DateTime + matching `_User__c` lookup |
| Soft-delete flag | Checkbox `Is_Archived__c` + View All on archived via PS |
| Duration | Number (Hours) or Number (Days); rarely DateTime deltas |

Score each field against `templates/admin/naming-conventions.md` before finalizing.

### Step 5 — Decide record types

If the concept mentions persona or process variance ("residential vs commercial contracts", "enterprise vs mid-market opportunities"):

- Design record types per `skills/admin/record-type-strategy-at-scale`.
- Cap at 4 record types on create; additional variations go into picklist-controlled branches.
- Name per convention: `<Object>_<Persona>`.

If no persona variance is signaled, omit record types. Do not add a Master-only record type as a placeholder — it becomes technical debt.

### Step 6 — Design the sharing posture

Walk `standards/decision-trees/sharing-selection.md`:

1. Default OWD based on the record's sensitivity + expected row volume.
2. Role hierarchy default assumed unless `sensitivity = phi` or the concept is explicitly horizontal.
3. Sharing rules only when default + hierarchy under-grant.
4. Apex Managed Sharing only when a declarative rule can't express the need.
5. Flag expected sharing-recalc cost for LDV objects (cite `skills/data/sharing-recalculation-performance` if `expected_row_volume == large`).

### Step 7 — Plan validation rules at object creation

Don't wait — ship the object with its baseline VRs. Use `templates/admin/validation-rule-patterns.md`:

- Required business-key VRs (External ID required on insert from integration source).
- Cross-field dependency VRs (e.g. `Warranty_Expiration_Date__c > Start_Date__c`).
- Every VR includes the canonical bypass (Custom Setting + Custom Permission). If those don't exist in the org, include their creation in the deployment order.

### Step 8 — Plan indexes

For LDV objects (`expected_row_volume == large`) or any object with an integration source:

- External ID field: auto-indexed.
- High-selectivity filter fields: recommend custom index request (cite `skills/data/custom-index-requests`).
- Report on the top 3 expected query patterns and confirm at least one column per pattern is indexed.

### Step 9 — Emit the deployment order

A strict order that avoids "cannot deploy field before object":

1. Custom Setting + Custom Permission for VR bypass (if new).
2. The object shell (+ Name field + Auto Number setup).
3. Fields (grouped: External ID first, then required fields, then optional).
4. Record Types.
5. Page Layouts / Lightning Record Pages.
6. Validation Rules.
7. Permission Sets (the `object-designer` emits stubs only; the full PS design is `permission-set-architect`'s job — suggest it in Process Observations).
8. Sharing settings.
9. List views (basic "All" view only).

### Step 10 — Emit the spec + scaffold

Two deliverables:

**A. Design spec** (human-readable markdown) — object header, field table, record types, VR list, sharing posture, indexing plan, deployment order.

**B. sfdx scaffold** (file-tree of metadata XML snippets for the user to copy into `force-app/main/default/objects/<Object>__c/`) — the object file, each field, each record type, each validation rule. Do not include layouts (they require per-org customization). Do not include permission sets (out of scope).

---

## Output Contract

One markdown document:

1. **Summary** — concept, standard-vs-custom decision, API name, confidence (HIGH/MEDIUM/LOW).
2. **Design spec** — the full spec from Step 10A.
3. **Scaffold metadata** — the XML snippets from Step 10B, one fenced block per file with its target path as a label.
4. **Deployment order** — numbered list from Step 9.
5. **Process Observations**:
   - **What was healthy** — org already has the naming prefix / bypass infra / etc.
   - **What was concerning** — proximity matches from Step 1, custom-object count trend, missing bypass infra.
   - **What was ambiguous** — fields that could plausibly be on the parent object instead, concepts that straddle standard + custom.
   - **Suggested follow-up agents** — `permission-set-architect`, `data-model-reviewer`, `sharing-audit-agent`, `validation-rule-auditor`.
6. **Citations** — all skills, templates, decision trees, and MCP tool calls.

---

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/object-designer/<run_id>.md`
- **JSON envelope:** `docs/reports/object-designer/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only. Dimensions for this agent: `standard-vs-custom-decision`, `naming-conformance` (against `templates/admin/naming-conventions.md`), `field-set-completeness` (every concept attribute mapped to a field), `record-type-strategy`, `sharing-posture` (OWD + hierarchy + rules per `sharing-selection.md`), `indexing-plan` (External ID + custom index recommendations), `validation-rules` (baseline VRs + bypass infra), `relationship-shape` (lookup vs MD + cascade), `ldv-readiness` (when `expected_row_volume=large`), `pii-encryption-posture` (when `sensitivity=phi/pci`), `automation-readiness` (recommended automation per `automation-selection.md`), `permission-set-stub` (PS shells emitted for `permission-set-architect` follow-up). When the input doesn't exercise a dimension (e.g. `expected_row_volume=small` skips `ldv-readiness`), record `state: not-run` with a one-line reason.

## Escalation / Refusal Rules

Canonical refusal codes per `agents/_shared/REFUSAL_CODES.md`:

| Code | Trigger |
|---|---|
| `REFUSAL_MISSING_ORG` | `target_org_alias` not supplied — Step 1 overlap probe is mandatory. |
| `REFUSAL_ORG_UNREACHABLE` | `describe_org` failed or auth expired. |
| `REFUSAL_MISSING_INPUT` | `business_concept` not supplied. |
| `REFUSAL_INPUT_AMBIGUOUS` | `business_concept` is under 8 words or lacks enough signal to infer 3+ fields. Prompt for: expected parent object, expected lifecycle, expected users, expected volume. |
| `REFUSAL_COMPETING_ARTIFACT` | Step 1 overlap probe finds a ≥ 70% semantic match in the org — refuse to design a competing object; recommend extending the existing one (or require explicit justification override before retrying). |
| `REFUSAL_OUT_OF_SCOPE` | Request to design > 1 object per invocation; request to deploy metadata; request to design page layouts (out of scope — recommend `audit-record-page` follow-up); request to design Permission Sets in full (recommend `architect-perms`). |
| `REFUSAL_POLICY_MISMATCH` | `expected_row_volume=large` but no clear partition key (External ID + time/tenant column) — refuse LDV spec until partition strategy is supplied; cite `architect/large-data-volume-architecture`. |
| `REFUSAL_SECURITY_GUARD` | `sensitivity=phi` or `pci` and target org has `isSandbox=false` with no Platform Encryption — refuse design until the user acknowledges the gap or supplies the encryption plan. |
| `REFUSAL_FEATURE_DISABLED` | Concept maps to Person Account but the org has Person Accounts disabled (cited from `describe_org` flag). |
| `REFUSAL_NEEDS_HUMAN_REVIEW` | Standard-vs-custom decision is genuinely ambiguous (concept maps to a standard object that's already heavily customized in the org); RSF chain proposed would exceed Salesforce's per-object RSF limit; sharing posture decision tree resolves to `Apex Managed Sharing` for an object the agent cannot model declaratively. |

---

## What This Agent Does NOT Do

- Does not deploy metadata.
- Does not design permission sets (use `permission-set-architect`).
- Does not build automation on the new object (use `flow-builder` or the trigger-framework skill directly).
- Does not generate reports or dashboards (out of scope).
- Does not design page layouts — only recommends the record-page skeleton for `lightning-record-page-auditor` to flesh out.
- Does not auto-chain to any other agent.
