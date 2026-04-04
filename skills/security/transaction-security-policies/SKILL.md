---
name: transaction-security-policies
description: "Transaction Security policy creation and configuration: condition builder, enhanced policies, enforcement actions (block, MFA, notification, end session), real-time monitoring mode, and policy troubleshooting. NOT for Event Monitoring log analysis or Shield Event Monitoring setup (use event-monitoring). NOT for Apex testing or debug-log analysis."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
triggers:
  - "how to block login from unknown location or unrecognized IP address"
  - "enforce MFA for specific reports access or sensitive data export"
  - "prevent data export by guest users or community users"
  - "set up a policy to block API access from suspicious connected apps"
  - "transaction security policy not triggering or not blocking as expected"
  - "create a condition-builder policy without writing Apex code"
  - "how to notify admin when a user exports more than N report rows"
tags:
  - transaction-security
  - shield
  - enforcement-actions
  - condition-builder
  - real-time-events
  - mfa
inputs:
  - "Salesforce org with Shield or Event Monitoring add-on license"
  - "Event type to enforce on (LoginEvent, ReportEvent, ApiEvent, etc.)"
  - "Conditions: user criteria, field values, thresholds, or profile/role targeting"
  - "Desired enforcement action: Block, MFA challenge, Notification, or End Session"
  - "List of notification recipients (policy owner, specific users, or event user)"
outputs:
  - "Transaction Security Policy configuration steps (Setup UI or Metadata API XML)"
  - "Condition builder filter expressions for the target event type"
  - "Enforcement action configuration including custom block message"
  - "Policy audit guidance (review active vs. monitor-only policies)"
  - "Troubleshooting checklist for policies that silently fail to fire"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Transaction Security Policies

