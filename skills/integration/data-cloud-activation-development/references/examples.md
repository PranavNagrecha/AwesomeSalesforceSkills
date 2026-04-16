# Examples — Data Cloud Activation Development

## Example 1: Webhook Data Action Target with HMAC Verification

**Context:** A retail company uses Data Cloud to unify customer profiles. When a customer's churn risk score exceeds a threshold (modeled as a Streaming Insight condition on the UnifiedIndividual DMO), an external customer success platform should receive a near-real-time webhook notification.

**Problem:** The team created a webhook Data Action Target but left the HMAC secret key blank because they planned to add it later. No webhook events were delivered and no error was logged in Data Cloud.

**Solution:**

1. Delete and recreate the Data Action Target with the HMAC secret key configured at creation.
2. Create a Streaming Insight monitoring ChurnRiskScore > 80 on the UnifiedIndividual DMO.
3. Link the Streaming Insight to the Data Action Target.
4. Implement HMAC verification in the receiver:

```python
import hmac
import hashlib
from flask import Flask, request, abort

app = Flask(__name__)
SECRET_KEY = "your-hmac-secret-key"

@app.route("/webhook/churn-alert", methods=["POST"])
def handle_churn_alert():
    sig = request.headers.get("X-SFDC-Signature", "")
    raw_body = request.get_data()
    
    expected = hmac.new(
        SECRET_KEY.encode("utf-8"),
        raw_body,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(expected, sig):
        abort(403, "Invalid signature")
    
    payload = request.json
    # Process churn alert
    return {"status": "received"}, 200
```

**Why it works:** The HMAC key must be set at creation — blank key causes silent payload drop. HMAC verification prevents unauthorized callers from submitting fake churn alerts.

---

## Example 2: Data Cloud-Triggered Flow Creating a CRM Task on New High-Value Profile

**Context:** When a new unified profile is created in Data Cloud with an estimated lifetime value above $50,000 (inserted into the HighValueIndividual custom DMO), a Salesforce task should automatically be created for the assigned Account Executive.

**Problem:** The team built a record-triggered Flow on the Contact object hoping it would fire when Data Cloud created unified profiles. It never fired because Data Cloud DMO insertions do not trigger CRM record-triggered Flows.

**Solution:**

1. Build an autolaunched Flow `DC_HighValueProfile_TaskCreate` with an input variable `{IndividualId}` (the DMO record ID).
2. In the Flow, query the CRM Contact by matching external ID, then create a Task for the associated Account Executive.
3. Activate the Flow.
4. In Data Cloud Setup > Data Cloud-Triggered Flows, create a new entry binding the Flow to the HighValueIndividual DMO.
5. Activate the triggered flow binding.

**Why it works:** Data Cloud-Triggered Flows fire on DMO row insertion — the correct trigger surface for Data Cloud → CRM automation. Record-triggered Flows on CRM objects cannot watch Data Cloud DMO insertions.

---

## Anti-Pattern: Using Activation Targets for Event-Level Webhook Integration

**What practitioners do:** Create a webhook target under "Activation Targets" in Data Cloud Setup, expecting it to fire near-real-time on individual profile events.

**What goes wrong:** Activation Targets are segment-level batch publishers — they export segment membership lists on a schedule, not individual profile events in near-real-time. The webhook fires once per batch publish with a full segment export payload, not per individual event.

**Correct approach:** Use "Data Action Targets" in Data Cloud Setup for event-level near-real-time webhook integration. Data Action Targets fire based on Streaming Insight conditions evaluated per DMO event.
