---
name: role-hierarchy-design
description: "Use when designing or maintaining the role hierarchy as a record-access mechanism. Trigger keywords: role hierarchy, manager cannot see subordinate records, grant access using hierarchies, role reparenting, portal role, how deep should the role hierarchy be, design the role hierarchy. NOT for territory models - use admin/enterprise-territory-management. NOT for rule-based grants - use admin/sharing-rules. NOT for the overall model - use admin/sharing-and-visibility."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Performance
  - Scalability
triggers:
  - "how deep should the role hierarchy be before it starts hurting performance"
  - "why can't my sales manager see the opportunities their rep owns"
  - "design a role hierarchy for a sales and service org with 1,200 users"
  - "what actually happens when I move a user to a different role"
  - "can I turn off grant access using hierarchies on a standard object"
  - "changing a user's role throws a could not acquire lock error"
  - "should this be a role or a territory or a public group"
  - "how many roles can I create in my Salesforce org"
  - "my manager lost visibility after I reparented a role in the hierarchy"
tags:
  - role-hierarchy
  - record-access
  - sharing
  - owd
  - grant-access-using-hierarchies
  - sharing-recalculation
  - portal-roles
  - access-control
inputs:
  - "Org-wide defaults per object: the hierarchy only grants anything where OWD is Private or Public Read Only"
  - "Which access requirements are vertical (manager sees subordinate) versus horizontal (peer sees peer)"
  - "Existing role count and the org's creation date, which decides the 500 vs 5,000 role ceiling"
  - "Whether Experience Cloud / partner or customer portal accounts exist, and who owns them"
  - "Whether any user owns more than 10,000 records of a single object (ownership skew)"
  - "Planned maintenance window, because role reparenting blocks almost all other group updates"
outputs:
  - "A role hierarchy design keyed to record-access requirements, not to the org chart"
  - "Deployable `Role` metadata with parentRole and the three account-child access levels set"
  - "A Grant Access Using Hierarchies decision per custom object, with the Controlled by Parent exclusions called out"
  - "A role-change runbook covering recalculation, locking, and portal-role side effects"
  - "A list of access requirements that the hierarchy cannot satisfy, routed to sharing rules, territories, or Apex managed sharing"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-08-15
---

# Role Hierarchy Design

This skill activates when the role hierarchy is being designed, extended, restructured, or blamed for a record-access problem. It treats the hierarchy as one access mechanism among several — the one that grants access upward, along a single branch, and nowhere else.

---

## Before Starting

Gather this context before touching a role:

- **Get the OWD table first.** Access grants exist only where an object's org-wide default is Private or Public Read Only. Where both the internal and external OWD are Public Read/Write, the object does not even get an Object Sharing table, so no hierarchy design changes anything. Every role conversation that starts before the OWD table is on the page ends in a redesign.
- **Separate vertical from horizontal requirements.** "The VP must see everything under them" is vertical and the hierarchy handles it. "The four EMEA reps must see each other's pipeline" is horizontal and the hierarchy will never handle it — that is `admin/sharing-rules` territory.
- **Find out when the org was created.** Orgs created in Spring '21 or later can create up to 5,000 roles; older orgs default to 500 and must ask Salesforce Customer Support to raise it. The Spring '21 release note is explicit that the point is not to use the headroom: "to improve performance, it's best to set up roles based on data access and eliminate any roles that aren't needed."
- **Count portal-enabled accounts.** For each portal-enabled account, 1–3 roles are appended to the main hierarchy below the account owner's role. These roles never appear on the Roles setup page and cannot be edited through the API.
- **Look for ownership skew before you move anyone.** A single user owning more than 10,000 records of an object is the configuration that turns a routine role change into a multi-hour recalculation. See `references/gotchas.md` Gotcha 6 for the placement rule that avoids it.
- **Confirm who holds the permissions.** Viewing roles requires **View Roles and Role Hierarchy**; creating, editing, and deleting them requires **Manage Roles**; assigning users to roles requires **Manage Internal Users**; changing OWD and the object-level Grant Access Using Hierarchies checkbox requires **Manage Sharing**, because both live on the Sharing Settings page. The identically labelled checkbox on a public group is a different screen with a different gate — creating or editing a public group requires **Manage Users**. Roles are available in Professional, Enterprise, Performance, Unlimited, and Developer Editions.

---

## Core Concepts

### What the hierarchy actually grants

Users at any role level can view, edit, and report on all data that is owned by or shared with users below them in their role hierarchy. The Salesforce Security Guide documents exactly two exceptions to that sentence:

