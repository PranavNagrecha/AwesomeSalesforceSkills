# Well-Architected Notes — Chatter Notification Tuning

## Relevant Pillars

- **Operational Excellence** — Notification noise is a productivity tax. Tuning is governance, and like all governance it works best when paired with automated detection (the bundled checker) and a re-measurement loop. Treat the noise audit as a quarterly cadence rather than a one-time cleanup.
- **Security** — `FeedItem.Visibility` defaults to `AllUsers`, which exposes posts to Experience Cloud / Customer Community users. Automated feed posts authored without the `InternalUsers` setting are a low-frequency but real data-leak vector. The tuning project is a good time to audit visibility defaults across all `FeedItem`-inserting automation.

## Architectural Tradeoffs

| Tradeoff | Why it matters |
|---|---|
| Custom Notification (bell) vs Chatter feed post | Bell is transient and recipient-targeted; feed is durable and visible to followers. Use bell for "you should know" alerts and feed for collaborative threads. Treating them as substitutes in either direction creates either lost alerts (if alert→thread) or audit-trail gaps (if thread→alert). |
| `Limited` digest as default vs `Daily` | `Limited` cuts volume 80–95% but skips group-context-only posts. Acceptable for project / interest groups; not acceptable for broadcast / announcement groups. Set per-group, not org-wide. |
| Auto-follow on for engagement vs off for noise | Auto-follow drives initial Chatter engagement but compounds into untraceable noise within 6 months. Recommended default: off, with explicit "Follow this record" actions on the records that matter. |
| Disable Chatter entirely vs tune | Disabling Chatter loses feed history on re-enable; re-enabling is not symmetric. Tune wherever possible. Disable only for compliance-driven full-channel-removal use cases. |
| Org-level email-off vs per-user mass-update | Org-level only affects default for new users. To affect existing users you must mass-update `User.UserPreferencesEmail*` via Tooling API — a heavy-handed user-experience override. Communicate first, then update only for users who don't respond. |

## Anti-Patterns

1. **Tuning at the user level when the noise is automated** — Telling users to filter their inbox doesn't fix a Flow that posts 800 times a day. Audit automation sources first; tune user-level controls last.
2. **Migrating *every* feed post to Custom Notification** — Custom Notifications don't preserve audit trail. Approval-rejected events, owner-change events, and similar durable records belong on the feed for compliance. Keep durable events on the feed; migrate transient alerts to bell.
3. **Tracking `LastModifiedDate` or rollup fields in Feed Tracking** — Generates a `FeedItem` on every save. Rollup fields recompute on dependent updates, multiplying the noise.
4. **Setting org-default group frequency without per-group review** — A blanket `Never` default means broadcast-group announcements never reach members. A blanket `Each post` floods inboxes. Decide per-group based on purpose.

## Official Sources Used

- Salesforce Help — Chatter Settings — https://help.salesforce.com/s/articleView?id=sf.collab_admin_settings.htm
- Salesforce Help — Set Up Chatter Email Notifications — https://help.salesforce.com/s/articleView?id=sf.collab_email_settings.htm
- Salesforce Help — Customize Feed Tracking — https://help.salesforce.com/s/articleView?id=sf.collab_feed_tracking.htm
- Salesforce Help — Custom Notifications — https://help.salesforce.com/s/articleView?id=sf.notif_builder_custom.htm
- Object Reference — `CollaborationGroup` — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_collaborationgroup.htm
- Object Reference — `CollaborationGroupMember` (`NotificationFrequency` codes) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_collaborationgroupmember.htm
- Object Reference — `FeedItem` (`Visibility` field) — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_feeditem.htm
- Apex Reference — `Messaging.CustomNotification` — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_Messaging_CustomNotification.htm
- Salesforce Well-Architected — Operational Excellence — https://architect.salesforce.com/docs/architect/well-architected/guide/operational-excellence.html
