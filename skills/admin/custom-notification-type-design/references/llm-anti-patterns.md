# LLM Anti-Patterns — Custom Notification Type Design

Mistakes AI assistants make specifically when *designing* a notification type, as
distinct from writing the send. Most of them share a cause: notification design is
a product decision expressed as configuration, and a model asked for
configuration will produce configuration that satisfies the sentence rather than
the goal.

---

## Anti-Pattern 1: `<slack>true</slack>` on the Custom Notification Type

**What the LLM generates:**

```xml
<CustomNotificationType xmlns="http://soap.sforce.com/2006/04/metadata">
    <customNotifTypeName>Deal_Won</customNotifTypeName>
    <masterLabel>Deal Won</masterLabel>
    <desktop>true</desktop>
    <mobile>true</mobile>
    <slack>true</slack>
</CustomNotificationType>
```

**Why it happens:** the field exists, it is named `slack`, the request said
"notify Slack", and the deploy succeeds. Every available signal points the same
way and none of them is the documentation.

**Correct pattern:** the Metadata API Developer Guide describes `slack` on
`CustomNotificationType` as **"Reserved for future use."** Leave it unset. A
Slack notification is a separate notification type created through Notification
Builder's Slack path, bound to a Slack app and a message configuration, and sent
by a Send Notification action. Separately, `NotificationTypeConfig` →
`notificationChannels` does carry a real `slackEnabled` boolean — so Slack is a
genuine channel at the org-settings layer even though this field is not the
switch for it.

**The mirror-image error to avoid:** having learned that `slack` is reserved, do
not then tell a user Salesforce cannot notify Slack. It can. "This field is
reserved" and "the feature does not exist" are different claims, and only the
first one is supported by the documentation.

**Detection hint:** a `slack` element in a `.notiftype` file, or any answer that
describes Slack as a third checkbox alongside desktop and mobile.

---

## Anti-Pattern 2: Shipping the Type Without `NotificationTypeConfig`

**What the LLM generates:** a complete, correct `.notiftype` file, a Flow or Apex
sender, and a `package.xml` containing `CustomNotificationType` and nothing else.

**Why it happens:** the request was "create a custom notification type", the type
is the named artifact, and the delivery settings are a different metadata type in
a different directory that the request never mentioned. Nothing in the type file
hints that a second file exists.

**Correct pattern:** `CustomNotificationType` (`.notiftype`, directory
`notificationtypes`) and `NotificationTypeConfig` (`.config`, directory
`notificationTypeConfig`) are one deployable unit. The second carries
`notificationChannels { desktopEnabled, mobileEnabled, slackEnabled }` and the
`appSettings` array naming which connected apps may deliver. Without it the type
exists in the target org and delivers nothing on mobile.

**Detection hint:** a deployment plan or `package.xml` naming
`CustomNotificationType` with no `NotificationTypeConfig` beside it.

---

## Anti-Pattern 3: Enumerating User IDs for an Audience That Is Really a Membership

**What the LLM generates:**

```apex
List<User> agents = [SELECT Id FROM User
                     WHERE Profile.Name = 'Support Agent' AND IsActive = TRUE];
Set<String> recipients = new Set<String>();
for (User u : agents) { recipients.add(u.Id); }
// ... then a chunking loop because the list might exceed 500
```

**Why it happens:** "notify the support agents" maps cleanly onto "query the
support agents", and a set of user IDs is the obvious shape for something called
`recipientIds`. The polymorphism of that parameter is a documented detail rather
than an inferable one.

**Correct pattern:** `recipientIds` accepts `UserId`, `GroupId`, `QueueId`,
`AccountId` (active Account Team members, requires account teams enabled) and
`OpportunityId` (active Opportunity Team members, requires team selling enabled).
Passing one public group ID or one queue ID replaces the query, replaces the
chunking loop, and makes membership an administrable thing rather than a
code-shaped thing.

The generated version also has a subtler defect: it hardcodes a profile name into
a runtime query, so the day the org migrates that profile to a permission set the
notification silently stops reaching anyone.

