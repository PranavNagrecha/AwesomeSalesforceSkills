# Gotchas — Gift History Import

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: Direct Opportunity Insert Produces a Successful Import with a Broken Data Model

Importing gift records directly into the Opportunity object via Data Loader or the standard import wizard does not trigger NPSP automation. The import completes with a green "success" status, but:
- No `npe01__OppPayment__c` payment records are created
- No Opportunity Contact Roles (soft credits) are created
- GAU Allocations are not created
- Household rollup totals (`Total_Gifts__c` on the Account) remain stale

This is the most dangerous failure mode because it produces no errors. The data appears to be in Salesforce, but the NPSP data model is structurally incomplete for every imported record.

**Fix:** Always use `npsp__DataImport__c` staging + BDI batch for NPSP gift imports. If direct imports were already done, plan a remediation batch using NPSP's BDI re-processing capability or manual Apex batch to create the missing related records.

---

## Gotcha 2: BDI Silently Ignores Custom Fields Without Advanced Mapping

If custom fields are included in the DataImport__c staging rows and Advanced Mapping is not enabled, BDI processes the standard fields and completes with a success status — but the custom field data is entirely ignored. There is no warning or error message indicating that custom mapping was skipped.

This means: all 50,000 records import with OK status, custom payment reference numbers or custom GAU fields are blank on every output record, and there is no automated way to detect the data loss without running post-import SOQL validation queries.

**Fix:** Enable Advanced Mapping before staging any records. Configure field maps before running BDI. Run validation SOQL immediately after import to confirm custom field values are populated.

---

## Gotcha 3: NPSP Contact Matching Creates Duplicate Contacts for Variant Name Spellings

BDI uses NPSP Contact Matching Rules to find existing donor records before creating new ones. If the source data contains variant spellings of the same donor name (Bob Smith vs. Robert Smith, or email address differences), BDI may create duplicate Contact records for the same individual.

Duplicates created during a gift import are particularly difficult to clean up because the newly created Contacts already have Opportunities, payments, and OCRs attached. Standard merge leaves orphaned related records.

**Fix:** Run deduplication on the source data before staging. If migrating from a system where donor IDs are known, use an External ID field on Contact and stage gifts with the External ID rather than name/email matching to guarantee exact donor matching.

---

## Gotcha 4: 50,000 Row and 100 MB File Limits Are Per-Batch, Not Per-Session

The NPSP Data Importer file size limit (100 MB) and record limit (50,000) apply per batch run, not to the DataImport__c object as a whole. However, DataImport__c rows that are staged but not yet processed accumulate in the object. A very large backlog of unprocessed staging rows can slow BDI batch performance significantly.

**Fix:** Process each chunk of staging rows with a BDI batch before inserting the next chunk. Do not allow DataImport__c to accumulate more than one batch worth of unprocessed rows at a time.

---

## Gotcha 5: Re-Processing Already-Imported DataImport__c Rows Requires Status Reset

If a DataImport__c row was processed by BDI (Status = Imported), BDI will not re-process it on a subsequent run even if the underlying Opportunity needs to be corrected. BDI skips rows that have already been imported.

To re-process a row: reset `npsp__Status__c` to blank (null) and `npsp__ImportedDate__c` to null. This reactivates the row for the next BDI batch run. However, if the Opportunity was already created, BDI will attempt to match or update it based on matching rules rather than creating a new record.

**Fix:** For correction scenarios, delete the incorrectly created Opportunity first, then reset the DataImport__c row status, then re-run BDI.
