---
name: chatter-notification-tuning
description: "Use when admins are reducing Chatter signal-to-noise across an org — covers org-level Chatter Email Settings, per-user Email Settings preferences, group-level email digest frequency (Daily / Weekly / Every post / Never), bell-icon Custom Notifications vs Chatter feed-post tradeoffs, automated-feed suppression on record types via Feed Tracking config, and the Chatter Settings org defaults that control whether new users start with everything-on. Triggers: 'chatter feed full of automated posts nobody reads', 'users complain about chatter email volume', 'turn off chatter notifications for a specific group', 'change default chatter digest frequency', 'stop process builder posts from filling the feed', 'NotificationFrequency invalid value', 'ChatterEmailsMD.settings will not deploy', 'custom notification recipient limit'. NOT for Custom Notifications API design (use apex/apex-custom-notifications-from-apex), NOT for Connect API / Chatter REST API integration patterns (use apex/apex-connect-api-chatter), NOT for Chatter group lifecycle, archiving, ownership and unlisted-group governance (use admin/chatter-group-governance)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Security
tags:
  - chatter-notification-tuning
  - chatter
  - email-notifications
  - feed-tracking
  - notification-builder
  - digest-frequency
triggers:
  - "the chatter feed is full of automated notifications nobody reads"
  - "users keep complaining about chatter email volume"
  - "how do I change the default chatter email digest frequency for a group"
  - "stop process builder or flow posts from cluttering the chatter feed"
  - "turn off chatter notifications for the new-hires group"
  - "set the default chatter notification preferences for new users"
  - "we want bell notifications instead of chatter feed posts"
  - "chatter group sends an email for every reply, how do we throttle"
  - "default 'follow' on every new account is creating noise"
  - "bulk update collaboration group member notification frequency with data loader"
  - "NotificationFrequency bad value for restricted picklist Limited"
  - "what are the valid values for CollaborationGroupMember NotificationFrequency"
  - "ChatterEmailsMD.settings deploy fails on an unknown element"
  - "which chatter email setting turns off notifications for the whole org"
  - "new users inherit daily chatter digests and nobody set that"
  - "migrate a flow post to chatter action to a custom notification"
  - "custom notification send failed for a large recipient list"
  - "deploy trackFeedHistory field but the object does not have feeds enabled"
  - "approval requests are posting to the chatter feed, how do we stop it"
  - "audit which flows and apex classes insert FeedItem records"
  - "count feed items by type to find what is generating the noise"
  - "reset chatter email preferences for users in bulk"
inputs:
  - "Symptom: feed noise, email volume, notification fatigue, or both"
  - "Scope: org-wide, per-group, per-user, or per-object-type"
  - "Whether the noise source is automated (Flow/PB/Apex feed posts) or human (group activity)"
  - "Whether Custom Notifications (bell) are an option, or org is locked into Chatter feed"
  - "A retrieved metadata tree containing settings/, objects/, flows/, classes/ (for the checker)"
  - "Whether the person running the change holds Modify All Data and View All Data"
outputs:
  - "Tuning plan with org-level, group-level, and user-level changes"
  - "List of automated-post sources to suppress with replacement strategy (bell, email alert, dashboard)"
  - "Migration recipe from Chatter feed posts to Custom Notifications where applicable"
  - "Deployable Chatter.settings, ChatterEmailsMD.settings, CustomNotificationType and Feed Tracking XML"
  - "A linted notification-policy.json plus the CollaborationGroupMember and User CSVs that apply it"
  - "Before/after FeedItem volume measurement by Type"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
runtime_orphan: true
---

# Chatter Notification Tuning

Activate this skill when an admin needs to reduce Chatter feed noise, lower email volume, or rebalance
the notification surface across Chatter feed posts, Custom Notifications (bell), and email. The skill
is about *governance* of the notification channel — not authoring new automation.

Group *lifecycle* — creation policy, archiving, ownership transfer, unlisted groups — belongs to
`admin/chatter-group-governance`. That skill governs which groups exist; this one governs what is
noisy inside them.

---

## Before Starting

Gather this context before proposing changes:

- **Where the noise comes from.** Do not guess this; the answer is one query and it changes everything
  downstream. `SELECT Type, COUNT(Id) FROM FeedItem WHERE CreatedDate = LAST_N_DAYS:30 GROUP BY Type`
  — direct `FeedItem` queries need the View All Data permission (object_reference.txt L136505–136507).
  Three sources, three different fixes:
  - **Automated feed posts** — Flow `chatterPost` action calls (api_meta.txt L68655), Apex `FeedItem`
    inserts. These show as `TextPost` from a small set of `CreatedById` values.
  - **Feed Tracking** — shows as `TrackedChange`, "a change **or group of changes** to a tracked
    field" (object_reference.txt L136377–136378).
  - **Group activity and approvals** — human `TextPost`, and `ApprovalPost` when
    `enableApprovalRequest` is on (api_meta.txt L112490–112496).
- **Who can actually make the change.** Two permissions gate most of this work.
  `CollaborationGroupMember.NotificationFrequency` "can only be set by the member or users with the
  'Modify All Data' permission" (object_reference.txt L67510–67513) — group ownership is not enough.
  Direct `FeedItem` queries need View All Data. Confirm both before planning a bulk change.
- **What the four frequencies are.** The whole design space is `P` (on every post), `D` (Daily),
  `W` (Weekly), `N` (Never) — object_reference.txt L67515–67518. There is no `Limited`. A plan built
  on "email me only for @mentions and threads I already joined" is built on a value the platform does
  not have; see `references/gotchas.md` gotcha 1 before you promise anyone a volume number.
- **Do you have Custom Notifications?** `CustomNotificationType` is deployable metadata, available in
  API version 46.0 and later (api_meta.txt L41785), with `desktop` and `mobile` as its only delivery
  channels (L41802–41812). If the org has never used it, migrating high-volume automated feed posts to
  the bell is the most-leveraged move available.
- **Is digital experiences enabled?** `FeedItem.Visibility` exists only "in API version 26.0 and later,
  if digital experiences is enabled for your org" (object_reference.txt L136412–136414). In an org
  without it, code that sets `Visibility` unconditionally breaks, and the internal/external exposure
  question does not arise.

---

## Questions to Ask Before Configuring

Ask these before touching Setup, writing XML, or staging a CSV. Each one maps to a gotcha that turns a
reasonable-looking tuning change into a change that fails, reverses itself, or overrides someone's
deliberate choice.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which channel is loud — the feed, the inbox, or the bell?" | They are three different data stores with three different fixes; `EntitySubscription` (follows), `CollaborationGroupMember` (digests) and `Messaging.CustomNotification` (bell) share nothing but a complaint | The one surface to work on, instead of a plan that touches all three and cannot be measured |
| "Who is running the bulk change, and do they hold Modify All Data?" | `NotificationFrequency` can only be set by the member or a Modify All Data holder (L67510–67513); a group owner's load fails per row | Either a named runner, or the decision to change only `User.DefaultGroupNotificationFrequency` and ask members to change their own |
| "Which of `P` / `D` / `W` / `N` is the intended default, and if it is `P`, why?" | `P` self-disables above 10,000 members in a site and silently switches everyone to Daily (L67519–67522) | A written justification the checker's `CNT-POLICY-EVERYPOST` will stop demanding, or a switch to `D` before that decision gets made for you |
| "Is the volume automated or human?" | An 800-post Flow is not a digest problem — no frequency setting makes those posts worth reading | The routing decision between migrating a `chatterPost` action (examples § 3) and tuning frequency (examples § 2) |
| "Are we changing what new joins inherit, or rewriting existing members' choices?" | `User.DefaultGroupNotificationFrequency` applies "when the user joins groups" (L295160–295163) and is not retroactive; rewriting `CollaborationGroupMember` rows overrides choices people made | Two separate changes with two separate consent stories, rather than one that quietly does both |
| "Does this org have digital experiences enabled?" | `FeedItem.Visibility` only exists if it does (L136412–136414), and for record posts it already defaults to `InternalUsers` (L136430–136431) | Whether the external-exposure audit is real work or a wild goose chase |
| "What does 'quiet enough' look like, and against which number?" | Without a before-measurement the change cannot be defended or reversed on evidence | The 30-day `FeedItem`-by-`Type` baseline that step 7 re-runs against |

