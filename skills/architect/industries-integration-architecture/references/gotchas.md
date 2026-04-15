# Gotchas — Industries Integration Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Integration Procedure HTTP Action Executes Synchronously — Timeout Risk on Slow External Systems

**What happens:** Integration Procedures execute server-side action chains synchronously within the OmniScript framework. When an HTTP Action element calls an external backend (policy admin, BSS, CIS) that takes longer than approximately 5–10 seconds to respond, the OmniScript session can time out or the Salesforce callout governor limit (120 seconds total per transaction) can be exhausted. The failure surface appears to the agent as a vague "Integration Procedure failed" message with no indication that the external system was slow.

**When it occurs:** Most commonly with insurance policy admin systems that have variable response times under load, and with BSS/OSS order management endpoints that queue requests asynchronously but return synchronously after queueing. Also triggered during CIS maintenance windows when SAP IS-U response times degrade.

**How to avoid:** For external calls that may exceed 5 seconds, move the callout out of the synchronous IP into an Async Apex method invoked via an IP `Apex Action` element. The Apex method dispatches the callout asynchronously and stores the result on a Platform Event or a Salesforce record that the OmniScript polls via a subsequent fast IP. This decouples OmniScript session lifetime from external system response time.

---

## Gotcha 2: MuleSoft Gateway Deprecation Is Not Surfaced in Communications Cloud Setup UI

**What happens:** Communications Cloud Setup still displays and accepts the MuleSoft API Gateway configuration path even after the Winter '27 deprecation announcement. There is no in-product warning that the pattern is deprecated. An architect reviewing an org's Communications Cloud integration cannot determine from the Setup UI alone whether the org is on a deprecated path — they must know to check the TM Forum API Settings access mode field explicitly.

**When it occurs:** During any Communications Cloud integration review, implementation, or upgrade planning session. New implementations are especially at risk if the architect is following older Salesforce documentation that pre-dates the deprecation announcement and finds the MuleSoft Gateway option in Setup without a deprecation badge.

**How to avoid:** Explicitly check Setup → TM Forum API Settings → Access Mode field in every Communications Cloud org review. If the value is "MuleSoft Gateway," flag it as requiring migration to Direct Access before Winter '27 in the architecture decision document. Never start a new Communications Cloud BSS/OSS integration on the MuleSoft Gateway path regardless of what the UI makes available.

---

## Gotcha 3: Named Credential OAuth Scope Mismatch Produces Non-Descriptive Auth Failure at IP Runtime

**What happens:** When an Integration Procedure's HTTP Action invokes a Named Credential whose associated OAuth 2.0 scope does not include the specific permission required by the target API endpoint, the HTTP Action fails at runtime with a generic auth error (HTTP 401 or 403). The error message does not indicate that the scope is the problem — it looks identical to an invalid credential error. Teams lose time rotating credentials and reconfiguring Named Credentials when the real fix is adding a scope.

**When it occurs:** Common when the Named Credential was configured by a middleware or infrastructure team using a minimum-scope OAuth token, and the IP was later extended to call a new endpoint on the same backend that requires an additional scope. Also common in Communications Cloud when BSS/OSS TMF API scopes are segmented by API family (product catalog, ordering, customer management each require separate scopes).

**How to avoid:** Before wiring a Named Credential to a new Integration Procedure HTTP Action endpoint, test the credential independently using Salesforce Developer Console (`Http.send()` with the Named Credential) and confirm the target endpoint returns HTTP 200. Document the required OAuth scope per endpoint in the Named Credential setup notes. When adding a new BSS/OSS endpoint, review the scope list first.

---

## Gotcha 4: CIS-Sourced Salesforce Records Are Silently Overwritten by Sync Without Field-Level Locking

**What happens:** When a CIS-to-Salesforce sync job (upsert by external ID) runs on a schedule, any field values on the Salesforce record that a user has manually edited since the last sync are overwritten without warning. DML upsert operations do not check whether a field was recently modified by a user — they blindly apply the CIS values. In an E&U org where agents can see rate plan fields, agents who manually correct display errors or test values will find their edits gone after the next sync window.

**When it occurs:** Whenever the CIS sync is not accompanied by immediate field-level security lockdown of all CIS-owned fields. This is especially common in early implementation phases when the sync is deployed before the FLS configuration is finalized, and in orgs where multiple field ownership decisions are still in flux.

**How to avoid:** Immediately after deploying the CIS sync job, configure Field-Level Security on all CIS-sourced fields to Read-Only for every profile and permission set that includes internal users. This prevents the "edit" action from being possible, eliminating the conflict entirely. For fields that genuinely need both CIS source values and Salesforce agent edits, use separate fields: a locked `CIS_RateName__c` for the synced value and a separate `AgentNote__c` for the agent's annotation.

---

## Gotcha 5: Integration Procedure Version Mismatch After Partial Deployment

**What happens:** Integration Procedures are versioned artifacts with a composite key of `IntegrationProcedureKey` + `IntegrationProcedureVersion`. If a deployment deploys an updated IP definition but does not deploy an updated OmniScript that references it — or vice versa — the OmniScript may invoke the wrong IP version at runtime. The mismatch is not surfaced as a deployment error; it only appears as unexpected behavior at OmniScript runtime when the old IP version returns a different response structure than the new OmniScript expects.

**When it occurs:** During staged deployments where OmniScript and Integration Procedure artifacts are split across separate deployment packages, or when a developer activates a new IP version in one sandbox but forgets to include it in the production deployment package. Also occurs when a rollback restores the OmniScript but not the IP it was rolled back to pair with.

**How to avoid:** Always deploy IP + dependent OmniScript + dependent DataRaptor as a single atomic package. Use change set or Salesforce CLI deployment packages that bundle all OmniStudio artifacts for a given OmniScript flow together. Before production deployment, run a version consistency check: verify that the `IntegrationProcedureVersion` referenced in the OmniScript element matches the deployed and activated IP version in the target org.
