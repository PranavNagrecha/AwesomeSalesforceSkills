# Gotchas — Change Advisory Board Process

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Sandbox Preview Creates Silent Platform-Behavior Drift

**What happens:** When Salesforce deploys the seasonal preview to sandboxes (approximately 4–6 weeks before the production upgrade), the sandbox begins running on the new platform release while production remains on the previous release. A deployment that is tested, validated, and CAB-approved against the preview sandbox may exhibit different behavior in production — not because the metadata changed, but because the production runtime is different. Common failure modes include Flow engine behavior changes, Apex API version behavioral differences, and authentication handshake changes in Named Credentials.

**When it occurs:** During the 4–6 week overlap between sandbox preview start and production upgrade Wave 1. UNVERIFIED (2026-09-05): the "approximately 4–6 weeks" preview lead time and the three-weekend wave structure are not asserted in any of the extracted guides, and help.salesforce.com cannot be fetched from this environment. What the Metadata API Developer Guide does state is that "Salesforce performs major service upgrades three times per year" and that you should "avoid running deployments during the service upgrade", checking Salesforce Trust for your instance's date (api_meta.txt L2115–2125). Take the instance-specific dates from Trust and the preview rules from `admin/salesforce-release-preparation`; do not hard-code the interval.  Orgs that continuously deploy and test in sandbox but deploy to production on a slower cadence are most exposed.

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

---

## Gotcha 6: A Validation Is Bound to One Target Org and Expires in 10 Days

**What happens:** A CAB approves on the strength of a green validation run, then the deploy
happens three weeks later — or the validation was run against UAT and the deploy goes to
production. Neither works as a quick deploy. The Metadata API states the conditions for
deploying a validated component set without re-running tests: "The components have been
validated successfully **for the target environment** within the last **10 days**", the Apex
tests in the target org passed, and coverage requirements are met (`api_meta.txt` L4863–4869;
identically at L3452–3458 for the REST `deployRequest` resource). A validation against a
sandbox is evidence that the package compiles somewhere. It does not qualify — or reserve, or
lock — the production target for anything.

**When it occurs:** Any board whose approval-to-window gap can exceed ten days, which is most
boards with a standing weekly meeting and a monthly release train. Also any pipeline that
validates in the lowest environment on the theory that "a validation is a validation".

**How to avoid:** Record three fields on the decision, not one: the validation id, the org it
ran against, and the date it ran. The board approves *that* validation, not the idea of one.
`scripts/check_change_advisory_board_process.py` fails a record whose `validation_target_org`
differs from `deploy_window.target_org` or whose `validation_date` is more than ten days before
the window opens. If the gap is structural, stop treating validation as an approval input and
re-validate inside the window as the first step of the deploy runbook.

---

## Gotcha 7: `checkOnly` Cannot Validate a Master-Detail ↔ Lookup Conversion At All

**What happens:** A board with a "nothing is approved without a green validation" rule meets a
package that converts a relationship field, and the validation fails for a reason that has
nothing to do with the change being wrong. The guide is explicit: "If you change a field type
from Master-Detail to Lookup or vice versa, the change isn't supported when using the
`checkOnly` option to test a deployment. This change isn't supported for test deployments to
avoid permanently altering your data. If a change that isn't supported for test deployments is
included in a deployment package, the test deployment fails and issues an error."
(`api_meta.txt` L4176–4184.) The remedy the guide gives is a *full deployment to another test
sandbox*, because a full deployment includes a validation as part of the process. There is a
second edge here the board should be told about before it approves: a real deployment
introducing a Master-Detail field, or converting Lookup to Master-Detail, "permanently deletes
any detail records in the Recycle Bin" and they can't be recovered (`api_meta.txt` L4191–4204).

**When it occurs:** Data-model reshaping releases. Rare enough that the board has no muscle
memory for it, common enough that the "validation failed, so reject" reflex fires.

**How to avoid:** Put relationship-type conversions in their own row of the classification
matrix with a different evidence requirement — a full deploy to a spare sandbox, with the
Recycle Bin state of the detail object recorded before and after. The board is then reviewing
the right artefact instead of arguing about a red validation it was always going to get.

---

## Gotcha 8: `SetupAuditTrail` Proves Who and What Category, Not What Changed or Why

