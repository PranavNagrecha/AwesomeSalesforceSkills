# Gotchas: Data Import and Management

---

## Upsert Without a Stable Match Key

**What happens:** The team says they are doing an "upsert" but matches are based on Name or Email. Some source rows match the wrong records, some create duplicates, and nobody notices until reporting breaks.

**When it bites you:** Legacy migrations, spreadsheets from business teams, and integrations that do not have External IDs.

**How to avoid it:** Use an immutable External ID or source-system key. Validate uniqueness in the source file before the load starts.

**Example:**
```csv
Email,FirstName,LastName
sales@example.org,Ana,Lopez
sales@example.org,Devon,Price
```

---

## Validation Rules and Flows at Volume

**What happens:** The first 100 records load fine in sandbox. Production load of 250,000 rows starts failing because record-triggered flows, duplicate rules, and validation formulas all execute at scale.

**When it bites you:** Weekend cutovers, mass owner changes, large historical backfills.

**How to avoid it:** Test with realistic batch size, define bypass controls deliberately, and use maintenance windows when recalculation or automation volume is high.

**Example:**
```text
Load objective: 300,000 Cases
Observed issue: flow updates parent Account on every Case insert
Result: locks and failed batches
Fix: bypass non-critical automation during cutover, then backfill downstream logic separately
```

---

## Duplicate Rules in Alert Mode Still Affect Operations

**What happens:** Teams assume alert mode is harmless because it does not block saves. The load completes, but thousands of near-duplicates get through because alerts were ignored by the service account or not reviewed afterward.

**When it bites you:** Contact imports, Account merges, and any migration with dirty source data.

**How to avoid it:** Test blocking vs alert behavior intentionally, assign an owner for duplicate review, and reconcile duplicates in the same cutover window.

**Example:**
```text
Duplicate rule: Alert on Contact email match
Load result: 40,000 Contacts loaded, 3,200 duplicate alerts ignored
Operational impact: sales reps now have multiple Contact records for the same person
```

---

## Child Rows Loaded Before Parent Rows

**What happens:** Contacts or Opportunities are loaded before the parent Account records exist. Lookup resolution fails and the error file grows fast.

**When it bites you:** Any multi-object load run by separate teams or separate jobs without a runbook.

**How to avoid it:** Load parent objects first, then child objects, and use External IDs for lookup resolution.

**Example:**
```text
Wrong order: Contacts -> Accounts
Correct order: Accounts -> Contacts -> Opportunities
```

---

## Turning On Bulk API Silently Changes What Batch Size Means

**What happens:** An admin sets `sfdc.loadBatchSize` to 2,000 in `process-conf.xml`, and the SOAP-path
job rejects it or clamps it. Another admin sets it to 200, turns on Bulk API, and wonders why a
4-million-row load is issuing 20,000 batches and running into the 24-hour batch allocation. The setting
never moved; the API under it did.

**When it bites you:** Any time `sfdc.useBulkApi` or the **Use Bulk API** checkbox is toggled without
revisiting the batch size, and any time a `process-conf.xml` is copied between two jobs that use
different APIs.

**How to avoid it:** Read the two ceilings as one rule — "The maximum import batch size is 200 records
for SOAP API and 10000 records for Bulk API… If the Use Bulk API 2.0 option is selected, then neither
batch size is used because Bulk API 2.0 handles batch size automatically"
(Data Loader Guide, salesforce_data_loader.txt:351-360). The command-line parameter table's
"The maximum is 200 records. We recommend a value from 50 through 100" (lines 1764-1769) describes the
SOAP path only. Set the number for the API the config actually turns on, and let
`scripts/check_load_plan.py --manifest-dir` re-check it whenever the file changes. Batch-window sizing
for a specific load belongs to `data/data-loader-batch-window-sizing`.

**Example:**

WRONG — Bulk API on, SOAP-era batch size. 4M rows becomes 20,000 batches, over the
15,000-batch 24-hour allocation before the job finishes:

```xml
<map>
    <!-- excerpt: the configOverrideMap <map> of one process-conf.xml bean -->
    <entry key="sfdc.useBulkApi" value="true"/>
    <entry key="sfdc.loadBatchSize" value="200"/>
</map>
```

