---
name: technical-debt-assessment
description: "Use when auditing a Salesforce org for technical debt: dead code, unused automations, overlapping Flow and Apex triggers, deprecated features, configuration complexity, and legacy patterns. Triggers: technical debt review, org health check, dead code analysis, automation overlap, deprecated features, complexity audit, audit our org for technical debt. NOT for actually deleting the unused fields, inactive Flow versions and old workflow rules — use admin/org-cleanup-and-technical-debt. NOT for a security-specific review — use architect/security-architecture-review."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
tags:
  - technical-debt
  - org-health
  - dead-code
  - automation-overlap
  - architect
inputs:
  - Org type and approximate age (how long it has been in production)
  - List of Salesforce features in use (approximate)
  - Known pain points or areas of concern
outputs:
  - Technical debt findings report with severity ratings
  - Prioritized remediation backlog
  - Complexity hotspot map
triggers:
  - "how do I find technical debt in my Salesforce org"
  - "dead code and unused apex classes"
  - "overlapping flow and trigger automation"
  - "deprecated process builder flows to migrate"
  - "org health check before a major project"
  - "complexity audit for salesforce automation"
  - "audit our org for technical debt and give me a prioritized remediation backlog"
  - "find Apex classes nobody calls before we delete them"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

Use this skill when auditing a Salesforce org to identify and document technical debt across automation, code, data model, security configuration, and integrations. This skill produces a structured findings report with severity ratings and a prioritized remediation backlog. It does not implement fixes — use domain-specific skills (apex/, flow/, security/, integration/) for remediation work.

---

## Before Starting

Gather this context before conducting the assessment:

- **How old is this org, and when was it last audited?** Older orgs accumulate more automation strata and legacy patterns.
- **What features are actively in use?** Apex, Flow, Process Builder, Workflow Rules, Aura components, integrations — each area is a debt category.
- **Are there known pain points?** "Automation keeps firing twice on Case" or "deployments break tests" are symptoms that guide where to look first.
- **What is the managed package footprint?** Managed package components create debt you cannot modify. Note them separately — they are vendor debt, not org debt.
- **What is the scope?** A full org audit, a targeted automation review, or a pre-release health check each require different depth.

---

## Questions to Ask Before Configuring

Ask these before running a single query. Each one traces to a gotcha in `references/gotchas.md`; skipping it produces a backlog full of findings nobody can act on.

| Question | Why it matters | What a good answer adds | What a proper assessment adds over just doing it |
|---|---|---|---|
| "Which namespaces belong to managed packages, and which code is ours?" | Managed package Apex is excluded from org coverage and cannot be edited (Gotcha 4) | A namespace allow-list that splits org debt from vendor debt | The backlog only holds items the team can fix; vendor debt goes to the package owner |
| "When did the full local test suite last run, and can we run it now?" | Coverage is stale until tests rerun (Gotcha 5) | A fresh test-run ID and timestamp to quote beside every coverage figure | "0% coverage" findings are real, not artifacts of a stale run |
| "Do we have Event Monitoring (Shield or the add-on)?" | Trigger execution evidence and old-API-version evidence both come from event log files (Gotchas 7 and 10) | Observed "last fired" data instead of inference | "Dead trigger" and "retired API client" findings are proven, not guessed |
| "Which external systems call Salesforce APIs, and on which API version?" | Versions 30.0 and below already return `410 GONE` (Gotcha 7) | An integration inventory with versions and owners | Critical integration findings land before the next retirement release, not after the outage |
| "Which objects still have active Workflow Rules or processes beside flows or triggers?" | Legacy layers re-fire update triggers and run in no guaranteed order (Gotchas 2, 8, 9) | A per-object automation list to build the overlap matrix from | Overlap is rated by real consequence (double trigger runs, last-writer-wins), not by count |
| "Is any Apex invoked by name at runtime (`Type.forName`, class names in Custom Metadata, scheduled jobs)?" | The Dependency API misses dynamic references and truncates at 2,000 rows (Gotchas 3 and 6) | A list of dynamic entry points to exclude from deletion | No "dead" class is deleted that a scheduled job or configuration record still calls |

