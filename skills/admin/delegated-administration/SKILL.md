---
name: delegated-administration
description: "Use when configuring delegated administration to allow non-system-admin users to manage specific user groups, reset passwords, assign permission sets, or administer custom objects. Covers the DelegateGroup metadata type (delegateGroups/*.delegateGroup-meta.xml), its roles / profiles / permissionSets / permissionSetGroups / groups / customObjects / loginAccess fields, delegate-group log-in-as, and the deploy and review path for them. NOT for creating, deactivating or licensing users yourself — use admin/user-management. NOT for auto-assigning permission sets from user attributes — use admin/user-access-policies."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "how do I let a manager reset passwords for their team without making them a system admin"
  - "delegate user admin to department heads so HR does not need to raise IT tickets"
  - "allow a non-admin to create users and assign profiles in a specific business unit"
  - "set up a regional admin who can only manage users in their own role hierarchy"
  - "delegated administrator cannot see the manage users button after being configured"
  - "how do I set up a user to receive someone else's emails when they're on vacation"
  - "out of office email forwarding receive emails on behalf of another user"
  - "manager needs to handle records for a teammate who is on leave"
  - "deploy a delegate group as metadata instead of clicking through setup"
  - "delegated admin can log in as the users they manage login access"
  - "delegated admin cannot create a lookup relationship on the custom object they administer"
  - "which profiles and permission sets can a delegated administrator assign"
  - "delegate group vs public group what is the difference in salesforce"
  - "audit who can create users in our org without being a system admin"
tags:
  - delegated-administration
  - delegate-group
  - user-management
  - security
  - role-hierarchy
  - profiles
  - permission-sets
  - login-access
inputs:
  - "Target org with existing role hierarchy and profiles defined"
  - "List of users who will act as delegated administrators"
  - "List of profiles the delegated admins are allowed to assign"
  - "List of permission sets (if any) the delegated admins are allowed to assign"
  - "Custom objects (if any) the delegated admins should be able to administer"
outputs:
  - "Configured Delegated Administrator group(s) in Setup"
  - "Delegated admin group members list with scoped access"
  - "Checklist confirming what delegated admins can and cannot do in the target org"
  - "Troubleshooting notes for permission errors"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

# Delegated Administration

This skill activates when you need to grant a non-System-Administrator user the ability to manage a scoped subset of users — including creating users, resetting passwords, assigning profiles and permission sets, or administering custom objects — without granting them full System Administrator access. It covers setup from scratch, review of existing configuration, and troubleshooting delegated admin permissions that are not working as expected.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the org has a role hierarchy defined. Scope comes entirely from the group's `roles` field — "the roles and subordinates for which delegated administrators of the group can create and edit users" (Metadata API Developer Guide, `DelegateGroup`). Listing a role puts every role beneath it in scope. UNVERIFIED (2026-09-04): the frequently repeated rule that a delegated admin can only manage users **at or below their own role** is not in the `DelegateGroup` field table, which describes the configured `roles` list as the only constraint. Aligning the delegated admin's own role with the top of the branch they manage is still sound practice for consistent report and sharing visibility, but do not design around the "own role" rule as a security control.
- Identify which profiles, permission sets, and permission set groups the delegated admins should be permitted to assign — three separate fields (`profiles`, `permissionSets`, `permissionSetGroups`). Only the specific names listed can be assigned; each list is a menu, not a scope.
- Decide `loginAccess` before you write the file. It is a **required** boolean that "allows users in this group to log in as users in the role hierarchy that they administer". Default it to `false`; treat `true` as a privileged-access grant.
- Confirm whether custom object administration is required, and check the two documented exclusions: delegated admins "can customize nearly every aspect of each of those custom objects, including creating a custom tab. However, they can't create or modify relationships on the objects or set organization-wide sharing defaults."
- Confirm the intended delegated admins hold **View Setup and Configuration**. The guide's Special Access Rules: "Only users with the 'View Setup and Configuration' permission can be delegated administrators. As of Spring '20 and later, only users with 'View Setup' or 'Configuration' permission can access this object."
- Know the key limit: delegated admins **cannot** manage System Administrator users, regardless of role hierarchy position. UNVERIFIED (2026-09-04): this protection is not stated in the `DelegateGroup` documentation and there is no delegate-group SObject in the Object Reference to check it against — verify it in a sandbox rather than relying on it as your only guard against a delegated admin minting administrators. The guard that *is* documented and checkable is keeping the System Administrator profile out of `profiles`.

