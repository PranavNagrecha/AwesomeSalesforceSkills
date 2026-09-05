---
name: permission-set-architecture
description: "Use when designing or refactoring Salesforce access architecture around minimal profiles, permission sets, permission set groups, muting, and assignment governance. Triggers: 'profile sprawl', 'permission set strategy', 'PSG architecture', 'access bundle design', 'least privilege', 'how to slice permission sets', 'permission set naming convention', 'permission set license restriction', 'PSG status Outdated', 'permissionset-meta.xml'. NOT for PSG muting mechanics and recalculation order — use admin/permission-set-group-composition. NOT for record-sharing model design — use admin/sharing-and-visibility. NOT for time-boxing an assignment — use admin/permission-set-expiration."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
  - Reliability
tags:
  - permission-set-architecture
  - least-privilege
  - permission-set-groups
  - profiles
  - access-governance
triggers:
  - "too many custom profiles to manage safely"
  - "how should I slice permission sets by object, function, and persona"
  - "profile sprawl is making access changes risky"
  - "user has the permission set but still cannot see the field"
  - "permission set group status is stuck on Outdated after a deploy"
  - "cannot assign this permission set because of the user license"
  - "find which permission set granted this user Modify All Data"
  - "deploy permission sets and permission set groups from sandbox to production"
  - "need a least privilege access bundle model"
  - "permission set group strategy for multiple personas"
inputs:
  - "current profile, permission-set, and permission-set-group inventory"
  - "target personas, feature bundles, and license constraints"
  - "the entitlement list per persona: objects, fields, tabs, apps, Apex, flows, custom permissions"
  - "assignment process such as manual admin work, Flow, or identity provisioning"
outputs:
  - "access architecture recommendation"
  - "deployable permissionsets/, permissionsetgroups/, and mutingpermissionsets/ metadata"
  - "review findings for profile-heavy or inconsistent access models"
  - "migration plan from profile-centric access to governed bundles"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

Use this skill when the problem is no longer "which permission do I grant" and has become "how should the org structure access so future changes stay safe?" The goal is to produce a layered access model that supports least privilege, lowers operational risk, and makes persona-based changes predictable.

## Before Starting

- Which user licenses are in scope, and do those licenses restrict which permissions can even be granted?
- How many custom profiles, permission sets, and permission set groups already exist, and which of them are genuinely assigned?
- Is the pain coming from feature access composition, one-off exceptions, or a sharing model problem that permission architecture cannot solve?

## Questions to Ask Before Configuring

Answer these before the first `.permissionset-meta.xml` is written. Each one maps to a platform behaviour documented in `references/gotchas.md`; skipping them produces a bundle that deploys cleanly and grants the wrong thing.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which user or permission set license does every person in this persona hold?" | The `license` element pins a permission set to one license; a mixed-license persona needs it left empty | One bundle family per license boundary, or a deliberate empty `license` recorded as a choice |
| "Which objects does this capability touch, and at what CRUD level?" | Object permissions have a dependency chain (`allowEdit` needs read, `allowDelete` needs read + edit), and field permissions cannot exceed the object grant | The object-access slice, sized before any FLS is written |
| "Does anything here need View All Records or Modify All Records?" | Those bypass sharing per object; `modifyAllRecords` additionally requires read, edit, delete, and `viewAllRecords` | A decision to isolate the override in its own set that is never composed into a persona |
| "Is this bundle for a named person or for a standing role that changes people?" | The PSG is the reviewable assignment unit; a per-person pile of sets has no name to attest against | The persona → PSG map, plus the owner of each PSG |
| "Should any of this expire?" | `PermissionSetAssignment.ExpirationDate` (API 52.0+) time-boxes elevation instead of leaving it to drift | A time-limited set handed to `admin/permission-set-expiration` rather than a permanent grant |
| "Does any permission need step-up activation?" | `hasActivationRequired` survives standalone assignment but not group membership | Session-based sets kept out of persona PSGs on purpose |
| "Who checks the group after deploy, and against which user?" | PSG recalculation is a state machine, not a synchronous write; effective access lags the metadata | A post-deploy `PermissionSetGroup.Status` poll and a real-user verification step |

What a proper configuration adds over just doing it: every grant traces to one capability set, the license boundary is a design input instead of a deploy error, sharing-bypass permissions are visible in one place, and the persona bundle can be re-attested a year later without re-deriving it from user records.

## Core Concepts

### Profiles Are The Base Layer, Not The Whole Architecture

Profiles still matter for baseline settings such as login hours, page layout assignment, and a minimal set of app access, but they should not carry every feature permission for every job role. When profiles become job-title snapshots, every change request turns into profile cloning, regression risk, and audit noise.

