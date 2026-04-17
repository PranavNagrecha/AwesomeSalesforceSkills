# Agentforce In Slack — Configuration Checklist Template

Use this template to plan and track Slack-specific Agentforce configuration for an agent that is already deployed to a Slack workspace. Complete each section before and after configuration work.

Replace all `[PLACEHOLDER]` values with real values for your deployment.

---

## Pre-Flight Checks

Complete all pre-flight checks before making any configuration changes. Configuration done before the baseline is confirmed is likely to be repeated.

| Check | Status | Notes |
|---|---|---|
| Slack deployment flow complete in Setup | [ ] Pass / [ ] Fail | Navigate to Setup > Agentforce > Slack Deployment and confirm workspace is connected |
| Agent is in Active state | [ ] Pass / [ ] Fail | Setup > Agentforce Agents > [AGENT NAME] — status must be Active, not Draft or Inactive |
| At least one Slack user can message the agent successfully | [ ] Pass / [ ] Fail | Basic message flow confirms the base deployment is healthy before adding Slack-native actions |
| Slack workspace plan confirmed | [ ] Free / [ ] Pro / [ ] Business+ / [ ] Enterprise Grid | Required to determine canvas capability. Free plan cannot use Create Canvas. |
| Einstein Trust Layer reviewed for channel audience | [ ] Pass / [ ] Needs Review | Confirm ZDR and masking policies cover Slack action traffic (canvas content, DMs, search results) |

**Pre-flight verdict:** [ ] Ready to proceed / [ ] Blocking issues — resolve before continuing

Blocking issues (if any):
- [DESCRIBE ANY BLOCKING ISSUES]

---

## General Slack Actions Topic Setup

The General Slack Actions topic must be explicitly added to the agent in Agent Builder after Slack deployment. It is never added automatically. This single step unlocks all four Slack-native actions.

### Step-By-Step

| Step | Action | Status |
|---|---|---|
| 1 | Open Setup > Agentforce Agents > [AGENT NAME] > Agent Builder | [ ] Done |
| 2 | Navigate to Topics tab | [ ] Done |
| 3 | Click Add Topic | [ ] Done |
| 4 | Search for "General Slack Actions" in the topic picker (standard/managed topic, not custom) | [ ] Done |
| 5 | Select "General Slack Actions" and click Add | [ ] Done |
| 6 | Save the agent | [ ] Done |
| 7 | If agent transitions out of Active state, click Activate | [ ] Done |

### Actions Unlocked By General Slack Actions Topic

| Action Name | Available After Topic Added | Requires Paid Plan |
|---|---|---|
| Create Canvas | Yes | YES — unavailable on Free plan |
| Search Message History | Yes | No |
| Send DM | Yes | No |
| Look Up User | Yes | No |

**Post-topic verification:** Test at least one action in Slack. Suggested test:

```
User message to agent: Look up [TEST_SLACK_USERNAME] in Slack.
Expected: Agent returns the user's Slack profile details.
```

Result: [ ] Pass / [ ] Fail

If Look Up User fails, check: (a) General Slack Actions topic is shown in Active Topics list for the agent, and (b) agent is in Active state.

---

## Public vs. Private Action Matrix

Complete this table for every action registered in the agent. Use it to confirm each action has the correct scope before enabling the agent for users.

| Action Name | Action Type | Accesses User-Specific Data? | Recommended Scope | Configured Scope | Identity Mapping Required? |
|---|---|---|---|---|---|
| [ACTION_1] | Apex Invocable / Flow / External | [ ] Yes / [ ] No | Public / Private | [ ] Public / [ ] Private | [ ] Yes / [ ] No |
| [ACTION_2] | Apex Invocable / Flow / External | [ ] Yes / [ ] No | Public / Private | [ ] Public / [ ] Private | [ ] Yes / [ ] No |
| [ACTION_3] | Apex Invocable / Flow / External | [ ] Yes / [ ] No | Public / Private | [ ] Public / [ ] Private | [ ] Yes / [ ] No |
| Create Canvas (General Slack Actions) | Managed Slack Action | [ ] Yes / [ ] No | Public | Public | No |
| Search Message History (General Slack Actions) | Managed Slack Action | [ ] Yes / [ ] No | Public | Public | No |
| Send DM (General Slack Actions) | Managed Slack Action | [ ] Yes / [ ] No | Public | Public | No |
| Look Up User (General Slack Actions) | Managed Slack Action | [ ] Yes / [ ] No | Public | Public | No |

