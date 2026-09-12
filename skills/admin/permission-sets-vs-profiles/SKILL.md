---
name: permission-sets-vs-profiles
description: "Use when designing or auditing Salesforce access control — deciding between Profiles, Permission Sets, and Permission Set Groups. Triggers: 'user can't see field', 'too many profiles', 'permission model', 'least privilege', 'profile migration', 'what stays on the profile', 'profile only settings', 'login hours permission set', 'layout assignment permission set', 'IsOwnedByProfile', 'profile retrieve empty'. NOT for sharing rules or record-level access — use admin/sharing-and-visibility for that."
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
  - "profile retrieve missing object permissions field permissions"
  - "what has to stay on the profile when we move to permission sets"
  - "can login hours be set in a permission set"
  - "retrieved profile xml is almost empty"
  - "deployed the profile but the permission is still there"
  - "user landed on the wrong app after we moved them to a minimum access profile"
  - "permission set assignment failed licence mismatch"
  - "where are a profile's object permissions stored in soql"
  - "copied tabVisibilities into a permission set and the deploy failed"
  - "should I move this permission from the profile to a permission set"
  - "description data value too large max length 255"
inputs: ["persona matrix", "current access model", "managed package constraints"]
outputs: ["permission model recommendation", "profile residue list — what cannot move", "deployable base-profile and permission-set XML", "access migration findings", "least-privilege guidance"]
dependencies: []
version: 1.2.2
author: Pranav Nagrecha
updated: 2026-09-12
---

You are a Salesforce Admin expert in access control architecture. Your goal is to design a permission model that follows least-privilege, scales as the org grows, and follows Salesforce's recommended permission-set-led model — a recommendation, not a deadline (see **Salesforce roadmap callout** below). Use this skill when there are too many profiles and the user wants to know how to simplify—typically by moving to permission sets and permission set groups.

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first — particularly org edition, sharing model, and whether managed packages are involved.
Only ask for information not already covered there.

Gather if not available:
- How many custom profiles exist today?
- Is this a greenfield design or migrating an existing org?
- Are managed packages in use? (They often force specific profile assignments)
- Is Person Accounts enabled? (Affects profile assignment complexity)

## Questions to Ask Before Configuring

Ask these before writing any XML. Each answer removes one of the failure modes in `references/gotchas.md`; an assistant that skips them produces a decomposition that deploys cleanly and leaves users worse off.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "What is on the current profile that has no permission-set equivalent?" | `loginHours`, `loginIpRanges`, `layoutAssignments`, the `default` app and the `default` record type exist only on `Profile`. They are the residue, and they are the only reason a profile still exists | The residue list — the exact contents of the base profile file |
| "Which users hold this profile, and do they all hold the same user licence?" | A permission set with a `LicenseId` can only be assigned where the profile's `UserLicenseId` matches; a mixed-licence population needs to be split before, not after | The population split, and whether `LicenseId` should be left empty |
| "Which objects, fields, tabs, apps, record types, layouts and classes are in scope?" | A profile retrieve returns permissions only for what else is in the same manifest. Without this list the retrieved profile is silently incomplete | The package.xml that makes the retrieve honest, reused for the deploy |
| "Are we adding access, or taking it away?" | Permission sets only grant. Removing access means editing the profile explicitly to `false`, or muting inside a group — two different mechanisms with different blast radii | Whether this is an additive change or a strip, and which mechanism applies |
| "Is the profile standard (`custom=false`) or custom?" | Editing standard objects on standard profiles is disabled in API 50.0+, so the strip phase will not apply | A clone-first decision before any deploy is attempted |
| "Does a managed package require this profile to be assigned?" | Some packages ship profile-dependent configuration that a permission set cannot replace | A documented exception list, or confirmation that the package ships its own permission sets |
| "Who verifies afterwards, and against what?" | "It deployed" is not evidence. Effective access is the union of the profile and every assigned permission set, visible per user in Setup | A named verification step: a View Summary check plus the assignment-count SOQL |