1. For custom objects, Grant Access Using Hierarchies can be disabled on the Sharing Settings page. When disabled, only the record owner and users who are granted access have access to the custom object's records.
2. After a folder is shared with a role, it is visible only to users in that role, not to superior roles in the hierarchy.

Everything else about the hierarchy follows from three mechanical facts:

| Fact | Consequence for design |
|---|---|
| Hierarchy access is an **inherited grant**. Object Sharing tables "store the data that supports explicit and implicit grants"; group membership and inherited grants live in the Group Maintenance tables and are resolved by a join at query time | There is no share row that says "manager", and the table split is the evidence for that. Do not argue it from `AccountShare.RowCause`: the current Object Reference lists "Valid values **include**" fourteen causes (Manual, Owner, Team, Rule, GuestRule, ImplicitParent, GuestParentImplicit, LpuParentImplicit, LpuImplicit, PortalImplicit, ARImplicit, Territory, Territory2AssociationManual, TerritoryManual) and still qualifies the list as open, so its contents cannot prove what is absent. The same page adds that rows for `ImplicitParent` / `Manual` / `Owner` "are compressed into one record with the highest level of access", and that for some mechanisms "sharing entries aren't stored at all". A share query cannot prove or disprove manager access. |
| Salesforce materialises up to three system-defined groups per role — `Role`, `RoleAndSubordinates`, and `RoleAndSubordinatesInternal` — "depending on if digital experiences is enabled". The availability note in that table sits on **`RoleAndSubordinates`**, not on the `Internal` variant | Every user above a role is stored as an **indirect member** of that role's group. Depth is not free: it is rows. Check which group types the org actually has before writing a query that assumes one. |
| Access flows **up one branch only** | Two peers in different branches never see each other through the hierarchy, no matter how close their boxes are on the org chart. |

The practical test: if the requirement can be expressed as "everyone above X in exactly one chain", the hierarchy is the right tool. Anything else needs a different mechanism.

### Grant Access Using Hierarchies

Two independent switches share this label. Confusing them is the most common configuration error in this domain.

| Switch | Where | API surface | Effect |
|---|---|---|---|
| Object-level | Setup → Sharing Settings → Organization-Wide Defaults → Edit | Not exposed on the `CustomObject` metadata type — only `sharingModel` and `externalSharingModel` are | Turns off upward inheritance for that object entirely |
| Public-group-level (and, from API 67.0, queues) | Setup → Public Groups → New/Edit | `Group.DoesIncludeBosses`, which "corresponds to the Grant Access Using Hierarchies checkbox on the detail pages of public groups and queues" and "is only available for groups of type Regular and Queue" | Controls whether records shared *with that group* also reach users above the group's members |

Constraints on the object-level switch, verbatim from the Security Guide: it can be deselected only for custom objects, and "You can only deselect this setting for custom objects that don't have a default access of `Controlled by Parent`." Standard objects have no editable checkbox at all. Changes to it are recorded in the Setup Audit Trail alongside public groups, sharing rules, and org-wide sharing.

The switch also governs how sharing rules propagate: users in the role hierarchy are automatically granted the same access that users below them get from a sharing rule, provided the object is a standard object, or Grant Access Using Hierarchies is selected if the object is custom. Turning it off on a custom object therefore silently narrows every sharing rule on that object too.

For the public-group switch, the Security Guide gives one concrete tuning instruction: deselect Grant Access Using Hierarchies when creating a public group with All Internal Users as members, which optimizes performance for sharing records with groups.

### The three access levels stored on the role

A role carries its own access settings for the child records of accounts that its users **own** — and that access applies regardless of who owns the child records.

| Metadata field | UserRole field | Valid values | Unavailable when |
|---|---|---|---|
| `caseAccessLevel` | `CaseAccessForAccountOwner` | `Read`, `Edit`, `None` | Case sharing model is Public Read/Write |
| `contactAccessLevel` | `ContactAccessForAccountOwner` | `Read`, `Edit`, `None` | Contact sharing model is Public Read/Write **or** Controlled by Parent |
| `opportunityAccessLevel` | `OpportunityAccessForAccountOwner` | `Read`, `Edit`, `None` | Opportunity sharing model is Public Read/Write |

