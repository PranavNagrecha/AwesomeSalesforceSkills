---
name: data-seeding-for-testing
description: "Use when creating test data for scratch orgs, sandboxes, or CI pipelines: Apex @testSetup factories, sf data import tree plans, CumulusCI datasets, Snowfakery. NOT for production data migration or ETL pipelines."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "how do I load test data into a scratch org before running tests"
  - "what is the best way to seed data for Apex unit tests in CI"
  - "how to create realistic test data for a sandbox without copying production"
  - "sf data import tree plan failing due to parent-child record order"
  - "CumulusCI dataset seeding for partial sandbox"
tags:
  - test-data
  - data-seeding
  - scratch-orgs
  - ci-cd
  - apex-testing
inputs:
  - "Target org type: scratch org, developer sandbox, or partial/full sandbox"
  - "Existing object relationships and required parent records"
  - "Volume of records needed and whether referential integrity is required"
outputs:
  - "Recommended seeding layer (Apex @testSetup vs sf data tree vs CumulusCI)"
  - "sf data import plan JSON or Apex test data factory pattern"
  - "CumulusCI dataset or Snowfakery recipe if applicable"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Data Seeding For Testing

This skill activates when a practitioner needs to create, load, or manage test data for Salesforce development and testing environments. It covers the three primary seeding layers — Apex `@testSetup` factories for unit tests, `sf data import tree` plans for scratch orgs and developer sandboxes, and CumulusCI datasets with Snowfakery for partial and full sandboxes.

---

## Before Starting

Gather this context before working on anything in this domain:

- Identify the target org type (scratch org, developer sandbox, partial sandbox, full sandbox) — this determines which seeding layer is appropriate.
- Determine record volume and relationship depth — large volumes (>200MB JSON) exceed the `sf data import tree` limit and require CumulusCI or Bulk API.
- Confirm whether data must survive across test transactions (`@testSetup`) or exist persistently in the org (data plans, datasets).

---

## Core Concepts

### Three Seeding Layers

Salesforce has three distinct seeding layers, each suited to a different context:

1. **Apex `@testSetup`** — creates records in-memory within the test transaction. Records are rolled back after every test method. Use for unit and integration tests that run in Apex. Limit: `@isTest(SeeAllData=true)` is incompatible with `@testSetup` and should never be used together.
2. **`sf data import tree` plan (JSON)** — imports hierarchical record trees from JSON files into a target org. Cap is 200MB of JSON per plan execution. Supports parent-child relationships via `@sf_reference_id`. Use for scratch orgs and developer sandboxes in CI pipelines.
3. **CumulusCI datasets + Snowfakery** — designed for partial and full sandboxes where realistic, anonymized, or synthetic volumes of data are needed. CumulusCI `capture_dataset` extracts and anonymizes records; Snowfakery generates synthetic records from YAML recipes.

### `@isTest(SeeAllData=true)` Incompatibility

`@isTest(SeeAllData=true)` is incompatible with `@testSetup`. If both annotations appear on the same class, `@testSetup` methods are ignored and the class sees production data — this is a silent failure. The correct pattern is to always use `@testSetup` for isolated data and never mix with `SeeAllData=true`.

### Scratch Org Snapshots

Scratch Org Snapshots (available with Dev Hub) capture both metadata and data state of a scratch org and allow it to be cloned. Snapshots reduce CI pipeline time by eliminating repeated data seeding. Each snapshot consumes an allocation from the Dev Hub snapshot limit (25 active snapshots by default). Snapshots are not a replacement for data seeding — they pre-bake a seeded state that can be rapidly re-used.

### `sf data import tree` Plan JSON

A plan JSON file describes the import sequence for related objects. Parent objects must appear before child objects in the plan array. Each record in the source JSON must have an `@sf_reference_id` (a client-side string) that allows child records to reference parent records by ID within the same import. The `sf data import tree` command resolves these references at import time and substitutes real Salesforce IDs.

---

## Common Patterns

### Apex Test Data Factory

**When to use:** Unit and integration tests in Apex that need isolated records not shared with other tests.

**How it works:**
```apex
@isTest
public class AccountFactory {
    public static Account create(String name) {
        Account a = new Account(Name = name, BillingCountry = 'US');
        insert a;
        return a;
    }

    public static List<Account> createBulk(Integer count) {
        List<Account> accts = new List<Account>();
        for (Integer i = 0; i < count; i++) {
            accts.add(new Account(Name = 'Test Account ' + i, BillingCountry = 'US'));
        }
        insert accts;
        return accts;
    }
}

@isTest
private class OpportunityServiceTest {
    @testSetup
    static void setup() {
        Account a = AccountFactory.create('ACME');
        Opportunity o = new Opportunity(
            Name = 'Test Opp', AccountId = a.Id,
            StageName = 'Prospecting', CloseDate = Date.today().addDays(30)
        );
        insert o;
    }

    @isTest
    static void testOpportunityStageUpdate() {
        Opportunity o = [SELECT Id, StageName FROM Opportunity LIMIT 1];
        // test logic here
    }
}
```

**Why not `SeeAllData=true`:** Test isolation is broken — tests pass locally but fail in fresh scratch orgs because production data is not present. CI pipelines will be unreliable.

### sf data import tree Plan

**When to use:** Loading hierarchical records into a scratch org or developer sandbox as part of a CI pipeline setup step.

