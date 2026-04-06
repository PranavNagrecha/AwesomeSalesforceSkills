# Gotchas — Data Seeding For Testing

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: @testSetup Is Silently Ignored When Combined with SeeAllData=true

**What happens:** If a test class has both `@isTest(SeeAllData=true)` and a `@testSetup` method, the `@testSetup` method is silently ignored. The test class runs using production org data, and the `@testSetup` records are never created. No error is thrown.

**When it occurs:** Any time both annotations appear on the same class — either because a developer added `@testSetup` to a class that already had `SeeAllData=true`, or copy-paste from an older class.

**How to avoid:** Remove `@isTest(SeeAllData=true)` entirely. Use `@testSetup` with a Test Data Factory class. Search the codebase for `SeeAllData=true` and audit each class for a co-existing `@testSetup`.

---

## Gotcha 2: sf data import tree Plan Fails When Child Step Runs Before Parent

**What happens:** `sf data import tree` throws a reference resolution error if a child record references a `@sf_reference_id` from a parent object that has not yet been imported in the current plan execution.

**When it occurs:** Plan JSON has child objects listed before parent objects in the plan array, or `resolveRefs: true` is set on a step before the referenced object's step has run.

**How to avoid:** Always list parent objects before child objects in the plan JSON array. Set `resolveRefs: true` only on steps that reference records imported in a previous step. For complex hierarchies, use multiple plan files executed in sequence.

---

## Gotcha 3: Scratch Org Snapshots Count Against Dev Hub Limits Even When Inactive

**What happens:** Each Scratch Org Snapshot created consumes one allocation from the Dev Hub's 25-snapshot default limit regardless of whether the snapshot is being used. CI pipelines that create snapshots per feature branch exhaust the limit without a cleanup policy.

**When it occurs:** Teams use snapshots to accelerate CI without implementing a snapshot lifecycle policy.

**How to avoid:** Implement an automated snapshot cleanup step in CI. Delete snapshots after the branch is merged or closed. Use `sf org delete snapshot --snapshot <name>` in the cleanup job. Monitor snapshot count with `sf org list snapshots --target-dev-hub DevHub`.

---

## Gotcha 4: sf data import tree Has a 200MB JSON Cap Per Plan Execution

**What happens:** If the total size of all JSON source files in a plan execution exceeds 200MB, the import fails with a data size limit error.

**When it occurs:** Large record sets (tens of thousands of records) imported in a single plan execution.

**How to avoid:** For volumes above 200MB, switch to CumulusCI datasets or Bulk API 2.0 jobs. Break large plans into multiple smaller plans executed sequentially, or filter source JSON to include only the records needed for the test scenario.
