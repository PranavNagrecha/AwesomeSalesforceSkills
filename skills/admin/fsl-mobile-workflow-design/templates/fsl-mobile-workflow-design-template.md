# FSL Mobile Workflow Design — Work Template

Use this template when planning, reviewing, or troubleshooting FSL Mobile technician workflows — including job lifecycle, offline data capture, signature collection, parts consumption, and briefcase priming.

---

## Scope

**Skill:** `fsl-mobile-workflow-design`

**Request summary:** (describe what the practitioner or user is asking for)

**Org context:** (Production / Sandbox / Scratch; FSL version; Spring '25 or earlier)

---

## Context Gathered

Answer these before proceeding:

- **Offline mode enabled?** Yes / No
- **Briefcase Builder configured?** Yes / No / Unknown
- **Objects confirmed in briefcase:** ServiceResource / ServiceAppointment / WorkOrder / WorkOrderLineItem / ContentDocument / ContentDocumentLink / Other: ___
- **SA→WO status cascade automation:** Flow / Process Builder / Apex Trigger / None — describe: ___
- **Data Capture flows (Spring 25)?** In use / Not in use / Unknown
- **Service report in use?** Yes / No — template name: ___
- **Parts consumption (ProductConsumed) configured?** Yes / No / Partial

---

## Job Lifecycle Map

Document the required SA status transitions and any WO status that must track SA:

| SA Status | Triggered By | WO Status Change Required? | Automation Owner |
|---|---|---|---|
| Scheduled | Dispatcher | No | — |
| Dispatched | Dispatcher | No | — |
| In Progress | Technician (mobile) | Yes → In Progress | Record-Triggered Flow |
| Completed | Technician (mobile) | Yes → Completed (if last SA) | Record-Triggered Flow |
| Cannot Complete | Technician (mobile) | Optional → review required | Record-Triggered Flow |

---

## Briefcase Field Audit

For each field required in the mobile UI or service report, confirm briefcase inclusion:

| Object | Field API Name | In Briefcase? | In Mobile Layout? | In Report Template? |
|---|---|---|---|---|
| WorkOrder | Status | [ ] | [ ] | [ ] |
| WorkOrder | Description | [ ] | [ ] | [ ] |
| WorkOrder | Subject | [ ] | [ ] | [ ] |
| ServiceAppointment | Status | [ ] | [ ] | N/A |
| (add rows as needed) | | | | |

---

## Server-Side Logic Inventory

For each automation on FSL Mobile objects, classify its sync behavior:

| Automation | Type | Object | Fires At | Risk if Offline? |
|---|---|---|---|---|
| Example: SetWOCompleted | Flow | ServiceAppointment | Sync | Low — acceptable delay |
| Example: RequireFailureCode | Validation Rule | WorkOrder | Sync | High — blocks sync if field not in mobile layout |
| (add rows) | | | | |

---

## Data Capture / Signature Configuration

- **Form type:** Data Capture Flow (Spring 25) / FSL Quick Action / Neither
- **Signature capture:** Yes / No — if yes, ContentDocument in briefcase: Yes / No
- **Signature merge field in report template:** Yes / No — field reference: ___
- **Required fields in Data Capture flow:** (list)
- **Conditional logic needed:** (describe)

---

## Parts Consumption Configuration

- **ProductRequired records in briefcase:** Yes / No
- **NewProductConsumed quick action on WO mobile layout:** Yes / No
- **Stakeholders informed of sync-delay inventory updates:** Yes / No
- **High-value parts requiring real-time accuracy:** (list — these require connectivity at consumption)

---

## Approach

Which pattern from SKILL.md applies? (check all that apply)

- [ ] Customer Signature Capture pattern
- [ ] Parts Consumption (ProductConsumed) pattern
- [ ] Automating WO Status from SA Status pattern
- [ ] Custom pattern — describe: ___

---

## Review Checklist

- [ ] SA status lifecycle documented and all required WO status cascades covered by Record-Triggered Flow
- [ ] Briefcase hierarchy confirmed: ServiceResource → SA → WO → WOLI
- [ ] All fields in mobile UI and service report template are in the briefcase
- [ ] No automation assumes server-side execution while technician is offline
- [ ] Data Capture flows (Spring 25+) or FSL quick actions configured for all structured offline forms
- [ ] Signature capture linked to ContentDocument; ContentDocument in briefcase; merge field in report template
- [ ] ProductConsumed quick action on WO mobile layout
- [ ] Stakeholders informed: inventory updates are sync-time, not real-time offline
- [ ] End-to-end airplane mode test completed
- [ ] Service report PDF validated after sync — no blank fields

---

## Notes

(Record any deviations from standard patterns, org-specific constraints, or decisions made during the engagement.)