RIGHT — the same two settings, sized for the API that is actually enabled:

```xml
<map>
    <!-- excerpt: the configOverrideMap <map> of one process-conf.xml bean -->
    <entry key="sfdc.useBulkApi" value="true"/>
    <entry key="sfdc.loadBatchSize" value="5000"/>
</map>
```

---

## Blanks Do Not Clear Fields, and #N/A Is the Only Thing That Does

**What happens:** A data-cleanup update ships a CSV where the `Phone` column is deliberately empty for
2,000 rows. The load succeeds. Every one of those 2,000 records keeps its old phone number. The empty
cell was read as "no instruction", not as "set to null".

**When it bites you:** Every blanking exercise: clearing stale `Description`, wiping a deprecated field
before deleting it, nulling `ParentId` to flatten a hierarchy — and specifically whenever Bulk API is
enabled, which is exactly the setting a large cleanup would turn on.

**How to avoid it:** Two different mechanisms, and only one of them is available at a time. With Bulk
API off, tick **Insert null values** / set `sfdc.insertNulls=true` — the guide is explicit that it
"instructs Data Loader to overwrite existing data in mapped fields". With Bulk API or Bulk API 2.0 on,
that option "isn't available… Empty field values are ignored when you update records using either API.
To set a field value to null when either API option is selected, use a field value of `#N/A` in the
import CSV file" (salesforce_data_loader.txt:366-375, restated at 618-624). Decide which you are using
before you build the file, because the file is shaped differently.

**Example:**
```csv
Id,Phone,Description
0035f00000AbcDeAAJ,#N/A,#N/A
0035f00000AbcDfAAJ,,Left blank on purpose - and therefore NOT cleared
```

---

## Static Variables Are Not Reset Between the 200-Record Chunks of One Bulk Request

**What happens:** A trigger carries the standard `if (Guard.hasRun) return; Guard.hasRun = true;`
recursion guard. A 10,000-record Bulk API batch fires that trigger fifty times, once per 200-record
chunk. The guard is set on chunk one. Chunks two through fifty skip the trigger entirely. 9,800 records
land without the automation that the load plan assumed would run, and nothing errors.

**When it bites you:** Any large load into an org whose triggers use static recursion guards or static
caches — which is most orgs with a mature trigger framework. The symptom shows up weeks later as
"why do only the first 200 records have a populated roll-up".

**How to avoid it:** Know the platform contract before you decide the automation stays on: "If a Bulk
API request causes a trigger to fire multiple times for chunks of 200 records, governor limits are
reset between these trigger invocations for the same HTTP request. Static variables aren't reset within
the multiple trigger invocations for the same Bulk API request." (Apex Developer Guide,
apexdev.txt:3789-3794 and 44981-44986). Governor limits reset per chunk; statics do not. If the load
depends on the trigger running for every row, the trigger's guard must be keyed per record Id rather
than per transaction, or the automation must be bypassed and the result backfilled deliberately. This
is a code change, so it belongs in the release, not in the load window.

**Example:**
```text
Load: 10,000 Opportunity updates, Bulk API, one job
Trigger: OpportunityTrigger with `private static Boolean hasRun = false;`
Fires:  50 chunks x 200 records
Runs:   chunk 1 only
Result: 200 rolled-up Accounts, 9,800 stale, zero errors in the success file
```

---

## Upsert on a Non-Unique External ID Rejects the Row Instead of Picking One

**What happens:** The External ID field was created with the *External ID* box checked but the *Unique*
box left clear. Two Salesforce records end up sharing the key `ACCT-22` — usually because someone loaded
before the field was unique, or a sandbox refresh reintroduced an old row. Every subsequent upsert of
`ACCT-22` fails. The row is neither created nor updated, so re-running the load does not fix it and the
count never reconciles.

**When it bites you:** Second and later runs of a migration; any org where the External ID field was
retrofitted onto data that already existed; person-account and lead-conversion paths that copy keys
across objects.

