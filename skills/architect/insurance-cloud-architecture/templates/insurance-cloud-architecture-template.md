# Insurance Cloud Architecture — Work Template

Use this template when working on tasks in this area.

---

## Scope

**Skill:** `insurance-cloud-architecture`

**Request summary:** (fill in what the user asked for)

---

## Context Gathered

Answer each question before designing anything. These gates control what can be built.

**FSC license type confirmed:**
- [ ] Base FSC only (insurance objects NOT available without add-on)
- [ ] FSC + Industries Insurance Add-On provisioned

**Insurance modules licensed (check each):**
- [ ] Brokerage Management — provides InsurancePolicy, InsurancePolicyCoverage, InsurancePolicyAsset, InsurancePolicyParticipant, Producer
- [ ] Claims Management — provides Claim, ClaimParticipant, claims-processing ConnectAPI endpoints
- [ ] Policy Administration — provides InsuranceUnderwritingRule and Insurance Product Administration APIs
- [ ] Group Benefits — provides Group Plan, Group Member Plan, benefit enrollment objects

**Account model:**
- [ ] Person Accounts (FSC default) — InsurancePolicyParticipant.AccountId links to PersonAccount record
- [ ] Business Accounts — confirm InsurancePolicyParticipant.AccountId links to business Account

**External systems:**
- External policy admin system (Guidewire, Duck Creek, other): _______________
- External rating engine: _______________
- System of record for policy data (Salesforce vs external): _______________
- [ ] Salesforce is engagement layer only — bidirectional sync required
- [ ] Salesforce is full system of record

**Line of business:**
- [ ] P&C (auto, home, liability)
- [ ] Life insurance
- [ ] Group benefits / employee benefits
- [ ] Mixed lines — list: _______________

**Channel requirements:**
- [ ] Agent/broker portal
- [ ] Customer self-service portal
- [ ] Contact center
- [ ] Other: _______________

---

## Approach

**Data model pattern selected:**
- [ ] P&C: InsurancePolicy → InsurancePolicyCoverage (per coverage line) → InsurancePolicyAsset (vehicles/properties)
- [ ] Life: InsurancePolicy → InsurancePolicyCoverage (benefit amount) → InsurancePolicyParticipant (beneficiaries)
- [ ] Group Benefits: Group Plan → Group Member Plan → benefit enrollment objects
- [ ] Mixed/other: _______________

**Rationale:** (describe why this pattern fits the org's requirements)

**Underwriting approach:**
- [ ] InsuranceUnderwritingRule records + Insurance Product Administration API — for configurable eligibility logic
- [ ] External rating engine via Integration Procedure HTTP callout
- [ ] Both

**Pattern from SKILL.md being applied:**
- [ ] Module-First Architecture Gating — capability-to-module mapping before any object design
- [ ] Declarative Underwriting via Integration Procedures
- [ ] Other: _______________

---

## Insurance Module Capability Mapping

| Business Capability | Required Module | Licensed? | Notes |
|---|---|---|---|
| Policy quoting and binding | Brokerage Management | [ ] Yes [ ] No | |
| Claims FNOL and handling | Claims Management | [ ] Yes [ ] No | |
| Underwriting rule evaluation | Policy Administration | [ ] Yes [ ] No | |
| Group enrollment | Group Benefits | [ ] Yes [ ] No | |
| (add rows as needed) | | | |

---

## Data Model Design

**InsurancePolicy hierarchy:**

```
InsurancePolicy
  └── InsurancePolicyCoverage (coverage lines)
  └── InsurancePolicyParticipant (policyholder, beneficiary, named insured — links to Account)
  └── InsurancePolicyAsset (vehicles, properties)
  └── InsurancePolicyTransaction (endorsements, renewals, cancellations)
```

Custom objects needed (list any not covered by standard Insurance objects):

| Object Name | Purpose | Parent Lookup |
|---|---|---|
| | | |

---

## Integration Pattern Selection

| External System | Pattern | Rationale |
|---|---|---|
| Rating engine | Integration Procedure + HTTP DataRaptor callout | Async-safe; no governor limit risk |
| External policy admin (system of record) | Bulk API 2.0 sync or MuleSoft bidirectional | High volume; Salesforce as engagement layer |
| Claims adjudication | (select: real-time IP callout / batch sync / CDC) | |
| (add rows as needed) | | |

---

## Review Checklist

Work through these before marking the architecture complete:

- [ ] All referenced Insurance objects confirmed in a licensed module — no unlicensed object references
- [ ] InsurancePolicyParticipant relationships reference Account records, not Contact
- [ ] Underwriting logic uses InsuranceUnderwritingRule, not Flow decision tables
- [ ] External rating/API calls use Integration Procedures, not synchronous Apex callouts
- [ ] InsuranceUnderwritingRule records will be deployed with Active status (Draft/Inactive rules are silently skipped)
- [ ] Compliant Data Sharing configured for applicable Insurance objects
- [ ] Each Insurance module's ConnectAPI namespace documented for integration teams
- [ ] FSC Insurance NOT conflated with Health Cloud MemberPlan anywhere in design docs
- [ ] SOQL for InsurancePolicyParticipant queries AccountId, not ContactId

---

## Notes

(Record deviations from the standard pattern and justification)
