# Gotchas — Sales Cloud Integration Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Converted Leads Are Read-Only via API

**What happens:** After Lead conversion, the Lead record still exists and is queryable, but any DML update via API returns a success response with no actual field changes, or throws an error depending on the API version and fields touched. External systems that continue syncing to the Lead ID see no errors but data stops flowing.

**When it occurs:** Any integration that syncs Leads from a marketing automation platform and does not handle the conversion lifecycle. The problem surfaces days or weeks later when marketing notices engagement data is stale.

**How to avoid:** Subscribe to Lead conversion events (trigger on `IsConverted` flip or Change Data Capture). Immediately notify the external system of the new Contact ID. Post-conversion, redirect all syncs to the Contact object.

---

## Gotcha 2: External ID Upsert with Null Values Creates Duplicates

**What happens:** If an External ID field value is null or empty string on the record being upserted, Salesforce treats it as a new record every time. This creates duplicate records on each sync run.

**When it occurs:** When the source system has records that lack the cross-reference ID (e.g., Accounts created manually in Salesforce that have no ERP ID yet). The next inbound ERP sync with a null External ID inserts a new Account instead of matching.

**How to avoid:** Filter out records with null or empty External ID values before upserting. For records created in Salesforce that do not yet have an external ID, use a separate outbound sync to register them in the external system first, then backfill the External ID.

---

## Gotcha 3: Order Activation Makes Most Fields Read-Only

**What happens:** Once an Order record's `StatusCode` is set to "Activated," Salesforce locks nearly all fields. Attempting to update locked fields via API returns `FIELD_NOT_UPDATABLE_FOR_ACTIVATED_ORDER`. This is a platform-level restriction, not a validation rule.

**When it occurs:** The ERP system sends an order update (e.g., revised shipping date) back to Salesforce after the Order was already activated. The integration fails because the field is locked.

**How to avoid:** Keep Orders in "Draft" status until the ERP confirms receipt. Only then activate the Order. For post-activation updates from ERP, write to custom fields on a related child object (e.g., `Order_ERP_Status__c` on a custom `Order_Fulfillment__c` object) rather than the Order itself.

---

## Gotcha 4: PricebookEntry Requires Standard Pricebook Entry First

**What happens:** Creating a PricebookEntry in a custom Pricebook fails if the Product2 does not already have an entry in the standard Pricebook. The error message (`FIELD_INTEGRITY_EXCEPTION: field integrity exception: PricebookEntryId`) is misleading and does not mention the standard Pricebook requirement.

**When it occurs:** Product catalog syncs from ERP that create Product2 records and custom PricebookEntry records in a single batch, skipping the standard Pricebook.

**How to avoid:** Always create the standard Pricebook entry first. In bulk sync jobs, process in two passes: (1) upsert Product2 and standard PricebookEntry, (2) upsert custom PricebookEntries.

---

## Gotcha 5: Bidirectional Triggers Cause Infinite Update Loops

**What happens:** An inbound integration updates an Account. This fires an after-update trigger that sends the Account outbound. The external system receives the update, applies it, and sends it back. The cycle repeats until governor limits kill the transaction or the integration queue overflows.

**When it occurs:** Any bidirectional sync where both inbound and outbound paths share the same trigger or automation, and there is no circuit breaker.

**How to avoid:** Use a static Boolean flag (`IntegrationContext.isInbound`) set to true before inbound DML and checked in the outbound trigger. Alternatively, assign a dedicated integration user and skip outbound processing when `UserInfo.getUserId()` matches the integration user.

---

## Gotcha 6: Campaign Member Status Values Must Be Pre-Created

**What happens:** Adding a CampaignMember with a Status value that does not exist on the Campaign's status picklist throws `INVALID_STATUS`. Marketing automation platforms that use custom statuses (e.g., "MQL Sent", "Webinar Attended") fail on the first sync.

**When it occurs:** When a marketing platform creates CampaignMembers with statuses that were not previously configured on the Salesforce Campaign record.

**How to avoid:** Pre-create all expected Campaign Member Status values on the Campaign before syncing members. Alternatively, use a before-insert trigger or Flow that checks for the status value and creates it if missing (via CampaignMemberStatus insert).
