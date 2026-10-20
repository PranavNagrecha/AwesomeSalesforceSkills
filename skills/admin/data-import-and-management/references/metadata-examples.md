# Load Artefacts: Data Import and Management

The deployable artefacts an admin-run import produces are **load configs**, not Setup metadata: a
`process-conf.xml` bean, a `.sdl` mapping file, a Bulk API 2.0 job body, a load-order table, and the
SOQL that proves the load landed. The one piece of real metadata this skill deploys is the External ID
field the whole plan hangs on, so that XML is here too.

| Artefact | Produced by | Lives in |
|---|---|---|
| External ID custom field | `sf project deploy` | `force-app/main/default/objects/<Object>/fields/<Field>.field-meta.xml` |
| `process-conf.xml` bean | hand-authored, run by `process.bat` | Data Loader config directory (not source control root — it holds an encrypted password) |
| `.sdl` mapping | Data Loader **Mapping > Save Mapping**, or hand-authored | beside `process-conf.xml` |
| Bulk API 2.0 job body | `curl` / script | your migration repo |
| Load-order table | this skill's `templates/data-load-plan-template.md` | the runbook |

---

## 1. The External ID field the upsert matches on

`force-app/main/default/objects/Account/fields/Legacy_Account_Id__c.field-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata">
    <fullName>Legacy_Account_Id__c</fullName>
    <label>Legacy Account ID</label>
    <type>Text</type>
    <length>50</length>
    <externalId>true</externalId>
    <unique>true</unique>
    <caseSensitive>false</caseSensitive>
    <required>false</required>
    <trackHistory>false</trackHistory>
    <description>Immutable primary key from the retired CRM. Upsert match key; never edited by users.</description>
</CustomField>
```

**How to read it**

- `<externalId>true</externalId>` — the property that makes the field usable as an upsert key. It is
  returned only when the field type is `AutoNumber`, `Email`, `Number`, or `Text` (Metadata API
  Developer Guide, `CustomField` field table, api_meta 264 L45637-45639), so a Formula or Picklist
  match key is not an option.
- `<unique>true</unique>` — **not** implied by `externalId`. They are separate booleans in the same
  table (`externalId` L45637, `unique` L45915). Without it, one key value can match more than one record,
  and the REST upsert-by-external-ID outcome is a 300 error with nothing created or updated (api_rest 264 L3082). UNVERIFIED (2026-10-20): the Data Loader / Bulk API 2.0 per-row outcome is not in the corpus.
- `<caseSensitive>false</caseSensitive>` — decide deliberately. With `true`, `ACCT-22` and `acct-22`
  are two different keys and your source extract must be case-stable forever.
- `<length>50</length>` — the field length (api_meta 264 L45716); size it to the source system's key, not to 255.

`manifest/package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Account.Legacy_Account_Id__c</members>
        <members>Contact.Legacy_Contact_Id__c</members>
        <name>CustomField</name>
    </types>
    <version>62.0</version>
</Package>
```

```bash
# Retrieve what exists today before you edit anything
sf project retrieve start --manifest manifest/package.xml --target-org migration-sandbox

# Deploy the External ID fields, and only them, ahead of the load
sf project deploy start --manifest manifest/package.xml --target-org migration-sandbox

# Field-level security is NOT in the CustomField file — grant it or the load user cannot write the key
sf project deploy start --metadata "PermissionSet:Data_Migration_Loader" --target-org migration-sandbox
```

**Verify before loading a single row.** In Setup > Object Manager > Account > Fields, the field must
show *External ID* and *Unique* checked. From the CLI:

```bash
# REST describe resource: GET /services/data/vXX.X/sobjects/Account/describe (api_rest 264 L1525)
curl -s -H "Authorization: Bearer $SF_TOKEN" "$SF_HOST/services/data/v68.0/sobjects/Account/describe" \
  | python3 -c "import json,sys; f=[x for x in json.load(sys.stdin)['fields'] if x['name']=='Legacy_Account_Id__c'][0]; print({k:f[k] for k in ('externalId','unique','idLookup','updateable','createable')})"
```

