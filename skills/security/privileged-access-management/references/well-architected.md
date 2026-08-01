# Well-Architected Notes — Privileged Access Management (PAM)

## Relevant Pillars

| Pillar | How this skill contributes |
|---|---|
| **Security** | The deliverable is the removal of standing admin-equivalent grants, not the addition of another control. "Modify All Data" edits every record of every object while storing no object permission record, so the only honest measure of blast radius is the count of people holding it today. |
| **Reliability** | The dominant failures are self-inflicted and silent. A session-based permission set folded into a permission set group stops requiring activation. A permission set group sitting at `Outdated` or `Failed` accepts the assignment and delivers nothing. Neither raises an error. |
| **Operational Excellence** | An inventory is true only on the day it ran, and running it needs View Setup and Configuration or an equivalent. The reporting identity, the review cadence, and the export schedule against the 180-day `SetupAuditTrail` floor are part of the design, not follow-up work. |

## Architectural Tradeoffs

- **Session activation versus a dated expiration.** A session-based grant ends when the session does, which is the tightest window available. `PermissionSetAssignment.ExpirationDate` is a `dateTime` the platform enforces without any job of yours, but it keeps privilege alive for a wall-clock window the requester may have walked away in. Session activation costs an activation step and a `SessionPermSetActivation` reader that itself needs Setup-read privilege.
- **Platform expiry versus a scheduled revoker.** Custom scheduled Apex can express policy the platform cannot, at the cost of a job that fails silently and leaves standing privilege behind — precisely the outcome PAM exists to prevent. It also has to model re-targeting correctly, since `AssigneeId`, `PermissionSetId`, and `PermissionSetGroupId` are Create-only and a move is a delete plus an insert.
- **Permission set group versus individual permission sets as the elevation unit.** The group gives one assignment, one expiry, and one `HasActivationRequired` flag. It also inserts recalculation between the grant and the permission — `Updated`, `Outdated`, `Updating`, `Failed` — with no assignment-level error, and it strips the activation requirement off any session-based member.
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

- Object Reference — PermissionSetAssignment — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_permissionsetassignment.htm — used for the Create-only field properties, the delete-and-insert rule, `ExpirationDate`, `IsActive`, `IsRevoked`, and the Special Access Rules.
- Object Reference — PermissionSet — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_permissionset.htm — used for `IsOwnedByProfile`, the profile-owned name and label warning, and the `describeSObjects()` instruction for permission names.
- Object Reference — ObjectPermissions — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_objectpermissions.htm — used for the "Modify All Data" behaviour: no stored records, the `000` ID, and the OR-in-the-parent query.
- Object Reference — PermissionSetGroup — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_permissionsetgroup.htm — used for the four `Status` values and `HasActivationRequired` in API version 53.0 and later.
- Object Reference — SessionPermSetActivation — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_sessionpermsetactivations.htm — used for the Note that group membership removes the session-activation requirement, and the object's access rules.
- Object Reference — SetupAuditTrail — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_setupaudittrail.htm — used for the no-aggregates rule, the standard-controller restriction, the 180-day floor, `DelegateUser`, and `CreatedByContext`.
- Object Reference — UserPermissionAccess — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_userpermissionaccess.htm — used for its current-user-only scope and supported calls.
- Object Reference — PermissionUpdateEventLog — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_permissionupdateeventlog.htm — used for detecting session-activation changes, in API version 65.0 and later, with View Event Log Object Data.
- Metadata API Developer Guide — DelegateGroup — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_delegategroup.htm — used for the assignable `profiles`, `permissionSets`, and `permissionSetGroups` lists and the `loginAccess` flag.
- Salesforce Developers — Boost Security by Auditing Your Privileged Users with SOQL — https://developer.salesforce.com/blogs/2021/05/boost-security-by-auditing-your-privileged-users-with-soql — used for the privileged permission field names and the two published admin-audit queries.