What a proper assessment adds over "just running a scanner": every finding carries its evidence source and freshness, vendor debt is separated from owned debt, and each Critical item names the platform behavior that makes it Critical.

---

## Core Concepts

### What Technical Debt Means in Salesforce

Technical debt in a Salesforce org falls into six categories:

1. **Dead code** — Apex classes with no test coverage, classes never referenced in metadata or by other code, triggers on objects with no active DML paths.
2. **Unused and redundant automation** — Inactive Flow versions that were never cleaned up, Process Builder flows left over from pre-Summer '22, Workflow Rules that were never migrated when the retirement deadline passed. UNVERIFIED (2026-10-03): the Summer '22 cut-off and the Workflow Rule retirement deadline are Help-only claims not confirmed in this pass.
3. **Automation overlap** — The same object triggering both a Record-Triggered Flow and an Apex trigger for similar operations, creating double-execution risk, ordering surprises, or governor limit contention.
4. **Deprecated features in active use** — Workflow Rules and Process Builder executing live logic despite official deprecation; Aura components owned by the org team rather than migrated to LWC.
5. **Configuration complexity** — Formula fields referencing deleted fields, validation rules that are tautologies (always-true or always-false), duplicate objects or fields serving the same purpose.
6. **Integration and security debt** — Hardcoded endpoint URLs, deprecated API versions below v50.0, Named Credential gaps, and overly broad permission grants.

### Severity Model

Use a consistent four-tier model for all findings:

| Severity | Definition |
|---|---|
| Critical | Poses immediate system stability, compliance, or data integrity risk. Requires urgent attention. |
| High | Actively degrades maintainability, causes intermittent failures, or will block future work. Fix within the next sprint cycle. |
| Medium | Technical hygiene: increases noise, slows developers, or creates future risk if left unaddressed. Fix within the next quarter. |
| Low | Cosmetic or minor: undescriptive names, minor duplication, low-impact patterns. Fix as a housekeeping exercise. |

### Remediation Ownership

Pair each finding with the recommended owner role:

| Owner | Remediation type |
|---|---|
| Admin | Configuration-level changes (deactivating flows, cleaning up permission sets, removing unused fields). |
| Developer | Code changes (deleting dead Apex, refactoring complex triggers, resolving automation overlap). |
| Architect | Structural decisions (consolidating duplicate objects, redesigning automation strategy, planning migration from Workflow Rules to Flow). |
| Release Manager | Deployment-related debt (hardcoded IDs, broken metadata dependencies, stale package versions). |

---

## Mode 1: Full Technical Debt Assessment (Fresh Org Audit)

Use this mode for a comprehensive review of an org with no recent audit history.

### Step 1 — Dead Code Detection

**Apex classes with 0% test coverage:**
- Run `sf apex run test --test-level RunLocalTests --code-coverage --result-format json` (the current form of the legacy `sfdx force:apex:test:run` command, per the Salesforce CLI Command Reference) and examine per-class coverage in the results. Coverage is stale until tests rerun, so run this first.
- Any Apex class with 0 covered lines and 0 uncovered lines is a candidate — it is either untested or unreferenced.
- Any class with coverage lines but 0 covered lines has tests that never exercise it — either the tests are bypassing the class or the class is dead.

**Apex classes never referenced in metadata:**
- Download the full metadata set (SFDX retrieve or Metadata API retrieve).
- Search Flow metadata XML files, custom object metadata, and other .cls files for references to each class name.
- Classes with no inbound references from other Apex, Flows, or LWC `@wire` calls are deletion candidates.
- Exception: scheduled Apex jobs reference class names dynamically — check the Scheduled Jobs list in Setup.

**Apex triggers on objects with no active DML:**
- An Apex trigger on an object that receives no writes in production (no insert, update, or delete) adds overhead without benefit.
- UNVERIFIED (2026-10-03): earlier text pointed at an "Apex Trigger Manager in Setup" for the last execution timestamp; no fetched Salesforce guide documents such a page. The documented evidence source is the `EventLogFile` Apex Trigger event type (Object Reference), which needs Event Monitoring.
- Cross-reference with the object's record count and last-modified-date statistics.

