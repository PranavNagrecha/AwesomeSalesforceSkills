# FSL Work Order Management — Configuration Checklist

Use this template when configuring or reviewing FSL Work Order Management in an org.

---

## Scope

**Skill:** `fsl-work-order-management`

**Request summary:** (fill in what the user asked for — e.g., "Configure work types and auto-create SAs for preventive maintenance jobs")

**Org:** (sandbox / production name)

**Date:** (YYYY-MM-DD)

---

## Pre-Flight: FSL Package and Permissions

- [ ] Field Service managed package is installed (verify in Setup > Installed Packages)
- [ ] Field Service is enabled under Setup > Field Service Settings
- [ ] **Field Service Admin** permission set assigned to dispatcher and admin users
- [ ] **Field Service Standard** permission set assigned to field technicians
- [ ] **Field Service Scheduling** permission set assigned to users who run optimization

---

## WorkType Configuration

For each WorkType to be created or reviewed:

| WorkType Name | Estimated Duration | DurationType | AutoCreateSvcAppt | Notes |
|---|---|---|---|---|
| (e.g., Preventive Maintenance) | (e.g., 90) | (Minutes / Hours) | (true / false) | |
| | | | | |
| | | | | |

- [ ] Every WorkType has Estimated Duration and DurationType set (not left blank)
- [ ] AutoCreateSvcAppt is explicitly set on each WorkType (true or false — no default assumption)
- [ ] WorkType names follow org naming convention and match what field ops teams expect

---

## Work Order Status Picklist

Status values to configure under Setup > Object Manager > WorkOrder > Fields > Status:

| Status Value | API Name | Description | Is Default? |
|---|---|---|---|
| New | New | WO created, not yet started | Yes |
| In Progress | In_Progress | Technician actively working | No |
| On Hold | On_Hold | WO paused pending parts/approval | No |
| Completed | Completed | All work done, WO closed | No |
| Canceled | Canceled | WO voided before start | No |

- [ ] Status values cover the full operational lifecycle
- [ ] No assumption made that WO status mirrors SA status — these are independent

---

## Service Appointment Status Picklist

Status values to configure under Setup > Object Manager > ServiceAppointment > Fields > Status:

| Status Value | API Name | Description |
|---|---|---|
| None | None | SA created but not yet scheduled |
| Scheduled | Scheduled | SA placed on Gantt with resource |
| Dispatched | Dispatched | Technician notified via mobile app |
| In Progress | In_Progress | Technician en route or on site |
| Cannot Complete | Cannot_Complete | Job blocked; requires follow-up |
| Completed | Completed | Work performed successfully |
| Canceled | Canceled | SA voided |

- [ ] SA status values are managed independently from WO status values
- [ ] Dispatched status is configured to trigger FSL mobile app notification (if applicable)

---

## Status Cascade Automation

Because WO and SA statuses do not cascade automatically, document any cascade logic here:

| Trigger | Condition | Action | Implemented By |
|---|---|---|---|
| SA Status → Completed | All sibling SAs on WO are Completed | Update WO Status → Completed | Record-Triggered Flow |
| WO Status → Canceled | WO is canceled | Cancel all open SAs | Record-Triggered Flow |
| (add rows as needed) | | | |

- [ ] All cascade rules documented above are implemented in automation (Flow or Apex)
- [ ] Cascade automation handles edge cases: SA deleted (not completed), SA manually bypassed
- [ ] No cascade behavior is assumed to exist without explicit automation

---

## Maintenance Plan Configuration (if applicable)

For each Maintenance Plan:

| Plan Name | WorkType | Frequency | FrequencyType | GenerationHorizon | Start Date | End Date |
|---|---|---|---|---|---|---|
| | | | | (days) | | |

- [ ] Maintenance Plans linked to the correct WorkType
- [ ] GenerationHorizon set to an appropriate lookahead window (typically 30–90 days)
- [ ] Operations team informed that WO generation occurs ~3x per day, not in real time
- [ ] No SLA commitments built on exact Maintenance Plan fire times

---

## Work Order Line Item Design

- [ ] Confirmed WO child record counts will not exceed 10,000 per WO
- [ ] Confirmed WOLI counts per WO will not exceed 500 (Gantt visibility limit)
- [ ] For jobs with >400 WOLIs, a parent-child WO hierarchy is used to distribute tasks
- [ ] Each WOLI that requires separate scheduling has its own SA

---

## Post-Configuration Validation

- [ ] Create a test WorkOrder with a WorkType where `AutoCreateSvcAppt = true` — confirm one SA is created in `None` status
- [ ] Confirm the SA appears in the Dispatcher Console unscheduled queue
- [ ] Complete the SA manually — confirm WO status does NOT change automatically (confirming independence)
- [ ] If cascade Flow is implemented, complete all sibling SAs — confirm WO status updates as expected
- [ ] Run `python3 scripts/check_fsl_work_order_management.py --manifest-dir <path>` against retrieved metadata and resolve any WARNs

---

## Notes and Deviations

(Record any deviations from standard patterns and the reason why)

---

## Sign-Off

| Reviewer | Role | Date | Status |
|---|---|---|---|
| | | | Approved / Needs Revision |
