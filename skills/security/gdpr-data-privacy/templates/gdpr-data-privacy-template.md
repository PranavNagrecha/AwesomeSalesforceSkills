# GDPR Data Privacy — Work Template

Use this template when planning or reviewing a GDPR/CCPA data privacy implementation in Salesforce.

---

## Scope

**Skill:** `gdpr-data-privacy`

**Request summary:** _(fill in: what the data subject or legal team is asking for — e.g., RTBF request, consent model build-out, DSR intake workflow)_

**Regulation(s) in scope:** `[ ] GDPR` `[ ] CCPA` `[ ] Both` `[ ] Other: ___________`

---

## Context Gathered

Answer these before proceeding:

| Question | Answer |
|---|---|
| Privacy Center licensed? | Yes / No |
| API version of org? | ___ (must be 42.0+ for Individual object) |
| Objects storing PII (list all) | Contact, Lead, ___, ___ |
| Consent channels in scope | Email, Phone, ___, ___ |
| Expected DSR volume per month | ___ |
| Existing Individual records? | Yes / No / Partial |
| Existing ContactPointTypeConsent records? | Yes / No / Partial |

---

## Individual Object Linkage Plan

| Person Object | Population Size | IndividualId Populated? | Migration Needed? |
|---|---|---|---|
| Contact | ___ | Yes / No / Partial | Yes / No |
| Lead | ___ | Yes / No / Partial | Yes / No |
| PersonAccount | ___ | Yes / No / Partial | Yes / No |

**IndividualId population mechanism:** _(Trigger / Flow / Data Loader migration / Privacy Center)_

---

## Consent Model Design

| Channel | Object Used | Consent Status | EffectiveFrom Source | CaptureSource |
|---|---|---|---|---|
| Email | ContactPointTypeConsent | OptIn / OptOut / Unknown | ___ | ___ |
| Phone | ContactPointTypeConsent | OptIn / OptOut / Unknown | ___ | ___ |
| Direct Mail | ContactPointTypeConsent | OptIn / OptOut / Unknown | ___ | ___ |
| _(custom)_ | ContactPointConsent | OptIn / OptOut / Unknown | ___ | ___ |

**DataUsePurpose records needed:** _(list processing purposes if per-purpose consent is required)_

- Purpose 1: ___ — Lawful basis: ___
- Purpose 2: ___ — Lawful basis: ___

---

## Right to Erasure Implementation

**RTBF mechanism:** `[ ] Privacy Center Erasure Policy` `[ ] Custom Batch Apex` `[ ] Both`

### If Privacy Center

| Policy Name | Objects Covered | Action (Delete / Anonymize) | Triggered by |
|---|---|---|---|
| ___ | Contact, Lead, ___ | ___ | DSR record |

### If Batch Apex

| Class Name | Objects Covered | Batch Size | Schedule |
|---|---|---|---|
| BatchForgotIndividuals | Contact, Lead, ___, ___ | 200 | ___ |

**Anonymization token pattern:** `ANON-<timestamp>` or ___

**Audit record object:** `DSR_Audit__c` or ___

---

## Data Subject Request Workflow

| Step | Owner | Tool / Object | SLA |
|---|---|---|---|
| Intake | ___ | ___ | ___ hours |
| Identity verification | ___ | ___ | ___ hours |
| Erasure / Export execution | ___ | ___ | ___ days |
| Confirmation to subject | ___ | ___ | ___ days |
| Audit record creation | ___ (automated) | DSR_Audit__c | on completion |

**Total SLA target:** ___ days _(GDPR requires response within 30 days)_

---

## Retention Exceptions Register

Fields or records that must be retained beyond an erasure request (document lawful basis):

| Object | Field(s) | Retention Period | Lawful Basis |
|---|---|---|---|
| Order | Amount, OrderNumber | 7 years | Legal obligation (tax records) |
| ___ | ___ | ___ | ___ |

---

## Review Checklist

- [ ] Every in-scope Contact, Lead, and PersonAccount has `IndividualId` populated
- [ ] `ContactPointTypeConsent` records created for each consent channel per person, with `EffectiveFrom` and `CaptureDate` set
- [ ] RTBF mechanism (Privacy Center or Batch Apex) covers ALL objects storing PII — not just Contact
- [ ] Anonymization used instead of hard delete for records with FK dependencies
- [ ] DSR intake, identity verification, fulfillment, and audit-trail steps tested end-to-end
- [ ] Audit trail records RTBF execution (requestor, fulfilled date, anonymization token, records affected)
- [ ] Retention exceptions documented with lawful basis
- [ ] Batch Apex tested at scale in sandbox with representative data volume
- [ ] Consent records for expired windows (`EffectiveTo < TODAY`) flagged and handled
- [ ] No `HasOptedOutOfEmail` used as the sole GDPR consent mechanism

---

## Notes

_(Record deviations from the standard pattern, decisions made, open questions, and follow-up items.)_
