# Gotchas — Chatter Notification Tuning

Non-obvious platform behaviors that bite admins during chatter-noise tuning.

---

## Gotcha 1: Org-level email-off doesn't reach users who saved preferences

**Symptom:** Admin disables Chatter Email Notifications at the org level. Users still receive emails.

**Why:** Once a user saves My Settings → Email → Email Notifications even once, the per-user `UserPreferencesEmail*` flags become the source of truth and override org defaults. The org-level setting only affects the *default starting state* for users who haven't yet visited the page.

**Fix:** Either (a) communicate and ask users to re-save their preferences, or (b) update `User.UserPreferencesEmail*` fields via Tooling API for the affected users. There is no admin-side "reset all user preferences" button.

---

## Gotcha 2: `NotificationFrequency` codes are short strings, not the picklist labels

**Symptom:** Admin writes a Flow / Apex update setting `CollaborationGroupMember.NotificationFrequency = 'Limited'`. The update silently fails or sets nothing visible.

**Why:** The stored value is a one-character code: `D` Daily, `W` Weekly, `P` Each post, `N` Never, `L` Limited. The UI displays the long form but the field accepts the code.

**Fix:** Always set the code, not the label.

---

## Gotcha 3: Disabling Feed Tracking does not delete old `FeedItem` records

**Symptom:** Admin removes a noisy field from Feed Tracking. The old change posts continue to clutter feeds for years.

**Why:** Feed Tracking is forward-only — disabling it stops *future* `FeedItem` creation but past records persist as historical audit. The field is unindexed for purge by design.

**Fix:** If you must purge old `TrackedChange`-type FeedItems, write a one-time Apex batch with explicit `WHERE Type = 'TrackedChange' AND CreatedDate < ...` filters, run in a sandbox first, and document for compliance. There's no UI for this.

---

## Gotcha 4: Custom Notifications have a 2,000 recipient cap per call

**Symptom:** Admin migrates a high-volume Chatter announcement to a Custom Notification. Notification fails for some recipients with no error.

**Why:** `Messaging.CustomNotification.send(Set<String> userIds)` accepts up to 2,000 user IDs per call. Larger recipient sets need batching.

**Fix:** Chunk the recipient set into 2,000-user batches and call `send()` once per batch. There is no `sendBulk` overload.

---

## Gotcha 5: `Visibility = AllUsers` on a `FeedItem` lets external users see it

**Symptom:** Admin posts an internal-only announcement via Flow Post to Chatter. Customer Community users see the post.

**Why:** `FeedItem.Visibility` defaults to `AllUsers`, which includes Experience Cloud / Customer Community users with feed access on the parent record. Only `InternalUsers` excludes them.

**Fix:** Always set `Visibility = 'InternalUsers'` on automated `FeedItem` inserts unless the post is *explicitly* meant for external users. Audit existing automated posts for this default.

---

## Gotcha 6: Auto-follow rules survive object deletion

**Symptom:** Admin deletes a custom object that had auto-follow enabled. Users who were auto-followed continue to receive notifications. The notifications point to deleted records.

**Why:** `EntitySubscription` records are not cascade-deleted when their parent object's metadata is removed. The subscription points at an orphaned record ID and produces zombie notifications.

**Fix:** Before deleting an object that had auto-follow / Feed Tracking, run a cleanup batch to delete `EntitySubscription` records pointing at that object's records.

---

## Gotcha 7: `Each post` group emails count toward your daily Email Single Volume limit

**Symptom:** Org hits the daily single-email limit (5,000 / 1,000 depending on edition) mysteriously. Most of the volume is Chatter group `Each post` digests.

**Why:** Chatter group emails count against the org's `EmailSingleVolume` daily limit. A group with 50 members and 30 posts/day on `Each post` = 1,500 emails just from that group.

**Fix:** This is the strongest argument for `Limited` digest. Estimate volume (members × post rate × frequency) before turning on email-heavy defaults.

---

## Gotcha 8: Disabling Chatter org-wide is not a one-click revert

**Symptom:** Org tries to disable Chatter entirely (e.g. for highly regulated tenants). Re-enabling later loses historical feed data.

**Why:** Disabling Chatter at the org level is supported but Salesforce documents that re-enabling is not a fully-symmetric operation — some Feed Tracking history may be lost or require resync.

**Fix:** Treat Chatter on/off as a one-way decision. If unsure, audit the noise and tune defaults instead of disabling.