---

## Questions to Ask Before Configuring

Ask these before opening Setup or writing the XML. Each answer changes a field in the `DelegateGroup` file, and the ones that get skipped are the ones that show up later as a privilege-escalation finding.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Name the exact roles — and show me what sits underneath each one." | `roles` is "roles **and subordinates**"; a role near the top of a branch quietly enrols every department under it | The role list plus a headcount for the branch, which is the group's real blast radius (`references/gotchas.md` #5, #8) |
| "Do these administrators need to log in *as* the people they manage?" | `loginAccess` is required, so it is set either way — usually to whatever the sample had | An explicit `true`/`false`, and if `true`, a named approver and the org's `SecuritySettings` login-access posture (#6) |
| "For each profile and permission set they may assign: what does it actually grant?" | The file stores bare names; nothing checks whether `Data_Steward` enables Modify All Data | A reviewed menu, and the checker run that proves no listed profile or permission set is an escalation ladder (#9) |
| "Do they also need to add users to public groups?" | `groups` is a separate field, routinely missed, and unrelated to the delegate group itself | Either the public-group list or a recorded decision that group membership stays central (#7) |
| "Which custom objects — and does their backlog include relationships or org-wide defaults?" | Those two are the documented exclusions; a delegation that cannot deliver them buys nothing | The object list, or the finding that this feature does not solve the requester's actual problem (#4) |
| "Which profile or permission set gives these people View Setup and Configuration today?" | The group grants scope; the user permission grants entry. Without it the group appears broken | The container that already grants it, or the one change needed before the group can be tested (#1) |
| "Who re-runs this when roles or permission sets get renamed?" | Every reference is a name with no version; renames degrade scope silently | A named owner and a scheduled retrieve-and-check, not a one-off deploy (#11) |

What a proper configuration adds over just creating the group: the delegated administrators can do the job they were given without any path to creating an administrator, the impersonation switch was a decision rather than a default, and a reviewer can read the file and see exactly which population is managed and exactly what may be handed to them.

---

## Core Concepts

### Delegated Administrator Groups

A Delegated Administrator group is the core configuration object. It is the `DelegateGroup` metadata type — available since API 36.0, deployable from `delegateGroups/<Name>.delegateGroup-meta.xml`, and retrievable with the `*` wildcard. Each Setup related list maps to one field:

| Setup related list | `DelegateGroup` field | Type | Purpose |
|---|---|---|---|
| Delegated Administrators | *(not in the metadata)* | — | The users who receive the rights. Configured on the group in Setup; the guide's field table has no element for them. |
| Users in Delegated Group | `roles` | `string[]` | "The roles and subordinates for which delegated administrators of the group can create and edit users." The only field that scopes *who* is managed. |
| Assignable Profiles | `profiles` | `string[]` | "The profiles that can be assigned to users by delegated administrators." |
| Assignable Permission Sets | `permissionSets` | `string[]` | Permission sets assignable "to users in specified roles and all subordinate roles". |
| Assignable Permission Set Groups | `permissionSetGroups` | `string[]` | Same, for permission set groups. |
| Groups | `groups` | `string[]` | "The groups with users assigned by delegated administrators" — public groups managed users may be placed into. |
| Custom Object Administration | `customObjects` | `string[]` | Custom objects the delegated admin may customize. |
| Enable Group for Login Access | `loginAccess` | `boolean` | **Required.** Log in as the users in the role hierarchy they administer. |
| Group name | `label` | `string` | **Required.** "The delegated group's non-API name." |

Read the fields in two halves: `roles` decides the population, and everything else is a menu offered inside it. Deployable examples and the package.xml are in `references/metadata-examples.md`.

You can create multiple groups to model different business units or regions, each with their own scope.

### Role Hierarchy Enforcement

The role hierarchy is a hard constraint on delegated administration. When you add roles to the "Users in Delegated Group" configuration, the delegated admin can manage any user whose role is at or below the roles listed. The delegated admin's own role does not need to be a parent of the target roles — the role list in the group configuration is what determines scope. However, best practice is to align the delegated admin's role with the top of the roles they manage, to ensure consistent visibility across related features (reports, sharing, etc.).

One critical platform behavior: if a target user's role is not in the configured role list (or below it), the delegated admin will not see that user in their Manage Users view, even if they share a profile or group membership.

### What Delegated Admins Can and Cannot Do

**Can do:**
- Create new users with any profile listed in the group's Assignable Profiles
- Edit user details (name, email, title, phone) for users in their group
- Reset passwords for users in their group
- Freeze or unfreeze users in their group
- Assign or remove permission sets listed in the group's Assignable Permission Sets
- (If configured) Customize specific custom objects: add/edit fields, page layouts, validation rules, and list views

**Cannot do:**
- Create or edit System Administrator users (platform-enforced; no workaround)
- Assign profiles not listed in the group configuration
- Assign permission sets not listed in the group configuration
- Modify their own user record via the delegated admin interface
- Access Setup areas beyond Manage Users and (if configured) the specific custom objects
- Manage users whose roles are not in the group's role scope
- Create other delegated administrator groups or modify group configuration

### Custom Object Administration

Custom object administration rights are configured per Delegated Administrator group through `customObjects`. The guide's wording is deliberately broad, with two named exclusions:

| | Detail |
|---|---|
| Granted | "Delegated administrators can customize nearly every aspect of each of those custom objects, including creating a custom tab." |
| Not granted | "They can't create or modify relationships on the objects or set organization-wide sharing defaults." |
| Side effect | "Delegated administrators must have access to custom objects to access the merge fields on those objects from formulas." |
| Out of scope by construction | The field names objects, not Setup areas — standard objects, Flow, Apex, and reports are untouched. |

This is useful for business unit owners who need to extend a custom object for their team without opening full Setup access — provided their backlog is not mostly relationship changes, which always route back to a full administrator.

---

## Common Patterns

### Pattern 1: Setting Up Delegated Administration From Scratch

**When to use:** A department head, regional manager, or HR coordinator needs to manage users in their business unit (create users, reset passwords, assign profiles) without escalating every request to the IT/Salesforce admin team.

**How it works:**

1. Go to **Setup > Users > Delegated Administrators**.
2. Click **New** to create a Delegated Administrator group. Give it a descriptive name (e.g., "APAC Sales Admin Group").
3. In the **Delegated Administrators** related list, click **Add** and search for the users who will act as delegated admins. Save.
4. In the **Users in Delegated Group** related list, click **Add** and select the roles whose users can be managed. The delegated admin will be able to manage users at these roles and all subordinate roles.
5. In the **Assignable Profiles** related list, click **Add** and select the profiles that the delegated admin is permitted to assign when creating or editing users.
6. (Optional) In the **Assignable Permission Sets** related list, click **Add** and select specific permission sets the delegated admin can assign.
7. (Optional) In the **Custom Object Administration** related list, click **Add** and select any custom objects the delegated admin should be able to customize.
8. Confirm the delegated admin users hold **View Setup and Configuration** (`ViewSetup`) on their own profile or via a permission set — the guide's Special Access Rules make it the prerequisite for being a delegated administrator. Enable **Manage Users** as well; UNVERIFIED (2026-09-04): the Manage Users requirement, though universally repeated, is not stated in the Metadata API Developer Guide or the Object Reference (`references/gotchas.md` #1).

**Why not the alternative:** Granting the System Administrator profile or cloning it with broad access creates an uncontrolled security risk. Permission sets alone cannot scope user-management rights to a subset of users — only Delegated Administrator groups provide role-scoped user management.

### Pattern 2: Reviewing Existing Delegated Admin Configuration

**When to use:** An admin suspects a delegated admin has too broad or too narrow access, or a compliance review requires audit of who can manage users.

**How it works:**

1. Go to **Setup > Users > Delegated Administrators**.
2. Review each group for: which users are Delegated Administrators, which roles are in scope, which profiles are assignable, and which permission sets are assignable.
3. For each delegated admin user, confirm their own profile or permission set still grants **View Setup and Configuration** (and Manage Users, if the org relies on it) — the entry permission is often lost when a user's profile changes post-setup. `scripts/check_delegated_administration.py` lists every retrieved container that grants `ViewSetup`.
4. Cross-reference the role list against the org's role hierarchy diagram. Roles added to the group include all subordinate roles implicitly — confirm no unintended roles are in scope.
5. Check whether any delegated admins have been inadvertently given System Administrator profile access directly, which would bypass all scoping.

### Pattern 3: Troubleshooting Delegated Admin Permissions Not Working

**When to use:** A configured delegated admin reports they cannot see the Manage Users button, cannot see specific users, or cannot assign a profile or permission set.

**How it works:**

1. **Manage Users button missing:** Check the delegated admin's profile and permission sets for **View Setup and Configuration**, then Manage Users. Neither is granted by group membership — the group supplies scope, the user permission supplies entry (`references/gotchas.md` #1).
2. **Cannot see specific users:** Check that those users' roles are in the Delegated Group's "Users in Delegated Group" configuration. If the target user has no role, or a role not in the list, they will not appear.
3. **Cannot assign a profile:** Check that the target profile is listed in the group's **Assignable Profiles** related list. Also confirm the target profile is not the System Administrator profile — that assignment is always blocked.
4. **Cannot assign a permission set:** Check the **Assignable Permission Sets** related list in the group configuration.
5. **Error when trying to manage a System Admin user:** This is expected platform behavior. System Administrator users are always protected and cannot be managed by delegated admins.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Manager needs to reset passwords only | Delegate group with `roles` set, `loginAccess` false, and `profiles` / `permissionSets` / `groups` all empty | Least privilege; no assignment menu means nothing can be handed out |
| HR team needs to onboard users for one business unit | Delegated Admin group scoped to that unit's roles with limited assignable profiles | Role-scoped; prevents HR from creating admins or assigning privileged profiles |
| Business unit owner needs to extend a custom object | Add Custom Object Administration to the Delegated Admin group | Avoids full Setup access; scoped to only the named objects |
| User needs to manage admins in a sub-org | Not possible via delegated administration | System Administrator users are platform-protected; use a separate Salesforce org or sandbox strategy |
| Multiple regions need independent admin groups | Create one Delegated Administrator group per region | Each group has independent role scope, profiles, and permission sets; no cross-region leakage |
| Delegated admin asks to "see what the user sees" to troubleshoot | `loginAccess` true, approved and time-boxed — not a wider role scope or a stronger profile | It is the only documented impersonation lever on this type; widening scope instead grants far more and diagnoses nothing |
| Business unit wants to add a lookup to their custom object | Not possible via delegated administration | `customObjects` explicitly excludes creating or modifying relationships and setting org-wide defaults |

---


## Recommended Workflow

1. **Answer the seven questions** in *Questions to Ask Before Configuring* using `templates/delegated-administration-template.md`. The `roles` answer needs a headcount for the whole branch, not a role name — that number is the group's blast radius.
2. **Retrieve what already exists.** `sf project retrieve start --metadata DelegateGroup --metadata Role --metadata Profile --metadata PermissionSet` — `DelegateGroup` supports the `*` wildcard, so one retrieve gets every group in the org. A partial retrieve makes step 5's dangling-reference warnings meaningless.
3. **Write the group file** from `references/metadata-examples.md`: `delegateGroups/<Name>.delegateGroup-meta.xml`, `label` and `loginAccess` present (both required), `roles` as the lowest roles covering the intent, and each assignment menu (`profiles`, `permissionSets`, `permissionSetGroups`, `groups`) trimmed to what the business role actually hands out.
4. **Read what the menu grants, not just its name.** Open every `.profile` and `.permissionset` named in the file and check for Modify All Data, View All Data, and Author Apex. This is the escalation path the group file cannot show you (`references/gotchas.md` #9).
5. **Run the checker** over the full retrieve: `python3 scripts/check_delegated_administration.py --manifest-dir force-app/main/default`. It errors on System Administrator in `profiles` and on escalation permissions inside listed profiles/permission sets, and warns on `loginAccess: true`, dead menus on a role-less group, and stale name references. Exit code 1 means an ERROR — do not deploy past it.
6. **Deploy `--dry-run` first, then for real**, and confirm the delegated administrators hold View Setup and Configuration (the checker lists which retrieved containers grant `ViewSetup`).
7. **Verify three ways** — retrieve round-trip and diff, the Setup related lists, and a log-in-as walkthrough as the delegated administrator, including one negative test outside the role branch (`references/metadata-examples.md` § Verification, `references/llm-anti-patterns.md` #5).

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Delegated Administrator group created with a clear, descriptive name (`label`), distinct from any public group name
- [ ] Delegated Administrators (users) added to the group in Setup — they are not part of the metadata file
- [ ] `roles` holds the lowest roles covering the intent; branch headcount recorded
- [ ] `loginAccess` was decided, not inherited from a sample; if `true`, approved and recorded as privileged access
- [ ] `profiles` does not contain System Administrator, and every listed profile / permission set was opened and read
- [ ] No listed profile or permission set enables Modify All Data, View All Data, or Author Apex
- [ ] Delegated admin users hold **View Setup and Configuration** via profile or permission set
- [ ] `python3 scripts/check_delegated_administration.py --manifest-dir <dir>` exits 0 over a full retrieve
- [ ] Retrieve round-trip after deploy shows no silently dropped `roles` / `profiles` / `permissionSets` entries
- [ ] Tested as the delegated admin: allowed profiles appear, a user outside the role branch does not
- [ ] Tested: delegated admin cannot see or modify System Administrator users (verify — see gotchas #2)
- [ ] (If custom object admin) Only the intended custom objects are listed, and the requester knows relationships and OWD are excluded

---

## Salesforce-Specific Gotchas

The full write-ups, with grounding, are in `references/gotchas.md`. In one line each:

| # | Behaviour |
|---|---|
| 1 | Group membership grants scope, not entry — the administrator still needs View Setup and Configuration on their own profile or permission set |
| 2 | System Administrator users appear to be protected from delegated admins, but the guide does not say so; keep that profile out of `profiles` instead |
| 3 | A user with no role is in no delegate group's scope, because `roles` is the only scoping field |
| 4 | `customObjects` covers "nearly every aspect", including creating a custom tab — but never relationships or org-wide defaults |
| 5 | `roles` means roles **and subordinates**; one role near the top of a branch enrols every department beneath it |
| 6 | `loginAccess` is required, so it is always set — often to the sample's `true`, which is an impersonation grant |
| 7 | Three different things are called "group" here: the delegate group, the public groups in `groups`, and the administrators themselves |
| 8 | Trimming `profiles` narrows what may be handed out, not who may be reached |
| 9 | Nothing validates what a listed profile or permission set actually grants — that is the escalation path |
| 10 | Setting up delegated admins exposes profile names even with Profile Filtering on |
| 11 | Every reference is a bare name with no version, so renames degrade scope silently

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `delegateGroups/<Name>.delegateGroup-meta.xml` | Deployable `DelegateGroup` file with `label`, `loginAccess`, `roles`, and the assignment menus — shaped from `references/metadata-examples.md` |
| `package.xml` entry | `DelegateGroup` type block, plus the `Role` / `Profile` / `PermissionSet` members the group references |
| Checker output | `check_delegated_administration.py --manifest-dir <dir>` run, attached to the change, exiting 0 |
| Delegated admin verification checklist | Completed checklist confirming what the delegated admin can and cannot do, tested in the org |
| Privileged-access note | Where `loginAccess` is `true`: who approved it, for which role branch, and when it is reviewed |
| Troubleshooting notes | Documented root cause and resolution for any permission gaps found during review |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing or reviewing deployable `DelegateGroup` XML, the package.xml, the CLI commands, and the post-deploy verification path |
| `references/gotchas.md` | The eleven platform behaviours behind the questions above — read before designing scope or approving `loginAccess` |
| `references/examples.md` | Two worked Setup walkthroughs (regional HR coordinator, custom-object-only group) and the too-high-role anti-pattern |
| `references/well-architected.md` | Framing the security / operational-excellence tradeoffs for a review, and the Official Sources list |
| `references/llm-anti-patterns.md` | Self-checking generated delegated-admin guidance, and the eight-step post-configuration verification script |

---

## Related Skills

- admin/user-management — full user provisioning, deactivation, license assignment, and role/profile setup that falls outside delegated admin scope
- admin/role-hierarchy-design — shaping the role branches that `roles` points at; the branch shape *is* the delegation scope
- admin/permission-set-architecture — what goes inside the permission sets listed in `permissionSets`, which is where the escalation risk actually lives
- security/privileged-access-management — governing standing administrative access and log-in-as, the home for any group deployed with `loginAccess: true`
- admin/custom-permissions — when the delegated task needs a named permission to gate against rather than a broader profile or permission set
- admin/user-access-policies — automatic, attribute-driven permission set assignment, which replaces manual delegated assignment for rule-shaped cases
