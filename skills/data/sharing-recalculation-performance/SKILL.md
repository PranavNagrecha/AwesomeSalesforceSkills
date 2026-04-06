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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Sharing Recalculation Performance

Use this skill when a Salesforce administrator or architect needs to plan or recover from a long-running sharing recalculation job — triggered by OWD changes, sharing rule modifications, role hierarchy restructuring, or group membership edits. This skill covers the Defer Sharing Calculations mechanism, OWD change cost estimation, Apex managed share rebuild requirements, and safe sequencing of structural sharing changes.

---

## Before Starting

Gather this context before working on anything in this domain:

- Identify the exact type of change being made: OWD change (direction matters — tightening is far more expensive than relaxing), sharing rule add/remove, role hierarchy edit, or public group restructuring.
- Know the approximate record count on each affected object. For objects with millions of records and Private or Read-Only OWD, any structural change will produce a long-running background job.
- Confirm whether any affected object uses Apex managed sharing (custom `RowCause` on the share object). If so, a registered `Database.Batchable` recalculation class is mandatory — without it, Apex grants are silently dropped on full recalculation and never rebuilt.
- Check current async job queue depth in Setup > Apex Jobs or Monitoring > Jobs. A full recalculation job will compete with other background Apex and sharing jobs.
- Determine whether a maintenance window is available. OWD tightening on objects with millions of records should never be done during business hours.

---

## Core Concepts

### Defer Sharing Calculations

Defer Sharing Calculations is a Setup checkbox (Setup > Defer Sharing Calculations) that suspends all incremental sharing recalculation triggered by individual structural changes. When enabled, Salesforce queues structural change events (OWD edits, sharing rule changes, role hierarchy edits, group membership updates) but does not process them immediately. When the checkbox is cleared, Salesforce collapses all queued events into a single background recalculation job.

**Why this matters:** Without deferral, each individual structural change — enabling a sharing rule, adding a role, updating a group — triggers its own incremental recalculation job. If you need to make ten structural changes, you pay recalculation cost ten times instead of once. Deferring batches all changes into one job run, typically scheduled off-peak.

**Important constraints:** While sharing is deferred, record access visible to users may be inconsistent — users may see records they should not yet have access to, or be denied records they should gain. Only enable deferral during maintenance windows or when access inconsistency is acceptable. Deferral is an org-wide setting; it cannot be scoped to a single object.

### OWD Tightening vs. Relaxing

Changing org-wide defaults (OWD) in the direction of more restriction — Public Read/Write → Public Read Only → Private — is the single highest-cost recalculation operation. When OWD is tightened, Salesforce must rebuild all sharing table rows for the affected object from scratch: every sharing rule, every manual share, and every Apex share must be re-evaluated against the new baseline. This runs as a single atomic background job with no rollback.

**Relaxing is cheaper but not free:** Going from Private → Public expands access; Salesforce still processes the change but generally scans fewer rows. Relaxing does not require deleting and rebuilding every share row. OWD tightening on an object with 5 million records in a complex role hierarchy can run for several hours; the job cannot be cancelled once started without rolling back the OWD change itself.

**Staging tightening changes:** Always use Defer Sharing Calculations before making multiple OWD edits in the same maintenance window. Tighten all target objects while deferred, then resume in one batch.

### Criteria-Based Sharing Rule Recalculation at Volume

Criteria-based sharing rules evaluate records against a field condition (e.g., `Account.Industry = 'Technology'`). Every time a mass field update changes the criteria field on a large number of records, Salesforce re-evaluates each affected record against all active criteria-based sharing rules for that object. On objects with millions of records and rules referencing frequently-updated fields (such as `Status` or `Rating`), this creates a compounding performance problem: the recalculation is triggered not just by rule changes but by every bulk DML operation that touches the criteria field.

**Mitigation:** Avoid writing criteria-based sharing rules on fields that are frequently mass-updated. Prefer role- or group-based sharing rules where the trigger (role membership change) is infrequent and controlled.

### Apex Managed Share Rebuild Requirement

When Salesforce performs a full sharing recalculation on an object, all Apex managed share rows for that object — rows with a custom `RowCause` value — are silently deleted before the rebuild. Salesforce does not automatically reinstate them. The only way to restore Apex grants after a full recalculation is to have a registered `Database.Batchable` recalculation class on the Apex sharing reason.

**Registration path:** Setup > Object Manager > [Object] > Apex Sharing Reasons > Edit > set Recalculation Apex Class to the batch class. Without this registration, any OWD change or manual sharing recalculation on the object will permanently destroy all Apex grants with no warning in the UI. The batch class must be idempotent — it should delete all existing Apex share rows for its reason and reinsert the correct set.

### Nested Public Groups and Recalculation Cost Multiplier

Nesting public groups inside other public groups multiplies the recalculation cost. When a member is added to a deeply nested group, Salesforce must trace all parent group memberships to determine which sharing rules reference any ancestor group. The cost grows exponentially with nesting depth and group size. Salesforce recommends keeping public groups flat — one level of nesting at most — for any group that is a source of sharing rules.

---

## Common Patterns

### Pattern 1 — Batch Multiple Structural Changes with Defer Sharing Calculations

**When to use:** You need to make several structural changes (multiple OWD edits, add several sharing rules, reorganize role hierarchy nodes) and want to pay recalculation cost only once.

