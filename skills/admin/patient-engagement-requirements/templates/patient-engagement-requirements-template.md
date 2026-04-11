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
| Health assessments | | OmniStudio (install required) + Discovery Framework | |
| Secure patient messaging | | Messaging for In-App and Web | |
| FHIR data in portal | | FHIR R4 for Experience Cloud perm set | |

## Prerequisites Checklist

- [ ] Experience Cloud for Health Cloud license included in contract
- [ ] Per-user Experience Cloud for HC license count estimated
- [ ] OmniStudio managed package installed in org (Setup > Installed Packages)
- [ ] Discovery Framework installed in org
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
