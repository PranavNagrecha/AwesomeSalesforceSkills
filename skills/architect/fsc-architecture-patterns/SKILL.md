---
name: fsc-architecture-patterns
description: "Use when designing or reviewing a Financial Services Cloud (FSC) solution architecture covering data model selection, Compliant Data Sharing design, integration strategy, and compliance framework alignment. Triggers: 'should I use the managed-package FSC data model or the platform-native model', 'how do I design Compliant Data Sharing for cross-team visibility in FSC', 'FSC integration architecture with core banking', 'which data model does FSC use for households and financial accounts'. NOT for individual FSC feature configuration (use admin/household-model-configuration or admin/financial-account-setup), NOT for person account mechanics outside FSC context (use data/person-accounts), NOT for generic sharing-rule design without FSC compliance requirements (use data/external-user-data-sharing)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Scalability
  - Reliability
  - Operational Excellence
triggers:
  - "should I use the managed-package FSC data model or the platform-native model"
  - "how do I design Compliant Data Sharing for cross-team visibility in FSC"
  - "FSC integration architecture with core banking or external financial systems"
  - "designing a sharing model for sensitive financial records in FSC"
  - "which FSC data model should I choose for a greenfield implementation"
  - "FSC compliance framework design for regulated financial services org"
  - "cross-team visibility of financial accounts without over-sharing in FSC"
tags:
  - fsc
  - financial-services-cloud
  - architecture
  - data-model
  - compliant-data-sharing
  - integration
  - compliance
  - person-accounts
  - sharing-model
inputs:
  - "Implementation type — greenfield, migration from managed-package FSC, or upgrade to platform-native FSC"
  - "Number of financial advisors / relationship managers and their team structure"
  - "Regulatory requirements (FINRA, SEC, GDPR, etc.) that govern data visibility"
  - "Integration landscape — core banking systems, market data feeds, document management, downstream reporting"
  - "Record volume projections for FinancialAccount, FinancialHolding, and related objects"
  - "Cross-team data-sharing requirements (who can see which client's accounts and why)"
  - "Existing Salesforce org topology — single org vs. multi-org, managed packages already installed"
outputs:
  - "FSC architecture decision record documenting data model selection with rationale"
  - "Compliant Data Sharing design document — share set configuration, activation steps, and compliance mapping"
  - "Integration boundary inventory — per-system direction, pattern, and data-ownership decisions"
  - "Sharing model design — OWD settings, CDS configuration, and role hierarchy alignment"
  - "Scalability assessment for FSC object volumes and sharing-rule overhead"
  - "Review checklist for FSC architecture go-live readiness"
dependencies:
  - admin/household-model-configuration
  - admin/financial-account-setup
  - architect/security-architecture-review
  - architect/well-architected-review
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-11
---

# FSC Architecture Patterns

Use this skill when designing, reviewing, or refactoring a Financial Services Cloud solution that spans multiple structural concerns — data model selection, Compliant Data Sharing configuration, integration with external financial systems, and regulatory compliance alignment. The focus is on foundational architectural decisions that have long-term consequences: the choice between managed-package FSC and the platform-native model made in Winter '23, and how Compliant Data Sharing differs from standard Salesforce sharing rules. These are the decisions that cannot be changed cheaply after go-live.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Managed-package vs. platform-native baseline** — Determine which data model the org is on. Managed-package orgs use the `FinServ__` namespace (e.g., `FinServ__FinancialAccount__c`). Platform-native orgs (Winter '23+) use standard FSC objects without a namespace (e.g., `FinancialAccount`). This distinction changes every API call, integration field mapping, and deployment artifact in the project.
- **Compliant Data Sharing activation state** — CDS must be explicitly enabled in FSC Settings. If it is not enabled, the org falls back to standard sharing rules, which do not have CDS's fine-grained financial-record sharing controls. Check before designing any sharing solution.
- **Regulatory data residency and visibility requirements** — Financial services orgs are frequently subject to FINRA, SEC, GDPR, or local banking regulations that restrict which users can see which client's financial data. Architecture decisions must be mapped against these requirements, not just against Salesforce platform defaults.

---

## Core Concepts

### Managed-Package vs. Platform-Native Data Model

FSC was originally delivered as a managed package with a `FinServ__` namespace. Starting with Winter '23, Salesforce began shipping a platform-native version of FSC where the financial services objects are standard Salesforce objects — no namespace, no package version dependency, and easier metadata deployment. This is the foundational architectural choice for any new FSC implementation.

