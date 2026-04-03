# User Management — Work Template

Use this template when working on a user management task (create, deactivate, freeze, or configure users).

## Task Type

- [ ] New user provisioning
- [ ] User deactivation (offboarding)
- [ ] User freeze (temporary lock)
- [ ] License or profile change
- [ ] Login restrictions (hours / IP ranges)
- [ ] Delegated administration setup

## New User Provisioning

| Field | Value |
|---|---|
| First Name | |
| Last Name | |
| Email | |
| Username | (must be globally unique; use `name@company.com.sandbox` convention for sandboxes) |
| User License | |
| Profile | |
| Role | |
| Feature Licenses needed | (Marketing User, Service Cloud User, Knowledge User, etc.) |

**Checklist:**
- [ ] License availability confirmed (Setup → Company Information → User Licenses)
- [ ] Profile compatible with license type
- [ ] Role assigned if org uses role hierarchy for sharing
- [ ] Feature licenses checked
- [ ] Welcome email received and password set by user

## Deactivation / Offboarding Checklist

**User being offboarded:** _______________

- [ ] User frozen (Setup → Users → Freeze)
- [ ] Open records identified (list view: Owner = departing user)
- [ ] Open records reassigned to: _______________
- [ ] Queues reviewed and user removed from: _______________
- [ ] Approval processes reviewed — pending items reassigned to: _______________
- [ ] Knowledge articles transferred (if applicable)
- [ ] User deactivated (Setup → Users → Edit → uncheck Active)
- [ ] Confirmed: at least one other active System Administrator remains

## Login Restrictions

**Profile being updated:** _______________

| Setting | Current Value | New Value |
|---|---|---|
| Login Hours — Start | | |
| Login Hours — End | | |
| Login IP Ranges (CIDR) | | |

**Note:** Login Hours only prevent new logins. To terminate active sessions at the hour boundary, also set:
- Setup → Session Settings → Force logout on session timeout: ☐ enabled

## Delegated Administration Setup

**Group Name:** _______________

| Component | Value |
|---|---|
| Delegated Administrators (users with delegated rights) | |
| Managed Profiles (profiles delegates can assign) | |
| User fields delegates can edit | |

**Verification:**
- [ ] Logged in as a delegate user and confirmed only managed profiles appear
- [ ] System Administrator profile is NOT in the managed profiles list
- [ ] Delegate can create a test user and reset a password

## Notes

Record any deviations from standard procedure and the reason:
