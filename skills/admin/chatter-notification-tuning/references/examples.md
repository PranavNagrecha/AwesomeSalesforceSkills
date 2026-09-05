# Examples — Chatter Notification Tuning

Concrete, before/after examples for each tuning lever, worked as scenarios. Apply in the order shown —
the surfaces layer, and fixing the source before the symptom saves the later steps.

Deployable XML, package.xml, `sf` commands and the CSV column tables live in
`references/metadata-examples.md`; this file is the reasoning that decides what goes in them.

---

## Example 1 — Org-level: the new-hire default is a `User` field, not a settings checkbox

**Symptom:** Every new hire complains in their first week about Chatter email volume. The admin goes
looking for the org setting that controls the starting digest frequency and cannot find it.

**Why they cannot find it:** There isn't one. `ChatterEmailsMDSettings` has ten boolean elements and
no frequency element at all (api_meta.txt L112383–112418). What new users inherit is the
**defaulted-on-create value of a `User` field**:

| Field | Values | Documented default | Source |
|---|---|---|---|
| `User.DefaultGroupNotificationFrequency` | `P` / `D` / `W` / `N` | `N` — but `D` for Professional, Enterprise, Unlimited and Developer orgs **that existed before API version 22.0** | object_reference.txt L295156–295172 |
| `User.DigestFrequency` | `D` / `W` / `N` | `D` | L295200–295207 |

The second column of that table is the whole finding. A long-lived Enterprise org is still handing
every new user `D` for group joins and `D` for the personal digest, twelve years after the platform
default changed for everyone else. Nobody set that; it is inherited history.

**Diagnose it before you change it:**

```sql
-- What are new users actually inheriting? Look at the most recent ones.
SELECT DefaultGroupNotificationFrequency, DigestFrequency, COUNT(Id) users
FROM User
WHERE IsActive = true AND CreatedDate = LAST_N_DAYS:90
GROUP BY DefaultGroupNotificationFrequency, DigestFrequency
```

**Before** — a pre-v22 Enterprise org, 90-day cohort:

```text
DefaultGroupNotificationFrequency  DigestFrequency  users
D                                  D                 47      ← inherited, nobody chose this
W                                  D                  3
N                                  N                  1
```

**After** — the onboarding load sets the two fields explicitly, so the value is a decision:

```text
DefaultGroupNotificationFrequency  DigestFrequency  users
W                                  W                 47
N                                  N                  4
```

**What this does not do:** it does not touch anyone already in the org. `DefaultGroupNotificationFrequency`
is the frequency inherited "when the user joins groups" (L295160–295163) — it is not retroactive to
existing memberships, which are `CollaborationGroupMember` rows and need Example 2.

---

## Example 2 — Group-level: bulk digest frequency, and who is allowed to run it

**Symptom:** 200 Chatter groups exist, most owned by long-departed users, and the member rows are a
mix of `P` and `D`.

**The permission gate comes first.** `CollaborationGroupMember.NotificationFrequency` "can only be set
by the member or users with the 'Modify All Data' permission" (object_reference.txt L67510–67513).
Group ownership does not cover it, and neither does the `Admin` `CollaborationRole`, which grants
member and settings management but not this (L67462–67469). Confirm who is running the load before
writing it.

**Anonymous Apex to move project-group members to weekly, leaving deliberate opt-outs alone:**

```apex
Set<Id> projectGroupIds = new Map<Id, CollaborationGroup>([
    SELECT Id
    FROM CollaborationGroup
    WHERE Name LIKE 'Project-%'
      AND CollaborationType = 'Public'
      AND IsArchived = false
]).keySet();

List<CollaborationGroupMember> updates = new List<CollaborationGroupMember>();
for (CollaborationGroupMember m : [
    SELECT Id, NotificationFrequency
    FROM CollaborationGroupMember
    WHERE CollaborationGroupId IN :projectGroupIds
]) {
    // Leave 'N' alone: someone chose silence. Leave 'W' alone: already there.
    if (m.NotificationFrequency != 'N' && m.NotificationFrequency != 'W') {
        m.NotificationFrequency = 'W';
        updates.add(m);
    }
}
if (!updates.isEmpty()) {
    List<Database.SaveResult> results = Database.update(updates, false);
    Integer failed = 0;
    for (Database.SaveResult r : results) {
        if (!r.isSuccess()) { failed++; }
    }
    System.debug('Updated ' + (updates.size() - failed) + ', failed ' + failed);
}
```

**The four valid values, and the two that do not exist:** `D` Daily, `W` Weekly, `N` Never,
`P` On every post (L67515–67518). There is no `L`, and no `Limited`. Any plan built on a
"send only for @mentions and threads I already joined" frequency is built on a value the field does
not have — see `references/gotchas.md` gotcha 1. Partial-success DML (`Database.update(list, false)`)
matters here because it surfaces the permission failure per row instead of rolling the whole batch
back on the first one.

---

## Example 3 — Migrate a noisy Flow `chatterPost` to a Custom Notification

**Symptom:** A Flow posts to Chatter every time an Opportunity moves to Closed Won. 800 closed-won
opportunities per quarter = 800 feed posts and 800 `FeedItem` rows.

**Before (Flow), in the shape the Metadata API guide's own sample uses (api_meta.txt L73247–73273):**

```xml
<actionCalls>
    <name>Post_to_Owner_Feed</name>
    <label>Post to Owner Feed</label>
    <actionName>chatterPost</actionName>
    <actionType>chatterPost</actionType>
    <flowTransactionModel>CurrentTransaction</flowTransactionModel>
    <inputParameters>
        <name>text</name>
        <value>
            <elementReference>chatterMessage</elementReference>
        </value>
    </inputParameters>
    <inputParameters>
        <name>subjectNameOrId</name>
        <value>
            <elementReference>$Record.OwnerId</elementReference>
        </value>
    </inputParameters>
    <nameSegment>chatterPost</nameSegment>
    <versionSegment>1</versionSegment>
</actionCalls>
```

**After (Flow):** the same element with `actionType` `customNotificationAction` — "Sends a custom
notification. This value is available in API version 46.0 and later" (api_meta.txt L68710) — pointed
at the `CustomNotificationType` whose XML is in `references/metadata-examples.md` § 3.

**One-time setup:** deploy `Opportunity_Won_Internal.notiftype-meta.xml`. Its only delivery channels
are `desktop` and `mobile`, both `Required` booleans; `slack` is "Reserved for future use"
(api_meta.txt L41802–41812). There is no "in-app" channel — a generated file with one will not
deploy.

**Effect:** 800 `FeedItem` rows per quarter eliminated. Recipients still get the alert. The
opportunity keeps its standard Chatter feed for actual collaboration; only the automated post goes
away.

**What to keep on the feed instead:** anything whose value is that it stays there. Approval outcomes,
owner changes, escalations — those are `TrackedChange` and `ApprovalPost` feed items with audit value
(object_reference.txt L136348, L136377–136378). A Custom Notification is transient by design and
leaves no record.

---

## Example 4 — Prune Feed Tracking on Account

**Symptom:** The Account feed shows a post on nearly every save.

**Where it lives:** Setup → Object Manager → Account → Feed Tracking, and in source at
`objects/Account/Account.object-meta.xml` (`enableFeeds`) plus each
`objects/Account/fields/*.field-meta.xml` (`trackFeedHistory`).

**Rule out the folklore first.** "Someone tracked `LastModifiedDate`" cannot be the cause: system
fields such as `CreatedById` and `LastModifiedDate` are not eligible for feed tracking at all
(api_meta.txt L2164–2167). If it is in the tracked list in someone's notes, the notes are wrong.

**Before** — twelve tracked fields on Account:

```text
Owner                  ← keep: qualitative state, low churn
Industry               ← keep: qualitative state, low churn
Type                   ← keep: qualitative state, low churn
Account_Status__c      ← keep: the field the business actually watches
AnnualRevenue          ← drop: numeric, flaps on every integration sync
NumberOfEmployees      ← drop: numeric, flaps on every integration sync
BillingStreet          ← drop: address components, five fields of one change
BillingCity            ← drop
BillingState           ← drop
BillingPostalCode      ← drop
Open_Cases__c          ← drop: roll-up, recomputes on every child insert
Last_Activity_Score__c ← drop: formula recalculated nightly
```

**After** — four:

```text
Owner
Industry
Type
Account_Status__c
```

The two that matter most are the roll-up and the nightly formula: they change without anyone touching
the Account, so they generate feed activity with no human event behind it.

**Migration note:** removing fields from Feed Tracking is expected to stop future `TrackedChange`
items without removing past ones. **UNVERIFIED (2026-09-05):** no supplied guide states what happens
to existing `FeedItem` rows when `trackFeedHistory` goes `false`; `trackFeedHistory` is documented
only as an enable/disable boolean (api_meta.txt L43668–43672). Query
`SELECT COUNT(Id) FROM FeedItem WHERE Type = 'TrackedChange'` before and a day after the change
rather than assuming either outcome. Note also that `TrackedChange` is documented as "a change
**or group of changes** to a tracked field" (object_reference.txt L136377–136378) — the twelve fields
above were not producing twelve feed items per save, so expect the volume drop to be smaller than the
field-count drop suggests. Measure it, do not project it.