**How it works:**
1. Create source JSON files for each object (e.g., `Account.json`, `Contact.json`).
2. Use `@sf_reference_id` in parent records, reference them in child records:

```json
// Account.json
{
  "records": [
    {
      "attributes": {"type": "Account", "referenceId": "AccountRef1"},
      "Name": "ACME Corp",
      "BillingCountry": "US"
    }
  ]
}
```

```json
// Contact.json
{
  "records": [
    {
      "attributes": {"type": "Contact", "referenceId": "ContactRef1"},
      "FirstName": "Jane",
      "LastName": "Doe",
      "AccountId": "@AccountRef1"
    }
  ]
}
```

3. Create a plan JSON (`plan.json`):
```json
[
  {
    "sobject": "Account",
    "saveRefs": true,
    "resolveRefs": false,
    "files": ["Account.json"]
  },
  {
    "sobject": "Contact",
    "saveRefs": true,
    "resolveRefs": true,
    "files": ["Contact.json"]
  }
]
```

4. Run: `sf data import tree --plan test-data/plan.json --target-org MyScratchOrg`

**Why not Bulk API:** For small volumes (< 200MB), `sf data import tree` handles parent-child relationships automatically. Bulk API requires manual ID resolution.

### CumulusCI Dataset Capture and Load

**When to use:** Partial or full sandboxes where anonymized production-like data is needed, or where Snowfakery synthetic data generation is required for realistic volumes.

**How it works:**
- Capture: `cci task run capture_dataset --org qa --dataset my_dataset` — extracts records, anonymizes PII fields, stores as dataset files.
- Load: `cci task run load_dataset --org staging --dataset my_dataset` — loads the captured dataset into target org.
- Snowfakery: define a YAML recipe and use `cci task run generate_and_load_from_yaml` for fully synthetic data at scale.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Apex unit or integration tests | `@testSetup` + Test Data Factory | Records are isolated per test class, rolled back automatically |
| Scratch org CI pipeline setup | `sf data import tree` with plan JSON | Declarative, version-controlled, supports parent-child refs |
| Record volume > 200MB or complex relationships | CumulusCI datasets or Bulk API | Exceeds `sf data tree` limit; CumulusCI handles complex graphs |
| Partial/full sandbox with realistic data | CumulusCI capture_dataset + Snowfakery | Extracts and anonymizes real data or generates synthetic records |
| Quick scratch org with pre-seeded data (repeated use) | Scratch Org Snapshot | Eliminates repeated seeding cost; consumes snapshot allocation |
| Anonymized production data for staging | CumulusCI capture_dataset with field masking | Preserves data shape, removes PII per GDPR/CCPA requirements |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. Identify target org type (scratch org, developer sandbox, partial sandbox) to determine the appropriate seeding layer.
2. For unit tests: create a Test Data Factory class with static helper methods; use `@testSetup` in test classes; never mix with `@isTest(SeeAllData=true)`.
3. For scratch org CI: export source JSON files per object, define parent-child references using `@sf_reference_id`, create a plan.json, run `sf data import tree --plan`.
4. For sandboxes with volume: use CumulusCI `capture_dataset` for production-sourced anonymized data, or Snowfakery YAML recipes for fully synthetic data.
5. Validate the seeded data by running a SOQL spot-check query after each import to confirm record counts and relationship integrity.
6. For repeated CI use: evaluate Scratch Org Snapshots to pre-bake seeded state and reduce pipeline time.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] `@testSetup` methods exist in test classes that need shared data — no `SeeAllData=true` mixing
- [ ] `sf data import tree` plan has parent objects listed before child objects in the plan array
- [ ] All `@sf_reference_id` values in child JSON files match the `referenceId` values in parent JSON files
- [ ] Total plan JSON size is under 200MB
- [ ] CumulusCI dataset captures PII-sensitive fields with masking configured
- [ ] Scratch Org Snapshot consumption has been accounted for against Dev Hub limits

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **`@isTest(SeeAllData=true)` silently disables `@testSetup`** — If both annotations appear on the same class, the `@testSetup` method is ignored without an error. Tests appear to pass locally (using production data) but fail in CI scratch orgs where production data is absent.
2. **`sf data import tree` order determines ID resolution** — Child records that reference a parent using `@sf_reference_id` must appear in a later plan step than the parent. If a child step has `resolveRefs: true` but the parent step has not yet run, the import fails with a reference resolution error.
3. **Scratch Org Snapshots consume allocations even if the snapshot is inactive** — Snapshots count against the 25-snapshot Dev Hub limit from the moment of creation until explicitly deleted. Teams that create snapshots per-branch in CI exhaust allocations quickly without a cleanup policy.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Test Data Factory class | Reusable Apex class with static helper methods for creating test records |
| sf data import tree plan | plan.json + source JSON files defining the record hierarchy for CLI import |
| CumulusCI dataset | Captured and anonymized dataset files loadable via CumulusCI `load_dataset` |
| Snowfakery recipe | YAML file defining synthetic record generation logic for large-volume seeding |

---

## Related Skills

- scratch-org-management — lifecycle management of scratch orgs that consume the seeded data
- continuous-integration-testing — CI pipeline integration that runs after data seeding completes
- sandbox-refresh-and-templates — sandbox refresh automation that may trigger data seeding post-copy
