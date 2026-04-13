# Deployment Monitoring — Work Template

Use this template when tracking or diagnosing the status of a Salesforce metadata deployment.

## Scope

**Skill:** `deployment-monitoring`

**Request summary:** (fill in what was asked — e.g. "check why deployment 0Af... shows Pending", "surface component errors for failed deploy", "set up CI polling loop")

---

## Deployment Context

Fill in before starting any monitoring work:

| Field | Value |
|---|---|
| Deployment ID | `0Af...` |
| Deployment type | Live deploy / Validation (checkOnly) / Quick deploy |
| Submitted via | SF CLI / Metadata API SOAP / Metadata API REST / DevOps Center |
| Target org | (alias or instance URL) |
| Submitted at | (timestamp with timezone) |
| Submitted by | (user or service account) |
| Quick deploy? | Yes — new deploy ID: `0Af...` / No |

---

## Current Status Check

Run the appropriate command and fill in the result:

```bash
# CLI
sf project deploy report --job-id <DEPLOY_ID> --json

# REST
curl -H "Authorization: Bearer $SF_TOKEN" \
  "$SF_INSTANCE_URL/services/data/v66.0/metadata/deployRequest/<DEPLOY_ID>?includeDetails=true"
```

| Field | Value |
|---|---|
| `status` | Pending / InProgress / Succeeded / Failed / Canceled |
| `numberComponentsDeployed` | |
| `numberComponentsTotal` | |
| `numberComponentErrors` | |
| `startDate` | |
| `completedDate` | |

---

## Component Failures (fill if status = Failed)

List each entry from `componentFailures[]`:

| # | `fileName` | `componentType` | `problemType` | `lineNumber` | `problem` |
|---|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |

---

## Apex Test Failures (fill if tests ran)

From `runTestsResult.failures[]`:

| # | `methodName` | `message` | `stackTrace` |
|---|---|---|---|
| 1 | | | |
| 2 | | | |

**Aggregate coverage:** `numTestsRun`: ___ | `numFailures`: ___ | Org coverage: ___%

---

## Per-Class Coverage (fill if RunSpecifiedTests or RunLocalTests)

Identify any class below 75%:

| Apex Class | Lines Covered | Lines Not Covered | Coverage % |
|---|---|---|---|
| | | | |

---

## Queue Status (fill if status = Pending)

- Is another deployment currently InProgress in this org? Yes / No
- If yes, what is the running deployment ID? `0Af...`
- Action: Wait for the running deployment to reach terminal status before expecting this one to start.

---

## Checklist

Work through these before closing the task:

- [ ] Deployment ID captured and confirmed (not the validation ID if quick deploy was used)
- [ ] Status polled to a terminal state — not stopped at InProgress
- [ ] All `componentFailures[]` entries reviewed and triaged
- [ ] Apex test failures reviewed with method name, message, and stack trace
- [ ] Per-class code coverage checked against 75% threshold
- [ ] Deployment result JSON written to external log store if audit retention > 30 days is required
- [ ] Deployment ID and outcome recorded in the release ticket or runbook

---

## Notes and Deviations

Record any non-standard behavior observed (e.g. unexpected Pending duration, ID change after quick deploy, coverage discrepancy):

(free text)

---

## Polling Script (CI — fill in job ID and org)

```bash
#!/usr/bin/env bash
set -euo pipefail

JOB_ID="0Af..."          # replace with actual deployment ID
TARGET_ORG="prod"        # replace with org alias
POLL_INTERVAL=30

while true; do
  REPORT=$(sf project deploy report --job-id "$JOB_ID" --target-org "$TARGET_ORG" --json 2>&1)
  STATUS=$(echo "$REPORT" | jq -r '.result.status')
  DEPLOYED=$(echo "$REPORT" | jq -r '.result.numberComponentsDeployed')
  TOTAL=$(echo "$REPORT"   | jq -r '.result.numberComponentsTotal')
  ERRORS=$(echo "$REPORT"  | jq -r '.result.numberComponentErrors')

  echo "$(date -u +%H:%M:%SZ) | $STATUS | $DEPLOYED/$TOTAL | $ERRORS errors"

  case "$STATUS" in
    Succeeded)
      echo "PASS: Deployment succeeded."
      exit 0
      ;;
    Failed|Canceled)
      echo "FAIL: Deployment $STATUS."
      echo "$REPORT" | jq '.result.details.componentFailures[]' 2>/dev/null || true
      exit 1
      ;;
    Pending|InProgress)
      sleep "$POLL_INTERVAL"
      ;;
    *)
      echo "Unknown status: $STATUS"
      sleep "$POLL_INTERVAL"
      ;;
  esac
done
```
