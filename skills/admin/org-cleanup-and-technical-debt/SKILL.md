---
name: org-cleanup-and-technical-debt
description: "Use when executing admin-level cleanup in a Salesforce org: deleting unused fields, removing inactive Flow versions, deactivating legacy automation, running Salesforce Optimizer or Org Check, and performing destructive metadata deploys. Triggers: 'clean up unused fields', 'delete inactive flows', 'run Optimizer', 'org has too many custom fields', 'remove old workflow rules', 'Flow version limit'. NOT for assessing or reporting on technical debt (use architect/technical-debt-assessment). NOT for code-level refactoring or Apex cleanup (use apex/ skills)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
triggers:
  - "how do I clean up unused custom fields in my org"
  - "we are hitting the Flow version limit and need to delete inactive versions"
  - "what does Salesforce Optimizer recommend for my org"
  - "how do I safely remove old workflow rules and process builder flows"
  - "our org has too many custom objects and fields nobody uses"
  - "how do I do a destructive deploy to remove metadata from production"
tags:
  - org-cleanup
  - technical-debt
  - optimizer
  - unused-fields
  - flow-versions
  - destructive-deploy
  - metadata-hygiene
inputs:
  - List of metadata types targeted for cleanup (fields, flows, workflow rules, etc.)
  - Access to Setup or a metadata retrieve of the org
  - Confirmation of whether a sandbox-first approach is available
outputs:
  - Prioritized cleanup action plan with safe deletion order
  - Destructive manifest (destructiveChanges.xml) when metadata removal is needed
  - Post-cleanup validation checklist
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Org Cleanup And Technical Debt

Activate this skill when an admin needs to execute cleanup actions in a Salesforce org — removing unused fields, deleting inactive Flow versions, deactivating or migrating legacy automation, and deploying destructive changes. This skill covers the hands-on removal work. For assessment and reporting on what needs cleanup, use `architect/technical-debt-assessment`.

---

## Before Starting

Gather this context before performing any cleanup:

- **What metadata types are targeted?** Fields, Flows, Workflow Rules, Process Builder, custom objects, page layouts, or a mix. Each has different deletion mechanics and risk profiles.
- **Is there a sandbox available for testing deletions first?** Never delete metadata directly in production without verifying in a sandbox that nothing breaks. If no sandbox is available, document the risk explicitly.
- **Has an assessment already been done?** If the org has a technical debt findings report (from `architect/technical-debt-assessment` or Salesforce Optimizer), start from that list rather than re-discovering what to clean.
- **Who owns the metadata being removed?** Managed package components cannot be deleted by an admin — only the publisher can remove them. Confirm every target is unmanaged before planning deletion.

---

## Core Concepts

### Salesforce Optimizer

Salesforce Optimizer is a built-in tool (Setup > Optimizer) that scans the org and produces a report of unused, underperforming, or misconfigured metadata. Key capabilities:

- Identifies custom fields with no data populated across records.
- Flags inactive users consuming licenses.
- Detects validation rules, workflow rules, and other automation that may be redundant.
- Reports on features enabled but not actively used.

Optimizer runs inside the org — no installation needed. It produces a downloadable PDF report. Use this as the starting point for any cleanup initiative when no prior assessment exists.

### Field Usage and the Deleted Fields Queue

Salesforce does not permanently delete custom fields immediately. Deleted fields enter a 15-day recycle period during which they can be restored. After 15 days they are hard-deleted and the field slot is reclaimed.

Key limits:
- Each standard or custom object has a limit on custom fields per data type (e.g., 500 custom fields for most Enterprise Edition objects, 800 for Unlimited).
- Fields in the deleted queue still count toward the limit until hard-deleted.
- To reclaim slots immediately, go to Setup > Object Manager > [Object] > Fields & Relationships > Deleted Fields and click "Erase**.

Always check field usage (reports, list views, Flows, Apex, validation rules, page layouts) before deleting. A field with zero populated records may still be referenced in automation or code.

### Flow Version Limits and Cleanup

Each Flow in the org can accumulate many versions. The org-wide limit is 2,000 total active and inactive Flow versions (may vary by edition). Inactive versions serve no runtime purpose but consume the version count.

