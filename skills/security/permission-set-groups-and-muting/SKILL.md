---
name: permission-set-groups-and-muting
description: "Use when designing or reviewing permission-set-group architecture, especially profile minimization, group composition, muting strategy, and migration away from profile-heavy security models. Triggers: 'permission set group', 'muting permission. NOT for record-sharing design or CRUD/FLS review in Apex code — use admin/permission-set-architecture."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
tags:
  - permission-set-groups
  - muting
  - profiles
  - least-privilege
  - access-architecture
triggers:
  - "how should we use permission set groups"
  - "muting permission set strategy"
  - "migrate from profiles to permission sets"
  - "permission bundle architecture in Salesforce"
  - "why use PSG instead of assigning many permission sets"
  - "mute one permission in a permission set group for a persona"
  - "deploy a permission set group and muting permission set as metadata"
inputs:
  - "current profile and permission-set model"
  - "target job functions or feature bundles"
  - "whether subtractive muting is needed"
outputs:
  - "PSG architecture recommendation"
  - "review findings for profile-heavy or unclear access design"
  - "migration pattern for permission bundle design"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

# Permission Set Groups And Muting

Use this skill when access design has outgrown direct profile customization and one-off permission-set assignments. Permission Set Groups (PSGs) compose reusable access bundles. A muting permission set subtracts permissions from one group's aggregate when the bundle is almost right but still too broad.

---

## Before Starting

Gather this context before working on anything in this domain:

- How many profiles, permission sets, and direct assignments already exist?
- Are the target bundles feature-based, role-based, or a mix?
- Is the real problem permission composition, or record visibility and sharing instead?
- Do any personas need time-boxed access (assignment expiration) or session-activated access (`hasActivationRequired`)?

---

## Questions to Ask Before Configuring

| Question | Why it matters | What a good answer adds | What proper configuration adds over just doing it |
|---|---|---|---|
| Is the permission you want to remove also granted by the user's profile or by a permission set assigned outside the group? | Permissions from profiles, permission sets, and PSGs are all honored; muting acts only inside the group, so another grant keeps the access. | Finds every grant path before muting. | Muting actually removes the access for the persona. |
| Which persona differs from the shared bundle, and by how many permissions? | Muting is meant for small subtractions; many mutes signal that the base permission sets should be split. | A short, named mute list per group. | The group stays explainable in an access review. |
| Will the PSG, its permission sets, and its muting set ship as metadata? | A PSG holds no permissions itself; the permissions live in the referenced permission sets, and the guide says to retrieve PermissionSet with PermissionSetGroup. Since API 40.0, a deployed permission set's file replaces its contents. | Deploys the whole bundle together with full permission set files. | No partial permission set overwrites a production grant. |
| Who will check group recalculation status after a change? | PSG status moves through Updating to Updated, or to Failed; until then the aggregate is not current. | A post-deploy check of `PermissionSetGroup.Status`. | Users get the new access only when the group says Updated. |
| Does any access need an end date or a session activation step? | `PermissionSetAssignment.ExpirationDate` (API 52.0+) ends an assignment; `hasActivationRequired` (API 53.0+) needs an active session activation. | Time-boxed or step-up access designed in. | Temporary access does not become permanent. |

---

## Core Concepts

### PSGs Are the Composition Layer

A PSG bundles permission sets so access can be assigned as one unit. The Metadata API sample says it plainly: "Individual permissions are included in the permission set referenced, not in the permission set group." Platform recalculation builds the group's aggregate from its `PermissionSetGroupComponent` rows, and `Status` reports `Updated`, `Outdated`, `Updating`, or `Failed`.

### Muting Subtracts From One Group's Aggregate

`MutingPermissionSet` has the same fields as `PermissionSet`. A setting that is **enabled** in the muting set is **turned off** for the PSG it belongs to. For field permissions, `PermissionsRead=true` and `PermissionsEdit=true` in a muting set mute read and edit (Object Reference, FieldPermissions > Muting Permissions). Muting is not a permission source, and it does not reach grants that come from the profile or from permission sets assigned directly.

### Grants Are Additive Across Every Path

The Security Guide states that profiles, permission sets, and PSGs "grant access but not to deny access," and that revoking a permission means removing every instance of it from the user. The same section names muting permission sets in PSGs as one way to remove a permission for the group's users.

### Minimal Profiles Still Matter

