# Gotchas — Change Advisory Board Process

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Sandbox Preview Creates Silent Platform-Behavior Drift

**What happens:** When Salesforce deploys the seasonal preview to sandboxes (approximately 4–6 weeks before the production upgrade), the sandbox begins running on the new platform release while production remains on the previous release. A deployment that is tested, validated, and CAB-approved against the preview sandbox may exhibit different behavior in production — not because the metadata changed, but because the production runtime is different. Common failure modes include Flow engine behavior changes, Apex API version behavioral differences, and authentication handshake changes in Named Credentials.

**When it occurs:** During the 4–6 week overlap between sandbox preview start and production upgrade Wave 1. Orgs that continuously deploy and test in sandbox but deploy to production on a slower cadence are most exposed.

**How to avoid:** Maintain a CAB calendar that includes both the sandbox preview start date and the production upgrade wave dates (from trust.salesforce.com). During the overlap window, treat all Normal changes as requiring explicit sign-off acknowledging the drift risk, and require that test evidence was captured on a non-preview sandbox (a Full or Partial sandbox that has not yet been refreshed onto the preview release) if the deployment must land before the production upgrade.

---

## Gotcha 2: Permission Set Deployment Adds But Does Not Remove

**What happens:** Deploying a Permission Set via the Metadata API (`sf project deploy start`) adds the permission entries present in the source XML and updates entries that already exist — but it does not remove permission entries that were manually added directly in the target org after the last source-tracked state. An org where a Permission Set was manually edited in Setup will retain those manual additions even after a "clean" deployment from source. The resulting effective permissions in production silently differ from what was approved by CAB.

**When it occurs:** Any time there is manual configuration drift between the source repository and the target org — which is common in environments where admins have direct Setup access alongside a deployment pipeline.

**How to avoid:** The CAB change ticket for any Permission Set change must require a pre-deployment audit step: retrieve the current live Permission Set from production and diff it against the source version. Include unexpected additions in the change scope. Post-deployment, run a permission audit comparing expected vs. actual effective permissions (using the Permission Set API or a report on PermissionSetAssignment records). Ideally, lock direct Setup access to Permission Sets in production so all changes flow through the pipeline.

---

## Gotcha 3: Profile XML Partial Retrieval Causes Silent Permission Revocation

**What happens:** When a Profile is retrieved from a Salesforce org using `sf project retrieve start`, the retrieved XML only includes the metadata types and components that are in the project's package.xml scope. If an FLS (field-level security) entry or object permission exists in the org but is not in scope of the retrieve, it is absent from the XML. When this incomplete Profile XML is then deployed, those absent entries can be silently removed from the target org — revoking permissions that real users depend on.

**When it occurs:** Any Profile deployment where the source was retrieved with a non-exhaustive package.xml. Most common when teams retrieve only the components that changed, not the full Profile.

**How to avoid:** Any CAB change involving Profile changes must require a full-profile retrieval before deployment. Use the `--metadata Profile:ProfileName` flag combined with a comprehensive package.xml that includes all object types in the org. Alternatively, migrate Profile-based access control to Permission Sets (which have safer additive deployment behavior) and remove reliance on Profile FLS deployments. The CAB approval for Profile changes should explicitly require a reviewer to confirm that the retrieved XML was complete.

---

## Gotcha 4: DevOps Center Has No Native ITSM Gate

**What happens:** Salesforce DevOps Center provides a visual pipeline for source-tracked deployments, but it does not have a native integration point where an external ITSM change ticket can gate a pipeline stage transition. There is no built-in "require ServiceNow approval" step. Teams that adopt DevOps Center expecting it to enforce CAB policy find that pipeline stage promotions require only the in-app role assignments — the person with the "Promote" permission can promote to production at any time.

**When it occurs:** When an organization adopts DevOps Center and assumes it provides CAB enforcement, then discovers during a compliance audit that production deployments occurred without corresponding change tickets.

**How to avoid:** For DevOps Center environments, the CAB gate must be enforced procedurally (pipeline stage promotions require a named approver in the DevOps Center work item, and that approver is responsible for confirming ITSM ticket approval before clicking Promote) or via a compensating control (a post-deployment webhook that verifies a valid change request existed and was approved, flagging any deployment without one). Document this gap explicitly in the CAB process documentation.

---

## Gotcha 5: Emergency Change Process Scope Creep

**What happens:** Once an Emergency change path exists with faster approval, teams begin classifying non-urgent deployments as Emergency to bypass the standard CAB review cycle. Over time, the majority of changes are classified Emergency, the ECAB approvers become fatigued and rubber-stamp approvals, and the entire governance framework degrades. Because ECAB post-reviews are often time-pressured, the root cause investigation required for genuine emergencies is also neglected.

**When it occurs:** When the Emergency classification criteria are poorly defined or unenforced, and when the standard CAB cycle is slow enough that bypassing it carries significant business pressure.

**How to avoid:** Define strict Emergency criteria in the CAB process document (e.g., "Production system is down or degraded in a way that directly impacts revenue or regulatory compliance, and the fix cannot wait for the next scheduled CAB meeting"). Require the ECAB to log the Emergency justification. Track the Emergency:Normal ratio monthly — a ratio above 15–20% signals that either Emergency criteria are being abused or the Normal change cycle is too slow and needs to be optimized.
