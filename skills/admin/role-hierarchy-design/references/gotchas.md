# Gotchas — Role Hierarchy Design

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Hierarchy Access Is Not a Share Row, So Share Queries Lie About It

**What happens:** An admin is asked to prove that a regional manager can see a rep's opportunities. They query `OpportunityShare` (or `AccountShare`) filtered to the manager's user ID, get zero rows, and report that the manager has no access. Then the manager logs in and sees everything.

**Why:** Salesforce classifies record access into four grant types — explicit, group membership, inherited, and implicit. Only explicit and implicit grants are backed by rows in the Object Sharing table. Inherited grants, which is the category the role hierarchy falls into, are resolved at query time by joining the Object Sharing table to the Group Maintenance tables, which store direct and indirect membership for every system-defined group. A user above another user in the hierarchy is stored as an *indirect member* of that user's Role group; no per-record row is ever written for them.

The share object's schema is consistent with that, but do not try to prove it from the `RowCause` picklist, and be careful which version of that picklist you are reading. The current `AccountShare` reference lists "Valid values **include**" `Manual`, `Owner`, `Team`, `Rule`, `GuestRule`, `ImplicitParent`, `GuestParentImplicit`, `LpuParentImplicit`, `LpuImplicit`, `PortalImplicit`, `ARImplicit`, `Territory`, `Territory2AssociationManual` and the deprecated `TerritoryManual` — an open list of fourteen, not the short four-value list that older archived versions of the page show. An argument of the form "there is no hierarchy value in the list, therefore no hierarchy row" is unsound against a list the docs describe as open.

Two sentences on the same page do carry real weight, and they are stronger than the picklist argument:

- Share rows are not one-per-grant. "If a user has access to an account for one or more of the following RowCause values, the records in the AccountShare object are compressed into one record with the highest level of access" — `ImplicitParent`, `Manual`, `Owner`. A row count is therefore not a grant count.
- Share rows are not guaranteed to exist at all. "For some sharing mechanisms, such as sharing sets, sharing entries aren't stored at all", and Salesforce warns that "it's possible that we'll stop storing certain share records to improve performance. As a best practice, don't create customizations that rely on the availability of these sharing entries."

The load-bearing evidence for the hierarchy specifically is still the table split above: the Object Sharing table is documented as storing explicit and implicit grants only.

**When it occurs:** Any access audit, access-certification exercise, or "prove least privilege" review that is executed as SOQL against the `__Share` objects. It also bites the reverse case — an auditor concludes a sensitive object is safe because the share table is small, while the entire management chain is reading it through inheritance.

**How to avoid:** Prove hierarchy access by structure and by impersonation, not by share query.

```soql
-- Structure: who is above whom. Resolve the chain client-side; do not
-- assume a traversable ParentRole relationship name.
SELECT Id, Name, DeveloperName, ParentRoleId, PortalType,
       OpportunityAccessForAccountOwner, CaseAccessForAccountOwner,
       ContactAccessForAccountOwner
FROM UserRole
ORDER BY Name

-- The system-defined groups that carry inheritance. DoesIncludeBosses is
-- deliberately NOT selected here: the Object Reference scopes that field to
-- "groups of type Regular and Queue", so it tells you nothing about a Role group.
SELECT Id, Name, Type, RelatedId
FROM Group
WHERE Type IN ('Role', 'RoleAndSubordinates', 'RoleAndSubordinatesInternal')

-- The public-group / queue switch, queried on the types that actually carry it:
SELECT Id, Name, Type, DoesIncludeBosses
FROM Group
WHERE Type IN ('Regular', 'Queue')
```

`Group.RelatedId` is documented as "For Groups of type 'Role,' the ID of the associated UserRole." Salesforce creates up to three of these groups per role — `Role`, `RoleAndSubordinates` and `RoleAndSubordinatesInternal` — "depending on if digital experiences is enabled". Read that carefully before assuming which types exist: in the Record-Level Access group table the availability note sits on **`RoleAndSubordinates`**, described as "Only available when digital experiences is enabled for your org and Experience Cloud site users are created with external account roles other than a shared person account role", while `RoleAndSubordinatesInternal` is the variant whose direct members exclude portal subordinates. The `Group` Object Reference says the same thing independently: it puts that "Only available when digital experiences is enabled..." sentence on `RoleAndSubordinates` and attaches no availability gate to `RoleAndSubordinatesInternal`. Widen the `Type IN` list, or drop the filter, rather than assuming. Then confirm the effective result with Setup → Users → Login as, or Setup → Users → *user* → Sharing.

