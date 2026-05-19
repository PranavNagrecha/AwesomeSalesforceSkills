# Well-Architected Notes — Custom Notification Types

## Relevant Pillars

Custom Notifications are interruption-channel infrastructure —
they pull users' attention away from whatever they were doing.
Three pillars carry the weight; the dominant one is Reliability
because a delivered-but-unseen notification, a silent send
failure, or a mistakenly-fired bulk send each degrades user trust
in the system in ways that are hard to recover from.

- **Reliability** — `send()` does not throw on invalid recipient
  Ids (deactivated users, wrong Id type) — it silently drops the
  notification. There is no platform-provided delivery receipt for
  Custom Notifications, no notification log table, and no
  retry-on-failure mechanism. Building reliable delivery requires
  Apex-side instrumentation (Platform Event markers, correlation
  Ids in the body) plus discipline around the 500-recipient cap.
- **Operational Excellence** — Notification types are
  org-configuration metadata, not data; they need to flow through
  the same CI/CD pipeline as Flows and Apex. Notification
  proliferation (every team creates their own) is a real
  governance problem at scale — without a catalog of which type
  fires when and to whom, the org accumulates dozens of types
  that no one can audit. The user-facing MasterLabel needs the
  same product-management care as a UI string.
- **Security** — Custom Notifications bypass sharing on the
  notification itself (the recipient sees the title, body, and the
  fact that something happened with the target record) but not on
  the target record click-through. A community user can receive a
  notification whose title leaks PII even if they can't open the
  underlying record. Treat notification bodies as if they were
  displayed in a public log.

## Architectural Tradeoffs

The defining choice is **which interruption channel** to use. The
four candidates each suit a different intent:

| Channel | When it fits | When it doesn't |
|---|---|---|
| **Custom Notification** (Flow or Apex) | Real-time interruption that should reach the user wherever they are — desktop bell, browser toast, mobile push. Best for escalations, approvals, SLA-at-risk warnings. | Audit-trail messages (no permanent record), external recipients (Salesforce users only), reply-able messages. |
| **Email Alert** (Workflow / Flow) | Audit-trail messages with a permanent record, recipients without Salesforce licenses, content that exceeds the 750-char body cap, replies expected. | Real-time alerts (email arrives minutes-to-hours late depending on spam filters), mobile-first audiences (push beats inbox), urgent escalations. |
| **Chatter @-mention** | Conversation-style notifications where the recipient is expected to read recent context and respond inline. Strong fit for collaboration flows. | High-volume automated notifications (Chatter feed becomes noise), users who disabled Chatter, mobile-first scenarios (Chatter mobile UX is heavier than push). |
| **Platform Event + LWC subscribe** | Targeted UI updates inside a specific Lightning page — e.g., refresh a related-list when a sibling record changes, show a toast only to users currently viewing a particular record. | Off-page alerts (the LWC has to be rendered to receive), cross-device delivery (the user must be in Salesforce when the event fires), persistent alerts. |

The handoff rules that work in practice:

- **Email AND Custom Notification together** for high-stakes events
  (Case escalations, approval requests). Email is the audit trail;
  the push is the attention nudge.
- **Custom Notification alone** for in-Salesforce real-time alerts
  that don't need a permanent record (territory realignment,
  daily-summary reminders).
- **Platform Event + LWC** when the alert is contextual to a
  specific page and the user is already there (e.g., the
  Opportunity record page shows "another user just edited this
  record" without leaving the page).

A second tradeoff: **Flow vs Apex** for the send. Flow's "Send
Custom Notification" core action is faster to build, visible in
Flow Builder for change review, and handles the common case
(notify one or a handful of recipients) cleanly. Apex's
`Messaging.CustomNotification` is necessary when the recipient
set is dynamically computed and exceeds Flow's practical handling
(hundreds of recipients), when the send must run inside a
Queueable or Batchable for governor budget reasons, or when
error handling needs to log to a custom logger. The handoff
rule: **switch to Apex when the audience computation is
non-trivial, when bulk volume consistently exceeds 100 recipients,
or when you need explicit try/catch around the send.**

## Anti-Patterns

1. **Hardcoding the Notification Type Id.** The `0ML...` Id is
   org-specific and changes on sandbox refresh. Always resolve at
   runtime via SOQL on `CustomNotificationType.DeveloperName`,
   ideally cached at class scope or in a Custom Metadata Type.
2. **Treating `send()` as exception-throwing.** Invalid recipients,
   deactivated users, and missing Connected App push credentials
   all cause silent drops, not exceptions. Build out-of-band
   delivery verification (Platform Event marker, correlation Id)
   for any notification you actually need to land.
3. **Email Alert as a substitute for real-time push.** Email
   arrives late, gets filtered, and cannot deep-link to a record
   on mobile. For escalations and approvals, fire both — email for
   audit, push for attention.
4. **Notification spam without a per-user opt-out path.** Custom
   Notifications can't be opted out per-type on desktop in the way
   email subscriptions can. Designing for "send to everyone, they
   can mute later" backfires because the mute path is per-app, not
   per-type. Design for restraint — make sure the notification is
   worth interrupting the recipient for.
5. **Deploying the Flow without deploying the
   `CustomNotificationType`.** The notification type is a metadata
   component, not data. Production deploys that move only the Flow
   leave the org with a dangling Notification Type Id reference.
   Always include `CustomNotificationType` members in `package.xml`
   or the Change Set.

## Official Sources Used

- Create and Send Custom Desktop or Mobile Notifications:
  https://help.salesforce.com/s/articleView?id=sf.notif_builder_custom.htm
- Send Custom Notification (Flow Core Action):
  https://developer.salesforce.com/docs/atlas.en-us.api_action.meta/api_action/actions_obj_custom_notification.htm
- CustomNotificationType (Object Reference):
  https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_customnotificationtype.htm
- Manage Your Notifications with Notification Builder:
  https://help.salesforce.com/s/articleView?id=sf.notif_builder.htm
- Standard Invocable Actions Introduction:
  https://developer.salesforce.com/docs/atlas.en-us.api_action.meta/api_action/actions_intro.htm
- CustomNotificationType (Metadata API):
  https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_customnotificationtype.htm
