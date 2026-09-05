# LLM Anti-Patterns — Chatter Notification Tuning

Common mistakes AI assistants make when an admin asks for chatter-noise reduction. Avoid these when
generating recommendations. Several of them are *confidently plausible* — they map cleanly onto the
Chatter UI or onto other Salesforce features — which is exactly why they survive review.

---

## Anti-Pattern 1: Recommending org-level disable as the first move

**What the LLM generates:** "Go to Setup → Chatter Settings and uncheck Enable Chatter to fix the
email volume," or the same move in metadata form, `enableCollaborationEmail = false`.

**Why it's wrong:**

- `enableCollaborationEmail = false` stops all collaboration email notification (api_meta.txt
  L112391–112392), which makes every per-user and per-group preference below it inert. It ends the
  complaint by ending the channel.
- Most "noise" complaints trace to a small set of automated sources, not to Chatter itself. A
  `SELECT Type, COUNT(Id) FROM FeedItem ... GROUP BY Type` finds them in one query.

**What to do instead:** Inventory automated `FeedItem` sources first, then Feed Tracking, then
per-group frequency. Reach for `enableChatter` or `enableCollaborationEmail` only when the real
decision is "we do not use this feature," and say that is the decision.

---

## Anti-Pattern 2: Inventing a `Limited` digest frequency

**What the LLM generates:**

```apex
// WRONG on two counts
update new CollaborationGroupMember(Id = m.Id, NotificationFrequency = 'Limited');
update new CollaborationGroupMember(Id = m.Id, NotificationFrequency = 'L');
```

…usually accompanied by a confident description: "Limited sends email only for posts that @mention
you or threads you already commented on, cutting volume 80–95%."

**Why it's wrong:** `CollaborationGroupMember.NotificationFrequency` is a Restricted picklist whose
documented values are exactly "`D`—Daily, `W`—Weekly, `N`—Never, `P`—On every post"
(object_reference.txt L67515–67518). There is no `L` and no `Limited`, and no behaviour matching that
description is documented anywhere in the Object Reference. The failure is worse than a typo: whole
tuning plans get approved on the strength of a volume reduction that the field cannot deliver.

**What to do instead:** Use the four real values, and pick per group purpose:

```apex
update new CollaborationGroupMember(Id = m.Id, NotificationFrequency = 'W');
```

---

## Anti-Pattern 3: Writing a `ChatterEmailsMD.settings` full of `emailOn*` elements

**What the LLM generates:**

```xml
<!-- None of these elements exist. This file will not deploy. -->
<ChatterEmailsMDSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <emailOnAllPosts>false</emailOnAllPosts>
    <emailOnFollowedPosts>false</emailOnFollowedPosts>
    <emailOnAtMention>true</emailOnAtMention>
    <defaultDigestFrequency>Weekly</defaultDigestFrequency>
</ChatterEmailsMDSettings>
```

**Why it's wrong:** The complete documented field table for the type is ten booleans —
`enableChatterDigestEmailsApiOnly`, `enableChatterEmailAttachment`, `enableCollaborationEmail`,
`enableDisplayAppDownloadBadges`, `enableEmailReplyToChatter`, `enableEmailToChatter`, and four
`noQn*` Chatter Questions flags (api_meta.txt L112383–112418). Nothing per-event; nothing about
frequency. The invention is well-formed and semantically plausible, which is why it gets committed.
The near-miss that makes it stickier: `ChatterAnswersSettings` (api_meta.txt L112253 onward) really
does have `emailFollowersOnReply` and `emailOwnerOnReply` — for the unrelated Chatter Answers forum.

**What to do instead:** Per-event email control lives on the `User` record
(`UserPreferencesDisable*Email`, object_reference.txt L296132–296300) and default frequency lives on
`User.DefaultGroupNotificationFrequency` (L295156–295172). Both are data, moved by Data Loader. Run
`scripts/check_chatter_notification_tuning.py --manifest-dir <root>` — `CNT-SETTINGS-ELEMENT` names
any invented element before the deploy does.

---

## Anti-Pattern 4: Asserting that `FeedItem.Visibility` defaults to `AllUsers`

**What the LLM generates:** "`Visibility` defaults to `AllUsers`, exposing every automated post to
Community users — add `fi.Visibility = 'InternalUsers'` everywhere."

**Why it's wrong:** For record posts the documented default is already the safe one: "For record
posts, `Visibility` is set to `InternalUsers` for all internal users by default" (object_reference.txt
L136430–136431). The advice sends an audit at code that is already correct while the real exposures —
an explicit `AllUsers` assignment, or a post whose parent is a user or group — go unexamined. Worse,
setting the field unconditionally breaks in orgs without Experience Cloud, because it exists only "if
digital experiences is enabled for your org" (L136412–136414).

**What to do instead:** Audit for explicit `AllUsers` and for non-record parents. Note also that
"`Visibility` can be updated on record posts" and "the `Update` property is supported only for feed
items posted on records" (L136432–136435) — a remediation script that tries to update `Visibility` on
a profile post has no effect.

---

## Anti-Pattern 5: Confusing Custom Notifications with Chatter, and mis-sizing the batch

