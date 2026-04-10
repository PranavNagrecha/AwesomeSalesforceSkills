# LLM Anti-Patterns — FSL Work Order Migration

Common mistakes AI coding assistants make when generating or advising on FSL Work Order Migration.

## Anti-Pattern 1: Wrong Insert Order — ServiceAppointment Before WorkOrder

**What the LLM generates:** Migration sequence that loads ServiceAppointment records before WorkOrder records, or combines them in a single mixed batch.

**Why it happens:** LLMs treat FSL objects like independent flat entities without modeling the required parent-child lookup chain.

**Correct pattern:** Strict hierarchy: Account/Contact/Asset → WorkOrder → WorkOrderLineItem → ServiceAppointment → AssignedResource → ProductConsumed. Each step must complete with zero errors before proceeding.

**Detection hint:** Any migration sequence that loads ServiceAppointment in the same step as or before WorkOrder is wrong.

---

## Anti-Pattern 2: Ignoring Status Picklist Activation

**What the LLM generates:** Migration steps that load ServiceAppointment records with Status = "Completed" without first verifying and activating the Completed value in the target org.

**Why it happens:** LLMs assume picklist values are globally available and don't model the org-specific picklist activation requirement for restricted picklists.

**Correct pattern:** Before loading any ServiceAppointment records, extract all distinct Status values from source data and confirm each is active in the target org's ServiceAppointment Status picklist. Activate missing values in Setup before the load.

**Detection hint:** Any migration plan that loads ServiceAppointment records without a status picklist validation step is incomplete.

---

## Anti-Pattern 3: Recommending Plain Insert Without External IDs

**What the LLM generates:** Data Loader insert (not upsert) commands without External ID field setup on FSL objects.

**Why it happens:** LLMs default to the simpler insert operation without modeling the re-run requirements of a migration.

**Correct pattern:** Add `Legacy_Id__c` External ID fields to WorkOrder, WorkOrderLineItem, ServiceAppointment, AssignedResource, and ProductConsumed. Use upsert with the External ID as the match key for all FSL object loads.

**Detection hint:** Any FSL migration procedure that doesn't mention External IDs or uses plain insert without a duplicate prevention strategy is risky.

---

## Anti-Pattern 4: Loading ProductConsumed Without PricebookEntry

**What the LLM generates:** ProductConsumed load mapping that references only `Product2Id`, assuming Salesforce resolves the pricebook relationship automatically.

**Why it happens:** LLMs know ProductConsumed is related to Product2 but don't always model the PricebookEntry intermediary that is required.

**Correct pattern:** Pre-load PricebookEntry records for all products. Map `ProductConsumed.PricebookEntryId` to the PricebookEntry External ID, not the Product2 ID.

**Detection hint:** Any ProductConsumed load that references `Product2Id` or `Product2.Legacy_Id__c` without a separate PricebookEntry load step is missing a required dependency.

---

## Anti-Pattern 5: Not Disabling Scheduling Automation Before AssignedResource Load

**What the LLM generates:** AssignedResource bulk load steps without any mention of disabling FSL optimization settings.

**Why it happens:** LLMs don't model the side effects of FSL's scheduling automation firing on record inserts.

**Correct pattern:** Disable "Enable Optimization" and "Enable In-Day Optimization" in Setup > Field Service Settings > Scheduling before loading AssignedResource records. Re-enable after migration validation.

**Detection hint:** Any AssignedResource bulk load procedure that doesn't include a step to disable FSL optimization settings will likely cause performance problems or data integrity issues.