**Deploy note:** package the object file with the field files. `trackFeedHistory` requires
`enableFeeds` on the object (api_meta.txt L43668–43672), and the checker's `CNT-TRACK-NO-FEEDS`
catches the missing half.

---

## Example 5 — Reset per-user email preferences at scale

**Symptom:** A tuning change lands and a cohort of long-tenured users keeps getting everything.

**Where their state lives:** the `UserPreferencesDisable*Email` family on the `User` record —
`UserPreferencesDisableAllFeedsEmail`, `...DisableBookmarkEmail`, `...DisableChangeCommentEmail`,
`...DisableEndorsementEmail`, `...DisableFileShareNotificationsForApi`, `...DisableFollowersEmail`,
`...DisableLaterCommentEmail`, `...DisableLikeEmail`, `...DisableMentionsPostEmail`,
`...DisMentionsCommentEmail`, `...DisableMessageEmail`, `...DisableProfilePostEmail`,
`...DisableSharePostEmail`, `...DisCommentAfterLikeEmail` (object_reference.txt L296132–296300).

**Every one of them is `Create, Filter, Update` on the standard `User` sObject.** Ordinary Data
Loader or `sf data update` reaches them; no Tooling API is involved. And every one is a double
negative — the descriptions are written from the `false` side, e.g. "**When `false`**, the user
automatically receives email every time someone likes their post or comment" (L296220–296227). `true`
suppresses.

**Find the cohort before you touch it:**

```sql
SELECT Id, Username, Name, DigestFrequency,
       UserPreferencesDisableAllFeedsEmail,
       UserPreferencesDisableLikeEmail,
       UserPreferencesDisCommentAfterLikeEmail,
       UserPreferencesDisableMentionsPostEmail
FROM User
WHERE IsActive = true
  AND UserPreferencesDisableAllFeedsEmail = false
  AND UserPreferencesDisableLikeEmail = false
ORDER BY LastLoginDate DESC
```

**Then choose one of two paths, and say which one you chose:**

1. **Communicate.** Send the cohort the four settings and where they live. Slower, and the only path
   that leaves the users' own choices intact.
2. **Mass-update the low-signal flags only.** Suppress likes and comment-after-like — the two highest
   volume, lowest information events — and leave mentions and messages alone, because those are the
   ones a user would notice going missing:

   ```csv
   Id,UserPreferencesDisableLikeEmail,UserPreferencesDisCommentAfterLikeEmail
   005RM000000001AAA,true,true
   005RM000000002AAA,true,true
   ```

   ```bash
   sf data update bulk --sobject User --file users_quiet_likes.csv --target-org prod --wait 10
   ```

Path 2 overrides a preference the user may have set deliberately. Record it in change management,
name the two flags you touched and the ones you did not, and run it on a pilot cohort first. The
narrow column list *is* the safety argument — a CSV with fourteen columns in it is a different change.

---

## Example 6 — Audit query to find the worst feed-item generators

**Permission gate:** "If you're using API version 23.0 or later and have View All Data permission, you
can directly query for a `FeedItem`" (object_reference.txt L136505–136507). Run this as an admin; a
non-admin gets a partial answer without being told.

```sql
-- 30-day FeedItem volume by type: is this tracking noise or automation noise?
SELECT Type, COUNT(Id) posts
FROM FeedItem
WHERE CreatedDate = LAST_N_DAYS:30
GROUP BY Type
ORDER BY COUNT(Id) DESC
```

Read the answer as a routing decision:

| Dominant `Type` | What it means | Which example fixes it |
|---|---|---|
| `TrackedChange` | Feed Tracking configuration | Example 4 |
| `TextPost` from a small set of `CreatedById` | Flow or Apex automation | Example 3 |
| `TextPost` from many human ids | Real collaboration — this is not a noise problem | Example 2 (digest frequency), not suppression |
| `ApprovalPost` | `enableApprovalRequest` is `true` | `references/gotchas.md` gotcha 12 |

Then narrow to the automation sources:

```sql
SELECT CreatedById, CreatedBy.Name, COUNT(Id) posts
FROM FeedItem
WHERE CreatedDate = LAST_N_DAYS:30 AND Type = 'TextPost'
GROUP BY CreatedById, CreatedBy.Name
ORDER BY COUNT(Id) DESC
LIMIT 20
```

An integration or automation user at the top of that list is the Flow or Apex to migrate. One caveat
on any date-window query against this object: "For all API versions of `FeedItem`, you can't query a
`FeedItem` object using the System Modstamp filter" (object_reference.txt L136555–136556) — filter on
`CreatedDate`, which is what these do.
