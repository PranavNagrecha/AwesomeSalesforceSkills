---
name: deployment-monitoring
description: "Tracking the real-time and historical status of Salesforce metadata deployments via Metadata API checkDeployStatus, REST deployRequest polling, and the Deployment Status Setup page. Covers DeployResult field interpretation, component error triage, concurrent deployment queue behavior, and 30-day history limits. NOT for post-deployment functional smoke testing (use post-deployment-validation). NOT for CI/CD pipeline setup (use github-actions-for-salesforce). NOT for rollback execution."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "how do I check whether my Salesforce deployment is still running"
  - "deployment status shows Pending but nothing is happening"
  - "how to programmatically poll deployment progress and surface component errors"
  - "quick deploy returned a new ID and I lost track of the real status"
  - "deployment history disappeared after 30 days and I need to audit it"
  - "multiple deployments are queued and I do not know which one will run next"
tags:
  - deployment-monitoring
  - deploy-status
  - metadata-api
  - checkDeployStatus
  - DeployResult
  - deployment-history
  - devops
inputs:
  - Deployment ID or validation ID returned by sf project deploy start or the Metadata API deploy() call
  - Target org alias or credentials (for CLI-based status polling)
  - Whether the deployment used checkOnly (validation) or a live deploy
outputs:
  - Real-time status snapshot with numberComponentsDeployed, numberComponentsTotal, numberComponentErrors, and status enum value
  - Component failure list with componentType, fileName, problemType, and problem fields
  - Apex test result summary with per-class pass/fail and code coverage percentages
  - Polling script or CI step that exits non-zero on failure and surfaces structured error detail
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Deployment Monitoring

This skill activates when a practitioner or agent needs to track the in-progress or historical status of a Salesforce metadata deployment — whether initiated via Metadata API SOAP, Metadata REST, or the Salesforce CLI — and needs to interpret the DeployResult payload to surface component errors, test failures, and queue position information in a reliable, non-guessing way.

---

## Before Starting

Gather this context before working on anything in this domain:

- Identify the deployment ID. The ID is returned by the Metadata API `deploy()` call, the REST POST to `services/data/vXX.0/metadata/deployRequest`, or the CLI command `sf project deploy start`. If using quick deploy (`deployRecentValidation`), capture the new deployment ID it returns — it is distinct from the original validation ID.
- Confirm the API surface you are using: SOAP Metadata API (`checkDeployStatus`), REST Metadata API (`GET .../deployRequest/{id}?includeDetails=true`), or Salesforce CLI (`sf project deploy report --job-id <id>`). All three expose the same underlying DeployResult data, but the call shape differs.
- Know that only one deployment runs at a time per org. Additional submissions enter a Pending queue and are not guaranteed to execute in submission order. A Pending status does not mean the deployment has failed or stalled — it means the org is already running another deployment.

---

## Core Concepts

### DeployResult Status Enum

Every deployment passes through a predictable status progression exposed on the `DeployResult.status` field:

| Status | Meaning |
|---|---|
| Pending | The deployment is queued. Another deployment is currently running in the org. |
| InProgress | The metadata is being compiled and deployed. `numberComponentsDeployed` increments as components succeed. |
| Succeeded | All components deployed successfully and all Apex tests passed (if a test level was specified). |
| Failed | One or more components failed or required Apex tests did not pass. The `componentFailures` and `runTestsResult` arrays contain detail. |
| Canceled | The deployment was explicitly canceled via the Metadata API `cancelDeploy()` call or from the Deployment Status page in Setup. |

Polling on `status` and treating any non-Succeeded terminal state as a failure is the correct pattern. Do not treat `InProgress` as success.

### checkDeployStatus and includeDetails

The primary programmatic monitoring mechanism is the Metadata API method `checkDeployStatus(ID id, boolean includeDetails)`. When `includeDetails` is `true`, the response includes:

- `componentFailures[]` — each entry has `componentType`, `fileName`, `problemType` (Error or Warning), `problem` (message), `lineNumber`, and `columnNumber`.
- `runTestsResult` — contains `numFailures`, `failures[]` (with `methodName`, `message`, `stackTrace`), `codeCoverage[]` (per-class lines covered/not covered), and `codeCoverageWarnings[]`.

