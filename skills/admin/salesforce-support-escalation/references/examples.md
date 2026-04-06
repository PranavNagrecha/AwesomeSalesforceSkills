# Examples — Salesforce Support Escalation

## Example 1: Opening a Sev1 Case for a Complete Org Outage

**Context:** A B2B SaaS company's production Salesforce org goes down at 9:15 AM on a Tuesday. Sales reps cannot log in, no orders can be entered, and the integration with the ERP system has stopped. The company has a Premier Success Plan.

**Problem:** The admin opens the Help portal and is unsure whether to call or submit online, what to write in the description, and whether the Trust site showing "Investigating" means a case is unnecessary.

**Solution:**

```
Step 1 — Check trust.salesforce.com for the org's instance (e.g., NA135).
  - The instance shows "Investigating" under Core Services.
  - This confirms Salesforce is already aware. Subscribe to the incident for email updates.

Step 2 — Open a support case anyway, because:
  - The case creates a formal record tied to the org ID.
  - The case can capture org-specific diagnostic data (custom code, integrations) that the
    general incident team may not be aware of.
  - Resolution of the general incident does not guarantee the org-specific issue resolves.

Step 3 — Navigate to help.salesforce.com > Contact Support > select "Salesforce Platform"
  > Severity: Sev1 > check "Request phone callback"

Step 4 — Case description (fill in exact values):
  Org ID: 00D3x000000XXXXX
  Instance: NA135
  Impact: ALL 200 users locked out of production since 09:15 AM PT
  Business impact: ~$15,000/hour in blocked orders; ERP integration down
  Error: "Service Unavailable" on login; Apex REST endpoint returning 503
  Time started: 09:15 AM PT Tuesday
  Steps to reproduce: Navigate to https://[instance].salesforce.com — login page
  does not load; returns HTTP 503

Step 5 — Post case number in #salesforce-incidents Slack channel with:
  - Case number
  - Trust site incident URL
  - Current status
  - Estimated resolution from Trust site (if available)
```

**Why it works:** Even when an incident is already on the Trust site, a case filed with org-specific data ensures the support team can correlate your org's symptoms. The clear business impact statement ("$15,000/hour") establishes urgency without overstating the severity classification.

---

## Example 2: Escalating a Stalled Sev2 Case

**Context:** A Premier customer filed a Sev2 case at 8 AM reporting that the Lightning Service Console is broken for 50 agents — case feeds are not loading. It is now 10:30 AM (2.5 hours later), and the only response was an automated acknowledgment. The Premier SLA for Sev2 is 1 hour. Stakeholders are asking for an update every 15 minutes.

**Problem:** The admin does not know whether to wait, re-open the case, or call someone. The case shows status "In Progress" with no engineer assigned.

**Solution:**

```
Step 1 — Add a case comment documenting the timeline:
  "Case opened at 08:00 AM PT. Premier SLA for Sev2 is 1 hour. It is now 10:30 AM PT
   with no engineer response beyond the automated acknowledgment. 50 agents remain
   unable to use Service Console. Issue persists — no workaround found."

Step 2 — Click the "Escalate to Technical Support Management" button on the case.
  This creates a formal escalation record with a timestamp and routes to a
  Support Manager's queue.
  Note the escalation timestamp: 10:32 AM PT.

Step 3 — Contact the Success Manager directly (Premier customers have a named contact).
  Message: "Case [number] — Sev2 Service Console outage for 50 agents, opened 8 AM,
   now 2.5h without engineer contact. Escalation button used at 10:32 AM.
   Can you check status internally?"

Step 4 — Update stakeholders:
  "Case [number] filed at 8 AM. Formal escalation submitted at 10:32 AM.
   Success Manager engaged. Expecting engineer contact within 1 hour."

Step 5 — If no contact by 11:30 AM, use Premier phone support line for Sev2 issues.
```

**Why it works:** The in-case escalation button is a formal mechanism, not just a notification. It moves the case to a manager's queue and creates an audit trail. Pairing it with a clear comment ensures the manager has context before they look at the case. The Success Manager engagement is a parallel track — not a replacement for the formal escalation path.

---

## Example 3: Using Known Issues to Avoid a Redundant Case

**Context:** After a Spring release refresh, multiple users report that a standard Lightning component (the Activity Timeline) is showing blank for all contacts. The issue appeared on a Monday after a weekend maintenance window.

**Problem:** The admin is about to file a Sev3 case. If this is a known release bug, that case will be closed as a duplicate and delay resolution.

**Solution:**

```
Step 1 — Navigate to help.salesforce.com/s/issues

Step 2 — Search: "Activity Timeline blank Lightning contact"
  Result: Known Issue W-12345678 — "Activity Timeline component renders blank on
  Contact record after Spring '26 release under specific Lightning page configurations"
  Status: Known Issue, Fix in Progress — Expected in Summer '26

Step 3 — Click "This issue affects me"
  Register the org ID and add a comment describing the exact page layout and profile
  where the blank rendering occurs. This adds diagnostic data for the engineering team.

Step 4 — Subscribe to email notifications for the known issue.

Step 5 — Do NOT open a separate support case.
  Instead, communicate internally: "This is a known Salesforce platform bug (W-12345678).
  Fix is expected in Summer '26. Interim workaround: use the Related Activities list view
  on the page layout as a substitute."
```

**Why it works:** Every org that registers on a Known Issue increases the visible impact count, which signals prioritization to the engineering team. Filing a duplicate case does not help — it creates noise in the support queue and typically receives a response pointing back to the known issue article.

---

## Anti-Pattern: Opening a Sev1 for a Sandbox Issue

**What practitioners do:** A developer cannot deploy metadata to the full copy sandbox because the deployment is failing with a timeout error. The admin opens a Sev1 case because "the entire dev team is blocked."

**What goes wrong:** Salesforce's support team downgrades the case to Sev3 or Sev4 because production is not impacted. The downgrade adds hours of delay. The admin is frustrated because the response does not match the urgency they communicated internally.

**Correct approach:** File as Sev3 with clear description of the sandbox impact and timeline pressure. If there is a genuine production deadline threatened (e.g., a deployment window is in 4 hours and sandbox validation is blocking it), state that context explicitly in the description — but understand the case will still be classified based on current production impact, not future risk.
