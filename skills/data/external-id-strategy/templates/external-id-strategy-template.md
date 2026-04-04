# External ID Strategy — Integration Spec Template

Use this template to document the external ID field design for a Salesforce integration or data migration project. Complete one table row per object that requires external ID support. Commit the completed template to the project repository as the canonical integration spec for this decision area.

---

## Project Context

**Project / Integration name:** (e.g., "ERP-to-Salesforce Nightly Sync")

**Integration pattern:** (Bulk API 2.0 / REST API upsert / Apex Database.upsert / Data Loader)

**Source system(s):** (e.g., SAP ERP, Salesforce Legacy Org, External CRM)

**Primary contact:** (person responsible for ETL key generation logic)

**Date completed:** (YYYY-MM-DD)

---

## Per-Object External ID Field Design

| Salesforce Object | Field API Name | Field Type | Unique | Case-Sensitive | Composite Key? | Composite Formula | Source Field(s) | Notes |
|---|---|---|---|---|---|---|---|---|
| Account | ERP_Customer_Number__c | Number | Yes | N/A | No | — | ERP.CUST_ID | Integer; no case concerns |
| Contact | Source_Composite_Key__c | Text(100) | Yes | No | Yes | `SYSTEMCODE\|SOURCE_CONTACT_ID` | system_code, contact_id | Pipe separator; normalize to uppercase |
| Opportunity | ERP_Opportunity_Id__c | Text(40) | Yes | No | No | — | ERP.OPP_ID | Alphanumeric; normalize to uppercase |
| (add rows as needed) | | | | | | | | |

**Column definitions:**
- **Field API Name** — The exact `__c` API name of the external ID field on this object.
- **Field Type** — Text(length), Number(precision, scale), or Email.
- **Unique** — Must be Yes for any field used as an upsert key.
- **Case-Sensitive** — For Text fields: Yes (case-sensitive option checked) or No (default case-insensitive). N/A for Number/Email.
- **Composite Key?** — Yes if the external ID value is assembled from multiple source fields in the ETL layer.
- **Composite Formula** — Exact formula used to construct the composite key. Leave blank if not composite.
- **Source Field(s)** — The source system field name(s) that contribute to this external ID value.

---

## Parent-Child Relationship Resolution

For each parent-child object pair where children reference parents by external ID (rather than by Salesforce `Id`):

| Child Object | Lookup/Master-Detail Field | Parent Object | Parent External ID Field | CSV Column Header Syntax | Load Order |
|---|---|---|---|---|---|
| Contact | AccountId (standard) | Account | ERP_Customer_Number__c | `Account.ERP_Customer_Number__c` | Accounts first |
| Opportunity | AccountId (standard) | Account | ERP_Customer_Number__c | `Account.ERP_Customer_Number__c` | Accounts first |
| (add rows as needed) | | | | | |

---

## Composite Key Formulas

For each object using a composite key, document the formula completely:

### Object: Contact — `Source_Composite_Key__c`

**Formula:** `{SYSTEM_CODE}|{SOURCE_CONTACT_ID}`

**Separator:** Pipe (`|`) — verified not to appear in either component field.

**Component fields:**
- `SYSTEM_CODE` — two- to six-character uppercase code identifying the source system (e.g., `ERP`, `LEGACY`, `ACQA`). Always uppercase.
- `SOURCE_CONTACT_ID` — the source system's contact identifier. Alphanumeric. Normalize to uppercase before concatenation.

**Null handling:** If either component is null, the ETL job must reject the row and log a data quality error. Do not load a record with a null composite key component.

**Maximum length:** Validated at 100 characters (field length). ETL must error if a generated key exceeds this limit.

**Example values:**
- `ERP|10042`
- `LEGACY|A-9871`
- `ACQA|1001`
- `ACQB|1001`

---

## ETL Normalization Rules

Rules that must be applied in the ETL layer before staging data for any external ID field:

| Object | Field | Normalization Rule |
|---|---|---|
| Contact | Source_Composite_Key__c | Uppercase all characters; trim leading/trailing whitespace from each component before concatenation |
| Opportunity | ERP_Opportunity_Id__c | Uppercase; strip any leading zeros only if the source system does not use zero-padded IDs |
| (add rows as needed) | | |

---

## Load Ordering

List the required order for loading objects when parent-child relationship resolution is used:

1. (Parent object 1, e.g., Account)
2. (Parent object 2, if applicable, e.g., custom object that is parent to another)
3. (Child object 1, e.g., Contact — depends on Account)
4. (Child object 2, e.g., Opportunity — depends on Account)
5. (Grandchild objects, if applicable)

**Validation gate between parent and child loads:** After each parent job completes, retrieve the job error file and confirm `numberRecordsFailed = 0` (or an accepted threshold). Do not submit child jobs if parent errors exceed the threshold.

---

## Review Checklist

Use this checklist when reviewing the completed strategy before the first production load:

- [ ] All external ID fields are created in production org with `External ID = true` and `Unique = true`
- [ ] For Text fields: case-sensitivity setting confirmed and matches ETL normalization rules
- [ ] Composite key formulas reviewed and signed off by integration lead
- [ ] ETL normalization rules implemented and unit-tested with representative source data samples
- [ ] No existing duplicate external ID values on any target object (verified by SOQL GROUP BY query)
- [ ] Parent-child load ordering enforced in the pipeline; validation gate between parent and child jobs
- [ ] Relationship column syntax validated against a small test batch before full load
- [ ] Field API names match exactly across: this spec, ETL code, Bulk API job configs, and any Apex/Flow references
- [ ] Strategy template committed to project repository and reviewed by at least one other team member

---

## Deviations From Standard Pattern

Record any intentional deviations from the recommended patterns in SKILL.md and the reason:

| Object | Deviation | Reason | Approved By |
|---|---|---|---|
| (e.g., Custom_Object__c) | Non-unique external ID used for correlation only, not upsert | Source system has non-unique keys; upsert is performed by a separate matching process | (name, date) |