What a proper configuration adds over just doing it: the org gets a notification policy that is written
down, linted against the real group population and the real enum, deployed from source control, and
measured against a before-baseline — instead of a one-off Setup change that nobody can explain in six
months, built on a frequency value that does not exist, applied by someone whose permissions silently
dropped half the rows.

---

## Core Concepts

### Concept 1 — Four control surfaces, and only two of them are metadata

| Surface | Where it lives | What it controls | Source |
|---|---|---|---|
| `ChatterSettings` | `settings/Chatter.settings-meta.xml` | `enableChatter`, `enableApprovalRequest`, feed presentation | api_meta.txt L112452–112648 |
| `ChatterEmailsMDSettings` | `settings/ChatterEmailsMD.settings-meta.xml` | the collaboration-email master switch, digest scheduling mode, email-to/reply-to-Chatter | L112368–112445 |
| `User` fields | data — Data Loader / DML | personal digest frequency, inherited group frequency, every per-event email | object_reference.txt L295156–295207, L296132–296300 |
| `CollaborationGroupMember.NotificationFrequency` | data — Data Loader / DML | one member's digest frequency in one group | L67503–67540 |

Two consequences follow from that table, and both are load-bearing.

**There is no org-level default digest frequency.** `ChatterEmailsMDSettings` has ten boolean elements
and none of them is a frequency (L112383–112418). What new users inherit is the defaulted-on-create
value of `User.DefaultGroupNotificationFrequency`: `N`, "but for Professional, Enterprise, Unlimited,
and Developer Edition organizations that existed before API version 22.0, the default value remains
`D`" (L295165–295172). In a long-lived Enterprise org, every new hire is inheriting a daily digest
that nobody chose.

**The only org-wide email lever is binary.** `enableCollaborationEmail` — "whether collaboration email
notifications can be sent (`true`) or not (`false`)" (L112391–112392). Setting it `false` makes every
preference below it inert. It ends the complaint by ending the channel; treat it as a decision about
whether the org uses Chatter email at all, not as a volume dial.

### Concept 2 — Feed Tracking is what makes records noisy, and its failure modes are not the folklore ones

Feed Tracking is two elements that must travel together: `enableFeeds` on the object
(api_meta.txt L42035–42039) and `trackFeedHistory` on each field, where "to set this field to `true`,
the `enableFeeds` field on the associated CustomObject must also be `true`" (L43668–43672). Deploying
the fields without the object is the most common failure, and the bundled checker raises
`CNT-TRACK-NO-FEEDS` on it.

Two real failure modes, and one that gets blamed but cannot happen:

1. **Roll-up and formula fields.** These recompute on dependent updates, so they generate feed activity
   with no human event behind it — the highest-yield removals when they are present.
   **UNVERIFIED (2026-09-05):** no supplied guide states whether roll-up summary or formula fields
   accept `trackFeedHistory` at all; the only documented eligibility restriction covers *standard*
   fields (L2164–2167). Read the retrieved `*.field-meta.xml` files for `trackFeedHistory` rather
   than assuming this category exists in the org in front of you.
2. **Whole-object tracking where a record type would do.** `recordTypeTrackFeedHistory`
   (L42234–42241) scopes feed tracking to one record type, with the same `enableFeeds` prerequisite.
   When one integration-fed record type is the noise source, this is the surgical cut.
3. **Not `LastModifiedDate`.** System fields "such as `CreatedById` or `LastModifiedDate`" are not
   eligible for feed tracking at all (L2164–2167). Anyone who reports finding it tracked is
   misremembering; sending an admin to look for that checkbox costs credibility.

Expect a smaller volume drop than the field-count drop suggests: a `TrackedChange` is "a change or
group of changes to a tracked field" (object_reference.txt L136377–136378), so several fields changed
in one save can collapse into one feed item.