**What the LLM generates:** "Use Notification Builder to send a Chatter post," "post to the user's
bell via `FeedItem`," or a correct migration chunked at 2,000 recipients per `send()` call.

**Why it's wrong:**

- A `FeedItem` does not produce a bell notification; the bell is `Messaging.CustomNotification`, a
  separate API with separate metadata (`CustomNotificationType`, api_meta.txt L41769–41934).
- The `send(Set<String> users)` maximum is **500 values**, not 2,000: "Values can be combined in a
  set, up to the maximum of 500 values" (apexrefguide.txt L166776–166778).

**What to do instead:** Chunk at 500 — or exploit the recipient-type expansion, since a `GroupId` or
`QueueId` costs one value and reaches every active member (L166766–166776). Add the Send Custom
Notifications permission to the running user (L166591–166594) and always set a target: with neither
`targetID` nor `targetPageRef`, `send()` throws, and the documented dummy is
`000000000000000AAA` (L166571–166576).

---

## Anti-Pattern 6: Blaming `LastModifiedDate` feed tracking

**What the LLM generates:** "Your Account feed posts on every save because Feed Tracking is enabled on
`LastModifiedDate` — remove it."

**Why it's wrong:** That configuration cannot exist. Feed tracking is supported only on standard
fields "to which you can add help text or enable history tracking or Chatter feed tracking. Other
standard fields aren't supported, including system fields (such as `CreatedById` or
`LastModifiedDate`) and autonumber fields" (api_meta.txt L2164–2167). The admin will go looking for a
checkbox that is not there and lose trust in the rest of the analysis.

**What to do instead:** Point at whatever the retrieved `*.field-meta.xml` files actually carry
`trackFeedHistory` on, and prioritise fields that change without a human event behind them — roll-up
summaries and nightly formulas are the usual suspects. **UNVERIFIED (2026-09-05):** no supplied guide
states whether roll-up or formula fields accept `trackFeedHistory`; read the metadata rather than
asserting the category. And be honest about the magnitude: a `TrackedChange` feed
item is "a change **or group of changes** to a tracked field" (object_reference.txt L136377–136378),
so removing eight tracked fields does not divide the volume by eight.

---

## Anti-Pattern 7: Recommending a `FeedItem` purge as "cleanup"

**What the LLM generates:** "Run a daily batch deleting `FeedItem` older than 30 days to keep feeds
clean."

**Why it's wrong:**

- `FeedItem` is the audit trail for Chatter-recorded business events — approvals (`ApprovalPost`),
  tracked changes, case milestones (`MilestoneEvent`) all live there (object_reference.txt
  L136330–136402).
- Deleting removes the record from the data layer, not just from a feed view.
- "Feed full of automated posts" is a *source* problem. Deleting the output while the source keeps
  running guarantees the batch runs forever.
- The related `FeedTrackedChange` rows cannot be handled independently in any case: "You can't
  explicitly create or delete a `FeedTrackedChange` record" (L136545–136546).

**What to do instead:** Migrate transient automated posts to Custom Notifications, which write no
`FeedItem` at all. Leave durable business-event posts in place.

---

## Anti-Pattern 8: Reaching for the Tooling API to change user email preferences

**What the LLM generates:** "There's no admin UI for this — you'll need to update
`UserPreferencesEmailNotificationsToMe` via the Tooling API / Salesforce Inspector."

**Why it's wrong:** Two errors in one sentence. The field name is invented; the real family is
`UserPreferencesDisable*Email` (object_reference.txt L296132–296300). And every member of that family
is a plain field on the `User` sObject with `Create, Filter, Update` properties — ordinary Data Loader,
`sf data update`, or Apex DML reaches them. Sending an admin to the Tooling API makes a routine bulk
update look like an exotic intervention, which is often enough for the change to be abandoned.

**What to do instead:** A two-column CSV and `sf data update bulk --sobject User`. Then remember the
polarity: these fields are disable-flags described from the `false` side, so `true` suppresses and
`false` sends (L296220–296227).

---

## Anti-Pattern 9: Confusing `EntitySubscription` with feed visibility, and trying to update it

**What the LLM generates:** "To stop chatter notifications for a user, update their
`EntitySubscription` records," or an org-wide follow inventory query with no `LIMIT` and no
`ParentId` / `SubscriberId` filter.

**Why it's wrong:**

- `EntitySubscription` is the follow relationship. Notifications also flow from group membership
  (`CollaborationGroupMember`), @mentions, approval posts, and the bell — none of which are
  `EntitySubscription` rows.
- The object has no `update()` call at all: "`create()`, `delete()`, `describeSObjects()`,
  `getDeleted()`, `getUpdated()`, `query()`, `retrieve()`" (object_reference.txt L111058–111060).
  Unfollowing is a delete.
- The unconstrained query is documented as undefined: without View All Data you must "specify a
  `LIMIT` clause of 1,000 records or fewer," and with user sharing on, an unconstrained query's
  "behavior at run time is undefined, meaning the result set can be incomplete or inconsistent from
  invocation to invocation" (L111176–111192).

**What to do instead:** Identify the *channel* of the unwanted notification first — followed records,
group activity, approvals, or bell — then tune the matching surface. If it really is follows, delete
the rows, run as a View All Data holder, and constrain by `ParentId` or `SubscriberId` anyway.
