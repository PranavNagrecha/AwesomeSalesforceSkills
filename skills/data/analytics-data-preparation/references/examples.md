# Examples — Analytics Data Preparation (XMD Metadata)

## Example 1: PATCH Main XMD to Add Business-Friendly Field Labels

**Context:** A CRM Analytics developer built a recipe extracting from custom objects. Field API names like `Acct_Tier__c` and `Prod_Cat__c` appeared in dashboard filter dropdowns.

**Problem:** Business users could not interpret these labels. The system XMD used the raw API names. The team needed "Account Tier" and "Product Category" as displayed labels.

**Solution:**
1. `GET /wave/datasets/{datasetId}/xmds/main` — backed up the response.
2. Identified both fields in the `dimensions` array of the system XMD.
3. Constructed PATCH payload:
```json
{
  "dimensions": [
    {"field": "Acct_Tier__c", "label": "Account Tier"},
    {"field": "Prod_Cat__c", "label": "Product Category"}
  ]
}
```
4. `PATCH /wave/datasets/{datasetId}/xmds/main` — HTTP 200.
5. Verified labels in an Analytics Studio lens.

**Why it works:** PATCH is additive-merge. Only the `label` properties changed. All other dimension attributes (format, aliases) were preserved.

---

## Example 2: CSV External Augmentation for Territory Mapping

**Context:** A CRM Analytics admin needed to enrich opportunity data with territory-to-region mapping that existed only as a CSV file managed by the sales operations team.

**Problem:** The territory-region mapping was not in any Salesforce object. The existing recipe could not join on territory because no Salesforce object held the mapping.

**Solution:**
1. Uploaded the mapping CSV to Salesforce Files (ContentDocument).
2. In Analytics Studio, created a new recipe and added a Files node selecting the uploaded CSV.
3. Added an Augment node joining the Files node to the primary Opportunity data node on the `Territory__c` field.
4. Selected left outer join to preserve all opportunities even where territory mapping was absent.
5. Ran the recipe and verified `RegionName` appeared as a new dimension in the output dataset.

**Why it works:** The Files node in CRM Analytics recipes accepts CSV files from Salesforce Files. The Augment node performs the join at recipe execution time. The output dataset includes the enriched field.