Profiles do not disappear. The thinner the base profile, the more a PSG design controls effective access, because a profile grant can't be muted.

### Migration Is an Access-Architecture Project

Moving from profile-centric design to PSGs needs naming, persona testing, and a staged rollout. It is not just a metadata conversion.

---

## Common Patterns

### Feature Bundle PSG

**When to use:** Many users need the same collection of capabilities, such as service console plus case tools.

**How it works:** Create focused permission sets per feature, then group them into one assignable PSG.

**Why not the alternative:** Repeating many direct assignments scales poorly and is harder to audit.

### Base Bundle Plus Muting

**When to use:** Two personas are almost identical except for a few restricted capabilities.

**How it works:** Create a second PSG with the same permission sets plus a muting permission set that enables (and so mutes) only the restricted permissions. The deployable files are in [references/metadata-examples.md](references/metadata-examples.md).

### Profile-Minimization Migration

**When to use:** The org has many feature-heavy profiles and access changes are risky.

**How it works:** Move feature access into permission sets, compose PSGs, assign them in parallel with the old profiles, verify effective access, then strip the profiles.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Many recurring permission-set combinations | Permission Set Groups | Better composition and assignment hygiene |
| One bundle is almost right for two personas | Second PSG with a muting permission set | Reuse without cloning permission sets |
| The permission to remove is also on the profile | Remove it from the profile first | Muting can't override a profile grant |
| Profiles still hold most feature access | Migrate toward minimal profiles plus PSGs | Better long-term governance |
| Access issue is record visibility | Use sharing and security-model skills | PSGs do not solve sharing architecture |
| Contractor or project access that must end | Assignment with `ExpirationDate` | The assignment ends on its own |

---

## Recommended Workflow

1. Inventory grants: query `PermissionSetAssignment` and the profile for each persona, and list every path that grants the permissions in scope (see the SOQL in [references/metadata-examples.md](references/metadata-examples.md)).
2. Design focused permission sets and the PSGs per persona; write down each mute and the reason for it.
3. Build the files: `PermissionSet`, `PermissionSetGroup`, and `MutingPermissionSet` in source format, then run `python3 skills/security/permission-set-groups-and-muting/scripts/check_permission_set_groups_and_muting.py --manifest-dir force-app`.
4. Deploy the whole bundle to a sandbox, wait for `PermissionSetGroup.Status = 'Updated'`, and test each persona with a real user login.
5. Roll out in phases: assign PSGs alongside old profiles, verify, then remove profile grants in batches with a rollback list.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Profiles are being minimized instead of expanded.
- [ ] Permission sets have clear, focused purposes.
- [ ] PSGs represent meaningful bundles, not random collections.
- [ ] Each muted permission is not also granted by the profile or a directly assigned permission set.
- [ ] Muting sets enable only the permissions to be removed, with a documented reason.
- [ ] Permission sets deploy as complete files together with their PSG.
- [ ] Group status confirmed `Updated` after each change; personas tested with real logins.
- [ ] Migration and rollback are planned for profile-centric orgs.

---

## Salesforce-Specific Gotchas

Full write-ups with sources are in [references/gotchas.md](references/gotchas.md).

| Gotcha | One-line summary |
|---|---|
| Enabled means muted | In a muting set, `true` turns the permission off for the group. |
| Muting scope | Muting can't remove a grant that comes from the profile or another assignment. |
| Permissions live in sets | A PSG file has no permissions; deploy and retrieve its permission sets with it. |
| Permission set deploy | Since API 40.0 a deployed permission set file replaces the set's contents. |
| Recalculation | Group access is current only when `Status` is `Updated`. |
| Expiring access | `ExpirationDate` ends an assignment; nothing else does. |

---

## Output Artifacts

| Artifact | Description |
|---|---|
| PSG design review | Findings on composition, muting, and profile minimization |
| Access-bundle plan | Recommended permission-set and PSG structure with mute list |
| Migration outline | Phased approach for moving from profile-heavy access to PSGs |
| Bundle metadata | `permissionsets/`, `permissionsetgroups/`, `mutingpermissionsets/` files |

---

## Related Skills

- `security/org-hardening-and-baseline-config`: use when baseline org controls are the concern rather than feature-access composition.
- `admin/permission-sets-vs-profiles`: use for the broader admin-side distinction between permission sets and profiles.
- `apex/apex-security-patterns`: use when code-level sharing and CRUD/FLS enforcement are the real issue.
