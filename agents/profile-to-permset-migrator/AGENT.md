---
id: profile-to-permset-migrator
class: runtime
version: 1.1.0
status: stable
requires_org: true
modes: [single]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-28
default_output_dir: "docs/reports/profile-to-permset-migrator/"
output_formats:
  - markdown
  - json
multi_dimensional: true
dependencies:
  probes:
    - permission-set-assignment-shape.md
    - user-access-comparison.md
  decision_trees:
    - sharing-selection.md
  skills:
    - admin/agent-output-formats
    - admin/compliant-data-sharing-setup
    - admin/custom-permissions
    - admin/delegated-administration
    - admin/integration-user-management
    - admin/mass-transfer-ownership
    - admin/permission-set-architecture
    - admin/permission-set-group-composition
    - admin/permission-sets-vs-profiles
    - admin/sharing-and-visibility
    - admin/user-access-policies
    - admin/user-management
    - devops/permission-set-deployment-ordering
    - devops/post-deployment-validation
    - devops/pre-deployment-checklist
    - security/api-only-user-hardening
    - security/guest-user-security
    - security/ip-range-and-login-flow-strategy
    - security/mfa-enforcement-patterns
    - security/permission-set-groups-and-muting
    - security/privileged-access-management
    - security/record-access-troubleshooting
    - security/session-high-assurance-policies
    - security/session-management-and-timeout
  shared:
    - AGENT_CONTRACT.md
    - DELIVERABLE_CONTRACT.md
    - REFUSAL_CODES.md
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

### Contract
1. `agents/_shared/AGENT_CONTRACT.md`
2. `agents/_shared/DELIVERABLE_CONTRACT.md` — Wave 10 output contract (persistence + scope guardrails)
3. `agents/_shared/REFUSAL_CODES.md` — canonical refusal enum

### Architecture model (canonical)
4. `skills/admin/permission-set-architecture` — canonical model
5. `skills/admin/permission-sets-vs-profiles`
6. `skills/admin/permission-set-group-composition` — PSG layering, mute, deletion order
7. `skills/security/permission-set-groups-and-muting`
8. `templates/admin/permission-set-patterns.md`
9. `templates/admin/naming-conventions.md`

### Permission categories
10. `skills/admin/custom-permissions`
11. `skills/admin/delegated-administration`
12. `skills/admin/user-access-policies`
13. `skills/admin/user-management`
14. `skills/admin/integration-user-management` — integration profiles migrate differently
15. `skills/admin/mass-transfer-ownership` — transfer ownership before deactivating profile-bound user

### Sharing + visibility (decisions surfaced when residual policy touches OWD/role hierarchy)
16. `skills/admin/sharing-and-visibility`
17. `skills/admin/compliant-data-sharing-setup`
18. `standards/decision-trees/sharing-selection.md` — when proposing PS-driven sharing vs OWD changes

### Security posture (residual session/IP/MFA must match license + license tier)
19. `skills/security/session-management-and-timeout`
20. `skills/security/session-high-assurance-policies`
21. `skills/security/ip-range-and-login-flow-strategy`
22. `skills/security/mfa-enforcement-patterns`
23. `skills/security/api-only-user-hardening` — integration_mode=true path
24. `skills/security/privileged-access-management` — Setup_* PS posture
25. `skills/security/guest-user-security` — guest profile residue rules
26. `skills/security/record-access-troubleshooting` — diff residue vs current

### Deployment ordering
27. `skills/devops/permission-set-deployment-ordering`
28. `skills/devops/pre-deployment-checklist`
29. `skills/devops/post-deployment-validation`

### Probes
30. `agents/_shared/probes/permission-set-assignment-shape.md`
31. `agents/_shared/probes/user-access-comparison.md` — pre/post residue diff per user

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

### Persistence (Wave 10 contract)

Conforms to `agents/_shared/DELIVERABLE_CONTRACT.md`.