### Step 2 — Unused Automation Inventory

**Inactive Flow versions:**
- Each time a Flow is saved, Salesforce creates a new version. UNVERIFIED (2026-10-03): earlier text said inactive versions consume an org-wide "2,000 Flow version limit"; the flow limits page is Help-only and the library also carries a conflicting 50-versions-per-flow figure (see `references/gotchas.md` Gotcha 1).
- Go to Setup → Flows → filter by Inactive status. Large counts of inactive versions for the same flow are a housekeeping finding.
- Document the count of inactive versions per flow and flag any flow with more than 5 inactive versions.

**Process Builder flows (legacy):**
- UNVERIFIED (2026-10-03): earlier text said no new Process Builder flows have been activatable since Summer '22; the retirement timeline is published only in Salesforce Help. Any active Process Builder flow is executing legacy automation either way. In the Tooling API `Flow` object these have `ProcessType = 'Workflow'`.
- Go to Setup → Process Builder. Any active flow is a migration candidate.
- Active Process Builder flows that overlap with existing Record-Triggered Flows on the same object are Critical findings.

**Workflow Rules (legacy):**
- Workflow Rules were formally deprecated with a migration deadline. Any Workflow Rule still active is a migration risk. UNVERIFIED (2026-10-03): the deadline and the claim that Salesforce can enforce retirement at any release are Help-only and were not confirmed in this pass.
- Go to Setup → Workflow Rules. Export the full list. Flag all active rules.
- Workflow Rule field updates can conflict silently with after-save Flow updates on the same field.

### Step 3 — Automation Overlap Analysis

For each object with more than one active automation type, assess overlap risk:

1. List all active automations per object: Record-Triggered Flows, Apex triggers, Process Builder, Workflow Rules.
2. For each pair of automations on the same object, answer:
   - Do they both respond to the same trigger event (before insert, after update, etc.)?
   - Do they write to any of the same fields?
   - Do they both send emails, create tasks, or create records of the same type?
3. Any "yes" to the above is an overlap finding. Rate severity by consequence:
   - Both write the same field → **Critical** (last writer wins; result is non-deterministic depending on execution order)
   - Both create the same related record type → **High** (duplicate records in production)
   - Both send email alerts for the same event → **Medium** (user experience degradation)

