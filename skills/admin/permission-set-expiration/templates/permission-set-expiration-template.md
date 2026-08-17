# Time-Boxed Access Request — Permission Set Expiration

Fill this in for every elevation that is supposed to end. The platform stores a
date and nothing else; everything that makes the date defensible lives here.

---

## 1. Request

| Field | Value |
|---|---|
| Requester | `[REPLACE: name and email]` |
| Assignee | `[REPLACE: username, e.g. j.okafor@northwind.com.prod]` |
| Assignee user type | `[REPLACE: Standard / Integration / System — integration, guest, Self-Service and system users are not available on the Manage Assignments page and must be assigned through the API]` |
| Business justification | `[REPLACE: what the assignee cannot do today and why it matters]` |
| Approver | `[REPLACE: name and role of the person accountable for this privilege]` |
| Approval date | `[REPLACE: YYYY-MM-DD]` |
| Ticket / change reference | `[REPLACE: e.g. SEC-4412]` |

---

## 2. Org Prerequisites

| Check | Answer | How to confirm |
|---|---|---|
| `psaExpirationUIEnabled` | `[REPLACE: true / false]` | `sf project retrieve start --metadata "Settings:UserManagement"` then read `UserManagement.settings-meta.xml`. Documented default is `false`, and while it is false the Setup screens show no expiration control. |
| `userAccessPoliciesEnabled` | `[REPLACE: true / false]` | Same file. If true, assignment rows also carry `IsRevoked` and audit queries need a second, `ALL ROWS` pass. |
| Grant path | `[REPLACE: Setup UI / API]` | Setup path that carries the expiration step: Permission Sets → the set → Manage Assignments → Add Assignments → select users → Next → set expiration → Assign. Requires Assign Permission Sets **and** View Setup and Configuration. |

If `psaExpirationUIEnabled` is false and the grant path is Setup, stop and deploy this first:

```xml
<!-- force-app/main/default/settings/UserManagement.settings-meta.xml -->
<!-- Retrieve the org's existing file and ADD this element. There is only one
     settings file per settings component — do not deploy a two-line file over
     whatever else is configured. -->
<?xml version="1.0" encoding="UTF-8"?>
<UserManagementSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <psaExpirationUIEnabled>true</psaExpirationUIEnabled>
</UserManagementSettings>
```

---

## 3. Unit of Expiry

| Field | Value |
|---|---|
| Grant target | `[REPLACE: permission set OR permission set group — never both on one row]` |
| API name | `[REPLACE: e.g. PS_Temp_ManageUsers]` |
| Is this target used for anything permanent? | `[REPLACE: Yes / No]` |

**If Yes, stop.** Expiring a permission set or group that also carries the
assignee's day-to-day access removes their day job on the expiry date. Build a
single-purpose elevation permission set containing only the temporary
capability, and name it for the elevation rather than for the person.

If the target is a permission set group, record its recalculation status —
`Updated`, `Outdated`, `Updating`, or `Failed`. A grant made against a group
that is not `Updated` does not deliver the aggregated permissions yet, and the
assignment row reports no error:

```soql
SELECT Id, DeveloperName, Status
FROM PermissionSetGroup
WHERE DeveloperName = '[REPLACE: PSG_Project_Migration]'
```

Status observed: `[REPLACE: Updated / Outdated / Updating / Failed]`

---

## 4. Exclusivity Proof

An expiry revokes a permission only when this assignment is the sole grant.
Run this before the grant, not after the lapse. Confirm the exact
`Permissions<PermissionName>` field name from `describeSObjects()` first — the
set of fields varies by org and licence type.

```soql
SELECT PermissionSet.Label, PermissionSet.IsOwnedByProfile, PermissionSet.Profile.Name
FROM PermissionSetAssignment
WHERE AssigneeId = '[REPLACE: 005 user id]'
  AND PermissionSet.[REPLACE: PermissionsManageUsers] = true
```

