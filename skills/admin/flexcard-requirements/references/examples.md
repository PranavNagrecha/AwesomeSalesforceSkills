# Examples — FlexCard Requirements

## Example 1: Patient Summary FlexCard for Health Cloud Service Console

**Context:** A healthcare org uses Health Cloud. Service agents need a Patient Summary FlexCard on the patient record page showing key health data, recent encounters, and a button to launch a new encounter OmniScript.

**Problem:** The BA produces a generic card wireframe without specifying data source types. The developer defaults to SOQL for all fields, but several fields (EncounterCount, LastCareGapStatus) come from an Integration Procedure that aggregates Care Observation records. The card shows blank values for those fields with no error message.

**Solution:**
Requirements document specifies a data source mapping matrix:
- Patient Name, DOB, MRN: SOQL (Patient/Account object direct fields)
- LastEncounterDate, EncounterCount: Integration Procedure (`GetPatientSummaryIP`) — aggregated from ClinicalEncounter__c
- ActiveCarePlans: Integration Procedure (`GetPatientSummaryIP`) — filtered CarePlan list
- LastCareGapStatus: Integration Procedure (`GetPatientSummaryIP`) — derived field

Action requirements:
- "New Encounter" button: OmniScript Launch action, Type=NewEncounterOmniScript, SubType=Intake, opens in modal, passes PatientId from FlexCard context

Card states: Two states — Active Patient (`Status == 'Active'`, full layout) and Inactive Patient (`Status != 'Active'`, reduced layout showing Name, DOB, MRN only with "Inactive" badge)

**Why it works:** The data source matrix prevents the developer from defaulting to SOQL for IP-required fields. The card states are documented with condition expressions so the developer can wire them directly without a design discovery session.

---

## Example 2: Order Status FlexCard for B2B Commerce Service Console

**Context:** A B2B Commerce org needs a FlexCard on the Order record page showing order status, line items, and an action to initiate a return via an OmniScript.

**Problem:** Requirements don't specify how many card states are needed or what the conditions are. The developer builds a single-state card. Later, stakeholders request a different layout for Cancelled orders. A new state template must be added, requiring reactivation during business hours and a brief outage.

**Solution:**
Requirements document specifies three card states upfront:
- Active Order: `OrderStatus__c IN ('Draft', 'Activated', 'InFulfillment')` — full layout with line items and Return action button
- Completed Order: `OrderStatus__c == 'Completed'` — read-only layout, no action buttons, shows Delivered date
- Cancelled Order: `OrderStatus__c == 'Cancelled'` — read-only layout with "Cancelled" badge, shows Cancellation reason

Build dependency noted: Child FlexCard `OrderLineItemCard` must be activated before parent `OrderStatusCard` can be activated.

**Why it works:** Documenting all card states upfront prevents mid-project state template additions that require reactivation. The child card build dependency ensures the build sequence is planned.

---

## Anti-Pattern: Treating FlexCard Requirements as Standard Report/Dashboard Requirements

**What practitioners do:** They produce a standard "dashboard widget" specification listing data fields and chart types — without specifying data source type, action type, or card state conditions.

**What goes wrong:** The developer cannot build the card without knowing whether the data comes from SOQL, DataRaptor, or Integration Procedure. The developer makes arbitrary choices, often defaulting to SOQL, which fails for aggregated or external API data. Action buttons are added without specifying the action type, leading to Navigation actions being used where OmniScript Launch is required.

**Correct approach:** Use a FlexCard-specific requirements template that specifies: data source type per field, action type per button/trigger, card state conditions, and embedded component build dependencies.
