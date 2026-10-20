# Well-Architected Notes — Privileged Access Management (PAM)

## Relevant Pillars

| Pillar | How this skill contributes |
|---|---|
| **Security** | The deliverable is the removal of standing admin-equivalent grants, not the addition of another control. "Modify All Data" edits every record of every object while storing no object permission record, so the only honest measure of blast radius is the count of people holding it today. |
| **Reliability** | The dominant failures are self-inflicted and silent. A session-based permission set folded into a permission set group stops requiring activation. A permission set group sitting at `Outdated` or `Failed` is not a safe grant target (UNVERIFIED (2026-10-20): that it accepts the assignment silently is Help-only). |
| **Operational Excellence** | An inventory is true only on the day it ran, and running it needs View Setup and Configuration or an equivalent. The reporting identity, the review cadence, and the export schedule against the 180-day `SetupAuditTrail` floor are part of the design, not follow-up work. |

## Architectural Tradeoffs

- **Session activation versus a dated expiration.** A session-based grant ends when the session does, which is the tightest window available. `PermissionSetAssignment.ExpirationDate` is a `dateTime` the platform enforces without any job of yours, but it keeps privilege alive for a wall-clock window the requester may have walked away in. Session activation costs an activation step and a `SessionPermSetActivation` reader that itself needs Setup-read privilege.
- **Platform expiry versus a scheduled revoker.** Custom scheduled Apex can express policy the platform cannot, at the cost of a job that fails silently and leaves standing privilege behind — precisely the outcome PAM exists to prevent. It also has to model re-targeting correctly, since `AssigneeId`, `PermissionSetId`, and `PermissionSetGroupId` are Create-only and a move is a delete plus an insert.
- **Permission set group versus individual permission sets as the elevation unit.** The group gives one assignment, one expiry, and one `HasActivationRequired` flag. It also inserts recalculation between the grant and the permission — `Updated`, `Outdated`, `Updating`, `Failed` (obj 264 L220011-220015) — and it strips the activation requirement off any session-based member (L264383-264384).
- **Detection versus pre-approval for break-glass.** An approval gate standing between an engineer and a production incident gets bypassed; detection cannot be. The cost lands on the evidence pipeline: `SetupAuditTrail` supports only `query()` and `retrieve()`, refuses aggregate queries, and retains at least 180 days, so detection is really an export design.
- **Delegated administration versus central administration.** Delegation shrinks the standing-admin population, then moves the risk onto a `DelegateGroup`'s assignable `profiles`, `permissionSets`, and `permissionSetGroups` lists plus its `loginAccess` flag. Fewer admins, more surfaces to review.

## Anti-Patterns

1. Counting admins by profile name rather than by the permission actually held.
2. Provisioning a PAM auditor identity without the Setup-read permissions the inventory objects require, then trusting the empty result it returns.
3. Reviewing standing privilege on a cadence longer than the Setup Audit Trail retention floor, so the evidence expires before the review reaches it.
4. Placing a session-based permission set inside a permission set group for assignment convenience.
5. Treating permission set group recalculation status as a post-mortem detail rather than a precondition of the grant.
6. Sharing one break-glass account across a team, which destroys the attribution the control exists to produce.
7. Adding profiles or permission sets carrying admin-equivalent permissions to a delegate group's assignable lists without a review step.

## Official Sources Used

- Object Reference (264) — `PermissionSetAssignment`: Special Access Rules (obj 264 L219705-219708), `ExpirationDate` (L219739-219745), `IsActive` (L219747-219753), `IsRevoked` (L219755-219762), delete-and-insert to update (L219864-219865), revoked `ALL ROWS` example (L219899-219901).
- Object Reference (264) — `PermissionSet.IsOwnedByProfile` (obj 264 L219414-219419) and the profile-owned Name/Label warning (L219684-219685); `PermissionSetGroup` `HasActivationRequired` (L219948-219954) and `Status` (L220006-220015).
- Object Reference (264) — `SessionPermSetActivation`: definition (obj 264 L264375-264377), supported calls (L264381), the group note (L264383-264384), Apex activate/deactivate example (L264509-264514, L264542-264543); `SetupAuditTrail` 180-day floor, no standard controller, no aggregates (L264576-264587), `DelegateUser` (L264628-264634); `PermissionUpdateEventLog` (L221839-221850); `UserPermissionAccess` (L303748-303752); `ObjectPermissions` Modify All Data note (L192721-192724).
- Metadata API Developer Guide (264) — `PermissionSet.hasActivationRequired` (api_meta 264 L97521-97523), `PermissionSetGroup` fields (L98032-98051), `DelegateGroup.loginAccess` / `profiles` (L53416, L53427), `psaExpirationUIEnabled` (L132107-132111), Flow `activateSessionPermSet` / `deactivateSessionPermSet` (L71098, L71249).
- Salesforce Security Guide (262) — Setup Audit Trail download and 180-day deletion (secguide 262 L4974-4975); assignment-expiration change tracking (L5034).
- Not corpus, used only for claims marked UNVERIFIED: Salesforce Developers blog, Boost Security by Auditing Your Privileged Users with SOQL — https://developer.salesforce.com/blogs/2021/05/boost-security-by-auditing-your-privileged-users-with-soql
