# FSL Mobile App Setup — Work Template

Use this template when planning, configuring, or reviewing an FSL Mobile deployment or extension.

## Scope

**Skill:** `fsl-mobile-app-setup`

**Request summary:** (fill in what the user asked for)

**In scope:**
- [ ] Offline priming configuration
- [ ] App extensions (LWC Quick Actions / HTML5 toolkit)
- [ ] Deep linking
- [ ] Custom branding
- [ ] Troubleshooting existing deployment

---

## Prerequisites Check

| Item | Status | Notes |
|---|---|---|
| Field Service license provisioned | | |
| Field Service Mobile license provisioned | | |
| Target users have Field Service Mobile permission set | | |
| FSL Mobile app version on device | | |
| Mobile App Plus add-on (required for branding) | | N/A if branding not in scope |

---

## Offline Priming Configuration

### Priming Hierarchy

| Level | Object | Enabled? | Notes |
|---|---|---|---|
| 1 | ServiceResource (technician) | | Base — always required |
| 2 | ServiceAppointment | | |
| 3 | WorkOrder | | |
| 4 | WorkOrderLineItem | | |

### Related Lists in Priming

| Object | Related List | Max Records per List | Notes |
|---|---|---|---|
| WorkOrder | | | Max 50 per list |
| WorkOrder | | | Max 50 per list |
| ServiceAppointment | | | Max 50 per list |

### Page Reference Budget

| Scheduling Window (days) | Appointments/Day (avg) | WOs/Appointment (avg) | Line Items/WO (avg) | Related List Records (total) | Estimated Page Refs | Status |
|---|---|---|---|---|---|---|
| | | | | | | Target: < 1,000 |

**Calculation:**
```
Page Refs ≈ (Appointments) + (Appointments × WOs/Appt) + (Appointments × WOs/Appt × LineItems/WO) + (Related List Records)
```

---

## App Extensions

### Extension Inventory

| Extension Name | Type (LWC / HTML5) | Target Object | Action Name | Status |
|---|---|---|---|---|
| | | | | |

### Extension Type Decision

**Reason for LWC Quick Action:** (fill in — default choice for all new extensions)

**Reason for HTML5 Toolkit (if applicable):** (fill in justification — should only be used for legacy or specific edge cases)

### LWC Quick Action Checklist

- [ ] LWC accepts `@api recordId`
- [ ] Data reads use `@wire` / `uiRecordApi` (not imperative Apex)
- [ ] Data writes use `createRecord` / `updateRecord` (benefits from LDS offline queue)
- [ ] Quick Action registered on target object (type: Lightning Web Component)
- [ ] Quick Action added to FSL Mobile action list in Field Service Mobile Settings

---

## Deep Link Specification (if in scope)

| Item | Value |
|---|---|
| URI scheme | (from Field Service Mobile connected app) |
| Target object type | |
| Target action | |
| Parameters included | |
| Estimated payload size | Must be < 1 MB |
| Source app | |

- [ ] Deep link payload verified < 1 MB with worst-case data
- [ ] Tested on physical device (iOS / Android)

---

## Custom Branding (if in scope)

| Item | Value |
|---|---|
| Mobile App Plus add-on confirmed | Yes / No |
| Logo file | (filename, dimensions) |
| Primary color hex | |
| Splash screen asset | |

- [ ] Mobile App Plus license confirmed before beginning
- [ ] Assets uploaded in Field Service Mobile Settings → Branding
- [ ] Connected app republished after branding changes
- [ ] Branding verified on physical device after reinstall / cache clear

---

## End-to-End Test Results

| Test | Result | Notes |
|---|---|---|
| Full priming sync on test device | Pass / Fail | |
| Offline record access — appointments | Pass / Fail | |
| Offline record access — work orders | Pass / Fail | |
| Offline record access — line items | Pass / Fail | |
| Offline write + sync back to org | Pass / Fail | |
| Quick action renders correctly offline | Pass / Fail | |
| Deep link navigates to correct record | Pass / Fail | (if in scope) |
| Custom branding displays correctly | Pass / Fail | (if in scope) |

---

## Review Checklist

- [ ] Field Service and FSL Mobile licenses confirmed on user profiles
- [ ] Offline priming hierarchy configured (resource → appointments → work orders → line items)
- [ ] Each related list in priming has ≤ 50 records in production data range
- [ ] Total estimated page references per resource < 1,000
- [ ] App extensions use LWC Quick Actions (or HTML5 with documented justification)
- [ ] Deep link payloads < 1 MB (if applicable)
- [ ] Custom branding only configured with Mobile App Plus add-on (if applicable)
- [ ] End-to-end offline test completed on physical device
- [ ] Technician user profiles have correct permission sets and app access

---

## Notes

(Record any deviations from the standard pattern and why.)
