# Patient Engagement Requirements — Work Template

Use this template when defining patient engagement requirements for Health Cloud.

## Scope

**Skill:** `patient-engagement-requirements`

**Request summary:** (fill in what the user asked for)

## Feature Inventory and License Dependencies

| Feature | In Scope? | License Required | Confirmed in Contract? |
|---------|-----------|-----------------|----------------------|
| Patient portal | | Experience Cloud for Health Cloud | |
| Appointment self-scheduling | | Intelligent Appointment Management (IAM) | |
| No-show prediction | | CRM Analytics (separate add-on) | |
| Health assessments | | OmniStudio runtime + Discovery Framework feature + HC and HC Platform PSLs | |
| Secure patient messaging | | Messaging for In-App and Web | |
| FHIR data in portal | | FHIR R4 for Experience Cloud Sites perm set + FHIR-Aligned Clinical Data Model org pref | |

## Prerequisites Checklist

- [ ] Experience Cloud for Health Cloud license included in contract
- [ ] Per-user Experience Cloud for HC license count estimated
- [ ] OmniStudio runtime recorded (managed package or standard runtime)
- [ ] Discovery Framework feature enabled in org
- [ ] EHR scheduling system of record, Named Credential, and AppointmentBookingConfig mapping planned
- [ ] AppointmentReason and channel matrix agreed with clinical operations
- [ ] CRM Analytics license confirmed (if no-show prediction in scope)
- [ ] Messaging add-on confirmed and BAA coverage verified

## HIPAA Channel Compliance

| Engagement Channel | PHI May Be Present? | BAA Coverage Confirmed? | HIPAA-Compliant Channel? |
|-------------------|--------------------|-----------------------|--------------------------|
| Appointment reminders | Possibly | | |
| Secure messaging | Yes | | Messaging for In-App and Web |
| Assessment responses | Yes | | |
| Patient education | Unlikely | | |

## Notes

(License scope decisions, stakeholder-agreed must-have vs. nice-to-have features, scheduling data source)