**Scope decision rule:**
- If the action queries or modifies records owned by or specific to the invoking user → **Private**
- If the action queries shared, non-sensitive, org-wide content → **Public** is acceptable
- When in doubt, prefer **Private** — it is always more secure; the only cost is identity mapping overhead

---

## Identity Mapping Configuration

Required for any action designated as Private scope. Skip this section if all actions are Public scope.

### User Population

| Field | Value |
|---|---|
| Total Salesforce users who will use private actions | [COUNT] |
| Users already mapped (from previous environment or prior setup) | [COUNT] |
| Users needing new mappings | [COUNT] |
| Provisioning method chosen | [ ] Self-service OAuth (user-initiated) / [ ] Admin bulk import |

### Self-Service OAuth Path (User-Initiated)

When an unmapped user triggers a private action, the agent returns a connection prompt. The user clicks the link and authenticates with Salesforce. The mapping is created automatically.

Action required: communicate to all affected Slack users that they will need to complete a one-time connection when they first trigger a private action. Suggested communication:

```
When you first ask [AGENT NAME] for information specific to your Salesforce account
(such as your cases, opportunities, or tasks), the agent will prompt you to connect
your Salesforce account. Click the link in the agent's response and follow the login
steps. This is a one-time step and only takes about 30 seconds.
```

### Admin Bulk Import Path

Use this path to pre-provision mappings before users interact with the agent, avoiding the connection prompt experience entirely.

**Step 1 — Collect Salesforce User IDs:**
```sql
SELECT Id, Name, Email FROM User WHERE IsActive = true AND Profile.Name != 'Chatter External User'
```

**Step 2 — Collect Slack User IDs:**

Use the Slack API method `users.lookupByEmail` with the `users:read.email` OAuth scope:
```
GET https://slack.com/api/users.lookupByEmail?email={user_email}
Header: Authorization: Bearer {slack_oauth_token}
Response: user.id contains the Slack User ID (format: U01XXXXXXXX)
```

**Step 3 — Format the mapping CSV:**
```csv
salesforceUserId,slackUserId
0051a000000ABC1,U01ABCDEF12
0051a000000ABC2,U01GHIJKL34
0051a000000ABC3,U01MNOPQR56
```

**Step 4 — Import via Salesforce Setup:**
Navigate to Setup > Slack for Salesforce > User Mappings > Bulk Import. Upload the CSV. Confirm import success.

**Step 5 — Verify:**
Navigate to Setup > Slack for Salesforce > User Mappings. Sort by connection status. Confirm all target users show as "Connected".

**Mapping verification result:** [ ] All target users mapped / [ ] [COUNT] users still unmapped

### Production Go-Live Note

Identity mappings are data records, not metadata. They WILL NOT be transferred by any metadata deployment (change set, SFDX push, Copado, or otherwise). Add this step explicitly to the production go-live runbook:

- [ ] Identity mapping re-provisioning step added to production go-live runbook
- [ ] At least one production user mapping tested before go-live is marked complete

---

## Canvas Plan Validation And Fallback Design

Complete this section only if Create Canvas is used in agent topics or instructions.

| Field | Value |
|---|---|
| Slack workspace plan | [ ] Free / [ ] Pro / [ ] Business+ / [ ] Enterprise Grid |
| Canvas creation supported | [ ] Yes / [ ] No (Free plan) |
| Fallback designed for canvas failure | [ ] Yes / [ ] Not needed |

### Fallback Topic Instruction (if canvas creation is unavailable or may fail)

Add this instruction to any topic that uses Create Canvas. Adjust the wording to match the agent's persona and tone:

```
If canvas creation is unavailable or returns an error, respond with a formatted
plain-text summary instead. Begin the plain-text summary with the section heading
"Summary" and use bullet points for each item. Do not surface a technical error
message to the user.
```

**Canvas plan validation confirmed:** [ ] Yes / [ ] Not applicable (no canvas actions configured)

---

## End-To-End Test Plan

Complete all test scenarios in sandbox before enabling the configuration for production users.

### Test Scenario 1: General Slack Actions Topic — Look Up User

| Field | Value |
|---|---|
| Test input | Ask the agent: "Look up [TEST_SLACK_USER] in Slack" |
| Expected behavior | Agent returns the user's Slack profile details (display name, email, or available profile fields) |
| Actual behavior | [FILL IN AFTER TEST] |
| Result | [ ] Pass / [ ] Fail |

### Test Scenario 2: Private Action — Mapped User

| Field | Value |
|---|---|
| Test user | [MAPPED_SLACK_USER] — confirmed mapped in Setup > Slack for Salesforce > User Mappings |
| Test input | Ask the agent to retrieve a private-action result specific to that user |
| Expected behavior | Agent returns data owned by or specific to the invoking Slack user's Salesforce account |
| Actual behavior | [FILL IN AFTER TEST] |
| Trust Layer check | Confirm in Trust Layer logs that the action invocation is stamped with [MAPPED_USER_SALESFORCE_ID], not the integration user's ID |
| Result | [ ] Pass / [ ] Fail |

### Test Scenario 3: Private Action — Unmapped User

| Field | Value |
|---|---|
| Test user | [UNMAPPED_SLACK_USER] — confirmed NOT mapped in Setup > Slack for Salesforce > User Mappings |
| Test input | Ask the agent to retrieve a private-action result |
| Expected behavior | Agent returns a clear "please connect your Salesforce account" message, not a generic error or the integration user's data |
| Actual behavior | [FILL IN AFTER TEST] |
| Result | [ ] Pass / [ ] Fail |

### Test Scenario 4: Canvas Creation (Paid Plan Only)

Skip if workspace is on Free plan.

| Field | Value |
|---|---|
| Test input | Ask the agent to create a canvas (e.g., "Create a canvas summarizing the top 3 open cases for [ACCOUNT_NAME]") |
| Expected behavior | Agent creates a Slack canvas and returns a link to it |
| Actual behavior | [FILL IN AFTER TEST] |
| Trust Layer check | Confirm canvas content is visible in Trust Layer logs |
| Result | [ ] Pass / [ ] Fail / [ ] Skipped (Free plan) |

### Test Scenario 5: Send DM

| Field | Value |
|---|---|
| Test input | Ask the agent to send a DM to [TEST_SLACK_USER] |
| Expected behavior | [TEST_SLACK_USER] receives a direct message from the agent |
| Actual behavior | [FILL IN AFTER TEST] |
| Result | [ ] Pass / [ ] Fail |

**If Send DM fails:** Check that `im:write` OAuth scope is granted to the Salesforce-managed Slack app. Navigate to api.slack.com/apps, find the Salesforce-managed app, and check OAuth Scopes under OAuth & Permissions. If `im:write` is missing, the Slack workspace admin must re-authorize the app through the Salesforce Setup Slack Deployment flow.

---

## Configuration Sign-Off

| Item | Verified By | Date |
|---|---|---|
| General Slack Actions topic added and agent is Active | [NAME] | [DATE] |
| Public/private scope confirmed for all actions | [NAME] | [DATE] |
| Identity mappings provisioned for all private-action users | [NAME] | [DATE] |
| Canvas plan validation complete (or not applicable) | [NAME] | [DATE] |
| All test scenarios passed in sandbox | [NAME] | [DATE] |
| Identity mapping re-provisioning step added to production runbook | [NAME] | [DATE] |
| Trust Layer logs reviewed for Slack action traffic | [NAME] | [DATE] |

**Ready for production promotion:** [ ] Yes / [ ] No — outstanding items: [LIST ANY OUTSTANDING ITEMS]
