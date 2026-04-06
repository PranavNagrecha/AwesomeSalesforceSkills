# LLM Anti-Patterns — Opportunity Pipeline Migration

Common mistakes AI coding assistants make when generating or advising on Opportunity Pipeline Migration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Direct Insert of OpportunityHistory Records

**What the LLM generates:** A migration step or code snippet that inserts records directly into the `OpportunityHistory` object via Bulk API 2.0 or SOAP API, often framed as "insert historical stage records to preserve pipeline history."

**Why it happens:** LLMs see OpportunityHistory in object reference documentation as a child of Opportunity and infer it is insertable like other child objects (e.g., Contact, OpportunityLineItem). The documentation describes OpportunityHistory's fields in detail, which reinforces the inference that it accepts inserts.

**Correct pattern:**

```
# OpportunityHistory is READ-ONLY — system generated only.
# Do NOT attempt: POST /services/data/v60.0/sobjects/OpportunityHistory

# Correct approach A: Load Task records per stage transition
# WhatId = OpportunityId (cross-ref), Subject = "Historical Stage: <stage>",
# ActivityDate = stage change date, Status = Completed

# Correct approach B: Sequential StageName updates on Opportunity
# Insert Opportunity with earliest stage, then update StageName wave by wave
# Each update auto-generates an OpportunityHistory row
```

**Detection hint:** Flag any migration plan step that references `OpportunityHistory` as a load target, or any code that calls `.insert()` or `.upsert()` on a list of `OpportunityHistory` sObjects.

---

## Anti-Pattern 2: Loading OpportunityLineItems Without Setting Pricebook2Id on Opportunity First

**What the LLM generates:** A migration sequence that loads Opportunities first (without Pricebook2Id), then loads PricebookEntries, then loads OpportunityLineItems — reasoning that Pricebook2Id is optional on Opportunity and can be set later.

**Why it happens:** LLMs correctly identify that Pricebook2Id is not a required field on Opportunity at the API level, and infer that it can be populated in a later update pass. They do not model the constraint that Pricebook2Id must be set before OLI records can reference Price Book Entries.

**Correct pattern:**

```
# WRONG sequence:
# 1. Insert Opportunity (no Pricebook2Id)
# 2. Insert OpportunityLineItem → FAILS: pricebook entry not available

# CORRECT sequence:
# 1. Upsert Product2
# 2. Insert Standard Price Book Entry (required prerequisite)
# 3. Insert Custom Price Book Entry (if using custom price book)
# 4. Upsert Opportunity WITH Pricebook2Id set
# 5. Insert OpportunityLineItem referencing PricebookEntryId from same price book
```

**Detection hint:** Flag migration plans where Opportunity load appears before Price Book Entry load, or where the Opportunity CSV does not include a `Pricebook2Id` column when line items are also being migrated.

---

## Anti-Pattern 3: Inserting Custom Price Book Entries Without Standard Price Book Entry First

**What the LLM generates:** A migration step that inserts PricebookEntry records directly into a custom Price Book for each Product2, skipping the Standard Price Book Entry creation step.

**Why it happens:** LLMs focus on the destination Price Book (the one the business uses) and skip the Standard Price Book Entry as an "unnecessary intermediate step." The Salesforce constraint requiring a Standard Price Book Entry for each product before any custom Price Book Entry can exist is a non-obvious data integrity rule not immediately apparent from API documentation.

**Correct pattern:**

```csv
# Step 1 — Standard Price Book Entry (required, even if $0):
Pricebook2Id,Product2.Legacy_Product_Id__c,UnitPrice,IsActive
<standard_pb_id>,PROD-001,0.00,true

# Step 2 — Custom Price Book Entry (only after Step 1 completes):
Pricebook2Id,Product2.Legacy_Product_Id__c,UnitPrice,IsActive
<custom_pb_id>,PROD-001,4500.00,true
```

