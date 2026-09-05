# Gotchas — DevOps Process Documentation

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Named Credentials Deploy Successfully But Break Integrations Silently

**What happens:** A credential deploys as a frame with no secret in it, and the deploy reports Succeeded. The mechanism is on the *retrieve* side, not the deploy side, and the guide is explicit about it for `AuthProvider`: "If a consumer secret is defined on an authentication provider, the consumer secret is always exported as a placeholder value, not as an encrypted secret" (api_meta.txt L24855–24856). So a retrieve → commit → deploy round trip carries the placeholder forward. You *can* deploy a working secret — since November 2022 `consumerSecret` is entered as plaintext in the XML (api_meta.txt L25120–25122) — but only if you put the real value in the file by hand, which means committing a secret to source control. Both branches end in the same operational fact: after a source-controlled deploy the target org has a credential that authenticates against nothing, and the failure surfaces at the first callout, not at the deploy.

UNVERIFIED (2026-09-05): the Metadata API guide states the placeholder-on-export rule for `AuthProvider.consumerSecret` specifically. The same behaviour for `ExternalCredential` principal secrets and for the deprecated `NamedCredential.password` field (api_meta.txt L90193–90200, deprecated in API 56.0) is asserted here from practice, not from a documented sentence. Verify against your own retrieve before relying on it.

**When it occurs:** Every time a Named Credential is included in a deployment to a new environment or after a sandbox refresh. It also occurs when `ExternalCredential` principal definitions are deployed — the principal exists but has no credentials bound to it until an admin re-enters them under External Credentials > Principals.

**How to avoid:** Make Named Credential re-entry a mandatory numbered step in every runbook that includes integration metadata. The step must include: the exact Setup navigation path, every field that requires a value, the secret source (password manager vault entry or secure handoff from the integration owner), and a verification callout with an expected HTTP status code. Never write "configure credentials" as a single checklist item.

---

## Gotcha 2: Sandbox Refresh Silently Invalidates Runbook Assumptions

**What happens:** After a Full Copy or Partial Copy sandbox refresh, the org is overwritten with a snapshot from production. All configuration changes made after the previous refresh are lost: custom settings values, Named Credential entries, permission set assignments, Remote Site Settings added manually, and any data created directly in the sandbox. A runbook authored against the pre-refresh sandbox is no longer accurate.

**When it occurs:** Whenever a sandbox refresh happens — whether scheduled (monthly or quarterly) or on-demand for a release preparation. The problem is amplified because Salesforce does not send a platform notification to runbook authors; only the sandbox admin who initiated the refresh receives an email.

**How to avoid:** Include a "confirm sandbox refresh date" step in the pre-deploy gate of every runbook. The step should specify: navigate to Setup > Sandbox, find the sandbox record, check the Last Refresh Date, and confirm it is after the date the runbook was authored. If the sandbox was refreshed after the runbook was written, re-validate all manual configuration steps listed in the runbook before proceeding.

---

## Gotcha 3: Flow Deployment Does Not Guarantee the Correct Version Is Active

**What happens:** Deploying a Flow through the Metadata API creates a new version of the Flow in the target org. Whether the newly deployed version becomes the active version depends on the `status` field value in the Flow metadata XML. If the deployed version has `status = Draft`, the previous active version continues running. If the target org has no Flow of that name yet, the deployed version may land as `Inactive` depending on the org's Flow behavior settings.

**When it occurs:** Most commonly when a Flow is deployed to a sandbox that previously had a manually-activated version, or when the CI/CD pipeline strips or overrides metadata `status` values. Also occurs when deploying to an org where the same Flow API name exists but belongs to a different Flow type.

**How to avoid:** Every runbook that includes Flow deployment must include a post-deploy step: navigate to Setup > Flows, filter by the Flow API name, confirm that the correct version number is active, and confirm the version was last modified at the expected timestamp. If the wrong version is active, manually activate the correct version from the Flow detail page before declaring the deployment complete.

---

## Gotcha 4: Environment Matrix Accuracy Decays Without a Forcing Function

**What happens:** The environment matrix is accurate when first authored. Over time, sandboxes are refreshed on different cadences, new sandboxes are provisioned without being added to the matrix, sandbox types are changed (e.g., a Partial Copy is upgraded to Full Copy), and ownership changes. Because Salesforce does not surface a team-visible changelog of sandbox state, the matrix drifts from reality quietly. By the time a new team member relies on it, several columns are wrong.

**When it occurs:** In any team where the environment matrix is treated as a one-time artifact rather than a living document. Common in teams that have rapid onboarding, multiple sandbox administrators, or infrequent release cycles that reduce the forcing function to review the matrix.

**How to avoid:** Add an explicit "review and update the environment matrix" step to the pre-release checklist at the start of every release cycle. Assign a named owner to the matrix (typically the DevOps lead or release manager). Include the last-reviewed date as a header in the matrix document itself. Teams using DevOps Center can cross-reference the environment list in DevOps Center against the matrix to catch discrepancies.

