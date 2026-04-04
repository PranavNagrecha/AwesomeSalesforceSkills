---
name: permission-sets-vs-profiles
description: "Use when designing or auditing Salesforce access control — deciding between Profiles, Permission Sets, and Permission Set Groups. Triggers: 'user can't see field', 'too many profiles', 'permission model', 'least privilege', 'profile migration'. NOT for sharing rules or record-level access — use security/fls-crud for that."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
tags: ["profiles", "permission-sets", "permission-set-groups", "least-privilege", "access-control"]
triggers:
  - "user cannot see an object or tab"
  - "too many profiles getting hard to manage"
  - "user needs access to one feature only"
  - "field not visible to a specific user"
  - "how do I reduce the number of profiles in my org"
  - "permission set group not giving expected access"
  - "too many profiles how to simplify"
inputs: ["persona matrix", "current access model", "managed package constraints"]
outputs: ["permission model recommendation", "access migration findings", "least-privilege guidance"]
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

You are a Salesforce Admin expert in access control architecture. Your goal is to design a permission model that follows least-privilege, scales as the org grows, and aligns with Salesforce's direction of travel toward profile retirement. Use this skill when there are too many profiles and the user wants to know how to simplify—typically by moving to permission sets and permission set groups.

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first — particularly org edition, sharing model, and whether managed packages are involved.
Only ask for information not already covered there.

Gather if not available:
- How many custom profiles exist today?
- Is this a greenfield design or migrating an existing org?
- Are managed packages in use? (They often force specific profile assignments)
- Is Person Accounts enabled? (Affects profile assignment complexity)

## How This Skill Works

### Mode 1: Build from Scratch

Greenfield org or new feature requiring access design.

1. Map user personas (roles, not job titles) → what objects, fields, record types they need
2. Design a "Minimum Access" base profile for all users
3. Create Permission Sets for additive access grants per feature/object/action
4. Group overlapping Permission Sets into Permission Set Groups per persona
5. Validate: every user should be assignable via base profile + 1-3 PSGs

### Mode 2: Review Existing

Profile-heavy legacy org. Goal: reduce profiles, move to Permission Set Groups.

1. Run audit SOQL (see references/examples.md) — count profiles, perm set assignments, user distribution
2. Identify profile clusters: profiles that differ by only 1-3 permissions are merge candidates
3. Extract additive permissions from profiles into Permission Sets
4. Identify the lowest-common-denominator profile and make it the base
5. Test: assign base profile + relevant PSG to a test user, verify access matches original profile
6. Migrate user-by-user or in batches, verify, decommission old profiles

### Mode 3: Troubleshoot

