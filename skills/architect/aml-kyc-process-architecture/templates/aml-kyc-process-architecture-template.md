# AML/KYC Process Architecture — Work Template

Use this template when working on an AML/KYC process architecture design for a Salesforce FSC org.

## Scope

**Skill:** `aml-kyc-process-architecture`

**Request summary:** (fill in what the practitioner or stakeholder asked for)

---

## Context Gathered

Answer these questions before designing anything:

- **FSC license type:** (FSC standard / FSC Plus / CRM Analytics licensed?)
- **OmniStudio licensed?** Yes / No
- **Screening vendor(s) in scope:** (Refinitiv World-Check / LexisNexis / Accuity / Other)
- **Vendor integration type:** (REST API / Managed Package / Batch File / Async Callback)
- **Vendor API SLA / typical response time:** (e.g., p95 < 3s)
- **Onboarding volume (new customers per day):**
- **Portfolio re-screening volume (records per annual cycle):**
- **Regulatory jurisdiction:** (BSA/FinCEN / EU AMLD / FATF-aligned / Other)
- **Customer risk tiers defined?** (Low / Medium / High / Prohibited — confirm picklist values)
- **Audit trail retention requirement:** (1 year / 5 years / 7 years — confirm with compliance)
- **Shield Field Audit Trail licensed?** Yes / No / Needs assessment

---

## Architecture Decisions

### Orchestration Pattern

| Decision | Selected Option | Rationale |
|---|---|---|
| New-customer onboarding screening | OmniStudio IP / Apex Callout / Flow + Async | (fill in) |
| Periodic re-screening | Batch Apex + Platform Events / Scheduled Flow | (fill in) |
| Change-triggered re-screening | Record-Triggered Flow → Platform Event → Apex | (fill in) |

### Risk Scoring Approach

| Decision | Selected Option | Rationale |
|---|---|---|
| Risk scoring engine | Rule-based Apex / CRM Analytics model | (fill in) |
| Scoring inputs | (list: screening result, geography, customer type, product type) | |
| Risk tier definitions | Low: / Medium: / High: / Prohibited: | (fill in criteria for each) |

### Vendor Integration Details

- **Named Credential name:** `_______________`
- **Authentication method:** (Named Principal OAuth / API Key header / Certificate)
- **Request format:** (JSON / XML)
- **Response mapping:** (DataRaptor Transform / Apex deserialization / DataWeave)
- **Retry strategy:** (max retries / backoff interval / dead-letter handling)
- **Timeout handling:** (block onboarding / mark as pending-review / allow with flag)

---

## Data Model

### PartyProfileRisk Field Usage

| Field | Source | Values |
|---|---|---|
| `RiskCategory` | Apex scoring class | Low / Medium / High / Prohibited |
| `RiskScore` | Vendor response or Apex formula | Numeric (0–100) |
| `RiskReason` | Apex / Integration Procedure | Free text — screening outcome summary |
| `RiskReviewDate` | Set at screening time | TODAY() + [review interval in days] |
| `ScreeningCaseRef__c` (custom) | Vendor response | Vendor case reference ID |
| `LastScreeningTimestamp__c` (custom) | Orchestration layer | Datetime of most recent screening call |

### Audit Trail Objects

| Object | Purpose | Retention |
|---|---|---|
| `PartyProfileRisk` (standard) | Current risk state | Platform field history: 18 months |
| `AMLAuditLog__c` (custom) | Point-in-time history of every screening and risk change | (specify: 5 / 7 years) |
| `ComplianceOverride__c` (custom) | Record of every manual risk rating override | (specify) |

---

## Compliance Review Routing

| Screening Outcome | Salesforce Action | Queue / Owner | SLA |
|---|---|---|---|
| Clear | Auto-advance onboarding; set RiskCategory | — | Immediate |
| Potential Match | Open Case; assign to Compliance Queue; block account activation | Compliance Review Queue | (e.g., 4 business hours) |
| Confirmed Match | Block onboarding; open High-Priority Case; notify Compliance Officer | Compliance Escalation Queue | (e.g., 1 business hour) |
| Screening Error / Timeout | Mark account as Pending Screening; open Case for manual action | Compliance Operations Queue | (e.g., 8 business hours) |

---

## Checklist

Copy and tick before marking the architecture design complete:

- [ ] FSC license type confirmed; `PartyProfileRisk` field usage documented
- [ ] Screening vendor API spec reviewed; Named Credential design specified (Named Principal auth)
- [ ] Orchestration pattern selected; governor limit calculations present for expected volume
- [ ] Synchronous vs. asynchronous decision explicitly justified
- [ ] Risk tier definitions documented with scoring inputs and Apex mapping
- [ ] Compliance review routing designed with queue assignments and SLAs
- [ ] Audit trail objects and retention periods specified
- [ ] Shield Field Audit Trail need assessed against retention requirements
- [ ] Vendor timeout / error handling documented with fallback behavior
- [ ] FSC Identity Verification explicitly excluded from AML screening scope in the design document

---

## Notes

(Record any deviations from the standard patterns in SKILL.md, regulatory-specific requirements not covered by the base design, or open decisions pending compliance officer input.)