**Managed-package FSC:** Objects like `FinServ__FinancialAccount__c`, `FinServ__FinancialHolding__c`, and `FinServ__Revenue__c` live under the `FinServ__` namespace. Package upgrades are controlled by Salesforce and must be explicitly applied. Custom fields, Flows, and Apex all reference the namespaced objects. This model is stable for orgs that implemented FSC before Winter '23 but introduces friction in CI/CD pipelines, integration field mapping, and metadata retrieval.

**Platform-native FSC:** Standard objects (`FinancialAccount`, `FinancialHolding`, `FinancialGoal`) behave like any other Salesforce standard object. No namespace. Full Metadata API control. No package upgrade dependencies. This is the recommended model for greenfield implementations started after Winter '23 and is the direction Salesforce continues to invest in.

The downstream consequences of this choice are significant: every API integration that reads or writes financial account data, every Apex class that references these objects, and every SOQL query will differ between the two models. Migrating from managed-package to platform-native after go-live requires a formal data migration project.

### Compliant Data Sharing

Compliant Data Sharing (CDS) is an FSC-specific framework that controls which users can see sensitive financial records — primarily `FinancialAccount` and related records — based on team membership and relationship data, rather than on standard Salesforce sharing rules.

Standard sharing rules operate at the record level based on ownership, role hierarchy, or criteria-based filters. CDS operates on a different model: it uses `AccountTeamMember`, `FinancialAccountRole`, and explicit share configuration objects to grant access to financial records only when a user has a documented relationship to a client. This aligns with financial services regulatory requirements that restrict data visibility to advisors who are formally assigned to a client.

Key CDS objects and mechanisms:
- **Account Share** and **FinancialAccount Share** are managed by the CDS engine, not manually.
- CDS must be activated in FSC Settings before it controls any sharing. Without activation, standard sharing rules remain in effect.
- CDS share sets can be configured to control visibility at the `FinancialAccount` level, not just the Account level.
- Over-sharing via broad CDS share configurations — for example, granting all members of a branch visibility to all client accounts at that branch — is a documented compliance risk that has appeared in FSC compliance audits.

### Integration Strategy for Financial Systems

FSC orgs integrate with core banking systems, market data feeds, document management platforms, and downstream regulatory reporting systems. These integrations have higher reliability and compliance demands than typical CRM integrations. Key architectural decisions:

- **System of record per data domain** — Core banking systems are typically the system of record for account balances, transaction history, and product holdings. FSC should display and contextualize this data, not own it. Architect a clear write-back boundary: what can a Salesforce user change in FSC that flows back to core banking, and under what approval process?
- **Real-time vs. batch** — Market data (portfolio valuations) updates on near-real-time schedules that standard Salesforce integrations cannot support via synchronous callouts. Design these as batch or event-driven feeds with a clear data-freshness SLA rather than trying to achieve live balance lookups.
- **Callout limits** — Synchronous Apex callouts are limited to 100 per transaction and 120-second timeout. FSC orgs that attempt real-time core banking lookups on record page loads routinely hit these limits, causing degraded advisor experience.

### Household and Client Data Model

The FSC client data model is built around the Person Account as the individual client record and either Household Accounts or Relationship Groups as the grouping construct. Person Accounts must be enabled at the org level before FSC can be deployed, and disabling them after FSC data exists would be destructive. The architect must confirm Person Account enablement is intentional and permanent.

Household rollups (total AUM per household, aggregate financial goals) rely on FSC's batch rollup engine. This engine is configurable but runs asynchronously; rollup fields on Household Accounts do not update in real time. Architects must communicate this to reporting teams who expect live household-level aggregates.

---

## Common Patterns

### Platform-Native First for Greenfield

**When to use:** Any new FSC implementation started after Winter '23 on a sandbox that does not have the legacy managed package installed.

**How it works:** Configure the org for platform-native FSC through FSC Settings. Do not install the `FinServ__` managed package. Build all Flows, Apex, LWC components, and integration configurations against the unnamespaced FSC standard objects. Use the FSC Data Model Gallery on architect.salesforce.com to identify the correct standard objects for each data entity.

**Why not the alternative:** Installing the managed package in a new org creates a version-upgrade dependency for the life of the implementation. Every sandbox refresh must align package versions. Every CI/CD pipeline must handle namespaced metadata retrieval. Platform-native eliminates this overhead and aligns with Salesforce's long-term FSC investment direction.

