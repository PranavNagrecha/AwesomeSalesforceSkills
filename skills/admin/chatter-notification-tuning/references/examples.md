# Examples — Chatter Notification Tuning

Concrete, before/after examples for each tuning lever. Apply in the order shown — settings cascade.

---

## Example 1 — Org-level: switch new-user default to "off"

**Symptom:** Every new hire complains in their first week about chatter email volume.

**Where it lives:** Setup → Email Settings (`Setup → Email → Email Settings`) → "Allow Email Notifications" checkbox + Setup → Chatter Settings → "Email Notifications" section.

**Before:**

```
Allow Chatter Email Notifications: ☑
   Personal Group Email Frequency (default): Daily
   Allow Coworker Invitations: ☑
```

**After:**

```
Allow Chatter Email Notifications: ☑    (leave on — users CAN opt in)
   Personal Group Email Frequency (default): Limited   ← key change
   Allow Coworker Invitations: ☐    ← stops auto-follow noise
```

The default group frequency only affects users who *haven't yet opened* their Email Notifications page. Existing users keep their saved preference.

---

## Example 2 — Group-level: bulk update digest frequency

**Symptom:** 200 Chatter groups exist, most owned by long-departed users, all defaulted to `Daily` digest.

**Anonymous Apex to set every project group's member preferences to `Limited`:**

```apex
List<CollaborationGroup> groups = [
    SELECT Id, Name
    FROM CollaborationGroup
    WHERE Name LIKE 'Project-%'
    AND CollaborationType = 'Public'
];
List<CollaborationGroupMember> updates = new List<CollaborationGroupMember>();
for (CollaborationGroupMember m : [
    SELECT Id, NotificationFrequency
    FROM CollaborationGroupMember
    WHERE CollaborationGroupId IN :new Map<Id, CollaborationGroup>(groups).keySet()
]) {
    if (m.NotificationFrequency != 'N') {
        m.NotificationFrequency = 'L';     // 'L' = Limited
        updates.add(m);
    }
}
if (!updates.isEmpty()) {
    update updates;
    System.debug('Updated ' + updates.size() + ' member preferences to Limited');
}
```

**Note:** `NotificationFrequency` codes are short strings: `D` Daily, `W` Weekly, `P` Each post, `N` Never, `L` Limited. The picklist label and stored code differ.

---

## Example 3 — Migrate a noisy Flow `Post to Chatter` to Custom Notification

**Symptom:** A Flow posts to Chatter every time an Opportunity moves to Closed Won. 800 closed-won opportunities per quarter = 800 feed posts cluttering the feed.

**Before (Flow):**

```
Element: Post to Chatter
  Target: TriggeringRecord.Owner.Id
  Message: "🎉 {!TriggeringRecord.Name} just closed at ${!TriggeringRecord.Amount}!"
  Visibility: AllUsers
```

**After (Flow):** Replace with `Send Custom Notification` action.

```
Element: Send Custom Notification (Action)
  Custom Notification Type: Opportunity_Won_Internal_Notification
  Recipients: TriggeringRecord.Owner.Id
  Title: "Opportunity won — congrats!"
  Body: "{!TriggeringRecord.Name} closed at ${!TriggeringRecord.Amount}"
  Target Page Reference: TriggeringRecord.Id
```

**Setup step (one-time):** Setup → Custom Notifications → New. Define `Opportunity_Won_Internal_Notification` with channels Desktop + Mobile + In-App.

**Effect:** 800 `FeedItem` rows per quarter eliminated. Recipients still get the alert (now in the bell). The opportunity itself still has its standard Chatter feed for actual collaboration — the automated post is the only thing that goes away.

---

## Example 4 — Prune Feed Tracking on Account

**Symptom:** Account feed shows a post on every save because someone enabled tracking on `LastModifiedDate` and `LastModifiedById`.

**Where it lives:** Setup → Object Manager → Account → Feed Tracking.

**Before:**

```
Tracked fields:
  - LastModifiedDate     ← noise, every save
  - LastModifiedById     ← noise, every save
  - Owner                ← keep, qualitative state
  - Industry             ← keep, qualitative state
  - Type                 ← keep, qualitative state
  - AnnualRevenue        ← debatable; numeric field, can flap
```

**After:**

```
Tracked fields:
  - Owner
  - Industry
  - Type
  - Account_Status__c    ← if it exists
```

**Migration note:** Removing fields from Feed Tracking does NOT delete past `FeedItem` records. Past noise is preserved (audit value) but new noise stops.

---

## Example 5 — Force user-level reset for "stuck on" users

**Symptom:** Org-level change to email-frequency doesn't take effect for power users who saved their Email Notifications page months ago.

**Why:** Once a user saves My Settings → Email → Email Notifications, a `User.UserPreferencesEmail*` flag is written and overrides the org default forever.

**Fix (admin):** there is no admin UI to "reset email preferences for user X." Two options:

1. **Communicate.** Send a one-time email with a screenshot showing the My Settings page and the recommended values. Most users will follow if the rationale is clear.
2. **Mass-update via the Tooling API.** `User.UserPreferencesEmailNotificationsToMe` and related fields can be updated by a system admin via Tooling API. Run a Salesforce Inspector / Workbench update on a flagged user list. Document this in change-management; users may not appreciate having their preferences reset without notice.

---

## Example 6 — Audit query to find the worst feed-item generators

```sql
-- 30-day FeedItem volume by parent type
SELECT Type, ParentId, COUNT(Id) cnt
FROM FeedItem
WHERE CreatedDate = LAST_N_DAYS:30
GROUP BY Type, ParentId
ORDER BY COUNT(Id) DESC
LIMIT 50
```

Run in Developer Console / Workbench. Top results are the records / patterns generating the most feed activity — usually 80% of the volume comes from <5 sources.

For automated-source identification (Flow vs Apex vs manual), filter on `Type = 'TextPost'` and `CreatedById = <integration user>` to find programmatic posts; manual posts come from real human user IDs.
