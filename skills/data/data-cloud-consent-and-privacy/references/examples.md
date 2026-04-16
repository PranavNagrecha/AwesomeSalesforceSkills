# Examples — Data Cloud Consent and Privacy

## Example 1: Consent-Aware Marketing Segment

**Context:** A retail company runs a Data Cloud-powered email marketing program. A compliance audit found that the "All Customers" segment used for monthly newsletters did not filter out opted-out customers, violating GDPR.

**Problem:** The segment was built targeting `ssot__Individual__dlm` with demographic filters but had no consent filter. Opted-out customers received marketing emails.

**Solution:**

In Data Cloud Segment Builder, add a related segment filter:

```sql
-- Conceptual filter (Segment Builder equivalent)
-- Base population: ssot__Individual__dlm WHERE Country = 'Germany'
-- Consent filter: ssot__ContactPointConsent__dlm.DataUsePurpose = 'Marketing Email'
--                 AND ssot__ContactPointConsent__dlm.Status = 'OptIn'
```

In the Segment Builder UI:
1. Add the base population filter (e.g., Country = Germany).
2. Click "Add Related Attribute" and select `ssot__ContactPointConsent__dlm`.
3. Set filter: `DataUsePurpose = 'Marketing Email'` AND `Status = 'OptIn'`.
4. Verify segment count decreases (reflecting opted-out exclusions).

**Why it works:** The consent filter joins the segment to the ContactPointConsent DMO and returns only individuals with an active opt-in for the specific Data Use Purpose. Without this explicit filter, opted-out individuals are included.

---

## Example 2: Programmatic GDPR Deletion Request

**Context:** A SaaS company receives GDPR Right to Be Forgotten requests via email. Volume is growing to 50+ requests per week and manual Privacy Center submission is too slow.

**Problem:** The team manually submitted each deletion request via Privacy Center, a process taking 10 minutes per request. With 50+ weekly requests, this consumed significant admin time.

**Solution:**

Automate deletion request submission via the Data Deletion API:

```python
import requests
import json

def submit_deletion_request(dc_token: str, dc_base: str, email: str) -> dict:
    headers = {
        "Authorization": f"Bearer {dc_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "identifiers": [
            {
                "type": "email",
                "value": email
            }
        ]
    }
    resp = requests.post(
        f"{dc_base}/api/v1/privacy/deletion",
        headers=headers,
        json=payload
    )
    resp.raise_for_status()
    return resp.json()

# Process weekly deletion requests from ticket system
requests_queue = ["user1@example.com", "user2@example.com"]
for email in requests_queue:
    result = submit_deletion_request(dc_token, dc_base, email)
    print(f"Deletion job submitted for {email}: {result['jobId']}")
    # Store jobId for status monitoring (processing takes up to 90 days)
```

**Why it works:** The Data Deletion API handles programmatic bulk submission. Processing takes up to 90 days, so job IDs must be stored for status tracking. Manual Privacy Center submission is replaced with an automated pipeline.

---

## Anti-Pattern: Assuming Consent Records Block Segment Membership Automatically

**What practitioners do:** Create consent records in `ssot__ContactPointConsent__dlm` marking customers as opted-out, then build segments without consent filters, assuming the platform will automatically exclude opted-out individuals.

**What goes wrong:** The platform does NOT enforce consent automatically. Opted-out customers appear in segments, get activated to ad platforms and Marketing Cloud, and receive communications they explicitly opted out of — a GDPR/CCPA violation.

**Correct approach:** Every segment used for marketing or activation must include an explicit consent filter joining to `ssot__ContactPointConsent__dlm` with `Status = 'OptIn'` for the relevant Data Use Purpose.
