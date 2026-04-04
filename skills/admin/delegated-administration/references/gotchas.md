# Gotchas — Delegated Administration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Manage Users Permission Is a Separate Prerequisite — Not Auto-Granted by Group Membership

**What happens:** After a Salesforce admin creates a Delegated Administrator group and adds users to it, those users still see no change in their Setup experience. The "Manage Users" button does not appear. The admin assumes the group configuration is broken and reconfigures it repeatedly.

**When it occurs:** Any time a user is added to a Delegated Administrator group but their profile (or any assigned permission set) does not have the **Manage Users** system permission enabled. The Delegated Admin group grants scope — it does not grant the underlying permission to access user management.

**How to avoid:** Before testing, go to Setup > Profiles > [Delegated Admin's Profile] > System Permissions and confirm **Manage Users** is enabled. Alternatively, assign a permission set that grants Manage Users. This is a two-part setup: (1) Delegated Admin group configuration + (2) Manage Users permission on the user's profile or permission set. Both are required.

---

## Gotcha 2: System Administrator Users Are Always Protected — No Workaround

**What happens:** A delegated admin tries to reset the password of, or edit the record of, a user with the System Administrator profile. Salesforce silently excludes those users from the Manage Users view, or shows an error if accessed directly. The delegated admin reports that the feature "doesn't work" for specific users.

**When it occurs:** Any time a user with the System Administrator profile is in a role that falls within the delegated admin's configured role scope. Even if the role hierarchy technically places the System Admin under the delegated admin's scope, Salesforce does not allow delegated admins to touch any System Administrator profile user.

**How to avoid:** Document this constraint clearly when handing off delegated admin rights. For any action that requires modifying a System Administrator user, the request must be escalated to a full System Administrator. There is no permission, configuration, or workaround that bypasses this platform behavior. When designing role-scoped admin groups, accept that System Admin users in those roles will remain invisible to delegated admins.

---

## Gotcha 3: Users Without a Role Are Invisible to Delegated Admins

**What happens:** A delegated admin is configured to manage users in a specific role branch. After setup, they report they can manage some users but not others. Upon investigation, the invisible users have no role assigned to their user record.

**When it occurs:** When users are created or migrated without a role assignment, or when a role is removed from a user record during an org cleanup. Salesforce scopes delegated admin access by role; users with a null role do not belong to any role in the hierarchy and are therefore excluded from every delegated admin group's scope.

**How to avoid:** Before assigning the delegated admin group, audit all users in the intended scope to confirm they have roles assigned. Add role assignment as a mandatory step in the user provisioning checklist. When troubleshooting "missing users" for a delegated admin, the first check should always be whether the missing users have a role.

---

## Gotcha 4: Custom Object Admin Rights Do Not Include Standard Objects or Apex/Flows

**What happens:** A business unit owner is granted Custom Object Administration rights for their custom object. They then ask why they cannot see the Flows section, or why they cannot edit validation rules on the Account object, or why they cannot create Apex triggers for their custom object.

**When it occurs:** When the scope of Custom Object Administration is misunderstood. Custom Object Administration grants rights to customize the named custom object's fields, page layouts, list views, and validation rules only. It does not grant access to standard objects, Flows, Apex, reports/dashboards, or any other Setup area.

**How to avoid:** Set expectations clearly during setup. Document exactly what the custom object admin rights cover and what requires escalation to a full admin. If the business unit owner needs Flow or Apex access, that work must be handled by a full admin or delegated through change management processes, not through the Delegated Administration feature.

---

## Gotcha 5: Role Scope Is Additive — Adding a High Role Grants Access to All Subordinate Roles

**What happens:** An admin configures a Delegated Administrator group to cover a regional manager's role and adds "EMEA Director" to the "Users in Delegated Group" list. The intent is to let the delegated admin manage the EMEA Director and their direct reports. Instead, the delegated admin can manage every user under the EMEA Director's entire branch — hundreds of users across multiple departments.

**When it occurs:** When the admin does not fully understand that Salesforce automatically includes all subordinate roles when a role is added to the group. The "Users in Delegated Group" configuration is not a single-role assignment — it is a branch assignment.

**How to avoid:** Map the role hierarchy before configuring group scope. Only add the lowest-level roles that represent the actual intended scope. If you need to give access to just the direct reports of a manager, add those individual subordinate roles explicitly rather than the manager's role. Review the role hierarchy diagram after configuration to confirm the actual scope matches intent.