When `includeDetails` is `false`, the response returns only aggregate counts (`numberComponentsTotal`, `numberComponentsDeployed`, `numberComponentErrors`) and the `status` enum, which is sufficient for a lightweight heartbeat poll. Use `includeDetails=true` only on the final status check or when you need to surface errors, because the payload can be large for orgs with many components.

The REST equivalent is `GET services/data/vXX.0/metadata/deployRequest/{id}?includeDetails=true`. The CLI equivalent is `sf project deploy report --job-id <id>`.

### Deployment Queue and Concurrency

Only one deployment can run at a time per Salesforce org. When a second deployment is submitted while one is running, it enters a Pending state. Multiple Pending deployments are not guaranteed to execute in submission order — Salesforce makes no FIFO guarantee for the pending queue. Submitting many deployments in rapid succession from a CI pipeline can result in unpredictable execution order.

If a connection drops while a deployment is running (`sf project deploy start` loses the terminal session), the deployment continues in the org. It can be resumed with `sf project deploy resume --job-id <id>`, which re-attaches the CLI to the already-running async job.

### Deployment History Retention

The Deployment Status page (Setup > Deployment Status) retains deployment history for exactly 30 days. After 30 days, records are purged and are not recoverable from Setup. If your audit or compliance process requires longer retention, the history must be externalized — for example by logging the full `DeployResult` payload to an external system (Splunk, Datadog, CloudWatch) at deployment time. The Tooling API `DeployRequest` object can also be queried for recent deployments but is subject to the same 30-day window.

---

## Common Patterns

### Pattern 1 — Polling Loop with Structured Error Output

**When to use:** Automated CI/CD pipelines where a deployment is submitted asynchronously and the pipeline must block until completion and surface errors in a parseable format.

**How it works:**

```bash
# Submit the deployment and capture the job ID
JOB_ID=$(sf project deploy start --manifest manifest/package.xml \
  --target-org prod --async --json | jq -r '.result.id')

# Poll until terminal status
while true; do
  RESULT=$(sf project deploy report --job-id "$JOB_ID" --json)
  STATUS=$(echo "$RESULT" | jq -r '.result.status')
  case "$STATUS" in
    Succeeded)
      echo "Deployment succeeded."
      exit 0
      ;;
    Failed|Canceled)
      echo "Deployment $STATUS."
      echo "$RESULT" | jq '.result.details.componentFailures[]'
      exit 1
      ;;
  esac
  sleep 30
done
```

**Why not the alternative:** Using `sf project deploy start` without `--async` blocks the terminal but loses the job ID on connection drop. The async pattern decouples submission from monitoring and lets the pipeline resume with `sf project deploy resume` if interrupted.

### Pattern 2 — REST Metadata API Polling with includeDetails

**When to use:** Server-side integrations (Apex HTTP callout from a tool, or a middleware service) where you need DeployResult detail without the CLI.

**How it works:**

```
GET /services/data/v66.0/metadata/deployRequest/{deployId}?includeDetails=true
Authorization: Bearer {accessToken}
```

Response includes the `deployResult` object with `status`, `numberComponentsDeployed`, `numberComponentsTotal`, `numberComponentErrors`, and the `details` block containing `componentFailures` and `runTestResult`. Poll this endpoint every 10–30 seconds. Stop polling when `status` is one of `Succeeded`, `Failed`, or `Canceled`.

**Why not the alternative:** The SOAP `checkDeployStatus` call requires constructing a SOAP envelope and parsing WSDL-typed responses. The REST endpoint returns JSON and is easier to integrate into modern tooling without a SOAP library.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| CLI-based deployment in a CI pipeline | `sf project deploy start --async` then poll `sf project deploy report` | Decouples submission from monitoring; survives terminal disconnects |
| Middleware or server-side monitoring | REST GET `.../deployRequest/{id}?includeDetails=true` | JSON response; no SOAP library required |
| Need per-component error detail | Set `includeDetails=true` on the final status check | Large payload; only pull detail when needed |
| Deployment shows Pending with no progress | Check whether another deployment is running in the org | Only one deployment runs at a time; Pending is normal when the queue is occupied |
| Status shows InProgress but CLI disconnected | `sf project deploy resume --job-id <id>` | The deployment continues in the org; resume re-attaches the CLI |
| Need audit trail beyond 30 days | Log the full DeployResult JSON to external storage at deploy time | Setup history is purged after 30 days with no recovery option |
| Quick deploy was executed | Monitor the new deployment ID returned by deployRecentValidation | The original validation ID shows stale data after quick deploy |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Capture the deployment ID** — Record the ID immediately from the `sf project deploy start --json` output (`.result.id`) or from the Metadata API `deploy()` response. If the ID was lost, check Setup > Deployment Status to find recent deployments by timestamp. If a quick deploy was executed, use the new ID returned by `deployRecentValidation`, not the original validation ID.

