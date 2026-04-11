# FSC Client Onboarding Design — Work Template

Use this template when designing the FSC client onboarding process. Fill in each section before producing any process map, task inventory, or technology recommendation.

---

## Scope

**Skill:** `client-onboarding-design`

**Request summary:** (Describe what the stakeholder asked for — e.g., "Design the client onboarding process for wealth management new account opening, including document collection, compliance review, and welcome email.")

---

## Baseline Checks

Before starting:

- [ ] **OmniStudio license confirmed?** Yes / No / Pending
  - If Yes: OmniScript is available for guided intake
  - If No: Screen Flow is the intake tool
  - Source of confirmation: (e.g., Setup > Installed Packages, AE confirmation)

- [ ] **FSC Action Plans feature enabled?** Yes / No / Pending

- [ ] **Anchor object identified:** (FinancialAccount / Account / InsurancePolicy / Opportunity / Other: _______)

- [ ] **Compliance requirements documented?** Yes / No / Pending
  - Regulatory basis: (e.g., KYC under FINRA Rule 4512, beneficial ownership under FinCEN CDD Rule)

---

## Stakeholder Requirements

| Stakeholder | Team | Onboarding Touchpoints They Own | SLA Expectations |
|---|---|---|---|
| | Advisor / RM | | |
| | Compliance | | |
| | Operations | | |
| | IT / Integration | | |

---

## Process Stage Map

Define each phase of the onboarding journey. Add or remove stages as needed.

### Stage 1: Pre-Onboarding

**Purpose:** (e.g., identity verification, KYC/AML clearance)

| Task | Owner Role/Queue | DaysFromStart | Required? | Document Type |
|---|---|---|---|---|
| | | | Yes / No | |

**Gate condition:** (What must be complete before Stage 2 begins?)

**Escalation path:** (What happens if the gate is not cleared within SLA?)

---

### Stage 2: Document Collection

**Purpose:** (e.g., collect signed agreements, disclosures, supporting documents)

| Task | Owner Role/Queue | DaysFromStart | Required? | Document Type |
|---|---|---|---|---|
| | | | Yes / No | |

**Gate condition:**

**Escalation path:**

---

### Stage 3: Compliance Review

**Purpose:** (e.g., compliance officer review and sign-off)

| Task | Owner Role/Queue | DaysFromStart | Required? | Document Type |
|---|---|---|---|---|
| | | | Yes / No | |

**Gate condition:**

**Escalation path:**

---

### Stage 4: Account Activation

**Purpose:** (e.g., fund account, send funding instructions, activate record)

| Task | Owner Role/Queue | DaysFromStart | Required? | Document Type |
|---|---|---|---|---|
| | | | Yes / No | |

---

### Stage 5: Welcome Journey Handoff

**Trigger field and value:** (e.g., FinancialAccount.Status = "Active")

**Channel:** (Email / SMS / Marketing Cloud Journey / Portal Notification)

**Timing:** (Immediate / N days after trigger: _____)

**Data payload required by downstream system:**

| Field | API Name | Source Object |
|---|---|---|
| Client first name | Contact.FirstName | Contact |
| Account number | FinancialAccount.AccountNumber | FinancialAccount |
| Advisor name | User.Name | User (FinancialAccount.OwnerId) |
| Advisor email | User.Email | User (FinancialAccount.OwnerId) |

**Fallback behavior if downstream unavailable:**

---

## Technology Selection

**Guided intake tool:**
- [ ] OmniScript (OmniStudio licensed — confirmed above)
- [ ] Screen Flow (OmniStudio not licensed)

**Rationale:** (one sentence documenting the license basis)

**Task execution tool:** Action Plan templates (standard FSC approach)

**Welcome journey tool:** (Flow-triggered email / Marketing Cloud Journey / Other: _______)

---

## Action Plan Task Inventory Summary

Total task count across all stages: _____

- [ ] Total is under 75 (hard platform limit). If over 75, split into phased templates — see gotchas.md.

**Template naming:**
- Template 1 name: (e.g., "Client Onboarding v1")
- Template 2 name (if split): (e.g., "Client Onboarding Phase 2 v1")

---

## Template Versioning Governance

**Template owner (role):**

**Change request protocol:** (Who initiates, who approves, minimum lead time)

**Naming convention:** (e.g., "[Use Case] v[N]")

**In-flight plan policy:** (e.g., "Clients in onboarding when v2 is published complete on v1. New onboardings started after v2 publish date use v2.")

**Review trigger:** (e.g., annually, on regulatory change, after audit finding)

---

## Deliverables Checklist

- [ ] Process stage map with gates, owners, SLAs, and escalation paths
- [ ] Action Plan task inventory (all stages, all fields)
- [ ] Technology selection rationale with license basis
- [ ] Welcome journey handoff specification with trigger and payload
- [ ] Template versioning governance document
- [ ] In-flight plan policy documented

---

## Notes and Deviations

(Record any deviations from the standard pattern and the business reason why.)
