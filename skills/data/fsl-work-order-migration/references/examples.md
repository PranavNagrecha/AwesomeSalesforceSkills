# Examples — FSL Work Order Migration

## Example 1: Loading Completed Historical Service Appointments

**Context:** A utility company is migrating 3 years of completed field service history from a legacy system. Source records include WorkOrders, ServiceAppointments with Status = "Completed", and AssignedResource records linking them to technicians.

**Problem:** The migration team runs the ServiceAppointment load and gets hundreds of `INVALID_OR_NULL_FOR_RESTRICTED_PICKLIST` errors on the Status field. The `Completed` value is not active in the target org's ServiceAppointment Status picklist because the org was freshly provisioned and only has default values.

**Solution:**
1. Before migration, run this SOQL to find all distinct status values in the source data extract: `SELECT DISTINCT Status FROM source_service_appointment`
2. In Setup > Object Manager > ServiceAppointment > Fields > Status > Edit, activate `Completed`, `Cannot Complete`, and any other historical values found in step 1
3. Confirm activation: `SELECT Id, MasterLabel, ApiName FROM ServiceAppointmentStatus`
4. Re-run the ServiceAppointment load with Data Loader upsert on `Legacy_SA_Id__c`

**Why it works:** ServiceAppointment Status is a restricted picklist — only active values are accepted. Activating values before load eliminates the validation error without requiring any data transformation.

---

## Example 2: Preventing Scheduling Automation During AssignedResource Load

**Context:** A telecom provider migrates 50,000 AssignedResource records representing historical assignments. When they run the load, FSL's optimization engine triggers territory recalculation for each affected service territory, generating 12,000 optimization jobs and taking 14 hours to complete instead of the expected 45 minutes.

**Problem:** FSL's scheduling automation fires on AssignedResource inserts, interpreting each new assignment as a scheduling change requiring evaluation.

**Solution:**
1. Before AssignedResource load, navigate to Setup > Field Service Settings > Scheduling tab
2. Uncheck "Enable Optimization" and "Enable In-Day Optimization" — save
3. Run the AssignedResource bulk load (this now takes 45 minutes)
4. After load and data validation, re-enable both settings
5. If Global Optimization is needed to refresh schedules after migration, run it explicitly for each territory

**Why it works:** Disabling optimization prevents the scheduling engine from processing each insert as a live scheduling event. After re-enabling, optimization runs on-demand rather than automatically for each migrated record.

---

## Anti-Pattern: Loading ProductConsumed Without PricebookEntry

**What practitioners do:** Export products and ProductConsumed records from the source system and load ProductConsumed with only the Product2 external ID, assuming Salesforce will resolve the pricebook relationship automatically.

**What goes wrong:** `ProductConsumed` requires a `PricebookEntryId` field — it cannot be inferred from the Product2 record. If PricebookEntry records don't exist in the target org for the referenced products, every ProductConsumed insert fails with `FIELD_INTEGRITY_EXCEPTION: PricebookEntryId`.

**Correct approach:**
1. Load Product2 records first with External IDs
2. Load PricebookEntry records linking each Product2 to the Standard Pricebook with the `IsActive = true` flag
3. Map `ProductConsumed.PricebookEntryId` to the PricebookEntry's External ID during the ProductConsumed load
4. Validate: `SELECT COUNT() FROM ProductConsumed WHERE PricebookEntryId = null`