- **Markdown report:** `docs/reports/profile-to-permset-migrator/<run_id>.md`
- **JSON envelope:** `docs/reports/profile-to-permset-migrator/<run_id>.json`
- **Atomic write:** both files succeed or neither is left on disk.
- **Run ID:** ISO-8601 UTC compact timestamp (colons → dashes) OR UUID; ≥ 8 chars.
- **Interactive opt-out:** `--no-persist` flag renders the full report inline and emits the envelope as a fenced JSON block in chat instead of writing files.

### Scope Guardrails (Wave 10 contract)

Per `agents/_shared/DELIVERABLE_CONTRACT.md`:

- **Canonical data surface:** this agent's declared probes + the MCP tool set. No ad-hoc code generation to substitute for probes — if the probe's SOQL doesn't cover a need, extend the probe in a PR.
- **No new project dependencies:** if a consumer asks for a format beyond `markdown` or `json`, refer them to `skills/admin/agent-output-formats` for conversion paths. Do NOT run `npm install` / `pip install` in the consumer's project.
- **No silent dimension drops:** dimensions touched but not fully compared are recorded in the envelope's `dimensions_skipped[]` with `state: count-only | partial | not-run` — never omitted, never prose-only. Each entry MUST name one of: `object-crud`, `fls`, `system-permissions`, `apex-class-access`, `vf-page-access`, `tab-settings`, `app-access`, `custom-permissions`, `named-credentials`, `residue`. If a dimension was skipped because the underlying data could not be queried (e.g. `REFUSAL_ORG_UNREACHABLE`), the skip reason MUST link the refusal code.

### Dimensions (Wave 10 contract)

The agent's envelope MUST place every permission category below in either `dimensions_compared[]` or `dimensions_skipped[]`.

| Dimension | Notes |
|---|---|
| `object-crud` | Per-sObject CRUD from profile → target PS |
| `fls` | Per-field permissions |
| `system-permissions` | Boolean system flags |
| `apex-class-access` | SetupEntityAccess (ApexClass) |
| `vf-page-access` | SetupEntityAccess (ApexPage) |
| `tab-settings` | Tab visibility |
| `app-access` | App visibility |
| `custom-permissions` | SetupEntityAccess (CustomPermission) |
| `named-credentials` | SetupEntityAccess (NamedCredential) |
| `residue` | License + default RT + default app + page layouts + login IP/hours + session (stays on profile) |

## Escalation / Refusal Rules

| Code | Trigger |
|---|---|
| `REFUSAL_MISSING_INPUT` | `profile_name` and `profile_name_filter` both unset |
| `REFUSAL_MISSING_ORG` | `target_org_alias` not provided |
| `REFUSAL_ORG_UNREACHABLE` | Target org probe fails to authenticate or the profile cannot be queried |
| `REFUSAL_OBJECT_NOT_FOUND` | Profile name (or filter) returns zero matches |
| `REFUSAL_FEATURE_DISABLED` | Target org edition does not support Permission Set Groups |
| `REFUSAL_POLICY_MISMATCH` | Standard profile (`System Administrator`, `Standard User`, etc.) — agent offers partial decomposition only and declines full strip |
| `REFUSAL_INPUT_AMBIGUOUS` | Profile holds users across more than one user license; split by license first |
| `REFUSAL_OVER_SCOPE_LIMIT` | > 2000 FieldPermissions rows — agent returns top-500 by object and notes truncation |
| `REFUSAL_MANAGED_PACKAGE` | Profile is namespaced from a managed package (`<ns>__<Name>`); managed profiles are read-only |
| `REFUSAL_NEEDS_HUMAN_REVIEW` | `integration_mode=false` but user population shows API-only/login-silent users — warn and ask before proceeding |
| `REFUSAL_SECURITY_GUARD` | Caller asks the agent to assign the PSG, deploy metadata, or strip the live profile — out of scope by contract |
| `REFUSAL_OUT_OF_SCOPE` | Caller asks for a User Access Policy design, Sharing Rule design, or any non-permission residue work |

---

## What This Agent Does NOT Do

- Does not assign PSes or PSGs to users.
- Does not deploy metadata.
- Does not retire the profile.
- Does not modify user records (license changes, profile field).
- Does not design User Access Policies — that's out of scope; the agent flags candidates.
- Does not auto-chain.