`idLookup` is the describe property for "can be used to specify a record in an upsert call" (object_reference 264 L2481); check it is `true`. The Bulk API 2.0 rule for a custom parent field in a relationship column header is that its External ID box is checked (§4, api_asynch 264 L1490). UNVERIFIED (2026-10-20): that a custom External ID field reports `idLookup` true is not stated in the corpus.

---

## 2. `process-conf.xml` — CLI Data Loader upsert on an External ID

One `<bean>` per process. Shaped from the sample config in the Data Loader Guide
(data loader 264 L2489-2535) and extended with the Bulk API, serial mode, batch size and
assignment rule settings from the process configuration parameter table (L1630-1906).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE beans PUBLIC "-//SPRING//DTD BEAN//EN"
 "http://www.springframework.org/dtd/spring-beans.dtd">
<beans>
    <bean id="accountUpsert"
          class="com.salesforce.dataloader.process.ProcessRunner"
          scope="prototype">
        <description>Upserts Account rows from the legacy CRM extract, matching on Legacy_Account_Id__c.</description>
        <property name="name" value="accountUpsert"/>
        <property name="configOverrideMap">
            <map>
                <entry key="sfdc.endpoint" value="https://example--migration.sandbox.my.salesforce.com"/>
                <entry key="sfdc.username" value="migration.loader@example.com.migration"/>
                <entry key="sfdc.password" value="e8a68b73992a7a54"/>
                <entry key="process.encryptionKeyFile" value="C:\Migration\Config\dataLoader.key"/>
                <entry key="sfdc.oauth.environment" value="Sandbox"/>
                <entry key="sfdc.endpoint.Sandbox" value="test.salesforce.com"/>

                <entry key="sfdc.entity" value="Account"/>
                <entry key="process.operation" value="upsert"/>
                <entry key="sfdc.externalIdField" value="Legacy_Account_Id__c"/>

                <entry key="sfdc.useBulkApi" value="true"/>
                <entry key="sfdc.bulkApiSerialMode" value="true"/>
                <entry key="sfdc.bulkApiCheckStatusInterval" value="5000"/>
                <entry key="sfdc.loadBatchSize" value="2000"/>
                <entry key="sfdc.timeoutSecs" value="600"/>

                <entry key="sfdc.assignmentRule" value=""/>
                <entry key="sfdc.insertNulls" value="false"/>
                <entry key="sfdc.timezone" value="GMT"/>

                <entry key="process.mappingFile" value="C:\Migration\Config\accountUpsertMap.sdl"/>
                <entry key="dataAccess.type" value="csvRead"/>
                <entry key="dataAccess.name" value="C:\Migration\In\accounts.csv"/>
                <entry key="process.outputSuccess" value="C:\Migration\Log\accountUpsert_success.csv"/>
                <entry key="process.outputError" value="C:\Migration\Log\accountUpsert_error.csv"/>
                <entry key="process.batchMode.exitWithErrorOnFailedRows" value="true"/>
                <entry key="sfdc.debugMessages" value="false"/>
            </map>
        </property>
    </bean>

    <bean id="caseInsert"
          class="com.salesforce.dataloader.process.ProcessRunner"
          scope="prototype">
        <description>Inserts historical Cases and runs the migration assignment rule instead of honouring OwnerId.</description>
        <property name="name" value="caseInsert"/>
        <property name="configOverrideMap">
            <map>
                <entry key="sfdc.endpoint" value="https://example--migration.sandbox.my.salesforce.com"/>
                <entry key="sfdc.username" value="migration.loader@example.com.migration"/>
                <entry key="sfdc.password" value="e8a68b73992a7a54"/>
                <entry key="process.encryptionKeyFile" value="C:\Migration\Config\dataLoader.key"/>
                <entry key="sfdc.entity" value="Case"/>
                <entry key="process.operation" value="insert"/>
                <entry key="sfdc.useBulkApi" value="true"/>
                <entry key="sfdc.bulkApiSerialMode" value="true"/>
                <entry key="sfdc.loadBatchSize" value="2000"/>
                <entry key="sfdc.assignmentRule" value="01Q5f000000XyZaEAK"/>
                <entry key="process.mappingFile" value="C:\Migration\Config\caseInsertMap.sdl"/>
                <entry key="dataAccess.type" value="csvRead"/>
                <entry key="dataAccess.name" value="C:\Migration\In\cases.csv"/>
                <entry key="process.outputSuccess" value="C:\Migration\Log\caseInsert_success.csv"/>
                <entry key="process.outputError" value="C:\Migration\Log\caseInsert_error.csv"/>
            </map>
        </property>
    </bean>
