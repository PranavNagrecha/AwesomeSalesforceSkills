---
name: insurance-cloud-architecture
description: "Architecture guidance for Salesforce Insurance Cloud on FSC: module licensing strategy, policy administration object model, claims processing workflow design, underwriting rule integration, and channel routing. NOT for Health Cloud payer architecture, FSC retail banking, or implementation-level OmniScript development."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Performance
triggers:
  - "how do I architect insurance policy administration on Salesforce FSC"
  - "what modules do I need to license for FSC Insurance claims and underwriting"
  - "designing a P&C or life insurance workflow on Financial Services Cloud"
  - "InsurancePolicy object model and data architecture for insurance on Salesforce"
  - "which FSC Insurance ConnectAPI namespaces are needed for brokerage vs claims vs policy admin"
tags:
  - insurance-cloud
  - fsc
  - financial-services-cloud
  - architecture
  - underwriting
  - claims
  - policy-administration
inputs:
  - "List of required insurance capabilities (brokerage, claims, policy admin, group benefits)"
  - "Org FSC license type (base FSC vs Industries Insurance add-on)"
  - "Integration requirements for external policy administration or rating engines"
  - "Channel requirements (agent portal, customer portal, contact center)"
outputs:
  - "Insurance module licensing decision matrix"
  - "Insurance data model architecture diagram (objects and relationships)"
  - "Claims and underwriting workflow design"
  - "ConnectAPI namespace mapping by module"
dependencies:
  - fsc-architecture-patterns
  - industries-insurance-setup
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# Insurance Cloud Architecture

This skill activates when an architect or senior practitioner needs to design or review a Salesforce Insurance Cloud solution on FSC — covering module licensing strategy, policy data model decisions, claims and underwriting workflow architecture, and integration patterns with external rating or policy administration systems. It does NOT cover Health Cloud payer (MemberPlan model), generic FSC retail banking, or OmniScript implementation work.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm which Insurance Cloud modules are licensed: Brokerage Management, Claims Management, Policy Administration, and Group Benefits are separately licensed add-ons on top of base FSC. Activating one does NOT activate others — license-to-feature mapping is the critical architectural gate.
- Determine whether the org uses Person Accounts (the FSC default) or Business Accounts — this drives InsurancePolicyParticipant relationship modeling.
- Identify external systems: does an external policy admin system (Guidewire, Duck Creek) own the record of truth, or does Salesforce?
- The most common wrong assumption: FSC Insurance and Health Cloud payer features share objects. They do not — InsurancePolicy (Insurance Cloud) and MemberPlan (Health Cloud) are different licensed products with entirely different object models.

---

## Core Concepts

### Insurance Cloud Module Licensing Gates

Insurance Cloud on FSC is composed of four separately licensed modules: **Brokerage Management**, **Claims Management**, **Policy Administration**, and **Group Benefits**. Each module surfaces a distinct set of standard objects and ConnectAPI namespaces. Activating one module does not unlock another. Before any data model or workflow design can begin, the architect must map each required business capability to a specific licensed module.

Key licensing facts:
- Base FSC license alone does NOT include insurance objects — the **FSC Insurance permission set license (Industries Insurance Add-On)** must be provisioned separately.
- Brokerage Management provides InsurancePolicy, InsurancePolicyCoverage, InsurancePolicyAsset, and the Producer object.
- Claims Management adds Claim and ClaimParticipant objects plus claim-processing ConnectAPI endpoints.
- Policy Administration adds InsuranceUnderwritingRule and Insurance Product Administration APIs.
- Group Benefits adds Group Plan, Group Member Plan, and benefit enrollment objects.

Failure to confirm licensing before design leads to architecture documents that reference inaccessible objects on go-live day.

### Insurance Object Model

The Insurance Cloud data model is additive on top of core Account/Contact:

- **InsurancePolicy** — the central object, linked to a policyholder Account (not Contact directly).
- **InsurancePolicyCoverage** — child of InsurancePolicy, representing individual coverage lines (auto, home, liability).
- **InsurancePolicyParticipant** — junction object linking InsurancePolicy to Account records as policyholder, beneficiary, or named insured. This links to Account — NOT Contact. Architects designing for FSC Person Account orgs must remember that the Person Account IS an Account record; SOQL must reflect this.
- **InsurancePolicyAsset** — insured assets (vehicles, properties) linked to InsurancePolicy.
- **InsurancePolicyTransaction** — endorsements, renewals, cancellations as transactional records on a policy.

### Underwriting Rules and the Policy Administration API

Underwriting rules are managed via the **InsuranceUnderwritingRule** object with Active/Inactive/Draft lifecycle statuses. Critically, underwriting decision logic belongs in InsuranceUnderwritingRule records and Insurance Product Administration APIs — NOT in native Flow decision elements. Flow can orchestrate process steps (collect applicant data, call an IP, present decisions), but the underwriting logic itself must live in the platform's underwriting framework to remain auditable and maintainable.

The Insurance Product Administration APIs (Connect REST) support rating, quoting, and policy issuance. External rating engines integrate via Integration Procedures calling out to the rating API — the pattern is declarative callout from OmniStudio, not synchronous Apex callout on record save.

---

## Common Patterns

### Module-First Architecture Gating

**When to use:** Every Insurance Cloud architecture engagement before any object or workflow design begins.

**How it works:**
1. Map each business capability requirement (quote, bind, claim FNOL, group enrollment) to the specific module that delivers it.
2. Confirm each module is licensed by inspecting Setup > Company Information > Permission Set Licenses.
3. Only design workflows and data models for licensed modules. Document unlicensed modules as future-phase scope gates.
4. Map ConnectAPI namespaces per module so integration teams know which APIs are accessible at launch.

