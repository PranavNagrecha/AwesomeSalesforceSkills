---
name: permission-set-group-composition
description: "Tactical guidance for composing Permission Set Groups: layering permission sets, applying Mute Permission Sets to subtract narrow capabilities, sequencing the recalculation lifecycle, deletion order, and assignment-vs-activation lifecycle. Triggers: 'PSG composition', 'mute permission set', 'PSG recalculation', 'cannot delete permission set in PSG', 'PSG explosion', 'expired PSG assignment'. NOT for the strategic question of profile-vs-PSG architecture (see admin/permission-set-architecture). NOT for record-sharing or CRUD/FLS in Apex."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
tags:
  - permission-set-groups
  - muting-permission-sets
  - psg-composition
  - psg-recalculation
  - assignment-lifecycle
  - access-governance
triggers:
  - "how do I subtract a permission from a permission set group without cloning the group"
  - "permission set group recalculation is stuck or stale"
  - "cannot delete permission set because it is in a permission set group"
  - "manager persona needs everything sales has but not delete on opportunity"
  - "expiration date on permission set group assignment"
  - "PSG explosion fifty permission set groups overlapping"
  - "PSG naming convention environment persona"
inputs:
  - "Existing PSG inventory and the permission sets each PSG includes"
  - "Target persona and the delta between persona and the closest existing PSG"
  - "Whether muting is needed (one-way subtract) vs a smaller composable PS"
  - "User license attached to the persona and the PSes that depend on a feature license"
  - "Deployment context — sandbox vs prod, source-tracked vs change-set"
outputs:
  - "PSG composition plan listing included PSes, mute PS (if any), and rationale"
  - "Recalculation and rollout sequence for changes to a high-fan-out PSG"
  - "Deletion sequence for retiring a PS that is referenced by one or more PSGs"
  - "Naming-convention check report and consolidation candidates"
  - "Assignment lifecycle plan covering expiration, activation, and audit trail"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Permission Set Group Composition

Activate this skill when the strategic decision to use Permission Set Groups is already made and the question is now tactical: which permission sets go into which PSG, when to add a Mute Permission Set, in what order to delete a PS that is wired into 50 PSGs, why a freshly assigned PSG still does not show its effective access, and how to keep PSG count from exploding. This is the operating manual that lives one floor down from `admin/permission-set-architecture` — that skill picks the access model, this skill makes the model survive contact with production.

This is NOT the place to argue PSG vs profile-stack — see `admin/permission-set-architecture` for the strategic case. This is also NOT for record-visibility design — sharing rules, OWD, and role hierarchy are out of scope.

## Before Starting

- How many PSGs already exist, and how many of them share at least one permission set? Heavy overlap is the signal for the "PSG explosion" anti-pattern this skill prevents.
- Is the desired delta from an existing PSG **subtractive** (mute) or **additive** (a new small PS)? Mute Permission Sets only ever subtract — they cannot grant.
- What user licenses are attached to the target personas, and do any included PSes require a feature license that the target user does not have?
- Is the org source-tracked (DX/Source) or change-set based? Mute Permission Sets are separate metadata files and must be retrieved explicitly — they do not travel inside the `permissionsetgroup-meta.xml` file.

## Core Concepts

### Composition Is A Union, Mute Is A One-Way Subtract

A Permission Set Group's effective access is the **union** of every permission granted by every included permission set, minus anything subtracted by an attached Mute Permission Set. The grant-side is symmetric (any included PS can grant a permission and the user gets it) but the mute-side is **not** symmetric — once a permission is muted on the PSG, no other included PS in the same PSG can grant it back. Grant-wins inside a PSG only applies between included PSes; mute always wins over included grants.

This asymmetry is the single most-misunderstood fact about PSGs. "Mute X then re-grant X via another PS in the same PSG" does not work — the user still does not get X.

### The Recalculation Lifecycle Is Asynchronous

When a permission set that lives in N PSGs changes, every one of those PSGs enters a **recalculation** state. During recalculation the PSG status shows "Updating" and the effective access is whatever was calculated last — a freshly assigned user can wait for access while the PSG completes its recalc. Recalc time scales with PSG count, included PS count, and assignee count. Plan rollouts so PS edits land in a quiet window, not at the start of a release where downstream agents will hit stale access.

`Status` on the PSG metadata reports the result: `Updated` (good), `Outdated` (recalc not started), `Updating` (recalc running), `Failed` (recalc could not complete). Until status is `Updated`, do not assume new permissions are live.

### Assignment Is Distinct From Activation

