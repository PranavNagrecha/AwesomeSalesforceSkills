---
name: territory-design-requirements
description: "Use this skill when gathering or evaluating requirements for a Salesforce Enterprise Territory Management (ETM) territory design: alignment criteria, coverage model selection, assignment rule logic, geographic considerations, hierarchy depth and breadth, and user-to-territory ratios. Trigger keywords: territory design, territory alignment, territory model requirements, sales coverage model, territory criteria, geographic territory, named account territory, overlay territory. NOT for ETM configuration or setup steps — use enterprise-territory-management for that. NOT for role hierarchy design — use sharing-and-visibility."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Operational Excellence
triggers:
  - "how should we design our territory structure before we configure ETM"
  - "what are the requirements for building a good territory model for our sales team"
  - "we need to decide whether to use geographic territories or named account territories"
  - "how many territories should we create and how deep should the hierarchy be"
  - "what information do I need to gather before setting up territory management"
  - "our territory alignment criteria need to be documented before implementation"
tags:
  - territory-design
  - territory-alignment
  - coverage-model
  - sales-territories
  - assignment-rules
  - etm
  - requirements
inputs:
  - go-to-market motion (geographic, named account, industry overlay, or hybrid)
  - number of sales reps and managers requiring territory coverage
  - account segmentation criteria (geography, industry, revenue, employee count)
  - existing territory boundaries or coverage maps if redesigning
  - forecast rollup requirements (territory-based vs role-based)
  - org edition (Enterprise, Performance, or Unlimited — affects territory limits)
outputs:
  - territory design requirements document capturing alignment criteria and hierarchy shape
  - recommended coverage model type (geographic, named account, overlay, or hybrid)
  - assignment rule criteria list with field-level specifications
  - hierarchy depth and breadth recommendations
  - user-to-territory ratio analysis and recommendations
  - checklist of requirements to hand off to the ETM configuration skill
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Territory Design Requirements

This skill activates when a practitioner needs to gather, evaluate, or document the requirements for a Salesforce Enterprise Territory Management (ETM) territory design before configuration begins. It covers alignment criteria selection, coverage model type, assignment rule logic, geographic considerations, hierarchy depth and breadth, and user-to-territory ratio targets. Use this skill before invoking enterprise-territory-management for configuration.

---

## Before Starting

Gather this context before working on anything in this domain:

- **ETM is the target platform.** ETM is not Legacy Territory Management. The design must account for ETM-specific constraints: up to 1,000 territories per model (Enterprise Edition default), a single Active model at a time, and assignment rules limited to filter criteria on account fields (no formula-based criteria).
- **The most common wrong assumption is that territory hierarchy mirrors role hierarchy.** ETM hierarchy is entirely independent of the role hierarchy. Territory hierarchy drives account record access and forecast rollups; role hierarchy drives manager visibility in the standard pipeline. Conflating them leads to over-engineered structures.
- **Assignment rule performance degrades above 10 filter criteria per territory.** The platform supports up to 25 filter criteria per assignment rule set, but Salesforce recommends no more than 10 for optimal rule execution performance. Design criteria to be tight and non-overlapping.
- **Territory access is always additive.** ETM cannot restrict access below the org-wide default. Any design that relies on territories to limit access will fail — that belongs in OWD and sharing rules.

---

## Core Concepts

### Coverage Model Types

ETM supports four coverage model patterns, and most orgs use a combination:

**Geographic:** Territories defined by physical location criteria — BillingState, BillingCountry, postal code ranges, or custom region picklists. Best for field sales organizations with clear geographic accountability.

**Named Account:** Specific accounts assigned to specific reps regardless of location. Implemented via Account Name, Account ID, or a custom named-account flag field on the account record. Accounts are manually assigned or matched via exact-match rules.

**Industry Overlay:** Cross-functional coverage that grants additional visibility into accounts across other territories based on industry, product line, or segment criteria. Overlay territories stack on top of primary coverage — members gain additive Read or Read/Write access.

**Hybrid:** A combination of geographic primary coverage plus named account or overlay territories. Most enterprise orgs eventually operate hybrid models. Requires clear documentation of which territory type takes precedence for opportunity territory assignment (governed by territory type priority values).

### Hierarchy Design Principles

The territory hierarchy defines parent-child relationships that control two things: how forecast data rolls up and how the `TerritoryAndSubordinates` sharing group is built for record access propagation.

**Depth:** Salesforce documentation and best practices recommend keeping hierarchy depth to 3–5 levels. Hierarchies deeper than 6 levels increase forecast rollup complexity and make it difficult for managers to understand their coverage scope. Common depth patterns: Country → Region → Sub-Region → Individual Rep, or Segment → Area → Territory.

**Breadth:** Span of control per hierarchy level should reflect the actual management structure. A territory node with 50 direct-child territories is difficult to audit and indicates missing intermediate levels.

**Independence from role hierarchy:** Territory hierarchy serves account coverage and forecasting. Role hierarchy serves opportunity ownership visibility and standard pipeline reports. These two hierarchies should be designed separately against their respective business purposes, even if they share similar shape.

