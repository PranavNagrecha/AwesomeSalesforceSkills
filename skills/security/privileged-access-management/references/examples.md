# Examples — Privileged Access Management (PAM)

## Example 1: Elevated PSG with 4-hour expiration

**Context:** ServiceNow ticket approves admin request.

**Problem:** Previous flow granted Modify All Data permanently.

**Solution:**

```apex
PermissionSetGroup psg = [SELECT Id FROM PermissionSetGroup WHERE DeveloperName='PAM_Elevated' LIMIT 1];
insert new PermissionSetAssignment(
    AssigneeId = requester.Id,
    PermissionSetGroupId = psg.Id,
    ExpirationDate = System.now().addHours(4)
);
```

**Why it works:** Platform auto-revokes at expiration; no custom scheduler.


---

## Example 2: Break-glass alert

**Context:** Break-glass user logs in.

**Problem:** Security team not notified in real time.

**Solution:**

Enable Transaction Security Policy on Login with condition User.Id IN ('<break-glass-1>','<break-glass-2>'). Policy action: Notify Slack via webhook action.

**Why it works:** Zero-latency detection of the two highest-risk identities.

