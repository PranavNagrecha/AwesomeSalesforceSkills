# Examples — NPSP Program Management Module (PMM)

## Example 1: Configuring Bulk Service Delivery with Correct Field Order

**Context:** A food bank uses PMM to record pantry visits. Staff enter deliveries for 30–50 clients each session using the Bulk Service Deliveries quick action. The admin set up the field set but placed Program Engagement before Client, which broke the cascading lookup.

**Problem:** When staff select a client, the Program Engagement column shows all engagements across all programs instead of filtering to the selected client's engagements. Staff cannot tell which engagement is correct, and some deliveries are saved against the wrong program.

**Solution:**

Navigate to Setup > Object Manager > Service Delivery > Field Sets > Bulk_Service_Deliveries_Fields.

Drag the fields into this order:
1. Client (Contact lookup)
2. Program Engagement (ProgramEngagement__c lookup)
3. Service (Service__c lookup)
4. Quantity
5. Delivery Date

After saving, test in the Bulk Service Deliveries action: selecting a Client should immediately filter the Program Engagement column to only that client's active engagements. Selecting a Program Engagement should filter the Service column to only services within that program.

**Why it works:** PMM's bulk entry component is wired to cascade lookup filters based on field-set position. Client must be in position 1 so the component knows which contact to filter engagements for. Program Engagement must be in position 2 so the component knows which program to filter services from. The cascade breaks silently if the order is wrong — no error is shown.

---

## Example 2: Enforcing Required Fields with Validation Rules

**Context:** A job training nonprofit tracks service deliveries for coaching sessions. The Delivery Date and Quantity fields are critical for grant reporting. The admin checked "Required" in the field set, but staff are saving records with these fields blank.

**Problem:** The field-set Required flag shows a red asterisk but does not prevent saving. ServiceDelivery__c records exist with null Quantity and null Delivery Date, making grant reports inaccurate.

**Solution:**

Create two validation rules on the ServiceDelivery__c object:

Validation Rule 1 — Require Delivery Date:
```
Rule Name: PMM_Require_Delivery_Date
Active: true
Error Condition Formula:
  ISBLANK(pmdm__DeliveryDate__c)
Error Message: "Delivery Date is required on all service delivery records."
Error Location: Field — pmdm__DeliveryDate__c
```

Validation Rule 2 — Require Quantity:
```
Rule Name: PMM_Require_Quantity
Active: true
Error Condition Formula:
  ISBLANK(pmdm__Quantity__c) || pmdm__Quantity__c <= 0
Error Message: "Quantity must be greater than zero for all service deliveries."
Error Location: Field — pmdm__Quantity__c
```

After activating the rules, test in the Bulk Service Deliveries action. Attempt to save a row with Delivery Date blank — the entire bulk submission should fail with the validation error displayed in the action UI.

**Why it works:** Salesforce validation rules run at the DML layer for all save operations, including the PMM bulk entry quick action. The field-set Required flag is a UI hint only and operates in the component layer, which does not invoke the validation pipeline.

---

## Example 3: Recording Attendance for a Scheduled Program

**Context:** A literacy program runs a weekly class on Tuesdays for 12 weeks. The org uses ServiceSchedule__c to model the recurring session and ServiceParticipant__c to roster enrolled clients. After each class, a coordinator records who attended by creating ServiceDelivery__c records.

**Problem:** The coordinator tries to create ServiceDelivery__c records directly without connecting them to the ServiceSchedule__c, so attendance reports do not show which session each delivery belongs to.

**Solution:**

1. Create a ServiceSchedule__c record: set Service__c = Literacy Coaching, set First Session Date, Last Session Date, and Day of Week = Tuesday.
2. For each enrolled client, create a ServiceParticipant__c: ProgramEngagement__c = the client's engagement record, ServiceSchedule__c = the literacy schedule created above.
3. After each class, use the PMM attendance quick action (available from the ServiceSchedule__c record page) to mark participants as Attended or Absent and auto-generate ServiceDelivery__c records. Do not create ServiceDelivery__c records manually without going through the schedule path — manual records lack the ServiceSchedule__c reference.

**Why it works:** PMM's attendance tracking reports aggregate ServiceDelivery__c records by ServiceSchedule__c. Deliveries created outside the schedule-attendance path are not counted in session attendance totals, only in aggregate service volume totals.

---

## Anti-Pattern: Trying to Roll Up Service Delivery Data into NPSP Giving Reports

**What practitioners do:** A grants manager wants a single report showing both donation revenue and service delivery counts for each program. They try to add ServiceDelivery__c as a related object in an NPSP Account/Contact report or attempt to write a formula field on the Opportunity that pulls from ServiceDelivery__c.

**What goes wrong:** ServiceDelivery__c and NPSP Opportunity have no direct relationship. The objects are in different namespaces (pmdm vs npe01/npo02). There is no lookup or master-detail between them. Cross-object formula fields are not possible across unrelated objects. Report joins across unrelated objects require a shared common field, which does not exist between NPSP giving records and PMM delivery records.

**Correct approach:** Build separate reports: one NPSP report for donation/grant revenue, one PMM report for service delivery volume. Present them side-by-side in a dashboard. If a unified view is required, use a Salesforce report with a cross-filter or export both to an external BI tool for joining. Do not attempt to create custom lookup fields between Opportunity and ServiceDelivery__c — this creates unsupported cross-package dependencies that break on package upgrades.