| Result | Value |
|---|---|
| Rows returned | `[REPLACE: n]` |
| Any row with `IsOwnedByProfile = true`? | `[REPLACE: Yes / No]` |
| Decision | `[REPLACE: Proceed — the elevation set will be the only grant / Blocked — fix the profile or the competing permission set first]` |

---

## 5. The Assignment

| Field | Value | Notes |
|---|---|---|
| `AssigneeId` | `[REPLACE: 005…]` | Create-only. Retargeting is a delete plus an insert. |
| `PermissionSetId` / `PermissionSetGroupId` | `[REPLACE: 0PS… or 0PG…]` | Create-only. Populate exactly one. |
| `ExpirationDate` | `[REPLACE: 2026-09-30T23:00:00Z]` | `dateTime`, Nillable, **updateable**. Write a full instant with an explicit offset so the cutoff is unambiguous. |
| Stated cutoff in business terms | `[REPLACE: end of business 30 September, Europe/London]` | Confirm what clock time and time zone the Setup screen applies in this org before quoting a cutoff to an auditor. Do not assume the UI and the API resolve to the same moment. |

```apex
insert new PermissionSetAssignment(
    AssigneeId      = '[REPLACE: 005…]',
    PermissionSetId = '[REPLACE: 0PS…]',
    ExpirationDate  = DateTime.newInstanceGmt([REPLACE: 2026, 9, 30, 23, 0, 0])
);
```

---

## 6. Renewal Policy

| Field | Value |
|---|---|
| Renewable? | `[REPLACE: Yes / No]` |
| Renewal requires | `[REPLACE: e.g. re-approval by the same approver, plus evidence the need still exists]` |
| Maximum total elevation | `[REPLACE: e.g. two renewals, then a permanent-access review]` |

Renewal is a **single-field update**, not a re-assignment:

```apex
PermissionSetAssignment psa = [
    SELECT Id, ExpirationDate
    FROM PermissionSetAssignment
    WHERE AssigneeId = '[REPLACE: 005…]'
      AND PermissionSet.Name = '[REPLACE: PS_Temp_ManageUsers]'
    LIMIT 1
];
psa.ExpirationDate = [REPLACE: new instant];
update psa;
```

Delete-and-insert is required only when a Create-only field changes, and in bulk
it risks leaving people with no assignment at all if the insert half fails.

---

## 7. Validation

Run all of these before closing the request. Every box must be ticked or
explicitly waived with a reason.

- [ ] `psaExpirationUIEnabled` state recorded in section 2
- [ ] Exclusivity proof in section 4 returned exactly one row, and it is not profile-owned
- [ ] The grant target is not used for anything permanent
- [ ] If the target is a permission set group, its `Status` is `Updated`
- [ ] `ExpirationDate` is populated with a full instant, not a bare date
- [ ] Approver and justification recorded in section 1
- [ ] Renewal policy agreed in section 6
- [ ] Assignment verified in the org after creation:

```soql
SELECT Id, Assignee.Username, PermissionSet.Name,
       PermissionSetGroup.DeveloperName, ExpirationDate, IsActive
FROM PermissionSetAssignment
WHERE AssigneeId = '[REPLACE: 005…]'
  AND ExpirationDate != NULL
ORDER BY ExpirationDate ASC
```

- [ ] Standing-privilege check returns nothing unexpected:

```soql
SELECT Id, Assignee.Name, PermissionSet.Name
FROM PermissionSetAssignment
WHERE ExpirationDate = NULL
  AND PermissionSet.Name LIKE '[REPLACE: PS_Temp_%]'
```

- [ ] Checker script run against the plan and the project:

```bash
python3 skills/admin/permission-set-expiration/scripts/check_permission_set_expiration.py \
    --manifest-dir [REPLACE: force-app] \
    --plan [REPLACE: elevation-plan.json]
```

- [ ] Setup Audit Trail export scheduled inside the 180-day retention window

---

## 8. Notes and Deviations

`[REPLACE: record any decision that departs from the patterns in SKILL.md, and
the reason. If an expiry was waived, name who accepted the standing privilege
and when it will be reviewed.]`
