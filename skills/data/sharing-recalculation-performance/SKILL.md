---
name: sharing-recalculation-performance
description: "Plan, batch, and monitor Salesforce sharing recalculation jobs — including OWD changes, sharing rule add/remove, role hierarchy restructuring, and Apex managed share rebuild — to avoid multi-hour background jobs and data-access blackouts. NOT for diagnosing data-skew root causes (use admin/data-skew-and-sharing-performance), NOT for designing the sharing model itself (use admin/sharing-and-visibility), and NOT for Apex managed sharing row-cause creation (use apex/apex-managed-sharing)."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
  - Security
triggers:
  - "OWD change is taking hours or running overnight and not finishing"
  - "sharing recalculation job still running after several hours on a large org"
  - "how do I use Defer Sharing Calculations before changing org-wide defaults"
  - "Apex managed sharing rows disappeared after sharing recalculation ran"
  - "role hierarchy restructuring caused long-running background sharing job"
  - "how to batch OWD changes and group updates to minimize recalculation time"
  - "criteria-based sharing rule is slow when target field is mass-updated"
  - "sharing recalculation isn't working"
  - "we're having issues with sharing recalculation"
tags:
  - sharing-recalculation
  - defer-sharing-calculations
  - owd-change
  - sharing-rules
  - apex-sharing
  - large-data-volumes
  - maintenance-window
inputs:
  - "Object(s) being changed: API name, approximate record count, current OWD"
  - "Type of change: OWD tightening/relaxing, sharing rule add/remove, role hierarchy edit, group membership change"
  - "Whether Apex managed sharing is in use on any affected object"
  - "Maintenance window availability and current async job queue depth"
outputs:
  - "Staged change plan using Defer Sharing Calculations to batch structural changes into one recalculation job"
  - "Risk assessment for OWD tightening versus relaxing on the affected object"
  - "Checklist for verifying Apex managed share rebuild class is registered and will re-run"
  - "Monitoring guidance for Setup Audit Trail and async job queue"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Sharing Recalculation Performance

Use this skill when a Salesforce administrator or architect needs to plan or recover from a long-running sharing recalculation job — triggered by OWD changes, sharing rule modifications, role hierarchy restructuring, or group membership edits. This skill covers the Defer Sharing Calculations mechanism, OWD change cost estimation, Apex managed share rebuild requirements, and safe sequencing of structural sharing changes.

---

## Before Starting

Gather this context before working on anything in this domain:

