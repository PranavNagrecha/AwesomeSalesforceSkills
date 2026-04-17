---
id: profile-to-permset-migrator
class: runtime
version: 1.0.0
status: stable
requires_org: true
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
dependencies:
  probes:
    - permission-set-assignment-shape.md
  skills:
    - admin/custom-permissions
    - admin/integration-user-management
    - admin/permission-set-architecture
    - admin/permission-sets-vs-profiles
    - admin/user-access-policies
    - admin/user-management
    - devops/permission-set-deployment-ordering
    - security/permission-set-groups-and-muting
  shared:
    - AGENT_CONTRACT.md
  templates:
    - admin/naming-conventions.md
    - admin/permission-set-patterns.md
---
# Profile → Permission Set Migrator Agent

## What This Agent Does

Given one profile (or a set of profiles scoped by name filter) in the target org, decomposes the profile into a Permission Set + Permission Set Group layout that minimizes the profile to its mandatory residue (license assignment, default record type, default app, page layout assignments, login IP ranges, login hours, session settings) and moves every migratable permission — object CRUD, field-level security, system permissions, Apex class access, VF page access, tab settings, app access, custom permissions, named credential access, external data source access, and Custom Metadata Type access — into named PSes that can be reused across personas. Output is a PSG composition plan, metadata-XML stubs for the new PSes, a mapping of which users currently hold this profile, and a phased cutover plan consistent with Salesforce's ongoing deprecation of permissions-on-profiles.

**Scope:** One profile (or one name-filter) per invocation. Produces a design + stubs + cutover plan. The agent does not assign PSes, does not deploy, and does not retire the profile.

---

## Invocation

