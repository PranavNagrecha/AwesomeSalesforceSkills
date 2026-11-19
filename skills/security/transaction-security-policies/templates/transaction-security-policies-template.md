# Transaction Security Policies — Work Template

Use this template when designing, reviewing, or troubleshooting a Transaction Security Policy.
Fill in each section before implementing or recommending changes.

---

## Scope

**Skill:** `transaction-security-policies`

**Request summary:** (Describe what the user is trying to achieve — e.g., "block logins from outside the US", "MFA on report export", "alert admin on excessive API calls")

---

## Context Gathered

Answer these before proceeding:

- **License confirmed?** Shield / Event Monitoring add-on present: [ ] Yes [ ] No [ ] Unknown
- **Admin holds Modify Transaction Security Policy + Customize Application?** [ ] Yes [ ] No — Customize Application alone is read-only [ ] Unknown
- **Existing `ReportEvent` policies inventoried (including any Salesforce-deployed default)?** [ ] Yes [ ] No [ ] N/A — not a ReportEvent policy
- **Event type to target:** ______________________________
- **Event type is policy-supported?** [ ] Yes [ ] No [ ] Unverified (check Platform Events Developer Guide)
- **Enforcement approach:** [ ] Block [ ] MFA [ ] Notification [ ] End Session [ ] Multiple
- **Handler ready?** Flow (Condition Builder) or Apex class exists: [ ] Yes [ ] No [ ] TBD (no execution user: Legacy Transaction Security only)
- **Monitor mode first?** [ ] Yes — will validate before activating [ ] No — reason: _______________

---

## Policy Design

### Event Type

Event type selected: ______________________________

Is it in the confirmed policy-supported list? [ ] Yes [ ] No

### Condition Logic

| # | Field | Operator | Value | Combine with |
|---|-------|----------|-------|--------------|
| 1 | | | | AND / OR |
| 2 | | | | AND / OR |
| 3 | | | | — |

Field value format verified? (e.g., ISO country codes for Country field): [ ] Yes [ ] No

### Enforcement Action(s)

- [ ] **Block** — Block message text: _______________________________________________
- [ ] **Multi-Factor Authentication** — No additional config required
- [ ] **Notification** — Recipients: ________________________________________________
- [ ] **End Session** — (use only for confirmed active threat scenarios)

### Notification Recipients

| Recipient | User Record Active? | Role/Purpose |
|-----------|---------------------|--------------|
| | [ ] Yes [ ] No | |
| | [ ] Yes [ ] No | |

---

## Metadata API Reference

Skeleton `TransactionSecurityPolicy` XML for version control:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<TransactionSecurityPolicy xmlns="http://soap.sforce.com/2006/04/metadata">
    <action>
        <block><!-- true to block the operation --></block>
        <twoFactorAuthentication><!-- true to require MFA --></twoFactorAuthentication>
        <notifications>
            <inApp><!-- true | false --></inApp>
            <sendEmail><!-- true | false --></sendEmail>
            <user><!-- username of the recipient --></user>
        </notifications>
    </action>
    <active><!-- true (enforcement) or false (Monitor mode) --></active>
    <apexClass><!-- required when type is CustomApexPolicy --></apexClass>
    <blockMessage><!-- only for ApiEvent, ListViewEvent, BulkApiResultEventStore, ReportEvent; max 1000 chars --></blockMessage>
    <description><!-- Human-readable description of what this policy does --></description>
    <developerName><!-- API name, no spaces --></developerName>
    <eventName><!-- Real-Time Event Monitoring event, e.g., LoginEvent, ReportEvent --></eventName>
    <flow><!-- required when type is CustomConditionBuilderPolicy: ID of the Flow --></flow>
    <masterLabel><!-- Display name in Setup UI --></masterLabel>
    <type><!-- CustomApexPolicy | CustomConditionBuilderPolicy --></type>
    <!-- eventType, resourceName, executionUser: Legacy Transaction Security only (retired Summer '20); do not set -->
</TransactionSecurityPolicy>
```

---

## Monitor Mode Validation Plan

Before activating enforcement, confirm the following in Monitor mode:

- [ ] Policy match log shows entries for the intended triggering scenario
- [ ] No unexpected users or scenarios are appearing in the match log
- [ ] Match frequency is as expected (not too broad, not zero matches when expected)
- [ ] Monitor period: _____________ (minimum 3–5 business days recommended for login policies)
- [ ] Sign-off from: _____________

---

## Activation Checklist

Complete before switching the policy to Active:

- [ ] Event type verified as policy-supported
- [ ] Handler (Flow or Apex class) exists and is valid; no legacy-only fields set
- [ ] Condition field values use correct formats (ISO codes, exact strings, correct operators)
- [ ] Block message is human-readable and includes contact/escalation instructions
- [ ] Notification recipients are all active users
- [ ] Monitor mode log reviewed and validated
- [ ] Metadata deployed to sandbox and tested with test user account
- [ ] Production deployment approved and change-managed

---

## Troubleshooting Notes

If the policy does not appear to fire after activation, check in order:

1. Active flag is `true` (not Monitor mode): [ ] Confirmed
2. Event type is policy-supported: [ ] Confirmed
3. Handler (Flow or Apex class) is valid: [ ] Confirmed
4. Condition field values match actual event field values: [ ] Confirmed
5. For Apex policies: PolicyCondition class compiles without errors: [ ] Confirmed / [ ] N/A
6. Time elapsed since activation (async delay — allow a few minutes): _______________
7. Notification action logs (if present): [ ] Checked — notifications fired / did not fire

---

## Notes

(Record any deviations from the standard pattern, org-specific constraints, or decisions made during implementation.)
