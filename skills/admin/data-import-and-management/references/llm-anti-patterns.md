# LLM Anti-Patterns — Data Import and Management

Common mistakes AI coding assistants make when generating or advising on Salesforce data imports, migrations, and bulk operations.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Data Import Wizard for large data volumes

**What the LLM generates:** "Use the Data Import Wizard to load your 500,000 account records."

**Why it happens:** LLMs default to the most user-friendly tool. The Data Import Wizard has a 50,000 record limit per operation and only supports Accounts, Contacts, Leads, Solutions, and custom objects. For large volumes or objects not supported by the wizard, Data Loader or the Bulk API is required.

**Correct pattern:**

```
Tool selection by volume and object:
- < 50,000 records AND supported object → Data Import Wizard.
  (Accounts, Contacts, Leads, Solutions, Campaign Members, Custom Objects)
- 50,000 - 5,000,000 records → Data Loader, with Use Bulk API selected.
  (Data Loader defaults to the SOAP-based API; Bulk API is a setting you turn on.)
- > 5,000,000 records → Data Loader with Bulk API 2.0 or third-party ETL.
- Unsupported objects (Opportunities, Cases, etc.) → Data Loader regardless of volume.

Data Import Wizard limits:
- Fewer than 50,000 records per import, and fewer than 50 fields on the target object.
- Does not support all standard objects.
- Does not support hard delete.
```

**Detection hint:** If the output recommends Data Import Wizard for more than 50,000 records or for unsupported objects like Opportunity or Case, the tool choice is wrong. Search for `Import Wizard` combined with large record counts.

---

## Anti-Pattern 2: Using insert instead of upsert without an External ID strategy

**What the LLM generates:** "Insert the records into Salesforce. If some already exist, update them in a separate batch."

**Why it happens:** LLMs separate insert and update operations instead of using upsert with an External ID. Splitting operations creates race conditions, duplicates, and requires two passes. Upsert with an External ID field handles both insert and update in a single operation.

**Correct pattern:**

```
Use upsert with an External ID for data loads that may contain
both new and existing records:
1. Create an External ID field (or use an existing unique identifier).
   - Mark it as External ID and Unique in field settings.
2. Include the External ID value in every row of the import file.
3. Use "Upsert" operation in Data Loader:
   - Matching records (by External ID) are updated.
   - Non-matching records are inserted.
4. Never use Name or auto-number fields as match keys —
   they are not reliable for deduplication.
```

**Detection hint:** If the output recommends separate insert and update passes instead of upsert, or uses Name as the match key, the approach creates duplicate risk. Search for `upsert` and `External ID` in the output.

---

## Anti-Pattern 3: Ignoring load sequence for related objects

**What the LLM generates:** "Load Accounts, Contacts, and Opportunities in any order."

**Why it happens:** LLMs treat data load as a flat operation. Salesforce requires parent records to exist before child records can reference them via lookup or master-detail relationships. Loading children before parents causes relationship field lookup failures.

**Correct pattern:**

```
Load in dependency order — parents before children:
1. Reference data (Users, Record Types, Queues) — must exist first.
2. Accounts (parent for Contacts, Opportunities, Cases).
3. Contacts (child of Account, parent for Activities).
4. Opportunities (child of Account, references Contact roles).
5. Opportunity Line Items (child of Opportunity, references Products/PricebookEntries).
6. Cases (child of Account/Contact).
7. Activities (child of multiple objects via WhoId/WhatId).

For each child load, map the parent lookup using the parent's External ID.
```

**Detection hint:** If the output does not specify a load sequence or says records can be loaded "in any order," the dependency order is missing. Search for `sequence`, `order`, or `parent` in the load instructions.

---

## Anti-Pattern 4: Failing to disable automation before bulk loads

**What the LLM generates:** "Load the records using Data Loader. The system will process them normally."

**Why it happens:** LLMs do not consider the side effects of automation during bulk loads. Active validation rules, flows, triggers, workflow rules, and duplicate rules fire on every record during a data load. This causes load failures, performance degradation, and unwanted side effects (e.g., email alerts firing for every imported record).

**Correct pattern:**

```
Pre-load automation management:
1. Identify all automation on the target object: validation rules,
   record-triggered flows, Apex triggers, workflow rules, duplicate rules.
2. Decide per automation:
   - Deactivate: for rules that should not apply to migrated data.
   - Bypass: use a custom permission or bypass flag checked by the automation.
   - Keep active: for rules that must validate migrated data.
3. Use a dedicated integration user with a bypass custom permission.
4. Load in a maintenance window for large volumes.
5. Re-activate or remove bypasses after the load completes.
6. Verify automation state matches pre-load documentation.
```