This skill activates when a practitioner needs to create, configure, audit, or troubleshoot Transaction Security Policies that enforce automated actions — block, MFA challenge, notification, or session termination — in response to real-time user activity events. It covers both the modern Enhanced Condition Builder UI (Spring '21+, no Apex required for most policies) and the legacy Apex `PolicyCondition` interface. It does not cover Event Monitoring log download, RTEM streaming channel setup, or custom platform event publishing.

---

## Before Starting

Gather this context before working on anything in this domain:

- **License check**: Transaction Security Policies require Salesforce Shield or the Event Monitoring add-on. Without one of these, the Transaction Security Policies setup area and enforcement engine are unavailable.
- **Enhanced vs. legacy**: Spring '21+ introduced the Enhanced Condition Builder, which supports most policy use cases without writing Apex. Legacy Apex-based policies (implementing `TxnSecurity.PolicyCondition`) still work but require "Author Apex" permission and are harder to maintain. Confirm which approach the org uses before editing.
- **Event type support**: Not every Real-Time Event Monitoring (RTEM) event type supports Transaction Security Policies. Always verify the target event type is policy-supported before designing logic. Unsupported event types silently produce no enforcement.
- **Asynchronous execution**: Policy evaluation is asynchronous. There is a slight delay between the triggering user action and the enforcement response. "Block" actions will interrupt the user's request, but the block is not instantaneous at the database level — it fires after the platform's async evaluation completes.
- **Monitor mode**: Every new policy should be created in Monitor mode before switching to active enforcement. Monitor mode logs policy matches without taking action, allowing you to confirm the condition logic fires as intended.

---

## Core Concepts

### Mode 1 — Create a New Policy

Creating a new Transaction Security Policy involves five decisions: which event type to monitor, what conditions must match, what enforcement action to take, who gets notified, and what custom message to show on a block.

**Navigation:** Setup > Security > Transaction Security Policies > New

**Step-by-step:**

1. **Select the event type.** Common choices:
   - `LoginEvent` — login attempts (City, Country, LoginType, Status, UserId, SourceIp)
   - `ReportEvent` — report runs and exports (Name, Operation, RowsProcessed, Format)
   - `ApiEvent` — API calls (URI, Method, Platform, UserId)
   - `ConnectedApplication` — connected app OAuth access
   - `ListViewEvent` — list view access (EntityName, UserId)

2. **Build the condition.** Enhanced Condition Builder provides a drag-and-drop filter. Each condition row selects a field from the event, an operator, and a value. Combine rows with AND/OR logic.

   Example: Block logins from outside the US:
   - Field: `Country` | Operator: `Not Equal To` | Value: `US`

   Example: Alert when a report exports more than 2000 rows:
   - Field: `RowsProcessed` | Operator: `Greater Than` | Value: `2000`
   - Field: `Operation` | Operator: `Equals` | Value: `Export`

3. **Choose the enforcement action:**
   - **Block** — prevents the operation and displays a custom message to the user. The message is configurable in the policy record. Use this for hard stops.
   - **Multi-Factor Authentication** — challenges the user with an MFA step-up before allowing the action to proceed. Use this for sensitive operations where you want friction rather than a hard block.
   - **Notification** — sends an email or in-app notification to specified recipients. Does not block the action. Use this for monitoring scenarios or alerting on-call staff.
   - **End Session** — terminates the user's current session immediately. Use for severe threats (e.g., `SessionHijackingEvent` match).

4. **Set notification recipients** (if applicable): policy owner, specific named users, or the user who triggered the event.

5. **Set mode to Monitor first.** Validate the policy fires on expected events before switching to active enforcement.

**Metadata API representation** (`TransactionSecurityPolicy` metadata type):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<TransactionSecurityPolicy xmlns="http://soap.sforce.com/2006/04/metadata">
    <action>
        <blockMessage>This action is restricted by your organization's security policy.</blockMessage>
        <type>Block</type>
    </action>
    <active>true</active>
    <apexPolicy>false</apexPolicy>
    <description>Block logins originating outside the United States</description>
    <developerName>Block_Non_US_Logins</developerName>
    <eventName>LoginEvent</eventName>
    <eventType>Login</eventType>
    <executionUser>005xx000001SwEeAAK</executionUser>
    <masterLabel>Block Non-US Logins</masterLabel>
    <resourceName>LoginEvent</resourceName>
</TransactionSecurityPolicy>
```

Note: Condition Builder logic is stored in platform metadata and is not directly editable as raw XML in the same way as legacy Apex policies. For complex conditions, use the Setup UI and then retrieve via Metadata API.

### Mode 2 — Review and Audit Policies

When auditing existing policies in an org:

1. **List all active policies:** Setup > Security > Transaction Security Policies. Review the "Active" column. Policies in Monitor mode will not enforce — confirm this is intentional.

2. **Review each policy's condition logic:** Open each policy and inspect the Condition Builder filters. Verify the conditions match the intended threat pattern.

3. **Check execution user:** The policy must have an execution user configured. This user's permissions determine what context the policy evaluates in. The execution user should have the "Author Apex" permission if the policy uses an Apex policy class.

4. **Verify event type is policy-supported:** Cross-reference the event type against the confirmed policy-supported list (see Gotchas). Unsupported event types produce no enforcement.

5. **Check notification recipients:** Ensure notification recipients are current employees with valid user records. Deactivated users as recipients silently stop receiving alerts.

6. **SOQL audit query for deployed policies:**
```soql
SELECT Id, MasterLabel, DeveloperName, EventType, Active, Description,
       CreatedDate, LastModifiedDate, LastModifiedBy.Name
FROM TransactionSecurityPolicy
ORDER BY EventType, MasterLabel
```

### Mode 3 — Troubleshoot a Policy That Is Not Triggering

When a Transaction Security policy appears to be configured but never fires:

**Diagnosis checklist:**

1. **Is the policy set to Active (not Monitor)?** Monitor mode logs matches but takes no enforcement action. Check the "Active" flag — this is the most common miss.

2. **Is the event type policy-supported?** Verify the `eventType` field value against the confirmed supported list. `MobileEmailEvent`, `IdentityVerificationEvent`, and several others do not support policy enforcement regardless of configuration.

3. **Is there an execution user set?** A policy without an execution user will not evaluate. The execution user must be an active user with appropriate permissions.

4. **Does the condition logic actually match the test scenario?** The condition builder uses exact-match semantics. Check field name capitalization, operator selection, and value formatting. Some fields (like `Country`) require ISO 3166-1 alpha-2 country codes (`US`), not full country names (`United States`).

5. **Is there an Apex governor limit issue?** Legacy Apex-based policies (`PolicyCondition`) run in synchronous Apex context and count against transaction limits. If the Apex class has bugs or limit exceptions, the policy silently fails without surfacing an error to the user.

6. **Has sufficient time passed?** Policy evaluation is asynchronous. In high-traffic scenarios, very brief delays are normal. However, multi-minute delays or consistent non-triggering indicate a configuration problem, not a timing issue.

7. **Check the Transaction Security notification logs:** If the policy has Notification as one of its actions, verify whether notification emails or in-app alerts were generated. If they were, the policy is firing; the enforcement action (Block or MFA) may be misconfigured rather than the condition logic.

---

## Common Patterns

### Pattern: Block Logins from Unrecognized Locations

**When to use:** The org stores sensitive data and must prevent access from high-risk geographies or non-approved IP ranges. No existing IP restriction covers the use case (or IP ranges are too broad).

**How it works:**
1. Create a policy on `LoginEvent`.
2. Condition: `Country` Not Equal To the allowed country code (e.g., `US`). For multi-country allowlists, chain OR conditions for each permitted country code, then negate using a "None of the following" block-level operator.
3. Set enforcement to Block with a clear message explaining the restriction.
4. Add Notification to alert the security team when a block fires.
5. Run in Monitor mode for 1–2 weeks. Review the policy match log to confirm no legitimate users are being matched before enabling enforcement.

**Why not the alternative:** Login IP Ranges on profiles handle IP-based restrictions but not geography-based restrictions. Session settings and connected app policies do not offer country-level granularity. Transaction Security Policies are the native mechanism for geography-based login control.

### Pattern: MFA Challenge on Sensitive Report Exports

**When to use:** Finance or HR reports contain PII or financial data. The org cannot enforce MFA globally but wants a targeted step-up challenge when these specific reports are exported.

**How it works:**
1. Create a policy on `ReportEvent`.
2. Condition: `Name` Contains the report name (or exact equals for strict matching), AND `Operation` Equals `Export`.
3. Set enforcement to Multi-Factor Authentication.
4. Optionally add a Notification action to alert the data owner that an export was attempted.
5. Test in Monitor mode with a test export of the target report.

**Why not the alternative:** Profile-level MFA enforces MFA on every login, which may be too disruptive for the org. Permission-based report restrictions prevent access entirely, which may be inappropriate for authorized users who legitimately export data. The MFA enforcement action provides a middle path: allow access, but verify identity at the moment of export.

### Pattern: Notify on High-Volume API Access from a Connected App

**When to use:** A third-party connected app has broad API access. You want to alert the admin when it generates unusually high API call volumes, without blocking it outright.

**How it works:**
1. Create a policy on `ApiEvent`.
2. Condition: `ConnectedAppId` Equals the connected app's ID, AND `QueryRunTime` Greater Than an elevated threshold.
3. Alternatively, target based on `UserId` if the connected app uses a dedicated integration user.
4. Set enforcement to Notification only (no Block). Recipients: security admin user.
5. Leave in Monitor mode initially to calibrate — check how often the notification would have fired before enabling it.

**Why not the alternative:** Salesforce API usage limits apply at the org level; there is no native per-app alerting mechanism. Connected app policies can revoke access but cannot send targeted alerts based on usage patterns. Transaction Security Notification action fills this gap without requiring a custom scheduled job or external monitoring tool.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Hard-stop a login from a foreign country | Block action on LoginEvent with Country condition | Native block with custom message; no code required |
| Require identity verification before a report export | MFA action on ReportEvent | Step-up MFA, not a full block; authorized users can proceed |
| Alert security team when an admin exports bulk data | Notification action on ReportEvent with RowsProcessed > threshold | Non-blocking alert; actionable without disrupting workflow |
| Terminate a session flagged by ML threat detection | End Session action on SessionHijackingEvent | Immediate session invalidation for active threat |
| Test a new policy without user impact | Monitor mode | Logs matches for review; zero enforcement until switched to Active |
| Complex condition logic not expressible in Condition Builder | Legacy Apex PolicyCondition class | Apex allows arbitrary logic; requires Author Apex permission |
| Audit what policies exist and their current state | SOQL on TransactionSecurityPolicy + Setup UI review | Single query covers all policies; Setup UI shows active/monitor status |
| Policy fires in Monitor mode but not in Active mode | Check execution user, policy active flag, and event type support | Most common root cause of this discrepancy |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Org has Shield or Event Monitoring add-on license; Transaction Security Policies are available in Setup
- [ ] Event type selected is confirmed policy-supported (not in the unsupported list: `MobileEmailEvent`, `IdentityVerificationEvent`, `IdentityProviderEvent`, `MobileScreenshotEvent`, etc.)
- [ ] Execution user is set on every policy and is an active user record
- [ ] New policies started in Monitor mode; match log reviewed before switching to Active enforcement
- [ ] Condition field values use correct formats (ISO country codes, exact field name capitalization, correct operator)
- [ ] Block message is human-readable and explains the restriction to the affected user
- [ ] Notification recipients are active users with valid email addresses
- [ ] Legacy Apex-based policies (if any) compile without errors; execution user has "Author Apex" permission
- [ ] Policies with End Session action tested carefully — session termination is immediate and non-reversible
- [ ] SOQL audit of `TransactionSecurityPolicy` run to inventory all policies and their active state

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Monitor mode policies never enforce — silently** — A policy in Monitor mode logs every match but takes zero enforcement action. If a practitioner creates a policy and sets it to Monitor expecting to see blocks or MFA prompts, nothing will happen. The only output is a log entry. Switch to Active to enable enforcement. This is the single most common root cause of "my policy isn't working."

2. **Not all RTEM event types support policy enforcement** — Event types including `MobileEmailEvent`, `MobileScreenshotEvent`, `IdentityVerificationEvent`, `IdentityProviderEvent`, and `MobileEnforcedPolicyEvent` explicitly do not support Transaction Security Policy enforcement. A policy created on these event types will never fire — there is no error or warning in the UI. Always check the "Can Be Used in a Transaction Security Policy?" column in the Salesforce Object Reference for the target event type before designing the policy.

3. **Country field uses ISO codes, not full country names** — The `Country` field on `LoginEvent` stores ISO 3166-1 alpha-2 two-letter country codes (`US`, `GB`, `DE`), not full country names. A condition that filters on `Country` Equals `United States` will never match. This is a silent failure — the condition evaluates but never finds a match.

4. **Execution user permissions affect policy evaluation context** — The execution user on each policy is not just an audit field — it defines the security context in which the policy logic runs. For legacy Apex-based policies, if the execution user lacks the "Author Apex" permission, the policy will fail silently. For Enhanced policies, the execution user must be active. Deactivated execution users cause the entire policy to stop evaluating without any system alert.

5. **Notification recipients must be active users — deactivation is silent** — If a user set as a notification recipient is later deactivated, the notification silently stops sending. No error is thrown; no fallback recipient is used. Regularly audit notification recipients, especially after org user offboarding, to avoid creating invisible alert gaps.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Policy configuration steps | Step-by-step Setup UI or Metadata API instructions for the specific event type and enforcement action |
| Condition builder expressions | Field, operator, and value combinations for the target policy use case |
| TransactionSecurityPolicy XML | Metadata API deployment-ready XML for the policy record |
| Policy audit SOQL | Query against `TransactionSecurityPolicy` to inventory all active and monitor-mode policies |
| Troubleshooting checklist | Ordered diagnosis steps for policies that silently fail to trigger |

---

## Related Skills

- event-monitoring — for Shield Event Monitoring log download, RTEM channel setup, and EventLogFile-based audit (the visibility layer that Transaction Security Policies enforce upon)
- security-health-check — for org-wide security posture review; Transaction Security Policies are one check category
- apex-security-patterns — for legacy Apex `PolicyCondition` implementation patterns and secure Apex design
