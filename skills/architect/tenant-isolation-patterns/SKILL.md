---
name: tenant-isolation-patterns
description: "Multi-tenant isolation patterns on Salesforce: custom metadata per-tenant, permission-based feature gating, data partitioning, namespace isolation, ISV managed-package patterns. NOT for multi-org strategy (use multi-org-architecture). NOT for data sharing design (use sharing-selection decision tree)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Scalability
  - Reliability
tags:
  - multi-tenant
  - isv
  - managed-packages
  - feature-gating
  - data-partitioning
  - namespace
  - tenant-isolation
triggers:
  - "how do i isolate tenants within a single salesforce org"
  - "multi tenant isv pattern managed package"
  - "feature gating per customer with custom metadata"
  - "data partitioning in a multi brand salesforce org"
  - "namespace separation in managed packages"
  - "tenant aware sharing and security"
inputs:
  - Tenant model (multi-brand single org, ISV managed package, multi-franchise)
  - Expected number of tenants and growth curve
  - Data isolation requirements (regulatory, contractual, business)
  - Tenant-specific customization requirements (fields, UI, automation)
outputs:
  - Tenant identification strategy (field on records, account hierarchy, or namespace)
  - Sharing and security model ensuring isolation
  - Feature-gating mechanism (custom metadata, permission sets)
  - Customization strategy (configuration-driven, not code-branched)
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-21
---

# Tenant Isolation Patterns

Activate when designing how multiple logical tenants coexist in one Salesforce environment: ISV managed package with customer orgs, multi-brand single org, franchise network, or multi-agency public sector deployment. Tenant isolation is an architect-level decision that touches sharing, packaging, customization, and integration.

## Before Starting

- **Distinguish logical tenants from separate orgs.** If each tenant needs its own release cadence, compliance boundary, or governance model, use separate orgs and federate. If tenants share the same release train and just need data/config partitioning, multi-tenant within one org is viable.
- **Know the regulatory posture.** HIPAA, FedRAMP, GDPR data-residency requirements may make single-org multi-tenant legally infeasible.
- **Audit the customization ask.** Tenant-specific fields are hard in one org; tenant-specific record types and page layouts are easier; tenant-specific Apex is a smell.

## Core Concepts

### Tenant identifier on the record

Most common pattern: a `Tenant__c` lookup or picklist on every tenant-scoped object. Every query filters by tenant; every sharing rule gates by tenant. Simple, auditable, but dependent on discipline.

### Account hierarchy as tenant

For B2B2C or franchise patterns, the tenant is an `Account` with a specific record type (e.g., "Franchisee"). Users roll up through the role hierarchy under that Account. Sharing falls out naturally from the role hierarchy.

### ISV managed package isolation

In a managed-package ISV scenario, the customer's org IS the tenant boundary. Isolation is by org. Your concern is packaging, upgrades, and not leaking customer data through shared infrastructure.

### Permission-based feature gating

Custom metadata or custom permissions define which features a tenant sees. Feature flags are queried at runtime; page layouts and UI conditionally render.

## Common Patterns

### Pattern: Single org, Tenant__c field, criteria-based sharing

Add `Tenant__c` to every tenant-scoped object. OWD is Private. Criteria-based sharing rules per tenant grant access to members of the tenant's permission set group. Reports filter by current user's Tenant ID.

### Pattern: Franchise model via Account hierarchy

Each franchise is an `Account` with record type "Franchisee" plus a role for its users. OWDs private; role hierarchy handles franchise-to-franchise isolation. Regional managers span franchises via overlay role.

### Pattern: ISV package with feature flags

Managed package ships with a Custom Metadata Type `Feature_Flag__mdt`. Each customer toggles flags without code changes. Apex checks flags via a central `FeatureService.isEnabled('X')` call.

### Pattern: Multi-brand single org

Brand = Tenant. Each record stamped with brand. Users have a `BrandId` on User. Sharing rules gate by brand. Integrations receive brand-scoped tokens.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| ISV B2B SaaS | Managed package, org-per-customer | Native isolation |
| Franchise / partner network | Single org, Account hierarchy | Easy rollup |
| Multi-brand agency | Single org, Tenant__c field, CBS | Tight ops, shared data model |
| Regulatory-bound tenants | Separate orgs, federated | Compliance |
| Per-tenant custom code | Reconsider — managed package + feature flags, not per-tenant Apex | Maintenance hell |

## Recommended Workflow

1. Classify the tenant model: single-org logical, ISV managed package, or multi-org federated.
2. Write the isolation requirements: data, config, compliance, release cadence, integration.
3. Choose the tenant identifier strategy (field, account, namespace).
4. Design sharing: OWD, role hierarchy, criteria-based sharing, permission set groups.
5. Design feature gating: custom metadata, custom permissions, permission sets.
6. Build a tenant-onboarding runbook: records to create, permissions to grant, flags to set.
7. Test isolation with two-tenant data set; verify no cross-tenant visibility in reports, queries, dashboards.

## Review Checklist

- [ ] Tenant model explicitly documented
- [ ] Tenant identifier chosen and consistently applied
- [ ] Sharing model validated with a two-tenant smoke test
- [ ] Feature flags in custom metadata or permissions, not Apex
- [ ] Onboarding runbook tested end-to-end
- [ ] Offboarding runbook (data export, access revocation) exists
- [ ] Cross-tenant reporting requirements addressed (aggregated view for owners)

## Salesforce-Specific Gotchas

1. **Role hierarchy bypasses sharing rules.** A tenant admin role placed above another tenant's role grants visibility — model the hierarchy carefully.
2. **Report folders do not have row-level filters.** A tenant user seeing a shared report folder may see records from the report's query regardless of sharing — use CRM Analytics with security predicates for sensitive reporting.
3. **Flow runs as the current user but can escalate.** `System Context` flows bypass sharing and FLS; auditing flow run mode is a tenant-isolation imperative.

## Output Artifacts

| Artifact | Description |
|---|---|
| Tenant model decision record | Single-org logical / ISV / federated with rationale |
| Sharing architecture diagram | OWD, role hierarchy, CBS, PSG mappings |
| Feature flag catalog | Custom metadata types and default values |
| Onboarding + offboarding runbooks | Step-by-step tenant lifecycle |

## Related Skills

- `architect/multi-org-architecture` — sibling for federated model
- `security/sharing-architecture` — sharing detail
- `devops/managed-package-publishing` — ISV patterns
- `standards/decision-trees/sharing-selection.md` — when to use which sharing
