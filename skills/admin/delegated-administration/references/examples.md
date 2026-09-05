# Examples — Delegated Administration

## Example 1: Regional HR Coordinator Managing APAC Users

**Context:** A global Salesforce org has sales users organized by region in the role hierarchy. APAC has 40 users under an "APAC Sales" role branch. The APAC HR Coordinator (not a System Admin) needs to onboard new APAC sales reps, reset passwords, and assign the standard "APAC Sales Rep" profile. Previously, every onboarding request required a ticket to the central IT team.

**Problem:** Without delegated administration, the HR Coordinator has no way to create or edit user records. Adding them as a System Administrator would give them org-wide access, violating least-privilege requirements. There is no native way to scope user management to a role branch using profiles or permission sets alone.

**Solution:**

Configuration steps (no code — UI only):

```
Setup > Users > Delegated Administrators > New

Group Name: APAC HR Admin Group

Delegated Administrators related list:
  Add: apac.hr@example.com (the HR coordinator user)

Users in Delegated Group related list:
  Add roles: APAC Sales Manager, APAC Sales Rep, APAC Sales SDR
  (All subordinate roles are automatically included)

Assignable Profiles related list:
  Add: APAC Sales Rep (standard user profile for this region)

No Custom Object Administration needed.
```

Then on the HR Coordinator's profile:
```
Setup > Profiles > [HR Coordinator Profile] > System Permissions
Enable: View Setup and Configuration   (ViewSetup)
Enable: Manage Users                   (ManageUsers)
```

The Metadata API Developer Guide grounds only the first of these: "Only users with the 'View Setup and Configuration' permission can be delegated administrators." UNVERIFIED (2026-09-04): the Manage Users line is retained from the original Salesforce Help walkthrough and is not confirmed by the Metadata API Developer Guide or the Object Reference — enable it, but verify in the org before documenting it as the requirement (`references/gotchas.md` #1).

The equivalent deployable file, rather than the click-path above, is in `references/metadata-examples.md`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<DelegateGroup xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>APAC HR Admin Group</label>
    <loginAccess>false</loginAccess>
    <profiles>APAC Sales Rep</profiles>
    <roles>APAC_Sales_Manager</roles>
    <roles>APAC_Sales_Rep</roles>
    <roles>APAC_Sales_SDR</roles>
</DelegateGroup>
```

`loginAccess` is `false` because onboarding and password resets need no impersonation — but the field is required, so it has to be written either way.

**Why it works:** The group configuration scopes user management to only users in the APAC role branch. The HR Coordinator can create users, edit details, and reset passwords only for users in those roles. She cannot assign any profile except "APAC Sales Rep," preventing accidental over-provisioning. System Administrator users in the same region remain protected.

---

## Example 2: Business Unit Owner Extending a Custom Object

**Context:** A product operations team owns a custom object `Product_Request__c` used to track internal requests. The Ops Manager needs to add custom fields and update page layouts as the process evolves, but the central Salesforce team has a 2-week backlog. Opening full Setup access is not acceptable under the company's security policy.

**Problem:** Without custom object administration rights, the Ops Manager must raise every field or layout change with the central admin. Granting System Administrator or a cloned admin profile would expose unrelated Setup areas (security settings, org-wide defaults, connected apps).

**Solution:**

```
Setup > Users > Delegated Administrators > New

Group Name: Product Ops Custom Object Admin

Delegated Administrators related list:
  Add: ops.manager@example.com

Users in Delegated Group (roles):
  (Leave empty — this group is for custom object admin only, not user management)

Assignable Profiles / Permission Sets / Groups:
  (Leave empty — with no roles there is no population for them to act on;
   the guide scopes all three to "users in specified roles and all
   subordinate roles", so entries here would be dead configuration)

Enable Group for Login Access (loginAccess): false

Custom Object Administration related list:
  Add: Product_Request__c
```

The Ops Manager's profile must grant **View Setup and Configuration** to reach the delegated admin area at all, even though this group manages no users. UNVERIFIED (2026-09-04): whether **Manage Users** is additionally required for a custom-object-only group is not documented in the Metadata API Developer Guide — test before promising it either way.

**Why it works:** The Ops Manager can now navigate to Setup > Object Manager > Product_Request__c and modify fields, page layouts, and validation rules independently. They cannot see or touch any other Setup area, any other custom object, or any user records. Audit trail (Setup Audit Trail) records all changes under the Ops Manager's user ID, maintaining traceability.

---

## Anti-Pattern: Adding Parent Roles That Are Too High in the Hierarchy

**What practitioners do:** When setting up a Delegated Administrator group for a business unit, an admin adds the top-level regional role (e.g., "APAC VP") to the "Users in Delegated Group" list, thinking it will scope access to the APAC region cleanly.

**What goes wrong:** Salesforce includes all subordinate roles automatically. If "APAC VP" is the parent of APAC Sales, APAC Finance, APAC Legal, and APAC Operations branches, the delegated admin can now manage users across all of those branches — not just the intended sales team. Finance and Legal users are now visible and editable by the HR Coordinator who was only supposed to manage sales users.

**Correct approach:** Add the most specific roles that represent the actual scope. For sales onboarding, add "APAC Sales Manager" and its direct children — not the top of the APAC hierarchy. If the scope genuinely spans multiple branches, create separate Delegated Administrator groups per branch or carefully enumerate only the exact roles needed.
