# Gotchas — Custom Notification Types

Non-obvious platform behaviors that bite teams between "the
notification fires in my sandbox" and "the notification reaches
the recipient's phone in production." These compound the rules in
`SKILL.md`'s gotchas section — they're the second-order issues
that only surface after the first round of fixes.

## Gotcha 1: CustomNotificationType is metadata, not data — deployment behavior surprises everyone

**What happens:** The `CustomNotificationType` sObject (API 47.0+)
looks like a regular sObject — it's queryable via SOQL, it has an
Id, you can pull it up in Workbench. So practitioners assume that
deploying it to a new org is a matter of inserting rows. It isn't.
`CustomNotificationType` is also a Metadata API type: the
notification type is a piece of org configuration that must be
deployed via `package.xml` (component name
`CustomNotificationType`, member `MyTypeDeveloperName`) or via a
managed/unmanaged package, not via Data Loader or Bulk API.

**When it occurs:** A team builds the notification type in a
sandbox using the Setup UI, tests the flow end-to-end, and is
ready to ship to production. The CI/CD pipeline (sfdx, ant, or
Change Sets) runs and the flow deploys but the notification type
does not — because the team retrieved Flows but not
`CustomNotificationType` metadata. The flow's Send Custom
Notification action references a Notification Type Id that doesn't
exist in production. Production runs throw
`INVALID_NOTIFICATION_TYPE_ID` or, in Flow context, silently fail
with a generic "An unhandled fault has occurred" toast.

**How to avoid:** Add `<types><members>*</members><name>CustomNotificationType</name></types>`
(or the specific DeveloperName) to your `package.xml` before
retrieving for deploy. In sfdx/Salesforce CLI, the metadata type
is `CustomNotificationType` — `sf project retrieve start -m
"CustomNotificationType:Case_Priority_High"` pulls just one. Add it
to a Change Set under "Custom Notification Type." When tracking
metadata in source control, the file lives at
`force-app/main/default/customNotificationTypes/<DevName>.notiftype-meta.xml`.

---

## Gotcha 2: Mobile push requires Connected App push credentials AND user-side push permissions — both must be in place or notifications never reach the phone

**What happens:** The notification type has the Mobile channel
checked. The flow fires successfully. The recipient's Salesforce
mobile app is installed and the user is logged in. The phone shows
no notification. The bell icon inside the app eventually displays
the entry when the user opens the app, but the OS-level push
banner never appears.

**When it occurs:** Mobile push notifications travel through a
multi-hop pipeline: Salesforce backend → APNs (Apple) or FCM
(Google) → device. Every hop has a gatekeeper. The most common
break is the Salesforce-side Connected App: the standard
"Salesforce for iOS" and "Salesforce for Android" connected apps
must have push notification credentials configured (Setup → Apps →
Connected Apps → Manage → Mobile App Settings → Push Notification
Settings) and the notification type must be listed in the
Connected App's "Supported Push Notification Types" — if you
created a new notification type after the Connected App was
configured, you have to come back and add it. The second-most
common break is on the device: iOS users who tapped "Don't Allow"
on the first launch's push prompt have to manually re-enable
notifications in Settings → Salesforce → Notifications, and
in-app under Settings → Notifications.

**How to avoid:** As part of the notification type rollout
checklist, (1) edit each relevant Connected App (typically
"Salesforce" for iOS and Android) and confirm the new notification
type appears under "Supported Push Notification Types," and (2)
test on a real device with a real user, not just the in-app bell
in a browser. A bell-only test is misleading because bell delivery
works even when push is broken end-to-end. Document that recipients
must keep OS-level notifications enabled for the Salesforce mobile
app or push silently won't reach them.

---

## Gotcha 3: Recipient list capped at 500 per `send()` call — bulk Apex must chunk explicitly

**What happens:** Apex code constructs a `Messaging.CustomNotification`,
populates a `Set<String>` of recipient Ids with 800 entries, and
calls `n.send(recipients)`. The call throws
`Messaging.CustomNotificationException: Invalid recipients`
(or a similar generic error message that does not mention the
500 cap). The notification is sent to no one, not to the first
500.

**When it occurs:** Quarterly bulk operations that fan out to a
large recipient set: territory realignments, mass approval reminders,
end-of-quarter close-the-books reminders, license-expiry warnings
for an entire customer base. Also surfaces when the recipient set
expands a Queue Id server-side and the queue has more than 500
members — though Queue expansion is usually counted as one
recipient on the client side, the platform-level fan-out happens
within Salesforce and doesn't trip the 500 cap. The bite is
exclusively on explicit `Set<String>` payloads that the Apex
author assembled.

