# Well-Architected Notes — Chatter Notification Tuning

## Relevant Pillars

- **Operational Excellence** — Notification noise is a productivity tax that nobody owns, so it
  compounds. The measurable form of the problem is a `FeedItem` volume distribution by `Type` and a
  `CollaborationGroupMember.NotificationFrequency` distribution; both are one SOQL query each
  (`references/metadata-examples.md` § 8). Tuning is governance, and governance works when it is
  paired with automated detection (`scripts/check_chatter_notification_tuning.py`) and a
  re-measurement loop rather than a one-time cleanup.
- **Security** — `FeedItem.Visibility` is the field that decides whether an internal post reaches
  Experience Cloud users. The platform's default is the safe one for record posts — "For record posts,
  `Visibility` is set to `InternalUsers` for all internal users by default" (object_reference.txt
  L136430–136431) — so the security work here is auditing the *explicit* `AllUsers` assignments and
  the posts whose parent is not a record, not adding a default that already exists. A second, quieter
  exposure: the field only exists "if digital experiences is enabled for your org" (L136412–136414),
  so code that sets it unconditionally breaks in orgs without Experience Cloud.

## Architectural Tradeoffs

| Tradeoff | Why it matters |
|---|---|
| Custom Notification (bell) vs Chatter feed post | Bell is transient and recipient-targeted; feed is durable and visible to followers. Use bell for "you should know" alerts and feed for collaborative threads and events with audit value. Treating them as substitutes creates either lost alerts or audit-trail gaps. The bell side has a hard fan-out shape: `send()` takes at most 500 values, but a single `GroupId` or `QueueId` counts as one and expands to all active members (apexrefguide.txt L166762–166778). |
| Which of the four digest frequencies is the default | The design space is exactly `P` / `D` / `W` / `N` (object_reference.txt L67515–67518). `W` is a defensible default heartbeat, `D` for broadcast groups, `N` for social groups, and `P` only with a written reason — because `P` self-disables above 10,000 members in a site and silently switches everyone to Daily (L67519–67522). Set it per group, not org-wide. |
| Change the inherited default vs change existing members | `User.DefaultGroupNotificationFrequency` governs what a user inherits *when they join a group* (L295160–295163) and is not retroactive. Fixing it is cheap, uncontroversial, and only helps future joins. Rewriting existing `CollaborationGroupMember` rows helps immediately but overrides choices people made, and needs Modify All Data (L67512–67513). Most orgs need both, in that order, and should say which they are doing. |
| Suppress at the source (automation) vs at the surface (frequency) | An 800-post-per-quarter Flow is not a digest problem; no frequency setting makes those posts worth reading. Migrating it to `customNotificationAction` (api_meta.txt L68710) removes the rows entirely. Frequency tuning is the right lever only once the remaining volume is genuine human collaboration. |
| Feed Tracking breadth vs feed usefulness | Every tracked field can produce a `TrackedChange` feed item, but the type is "a change *or group of changes* to a tracked field" (object_reference.txt L136377–136378) — so field count is a proxy for noise, not a multiplier. Track qualitative state (owner, status, stage). Roll-ups and formulas are the real offenders because they change with no human event behind them. |
| Org-wide master switch vs per-surface dials | `enableCollaborationEmail = false` (api_meta.txt L112391–112392) stops all collaboration email and makes every per-user and per-group preference inert. It ends the complaint and ends the channel. Reach for it only when the decision genuinely is "we do not use this," and record it as that decision rather than as a volume fix. |

## Anti-Patterns

1. **Tuning at the user level when the noise is automated** — telling users to filter their inbox does
   not fix a Flow posting 800 times a quarter. Query `FeedItem` by `Type` and by `CreatedById` first;
   tune user-level controls last.
2. **Migrating *every* feed post to Custom Notification** — Custom Notifications leave no record.
   Approval outcomes, owner changes and similar durable events belong on the feed. Migrate the
   transient alerts only.
3. **Tracking roll-up and formula fields** — they recompute on dependent updates, so they generate feed
   activity with no human event behind it. (Tracking `LastModifiedDate` is not on this list because
   the platform does not allow it — api_meta.txt L2164–2167.)
4. **Setting one org-default frequency without per-group review** — a blanket `N` means broadcast-group
   announcements reach nobody; a blanket `P` floods inboxes and, past 10,000 members in a site, gets
   silently reverted to `D` anyway.
