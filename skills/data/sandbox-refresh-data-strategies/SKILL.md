---
name: sandbox-refresh-data-strategies
description: "Use this skill when designing data management strategies for sandbox refreshes: deciding which reference data must be re-seeded after every refresh, using Salesforce's native Data Seeding feature, writing SandboxPostCopy implementations that hand off to Queueable jobs for large data loads, and cleaning up stale data between sprints. Trigger keywords: seed data after sandbox refresh, SandboxPostCopy data strategy, native data seeding Salesforce, reference data re-seed after refresh, post-refresh data cleanup. NOT for sandbox administration setup, sandbox type selection (use sandbox-strategy), sandbox refresh mechanics and PII masking (use sandbox-refresh-and-templates), or scratch org data seeding for CI (use data-seeding-for-testing)."
category: data
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "how do I automatically seed reference data after every sandbox refresh"
  - "my SandboxPostCopy script is hitting governor limits when loading data after sandbox refresh"
  - "how do I use the native Salesforce Data Seeding feature to populate a sandbox"
  - "what data should I re-seed after a Salesforce sandbox refresh"
  - "SandboxPostCopy is failing with Automated Process user errors during data load"
  - "which objects does native Data Seeding not support in Salesforce"
tags:
  - sandbox
  - data-seeding
  - sandboxpostcopy
  - reference-data
  - data-management
inputs:
  - "Sandbox type being refreshed (Developer, Developer Pro, Partial, Full)"
  - "List of reference data objects that must be present for application function"
  - "Data volume for each seed dataset"
  - "Automation-dependent objects (Flows, validation rules, triggers) that must be disabled during seeding"
outputs:
  - "Reference data seeding strategy documenting what to seed, when, and how"
  - "SandboxPostCopy implementation handing off to Queueable for large seeding jobs"
  - "Native Data Seeding template design guidance"
  - "Stale data cleanup procedure for sprint transitions"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-16
---

# Sandbox Refresh Data Strategies

Use this skill when designing the data management layer for sandbox refreshes — specifically the strategy for re-seeding reference data after a refresh, using Salesforce's native Data Seeding feature, and implementing SandboxPostCopy for automated post-refresh data population. Distinct from sandbox-refresh-and-templates (which covers refresh mechanics and PII masking) and data-seeding-for-testing (which covers scratch org and CI seeding).

---

## Before Starting

Gather this context before working on anything in this domain:

- What sandbox type is being refreshed? Developer, Developer Pro, Partial, or Full? Full Copy sandboxes include production data; others typically do not.
- What reference data (picklist-driving custom objects, configuration tables, territory hierarchies, product catalogs) must exist for the application to function after refresh?
- How large is the seed dataset per object? SandboxPostCopy cannot perform large DML directly — large seeding must be delegated to a Queueable.
- Are automations (Flows, Apex triggers, Process Builder) enabled on the seeded objects? They must be disabled during large seeding to avoid unwanted side effects and limit consumption.

---

## Core Concepts

### SandboxPostCopy Interface and Its DML Limitations

The `SandboxPostCopy` Apex interface provides a `runApexClass(SandboxContext context)` method that runs **immediately after sandbox creation or refresh**, as the **Automated Process user**. This user has DML capability but operates under specific constraints:

- SandboxPostCopy runs **synchronously** in the context of the refresh job. Large DML inside the method will time out.
- The Automated Process user has **no profile-based field access restrictions** but is subject to org-wide sharing and trigger/automation execution.
- **Recommended pattern for large data seeding**: The SandboxPostCopy method should only **enqueue a Queueable** (using `System.enqueueJob()`) that performs the actual DML. The Queueable runs asynchronously after the refresh completes.

The canonical anti-pattern is attempting large DML directly inside `runApexClass` — this times out for datasets exceeding a few hundred records per object.

### Native Salesforce Data Seeding Feature

Salesforce provides a native **Data Seeding** feature (accessible in Setup > Data Seeding) that supports three template types:
1. **Nodes**: Seed specific records from selected objects individually
2. **Levels**: Seed records up to a defined relationship depth (parent → child hierarchies)
3. **Generate**: Create synthetic test data matching field-level data types

Key capabilities:
- **Automation-disable during seed**: The feature automatically disables triggers, flows, and validation rules during seeding to prevent unwanted side effects
- **Incremental seeding**: Supports adding records to existing seed datasets without full replacement
- **Record type and picklist validation**: Validates that seeded records match valid record types and picklist values in the target org

**Native Data Seeding does NOT support these object types:**
- Big Objects
- Calculated fields
- Chatter-related objects (FeedItem, FeedComment)
- Files and ContentDocument
- External objects
- AgentWork

For unsupported object types, use SFDMU, Apex scripts, or Data Loader instead.

### Reference Data Classification

Not all data must be re-seeded after every refresh. Reference data falls into categories:

1. **Must seed every refresh**: Configuration tables that control application behavior (Custom Settings if not deployed via script, territory hierarchies, product category trees, approval chain configuration objects)
2. **Seed on initial setup only**: Master data that rarely changes (country/region codes, currency codes)
3. **Never seed**: Transactional data (Cases, Opportunities, Orders) — these are test artifacts that should be generated by test scripts, not pre-seeded

---

