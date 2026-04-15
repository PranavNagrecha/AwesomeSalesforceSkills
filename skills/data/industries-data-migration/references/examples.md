# Examples — Industries Data Migration

## Example 1: Insurance Policy Migration Failing at InsurancePolicyCoverage Tier

**Context:** A property and casualty insurer is migrating legacy policy records into Salesforce Insurance. The source system exports four files: policies, participants, coverages, and transaction history. The team loads all four files in a single Bulk API 2.0 job set, ordering rows by policy number within each file.

**Problem:** The InsurancePolicyCoverage job completes with 40% error rows. Every failed row carries the error `FIELD_INTEGRITY_EXCEPTION: InsurancePolicyId: id value of incorrect type`. Investigation reveals the InsurancePolicy job was still processing when the InsurancePolicyCoverage job started. Rows that referenced an InsurancePolicy not yet committed in the target org produced missing parent errors.

**Solution:**

```
Load sequence (separate Bulk API 2.0 jobs, each confirmed before next starts):

Job 1 — Account (upsert on Account_External_ID__c)
  Confirm: 0 error rows, total rows match source extract

Job 2 — InsurancePolicy (upsert on Policy_External_ID__c, Account_External_ID__c as parent ref)
  Confirm: 0 error rows, total rows match source extract

Job 3a — InsurancePolicyParticipant (upsert on Participant_External_ID__c)
Job 3b — InsurancePolicyAsset (upsert on Asset_External_ID__c)
  Run 3a and 3b after Job 2 is confirmed; these two can run in parallel

Job 4 — InsurancePolicyCoverage (upsert on Coverage_External_ID__c)
  Wait for both 3a and 3b to confirm before starting

Job 5 — InsurancePolicyTransaction (upsert on Transaction_External_ID__c)
  Wait for Job 4 to confirm
```

**Why it works:** Bulk API 2.0 processes rows in parallel within a batch. A coverage row and its parent policy row cannot be guaranteed to commit in the same order as their position in the file. Separate sequential jobs with explicit confirmation between each tier eliminate the race condition. Upsert on an external ID field makes the entire sequence re-runnable without creating duplicates.

---

## Example 2: Energy and Utilities ServicePoint Load Failing with Missing Premise

**Context:** A utility company is migrating service data into E&U Cloud. The migration team correctly loads Account and Premise records first, then attempts to load ServicePoint in a third job. The ServicePoint job fails with 100% error rows: `FIELD_INTEGRITY_EXCEPTION: PremiseId: id value of incorrect type`.

**Problem:** The ServicePoint load file uses Premise external IDs in a mixed-case format (`Prem-1042`, `prem-1043`) because the source extract came from two different legacy systems with different casing conventions. The Premise load file used uppercase (`PREM-1042`, `PREM-1043`). Bulk API 2.0 external ID resolution is case-sensitive; the lookup found no match and treated every ServicePoint row as a new insert attempting to resolve a non-existent parent.

**Solution:**

```python
# Pre-load normalization script (stdlib only)
import csv
import sys

def normalize_external_ids(input_path, output_path, id_columns):
    """Uppercase all external ID columns before loading."""
    with open(input_path, newline='', encoding='utf-8') as infile, \
         open(output_path, 'w', newline='', encoding='utf-8') as outfile:
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            for col in id_columns:
                if col in row and row[col]:
                    row[col] = row[col].upper()
            writer.writerow(row)

# Usage before loading ServicePoint file:
normalize_external_ids(
    'servicepoint_raw.csv',
    'servicepoint_normalized.csv',
    id_columns=['Premise_External_ID__c']
)
```

**Why it works:** Normalizing external ID columns to a consistent case (uppercase recommended) before any load job eliminates case-sensitivity mismatches. Apply this normalization to both the parent-tier file at load time and to all child-tier files that reference the same external ID values. Running the normalization script as part of the ETL pipeline prevents the issue from recurring on incremental loads.

---

## Example 3: Flat Single-Pass Upsert Using Account as the Only Anchor

**Context:** A team is asked to "keep the migration simple" and loads all InsurancePolicy, InsurancePolicyCoverage, and InsurancePolicyTransaction records in a single large CSV ordered by policy number. They use Account_External_ID__c as the only external ID field in all three files, assuming Salesforce will resolve intermediate lookups from context.

**Problem:** The load fails entirely at the InsurancePolicyCoverage rows. InsurancePolicyCoverage requires `InsurancePolicyId` — a Salesforce record ID or an external ID on InsurancePolicy itself. Account external ID is not a valid parent reference for InsurancePolicyCoverage. Every coverage row fails with a field type error. Because the entire load was in one file, the only remediation option is a full delete and reload.

**Correct approach:**

```
Step 1: Create custom external ID fields:
  - InsurancePolicy.Policy_External_ID__c (Text 36, Unique, External ID)
  - InsurancePolicyCoverage.Coverage_External_ID__c (Text 36, Unique, External ID)
  - InsurancePolicyTransaction.Transaction_External_ID__c (Text 36, Unique, External ID)

Step 2: Populate these fields in source extract files:
  - InsurancePolicy file: Account_External_ID__c (parent ref), Policy_External_ID__c (own key)
  - InsurancePolicyCoverage file: Policy_External_ID__c (parent ref), Coverage_External_ID__c (own key)
  - InsurancePolicyTransaction file: Policy_External_ID__c (parent ref), Transaction_External_ID__c (own key)

Step 3: Run separate upsert jobs in tier order, confirm each before next.
```

**Why it works:** Each object in the hierarchy needs its own external ID to serve as the parent reference anchor for the tier below it. Account external ID can only anchor direct Account children. Intermediate objects (InsurancePolicy, Premise, ServicePoint) must carry their own external ID fields to enable correct parent resolution further down the chain.
