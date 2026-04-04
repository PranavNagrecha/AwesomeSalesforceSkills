# Examples — Security Health Check

## Example 1: Score Drops After a Winter Release

**Context:** A production org has maintained a Health Check score above 92% for six months. After the Winter release activates, the security admin opens Health Check and sees the score has dropped to 74% with no admin changes since the last review.

**Problem:** The team assumes someone changed a setting. Without a systematic review process, they spend time investigating audit logs for setting changes that do not exist. The real cause — a new setting added by the Salesforce release defaulting to a non-compliant state — goes unidentified.

**Solution:**

```
Steps to investigate a post-release score drop:

1. Open Setup → Security → Health Check.
2. Sort or filter the findings by Risk Type — start with High Risk.
3. For each new finding not seen in the previous review, note the Setting Name
   and compare it against release notes for the current release.
4. Use the Tooling API to retrieve the current failing settings list:

   Tooling API endpoint:
   GET /services/data/v63.0/tooling/query/
   ?q=SELECT+SettingName,RiskType,OrgValue,StandardValue,MeetsStandard
      +FROM+SecurityHealthCheckRisks
      +WHERE+MeetsStandard+=+false
      +ORDER+BY+RiskType+ASC

5. Compare the current list against a snapshot taken before the release.
6. For settings that are new additions from the release, remediate by applying
   the standard value or explicitly accepting the risk via Informational
   reclassification with documented justification.
```

**Why it works:** The Tooling API provides a queryable, diff-able record of findings across time. Comparing pre- and post-release snapshots pinpoints which settings are new rather than requiring manual audit-log archaeology. Running Health Check immediately after every major Salesforce release is a required operational step.

---

## Example 2: Building a Custom Baseline for a Regulated Industry Org

**Context:** A financial services org is preparing for a SOC 2 Type II audit. The auditors require a minimum password length of 12 characters, session timeout no longer than 2 hours, and MFA enforcement. The Salesforce standard baseline requires a minimum password length of 8 characters and a 2-hour session timeout, but the org's compliance team wants to measure against stricter thresholds and make any relaxation of those standards visible in the Health Check score.

**Problem:** With the default Salesforce baseline, the org can pass Health Check at 100% with an 8-character minimum password. The compliance team needs the tool to flag any setting that falls below their stricter requirements.

**Solution:**

```
1. Export the current Salesforce standard baseline:
   Setup → Security → Health Check → Baseline Controls → Export Baseline
   This produces an XML file (e.g., SalesforceBaseline.xml).

2. Open the XML and locate the password policy entry. Example structure:

   <setting>
     <settingName>MinPasswordLength</settingName>
     <standardValue>8</standardValue>
     <riskType>HIGH_RISK</riskType>
   </setting>

3. Change standardValue to 12 (the compliance requirement).
   Do not lower any standardValue below the Salesforce default.

4. Repeat for session timeout and any other settings needing stricter thresholds.

5. Save the modified XML with a meaningful name, e.g., FinancialServicesBaseline_v1.xml.

6. Import the custom baseline:
   Setup → Health Check → Baseline Controls → Import Baseline
   Upload the modified XML. Health Check immediately re-evaluates against the new thresholds.

7. Document every changed threshold, the Salesforce default, your custom value,
   and the compliance justification. Store this documentation alongside the XML
   in version control.
```

**Why it works:** Custom baselines make compliance posture visible inside the tool rather than requiring external spreadsheet comparisons. Any admin who accidentally weakens a setting that was compliant under the stricter threshold will see it reflected in the score immediately, rather than discovering the drift during an audit.

---

## Example 3: Automated Health Check Gate in a Deployment Pipeline

**Context:** A DevOps team wants to prevent production deployments that would leave the org below a 90% Health Check score, catching configuration drift introduced by deployment artifacts.

**Problem:** Manual Health Check reviews happen weekly but deployments occur daily. A change set that modifies session settings or password policies could lower the score before the next manual review.

**Solution:**

```python
# Pseudocode for a Tooling API health check gate
# Run via a connected app with "api" scope, using requests (or any HTTP client)

import json, sys, urllib.request, urllib.parse

def get_health_check_score(instance_url, access_token):
    query = "SELECT Score FROM SecurityHealthCheck"
    encoded = urllib.parse.quote(query)
    url = f"{instance_url}/services/data/v63.0/tooling/query/?q={encoded}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    })
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data["records"][0]["Score"] if data["records"] else None

def get_failing_high_risk(instance_url, access_token):
    query = ("SELECT SettingName, OrgValue, StandardValue "
             "FROM SecurityHealthCheckRisks "
             "WHERE MeetsStandard = false AND RiskType = 'HIGH_RISK'")
    encoded = urllib.parse.quote(query)
    url = f"{instance_url}/services/data/v63.0/tooling/query/?q={encoded}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    })
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data.get("records", [])

# Gate logic
score = get_health_check_score(INSTANCE_URL, ACCESS_TOKEN)
high_risk_failures = get_failing_high_risk(INSTANCE_URL, ACCESS_TOKEN)

if score < 90 or high_risk_failures:
    print(f"GATE FAILED: Score={score}, High Risk Failures={len(high_risk_failures)}")
    for r in high_risk_failures:
        print(f"  - {r['SettingName']}: org={r['OrgValue']}, required={r['StandardValue']}")
    sys.exit(1)
print(f"Gate passed: Score={score}")
```

**Why it works:** The Tooling API's `SecurityHealthCheck` and `SecurityHealthCheckRisks` objects expose the same data the Setup UI shows, queryable over HTTP. Integrating this into a post-deployment step catches configuration drift caused by deployments before it goes unnoticed until the next manual review cycle.

---

## Anti-Pattern: Demoting Failing Settings to Informational to Achieve 100%

**What practitioners do:** An admin sees several Low Risk and Medium Risk settings failing Health Check. Rather than remediating the underlying settings, they export the custom baseline, change the `riskType` for each failing setting to `INFORMATIONAL`, reimport the baseline, and report a 100% score.

**What goes wrong:** The settings are still misconfigured — only their contribution to the score has been suppressed. The org remains exposed to the risk those settings represent. During a security audit or incident review, the gap between the reported score and the actual security posture will be visible. Additionally, other teams may rely on a "100% score" as evidence the org is hardened, leading to false assurance across the organization.

**Correct approach:** Remediate the settings if possible. If a setting genuinely cannot be changed due to a business constraint (for example, a legacy integration requires a longer session timeout for service account sessions), document the business justification explicitly, accept the risk formally, and move only that specific setting to Informational with a written exception on file. Blanket reclassification without documented exceptions is a risk governance failure.