---

## Gotcha 5: Runbooks Written for One Environment Are Incorrectly Reused for Another

**What happens:** A practitioner writes a detailed runbook for deploying release X to the staging sandbox. The release goes well. For the production deployment, they copy the staging runbook and update the org name but leave all other references pointing to staging-specific details: Named Credential values, user accounts, Remote Site Settings URLs, and smoke test endpoints. The production deployment proceeds against incorrect verification targets.

**When it occurs:** Under time pressure or when the person authoring the production runbook was not the same person who authored the staging runbook. Also common when teams treat "copy and update the org name" as sufficient runbook customization.

**How to avoid:** The deployment guide should explicitly identify which runbook sections are environment-independent (deploy commands, metadata scope, Flow activation steps) and which are environment-specific (Named Credential values, test user accounts, smoke test URLs, IP allowlist entries). Production runbooks should be derived from the deployment guide, not cloned from a prior environment's runbook.

---

## Gotcha 6: A FlowDefinition in the Package Silently Overrides Every Flow `status`

**What happens:** The runbook says "verify the deployed Flow version is active", the deploy succeeds, and an older version is active anyway — with no error. If the package contains a `FlowDefinition` component alongside the `Flow`, the guide states plainly that "the active version numbers in the flow definitions override the status fields in the flows", and gives the worked case: definition says version 3, latest flow is version 4 with `status` `Active`, and after the deploy the active version is 3 (api_meta.txt L73925–73931).

**When it occurs:** Whenever `flowDefinitions/` is still in the source tree. This is common in orgs that predate API 44.0, where `FlowDefinition` was the supported way to activate a flow; the guide has recommended discontinuing its use since then (api_meta.txt L73921–73924). Retrieving with a `<members>*</members>` wildcard on `FlowDefinition` reintroduces it into a repo that had moved on.

**How to avoid:** Make the runbook's Flow verification step read the *version number*, not just "Active/Inactive". Add a pre-deploy gate item that greps the package for `flowDefinitions/`; if any are present, the runbook must record the `activeVersionNumber` each one asserts, because that number and not the `Flow.status` field is what the org will honour. The five `FlowVersionStatus` values are `Active`, `Draft`, `Obsolete`, `InvalidDraft` and `UnderReview`, and both `Draft` and `Obsolete` display in the UI as "Inactive" (api_meta.txt L68416–68423) — so "the UI says Inactive" does not tell you which of the two you have.

---

## Gotcha 7: Submitting the Release as Four Deployments Does Not Give You Four Ordered Deployments

**What happens:** A release is split into schema → layouts → automation → destructive, all four are fired at the CI runner at once, and they land in the wrong order. The guide: "You can initiate multiple deployments, but only one deployment can run at a time. The other deployments remain in the queue waiting to run after the current deployment finishes. Queued deployments are listed under Pending Deployments and are not necessarily executed in the order in which they were submitted" (api_meta.txt L4117–4120). The documented way to get an order is to "submit them one at a time after the previous deployment has completed successfully" (api_meta.txt L4120–4121).

**When it occurs:** Any pipeline that fans out manifests in parallel, and any runbook that says "deploy the four packages" without saying "one at a time, each after the previous reports Succeeded". It also occurs when a human kicks off a hotfix while a release deploy is queued.

**How to avoid:** Write the deploy order as numbered, gated steps whose pass criterion is the *previous* deployment's status, not its submission. Then record the deploy id of each. A second constraint tightens this: in API version 65.0 and later a deployment with status `Finalizing Deploy` cannot be cancelled at all (api_meta.txt L4124–4127), so the escape hatch you were relying on to unwind a mis-ordered submission may not be there.

---

## Gotcha 8: A User Referenced by Deployed Metadata That Is Missing in the Target Halts the Whole Deployment

**What happens:** The package includes a dashboard running user, a workflow email recipient, or any component that names a user. Salesforce matches usernames between source and destination, adapting the org domain — the `.sandboxname` suffix is ignored. But "if a username in the source environment doesn't exist in the destination environment, Salesforce displays an error, and the deployment stops until the usernames are removed or resolved to users in the destination environment" (api_meta.txt L2705–2718). Not a warning on one component — the deployment stops.

**When it occurs:** Two shapes, both routine. A user created only in the sandbox (a test account, a contractor) is referenced by something that gets retrieved. Or a leaver is deactivated in production between the sandbox refresh and the deployment window, and the metadata still names them. The second shape is nastier because the package validated clean a week earlier.

**How to avoid:** Add a pre-deploy gate item that lists every username the package references and confirms each exists in the target. In the RACI this is an admin task, not a release-manager task, because it needs Setup access to both orgs. Re-run it on the day of the window rather than at validation time, since the org's user population moves between the two.

---