---

## Gotcha 2: Grant Access Using Hierarchies Is Two Independent Switches, and the Object-Level One Is Not in the Metadata

**What happens:** A team disables Grant Access Using Hierarchies on `Compensation_Plan__c` in the sandbox, validates it, deploys the object to production, and discovers that in production the whole management chain can still read the records. Separately, another team deselects the checkbox on a *public group* and expects it to stop object-level inheritance, which it does not.

**Why:** Two distinct settings carry the same label.

| | Object-level | Public-group-level |
|---|---|---|
| Location | Setup → Sharing Settings → Organization-Wide Defaults → Edit | Setup → Public Groups → New/Edit |
| API | none on `CustomObject` — that type exposes only `sharingModel` and `externalSharingModel` | `Group.DoesIncludeBosses` |
| Scope | all upward inheritance for that object | only records shared *to that group* |

The object-level checkbox is editable for custom objects only, and the Security Guide constrains it further: "You can only deselect this setting for custom objects that don't have a default access of `Controlled by Parent`." Because it is not represented on the `CustomObject` metadata type, it does not appear in a source diff, does not travel in a change set or package, and does not exist in a scratch org definition. It is org state, set by hand, in every environment.

**When it occurs:** Every promotion of a custom object that relies on the opt-out into an org that was built from source rather than copied from production — scratch orgs, fresh developer orgs, package installs into a new org. A sandbox refresh copies production's setting, which is why the gap usually surfaces first in a scratch org or in a brand-new target org, not in the full sandbox where the change was validated.

**How to avoid:** Treat the object-level setting as a manual post-deployment step with an owner and a checklist entry, the same way you treat a remote site setting. Verify it after every environment build. The Setup Audit Trail records changes to "Public groups, sharing rules, and org-wide sharing, including the Grant Access Using Hierarchies option", so drift is detectable after the fact even though it is not deployable.

Also note the knock-on effect on sharing rules: users in the hierarchy are automatically granted the same access that users below them get from a sharing rule, provided the object is a standard object or Grant Access Using Hierarchies is selected if the object is custom. Turning it off narrows every sharing rule on that object at the same time — usually the intent, occasionally a surprise.

---

## Gotcha 3: The Role's Access Levels Are About Accounts the Role Owns, and They Disappear When OWD Is Public Read/Write

**What happens:** An admin opens a role to set opportunity access and finds no such field on the page. Or they set `opportunityAccessLevel` to `Read` expecting it to limit what the role's users can do with opportunities generally, and instead nothing changes for opportunities on accounts the role's users do not own.

**Why:** Step 7 of creating a role is to specify the role's access to the child contacts, opportunities, and cases associated with accounts that users in the role **own**. The Security Guide is explicit that this access applies regardless of who owns the child records — a role can be given edit on all contacts under its accounts even where another user owns the contact. It says nothing about records unconnected to an owned account.

The fields are hidden, not defaulted, when the child object cannot be restricted: "If a child object's organization-wide default is Public Read/Write, you can't specify access, because you can't use the role hierarchy to restrict access further than your organization-wide defaults. If the organization-wide default for contacts is Controlled by Parent, you also can't specify access."

In the Metadata API these are `caseAccessLevel`, `contactAccessLevel`, and `opportunityAccessLevel`, each taking `Read`, `Edit`, or `None`. The fallback is widely misquoted as "organization settings"; what `RoleOrTerritory` — the shared base type behind both `Role` and `Territory` — actually says of each field is: "If no value is set for this field, this field value uses the default access level that is specified in the Manage Territory page in Setup." On the `UserRole` object they are `CaseAccessForAccountOwner`, `ContactAccessForAccountOwner`, and `OpportunityAccessForAccountOwner` — the last of which is a **required** field, and which per the Object Reference cannot be set "with an opportunity access less than that specified in organization-wide defaults". `ContactAccessForAccountOwner` cannot be created or updated at all when `DefaultContactAccess` is Controlled by Parent.

**When it occurs:** Most often during an OWD tightening project. When Opportunity moves from Public Read/Write to Private, the three settings become visible and meaningful on every role at once, and whatever they defaulted to becomes live policy. It also occurs when Account OWD is set to Private, which forces Opportunity and Case OWD to Private and Contact to Private or Controlled by Parent.

**How to avoid:** Set all three explicitly on every role in the design, including `None` where a branch must not pick up account children. Deploy them as part of the `.role-meta.xml` rather than leaving them to a platform default that never appears in a source diff. Before an OWD change, dump the current values for every role and diff them against intent.

