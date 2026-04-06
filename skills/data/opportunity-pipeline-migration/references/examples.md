# Examples — Opportunity Pipeline Migration

## Example 1: Migrating Opportunities with Product Line Items from a Custom Price Book

**Context:** A B2B manufacturing company is migrating 12,000 Opportunity records from Microsoft Dynamics 365 to Salesforce. Each Opportunity has between 1 and 15 product line items. The org uses a custom "Distributor Price Book" for all sales. The migration team initially attempts to load OpportunityLineItems immediately after loading Opportunities and receives batch failures.

**Problem:** The team loaded Opportunities without setting `Pricebook2Id`, then attempted to insert OpportunityLineItems referencing PricebookEntry records from the custom Price Book. Both steps fail: the Opportunity load succeeds (Pricebook2Id is not required to insert an Opportunity), but the OpportunityLineItem insert fails with `FIELD_INTEGRITY_EXCEPTION: pricebook entry does not exist or is not available` because the Opportunity has no Price Book assigned and thus cannot accept line items.

**Solution:**

Load sequence and CSV structure:

```
Step 1 — Product2 upsert CSV (external ID: Legacy_Product_Id__c):
Legacy_Product_Id__c,Name,ProductCode,IsActive
DYN-PROD-001,Hydraulic Pump 40L,HP-40L,true
DYN-PROD-002,Control Valve Assembly,CVA-200,true

Step 2 — Standard Price Book Entry insert CSV (cross-reference Product2):
Pricebook2Id,Product2.Legacy_Product_Id__c,UnitPrice,IsActive
<standard_pricebook_id>,DYN-PROD-001,0.00,true
<standard_pricebook_id>,DYN-PROD-002,0.00,true

Step 3 — Custom Price Book Entry insert CSV:
Pricebook2Id,Product2.Legacy_Product_Id__c,UnitPrice,IsActive
<distributor_pricebook_id>,DYN-PROD-001,4250.00,true
<distributor_pricebook_id>,DYN-PROD-002,875.00,true

Step 4 — Opportunity upsert CSV (note: Pricebook2Id populated):
Legacy_Opportunity_Id__c,Name,Account.Legacy_Account_Id__c,StageName,Amount,CloseDate,Pricebook2Id
DYN-OPP-10045,Northwest Industrial Q2,ACC-0091,Closed Won,18375.00,2024-09-30,<distributor_pricebook_id>

Step 5 — OpportunityLineItem insert CSV:
Opportunity.Legacy_Opportunity_Id__c,PricebookEntry.Product2.Legacy_Product_Id__c,Quantity,UnitPrice,TotalPrice
DYN-OPP-10045,DYN-PROD-001,3,4250.00,12750.00
DYN-OPP-10045,DYN-PROD-002,6,875.00,5250.00
```

**Why it works:** Setting `Pricebook2Id` on the Opportunity before loading line items unlocks the OLI insert. Using cross-reference notation (`Product2.Legacy_Product_Id__c`) in the PricebookEntry and OLI CSVs eliminates the need to pre-resolve Salesforce record IDs, making the load idempotent and re-runnable.

---

## Example 2: Preserving Stage History with Task Records

**Context:** A SaaS company is migrating 8,000 open Opportunities from HubSpot to Salesforce. HubSpot exports a deal stage history CSV showing every stage transition with the date and the rep who made the change. Sales leadership wants the stage history preserved so they can analyze pipeline progression patterns. The migration engineer attempts to insert OpportunityHistory records and receives an error.

**Problem:** `sObject type 'OpportunityHistory' is not supported` or `INVALID_TYPE_FOR_OPERATION: entity type Opportunity History does not support create`. The engineer misreads this as a permission error and escalates to Salesforce Support. Support confirms it is a platform constraint — the object is system-managed and read-only via API.

**Solution:**

Load stage history as completed Task records, one Task per stage transition:

```
Stage history source CSV (from HubSpot export):
deal_id,stage_name,changed_at,changed_by_email
HS-OPP-5001,Appointment Scheduled,2024-03-10,rep1@company.com
HS-OPP-5001,Qualified to Buy,2024-04-02,rep1@company.com
HS-OPP-5001,Presentation Scheduled,2024-04-18,rep2@company.com
HS-OPP-5001,Proposal/Price Quote,2024-05-07,rep2@company.com

Transformed to Task insert CSV:
WhatId (via cross-ref),Subject,ActivityDate,Status,Description,OwnerId (via cross-ref)
Opportunity.Legacy_Opportunity_Id__c=HS-OPP-5001,Historical Stage: Appointment Scheduled,2024-03-10,Completed,Stage as of 2024-03-10 (migrated from HubSpot),User.Username=rep1@company.com
Opportunity.Legacy_Opportunity_Id__c=HS-OPP-5001,Historical Stage: Qualified to Buy,2024-04-02,Completed,Stage as of 2024-04-02 (migrated from HubSpot),User.Username=rep1@company.com
```

After loading Tasks, the Opportunity record shows stage history context in the Activity Timeline. A custom report on Tasks filtered by `Subject LIKE 'Historical Stage:%'` reconstructs the full pipeline progression.

**Why it works:** Task records are insertable via Bulk API 2.0, support cross-reference lookups to Opportunity via `WhatId`, preserve the date and responsible user, and are reportable. This is the recommended workaround for OpportunityHistory's read-only constraint.

---

## Example 3: Enabling and Loading OpportunitySplits

**Context:** A financial services firm migrates 4,500 Opportunities with revenue splits already defined in the source CRM. Two team members share revenue credit on most deals. The migration team skips the "enable Splits" step and attempts to load OpportunitySplit records.

**Problem:** The OpportunitySplit object is not visible in the API schema because Opportunity Splits is not enabled. The load job fails before it begins: `entity type OpportunitySplit does not exist or cannot be described`.

**Solution:**

Pre-load configuration checklist and load CSV:

```
1. Setup > Opportunity Splits > Enable Opportunity Splits
   (Confirm: checkbox checked. IRREVERSIBLE in production — verify in sandbox first.)

2. Configure SplitType:
   Setup > Opportunity Split Types > Ensure "Revenue Split" is Active
   Query: SELECT Id, MasterLabel FROM OpportunitySplitType WHERE IsActive = true
   Note the SplitType Id for use in the CSV.

3. Load OpportunityTeamMember first:
   Opportunity.Legacy_Opportunity_Id__c,User.Username,TeamMemberRole,OpportunityAccessLevel
   OPP-SF-00123,ae1@company.com,Account Executive,Edit
   OPP-SF-00123,se1@company.com,Solution Engineer,Read

4. Load OpportunitySplit:
   Opportunity.Legacy_Opportunity_Id__c,SplitOwner.Username,SplitTypeId,SplitPercentage
   OPP-SF-00123,ae1@company.com,<revenue_split_type_id>,70
   OPP-SF-00123,se1@company.com,<revenue_split_type_id>,30
```

**Why it works:** Enabling Splits before the load makes the OpportunitySplit object available via API. Loading OpportunityTeamMember before OpportunitySplit ensures the user-opportunity relationship is established. Split percentages summing to 100 satisfies the org's split validation.

---

## Anti-Pattern: Inserting Opportunities Without Pricebook2Id When Line Items Are Required

**What practitioners do:** Load Opportunities first without setting `Pricebook2Id` (since the field is optional on the Opportunity itself), then attempt to load OpportunityLineItems referencing the correct Price Book Entries.

**What goes wrong:** The OpportunityLineItem insert fails for every row with `FIELD_INTEGRITY_EXCEPTION: pricebook entry does not exist or is not available`. Even though the PricebookEntry records exist and are active, Salesforce cannot associate them with an Opportunity that has no Price Book assigned. The error message is misleading — it implies the PricebookEntry is missing, but the real issue is the missing `Pricebook2Id` on the Opportunity.

**Correct approach:** Always set `Pricebook2Id` on Opportunity before loading OpportunityLineItems. If the Opportunity has already been loaded without a `Pricebook2Id`, issue an update operation to set it before proceeding to the line item load. Confirm the Price Book ID matches the Price Book referenced by the PricebookEntries being loaded.
