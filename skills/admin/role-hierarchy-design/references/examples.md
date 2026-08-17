# Examples — Role Hierarchy Design

## Example 1: Splitting Sales and Service in an Org Where Opportunity OWD Has Just Gone Private

**Context:** A 1,200-user org runs Sales and Service on the same instance. Opportunity OWD was Public Read/Write for years; legal has now required it to be Private. The existing hierarchy is a faithful copy of the org chart: one CEO role, one COO role beneath it, and both the Sales VP and the Service VP hanging off the COO, nine levels deep in places. Nobody has ever set the account-child access levels on any role because the fields were not visible while Opportunity was Public Read/Write.

**Problem:** The moment Opportunity OWD flips to Private, three things break at once. Service managers who own accounts lose or gain opportunity access depending on whatever `OpportunityAccessForAccountOwner` defaulted to. The COO role now inherits every opportunity in the company because it sits above both VPs. And nine levels of intermediate roles that existed only to mirror reporting lines now each carry indirect membership rows in the Group Maintenance tables, so every subsequent reorg is expensive.

**Solution:**

Step 1 — Establish the access requirement per branch before touching a role.

| Requirement | Vertical or horizontal | Mechanism |
|---|---|---|
| Sales VP sees all sales pipeline | Vertical | Role hierarchy |
| Service VP must **not** see pipeline | Vertical exclusion | Branch separation |
| Service agents who own accounts must not gain opportunity access | Role-level setting | `opportunityAccessLevel` = `None` |
| Deal desk (4 people, various branches) sees all opportunities over $1M | Horizontal | Criteria-based sharing rule + public group |
| CFO and CEO see everything | Vertical | Membership of the single top role |

Step 2 — Flatten the root. Delete the intermediate COO role rather than leaving a box that grants org-wide opportunity visibility as a side effect of the org chart. A role delete is also the gentler operation on concurrency: the granular-locking guidance records that "a single-long running process, such as a role delete, blocks only a small subset of operations", where reparenting blocks almost all other group updates. Make `Sales_VP` and `Service_VP` siblings directly under the top role, and put only the CEO and CFO in that top role.

Step 3 — Set the three account-child access levels explicitly, on every role, in source.

```xml
<!-- force-app/main/default/roles/Service_Manager.role-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<Role xmlns="http://soap.sforce.com/2006/04/metadata">
    <name>Service Manager</name>
    <description>Owns service accounts. Must not inherit pipeline.</description>
    <parentRole>Service_VP</parentRole>
    <caseAccessLevel>Edit</caseAccessLevel>
    <contactAccessLevel>Edit</contactAccessLevel>
    <opportunityAccessLevel>None</opportunityAccessLevel>
    <mayForecastManagerShare>false</mayForecastManagerShare>
</Role>
```

Step 4 — Route the deal desk to a sharing rule, not to a role. Four people spread across branches cannot be expressed as "everyone above X in one chain". Create a public group, add the four users, and build a criteria-based Opportunity sharing rule that targets it.

Step 5 — Sequence the change. Load role changes first, let the recalculation finish, then add the sharing rule. The Large Data Volumes guidance for exactly this order is: load users into roles, load record data with owners so calculations propagate through the hierarchy, configure public groups and queues and let those computations propagate, then add sharing rules one at a time, letting each rule's computation finish before adding the next.

Step 6 — Verify by impersonation. Log in as a Service Manager who owns an account with an open opportunity and confirm the opportunity is not visible. Do not verify with a query against `OpportunityShare`; inherited access produces no rows there.

**Why it works:** The branch split is the only mechanism that stops opportunity inheritance for a standard object — Grant Access Using Hierarchies is not editable for standard objects, so there is no switch to reach for. Removing the COO role removes an inheritance path rather than trying to filter one. And setting `opportunityAccessLevel` to `None` closes the second, quieter path, where a Service Manager picks up opportunity access not by hierarchy but by owning the account the opportunity hangs off.