</beans>
```

**How to read it**

- `sfdc.externalIdField` is only consulted for `process.operation` = `upsert`. Set on an `insert` it is
  inert — and the false comfort that you "configured the match key" is how a re-run doubles the data.
  Valid `process.operation` values, lowercase: `extract`, `extract_all`, `insert`, `update`, `upsert`,
  `delete`, `hard_delete` (data loader 264 L1921-1953).
- `sfdc.useBulkApi=true` switches the meaning of `sfdc.loadBatchSize`. The Settings reference gives the
  ceiling as **200 records for SOAP API and 10,000 for Bulk API**, and says Bulk API 2.0 ignores batch
  size entirely because it batches for you (L351-360). The command-line parameter table for
  `sfdc.loadBatchSize` still reads "The maximum is 200 records. We recommend a value from 50 through
  100" (L1753-1757) — that sentence is written for the SOAP path. Set the value for the API you
  actually turned on.
- `sfdc.bulkApiSerialMode=true` processes batches one at a time. The guide's reason is database
  contention: "Processing in parallel can cause database contention. When contention is severe, the
  load can fail" (L1656-1659, L602-604). Pay the wall-clock cost on any load that touches a shared parent
  (Contacts under a few large Accounts, Cases under one Account) or that fires ownership changes.
- `sfdc.assignmentRule` takes the **ID** of the rule, sample value `03Mc00000026J7w`, applies to
  inserts, updates and upserts on Cases and Leads only, and **overrides `OwnerId` values in your CSV**
  (L379-383, L1630-1633). Leave it empty when the CSV owns the ownership. See `admin/assignment-rules` for
  the rule definition itself.
- `sfdc.insertNulls=false` is the shipped sample value (L1751). It is also *unavailable* when Bulk
  API or Bulk API 2.0 is on — empty values are simply ignored on update, and the way to null a field is
  the literal `#N/A` in the CSV cell (L366-377, L621-625).
- `sfdc.timezone` defaults to the time zone of the machine Data Loader is installed on (L1852-1853,
  L1859-1860). Pin it.
- `process.batchMode.exitWithErrorOnFailedRows=true` makes `process.bat` exit **4** when rows failed;
  the default is `false`, under which a load with failed rows exits **0** and a CI wrapper calls it a
  success (data loader 264 L1957-1975). The guide places the property in `config.properties` and says these exit codes
  apply to Data Loader version 62 and later (L1958); UNVERIFIED (2026-10-20): that the same key set in a `process-conf.xml` bean behaves the same is not in the corpus.

**Never commit this file with a live `sfdc.password`.** The value must be produced by `encrypt.bat`
against the key file (L2395-2435):

```bat
rem 1. Create the key file once
encrypt.bat -k C:\Migration\Config\dataLoader.key

rem 2. Encrypt password + security token together, against that key
encrypt.bat -e myP4sswordsRock00DE0X0A0M0PeLE!AQcAQH0dMHEXAM C:\Migration\Config\dataLoader.key

rem 3. Run one bean by id
process.bat "C:\Migration\Config" accountUpsert
```

