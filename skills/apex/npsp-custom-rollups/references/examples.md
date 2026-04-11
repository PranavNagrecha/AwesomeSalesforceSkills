# Examples — NPSP Custom Rollups (CRLP)

## Example 1: Creating a Fiscal Year Gift Total Rollup With a Filter Group

**Context:** A nonprofit org tracks an annual fundraising campaign and needs a Contact-level field showing total gifts closed in the current fiscal year. The org uses a non-standard fiscal year (July 1 – June 30). Standard NPSP rollup fields use calendar year; CRLP supports fiscal year natively.

**Problem:** Without a custom Rollup Definition using the fiscal year date range setting, the org falls back on workarounds like formula fields that compute fiscal year boundaries or scheduled Apex that queries and writes values directly. These break during daylight saving transitions or when the NPSP batch job also writes to the same field.

**Solution:**

```
1. NPSP Settings > Customizable Rollups > Filter Groups > New

   Filter Group Name: FY Gifts — Unrestricted        (38 chars — under 40 limit)
   Filter Row 1:
     Object: Opportunity
     Field: Type
     Operator: Equals
     Value: Donation

2. NPSP Settings > Customizable Rollups > Rollup Definitions > New

   Label: Contact FY Total Giving
   Summary Object: Contact
   Detail Object: Opportunity
   Aggregate Operation: Sum
   Amount Field: Amount
   Date Field: Close Date
   Date Range: Current Fiscal Year
   Store Field: npsp__TotalOppAmountThisYear__c (or a custom currency field)
   Filter Group: FY Gifts — Unrestricted

3. Save the Rollup Definition.

4. NPSP Settings > Batch Processing > Recalculate Rollups (Full)
   Wait for the batch to complete. Verify totals on 5–10 sample Contacts.

5. Schedule Incremental recalculation to run nightly via NPSP Settings > Batch Processing.
```

**Why it works:** CRLP's fiscal year date range setting reads the org's defined fiscal year boundaries rather than calendar year boundaries. The filter group restricts the aggregation to donation-type opportunities only, so test records or pledges of a different type are excluded cleanly.

---

## Example 2: Deploying CRLP Definitions from Sandbox to Production via SFDX

**Context:** A consultant builds and validates 12 custom Rollup Definitions and 4 Filter Groups in a full-copy sandbox. Production needs the same definitions without manual recreation.

**Problem:** Manually recreating Rollup Definitions in production introduces transcription errors, cannot be reviewed in a pull request, and creates version drift between environments. CRLP definitions that are misconfigured in production can produce incorrect gift totals across thousands of records before anyone notices.

**Solution:**

```bash
# 1. From the sandbox, retrieve CRLP custom metadata using SFDX
sfdx force:source:retrieve \
  --metadata "CustomMetadata:Customizable_Rollup__mdt,CustomMetadata:Customizable_Rollup_Filter_Group__mdt,CustomMetadata:Customizable_Rollup_Filter_Rules__mdt" \
  --targetusername sandbox_alias

# 2. Inspect the retrieved files under force-app/main/default/customMetadata/
# Files will be named like:
#   Customizable_Rollup__mdt.Contact_FY_Total_Giving.md-meta.xml
#   Customizable_Rollup_Filter_Group__mdt.FY_Gifts_Unrestricted.md-meta.xml

# 3. Add to version control and open a pull request for review.

# 4. Deploy to production
sfdx force:source:deploy \
  --metadata "CustomMetadata:Customizable_Rollup__mdt,CustomMetadata:Customizable_Rollup_Filter_Group__mdt,CustomMetadata:Customizable_Rollup_Filter_Rules__mdt" \
  --targetusername production_alias

# 5. After deploy, trigger Full recalculation in production
# NPSP Settings > Batch Processing > Recalculate Rollups > Full
```

**Why it works:** CRLP configuration is stored as custom metadata records, which are fully Metadata API-compatible. SFDX retrieves them as human-readable XML files that can be diffed, reviewed, and deployed like any other metadata. The Full recalculation after deploy is mandatory — deployed definitions do not auto-populate existing records.

---

## Example 3 (Anti-Pattern): Assuming Rollup Fields Are Current Without Running a Batch

**What practitioners do:** After enabling CRLP and creating rollup definitions, they query or display rollup fields immediately on existing records and assume the values are correct. They also build flows or reports that read rollup fields without considering recency.

**What goes wrong:** CRLP rollup fields on existing records remain at their pre-migration values (often zero or null) until a Full recalculation batch completes. If a report is delivered to leadership before the batch runs, gift totals appear drastically understated. Flows that gate on a rollup threshold (e.g., "if Total Giving > 1000, send acknowledgment") will silently misfire.

**Correct approach:** Always run a Full recalculation batch immediately after enabling CRLP, after creating or modifying rollup definitions, and after any bulk data load. Verify the batch completed without errors under NPSP Settings > Batch Processing before treating rollup values as reliable.
