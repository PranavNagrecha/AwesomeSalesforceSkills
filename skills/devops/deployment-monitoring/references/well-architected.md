# Well-Architected Notes — Deployment Monitoring

## Relevant Pillars

- **Reliability** — The primary pillar for this skill. Reliable deployment monitoring ensures that failures are detected immediately rather than discovered through end-user reports. Polling to a terminal status, not just polling until a non-error HTTP response, is the difference between a reliable pipeline and one that silently ignores failures. Pending queue management and duplicate-submission prevention are reliability concerns.

- **Operational Excellence** — Deployment monitoring is a direct operational excellence practice. Externalizing deployment logs beyond the 30-day Setup retention window, surfacing structured component failure detail in CI build logs, and maintaining deployment audit trails in change tickets are all operational excellence behaviors that reduce mean time to diagnosis after a production incident.

- **Security** — Deployment monitoring surfaces the full list of metadata components that landed in an org, including changes to permission sets, profiles, sharing rules, and Apex classes with system access. This makes monitoring output a security audit trail. Ensuring that deployment IDs and their associated component lists are retained and correlated with the submitting user's identity supports change traceability requirements in regulated environments.

## Architectural Tradeoffs

**Polling interval vs. payload size:** Using `includeDetails=true` on every poll reduces latency in detecting errors but increases payload size for large orgs. The correct tradeoff is `includeDetails=false` during heartbeat polling and `includeDetails=true` on the first terminal-status poll. Teams that invert this — always including details, or never including details — pay either a bandwidth cost or a diagnostic cost.

**Async submission vs. synchronous blocking:** `sf project deploy start` without `--async` blocks the terminal and ties the deployment lifecycle to the connection. `--async` decouples submission from monitoring but requires explicit ID capture and polling. For CI pipelines running on ephemeral agents, `--async` with an ID-capture step is the only resilient choice. For developer laptops, the tradeoff is convenience versus robustness.

**Abortability vs. release size:** The window in which a deployment can still be canceled closes when it enters `FinalizingDeploy`, and finalizing is where a large package's commit work concentrates — so the bigger the release, the smaller the fraction of its runtime that is actually abortable. Splitting a release into smaller deployments buys back abortability at the cost of queue contention, since only one deployment runs per org at a time. Teams that keep releases monolithic should design for forward-fix rather than assume a mid-flight abort exists.

**In-Salesforce history vs. external log store:** The 30-day Setup retention window is a hard platform constraint. Teams that rely on it for audit purposes are one month from losing all evidence of a given deployment. The architectural recommendation is to treat the Setup Deployment Status page as an operational convenience, not an audit system. An external log store is the authoritative audit record.

## Anti-Patterns

1. **Poll-and-forget** — Submitting a deployment and checking its status only once, immediately after submission, then treating `InProgress` or `Pending` as success. This is the most common monitoring failure mode. The deployment may still fail minutes later. All status checks must poll to one of the five terminal states (`Succeeded`, `SucceededPartial`, `Failed`, `FinalizingDeployFailed`, `Canceled`) — a loop that recognises only three of them has the mirror-image failure, hanging instead of exiting early.

2. **Reusing the validation ID as the quick deploy status handle** — After executing a quick deploy, monitoring the original validation ID rather than the new deployment ID returned by `deployRecentValidation`. The validation ID permanently shows a stale `Succeeded` result. This anti-pattern causes teams to believe deployments succeeded when they are still running or have failed.

3. **Relying on Setup Deployment Status as the sole audit record** — Treating the 30-day Deployment Status page as the system of record for deployment history. For compliance, regulatory, or post-incident review purposes, this creates a silent data retention gap. All deployment results must be externalized at completion time.

4. **Treating cancellation as the rollback plan** — Designing a release process whose abort path is "cancel the deployment if it looks wrong." At Metadata API 65.0+ a deployment in `FinalizingDeploy` cannot be canceled at all; below 65.0 a cancel could succeed while the deployment's data was also committed. Neither version gives the guarantee the plan assumes. The reliable abort path is a validated, known-good prior package plus a forward-fix deployment — see `rollback-and-hotfix-strategy`.

## Official Sources Used

- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Metadata API `checkDeployStatus` — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_deploy_checkdeploystatus.htm
- Metadata API `deployRecentValidation` — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_deployrecentvalidation.htm
- REST Metadata API `deployRequest` — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_rest_deploy.htm
- Salesforce CLI Reference (`sf project deploy report`) — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm
- Salesforce DX Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm
- Metadata API `cancelDeploy()` — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_canceldeploy.htm — confirms that at API 65.0+ a deployment with a status of Finalizing Deploy can't be cancelled, that below 65.0 a cancel may fail after data commit has started or succeed while data is also committed, the `INVALID_ID_FIELD` message `You cannot cancel the deployment while finalizing is in progress`, and the Modify Metadata Through Metadata API Functions / Modify All Data permission requirement (verified 2026-08-13)
- Metadata API — Cancel a Deployment in Progress Using REST — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_rest_deploy_cancel.htm — confirms the `PATCH .../metadata/deployRequest/{id}` shape with body `{"deployResult": {"status": "Canceling"}}`, the same 65.0 gate, and that the request is asynchronous so the response status can read `Canceling` or `Canceled` (verified 2026-08-13)
- Metadata API `DeployResult` — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_deployresult.htm — the on-dimension source for the `status` field this skill's poll loops read: documents `status` as type `DeployStatus` and enumerates the same nine values (`Pending`, `InProgress`, `FinalizingDeploy`, `FinalizingDeployFailed`, `Succeeded`, `SucceededPartial`, `Failed`, `Canceling`, `Canceled`) (verified 2026-08-14)
- `DeployStatus` Enum, Apex Reference Guide — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_enum_Metadata_DeployStatus.htm — the Apex `Metadata` namespace mirror of the same enum; carries the per-value descriptions quoted in this package, including `FinalizingDeploy` ("Deployments in the state can't be canceled"), `FinalizingDeployFailed`, `SucceededPartial`, and `Canceling` (verified 2026-08-13)
- Salesforce Well-Architected Framework — https://architect.salesforce.com/well-architected/overview
