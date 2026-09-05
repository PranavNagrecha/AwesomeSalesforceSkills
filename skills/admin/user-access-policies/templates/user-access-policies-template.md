# User Access Policies — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `user-access-policies`

**Request summary:** (fill in what the user asked for)

---

## Context Gathered

- **`userAccessPoliciesEnabled` in the target org:** Yes / No / Unknown — (API v58.0+; without it the UAP-gated fields on `PermissionSetAssignment` do not exist)
- **Deploying identity holds Manage User Access Policies:** Yes / No
- **Access mechanisms to grant or revoke:** (developer name + `type` for each — `PermissionSet`, `PermissionSetGroup`, `PermissionSetLicense`, `PackageLicense`, `Group`, `Queue`)
- **Population:** (which user attributes define it, and whether alternatives exist)
- **`triggerType`:** Create / Update / CreateAndUpdate
- **Existing Apex triggers to deactivate:** (list any triggers on the User object managing these assignments)
- **Backfill needed for the existing population:** Yes / No — if Yes, document the one-time operation

---

## Policy Design

### Filters

| `sortOrder` | `type` | `columnName` (User only) | `operation` | `target` | `value` (User only) |
|---|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |

**`booleanFilter`:** (required — e.g. `1`, `1 AND 2`, `(1 OR 2) AND 3`; every number must match a `sortOrder` above)

### Actions

| `action` | `type` | `target` | Exists in target org? |
|---|---|---|---|
| Grant / Revoke | | | |

Grant and Revoke actions belong in the same policy when they fire on the same event.

### Order Register

Every active policy that could match an overlapping population. Only the lowest `order` runs; the rest do not.

| `order` (0–10,000) | Policy | Criteria it matches | Actions it contributes |
|---|---|---|---|
| | | | |

- Which existing policy does this new one outrank? →
- What was that policy granting that must now be repeated here? →
- Are any two active policies sharing an `order` value? (must be No) →

---

## Approach

(Which pattern from SKILL.md applies? Why?)

- [ ] One policy, several values of one attribute (`operation` `in`)
- [ ] One policy, several attributes (`booleanFilter` with `OR`)
- [ ] Grant and revoke in the same policy on a role change
- [ ] Licence plus permission set group for a gated feature
- [ ] Custom scenario — describe:

---

## Checklist

- [ ] `userAccessPoliciesEnabled` confirmed true; Manage User Access Policies held
- [ ] `booleanFilter` present, and every number in it matches a declared `sortOrder`
- [ ] Every `operation` supported at the deployment API version (`in` v58.0+; `includes` / `equalsIgnoreCase` v59.0+)
- [ ] Filter rows with `type` `User` set `target` to `User` and populate `columnName` and `value`
- [ ] Every action `target` resolves to a component that exists in the target org
- [ ] `order` unique across active policies and within 0–10,000; numbered in gaps
- [ ] Suppressed-policy actions repeated in the winning policy where still required
- [ ] `triggerType` matches the intended event
- [ ] Post-deploy Setup activation step assigned to a named owner
- [ ] Verification query over `PermissionSetAssignment.LastCreatedByChange.Source` written and run
- [ ] No active Apex trigger writes the same assignment rows
- [ ] `checker` run clean: `python3 skills/admin/user-access-policies/scripts/check_user_access_policies.py --manifest-dir <dir>`

---

## Deployment Notes

**Metadata type:** `UserAccessPolicy` — suffix `.useraccesspolicy`, folder `useraccesspolicies`.

**package.xml entry** (this type supports the `*` wildcard, useful for taking a baseline of an org you did not build):

```xml
<types>
    <members>Sales_Rep_Onboarding</members>
    <name>UserAccessPolicy</name>
</types>
```

**Deploy order:** `Settings:UserManagement` → the permission sets / groups / queues each `target` names → the `UserAccessPolicy` files → manual activation in Setup → deactivate the superseded Apex trigger.

**Activation owner:** (name — a policy deployed with status `Active` arrives as `Design`)

---

## Notes

(Record any deviations from the standard pattern and why.)