---

## Gotcha 4: Reparenting Is the One Operation That Blocks Almost Everything Else

**What happens:** During a quarter-end realignment, an admin moves a role to a different branch while an integration is provisioning users. Both operations fail intermittently. The user-facing text is a "could not acquire lock" or "Group membership operation already in progress" error, and the operation must be repeated.

**Why:** The sharing system locks the tables holding group membership information during updates, to prevent incompatible simultaneous updates or timing issues that could produce inaccurate access data. Granular locking is enabled by default and lets unrelated operations proceed in parallel — groups in separate hierarchies can be manipulated concurrently, user provisioning can occur in parallel, and even "a single long-running process, such as a role delete, blocks only a small subset of operations." Reparenting is the documented exception: "certain operations, such as reparenting (moving roles within the role hierarchy), still block almost all other group updates."

Locks are normally held very briefly. They are held long enough to collide when a change in role triggers a sharing rule recalculation, which is exactly the situation during a realignment.

**When it occurs:** Periodic organizational realignment events — end-of-year, end-of-quarter — where many account assignments and user roles change at once, and large-scale data loads or integrations are running concurrently. Deployments and Apex tests that touch group membership cause the same collision; the guidance is to wait for the deployment or Apex tests to finish.

**How to avoid:** Schedule separate group maintenance processes so they do not overlap. Implement retry logic in integrations and automated group maintenance. If parallel processing produces lock errors, fall back to serial processing. Move roles in a window with no data loads, no deployments, and no test runs. Where the org supports it, defer sharing calculations before large-scale updates and restart and recalculate later — the Security Guide recommends exactly this when sharing evaluations time out.

---

## Gotcha 5: Portal Roles Are Invisible in Setup, Immutable via the API, and They Follow the Account Owner

**What happens:** An admin counts roles in Setup → Roles, gets a number well under the ceiling, and is then surprised by a role-count problem. Or an integration tries to update a role and fails. Or a routine account-owner change on a partner account triggers a long recalculation nobody predicted.

**Why:** Roles for customer and partner users are not included on the role hierarchy setup page. They exist in the hierarchy nonetheless: for each portal-enabled account, 1–3 roles are appended to the main hierarchy below the account owner's role. The `UserRole` object exposes them through `PortalType` (`None` for a Salesforce application role, `CustomerPortal`, or `Partner`) and `PortalRole` (`Executive`, `Manager`, `User`, or `PersonAccount`), and the Object Reference states flatly: "You can't update any field for a portal role."

Because those roles hang below the account owner's role, ownership is load-bearing. When a user with portal-enabled accounts moves roles, Salesforce removes the portal roles from the old role and appends them to the new role for every portal-enabled account that user owns, deleting the shares written to the old role and adding them to the new one. Changing the owner of a portal account does the same reparenting plus adjusts sharing for all of the data associated with that account — which is why "changing the name of the user in the Account Owner field" can be an expensive operation.

**When it occurs:** Partner or customer account owner changes, channel-manager turnover, and any user role change where the user owns partner accounts. Also whenever sharing rules use portal roles as a source group: those rules may need recalculation and may no longer be valid after a move, in which case an admin must modify or delete them.

**How to avoid:** Inventory portal roles by query rather than by the Setup page, and budget role headroom for them before enabling portal access on a new tranche of accounts.

```soql
SELECT Id, Name, PortalType, PortalRole, ParentRoleId
FROM UserRole
WHERE PortalType != 'None'
```

Treat "change the owner of a partner account" as a scheduled maintenance operation, not a data edit. Note also that high-volume Experience Cloud site users have no role at all, so they cannot be included in owner-based sharing rules or granted access to user records via a sharing rule; plan their access through guest-user or criteria-based sharing rules and share groups instead.

<!-- UNVERIFIED: whether portal roles are counted against the same 500/5,000 org role ceiling as internal roles. The 1-3-roles-per-portal-account figure is sourced (Record-Level Access: Under the Hood); the interaction with the ceiling is not documented in any source fetched for this skill. Budget headroom conservatively and confirm with Salesforce Support before enabling portal access at scale. -->

---

## Gotcha 6: Ownership Skew Turns a Role Change Into a Multi-Hour Recalculation

**What happens:** A migration user or an "unassigned leads" bucket user owns a very large share of an object's records. Someone assigns that user to a role, or moves them, or adds them to a public group that is the source of a sharing rule. The operation runs for hours, holds locks, and takes unrelated admin work down with it.

