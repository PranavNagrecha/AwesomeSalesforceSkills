# Examples — Data Seeding For Testing

## Example 1: CI Pipeline with sf data import tree

**Context:** A development team uses scratch orgs in GitHub Actions to run integration tests. Each pipeline run needs a fresh Account → Contact → Opportunity hierarchy loaded before tests execute.

**Problem:** Tests were using `@isTest(SeeAllData=true)` which worked locally but failed in CI because scratch orgs have no production data.

**Solution:**
1. Created `test-data/Account.json` and `test-data/Contact.json` with `@sf_reference_id` parent-child links.
2. Created `test-data/plan.json` with Account first, Contact second.
3. In GitHub Actions workflow: `sf data import tree --plan test-data/plan.json --target-org $SCRATCH_ORG_ALIAS`
4. Tests use `@testSetup` with factory methods that query records by name.

```json
[
  {"sobject": "Account", "saveRefs": true, "resolveRefs": false, "files": ["Account.json"]},
  {"sobject": "Contact", "saveRefs": true, "resolveRefs": true, "files": ["Contact.json"]}
]
```

**Why it works:** `sf data import tree` resolves parent-child references using `@sf_reference_id` cross-file linking. Each scratch org gets an identical starting data state regardless of when it was created.

---

## Example 2: CumulusCI Dataset for Staging Sandbox

**Context:** A financial services org needed realistic Account and Contact data in their staging sandbox for UAT, but could not copy production data due to PII compliance requirements.

**Problem:** Manually created test data was unrealistic and inconsistent between sandbox refreshes. Manual creation took 2 hours per refresh cycle.

**Solution:**
1. Created CumulusCI dataset configuration with field masking rules for Email, Phone, and SSN fields.
2. Ran `cci task run capture_dataset --org production --dataset financial_uat` to extract and anonymize records.
3. Stored dataset files in source control.
4. After each sandbox refresh: `cci task run load_dataset --org staging --dataset financial_uat` as part of post-refresh automation.

**Why it works:** CumulusCI `capture_dataset` preserves relationship structure and data volume while applying configured field masking. The dataset is version-controlled and reproducible across any sandbox refresh.

---

## Anti-Pattern: Using SeeAllData=true Instead of Test Data Factory

**What practitioners do:** Add `@isTest(SeeAllData=true)` to test classes to access existing records rather than building a test data factory.

**What goes wrong:** Tests pass locally in the developer's sandbox but fail in CI scratch orgs which have no data. Additionally, if `@testSetup` is also present on the class, it is silently ignored — tests use production data and give false confidence.

**Correct approach:** Remove `SeeAllData=true`. Create a Test Data Factory class with static helper methods. Use `@testSetup` to create isolated records before each test class runs.
