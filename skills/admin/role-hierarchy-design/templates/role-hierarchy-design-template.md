# Role Hierarchy Design — Worksheet

Fill this in before creating, moving, or deleting any role. Replace every
`[REPLACE: …]` marker. Sections left unanswered are the sections that produce
the rework.

**Org:** `[REPLACE: org name / instance]`
**Environment:** `[REPLACE: production | full sandbox | scratch]`
**Author:** `[REPLACE: name]`
**Date:** `[REPLACE: YYYY-MM-DD]`
**Change type:** `[REPLACE: new hierarchy | add role | reparent role | delete role | bulk user role change]`

---

## 1. Preconditions

| Question | Answer | Why it matters |
|---|---|---|
| Org creation date | `[REPLACE: YYYY-MM-DD or "before Spring '21"]` | Decides the 500 vs 5,000 role ceiling |
| Current internal role count | `[REPLACE: n]` | Headroom check |
| Current portal role count (`WHERE PortalType != 'None'`) | `[REPLACE: n]` | Not visible on the Setup Roles page |
| Portal-enabled accounts in scope | `[REPLACE: n]` | Each appends 1–3 roles below its owner's role |
| Any user owning >10,000 records of one object? | `[REPLACE: yes — user + object + count / no]` | Ownership skew turns a role change into a long recalculation |
| Digital experiences enabled? | `[REPLACE: yes / no]` | Decides which role-based sharing member types exist |
| Who holds `Manage Roles` / `Manage Sharing`? | `[REPLACE: names]` | Required to execute the change |

---

## 2. Org-Wide Defaults in Scope

The hierarchy is inert where OWD is Public Read/Write. List only objects the
change is meant to affect.

| Object | Internal OWD | External OWD | Grant Access Using Hierarchies | Editable? |
|---|---|---|---|---|
| `[REPLACE: Account]` | `[REPLACE: Private]` | `[REPLACE: Private]` | `[REPLACE: on]` | No — standard object |
| `[REPLACE: Opportunity]` | `[REPLACE: Private]` | `[REPLACE: Private]` | `[REPLACE: on]` | No — standard object |
| `[REPLACE: Custom_Object__c]` | `[REPLACE: Private]` | `[REPLACE: Private]` | `[REPLACE: off]` | Yes, unless default access is Controlled by Parent |

> Any row where the OWD is Public Read/Write is out of scope for this change.
> Any custom object with the checkbox off needs an entry in section 6.

---

## 3. Access Requirements

One row per requirement. A requirement that is not vertical does not belong to
the hierarchy.

| # | Requirement (in the business's words) | Vertical / horizontal | Mechanism | Skill |
|---|---|---|---|---|
| 1 | `[REPLACE: e.g. the EMEA sales director must see all pipeline under her]` | Vertical | Role hierarchy | this skill |
| 2 | `[REPLACE: e.g. the four deal-desk analysts must see all deals over $1M]` | Horizontal | Criteria-based sharing rule + public group | `admin/sharing-rules` |
| 3 | `[REPLACE: e.g. reps cover accounts by both region and product line]` | Neither | Territory model | `admin/enterprise-territory-management` |

---

## 4. Proposed Hierarchy

Every role needs an access justification. "Reports to X" is not one.

| Role (label) | `fullName` | Parent | Records it sees that its parent does not | Keep? |
|---|---|---|---|---|
| `[REPLACE: Executive]` | `[REPLACE: Executive]` | — | Top of hierarchy; inherits everything | Yes |
| `[REPLACE: Sales VP]` | `[REPLACE: Sales_VP]` | `[REPLACE: Executive]` | `[REPLACE: all sales-owned records]` | Yes |
| `[REPLACE: role]` | `[REPLACE: Api_Name]` | `[REPLACE: Parent_Api_Name]` | `[REPLACE: …]` | `[REPLACE: yes / DELETE — grants nothing new]` |

---

## 5. Account-Child Access Per Role

Set all three deliberately. An unset field falls back to a platform default —
the `RoleOrTerritory` reference says it "uses the default access level that is
specified in the Manage Territory page in Setup" — which is a decision made by
accident and invisible in a source diff. Valid values: `Read`, `Edit`, `None`.

| Role | `caseAccessLevel` | `contactAccessLevel` | `opportunityAccessLevel` | Rationale |
|---|---|---|---|---|
| `[REPLACE: Sales_VP]` | `[REPLACE: Read]` | `[REPLACE: Edit]` | `[REPLACE: Edit]` | `[REPLACE: …]` |
| `[REPLACE: Service_Manager]` | `[REPLACE: Edit]` | `[REPLACE: Edit]` | `[REPLACE: None]` | `[REPLACE: must not pick up pipeline via owned accounts]` |

