# Examples — Data Cloud Data Model Objects

## Example 1: Identity Resolution Fails Because Mandatory DMOs Are Not Mapped

**Scenario:** A retail company ingested purchase transaction data and web event data into Data Cloud. After running identity resolution, the unified profile count was zero with no matching errors reported.

**Problem:** Neither data stream mapped fields to the five mandatory identity resolution DMOs (Individual, Party Identification, Contact Point Email, Contact Point Phone, Contact Point Address). Identity resolution operates exclusively on these five DMOs — data not mapped to them is invisible to the matching ruleset.

**Solution:**
1. Review data stream field mappings for each source
2. Map customer identifier fields to mandatory DMOs: email → Contact Point Email, phone → Contact Point Phone, customer ID → Party Identification, name → Individual
3. Re-run identity resolution after mappings are configured

**Why this works:** Identity resolution can only match records present in the mandatory DMOs. Any source data not mapped to these DMOs cannot contribute to unified profiles.

---

## Example 2: SOQL Query Against a DMO Returns No Results

**Scenario:** A developer queried Data Cloud customer data with SOQL: `SELECT Id FROM Individual__c WHERE CreatedDate = TODAY`. The query returned 0 rows despite 2 million Individual DMO records.

**Problem:** DMOs are not Salesforce CRM objects. They reside in the Data Cloud data lake, not the CRM object model, and cannot be queried with SOQL. The Data Cloud Query API (ANSI SQL) must be used.

**Solution:**
```sql
-- Data Cloud Query API (ANSI SQL via POST /ssot/queryapis/queryjobs)
SELECT ssot__Id__c, ssot__Email__c 
FROM ssot__Individual__dlm 
WHERE ssot__CreatedDate__c = CURRENT_DATE
```

**Why this works:** DMOs are columnar store objects. Access requires the Data Cloud Query API with ANSI SQL, not SOQL.

---

## Example 3: XMD PATCH Returns 403 — Wrong XMD Type Targeted

**Scenario:** A data analyst tried to rename a field label via REST API: `PATCH .../xmds/system`. The request returned HTTP 403.

**Problem:** System XMD is platform-generated and immutable. It cannot be modified. The correct target for field label customization is Main XMD.

**Solution:**
1. Retrieve Main XMD: `GET .../wave/datasets/{id}/xmds/main`
2. Modify the `fields` array: update `label` for the target field
3. Submit: `PATCH .../wave/datasets/{id}/xmds/main` with modified JSON body
4. Validate in CRM Analytics dataset viewer

**Why this works:** Main XMD is the org-level customizable tier. Targeting `main` instead of `system` allows field customization without errors.
