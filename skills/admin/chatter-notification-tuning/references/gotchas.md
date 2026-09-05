# Gotchas — Chatter Notification Tuning

Non-obvious platform behaviors that bite admins during chatter-noise tuning. Line references are into
the v62 PDFs listed in `well-architected.md` § Official Sources Used.

Group *lifecycle* gotchas — archiving, unlisted groups, ownership transfer, the 300-group cap, what
mass user deactivation does to follow relationships — live in
`admin/chatter-group-governance/references/gotchas.md`. This file is the notification half only.

---

## Gotcha 1: `Limited` is not a digest frequency, and the "L" code does not exist

**What happens:** A digest-tuning plan is built around setting group members to `Limited` — "email
only for @mentions and threads I already commented on." The Apex or Data Loader update sets
`NotificationFrequency = 'L'` (or `'Limited'`) and the rows fail, or the field simply does not hold
the value. The tuning plan's central promise — the 80–95% volume cut everyone signed off on — never
materialises because the setting it depends on is not a setting.

**When it occurs:** Any time the plan is drafted from a Chatter UI recollection or from an assistant's
output rather than from the Object Reference. `CollaborationGroupMember.NotificationFrequency` is a
**Restricted picklist** and its documented values are exactly four: "`D`—Daily, `W`—Weekly,
`N`—Never, `P`—On every post" (object_reference.txt L67510–67520). The sibling field
`User.DefaultGroupNotificationFrequency` carries the same four (L295156–295172), and
`User.DigestFrequency` carries three — `D`, `W`, `N` (L295200–295207). No `L`. No `Limited`.

**How to avoid:** The real four-value ladder is the whole design space, so choose per group purpose:
`N` for social groups nobody needs to be pushed, `W` as the default heartbeat, `D` for broadcast
groups, `P` only for a small, genuinely urgent group with a written reason. Run
`scripts/check_chatter_notification_tuning.py --policy notification-policy.json --member-csv ...`
before any load: `CNT-FREQ-VALUE` rejects `L`, `Limited`, and the long labels with a message naming
the code you meant.

---

## Gotcha 2: Owning a Chatter group does not let you set its members' digest frequency

**What happens:** A group owner is handed the tuning task, updates their members' rows, and the
update fails or silently touches nothing. The org concludes the field is read-only.

**When it occurs:** On every attempt by anyone who is not the member themselves and does not hold
Modify All Data. The field is documented as "Required. The frequency at which Salesforce sends Chatter
group email digests to this member. **Can only be set by the member or users with the 'Modify All
Data' permission**" (object_reference.txt L67510–67513). Group ownership and the `Admin`
`CollaborationRole` — which does grant "change member roles, edit group settings, add and remove
members, delete posts and comments" (L67462–67469) — do not include this.

**How to avoid:** Run the bulk frequency change as a Modify All Data holder, or do not run it at all
and instead change `User.DefaultGroupNotificationFrequency` so *future* joins inherit the right value
and ask existing members to change their own. Decide which of those two you are doing before you
write the CSV — they have different blast radii and different consent stories.

---

## Gotcha 3: `Each post` self-disables at 10,000 members and silently rewrites everyone to Daily

**What happens:** A large group is deliberately set to per-post email. It works, then one day
everybody is on a daily digest instead and nobody changed anything. The change is not in the audit
trail because no user made it.

**When it occurs:** In Experience Cloud sites, at the 10,000-member threshold: "In communities, the
`Email on every post` option is disabled once more than 10,000 members choose this setting for the
group. All members who had this option selected are automatically switched to Daily digests"
(object_reference.txt L67519–67522). The same sentence appears on
`NetworkMember.DefaultGroupNotificationFrequency` (L188325–188332).

**How to avoid:** Never design a notification guarantee on top of `P` for a group that can grow past
five figures. If the alert genuinely must reach everyone on every event, it is not a Chatter digest —
it is a Custom Notification or an email alert. The checker's `CNT-POLICY-EVERYPOST` makes you write
down *why* `P` is acceptable before the policy file passes, which is the point at which this usually
gets caught.