### Compliant Data Sharing with Minimum Necessary Access

**When to use:** Any FSC org where multiple teams (wealth management, retail banking, mortgage) share client records but must not see each other's financial account details without a documented relationship.

**How it works:** Enable CDS in FSC Settings. Configure share sets at the `FinancialAccount` level, not just the Account level. Assign `FinancialAccountRole` records to link advisors to specific financial accounts. Validate that the default OWD for `FinancialAccount` is Private or Read-Only before activating CDS — if OWD is Public Read/Write, CDS cannot enforce meaningful restrictions.

Define a per-team share set that grants access only to financial accounts where the user holds an active `FinancialAccountRole`. Audit the configuration to confirm no share set grants branch-level or team-level access that effectively exposes all client financial accounts to all branch employees.

**Why not the alternative:** Standard sharing rules do not have the granularity to enforce financial account-level visibility based on advisor relationships. Criteria-based sharing rules can approximate this but require custom logic to stay synchronized with `AccountTeamMember` changes, creating a maintenance burden and a compliance gap when assignments change.

### Event-Driven Core Banking Integration

**When to use:** When FSC must receive account balance updates, transaction feeds, or product holding changes from a core banking system on a sub-hourly basis.

**How it works:** Use Platform Events or Change Data Capture to consume banking events asynchronously. The core banking middleware (MuleSoft or external ETL) publishes events to a Salesforce Platform Event object. An Apex trigger or Flow subscribes to the event and updates the corresponding `FinancialAccount` or `FinancialHolding` record. This keeps the integration decoupled from user-facing transactions.

**Why not the alternative:** Synchronous callouts from page loads or record-save triggers to core banking systems couple the advisor's user experience to banking system availability and latency. Banking system downtime or slowness becomes a Salesforce outage for advisors.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New FSC implementation (post Winter '23) | Platform-native FSC | No namespace overhead, full metadata control, aligned with Salesforce roadmap |
| Migration from legacy managed-package FSC | Managed data migration to platform-native; plan for full data re-mapping | Cannot upgrade in place; requires schema and data migration project |
| Cross-team financial record visibility | Compliant Data Sharing with FinancialAccountRole | Standard sharing rules lack advisor-relationship granularity required for compliance |
| OWD for FinancialAccount in regulated org | Private OWD + CDS share sets | CDS requires Private OWD to be effective; Public OWD bypasses CDS restrictions |
| Real-time core banking balance lookups | Reject; design as batch feed with data-freshness SLA | Callout limits and banking system latency make real-time lookups architecturally unsound |
| Household aggregate KPIs (total AUM) | FSC batch rollup engine + scheduled reporting snapshots | Rollups are asynchronous; live queries against financial holdings at scale are too slow |
| Integration with document management | External Object + Salesforce Files + Named Credential | Keeps documents in their authoritative system while surfacing them in FSC context |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Determine data model baseline** — Confirm whether the org uses managed-package FSC (`FinServ__` namespace) or platform-native FSC (standard objects). Check `Setup > Installed Packages` for the Financial Services Cloud package. If present, identify the installed version. If absent on a new org, plan for platform-native. Document this decision before any design work proceeds.

2. **Audit Compliant Data Sharing state** — Navigate to `Setup > Financial Services > FSC Settings` and confirm whether CDS is enabled. Record the current OWD for `FinancialAccount`, `Account`, and `Contact`. If CDS is enabled but OWD is not Private, flag this as a compliance risk requiring remediation before proceeding with the sharing model design.

3. **Map regulatory data visibility requirements** — Work with the compliance team to document which user roles and teams are permitted to see which categories of financial records (investment accounts, banking accounts, insurance policies). Translate these requirements into CDS share-set configurations and `FinancialAccountRole` assignment rules.

4. **Design the integration boundary inventory** — For each external system (core banking, market data, document management, regulatory reporting), document: direction (inbound/outbound/bidirectional), pattern (real-time API/Platform Event/batch ETL), system of record, write-back permissions and approval requirements, error handling, and data-freshness SLA. Validate that no integration design requires synchronous callouts on record page loads.

5. **Validate household and rollup configuration** — Confirm that Person Accounts are enabled and that the Household object configuration (Household Account vs. Relationship Group) aligns with the org's client relationship model. Document the rollup batch schedule and the data-freshness characteristics of household-level KPIs.