**Why:** Ownership data skew is defined as a single user owning more than 10,000 records of an object. It commonly arises from concentrating ownership so that a single user or queue, or all the members of a single role or public group, owns most or all records for a particular object. When such a user moves around the hierarchy, or into or out of a role or group that is a sharing-rule source, Salesforce must adjust a very large number of entries in the sharing tables, which leads to a long-running recalculation of access rights. The Large Data Volumes best-practice table states the rule with no qualification: "Avoid having any user own more than 10,000 records."

**When it occurs:** Data migrations that park records on a service account; lead pools; integration users that own everything they create; and any org that uses a single "system" user as a catch-all owner.

**How to avoid:** Distribute ownership across more users where the business allows it. Where concentration is genuinely required, the documented mitigation is to not assign that user to a role at all. If the user must have a role in order to share data:

- Place them in a separate role at the top of the hierarchy, accepting that this user then inherits access to all data owned by or shared with users below them.
- Never move them out of that top-level role, to avoid triggering sharing recalculations.
- Keep them out of public groups that can be used as the source for sharing rules.

The same reasoning applies to a large volume of data owned by or visible to the users under a single partner or customer account: changing that account's owner, or moving those users in the hierarchy, forces recalculation of all the sharing and inheritance for all the data under the account.

Deep treatment of skew detection and remediation lives in `skills/admin/data-skew-and-sharing-performance`.

---

## Gotcha 7: Role-Based Sharing Targets Were Renamed and the Behaviour Depends on the Org's Creation Date

**What happens:** A sharing rule or public group is built against "Roles and Subordinates", the metadata is promoted to another org, and the member type either is not offered or does not mean what it meant in the source org.

**Why:** The category list for sharing rule and public group members now distinguishes internal from portal subordinates, and availability is gated on org age and on whether digital experiences is enabled. The Security Guide describes "Roles and Subordinates" as "Only available in production orgs created before February 8, 2024 and in non-preview sandboxes if digital experiences or portals aren't enabled for your organization." "Roles and Internal Subordinates" — all users in the role plus all users in roles below it, excluding site and portal roles — "is available by default" in orgs created on February 8, 2024 or later and in preview sandboxes, and in older production orgs "after digital experiences or portals are enabled." A third category, "Roles, Internal and Portal Subordinates", includes site and portal roles and is "only available when digital experiences or portals are enabled for your org."

**When it occurs:** Any cross-org promotion of sharing rules or public groups, any org that enables digital experiences after the fact, and any sandbox refresh where the sandbox is a preview instance and production is not.

**How to avoid:** Check the target org's available member types before writing sharing metadata against a role, rather than assuming the source org's list. The API-name side of this rename, and the transitional dynamic translation Salesforce applies to old references, are covered in depth in `skills/admin/queues-and-public-groups` Gotcha 6 — read that before rewriting metadata.

[STALE-RISK: the February 8, 2024 cutover and the digital-experiences gating are release-update driven. Re-verify the available member types and their availability conditions in the current Security Guide before relying on any of the three category names.]

---

## Gotcha 8: A Role Change Is a Forecast-Hierarchy Change

**What happens:** After a reorganisation, opportunity access looks correct but forecasts roll up to the wrong person, or a manager cannot see a subordinate's forecast at all.

**Why:** The forecast manager is an attribute of the *role*, not of the user: `UserRole.ForecastUserId` is documented as "The ID of the forecast manager associated with this role", `UserRole.RollupDescription` as "Description of the forecast rollup", and `UserRole.MayForecastManagerShare` indicates "whether the forecast manager can manually share their own forecast" (`mayForecastManagerShare` in the `Role` metadata type). Forecast visibility is governed separately from record access: the Security Guide lists it among the org-wide-default exceptions — "Users can view forecasts only of users and territories below them in the forecast hierarchy, unless forecast sharing is enabled."

**When it occurs:** Any reparent, any role deletion, and any change of the user who holds a forecast-manager assignment.

**How to avoid:** Include a forecast-hierarchy verification step in every role-change runbook. Query the assignments before and after:

```soql
SELECT Id, Name, ParentRoleId, ForecastUserId, RollupDescription, MayForecastManagerShare
FROM UserRole
WHERE ForecastUserId != NULL
```

<!-- UNVERIFIED: the exact rollup mechanics of Collaborative Forecasts when a role is reparented mid-period. The role-level forecast-manager fields above are sourced from the UserRole Object Reference and the Role metadata type; no fetched source documents what happens to in-flight forecast data during a reparent. Test in a sandbox before a live reorg. -->
