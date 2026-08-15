# Well-Architected Notes — Custom Notification Type Design

## Relevant Pillars

- **User Experience** — Primary pillar, and the one the platform gives you no
  help with. Every other Salesforce capability degrades visibly when misused; a
  misdesigned notification degrades *the channel*, silently, for everybody else.
  A user who mutes the bell because of one noisy type has also muted the
  escalation notification that would have mattered. Attention is a shared org
  resource with no quota, no dashboard, and no error when it is exhausted, which
  is why the design discipline has to substitute for the missing guardrail.

- **Operational Excellence** — Four independent delivery gates (the type's
  channel flags, the org's `NotificationTypeConfig` including its per-connected-app
  `appSettings`, the user's own preferences, and the device or browser
  permission) all fail closed and none of them raises an error. That makes
  "verified delivered on a real device" a release step rather than a nicety, and
  it makes the type-plus-config pairing a deployment invariant. A registry of
  what exists, who owns it, and when it is next reviewed is the only thing that
  stops the set of types growing monotonically.

- **Security** — A notification body travels outside the record's sharing model.
  The title and body are composed by the sender and delivered to whoever the
  recipient expression resolved to, so a body that embeds a field value hands
  that value to people whose access to the record was never checked. Deep links
  are safe here — the recipient still hits the record's access check on arrival —
  but the 750 characters you put in the body are not. Design bodies as pointers,
  not summaries.

- **Reliability** — Delivery is best-effort and unacknowledged. There is no
  retry, no read receipt the org can query, and no failure signal to alert on. A
  notification is therefore never an acceptable sole mechanism for anything with
  a consequence: it is an accelerator on top of a queue, a task, an approval
  record, or an SLA milestone that would still be discoverable if every
  notification in the org vanished.

## Architectural Trade-offs

**Per-event notification vs digest.** Per-event is what the requirement usually
says and is right when the recipient's response time is measured in minutes. It
scales badly by construction: a routing run that assigns fifty leads sends fifty
notifications to one person, and the fiftieth is worth less than nothing because
it is why the first forty-nine get muted. A digest converts N interruptions into
one and degrades gracefully at any volume, but it is not real-time and it moves
the "which one do I work first" decision from the notification to a list view.
Choose on the recipient's actual required response time — not on which is easier
to build, which is always per-event.

**Group and queue IDs vs enumerated user IDs.** Passing a `GroupId` or `QueueId`
makes membership an administrable thing with an owner, keeps the design inside a
single value of the 500-value cap, and survives leavers and role changes. It also
gives up precision: you cannot notify "the three people on this account" without
a group that means exactly that, and creating a group per audience has its own
sprawl cost. Enumerated user IDs are precise on the day they ship and wrong
within a quarter. Prefer memberships, and accept a small number of purpose-built
groups as the price.

**Desktop-only vs desktop plus mobile push.** The bell is persistent, cheap to
ignore, and reviewable later — the recipient consumes it on their own schedule.
Mobile push interrupts a person who may be driving, in a meeting, or off shift,
and buys a response time that is genuinely shorter. The asymmetry is that the
cost of an unnecessary push is not paid on the notification that was
unnecessary; it is paid later, on the one that mattered, by a recipient who has
since disabled push. Enable mobile when minutes matter and be able to say why.

**Actionable notifications (action groups) vs deep links.** An action group turns
the notification into the place the work happens — approve or reject without
opening the record — which is the single largest available increase in the value
of a mobile notification. It is labelled Beta in the Metadata API Developer
Guide, it needs an Apex class per action, and it moves a business decision to a
surface with almost no context around it. Design the deep-link path first so the
notification is complete without the beta feature; treat action groups as an
enhancement with a schedule risk attached.

**Notification as accelerator vs notification as mechanism.** Treating the
notification as an accelerator — the work is also in a queue, a task, or a
report — costs a second surface to build and maintain, and means some
notifications are redundant. Treating it as the mechanism is cheaper and creates
a system whose correctness depends on four gates you do not control, one of which
is whether a user tapped "Allow" on a permission dialog months ago. The first is
the only defensible choice for anything with a consequence.

**Where the throttle lives.** A static in the trigger handler is free and
suppresses nothing beyond the current transaction. A datetime field on the
subject record survives transactions, is visible to admins, is queryable during
an incident, and is shared by Flow and Apex senders alike — at the cost of a
field, a permission, and an extra DML. A separate delivery-log object adds true
auditability and per-recipient granularity at the cost of an object with a
retention policy. Most designs want the field; anything that has to prove what
was sent wants the log.

## Anti-Patterns

1. **Building a notification for a requirement whose verb is "know".** If nobody
   acts within minutes, this is a report subscription or a dashboard. Building it
   as a notification degrades every other notification in the org.

