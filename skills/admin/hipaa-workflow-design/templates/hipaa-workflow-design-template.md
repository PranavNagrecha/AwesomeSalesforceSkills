# HIPAA Workflow Design — Work Template

Use this template when designing HIPAA-compliant workflow requirements for Health Cloud.

## Scope

**Skill:** `hipaa-workflow-design`

**Request summary:** (fill in what the user asked for)

## Prerequisites Verified

- [ ] Salesforce BAA executed (or confirmed in procurement)
- [ ] BAA-covered products confirmed (list all products that will process PHI)
- [ ] Shield licenses confirmed: Platform Encryption, Field Audit Trail, Event Monitoring
- [ ] PHI field inventory started

## PHI Field Inventory

| Object | Field API Name | PHI Category | Encryption Required | Field Audit Trail Required |
|--------|---------------|--------------|--------------------|-----------------------------|
| Account | | Name / DOB / Address | Yes | Yes |
| (add rows) | | | | |

## HIPAA Security Rule Control Mapping

| HIPAA Requirement | Salesforce Control | Status |
|---|---|---|
| Access Control §164.312(a)(1) | OWD-Private + care team sharing | |
| Audit Controls §164.312(b) | Shield Field Audit Trail (10yr) + Event Monitoring + SIEM | |
| Integrity §164.312(c)(1) | Shield Platform Encryption + TLS | |
| Transmission Security §164.312(e)(1) | TLS enforced | |
| Minimum Necessary §164.514(d) | OWD-Private + role-scoped permission sets | |

## Access Control Matrix

| Role | Objects Accessible | PHI Fields Accessible | Access Level |
|------|-------------------|----------------------|--------------|
| Primary care physician | Account, CarePlan, ClinicalEncounter, HealthCondition | All clinical PHI | Read/Edit (own patients) |
| Administrative staff | Account | Demographic PHI only | Read/Edit |
| Billing | Account | Billing/insurance fields only | Read |
| (add roles) | | | |

## Event Monitoring Streaming Requirements

- Target SIEM: 
- Log types to stream: Login, Logout, Report, API Access, ListViewEvent
- Streaming frequency: Daily (before 30-day expiration)
- Retention policy: 6 years minimum

## Notes

(Record BAA coverage decisions, custom PHI field identification, Shield configuration scope)