If you authenticate with OAuth instead, remove `sfdc.password` entirely (L2487). The Data Loader
command-line interface is Windows-only (stated repeatedly, e.g. L2480).

---

## 3. `accountUpsertMap.sdl` — the mapping file

`process.mappingFile` points here. Syntax from data loader 264 L2203-2265: one pair per line,
`=` as separator, **CSV column on the left and Salesforce field on the right for an import** (the sides
reverse for an export). Constants go in double quotes on the left. Spaces are escaped with `\`.

```properties
#Mapping values
#accountUpsertMap.sdl - import: source column = Salesforce field
LEGACY_ACCT_ID=Legacy_Account_Id__c
ACCT_NAME=Name
PHONE=Phone
BILLING_STREET=BillingStreet
BILLING_CITY=BillingCity
BILLING_STATE=BillingState
BILLING_POSTCODE=BillingPostalCode
ANNUAL_REV=AnnualRevenue
EMPLOYEES=NumberOfEmployees
SYSTEMMODSTAMP=
"Legacy CRM"=Migration_Source__c
"Food\ &\ Beverage"=Industry
```

**How to read it**

- `SYSTEMMODSTAMP=` with an empty right-hand side drops that source column. The guide's own worked
  insert example lists it with an empty destination (L2225). UNVERIFIED (2026-10-20): the guide does not say in words that an empty destination drops the column.
- `"Legacy CRM"=Migration_Source__c` writes a constant into every row. Constants are supported for
  insert, update and upsert, must contain at least one alphanumeric character, and can fan out to
  several fields: `"California"=BillingState, ShippingState` (L2250-2265).
- `"Food\ &\ Beverage"=Industry` — a space inside a constant is escaped with a backslash. So is a space
  inside a **source column name**: `Account\ Name=Name` (L2218-2219); the constant form is at L2267-2269.
- Nothing in the `.sdl` syntax rules (L2205-2213) addresses writing the same destination field twice. UNVERIFIED (2026-10-20): what Data Loader does then is not in the corpus. `scripts/check_load_plan.py --manifest-dir` warns on it.
- Building the map in the Data Loader UI and clicking **Save Mapping** on the Mapping dialog emits this
  file (L2467; also L940) — faster and less error-prone than typing 80 lines by hand.

---

## 4. Bulk API 2.0 — job body, CSV rules, results

### Create the job

`POST /services/data/v62.0/jobs/ingest/`

```json
{
  "object": "Contact",
  "operation": "upsert",
  "externalIdFieldName": "Legacy_Contact_Id__c",
  "contentType": "CSV",
  "lineEnding": "CRLF",
  "columnDelimiter": "COMMA",
  "assignmentRuleId": "01Q5f000000XyZaEAK"
}
```

| Field | Rule | Source |
|---|---|---|
| `operation` | `insert`, `delete`, `hardDelete`, `update`, `upsert`; `hardDelete` needs the "Bulk API Hard Delete" permission | asynch 264 L1606-1611, L1630-1635 |
| `externalIdFieldName` | **Required** for `upsert`; the values must also exist in the CSV | asynch 264 L1586-1588 |
| `lineEnding` | `LF` (default) or `CRLF`. Match the file, not your assumptions — a Windows editor writes CRLF | asynch 264 L1275-1277, L560-561 |
| `columnDelimiter` | `COMMA` (default), `BACKQUOTE`, `CARET`, `PIPE`, `SEMICOLON`, `TAB` | asynch 264 L1573-1581 |
| `assignmentRuleId` | Case or Lead only; the rule may be **active or inactive**; API 49.0+ | asynch 264 L1555-1556, L1570 |
| `contentType` | `CSV` is the only valid value | asynch 264 L1583-1584 |

### The CSV

```csv
Legacy_Contact_Id__c,FirstName,LastName,Email,Account.Legacy_Account_Id__c
SRC-1001,Ana,Lopez,ana.lopez@example.org,ACCT-22
SRC-1002,Devon,Price,devon.price@example.org,ACCT-31
SRC-1003,Kim,Tran,kim.tran@example.org,ACCT-31
```

- Row 1 is the field names; every later row is one record (asynch 264 L1246-1247).
- `Account.Legacy_Account_Id__c` resolves the parent **by the parent's External ID**, so you do not need
  a two-pass load that exports Salesforce IDs and re-joins them. The rules
  (asynch 264 L1488-1491): child-to-parent only, never parent-to-child; one hop only, no
  child-to-parent-grandparent; and the parent field must be indexed — a custom field is indexed when
  its *External ID* box is checked, a standard field when its `idLookup` property is `true`.
- For a **custom** parent object the header uses the relationship name: replace the child lookup field's
  `__c` with `__r`, e.g. `Mother_Of_Child__r.External_ID__c` (asynch 264 L1498-1501).
- Upload the CSV to `contentUrl` (`/jobs/ingest/<jobId>/batches/`) with `Content-Type: text/csv`, then
  `PATCH` `{"state":"UploadComplete"}`. **This PATCH is required — the `state` property is how you tell Salesforce the job is ready for processing** (asynch 264 L1798-1799, L275).

### The lifecycle you poll

`Open` → `UploadComplete` → `InProgress` → `JobComplete` (or `Failed` / `Aborted`)
(asynch 264 L272-287). `Aborted` also lands there when someone with *Manage Data Integrations*
cancels the job out from under you (L286-287).

### The three results endpoints — read all three

| Endpoint | Returns | Why you must read it |
|---|---|---|
| `GET /jobs/ingest/<jobId>/successfulResults/` | CSV with `sf__Id`, `sf__Created` + your original columns | `sf__Created` distinguishes an upsert's inserts from its updates |
| `GET /jobs/ingest/<jobId>/failedResults/` | CSV with `sf__Error`, `sf__Id` + your original columns | Rows that were processed and rejected |
| `GET /jobs/ingest/<jobId>/unprocessedrecords/` | CSV of rows never processed at all | "Unprocessed rows are not the same as failed rows" (asynch 264 L2165-2166). A job that fails or is aborted leaves rows here that appear in **neither** of the other two files |

Row order in the unprocessed file is not guaranteed to match the upload, and results are not recorded
at all for batches that exceeded the daily batch allocation (asynch 264 L2177, L2179). All three files
are retrievable for **7 days** after job completion (cheat sheet 264 L386-389).

```bash
JOB=7505fEXAMPLE4C2AAM
for R in successfulResults failedResults unprocessedrecords; do
  curl -s -H "Authorization: Bearer $SF_TOKEN" \
    "$SF_HOST/services/data/v62.0/jobs/ingest/$JOB/$R/" -o "$JOB.$R.csv"
  echo "$R: $(( $(wc -l < "$JOB.$R.csv") - 1 )) rows"
