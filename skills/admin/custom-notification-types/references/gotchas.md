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

**How to avoid:** Name every type explicitly in `package.xml` —
`<types><members>Case_Priority_High</members><name>CustomNotificationType</name></types>`.
The wildcard is not an option here: "This metadata type doesn't
support the wildcard character `*` (asterisk) in the `package.xml`
manifest file" (Metadata API Developer Guide,
`api_meta.txt:41892-41894`), so a manifest built by pasting `*`
retrieves nothing and fails silently at the manifest level. In the
Salesforce CLI the type name is `CustomNotificationType` —
`sf project retrieve start -m "CustomNotificationType:Case_Priority_High"`
pulls just one. Add it to a Change Set under "Custom Notification
Type." In source control the file lives in the **`notificationtypes`**
directory with the **`.notiftype`** suffix —
`force-app/main/default/notificationtypes/<DevName>.notiftype-meta.xml`
(`api_meta.txt:41783-41784`) — not in a `customNotificationTypes`
folder, which is the plural-camelCase name people assume by analogy
with `customMetadata` and which produces a directory the CLI ignores.

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
500. UNVERIFIED (2026-09-04): the exact exception type and message
are not documented in the Apex Reference Guide; what *is* documented
is the cap itself — "Values can be combined in a set, up to the
maximum of 500 values." (`apexrefguide.txt:166781`) — and that
`CustomNotification.send()` can throw (`apexrefguide.txt:166648`).

**The 500 counts Ids, not people.** `send(Set<String> users)` accepts
`UserId`, `GroupId`, `QueueId`, `AccountId` (Account Team) and
`OpportunityId` (Opportunity Team) values
(`apexrefguide.txt:166766-166781`), and each non-user Id fans out
server-side. One `GroupId` is one value regardless of how many people
are in the group. So the chunking loop below is only needed for
hand-assembled user-Id sets; when the audience is a membership, the
right fix is to send one group Id, not to chunk 800 user Ids. See
`admin/custom-notification-type-design` Gotcha 5 for the design-side
version of this choice.

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

---

## Gotcha 6: The chunking loop has a ceiling — a transaction gets ten push notification method calls, not unlimited ones

**What happens:** the standard fix for the 500 cap is a loop that
calls `send()` once per 500-recipient chunk. It works in a unit test
with 1,200 recipients (3 calls). It is then pointed at a 12,000-user
audience, the loop makes 24 calls, and the transaction dies partway
through with a governor limit — after some recipients have already
been notified and the rest have not. There is no rollback of the
notifications that already went out.

**When it occurs:** the Salesforce Developer Limits and Allocations
Quick Reference lists, in the per-transaction Apex governor table,
"Maximum number of push notification method calls allowed per Apex
transaction — 10" and "Maximum number of push notifications that can
be sent in each push notification method call — 2,000", identical for
synchronous and asynchronous contexts
(`salesforce_app_limits_cheatsheet.txt:96-100`). Ten calls is the
budget for the whole transaction, shared with anything else in the
call stack that also sends — a trigger, a Flow invoked from the same
DML, a managed package.

UNVERIFIED (2026-09-04): the cheat sheet names the governed operation
"push notification method calls" without naming
`Messaging.CustomNotification.send()` specifically; historically this
row governs `Messaging.PushNotification.send()`. Confirm against a
debug log in your own org — `LIMIT_USAGE_FOR_NS` reports the counter
— before designing a fan-out that assumes either answer.

**How to avoid:** size the fan-out against the *call count*, not just
the recipient count. Collapse the audience into group or queue Ids so
one call covers many people (Gotcha 3). When a genuinely large set of
distinct user Ids is unavoidable, chunk across **transactions** rather
than inside one — a Queueable that sends a bounded number of chunks
and then re-enqueues itself, or a Batchable with a scope size chosen
so each `execute()` stays inside the budget. Log the last chunk index
you completed so a mid-run failure can resume rather than re-notify.

---

## Gotcha 7: The bell keeps working after mobile push has stopped — so a bell test proves nothing about push

**What happens:** QA verifies a new notification by watching the bell
icon light up, signs off, and ships. In production during a bulk
event, users report that the bell shows the notifications but their
phones stayed silent. Nothing errored, nothing was logged, and the
notifications are all present and correct in the org.

**When it occurs:** the org has an hourly push allocation — "An org
can send up to 20,000 iOS and 10,000 Android push notifications per
hour" — and "Only deliverable notifications count toward this limit",
so recipients without the mobile app installed do not consume it
(`salesforce_app_limits_cheatsheet.txt:449-454`). The behaviour when
it runs out is the trap: "When an org's hourly push notification limit
is met, any additional notifications are still created for in-app
display and retrieval via REST API."
(`salesforce_app_limits_cheatsheet.txt:465-466`). The in-app channel
degrades gracefully and invisibly. A test-push generated from the Test
Push Notification page is capped at one recipient and still counts
against the same hourly allocation
(`salesforce_app_limits_cheatsheet.txt:455-456`), so a QA cycle that
leans on it is spending production budget.

