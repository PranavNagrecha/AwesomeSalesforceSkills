# Well-Architected Notes — Deployment Monitoring

## Relevant Pillars

- **Reliability** — The primary pillar for this skill. Reliable deployment monitoring ensures that failures are detected immediately rather than discovered through end-user reports. Polling to a terminal status, not just polling until a non-error HTTP response, is the difference between a reliable pipeline and one that silently ignores failures. Pending queue management and duplicate-submission prevention are reliability concerns.

- **Operational Excellence** — Deployment monitoring is a direct operational excellence practice. Externalizing deployment logs beyond the 30-day Setup retention window, surfacing structured component failure detail in CI build logs, and maintaining deployment audit trails in change tickets are all operational excellence behaviors that reduce mean time to diagnosis after a production incident.

- **Security** — Deployment monitoring surfaces the full list of metadata components that landed in an org, including changes to permission sets, profiles, sharing rules, and Apex classes with system access. This makes monitoring output a security audit trail. Ensuring that deployment IDs and their associated component lists are retained and correlated with the submitting user's identity supports change traceability requirements in regulated environments.

## Architectural Tradeoffs

**Polling interval vs. payload size:** Using `includeDetails=true` on every poll reduces latency in detecting errors but increases payload size for large orgs. The correct tradeoff is `includeDetails=false` during heartbeat polling and `includeDetails=true` on the first terminal-status poll. Teams that invert this — always including details, or never including details — pay either a bandwidth cost or a diagnostic cost.

**Async submission vs. synchronous blocking:** `sf project deploy start` without `--async` blocks the terminal and ties the deployment lifecycle to the connection. `--async` decouples submission from monitoring but requires explicit ID capture and polling. For CI pipelines running on ephemeral agents, `--async` with an ID-capture step is the only resilient choice. For developer laptops, the tradeoff is convenience versus robustness.

**In-Salesforce history vs. external log store:** The 30-day Setup retention window is a hard platform constraint. Teams that rely on it for audit purposes are one month from losing all evidence of a given deployment. The architectural recommendation is to treat the Setup Deployment Status page as an operational convenience, not an audit system. An external log store is the authoritative audit record.

## Anti-Patterns

1. **Poll-and-forget** — Submitting a deployment and checking its status only once, immediately after submission, then treating `InProgress` or `Pending` as success. This is the most common monitoring failure mode. The deployment may still fail minutes later. All status checks must poll to a terminal state (`Succeeded`, `Failed`, or `Canceled`).

2. **Reusing the validation ID as the quick deploy status handle** — After executing a quick deploy, monitoring the original validation ID rather than the new deployment ID returned by `deployRecentValidation`. The validation ID permanently shows a stale `Succeeded` result. This anti-pattern causes teams to believe deployments succeeded when they are still running or have failed.

3. **Relying on Setup Deployment Status as the sole audit record** — Treating the 30-day Deployment Status page as the system of record for deployment history. For compliance, regulatory, or post-incident review purposes, this creates a silent data retention gap. All deployment results must be externalized at completion time.

## Official Sources Used

- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Metadata API `checkDeployStatus` — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_deploy_checkdeploystatus.htm
- Metadata API `deployRecentValidation` — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_deployrecentvalidation.htm
- REST Metadata API `deployRequest` — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_rest_deploy.htm
- Salesforce CLI Reference (`sf project deploy report`) — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm
- Salesforce DX Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.sfdx_dev.meta/sfdx_dev/sfdx_dev_intro.htm
- Salesforce Well-Architected Framework — https://architect.salesforce.com/well-architected/overview