**Detection hint:** a SOQL query against `User` immediately before a notification
send, or any chunking loop over recipients where the audience has a name
("the support team", "the account team") in the requirement.

---

## Anti-Pattern 4: A Notification for Every Field Change

**What the LLM generates:** a record-triggered flow on "A record is created or
updated" with no entry criteria and a Send Custom Notification action, or an Apex
trigger that notifies from `after update` unconditionally.

**Why it happens:** the requirement said "notify when the record changes", and
that is exactly what was built. The unstated requirement — that a notification is
an interruption with a cost, and that most saves are not events a human should be
told about — is not in the prompt and is not recoverable from it.

**Correct pattern:** notify on a *transition* the recipient can act on, and
exclude the actor. Entry criteria along the lines of:

```text
AND(
  ISCHANGED({!$Record.OwnerId}),
  NOT(ISBLANK({!$Record.OwnerId})),
  {!$User.Id} <> {!$Record.OwnerId}
)
```

The third clause is the one that gets omitted, and it is why the person who did
the thing is told the thing was done.

**Detection hint:** notification actions in a flow whose entry criteria contain
no `ISCHANGED` and no comparison against `$Record__Prior`, or a trigger sending
from `after update` with no field-change guard.

---

## Anti-Pattern 5: Multi-Channel by Default

**What the LLM generates:** `desktop: true`, `mobile: true`, and a
recommendation to also post to Slack and send an email "for redundancy".

**Why it happens:** every channel is a capability, capabilities enumerate well,
and more delivery reads as more reliability. The cost of a channel is paid by
someone who is not in the conversation.

**Correct pattern:** each channel needs its own justification tied to the
recipient's required response time. Desktop is the default because the bell is
persistent and cheap to ignore. Mobile push interrupts a person who may be
driving, and earns that only when minutes matter. Redundant delivery of the same
message across channels does not increase the chance of action; it increases the
chance the user mutes the channel that mattered.

**Detection hint:** every channel enabled with no per-channel rationale, or the
words "for redundancy" / "to make sure they see it" attached to a channel choice.

---

## Anti-Pattern 6: A Hand-Built Lightning URL as the Deep Link

**What the LLM generates:**

```apex
n.setTargetPageRef('/lightning/r/Case/' + c.Id + '/view');
```

or a `targetPageRef` containing a URL string rather than a serialized
`PageReference`.

**Why it happens:** `/lightning/r/Object/Id/view` is the URL in the browser bar,
it is enormously represented in blog posts and older admin guidance, and it
appears to work on desktop.

**Correct pattern:** for a record destination, `setTargetId(recordId)` — the
platform resolves it per surface, so the same notification opens correctly in the
mobile app and on desktop with no URL construction. `targetPageRef` is for
non-record destinations and takes a serialized `PageReference`:

```apex
n.setTargetPageRef(JSON.serialize(new Map<String, Object>{
    'type' => 'standard__objectPage',
    'attributes' => new Map<String, Object>{
        'objectApiName' => 'Lead',
        'actionName'    => 'list'
    }
}));
```

Exactly one of `targetId` / `targetPageRef` is required, and choosing the wrong
one is a design error that only shows up on the surface you did not test.

**Detection hint:** the literal `/lightning/r/` anywhere near a notification, or
a `targetPageRef` whose value is a string starting with `/`.

---

## Anti-Pattern 7: A Static Boolean as the Throttle

**What the LLM generates:**

```apex
public class NotificationGuard {
    private static Boolean alreadySent = false;
    public static Boolean shouldSend() {
        if (alreadySent) { return false; }
        alreadySent = true;
        return true;
    }
}
```

**Why it happens:** the static-recursion-guard idiom is the standard Apex answer
to "stop this firing twice", it is correct for its actual purpose, and
"don't notify the same person repeatedly" sounds like the same problem.

**Correct pattern:** a static guards *one transaction*. Notification fatigue is
produced by many transactions — six separate saves over four minutes are six
transactions and six fresh statics. Throttling state has to outlive the
transaction, which means it lives on the record (a `Last_Notified_At__c`
datetime) or on a delivery-log row. That also makes it visible to admins and
answerable when someone asks why a notification fired six times.

