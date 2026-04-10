# FSL Service Report Templates — Work Template

Use this template when designing, implementing, or reviewing a Field Service service report template solution.

---

## Scope

**Skill:** `fsl-service-report-templates`

**Request summary:** (fill in what the user asked for — e.g., "auto-generate service report PDF on appointment completion with customer signature")

---

## Context Gathered

Answer these before designing the solution:

- **Target record type:** WorkOrder / ServiceAppointment / both
- **Generation trigger:** Manual (user button) / Automatic on status change / External API call
- **API version in use:** (confirm v40.0+ for createServiceReport)
- **Signature capture required?** Yes / No — if yes, Customer / Technician / both
- **Conditional sections required?** Yes / No — if yes, describe conditions
- **Offline mobile generation required?** Yes / No
- **Multiple templates needed?** Yes (per Work Type) / No (single template)
- **Document Builder or classic ServiceReportLayout?** (see Decision Guidance in SKILL.md)
- **FSL managed package installed and confirmed?**

---

## Template Design

Describe the intended ServiceReportLayout (or Document Builder template) structure:

| Section | Content | Conditional? |
|---|---|---|
| Header | (org logo, address, report number) | No |
| Work Order Details | (fields: Status, Subject, Description) | No |
| Service Appointment Details | (fields: SchedStartTime, ActualDuration) | No |
| Products Consumed | (related list) | No |
| Time Sheet Entries | (related list) | No |
| Customer Signature | (DigitalSignature placeholder) | No |
| Technician Signature | (DigitalSignature placeholder) | No |
| (add rows as needed) | | |

---

## Generation Approach

Which pattern from SKILL.md applies?

- [ ] Pattern 1: Async Queueable generation on ServiceAppointment Completion
- [ ] Pattern 2: Document Builder with Flow-driven conditional sections
- [ ] Other: ___________

**Template Id selection logic:**
- Static (single template Id hardcoded / stored in Custom Metadata): ___________
- Dynamic (based on Work Type lookup): ___________

---

## Signature Capture Plan

- [ ] DigitalSignature placeholder added to ServiceReportLayout
- [ ] Signature capture confirmed to occur BEFORE report generation trigger fires
- [ ] Queueable checks for `Captured` DigitalSignature before calling `createServiceReport`
- [ ] Retry / defer logic in place for signature sync race condition

---

## Offline / Briefcase Builder Audit

Complete this table after finalizing the template:

| Template Field | SObject.Field | In Briefcase Priming? |
|---|---|---|
| (example) Work Order Subject | WorkOrder.Subject | Yes / No |
| (example) Site Address | WorkOrder.ServiceTerritoryId → ... | Yes / No |
| (add a row per field in the template) | | |

- [ ] All fields confirmed in Briefcase Builder priming rules
- [ ] Mobile devices re-primed after changes

---

## Generated Artifact Verification

After implementation, verify:

- [ ] `createServiceReport` call is inside a Queueable `execute()` method (not direct in trigger)
- [ ] Old-value guard present: `sa.Status == 'Completed' && old.Status != 'Completed'`
- [ ] ContentDocumentLink query uses `LinkedEntityId = :recordId` (not direct ContentDocument query)
- [ ] PDF generated in sandbox — confirm it is not blank
- [ ] Signature image appears in PDF when signature is captured before generation
- [ ] Offline test: generate report on device with airplane mode — no blank fields
- [ ] No duplicate PDFs accumulate on repeated saves (deduplication logic confirmed)

---

## Notes

Record any deviations from the standard pattern and the reason:

- 
- 

---

## Related Checklist Items from SKILL.md

Copy from SKILL.md Review Checklist and tick as complete:

- [ ] ServiceReportLayout configured and associated with correct Work Type
- [ ] createServiceReport in Queueable (async)
- [ ] DigitalSignature synced before generation
- [ ] Briefcase Builder priming covers all template fields
- [ ] Generated PDFs verified as ContentDocument on source record
- [ ] Conditional sections tested via Document Builder + Flow (if applicable)
- [ ] API v40.0+ confirmed
