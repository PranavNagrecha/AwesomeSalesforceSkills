# LLM Anti-Patterns — Industries Data Migration

Common mistakes AI coding assistants make when generating or advising on Industries Data Migration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending a Flat Single-Pass Upsert Anchored Only on Account External ID

**What the LLM generates:**

```
# Recommended approach: load all policy objects in a single upsert
# Use Account.Migration_ID__c as the anchor for all lookups

upsert InsurancePolicy AccountId:Account.Migration_ID__c from policy_file.csv
upsert InsurancePolicyCoverage InsurancePolicyId:Account.Migration_ID__c from coverage_file.csv
```

**Why it happens:** LLMs generalize from standard Salesforce migration patterns where Account is the master record and most objects reference it directly. They do not recognize that InsurancePolicyCoverage references InsurancePolicy (not Account) and that Account external ID cannot serve as a proxy parent reference for objects two levels down the hierarchy.

**Correct pattern:**

```
# Each tier requires its own external ID field
# Tier 1: Account (own key: Account_External_ID__c)
# Tier 2: InsurancePolicy (own key: Policy_External_ID__c; parent ref: Account_External_ID__c)
# Tier 3: InsurancePolicyCoverage (own key: Coverage_External_ID__c; parent ref: Policy_External_ID__c)

upsert InsurancePolicy Policy_External_ID__c from insurance_policy.csv
# Confirm 0 errors before proceeding
upsert InsurancePolicyCoverage Coverage_External_ID__c from insurance_policy_coverage.csv
# InsurancePolicyCoverage.csv references Policy_External_ID__c as the parent field
```

**Detection hint:** Flag any migration plan that uses Account external ID as the parent reference in an InsurancePolicyCoverage, InsurancePolicyTransaction, BillingStatement, ServicePoint, or ServiceAccount load file. These objects reference intermediate parents, not Account directly.

---

## Anti-Pattern 2: Loading All Object Tiers in Parallel or in a Single Combined File

**What the LLM generates:**

```python
# Load all Insurance objects simultaneously for speed
jobs = [
    load_bulk_api("account.csv", "Account"),
    load_bulk_api("policy.csv", "InsurancePolicy"),
    load_bulk_api("coverage.csv", "InsurancePolicyCoverage"),
    load_bulk_api("transaction.csv", "InsurancePolicyTransaction"),
]
await asyncio.gather(*jobs)  # parallel for efficiency
```

**Why it happens:** LLMs optimize for efficiency by default and apply async/parallel patterns from software engineering to data loading. They do not account for the referential integrity constraint that a child row cannot commit before its parent row is committed in a separate transaction.

**Correct pattern:**

```python
# Sequential execution with gate confirmation between each tier
tiers = [
    ("Account", "account.csv", "Account_External_ID__c"),
    ("InsurancePolicy", "policy.csv", "Policy_External_ID__c"),
    ("InsurancePolicyCoverage", "coverage.csv", "Coverage_External_ID__c"),
    ("InsurancePolicyTransaction", "transaction.csv", "Transaction_External_ID__c"),
]

for obj_name, file_path, external_id_field in tiers:
    job_id = submit_bulk_api_job(obj_name, file_path, external_id_field)
    result = wait_for_completion(job_id)
    assert result.failed_records == 0, f"Tier {obj_name} has errors — halt migration"
```

**Detection hint:** Flag any migration architecture that submits InsurancePolicyCoverage, InsurancePolicyAsset, or ServicePoint jobs simultaneously with their parent jobs, or any code that uses `asyncio.gather`, `ThreadPoolExecutor`, or similar constructs across dependent object tiers.

---

## Anti-Pattern 3: Omitting External ID Fields on Intermediate Objects

**What the LLM generates:**

```
Migration plan:
1. Load Account with external ID Account.Ext_ID__c
2. Load InsurancePolicy — reference Account by Account.Ext_ID__c
3. Load InsurancePolicyCoverage — reference InsurancePolicy by Salesforce record ID (retrieved after step 2)
4. Load transactions — reference InsurancePolicy by Salesforce record ID
```

**Why it happens:** LLMs know that Salesforce record IDs are the native reference mechanism. They propose querying IDs after each load and using them in the next file. This appears correct but creates a fragile pipeline: the ID retrieval query must be run post-load, results must be joined back to the child file, and any re-run of the migration requires repeating the ID lookup step with the new IDs.

**Correct pattern:**

```
Migration plan:
1. Pre-migration: create external ID fields on ALL intermediate objects:
   - InsurancePolicy.Policy_External_ID__c (Text 36, Unique, External ID)
   - InsurancePolicyCoverage.Coverage_External_ID__c (Text 36, Unique, External ID)
   - InsurancePolicyTransaction.Transaction_External_ID__c (Text 36, Unique, External ID)

2. Populate these fields in source extract files before any load begins.

3. Load using upsert on external ID fields — no ID retrieval step required.
   The coverage file references Policy_External_ID__c directly; Salesforce resolves the lookup.
```

