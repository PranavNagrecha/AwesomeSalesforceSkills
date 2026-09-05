# Chatter Notification Tuning — Work Template

Fill this in as you run workflow steps 1–4 in `SKILL.md`. It is the artefact the change record
points at.

## Scope

**Skill:** `chatter-notification-tuning`

**Request summary:**

**Who is complaining, and about which channel** (feed volume / email volume / bell / all three):

---

## 1. Diagnosis — where the volume actually comes from

Run as a View All Data holder (`FeedItem` direct queries require it — object_reference.txt
L136505–136507).

```sql
SELECT Type, COUNT(Id) posts
FROM FeedItem
WHERE CreatedDate = LAST_N_DAYS:30
GROUP BY Type
ORDER BY COUNT(Id) DESC
```

| `FeedItem.Type` | 30-day count | Routes to |
|---|---|---|
| `TrackedChange` | | Feed Tracking pruning — workflow step 3 |
| `TextPost` (automation ids) | | Flow / Apex migration — workflow step 4 |
| `TextPost` (human ids) | | Digest frequency, not suppression — step 5 |
| `ApprovalPost` | | `enableApprovalRequest` — gotcha 12 |
| other | | |

**Checker baseline** — paste the finding codes and counts:

```
python3 scripts/check_chatter_notification_tuning.py --manifest-dir force-app/main/default
```

---

## 2. Answers to the Questions to Ask table

| Question | Answer |
|---|---|
| Which channel is loud — feed, email, or bell? | |
| Who holds Modify All Data, and are they running the load? | |
| Which of the four frequencies (`P`/`D`/`W`/`N`) is the intended default, and why not `N`? | |
| Is the volume automated or human? | |
| Are we changing what new joins inherit, or rewriting existing members' choices — or both? | |
| Does the org have Experience Cloud / digital experiences enabled? | |
| What does "quiet enough" look like, measured? | |

---

## 3. The policy

`notification-policy.json` — lint with
`python3 scripts/check_chatter_notification_tuning.py --policy notification-policy.json --group-inventory groups.csv`

| Scope | Frequency | Reason |
|---|---|---|
| Org default (`User.DefaultGroupNotificationFrequency`) | | |
| Broadcast / announcement groups | | |
| Project groups | | |
| Social / interest groups | | |

**If any row is `P`:** the written justification, and the member-count headroom against the
10,000-member auto-switch (gotcha 3):

---

## 4. Changes, by surface

| Surface | Artefact | Change | Reversible? |
|---|---|---|---|
| `Chatter.settings` | | | |
| `ChatterEmailsMD.settings` | | | |
| Feed Tracking (`enableFeeds` + `trackFeedHistory`) | | | |
| `CustomNotificationType` + Flow `actionType` | | | |
| `CollaborationGroupMember` CSV | | | |
| `User` CSV | | | |

**Deliberate non-changes** — what you looked at and left alone, and why (this is the half that gets
questioned later):

---

## 5. Deviations and open items

Record anything that departed from the workflow, any `UNVERIFIED` claim you had to act on, and any
finding the checker raised that you accepted rather than fixed.

---

## 6. Re-measure

Date to re-run step 1: (two weeks after the change)

| Metric | Before | After | Target |
|---|---|---|---|
| 30-day `FeedItem` count by dominant `Type` | | | |
| Members on `P` | | | |
| Active users with `UserPreferencesDisableAllFeedsEmail = false` | | | |
| Checker ERROR/WARN count | | | |
