# Examples — FSL Reporting Data Model

## Example 1: First-Time Fix Rate via Record-Triggered Flow

**Context:** A telecom field service org needs to track first-time fix rate as a primary KPI. Management wants a live FSL dashboard showing FTF rate by territory and technician.

**Problem:** There is no native FSL FTF field. The team tries to calculate FTF using a report formula on a cross-object report, but the formula can't reliably evaluate whether a "Cannot Complete" predecessor SA exists for the same Work Order.

**Solution:**
1. Add a custom checkbox field `Is_First_Time_Fix__c` on WorkOrder
2. Create a Record-Triggered Flow on ServiceAppointment, triggered when Status changes to "Completed":
   - Get the parent WorkOrder
   - Get all ServiceAppointments on the same WorkOrder
   - Check if any SA (other than current) has Status = "Cannot Complete"
   - If none: update WorkOrder `Is_First_Time_Fix__c = true`
   - If any: update WorkOrder `Is_First_Time_Fix__c = false`
3. Build the FTF dashboard chart from the WorkOrder object using `Is_First_Time_Fix__c`

**Why it works:** The Flow runs in near-real-time when appointments are completed. The checkbox field is directly reportable as a simple aggregate metric (sum of true / count total = FTF rate).

---

## Example 2: Investigating Empty Travel Time Data

**Context:** An operations manager notices that the "Average Travel Time by Territory" dashboard shows no data for half the territories. The IT team investigates.

**Problem:** Technicians in the affected territories use the desktop Salesforce app (not FSL Mobile) to update appointment status to "Completed" directly. The FSL Mobile check-in workflow (En Route → On Site transitions) that populates `ActualTravelTime` is never triggered.

**Solution:**
1. Run this diagnostic SOQL to find the scope:
   ```soql
   SELECT ServiceTerritory.Name, COUNT(Id) total, 
          SUM(CASE WHEN ActualTravelTime != null THEN 1 ELSE 0 END) has_travel_data
   FROM ServiceAppointment
   WHERE Status = 'Completed' AND SchedStartTime = LAST_N_DAYS:90
   GROUP BY ServiceTerritory.Name
   ```
2. For territories with `has_travel_data = 0`, confirm whether FSL Mobile is deployed and the permission set is assigned
3. Implement a change management process requiring FSL Mobile usage for all status transitions
4. Document in the dashboard: "Travel time data requires FSL Mobile check-in. Territories with <90% mobile adoption may show incomplete data."

**Why it works:** The root cause is a process gap, not a reporting configuration issue. The diagnostic SOQL surfaces the gap by territory before corrective action.

---

## Anti-Pattern: Reporting on ServiceReport for Operational Metrics

**What practitioners do:** A report is built on the `ServiceReport` object expecting to find job duration, completion status, and technician performance data.

**What goes wrong:** `ServiceReport` is a customer-facing PDF/document object (like a field completion receipt). It contains a `ContentDocumentId` and metadata about when the report was generated, not operational ServiceAppointment metrics. Reports built on this object return document metadata, not job performance data.

**Correct approach:** Use `ServiceAppointment` as the primary reporting object for operational metrics. Use `WorkOrder` for job-level aggregation. ServiceReport is only relevant when auditing whether customer sign-off documents were generated.