---

## Gotcha 4: `Messaging.CustomNotification.send()` takes 500 values, not 2,000

**What happens:** A broadcast Chatter post is migrated to a Custom Notification. The recipient set is
chunked at 2,000 — a number that circulates widely — and the sends fail.

**When it occurs:** On any recipient set larger than 500. The documented parameter is "A set of
recipient IDs… Values can be combined in a set, up to **the maximum of 500 values**"
(apexrefguide.txt L166762–166778). "Values", not "users": a single entry may be a `UserId`,
`AccountId` (account team), `OpportunityId` (opportunity team), `GroupId`, or `QueueId`, and the group
and queue forms expand to all *active* members on the platform's side.

**How to avoid:** Chunk at 500. Better, use the expansion: one `GroupId` or `QueueId` in the set
reaches every active member of that group or queue and costs one value, which turns most
"thousands of recipients" problems into a set of size one. Note also that `send()` requires the Send
Custom Notifications user permission and fails without it (L166591–166594), and that a notification
with neither `targetID` nor `targetPageRef` throws — set `targetID` to the documented dummy
`000000000000000AAA` when there is no natural target (L166571–166576).

---

## Gotcha 5: `FeedItem.Visibility` already defaults to `InternalUsers` for record posts — the leak is elsewhere

**What happens:** An audit is opened on the premise that every automated feed post is exposed to
Experience Cloud users by default. Weeks are spent adding `Visibility = 'InternalUsers'` to Apex that
already behaved correctly, while the actual exposure — a post whose parent is a user or a group, or
one that explicitly sets `AllUsers` — is never examined.

**When it occurs:** The documented default is the opposite of the folklore: "For record posts,
`Visibility` is set to `InternalUsers` for all internal users by default" (object_reference.txt
L136430–136431). Three further clauses matter: "External users can set `Visibility` only to
`AllUsers`"; "`Visibility` can be updated on record posts"; and "The `Update` property is supported
only for feed items posted on records" (L136432–136435). The field itself only exists "in API version
26.0 and later, **if digital experiences is enabled for your org**" (L136412–136414) — in an org
without Experience Cloud it is not there to set.

**How to avoid:** Audit for the explicit `AllUsers` assignment and for non-record parents, not for a
missing assignment on record posts. The checker's `CNT-APEX-FEEDITEM` reports every `FeedItem` insert
with that distinction in the message rather than asserting a leak. And do not write code that sets
`Visibility` unconditionally: in an org without digital experiences the field is absent.

---

## Gotcha 6: You cannot feed-track `LastModifiedDate` — so it is never the cause

**What happens:** "Someone enabled Feed Tracking on `LastModifiedDate`, that is why there is a post on
every save" becomes the accepted diagnosis. The team opens Object Manager, finds no such tracked
field, and concludes the UI is lying or that the setting is hidden.

**When it occurs:** Always, because the configuration being blamed cannot exist. Feed tracking is
available only for standard fields "to which you can add help text or enable history tracking or
Chatter feed tracking. Other standard fields aren't supported, **including system fields (such as
`CreatedById` or `LastModifiedDate`) and autonumber fields**" (api_meta.txt L2164–2167, repeated
L43210–43213).

**How to avoid:** Diagnose from the data. `SELECT Type, COUNT(Id) FROM FeedItem WHERE CreatedDate =
LAST_N_DAYS:30 GROUP BY Type` separates `TrackedChange` volume from `TextPost` volume, and the
`TrackedChange` type is documented as "a change **or group of changes** to a tracked field"
(object_reference.txt L136377–136378) — several fields changed in one save can collapse into one feed
item, so a long tracked-field list is a proxy for noise rather than a per-field multiplier. If the
real source is a formula or roll-up field recomputing, that is a genuine tracked field and a genuine
fix.

---

## Gotcha 7: `trackFeedHistory` will not deploy without `enableFeeds` on the object in the same package

