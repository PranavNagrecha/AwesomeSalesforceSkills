# Delegated Administration — Work Template

Use this template when setting up, reviewing, or troubleshooting delegated administration in a Salesforce org.

## Scope

**Skill:** `delegated-administration`

**Request summary:** (fill in what the user asked for)

**Task type:**
- [ ] New delegated admin group setup
- [ ] Review of existing delegated admin configuration
- [ ] Troubleshooting delegated admin permissions not working
- [ ] Custom object administration setup

---

## Context Gathered

Before starting, record answers to these questions:

| Question | Answer |
|---|---|
| Does the org have a defined role hierarchy? | |
| Who are the users that will act as delegated admins? | |
| Which roles (and their subordinates) should be in scope? | |
| Which profiles should be assignable by these delegated admins? | |
| Which permission sets (if any) should be assignable? | |
| Are custom object admin rights needed? If so, which objects? | |
| Do the delegated admin users currently have the Manage Users permission on their profile? | |

---

## Delegated Administrator Group Configuration

**Group Name:** _______________

| Component | Value |
|---|---|
| Delegated Administrators (users) | |
| Users in Delegated Group (roles) | |
| Assignable Profiles | |
| Assignable Permission Sets | |
| Custom Object Administration | |

---

## Approach

Which pattern from SKILL.md applies?

- [ ] Pattern 1: Setting up from scratch
- [ ] Pattern 2: Reviewing existing configuration
- [ ] Pattern 3: Troubleshooting permissions not working

Notes on approach:

_______________

---

## Checklist

- [ ] Delegated Administrator group created with a clear, descriptive name
- [ ] Delegated Administrators (users) added to the group
- [ ] Roles in "Users in Delegated Group" are correct — not too broad (see gotcha: role scope is additive)
- [ ] Assignable Profiles list is minimal and does not include System Administrator or high-privilege profiles
- [ ] Delegated admin users' own profiles have the "Manage Users" system permission enabled
- [ ] Delegated admin confirmed they can see Manage Users in personal setup (log in as user to verify)
- [ ] Tested: delegated admin cannot see or modify System Administrator users
- [ ] Tested: delegated admin cannot assign profiles outside the configured list
- [ ] Tested: delegated admin cannot manage users with no role assigned (document if this is a gap)
- [ ] (If custom object admin) Confirmed only the intended custom objects are listed

---

## Known Limitations to Communicate

Record any platform constraints relevant to this request:

- System Administrator users cannot be managed by delegated admins — escalate to a full admin
- Users without a role assignment are not visible to delegated admins — roles must be assigned
- Custom object admin does not extend to standard objects, Flows, or Apex
- Delegated admins can only assign profiles and permission sets explicitly listed in their group

---

## Notes

Record any deviations from the standard pattern and why:

_______________
