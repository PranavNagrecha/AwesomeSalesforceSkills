# Examples — DevOps Center Pipeline

## Example 1: Admin Team Moving from Change Sets to DevOps Center

**Scenario:** A two-person Salesforce admin team at a mid-market company has been using outbound change sets for three years. They have a Developer Pro sandbox (Dev) and production. Changes frequently arrive in production missing dependent components because change sets have no dependency checking. They want to move to a tracked, auditable release process without hiring a developer.

**Problem:** Change sets do not track which org a component came from, do not detect conflicts between concurrent changes, and leave no audit trail. Two admins modifying the same flow simultaneously will silently overwrite each other's work.

**Solution:**

Step 1 — Install DevOps Center from AppExchange and enable it in Setup.

Step 2 — Assign the DevOps Center Admin permission set to both admins.

Step 3 — Connect to GitHub using the GitHub OAuth flow in DevOps Center Setup. Create a new repository named `sf-org-config`.

Step 4 — Create a pipeline with two stages:
- Stage 1: `Development` — mapped to the Developer Pro sandbox
- Stage 2: `Production` — mapped to the production org

DevOps Center automatically creates the `main` branch for Production and a `stage/development` branch for the Dev sandbox.

Step 5 — For each change request (e.g., "add a new Opportunity stage"), the admin creates a Work Item titled accordingly. DevOps Center creates a feature branch (`feature/add-opportunity-stage`) automatically when the Work Item is started.

Step 6 — The admin makes changes in the Dev sandbox. DevOps Center tracks them via source tracking and associates them with the active Work Item.

Step 7 — The admin marks the Work Item as Ready to Promote. They promote it to Production. DevOps Center opens a pull request from the feature branch to `main`, runs the Metadata API deployment to production, and merges the PR on success.

**Why it works:** Each change is tracked to a named Work Item and a Git branch. If the deployment fails, the error appears in Deployment Status in Setup. The Git history provides a permanent audit trail. No more silent overwrites — if two Work Items touch the same flow, DevOps Center flags the conflict before deployment.

---

## Example 2: Multi-Developer Sprint with Bundled Promotions

**Scenario:** A team of three developers is running two-week sprints. Sprint 3 has four Work Items: a new custom object, a related flow, a permission set update, and an LWC component. The custom object Work Item and the flow Work Item share the same object's field metadata. If the flow is promoted before the object, the deployment fails because the field it references does not yet exist in QA.

**Problem:** Promoting Work Items individually in sequence is fragile. A developer promotes the flow before the object is ready, the QA deployment fails, and the team spends time diagnosing a dependency error rather than a logic error.

**Solution:**

Step 1 — All four Work Items are in the Development stage and marked Ready to Promote.

Step 2 — The release manager navigates to the QA stage in DevOps Center and creates a Bundle containing all four Work Items.

Step 3 — DevOps Center merges all four feature branches into the QA stage branch. Because the custom object and flow branches both touch the same field metadata, a conflict is flagged immediately. DevOps Center links to the GitHub pull request.

Step 4 — The developer resolves the conflict in GitHub: the flow's field reference is updated to match the canonical definition from the custom object Work Item. The PR is merged.

Step 5 — The Bundle promotion to QA proceeds. All four components arrive in QA together in a single deployment.

Step 6 — QA passes. The same Bundle is promoted to UAT, then to Production. Each promotion is one deployment event with one GitHub PR and one audit record.

**Why it works:** Bundling forces all dependency and conflict issues to surface at the bundle-creation step, not mid-pipeline. The entire sprint's work travels as one unit, reducing the risk of partial deployments where some components are in production but their dependencies are not.

---

## Anti-Pattern: Mixing SFDX CLI Deployments with DevOps Center

**What practitioners do:** A developer using the Salesforce CLI runs `sf project deploy start --source-dir force-app/main/default/classes` to quickly push an Apex fix to the QA sandbox that is also managed as a DevOps Center pipeline stage.

**What goes wrong:** The CLI deployment bypasses DevOps Center entirely. The Apex class is now in the QA org but its version does not match the feature branch in GitHub. When the next Work Item is promoted to QA, DevOps Center compares the org state to the GitHub branch and detects a drift. Subsequent promotions may overwrite the CLI-deployed fix, or the promotion fails with a confusing metadata conflict that has no corresponding Work Item.

**Correct approach:** All changes to orgs managed by a DevOps Center pipeline must go through DevOps Center Work Items. If a quick fix is needed, create a Work Item for it, make the change in the Development org, and promote it through the pipeline. The extra two minutes of overhead prevents state drift that can take hours to diagnose.