**What happens:** A Feed Tracking change is packaged as field files only — the natural shape when the
change is "track these three fields." The deploy fails on an object that did not previously have feeds
enabled, or succeeds in the sandbox where feeds were already on and fails in production where they
were not.

**When it occurs:** Whenever the object's `enableFeeds` is not already `true` in the target org: "To
set this field to `true`, the `enableFeeds` field on the associated CustomObject must also be `true`"
(api_meta.txt L43668–43672). The same prerequisite governs `recordTypeTrackFeedHistory`
(L42234–42241).

**How to avoid:** Include the `.object-meta.xml` with `enableFeeds` in the package alongside the field
files. `scripts/check_chatter_notification_tuning.py --manifest-dir <root>` raises
`CNT-TRACK-NO-FEEDS` on exactly this shape, before the deploy does.

---

## Gotcha 8: `ChatterEmailsMDSettings` has no per-event elements, and the ones that look right belong to a different feature

**What happens:** An assistant produces a `ChatterEmailsMD.settings` containing `emailOnAllPosts`,
`emailOnFollowedPosts`, `emailOnAtMention`, or a default digest frequency. It is plausible, it maps
cleanly onto the Chatter UI, and it fails to deploy.

**When it occurs:** Every time, because the type's complete documented field table is ten boolean
elements and none of them is per-event: `enableChatterDigestEmailsApiOnly`,
`enableChatterEmailAttachment`, `enableCollaborationEmail`, `enableDisplayAppDownloadBadges`,
`enableEmailReplyToChatter`, `enableEmailToChatter`, and four `noQn*` Chatter Questions flags
(api_meta.txt L112383–112418). The per-event controls are `User` fields —
`UserPreferencesDisableMentionsPostEmail`, `UserPreferencesDisableLikeEmail`, and the rest of the set
at object_reference.txt L296132–296300 — and the default digest frequency is
`User.DefaultGroupNotificationFrequency` (L295156–295172), not a settings element at all. The trap is
sharpened by `ChatterAnswersSettings` (api_meta.txt L112253 onward), which *does* carry
`emailFollowersOnReply` and `emailOwnerOnReply` — for the unrelated Chatter Answers forum feature.

**How to avoid:** Treat any `emailOn*` element in a Chatter settings file as a deploy failure waiting
to happen. `CNT-SETTINGS-ELEMENT` checks both files against the guide's field tables and names the
offending element.

---

## Gotcha 9: The `UserPreferencesDisable*Email` fields are double negatives, and `false` is the noisy state

**What happens:** A CSV is prepared to "turn off the like emails" and every row is set to `false`.
The load succeeds and the volume goes *up*.

**When it occurs:** On every one of these fields, because they are all phrased as disable-flags with
the description written from the `false` side: "**When `false`**, the user automatically receives
email every time someone likes their post or comment" (`UserPreferencesDisableLikeEmail`,
object_reference.txt L296220–296227); the same construction on
`UserPreferencesDisableAllFeedsEmail` (L296132–296140), `UserPreferencesDisableMentionsPostEmail`
(L296228–296235), `UserPreferencesDisCommentAfterLikeEmail` (L296271–296278), and the rest.
`true` suppresses; `false` sends.

**How to avoid:** Read the column header as "Disable? " and the value as the answer. Stage the load as
a small pilot cohort and query the same fields back before running the full set. And note that these
are plain `User` fields with `Create, Filter, Update` properties — ordinary Data Loader reaches them;
no Tooling API is involved, and a plan that says "we will need the Tooling API for this" is a plan
written from a wrong premise.

---

## Gotcha 10: `EntitySubscription` cannot be updated, and querying it is fenced in three separate ways

**What happens:** A cleanup script is written to "repoint" or "adjust" follow records, or to inventory
who follows what across the org. The update call has no effect. The inventory query returns a
plausible-looking but incomplete result, and the incompleteness is silent.