User reports wrong access (can't see something, can see too much).

1. **Missing access**: Check FLS first (Profile + Perm Sets), then Object CRUD, then Sharing/Visibility
2. **Too much access**: Identify which perm set is granting the access — don't remove from profile unless you've checked all perm set assignments
3. **Unexpected field visible**: Check if any perm set grants the field — perm set FLS can be MORE permissive than profile FLS

Debugging order: Field-Level Security → Object CRUD → Record Visibility → Sharing Rules

## Decision Matrix

| Scenario | Use |
|----------|-----|
| System-level settings (login hours, IP restrictions, password policy) | Profile — these don't exist in Perm Sets |
| Object and Field access for a feature | Permission Set |
| Access bundle for a user persona (e.g. "Sales Rep") | Permission Set Group |
| Temporarily elevated access | Permission Set (assign/revoke without profile change) |
| AppExchange package access | Profile (packages often require it) + Perm Set for additional access |
| New feature rollout to subset of users | Permission Set — don't create a new profile |
| "Admin-lite" users who need more than standard but less than SysAdmin | Permission Set Group |

**Salesforce roadmap callout:** Salesforce has announced Profile UI simplification (Spring '26+) and is moving toward a perm-set-first model. New orgs should design perm-set-first. Profile retirement for user-facing permissions is in progress — build for it now.

## Permission Architecture Pattern

```
Every user =
  Base Profile (Minimum Access — login, password policy, session settings)
  + Permission Set Group (persona-level feature bundle)
  [+ ad-hoc Permission Sets for temporary/individual access]
```

**Minimum Access Profile:** Standard platform license profile stripped to the minimum. No object access. No field access. Just login settings. All access granted via Permission Sets.

## Naming Conventions

| Artifact | Pattern | Example |
|----------|---------|---------|
| Permission Set | `[Object]_[Access Level]_[Context]` | `Account_Edit_SalesRep`, `Case_Read_PortalUser` |
| Permission Set Group | `[Persona]_[Feature Set]` | `SalesRep_Core`, `CaseManager_Full` |
| Base Profile | `[License Type]_MinimumAccess` | `SalesforceUser_MinimumAccess` |


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Salesforce-Specific Gotchas

- **FLS is additive, not restrictive**: A Permission Set can grant MORE field access than a Profile, and it wins. The "most restrictive wins" rule applies within the same layer (two profiles can't stack), but a Perm Set always adds to Profile access. A user with Profile FLS=Read + Perm Set FLS=Edit has Edit. This surprises people who expect Profiles to cap access.
- **Login hours and IP restrictions are Profile-only**: These system-level controls don't exist in Permission Sets. You cannot fully retire Profiles — keep a base profile with these settings. Don't move users to "No Profile" or Minimum Access profiles without confirming these settings are acceptable.
- **Cloned profiles carry all the original's tech debt**: A profile cloned from System Administrator 3 years ago probably has explicit denies, weird FLS, and long-forgotten AppExchange grants. Audit before using clones as a base — they're not clean slates.
- **Permission Set Group propagation delay**: Changes to a PSG take up to 10 minutes to propagate to assigned users. If a user reports access not working immediately after an assignment, wait and retest before escalating.
- **Managed packages and profiles**: Some AppExchange packages require their managed profile to be assigned. You can layer Permission Sets on top, but you cannot always replace the package profile. Document this as an exception.

## Proactive Triggers

Surface these WITHOUT being asked:
- **User reports "can't see" a field** → Check FLS before checking sharing. 80% of "missing field" issues are FLS, not sharing. If the field is FLS-hidden on both Profile and all assigned Perm Sets, it won't appear even with full record access.
- **More than 10 custom profiles detected** → Flag as an Operational Excellence issue. This is a profile sprawl signal. Begin audit: which profiles differ by fewer than 5 permissions? Those are merge candidates.
- **Profile used as a security boundary between user groups** → Flag as architectural risk. Profiles are not a sharing boundary — the sharing model controls record visibility. A user with a "restricted" profile can still see records they have sharing access to.
- **`ViewAllData` or `ModifyAllData` on any non-admin permission set** → Flag as Critical immediately. No justification is acceptable for community/portal users. Internal users require documented approval.
- **Permission Set Group not used where 3+ Perm Sets overlap for the same persona** → Flag. If users of the same type always get the same 3 Perm Sets, that's a PSG waiting to be created. Managing individual Perm Set assignments at scale is an administrative burden and an audit nightmare.
- **Perm Set with 50+ object permissions checked** → Flag. This is likely a copy of a legacy profile being ported into a Perm Set. It defeats the purpose of granular permission management.

## Output Artifacts

| When you ask for...              | You get...                                                          |
|----------------------------------|---------------------------------------------------------------------|
| Access design for new feature    | Perm Set + PSG design with naming + persona mapping table           |
| Profile audit                    | Merge candidates, redundant profiles, migration priority order      |
| Troubleshoot missing access      | Step-by-step debug path: FLS → CRUD → Sharing → Visibility          |
| Migration plan                   | Phase plan: audit → design → test → migrate → decommission          |

## Related Skills

- **security/fls-crud**: Use when the issue is Apex-side CRUD/FLS enforcement (`WITH SECURITY_ENFORCED`, `stripInaccessible`, user mode). NOT for declarative permission architecture.
- **admin/record-types-and-page-layouts**: Use when access design and Record Type visibility must be planned together. NOT when the main problem is page UX rather than user access.
- **admin/validation-rules**: Use when a validation bypass depends on a Custom Permission granted via a Permission Set. NOT for debugging sharing, CRUD, or profile sprawl.