### Concept 3 — Custom Notifications (bell) vs Chatter feed posts

| Goal | Use |
|---|---|
| Targeted, transient alert ("your case was reassigned") | Custom Notification (bell). No `FeedItem` written. Desktop and/or mobile channel. |
| Durable record of an event ("approval rejected on Opp #4567") | Chatter `FeedItem`. Preserves the audit trail; `ApprovalPost` and `TrackedChange` types exist for exactly this. |
| Broadcast announcement ("system maintenance Sunday") | Custom Notification with a `GroupId` or `QueueId` recipient, NOT a feed post on user records. |
| Process telemetry ("flow completed successfully") | NEITHER. Email alert or a dashboard. Chatter is not a logging channel. |

The migration is one `actionType` swap in the Flow — `chatterPost` (api_meta.txt L68655) to
`customNotificationAction`, "available in API version 46.0 and later" (L68710) — plus a deployed
`CustomNotificationType`. A Flow posting a feed item on every Closed Won produces thousands of
`FeedItem` rows a year; the bell reaches the same people and writes none.

Two limits shape the recipient design. `Messaging.CustomNotification.send()` takes at most **500
values** (apexrefguide.txt L166776–166778) — not 2,000 — but a single `GroupId` or `QueueId` counts as
one value and expands to every active member (L166766–166776), which collapses most large fan-outs to
a set of size one. And `send()` requires the Send Custom Notifications permission, failing without it
(L166591–166594).

### Concept 4 — Choosing among four frequencies, with `N` as the honest default

The design space is `P` / `D` / `W` / `N` (object_reference.txt L67515–67518). Match it to group
purpose rather than reaching for one org-wide answer:

| Group purpose | Frequency | Why |
|---|---|---|
| Broadcast / announcement (`IsBroadcast = true`) | `D` | Low post rate, high must-read; a daily digest is the whole point |
| Active project group | `W` | A heartbeat that says "this is still moving" without an inbox per thread |
| Social / interest group | `N` | People read these when they choose to; pushing them is what generates the complaint |
| Genuinely urgent, small, bounded | `P` | Only with a written reason — and only if the group cannot grow past 10,000 members, above which `P` self-disables and everyone is switched to Daily (L67519–67522) |

The org-wide question is a different one: what should a *new* member inherit? That is
`User.DefaultGroupNotificationFrequency`, and `N` is both the platform's own current default
(L295165–295168) and the defensible choice — it makes every noisier setting a decision somebody made
rather than a default nobody noticed.

---

## Recommended Workflow

1. **Measure before you plan.** Run the 30-day `FeedItem`-by-`Type` query in
   `references/metadata-examples.md` § 8 as a View All Data holder. The dominant `Type` routes the rest
   of this workflow, and the number is the baseline step 7 re-runs against. Record both in
   `templates/chatter-notification-tuning-template.md` § 1.

2. **Retrieve the metadata baseline and lint it.**
   ```bash
   sf project retrieve start --metadata Settings:Chatter Settings:ChatterEmailsMD --target-org prod-audit
   python3 scripts/check_chatter_notification_tuning.py --manifest-dir force-app/main/default
   ```
   Two findings stop everything else. `CNT-SETTINGS-ELEMENT` means the file in source control contains
   an element the guide does not document, so nothing in it will deploy. `CNT-EMAIL-MASTER` means
   `enableCollaborationEmail` is already `false` — the channel is off, and whatever people are
   complaining about is not Chatter email. `references/metadata-examples.md` §§ 1–2 carry the
   deployable shapes.

3. **Prune Feed Tracking, if step 1 said `TrackedChange`.** Remove roll-up and formula fields first;
   consider `recordTypeTrackFeedHistory` before removing tracking wholesale. Package the
   `.object-meta.xml` with the field files — `CNT-TRACK-NO-FEEDS` fires when you forget, and so does
   the deploy. `references/examples.md` § 4 works a twelve-field Account down to four.

