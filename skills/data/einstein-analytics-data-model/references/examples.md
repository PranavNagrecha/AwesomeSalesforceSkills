# Examples — Einstein Analytics Data Model (XMD)

## Example 1: Renaming Cryptic Field Labels via Main XMD

**Context:** A CRM Analytics admin built a dataflow extracting from Opportunity and Account. Field API names like `Owner.UserRole.Name` appeared in dashboards with raw API names — unusable for business users.

**Problem:** Business users could not interpret field labels in chart axes and filter dropdowns.

**Solution:**
1. `GET /wave/datasets/{id}/xmds/main` — saved response as backup.
2. Constructed minimal PATCH payload:
```json
{
  "dimensions": [
    {"field": "Owner.UserRole.Name", "label": "Rep Role"},
    {"field": "Account.Industry", "label": "Industry Segment"}
  ]
}
```
3. `PATCH /wave/datasets/{id}/xmds/main` — HTTP 200 confirmed.
4. Verified labels in Analytics Studio lens.

**Why it works:** Main XMD PATCH is an additive merge — only the `label` property was modified; all other XMD properties preserved. The change applies to all users viewing the dataset.

---

## Example 2: Diagnosing Silent Schema Drift After Recipe Refresh

**Context:** An analyst noticed `Annual_Revenue_Band__c` disappeared from filter options after a recipe run.

**Problem:** During a recipe update, the field was accidentally omitted from the output schema. Main XMD still contained the label customization but system XMD for the new dataset version no longer included the field. Dashboard silently lost the filter.

**Solution:**
1. Compared dataset versions: `GET /wave/datasets/{id}/versions`.
2. Confirmed the field was absent from the new version's system XMD.
3. Updated the recipe to re-include the field and re-ran it.
4. Verified the field reappeared in the new system XMD; main XMD label persisted.

**Why it works:** Dataset versioning creates a new system XMD per version but preserves main XMD at the dataset level. Understanding this separation is key to diagnosing schema drift.