## Common Patterns

### Pattern: SandboxPostCopy with Queueable Delegation

**When to use:** Any time more than ~100 records per object need to be seeded post-refresh.

**How it works:**
```apex
global class PostRefreshSeedHandler implements SandboxPostCopy {
    global void runApexClass(SandboxContext context) {
        // Only enqueue — never do large DML here
        if (!Test.isRunningTest()) {
            System.enqueueJob(new SeedReferenceDataQueueable());
        }
    }
}
```

The `SeedReferenceDataQueueable` class chains additional Queueables if needed (Salesforce allows up to 50 chained Queueable jobs). Each Queueable processes one object or a manageable batch.

**Why not DML in SandboxPostCopy directly:** Large DML in the SandboxPostCopy method causes the refresh completion step to time out, resulting in a failed or incomplete seeding with no clear error.

### Pattern: Native Data Seeding Template for Reference Objects

**When to use:** Reference object data is stable enough to be defined once and re-used across all sandbox refreshes without code.

**How it works:**
1. In production or a reference sandbox, navigate to Setup > Data Seeding.
2. Create a seeding template selecting the reference objects and record criteria.
3. Choose template type: Nodes (specific records) or Levels (with children).
4. Assign the template to sandbox environments that need this data after refresh.
5. Configure the seeding to run automatically on sandbox creation/refresh.

**Why use Data Seeding over scripts for stable reference data:** Data Seeding handles automation-disable automatically, supports incremental updates, and requires no Apex deployment. For stable reference data, it is lower maintenance than custom scripts.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| < 100 records, simple object | SandboxPostCopy with direct DML | Small datasets are safe within the method timeout |
| > 100 records or complex parent-child hierarchy | SandboxPostCopy → Queueable delegation | Direct DML in SandboxPostCopy times out for large datasets |
| Stable reference data, no Apex team needed | Native Data Seeding templates | No code; handles automation-disable; incremental updates |
| ContentDocument or Big Object seeding needed | SFDMU or Data Loader post-refresh step | Not supported by native Data Seeding |
| Stale transactional data cleanup between sprints | Separate cleanup Queueable or Data Loader delete job | Transactional data should not be pre-seeded |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Classify reference data** — Identify which objects must be seeded after every refresh (application configuration) vs. objects that should never be pre-seeded (transactional test data).
2. **Assess data volume per object** — Count the records that must be seeded. Objects over ~100 records require Queueable delegation; very large sets may need native Data Seeding or SFDMU.
3. **Check native Data Seeding eligibility** — Confirm the objects are supported by native Data Seeding (not Big Objects, Files, Chatter, external objects).
4. **Design the SandboxPostCopy class** — Write a minimal `runApexClass` that only enqueues the seeding Queueable. All actual DML lives in the Queueable(s).
5. **Build Queueable chain** — Implement `SeedReferenceDataQueueable` that processes one object per execution, chains to the next Queueable for the next object.
6. **Configure automation disable** — For objects with active triggers or flows, add logic to disable automations before seeding (or use native Data Seeding which handles this automatically).
7. **Test the full refresh cycle** — Refresh a Developer sandbox, confirm seeding runs automatically, verify all reference data is present and valid.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] SandboxPostCopy only enqueues — no large DML directly in runApexClass
- [ ] Queueable chain handles all large object seeding
- [ ] Native Data Seeding configured for stable reference data if applicable
- [ ] Automation disable/enable logic present for seeded objects
- [ ] Big Objects, Files, ContentDocument not attempted via native Data Seeding
- [ ] Stale transactional data cleanup process documented for sprint transitions
- [ ] Full refresh test completed in Developer sandbox

---

## Salesforce-Specific Gotchas

1. **SandboxPostCopy large DML times out** — Running DML for hundreds or thousands of records directly inside `runApexClass` causes the post-copy step to time out, leaving the sandbox seeded incompletely with no clear failure message. Always delegate large seeding to a Queueable.

2. **Native Data Seeding does not support Big Objects, Files, or Chatter** — These object types silently fail in Data Seeding templates. Use SFDMU or Apex scripts for these types.

3. **SandboxPostCopy runs as Automated Process user** — This user is not a named user and does not appear in audit logs as a standard user. Org-wide sharing rules apply, but profile-based field-level security does not. Be aware that seeded records may have visibility behavior that differs from named user-created records.

4. **Automations fire on seeded records by default** — Without explicit automation disable logic, triggers and flows execute on seeded records. This can cause unwanted data changes, platform event publishing, or email sends. Use native Data Seeding's automation-disable feature or write explicit disable/enable logic.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Reference data seeding strategy | Classification of objects by seed frequency with rationale |
| SandboxPostCopy class | Minimal class that enqueues the seeding Queueable |
| Seeding Queueable | Queueable chain handling all large-volume reference data seeding |
| Native Data Seeding template plan | Object selection, template type, and automation settings |

---

## Related Skills

- `devops/sandbox-refresh-and-templates` — Use for sandbox refresh mechanics, refresh intervals, and PII masking — the operational layer above data seeding strategy
- `data/deployment-data-dependencies` — Use for managing org-specific ID remapping in data records being deployed
- `data/data-seeding-for-testing` — Use for scratch org and CI pipeline test data seeding