**Known automation execution order (simplified from the Apex Developer Guide, "Triggers and Order of Execution"; step numbers are the guide's):**
1. Step 3: before-save Record-Triggered Flows
2. Step 4: before Apex triggers
3. Steps 5–7: validation, duplicate rules, record saved but not committed
4. Step 8: after Apex triggers
5. Step 11: Workflow Rules (legacy). A Workflow field update re-runs before update and after update triggers one more time.
6. Step 13: processes built with Process Builder and flows launched by workflow rules, in no guaranteed order
7. Step 14: after-save Record-Triggered Flows

A before-save Flow writing a field and an Apex after trigger reading that same field will see the Flow-written value. This is intentional — but it must be documented, because it is not obvious to a developer reading only the Apex code. Because the after-save Flow runs after processes, a "replacement" Flow overwrites whatever a still-active process wrote to the same field.

### Step 4 — Deprecated Features Inventory

| Feature | Status | Finding |
|---|---|---|
| Workflow Rules | Deprecated — no new activations; existing rules still execute | Migration to Record-Triggered Flow is required |
| Process Builder | Deprecated — no new flows since Summer '22 (UNVERIFIED 2026-10-03, Help-only); existing flows still execute, at order-of-execution step 13 in no guaranteed order | Migration to Record-Triggered Flow is required |
| Aura components (org-owned) | Legacy — supported but not receiving new features; LWC is the current standard | Migration to LWC for any component that will receive future enhancements |
| Legacy API versions (below v50.0) | Versions 21.0–30.0 were retired in Summer '25 and return `410 GONE` (REST API Developer Guide, "API End-of-Life Policy"); v50.0 is this skill's planning threshold, not a platform boundary | Upgrade integration endpoints to current API version; treat 30.0 and below as Critical |

### Step 5 — Complexity Indicators

Flag the following as complexity hotspots:

| Hotspot | Why it matters |
|---|---|
| Apex classes with cyclomatic complexity > 20 | Use a static analysis tool (PMD, CodeScan) or review manually for method-level branching density. High complexity = high maintenance cost and high bug introduction risk. |
| Flows with more than 50 elements | 50+ element Flows are difficult to read, debug, and test. Candidates for subflow decomposition. UNVERIFIED (2026-10-03): earlier text cited a "2,000-element interview limit"; no fetched guide states it. |
| Nested subflows more than 3 levels deep | Subflow chains that go 4+ levels deep become effectively unreadable in the Flow Builder canvas. Refactor using Invocable Actions backed by Apex, or flatten the logic. |
| Apex trigger files that contain business logic directly | Logic embedded in trigger files (not delegated to handler classes) cannot be unit tested in isolation. This is both a debt and a test coverage risk. |
| Formula fields referencing fields that no longer exist | These produce runtime errors or display `#Error!` in the UI. Identifiable via Setup → Schema Builder or a metadata scan for broken references. |

### Step 6 — Security Debt Indicators

These are not full security findings (use `security-architecture-review` for that) but are indicators of accumulated access debt:

- Profiles with "View All Data" or "Modify All Data" granted to more users than strictly necessary.
- Permission sets with no assigned users — these are either unused (clutter) or documentation gaps (someone should be assigned).
- Apex classes running `without sharing` without inline documentation explaining why elevated access is needed.
- Validation rules with hard-coded user IDs, profile names, or role names — these are fragile and break on org changes.

### Step 7 — Integration Debt Indicators

- Hardcoded endpoint URLs in Named Credentials, Apex classes, or Custom Settings — any URL that is not parameterized will break when the endpoint changes.
- API version references below v50.0 in integration code — Salesforce API v50.0 corresponds to Winter '21. Versions 30.0 and below are already retired; Salesforce supports a version for at least 3 years and gives at least 1 year of notice before ending support (REST API Developer Guide, "API End-of-Life Policy").
- HTTP callouts using hardcoded credentials (username/password in Apex string literals) — a security and integration debt item.
- Named Credential records with no associated authentication provider — may be using legacy password auth instead of OAuth.

### Step 8 — Compile the Findings Report

Structure every finding as:

```
Area: [Dead Code | Automation | Deprecated Feature | Complexity | Security Config | Integration]
Finding: [One-sentence description of what was found]
Location: [Class name, Flow API name, object name, or Setup path]
Severity: [Critical | High | Medium | Low]
Remediation Effort: [Hours estimate or T-shirt size: XS/S/M/L/XL]
Recommended Owner: [Admin | Developer | Architect | Release Manager]
```

---

## Mode 2: Targeted Review of a Specific Area

Use this mode when the scope is narrowed to one category — automations, code, or data model.

### Targeted Automation Review

Focus: identify overlap and legacy automation on a specific object or business process.

1. Pull all automation for the target object from Setup.
2. Map each automation to its trigger event, field writes, and record creates/updates.
3. Draw (or tabulate) the execution sequence using the order of execution reference.
4. Flag any two automations that share a trigger event and share a write target.

### Targeted Code Review

Focus: identify dead, over-complex, or untested Apex in a specific domain.

1. Pull test coverage report filtered to the relevant namespace or class prefix.
2. Flag classes below 75% coverage (minimum for deployment) and classes at 0%.
3. Run PMD or equivalent static analysis for cyclomatic complexity on the class set.
4. Review trigger files for direct DML/SOQL (no handler delegation).

### Targeted Data Model Review

Focus: identify formula field errors, tautological validation rules, and duplicate objects.

1. Export all custom fields on the target object(s). Check formula fields for references to deleted or renamed fields.
2. Review validation rules: test each rule against a representative record to confirm it actually fires. Rules that never fire are either dead or incorrectly written.
3. Check for duplicate objects: objects with the same purpose introduced at different points in the org's history (e.g., `Custom_Order__c` and `Sales_Order__c` both storing order records).

---

## Mode 3: Pre-Release Health Check Before a Major Project

Use this mode before starting a significant feature build to understand the debt landscape that will affect the project.

### Pre-Release Checklist

- [ ] **Test coverage baseline:** Is the org at or above 75% overall Apex coverage? Deployments will fail if coverage drops below this. Identify the lowest-coverage classes in the project's domain.
- [ ] **Automation overlap on affected objects:** Are there active Process Builder flows or Workflow Rules on the objects the project will touch? These must be accounted for in the automation design.
- [ ] **Flow version headroom:** Are flows the project will extend carrying a long tail of obsolete versions? If so, clean them before adding new versions. UNVERIFIED (2026-10-03): the earlier "1,800 of 2,000" buffer rests on a limit no fetched source confirms; check the current Flow limits page in Salesforce Help.
- [ ] **API version currency:** Are the integration endpoints the project will use on API v56.0 or higher? If not, plan an upgrade alongside the build.
- [ ] **Hardcoded IDs on affected objects:** Are there hardcoded record IDs in Flows or Apex that reference records on the objects the project will touch? These may break during sandbox refresh or deployment.
- [ ] **Complexity budget:** Are the Apex classes and Flows the project will extend already at high complexity? If so, refactor before adding to them.

---

## Findings Report Format

The output of this skill is a structured findings report. Use the template in `templates/technical-debt-assessment-template.md`.

Key sections:

1. **Org Profile** — Age, size, team composition, last audit date.
2. **Automation Audit Summary** — Active vs. inactive counts per automation type; overlap risk matrix.
3. **Dead Code Summary** — Apex classes with low/zero coverage; unreferenced classes; stale triggers.
4. **Deprecated Features Inventory** — Active Process Builder flows, Workflow Rules, Aura components to migrate.
5. **Complexity Hotspots** — High-complexity Apex, oversized Flows, deep subflow chains.
6. **Security Config Indicators** — Broad permission grants, unused permission sets, `without sharing` classes.
7. **Integration Debt** — Hardcoded URLs, old API versions, credential gaps.
8. **Prioritized Remediation Backlog** — All findings sorted by Severity then Effort, with recommended owner.

---

## Related Skills

- `architect/solution-design-patterns` — for redesigning automation after debt is identified
- `apex/trigger-framework` — for remediating Apex trigger debt
- `flow/process-builder-to-flow-migration` and `flow/workflow-rule-to-flow-migration`: for rebuilding migrated Process Builder and Workflow Rule logic
- `admin/org-cleanup-and-technical-debt`: for executing the deletions this assessment recommends
- `architect/security-architecture-review`: for deep security posture review beyond indicators
- `standards/decision-trees/automation-selection.md`: for deciding what each overlapping automation should become

## Recommended Workflow

1. Ask the six questions in "Questions to Ask Before Configuring" and record the namespace allow-list, Event Monitoring status, and integration inventory before collecting any evidence.
2. Refresh the evidence: run the full local test suite with coverage, then run the Tooling API queries in `references/examples.md` (coverage aggregate, flow versions, active processes, dependency rows) and save the raw output with its timestamp.
3. Build the per-object automation matrix from the order of execution in Mode 1 Step 3, marking Workflow field-update re-fires and unordered processes explicitly.
4. Rate each finding with the severity model, splitting vendor debt (namespaced) from owned debt and marking inferred findings (no Event Monitoring data) as inferred.
5. Fill `templates/technical-debt-assessment-template.md`, then run `python3 skills/architect/technical-debt-assessment/scripts/check_technical_debt.py --project-dir <retrieved-project>` to catch stale Flow versions, deprecated API versions, hardcoded IDs, trigger bodies with inline logic, and assert-free tests.
6. Hand deletions to `admin/org-cleanup-and-technical-debt` and automation rebuilds to the flow migration skills; this skill stops at the prioritized backlog.

---