5. **Designing around a setting that does not exist** — `Limited`, an `emailOnAllPosts` settings
   element, and a "default digest frequency" in `ChatterEmailsMD.settings` are all plausible and none
   of them is real. Check the field table before the plan gets approved, not after the deploy fails.

## Official Sources Used

- Metadata API Developer Guide (v62) — `ChatterEmailsMDSettings` field table and sample definition,
  api_meta.txt L112368–112445 (§ the ten documented email elements; the absence of any per-event or
  default-frequency element — gotcha 8, metadata-examples § 1) —
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide (v62) — `ChatterSettings` field table, sample definition and manifest
  sample, api_meta.txt L112452–112648 (§ `enableApprovalRequest` default `false` and its per-user
  opt-out — gotcha 12; `allowSharingInChatterGroup` Removed — checker `CNT-SETTINGS-REMOVED`;
  the package.xml `Settings` shape)
- Metadata API Developer Guide (v62) — `CustomNotificationType`, api_meta.txt L41769–41934
  (§ `.notiftype` suffix, `notificationtypes/` directory, API 46.0+, `desktop`/`mobile` as the only
  channels with `slack` reserved, no wildcard support — metadata-examples § 3, examples § 3)
- Metadata API Developer Guide (v62) — `trackFeedHistory` L43668–43672, `enableFeeds` L42035–42039,
  `recordTypeTrackFeedHistory` L42234–42241, and the standard-field restriction at L2164–2167
  (§ the `enableFeeds` prerequisite — gotcha 7, checker `CNT-TRACK-NO-FEEDS`; system fields cannot be
  feed-tracked — gotcha 6)
- Metadata API Developer Guide (v62) — Flow `InvocableActionType` values, api_meta.txt L68655
  (`chatterPost`) and L68710 (`customNotificationAction`, API 46.0+), plus the `chatterPost`
  `actionCalls` sample at L73247–73273 (§ the migration in examples § 3 and the checker's Flow scan)
- Object Reference (v62) — `CollaborationGroupMember`, object_reference.txt L67430–67540
  (§ `NotificationFrequency` values `D`/`W`/`N`/`P` and the Modify All Data restriction — gotchas 1
  and 2; the 10,000-member auto-switch — gotcha 3) —
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Object Reference (v62) — `User`, object_reference.txt L295156–295207 and L296124–296300
  (§ `DefaultGroupNotificationFrequency` default `N` with the pre-API-22 `D` carve-out and
  `DigestFrequency` default `D` — examples § 1; the `UserPreferencesDisable*Email` family, their
  `Create, Filter, Update` properties and their inverted polarity — gotcha 9, examples § 5)
- Object Reference (v62) — `FeedItem`, object_reference.txt L136330–136560 (§ `Type` values including
  `TrackedChange` as "a change or group of changes"; `Visibility` defaulting to `InternalUsers` for
  record posts — gotcha 5; the View All Data requirement for direct queries and the System Modstamp
  restriction — examples § 6; the trigger-strips-mentions behaviour — gotcha 11)
- Object Reference (v62) — `EntitySubscription`, object_reference.txt L111051–111200 (§ no `update()`
  call, the 1,000-record LIMIT without View All Data, the `ParentId`/`SubscriberId` constraint
  requirement, and the 500-record visibility scan — gotcha 10)
- Apex Reference Guide (v62) — `Messaging.CustomNotification`, apexrefguide.txt L166555–166800
  (§ the 500-value `send()` maximum, the `GroupId`/`QueueId` recipient expansion, the Send Custom
  Notifications permission, and the `targetID` dummy-value requirement — gotcha 4) —
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Apex Developer Guide (v62) — Outbound Email limits, apexdev.txt L19959–19983 (§ the 5,000/day cap
  counts *external* addresses and "You can send an unlimited amount of email through the UI to your
  org's internal users" — which is why internal Chatter digest volume is not the daily-limit problem
  it is often assumed to be)
- Salesforce Developer Limits and Allocations Quick Reference, salesforce_app_limits_cheatsheet.txt —
  **negative result**: no Chatter feed, follow, group-email or digest limit appears anywhere in it.
  The only adjacent entry is the Connect REST API rate limit at L706–716 (per user, per application,
  per hour; 503 on exceed), which bounds programmatic feed reads, not notification volume. Do not
  quote a "Chatter limit" from this document; there isn't one.
- Salesforce Well-Architected — Operational Excellence —
  https://architect.salesforce.com/docs/architect/well-architected/guide/operational-excellence.html