A PSG is **activated** by Salesforce after recalculation completes. A PSG is **assigned** to a user via `PermissionSetAssignment` (yes — the same SObject that holds permission-set assignments; `PermissionSetGroupId` is set instead of `PermissionSetId`). A user can be assigned to a PSG that is still `Outdated`; they will not see effective access until the PSG flips to `Updated`. Conversely, deactivating or deleting a PSG without first removing assignments is blocked.

### Expiration On PSG Assignments

Since Spring '23 Salesforce supports `ExpirationDate` on Permission Set Group assignments — the same way it has supported expiration on Permission Set assignments. This is the right primitive for time-boxed elevation (contractor access, quarterly approver rights). Do not invent a Flow that "removes the PSG at midnight" — set the expiration and let the platform expire it automatically.

### Deletion Order: Detach, Wait, Delete

You cannot delete a permission set that is still referenced by a PSG. The supported sequence is:

1. Remove the PS from every PSG that includes it.
2. Wait for every affected PSG to finish recalculation (`Status = Updated`).
3. Delete the PS.

Skipping step 2 risks a delete that fails mid-deployment because the recalc had not yet released the dependency. Tooling that runs `delete` immediately after `update` on a PSG often hits this — add an explicit wait or split the deployment.

## Common Patterns

### Sales-Rep-With-Manager-Mute Pattern

**When to use:** A manager persona needs everything a sales rep has, except one or two narrow permissions (classic example: "Manager has Sales but NOT Delete on Opportunity" — managers should not bulk-delete pipeline data).

**How it works:** Build one `PSG_SalesRep_Prod` that includes the small composable PSes (`PS_OpportunityRead`, `PS_OpportunityCreate`, etc.). Build one Mute Permission Set `MutePS_NoOpportunityDelete` that subtracts `Delete` on `Opportunity`. Build `PSG_SalesManager_Prod` that includes the same sales PSes **plus** the mute PS. Two PSGs, one set of underlying PSes, one mute. No cloning.

**Why not the alternative:** Cloning `PSG_SalesRep_Prod` to `PSG_SalesManager_Prod` and editing one permission means every future change to the rep bundle has to be re-applied to the manager bundle. Drift starts the day the clone happens.

### Small Composable PSes Over Mega-PSes

**When to use:** Whenever a PS is starting to grow past ~30 object-permission grants or covers more than one "capability."

**How it works:** Split into `PS_<feature>_Read`, `PS_<feature>_Edit`, `PS_<feature>_Delete` and let PSGs compose them. The PSG carries the persona shape; PSes carry the feature shape.

**Why not the alternative:** A single `PS_Sales_Everything` PS forces every persona that wants any of it to get all of it, which forces a mute for every exclusion, which inflates mute count and hides intent.

### Time-Boxed Elevation

**When to use:** A user needs temporary elevated access (contractor, on-call rotation, audit support).

**How it works:** Assign the existing PSG with an `ExpirationDate` set on the `PermissionSetAssignment` row. Salesforce expires the assignment automatically; Setup Audit Trail records the expiration.

**Why not the alternative:** A custom Flow that deletes the assignment introduces a moving part that can fail silently. The platform-native expiration is auditable and does not depend on scheduled job health.

### Deletion-Order Dance For Retiring A PS

**When to use:** A permission set is referenced by N PSGs and needs to go away.

**How it works:**

1. Retrieve every PSG that lists the PS in `permissionSets`.
2. Update each PSG to remove the reference (one deployment).
3. Poll PSG `Status` until every affected PSG reports `Updated`.
4. Deploy the PS deletion.

**Why not the alternative:** A single deployment that updates the PSGs and deletes the PS in the same transaction will fail because the recalc has not yet released the FK-style reference.

## Decision Guidance

Use this when the request is "I need persona Y who is mostly like persona X except…":

| Situation | Recommended Approach | Reason |
|---|---|---|
| Persona Y needs **less** than the closest PSG (a permission must NOT be granted) | Add a **Mute Permission Set** to a new PSG variant | Subtractive delta is exactly what mute is for; no PS duplication |
| Persona Y needs **more** than the closest PSG (a new capability) | Build a **new small composable PS** and add it to the PSG | Mute cannot grant — additive deltas need a real PS |
| Persona Y needs a different **combination** of existing PSes | Build a **new PSG** referencing the existing PSes | PSGs are cheap; PSes are the reusable unit |
| Persona Y is a one-off (single user, ≤30 days) | Direct PS or PSG assignment with `ExpirationDate` | Don't distort the architecture for a temporary need |
| Existing PSG is "almost right" for many personas | Refactor — split the mega-PS into composable PSes | A PSG that needs muting for every persona is signalling its underlying PSes are too coarse |
| The same PS appears in 5+ PSGs | Likely fine — that is reuse working | Reuse of small PSes across PSGs is the goal, not a smell |
| The same permission appears granted in multiple PSes inside the same PSG | Consolidate the duplicates into one PS | Hidden duplication makes future muting harder to reason about |

