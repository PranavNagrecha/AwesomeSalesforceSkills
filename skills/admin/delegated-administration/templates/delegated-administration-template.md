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

**Group Name (`label`):** _______________

**File:** `delegateGroups/________________.delegateGroup-meta.xml`

| Setup related list | `DelegateGroup` field | Value | Notes |
|---|---|---|---|
| Delegated Administrators (users) | *(Setup only — not in the file)* | | |
| Users in Delegated Group | `roles` | | Branch headcount: ______ (roles **and subordinates**) |
| Assignable Profiles | `profiles` | | Each one opened and read? |
| Assignable Permission Sets | `permissionSets` | | Modify All / View All / Author Apex checked? |
| Assignable Permission Set Groups | `permissionSetGroups` | | |
| Groups | `groups` | | Public groups managed users may be placed into |
| Custom Object Administration | `customObjects` | | Relationships and OWD are excluded — is that acceptable? |
| Enable Group for Login Access | `loginAccess` (**required**) | `true` / `false` | If `true`: approver ______, review date ______ |

Deployable shape and package.xml: `references/metadata-examples.md`.

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

## Verification Run

| Step | Command / place | Result |
|---|---|---|
| Full retrieve | `sf project retrieve start --metadata DelegateGroup --metadata Role --metadata Profile --metadata PermissionSet` | |
| Static check | `python3 scripts/check_delegated_administration.py --manifest-dir <dir>` | ____ error(s), ____ warning(s) |
| Dry-run deploy | `sf project deploy start --source-dir .../delegateGroups --dry-run` | |
| Retrieve round-trip diff | re-retrieve, `git diff` — any dropped entries? | |
| Setup related lists match the file | Setup > Users > Delegated Administrators | |
| Negative test as the delegated admin | user outside the role branch; profile not in the list | |

---

## Known Limitations to Communicate

Record any platform constraints relevant to this request:

- System Administrator users cannot be managed by delegated admins — escalate to a full admin (unverified against the Metadata API guide; see `references/gotchas.md` #2)
- Users without a role assignment are not visible to delegated admins — roles must be assigned
- Custom object admin covers nearly every aspect of the named objects, including creating a custom tab, but never relationships or org-wide sharing defaults
- Delegated admins can only assign the profiles, permission sets, permission set groups, and public groups explicitly listed in their group
- With `loginAccess` true, the delegated admin can log in as the users they administer — subject to the org's login access policy
- There is no delegate-group SObject to query; verification is a retrieve round-trip plus Setup, not SOQL

---

## Notes

Record any deviations from the standard pattern and why:

_______________
