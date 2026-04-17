# Examples — Agent Deployment Checklist

## Example 1: Rollback rehearsal

**Context:** Agent v2 activation.

**Problem:** Rollback procedure was never tested; in the incident, CMDT flip caused cascading Flow failure.

**Solution:**

Staging rehearsal: flip v2 on, observe one live conversation, flip back to v1, confirm conversation continuity. Record duration, observed impact, and any side effects in the activation record.

**Why it works:** Rehearsal converts 'we have a rollback' (belief) into 'rollback takes 90 seconds with X side effect' (fact).


---

## Example 2: Stakeholder sign-off record

**Context:** Quarterly audit.

**Problem:** Who approved v2? Only a Slack message exists.

**Solution:**

`Agent_Activation__c` record with: Agent_Version__c, Business_Owner_Approval__c (User lookup), Security_Approval__c, SRE_Approval__c, Approved_At__c. All three must be populated before the flow to activate can complete.

**Why it works:** Auditable, queryable, and immutable — unlike chat history.

