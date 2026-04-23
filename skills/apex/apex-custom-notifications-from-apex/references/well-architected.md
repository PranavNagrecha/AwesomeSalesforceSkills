# Well-Architected Notes — Apex Custom Notifications From Apex

## Relevant Pillars

### Reliability

Custom Notifications fail silently when Ids are stale, users are deactivated, or targets are invalid. Reliable code validates inputs before send, handles exceptions without affecting the enclosing DML, and does not couple notification delivery to the success of business logic.

Tag findings as Reliability when:
- sync sends from a trigger can abort the DML
- recipients are not filtered for active users
- no retry story exists for transient notification send failures
- the Notification Type Id is hardcoded

### Security

Custom Notifications can expose sensitive text (PII, account numbers, internal reasoning) to every user in the recipient set. If the recipient list is misconfigured, private data leaks.

Tag findings as Security when:
- recipient sets contain Ids the running user wouldn't normally share with
- body text includes unredacted PII
- the notification target is a record the recipient lacks access to (the click lands on "Insufficient Privileges")

### Operational Excellence

The platform does not retain notification history. Operators need visibility into "did we send it?" for compliance or incident triage. Build a lightweight `Notification_Log__c` to capture sender, target, recipients, and outcome.

Tag findings as OpEx when:
- no log exists for sent notifications
- failures are only logged to debug logs (which rotate)
- there is no mechanism to re-drive missed notifications

## Architectural Tradeoffs

- **Custom Notification vs Chatter Feed Post:** Custom Notification is ephemeral and user-targeted; Chatter post is durable and collaborative. Pick Chatter when you need audit trail and threaded discussion.
- **Custom Notification vs Email:** Custom Notification reaches users inside Salesforce; Email reaches anyone. Use email for external parties, Custom Notification for logged-in Salesforce users.
- **Sync vs Queueable Send:** Sync is simple but couples DML to notification success. Queueable decouples and adds retry potential.

## Anti-Patterns

1. **Hardcoded Notification Type Id** — Ids differ across orgs; deploy-time brittleness. Always resolve by DeveloperName.
2. **Sync send from a trigger** — a notification platform hiccup aborts the user's save. Delegate to Queueable.
3. **Broadcasting PII without sharing check** — sending customer detail to a queue whose members include partner users. Filter recipients against the target record's sharing model first.

## Official Sources Used

- Apex Reference — Messaging.CustomNotification: https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Messaging_CustomNotification.htm
- Salesforce Help — Create and Use Custom Notification Types: https://help.salesforce.com/s/articleView?id=sf.custom_notifications_create.htm
- Apex Developer Guide — Working with Queueable: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_queueing_jobs.htm
- Apex Governor Limits: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Salesforce Well-Architected — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
