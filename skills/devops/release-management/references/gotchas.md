# Gotchas — Release Management

## 1. Quick Deploy Returns a New Deploy ID (Not the Validation ID)

**What happens:** You run `sf project deploy quick --job-id 0Af...validationId`. The command immediately returns a NEW deploy request ID. If you monitor the original validation ID, it shows "Succeeded" (from the validation), giving a false impression that the quick deploy is complete.

**Why:** Quick Deploy creates a separate deployment job from the validation. The validation job's status is permanently "Succeeded" because it did succeed — as a checkOnly deploy. The actual deployment is a new job with a different ID.

**How to avoid:** Save the ID returned by the `sf project deploy quick` command, not the validation ID. Monitor that new ID with `sf project deploy report --job-id <newId>`.

---

## 2. Sandbox Preview is Per-Sandbox, Not Per-Org

**What happens:** A developer refreshes their personal Developer sandbox in August and gets the next Salesforce release (e.g., Winter '26 preview). The rest of the team is still on Summer '25. Metadata created by the developer — especially new metadata types introduced in Winter '26 — cannot be deployed to the team's non-preview sandboxes.

**Why:** Salesforce opens sandbox preview opt-in 4–6 weeks before the production upgrade. Each sandbox refresh after preview opens goes to the preview release. Sandboxes refreshed before preview opens stay on the current release.

**How to avoid:** Coordinate sandbox refreshes during the period immediately before preview opens. Designate exactly one sandbox for preview testing. Communicate to the team which sandboxes are on which release.

---

## 3. Rollback Cannot Undo Platform-Event-Triggered Data Changes

**What happens:** A release includes a Flow triggered by a Platform Event. The deployment succeeds, the Flow fires, and it creates 500 records. A defect is discovered and the deployment is rolled back. The 500 records created by the Flow remain — metadata rollback does not delete records created by automation.

**Why:** Metadata deployment (deploying old Apex/Flow) does not reverse DML that was committed by previously-running automation. The records are owned by the platform's data layer, not the metadata layer.

**How to avoid:** For releases that include automation creating records on activation, pre-plan a data compensating script. Document in release notes: "If rollback is triggered after [component X] deploys, run data cleanup script [Y] to remove created records."

---

## 4. RunSpecifiedTests Coverage Is Per-Class, Not Org-Wide

**What happens:** A deployment with `--test-level RunSpecifiedTests --tests MyNewTest` passes with 80% org-wide coverage but fails because `MyNewTrigger` only has 60% coverage from `MyNewTest` alone. The deployment fails with "Insufficient code coverage".

**Why:** `RunSpecifiedTests` requires each Apex class and trigger in the **deployment package** to have ≥75% coverage from the specified tests. This is stricter than `RunLocalTests` which uses the org-wide aggregate.

**How to avoid:** When using `RunSpecifiedTests` for a deployment that includes triggers, ensure the specified test class covers at least 75% of every trigger in the deployment scope. Add additional test classes to the `--tests` list if a single class does not provide enough coverage.