Deployable form:

```xml
<!-- force-app/main/default/roles/[REPLACE: Api_Name].role-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<Role xmlns="http://soap.sforce.com/2006/04/metadata">
    <name>[REPLACE: Role Label]</name>
    <description>[REPLACE: one line — what access this role exists to grant]</description>
    <parentRole>[REPLACE: Parent_Api_Name]</parentRole>
    <caseAccessLevel>[REPLACE: Read | Edit | None]</caseAccessLevel>
    <contactAccessLevel>[REPLACE: Read | Edit | None]</contactAccessLevel>
    <opportunityAccessLevel>[REPLACE: Read | Edit | None]</opportunityAccessLevel>
    <mayForecastManagerShare>[REPLACE: true | false]</mayForecastManagerShare>
</Role>
```

Omit an access-level element entirely when the corresponding object's sharing
model is Public Read/Write — the platform hides the field in that case, and
`contactAccessLevel` is also hidden when the contact model is Controlled by
Parent.

---

## 6. Non-Deployable Settings Register

Grant Access Using Hierarchies is not on the `CustomObject` metadata type. It
does not travel with a deployment. Record it here and re-apply it by hand in
every environment.

| Object | Setting | Applied in sandbox | Applied in production | Owner |
|---|---|---|---|---|
| `[REPLACE: Custom_Object__c]` | Grant Access Using Hierarchies = OFF | `[REPLACE: date]` | `[REPLACE: date]` | `[REPLACE: name]` |
| `[REPLACE: Public group name]` | `DoesIncludeBosses` = false | `[REPLACE: date]` | `[REPLACE: date]` | `[REPLACE: name]` |

---

## 7. Execution Plan

| Step | Action | Window | Owner |
|---|---|---|---|
| 1 | `[REPLACE: remove skewed owner from role / confirm none exists]` | `[REPLACE: …]` | `[REPLACE: …]` |
| 2 | `[REPLACE: create new roles (no reparenting yet)]` | `[REPLACE: …]` | `[REPLACE: …]` |
| 3 | `[REPLACE: assign users to roles]` | `[REPLACE: …]` | `[REPLACE: …]` |
| 4 | `[REPLACE: reparent — nothing else running]` | `[REPLACE: …]` | `[REPLACE: …]` |
| 5 | `[REPLACE: add sharing rules one at a time]` | `[REPLACE: …]` | `[REPLACE: …]` |

Concurrency holds for the reparent window:

- [ ] No data loads running
- [ ] No deployments running
- [ ] No Apex test runs in flight
- [ ] Integrations that touch group membership have retry logic for
      "could not acquire lock" and "Group membership operation already in progress"
- [ ] Serial processing configured if parallel processing has produced lock errors before
- [ ] Defer-sharing-calculations decision made: `[REPLACE: deferred / not deferred — why]`

---

## 8. Validation

Run these before calling the change complete. Every box must be ticked with
evidence, not with intent.

- [ ] `python3 skills/admin/role-hierarchy-design/scripts/check_role_hierarchy_design.py --roles-dir [REPLACE: force-app/main/default/roles]` exits 0
- [ ] Role count after the change: `[REPLACE: n]` — under the org ceiling with headroom for portal roles
- [ ] Background Jobs page shows the sharing recalculation completed: `[REPLACE: timestamp]`
- [ ] Logged in as a user in each branch and confirmed what they can and cannot see:

| Branch | Test user | Should see | Should NOT see | Result |
|---|---|---|---|---|
| `[REPLACE: Sales]` | `[REPLACE: user]` | `[REPLACE: …]` | `[REPLACE: …]` | `[REPLACE: pass / fail]` |
| `[REPLACE: Service]` | `[REPLACE: user]` | `[REPLACE: …]` | `[REPLACE: …]` | `[REPLACE: pass / fail]` |

- [ ] Verification was **not** done by querying `__Share` objects — inherited
      grants leave no rows there
- [ ] Forecast managers re-checked:
      `SELECT Id, Name, ParentRoleId, ForecastUserId FROM UserRole WHERE ForecastUserId != NULL`
- [ ] Portal roles re-inventoried:
      `SELECT Id, Name, PortalType, PortalRole, ParentRoleId FROM UserRole WHERE PortalType != 'None'`
- [ ] Section 6 settings re-applied and confirmed in the target environment

---

## 9. Notes and Deviations

`[REPLACE: record anything done differently from the plan, and why. Include any
requirement that was routed away from the hierarchy and where it went.]`
