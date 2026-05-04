---
name: migration-architecture-patterns
description: "Architectural patterns for org migration — org merge (consolidate two orgs into one), org split (separate one org into two), and coexistence (run both for a transition period with identity / data / metadata bridges). Covers the pre-migration metadata audit (the most-skipped step), the why-vs-how decision separation for splits, record-Id remapping for external systems that hardcoded 15/18-digit IDs, and rollback-safe deployment windows. NOT for the go-live cutover sequencing itself (see devops/go-live-cutover-planning), NOT for the upstream multi-org-strategy decision (see architect/multi-org-strategy)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
  - Operational Excellence
triggers:
  - "salesforce org merge consolidate two orgs"
  - "org split regulatory isolation m&a"
  - "salesforce coexistence identity sso bridge"
  - "metadata audit before data migration"
  - "record id remapping 18 digit external system"
  - "org migration rollback safe deployment window"
tags:
  - org-migration
  - org-merge
  - org-split
  - coexistence
  - cutover
  - identity-bridging
  - metadata-audit
inputs:
  - "Direction: merge (N → 1), split (1 → N), or coexistence (1 → 1+1 with bridge)"
  - "Driver: regulatory, M&A, capacity / limits, divestiture, business unit autonomy"
  - "Inventory of metadata in scope (objects, fields, picklists, validation rules, automation)"
  - "Inventory of data volume per object plus relationships (parent-child trees)"
  - "External systems that reference Salesforce record IDs"
  - "Hyperforce region constraints (same / different)"
outputs:
  - "Migration architecture decision document — direction, driver, sequencing, freeze windows"
  - "Pre-migration metadata audit (delta map between source orgs / target structure)"
  - "Record-ID remapping plan for external integrations"
  - "Coexistence bridge design (Salesforce Connect external objects, Platform Events, identity / SSO)"
  - "Rollback plan tied to each cutover window"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-04
---

# Org Migration Architecture Patterns

The architecture-level decisions for org migration. Three shapes —
**merge**, **split**, **coexistence** — each with its own discipline of
metadata audit, data partitioning, identity continuity, and rollback
planning. The cutover mechanics (freeze windows, parallel-run vs
hard-cutover, runbook ordering) live in `devops/go-live-cutover-planning`.
The upstream "should we have one org or many" decision lives in
`architect/multi-org-strategy`. This skill is the *how-to-execute* layer
in between.

What this skill is NOT. Picking go-live time-of-day, comm plans, and
rollback runbooks is operations — that's the cutover skill. Whether
multi-org is the right end-state at all is strategic — that's the
multi-org-strategy skill. Here we assume the strategic call has been
made and the cutover-runbook team is downstream.

---

## Before Starting

- **Name the direction explicitly.** Merge (N → 1), split (1 → N), or
  coexistence (1 → 1+1 with a runtime bridge). Each has different
  failure modes; mixing them in a single design produces ambiguous
  ownership.
- **Name the driver.** Regulatory isolation (compliance), M&A
  consolidation, divestiture (split for sale), capacity / limits
  relief (split because hitting org-level governors), business-unit
  autonomy. The driver decides which trade-offs are acceptable —
  e.g. for divestiture, "no cross-org access ever again" outranks
  data continuity.
- **Inventory before designing.** Metadata audit (objects, fields,
  picklists, validation rules, automation) and data inventory (record
  counts, object relationships) both happen *before* the architecture
  decision is finalized. Designing without inventory produces a plan
  that hits unexpected metadata conflicts in week 2 of execution.
- **Identify external dependencies on record IDs.** Any external
  system that stores a 15- or 18-character Salesforce record ID will
  break on merge / split unless you plan a remapping layer. This is
  one of the highest-risk surprises.

---

## Core Concepts

### The three migration shapes

| Shape | Definition | Typical driver |
|---|---|---|
| **Merge** | N source orgs → 1 target org. Source orgs are decommissioned (or become read-only archives). | M&A consolidation; cost reduction; eliminating org sprawl |
| **Split** | 1 source org → N target orgs. Some users / data move to a new org; the source org may keep a subset. | Regulatory isolation; divestiture; org-limit relief; BU autonomy |
| **Coexistence** | Both orgs continue to operate, with a runtime bridge (identity, data, events) between them. | Phased migration; long-term federation; mid-acquisition transition |

