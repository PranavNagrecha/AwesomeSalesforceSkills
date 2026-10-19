# Examples — DevOps Center Pipeline

## Example 1: Admin Team Moving from Change Sets to DevOps Center

**Scenario:** A two-person Salesforce admin team has been using outbound change sets for three years. They have a Developer Pro sandbox (Dev) and production. Changes frequently arrive in production missing dependent components. They want a tracked, auditable release process without hiring a developer.

**Problem:** Change sets do not record which work a component belongs to, do not detect conflicts between concurrent changes, and leave no branch history. Two admins modifying the same flow silently overwrite each other's work.

**Solution:**

Step 1 — In production, deploy `SourceTrackingSettings` with `enableSourceTrackingSandboxes` set to true, then refresh the Developer Pro sandbox so it starts tracking (an existing sandbox does not pick up the setting until it is created or refreshed).

Step 2 — Enable DevOps Center, assign its permissions to both admins, and connect the GitHub organization through the provider's Named Credential using a service account.

Step 3 — Create a pipeline with two stages: `Development` (the Developer Pro sandbox) and `Production` (its `NextStageId` is empty). Set the Production deployment test level explicitly.

Step 4 — For each change request, create a work item. It gets its own branch (the object reference's example name is `feature/WI-000001`).

Step 5 — Make the change in the Dev sandbox, commit it to the work item (status moves to `IN_REVIEW`, with a pull request), then mark it `READY_TO_PROMOTE`.

Step 6 — Promote. If the promotion does not finish, query the newest `DevopsRequestInfo` record for the work item's promotion and read `ErrorDetails`.

**Why it works:** Each change is tied to a work item and a branch, so the history is permanent and reviewable. When two work items touch the same flow, the second one stops at `MERGE_CONFLICT` instead of overwriting the first.

---

## Example 2: Multi-Developer Sprint with a Bundling Stage

**Scenario:** A team of three developers runs two-week sprints through Dev → QA → UAT → Production. Sprint 3 has four work items: a custom object, a flow that uses its new field, a permission set update, and an LWC.

**Problem:** Promoting the flow before the object fails in QA because the field does not exist there yet. Promoting all four separately to production produces four deployments and four chances for a partial release.

**Solution:**

Step 1 — Combine the object and flow work items before promotion (recorded as a `REBASE_AND_COMBINE` request); the flow item moves to `COMBINED` and its changes travel with the object item.

Step 2 — Promote the three remaining items individually into QA as each is ready. QA's deployment uses `RunSpecifiedTests` with the sprint's test classes, not `Default`.

Step 3 — UAT is the bundling stage (`IsBundled = true`). Once all three items are promoted into UAT, they promote onward to Production together.

Step 4 — After the UAT promotion, back sync the developers' environments from UAT so the next sprint starts from current metadata.

**Why it works:** The dependency is resolved by combining, before any stage sees half of it; the release is assembled and tested as a unit in UAT; and the QA test level catches test failures two stages before production.

---

## Example 3: Stage Export Checked Before Go-Live

The stage export used by the checker is plain `sf data query --json` output:

```json
{
  "status": 0,
  "result": {
    "records": [
      {"Id": "0Xs000000000001", "Name": "Development", "DevopsPipelineId": "0Xp000000000001", "NextStageId": "0Xs000000000002", "IsBundled": false, "DevOpsEnvironmentId": "0Xe000000000001"},
      {"Id": "0Xs000000000002", "Name": "UAT", "DevopsPipelineId": "0Xp000000000001", "NextStageId": "0Xs000000000003", "IsBundled": true, "DevOpsEnvironmentId": "0Xe000000000002"},
      {"Id": "0Xs000000000003", "Name": "Production", "DevopsPipelineId": "0Xp000000000001", "NextStageId": null, "IsBundled": false, "DevOpsEnvironmentId": "0Xe000000000003"}
    ]
  }
}
```

The record IDs are placeholders; the checker only compares them with each other.

---

## Anti-Pattern: Mixing SFDX CLI Deployments with DevOps Center

**What practitioners do:** A developer runs `sf project deploy start --source-dir force-app/main/default/classes` to push an Apex fix straight to the QA sandbox that is also a DevOps Center stage.

**What goes wrong:** The class is now in the QA org but not in the QA stage branch. The next promotion into QA can overwrite the fix, or a later work item that touches the class hits a conflict with no corresponding work item behind it.

**Correct approach:** Route every change to a pipeline org through a work item, even a two-line fix. If an environment has already drifted, recover with a back sync or rebase rather than editing stage branches by hand.
