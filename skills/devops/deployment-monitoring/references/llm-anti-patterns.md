# LLM Anti-Patterns — Deployment Monitoring

Common mistakes AI coding assistants make when generating or advising on Deployment Monitoring.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating `InProgress` as a Success Indicator

**What the LLM generates:**

```bash
sf project deploy start --manifest package.xml --target-org prod
echo "Deployment in progress — assuming success."
# continues without polling
```

Or in polling logic:

```bash
STATUS=$(sf project deploy report --job-id "$JOB_ID" --json | jq -r '.result.status')
if [ "$STATUS" != "Failed" ]; then
  echo "Success"
fi
```

**Why it happens:** LLMs trained on general CI patterns assume that the absence of an error code equals success. `InProgress` is not a failure, so naive negative-condition checks treat it as success.

**Correct pattern:**

```bash
# Only treat the explicit terminal Succeeded state as success
case "$STATUS" in
  Succeeded) echo "Success"; exit 0 ;;
  Failed|Canceled) echo "Failed"; exit 1 ;;
  Pending|InProgress) sleep 30; continue ;;  # keep polling
esac
```

**Detection hint:** Look for `!= "Failed"` or `== "InProgress"` as the sole condition for treating a deployment as complete. Any check that does not wait for `Succeeded` as the explicit positive terminal state is wrong.

---

## Anti-Pattern 2: Monitoring the Validation ID After Quick Deploy

**What the LLM generates:**

```bash
# After validation
VALIDATION_ID="0AfXXXXXXXXXXXXX"

# Execute quick deploy
sf project deploy quick --job-id "$VALIDATION_ID" --target-org prod

# Monitor the same validation ID — WRONG
sf project deploy report --job-id "$VALIDATION_ID"
```

**Why it happens:** LLMs see the validation ID used for the quick deploy command and assume the same ID tracks the resulting deployment. The API distinction between a validation record and a new deployment record created by `deployRecentValidation` is a Salesforce-specific behavior not present in most deployment systems.

**Correct pattern:**

```bash
# Capture the NEW deployment ID from the quick deploy output
QUICK_RESULT=$(sf project deploy quick --job-id "$VALIDATION_ID" --json)
QUICK_DEPLOY_ID=$(echo "$QUICK_RESULT" | jq -r '.result.id')

# Monitor the new ID — not the validation ID
sf project deploy report --job-id "$QUICK_DEPLOY_ID"
```

**Detection hint:** Any script that uses the same variable for both `sf project deploy quick --job-id` and the subsequent `sf project deploy report --job-id` without reassigning the ID from the quick deploy output is wrong.

---

## Anti-Pattern 3: Assuming `includeDetails=true` Is the Default

**What the LLM generates:**

```python
# Python pseudo-code
response = requests.get(
    f"{instance_url}/services/data/v66.0/metadata/deployRequest/{deploy_id}",
    headers={"Authorization": f"Bearer {token}"}
)
failures = response.json()["deployResult"]["details"]["componentFailures"]
# KeyError or empty list — details were not requested
```

**Why it happens:** LLMs model the REST endpoint as returning full detail by default. The `includeDetails=true` query parameter is a Salesforce-specific requirement that does not have an obvious analogue in generic REST APIs.

**Correct pattern:**

```python
response = requests.get(
    f"{instance_url}/services/data/v66.0/metadata/deployRequest/{deploy_id}",
    params={"includeDetails": "true"},  # required to get componentFailures
    headers={"Authorization": f"Bearer {token}"}
)
result = response.json()["deployResult"]
failures = result.get("details", {}).get("componentFailures", [])
```

**Detection hint:** Any REST call to the `deployRequest` endpoint that lacks `?includeDetails=true` and then accesses `componentFailures` or `runTestResult` is incorrect.

---

## Anti-Pattern 4: Re-Submitting the Deployment Instead of Resuming After a Disconnect

**What the LLM generates:**

```bash
# Connection dropped. Resume by re-running:
sf project deploy start --manifest package.xml --target-org prod
```

**Why it happens:** LLMs apply a generic "retry failed command" heuristic. The distinction between a dropped terminal connection (deployment still running in the org) and an actual deployment failure (deployment stopped) is Salesforce-specific. Most systems require resubmission on connection loss; Salesforce deployments continue asynchronously.

**Correct pattern:**

```bash
# Check if the original deployment is still running
sf project deploy report --job-id "$SAVED_JOB_ID"

# If InProgress or Pending, re-attach — do NOT resubmit
sf project deploy resume --job-id "$SAVED_JOB_ID"

# Only resubmit if the deployment actually failed or was canceled
```

**Detection hint:** Any advice to re-run `sf project deploy start` after a connection loss without first checking the status of the original deployment is incorrect. Always check status before resubmitting.

---

## Anti-Pattern 5: Treating the 30-Day Deployment Status Page as an Audit System

**What the LLM generates:**

```
"To audit deployments from last quarter, go to Setup > Deployment Status 
and review the deployment history there."
```

Or in runbook guidance:

```
"Deployment history can be reviewed in Setup > Deployment Status for all 
past deployments."
```

**Why it happens:** LLMs describe the Deployment Status page as the Salesforce deployment history feature, which is accurate as far as it goes, but omit the critical 30-day retention limit. Training data includes Salesforce documentation that describes the page without prominently featuring the retention window.

**Correct pattern:**

```
"Setup > Deployment Status retains records for exactly 30 days. For compliance 
or post-incident review beyond 30 days, deployment results must be externalized 
to an external log store (e.g. Splunk, Datadog, S3) at deployment completion 
time. The Tooling API DeployRequest object is subject to the same 30-day limit."
```

**Detection hint:** Any reference to Setup > Deployment Status as a source of historical deployment data without mentioning the 30-day retention limit is incomplete and potentially misleading for regulated orgs.

---

## Anti-Pattern 6: Using SOAP `checkDeployStatus` Without Setting a Timeout on Long-Running Deployments

**What the LLM generates:**

```java
// Synchronous polling with no timeout
while (true) {
    DeployResult result = metadataConnection.checkDeployStatus(deployId, true);
    if (result.isDone()) break;
    Thread.sleep(5000);
}
```

**Why it happens:** LLMs model the polling loop as a simple `isDone()` check without a maximum duration guard. For large orgs with many Apex tests, deployments can run for 30–90 minutes. A polling loop without a timeout ceiling will block indefinitely if the org becomes unresponsive or the deployment stalls.

**Correct pattern:**

```java
long maxWaitMs = 90 * 60 * 1000L; // 90 minutes
long started = System.currentTimeMillis();
while (true) {
    if (System.currentTimeMillis() - started > maxWaitMs) {
        throw new RuntimeException("Deployment monitoring timed out after 90 minutes");
    }
    DeployResult result = metadataConnection.checkDeployStatus(deployId, false);
    if (result.isDone()) {
        // Re-fetch with includeDetails for the final result
        result = metadataConnection.checkDeployStatus(deployId, true);
        break;
    }
    Thread.sleep(30_000);
}
```

**Detection hint:** Any SOAP or REST polling loop that calls `checkDeployStatus` or polls the REST endpoint without a maximum elapsed time guard is missing a critical safety bound.
