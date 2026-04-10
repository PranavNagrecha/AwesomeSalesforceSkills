# Gotchas — FSL Reporting Data Model

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: ActualDuration and ActualTravelTime Are Null Without Mobile Check-In

**What happens:** Reports on job duration and travel time show blank values for appointments that were completed without using the FSL Mobile app's En Route and On Site workflow. `ActualDuration` and `ActualTravelTime` are populated by the mobile check-in flow — not by status changes made in the desktop browser.

**When it occurs:** Any org where technicians update appointment status via the desktop Salesforce app, the standard Salesforce Mobile app, or via direct API calls without going through FSL Mobile's workflow steps.

**How to avoid:** Document this dependency in dashboard descriptions. Query the mobile adoption rate: `SELECT COUNT() FROM ServiceAppointment WHERE Status = 'Completed' AND ActualDuration = null`. Address the process gap before committing to KPIs that require these fields.

---

## Gotcha 2: ServiceReport Is a Customer-Facing PDF — Not an Operational Report

**What happens:** Admins or developers query `ServiceReport` expecting job completion metrics and find ContentDocumentId and PDF generation metadata instead of appointment performance data.

**When it occurs:** Any time someone looks for "service reports" in Salesforce without knowing the FSL-specific meaning of the term.

**How to avoid:** Operational metrics live on `ServiceAppointment` and `WorkOrder`. `ServiceReport` is exclusively for customer-facing completion documents. Clarify terminology in project documentation.

---

## Gotcha 3: First-Time Fix Rate Has No Native FSL Field

**What happens:** Admins try to find a standard "First Time Fix" field or report type in FSL and it doesn't exist. Building FTF rate without custom logic produces no real-time metric.

**When it occurs:** Any project that specifies FTF rate as a KPI without a custom field development budget.

**How to avoid:** Plan for custom FTF tracking at project start: Flow + checkbox field on WorkOrder. Without it, FTF can only be calculated via ad-hoc SOQL or manual Excel analysis.

---

## Gotcha 4: SchedStartTime vs. ActualStartTime — Different Fields for Different Purposes

**What happens:** Reports mix up `SchedStartTime` (when the FSL engine planned for work to start) with `ActualStartTime` (when the technician actually checked in). Using SchedStartTime in "on-time arrival" calculations gives planned vs. committed window, not actual arrival time.

**When it occurs:** Report builders new to FSL who assume "start time" is unambiguous.

**How to avoid:** Define clearly in report documentation: SchedStartTime = FSL engine's plan; ArrivalWindowStart = customer commitment; ActualStartTime = mobile check-in time. Use the appropriate field for each metric.

---

## Gotcha 5: Cross-Filter Reports for FTF Are Complex and Slow

**What happens:** Attempting to build an FTF report using cross-filters (ServiceAppointments where WorkOrder has no other SA with Status = "Cannot Complete") works but is computationally expensive on large orgs. Report timeouts occur in orgs with hundreds of thousands of ServiceAppointments.

**When it occurs:** Large FSL implementations without a custom FTF field who try to calculate FTF natively in report filters.

**How to avoid:** Implement the Flow + custom checkbox pattern for FTF tracking. This moves the calculation to data-write time (fast, real-time) rather than report-read time (slow, potentially timeout-prone).