**How to avoid:** treat "bell appeared" and "push arrived" as two
separate assertions with two separate tests, and make the second one a
real device with a real user. For any sender that can burst — a data
load, a batch job, a mass reassignment — bound the per-hour volume in
the sender rather than discovering the ceiling from user reports.
Because exhaustion is invisible from inside Salesforce, the only
practical detector is a canary: one instrumented device on the
recipient list whose owner reports when push goes quiet.

---

## Gotcha 8: `desktop` and `mobile` default to false — a type can deploy cleanly and deliver to nowhere

**What happens:** the `.notiftype` deploys, the Flow deploys, the Flow
runs green, the debug log shows the action completing, and no
recipient sees anything on any channel. Every artefact reports
success because nothing failed — the notification was created for a
type with no enabled delivery channel.

**When it occurs:** two routes get you here. Hand-authoring the XML
from the Metadata API sample and dropping the channel elements
believing they are optional — they are documented as **required**
booleans, `desktop` "Indicates whether the desktop delivery channel is
enabled (true) or not (false)" and `mobile` likewise
(`api_meta.txt:41805-41806`, `api_meta.txt:41810-41811`). Or creating
the type through the API/Tooling path, where the sObject fields
`Desktop` and `Mobile` are both "Defaulted on create" with "The
default value is `false`" (`object_reference.txt:88332-88338`,
`object_reference.txt:88369-88386`). The send call has no say in this:
`Messaging.CustomNotification` and the Flow action choose *what* is
sent and to *whom*, never over which channel — that is a property of
the type, and separately of `NotificationTypeConfig`.

**How to avoid:** assert the flags, do not eyeball them. Post-deploy,
`SELECT DeveloperName, Desktop, Mobile FROM CustomNotificationType`
in the target org and fail the release if either the row is missing or
both booleans are false. The checker in this skill's `scripts/`
enforces the same rule against the `.notiftype` files in a DX tree
before they leave the branch.

---

## Gotcha 9: Omitting both `targetId` and `targetPageRef` throws — and the documented workaround is a fake Id

**What happens:** a "nothing to open" notification — a nightly summary,
a job-finished ping — is built with a title and a body and no target,
on the reasonable assumption that a target is optional because neither
setter is individually required. `send()` throws.

**When it occurs:** the guide states the rule in one sentence: "You
must specify a target for a notification. The target can be specified
using either the `targetID` or the `targetPageRef` attribute. Neither
attribute is required, but if both are omitted, `send()` throws an
exception." (`apexrefguide.txt:166572-166573`). The documented escape
is deliberately unlovely: "If there's no natural target for a
notification, set the `targetID` to a dummy value, such as
`000000000000000AAA`. A dummy value prevents the exception, and also
prevents automatic navigation when responding to the notification in
the client app." (`apexrefguide.txt:166573-166575`).

There is a second edge on the same rule. Both attributes may be set
together, and then "The client app that receives the notification
determines which target, if any, to use"
(`apexrefguide.txt:166576-166577`) — the sender does not get to
decide. Since before Winter '21 only `targetId` existed, "Most client
applications expect to find a `targetID` in the notification payload",
and a client that cannot handle a `targetPageRef`-only notification
needs the dummy `targetID` too (`apexrefguide.txt:166587-166589`).

**How to avoid:** make the target an explicit decision in the design,
with three named outcomes rather than two: a real record Id, a
`pageReference` for a list or page, or the documented dummy Id when
the notification genuinely opens nothing. Write the dummy as a named
constant (`NO_TARGET = '000000000000000AAA'`) so a reviewer sees an
intent instead of a typo. Never let it be reached by accident — a
`targetId` that silently arrived as null is the failure this rule
exists to surface.

---

## Gotcha 10: The lookup that resolves the type Id runs as the user, so a missing permission reports as "type not found"

**What happens:** the notification works for admins and fails for
everyone else with a `List has no rows for assignment` or
`QueryException` pointing at the `CustomNotificationType` query — a
line that has nothing to do with notifications. Teams chase a
deployment problem ("the type isn't in this org") that is really a
permission problem.

**When it occurs:** the Apex Reference Guide's own example queries the
type `WITH USER_MODE` (`apexrefguide.txt:166604-166609`), and states
the surrounding rule: "By default, Apex code executes in user mode,
which means that user permissions on objects and field-level security
are respected… to send notifications with `CustomNotification`, you
must have the **Send Custom Notifications** user permission. If you
don't have the required permission, the `send()` method fails."
(`apexrefguide.txt:166590-166594`). A user lacking access to the
`CustomNotificationType` object never reaches `send()` at all — the
query returns zero rows first, converting a clear permission failure
into a misleading data-shaped one.

**How to avoid:** provision **Send Custom Notifications** on the
permission set that grants the feature, alongside whatever grants the
Flow or class, and test as a least-privileged user rather than as an
admin — this is the single test that separates the two failure modes.
In code, guard the lookup so the diagnosis survives:
`if (types.isEmpty()) { throw new IllegalArgumentException('Notification type ' + devName + ' not visible to ' + UserInfo.getUserName()); }`.
A record-triggered Flow running in system context will not reproduce
the failure, which is why the bug reaches production.