Note that `ObjectPermissions` and `FieldPermissions` records are children of `PermissionSet`, not of `Profile` — the Object Reference states this for both objects. Every profile is itself backed by a permission set (`PermissionSet.IsOwnedByProfile = true`), which is why a profile-vs-permission-set audit can be written as one SOQL query over `PermissionSet`.

### Permission Sets Should Model Capabilities

Permission sets work best when they describe a coherent capability such as "Case Console Core", "Refund Approval", or "Quote Generation". They become difficult to govern when they are named after people, projects, or emergency exceptions. Capability-based design is what makes bundle reuse possible.

The canonical slicing taxonomy — App / Object / Feature / Setup / Session-Based / Time-Limited, with naming patterns for each — lives in `templates/admin/permission-set-patterns.md`. Map every requested entitlement to exactly one of those categories before writing XML; do not re-derive a taxonomy per project.

### Permission Set Groups Are The Assignment Unit

A user should rarely receive a large pile of unrelated permission sets one by one. Permission Set Groups let the architecture describe a persona or bundle as a unit. That makes onboarding, change review, and attestation easier because the assignment object has meaning.

`PermissionSetAssignment` carries either `PermissionSetId` or `PermissionSetGroupId` (the group field is API 45.0+), so the same assignment object serves both — a governance report can count how many assignments are to a named persona group versus loose sets.

### Muting And Exceptions Need Governance

Muting is useful when a shared bundle is almost right but slightly too broad. It is not a substitute for coherent bundle design. A good architecture limits subtractive exceptions and documents who owns them, because muted access can drift away from the intent of the base bundle if nobody reviews it.

A `MutingPermissionSet` has the same fields as `PermissionSet` plus `label`, but the Metadata API guide inverts the meaning: settings *enabled* in a muting permission set are *turned off* for the group it belongs to. A muting set that lists a permission no member set grants is dead weight, and reads to a future admin as if it were granting something.

### The Deployable Shapes

| Type | package.xml `<name>` | File in a DX project | API |
|---|---|---|---|
| Permission set | `PermissionSet` (wildcard `*` allowed) | `permissionsets/Obj_Case_Full.permissionset-meta.xml` | 22.0+ |
| Permission set group | `PermissionSetGroup` (wildcard `*` allowed) | `permissionsetgroups/Persona_Service_Agent.permissionsetgroup-meta.xml` | 45.0+ |
| Muting permission set | `MutingPermissionSet` | `mutingpermissionsets/Mute_Tier1_Refunds.mutingpermissionset-meta.xml` | 46.0+ |

Deployable examples of all three, plus `package.xml`, retrieve/deploy commands, assignment, and verification SOQL, are in `references/metadata-examples.md`.

## Common Patterns

### Baseline Plus Feature Bundles

**When to use:** Multiple business personas share a common baseline but need different feature combinations.

**How it works:** Keep profiles thin, create focused permission sets per capability, then compose job-specific bundles through permission set groups. Use naming that exposes scope and ownership.

**Why not the alternative:** One profile per persona mixes baseline setup and feature entitlements into one brittle object. Every new feature becomes a profile-change project.

### Shared Bundle With Controlled Muting

**When to use:** Several personas need the same large bundle except for a few permissions that one persona must not receive.

**How it works:** Build one reusable PSG, apply muting only for the delta, and track the business reason for the muted variant.

**Why not the alternative:** Cloning nearly identical groups or permission sets multiplies maintenance and makes audits harder.

### Migration Off Profile-Centric Access

**When to use:** The org already has many custom profiles and access changes are slow or unsafe.

**How it works:** Identify common permissions in profiles, move feature access to permission sets, introduce PSGs for recurring personas, and leave profiles as thinner baselines over time.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| One capability must be granted to many personas | Permission Set | Capability-level reuse is cleaner than editing many profiles |
| A recurring job role needs several capability bundles together | Permission Set Group | PSGs are the right assignment and review unit |
| One persona needs slightly less than the shared bundle | Muting Permission Set in a PSG | Subtractive exception is clearer than cloning the whole bundle |
| The persona spans Salesforce and Platform licenses | Two license-scoped set families, `license` left empty on shared sets | `license` pins a set to one license and blocks assignment to the rest |
| A capability needs step-up authentication before use | Standalone session-based set, assigned directly | Group membership removes the session-activation requirement |
| Users see the right permissions but the wrong records | Use sharing-model skills instead | Permission architecture does not solve record visibility |
| A request is truly one-off and temporary | Time-boxed permission set assignment | Avoid distorting the core architecture for an exception |

## Recommended Workflow