2. **Poll for status using the appropriate surface** — Use `sf project deploy report --job-id <id>` for CLI-based monitoring, `GET .../deployRequest/{id}` for REST-based monitoring, or `checkDeployStatus(id, false)` via SOAP for lightweight heartbeat polling. Continue polling until `status` is `Succeeded`, `Failed`, or `Canceled`. A `Pending` status is normal while another deployment occupies the queue.

3. **On failure, pull component error detail** — Re-issue the status call with `includeDetails=true` (or `sf project deploy report --job-id <id>` which includes detail by default). Iterate over `componentFailures[]` and surface `fileName`, `problemType`, `lineNumber`, and `problem` for each failure. For Apex test failures, check `runTestsResult.failures[]` for `methodName`, `message`, and `stackTrace`.

4. **Validate coverage if tests ran** — If the deployment ran Apex tests, check `runTestsResult.codeCoverage[]` for per-class coverage percentages. The minimum is 75% per class in the deployment package when using RunSpecifiedTests. Identify any under-covered classes and surface them explicitly, not just the aggregate.

5. **Externalize the result if audit retention is required** — If the org's compliance policy requires deployment history longer than 30 days, write the full `DeployResult` payload (serialized as JSON) to an external log store. The Setup Deployment Status page purges records at 30 days.

6. **Document the deployment ID and outcome** — Record the deployment ID, timestamp, status, component count, and any errors in the release runbook or change ticket. This ID is the primary reference for post-mortem analysis and cross-references the Tooling API `DeployRequest` object.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Deployment ID captured and recorded (not lost on terminal disconnect)
- [ ] Status polled to a terminal state (`Succeeded`, `Failed`, or `Canceled`) — not stopped at `InProgress`
- [ ] Component failures iterated and surfaced with `fileName`, `problemType`, and `problem` fields
- [ ] Apex test failures reviewed via `runTestsResult.failures[]` with method name and stack trace
- [ ] Per-class code coverage checked against the 75% threshold for all classes in the package
- [ ] Quick deploy ID confirmed as the new ID from `deployRecentValidation`, not the validation ID
- [ ] Deployment result logged to external storage if 30-day audit retention is required

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Quick deploy returns a brand-new deployment ID** — When `deployRecentValidation` is called to execute a quick deploy, Salesforce assigns a new deployment ID to the live commit. The original validation ID shows the old validation result, not the current deployment status. Monitoring the wrong ID silently reports a stale completed status while the real deployment is still running or has failed.

2. **Pending queue order is not guaranteed** — Salesforce does not guarantee FIFO ordering for the Pending deployment queue. If multiple deployments are submitted in rapid succession from a CI pipeline, they may execute in any order. This can cause a hotfix deployment submitted after a feature deployment to execute first, producing an unexpected metadata state.

3. **Deployment history is purged after exactly 30 days** — The Deployment Status page and its underlying data are deleted 30 days after the deployment completed. There is no archive, export, or recovery mechanism. Teams that discover a compliance gap after 30 days have no recourse from within Salesforce.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Real-time status snapshot | Current `status`, `numberComponentsDeployed`, `numberComponentsTotal`, `numberComponentErrors` from DeployResult |
| Component failure report | List of `componentFailures[]` entries with `fileName`, `componentType`, `problemType`, `lineNumber`, and `problem` for each failure |
| Apex test result summary | `runTestsResult` breakdown: total tests, failures with stack traces, per-class code coverage percentages |
| Deployment audit log entry | Full serialized DeployResult JSON written to external log store with deployment ID, timestamp, and org identifier |

---

## Related Skills

- `post-deployment-validation` — use after monitoring confirms a `Succeeded` status; covers functional smoke testing, permission verification, and rollback planning
- `release-management` — use for deployment sequencing strategy, environment promotion ordering, and change advisory board coordination
- `devops-process-documentation` — use to document deployment runbooks that embed deployment IDs, monitoring steps, and rollback procedures
- `automated-regression-testing` — use for CI pipeline construction that triggers deployments and parses monitoring output to gate releases
