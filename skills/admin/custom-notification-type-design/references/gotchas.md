# Gotchas — Custom Notification Type Design

Failure modes that come from the *design* of a notification type rather than from
the code that sends it. Grounded in the Metadata API Developer Guide, the Actions
Developer Guide, and the Apex Reference Guide (Summer '26, API 67.0).

The unifying property of almost everything below: **a misdesigned notification
does not raise an error.** `send()` returns, the Flow shows a green path, and the
notification does not arrive. There is no failure signal to alert on, so the
design has to be right on the way in.

---

## Gotcha 1: Four Independent Delivery Gates, Three Outside Your Code

**What happens:** the automation runs, the debug log is clean, no exception is
thrown, and the recipient has nothing. Someone re-runs it. Still nothing.

A notification is delivered only if all four of these are open:

1. **The type declares the channel.** `CustomNotificationType.desktop` /
   `.mobile` — both documented as "Required" booleans.
2. **The org enables it.** `NotificationTypeConfig` →
   `notificationChannels { desktopEnabled, mobileEnabled, slackEnabled }`, plus
   `appSettings { connectedAppName, enabled }` per connected app.
3. **The user has not turned it off** in their own notification preferences.
4. **The device or browser permits it** — the mobile app installed and push
   granted at OS level; the browser's notification permission granted.

**When it occurs:** on the first production deploy of any new notification type,
and again every time a new mobile app is introduced to the org.

**How to avoid:** debug the gates in order, and out loud. Gate 1 is in the
`.notiftype` file. Gate 2 is Setup → Notification Delivery Settings (and is
deployable — see Gotcha 2). Gate 3 you can only ask the user about. Gate 4 needs
a real device, and there is no substitute: a desktop test proves nothing about
mobile because gates 2 and 4 are per-channel.

---

## Gotcha 2: `NotificationTypeConfig` Does Not Travel With the Type

**What happens:** the notification works in the sandbox where it was built and
delivers nothing in production, with identical metadata for the type.

`CustomNotificationType` and `NotificationTypeConfig` are two separate metadata
types with different suffixes and different directories:

| | Suffix | Directory | Since |
|---|---|---|---|
| `CustomNotificationType` | `.notiftype` | `notificationtypes` | API 46.0 |
| `NotificationTypeConfig` | `.config` | `notificationTypeConfig` | API 48.0 |

A change set or package containing only the first moves the definition. The
delivery settings in the target org stay at whatever they were, which for a type
that has never existed there is "nothing enabled."

**When it occurs:** every promotion between orgs, unless someone has deliberately
added the config to the deployment.

**How to avoid:** treat the pair as one deployable unit — same package.xml, same
PR, same review. Add a post-deploy step that verifies delivery settings in the
target org rather than assuming, because the failure is silent on both sides.

---

## Gotcha 3: Mobile Push Needs a Connected App, Not Just a Checkbox

**What happens:** `mobile` is `true` on the type, `mobileEnabled` is `true` in the
config, and phones still receive nothing.

`NotificationTypeConfig` → `notificationTypeSettings` → `appSettings` is
documented as "An array of settings for the connected apps supported for a
notification type", with `connectedAppName` ("Required. Specifies the API name of
a connected app") and `enabled`. Delivery to a device happens through a connected
app. If no connected app is enabled for the notification type, `mobileEnabled`
describes a channel with no carrier.

**When it occurs:** most reliably when an org uses a branded Mobile SDK app or a
Field Service app rather than (or in addition to) the standard Salesforce mobile
app — each is a separate connected app and each needs enabling per notification
type.

**How to avoid:** enumerate, at design time, every connected app that must
deliver this type, and read the exact `connectedAppName` values out of the target
org rather than inventing them; the set differs between orgs. Then verify on each
app family you listed, because "it arrived on my phone" only proves the app on
your phone.

---

## Gotcha 4: `slack` on `CustomNotificationType` Is Reserved

**What happens:** someone sets `<slack>true</slack>` on the type, deploys
successfully, and nothing about Slack changes.

The Metadata API Developer Guide describes the `slack` field on
`CustomNotificationType` as **"Reserved for future use."** A successful deploy is
not evidence the field does anything.

**The inverse mistake is equally wrong.** Do not conclude from that field that
Salesforce cannot notify Slack. Two things say otherwise:

- `NotificationTypeConfig` → `notificationChannels` carries a documented
  `slackEnabled` boolean alongside `desktopEnabled` and `mobileEnabled`.
- Notification Builder has a distinct "Create a Slack Notification" path that
  binds a notification to a Slack app and a Slack message configuration, sent by
  a Send Notification action.

**When it occurs:** whenever a requirement says "and post it to Slack" and
someone reaches for the nearest field with the right name.

**How to avoid:** design Slack as its own notification type with its own audience
and its own copy. That is both what the platform supports and the better design —
the person who must act and the channel that is celebrating want different
messages at different frequencies.

---

## Gotcha 5: 500 Is a Cap on IDs, Not on People

**What happens:** a design is rejected as "over the 500-recipient limit" for an
audience of 800 users, and someone builds a chunking loop that was never needed.

The Actions Developer Guide says of `recipientIds`: "Values can be combined in a
list up to 500 values." The corresponding Apex method is
`send(Set<String> users)`, documented with "Values can be combined in a set, up to
the maximum of 500 values."

Those 500 values are **IDs**, and the documented ID kinds fan out:

| ID kind | Resolves to | Prerequisite |
|---|---|---|
| `UserId` | that user, if active | — |
| `GroupId` | all active group members | — |
| `QueueId` | all active queue members | — |
| `AccountId` | all active Account Team members | account teams enabled |
| `OpportunityId` | all active Opportunity Team members | team selling enabled |

One `GroupId` covers an 800-person audience inside a single value.

**When it occurs:** any time the audience is conceived as a list of users rather
than as a membership.

**How to avoid:** express the audience as the smallest set of IDs that describes
it. This is also the maintainable choice — membership changes become a Setup
task instead of a deployment.

---

## Gotcha 6: `AccountId` and `OpportunityId` Recipients Resolve to Nobody Without Teams

**What happens:** a design that notifies "the account team" ships, sends cleanly,
and reaches zero people. No error, no warning.

The Actions Developer Guide qualifies both of the team-shaped recipient kinds:
`AccountId` is "sent to all active Account Team members; requires account teams
enabled", and `OpportunityId` is "sent to all active Opportunity Team members;
requires team selling enabled". Those are org-level features that may simply be
off, and are frequently off in a fresh scratch org or a newly provisioned
production org.

**When it occurs:** at the boundary between orgs — the feature is on in the
sandbox that was cloned from a mature production org and off in the scratch org
the developer used.

**How to avoid:** record the prerequisite next to the design decision, and assert
it during deployment rather than discovering it in production. If the feature
cannot be enabled, the audience has to be re-expressed as a public group, which
is a design change, not a configuration one.

---

## Gotcha 7: Title 250 / Body 750 Are Runtime Properties

**What happens:** the notification is fine for six months and then starts failing
for one account, because that account's name is long.

The documented maxima are "Maximum characters: 250" for the title and "Maximum
characters: 750" for the body — on both the Apex setters and the Flow action
inputs. Every real notification body is built from merge fields, so the length
that matters is the *resolved* length, which depends on data you do not control.

**When it occurs:** in production, on the record with the longest name, months
after launch, to one recipient — which is exactly the shape of bug nobody
reproduces.

**How to avoid:** build the body from a bounded template. Truncate the variable
parts explicitly rather than the whole string, so the truncation lands somewhere
harmless:

```apex
// Clip the variable part, not the sentence, so the call to action survives.
String subject = clip(acct.Name, 60);
n.setBody('Renewal for ' + subject + ' closes in 3 days. Open to review terms.');
```

Design bodies short on purpose. The notification is a pointer to the record, not
a substitute for opening it.

---

## Gotcha 8: `WITH USER_MODE` Turns a Permission Problem Into "The Type Doesn't Exist"

**What happens:** `System.QueryException: List has no rows for assignment to
SObject` from the notification-type lookup. Everybody goes to Setup, confirms the
type is there, and is confused.

The Apex Reference Guide's own sample queries the type with `WITH USER_MODE`:

```apex
CustomNotificationType notificationType =
    [SELECT Id, DeveloperName
     FROM CustomNotificationType
     WHERE DeveloperName='Custom_Notification'
     WITH USER_MODE
     LIMIT 1];
```

A user-mode query enforces the running user's access. If that user cannot read
`CustomNotificationType`, the query returns zero rows — which is
indistinguishable, at the call site, from the type not being deployed.

**When it occurs:** when the sender runs as a low-privilege user (a community
user, an integration user, a guest-adjacent context) rather than as the admin who
built it.

**How to avoid:** catch the empty result and say which of the two causes it might
be, in the exception message. A design decision hides here too: if the sender
must run for users who legitimately should not read notification metadata, the
send belongs in a context that does not depend on their access.

---

## Gotcha 9: Notification Actions Are Rate-Limited Org-Wide

**What happens:** a data load or a batch job fires notifications per record, and
notifications elsewhere in the org — approvals, escalations — stop arriving.

Custom notifications draw on an org-wide allocation of notification actions per
period rather than a per-Flow or per-user one, so a single noisy sender competes
with every other notification in the org. Salesforce Help publishes the current
numbers under the considerations for sending custom notifications; treat the
exact figure as something to re-read rather than memorise, because it is the sort
of number that moves between releases.

<!-- UNVERIFIED: widely reported figures are 10,000 notification actions per hour
     per org, 500 custom notification types, and up to 10,000 recipients resolved
     per notification. These appear in Salesforce Help ("Considerations for
     Notifications" / "Considerations for Processes that Send Custom
     Notifications"), but that page is Aura-rendered and could not be fetched to
     confirm the wording. Re-check before quoting a number to a customer. -->

**When it occurs:** during migrations and bulk edits — precisely when the org is
least able to notice that its escalation notifications went quiet.

**How to avoid:** three design controls, in order of leverage. Suppress
notifications for system-driven writes (a `Bypass_Notifications__c` flag on a
custom setting the load process sets). Prefer group and queue IDs so one action
covers many people. Use digests for anything bulk-shaped. And when a bulk job
genuinely must notify, notify a queue once rather than every affected owner
individually.

---

## Gotcha 10: Inactive Users Silently Drop Out of Every Recipient Expression

**What happens:** the on-call notification stops reaching one person after they
change roles, and nobody notices until the incident.

Every documented recipient expansion is qualified with "active": `UserId` is
"sent to this user if active", groups and queues resolve to "all active"
members, and the team-based kinds resolve to active team members. A deactivated
user is not an error, it is an absence.

**When it occurs:** at every leaver, and at every role change that also
deactivates a user record.

**How to avoid:** never let a notification's audience be a single user ID for
anything operationally important — one leaver then produces a silent zero-recipient
notification. A queue or group with a documented minimum membership degrades to
"fewer people" instead of "nobody", and can be monitored.

---

## Gotcha 11: Deep Links — `targetId` Beats a Hand-Built URL, Every Time

**What happens:** the notification opens correctly on desktop and lands somewhere
useless in the mobile app, or opens the record in the wrong app context.

The platform requires exactly one of `targetId` or `targetPageRef`
("Either a targetID or a targetPageRef is required to send a custom
notification"). `targetId` takes a record ID and lets the platform resolve the
destination per surface. `targetPageRef` takes a serialized `PageReference` and
is the supported route for non-record destinations.

A hand-built `/lightning/r/Case/{id}/view` string is neither. It is a
Lightning-specific URL that bypasses the platform's navigation resolution and
bakes in an assumption about which app the recipient is in.

**When it occurs:** whenever the design was written by someone thinking in terms
of the URL bar.

**How to avoid:** record destination → `targetId`. Non-record destination →
`targetPageRef` built from a `PageReference` shape and serialized. Never a raw
URL string. And if the destination is a *filtered list view*, treat that as a
signal that the notification has no specific record to point at, which usually
means it should have been a digest or a report subscription.

---

## Gotcha 12: The Bell Has No Acknowledgement

**What happens:** the quarterly review asks "is anyone reading these?" and there
is no answer, so the notification survives another quarter on the strength of the
fact that nobody has complained.

Custom notifications carry no built-in read receipt or click-through metric that
the sending org can query. Delivery is not readership, and neither is engagement.

**When it occurs:** at the first review of any notification type built without a
measurement plan — which is most of them.

**How to avoid:** instrument the *destination*, not the notification. Append a
tracking parameter to the `targetPageRef` state, or record the follow-on action
you actually care about (case reassigned within 30 minutes of the escalation
notification) and measure that. Decide the metric and the cut-off threshold
before launch: "engagement below X% at review means this type is redesigned or
deleted" is a commitment; "we'll see how it goes" is how orgs end up with forty
notification types nobody owns.

---

## Gotcha 13: Action Groups Are Beta, and Beta Is a Design Input

**What happens:** a roadmap is built around actionable mobile notifications —
approve/reject from the notification shade — and the feature's status turns out
to matter to the customer's risk review.

`CustomNotificationType.actionGroups` is labelled **(Beta)** in the Metadata API
Developer Guide. Its nested `CustomNotificationActionDefinition` requires an
`actionLabel`, an `actionName`, and an `actionType` that "Required. Values are:
NotificationApiAction or Share", with `actionTarget` naming "the name of the Apex
class where the action is implemented". Apex selects the group at send time via
`setActionGroupId(...)`.

**When it occurs:** in Industry and Field Service designs, where "act from the
notification" is a genuinely valuable requirement and the feature is exactly what
is wanted.

**How to avoid:** design the non-actionable path first so the notification is
useful without the beta feature, then add action groups as an enhancement. Check
current beta status before committing — the useful question is not "does it
exist" but "what does the release documentation say about it *today*", because
beta features change and a design that hard-depends on one is a design with a
schedule risk in it.