done
```

`source rows == successful + failed + unprocessed`. If that identity does not hold, you have not
finished reading the results.

---

## 5. Load order

Each step names the key it matches on and how its lookups resolve. "Parent lookup by External ID" means
the child CSV uses the `Parent.External_Id__c` header from §4 and needs no ID re-join.

| # | Object | Operation | Match key | Lookups resolved by | Blocks |
|---|---|---|---|---|---|
| 1 | User | upsert | `FederationIdentifier` or `Legacy_User_Id__c` | — | every `OwnerId`, `CreatedById` audit-field write |
| 2 | UserRole / Group / Queue | metadata deploy | — | — | sharing and ownership on 3-8 |
| 3 | RecordType, picklist values | metadata deploy | — | — | rows whose Record Type or picklist value does not exist yet |
| 4 | Account | upsert | `Legacy_Account_Id__c` | `Owner.Legacy_User_Id__c` | 5, 6, 7, 8 |
| 5 | Contact | upsert | `Legacy_Contact_Id__c` | `Account.Legacy_Account_Id__c` | 7, 8 |
| 6 | Product2 / Pricebook2 / PricebookEntry | upsert | `Legacy_Product_Id__c` | `Pricebook2.Legacy_Pricebook_Id__c` | 7 |
| 7 | Opportunity | upsert | `Legacy_Opp_Id__c` | `Account.Legacy_Account_Id__c` | OpportunityLineItem, OpportunityContactRole |
| 8 | Case | insert | none (no natural key) | `Account.Legacy_Account_Id__c`, `Contact.Legacy_Contact_Id__c` | CaseComment, EmailMessage |
| 9 | Attachments / ContentVersion | insert | — | parent Salesforce Id from step 4-8 success files | — |
| 10 | Self-referencing lookups (`ParentId`, `ReportsTo`) | update | the object's own External ID | the same object's External ID, loaded in 4-8 | — |

Two orderings that are not negotiable:

- **Step 10 exists because step 4 cannot do it.** An Account whose `ParentId` points at an Account later
  in the same file has nothing to resolve against. Load the objects flat, then a second update pass
  wires the hierarchy.
- **Step 8 has no match key, so it is insert-only and not re-runnable.** If the Case load half-fails you
  delete what landed (by `CreatedDate` + `CreatedById`, §7) before you re-run it. Give any object you
  expect to re-run an External ID at step 3, even a throwaway one.

---

## 6. Pre-load checks, as SOQL

Run these against the **target** org, in the load window, and paste the output into the runbook.

```soql
-- 1. What is already there? The baseline every post-load count is compared against.
SELECT COUNT() FROM Account WHERE Legacy_Account_Id__c != null
SELECT COUNT() FROM Account