**Source:** Salesforce Security Guide (Spring '26), "Create a User Role" and "Organization-Wide Sharing Defaults"; Best Practices for Deployments with Large Data Volumes; `Role` / `RoleOrTerritory` Metadata API types. [T1]

---

## Example 2: A Compensation Object That Must Not Roll Up to Management

**Context:** HR needs `Compensation_Plan__c` in Salesforce. Each plan is owned by the HR business partner who authored it. Named comp-committee members must read all plans. Nobody else — including the HR business partner's own manager, and including the CEO — may read a plan they do not own or that has not been shared with them explicitly.

**Problem:** The default behaviour is the opposite of the requirement. With OWD Private and no further configuration, every user above the owning HRBP in the hierarchy reads every plan, and the higher the role, the more they read. No sharing rule fixes this — sharing rules only grant, they never subtract.

**Solution:**

Step 1 — Confirm the object is eligible for the opt-out. It must be a custom object, and its default access must not be Controlled by Parent. Controlled by Parent is defined against master-detail generally — "Users can perform actions (such as view, edit, delete) on a record on the detail side of a master-detail relationship if they can perform the same action on all associated master records" — and the Security Guide records the standard-object case as explicitly non-editable: "When a custom object is on the detail side of a master-detail relationship with a standard object, its organization-wide default is set to Controlled by Parent and it's not editable." Do not read that as permission to use a master-detail to a custom master instead: put `Compensation_Plan__c` on a lookup to `User` or `Employee__c` so it keeps its own OWD.

Step 2 — Set OWD and disable inheritance.

```
Setup → Sharing Settings → Organization-Wide Defaults → Edit
  Compensation Plan
    Default Internal Access: Private
    Default External Access: Private
    Grant Access Using Hierarchies: UNCHECKED
```

Step 3 — Grant the committee through a public group, with its own inheritance switch off.

```
Setup → Public Groups → New
  Label: Compensation Committee
  Grant Access Using Hierarchies: UNCHECKED    (Group.DoesIncludeBosses = false)
  Members: the named committee users

Setup → Sharing Settings → Compensation Plan Sharing Rules → New
  Rule Type: Based on criteria
  Criteria: Status__c equals 'Approved'
  Share with: Public Group — Compensation Committee
  Access Level: Read Only
```

Step 4 — Record the object-level checkbox as a manual environment step. It is not on the `CustomObject` metadata type, which exposes only `sharingModel` and `externalSharingModel`, so it will not deploy with the object and will not appear in a source diff.

Step 5 — Add a post-refresh verification.

```soql
-- Committee grants are Rule-caused shares and ARE visible here.
-- Any row you did not expect is a real finding; the absence of manager
-- rows is expected and proves nothing on its own.
SELECT Id, ParentId, UserOrGroupId, AccessLevel, RowCause
FROM Compensation_Plan__Share
WHERE RowCause != 'Owner'
```

**What this does not stop:** the object-level opt-out is not a confidentiality boundary against administrators. The Security Guide is explicit that "System Administrators and users with the View All and Modify All object permissions and the View All Data and Modify All Data system permissions can also access records they don't own." If the requirement is to keep plans from admins too, the hierarchy is the wrong layer entirely and the conversation moves to Shield Platform Encryption and permission-set hygiene.

**Why it works:** Deselecting the object-level checkbox means only the record owner and users who are granted access have access to the custom object's records — the hierarchy path is switched off at the object rather than filtered per user. Deselecting the group-level checkbox stops the committee members' own managers from picking the records up through the rule, since users in the hierarchy would otherwise be granted the same access that users below them get from a sharing rule when the object's Grant Access Using Hierarchies is selected.

**Source:** Salesforce Security Guide (Spring '26), "Create a User Role", "Organization-Wide Sharing Defaults", "Public and Personal Groups", "Sharing Rules"; `CustomObject` Metadata API type. [T1]

---

## Anti-Pattern: Reparenting a Role Mid-Quarter With a Skewed Owner Underneath It

**What practitioners do:** A channel reorg moves the `Partner_Sales_West` role from under `Sales_VP_Americas` to under a new `Channel_VP`. The move is done at 10:00 on a Tuesday because the change is "just a dropdown". Under that role sits an integration user that owns 2.4 million lead records, and three partner-enabled accounts whose owners are in the moved role.

**What goes wrong:** Three failures compound.

1. Reparenting blocks almost all other group updates. Every concurrent user-provisioning call, every deployment touching group membership, and every admin editing a public group starts failing with "could not acquire lock" or "Group membership operation already in progress".
2. The skewed owner forces Salesforce to adjust a very large number of sharing-table entries, because that user's records move into the scope of a different set of hierarchy relationships. The threshold at which this becomes a documented problem is a single user owning more than 10,000 records of an object; this one is two orders of magnitude past it.
3. The partner accounts drag their portal roles with them. For each portal-enabled account, 1–3 roles sit below the account owner's role, and Salesforce must delete the shares written to the old role and add them to the new one for every one of those accounts.

The recalculation runs for hours with no progress bar in Setup. Nobody can tell whether it is stuck or working, and access is partially applied the whole time.

**Correct approach:**

1. Before the move, take the skewed owner out of the blast radius. If the integration user does not need to share data through roles, remove its role entirely. If it must have one, put it in a separate role at the top of the hierarchy, keep it there permanently, and keep it out of any public group used as a sharing-rule source.
2. Inventory the portal roles that will move: `SELECT Id, Name, PortalType, ParentRoleId FROM UserRole WHERE PortalType != 'None'`. Reassigning portal account ownership and reparenting the role are both expensive; do not do them in the same window.
3. Schedule the reparent into a window with no data loads, no deployments, and no Apex test runs, since deployments and tests that update group membership cause the same lock contention.
4. Where the org supports it, defer sharing calculations before the update and recalculate afterwards, which is the documented mitigation when sharing evaluations time out.
5. Add retry logic to any integration that performs group maintenance, and fall back to serial processing if parallel processing produces lock errors.
6. Watch the Background Jobs page for completion, then verify access by logging in as a user under the moved branch.

**Recovery if it has already started:** Let the recalculation finish. Stop the concurrent processes that are competing for the lock rather than retrying them into the same contention, and do not launch a second structural change on top of the first — the second one will queue behind the first and extend the window.

**Source:** Designing Record Access for Enterprise Scale (Spring '26); Record-Level Access: Under the Hood (Spring '26); Salesforce Security Guide (Spring '26). [T1]