- Identify the exact type of change being made: OWD change (direction matters — tightening is far more expensive than relaxing), sharing rule add/remove, role hierarchy edit, or public group restructuring.
- Know the approximate record count on each affected object. For objects with millions of records and Private or Read-Only OWD, any structural change will produce a long-running background job.
- Confirm whether any affected object uses Apex managed sharing (custom `RowCause` on the share object). If so, associate a `Database.Batchable` recalculation class with the object: it is executed every time the OWD changes (apexdev 264 L13071-13072) and is how Apex managed sharing is recalculated (apexdev 264 L13053-13055). UNVERIFIED (2026-10-20): that without one "Apex grants are silently dropped on full recalculation and never rebuilt" is Help-level; the guide says only that recalculation "adds managed sharing when appropriate" and removes sharing whose access is redundant (apexdev 264 L13049-13052).
- Check Setup > Background Jobs for sharing recalculations already running (secguide 262 L3541-3542; you can't change OWD while a sharing rule recalculation runs, L3585-3586) and Apex Jobs for Apex work. A full recalculation job will compete with other background Apex and sharing jobs.
- Determine whether a maintenance window is available. OWD tightening on objects with millions of records should never be done during business hours (UNVERIFIED (2026-10-20): the record-count thresholds used in this skill, such as 100K and 500K, are rules of thumb, not documented limits).

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Which structural changes are planned, and can they land in one window? | Gotcha 2 and Pattern 1: deferral suspends group membership and sharing rule calculation (ldv 264 L598-599) | One staged change plan instead of N separate recalculations |
| Which objects use Apex managed sharing, and is a recalculation class associated with each? | Gotcha 1: the class is executed on every OWD change (apexdev 264 L13071-13072) | A per-object class name and the association path (Apex Sharing Recalculations) |
| Is the object custom or standard, and what API version is the sharing reason? | Gotcha 1: sharing reasons for standard objects need API 68.0 (api_meta 264 L47650-47651), older text says custom only (apexdev 264 L12613) | Whether Example 2 on Opportunity is even available |
| What is the OWD direction and record count on each object? | Gotcha 3: tightening cost and duration are UNVERIFIED rules of thumb | A maintenance-window decision grounded in your own job history |
| Which criteria-based rules reference fields that integrations update in bulk? | Gotcha 4: the per-DML re-evaluation claim is UNVERIFIED | A list of rules to review, not a proven cost |
| How deep is public-group nesting for groups used as rule sources? | Gotcha 5: the non-linear cost claim is UNVERIFIED | A flatten-or-keep decision |
| Who else deploys or edits sharing during the window? | Gotcha 2: deferral applies to sharing processing org-wide (scope claim UNVERIFIED) | A change freeze and an Audit Trail review step |

A proper configuration adds one staged change plan, a named recalculation class per Apex-shared object, and a verification log, instead of making changes one at a time and watching the queue.

---

## Core Concepts

### Defer Sharing Calculations

Defer sharing calculation is a permission, not a checkbox: "An organization's administrator can use a defer sharing calculation permission to suspend and resume sharing calculations, and to manage two processes: group membership calculation and sharing rule calculation" (salesforce_large_data_volumes_bp 264 L595-599). The guide's stated use is to suspend these "when performing a large number of configuration changes, which might lead to very long sharing rule evaluations or timeouts" and resume them during a maintenance period (L599-602). UNVERIFIED (2026-10-20): the "Setup > Defer Sharing Calculations" checkbox label, deferral of OWD and role hierarchy edits (the guide names only group membership and sharing rule calculation) are not in the corpus. The claim that clearing it "collapses all queued events into a single background job" is contradicted: after deferral "you must resume sharing rule calculations and manually initiate a full sharing rule recalculation" (secguide 262 L3533-3534).

**Why this matters:** Without deferral, each individual structural change — enabling a sharing rule, adding a role, updating a group — triggers its own recalculation: "Sharing rule recalculation occurs automatically after adding or removing individual users from a group, role, or territory, changing which role a particular role reports to ... or adding or removing a group from within another group" (secguide 262 L3520-3522). Deferring lets you pay for one full recalculation at the end. (UNVERIFIED (2026-10-20): the ten-times cost arithmetic is not in the corpus; the guide's grounded advice for loads is to add sharing rules "one at a time, letting computations for each rule finish before adding the next one", ldv 264 L862-863, L869-870, to use Public Read/Write during an initial load, L852-853, and to avoid any user owning more than 10,000 records, L1033.)

**Important constraints:** While sharing is deferred, record access visible to users may be inconsistent — users may see records they should not yet have access to, or be denied records they should gain. Only enable deferral during maintenance windows or when access inconsistency is acceptable. Deferral is an org-wide setting; it cannot be scoped to a single object. (UNVERIFIED (2026-10-20): inconsistency during deferral and org-wide scope are Help-level; not in the corpus.)

### OWD Tightening vs. Relaxing

Salesforce "automatically recalculates sharing for all records on an object when its organization-wide sharing default access level changes" and removes sharing whose access becomes redundant, for example manual Read Only sharing when the model goes from Private to Public Read Only (apexdev 264 L13049-13052). UNVERIFIED (2026-10-20): everything else in this section is Help-level and not in the corpus — that tightening is the single highest-cost operation, that every share row is rebuilt from scratch, that the job is atomic, cannot be cancelled and has no rollback, and the several-hours figure for 5 million records. Treat the cost guidance as a planning rule of thumb. Changing org-wide defaults (OWD) in the direction of more restriction — Public Read/Write → Public Read Only → Private — is expected to be the most expensive direction.

**Relaxing is cheaper but not free:** Going from Private → Public expands access; Salesforce still processes the change but generally scans fewer rows. Relaxing does not require deleting and rebuilding every share row. OWD tightening on an object with 5 million records in a complex role hierarchy can run for several hours; the job cannot be cancelled once started without rolling back the OWD change itself. (UNVERIFIED (2026-10-20): same as above. The guide documents monitoring or stopping only the Apex recalculation job, via Setup > Apex Jobs, apexdev 264 L13073-13074.)

**Staging tightening changes:** Always use Defer Sharing Calculations before making multiple OWD edits in the same maintenance window. Tighten all target objects while deferred, then resume in one batch.

### Criteria-Based Sharing Rule Recalculation at Volume

Criteria-based sharing rules (metadata `SharingCriteriaRule` with `criteriaItems`, api_meta 264 L132857-132865) evaluate records against a field condition (e.g., `Account.Industry = 'Technology'`). UNVERIFIED (2026-10-20): the rest of this section, that every mass update to the criteria field triggers re-evaluation, is Help-level and not in the corpus. Every time a mass field update changes the criteria field on a large number of records, Salesforce re-evaluates each affected record against all active criteria-based sharing rules for that object. On objects with millions of records and rules referencing frequently-updated fields (such as `Status` or `Rating`), this creates a compounding performance problem: the recalculation is triggered not just by rule changes but by every bulk DML operation that touches the criteria field.

**Mitigation:** Avoid writing criteria-based sharing rules on fields that are frequently mass-updated. Prefer role- or group-based sharing rules where the trigger (role membership change) is infrequent and controlled.

### Apex Managed Share Rebuild Requirement

When the OWD changes, Salesforce recalculates sharing for all records on the object, and "any Apex recalculation classes defined for associated custom object are also executed" (apexdev 264 L13049-13052, L13071-13072). UNVERIFIED (2026-10-20): that a full recalculation "silently deletes" every row with a custom `RowCause`, that nothing reinstates them, and that this happens "with no warning in the UI" are Help-level and not in the corpus; test it in a sandbox. What the guide does say: an administrator might need to recalculate Apex managed sharing "if a locking issue prevented Apex code from granting access" (apexdev 264 L13059-13061), and you can also run it with `Database.executeBatch` (apexdev 264 L13068-13069).

**Registration path (corrected):** an earlier version of this skill said "Setup > Object Manager > [Object] > Apex Sharing Reasons > Edit > set Recalculation Apex Class". The guide associates the class through the object's Apex Sharing Recalculations related list ("associate the class with the custom object, on the custom object's detail page, in the Apex Sharing Recalculation related list", apexdev 264 L13054-13055, L13346-13351; metadata `CustomObject.sharingRecalculations.className`, api_meta 264 L47714-47720). The class "must implement the Database.Batchable interface" and cannot be associated twice with the same object (apexdev 264 L13350-13351). The batch class should delete and re-create: "we recommend that the execute method delete and then re-create all Apex managed sharing for the records in the batch" (apexdev 264 L17959-17960).

**Version gate:** the Apex Developer Guide states both "Apex sharing reasons and Apex managed sharing recalculation are only available for custom objects" (apexdev 264 L12613) and "Apex managed sharing recalculation is supported for both custom and standard objects" (apexdev 264 L12881-12882). The Metadata API resolves it by release: sharing reasons for custom objects are API 14.0+, for standard objects API 68.0+ (api_meta 264 L47650-47651). Treat the custom-only text as the pre-68.0 rule. For custom objects the OWD "must not be set to the most permissive access level" (apexdev 264 L13085-13086).

### Nested Public Groups and Recalculation Cost Multiplier

Nesting public groups inside other public groups multiplies the recalculation cost. When a member is added to a deeply nested group, Salesforce must trace all parent group memberships to determine which sharing rules reference any ancestor group. The cost grows exponentially with nesting depth and group size. Salesforce recommends keeping public groups flat — one level of nesting at most — for any group that is a source of sharing rules. UNVERIFIED (2026-10-20): the nested-group cost, the "exponential" growth and the one-level recommendation are not in the corpus; the only related lines are the group-membership calculation that deferral manages (ldv 264 L598-599) and the load-order advice at ldv 264 L859-870.

---

## Common Patterns

### Pattern 1 — Batch Multiple Structural Changes with Defer Sharing Calculations

**When to use:** You need to make several structural changes (multiple OWD edits, add several sharing rules, reorganize role hierarchy nodes) and want to pay recalculation cost only once.

**How it works:**
1. Schedule a maintenance window during low-usage hours (typically nights or weekends for production orgs).
2. Suspend sharing calculation with the defer sharing calculation permission (ldv 264 L598; UNVERIFIED (2026-10-20): the Setup path and checkbox label are not in the corpus).
3. Make all planned structural changes: OWD edits, sharing rule additions or removals, role or group membership changes.
4. Verify the change set is complete. Once you re-enable recalculation, the job starts immediately.
5. Resume sharing calculation, then start the full recalculation yourself: "you must resume sharing rule calculations and manually initiate a full sharing rule recalculation" (secguide 262 L3533-3534); the Recalculate button is disabled while calculations are deferred (L3545). An earlier version said clearing deferral collapses the queue into one job automatically.
6. Monitor sharing recalculation on the Background Jobs page (secguide 262 L3541-3542, L3580) and the Apex recalculation in Apex Jobs (apexdev 264 L13073-13074). Also check Setup Audit Trail to confirm all structural changes were captured.

**Why not make changes one at a time:** Each change triggers its own recalculation (secguide 262 L3520-3522), and while a sharing rule recalculation is in progress you can't modify org-wide defaults, nor sharing rules while an OWD recalculation runs (secguide 262 L3585-3586).

### Pattern 2 — OWD Tightening with Apex Managed Share Protection

**When to use:** You are tightening OWD on an object that uses Apex managed sharing and need to ensure Apex grants survive the full recalculation.

**How it works:**
1. Before making any OWD change, verify the object has a recalculation batch class associated in its Apex Sharing Recalculations related list (apexdev 264 L13054-13055).
2. If no class is registered, write and deploy one now. The class should: query all records for which Apex grants are needed, delete existing Apex share rows for the custom reason, and insert fresh grants.
3. Enable Defer Sharing Calculations.
4. Apply the OWD tightening change.
5. Disable Defer Sharing Calculations to trigger the recalculation job.
6. Expect the associated batch class to run as part of the OWD change ("any Apex recalculation classes defined for associated custom object are also executed", apexdev 264 L13071-13072); its timing relative to the main recalculation is UNVERIFIED (2026-10-20): not stated in the corpus. Monitor it in Apex Jobs.
7. Verify Apex share rows exist on sample records post-rebuild.

### Pattern 3 — Role Hierarchy Restructuring in Maintenance Window

**When to use:** You need to add, remove, or reparent multiple role nodes as part of a territory or org restructuring.

**How it works:**
1. Enable Defer Sharing Calculations before any role changes.
2. Make all role hierarchy changes — add nodes, reparent nodes, update group memberships — while deferred.
3. Do not add or remove users from roles while deferred unless their access inconsistency is acceptable during the window.
4. Resume sharing calculation and manually initiate the full sharing rule recalculation (secguide 262 L3533-3534); let it run to completion.
5. Monitor the async job queue. Do not make additional structural changes until the job finishes.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single OWD change on a small object (<100K records) | Apply directly without deferral | Low cost; recalculation completes in minutes |
| Multiple OWD changes or multiple sharing rule changes | Use Defer Sharing Calculations to batch | Reduces recalculation cycles from N to 1 |
| OWD tightening on object with millions of records | Maintenance window + deferral + Apex share rebuild verification | Highest-cost single operation; no rollback once started |
| Object uses Apex managed sharing and OWD will change | Associate a recalculation batch class before changing OWD | The class runs on every OWD change (apexdev 264 L13071-13072); the "silently dropped permanently" outcome is UNVERIFIED (2026-10-20) |
| Criteria-based rule on frequently mass-updated field | Replace with role/group-based rule if possible | Criteria rules re-evaluate on every matching DML, not just rule changes |
| Nested public groups (3+ levels deep) used in sharing rules | Flatten group hierarchy to 1 level of nesting | Deep nesting multiplies recalculation fan-out exponentially |
| OWD change running for hours with no completion | Check async job queue for blocking jobs; do not restart | Restarting can produce duplicate recalculation jobs; let it finish (UNVERIFIED (2026-10-20): Help-level) |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Identify the change type and affected objects — confirm record counts, current OWD, and whether Apex managed sharing is in use on any affected object.
2. Assess Apex share rebuild readiness — if any affected object uses Apex managed sharing, verify a registered `Database.Batchable` recalculation class exists before proceeding.
3. Plan the change set — collect all structural changes needed (OWD, sharing rules, roles, groups) and sequence them to be applied together under a single deferral window.
4. Schedule a maintenance window — for OWD tightening on objects with >500K records or complex role hierarchies, require a maintenance window and communicate access inconsistency to stakeholders.
5. Enable Defer Sharing Calculations, apply all structural changes, then resume calculation and manually initiate a full sharing rule recalculation (secguide 262 L3533-3534).
6. Monitor async jobs until recalculation completes — verify Apex share rows on sample records, check Setup Audit Trail for all applied changes, and confirm no additional structural changes were made while the job was running.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All structural changes were applied while Defer Sharing Calculations was enabled, not one-at-a-time.
- [ ] Every object with Apex managed sharing has a registered recalculation batch class before any OWD change is applied.
- [ ] OWD tightening changes were scheduled during a maintenance window, not business hours.
- [ ] The recalculation background job completed without error (check async job queue and Setup Audit Trail).
- [ ] Sample Apex share rows were verified post-recalculation on at least one affected record.
- [ ] No new criteria-based sharing rules were written on fields that are frequently mass-updated.
- [ ] Nested public groups used as sharing rule sources have been reviewed and flattened where depth exceeds 1 level.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **OWD tightening is atomic with no rollback** (UNVERIFIED (2026-10-20): Help-level, not in the corpus) — Once you submit an OWD change from Public to Private on an object with 10 million records, the recalculation job starts immediately and cannot be cancelled. The only recovery is to re-tighten the OWD in the opposite direction, which triggers another full recalculation. Plan tightening changes in a maintenance window and confirm the change set before saving.

2. **Apex managed share rows may be removed on full recalculation** (UNVERIFIED (2026-10-20): the silent-deletion claim is not in the corpus; the guide documents that recalculation removes redundant sharing, apexdev 264 L13050-13052, and that the associated recalculation class runs on an OWD change, L13071-13072) — There is no UI warning, no error message, and no audit trail entry when Apex share rows are removed during a full recalculation. Users simply lose access. If no batch recalculation class is registered, the grants are gone permanently until someone manually re-runs the Apex batch or redeploys.

3. **Defer Sharing Calculations affects the entire org, not a single object** (UNVERIFIED (2026-10-20): scope is Help-level) — When deferral is enabled, all incremental sharing recalculation is suspended across every object. Any structural sharing change made by any admin during the deferral window is queued. If someone unknowingly makes a sharing change during a deferral window, it will be included in the full recalculation you run afterwards (secguide 262 L3533-3534), potentially expanding its scope.

4. **Parallel recalculation does not eliminate lock contention on skewed objects** (automatic OWD and sharing rule recalculation is "processed asynchronously and in parallel", secguide 262 L3556-3558; UNVERIFIED (2026-10-20): that parallelism worsens skew contention is not in the corpus; Bulk API 2.0 lists user, role and ownership updates under private sharing as lock-contention causes, api_asynch 264 L2627-2640) — However, if the affected object has ownership skew or parent-child skew, parallel recalculation can actually increase lock contention because multiple parallel threads compete for the same skewed record locks. On highly skewed objects, the job may still run for many hours.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Staged Change Plan | Ordered list of structural sharing changes to apply under a single Defer Sharing Calculations window, with maintenance window timing |
| Apex Share Rebuild Checklist | Per-object checklist confirming registered recalculation batch class name, last verified date, and sample record validation |
| Post-Recalculation Verification Log | Record of async job completion, Setup Audit Trail entries, and Apex share row spot-checks |

---

## Related Skills

- admin/data-skew-and-sharing-performance — Use when the root cause of slow recalculation is ownership or parent-child skew. This skill covers the recalculation job lifecycle and safe change sequencing, not the data distribution root cause.
- admin/sharing-and-visibility — Use for designing the overall sharing model (OWD, roles, sharing rules). This skill handles recalculation performance during execution, not model design decisions.
- apex/apex-managed-sharing — Use when creating or debugging Apex sharing rows (custom RowCause, share object DML, recalculation class implementation). This skill covers the impact of recalculation on existing Apex grants.
