# Gotchas — DevOps Process Documentation

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Named Credentials Deploy Successfully But Break Integrations Silently

**What happens:** When a `NamedCredential` or `ExternalCredential` metadata component is included in a deployment, the Metadata API creates or updates the structural record in the target org but does not transfer secret values — passwords, tokens, client secrets, or certificates. The deploy completes with a "Succeeded" status. The integration fails only when the first callout is made, often minutes or hours after the deployment window closes.

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
