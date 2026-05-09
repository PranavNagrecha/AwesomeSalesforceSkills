# Well-Architected Notes — Chatter Group Governance

## Relevant Pillars

- **Operational Excellence** — Group sprawl is operational debt. Without governance the group population grows unbounded, ownership decays as users leave, and the cost of finding "is there already a group for this" rises faster than the value of any single new group. Treat group governance as a quarterly cadence (inventory + cleanup) rather than a one-time project. Pair the inventory checker with a documented runbook for archive vs delete decisions, and for the offboarding ownership-transfer hook.
- **Security** — Group type (`Public` / `Private` / `Unlisted`) drives content visibility, and the defaults are not what casual users assume. "Public" includes Experience Cloud users on default visibility; Unlisted hides content from compliance discovery; Private is the most common safe choice for internal-sensitive content. Group governance is also a *deactivation* problem — orphaned groups owned by departed users are a low-frequency but real footgun for both operational continuity (no one can delete the group) and security (a deactivated user's group ownership prevents a clean offboarding posture).

## Architectural Tradeoffs

| Tradeoff | Why it matters |
|---|---|
| Open group creation vs perm-set restriction | Open creation drives engagement at the cost of sprawl; perm-set restriction stops sprawl at the cost of friction for ad-hoc collaboration. For orgs >100 users, restriction usually wins because the cost of dormant-group cleanup compounds nonlinearly. For orgs <50 users, leave it open and rely on social norms. |
| Archive vs delete dormant groups | Archive preserves audit trail at the cost of registry clutter; delete frees the namespace at the cost of permanent history loss. Default to archive for any group with >10 substantive posts or any post >12 months old (these have audit / institutional-memory value). Delete only empty / abandoned / clearly-test groups. |
| Public vs Private vs Unlisted | Public maximizes discoverability and serendipitous collaboration but exposes content to all internal users (and possibly community users). Private balances discovery and confidentiality (members-only posts, but the group's existence is public). Unlisted prioritizes confidentiality at the cost of all governance discoverability — even compliance can't find Unlisted groups via UI. Choose Unlisted only when the *existence* of the group must be confidential, not just the content. |
| Per-user owner vs steward service-account owner | Person-owners feel natural and create accountability ("Jane owns this") but generate re-orphan risk when Jane leaves. A "Chatter Stewards" service account is institutionally owned and never leaves the company; ownership is permanent. Trade some accountability for cleanup-cost reduction; pair the steward owner with a named human "manager" via `CollaborationGroupMember.CollaborationRole = 'Admin'` for day-to-day moderation. |
| Auto-archive aggressively (90 days) vs conservatively (180+ days) | Aggressive auto-archive keeps the active list clean but archives slow-burn standing groups (reference libraries, broadcast channels) prematurely. Conservative auto-archive keeps standing groups visible at the cost of slower cleanup of truly-dead groups. Set the org-wide value to match the *median* group lifecycle (usually 90–180 days for project-heavy orgs, 180–365 for team-heavy orgs). |
| Group Information Templates as policy enforcement | Templates encode policy at creation time but are advisory-only — users can ignore them. Combined with creation-permission restriction, they're highly effective. Standalone, they cut sprawl ~30% and that's it. The leverage is in the *combination* (perm-set + template + steward-account fallback). |

## Anti-Patterns

1. **Deleting groups en masse without archiving the substantive ones first.** Conversation history in `FeedItem` is a real audit trail — approval discussions, decision threads, customer escalations may live in there. A blanket "delete groups inactive >12 months" loses institutional memory permanently. Always do an archive-first pass; delete only the empty / clearly-disposable subset.
2. **Reassigning orphaned-owner groups to a department head ("VP of Sales").** The VP becomes the de facto owner of dozens of unrelated groups. When the VP leaves, you re-orphan everything. Use a named service account (`chatter.stewards@company.com`) instead — institutionally owned, never leaves.
3. **Treating Unlisted as "more secure than Private."** It's not — it's *less discoverable*. Members of Private groups are visible to all internal users (the group's existence is known); Unlisted groups hide existence too. For *security*, Private is sufficient. Unlisted should be reserved for cases where the group's existence is itself confidential (M&A working group, executive committee). Most "Unlisted" groups in the wild should be Private.
4. **Skipping the offboarding ownership-transfer step.** "We'll fix it later" produces the orphaned-owner problem. Doing the transfer at deactivation time is one query and one DML; doing it later requires a full-org audit. Bake into the offboarding checklist before the User record's `IsActive` flips.
5. **Creating a group for every short-term project without an end-of-life trigger.** Projects end; groups linger. The Group Information Template should make the end-of-life trigger explicit ("archive when project closes"). Without it, project groups become permanent fixtures and the active group count creeps upward forever.
6. **Letting end users freely change group type from Public → Private mid-life.** A group that started Public has accumulated content under "everyone can see" assumptions; flipping to Private makes that content invisible to non-members but doesn't notify them or migrate their participation. The transition is technically allowed but social-cost-heavy. Group type should be set at creation and changed only with admin involvement.

## Official Sources Used

- Salesforce Help — Set Up Salesforce Chatter — https://help.salesforce.com/s/articleView?id=sf.collab_setup_parent.htm
- Salesforce Help — Customize Chatter Settings — https://help.salesforce.com/s/articleView?id=sf.collab_admin_settings.htm
- Salesforce Help — Set Up Chatter Groups — https://help.salesforce.com/s/articleView?id=sf.collab_groups_setup.htm
- Salesforce Help — Manage Group Membership — https://help.salesforce.com/s/articleView?id=sf.collab_groups_membership.htm
- Salesforce Help — Archive Chatter Groups — https://help.salesforce.com/s/articleView?id=sf.collab_groups_archive.htm
- Salesforce Help — Group Information Templates — https://help.salesforce.com/s/articleView?id=sf.collab_groups_information_templates.htm
- Salesforce Help — Unlisted Chatter Groups — https://help.salesforce.com/s/articleView?id=sf.collab_groups_unlisted.htm
- Object Reference — `CollaborationGroup` — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_collaborationgroup.htm
- Object Reference — `CollaborationGroupMember` — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_collaborationgroupmember.htm
- Object Reference — `EntitySubscription` — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_entitysubscription.htm
- Chatter REST API Developer Guide — Group Resources — https://developer.salesforce.com/docs/atlas.en-us.chatterapi.meta/chatterapi/connect_resources_groups.htm
- Salesforce Well-Architected — Operational Excellence — https://architect.salesforce.com/docs/architect/well-architected/guide/operational-excellence.html
- Salesforce Well-Architected — Trusted (Security) — https://architect.salesforce.com/docs/architect/well-architected/guide/trusted.html
