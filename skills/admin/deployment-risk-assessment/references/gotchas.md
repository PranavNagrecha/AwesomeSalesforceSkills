# Gotchas — Deployment Risk Assessment

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: No Undo Deployment Button Exists in the Platform

**What happens:** Practitioners expect to find a rollback or "undo deployment" option in Setup or in the Deployment Status page after a deployment completes. No such mechanism exists. Once a deployment succeeds, the new metadata is the active state in the org. The prior state is gone unless it was explicitly captured before the deployment.

**When it occurs:** Any deployment that needs to be reversed. This assumption is most dangerous during incident response when a practitioner searches Setup under Deployment Status for a revert option — wasting critical time during a production outage.

**How to avoid:** Include the statement "no platform undo exists — rollback requires re-deploy" explicitly in every release runbook. Require a pre-retrieve backup of all components that will be overwritten before opening the deployment window. Train the team on the rollback procedure so the absence of a platform undo button is not a surprise under pressure.

---

## Gotcha 2: Sandbox Validation State May Not Match Production at Deployment Time

**What happens:** A deployment validates successfully in Full sandbox at time T. By the time the production deployment window opens at time T+14 days, production has received additional admin changes (field adds, permission tweaks, flow activations) that are not reflected in the sandbox. The deployment validates against a stale baseline, and dependencies that exist in production but not in the sandbox cause unexpected runtime behavior after deploy.

**When it occurs:** Any team with frequent admin activity between the sandbox validation date and the production deployment date. More common in orgs with multiple release tracks or where separate sandbox environments are used for different feature teams.

**How to avoid:** At the start of risk classification, compare the production metadata state against the sandbox used for validation. Flag any production metadata that changed since the validation run. If the delta is significant for HIGH-risk components, re-validate in a refreshed sandbox or in a production validation-only run before opening the window.

---

## Gotcha 3: Flow Version Rollback Does Not Affect In-Flight Interviews

**What happens:** A new Flow version is deployed and found to be defective. The team rolls back by redeploying the prior version and re-activating it. However, Flow interviews that started on the new (defective) version while it was active continue running on that version to completion. They are not transferred to the prior version. This means a rollback does not immediately eliminate all defective behavior — it stops new interviews from starting on the defective version but does not terminate existing ones.

**When it occurs:** Any Record-Triggered or Schedule-Triggered Flow that was active for more than a few seconds before rollback was initiated, or any Flow that has long-running paused interviews (Wait elements).

**How to avoid:** After rolling back a Flow version, check for in-flight interviews using the Paused and Waiting Interviews list in Setup. For defective paused interviews, evaluate whether they need to be manually resumed on the correct path, terminated, or allowed to complete. Document this as a post-rollback task in the runbook.

---

## Gotcha 4: Destructive Changes Must Be Authored Before the Window, Not During

**What happens:** A deployment includes a component that needs to be removed as part of rollback. During the incident, the team attempts to author a destructive change XML file on the fly. The XML schema for destructive changes differs from standard deployment XML, and errors in the file extend the outage. Additionally, a destructive change that has not been tested in a sandbox may itself fail validation in production.

**When it occurs:** Any rollback scenario where the prior state requires deleting a component that was added by the forward deployment — for example, a new custom field that triggers automation, a new Flow that has no prior version to revert to, or a new connected app.

**How to avoid:** For every HIGH-risk component in a release, author and test the rollback destructive change XML in a sandbox before the production window opens. Store it in source control alongside the forward deployment package. Reference the exact file path in the rollback runbook.

---

## Gotcha 5: PermissionSet Deployment Order Determines Intermediate Access State

**What happens:** A release includes a new PermissionSet and an assignment of that PermissionSet to a specific user or PermissionSet Group. If the PermissionSet deploys first and the assignment deploys second, there is a window where the PermissionSet exists but is not assigned — users have less access than intended. If the deployment is interrupted between these two steps, users remain in the under-privileged state until the deployment resumes or is manually corrected.

**When it occurs:** Any deployment that includes both PermissionSet metadata and PermissionSet assignment configuration in the same deployment package. Also occurs when PermissionSets that grant access are deployed before Profiles that restrict access are updated — producing a window of over-privileged access.

**How to avoid:** Classify any release that includes both PermissionSet creation and assignment as HIGH risk. In the risk plan, document the access state at each step of deployment and confirm the intermediate states are acceptable. For security-sensitive access grants, consider deploying the PermissionSet in a separate prior release and the assignment in the current release to eliminate the intermediate state risk.