`OpportunityAccessForAccountOwner` is a required field on `UserRole`, and the Object Reference adds that "you can't set a user role with an opportunity access less than that specified in organization-wide defaults." When an org tightens Opportunity OWD from Public Read/Write to Private, these settings appear on the role edit page for the first time carrying whatever the platform supplied. Do not assume that fallback is "organization settings": the `RoleOrTerritory` metadata reference says of each of the three fields, "If no value is set for this field, this field value uses the default access level that is specified in the Manage Territory page in Setup." Whatever it resolves to, it is not a value your repository chose — which is why an OWD change frequently produces a wave of "the account team lost the opportunity" tickets that has nothing to do with the hierarchy shape.

A deployable role, with the child-record access made explicit rather than defaulted:

```xml
<!-- force-app/main/default/roles/EMEA_Sales_Manager.role-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<Role xmlns="http://soap.sforce.com/2006/04/metadata">
    <name>EMEA Sales Manager</name>
    <description>Field sales managers, EMEA. Inherits rep-owned records one level down.</description>
    <parentRole>EMEA_Sales_VP</parentRole>
    <caseAccessLevel>Read</caseAccessLevel>
    <contactAccessLevel>Edit</contactAccessLevel>
    <opportunityAccessLevel>Read</opportunityAccessLevel>
    <mayForecastManagerShare>false</mayForecastManagerShare>
</Role>
```

The `Role` metadata type has been available since API version 24.0; files use the `.role` suffix and live in the `roles` directory. `parentRole` takes the parent's `fullName`, so a deployment that includes a child role but not its parent fails on an unresolved reference.

### Depth, and what depth actually costs

None of the sources listed in `references/well-architected.md` documents a maximum number of *levels*. What is documented is a maximum number of *roles* (500 or 5,000, above) and a mechanism that makes depth expensive. Do not supply the missing number from memory — see `references/llm-anti-patterns.md` Anti-Pattern 1.

- Each level adds indirect members to every Role group beneath it. A user near the top of a branch is an indirect member of every role group in the subtree below them.
- Moving a role reparents that whole subtree. The Designing Record Access for Enterprise Scale guide is blunt about the cost: moving a whole role means Salesforce "must do all of the work involved in moving a single user for all users in the role being moved and for all of those users' data."
- Reparenting is the operation with the worst concurrency profile. Granular locking is on by default and lets unrelated group operations run in parallel, but "certain operations, such as reparenting (moving roles within the role hierarchy), still block almost all other group updates." A role *delete*, by contrast, "blocks only a small subset of operations."

So the design rule is not a number, it is a shape: add a level only when a real access requirement needs an intermediate viewer. Levels that exist purely to mirror reporting lines add recalculation cost and grant nothing new, because a user two levels up already inherits everything a user one level up inherits.

### Role changes are asynchronous, and portal roles move with the account

When groups, roles, and territories are edited, sharing rules are recalculated to add or remove access as needed, and "depending on the nature of your updates and your org's setup, these sharing calculations can take a while to complete." The Setup UI returns before that work is done. The documented monitoring surface is the Background Jobs page; a completion email is documented for org-wide default recalculation specifically, so plan the cutover around the Background Jobs page rather than around an email.

Moving a *user* between roles triggers, per the enterprise-scale guide: new indirect membership for everyone above the new role, share adds and removes when the two roles have different account-child access settings, group membership changes plus share reparenting for every portal-enabled account that user owns, and recalculation of every sharing rule that names the old or new role in its source group. Managers above the old role lose access to that user's data as part of normal inheritance, with no table updates required.

---

## Common Patterns

### Pattern: two branches with a deliberately thin root

**When to use:** Sales and Service must not inherit each other's records, but a small executive group must see both.

**How it works:**
1. Create one top role (`Executive`) and assign only the users who genuinely need org-wide visibility. Everyone in it inherits everything below, so treat membership as a privilege review, not an org-chart exercise.
2. Create `Sales_VP` and `Service_VP` as siblings under it. Neither inherits from the other.
3. Hang functional roles under each VP only where a real "must see subordinate records" requirement exists.
4. Set `opportunityAccessLevel` on the Service branch roles to `None` so that service users who own accounts do not pick up opportunity access on those accounts.
5. Give cross-branch requirements to sharing rules, not to a shared parent role.

**Why not one deep chain:** Collapsing both functions into a single chain forces every Service manager to sit under, or above, Sales roles. Once that is built, there is no exit that is not structural. Opportunity is a standard object, so there is no Grant Access Using Hierarchies checkbox to switch off — and restriction rules are not a fallback either, because the Security Guide scopes them to "custom objects, external objects, contracts, events, quotes, tasks, time sheets, and time sheet entries". Opportunity is on none of those lists. The only remaining correction is to reshape the hierarchy, which is the most expensive operation in this domain.