**How to avoid it:** Set `<unique>true</unique>` alongside `<externalId>true</externalId>` — they are
separate properties on `CustomField` (Metadata API Guide, api_meta.txt:43402-43405 and 43702), and the
platform enforces nothing from the first one alone. The failure is documented: "If the external ID is
matched multiple times, then a 300 error is reported, and the record isn't created or updated"
(Bulk API 2.0 Guide, api_asynch.txt:2500); the REST guide gives the same 300 as "the value returned
when an external ID exists in more than one record" with the matching records in the body
(api_rest.txt:1134). Find the collisions with the `GROUP BY … HAVING COUNT(Id) > 1` query in
`references/metadata-examples.md` §7 before the load, not after.

**Example:**
```soql
-- Run this BEFORE flipping the field to Unique; the flip fails while duplicates exist
SELECT Legacy_Account_Id__c, COUNT(Id) recs
FROM Account
WHERE Legacy_Account_Id__c != null
GROUP BY Legacy_Account_Id__c
HAVING COUNT(Id) > 1
```

---

## The Assignment Rule Setting Overrides the OwnerId Column You Carefully Prepared

**What happens:** A Case migration maps `OWNER_ID` to `OwnerId` and the CSV carries the correct owner
for all 900,000 rows. Someone leaves `sfdc.assignmentRule` populated from the previous job, or passes
`assignmentRuleId` on the Bulk API 2.0 job body. Every Case is routed by the rule instead. The
`OwnerId` column was read and discarded.

**When it bites you:** Reused `process-conf.xml` beans; scripted Bulk API jobs where the job template is
shared across objects; the "let's route the backlog properly" decision made mid-cutover without
checking what the file already contains.

**How to avoid it:** Treat the setting as mutually exclusive with an `OwnerId` mapping. The Data Loader
Guide states it plainly: the assignment rule "applies to inserts, updates, and upserts on cases and
leads. The assignment rule overrides Owner values in your CSV file"
(salesforce_data_loader.txt:377-383, repeated at 1631-1638). Two further traps: the value is the rule's
**Id**, not its name (sample `03Mc00000026J7w`), and on the Bulk API 2.0 side "the assignment rule can
be active or inactive" (api_asynch.txt:1588-1592) — an inactive rule will happily route your load.
Query `AssignmentRule` for the Id in the pre-load checks; `admin/assignment-rules` owns the rule design
itself.

**Example:**

Pick one. Never both — and the `.sdl` must agree with the choice.

Option A — the CSV owns ownership, so the setting is empty and `OwnerId` is mapped:

```xml
<map>
    <!-- excerpt: the configOverrideMap <map> of one process-conf.xml bean -->
    <entry key="sfdc.assignmentRule" value=""/>
</map>
```

Option B — the rule routes, so `OwnerId` must not appear in the mapping file at all:

```xml
<map>
    <!-- excerpt: the configOverrideMap <map> of one process-conf.xml bean -->
    <entry key="sfdc.assignmentRule" value="01Q5f000000XyZaEAK"/>
</map>
```

---

## Failed Rows and Unprocessed Rows Are Different Files, and Only One of Them Is Obvious

**What happens:** A Bulk API 2.0 job reaches `Failed`. The admin pulls `failedResults`, sees 4,000 rows
with real error messages, fixes them, and re-runs those 4,000. The job had 500,000 rows. The 180,000
that were never processed at all are in a third file nobody opened. They are re-loaded weeks later, as
duplicates, by someone reconciling counts.

**When it bites you:** Aborted jobs, jobs that trip the daily allocation mid-run, and any job whose
batches exhausted the automatic retries.

**How to avoid it:** Read all three result resources every time —
`successfulResults`, `failedResults`, and `unprocessedrecords`. The guide draws the distinction
explicitly: "Unprocessed rows are not the same as failed rows. Failed rows are processed but encounter
an error during processing." (api_asynch.txt:2205-2206). Two more properties of that file matter: row
order is not guaranteed to match the upload, and "Results are not recorded for batches that exceed the
daily batch allocation" (lines 2217-2221) — so a job that blew the allocation can leave rows in *no*
file at all, and only the source-count identity catches it. All three are retrievable for seven days
after job completion (App Limits Cheat Sheet, lines 812-815); after that the evidence is gone.