2. **Deploying `CustomNotificationType` without `NotificationTypeConfig`.** The
   type arrives, the delivery settings do not, mobile silently delivers nothing,
   and no error is raised anywhere.

3. **Enabling every channel "to make sure they see it".** Redundant delivery
   across channels does not increase action; it increases the probability the
   recipient mutes the one channel that mattered.

4. **Enumerating user IDs for an audience that has a name.** A queue or public
   group ID is one value, self-maintaining, and correct after the next
   reorganisation.

5. **Embedding record data in the body.** The body bypasses the record's sharing
   model. Point at the record; let the platform's access check do its job on
   arrival.

6. **Hand-built `/lightning/r/...` deep links.** `targetId` resolves per surface
   for free; a URL string is a Lightning-only assumption that breaks on mobile.

7. **Shipping without a measurement plan and a cut-off threshold.** "We'll see
   how it goes" is how an org accumulates forty notification types that nobody
   owns and nobody can justify deleting.

8. **Letting notification volume ride on bulk operations.** A data load that
   notifies per record consumes the org-wide notification allocation and starves
   the approvals and escalations that were the reason the channel existed.

## Official Sources Used

- Apex Reference Guide — `Messaging.CustomNotification` class: constructors, `setNotificationTypeId`, `setTitle` ("Maximum characters: 250"), `setBody` ("Maximum characters: 750"), `setSenderId`, `setTargetId` / `setTargetPageRef` ("Either a targetID or a targetPageRef is required to send a custom notification"), `setActionGroupId`, and `send(Set<String> users)` ("Values can be combined in a set, up to the maximum of 500 values"), plus the worked example that queries `CustomNotificationType` by `DeveloperName` `WITH USER_MODE` — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Messaging_CustomNotification.htm
- Metadata API Developer Guide — `CustomNotificationType` (file suffix `.notiftype`, directory `notificationtypes`, API 46.0+; `customNotifTypeName` max 80; `description` max 255 "displayed with the notification type name"; `desktop` and `mobile` required booleans; `slack` — "Reserved for future use"; `actionGroups` (Beta) with `CustomNotificationActionGroup` / `CustomNotificationActionDefinition`, `actionType` values `NotificationApiAction` or `Share`, `actionTarget` "the name of the Apex class where the action is implemented") — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_customnotificationtype.htm
- Metadata API Developer Guide — `NotificationTypeConfig` (file suffix `.config`, directory `notificationTypeConfig`, API 48.0+; `notificationTypeSettings` → `notificationType`, `appSettings` "An array of settings for the connected apps supported for a notification type" with `connectedAppName` and `enabled`, and `notificationChannels` → `desktopEnabled` / `mobileEnabled` / `slackEnabled`) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_notificationtypeconfig.htm
- Actions Developer Guide — Custom Notification Actions (`customNotifTypeId`, `recipientIds` and its documented ID kinds: "UserId (sent to this user if active), AccountId (sent to all active Account Team members; requires account teams enabled), OpportunityId (sent to all active Opportunity Team members; requires team selling enabled), GroupId (sent to all active group members), or QueueId (sent to all active queue members). Values can be combined in a list up to 500 values.", `title`, `body`, `targetId`, `targetPageRef`, `actionGroup`, `senderId`) — https://developer.salesforce.com/docs/atlas.en-us.api_action.meta/api_action/actions_obj_custom_notification.htm
- Object Reference for the Salesforce Platform — `CustomNotificationType` object (queried by `DeveloperName` to obtain the ID Apex and Flow require) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_customnotificationtype.htm
- Apex Developer Guide — Custom Metadata Types in Apex (`getAll()` / `getInstance()` cost no SOQL query, used here for the notification registry and the suppression window) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_metadata_types.htm
- Salesforce Help — Create and Send Custom Slack Notifications (the Slack notification is created as its own notification type through Notification Builder and bound to a Slack app) — https://help.salesforce.com/s/articleView?id=platform.notif_builder_create_send_slack.htm&type=5
- Salesforce Help — Considerations for Notifications (org-wide allocation for notification actions, notification-type and recipient ceilings) — https://help.salesforce.com/s/articleView?id=platform.notif_builder_considerations.htm&type=5
- Salesforce Well-Architected — Adaptable / User Experience — https://architect.salesforce.com/docs/architect/well-architected/adaptable/adaptable

### Sources consulted but not directly quotable

The two Salesforce Help pages listed above are Aura-rendered and did not return
article body text to a plain fetch. Their substance is reflected here from search
indexing of the same pages and is flagged inline in
[`gotchas.md`](gotchas.md) (Gotcha 9) and in the Slack discussion, rather than
quoted as though verified. Re-read them directly before quoting a specific number
to a customer.