A real migration is often **temporal coexistence followed by hard
cutover** — coexistence as a transition shape, ending in a merge or a
clean split. Designing coexistence as a permanent state is rarer (and
usually a sign that the multi-org-strategy decision wasn't actually
made).

### Pre-migration metadata audit (the most-skipped step)

Before any data moves, build a metadata delta between source and target.
This is the single most important deliverable — skipping it is the most
common cause of cutover failures.

For each metadata type, compare:

- **Objects + fields.** Same API name? Same data type? Same picklist
  values? Same field-level security? Custom objects with the same name
  but different schemas are landmines.
- **Picklists.** Same values? Same labels? Globally-shared vs
  per-record-type? Inactive values that must / must not flow?
- **Validation rules.** Will rules in the target reject data from the
  source? (Yes, often.) Plan a controlled disable / re-enable around
  the data load.
- **Automation.** Process Builders, Flows, Apex triggers. Will
  duplicate / conflicting automation fire on imported records? Almost
  always yes — disable bulk-load-side automation during migration,
  re-enable after data validation.
- **Record types + page layouts.** Mappings between source-org record
  types and target-org record types must be explicit per object.
- **Profiles / permission sets.** User access in target may be
  narrower than source — users who could see records in their old org
  may not see them in the new one without permission updates.

The audit produces a **delta document** — for every metadata
mismatch, a decision: align source, align target, or accept the
mismatch with a documented mitigation.

### Record ID remapping

Salesforce record IDs are org-scoped. A 15- or 18-character ID from
the source org has no meaning in the target.

External systems that have stored Salesforce IDs (CRMs that link to
SF records, data warehouses, analytics tools, integration mapping
tables) will fail if you don't remap.

The remapping pattern:

1. **Capture source-Id → external-key** before migration. Every
   record that's about to move must have a stable external key
   (custom external-Id field, or a synthetic one generated for the
   migration).
2. **Insert into target with the external-Id field populated.**
   Salesforce assigns new IDs.
3. **Build the target-Id ↔ external-key ↔ source-Id table.** Persist
   it.
4. **Update external systems.** Replace stored source IDs with target
   IDs using the remapping table.
5. **Maintain the remapping table for the life of any external system
   that might still reference source IDs.** Some never get fully
   migrated.

The most common failure: external systems that nobody knew were
storing Salesforce IDs. Surface them in the inventory step;
post-cutover discovery is expensive.

### Coexistence bridges

When both orgs run simultaneously (transitional or permanent), choose
the bridge based on what crosses the boundary:

| Crossing | Bridge | Notes |
|---|---|---|
| Users (same person uses both orgs) | **SSO via Salesforce Identity** + per-org permission sets | Identity is the first thing to bridge; otherwise users have separate accounts that drift |
| Real-time data viewing (read records from the other org without copy) | **Salesforce Connect** with a cross-org adapter (oData) | No data copy; reads on demand. Latency-sensitive |
| Eventual-consistency data sync (changes in one org propagate to the other) | **Platform Events + Apex subscribers** in each org | Decoupled, durable, retry built in |
| Bulk batch sync | **MuleSoft / middleware** or a scheduled Heroku Connect-style worker | Right when volume + transformation are heavy |
| Authentication tokens / API access | **Connected Apps** with mutual OAuth | Each org grants the other an integration user / client credentials |

Coexistence design must address: identity continuity (SSO), data
continuity (which records are visible to which org), and rollback
(can we cleanly disable the bridge if migration is paused or
reversed?).

---

## Common Patterns

### Pattern A — Org merge with phased cutover

**When to use.** Two source orgs need to consolidate into one target.
Both source orgs continue operating during the transition.

**Sequence.**

