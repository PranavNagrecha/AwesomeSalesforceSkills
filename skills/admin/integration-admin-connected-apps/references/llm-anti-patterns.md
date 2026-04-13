# LLM Anti-Patterns — Integration Admin: Connected Apps

Common mistakes AI coding assistants make when advising on Connected App configuration.

## Anti-Pattern 1: Recommending Pre-Authorized Mode Without Profile/Permission Set Assignment

**What the LLM generates:** "Set the Permitted Users option to 'Admin approved users are pre-authorized' to restrict the connected app to specific users. This will prevent unauthorized OAuth access."

**Why it happens:** LLMs describe the pre-authorized setting correctly but omit the mandatory follow-up step of assigning the connected app to a Profile or Permission Set, which is documented separately in Salesforce help.

**Correct pattern:**

```
After setting "Admin approved users are pre-authorized":
1. Go to: Setup > Users > Profiles > [Integration User Profile]
2. Find "Connected App Access" section
3. Enable the checkbox for the connected app
4. Save

OR via Permission Set:
1. Go to: Setup > Permission Sets > [Integration Permission Set]
2. Click "Assigned Apps"
3. Enable the connected app

Without this assignment, ALL authentication attempts fail.
```

**Detection hint:** Any recommendation to set "Admin approved users are pre-authorized" without immediately following with the Profile or Permission Set assignment steps.

---

## Anti-Pattern 2: Recommending CSP Trusted Sites for Connected App Callout Issues

**What the LLM generates:** "Add your integration endpoint to CSP Trusted Sites to allow the connected app to call the external service."

**Why it happens:** LLMs conflate browser-side CSP (which governs what resources Lightning components can load) with server-side callout restrictions (which are governed by Remote Site Settings). Connected apps and their OAuth flows involve server-side calls, not browser-side CSP.

**Correct pattern:**

```
Connected App OAuth flows are server-side — governed by Remote Site Settings, not CSP.

For Apex callouts from Salesforce to an external system:
→ Add the endpoint URL to Remote Site Settings (Setup > Security > Remote Site Settings)

For Lightning components loading external resources in the browser:
→ Add to CSP Trusted Sites (Setup > CSP Trusted Sites)

CSP Trusted Sites have NO effect on Apex callouts or OAuth server-to-server flows.
```

**Detection hint:** Any suggestion to add a connected app endpoint to CSP Trusted Sites to fix an integration or callout issue.

---

## Anti-Pattern 3: Using Login History as the Source for OAuth Token Monitoring

**What the LLM generates:** "To monitor connected app usage, check Setup > Security > Login History and filter by the integration user."

**Why it happens:** Login History is the most visible audit tool in Salesforce Setup. LLMs recommend it for any monitoring question. It does not capture OAuth token-level events.

**Correct pattern:**

```
Login History: Shows login events (username, IP, login type). 
NOT sufficient for OAuth token monitoring.

For OAuth token-level monitoring:
- Requires Event Monitoring add-on
- Query EventLogFile via REST API:
  GET /services/data/vXX.0/query?q=SELECT+Id+FROM+EventLogFile
  +WHERE+EventType='ConnectedAppOAuth'+AND+LogDate=TODAY
- Download the CSV log and review TOKEN_TYPE, GRANT_TYPE, IP_ADDRESS columns
```

**Detection hint:** Any monitoring recommendation that only mentions Login History for connected app or OAuth investigation.

---

## Anti-Pattern 4: Recommending System Administrator Profile for Integration Users

**What the LLM generates:** "For simplicity, assign the System Administrator profile to your integration user to ensure it has all necessary permissions."

**Why it happens:** System Administrator profile is the universal "all access" shortcut in Salesforce. LLMs recommend it to resolve permission errors without considering the principle of least privilege.

**Correct pattern:**

```
NEVER assign System Administrator profile to integration users.
Reasons:
- Bypasses API-only flag (grants interactive login capability)
- Violates least privilege — gives access to all data and configuration
- Creates security risk if token is compromised

Correct approach:
1. Use Salesforce Integration user license
2. Pair with "Minimum Access - API Only Integrations" profile (non-editable, enforces API-only)
3. Grant specific object/field access via targeted Permission Sets
4. Assign connected app to the Permission Set
```

**Detection hint:** Any recommendation to assign System Administrator profile or a "cloned admin" profile to an integration user.

---

## Anti-Pattern 5: Ignoring the September 2025 Uninstalled App Blocking Policy

**What the LLM generates:** "The integration worked before the app was uninstalled — the tokens should still be valid and the integration should continue working."

**Why it happens:** Historically, uninstalled connected app tokens did continue to work. The September 2025 policy change (blocking uninstalled apps by default) post-dates much of the training data.

**Correct pattern:**

```
As of September 2025: Uninstalled connected apps are blocked by default.

If an integration is failing with OAuth errors after an app was uninstalled:
1. Go to: Setup > Apps > Connected Apps > OAuth Usage
2. Identify the uninstalled app still in use
3. Either: Re-authorize the app (re-install or re-register)
         Or: Migrate the integration to a new connected app
4. Run quarterly audits to catch orphaned integrations before they fail
```

**Detection hint:** Any claim that uninstalled connected app tokens remain valid without qualifying with the current Salesforce policy.
