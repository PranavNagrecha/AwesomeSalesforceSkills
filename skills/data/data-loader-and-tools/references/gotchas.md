# Gotchas — Data Loader and Tools

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: "Bulk API Hard Delete" Is a Separate Permission — Not Implied by Modify All Data

**What happens:** A user with "Modify All Data" and "Delete" on an object runs a hard delete operation via Data Loader with Bulk API enabled. Records go to the Recycle Bin instead of being permanently deleted. No error is shown — the operation appears to succeed. The admin discovers days later that 50,000 "deleted" records are still in the Recycle Bin consuming storage.

**When it occurs:** Any time a Data Loader hard-delete operation runs without the "Bulk API Hard Delete" system permission assigned to the running user. The permission must be enabled regardless of whether Bulk API v1 or Bulk API 2.0 is used for the operation.

**How to avoid:** Before any hard-delete operation, confirm the running user has "Bulk API Hard Delete" via a permission set. Assign it via a permission set (not profile) so it can be granted temporarily and audited. After the operation completes, remove it from the permission set if it was granted temporarily. Verify deletion success by running a quick SOQL `SELECT COUNT() FROM RecycleBin` (or `SELECT COUNT() FROM DeletedObject__c` via `queryAll()`) to confirm records are not in the Recycle Bin.

---

## Gotcha 2: Data Import Wizard Silently Truncates Files Larger Than 50,000 Rows

**What happens:** An admin uploads a 75,000-row CSV into Data Import Wizard. The wizard runs successfully and reports "50,000 records processed" with no warning about the remaining 25,000 rows. The admin assumes all records were imported. Missing records are discovered in data quality checks days later.

**When it occurs:** Any time a CSV uploaded to Data Import Wizard contains more than 50,000 data rows (not counting the header). The wizard stops at 50,000 without alerting the user to the truncation.

**How to avoid:** Always check the row count of any CSV before using the wizard: `wc -l file.csv` (macOS/Linux) or open in Excel and check the row count. If the file has more than 50,000 rows (including header → more than 50,001 lines), use Data Loader instead. If the Data Import Wizard is required for business reasons, split the file into chunks of ≤50,000 rows using a CSV splitter.

---

## Gotcha 3: Bulk API 2.0 Does Not Support Certain sObjects

**What happens:** A developer enables Bulk API 2.0 in Data Loader (the recommended setting for large loads) and attempts to load `ContentDocumentLink` records to attach files to records. Data Loader returns `FEATURENOTENABLED` or `INVALIDTYPE` errors. The same operation works fine when Bulk API 2.0 is disabled (reverts to SOAP mode).

**When it occurs:** Bulk API 2.0 does not support all sObjects. Notable unsupported objects include: `ContentDocumentLink`, `UserTerritory2Association`, `FlowInterviewLog`, and some metadata-adjacent sObjects. The Bulk API 2.0 Developer Guide lists supported objects; any object not on the list requires SOAP mode.

**How to avoid:** Before a large Bulk API 2.0 load, verify the target object is listed in the Bulk API 2.0 Developer Guide as supported. If it is not, uncheck "Use Bulk API 2.0" in Data Loader settings and use SOAP mode for that specific operation. For `ContentDocumentLink` specifically, consider using the Files Connect pattern or SOAP API with a standard insert operation.

---

## Gotcha 4: SOAP Mode Fires Triggers and Validation Rules Per Batch of 200

**What happens:** A SOAP-mode Data Loader load of 500,000 records processes successfully in a developer sandbox with clean data. In production, the same load fails with governor limit errors ("Too many SOQL queries: 101") on batch number 47 out of 2,500. The trigger was written assuming bulk-safe patterns but a third-party managed package trigger on the same object is not bulk-safe. Each batch of 200 records shares one governor context.

**When it occurs:** SOAP API processes 200 records per batch, each batch sharing a single Apex transaction context (governor limits). A trigger that performs 1 SOQL query per record will hit the 101 SOQL limit at 101 records within a single 200-record batch. Bulk API 2.0 processes records in parallel chunks with separate governor limits per chunk, making it far more tolerant of imperfectly bulkified triggers.

**How to avoid:** For large loads (>10,000 records), always use Bulk API 2.0 rather than SOAP mode. If SOAP mode is required (e.g., the target object is unsupported by Bulk API 2.0), first audit all Apex triggers on the target object — including managed package triggers — for per-record SOQL/DML patterns. Reduce the SOAP batch size in Data Loader settings (minimum is 1, default is 200) as a temporary mitigation; this reduces throughput significantly but avoids limit failures.

---

## Gotcha 5: Data Loader Version Is Tightly Coupled to API Version — Do Not Run Old Versions

**What happens:** A team runs Data Loader v56.0 (two years old) against a production org that has been upgraded through multiple releases. Certain new standard fields are invisible to the old version because they were added in a later API version. The load proceeds without those fields, missing required field values that were added to validation rules in a later org release. The success.csv shows all records as "success" but validation failures appear only in the error.csv.

**When it occurs:** Data Loader's major version number corresponds to the Salesforce API version (v66.0 = Spring '26 API). Old versions do not expose fields, objects, or picklist values added after their API version. Salesforce explicitly does not support older versions of Data Loader.

**How to avoid:** Always download and use the latest version of Data Loader from https://developer.salesforce.com/tools/data-loader. Update Data Loader after every Salesforce release (3 times per year). When upgrading, copy `config.properties` from the old installation's `configs/` subfolder to the new one to preserve settings, then re-verify all saved field mapping files (`.sdl`) for accuracy.

---

## Gotcha 6: Workbench Session Tokens Expire Quickly — Saved Bookmarks Can Expose Auth Tokens

**What happens:** A developer bookmarks a Workbench URL that includes an active session token in the query string. The bookmark is shared with a team member. If the session has not expired, the recipient gains access to the org under the original developer's identity.

**When it occurs:** Workbench passes session context in URLs in some flows. Bookmarked or shared Workbench URLs with session tokens active can be replayed.

**How to avoid:** Never share Workbench URLs that contain session IDs. Always use the OAuth login flow for Workbench (not username/password). Log out of Workbench explicitly after use rather than closing the browser tab. Prefer Salesforce CLI or VS Code Extensions for shared workflows where URL-based session leakage is a concern.
