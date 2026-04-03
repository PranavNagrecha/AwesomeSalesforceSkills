# Examples — User Management

## Example 1: Onboarding a New Sales Rep

**Context:** A new account executive joins the sales team. They need full Sales Cloud access including Leads, Opportunities, Accounts, Contacts, and Cases. They report to the Regional Sales Manager in the role hierarchy.

**Problem:** The admin selects the "Salesforce Platform" license because it is available and cheaper than the full Salesforce license. The user is saved, but when they log in they cannot see the Leads or Opportunities tabs. Cases are also invisible. The admin cannot find a page layout assignment for Opportunities.

**Solution:**

```
1. Setup → Users → Edit the user
2. Change User License from "Salesforce Platform" to "Salesforce"
3. Note: changing the license resets the Profile field — reassign the correct Sales profile
4. Set Role to "Regional Sales — AMER" (the correct node under the manager)
5. Save and confirm the user can now navigate to Leads, Opportunities, Contacts
```

**Why it works:** The Salesforce Platform license excludes standard Sales Cloud objects (Lead, Opportunity, Forecast). Only the full Salesforce license grants access to these objects. The profile must also be compatible — after changing the license, the system clears the profile field because the previously selected profile may be invalid for the new license type.

---

## Example 2: Emergency Offboarding — Finance Employee with Open Approvals

**Context:** A finance manager is terminated unexpectedly on a Wednesday morning. They are the sole approver on seven active expense approval processes. The company needs immediate access revocation but cannot lose those pending approvals.

**Problem:** The admin immediately deactivates the user. The seven active approval requests are now stuck — the approval process cannot route to a deactivated user, the requestors cannot resubmit, and Finance operations are stalled.

**Solution:**

```
Step 1 — FREEZE first (immediate):
  Setup → Users → Find the user → Click "Freeze"
  This blocks login within seconds. The user is locked out.
  Existing sessions are terminated on next page load.

Step 2 — Identify open approvals:
  Setup → Approval Processes → identify processes where this user is approver
  OR run a SOQL query:
    SELECT Id, TargetObjectId, Status, ActorId FROM ProcessInstanceWorkitem
    WHERE ActorId = '<user_id>' AND Status = 'Pending'

Step 3 — Reassign pending approvals:
  For each ProcessInstanceWorkitem, reassign ActorId to the backup approver (HR Director)
  Use Data Loader or Admin-level record update. Or recall and resubmit each request.

Step 4 — Remove from queues:
  Setup → Queues → check each queue → remove the user as a member

Step 5 — Reassign owned records:
  Accounts, Opportunities, Cases: Create list views filtered by owner, mass-reassign to manager

Step 6 — Deactivate:
  Setup → Users → Edit → uncheck Active → Save
```

**Why it works:** Freezing is instant and reversible. Deactivating before reassigning approvals creates a stuck state that requires individual admin intervention on each approval step. The freeze buys time to complete cleanup before permanent deactivation.

---

## Example 3: Delegated Admin for Regional HR Team

**Context:** A company has 12 regional HR coordinators who need to create new users and reset passwords for employees in their region. Currently every user request goes to a central Salesforce admin, creating a 2-day backlog. The security team refuses to give HR the System Administrator profile.

**Problem:** Without admin access, HR cannot create or edit users. With full admin access, HR could edit System Administrator accounts, change sharing settings, or modify other configurations they should not touch.

**Solution:**

```
1. Setup → Delegated Administration → New Group
   Name: "HR Regional Coordinators"

2. Delegated Administrators tab → Add HR coordinator user records
   (The HR coordinators who will have delegated rights)

3. Managed Profiles tab → Add:
   - "Sales User — Standard"
   - "Service User — Standard"
   - "Read Only"
   (Any profile these delegates should be able to assign to new users)
   NOTE: Do NOT add "System Administrator" — delegates cannot manage that profile

4. User Administration tab → Set which user fields HR can edit:
   - First Name, Last Name, Email, Title, Department, Phone
   - Username (allow HR to set username following naming convention)

5. Grant the HR coordinator users the "Manage Users" permission
   via a permission set or their profile

6. Test: log in as an HR coordinator, create a test user,
   verify only the managed profiles appear in the Profile picklist
```

**Why it works:** Delegated administration restricts authority to the specified profiles. HR cannot see or edit any user assigned a profile outside the managed list. They cannot access System Administrator accounts. The Manage Users permission is required for delegates to access the user management UI, but their editable scope is controlled by the delegation group — not the permission alone.

---

## Anti-Pattern: Creating Users Without Checking License Availability

**What practitioners do:** Click "New User" immediately and fill in all fields, only to hit a save error: "You have exceeded the maximum number of Salesforce licenses."

**What goes wrong:** Time is wasted filling in a full user form that cannot be saved. In urgent onboarding situations this causes frustration and delay.

**Correct approach:** Before creating any user, check Setup → Company Information → User Licenses to confirm available licenses. If no licenses are available, either deactivate an unused user to free one up, or contact Salesforce Account Executive to add licenses. Only start user creation after confirming a license is available.