To delete inactive Flow versions: Setup > Flows > select the Flow > Versions tab > delete individual inactive versions. You cannot delete the currently active version or any version that was active within the last 24 hours.

Bulk deletion of Flow versions requires the Metadata API — either a destructive deploy or the Tooling API `DELETE` on `FlowDefinition` records.

### Destructive Deploys

A destructive deploy removes metadata from the target org. This is the only supported way to remove certain metadata types (like Apex classes, triggers, custom labels, or Lightning components) from production.

The process requires:
1. A `destructiveChanges.xml` manifest listing the components to remove.
2. A minimal `package.xml` (can be empty of members but must exist).
3. A deploy via Metadata API, SFDX CLI (`sf project deploy start --metadata`), or an equivalent tool.

Destructive deploys are irreversible once executed. Always test in a sandbox first.

---

## Common Patterns

### Pattern 1: Field Cleanup Sprint

**When to use:** The org has hundreds of custom fields with no data or references, and new field creation is being blocked by limits.

**How it works:**
1. Export field metadata using a describe call or Metadata API retrieve.
2. Cross-reference each field against: record data population (run a SOQL `SELECT COUNT(Id) FROM Object WHERE Field != null`), Flow references, Apex references, validation rule references, report references, and page layout placement.
3. Categorize fields into: (a) safe to delete — no data, no references; (b) data-only — has data but no automation references, confirm with stakeholders; (c) referenced — still in use, do not delete.
4. Delete category (a) fields in a sandbox first. Verify all tests pass, all Flows compile, and all reports render.
5. Deploy the same deletions to production using a destructive deploy or manual deletion.
6. Purge the deleted fields queue if field slots are needed immediately.

**Why not just delete in production directly:** A field referenced by a Flow or validation rule will cause a compile error when deleted. Salesforce will block the deletion in some cases, but not all — some references only fail at runtime.

### Pattern 2: Legacy Automation Deactivation and Removal

**When to use:** The org has active Workflow Rules or Process Builder flows that have been superseded by Record-Triggered Flows.

**How it works:**
1. Inventory active Workflow Rules (Setup > Workflow Rules) and active Process Builder flows (Setup > Process Builder).
2. For each legacy automation, confirm that a replacement Record-Triggered Flow exists and covers the same trigger event and actions.
3. Deactivate the legacy automation in a sandbox. Run regression tests.
4. If stable, deactivate in production. Leave the deactivated automation in place for 1-2 sprint cycles as a rollback safety net.
5. After the observation period, delete the deactivated automation via Setup or destructive deploy.

**Why not delete immediately:** Deactivating first gives a rollback path. If a replacement Flow missed an edge case, reactivating the old automation is faster than rebuilding it.

### Pattern 3: Flow Version Pruning

**When to use:** The org is approaching the 2,000 Flow version limit, or Flow management is cluttered with dozens of inactive versions per Flow.

**How it works:**
1. In Setup > Flows, sort by Status = Inactive. Note the Flow name and version number.
2. For each Flow, keep the currently active version and the most recent inactive version (as a rollback reference). Delete all older inactive versions.
3. For bulk cleanup, use the Tooling API or a destructive deploy targeting specific `Flow` versions by their API name and version number.
4. After cleanup, verify the active version of each Flow still runs correctly — version deletion does not affect the active version, but confirm anyway.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need to remove unused custom fields | Manual delete via Setup or destructive deploy | Fields enter a 15-day recycle queue; purge immediately if slot recovery is urgent |
| Need to remove Apex classes or triggers | Destructive deploy only | Apex cannot be deleted via Setup in production — Metadata API is required |
| Legacy Workflow Rules still active | Deactivate first, observe, then delete | Immediate deletion has no rollback; deactivation is reversible |
| Flow version count approaching 2,000 | Bulk-delete inactive versions via Tooling API | Manual deletion through Setup is feasible for small counts but impractical at scale |
| Managed package components are clutter | Do NOT delete — contact publisher or uninstall package | Admins cannot modify or remove managed package metadata |
| Unsure if a field is used | Run usage analysis before deleting | Check data population, automation references, report references, and page layouts |

---

## Recommended Workflow

Step-by-step instructions for an admin executing org cleanup:

1. **Run Salesforce Optimizer** — Go to Setup > Optimizer and generate a fresh report. Review the findings for unused fields, redundant automation, and underused features. If an `architect/technical-debt-assessment` report already exists, use that instead.
2. **Categorize cleanup targets** — Group findings into: fields, automation (Flows, Workflow Rules, Process Builder), code-dependent metadata (requires developer), and managed package items (cannot clean).
3. **Validate references for each target** — Before deleting any metadata, confirm it is not referenced by Flows, Apex, validation rules, reports, dashboards, or page layouts. Use the "Where is this used?" feature in Setup or run metadata searches.
4. **Test deletions in a sandbox** — Perform all planned deletions in a Full or Partial Copy sandbox. Run all Apex tests. Verify critical Flows execute without error. Confirm reports still render.
5. **Execute in production** — Deploy deletions to production using the same method tested in sandbox (manual Setup deletion, destructive deploy, or Tooling API). Schedule during a low-activity window.
6. **Purge and verify** — If field slots are needed, purge the deleted fields queue. Run Optimizer again to confirm the cleanup items are resolved. Document what was removed for audit purposes.
7. **Establish ongoing hygiene** — Set a quarterly calendar reminder to re-run Optimizer. Add field-description requirements to your change management process to prevent future accumulation of undocumented metadata.

---

## Review Checklist

Run through these before marking cleanup work complete:

- [ ] All targeted metadata confirmed as unreferenced before deletion (no orphaned Flow references, no broken validation rules, no report errors)
- [ ] Deletions tested in sandbox with full Apex test run passing
- [ ] Destructive deploy manifest reviewed by a second admin or developer before production execution
- [ ] Deleted fields queue purged if field limit recovery was the goal
- [ ] Legacy automation deactivated for an observation period before permanent deletion
- [ ] Post-cleanup Optimizer report generated showing resolved findings
- [ ] Cleanup actions documented (what was removed, when, by whom) for audit trail

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Deleted fields still count toward limits for 15 days** — Deleting a field does not immediately free the field slot. The field enters a recycle queue for 15 days. If you are deleting fields specifically to make room for new ones, you must also purge the deleted fields queue (Setup > Object Manager > [Object] > Deleted Fields > Erase). Failing to do this leads to confusion when the "Add Field" button still shows the limit as reached.

2. **Flow version deletion can fail silently for versions referenced by other Flows** — If a subflow element in another Flow references a specific version of a Flow (rare but possible in orgs that pin subflow versions), deleting that version will break the parent Flow at runtime without a compile-time error. Always test parent Flows after deleting subflow versions.

3. **Destructive deploys cannot be rolled back** — Once a destructive deploy succeeds, the metadata is gone from the target org. There is no "undo deploy" operation. The only recovery path is to re-deploy the component from source control or a prior metadata backup. If you do not have the component in source control, it is lost.

4. **Workflow Rule field updates can linger after deactivation** — Deactivating a Workflow Rule stops it from firing, but if the Workflow Rule had a time-dependent field update that was already queued before deactivation, that queued action will still execute. Check Setup > Time-Based Workflow to flush any pending actions before declaring the rule fully deactivated.

5. **"Where Is This Used?" in Setup is incomplete** — The dependency lookup in Setup does not cover all reference types. It misses references from: report formulas, dashboard filters, some Apex string references (e.g., `Schema.SObjectType.Account.fields.Custom_Field__c`), and certain Flow formula expressions. Always supplement Setup lookups with a metadata text search.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Cleanup action plan | Prioritized list of metadata to remove, grouped by type, with safe deletion order and method |
| destructiveChanges.xml | Metadata API manifest for removing components via destructive deploy |
| Post-cleanup validation report | Summary of test results, Optimizer re-run, and confirmation of resolved findings |

---

## Related Skills

- `architect/technical-debt-assessment` — use for assessing and reporting on technical debt before executing cleanup; produces the findings that this skill acts on
- `admin/change-management-and-deployment` — use for deploying cleanup changes through a governed release process
- `admin/sandbox-strategy` — use for selecting the right sandbox type to test cleanup before production
- `devops/destructive-changes-deployment` — use for detailed guidance on constructing and executing destructive metadata deploys
- `admin/custom-field-creation` — use for understanding field limits and data types when cleaning up fields