**Detection hint:** If the output does not mention deactivating or bypassing automation before a bulk load, side effects are unmanaged. Search for `validation rule`, `flow`, `trigger`, `bypass`, or `deactivate` in the load plan.

---

## Anti-Pattern 5: Not planning rollback for failed data loads

**What the LLM generates:** "Load the data into production. If there are errors, fix them and re-run."

**Why it happens:** LLMs treat data loads as idempotent retries. In practice, a partially failed load may insert some records while rejecting others, creating orphaned records, broken relationships, or partial data. Without a rollback plan, cleanup is manual and error-prone.

**Correct pattern:**

```
Data load rollback strategy:
1. Before loading: export the current state of affected records.
2. Save the Data Loader success and error files for every batch.
3. For inserts: the success file contains the new Salesforce IDs.
   Rollback = hard delete using those IDs.
4. For updates: rollback = re-import the pre-load export to restore
   original field values.
5. For upserts: separate inserted records (new IDs in success file)
   from updated records (existing IDs) for targeted rollback.
6. Test the rollback procedure in a sandbox before production loads.
```

**Detection hint:** If the output does not mention saving success/error files or planning for rollback after a failed load, the recovery strategy is missing. Search for `rollback`, `success file`, or `error file`.

---

## Anti-Pattern 6: Generating a process-conf.xml with a plaintext password and a SOAP-era batch size

**What the LLM generates:**

```xml
<map>
    <!-- excerpt: the configOverrideMap <map> of one process-conf.xml bean -->
    <entry key="sfdc.password" value="MyPassword123!"/>
    <entry key="sfdc.useBulkApi" value="true"/>
    <entry key="sfdc.loadBatchSize" value="200"/>
    <entry key="process.operation" value="Upsert"/>
</map>
```

**Why it happens:** Three separate pattern-matches, each individually plausible. The password field looks like any other config value. `200` is the number that appears next to `sfdc.loadBatchSize` in the parameter reference, because that table describes the SOAP path. And `Upsert` is capitalised the way it is in the UI. All three are wrong here: the Data Loader Guide requires the password to be `encrypt.bat` output decryptable by `process.encryptionKeyFile`; the Bulk API ceiling is 10,000, and 200 wastes the 15,000-batch 24-hour allocation; and operation values are lowercase.

**Correct pattern:**

```xml
<map>
    <!-- excerpt: the configOverrideMap <map> of one process-conf.xml bean.
         Password produced by:
         encrypt.bat -e PASSWORD+SECURITYTOKEN C:\Migration\Config\dataLoader.key -->
    <entry key="sfdc.password" value="e8a68b73992a7a54"/>
    <entry key="process.encryptionKeyFile" value="C:\Migration\Config\dataLoader.key"/>
    <entry key="sfdc.useBulkApi" value="true"/>
    <entry key="sfdc.bulkApiSerialMode" value="true"/>
    <entry key="sfdc.loadBatchSize" value="5000"/>
    <entry key="process.operation" value="upsert"/>
    <entry key="sfdc.externalIdField" value="Legacy_Account_Id__c"/>
</map>
```

**Detection hint:** Run `python3 scripts/check_load_plan.py --manifest-dir <config dir>`. It flags all four: a password that is not hex, a password with no key file, a batch size wrong for the enabled API, and an operation value outside the documented lowercase set. If the generated config also sets `sfdc.externalIdField` on an `insert`, the checker WARNs on that too — that combination is how an LLM produces a load that looks idempotent and is not.

---

## Anti-Pattern 7: Declaring a load reconciled after reading only the error file

**What the LLM generates:** "The load completed. Check `accountUpsert_error.csv` — if it is empty, all records loaded successfully."

**Why it happens:** The two-file mental model (success + error) is correct for Data Loader's SOAP path and wrong for Bulk API 2.0, which exposes a third resource. A job that failed mid-run, was aborted, or exhausted the daily batch allocation leaves rows that are in neither the success nor the failed file. An empty error file on such a job means "nothing was rejected", not "everything landed".

**Correct pattern:**

```bash
JOB=7505fEXAMPLE4C2AAM
for R in successfulResults failedResults unprocessedrecords; do
  curl -s -H "Authorization: Bearer $SF_TOKEN" \
    "$SF_HOST/services/data/v62.0/jobs/ingest/$JOB/$R/" -o "$JOB.$R.csv"
done
# The identity that must hold:
#   source rows == successfulResults + failedResults + unprocessedrecords
# And separately, target-org COUNT() must match the success count.
```

**Detection hint:** If the output names `failedResults` without `unprocessedrecords`, or reconciles on two numbers instead of four, the reconciliation is incomplete. Search for `error file` or `failedResults` and check whether unprocessed records are mentioned at all.
