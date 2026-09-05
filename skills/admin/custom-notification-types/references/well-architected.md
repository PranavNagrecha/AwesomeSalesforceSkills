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

Sources read as extracted text from the Summer '26 / v62 PDFs, with the
section each claim rests on:

- Metadata API Developer Guide — `CustomNotificationType`
  (`api_meta.txt:41769-41894`): file suffix `.notiftype` and the
  `notificationtypes` directory (L41783-41784); API 46.0+ (L41791);
  `customNotifTypeName` required, max 80 (L41799-41800); `description` max
  255 (L41802-41803); `desktop` and `mobile` required booleans
  (L41805-41811); `masterLabel` required (L41808); `slack` "Reserved for
  future use" (L41813); `actionGroups` (Beta) and the
  `NotificationActionType` values `NotificationApiAction` / `Share`
  (L41795-41864); the sample definition this skill's XML extends
  (L41877-41882); **no wildcard support in `package.xml`** (L41892-41894).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide — `NotificationTypeConfig`
  (`api_meta.txt:92197-92296`): suffix `.config`, folder
  `notificationTypeConfig`, API 48.0+ (L92203-92207); `notificationType`
  takes the type's API name (L92221-92225); `desktopEnabled` /
  `mobileEnabled` / `slackEnabled` (L92269-92274); `connectedAppName`
  required and to be harvested by retrieving (L92248-92251); the ECA/CA
  deploy caveat (L92258-92262) — supports the "delivery settings do not
  travel with the type" point in `references/metadata-examples.md` §2.
- Metadata API Developer Guide — `Flow` (`api_meta.txt`): the
  `customNotificationAction` `actionType` enum value, "available in API
  version 46.0 and later" (L68710), and the `actionCalls` /
  `inputParameters` element shape the Flow excerpt follows (L73211-73275).
  The *input parameter names* for this action are **not** in this guide —
  they live in the Actions Developer Guide, which is why
  `references/metadata-examples.md` §3 carries an UNVERIFIED marker and a
  retrieve-to-harvest instruction rather than an asserted schema.
- Apex Reference Guide — `Messaging.CustomNotification`
  (`apexrefguide.txt:166555-166944`): the target rule — either `targetId` or
  `targetPageRef`, both omitted throws, dummy Id `000000000000000AAA`
  (L166572-166575), and the pre-Winter '21 client-compatibility note
  (L166587-166589); the **Send Custom Notifications** user permission and
  user-mode execution (L166590-166594); the worked example this skill's Apex
  excerpt is adapted from, including `WITH USER_MODE` on the type lookup
  (L166600-166635); `send(Set<String>)` and the five valid recipient Id kinds
  with their active-user and team-enablement preconditions, capped at 500
  values (L166757-166781); `setTitle` max 250 and `setBody` max 750, both
  required (L166830, L166860-166861); the six-argument constructor
  (L166689-166690). Corrects the previously stated 64-character title cap.
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/apexref.pdf
- Object Reference for Salesforce — `CustomNotificationType`
  (`object_reference.txt:88293-88394`): sObject available API 47.0+
  (L88294); supported calls (L88301); `CustomNotifTypeName` `idLookup` /
  `Unique`, max 80, "isn't namespaced, so it can't be duplicated across
  installed packages" (L88306-88313); `DeveloperName` as the API name
  (L88340-88345); `Desktop` and `Mobile` both "Defaulted on create" with
  default `false` (L88332-88338, L88369-88386); `IsSlack` reserved
  (L88347-88352) — the grounding for the verification SOQL and for
  `references/gotchas.md` Gotcha 8.
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Salesforce Developer Limits and Allocations Quick Reference
  (`salesforce_app_limits_cheatsheet.txt`): "Maximum number of push
  notification method calls allowed per Apex transaction — 10" and "Maximum
  number of push notifications that can be sent in each push notification
  method call — 2,000" (L96-100); "An org can send up to 20,000 iOS and
  10,000 Android push notifications per hour", only deliverable
  notifications counting (L449-456); and the fail-open behaviour, "When an
  org's hourly push notification limit is met, any additional notifications
  are still created for in-app display and retrieval via REST API"
  (L465-466) — the grounding for `references/gotchas.md` Gotchas 6 and 7.
  The cheat sheet names the governed operation "push notification method
  calls" without naming `Messaging.CustomNotification.send()`, which is why
  Gotcha 6 carries an UNVERIFIED marker on that applicability.
