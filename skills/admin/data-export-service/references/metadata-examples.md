# Metadata & Artifact Examples — Salesforce Data Export Service

## What is and is not deployable here

The Data Export Service UI (Setup → Data Management → Data Export) has **no Metadata API type**. A search of the Metadata API Developer Guide for `DataExport`, `WeeklyExport`, and "weekly export" returns only the retired `TransactionSecurityPolicy.eventType` enum value `DataExport` (api_meta.txt:135185, which "notifies you when the selected object type has been exported using the Data Loader API client" and is part of Legacy Transaction Security, "a retired feature in all Salesforce orgs" as of Summer '20). There is no `DataExportSettings`, no `dataExport-meta.xml`, and no `<types><name>DataExport</name></types>` you can put in `package.xml`.

UNVERIFIED (2026-09-05): the *absence* of a metadata type is a negative result from the Summer '26 Metadata API guide text, not a positive statement in any guide. If Salesforce ships one, this section is the first thing to re-check.

So the deployable, repeatable, reviewable artefacts for this skill are the five below. Everything the UI does that is *not* covered by them is a manual Setup click that survives only in the runbook.

| # | Artefact | File | Deployable via | Checked by |
|---|---|---|---|---|
| 1 | Export inventory | `export-inventory.json` | Git (contract, not metadata) | `check_data_export_service.py --manifest-dir` |
| 2 | Operator permission set | `SF_Data_Export_Operator.permissionset-meta.xml` | `sf project deploy start` | same |
| 3 | Data Loader export batch | `process-conf.xml` | copied to the batch host | same |
| 4 | Data Loader defaults | `config.properties` | copied to the batch host | (reviewed, not linted) |
| 5 | Bulk API 2.0 query job | `*.http` / curl script | run against the org | (verified by response) |

---

## 1. `export-inventory.json` — the contract the checker enforces

This is the artefact that turns "we run a weekly export" into something reviewable: every object in scope names its filter, its schedule, its retention, its owner, and — if it carries PII — how it is masked at the destination.

```json
{
  "org": "acme-prod",
  "generatedBy": "admin/data-export-service",
  "policy": {
    "maxRetentionDays": 2555,
    "piiRequiresMaskingNote": true,
    "incrementalWatermarkField": "SystemModstamp"
  },
  "objects": [
    {
      "apiName": "Account",
      "mode": "full",
      "filter": null,
      "soql": "SELECT Id, Name, Type, OwnerId, CreatedDate, SystemModstamp FROM Account",
      "transport": "bulk-api-2.0",
      "operation": "query",
      "schedule": "0 2 1 * *",
      "retentionDays": 2555,
      "owner": "data-export-ops@acme.example",
      "containsPii": false,
      "maskingNote": null
    },
    {
      "apiName": "Contact",
      "mode": "incremental",
      "filter": "SystemModstamp >= 2026-09-01T00:00:00Z AND SystemModstamp < 2026-10-01T00:00:00Z",
      "soql": "SELECT Id, AccountId, LastName, Email, Phone, SystemModstamp FROM Contact WHERE SystemModstamp >= 2026-09-01T00:00:00Z AND SystemModstamp < 2026-10-01T00:00:00Z",
      "transport": "bulk-api-2.0",
      "operation": "query",
      "schedule": "0 2 1 * *",
      "retentionDays": 1095,
      "owner": "data-export-ops@acme.example",
      "containsPii": true,
      "maskingNote": "Email and Phone hashed with SHA-256 + per-tenant salt in the S3 landing lambda before the object is written to the analytics prefix; raw copy stays in the SSE-KMS vault prefix only."
    },
    {
      "apiName": "Case",
      "mode": "incremental",
      "filter": "SystemModstamp >= 2026-09-01T00:00:00Z AND SystemModstamp < 2026-09-08T00:00:00Z",
      "soql": "SELECT Id, CaseNumber, Subject, Status, ContactId, SystemModstamp, IsDeleted FROM Case WHERE SystemModstamp >= 2026-09-01T00:00:00Z AND SystemModstamp < 2026-09-08T00:00:00Z",
      "transport": "bulk-api-2.0",
      "operation": "queryAll",
      "schedule": "0 2 * * 1",
      "retentionDays": 2555,
      "owner": "data-export-ops@acme.example",
      "containsPii": true,
      "maskingNote": "Subject free-text is redacted by the DLP scanner before the analytics prefix; ContactId is a surrogate key, not PII on its own."
    },
    {
      "apiName": "ContentVersion",
      "mode": "full",
      "filter": "IsLatest = true",
      "soql": "SELECT Id, ContentDocumentId, Title, FileExtension, ContentSize, IsLatest FROM ContentVersion WHERE IsLatest = true",
      "transport": "data-loader-extract",
      "operation": "extract",
      "schedule": "0 3 1 * *",
      "retentionDays": 2555,
      "owner": "content-ops@acme.example",
      "containsPii": true,
      "maskingNote": "Metadata only — VersionData (the file body) is NOT extracted here; binary bodies are covered by the separate content-archive job with its own DPIA reference DPIA-2026-11."
    }
  ]
}
```

### How to read it

- **`policy.incrementalWatermarkField` is `SystemModstamp`, not `LastModifiedDate`.** `SystemModstamp` is "date and time when a user **or automated process (such as a trigger)** last modified this record" (object_reference.txt:2533–2540). `LastModifiedDate` records only user modification (object_reference.txt:2530–2531), so a roll-up or a standard-functionality trigger moves `SystemModstamp` and not `LastModifiedDate` — an incremental export watermarked on `LastModifiedDate` silently drops those rows.
- **`mode: "incremental"` therefore requires `SystemModstamp` in the filter.** The checker enforces exactly this.
- **`operation` is `query` or `queryAll`.** `queryAll` "returns records that have been deleted because of a merge or delete, and returns information about archived Task and Event records" (api_asynch.txt:2959–2961). Use it on the object where deletions must be visible in the archive (Case above); use plain `query` where they must not.
- **Both bounds on every incremental window are deliberate.** An open-ended `>=` filter on a large object degrades over time: `SystemModstamp` carries a *standard* index (ldv.txt:309, ldv.txt:404), and a standard index is used only "if the filter matches less than 30% of the first million records and less than 15% of additional records" (ldv.txt:462–465). A widening window eventually crosses that threshold and the query falls back to a full scan.
- **`retentionDays` is checked against `policy.maxRetentionDays`, per object.** The Contact row deliberately retains for less than the Account row — a shorter clock on the PII-carrying object is the point of having per-object retention at all.
- **`containsPii: true` requires a non-empty `maskingNote` describing where masking happens.** The checker fails the file otherwise. "PII is handled" is not a masking note; naming the transform, the boundary it happens at, and what is left unmasked is.
- **The `ContentVersion` row extracts metadata only.** `ContentVersion.VersionData` is `base64` and, on API upload/download, "is converted to base64 and stored in `VersionData`. This conversion increases the document size by approximately 37%" (object_reference.txt:79772–79773). Putting `VersionData` in a CSV export inventory is how a 40 GB content estate becomes a 55 GB CSV. `IsLatest = true` is present because "SOQL queries on the ContentVersion object return all versions of the document" (object_reference.txt:79848).

---

## 2. `SF_Data_Export_Operator.permissionset-meta.xml`

Shaped from the guide's own `PermissionSet` sample definition (api_meta.txt:95191–95230) and the `PermissionSetUserPermission` field table (api_meta.txt:95170–95180: `enabled` boolean Required, `name` string Required).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>SF Data Export Operator</label>
    <description>Read-only export operator. Grants API access and read on the objects named in export-inventory.json. Grants no create, edit, delete or modifyAllRecords: an export operator that can write is an export operator that can destroy the thing being archived.</description>
    <hasActivationRequired>false</hasActivationRequired>
    <userPermissions>
        <enabled>true</enabled>
        <name>ApiEnabled</name>
    </userPermissions>
    <userPermissions>
        <enabled>true</enabled>
        <name>WeeklyExport</name>
    </userPermissions>
    <objectPermissions>
        <object>Account</object>
        <allowRead>true</allowRead>
        <allowCreate>false</allowCreate>
        <allowEdit>false</allowEdit>
        <allowDelete>false</allowDelete>
        <viewAllRecords>true</viewAllRecords>
        <modifyAllRecords>false</modifyAllRecords>
    </objectPermissions>
    <objectPermissions>
        <object>Contact</object>
        <allowRead>true</allowRead>
        <allowCreate>false</allowCreate>
        <allowEdit>false</allowEdit>
        <allowDelete>false</allowDelete>
        <viewAllRecords>true</viewAllRecords>
        <modifyAllRecords>false</modifyAllRecords>
    </objectPermissions>
    <objectPermissions>
        <object>Case</object>
        <allowRead>true</allowRead>
        <allowCreate>false</allowCreate>
        <allowEdit>false</allowEdit>
        <allowDelete>false</allowDelete>
        <viewAllRecords>true</viewAllRecords>
        <modifyAllRecords>false</modifyAllRecords>
    </objectPermissions>
    <objectPermissions>
        <object>ContentVersion</object>
        <allowRead>true</allowRead>
        <allowCreate>false</allowCreate>
        <allowEdit>false</allowEdit>
        <allowDelete>false</allowDelete>
        <viewAllRecords>true</viewAllRecords>
        <modifyAllRecords>false</modifyAllRecords>
    </objectPermissions>
</PermissionSet>
```

### How to read it

- **`ApiEnabled` is the guide's own example of a user permission** — it is the `<name>` used in the `PermissionSet` sample definition (api_meta.txt:95216) and the one named in the `userPermissions` field description ("Specifies an app or system permission (such as 'API Enabled')", api_meta.txt:94863–94866). Bulk API 2.0 and Data Loader both need it.
- **`WeeklyExport` — UNVERIFIED (2026-09-05):** the API name of the Weekly Data Export permission does not appear anywhere in the Metadata API Developer Guide text (`grep -in "weekly" api_meta.txt` returns only `Weekly` as a schedule/recurrence enum at lines 12466, 15785, 22843, 71356, 134865 — never a user permission). Deploy this element to a scratch org before trusting the spelling; if the deploy rejects the name, retrieve the permission set from an org where the checkbox is ticked and read the name back.
- **The guide names `Read on the records` as the export permission, and nothing more.** The Data Loader guide's USER PERMISSIONS box says "To export records: Read on the records" and "To export all records: Read on the records" (salesforce_data_loader.txt:848–856). It does **not** name `ViewAllData` — so `viewAllRecords` here is a scoping decision you are making (an operator archiving the whole org needs to see the whole org), not a documented requirement. Drop it to `false` and rely on the sharing model when the archive is deliberately owner-scoped.
- **Every write flag is explicitly `false`.** In API version 40.0 and later, "if a permission isn't specified for a deployment, it's disabled" (api_meta.txt:94863–94869) — so omitting them would work. Writing them out makes the intent survive a reviewer skim.
- **`hasActivationRequired` false** keeps this assignable directly; a session-activated permission set would break an unattended batch host.

---

## 3. `process-conf.xml` — Data Loader export batch

Shaped from the guide's sample `ProcessRunner` bean (salesforce_data_loader.txt:2489–2534) and re-pointed from the sample's `insert` to an `extract`. Every `<entry key=…>` below appears in the Data Loader Process Configuration Parameters tables (salesforce_data_loader.txt:1413–1910).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE beans PUBLIC "-//SPRING//DTD BEAN//EN"
  "http://www.springframework.org/dtd/spring-beans.dtd">
<beans>
    <bean id="contactIncrementalExtract"
          class="com.salesforce.dataloader.process.ProcessRunner"
          scope="prototype">
        <description>Monthly incremental Contact extract, watermarked on SystemModstamp. Writes CSV; never writes to Salesforce.</description>
        <property name="name" value="contactIncrementalExtract"/>
        <property name="configOverrideMap">
            <map>
                <entry key="sfdc.endpoint" value="https://acme.my.salesforce.com"/>
                <entry key="sfdc.username" value="svc.export@acme.example"/>
                <entry key="sfdc.password" value="e8a68b73992a7a54"/>
                <entry key="process.encryptionKeyFile" value="c:\Users\svcexport\.dataloader\dataLoader.key"/>
                <entry key="sfdc.timeoutSecs" value="600"/>
                <entry key="sfdc.entity" value="Contact"/>
                <entry key="process.operation" value="extract"/>
                <entry key="sfdc.extractionSOQL" value="SELECT Id, AccountId, LastName, Email, Phone, SystemModstamp FROM Contact WHERE SystemModstamp &gt;= 2026-09-01T00:00:00Z AND SystemModstamp &lt; 2026-10-01T00:00:00Z"/>
                <entry key="sfdc.extractionRequestSize" value="500"/>
                <entry key="dataAccess.type" value="csvWrite"/>
                <entry key="dataAccess.name" value="D:\export\out\contact_2026-09.csv"/>
                <entry key="dataAccess.writeUTF8" value="true"/>
                <entry key="process.mappingFile" value="D:\export\conf\contactExtractMap.sdl"/>
                <entry key="process.enableExtractStatusOutput" value="true"/>
                <entry key="process.statusOutputDirectory" value="D:\export\status"/>
                <entry key="process.outputError" value="D:\export\status\contactExtract_error.csv"/>
                <entry key="process.outputSuccess" value="D:\export\status\contactExtract_success.csv"/>
                <entry key="sfdc.debugMessages" value="false"/>
            </map>
        </property>
    </bean>

    <bean id="caseIncrementalExtractAll"
          class="com.salesforce.dataloader.process.ProcessRunner"
          scope="prototype">
        <description>Weekly incremental Case extract including soft-deleted rows, so the archive can show what was deleted.</description>
        <property name="name" value="caseIncrementalExtractAll"/>
        <property name="configOverrideMap">
            <map>
                <entry key="sfdc.endpoint" value="https://acme.my.salesforce.com"/>
                <entry key="sfdc.username" value="svc.export@acme.example"/>
                <entry key="sfdc.password" value="e8a68b73992a7a54"/>
                <entry key="process.encryptionKeyFile" value="c:\Users\svcexport\.dataloader\dataLoader.key"/>
                <entry key="sfdc.entity" value="Case"/>
                <entry key="process.operation" value="extract_all"/>
                <entry key="sfdc.extractionSOQL" value="SELECT Id, CaseNumber, Subject, Status, ContactId, IsDeleted, SystemModstamp FROM Case WHERE SystemModstamp &gt;= 2026-09-01T00:00:00Z AND SystemModstamp &lt; 2026-09-08T00:00:00Z"/>
                <entry key="dataAccess.type" value="csvWrite"/>
                <entry key="dataAccess.name" value="D:\export\out\case_2026-09.csv"/>
                <entry key="dataAccess.writeUTF8" value="true"/>
                <entry key="process.enableExtractStatusOutput" value="true"/>
                <entry key="process.statusOutputDirectory" value="D:\export\status"/>
            </map>
        </property>
    </bean>
</beans>
```

### How to read it

- **`process.operation` values are lowercase.** The guide is explicit: "Enter values in the `process.operation` parameter in lowercase" (salesforce_data_loader.txt:1922). `extract` "uses the Salesforce Object Query Language to export a set of records from Salesforce… Soft-deleted records are not included"; `extract_all` "uses SOQL to export a set of records from Salesforce, including existing and soft-deleted records" (salesforce_data_loader.txt:1926–1936).
- **`dataAccess.type` is `csvWrite` for an export.** The DAO list names `csvRead`, `csvWrite`, `databaseRead`, `databaseWrite` (salesforce_data_loader.txt:2071–2079); `csvWrite` "allows writing to a comma-delimited file. A header row is added to the top of the file based on the column list provided by the caller." The guide's sample bean uses `csvRead` because it is an *insert*; copying that sample without flipping this key is the single most common way a "why is my export empty" ticket starts.
- **`sfdc.password` must be encrypted, and needs its key file.** "When running Data Loader in batch mode from the command line, you **must** encrypt the following configuration parameters: `sfdc.password`, `sfdc.proxyPassword`" (salesforce_data_loader.txt:1291–1293), produced by `encrypt.bat -e <plain text> <path to key file>` (salesforce_data_loader.txt:2427–2433) after `encrypt.bat -k [path to key file]` generates the key into `%userprofile%\.dataloader\dataLoader.key` (salesforce_data_loader.txt:2301–2303). An encrypted value without `process.encryptionKeyFile` will not decrypt.
- **`sfdc.debugMessages` stays `false`.** "Debug messages can contain sensitive information such as session id" (salesforce_data_loader.txt:2556) and the trace file "does not have a size limit" (salesforce_data_loader.txt:1694–1697).
- **`&gt;` and `&lt;` are required in the SOQL.** `process-conf.xml` is XML; a bare `>` in a `WHERE SystemModstamp >= …` clause is a parse error. The guide's own warning is adjacent: "Use caution when using different XML editors to edit the `process-conf.xml` file. Some editors add XML tags to the beginning and end of the file, which causes the import to fail" (salesforce_data_loader.txt:2559–2561).
- **This is Windows-only.** "The Data Loader command-line interface is supported for Windows only" is repeated at salesforce_data_loader.txt:1213, 1922, 2062, 2287. A Linux CI runner cannot host this bean; use artefact 5 there.
- **Data Loader export has three shape limits the SOQL must respect** (salesforce_data_loader.txt:895–906, 916–920): no nested/child queries, no polymorphic relationships (`Owner.Type` on Case errors), and compound fields "cause error messages" — query the individual components instead. Relationship field names are case-sensitive (`Account.Name`, not `ACCOUNT.NAME`).

Run it with (`<configdir>` is "the absolute or relative path to the directory containing `process-conf.xml`", salesforce_data_loader.txt:1364; the process name is "the name of the `ProcessRunner` bean", salesforce_data_loader.txt:2288):

```bat
process.bat "D:\export\conf" contactIncrementalExtract
```

---

## 4. `config.properties` — batch-host defaults

`config.properties` lives in "the `configs` default configuration directory" (salesforce_data_loader.txt:312, 661) and holds the defaults; "the settings in `configOverrideMap` take precedence over the default configuration parameters in `config.properties`" (salesforce_data_loader.txt:1394–1404).

```properties
# Transport. Bulk API is "optimized to load or delete many records asynchronously.
# It's faster than the default SOAP-based API due to parallel processing and fewer
# network round-trips."  (salesforce_data_loader.txt:1893-1901)
sfdc.useBulkApi=true

# Export-side batching. "Larger values can improve performance but use more memory
# on the client."  (salesforce_data_loader.txt:1438-1443)
sfdc.extractionRequestSize=500

# Connection resilience.  (salesforce_data_loader.txt:1477-1490)
sfdc.enableRetries=true
sfdc.maxRetries=3
sfdc.minRetrySleepSecs=2
sfdc.timeoutSecs=600

# Output shape.
dataAccess.type=csvWrite
dataAccess.writeUTF8=true
process.enableExtractStatusOutput=true

# Never on an unattended export host.  (salesforce_data_loader.txt:2556)
sfdc.debugMessages=false
```

UNVERIFIED (2026-09-05): the Data Loader guide documents these keys in the *process configuration parameter* tables and states that `config.properties` holds their defaults, but it does not print a full annotated `config.properties` sample. The key spellings above are the ones the parameter tables use; the file's `key=value` syntax is asserted from the guide's own two worked examples (`sfdc.useBulkApi=false`, `process.keepAccountTeam=true`, salesforce_data_loader.txt:665–666).

---

## 5. Bulk API 2.0 query job — the Linux-friendly, scriptable path

This is the artefact to reach for when the export must run unattended, on any OS, from CI. Shaped from the guide's Step 6 walkthrough (api_asynch.txt:1067–1181).

```bash
#!/usr/bin/env bash
set -euo pipefail
INSTANCE="https://acme.my.salesforce.com"
API="v62.0"                 # use the SAME version for create and results (api_asynch.txt:3341)
TOKEN="${SF_ACCESS_TOKEN:?export SF_ACCESS_TOKEN first}"

# --- 1. create the query job -------------------------------------------------
JOB=$(curl -sS "${INSTANCE}/services/data/${API}/jobs/query" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -X POST --data-raw '{
    "operation": "queryAll",
    "query": "SELECT Id, CaseNumber, Subject, Status, ContactId, IsDeleted, SystemModstamp FROM Case WHERE SystemModstamp >= 2026-09-01T00:00:00Z AND SystemModstamp < 2026-09-08T00:00:00Z",
    "contentType": "CSV",
    "columnDelimiter": "COMMA",
    "lineEnding": "LF"
  }' | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])')

# --- 2. poll until JobComplete ----------------------------------------------
while :; do
  STATE=$(curl -sS "${INSTANCE}/services/data/${API}/jobs/query/${JOB}" \
    -H "Authorization: Bearer ${TOKEN}" \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)["state"])')
  case "$STATE" in
    JobComplete) break ;;
    Failed|Aborted) echo "job ${JOB} ended in ${STATE}" >&2; exit 1 ;;
    *) sleep 15 ;;
  esac
done

# --- 3. page the results with the Sforce-Locator header ----------------------
LOCATOR=""
PAGE=0
while :; do
  URL="${INSTANCE}/services/data/${API}/jobs/query/${JOB}/results?maxRecords=50000"
  [ -n "$LOCATOR" ] && URL="${URL}&locator=${LOCATOR}"
  curl -sS "$URL" -H "Authorization: Bearer ${TOKEN}" -H "Accept: text/csv" \
       -D "headers_${PAGE}.txt" -o "case_page_${PAGE}.csv"
  LOCATOR=$(awk 'BEGIN{IGNORECASE=1} /^Sforce-Locator:/ {print $2}' "headers_${PAGE}.txt" | tr -d '\r')
  [ "$LOCATOR" = "null" ] && break
  PAGE=$((PAGE+1))
done
```

Response of step 1, from the guide (api_asynch.txt:1090–1104) — the job id in `id` is what steps 2 and 3 use:

```json
{
  "id" : "7986gEXAMPLE4X2OPT",
  "operation" : "query",
  "object" : "Account",
  "createdDate" : "2022-01-02T17:38:59.000+0000",
  "state" : "UploadComplete",
  "concurrencyMode" : "Parallel",
  "contentType" : "CSV",
  "apiVersion" : 67.0,
  "lineEnding" : "LF",
  "columnDelimiter" : "COMMA"
}
```

### How to read it

- **Poll until `state` is `JobComplete`** — "Repeat this step until the state is `JobComplete`" (api_asynch.txt:1120). The results resource requires it: "The job must have the state JobComplete" (api_asynch.txt:2813).
- **`Sforce-Locator` drives the paging loop, and only `Sforce-Locator`.** "If there are no more sets of query results, this value is the string 'null'" (api_asynch.txt:3403–3412) — the string, not JSON null. And: "For `locator`, use only the value from the `Sforce-Locator` header. Don't try to guess what it is" (api_asynch.txt:3506).
- **Use the same API version to create and to fetch.** "Use the same API version to get query results that you used to create the query. Otherwise, the call returns a 409 error" (api_asynch.txt:3341).
- **`maxRecords` prevents client-side timeouts, it does not raise a cap.** "The request is still subject to the size limits… specify the maximum number of records your client is expecting to receive in the `maxRecords` parameter. This splits the results into smaller sets with this value as the maximum size" (api_asynch.txt:3366–3384).
- **Leave `LIMIT` and `ORDER BY` out.** "LIMIT and ORDER BY disable PKChunking for SOQL queries. With PKChunking disabled, queries take longer to execute, and potentially result in query timeouts" (api_asynch.txt:2888–2891). Bulk API 2.0 chunks large query jobs automatically where the object supports it (api_asynch.txt:2880–2886).
- **Query jobs do not consume the batch allocation.** "In Bulk API 2.0, only ingest jobs consume batches. Query jobs don't" (salesforce_app_limits_cheatsheet.txt:740–741) — so the 15,000-batches-per-rolling-24-hours allocation (cheatsheet:737) is not the ceiling here. The ceilings that *do* apply to a query-based export are 10,000 query jobs per 24-hour rolling window and 1 TB of total query results per 24-hour rolling window (cheatsheet:920–932), both readable live from `/vXX.X/limits/` as `DailyBulkV2QueryJobs` and `DailyBulkV2QueryFileStorageMB`.
- **Results are retrievable for 7 days**, with a 20-minute retrieval timeout and 1 GB maximum retrieved file size (cheatsheet:906–917). That is a far longer collection window than the Data Export Service UI gives you, and it is the strongest single argument for this artefact over artefact 1's UI path.
- **These SOQL shapes are rejected outright** (api_asynch.txt:2892–2899, 2915–2923): `GROUP BY`, `OFFSET`, `TYPEOF`, aggregate functions such as `COUNT()`, date functions inside `GROUP BY`, compound address/geolocation fields and `FIELDS()`, and parent-to-child relationship queries. Child-to-parent is fine.

---

## `package.xml` and deploy

Only artefact 2 is Metadata API material.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>SF_Data_Export_Operator</members>
        <name>PermissionSet</name>
    </types>
    <version>62.0</version>
</Package>
```

```bash
# Retrieve the permission set from an org where the export checkboxes are already ticked,
# so you can read back the real user-permission API names (see the WeeklyExport note above).
sf project retrieve start --metadata "PermissionSet:SF_Data_Export_Operator" --target-org acme-uat

# Validate before deploying: a permission set that names a nonexistent user permission
# fails the whole deployment, so never skip the dry run.
sf project deploy start \
  --source-dir force-app/main/default/permissionsets \
  --target-org acme-prod --dry-run --test-level NoTestRun

sf project deploy start \
  --source-dir force-app/main/default/permissionsets \
  --target-org acme-prod
```

UNVERIFIED (2026-09-05): the `sf` CLI command syntax above is not documented in any of the Salesforce PDF guides used to ground this skill (Metadata API, Object Reference, Data Loader, Bulk API, REST API, App Limits, LDV). It is the current Salesforce CLI shape; confirm flags against `sf project deploy start --help` on the machine you run it from.

---

## Verification

Run these after the permission set deploys and after the first export cycle. All four are grounded in the guides.

**1. The operator actually holds the permission set.** Query shape from the guide's own `PermissionSetAssignment` example (object_reference.txt:88558–88568); `Assignee` is the relationship name for `AssigneeId` (object_reference.txt:217414–217423).

```sql
SELECT Id, Assignee.Username, PermissionSet.Name, IsActive, ExpirationDate
FROM PermissionSetAssignment
WHERE PermissionSet.Name = 'SF_Data_Export_Operator'
```

Note the special access rule: only users with View Setup and Configuration, Assign Permission Sets, or Manage User can query this object at all (object_reference.txt:217405–217409). If this returns zero rows for an admin, check that before assuming the assignment failed.

**2. The exported row count reconciles.** Run the same predicate as the job and compare to the CSV line count minus the header row (`csvWrite` "adds a header row to the top of the file", salesforce_data_loader.txt:2073–2075).

```sql
SELECT COUNT() FROM Contact
WHERE SystemModstamp >= 2026-09-01T00:00:00Z
  AND SystemModstamp <  2026-10-01T00:00:00Z
```

**3. The `queryAll` rows really include deletions.** If this returns rows and your Case CSV has no `IsDeleted` true values, the job ran `query`, not `queryAll`.

```sql
SELECT COUNT() FROM Case WHERE IsDeleted = true
  AND SystemModstamp >= 2026-09-01T00:00:00Z
  AND SystemModstamp <  2026-09-08T00:00:00Z
```

`IsDeleted` "indicates whether the record has been moved to the Recycle Bin (true) or not (false)" (object_reference.txt:2503–2505), and it is queryable only under `queryAll` — plain `Query` "will automatically filter out items that have been deleted" (api_rest.txt:3649–3650).

**4. Deletions inside the window are not silently missing.** The REST delete-log resource is the cross-check, and it has hard edges that belong in the runbook:

```bash
curl "${INSTANCE}/services/data/v62.0/sobjects/Case/deleted/?start=2026-09-01T00%3A00%3A00%2B00%3A00&end=2026-09-15T00%3A00%3A00%2B00%3A00" \
  -H "Authorization: Bearer ${SF_ACCESS_TOKEN}"
```

Its response carries `earliestDateAvailable` and `latestDateCovered` (api_rest.txt:3532–3533) — compare `earliestDateAvailable` against your window start. "Results are returned for no more than 15 days previous to the day the call is executed (or earlier if an administrator has purged the Recycle Bin)", and "there is a limit of 600,000 IDs returned from this resource. If more than 600,000 IDs are found, `EXCEEDED_ID_LIMIT` is returned" (api_rest.txt:8346–8349).

**5. Setup check for the UI path.** Setup → Data Management → Data Export shows the current schedule and the most recent run.

UNVERIFIED (2026-09-05): the Setup navigation path, the schedule screen's fields, and everything the run row displays are documented only on help.salesforce.com, which cannot be fetched. None of the seven grounding PDFs mentions Data Export Service at all — `grep -in "data export\|weekly export\|export service\|48.hour"` over `salesforce_app_limits_cheatsheet.txt` returns zero hits, and the only mention anywhere in the set is the Data Loader guide's aside that "Data Loader currently does not support exporting attachments. As a workaround, use the weekly export feature in the online application to export attachments" (salesforce_data_loader.txt:916–917). Verify the screen against a live org before scripting a runbook around it.

---

## Cross-references

- `references/gotchas.md` — the failure modes these artefacts are shaped to avoid
- `templates/data-export-service-template.md` — the runbook wrapper around them
- `scripts/check_data_export_service.py` — lints artefacts 1, 2 and 3 with `--manifest-dir`
