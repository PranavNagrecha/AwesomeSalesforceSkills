# Examples — Deployment Monitoring

## Example 1: CI Pipeline Polling Loop with Structured Error Surfacing

**Context:** A GitHub Actions workflow deploys metadata to a production org using `sf project deploy start --async`. The pipeline must block until the deployment completes, then fail the job with structured error output if any components fail.

**Problem:** Without an explicit polling loop, the pipeline either exits immediately (missing the async result) or relies on a fixed sleep duration that is too short for large deployments and too long for small ones. Component error detail is swallowed rather than surfaced in the build log.

**Solution:**

```bash
#!/usr/bin/env bash
set -euo pipefail

# Step 1: Submit the deployment asynchronously and capture the job ID
JOB_OUTPUT=$(sf project deploy start \
  --manifest manifest/package.xml \
  --target-org prod \
  --test-level RunLocalTests \
  --async \
  --json)

JOB_ID=$(echo "$JOB_OUTPUT" | jq -r '.result.id')
echo "Deployment submitted: $JOB_ID"

# Step 2: Poll until terminal status
POLL_INTERVAL=30
while true; do
  REPORT=$(sf project deploy report --job-id "$JOB_ID" --json 2>&1)
  STATUS=$(echo "$REPORT" | jq -r '.result.status')
  DEPLOYED=$(echo "$REPORT" | jq -r '.result.numberComponentsDeployed')
  TOTAL=$(echo "$REPORT"   | jq -r '.result.numberComponentsTotal')
  ERRORS=$(echo "$REPORT"  | jq -r '.result.numberComponentErrors')

  echo "Status: $STATUS | $DEPLOYED/$TOTAL components | $ERRORS errors"

  case "$STATUS" in
    Succeeded)
      echo "Deployment succeeded."
      exit 0
      ;;
    Failed|Canceled)
      echo "Deployment $STATUS — component failures:"
      echo "$REPORT" | jq '.result.details.componentFailures[] | {file: .fileName, type: .problemType, line: .lineNumber, message: .problem}'
      echo "Apex test failures:"
      echo "$REPORT" | jq '.result.details.runTestResult.failures[] | {method: .methodName, message: .message}' 2>/dev/null || true
      exit 1
      ;;
    Pending|InProgress)
      sleep "$POLL_INTERVAL"
      ;;
    *)
      echo "Unknown status: $STATUS — waiting."
      sleep "$POLL_INTERVAL"
      ;;
  esac
done
```

**Why it works:** The `--async` flag decouples submission from monitoring so the pipeline survives terminal reconnects. The loop polls every 30 seconds rather than blocking, and the `case` statement maps each possible `status` value explicitly. Component failures are extracted from `details.componentFailures[]` rather than relying on the human-readable summary, making the output parseable by downstream log aggregation tools.

---

## Example 2: REST Metadata API Polling from a Python Middleware Service

**Context:** A release orchestration service (written in Python) submits deployments to multiple orgs and needs to track status for each deployment without relying on the CLI. The service runs in a container where the Salesforce CLI is not installed.

**Problem:** The service has no way to use CLI commands. The SOAP Metadata API requires a SOAP library and WSDL parsing. The team needs a lightweight HTTP-based approach that returns JSON.

**Solution:**

```python
import time
import urllib.request
import urllib.parse
import json

def poll_deployment(instance_url: str, access_token: str, deploy_id: str,
                    poll_interval: int = 30, api_version: str = "66.0") -> dict:
    """
    Poll the REST Metadata API until the deployment reaches a terminal status.

    Returns the final DeployResult-equivalent JSON dict.
    Raises RuntimeError on non-200 HTTP responses.
    """
    endpoint = (
        f"{instance_url}/services/data/v{api_version}/metadata/"
        f"deployRequest/{deploy_id}?includeDetails=true"
    )
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    terminal_statuses = {"Succeeded", "Failed", "Canceled"}

    while True:
        req = urllib.request.Request(endpoint, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Unexpected HTTP {resp.status} from deployRequest endpoint")
            body = json.loads(resp.read().decode())

        result = body.get("deployResult", {})
        status = result.get("status", "Unknown")
        deployed = result.get("numberComponentsDeployed", 0)
        total = result.get("numberComponentsTotal", 0)
        errors = result.get("numberComponentErrors", 0)

        print(f"Status: {status} | {deployed}/{total} components | {errors} errors")

        if status in terminal_statuses:
            if status == "Failed":
                failures = result.get("details", {}).get("componentFailures", [])
                for f in failures:
                    print(f"  FAIL [{f.get('componentType')}] {f.get('fileName')} "
                          f"line {f.get('lineNumber')}: {f.get('problem')}")
            return result

        time.sleep(poll_interval)


# Usage:
# result = poll_deployment(
#     instance_url="https://myorg.my.salesforce.com",
#     access_token=os.environ["SF_ACCESS_TOKEN"],
#     deploy_id="0Af...",
# )
# assert result["status"] == "Succeeded", f"Deployment failed: {result}"
```

**Why it works:** The REST endpoint `GET .../deployRequest/{id}?includeDetails=true` returns a JSON payload equivalent to the SOAP `DeployResult` without requiring a SOAP library. The `urllib.request` module is Python stdlib — no `requests` dependency. The function blocks until a terminal status is reached and surfaces component failures inline.

---

## Anti-Pattern: Monitoring the Validation ID After Quick Deploy

**What practitioners do:** After running `sf project deploy quick --job-id <validationId>`, practitioners continue polling `sf project deploy report --job-id <validationId>` to check whether the quick deploy succeeded.

**What goes wrong:** The validation ID shows the old completed validation status — `Succeeded` — immediately. The practitioner concludes the deployment succeeded, but the actual quick deploy (which has a different ID) may still be running, queued, or may have failed due to a lock conflict or a concurrent change. The real deployment outcome is silently missed.

**Correct approach:** Capture the new deployment ID returned by the quick deploy command or `deployRecentValidation` API call. This is the ID to monitor. The validation ID is only useful for determining whether the validation is still within the 10-day quick deploy window.

```bash
# WRONG — monitoring the validation ID after quick deploy
sf project deploy report --job-id 0Af_VALIDATION_ID   # shows old "Succeeded"

# CORRECT — capture and monitor the new quick deploy ID
QUICK_DEPLOY_RESULT=$(sf project deploy quick --job-id 0Af_VALIDATION_ID --json)
QUICK_DEPLOY_ID=$(echo "$QUICK_DEPLOY_RESULT" | jq -r '.result.id')
sf project deploy report --job-id "$QUICK_DEPLOY_ID"  # monitors the actual commit
```