### Assignment Rule Design

Account assignment rules are filter-based criteria that execute against account field values to automatically assign accounts to territories. Key design requirements:

- **Supported field types:** Text, picklist, numeric (number, currency, percent), checkbox. Date fields are not supported as assignment rule criteria.
- **Criteria limit:** Up to 25 filter conditions per assignment rule set. Salesforce recommends 10 or fewer for performance.
- **Non-overlapping criteria:** If two territories have overlapping criteria, accounts matching both will be assigned to both. For primary coverage this is usually unintended — design criteria to be mutually exclusive at each hierarchy level.
- **Numeric field performance:** Numeric field criteria (Annual Revenue, Employee Count) perform better in rule execution than large text-based criteria lists. Where possible, prefer numeric segmentation for primary alignment.
- **Blanket coverage:** Every territory hierarchy should have a catchall territory or explicit rule to handle accounts that do not match any specific rule. Unassigned accounts will not appear in any territory member's forecast.

### User-to-Territory Ratio

The user-to-territory ratio is the primary scalability metric for territory design. From Salesforce best practices:

- **Target ratio: approximately 3:1** — three territories per active user. This ratio balances adequate coverage segmentation with administrative overhead.
- Ratios above 10:1 are a signal that the hierarchy has too many leaf-level territories relative to the team size, making future maintenance expensive.
- Ratios below 1:1 (more users than territories) often indicate that territories are too broad and that coverage accountability is unclear.
- Users can belong to multiple territories (useful for named account overlays), but count each user-territory association independently when calculating ratio.

---

## Common Patterns

### Geographic Primary Coverage Model

**When to use:** Sales organization has clear geographic accountability, field reps own a region, and account assignment can be reliably determined from BillingState or BillingCountry values.

**How it works:**
1. Define territory types: National → Regional → Sub-Regional (or similar).
2. Build hierarchy matching the management structure (e.g., Country → Region → State/Province → Rep territory).
3. Create mutually exclusive assignment rules at the leaf level: `BillingState = 'CA'` for California territory, `BillingState = 'OR'` for Oregon territory.
4. Parent territories do not need assignment rules — their access is derived from child territory membership via the `TerritoryAndSubordinates` group.
5. Define a catch-all territory at the top of each region for accounts not matching any leaf-level rule (useful for unclassified or international accounts).

**Why not a flat structure:** A single-level list of 50 territory nodes with no hierarchy makes forecast rollup and manager visibility impossible without custom reporting.

### Named Account Overlay Model

**When to use:** A subset of accounts is owned by strategic/enterprise reps regardless of their billing location. These reps need access to accounts that are also covered by geographic territories.

**How it works:**
1. Create a separate territory type with a distinct priority value lower (higher priority) than geo territories.
2. Create a territory node for each named account rep or named account book.
3. Assign accounts to named account territories using manual assignment or exact-match rules (e.g., `Account Name = 'Acme Corp'`, or a custom `IsNamedAccount__c = true` picklist/checkbox field).
4. Named account reps and geo reps both gain access to the shared accounts — access is additive.
5. Set named account territory type priority to ensure correct opportunity territory assignment when an opportunity's account belongs to both a named account and a geo territory.

**Why not a sharing rule:** Named account sharing via sharing rules requires ongoing manual maintenance and does not integrate with territory-based forecasting. Territory membership is the correct mechanism when territory forecasting is in scope.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Reps cover fixed geographic regions with no overlap | Geographic coverage model with mutually exclusive BillingState/Country rules | Simple to maintain; criteria are stable and easy to audit |
| Enterprise reps own accounts across multiple geographies | Named account territory type as an overlay on top of geographic primary coverage | Keeps named account lists separate; both coverage layers contribute to forecast |
| Industry specialists cover accounts across all regions | Overlay territory type per industry vertical | Access is additive; primary geo coverage and industry overlay coexist |
| Hierarchy deeper than 6 levels being proposed | Flatten to 4–5 levels and consolidate intermediate nodes | Deep hierarchies degrade forecast rollup readability and maintenance |
| More than 10 criteria conditions needed per territory | Refactor segmentation using a custom account field (e.g., TerritoryRegion__c picklist) | Reduces rule count; improves assignment performance; easier to maintain |
| Assignment criteria include date fields | Use a numeric or picklist proxy field instead (dates are not supported in ETM rules) | ETM assignment rules do not support date field criteria |
| Org has fewer than 50 accounts per territory | Check if territory count is too high relative to team size; aim for ~3:1 territory-to-user ratio | Over-segmentation increases admin overhead without improving coverage clarity |
| Named account list changes frequently (monthly or faster) | Prefer manual account-to-territory assignment over rule-based named account matching | Avoids frequent rule edits and manual rule reruns; reduces risk of misassignment |

---

## Recommended Workflow

Step-by-step instructions for gathering and documenting territory design requirements:

1. **Gather go-to-market context** — Interview sales leaders to understand the coverage motion: geographic, named account, industry overlay, or hybrid. Confirm whether territory-based forecasting is required (if yes, the hierarchy must match the forecast rollup structure).
2. **Inventory account segmentation criteria** — Identify which account fields will drive territory assignment (BillingState, BillingCountry, AnnualRevenue, Industry, a custom region field, etc.). Confirm the fields exist, are populated on account records, and are of a supported type (text, picklist, numeric, checkbox — not date).
3. **Draft the hierarchy model** — Sketch the hierarchy levels (e.g., Country → Region → Territory). Validate depth is 3–5 levels. Confirm each level maps to a real management or forecast rollup node. Do not mirror the role hierarchy — design the territory hierarchy for its own purpose.
4. **Define territory types and priority values** — Document each territory type (Geographic, Named Account, Overlay, etc.) and assign priority values. Lower integer = higher priority for opportunity territory assignment. Confirm priority ordering is intentional and documented.
5. **Specify assignment rule criteria per territory** — For each leaf-level territory, document the filter criteria (field, operator, value). Verify criteria are mutually exclusive for primary coverage territories. Flag any territory requiring more than 10 criteria for redesign.
6. **Calculate user-to-territory ratio** — Count expected active users and proposed territory count. Target approximately 3:1. Flag any ratio above 10:1 or below 1:1 for review with sales leadership.
7. **Produce the requirements handoff document** — Compile all outputs into a structured design requirements document. Hand off to the enterprise-territory-management skill for implementation.

---

## Review Checklist

Run through these before marking requirements complete:

- [ ] Go-to-market coverage motion is confirmed (geographic, named account, overlay, or hybrid)
- [ ] All account fields used as assignment rule criteria are identified, exist in the org, and are of a supported type (not date fields)
- [ ] Hierarchy depth is 3–5 levels and each level maps to a real management or forecast rollup node
- [ ] Territory hierarchy is documented independently of the role hierarchy
- [ ] All territory types are named and priority values are assigned and ordered intentionally
- [ ] Assignment rule criteria are documented per leaf-level territory and are mutually exclusive for primary coverage
- [ ] No territory has more than 10 filter criteria; territories approaching that limit are flagged for redesign
- [ ] A catch-all territory or explicit unassigned-account handling strategy is defined
- [ ] User-to-territory ratio is calculated and is approximately 3:1 (flagged if outside acceptable range)
- [ ] If territory-based forecasting is required, hierarchy shape matches the desired forecast rollup structure
- [ ] Requirements handoff document is complete and ready for enterprise-territory-management skill

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Date fields are not supported as assignment rule criteria** — A common design request is "assign accounts to territories based on contract renewal date or onboarding date." ETM assignment rules only support text, picklist, numeric, and checkbox fields. Attempting to configure a date field as rule criteria will fail at setup. Design workaround: use a custom picklist or numeric proxy field (e.g., `RenewalQuarter__c`).

2. **Assignment rules do not handle overlapping criteria gracefully** — If two territories have assignment rules that can match the same account (e.g., Territory A: BillingState = 'CA', Territory B: AnnualRevenue > 1000000), accounts matching both criteria are assigned to both territories. For primary coverage this causes dual ownership. Requirements must specify that primary coverage criteria are mutually exclusive.

3. **Territory hierarchy is independent of role hierarchy — conflating them breaks both** — Designing the territory hierarchy to exactly mirror the role hierarchy is a common mistake. The two hierarchies serve different purposes and will diverge as the org scales. Changes to territory structure (e.g., splitting a region) should not require role hierarchy changes, and vice versa.

4. **The 1,000-territory-per-model limit is a default ceiling, not a hard limit** — Enterprise Edition orgs are capped at 1,000 territories per model by default. Orgs planning 800+ territories must proactively request a limit increase from Salesforce Support before go-live — this cannot be changed reactively in production. Requirements for large orgs must explicitly check this limit.

5. **Non-contiguous territories are supported but require explicit documentation** — ETM does not enforce geographic contiguity. A territory named "US West" can technically include accounts from any billing state. However, non-contiguous territories cause confusion for reps and introduce assignment rule complexity. Requirements should explicitly flag any non-contiguous coverage intent and document the rationale.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Territory design requirements document | Structured document capturing coverage model, hierarchy shape, criteria, ratio analysis, and open decisions |
| Assignment rule criteria list | Per-territory table of field, operator, and value criteria ready for configuration |
| Hierarchy diagram | Visual representation of territory levels, parent-child relationships, and territory types |
| User-to-territory ratio analysis | Count of users vs territories per hierarchy level with flagged anomalies |
| Territory type and priority table | Ordered list of territory types with priority values and business justification |

---

## Related Skills

- enterprise-territory-management — use after requirements are complete to configure ETM: build the territory model, create territories, configure assignment rules, assign users, and activate
- sharing-and-visibility — use for role hierarchy design, OWD configuration, and sharing rules; territory design requirements must account for the sharing model baseline
- requirements-gathering-for-sf — use for general Salesforce requirements gathering patterns when territory design is one workstream among several
- collaborative-forecasts — use when territory-based forecasting requirements need to be validated against the broader forecast configuration