1. **Inventory + audit.** Metadata delta between source A, source B, and target. Data inventory. External integration inventory.
2. **Target-org schema reconciliation.** Resolve metadata deltas in target — pick winning picklist values, harmonize validation rules, resolve API name conflicts.
3. **Build coexistence bridge.** SSO so users from both source orgs can authenticate to target during cutover. Salesforce Connect or Platform Events for cross-org read during phased data load.
4. **Pilot data load (≤1% of records).** Validate the migration ETL produces correct records in target. Verify external-Id remapping table.
5. **Wave 1 — least-coupled records first.** Reference data, then customers, then transactions. Each wave validated before next.
6. **External integration cutover.** Update each external system's Salesforce-Id references using the remapping table.
7. **Source-org freeze.** Source orgs go read-only. Final delta sync from source to target.
8. **Hard cutover.** Source orgs decommissioned (or kept as archives). Target is canonical.

Each wave has a documented rollback: the previous wave's data state
is recoverable.

### Pattern B — Org split with regulatory isolation

**When to use.** A regulator demands that a subset of users / data be
in a separately-governed org. (HIPAA-segregated patient data, geographic
data residency, divestiture of a business unit.)

**Critical constraint.** After cutover, the new org must be operationally
independent — no shared admin users, no shared integration credentials,
no Salesforce Connect bridge into the regulated data.

**Sequence.**

1. **Define the regulatory boundary.** Which objects, which records, which users. The boundary is the most contested part of the design — get regulator sign-off.
2. **Provision the new org.** Edition, license counts, region (Hyperforce locality may be the regulatory driver).
3. **Replicate the relevant metadata.** Subset of source-org metadata, deployed to the new org. New org's metadata then evolves independently.
4. **Move the records.** Bulk insert with external-Id preservation; capture Id-remapping for any external integrations.
5. **Cut over identity.** Move users to the new org's IdP. Source-org access for migrated users is revoked at the same time.
6. **Cut over external integrations.** Each integration that referenced moved records now points at the new org.
7. **Source-org cleanup.** The migrated records / users are removed from source; source-org metadata is purged of fields that are now exclusive to the new org.

The most common failure: leaving a Salesforce Connect bridge in
place "for convenience" — it defeats the regulatory isolation that
was the entire point.

### Pattern C — Coexistence as a permanent state

**When to use.** Two business units that share customers but operate
distinct domains, with no executive mandate to consolidate. (Or a
partnership where each side keeps its own org.)

**Design.**

- **Identity.** SSO via a shared IdP. Per-user permission set per org.
- **Customer record.** Master in one org, replica in the other via Platform Events. Updates flow both directions through a conflict-resolution rule (last-write-wins, or org-A-wins for some fields, org-B-wins for others).
- **Lookup-only data.** Salesforce Connect external objects on the consuming side; data lives in the producing org.
- **Reporting.** Either CRM Analytics with a cross-org connector, or a downstream warehouse that ingests from both.

Coexistence is harder to maintain than people expect. Schema drift
between the two orgs is constant; the bridge needs ongoing
investment.

---

## Decision Guidance

| Situation | Approach | Reason |
|---|---|---|
| Two source orgs, M&A driver, exec-mandated consolidation | **Merge with phased cutover** (Pattern A) | Standard consolidation; sequenced waves de-risk the data load |
| Regulator demands data isolation | **Split with hard isolation** (Pattern B) | Coexistence bridge undermines the isolation requirement |
| Hitting org-level governors / limits | **Split for capacity** | Splitting low-coupled BUs is faster than redesigning to fit limits |
| Two BUs share customers, no consolidation mandate | **Coexistence** (Pattern C) | Forced merge without business driver fails politically |
| Small data volume, low complexity | **Hard cutover, no coexistence** | Overhead of building a bridge isn't justified |
| External systems reference SF record IDs | **Build remapping table FIRST** | Discovery during cutover is expensive |
| Source-org and target-org metadata diverge significantly | **Metadata reconciliation phase before any data movement** | Skip = data load fails on validation rules / triggers |
| User access patterns differ between orgs | **Permission inventory + reconciliation** | Users seeing fewer records post-cutover is a noisy escalation |
| Asking "should we even merge / split / coexist?" | **Defer to architect/multi-org-strategy** | Strategic question; this skill assumes that decision is made |
| Asking "what time on Saturday do we cutover?" | **Defer to devops/go-live-cutover-planning** | Operational question; out of scope here |