-- 2. Which duplicate rules will run against this load, and are they blocking?
--    DuplicateRule needs "View Setup and Configuration" (Summer '20 and later, object_reference 264 L103364). `AssignmentRule` is read-only and queryable (object_reference 264 L42463, L42467).
SELECT DeveloperName, MasterLabel, sObjectType, IsActive
FROM DuplicateRule
WHERE sObjectType IN ('Account','Contact','Lead')
ORDER BY sObjectType, DeveloperName

-- 3. Which assignment rule is active, and what is its Id for sfdc.assignmentRule / assignmentRuleId?
SELECT Id, Name, SobjectType, Active
FROM AssignmentRule
WHERE SobjectType IN ('Case','Lead')
ORDER BY SobjectType, Active DESC

-- 4. Can the load user actually write the key? (Run as the load user.)
SELECT Id, Name, Profile.Name, IsActive, TimeZoneSidKey
FROM User
WHERE Username = 'migration.loader@example.com.migration'
```

Validation rules: UNVERIFIED (2026-10-20) that they are not queryable through SOQL and that the Tooling API query below returns them (the Tooling API reference is not in the corpus; only the `--use-tooling-api` flag is, sfdx_dev 264 L12575). Pull them with the Tooling API or the manifest:

```bash
sf data query --use-tooling-api --target-org migration-sandbox \
  --query "SELECT EntityDefinition.QualifiedApiName, ValidationName, Active FROM ValidationRule WHERE EntityDefinition.QualifiedApiName IN ('Account','Contact','Case') AND Active = true"
```

Every rule this returns must be answered in the plan with one of: *the data satisfies it*, *the load
user holds the bypass Custom Permission*, or *the rule ships inactive for the window*. The bypass
contract is `NOT($Permission.Bypass_Validation_Rules)` in the rule's `errorConditionFormula` plus the
Custom Permission on the load user's Permission Set — see `admin/validation-rules`. Deactivating rules
in production is not on the list.

Duplicate rule design, matching-rule tuning and the `DuplicateRule` / `MatchingRule` XML belong to
`admin/duplicate-management`; the assignment and auto-response rule XML belongs to
`admin/assignment-rules`. This skill only checks that they are *known* before the load runs.

---

## 7. Post-load verification, as SOQL

```soql
-- A. Did the expected number of rows land, and are they yours?
--    CreatedById + CreatedDate is the only reliable fence around one load window
--    when the object has no External ID.
SELECT COUNT()
FROM Case
WHERE CreatedById = '0055f00000ABCDEAA1'
  AND CreatedDate >= 2026-09-04T22:00:00Z
  AND CreatedDate <= 2026-09-05T06:00:00Z

-- B. Upsert split: how many were created vs updated?
--    Compare against the count of sf__Created = true in successfulResults.
SELECT COUNT()
FROM Account
WHERE Legacy_Account_Id__c != null
  AND CreatedDate >= 2026-09-04T22:00:00Z

-- C. Orphans: children whose parent lookup silently stayed null.
SELECT COUNT()
FROM Contact
WHERE Legacy_Contact_Id__c != null AND AccountId = null

-- D. Duplicate keys that got through anyway (only possible if <unique> was false).
SELECT Legacy_Account_Id__c, COUNT(Id) recs
FROM Account
WHERE Legacy_Account_Id__c != null
GROUP BY Legacy_Account_Id__c
HAVING COUNT(Id) > 1

-- E. The delete-what-landed query, for the insert-only objects in step 8.
SELECT Id
FROM Case
WHERE CreatedById = '0055f00000ABCDEAA1'
  AND CreatedDate >= 2026-09-04T22:00:00Z
```

Error-file triage — group the failures before you fix anything:

```bash
# Data Loader error file: the reason column is the last one
tail -n +2 accountUpsert_error.csv | cut -d, -f2 | sort | uniq -c | sort -rn | head -20

# Bulk API 2.0 failed results: sf__Error is column 1
tail -n +2 "$JOB.failedResults.csv" | cut -d, -f1 | sed 's/:.*//' | sort | uniq -c | sort -rn
```

Triage by error **class**, not by row:

| Error text starts with | Class | Next action |
|---|---|---|
| `FIELD_CUSTOM_VALIDATION_EXCEPTION` | validation rule | Bypass permission missing, or the source data is genuinely wrong — decide which before re-running |
| `DUPLICATES_DETECTED` | duplicate rule in block mode | `admin/duplicate-management`; do not "just deactivate the rule" |
| `INVALID_CROSS_REFERENCE_KEY` / `MALFORMED_ID` | lookup unresolved | Parent missing, or the Id is malformed (`MALFORMED_ID` appears at api_rest 264 L1199) |
| `UNABLE_TO_LOCK_ROW` | contention | Turn on serial mode (data loader 264 L602-604), or group the child rows by parent so one batch does not fight another (LDV guide 264 L894-896) |
| `ENTITY_IS_DELETED` | recycled key | Target record is in the Recycle Bin |
| `REQUEST_LIMIT_EXCEEDED` | allocation | API request limits exceeded (api_rest 264 L1147); the batch allocation is 15,000 per rolling 24 hours (cheat sheet 264 L301-303) |

UNVERIFIED (2026-10-20): the error-class names `INVALID_CROSS_REFERENCE_KEY` and `ENTITY_IS_DELETED`, the 15-versus-18-character Id cause for `MALFORMED_ID`, and that an upsert will not resurrect a Recycle Bin key, are not in the corpus. `FIELD_CUSTOM_VALIDATION_EXCEPTION` is in apexdev 264 L42130 and `DUPLICATES_DETECTED` in api_rest 264 L7129, but neither passage maps them to a load "class"; that mapping is this skill's triage convention.

The four numbers that must reconcile in the runbook: **source rows**, **success file rows**, **error
file rows**, and the target-org `COUNT()` from query A. Query C and D exist because those four can all
agree while the data is still wrong.