**Example:**
```text
Source CSV:            500,000
successfulResults:     316,000
failedResults:           4,000
unprocessedrecords:    180,000
                       -------
                       500,000  <- identity holds, nothing is unaccounted for
```

---

## Batches Time Out at Five Minutes and Retry Twenty Times Before the Whole Job Dies

**What happens:** A load that ran in eleven minutes in a fresh sandbox takes hours in production and
then fails outright. Nobody changed the file. The difference is that each production batch now carries
a record-triggered flow, a roll-up recalculation and a sharing recalculation, and stopped fitting inside
the per-batch time budget.

**When it bites you:** The first production run after a sandbox rehearsal on thin data; loads into
objects with deep role hierarchies or many sharing rules; any object where automation touches a shared
parent record.

**How to avoid it:** Know the budget you are spending. Bulk API 2.0 "creates a separate batch for every
10,000 records in your job data… If Salesforce can't process all the records in a batch within 5
minutes, the batch fails. Salesforce automatically retries failed batches up to a maximum of 20 times.
If the batch still can't be processed after 20 retries, the entire ingest job is moved to the Failed
state and remaining job data isn't processed." (api_asynch.txt:1242-1251). The lever on the Bulk API 2.0
side is a smaller upload file, not a batch-size setting, because Bulk API 2.0 does not expose one. On
the classic Bulk API side the equivalent guidance is to start at the 10,000 maximum and reduce it if
batches time out, while avoiding batches so small that the 15,000-per-24-hours allocation becomes the
constraint (App Limits Cheat Sheet, lines 788-806). Rehearse on production-shaped volume with the
production automation on, or the rehearsal measured nothing.

**Example:**
```text
Sandbox rehearsal: 50,000 Cases, no flows active   -> 4 min, JobComplete
Production run:    500,000 Cases, 3 flows active   -> batch 7 exceeds 5 min
                                                      20 retries
                                                      job state Failed at ~140,000 rows
Fix: bypass the two non-critical flows, split into 5 x 100,000, backfill afterwards
```

---

## Date Fields Shift by a Day When the Loading Machine Is East of GMT

**What happens:** A close-date column reads `2026-03-31` in the CSV and `2026-03-30` in Salesforce for
every row. Nobody transformed anything. The Data Loader machine sits in a UTC+ time zone and applied it
to a date that carried no offset.

**When it bites you:** Loads run from a laptop in Europe, India or APAC into a US-hosted org; any CSV
whose date column has no time-zone offset; month-end and quarter-end dates, where a one-day shift moves
the record into the wrong reporting period.

**How to avoid it:** Two settings and one file convention. `sfdc.timezone` "is the time zone on the
computer where Data Loader is installed" unless you set it, and it is applied whenever "a date value
doesn't include a time zone" (salesforce_data_loader.txt:538-550, 1846-1861). The guide's own advice is
blunt: "If your computer's locale is east of Greenwich Mean Time (GMT), we recommend that you change
your computer setting to GMT in order to avoid date adjustments when inserting or updating records"
(lines 823-824). Best of all, write the offset into the file — the recommended format is
`yyyy-MM-ddTHH:mm:ss.SSS+/-HHmm` (lines 785-794) — and then no setting can reinterpret it. Two related
traps in the same section: `Use European date format` flips parsing to `dd/MM/yyyy`, so an ambiguous
`03/04/2026` changes meaning with a checkbox; and valid dates run from `1700-01-01T00:00:00Z` to
`4000-12-31T00:00:00Z`, offset by your time zone, so a legacy `0000-00-00` sentinel is rejected rather
than nulled (lines 826-830).

**Example:**
```csv
# Ambiguous - reinterpreted by sfdc.timezone
CloseDate
2026-03-31

# Unambiguous - survives any machine, any setting
CloseDate
2026-03-31T00:00:00.000+0000
```

---

## Hard Delete Needs Bulk API, a Separate Permission, and Has No Undo

**What happens:** A cleanup plan says "hard delete the 2 million test records". The load user has
*Delete* on the object, the Data Loader **Hard Delete** button is greyed out or the `hard_delete`
operation fails, and someone "fixes" it by granting *Modify All Data* — a far larger grant than the job
needed. Or it works, and there is no Recycle Bin to restore from.

