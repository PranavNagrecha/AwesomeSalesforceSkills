# Gotchas — OmniStudio Debugging

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Navigation Actions Are Silently Excluded from OmniScript Preview

**What happens:** A practitioner runs an OmniScript in the designer's Preview tab and observes that the Navigation Action element does nothing — the script completes without redirecting. The element configuration looks correct. Debugging the element yields no errors in the Action Debugger.

**When it occurs:** Any time a Navigation Action element is present in an OmniScript and the practitioner is testing via the Preview tab in the OmniScript designer. This affects every practitioner who relies on Preview for full end-to-end validation.

**How to avoid:** Never use Preview to validate Navigation Action elements. The OmniScript Preview environment does not have a Lightning app or Experience Site routing context, so Navigation Actions are platform-excluded from Preview execution (documented in Salesforce Help — Preview and Test an OmniScript). Test Navigation Actions only in a deployed Lightning app page or Experience Site. Use the Action Debugger in Preview only to validate that the data node feeding the Navigation Action is correctly populated — not to confirm the navigation itself fires.

---

## Gotcha 2: DataRaptor Preview Reflects the Designer User's Access, Not the Runtime User's

**What happens:** A DataRaptor Extract appears to work correctly when previewed by the designer (a system administrator). The same asset returns zero records when executed by a community portal user or an internal user with a restricted profile. No error is raised — the DataRaptor silently returns an empty result set.

**When it occurs:** Whenever a DataRaptor Extract retrieves records that are subject to OWD settings, sharing rules, or profile-level restrictions that differ between the designer and the intended runtime user. Particularly common in Experience Site implementations where internal admins build assets for external users.

**How to avoid:** Test DataRaptors that serve restricted users by running the OmniScript as a representative user in the deployment context. Inspect the generated SOQL from Preview and manually run it against the restricted user's access to observe the difference. If full system-level access is required by the business scenario, use an Apex action with appropriate sharing controls, explicitly documented and reviewed for security implications.

---

## Gotcha 3: Deploying a New IP Version Does Not Activate It

**What happens:** A team deploys a new Integration Procedure version to production via a change set. The IP continues behaving as the old version. The new element configuration changes are not reflected. The new version exists in the designer but is marked Inactive.

**When it occurs:** Every change set or Metadata API deployment of an OmniStudio asset. Activation is a separate manual step that deployments do not perform automatically.

**How to avoid:** After every OmniStudio asset deployment, explicitly verify and activate the intended version in the target org's designer. Document this as a required post-deployment step in the release runbook. Run the IP Debug tab after activation with a representative input payload to confirm the new version's behavior before declaring the release complete.

---

## Gotcha 4: IP Elements Fail Open Without rollbackOnError

**What happens:** An Integration Procedure includes a critical HTTP action that fails (returns a 500 or receives no response). The IP does not surface an error to the calling OmniScript or FlexCard. The experience appears to complete normally, but the expected data is absent. No user-visible error occurs.

**When it occurs:** Any IP where `rollbackOnError` is not set to `true` at the root and where individual HTTP or DataRaptor action elements have no `failureResponse` configured. This is the OmniStudio default — elements fail open unless explicitly configured to propagate failure.

**How to avoid:** Set `rollbackOnError: true` at the IP root. Configure a meaningful `failureResponse` on every element whose failure should stop execution. The calling OmniScript or FlexCard must then be designed to check an error indicator in the IP response and surface a real user-facing message when the IP did not succeed.

---

## Gotcha 5: Remote Site Settings Are Not Promoted by Change Sets

**What happens:** An HTTP action inside an IP works in sandbox but fails silently in production. The Named Credential exists and is correctly configured in both orgs. The IP Debug log shows a connection failure with no meaningful status code.

**When it occurs:** After promoting an Integration Procedure that uses HTTP actions to a production org where the Required Remote Site Setting for that external domain was never created or is inactive. Remote Site Settings control whether the org can make outbound HTTP calls to a domain. Without a matching active Remote Site Setting, callouts fail at the network level before the Named Credential is even evaluated.

**How to avoid:** Treat Remote Site Settings as a required manual promotion step alongside Named Credentials. After any deployment involving HTTP actions, verify in Setup that an active Remote Site Setting exists for every external domain the IP calls. Include Remote Site Setting validation in the deployment runbook and post-deployment smoke test.