**Detection hint:** Flag any migration plan that inserts PricebookEntry records referencing a non-standard Pricebook2Id without a prior step inserting PricebookEntry records referencing the Standard Price Book. Check by querying `SELECT Id FROM Pricebook2 WHERE IsStandard = true`.

---

## Anti-Pattern 4: Treating ForecastCategoryName as a Directly Settable Field

**What the LLM generates:** A migration CSV or Apex insert that includes `ForecastCategoryName` as a field to be set on Opportunity, mapping source CRM forecast categories directly to Salesforce forecast category values.

**Why it happens:** LLMs see `ForecastCategoryName` in the Opportunity object reference fields list and infer it is a settable picklist like `StageName`. In fact, `ForecastCategoryName` is derived automatically from the `StageName`-to-ForecastCategory mapping in the org's Sales Process configuration.

**Correct pattern:**

```
# DO NOT include ForecastCategoryName in the Opportunity load CSV.
# It is derived from StageName via the Sales Process configuration.
# Setting it explicitly is ignored by the API or causes an error.

# Correct: load StageName only
# Salesforce derives ForecastCategoryName from the StageName → ForecastCategory
# mapping in Setup > Opportunities > Sales Processes

# If source forecast categories don't match, update the Sales Process mapping
# in Setup rather than loading ForecastCategoryName directly.
```

**Detection hint:** Flag any Opportunity load CSV or Apex code that includes `ForecastCategoryName` as a field being explicitly set during insert or update.

---

## Anti-Pattern 5: Loading OpportunitySplit Without Verifying Feature Enablement and SplitType Configuration

**What the LLM generates:** A migration step that directly loads OpportunitySplit records via Bulk API 2.0 without checking whether Opportunity Splits is enabled or whether SplitType records are configured and active.

**Why it happens:** LLMs see OpportunitySplit in the object reference and generate standard Bulk API 2.0 load instructions without modeling the prerequisite feature flag and configuration state. The dependency on a Setup flag and on SplitType configuration is not captured in standard object field descriptions.

**Correct pattern:**

```
# Pre-load verification (SOQL — run before attempting split load):
SELECT Id, IsActive FROM OpportunitySplitType WHERE IsActive = true
# Must return at least 1 row. If 0 rows: Splits not enabled or no SplitType configured.

# If 0 rows returned:
# 1. Setup > Opportunity Splits > Enable (IRREVERSIBLE in production — confirm in sandbox first)
# 2. Setup > Opportunity Split Types > Set at least one SplitType to Active

# Only after verification passes:
# Load OpportunityTeamMember first, then OpportunitySplit
# Validate: SplitPercentage values per OpportunityId per SplitTypeId sum to 100
```

**Detection hint:** Flag any OpportunitySplit migration plan that does not include a pre-load verification step for `OpportunitySplitType` records, or that loads splits before loading OpportunityTeamMember records.

---

## Anti-Pattern 6: Advising That StageName Can Be Any Picklist Value Regardless of Record Type

**What the LLM generates:** A mapping table that uses source system stage names as Salesforce StageName values without checking whether those stage names are included in the Sales Process associated with the target Record Type.

**Why it happens:** LLMs know that StageName is a picklist on Opportunity and list global picklist values as valid options. They do not model the constraint that each Record Type is associated with a specific Sales Process that may not include all global stage picklist values.

**Correct pattern:**

```soql
-- Query valid stages for each Sales Process in the org:
SELECT SalesProcessId, StageName, IsClosed, IsWon
FROM OpportunityStage
WHERE IsActive = true
ORDER BY SalesProcessId, SortOrder

-- Cross-reference all unique StageName values in source export
-- against stages in the Sales Process assigned to the target Record Type.
-- Any stage not in the Sales Process must be remapped or added before load.
```

**Detection hint:** Flag migration plans that use source system stage names directly as `StageName` values without a documented stage mapping validation step. Always include a stage audit query as the first verification step in any opportunity migration plan.