1. Slice the entitlement list — map every requested permission to exactly one category in `templates/admin/permission-set-patterns.md` (App / Object / Feature / Setup / Session-Based / Time-Limited). One concern per permission set; a set that needs "and" in its name is two sets.
2. Draw the license boundaries — group the slices into families per user or permission set license, and decide per set whether `license` is populated or deliberately empty. A shared set assigned across Salesforce and Platform users must leave it empty.
3. Write object access before field access — `objectPermissions` first, honouring the dependency chain, then `fieldPermissions` only for fields the object grant can carry. Shapes and the full element list are in `references/metadata-examples.md`.
4. Compose the personas — one PSG per persona listing its `permissionSets`; add a `mutingPermissionSets` entry only for a delta that splitting a set cannot express, and record the business reason in the muting set's `description`.
5. Check the tree — `python3 skills/admin/permission-set-architecture/scripts/check_permission_set_architecture.py --manifest-dir force-app/main/default`. It flags edit-without-read FLS, sharing-bypass grants, oversized sets, dangling PSG members, session sets inside groups, and no-op muting entries.
6. Deploy in order and wait for recalculation — permission sets before groups before muting; then poll `PermissionSetGroup.Status` until it reads `Updated` (see `references/metadata-examples.md`). A `Failed` status is silent in the deploy result.
7. Verify against a real user — run the `PermissionSetAssignment` and `ObjectPermissions` verification queries in `references/metadata-examples.md` for one member of each persona, then record the persona-to-bundle matrix in `templates/permission-set-architecture-template.md`.

---

## Review Checklist

- [ ] Profiles are being minimized instead of expanded for every new feature.
- [ ] Permission sets have clear capability-based names drawn from the shared taxonomy, plus a named owner.
- [ ] Recurring access bundles are represented as PSGs rather than manual piles of assignments.
- [ ] Every set's `license` is populated or empty by decision, and the decision is written down.
- [ ] No `fieldPermissions` entry has `editable` true with `readable` false, and no field is granted beyond its object grant.
- [ ] `viewAllRecords` / `modifyAllRecords` appear only in a named override set that is not composed into a persona PSG.
- [ ] Muting is rare, intentional, documented, and every muted permission is actually granted by a member set.
- [ ] Session-based sets are assigned directly, not through a PSG.
- [ ] Every PSG reached `Updated` status after deploy and effective access was confirmed with a real user.
- [ ] The architecture distinguishes feature entitlements from record-sharing decisions.

## Salesforce-Specific Gotchas

1. **Permission Set Group recalculation is a state machine, not a synchronous write** — `Status` moves through `Updated`, `Outdated`, `Updating`, and `Failed`, so a rollout plan must poll it rather than assume the deploy result is the whole story.
2. **License fit matters before architecture elegance** — a permission set with `license` populated can only be held by users on that license, so a clean bundle model still fails if it ignores license boundaries.
3. **Muting only subtracts from grouped permissions** — it never grants access and it cannot fix a poor base design that should have been split into smaller capabilities.
4. **Apex class, tab, app, and object access often drift separately** — teams sometimes move object permissions into permission sets but forget Apex class access and UI entry points, creating half-migrated bundles.
5. **A session-based set loses its step-up requirement inside a group** — the Object Reference is explicit that permissions in session-based sets included in a PSG no longer require session activation.

Deeper treatment, each with the platform behaviour behind it, in `references/gotchas.md`.

## Output Artifacts

| Artifact | Description |
|---|---|
| `permissionsets/*.permissionset-meta.xml` | Capability-sliced sets, each mapped to one taxonomy category |
| `permissionsetgroups/*.permissionsetgroup-meta.xml` | One per persona, listing `permissionSets` and any `mutingPermissionSets` |
| `mutingpermissionsets/*.mutingpermissionset-meta.xml` | Documented subtractive deltas only |
| Access architecture review | Findings on profile sprawl, bundle reuse, muting overuse, and governance gaps |
| Persona-to-bundle matrix | Recommended baseline profile, permission sets, and PSGs per persona |
| Migration backlog | Sequenced changes for moving from profile-heavy access to governed bundles |

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing the XML: object set, function set, persona PSG, muting set, package.xml, retrieve/deploy, assignment, verification SOQL |
| `references/gotchas.md` | A bundle deployed cleanly but grants or hides the wrong thing |
| `references/examples.md` | Sizing a persona model against a worked sales/service example, or naming an anti-pattern you already have |
| `references/well-architected.md` | Justifying the design in a review, or citing the official sources behind a claim |
| `references/llm-anti-patterns.md` | Reviewing permission-set output an assistant generated |

## Related Skills

- admin/permission-sets-vs-profiles — the prior decision: whether a grant belongs on a profile or a permission set at all.
- admin/permission-set-group-composition — PSG layering mechanics, recalculation sequencing, and deletion order.
- security/permission-set-groups-and-muting — muting strategy and the security review of a group-based model.
- admin/permission-set-expiration — time-boxing an assignment with `ExpirationDate` instead of a standing grant.
- admin/custom-permissions — creating the custom permissions that a Feature-category set carries.
- admin/sharing-and-visibility — when the real issue is record access, OWD, roles, or sharing rules.