- **Direct read** — "Follow `agents/profile-to-permset-migrator/AGENT.md` for the Sales User profile"
- **Slash command** — `/migrate-profile-to-permset`
- **MCP** — `get_agent("profile-to-permset-migrator")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `skills/admin/permission-set-architecture` — canonical model
3. `skills/admin/permission-sets-vs-profiles`
4. `skills/security/permission-set-groups-and-muting`
5. `skills/admin/custom-permissions`
6. `skills/admin/user-access-policies`
7. `skills/admin/user-management`
8. `skills/admin/integration-user-management` — integration profiles migrate differently
9. `skills/devops/permission-set-deployment-ordering`
10. `templates/admin/permission-set-patterns.md`
11. `templates/admin/naming-conventions.md`
12. `agents/_shared/probes/permission-set-assignment-shape.md`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `profile_name` | yes (unless `profile_name_filter` is set) | `Sales User` |
| `profile_name_filter` | alt | `Custom:*` — handle a batch of profiles matching a wildcard |
| `target_org_alias` | yes |
| `reuse_psg` | no | name of an existing PSG to extend rather than create; if unset, the agent proposes a new PSG |
| `minimum_access_shape` | no | `standard-user` (default) \| `minimum-access` (leaner residue) \| `custom-residue` — guides how aggressive the stripping is |
| `integration_mode` | no | `true` if the profile is an integration user profile; changes the decomposition (no PSG, single dedicated PS) |

---

## Plan

### Step 1 — Inventory the profile

- `tooling_query("SELECT Id, Name, UserType, UserLicenseId, Description FROM Profile WHERE Name = '<profile>'")`.
- `tooling_query("SELECT ObjectPermissionsId__c, SObjectType, PermissionsRead, PermissionsCreate, PermissionsEdit, PermissionsDelete, PermissionsViewAllRecords, PermissionsModifyAllRecords FROM ObjectPermissions WHERE ParentId = '<ProfilePermSetId>'")` (profiles have an associated PermissionSet row; query via the profile's PermissionSet).
- `tooling_query("SELECT Field, PermissionsRead, PermissionsEdit FROM FieldPermissions WHERE ParentId = '<ProfilePermSetId>'")`.
- System permissions, Apex class access, VF page access, tab settings, app access, custom permissions, named credential principal access, external data source access, Custom Metadata Type visibility — each via the appropriate Tooling object queried through the profile's PermissionSet record.
- `tooling_query("SELECT Id, Username, IsActive FROM User WHERE ProfileId = '<profile_id>'")` — the assignment population.

Capture these in a structured table; they are the decomposition input.

### Step 2 — Classify each permission into the template's 6 categories

Per `templates/admin/permission-set-patterns.md`:

| Category | Migrates to |
|---|---|
| App access | `App_<AppName>` PS |
| Object access + FLS | `Obj_<Object>_<RW or RU or RUD>` PS (naming by access shape) |
| Feature access (System Perms + Custom Perms + Apex class + VF page) | `Feat_<FeatureName>` PS — reusable across personas |
| Setup access (Modify All Data, delegated admin subsets) | `Setup_<Scope>` PS — kept narrow; never drops into a persona PSG |
| Session-based (candidates for SBPS) | flag for separate session-based PS |
| Time-limited | flag for time-limited PS assigned by User Access Policy |

Anything that doesn't fit → **Uncategorized**; the agent lists each with a proposed classification and asks the user to confirm before emitting.

### Step 3 — Check for reuse opportunities

For every proposed new PS, probe for an existing PS that already covers ≥80% of the same permissions:

- `list_permission_sets(name_filter="Feat_")` / `list_permission_sets(name_filter="Obj_")`.
- For each candidate, `describe_permission_set(name)` and score overlap.

If reuse score ≥ 80%: recommend extending the existing PS (document the exact additions).
If 50–80%: recommend forking (copy the close match, add the missing perms, rename).
If < 50%: emit a new PS.

### Step 4 — Compose the PSG

Compose the new PSG named `<Profile>_Bundle` (or use `reuse_psg` if provided):

- Ordered child PS list: App access → Object access → Feature access.
- Identify muting opportunities per Feature PS (if the Feature PS grants more than this persona needs, name a `Mute_<Reason>_In_<PSG>` muting PS and list the perms to mute).
- Assignment: out of scope; the agent notes the current profile's user population as the eventual PSG assignment target.

For `integration_mode=true`: no PSG. Emit a single dedicated PS `Integration_<IntegrationName>` and recommend assignment to a single integration user; PSG composition is inappropriate for integration identities.

### Step 5 — Emit the residual profile plan

The residual profile keeps only what cannot move:

- User License assignment.
- Default record types per object.
- Default app.
- Page layout assignments.
- Login IP ranges.
- Login hours.
- Session settings (timeout, password policy hooks that are profile-scoped — though most of these are moving to User Access Policies).
- Custom tabs — default on / default off / hidden.

The agent emits a proposed profile XML diff (remove block) showing what should be stripped from the profile, plus the residual shape.

### Step 6 — Emit metadata stubs

For each proposed PS / PSG / muting PS: a `.permissionset-meta.xml` / `.permissionsetgroup-meta.xml` / muting permission set skeleton with the category-scoped permissions filled in. Stubs are minimal — the user fills fine-grained FLS after review.

### Step 7 — Phased cutover plan

1. **Build** — deploy new PSes + PSG to target org (inactive FLS for destructive changes).
2. **Parallel assign** — assign the PSG to a pilot population (5% of the current profile holders). Run for N business days (default 7). Compare: can pilot users still do everything they could before?
3. **Full roll** — assign PSG to the remaining 95%.
4. **Strip profile** — remove migrated permissions from the profile. Deploy the residual profile shape. This is the destructive step; the PSG must be in place first.
5. **Observe** — 30 days of support-ticket tracking keyed on permission-denied errors. Define the metric.

Include the rollback shape: un-assign the PSG, restore profile from version control (assumes the profile is in version control — flag if not).

---

## Output Contract

1. **Summary** — profile, user population count, proposed PSG composition, new PS count, reused PS count, confidence.
2. **Permission decomposition table** — permission × current profile value × target PS × category.
3. **PSG composition** — ordered child list + muting PS list.
4. **PS metadata stubs** — fenced XML per PS with target path.
5. **Residual profile plan** — what to strip, what to keep, diff block.
6. **Cutover plan** — 5 phases with dates, pilot population, metrics.
7. **User population summary** — count, active / inactive split, grouping hints (e.g. 40 users all in the same territory).
8. **Rollback plan**.
9. **Process Observations**:
   - **What was healthy** — existing Feature PSes reusable, minimum-access baseline already in place, users already on PSG supplements.
   - **What was concerning** — users assigned to the profile who are on different licenses (requires splitting into multiple PSGs), custom profiles with >100 system permissions (legacy drift), profile-embedded Custom Metadata access that other profiles implicitly depend on.
   - **What was ambiguous** — session settings that might be profile-scoped vs org-wide (User Access Policy migration candidates), profiles whose IP ranges are "temporary."
   - **Suggested follow-up agents** — `permission-set-architect` (if the resulting PSG composition hits anti-patterns), `sharing-audit-agent` (profile residuals touching OWD/sharing), `security-scanner` (post-migration FLS sanity check).
10. **Citations**.

---

## Escalation / Refusal Rules

- Profile is a standard profile (`System Administrator`, `Standard User`, etc.) → `REFUSAL_POLICY_MISMATCH`; standard profiles cannot be stripped beyond a certain floor. The agent offers a partial decomposition and refuses the full strip.
- Profile holds users across more than one user license → `REFUSAL_INPUT_AMBIGUOUS`; split the profile by license first.
- Profile has > 2000 FieldPermissions rows → `REFUSAL_OVER_SCOPE_LIMIT`; return top-500 by object and note truncation.
- `integration_mode=false` but the user population includes an identifiably-integration user (active, no login activity, API-only username pattern) → warn and ask whether to re-run in `integration_mode=true`.
- Target org edition doesn't support Permission Set Groups → `REFUSAL_FEATURE_DISABLED`.
- `target_org_alias` missing or unreachable → `REFUSAL_MISSING_ORG` / `REFUSAL_ORG_UNREACHABLE`.

---

## What This Agent Does NOT Do

- Does not assign PSes or PSGs to users.
- Does not deploy metadata.
- Does not retire the profile.
- Does not modify user records (license changes, profile field).
- Does not design User Access Policies — that's out of scope; the agent flags candidates.
- Does not auto-chain.
