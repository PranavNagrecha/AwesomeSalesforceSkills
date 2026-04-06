# User Access Policies — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `user-access-policies`

**Request summary:** (fill in what the user asked for)

---

## Context Gathered

- **Org release version:** (confirm release 242+ for UAP GA; release 246+ for custom field filters)
- **Permission sets / PSGs to assign or revoke:** (list names)
- **PSLs to include:** (list if applicable)
- **Filter criteria to use:** (e.g., Profile = Sales Rep Profile; Department = Finance)
- **Trigger event:** User Create / User Field Update / Both
- **Existing Apex triggers to deactivate:** (list any triggers on the User object managing these permissions)
- **Backfill needed for existing users:** Yes / No — if Yes, document the bulk operation plan

---

## Policy Design

### Grant Policies

| Policy Name | Filter Field | Filter Value | Assignments (PS / PSG / PSL) |
|---|---|---|---|
| | | | |

### Revoke Policies

| Policy Name | Filter Field | Filter Value | Assignments to Revoke |
|---|---|---|---|
| | | | |

### Evaluation Order Notes

- Are any users in scope for both a Grant and a Revoke policy targeting the same permission set? (Yes / No)
- If Yes, document the expected outcome and confirm it is intentional:

---

## Approach

(Which pattern from SKILL.md applies? Why?)

- [ ] Profile-Based Permission Provisioning on Create
- [ ] Role-Change Permission Revocation
- [ ] PSL and PSG Co-Assignment
- [ ] Custom scenario — describe:

---

## Checklist

- [ ] Org confirmed on release 242 (Spring '25) or later
- [ ] All referenced permission sets, PSGs, and PSLs exist and are active
- [ ] Filter criteria cover all qualifying user segments
- [ ] Grant and revoke policies use mutually exclusive filter criteria for the same permission sets
- [ ] No active Apex triggers conflict with the new UAP policies
- [ ] Policies validated in sandbox by creating and updating test users
- [ ] Custom user field filters confirmed only used on release 246+
- [ ] PSL and PSG included in the same policy where co-assignment is required
- [ ] UserAccessPolicy metadata included in deployment package
- [ ] Backfill plan documented if existing users need retroactive assignment

---

## Deployment Notes

**Metadata type:** `UserAccessPolicy`

**Sample SFDX package.xml entry:**

```xml
<types>
    <members>PolicyName</members>
    <name>UserAccessPolicy</name>
</types>
```

---

## Notes

(Record any deviations from the standard pattern and why.)
