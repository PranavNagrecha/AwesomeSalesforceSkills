# Marketing Consent Architecture — Work Template

Use this template when designing or evaluating consent management architecture spanning Salesforce CRM and Marketing Cloud.

## Scope

**Skill:** `marketing-consent-architecture`

**Request summary:** (fill in what was asked — e.g., "design consent data model for GDPR compliance across MC and CRM")

## Context Gathered

Answer these before proceeding:

- **MC connected to CRM?** Yes / No
- **Consent Management integration enabled?** Yes / No / Unknown
- **Channels in scope:** Email / SMS / Phone / Push / Other: ___
- **Regulatory regimes:** GDPR / CCPA / CAN-SPAM / None / Other: ___
- **Current consent storage:** Custom fields on Contact / Individual boolean / ContactPointTypeConsent / MC All Subscribers only / Unknown
- **Multiple email addresses per person?** Yes / No
- **Known per-purpose requirements (e.g., marketing vs. transactional)?** Yes / No — purposes: ___

## Consent Data Model Design

### Data Use Purposes Required

| Purpose Name | LegalBasis | LegalBasisSource | Channels |
|---|---|---|---|
| (e.g. Email Marketing) | Consent | Web preference center | Email |
| (e.g. Email Transactional) | ContractPerformance | Customer Agreement | Email |
| (e.g. SMS Marketing) | Consent | Mobile opt-in | SMS |

### ContactPointTypeConsent Records Per Individual

| Channel | Purpose | Default Status | Notes |
|---|---|---|---|
| Email | Email Marketing | OptIn / OptOut | |
| Email | Email Transactional | OptIn | Usually always OptIn |
| SMS | SMS Marketing | OptIn / OptOut | |

### ContactPointConsent Required?

- [ ] No — one address per person per channel, ContactPointTypeConsent is sufficient
- [ ] Yes — multiple addresses per person, ContactPointConsent needed for address-level control

## Sync Pattern

| Consent Signal | Source System | Target System | Sync Mechanism | Trigger |
|---|---|---|---|---|
| (e.g. Email unsubscribe) | MC | CRM | MC Consent Mgmt writeback | MC unsubscribe event |
| (e.g. Preference center update) | CRM | MC | MC reads at send time | Send execution |
| (e.g. DSAR erasure) | CRM | MC | Custom sync / REST API | Manual or automated process |

## Architecture Decision

**Pattern selected:** CRM as system of record / MC as system of record / Hybrid

**Rationale:** (explain why this pattern was chosen given regulatory requirements and org capabilities)

## MC Integration Configuration Checklist

- [ ] Marketing Cloud Consent Management feature enabled in connector settings
- [ ] Data Use Purpose records created in CRM for each purpose in scope
- [ ] MC Send Classifications / Journeys mapped to corresponding Data Use Purpose records
- [ ] MC unsubscribe writeback to CRM configured and tested
- [ ] Suppression test completed: subscriber with OptOut CRM record not delivered test send

## Validation Steps

- [ ] Individual records exist for all Contacts and Leads in scope
- [ ] ContactPointTypeConsent records exist for each channel + purpose combination
- [ ] All ContactPointTypeConsent records have DataUsePurposeId populated
- [ ] No ContactPointTypeConsent records use Contact.Id as IndividualId (should use Contact.IndividualId)
- [ ] Permission sets grant access to Individual, ContactPointTypeConsent, ContactPointConsent, DataUsePurpose
- [ ] Reconciliation query shows MC opted-out count matches CRM OptOut consent record count

## Notes

(Record any deviations from the standard pattern and why.)