6. **Assess scalability for FSC object volumes** — Estimate projected record counts for `FinancialAccount`, `FinancialHolding`, and `FinancialGoal`. Validate that SOQL queries supporting key pages (household wealth summary, advisor book of business) use indexed fields and stay within governor limits at projected scale. Flag any queries that traverse deep relationship chains without filtering by indexed fields.

7. **Produce architecture deliverables and review against Well-Architected pillars** — Generate the architecture decision record (data model choice, CDS design, integration patterns), the sharing model design document, and the integration boundary inventory. Walk each deliverable through the Security (does CDS enforce minimum necessary access?), Reliability (what happens when core banking is unavailable?), Scalability (can the sharing model handle 10x advisor growth?), and Operational Excellence (can compliance teams audit sharing changes without developer help?) pillars.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Data model confirmed as managed-package or platform-native; choice is documented with rationale
- [ ] Compliant Data Sharing is enabled if the org has cross-team financial record visibility requirements
- [ ] OWD for `FinancialAccount` is Private or Read-Only where CDS is in use
- [ ] No CDS share set grants branch-wide or team-wide access that bypasses advisor-relationship filtering
- [ ] Integration designs do not require synchronous callouts from record save or page load events
- [ ] System of record is defined per data domain; FSC write-back to core banking is gated by approval
- [ ] Household rollup batch schedule is documented; reporting teams understand data-freshness characteristics
- [ ] Person Accounts are enabled and confirmed as permanent (disabling after FSC data exists is destructive)
- [ ] Architecture decision record documents the managed-package vs. platform-native choice and the CDS design

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **CDS requires Private OWD to be meaningful** — If the default OWD for `FinancialAccount` is set to Public Read/Write before CDS is activated, CDS share sets have no effect on restricting access. Users already have implicit access through OWD. Architects who enable CDS without first setting OWD to Private produce a system where CDS appears configured but enforces no restrictions.

2. **Managed-package objects cannot be promoted to standard objects in place** — There is no Salesforce-supported upgrade path that converts `FinServ__FinancialAccount__c` records and metadata to the platform-native `FinancialAccount` standard object. Migration requires a full ETL extract, schema remapping, and re-import. Projects that defer this decision until late in the implementation pay a disproportionate migration cost.

3. **FSC rollup batch is asynchronous and has its own scheduling** — Household-level rollup fields (Total AUM, aggregated goal progress) are populated by a background batch process, not by real-time triggers. If the batch is not scheduled, rollup fields never update. If the batch fails silently, rollup fields show stale data without any platform-visible error. Architects must include rollup batch monitoring in the operational runbook.

4. **CDS does not apply to Community (Experience Cloud) users by default** — CDS controls internal user visibility. When external users access financial account records through an Experience Cloud portal, the sharing model falls back to sharing sets and org-level OWD for external users. An FSC org with CDS properly configured for advisors may inadvertently expose financial account data to portal users if external-user OWD is not separately reviewed.

5. **Platform-native FSC and managed-package FSC cannot coexist in the same org** — Installing the `FinServ__` managed package in an org that has already been configured for platform-native FSC, or vice versa, creates object naming conflicts and is not supported. Sandbox org topology must be managed carefully to prevent accidental package installation that pollutes a platform-native implementation.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| FSC Architecture Decision Record | Documents data model choice (managed vs. platform-native), CDS design, integration patterns, and compliance mapping with rationale |
| Sharing Model Design | OWD settings, CDS share-set configuration, FinancialAccountRole assignment rules, and compliance requirement traceability |
| Integration Boundary Inventory | Per-system table with direction, pattern, system of record, write-back permissions, error strategy, and data-freshness SLA |
| Scalability Assessment | Projected record volumes for FSC objects, SOQL query profiles, rollup batch estimates, and governor limit headroom |
| Rollup Batch Operational Runbook | Schedule configuration, monitoring approach, failure alerting, and re-run procedure for the FSC rollup batch |

---

## Related Skills

- `admin/household-model-configuration` — configure the FSC household data model, Primary Group assignment, and household rollup batch settings after architecture decisions are made
- `admin/financial-account-setup` — configure individual FinancialAccount record types, ownership types, and page layouts after the data model is selected
- `architect/security-architecture-review` — use for a PCI/financial security posture review that encompasses Shield, Platform Encryption, and audit trail requirements
- `architect/well-architected-review` — use for a formal Well-Architected review across all pillars after the FSC architecture is drafted
- `data/person-accounts` — reference for person account mechanics when the FSC data model discussion surfaces person account configuration questions