### Pattern: opting a sensitive custom object out of inheritance

**When to use:** A custom object such as `Compensation_Plan__c` must be visible to its owner and to named reviewers only, never to the owner's management chain.

**How it works:**
1. Set the object's OWD to Private. Confirm it is not on the detail side of a master-detail relationship — a custom object on the detail side of a master-detail with a standard object has its OWD set to Controlled by Parent and it is not editable.
2. In Setup → Sharing Settings → Organization-Wide Defaults → Edit, deselect Grant Access Using Hierarchies for that object.
3. Grant the reviewers access with a criteria-based sharing rule targeting a public group, and deselect Grant Access Using Hierarchies on that group as well if the reviewers' own managers must stay out.
4. Record the decision — the checkbox is not in the `CustomObject` metadata, so it does not travel with a deployment and it will not appear in a source diff.

**Why not a restriction rule:** Restriction rules filter what specified users can access; they are the right tool when only *some* users must be narrowed. When *nobody* should inherit upward, turning the inheritance off at the object is one switch instead of a rule per persona.

### Pattern: parking a high-volume owner outside the hierarchy

**When to use:** An integration user, migration user, or "unassigned leads" bucket owns a very large share of an object's records.

**How it works:**
1. Confirm the skew: a single user owning more than 10,000 records of an object is the documented threshold at which sharing computations become a problem.
2. If that user does not need to share data through roles, leave them with **no role at all**.
3. If a role is required, place them in a separate role at the top of the hierarchy — noting that this user then inherits access to all data owned by or shared with users below them — never move them out of it, and keep them out of public groups used as the source for sharing rules.

**Why not just assign them to the obvious functional role:** Moving a skewed owner into or out of a role, or into or out of a sharing-rule source group, forces Salesforce to adjust a very large number of sharing-table entries, which is what produces the long-running recalculations and the lock errors covered in `references/gotchas.md`.

---

## Decision Guidance

| Situation | Mechanism | Reason |
|---|---|---|
| Manager must see everything their reports own | Role hierarchy | This is the only thing the hierarchy does natively |
| Peers at the same level must see each other's records | Sharing rule with a public group | Access flows up a branch, never sideways |
| A user must see records across several unrelated branches | Sharing rule, or territories if the axis is account-based | Roles are single-parent; a user holds exactly one role |
| Coverage is account-based and multi-dimensional (geography × segment × product) | Enterprise Territory Management — `admin/enterprise-territory-management` | Territories allow many-to-many account-to-user coverage; roles cannot |
| A custom object must not roll up to management | OWD Private + deselect Grant Access Using Hierarchies | The only supported way to stop inheritance, and only for custom objects |
| A standard object must not roll up to management | Reshape the hierarchy so the chain does not sit above the owner, or move the data to a custom object | The Grant Access Using Hierarchies checkbox is not editable for standard objects, and restriction rules are not a fallback for most of them — they cover only custom objects, external objects, contracts, events, quotes, tasks, time sheets and time sheet entries |
| Records shared to a group must not reach the group members' managers | Deselect Grant Access Using Hierarchies on the public group (`Group.DoesIncludeBosses`) | Separate switch from the object-level one |
| Access rule cannot be expressed declaratively at all | Apex managed sharing — `security/apex-managed-sharing-patterns` | `__Share` rows with a custom row cause |
| Object OWD is Public Read/Write | Do nothing to the hierarchy | Everyone already has access; the hierarchy is inert |
| Need to grant *object* or *field* access | Permission sets, not roles | Roles never grant CRUD or FLS |

---

## Recommended Workflow

1. **Build the OWD × requirement matrix.** For each object in scope, record the internal OWD, the external OWD, and whether the requirement is vertical or horizontal. Drop every object whose OWD is Public Read/Write — the hierarchy cannot affect it.
2. **Draft the hierarchy from access requirements only.** Add a level only where a named person must see records owned by a named group. Do not transcribe the org chart. Record, for each role, the reason it exists; a role with no access justification is a role to delete.
3. **Set the three account-child access levels explicitly on every role** (`caseAccessLevel`, `contactAccessLevel`, `opportunityAccessLevel`). An unset field falls back to a platform default the metadata reference describes as "the default access level that is specified in the Manage Territory page in Setup" — a decision made by accident, and one that never shows up in a source diff.
4. **Decide Grant Access Using Hierarchies per custom object** and write the decision down outside the metadata, since it is not part of the `CustomObject` source.
5. **Run the checker** — `python3 skills/admin/role-hierarchy-design/scripts/check_role_hierarchy_design.py --roles-dir force-app/main/default/roles` — to catch cycles, unresolved `parentRole` references, invalid access-level values, and role counts above the org ceiling before a deploy fails.
6. **Sequence the rollout against recalculation.** Load users into roles before creating sharing rules; add sharing rules one at a time and let each finish; schedule reparenting into a window where no other group maintenance, deployment, or Apex test run is in flight.
7. **Verify by impersonation, not by query.** Log in as a user under each branch and confirm what they see. Hierarchy access produces no share rows, so a SOQL check against `AccountShare` or `OpportunityShare` will not show it.

