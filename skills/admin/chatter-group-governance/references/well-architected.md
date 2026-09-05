# Well-Architected Notes — Chatter Group Governance

## Relevant Pillars

- **Operational Excellence** — Group sprawl is operational debt. Without governance the group population grows unbounded, ownership decays as users leave, and the cost of finding "is there already a group for this" rises faster than the value of any single new group. Treat group governance as a quarterly cadence (inventory + cleanup) rather than a one-time project. Pair the inventory checker with a documented runbook for archive vs delete decisions, and for the offboarding ownership-transfer hook.
- **Security** — Group type (`Public` / `Private` / `Unlisted`) drives content visibility, and the defaults are not what casual users assume. "Public" includes Experience Cloud users on default visibility; Unlisted hides content from compliance discovery; Private is the most common safe choice for internal-sensitive content. Group governance is also a *deactivation* problem — orphaned groups owned by departed users are a low-frequency but real footgun for both operational continuity (no one can delete the group) and security (a deactivated user's group ownership prevents a clean offboarding posture).

## Architectural Tradeoffs

| Tradeoff | Why it matters |
|---|---|
| Open group creation vs perm-set restriction | Open creation drives engagement at the cost of sprawl; perm-set restriction stops sprawl at the cost of friction for ad-hoc collaboration. For orgs >100 users, restriction usually wins because the cost of dormant-group cleanup compounds nonlinearly. For orgs <50 users, leave it open and rely on social norms. |
| Archive vs delete dormant groups | Archive preserves audit trail at the cost of registry clutter; delete frees the namespace at the cost of permanent history loss. Default to archive for any group with >10 substantive posts or any post >12 months old (these have audit / institutional-memory value). Delete only empty / abandoned / clearly-test groups. |
| Public vs Private vs Unlisted | Public maximizes discoverability and serendipitous collaboration but exposes content to all internal users (and possibly community users). Private balances discovery and confidentiality (members-only posts, but the group's existence is public). Unlisted prioritizes confidentiality at the cost of governance discoverability, and the cost is larger than "not in the UI": a View All Data or Modify All Data holder cannot see unlisted groups at all without Modify Unlisted Groups / Manage Unlisted Groups (L67109–67115), so an admin's SOQL audit is incomplete and silent about it. Choose Unlisted only when the *existence* of the group must be confidential, and only alongside a named permission holder who can audit it. |
| Per-user owner vs steward service-account owner | Person-owners feel natural and create accountability ("Jane owns this") but generate re-orphan risk when Jane leaves. A "Chatter Stewards" service account is institutionally owned and never leaves the company; ownership is permanent. Trade some accountability for cleanup-cost reduction; pair the steward owner with a named human "manager" via `CollaborationGroupMember.CollaborationRole = 'Admin'` for day-to-day moderation. |
| Tune the org-wide archive window vs exempt named groups | The org-wide inactivity window is one number for every group purpose, so tuning it for standing groups under-archives dead project groups and vice versa. `CollaborationGroup.IsAutoArchiveDisabled` (object_reference.txt L67282–67290) exempts one group at a time and costs nothing. Prefer per-group exemption, driven by the read-signal query in `examples.md` Example 5, and leave the org window matched to the *dominant* group purpose. Never reach for `allowChatterGroupArchiving = false` as the fix — it removes manual archiving too (api_meta.txt L112476–112480). |
| Group Information Templates as policy enforcement | Templates encode policy at creation time but are advisory-only — users can ignore them. Combined with creation-permission restriction, they're highly effective. Standalone, they cut sprawl ~30% and that's it. The leverage is in the *combination* (perm-set + template + steward-account fallback). |

## Anti-Patterns

1. **Deleting groups en masse without archiving the substantive ones first.** Conversation history in `FeedItem` is a real audit trail — approval discussions, decision threads, customer escalations may live in there. A blanket "delete groups inactive >12 months" loses institutional memory permanently. Always do an archive-first pass; delete only the empty / clearly-disposable subset.
2. **Reassigning orphaned-owner groups to a department head ("VP of Sales").** The VP becomes the de facto owner of dozens of unrelated groups. When the VP leaves, you re-orphan everything. Use a named service account (`chatter.stewards@company.com`) instead — institutionally owned, never leaves.
3. **Treating Unlisted as "more secure than Private."** It is not — it is *less discoverable*, and that is a governance liability rather than a security gain. Private already restricts content: "Only members can see the group feed and post updates. Non-members can only see the group name and a few other details in list views, search, and on the group page" (L67194–67198). Unlisted adds only the hiding of existence, and it hides it from the org's own auditors too. Reserve it for cases where the group's existence is itself confidential, and provision Manage Unlisted Groups to a named holder in the same change.
4. **Skipping the offboarding ownership-transfer step.** "We'll fix it later" produces the orphaned-owner problem. Doing the transfer at deactivation time is one query and one DML; doing it later requires a full-org audit. Bake into the offboarding checklist before the User record's `IsActive` flips.
5. **Creating a group for every short-term project without an end-of-life trigger.** Projects end; groups linger. The Group Information Template should make the end-of-life trigger explicit ("archive when project closes"). Without it, project groups become permanent fixtures and the active group count creeps upward forever.
6. **Letting end users freely change group type from Public → Private mid-life.** A group that started Public has accumulated content under "everyone can see" assumptions; flipping to Private makes that content invisible to non-members but doesn't notify them or migrate their participation. The transition is technically allowed but social-cost-heavy. Group type should be set at creation and changed only with admin involvement.

## Official Sources Used

- **Object Reference (Summer '26 / v62 PDF) — `CollaborationGroup`, Special Access Rules**,
  object_reference.txt L67092–67133 —
  https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_collaborationgroup.htm
  (the Public/Private/Unlisted security tradeoff; that View All Data and Modify All Data do **not** reach
  unlisted groups without Modify Unlisted Groups / Manage Unlisted Groups; that Apex runs in system mode
  and can expose unlisted groups; the Group Triggers enforcement hook)
- **Object Reference — `CollaborationGroup` fields**, L67172–67405
  (`CanHaveGuests`, `CollaborationType`, `IsArchived`, `IsAutoArchiveDisabled`, `LastFeedModifiedDate`,
  `MemberCount`, `Name` uniqueness, `NetworkId` immutability, and the `OwnerId` rule that only the owner
  or a Modify All Data holder can repoint it — the "per-user owner vs steward service-account owner" and
  "archive vs delete" tradeoffs below both rest on this block, as does the delete cascade at L67402–67404)
- **Object Reference — `CollaborationGroupMember` and `CollaborationGroupMemberRequest`**, L67430–67632 —
  https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_collaborationgroupmember.htm
  (`CollaborationRole` Admin vs Standard and what a manager can and cannot do; `NotificationFrequency`;
  `LastFeedAccessDate` as the read signal the archive sweep ignores; the 300-groups-per-user membership
  limit with pending requests counting against it)
- **Object Reference — `EntitySubscription`**, L111051–111180 —
  https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_entitysubscription.htm
  (that archive leaves subscriptions intact, and that deactivating multiple mutually-following users at
  once hard-deletes their subscriptions unrecoverably — the sequencing argument in the offboarding
  anti-pattern below)
- **Metadata API Developer Guide (v62 PDF) — `ChatterSettings`**, api_meta.txt L112452–112648 —
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
  (`allowChatterGroupArchiving` covering manual *and* automatic archiving, `unlistedGroupsEnabled`,
  `allowRecordsInChatterGroup`, `enableInviteCsnUsers`, the sample definition and manifest — the whole
  "governance baseline belongs in source control" position)
- **Metadata API Developer Guide — `PermissionSet`**, api_meta.txt L94863, L95214–95217, L95373–95393
  (the `userPermissions` element shape used for the creation and unlisted-auditor permission sets;
  note that the guide does not publish the permission API-name catalogue — see the UNVERIFIED marker in
  `metadata-examples.md` section 2)
- **Apex Reference Guide (v62 PDF) — `ConnectApi.ChatterGroups`, `ChatterGroupInput`, `ChatterGroup`**,
  apexrefguide.txt L66502–68930, L111938–111975, L125225–125285 —
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
  (that `updateGroup` requires manager, owner, or Modify All Data; that `owner` is PATCH-only; that
  `canHaveChatterGuests` cannot be set back to false; that `GroupVisibilityType.Unlisted` is reserved for
  future use — the reason this skill routes unlisted work through the sObject, not Connect API)
- **Data Loader Guide (v62 PDF)**, salesforce_data_loader.txt L605–606, L964 —
  (hard-deleted records bypass the Recycle Bin entirely; the basis for the "never hard-delete a group"
  rule in the archive-vs-delete tradeoff)
- **Salesforce Well-Architected — Operational Excellence** —
  https://architect.salesforce.com/docs/architect/well-architected/guide/operational-excellence.html
  (the quarterly-cadence framing for group population management)
- **Salesforce Well-Architected — Trusted (Security)** —
  https://architect.salesforce.com/docs/architect/well-architected/guide/trusted.html
  (the visibility-defaults and offboarding-posture framing in the Security pillar note above)