**How to avoid:** Wrap `send()` in a helper that asserts the cap
and chunks the recipient set. The pattern is mechanical:

```apex
private static void sendChunked(Messaging.CustomNotification n,
                                Set<String> allRecipients) {
    List<Id> asList = new List<Id>();
    for (String id : allRecipients) asList.add((Id) id);
    Integer chunkSize = 500;
    for (Integer i = 0; i < asList.size(); i += chunkSize) {
        Integer end = Math.min(i + chunkSize, asList.size());
        Set<String> chunk = new Set<String>();
        for (Id id : asList.subList(i, end)) chunk.add(String.valueOf(id));
        n.send(chunk);
    }
}
```

For audiences larger than 5,000 recipients, also move the work into
a Queueable or Batchable so you don't burn the synchronous CPU
budget on the chunking loop.

---

## Gotcha 4: `Target Page Reference` or `Target Id` must point to a real, accessible record or URL — otherwise the notification opens to an error page

**What happens:** The notification fires, the recipient sees it on
desktop and mobile, they tap it, and the Salesforce mobile app
shows "This record doesn't exist" or the desktop browser lands on
the generic "Insufficient Privileges" page. The recipient assumes
the notification system is broken; the actual problem is that the
Target points to a record they can't see, a record that was
deleted between the send and the click, or a `pageReference` JSON
blob that doesn't deserialize.

**When it occurs:** Several common triggers. (1) The notification
fires before the target record is committed — e.g., a "before
insert" trigger sends a notification with `setTargetId(record.Id)`
but the record's Id is null at that point because the DML hasn't
happened yet. (2) The notification's target is a record in a
restricted sharing context — the recipient User can receive the
notification (notifications bypass sharing) but cannot see the
record (sharing applies on click). (3) The
`setTargetPageRef(jsonString)` value contains a malformed JSON
blob or references a non-existent component — there's no validation
at send time, so the bad payload only surfaces on tap.

**How to avoid:** Always fire notifications from `after insert`
(or later) contexts so the target record's Id exists. Before
sending, verify the recipient has at least Read access to the
target — for community/partner notifications, route to a Community
URL via `setTargetPageRef` instead of a raw record Id. Validate
`pageReference` JSON against Salesforce's documented schema (the
shape `{"type":"<page type>","attributes":{...}}`) and use a Custom
Metadata Type to store the JSON templates so QA can preview them
without rebuilding Apex.

---

## Gotcha 5: Custom Notification "Type Name" appears in user notification settings — name it with the customer in mind, not engineering jargon

**What happens:** A team creates a notification type with
DeveloperName `Opp_Stage_Closed_Won` and MasterLabel
`Opp_Stage_Closed_Won` (someone took the lazy shortcut of typing
the same thing in both fields). Two months later, users complain
they're getting too many notifications and IT tells them to disable
specific types in Setup → My Settings → Display & Layout →
Notification Builder. Users scan the list and see ten entries that
look like database column names — `Opp_Stage_Closed_Won`,
`Case_Pri_Escalation_v2`, `Wrkflw_Rmndr_30Day` — and either disable
all of them (losing important alerts) or disable nothing (giving
up on the notification problem).

**When it occurs:** Notification type proliferation: any org with
more than ~5 notification types accumulates over a year, especially
when multiple teams create their own. The MasterLabel field appears
in the user-facing notification preferences UI, in the mobile
app's notification list, and in the desktop notification toast's
secondary text — it is a customer-visible string, even though the
admin UI displays it next to the developer-style DeveloperName and
encourages treating them as the same kind of value.

**How to avoid:** Treat MasterLabel as customer copy. Use plain
language: `Case escalation` not `Case_Pri_Escalation_v2`,
`Opportunity closed won` not `Opp_Stage_Closed_Won`, `Quote awaiting
approval` not `Qte_Apprvl_Pending`. Reserve DeveloperName for the
underscore_separated machine identifier; it never appears in
user-facing surfaces. When auditing existing notification types,
list every MasterLabel against the user-facing preference UI and
rename anything that reads like a variable name. Renaming the
MasterLabel does not invalidate existing flows or Apex (they reference
the DeveloperName or Id, not the label), so the rename is
zero-risk from a code perspective.