Order matters and is easy to get backwards: **send, then stamp**. Stamping first
means a failed send still consumes the window, so the event that most needed the
notification is the one that never arrives.

**Detection hint:** a static `Boolean` or static `Set<Id>` presented as the
answer to notification frequency, rather than to trigger recursion.

---

## Anti-Pattern 8: Treating the 500 Limit as a Recipient Ceiling

**What the LLM generates:** a chunking loop that splits an 800-user audience into
two batches of 500 and 300, plus a caveat that the design "may need Batch Apex
above a few thousand recipients".

**Why it happens:** "up to the maximum of 500 values" reads as 500 people, and
chunking is the correct and familiar response to a batch-size limit. The
distinction between an ID and the humans it expands to is not in the sentence.

**Correct pattern:** 500 is the cap on the *values passed*. One `GroupId` or
`QueueId` covers the whole 800-person audience within a single value, with no
chunking, no `User` query, and membership maintained in Setup. Chunking is only
necessary when the design genuinely needs hundreds of distinct, individually
chosen recipients — which is rare, and usually means the audience was modelled
wrong.

**Detection hint:** a chunking loop over recipients where the audience is
describable in words as a team, queue, role, or group.

---

## Anti-Pattern 9: A Notification Where a Report Subscription Was the Answer

**What the LLM generates:** a complete, well-formed notification design for a
requirement like "keep managers informed about pipeline health" — type,
recipients, throttle, deep link to a dashboard.

**Why it happens:** the request contained the word "notify" (or the model
supplied it), and the model's job is to build what was asked for. Declining to
build the requested artifact is not a shape most completions take.

**Correct pattern:** a notification is an interruption, and an interruption is
justified by an action the recipient must take *now*. "Be informed" is served by
a report subscription, a dashboard, or a Chatter post — all of which the
recipient consumes on their own schedule and none of which erode the credibility
of the bell. The design question to answer first, in one sentence, is what the
recipient does within minutes of receiving it. If it cannot be written, the
notification should not be built, and saying so is the more useful answer.

**Detection hint:** a notification design whose stated purpose contains
"awareness", "visibility", "keep informed", or "so they know", with no verb
describing what the recipient does.

---

## Anti-Pattern 10: Ignoring the Team-Feature Prerequisites

**What the LLM generates:** `recipientIds` populated with an `AccountId` and a
confident note that this reaches the account team.

**Why it happens:** the documentation sentence is compound — "sent to all active
Account Team members; requires account teams enabled" — and completions
frequently carry the first half and drop the qualifier after the semicolon.

**Correct pattern:** carry the prerequisite into the design artifact.
`AccountId` requires account teams enabled; `OpportunityId` requires team selling
enabled. Both are org-level features that are commonly off in scratch orgs and in
newly provisioned production orgs, and when they are off the notification
resolves to zero recipients with no error at all.

**Detection hint:** an `AccountId` or `OpportunityId` in a recipient expression
with no accompanying statement about the org feature it depends on.

---

## Anti-Pattern 11: Writing the Type Description for the Release Notes

**What the LLM generates:**

```xml
<description>Custom notification type for the Q3 case escalation project (PROJ-4412).</description>
```

**Why it happens:** a description field in a metadata file reads as developer
documentation, and the surrounding context is a project.

**Correct pattern:** the Metadata API Developer Guide says this field "Specifies
a general description of the notification type, which is displayed with the
notification type name." Wherever the name appears, this appears — so write it
for whoever is reading the name and deciding what the notification is for, in
255 characters or fewer. "Fires when a case you cover is 30 minutes from
breaching its SLA" earns its place; a Jira key does not.

<!-- UNVERIFIED: the exact surfaces on which the description renders (Setup only,
     or also the recipient's own notification-preference screen) is not stated in
     the Metadata API Developer Guide, and the Salesforce Help pages for
     Notification Builder could not be fetched to confirm. Write it as
     user-readable prose regardless; that is correct either way. -->

**Detection hint:** a project code, a sprint name, a date, or the phrase "custom
notification type for" in the `description` element.
