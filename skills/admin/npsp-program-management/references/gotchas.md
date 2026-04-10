# Gotchas — NPSP Program Management Module (PMM)

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Field-Set Required Flag Does Not Enforce Saves in Bulk Service Delivery

**What happens:** Fields marked Required in the Bulk_Service_Deliveries_Fields field set show a red asterisk in the bulk entry UI, but the save operation succeeds even if those fields are left blank. ServiceDelivery__c records are created with null values for "required" fields.

**When it occurs:** Any time a staff member uses the Bulk Service Deliveries quick action and leaves a field blank that the admin intended to be required. The issue is not visible during setup — it only manifests when staff enter the first real delivery records.

**How to avoid:** Treat the field-set Required flag as a UI decoration only. For any field that must contain a value, create a validation rule on ServiceDelivery__c with an ISBLANK() or equivalent condition. Test validation rules from within the Bulk Service Deliveries action specifically — some validation rules behave differently in quick actions vs. record-edit pages.

---

## Gotcha 2: Bulk Service Delivery Cascade Filtering Breaks If Field Order Is Wrong

**What happens:** The Bulk Service Deliveries action displays all Program Engagements across all programs (not filtered to the selected client) and all Services across all programs (not filtered to the selected program) when the field-set order is incorrect. No error message appears — filtering simply does not work.

**When it occurs:** When Client is not in position 1, or Program Engagement is not in position 2, or Service is not in position 3 in the Bulk_Service_Deliveries_Fields field set. This frequently happens when an admin adds a new field to the set and accidentally displaces one of the first three required fields via drag-and-drop.

**How to avoid:** After any change to the Bulk_Service_Deliveries_Fields field set, always manually verify the order: (1) Client, (2) Program Engagement, (3) Service. Write this into the org's admin runbook. If additional fields must appear early in the table for usability reasons, consult PMM release notes — the ordering requirement may change between package versions.

---

## Gotcha 3: Concurrent Bulk Saves Cause UNABLE_TO_LOCK_ROW Errors

**What happens:** When two or more staff members submit bulk service delivery batches at the same time, Salesforce's row-locking mechanism causes UNABLE_TO_LOCK_ROW errors on some of the records being inserted. The bulk save partially succeeds — some rows insert cleanly, and others fail silently or show an inline error in the action UI. Staff may not notice which rows failed.

**When it occurs:** In any org where multiple staff enter service deliveries simultaneously — common at the end of a program session when all volunteers submit attendance at once. The collision risk is higher when deliveries share the same parent Program Engagement or when the same Contact lookup is used in multiple simultaneous submits.

**How to avoid:** Train staff to stagger submission timing by a few minutes after each session. For high-volume orgs, consider replacing the PMM bulk action with a custom Flow-based entry screen that batches inserts asynchronously. Monitor the ServiceDelivery__c record count after each bulk entry session to confirm all expected rows were created.

---

## Gotcha 4: Deleting a ProgramEngagement__c Does Not Cascade-Delete Related ServiceDelivery__c Records

**What happens:** ServiceDelivery__c has a lookup relationship (not master-detail) to ProgramEngagement__c. Deleting a ProgramEngagement__c record leaves orphaned ServiceDelivery__c records with a null ProgramEngagement__c value. These records still exist and count in aggregate reports but lack program context, making them unfilterable by program.

**When it occurs:** When an admin bulk-deletes ProgramEngagement__c records (e.g., during a data cleanup or re-enrollment migration) without first deleting or reassigning the related ServiceDelivery__c records. Also occurs when using Data Loader to delete engagements directly.

**How to avoid:** Before deleting any ProgramEngagement__c records, query for related ServiceDelivery__c records (WHERE ProgramEngagement__c = [the ID]) and decide whether to delete them, reassign them to a new engagement, or archive them. Add a pre-delete Flow or trigger check if the org frequently manages engagement lifecycles.

---

## Gotcha 5: PMM Objects Are Namespaced — Direct API Calls Must Use pmdm__ Prefix

**What happens:** Code, Flow, or external integrations that reference PMM fields without the pmdm__ namespace prefix fail with field-not-found errors. This is common when copying SOQL from a Community post or internal documentation that omits the namespace.

**When it occurs:** In Apex triggers, Flow Get Records/Create Records elements, Data Loader field mappings, API integrations, and report formula fields that reference PMM custom fields without the pmdm__ prefix. Affects fields like pmdm__Quantity__c, pmdm__DeliveryDate__c, pmdm__Service__c, pmdm__ProgramEngagement__c, etc.

**How to avoid:** Always query the actual API names from Setup > Object Manager when building integrations or automation against PMM objects. Use SOQL like `SELECT pmdm__Quantity__c, pmdm__DeliveryDate__c FROM pmdm__ServiceDelivery__c` — every field and the object itself carries the pmdm__ prefix. When building validation rule formulas, use the field API name shown in the formula editor, which will include the namespace automatically.