## Recommended Workflow

1. **Inventory existing PSGs.** Run `scripts/check_permission_set_group_composition.py` against the `permissionsetgroups/` and `permissionsets/` directories — capture which PSes are referenced in multiple PSGs (good — reuse), which PSGs have zero included PSes (orphan), which PSGs use mute PSes (good — explicit subtract), and which names violate the convention.
2. **Identify the closest existing PSG.** Compare the target persona to existing PSGs and decide: subtractive delta (mute), additive delta (new PS), or different combination (new PSG).
3. **Apply the Decision Guidance table.** Choose mute, new PS, or new PSG based on the row that matches the request. Avoid cloning; cloning is the explosion vector.
4. **Compose the PSG.** Use the template at `templates/permission-set-group-composition-template.md`. Fill persona name, included PSes, mute PS (if any), license dependency, and lifecycle stage (draft / piloted / production).
5. **Plan recalculation.** If a frequently-referenced PS is being touched, list every PSG that will recalc. Schedule the change for a quiet window. Do not pair a PS edit with a PS deletion in the same deployment.
6. **Roll out with assignment-vs-activation in mind.** Wait for `Status = Updated` before assigning users. For time-boxed elevation, set `ExpirationDate` on the assignment.
7. **Verify and audit.** Confirm Setup Audit Trail captured the composition change, run the checker again, and update the inventory artifact.

## Review Checklist

- [ ] No PSG was cloned to make a small variant — mute PS used instead for subtractive deltas.
- [ ] No mute-then-re-grant pattern inside the same PSG (mute always wins).
- [ ] Naming follows `PSG_<persona>_<env>` and `MutePS_<scope>_<delta>`.
- [ ] Every PSG `Status` is `Updated` before users are assigned to it.
- [ ] Permission set deletion sequenced as detach → wait for recalc → delete.
- [ ] Time-boxed assignments use `ExpirationDate`, not custom Flows.
- [ ] Each included PS appears in ≥2 PSGs OR is documented as persona-specific.
- [ ] Mute Permission Sets retrieved as separate metadata in source-tracked deployments.
- [ ] Setup Audit Trail change reviewed for the rollout.

## Salesforce-Specific Gotchas

1. **Mute is one-way subtract — grant inside the same PSG cannot beat it.** A user with a muted permission stays muted even if another included PS grants it. Architecture diagrams that show "PS_A grants Delete, MutePS subtracts Delete, PS_B grants Delete → user gets Delete" are wrong.
2. **Recalculation is asynchronous and can fail.** Until `Status = Updated`, assigned users do not see new effective access; if status is `Failed`, the cause must be diagnosed (most often a deleted PS reference or a license incompatibility).
3. **You cannot delete a PS while any PSG still references it.** Salesforce returns a delete error; the fix is the detach → wait → delete sequence.
4. **Mute Permission Sets are separate metadata.** A change set or `package.xml` retrieve that pulls only `PermissionSetGroup` will not bring the mutes — they require an explicit `MutingPermissionSet` (Metadata API type) entry.
5. **License mismatch on an included PS silently breaks the PSG for some users.** A PSG that includes a PS scoped to "Salesforce" license cannot grant those permissions to a user on the "Platform" license — the PSG is valid, but the effective access for that user is reduced without warning.

## Output Artifacts

| Artifact | Description |
|---|---|
| Composition plan | Persona, included PSes, mute PS, license dependency, lifecycle stage (uses the template) |
| Recalculation rollout sequence | Ordered list of PSGs that will recalc when a referenced PS changes, with a quiet-window recommendation |
| Deletion plan | Detach → wait → delete sequence for retiring a PS that is referenced by one or more PSGs |
| Composition checker report | Output of `scripts/check_permission_set_group_composition.py` flagging multi-PSG PSes, mute usage, orphans, and naming-convention violations |

## Related Skills

- `admin/permission-set-architecture` — strategic counterpart: profile-vs-PS-vs-PSG architecture and migration off profile-centric access. Read it first if the request is "should we even be using PSGs."
- `security/permission-set-groups-and-muting` — security-pillar framing for the same domain; reach for it during security review.
- `admin/permission-sets-vs-profiles` — admin-level distinction between PSes and profiles; useful when the request is about the assignment basics rather than composition tactics.
- `devops/source-tracked-metadata-retrieve` — when the deployment context surfaces the Mute Permission Set retrieval gotcha.