---

## Recommended Workflow

1. **Confirm direction (merge / split / coexistence) and driver.** Both must be named in writing before any other work.
2. **Inventory metadata, data, and external dependencies in scope.** Output: three documents — metadata delta map, data volume per object, external-system reference list.
3. **Reconcile metadata in target.** Resolve every delta from step 2.
4. **Design the bridge / cutover / split mechanics.** Pattern A / B / C from above as the starting template.
5. **Plan record-Id remapping.** Define external-Id strategy; capture source-Id → target-Id mapping.
6. **Plan rollback per phase.** Each cutover wave has a documented rollback that lands the system in a known good state.
7. **Hand off to the cutover-runbook team.** Ops sequencing, freeze windows, comm plan are downstream.

---

## Review Checklist

- [ ] Direction (merge / split / coexistence) is named explicitly in the design.
- [ ] Driver (regulatory / M&A / limits / autonomy) is named.
- [ ] Pre-migration metadata audit document exists; every delta has a decision.
- [ ] Data volume inventory per object is captured.
- [ ] External-system inventory of Salesforce-Id references is complete.
- [ ] Record-Id remapping table design is documented.
- [ ] If split: regulatory isolation is enforced (no Salesforce Connect bridge into protected data).
- [ ] If coexistence: identity (SSO), data (sync mechanism), and rollback are each addressed.
- [ ] Per-phase rollback is documented.
- [ ] Hand-off to cutover team is explicit (where this skill ends).

---

## Salesforce-Specific Gotchas

1. **Skipping the pre-migration metadata audit is the #1 failure mode.** Don't move data before reconciling object / field / picklist / validation / automation deltas. (See `references/gotchas.md` § 1.)
2. **Salesforce record IDs are org-scoped.** Any external system that stored an Id from the source org will break on merge / split unless remapped. (See `references/gotchas.md` § 2.)
3. **Validation rules in the target will reject imported source data.** Plan a controlled disable / re-enable around the data load. (See `references/gotchas.md` § 3.)
4. **Automation in the target fires on imported records by default.** Bulk migration without disabling automation produces side effects (auto-emails sent, fields auto-stamped) on data that didn't go through the normal lifecycle. (See `references/gotchas.md` § 4.)
5. **Coexistence bridges are operational debt that grows over time.** Schema drift is constant; budget for ongoing bridge maintenance, not just initial build. (See `references/gotchas.md` § 5.)
6. **Splits "for regulatory isolation" with a Salesforce Connect bridge defeat the isolation.** Hard rule: regulated splits have NO runtime bridge to protected data. (See `references/gotchas.md` § 6.)
7. **Hyperforce region constraints affect data residency** during merge / split when source and target are in different regions. (See `references/gotchas.md` § 7.)

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Migration Architecture Decision Document | Direction, driver, pattern (A/B/C), sequencing, success criteria |
| Metadata Delta Map | Per-metadata-type comparison source(s) ↔ target with decisions |
| Data Volume Inventory | Per-object record counts and parent-child relationship depth |
| External-System Reference List | Every external system that holds Salesforce record IDs, with the remapping plan |
| Record-Id Remapping Table Design | Schema + persistence strategy for source-Id ↔ target-Id mapping |
| Per-Phase Rollback Plans | What "rollback" means per cutover wave, and how to execute |

---

## Related Skills

- `architect/multi-org-strategy` — the upstream "single-org vs multi-org" decision; consult before this skill if the strategic call hasn't been made.
- `devops/go-live-cutover-planning` — the downstream operational cutover (freeze windows, comm plan, parallel-run vs hard-cutover); consult after this skill.
- `data/bulk-migration-runbook` — Bulk API patterns, parent-child sequencing, error-row handling for the actual data load.
- `architect/hybrid-integration-architecture` — when the bridge crosses into AWS / Heroku / MuleSoft territory.
- `security/byok-key-rotation` — when migrated data is Shield-encrypted and key custody must move with the data.