What a proper configuration adds over just moving permissions across: the profile keeps exactly the settings that cannot live anywhere else, the permission set carries a complete and licence-compatible grant, and the strip phase actually revokes what it claims to revoke instead of silently overlaying.

## What Only a Profile Can Hold

This is the decision, reduced to its schema. Left column = in the `Profile` metadata field table and absent from `PermissionSet`; nothing here can migrate.

| Profile-only | Permission-set equivalent |
|---|---|
| `loginHours`, `loginIpRanges` | none |
| `layoutAssignments` | none |
| `categoryGroupVisibilities`, `loginFlows`, `custom` | none |
| `<default>` inside `applicationVisibilities` — the landing app | `visible` only; no `default` child |
| `<default>` / `<personAccountDefault>` inside `recordTypeVisibilities` | `visible` only; access moves, the preselection does not |
| `tabVisibilities` (`DefaultOff` / `DefaultOn` / `Hidden`) | `tabSettings` (`Available` / `None` / `Visible`) — different tag, different enum |

Everything else — object CRUD, FLS, system and app permissions, Apex class and Visualforce page access, custom permissions, flow access, custom metadata and custom setting access, external data sources — exists on both types and migrates. The full element-by-element table, with the `PermissionSet`-only side and the required-field differences, is in `references/metadata-examples.md`.

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

**Salesforce roadmap callout (updated June 2026 — read before quoting a deadline):**
The planned retirement of permissions in profiles is **cancelled**, not deferred. Salesforce Help article 003834041, published 6 Jun 2026: *"Salesforce previously announced the retirement of permissions in profiles starting in Spring '26. This enforcement has now been cancelled"* — citing customer feedback and remaining feature gaps. No replacement end-of-life date has been published.

What this means in practice:
- Object, field, system and app permissions stay configurable on Profiles. Nothing breaks in a Summer '26 org that still grants access through profiles. Note Salesforce's hedge, though — the article says profiles *"will continue to support permissions **for now**"*. No replacement date, but no promise of permanence either; don't tell a customer profiles are safe forever.
- Profiles themselves were never being retired — that claim was always wrong.
- Salesforce *"recommends transitioning to a permission set–led security model for improved flexibility and scalability."* That is a recommendation, not a cutoff.

So: still design perm-set-first, because it is easier to audit, assign and unwind — and sequence any migration on business value, not on a clock. Do not sell a customer a profile decomposition as compliance with a Spring '26 deadline; there isn't one.

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

1. **Split the profile on the schema, not on judgement** — walk the *What Only a Profile Can Hold* table above and sort every element into residue or migratable. Record the residue in `templates/permission-set-design-template.md` § Base Profile Residue; that list is the base profile file
2. **Build the manifest before the retrieve** — name every object, field, tab, app, record type, layout and class whose permissions are in scope, then retrieve with `--manifest`. A `Profile:` retrieve without them returns an incomplete file (`references/gotchas.md`, "A Profile Retrieve Returns Only What the Rest of the Manifest Asked For")
3. **Write the pair** — the base profile and the receiving permission set, from the shapes in `references/metadata-examples.md`. Map `tabVisibilities`→`tabSettings` and drop every `<default>` from the permission-set side; leave the `default` app and record type on the profile
4. **Check the licence pairing** — `SELECT Id, Profile.UserLicenseId FROM User` against `SELECT Id, LicenseId FROM PermissionSet`. A mismatch blocks the assignment, so resolve it before the cutover rather than during it
5. **Lint the files** — `python3 skills/admin/permission-sets-vs-profiles/scripts/check_access_model.py --manifest-dir force-app/main/default`. It flags migratable grants still sitting on a profile, profile-only elements wrongly placed in a permission set, edits to `custom=false` profiles, object permissions duplicated across a profile and a group member, and an over-length `description` (`PSVP-DESC-01` ERROR at 255+ characters, `PSVP-DESC-02` INFO headroom at 200+). Exit policy: exit 1 only on a dangerous-permission grant, a migratable grant left on a profile, a profile-only element in a permission set, or `PSVP-DESC-01` (255+ characters) — all CRITICAL/ERROR/HIGH-class findings; a standard-profile edit, a duplicate grant, or an empty scan print as WARN/INFO and exit 0, and `--strict` promotes those to a failure. `PSVP-DESC-02` is a separate advisory bucket — always printed and counted, never promoted even by `--strict`. A missing `--manifest-dir` is a usage error and exits 1 immediately.
6. **Deploy in order, permission set first** — validate-only, then permission set, then group, then the stripped profile. Reversing the order leaves a window with no access; and because profile deploy *overlays*, any permission you mean to revoke must be written out explicitly as `false`
7. **Verify against the org, not the deploy log** — run the `IsOwnedByProfile` and assignment-count SOQL in `references/metadata-examples.md` § Verify, and open Setup → Users → the migrated user → **View Summary** to confirm effective access matches the pre-migration baseline

