---
name: chatter-notification-tuning
description: "Use when admins are reducing Chatter signal-to-noise across an org — covers org-level Chatter Email Settings, per-user Email Settings preferences, group-level email digest frequency (Daily / Weekly / Limited / Never), bell-icon Custom Notifications vs Chatter feed-post tradeoffs, automated-feed suppression on record types via Feed Tracking config, and the Chatter Settings org defaults that control whether new users start with everything-on. Triggers: 'chatter feed full of automated posts nobody reads', 'users complain about chatter email volume', 'turn off chatter notifications for a specific group', 'change default chatter digest frequency', 'stop process builder posts from filling the feed'. NOT for Custom Notifications API design (use apex/apex-custom-notifications-from-apex), NOT for Connect API / Chatter REST API integration patterns (use apex/apex-connect-api-chatter), NOT for Chatter group lifecycle and governance (use admin/chatter-group-governance once authored)."
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
inputs:
  - "Symptom: feed noise, email volume, notification fatigue, or both"
  - "Scope: org-wide, per-group, per-user, or per-object-type"
  - "Whether the noise source is automated (Flow/PB/Apex feed posts) or human (group activity)"
  - "Whether Custom Notifications (bell) are an option, or org is locked into Chatter feed"
outputs:
  - "Tuning plan with org-level, group-level, and user-level changes"
  - "List of automated-post sources to suppress with replacement strategy (bell, email alert, dashboard)"
  - "Migration recipe from Chatter feed posts to Custom Notifications where applicable"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-08
runtime_orphan: true
---

# Chatter Notification Tuning

Activate this skill when an admin needs to reduce Chatter feed noise, lower email volume, or rebalance the notification surface across Chatter feed posts, Custom Notifications (bell), and email alerts. The skill is about *governance* of the notification channel — not authoring new automation.

---

## Before Starting

Gather this context before proposing changes:

- **Where the noise comes from.** Three sources, three different fixes:
  - **Automated feed posts** — Flow `Post to Chatter` actions, Process Builder posts, Apex `FeedItem` inserts, automated `@mentions` in feed. Look in Setup → Object Manager → relevant object → Feed Tracking, plus search Flows for "Post to Chatter" actions and Apex for `FeedItem` inserts.
  - **Group activity emails** — Member-driven posts in Chatter groups. Per-group `Email Frequency` controls digest vs per-post.
  - **Follower / record-followed emails** — Triggered when a user follows a record (manual or auto-follow), tied to Feed Tracking changes.
- **Who's complaining.** A single noisy executive often drives a full-org tuning project; a quieter pattern is "everyone deletes the digest unread." Both need different responses.
- **Do you have Custom Notifications (Notification Builder)?** Available since Summer '20. The bell-icon channel is generally a better fit than feed posts for *targeted, transient* notifications. If the answer is "we never used it," the most-leveraged tuning is migrating high-volume automated feed posts to Custom Notifications.
- **License constraints.** Chatter Free / Chatter External users have a smaller subset of email-notification controls. Customer Community + Customer Community Plus follow Experience Cloud notification mechanics, not the standard Chatter set.

---

## Core Concepts

### Concept 1 — Three control surfaces, layered

Chatter notifications layer like a CSS cascade. Each surface can override the layer above it:

1. **Org-level Chatter Settings** (Setup → Chatter Settings + Setup → Email Settings → Chatter Email Settings).
   - `EnableChatter`, `EnableEmailNotifications`, `EnableMyChatterMessages`.
   - Sets the *default* on for new users and the global ceiling — disabling at this level overrides everything below.
2. **Group-level Email Frequency** on each `CollaborationGroup` record.
   - Values: `Daily`, `Weekly`, `Each post`, `Limited`, `Never`. `Limited` sends emails only for posts that @mention the user or are in the user's first-degree-followed records.
   - Group owners and admins can change this; non-owner users can only change *their own* per-group preference under My Settings.
3. **User-level Email Settings** (My Settings → Email → Email Notifications).
   - Per-user opt-out of bookmark replies, comments on followed posts, group digest choices. The user's settings always override the org default once they touch the page.

The cascade explains why an org-level "turn off chatter emails" doesn't always work — existing users who once saved their Email Notifications page now have a per-user record that pins them on.

