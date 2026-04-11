# Examples — Einstein Discovery Development

## Example 1: Real-Time Opportunity Score via Apex Callout

**Context:** A Sales Cloud org has an Einstein Discovery story trained on Opportunity data to predict the expected revenue (regression). The business wants the predicted CLV displayed on the Opportunity record page as a field, refreshed when a sales rep clicks a "Recalculate" button. The prediction definition ID is `1ORB000000000bOOAQ`.

**Problem:** Without this skill's guidance, a developer might attempt to use SOQL or a custom formula field to retrieve an "Einstein score," or assume the score auto-updates when opportunity fields change. Neither works—Einstein Discovery scores require an explicit API call and do not update reactively.

**Solution:**

```apex
// Named Credential: EinsteinDiscoveryNC (OAuth, session-based or connected app)
// Run from an @InvocableMethod or Lightning component Apex controller

public class EinsteinDiscoveryCallout {

    public static String predict(String recordId, String predDefId) {
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:EinsteinDiscoveryNC/services/data/v66.0/smartdatadiscovery/predict');
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/json');

        // Request type 'Records': pass up to 200 Salesforce record IDs
        Map<String, Object> body = new Map<String, Object>{
            'predictionDefinition' => predDefId,
            'type' => 'Records',
            'records' => new List<String>{ recordId },
            'settings' => new Map<String, Object>{
                'maxPrescriptions' => 3,
                'maxMiddleValues' => 3,
                'prescriptionImpactPercentage' => 80
            }
        };
        req.setBody(JSON.serialize(body));

        HttpResponse res = new Http().send(req);
        if (res.getStatusCode() != 200) {
            throw new CalloutException('Einstein predict failed: ' + res.getBody());
        }

        // Parse prediction total from response
        Map<String, Object> responseMap = (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
        List<Object> predictions = (List<Object>) responseMap.get('predictions');
        Map<String, Object> first = (Map<String, Object>) predictions[0];
        Map<String, Object> prediction = (Map<String, Object>) first.get('prediction');
        return String.valueOf(prediction.get('total'));
    }
}
```

**Why it works:** Using type `Records` with a Salesforce record ID lets Einstein Discovery look up all the feature values mapped in the story automatically. The `settings` object is required from API v50.0 onward to receive top predictors and prescriptions—without it, only the raw score total is returned. The Named Credential handles OAuth token management without embedding credentials in Apex.

---

## Example 2: Scheduled Bulk Scoring After Nightly Model Refresh

**Context:** A financial services org runs a daily batch job to re-score all active Account records with Einstein Discovery's churn probability model (binary classification). After the model is refreshed each Sunday, the following Monday batch must use the new model version. The story is tied to a prediction definition with ID `1ORB00000004CApOAM`.

**Problem:** Without explicit handling, teams often miss that (1) a refreshed model must be activated before bulk scoring picks it up, and (2) bulk scoring jobs silently pause when the org daily predictions limit is reached, causing downstream pipelines to time out waiting for a `Completed` status that never arrives.

**Solution:**

```python
# External integration script (Python, using Connected App OAuth)
# Demonstrates bulk predict job creation and polling with pause handling

import requests, time

BASE_URL = "https://myorg.my.salesforce.com/services/data/v66.0/smartdatadiscovery"
HEADERS = {"Authorization": "Bearer <access_token>", "Content-Type": "application/json"}
PRED_DEF_ID = "1ORB00000004CApOAM"

# Step 1: Create bulk predict job scoped to active Accounts
job_payload = {
    "predictionDefinition": PRED_DEF_ID,
    "filter": {"fieldName": "IsActive__c", "operator": "eq", "value": "true"}
}
resp = requests.post(f"{BASE_URL}/predictjobs", json=job_payload, headers=HEADERS)
resp.raise_for_status()
job_id = resp.json()["id"]
print(f"Bulk job created: {job_id}")

# Step 2: Poll for completion; handle Paused gracefully
max_polls = 120
poll_interval = 60  # seconds
for attempt in range(max_polls):
    status_resp = requests.get(f"{BASE_URL}/predictjobs/{job_id}", headers=HEADERS)
    status = status_resp.json().get("status")
    print(f"Attempt {attempt+1}: status={status}")

    if status == "Completed":
        print("Scoring complete.")
        break
    elif status == "Paused":
        # Daily predictions limit reached — job auto-resumes tomorrow
        # Do NOT call delete or restart; log and exit gracefully
        print("Job paused due to daily predictions limit. Will resume automatically tomorrow.")
        break
    elif status == "Failed":
        raise RuntimeError(f"Bulk predict job failed: {status_resp.json()}")

    time.sleep(poll_interval)
else:
    print("Max polls reached without completion. Check job manually.")
```

**Why it works:** The explicit `Paused` branch prevents false-failure alerts. Polling at 60-second intervals with a cap avoids hammering the API. In production, replace the `time.sleep` loop with a scheduled async check (e.g., a Platform Event or scheduled Apex) rather than blocking synchronously.

---

## Anti-Pattern: Using RawData Without Matching Story Column Names

**What practitioners do:** When calling `POST /smartdatadiscovery/predict` with `type: RawData`, developers guess column names or copy field API names directly from the Salesforce object, resulting in all values landing in `importWarnings.missingColumns`.

**What goes wrong:** If the column names in the `columnNames` array do not exactly match the field names the story was trained on, Einstein Discovery cannot map the inputs. The prediction still returns a score (using base rates), but the `importWarnings.missingColumns` array is populated and the score is unreliable. This is a silent failure—the API returns HTTP 200 with a prediction value, giving no obvious error signal.

**Correct approach:** Retrieve the active model's field configuration with `GET /smartdatadiscovery/models/{modelId}` and inspect the `fields` array to get the exact column names used during training. Use those names verbatim in the `columnNames` array of the RawData request. Always check `importWarnings.missingColumns` in the response before trusting the returned score.
