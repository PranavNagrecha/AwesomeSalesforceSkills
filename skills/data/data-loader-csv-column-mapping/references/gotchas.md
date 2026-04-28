# Gotchas — Data Loader CSV Column Mapping

Non-obvious Salesforce platform behaviours that cause real production problems when mapping CSV columns to fields.

---

## Gotcha 1: Bulk API V2 headers are case-sensitive; Data Loader's are not

**What happens:** a CSV with header `accountid` loads cleanly via Data Loader UI (which matches case-insensitively against `AccountId`). The same CSV piped through a custom Bulk API V2 client (`POST /services/data/vXX.X/jobs/ingest`) either errors with `InvalidBatch — column not found` or silently writes null to `AccountId` while the column is dropped, depending on the client.

**When it occurs:** any time a CSV authored for Data Loader is reused in a CI pipeline, sfdx automation, or a custom integration that hits the Bulk V2 ingest REST endpoint directly.

**How to avoid:** author every CSV header in the **exact field API name casing** — `Id`, `AccountId`, `My_Field__c`, `npe01__Payment_Method__c`. Treat lower-case headers as a bug. The pre-load checker flags case mismatches.

---

## Gotcha 2: Datetime without timezone applies the loading user's profile TZ, silently

**What happens:** the CSV cell is `2026-04-28T09:00:00`. The loading user's profile TZ is `America/Los_Angeles`. Salesforce stores the datetime as `2026-04-28T16:00:00Z` (UTC). A user in `Asia/Kolkata` later opens the record and sees `2026-04-28T21:30:00 IST`. The "9 AM" intent is gone.

**When it occurs:** every load where the source system exports naive datetimes (no offset, no `Z`). Excel, in particular, strips timezones when CSVs are round-tripped through it.

**How to avoid:** export with explicit ISO 8601 offsets — `2026-04-28T09:00:00-07:00` or `2026-04-28T16:00:00Z`. If the source cannot include offsets, document the assumed TZ in the load runbook and ensure the loading user's profile TZ matches that assumption (`Setup → Users → loader user → Time Zone`).

---

## Gotcha 3: Empty cell vs `#N/A` vs absent column — three different behaviours

**What happens:**

- **Bulk V1, blank cell, "Insert Null Values" off:** field is left unchanged on update, defaulted on insert.
- **Bulk V1, blank cell, "Insert Null Values" on:** field is set to null.
- **Bulk V1, cell = `#N/A`:** field is set to null regardless of the checkbox.
- **Bulk V2, blank cell:** field is set to null on update, errors on insert if non-nillable.
- **Bulk V2, cell = `#N/A`:** literal string `#N/A` is written. There is no null sentinel in V2.
- **Column absent from CSV entirely:** field default fires on insert; field is untouched on update.

**When it occurs:** every cross-tool migration. A team prototypes with Data Loader UI in V1 mode, perfects the CSV, then ships it to a Bulk V2 pipeline — and the `#N/A` sentinels they relied on now write the literal string into Long Text Area fields.

**How to avoid:** pick the target API mode (V1 or V2) and pre-process the CSV for that mode. For V2, never write `#N/A` — leave the cell blank if you want null. For "leave field unchanged" semantics on update, **drop the column from the CSV entirely** rather than blanking it.

---

## Gotcha 4: Field default does NOT fire when the column is present-but-blank

**What happens:** a custom field `Created_From__c` has Default Value `"CSV Import"`. The CSV contains a `Created_From__c` column with all rows blank. The expectation is that all rows get `"CSV Import"` from the default. The reality: all rows store null (V2) or are unchanged (V1), and the default never fires.

**When it occurs:** any insert where the loader thinks "I'll put the column in the CSV but leave it blank to use the default." That is not how Salesforce defaults work — defaults fire only when the field is **absent from the request payload**.

**How to avoid:** if you want the field default to apply, **omit the column from the CSV entirely**. To explicitly populate, write the value in every row. There is no middle ground.

---

## Gotcha 5: FLS-hidden fields drop silently — green job, missing data

**What happens:** the loading user's profile has Field-Level Security `Read-Only` (or no access) on `Account.Annual_Revenue__c`. The CSV contains an `Annual_Revenue__c` column with values. The job completes successfully — Bulk API V2 returns `state: JobComplete` with all rows in `processed` and zero in `failed`. The loaded records have null on `Annual_Revenue__c`. No per-row error, no warning.

**When it occurs:** any load run as a non-System Administrator user, especially after a permission set was revoked between dev and prod, or after a managed package update changed FLS defaults.

**How to avoid:** before any production load, run a "describe with FLS" check — the user running the load must have `updateable=true` (insert) or `updateable=true` (update) on every mapped field. The pre-load checker can be extended to consume a user's effective permission set and flag this. Always run a post-load diff SOQL query confirming the key fields are non-null.

---

## Gotcha 6: Polymorphic External ID upsert needs explicit type, not just field

**What happens:** a CSV header `Who.External_Id__c` is written with the intent "upsert WhoId by my custom External_Id__c that exists on both Lead and Contact." Bulk API V2 rejects every row with `InvalidBatch — relationship Who is polymorphic, type required`.

**When it occurs:** any Task or Activity load where the source data does not pre-classify rows as Lead-bound or Contact-bound.

**How to avoid:** add a discriminator column in the source export, then split into two columns: `Who.Lead.External_Id__c` and `Who.Contact.External_Id__c`. Each row populates exactly one. The pre-load checker flags `Who.<field>` (without a type) as a polymorphic-prefix error.

---

## Gotcha 7: Namespace-prefixed fields require the prefix in the CSV header

**What happens:** a managed package installed `npe01__Payment_Method__c` on Opportunity. A CSV with header `Payment_Method__c` (no prefix) loads via Data Loader. The job reports green. The field stores null. The column was silently unmapped because no `Payment_Method__c` field exists on Opportunity in this org.

**When it occurs:** any org with NPSP, EDA, FSC, Health Cloud, CPQ, or any managed package whose fields you intend to populate via CSV.

**How to avoid:** pull the describe and use the prefixed API name verbatim in the header — `npe01__Payment_Method__c`. The pre-load checker flags un-prefixed names that resolve to a prefixed field.

---

## Gotcha 8: `RecordType.DeveloperName` works in Data Loader, not in raw Bulk V2 ingest

**What happens:** a CSV uses `RecordType.DeveloperName` as the Record Type binding column. It loads fine via Data Loader UI. Ported to a custom Bulk V2 client, the column is rejected because the raw `/jobs/ingest` endpoint does not support relationship-name resolution for `RecordType` (only for true reference fields with an indexed external-id target).

**When it occurs:** migrating a Data Loader workflow to a CI pipeline.

**How to avoid:** pre-resolve the Record Type Id with SOQL, write the 18-char Id into a `RecordTypeId` column in the CSV, and load. Cache the lookup table in the pipeline.