## Gotcha 9: `SucceededPartial` Is a Deploy Status, and `rollbackOnError` Defaults to False

**What happens:** A deployment reports success, and only some of it landed. `SucceededPartial` is one of the documented deploy statuses, alongside `Succeeded`, `Failed`, `Canceling` and `Canceled` (api_meta.txt L3338–3352). It exists because `rollbackOnError` "indicates whether any failure causes a complete rollback (true) or not (false). If false, whatever actions can be performed without errors are performed, and errors are returned for the remaining actions. This parameter must be set to true if you're deploying to a production org. The default is false" (api_meta.txt L3126–3129).

**When it occurs:** Any deploy path that does not set the option explicitly. A CLI or CI wrapper may set a sane default for you; a raw Metadata API call, an Apex-enqueued deployment, or a hand-rolled REST `deployRequest` will not.

**How to avoid:** Record the deploy contract — the actual `deployOptions` values — in the runbook, and make the post-deploy gate read the `status` field rather than a shell exit code. Treat `SucceededPartial` as a failure and route it to the rollback decision gate. `admin/change-management-and-deployment` owns the choice of values; this skill owns the fact that they are written down and verified after the fact.

---

## Gotcha 10: The Sandbox Rehearsal Runs Zero Tests Unless You Ask, and Production May Too

**What happens:** The team rehearses the release in UAT, it takes four minutes, and the production window is booked for fifteen. Production then runs the full local test suite and takes fifty. The two defaults differ: "by default, no tests are run in a deployment to a non-production organization, such as a sandbox or a Developer Edition organization" (api_meta.txt L2662–2664), while "tests are executed by default in production only if your deployment package contains Apex classes or triggers" (api_meta.txt L2675–2677).

**When it occurs:** Every rehearsal where `testLevel` is left unset. The inverse bites too: an Apex-free admin release deployed to production runs no tests by default, so a team that budgeted an hour for the test run discovers the window was never the constraint — and a team that assumed tests would catch a regression discovers none ran.

**How to avoid:** Set `testLevel` explicitly on both the rehearsal and the production run and record both in the runbook, so the rehearsal's duration is a real estimate. `RunLocalTests` "is enforced regardless of the contents of the deployment package" (api_meta.txt L2675–2676), which is what makes it the value that makes sandbox and production comparable. The five valid values are `NoTestRun`, `RunSpecifiedTests`, `RunRelevantTests` (beta), `RunLocalTests` and `RunAllTestsInOrg` (api_meta.txt L3140–3168).

---

## Gotcha 11: The Quick-Deploy Licence Is Target-Specific and Expires in Ten Days

**What happens:** A release is validated well in advance so the window can be short, the window slips, and on the day the quick deploy is refused — so the full test run happens inside the window after all. The requirement is that "the components have been validated successfully for the target environment within the last 10 days" (api_meta.txt L4863), with the further conditions that the validation's Apex tests passed and coverage requirements were met (api_meta.txt L4864–4868).

**When it occurs:** Long-lead releases, releases that slip past a change freeze, and — the one people miss — releases validated against UAT and then quick-deployed to production. The validation is bound to *that* target environment; a UAT validation does not license a production quick deploy.

**How to avoid:** Put the validate-only run on the release calendar as a dated activity inside the ten-day window before the production slot, targeted at production, not at UAT. If the window slips past the tenth day, the runbook's deploy step reverts to a full deploy with the documented test level and the window estimate must be revised before the go/no-go, not during it.

---

## Gotcha 12: `purgeOnDelete` Is Inert in Production, and Roll-Up Summary Fields Ignore It Anyway

**What happens:** A retirement release documents "deleted components bypass the Recycle Bin" as its rollback constraint, and in production the components are in the Recycle Bin after all — or, for one field type, they are gone when the runbook said they would be recoverable. `purgeOnDelete` "only works in Developer Edition or sandbox orgs. It doesn't work in production orgs" (api_meta.txt L3119–3123). Separately: "when you delete a roll-up summary field using Metadata API, the field isn't saved in the Recycle Bin. The field is purged even if you don't set the `purgeOnDelete` deployment option to true" (api_meta.txt L4638–4640).

**When it occurs:** Any release with a `destructiveChanges` manifest. The sandbox rehearsal behaves one way and production the other, so the rehearsal actively misleads the runbook author about what rollback will look like.

**How to avoid:** State the rollback path per deleted component type, not per release. For most types in production, undelete from the Recycle Bin is a real rollback step and should be written as one. For roll-up summary fields it is not, so the rollback path is "redeploy the field definition from the pre-deploy retrieve" — which is why the runbook takes that retrieve before anything changes. Deletions are also processed before additions by default, and `destructiveChangesPre.xml` / `destructiveChangesPost.xml` are the documented way to move them (api_meta.txt L4645–4660); `devops/destructive-changes-deployment` owns the mechanics.