**When it occurs:** `EntitySubscription` supports "`create()`, `delete()`, `describeSObjects()`,
`getDeleted()`, `getUpdated()`, `query()`, `retrieve()`" (object_reference.txt L111058–111060) —
there is no `update()`. Unfollowing is a delete, not an edit. On the read side, three separate fences
apply (L111176–111200): without View All Data you must "specify a `LIMIT` clause of 1,000 records or
fewer"; with user sharing enabled and a non-admin running it, "a SOQL query must be constrained either
by the `ParentId` or `SubscriberId`" or "the query behavior at run time is undefined, meaning the
result set can be incomplete or inconsistent from invocation to invocation"; and for users without
View All Data "a query evaluates visibility criteria on a maximum of 500 records", returning "only
matches within the first 500 records scanned." The guide's own recommendation is to "use the Connect
REST API to query `EntitySubscription` data instead of running a SOQL query."

**How to avoid:** Model unfollow as delete-and-recreate. Run any org-wide follow inventory as a View
All Data holder, or accept that it is a sample rather than a census. Constrain by `ParentId` or
`SubscriberId` even when you have the permission, so the query does not quietly change behaviour when
someone else runs it.

---

## Gotcha 11: An Apex trigger that touches `FeedItem.Body` strips the @mentions and suppresses their notifications

**What happens:** A trigger is added to sanitise, prefix, or translate feed post bodies. Mentions stop
notifying. The people who were @mentioned never hear about the post, and the post still visibly
contains their names — as plain text.

**When it occurs:** On any trigger that modifies the field: "If you use an Apex trigger to modify the
`Body` of a `FeedItem` object, all mentions hyperlinks are converted to plain text. The mentioned
users don't get email notifications" (object_reference.txt L136547–136549).

**How to avoid:** Do not modify `Body` in a trigger on posts where mentions matter. If content has to
be normalised, do it before the insert in the code that creates the post, not in a trigger that
rewrites it afterwards. This one cuts both ways during a tuning project: it is a bug when mentions
were wanted, and it is a tempting but unmaintainable "fix" when they were not.

---

## Gotcha 12: Approval requests in the feed are an org flag with a per-user opt-out, and only the flag is yours

**What happens:** The approval-heavy part of the org is the loudest feed in it. An admin sets out to
suppress those posts for a department and finds no lever with that scope.

**When it occurs:** Because the only org-level control is binary: `enableApprovalRequest` — "When the
value is `true`, users see approval requests as posts in Chatter feeds. **Users can update their own
Chatter feeds settings to opt out** of receiving approval requests as Chatter posts. When the value is
`false`, approval requests aren't posted to Chatter. The default value is `false`" (api_meta.txt
L112490–112496). There is no per-profile, per-process, or per-department scoping in between.

**How to avoid:** Decide it as an org-wide question. If approvals must reach people, they should reach
them as approval notifications and the approval UI, not as feed posts that also happen to be
approvals. If the org has this on and nobody remembers turning it on, the default is `false` — someone
did, and it is worth finding out why before turning it back.

---

## Gotcha 13: Disabling Chatter org-wide is not a one-click revert

**What happens:** An org disables Chatter entirely — usually for a regulated tenant — and later wants
it back. Historical feed data is reported not to come back cleanly.

**When it occurs:** On re-enable. **UNVERIFIED (2026-09-05):** none of the supplied guides
(api_meta, object_reference, apexdev, apexrefguide, ldv, app-limits cheat sheet) documents what
happens to feed history when `enableChatter` goes `false` and then `true`. `ChatterSettings`
documents `enableChatter` as a plain boolean with no reversibility note (api_meta.txt
L112517–112519). Treat the asymmetry as unverified folklore and test the round trip in a sandbox
before relying on either outcome — including before quoting it to a compliance stakeholder as a
reason not to disable.

**How to avoid:** Treat Chatter on/off as a one-way decision until you have tested the round trip in a
sandbox. In almost every case the presenting problem — too many emails, too many automated posts —
is solved by the levers in this skill, and `enableChatter` is not one of them.