4. **Migrate transient automated posts, if step 1 said `TextPost` from automation ids.** The checker's
   `CNT-FLOW-CHATTERPOST` and `CNT-APEX-FEEDITEM` findings are the worklist. Swap `chatterPost` for
   `customNotificationAction` and deploy the `CustomNotificationType`
   (`references/metadata-examples.md` § 3). Keep durable business events on the feed — read
   `references/llm-anti-patterns.md` anti-pattern 7 before anyone proposes a `FeedItem` purge instead.
   Run the two in parallel for two weeks before deactivating the original.

5. **Write the digest policy down, then lint it against the real group population.**
   ```bash
   sf data query --result-format csv --target-org prod \
       --query "SELECT Id, Name, IsBroadcast, IsArchived FROM CollaborationGroup" > groups.csv
   python3 scripts/check_chatter_notification_tuning.py \
       --manifest-dir force-app/main/default \
       --policy notification-policy.json --group-inventory groups.csv
   ```
   `CNT-POLICY-GROUP` catches overrides that name a group that no longer exists; `CNT-FREQ-VALUE`
   rejects `L` and `Limited`; `CNT-POLICY-EVERYPOST` makes you justify `P` in writing. The policy
   shape is in `references/metadata-examples.md` § 7.

6. **Apply it in two separate changes.** First `User.DefaultGroupNotificationFrequency` and
   `User.DigestFrequency`, which only affect what people inherit going forward. Then, as a Modify All
   Data holder and only if you decided to, the `CollaborationGroupMember` rows — which override
   choices people made. Lint the CSV before each load:
   ```bash
   python3 scripts/check_chatter_notification_tuning.py --member-csv members_update.csv
   ```
   `references/examples.md` § 5 covers the per-user email flags and their inverted polarity;
   `references/gotchas.md` gotcha 9 is the one that turns a suppression load into an amplification.

7. **Re-measure at two weeks and diff.** Re-run step 1's query and step 2's checker invocation. The
   dominant `Type` should have changed, not just shrunk — if `TrackedChange` still leads after a
   `chatterPost` migration, step 3 was the work that mattered and did not happen. Commit
   `Chatter.settings`, `ChatterEmailsMD.settings`, the notification types and the policy JSON so the
   next org inherits the decision rather than rediscovering it.

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing the deployable `ChatterEmailsMD.settings`, `Chatter.settings`, `CustomNotificationType` or Feed Tracking XML, the package.xml and `sf project` commands — or any of the data-side artefacts: the policy JSON, the member and user CSVs, the DML alternative, and the verification queries |
| `references/gotchas.md` | The change failed, reversed itself, or did the opposite of what you intended — an invalid `NotificationFrequency`, a settings element that will not deploy, a per-post setting that became Daily on its own, a `send()` that failed above 500, a suppression load that increased volume |
| `references/examples.md` | Working a scenario end to end before any XML exists — the new-hire default, a bulk group-frequency change, a `chatterPost` migration, Feed Tracking pruning, per-user preference resets, and the audit query that routes between them |
| `references/well-architected.md` | Justifying bell vs feed, `W` vs `D` vs `N`, inherited-default vs rewrite, or source-suppression vs frequency-tuning — and locating the official source behind any claim in this skill |
| `references/llm-anti-patterns.md` | Reviewing output an AI assistant produced here, especially anything mentioning `Limited`, an `emailOn*` settings element, a 2,000-recipient batch, the Tooling API, or a `FeedItem` purge |
| `templates/chatter-notification-tuning-template.md` | Running workflow steps 1–4 — the diagnosis, the questions, the policy, and the record of what you deliberately left alone |
| `scripts/check_chatter_notification_tuning.py` | Workflow steps 2, 5, 6 and 7 — before any settings deploy, before any policy is agreed, and before every CSV load |

---

## Related Skills

- `admin/chatter-group-governance` — the group population itself: creation policy, public/private/unlisted, archiving, ownership transfer (this skill tunes what is noisy inside a group; that one governs which groups exist)
- `apex/apex-custom-notifications-from-apex` — Custom Notification API patterns, recipient targeting, target page navigation
- `apex/apex-connect-api-chatter` — programmatic feed manipulation via Connect API
- `admin/email-deliverability-strategy` — broader email volume management beyond Chatter