**What happens:** "We have the audit trail" is offered as the CAB's evidence of control, and it
does not carry what people assume. The object "represents changes you or other admins made in
your org's Setup area for at least the last 180 days" and its documented fields are `Action`
(the *category* — "a value of `PermSetCreate` indicates that an administrator created a
permission set"), `Display` (the full description), `Section` (the Setup menu area),
`CreatedByContext`, `DelegateUser` (the Login-As user, blank when nobody logged in as someone
else) and the `CreatedBy` relationship (`object_reference.txt` L261536–261600). Three limits
follow directly from that definition. Supported calls are `query()` and `retrieve()` only — you
cannot stamp a change-ticket number onto a row, so the audit trail can never link a Setup change
to a CAB decision by itself. Aggregate queries are not supported: `SELECT count() FROM
SetupAuditTrail` works but `SELECT count(Id) FROM SetupAuditTrail` fails, so "how many
permission-set changes last month" is not the one-line query people expect. And its scope is
the Setup *area*: a file-based Metadata API deployment's own record of who ran it lives on
`DeployResult`, not here.

**When it occurs:** At the compliance audit, and at the post-implementation review — the two
moments the evidence is finally read rather than cited.

**How to avoid:** Use both objects for their actual strengths. `SetupAuditTrail`, queried for
the deploy window, answers "was there Setup activity in this window that was not in the approved
package" — the out-of-band change nobody put through the board. `DeployResult` answers "who
deployed the package, did tests run, was it cancelled": it carries `createdBy` / `createdByName`
and `canceledBy` / `canceledByName` in API version 30.0 and later (`api_meta.txt` L7346–7360).
The CAB decision record holds the ticket number that joins them, because neither object can.

---

## Gotcha 9: Cancelling a Deploy Is Not a Rollback, and There Is a Window Where You Cannot Cancel

**What happens:** The rollback plan on the change ticket says "cancel the deployment". For a
deploy still queued, `cancelDeploy()` does cancel immediately. Once it is running, the guide is
blunt about the two failure modes: "For API versions 65.0 and higher, deployments with a status
of `Finalizing Deploy`, can't be cancelled. For API versions below 65.0, attempts to cancel a
deployment may fail if the deployment has started committing data. Alternatively, it's possible
that the cancellation will succeed, but data from the deployment is also committed."
(`api_meta.txt` L4750–4753.) There is also an `INVALID_ID_FIELD` fault with the message "You
cannot cancel the deployment while finalizing is in progress" in API 65.0 and later. Cancelling
is a best-effort abort during a window you do not control, not an undo.

**When it occurs:** Exactly when it matters — a long production deploy that is visibly going
wrong while the board watches.

**How to avoid:** Write the rollback as a second, forward deployment: a pinned previous package
with its own manifest, an owner, an RTO, and the manual steps the package cannot carry (org-wide
defaults reset in Setup, routing addresses re-verified, Flow versions re-activated). Rehearse it
in a sandbox and record `rehearsed: true` with the date. `rollbackOnError: true` is what protects
you *within* a single deploy — it "must be set to true if you're deploying to a production org"
(`api_meta.txt` L4255–4260) — and with it false the deploy can land as `SucceededPartial`, a real
`DeployStatus` value (`api_meta.txt` L7451), leaving a half-applied package nobody reviewed.

---

## Gotcha 10: `Author Apex` Silently Grants the Ability to Bypass the Gate

**What happens:** The board scopes its gate to "people with pipeline credentials" and misses the
real perimeter. To use the Metadata API a user needs one of these editions and "Either the Modify
Metadata Through Metadata API Functions OR Modify All Data permission", plus "Permission that
enables their deployment tool, such as Salesforce CLI, or change sets" (`api_meta.txt`
L1094–1099). And then: "The Modify Metadata Through Metadata API Functions permission is enabled
automatically when either the **Deploy Change Sets** OR **Author Apex** permission is selected."
(`api_meta.txt` L1108–1109.) So granting a developer `Author Apex` in production grants metadata
deployment as a side effect, without anyone choosing to. The guide adds the warning itself:
"Some metadata, such as Apex, executes in system context, so be careful how you delegate the
Modify Metadata Through Metadata API Functions permission."

There is a second half that closes off the obvious fix. "The Modify Metadata Through Metadata
API Functions permission doesn't affect direct customization of metadata using Setup UI pages
because those pages don't use Metadata API for updates" (`api_meta.txt` L1103–1104) — revoking
it does not stop anyone editing the same metadata by hand in Setup.

**When it occurs:** In every org where a permission set built for development was assigned in
production, and in every "temporary" elevated-access grant that outlived its ticket.

**How to avoid:** Make the gate's perimeter an explicit, reviewed list: every production user
holding `Modify All Data`, `Modify Metadata Through Metadata API Functions`, `Deploy Change
Sets`, or `Author Apex`. Review it at the charter's quarterly cadence, not at the audit. Then
accept that the gate is procedural for Setup-UI changes no matter what you do, and compensate
with the `SetupAuditTrail` sweep in Gotcha 8 rather than pretending the perimeter is closed.

---

## Gotcha 11: A Change Set Is Built by Hand, So What the Board Reviewed Is Not Version-Controlled

**What happens:** The board approves "change set `CI-2026.10`" and someone later adds a
component to it. Nothing in the approval record notices, because a change set is not a file in
a repository — the Metadata API guide's own framing is that "outside of Metadata API, admins
typically use change sets to send customizations from one sandbox to another. Unlike Metadata
API calls, you must build change sets manually" (`api_meta.txt` L956–957). There is no
manifest to diff, no commit to pin the approval to, and the guide documents no approval or
versioning mechanism for change sets at all.

UNVERIFIED (2026-09-05): the specific behaviour — that an outbound change set already uploaded
must be re-uploaded before added components appear in the target org's inbound list, and that
the inbound view therefore does not update in place after approval — is not asserted in any of
the extracted guides, and help.salesforce.com cannot be fetched from this environment. Verify
against Setup > Outbound Change Sets before relying on the mechanism; the governance
consequence below holds either way, because it rests only on change sets being built manually.

**When it occurs:** Any org still deploying by change set, which is most orgs that have a CAB
in the first place — the CAB usually predates the pipeline.

**How to avoid:** Approve a `package.xml` and a commit, not a change set name. If change sets
are the only mechanism available, make the decision record carry a component list captured at
approval time and have the deployer diff the inbound change set against it before clicking
Deploy. That diff is a five-minute manual step and it is the whole control.