**When it bites you:** Post-migration cleanup, sandbox seeding resets, and storage-reclamation work.

**How to avoid it:** Three separate prerequisites. First, hard delete is only available when Data Loader
is configured to use Bulk API or Bulk API 2.0 (salesforce_data_loader.txt:604-606, 649-653) — it is not
a SOAP-path operation. Second, the required permissions are *Delete* on the record **plus** the
**Bulk API Hard Delete** permission, and only "if you configure Data Loader to use Bulk API to
hard-delete records" (lines 178-186, 260-266); *Modify All Data* is the requirement for **mass delete**,
a different operation (line 957), and granting it here is over-provisioning. Third, and permanently:
"hard-deleted records are immediately deleted and can't be recovered from the Recycle Bin" (lines
605-607). Export the full record set first — the export *is* the rollback plan — and use the
`process.operation` value `hard_delete` in lowercase (line 1921).

**Example:**
```xml
<map>
    <!-- excerpt: the configOverrideMap <map> of one process-conf.xml bean.
         Load user needs Delete on Test_Record__c AND "Bulk API Hard Delete". -->
    <entry key="sfdc.useBulkApi" value="true"/>
    <!-- prerequisite, not optional: hard delete is unreachable on the SOAP path -->
    <entry key="process.operation" value="hard_delete"/>
    <entry key="sfdc.entity" value="Test_Record__c"/>
</map>
```

---

## Bulk API Fails the Row That SOAP Would Have Truncated

**What happens:** The same CSV loads clean through the SOAP path and produces thousands of
`STRING_TOO_LONG` errors through Bulk API. The **Allow field truncation** setting that was quietly
absorbing over-length values is not available once Bulk API is on.

**When it bites you:** Migrating a source system with wider text columns than the Salesforce fields —
legacy `Description`, address lines, `Subject` — and specifically on the switch from a small SOAP
rehearsal to the Bulk API production run.

**How to avoid it:** Read the trade honestly rather than turning Bulk API off to make the errors go
away. The guide lists **Allow field truncation** among the settings that are unavailable when Use Bulk
API is selected: it "directs Data Loader to truncate data for certain field types when the Bulk API is
disabled. A load operation fails for the row if a value is specified that is too large for the field
when the Use Bulk API option is selected" (salesforce_data_loader.txt:626-631). Truncating silently was
never the safe behaviour — it was data loss you did not see. Trim in the extract, where the rule is
visible and reviewable, and keep Bulk API's rejection as the safety net. Related ceilings if you are
sizing the extract: 131,072 characters per field, 400,000 per record, 5,000 fields per record
(App Limits Cheat Sheet, lines 844-853).

**Example:**
```text
Source column: NOTES (nvarchar(max), max observed 12,400 chars)
Target field:  Description (Long Text Area, 32,768)
SOAP + Allow field truncation: silently truncated at 32,768, no error
Bulk API:                      row fails, STRING_TOO_LONG, visible in failedResults
Correct fix:                   truncate in the extract SQL with a documented rule
```

---

## Keeping Account Teams on a Mass Owner Change Requires Turning Bulk API Off

**What happens:** A reorg moves 40,000 Accounts to new owners through Data Loader with Bulk API on for
speed. Every Account Team on those records is wiped. The teams were not in the CSV, so nobody thought
they were in scope.

**When it bites you:** Territory realignments, sales reorganisations, and offboarding sweeps — the exact
loads that are large enough to want Bulk API.

**How to avoid it:** The documented behaviour requires the *slower* path plus a config-file change made
with the application closed: Data Loader v56.0.3 or later, `sfdc.useBulkApi=false` **and**
`process.keepAccountTeam=true` in `config.properties`, edited while Data Loader is shut down
(salesforce_data_loader.txt:658-671). One more constraint the note adds: "the uploaded .csv file must
have the same value for all Current Account owner records" — so a mixed-owner file has to be split into
one file per current owner. Budget the extra wall-clock time, or accept that the teams must be
re-created afterwards as a deliberate second load.

**Example:**
```properties
# config.properties - edit with Data Loader CLOSED
sfdc.useBulkApi=false
process.keepAccountTeam=true
```