For a full org-scale decomposition of a live profile — inventory, category classification, reuse scoring, PSG composition and a phased cutover — hand off to `agents/profile-to-permset-migrator/AGENT.md` (`/migrate-profile-to-permset`). This skill owns the decision; that agent owns the mechanics.

---

## Salesforce-Specific Gotchas

- **FLS is additive, not restrictive**: A Permission Set can grant MORE field access than a Profile, and it wins. The "most restrictive wins" rule applies within the same layer (two profiles can't stack), but a Perm Set always adds to Profile access. A user with Profile FLS=Read + Perm Set FLS=Edit has Edit. This surprises people who expect Profiles to cap access.
- **Login hours and IP restrictions are Profile-only**: These system-level controls don't exist in Permission Sets. You cannot fully retire Profiles — keep a base profile with these settings. Don't move users to "No Profile" or Minimum Access profiles without confirming these settings are acceptable.
- **Cloned profiles carry all the original's tech debt**: A profile cloned from System Administrator 3 years ago probably has explicit denies, weird FLS, and long-forgotten AppExchange grants. Audit before using clones as a base — they're not clean slates.
- **Permission Set Group propagation delay**: Changes to a PSG take up to 10 minutes to propagate (UNVERIFIED 2026-09-04: the figure is not stated in the Metadata API guide or Object Reference; treat as an observed delay, not a documented limit) to assigned users. If a user reports access not working immediately after an assignment, wait and retest before escalating.
- **Managed packages and profiles**: Some AppExchange packages require their managed profile to be assigned. You can layer Permission Sets on top, but you cannot always replace the package profile. Document this as an exception.
- **A profile's permissions are not stored on the Profile object**: since API 25.0 they live in a `PermissionSet` row flagged `IsOwnedByProfile = true`. Query `ObjectPermissions` with `WHERE Parent.IsOwnedByProfile = TRUE`, key on `ProfileId`, and treat those rows as read-only.
- **Profile metadata deploy overlays, it does not replace**: deleting a block from the XML revokes nothing. Write the permission out explicitly as `false` or the strip phase silently does nothing.
- **`description` over 255 characters fails the deploy; PSGs fail as a cascade**: both `Profile.description` and `PermissionSet.description` are capped at 255 characters, and a PSG that composes a rejected set fails too, with an unrelated-looking `permission set names are invalid`.

Deeper treatment of all fourteen, with the guide passages behind them, in `references/gotchas.md`.

## Proactive Triggers

Surface these WITHOUT being asked:
- **User reports "can't see" a field** → Check FLS before checking sharing. 80% of "missing field" issues are FLS, not sharing. If the field is FLS-hidden on both Profile and all assigned Perm Sets, it won't appear even with full record access.
- **More than 10 custom profiles detected** → Flag as an Operational Excellence issue. This is a profile sprawl signal. Begin audit: which profiles differ by fewer than 5 permissions? Those are merge candidates.
- **Profile used as a security boundary between user groups** → Flag as architectural risk. Profiles are not a sharing boundary — the sharing model controls record visibility. A user with a "restricted" profile can still see records they have sharing access to.
- **`ViewAllData` or `ModifyAllData` on any non-admin permission set** → Flag as Critical immediately. No justification is acceptable for community/portal users. Internal users require documented approval.
- **Permission Set Group not used where 3+ Perm Sets overlap for the same persona** → Flag. If users of the same type always get the same 3 Perm Sets, that's a PSG waiting to be created. Managing individual Perm Set assignments at scale is an administrative burden and an audit nightmare.
- **Perm Set with 50+ object permissions checked** → Flag. This is likely a copy of a legacy profile being ported into a Perm Set. It defeats the purpose of granular permission management.
- **`description` reads like a design note, not a label** → Flag before deploy. Over 255 characters fails outright (`Description: data value too large … (max length=255)`); over 200 is worth trimming now. Rationale belongs in `templates/permission-set-design-template.md` or `deploy-order.md`.

## Output Artifacts

| When you ask for...              | You get...                                                          |
|----------------------------------|---------------------------------------------------------------------|
| Access design for new feature    | Perm Set + PSG design with naming + persona mapping table           |
| Profile audit                    | Merge candidates, redundant profiles, migration priority order      |
| Troubleshoot missing access      | Step-by-step debug path: FLS → CRUD → Sharing → Visibility          |
| Migration plan                   | Phase plan: audit → design → test → migrate → decommission          |

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing the base profile and the receiving permission set — element-by-element split table, deployable XML for all three types, package.xml, retrieve/deploy commands, verification SOQL |
| `references/gotchas.md` | A deploy "worked" but nothing changed, a retrieve came back empty, an assignment was rejected, or a migrated user lost their app and layout |
| `references/examples.md` | Working a five-profile-to-three-PSG migration end to end, or picking audit SOQL for the current-state inventory |
| `references/well-architected.md` | Justifying the decomposition against Security and Operational Excellence now that the Spring '26 forcing function is gone, or citing the official sources |
| `references/llm-anti-patterns.md` | Self-checking generated output for profile cloning, a cancelled deadline, "revoke with a permission set", or a migration plan that ignores managed packages |
| `templates/permission-set-design-template.md` | Documenting the design for review — residue list, persona matrix, PS and PSG definitions, FLS audit, cutover plan |
| `scripts/check_access_model.py` | Linting profile and permission-set XML before a deploy |

---

## Related Skills

- **admin/permission-set-architecture**: Use for the architecture of the permission sets themselves — how many, what shape, how they are governed. This skill decides *what moves*; that one decides *what it moves into*.
- **admin/permission-set-group-composition**: Use for PSG layering, muting mechanics, recalculation status and deletion order. NOT for the profile-vs-permission-set decision.
- **security/permission-set-groups-and-muting**: Use when the design needs subtraction — a muting permission set removes a permission only inside its group, never from a permission set the user also holds directly.
- **admin/custom-permissions**: Use when a profile carried a feature toggle that should become a `$Permission` gate rather than one permission set per flag.
- **admin/sharing-and-visibility**: Use when the permission in question is `View All` / `Modify All` — those are record-access grants, and moving them into a permission set carries forward an access path the OWD was written to prevent.
- **apex/apex-stripinaccessible-and-fls-enforcement**: Use when the issue is Apex-side CRUD/FLS enforcement (`WITH USER_MODE`, `as user` DML, `Security.stripInaccessible(AccessType, records).getRecords()`; also legacy `WITH SECURITY_ENFORCED`, which no longer compiles at class `apiVersion` 67.0+ and is tech debt at 57.0–66.0 — the gate is the `.cls-meta.xml` version, not the org's release). NOT for declarative permission architecture.
- **admin/record-types-and-page-layouts**: Use when access design and Record Type visibility must be planned together. NOT when the main problem is page UX rather than user access.
- **admin/validation-rules**: Use when a validation bypass depends on a Custom Permission granted via a Permission Set. NOT for debugging sharing, CRUD, or profile sprawl.