**Detection hint:** Flag any migration plan that includes a step to "retrieve Salesforce IDs after load and join to child file." This is a signal that external ID fields were not created for intermediate objects.

---

## Anti-Pattern 4: Treating InsurancePolicy.Status as Writable Without Validation Bypass Consideration

**What the LLM generates:**

```csv
# Load file for InsurancePolicy
Policy_External_ID__c,AccountId:Account_External_ID__c,Status,EffectiveDate,ExpirationDate
POL-001,ACC-100,Cancelled,2020-01-01,2021-01-01
POL-002,ACC-101,Expired,2019-06-01,2020-06-01
```

The LLM generates this file and submits it without noting that validation rules may block inserting policies in terminal statuses, or that BillingStatement child records for cancelled policies require additional bypass configuration.

**Why it happens:** LLMs generate syntactically correct CSV without awareness of org-specific validation rules that check Status at insert time. They assume all field values that are valid picklist options are also valid for bulk insert.

**Correct pattern:**

```
Pre-load validation checklist for non-active InsurancePolicy records:
1. Query all active validation rules on InsurancePolicy that reference the Status field.
2. For each such rule, add a bypass condition: AND NOT(Migration_Bypass__c = TRUE)
3. Add Migration_Bypass__c = TRUE to the load file for all non-active policies.
4. After load is confirmed, run: UPDATE InsurancePolicy SET Migration_Bypass__c = FALSE WHERE Migration_Bypass__c = TRUE
5. Extend the same bypass analysis to BillingStatement if billing history for non-active policies is in scope.
```

**Detection hint:** Flag any migration plan that loads InsurancePolicy records with Status values of Cancelled, Expired, Lapsed, or similar without a corresponding validation rule bypass step.

---

## Anti-Pattern 5: Ignoring the Three-Tier E&U Hierarchy and Loading ServicePoint Before Premise

**What the LLM generates:**

```
E&U migration order:
1. Load Account
2. Load ServicePoint (includes Premise address fields inline on ServicePoint)
3. Load ServiceAccount
```

The LLM conflates Premise (a distinct object representing the physical service location) with an address field on ServicePoint, omitting Premise as a separate load tier entirely.

**Why it happens:** LLMs are not always aware that Energy and Utilities Cloud uses Premise as a distinct intermediate object between Account and ServicePoint. They collapse the three-tier hierarchy into two tiers by assuming ServicePoint carries its own address fields. This works in generic CRM thinking but does not match the E&U data model.

**Correct pattern:**

```
E&U migration order (four explicit tiers):
Tier 1: Account (upsert on Account_External_ID__c)
Tier 2: Premise (upsert on Premise_External_ID__c; references Account_External_ID__c)
Tier 3: ServicePoint (upsert on ServicePoint_External_ID__c; references Premise_External_ID__c)
Tier 4: ServiceAccount (upsert on ServiceAccount_External_ID__c; references Account_External_ID__c AND ServicePoint_External_ID__c)
```

**Detection hint:** Flag any E&U migration plan that loads ServicePoint before Premise, that omits Premise entirely, or that references Premise fields as inline address attributes on ServicePoint rather than as a separate parent object.

---

## Anti-Pattern 6: Assuming InsurancePolicyTransaction Can Be Loaded Before InsurancePolicyCoverage

**What the LLM generates:**

```
Insurance migration order:
1. Account
2. InsurancePolicy
3. InsurancePolicyTransaction (premium payments and endorsements loaded early)
4. InsurancePolicyCoverage (coverages loaded after transactions)
```

**Why it happens:** LLMs reason from general domain knowledge that transactions are logically "after" coverages but may produce a load order that looks valid for transactions that only reference InsurancePolicy (not InsurancePolicyCoverage). They do not flag that some InsurancePolicyTransaction records reference specific coverages, and that loading transactions before coverages exist creates lookup failures for those records.

**Correct pattern:**

```
Correct order:
1. Account
2. InsurancePolicy
3. InsurancePolicyParticipant (parallel with InsurancePolicyAsset)
   InsurancePolicyAsset (parallel with InsurancePolicyParticipant)
4. InsurancePolicyCoverage (after both Participant and Asset are confirmed)
5. InsurancePolicyTransaction (after Coverage is confirmed)
   BillingStatement (parallel with InsurancePolicyTransaction, after Coverage is confirmed)
```

**Detection hint:** Flag any Insurance migration plan that places InsurancePolicyTransaction at tier 3 or earlier, or that loads InsurancePolicyCoverage in the same tier as or after InsurancePolicyTransaction.