**Why not the alternative:** Designing a comprehensive insurance platform architecture first and resolving licensing last causes late-project scope cuts and rearchitecture when modules turn out to be unlicensed.

### Declarative Underwriting via Integration Procedures

**When to use:** When underwriting rules must be configurable by business analysts without developer involvement, or when rating calls must be made to external engines.

**How it works:**
1. Build an OmniScript collecting applicant and asset data.
2. Invoke an Integration Procedure that calls the Insurance Product Administration APIs (or an external rating endpoint via DataRaptor HTTP action).
3. Return the rated quote or underwriting decision to the OmniScript for agent review and policy issuance.
4. Use InsuranceUnderwritingRule records to configure eligibility criteria declaratively.

**Why not synchronous Apex:** Apex callouts on record-save triggers violate the 100-callout-per-transaction limit and cannot be used in before/after triggers. Declarative IP calls are async-safe and governor-limit-aware.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Org needs quotes, policies, and renewals | Brokerage Management + Policy Administration modules | Brokerage provides the core policy object model; Policy Admin provides the underwriting and issuance APIs |
| Claims intake and claims processing workflows | Claims Management module required | Claim and ClaimParticipant objects only available in this module |
| Group employee benefits enrollment | Group Benefits module | Group Plan/Member Plan objects are module-specific |
| External policy admin system is system of record | Salesforce as engagement layer; bidirectional sync via Bulk API or MuleSoft | Avoid duplicating policy admin logic in both systems |
| Underwriting decision logic | InsuranceUnderwritingRule + Insurance Product Administration API | Flow decision tables cannot enforce underwriting audit trail requirements |
| Rating against external engine | Integration Procedure + HTTP DataRaptor callout | Declarative, governor-safe, maintainable without Apex |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **License audit** — Confirm which Insurance Cloud modules are provisioned. Check Setup > Company Information > Permission Set Licenses. Refuse to design object models for unlicensed modules without a licensing procurement confirmation.
2. **Capability-to-module mapping** — Map every business requirement to its module. Identify gaps where required capabilities require unlicensed modules; document these as licensing decisions, not technical ones.
3. **Data model design** — Design the InsurancePolicy hierarchy: policyholder Account, InsurancePolicyCoverage lines, InsurancePolicyParticipant roles, InsurancePolicyAsset records, and InsurancePolicyTransaction history.
4. **Workflow architecture** — Map each business process (quoting, binding, FNOL, claims handling, renewals) to the appropriate orchestration layer: OmniScript for guided UI, Integration Procedures for data transformation and external callouts, InsuranceUnderwritingRule for eligibility logic.
5. **Integration pattern selection** — For each external system (rating engine, policy admin, claims adjudication), select the integration pattern: real-time IP callout, batch Bulk API sync, or event-driven Change Data Capture.
6. **Sharing and security design** — Configure Compliant Data Sharing for sensitive policy data. Define record access for agents vs adjusters vs underwriters using FSC sharing frameworks, not ad hoc sharing rules.
7. **Review** — Validate all object relationships respect InsurancePolicyParticipant → Account (not Contact). Confirm no underwriting logic is in Flow decision tables. Confirm all async callouts use Integration Procedures.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All referenced Insurance objects belong to a confirmed licensed module
- [ ] InsurancePolicyParticipant relationships reference Account records, not Contact
- [ ] Underwriting logic uses InsuranceUnderwritingRule, not Flow decision tables
- [ ] External rating/API calls use Integration Procedures, not synchronous Apex callouts
- [ ] Compliant Data Sharing is configured for applicable Insurance objects
- [ ] Each Insurance module's ConnectAPI namespace is documented for integration teams
- [ ] FSC Insurance is not conflated with Health Cloud MemberPlan anywhere in design docs

---

## Salesforce-Specific Gotchas

1. **Module activation is not automatic** — Purchasing the FSC Insurance Add-On does not activate all modules. Each module (Brokerage, Claims, Policy Admin, Group Benefits) requires explicit provisioning in Setup. Organizations regularly discover on go-live day that expected objects are unavailable because a specific module was not activated.
2. **InsurancePolicyParticipant links to Account, not Contact** — Architects designing participant roles (policyholder, beneficiary, named insured) consistently model this as a Contact relationship from Force.com habit. The object uses AccountId as the participant lookup, which works naturally with FSC Person Accounts but breaks SOQL written for standard Contact queries.
3. **Underwriting rules have an Active/Inactive/Draft lifecycle** — Newly created InsuranceUnderwritingRule records default to Draft status. Rules in Draft or Inactive status are not evaluated by the Insurance Product Administration APIs. Deployments that create underwriting rules without explicitly activating them silently produce no underwriting decisions.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Module licensing decision matrix | Maps each business capability to its required Insurance Cloud module and confirms license availability |
| Insurance data model diagram | Object relationship diagram covering InsurancePolicy hierarchy, participant roles, and transaction history |
| Workflow architecture document | Process flows for quoting, binding, FNOL, claims handling mapped to OmniStudio + Integration Procedure layers |

---

## Related Skills

- `fsc-architecture-patterns` — For broad FSC data model, sharing model, and integration strategy outside insurance-specific objects
- `industries-insurance-setup` — For implementation-level setup of insurance objects, permission sets, and OmniScript configuration
- `industries-data-model` — For cross-industry object model reference including the full insurance object set in context