### Concept 2 — Feed Tracking is what makes records noisy, not Chatter

Feed Tracking on an object/field generates a `FeedItem` every time a tracked field changes on a record that someone follows. Two failure modes:

1. **Tracking too many fields.** Tracking `LastModifiedDate` on `Account` will generate a `FeedItem` on every save — usually unwanted. Recommended: track only fields tied to *qualitative state* (Stage, Owner, Status), never timestamps or rollup fields.
2. **Auto-follow is on.** Setup → Chatter Settings → "Allow Coworker Invitations" + per-object Auto-Follow rules cause users to silently accumulate followed records. The user later sees floods of automated activity in their feed and has no idea where the follows came from. Audit auto-follow rules early.

To kill noise at the source: prune Feed Tracking to ≤5 fields per object, and disable auto-follow on objects that are mass-edited (Lead, Case).

### Concept 3 — Custom Notifications (bell) vs Chatter feed posts

Decision tree for "I want to tell users something happened":

| Goal | Use |
|---|---|
| Targeted, transient alert ("your case was reassigned") | Custom Notification (bell). Disappears when read. Optional desktop / mobile push. |
| Durable record of an event ("approval rejected on Opp #4567") | Chatter `FeedItem` with `Visibility = InternalUsers`. Preserves audit trail. |
| Broadcast announcement ("system maintenance Sunday") | Custom Notification with broad recipient list, NOT a feed post on user records. |
| Process telemetry ("flow completed successfully") | NEITHER. Use Email Alert or a dashboard. Chatter is not a logging channel. |

The most-leveraged tuning move in a noisy org is auditing Flow / Apex `FeedItem` inserts and migrating the transient-alert ones to Custom Notifications. A single Flow that posts a "Stage moved to Closed Won" feed item on every opportunity may produce thousands of `FeedItem` rows per day; Custom Notifications target the same recipients without the storage and feed-pollution cost.

### Concept 4 — `Limited` digest is underused

Most orgs default group email frequency to `Each post` or `Daily`. The `Limited` setting is the smartest default for collaboration groups:

- Sends emails only for posts that @mention the recipient OR posts that comment on a thread the recipient already participated in.
- Cuts email volume by 80–95% in active groups while preserving the "this involves me" signal.

For broadcast groups (announcements, all-hands), `Daily` digest is appropriate. For project-specific or interest groups, `Limited` is almost always the right default.

---

## Recommended Workflow

1. **Inventory the noise sources.** Run the bundled `scripts/check_chatter_notification_tuning.py` against your retrieved metadata to enumerate Flows that post to Chatter, Apex classes that insert `FeedItem`, and objects with Feed Tracking on more than 5 fields.
2. **Audit Feed Tracking per object.** For each object reported by the checker, open Setup → Object Manager → Feed Tracking. Remove timestamp / rollup / formula fields from the tracking list. Aim for ≤5 qualitative fields per object.
3. **Migrate transient automated feed posts to Custom Notifications.** Replace each `FeedItem`-inserting Flow / Apex with a Custom Notification action. Delete or deactivate the original after a 2-week parallel-run window.
4. **Set group email frequency defaults.** For each `CollaborationGroup`, decide between `Daily`, `Limited`, and `Never` based on group purpose. Communicate the change to group owners with the rationale.
5. **Audit auto-follow rules.** Setup → Chatter Settings → User Auto-Follow defaults + any per-object follow automation. Disable auto-follow on mass-edited objects. Existing follows can be cleaned with a one-time `EntitySubscription` purge.
6. **Reset user-level Email Notifications stuck-on state.** For users who saved their settings before the org-level change, only they can re-save their Email Notifications page. Communicate the action with a step-by-step screenshot in the change announcement.
7. **Re-measure.** Two weeks after the change, re-run the checker and pull `FeedItem` count + `EntitySubscription` count by date to confirm the curve.

---

## Related Skills

- `apex/apex-custom-notifications-from-apex` — Custom Notification API patterns, recipient targeting, target page navigation
- `apex/apex-connect-api-chatter` — programmatic feed manipulation via Connect API
- `admin/email-deliverability-strategy` — broader email volume management beyond Chatter