---

## Review Checklist

- [ ] Every role traces to a written access requirement, not to a reporting line
- [ ] No object in scope has OWD Public Read/Write while the design assumes the hierarchy controls it
- [ ] `caseAccessLevel`, `contactAccessLevel`, and `opportunityAccessLevel` are set deliberately on every role, with `None` used where the branch must not inherit account children
- [ ] Grant Access Using Hierarchies decisions are documented per custom object, and no attempt is made to disable it on a standard object or on a Controlled by Parent object
- [ ] Public groups used in sharing rules have `DoesIncludeBosses` reviewed against intent
- [ ] Horizontal access requirements have been routed to sharing rules, not to a contrived shared parent role
- [ ] No user who owns more than 10,000 records of an object is scheduled to be moved between roles
- [ ] Role count is under the org's ceiling with headroom for the 1–3 roles each new portal-enabled account will append
- [ ] Reparenting is scheduled in a maintenance window, with retry logic in any integration that touches group membership
- [ ] Post-change verification is by login-as, and the Background Jobs page was checked for a completed recalculation
- [ ] Forecast managers (`UserRole.ForecastUserId`) were re-verified after any reparent

---

## Salesforce-Specific Gotchas

Short form; the mechanism and the recovery for each are in `references/gotchas.md`.

1. **Manager access leaves no evidence.** Inherited access is computed from group membership, so no `AccountShare` or `OpportunityShare` row explains it. Debugging by share query produces false "the manager has no access" conclusions.
2. **The standard-object opt-out does not exist.** Grant Access Using Hierarchies is editable for custom objects only, and not even for those when the default access is Controlled by Parent.
3. **The role's Opportunity/Case/Contact settings are about accounts the role owns**, not about records the role owns, and they vanish from the edit page when the child object's OWD is Public Read/Write.
4. **Reparenting is the blocking operation.** It blocks almost all other group updates; expect "could not acquire lock" and "Group membership operation already in progress" during concurrent loads.
5. **Portal roles are invisible and immutable.** They do not appear on the Roles setup page, they are appended below the portal account owner's role, and no field on a portal role can be updated.
6. **Ownership skew converts a role change into an outage.** One user owning more than 10,000 records of an object is the documented threshold.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Access requirement matrix | Object × OWD × vertical/horizontal, the input that decides whether the hierarchy is relevant at all |
| Role hierarchy design | Named roles, parentage, and a one-line access justification per role |
| `Role` metadata files | Deployable `.role-meta.xml` with `parentRole` and the three account-child access levels set explicitly |
| Grant Access Using Hierarchies register | Per-custom-object decision, kept outside metadata because the setting is not in `CustomObject` source |
| Role-change runbook | Sequencing, maintenance window, lock-retry behaviour, and post-change verification steps |
| Checker output | Cycles, unresolved parents, invalid access-level values, and role-count breaches from `check_role_hierarchy_design.py` |

---

## Related Skills

- `admin/sharing-and-visibility` — the whole record-access model; start there when the question is "who can see this record" rather than "how should the hierarchy be shaped"
- `admin/sharing-rules` — every horizontal and cross-branch requirement the hierarchy cannot express
- `admin/enterprise-territory-management` — account-based, many-to-many coverage; the correct answer when a user must cover accounts in several branches
- `admin/territory-design-requirements` — the requirements work that precedes a territory model, and the fork where a territory answer beats a role answer
- `admin/data-skew-and-sharing-performance` — deep treatment of ownership and parent-child skew, including the lock errors a role change surfaces
- `security/dynamic-sharing-recalculation` — forcing and orchestrating recalculation after a reorg
- `security/apex-managed-sharing-patterns` — programmatic `__Share` grants when no declarative mechanism fits
- `admin/user-management` — role assignment during onboarding, offboarding, and delegated administration