**How it works:**
1. Schedule a maintenance window during low-usage hours (typically nights or weekends for production orgs).
2. In Setup > Defer Sharing Calculations, enable the "Defer Sharing Calculations" checkbox.
3. Make all planned structural changes: OWD edits, sharing rule additions or removals, role or group membership changes.
4. Verify the change set is complete. Once you re-enable recalculation, the job starts immediately.
5. Clear the Defer Sharing Calculations checkbox. Salesforce collapses all queued changes into a single background job and begins processing.
6. Monitor the job in Setup > Apex Jobs (for Apex-driven recalculation) and the async job queue. Also check Setup Audit Trail to confirm all structural changes were captured.

**Why not make changes one at a time:** Each individual change triggers an incremental recalculation job. Ten changes = ten recalculation cycles = significantly more total elapsed time.

### Pattern 2 — OWD Tightening with Apex Managed Share Protection

**When to use:** You are tightening OWD on an object that uses Apex managed sharing and need to ensure Apex grants survive the full recalculation.

**How it works:**
1. Before making any OWD change, verify the Apex sharing reason has a registered recalculation batch class (Object Manager > [Object] > Apex Sharing Reasons).
2. If no class is registered, write and deploy one now. The class should: query all records for which Apex grants are needed, delete existing Apex share rows for the custom reason, and insert fresh grants.
3. Enable Defer Sharing Calculations.
4. Apply the OWD tightening change.
5. Disable Defer Sharing Calculations to trigger the recalculation job.
6. After the recalculation job completes, Salesforce automatically invokes the registered batch class to rebuild Apex grants.
7. Verify Apex share rows exist on sample records post-rebuild.

### Pattern 3 — Role Hierarchy Restructuring in Maintenance Window

**When to use:** You need to add, remove, or reparent multiple role nodes as part of a territory or org restructuring.

**How it works:**
1. Enable Defer Sharing Calculations before any role changes.
2. Make all role hierarchy changes — add nodes, reparent nodes, update group memberships — while deferred.
3. Do not add or remove users from roles while deferred unless their access inconsistency is acceptable during the window.
4. Disable Defer Sharing Calculations and allow the single collapsed recalculation job to run to completion.
5. Monitor the async job queue. Do not make additional structural changes until the job finishes.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single OWD change on a small object (<100K records) | Apply directly without deferral | Low cost; recalculation completes in minutes |
| Multiple OWD changes or multiple sharing rule changes | Use Defer Sharing Calculations to batch | Reduces recalculation cycles from N to 1 |
| OWD tightening on object with millions of records | Maintenance window + deferral + Apex share rebuild verification | Highest-cost single operation; no rollback once started |
| Object uses Apex managed sharing and OWD will change | Register recalculation batch class before changing OWD | Without it, all Apex grants are silently dropped permanently |
| Criteria-based rule on frequently mass-updated field | Replace with role/group-based rule if possible | Criteria rules re-evaluate on every matching DML, not just rule changes |
| Nested public groups (3+ levels deep) used in sharing rules | Flatten group hierarchy to 1 level of nesting | Deep nesting multiplies recalculation fan-out exponentially |
| OWD change running for hours with no completion | Check async job queue for blocking jobs; do not restart | Restarting can produce duplicate recalculation jobs; let it finish |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Identify the change type and affected objects — confirm record counts, current OWD, and whether Apex managed sharing is in use on any affected object.
2. Assess Apex share rebuild readiness — if any affected object uses Apex managed sharing, verify a registered `Database.Batchable` recalculation class exists before proceeding.
3. Plan the change set — collect all structural changes needed (OWD, sharing rules, roles, groups) and sequence them to be applied together under a single deferral window.
4. Schedule a maintenance window — for OWD tightening on objects with >500K records or complex role hierarchies, require a maintenance window and communicate access inconsistency to stakeholders.
5. Enable Defer Sharing Calculations, apply all structural changes, then disable deferral to trigger a single collapsed recalculation job.
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

1. **OWD tightening is atomic with no rollback** — Once you submit an OWD change from Public to Private on an object with 10 million records, the recalculation job starts immediately and cannot be cancelled. The only recovery is to re-tighten the OWD in the opposite direction, which triggers another full recalculation. Plan tightening changes in a maintenance window and confirm the change set before saving.

2. **Apex managed share rows are silently deleted on full recalculation** — There is no UI warning, no error message, and no audit trail entry when Apex share rows are removed during a full recalculation. Users simply lose access. If no batch recalculation class is registered, the grants are gone permanently until someone manually re-runs the Apex batch or redeploys.

3. **Defer Sharing Calculations affects the entire org, not a single object** — When deferral is enabled, all incremental sharing recalculation is suspended across every object. Any structural sharing change made by any admin during the deferral window is queued. If someone unknowingly makes a sharing change during a deferral window, it will be included in the collapsed recalculation job, potentially expanding its scope.

4. **Parallel recalculation does not eliminate lock contention on skewed objects** — Salesforce enables parallel sharing recalculation by default to speed up large jobs. However, if the affected object has ownership skew or parent-child skew, parallel recalculation can actually increase lock contention because multiple parallel threads compete for the same skewed record locks. On highly skewed objects, the job may still run for many hours.

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
