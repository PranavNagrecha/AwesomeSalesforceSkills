# Gotchas — Deployment Monitoring

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Quick Deploy Returns a Brand-New Deployment ID Distinct from the Validation ID

**What happens:** When `deployRecentValidation` is called (via Metadata API) or `sf project deploy quick --job-id <validationId>` is executed, Salesforce creates a brand-new deployment record and returns a new deployment ID. The original validation ID permanently shows the old validation result — `status: Succeeded` from when the validation completed — not the status of the live commit. Any monitoring tool that polls the validation ID after a quick deploy is silently reading stale data.

**When it occurs:** Every time a quick deploy is executed. This is true regardless of whether the quick deploy is submitted via SOAP, REST, or CLI. The behavior is documented in the Metadata API Developer Guide under `deployRecentValidation` but is frequently overlooked because the validation result looks like a completed success.

**How to avoid:** Capture the new deployment ID returned by the quick deploy call before discarding the CLI output or API response. In the CLI, parse `--json` output and extract `.result.id`. In the REST API, the response body contains the new `id`. Pass this new ID to all subsequent `checkDeployStatus` or `sf project deploy report` calls. Never re-use the validation ID as a proxy for quick deploy status.

---

## Gotcha 2: Pending Queue Order Is Not Guaranteed to Be FIFO

**What happens:** When two or more deployments are submitted to the same org while another is running, they enter a Pending state. Salesforce does not guarantee that Pending deployments execute in submission order. A second deployment submitted 5 seconds after the first may execute before it, particularly under load or when the first deployment entered Pending state very briefly before an earlier one completed.

**When it occurs:** CI pipelines that submit multiple deployments in rapid succession — for example, a feature branch deployment and a concurrent hotfix deployment — are the most common trigger. It also occurs when automated tooling retries a failed submission without checking whether the prior attempt entered Pending rather than failing outright.

**How to avoid:** Serialize deployment submissions in CI pipelines: poll the current org deployment status before submitting the next deployment and only submit when the org is idle (no InProgress or Pending deployments). The REST endpoint `GET .../deployRequest` returns a list of recent requests including their statuses. Alternatively, use a deployment queue abstraction (such as Salesforce DevOps Center pipeline stages) that enforces promotion order by design.

---

## Gotcha 3: Deployment History Is Purged After Exactly 30 Days With No Recovery Option

**What happens:** The Deployment Status page in Setup retains completed deployment records for exactly 30 days. After that, the records are deleted. There is no archive, export button, or recovery path from within Salesforce. The Tooling API `DeployRequest` object is subject to the same 30-day window. Once purged, there is no way to retrieve the original `componentFailures`, `runTestsResult`, or coverage detail for a specific deployment.

**When it occurs:** Any deployment older than 30 days. For teams with audit or compliance requirements — regulated industries, SOX-controlled orgs — this is a persistent risk if deployment results are not externalized at deployment time.

**How to avoid:** At deployment completion, serialize the full DeployResult payload (including `componentFailures` and `runTestsResult`) to an external log store. Common targets include Splunk, Datadog, Elasticsearch, or a CI artifact store (GitHub Actions artifacts, S3). Attach the deployment ID, org ID, timestamp, and the submitting user's identity as indexed fields. Do not rely on screenshots of the Deployment Status page — they are not queryable.

---

## Gotcha 4: `includeDetails=false` Silently Omits Component Failures and Test Results

**What happens:** Calling `checkDeployStatus(id, false)` or the REST endpoint without `?includeDetails=true` returns only the aggregate counts (`numberComponentsDeployed`, `numberComponentsTotal`, `numberComponentErrors`) and the `status` enum. The `componentFailures[]` and `runTestsResult` objects are absent from the response — not empty, absent. Code that inspects these fields without first ensuring `includeDetails=true` silently processes null/empty collections and reports no failures even when the deployment failed.

**When it occurs:** Performance-optimized polling loops that use `includeDetails=false` for heartbeat polls often forget to switch to `includeDetails=true` for the final status check when the deployment has reached a terminal state.

**How to avoid:** Use `includeDetails=false` only during the intermediate polling iterations to reduce payload size. On the first poll that returns a terminal status (`Succeeded`, `SucceededPartial`, `Failed`, `FinalizingDeployFailed`, or `Canceled`), re-issue the call with `includeDetails=true` to capture the full error detail before returning results to the caller.

---

## Gotcha 5: `sf project deploy resume` Re-Attaches but Does Not Re-Submit

**What happens:** If a terminal session is lost while `sf project deploy start` (without `--async`) is running, practitioners sometimes re-run `sf project deploy start` with the same package, believing they are resuming the dropped deployment. This actually submits a second deployment, which enters the Pending queue behind the first. The org is now running two deployments of the same package — one in progress and one pending — which can result in a conflict, a double-application of metadata changes, or an unexpected ordering interaction.

**When it occurs:** Local development environments where a long-running deploy loses the VPN or Wi-Fi connection, or CI runners where the job is cancelled mid-deploy without sending a cancel signal to Salesforce.

**How to avoid:** When a connection is dropped, use `sf project deploy resume --job-id <id>` to re-attach to the already-running async job. If the deployment ID was not saved before the connection was lost, check Setup > Deployment Status or the Tooling API `DeployRequest` to find the in-progress deployment ID. Never re-submit `sf project deploy start` for the same package without first confirming the original deployment is no longer running.

---

## Gotcha 6: A Deployment in `FinalizingDeploy` Cannot Be Canceled at API 65.0+ — and Below 65.0 a Successful Cancel Can Still Commit Data

**What happens:** Cancellation is bounded by a window that closes before the deployment finishes. From Metadata API 65.0 (Winter '26): "For API versions 65.0 and higher, deployments with a status of Finalizing Deploy, can't be cancelled." The call is rejected with `INVALID_ID_FIELD` and the message `You cannot cancel the deployment while finalizing is in progress` — alongside the pre-existing `Invalid deploy ID` and `Deployment already completed` messages. Below 65.0 the platform behaved worse, not better: "For API versions below 65.0, attempts to cancel a deployment may fail if the deployment has started committing data. Alternatively, it's possible that the cancellation will succeed, but data from the deployment is also committed." A `Canceled` status returned by an older call is therefore not evidence that the org is unchanged.

**When it occurs:** Any attempt to abort a large or long-running deployment after it has left `InProgress`. The gating dimension is the **API version of the cancel call** — the `vXX.0` in the REST URI, the WSDL binding version for SOAP, or the version the CLI sends — not the org's release. A Summer '26 org reached at v64.0 by an older integration or a pinned `sourceApiVersion` still exhibits the old, ambiguous behaviour. Teams most often hit this when a production deploy is spotted as wrong mid-flight and someone reaches for cancel as a rollback.

**How to avoid:** Read `status` before offering to cancel. If it is already `FinalizingDeploy`, say so — the only remaining options are to let it finish and then deploy a corrective change, or to restore from a prior known-good package. Do not present cancellation as a rollback at any API version: at 65.0+ it is unavailable once finalizing starts, and below 65.0 a `Canceled` result must be followed by verifying the org's actual metadata state. Because both `cancelDeploy(id)` and `PATCH .../metadata/deployRequest/{id}` (body `{"deployResult": {"status": "Canceling"}}`) are processed asynchronously, the immediate response can read `Canceling` rather than `Canceled` — keep polling `checkDeployStatus` until it settles rather than reporting the first response as the outcome. Both calls require **Modify Metadata Through Metadata API Functions** or **Modify All Data**.
