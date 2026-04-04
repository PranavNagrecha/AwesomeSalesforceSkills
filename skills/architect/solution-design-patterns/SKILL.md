---
name: solution-design-patterns
description: "Use when selecting the right automation layer (Flow, Apex, LWC) for a new feature, reviewing an existing design for technical debt, or troubleshooting a mismatched automation architecture. Triggers: 'should I use Flow or Apex', 'declarative vs programmatic', 'which layer should handle this', 'automation design review', 'should I use LWC or standard components', 'is this over-engineered'. NOT for individual feature design (use role-specific skills), NOT for detailed Apex implementation (use apex/ skills), NOT for LWC component authoring (use lwc/ skills), NOT for Flow-specific build steps (use flow/ skills)."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Scalability
  - Operational Excellence
  - Reliability
tags:
  - solution-design
  - automation-layers
  - declarative-vs-programmatic
  - flow
  - apex
  - lwc
  - architecture-decision
  - design-patterns
  - clicks-before-code
triggers:
  - "should I use Flow or Apex for this automation requirement"
  - "when does declarative automation stop being enough and I need code"
  - "my org has automation in Flow and Apex doing the same thing — is that a problem"
  - "how do I decide between LWC and a standard Lightning component"
  - "I want to design a solution that is maintainable long-term — where do I start"
  - "we are migrating off Process Builder and Workflow Rules — what replaces them"
  - "which automation tool should handle our lead routing logic"
inputs:
  - "Feature or business requirement being designed (what should happen and when)"
  - "Object(s) involved and expected data volumes"
  - "User-initiated vs. record-triggered vs. scheduled vs. platform-event-driven execution"
  - "Whether external system callouts are required in the same transaction"
  - "Existing automation already present on the object (triggers, flows, process builders)"
  - "Team skill set: admin-heavy vs. developer-heavy"
outputs:
  - "Recommended automation layer with explicit reasoning for the choice"
  - "Callout of anti-patterns present or at risk in the proposed design"
  - "Escalation criteria — when to move from declarative to programmatic"
  - "Future-proofing guidance (Custom Metadata, avoid hard-coded IDs)"
  - "Migration path recommendation when replacing legacy automation (Process Builder, Workflow Rules)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

Use this skill when choosing the right automation layer for a Salesforce requirement, reviewing an existing design for hidden complexity or technical debt, or troubleshooting a system that mixes automation tools in conflicting or redundant ways. This skill covers the structural decision-making layer — it does not replace role-specific skills for building individual features.

---

## Before Starting

- **What is the trigger type?** User-initiated action, record save (before/after), scheduled time, or external platform event?
- **Does the use case require a same-transaction HTTP callout?** Callouts after record save are not allowed from Flow. This alone forces Apex.
- **What automation already exists on this object?** Overlapping record-triggered Flows and Apex triggers on the same object share governor limits and execute in a defined order. Know what is already there.
- **Who will maintain this?** A team of admins maintaining Flow is a different risk profile from a developer team owning Apex. The right tool depends partly on who will own it.

---

## Core Concepts

### The Layered Automation Model

Salesforce provides three primary automation layers. They form a hierarchy: start at the top and only drop to a lower layer when the requirements genuinely cannot be met at the current layer.

```
Flow (declarative)
   ↓ escalate only when Flow cannot satisfy the requirement
Apex (programmatic logic)
   ↓ escalate only when Apex alone cannot handle the UI requirement
LWC (custom user interface)
```

**This is not a ranking of capability — it is a ranking of maintainability and blast radius.** Flow changes are deployable by trained admins and visible in a visual interface. Apex changes require code review, test classes, and deployment pipelines. LWC adds DOM rendering complexity. Each step down adds specialization and maintenance cost.

### When to Use Flow

Use Flow when:

- **User-initiated:** Screen Flows handle form-like processes (onboarding wizards, guided data entry, case intake).
- **Record-triggered:** Record-Triggered Flows handle before-save field updates, after-save record creation, and automated notifications.
- **Scheduled:** Scheduled Flows and Scheduled Paths in Record-Triggered Flows handle time-based automation (follow-up tasks, SLA escalation, batch email sends).
- **Subflows:** Complex logic can be modularized using subflows — a declarative equivalent of method composition.
- **The team is admin-led:** Flow is the right default when the maintenance team is certified admins without deep Apex experience.

**Flow governor limits to know:**
- A single Flow interview can execute up to 2,000 elements.
- An org can have up to 50 active autolaunched Flows (not including Screen Flows).
- Record-Triggered Flows run in the same transaction as the triggering DML operation — before-save Flows run before the record is committed; after-save Flows run after.
- Flow cannot make synchronous HTTP callouts after a record save. Use Platform Events or Apex if a same-transaction callout is required.

### When to Use Apex

Escalate to Apex when Flow cannot satisfy the requirement:

- **Same-transaction REST callouts:** Flow cannot make HTTP callouts in after-save context. Apex `@future(callout=true)` or Queueable Apex with callout support handles this.
- **Complex data transformation:** Multi-step conditional logic involving more than a few objects, especially if intermediate values cannot be easily expressed in Flow formulas, is cleaner and more testable in Apex.
- **Bulk processing:** Apex is designed with bulkification in mind. While Flow handles bulk scenarios, Apex gives explicit control over collection processing, chunked DML, and SOQL optimization.
- **Bypass record trigger limits:** Apex triggers can set static boolean flags to prevent re-entrant execution — a common pattern when the same record is touched multiple times in one transaction.
- **Cross-object logic that exceeds Flow's subflow depth:** Deeply nested subflow hierarchies become hard to debug. If the logic requires the same level of composition as a class hierarchy, use Apex.
- **Custom metadata-driven routing:** Flow can read Custom Metadata, but complex branching based on CMDT values (routing rules with nested conditions) is easier to unit test in Apex.

**Apex trigger order of execution (simplified, per record save):**
1. System validation rules (required fields, field type enforcement)
2. Before-save record-triggered Flows
3. Before Apex triggers
4. Record saved to database (in memory — not yet committed)
5. After Apex triggers
6. Assignment rules, auto-response rules, workflow rules (legacy — do not add new)
7. After-save record-triggered Flows
8. Escalation rules, entitlement rules

This ordering matters when both Flow and Apex handle the same object: a before-save Flow fires before an Apex before trigger, so Flow field writes are visible to the Apex before trigger.

### When to Use LWC

Add LWC when the standard Salesforce UI cannot deliver the user experience the requirement demands:

- **Rich interactive UI:** Real-time data refresh without page reload, drag-and-drop interfaces, custom data visualizations.
- **Reusable components:** A validated input widget, a shared layout, or a record card used across multiple pages.
- **Mobile support:** LWC is fully supported on Salesforce Mobile. Aura components are legacy and do not reliably support mobile features introduced after ~2021.
- **Integration with external APIs from the UI layer:** Display data from external systems without creating Salesforce records (data virtualization, mashups).

**LWC vs. Aura:** Aura is legacy. Do not create new Aura components. All net-new custom UI work should use LWC. Aura components and LWC can coexist — Aura can contain LWC, but LWC cannot contain Aura.

### Future-Proofing Principles

Regardless of layer chosen, apply these principles to avoid design rot:

1. **No hard-coded IDs.** Record IDs, user IDs, profile IDs, and queue IDs change between sandboxes and orgs. Store configurable values in Custom Labels or Custom Metadata Types (CMDT).
2. **Use Custom Metadata Types for configuration.** CMDT records are deployable, queryable without SOQL limits (cached after first access), and version-controllable. Use them for routing rules, threshold values, and feature flags.
3. **Do not use Process Builder for new automation.** Process Builder is scheduled for deprecation. Migrate existing Process Builders to Flow using the Migration Tool in Setup.
4. **Do not use Workflow Rules for new automation.** Workflow Rules were deprecated in Summer '23. No new Workflow Rules can be activated; all remaining ones should be migrated to Flow.
5. **One automation owner per trigger event.** Avoid a pattern where a Record-Triggered Flow and an Apex trigger both react to the same `after insert` event on the same object doing similar things. This creates hidden coupling and makes execution order non-obvious.

---

## Mode 1: Design a Solution from Scratch

Use this mode when a new feature or requirement needs a recommended automation approach before any build starts.

### Step 1 — Classify the trigger type

| Trigger | Recommended starting layer |
|---|---|
| User clicks a button or completes a form | Screen Flow |
| Record is created or updated | Record-Triggered Flow (before or after save) |
| Time passes since a record event | Scheduled Path in Record-Triggered Flow |
| Nightly or scheduled batch job | Scheduled Flow or Scheduled Apex |
| Platform Event received | Apex trigger on the platform event (or Flow if logic is simple) |
| External system pushes data | Apex REST endpoint (custom REST API via `@RestResource`) |

### Step 2 — Apply the escalation criteria

Ask each question in order. Stop at the first "yes":

1. Can the logic be expressed entirely with Flow formulas and standard actions? → **Use Flow.**
2. Does the logic require a same-transaction HTTP callout? → **Use Apex.**
3. Does the logic require bulk-safe processing of more than ~200 records in one transaction with explicit governor limit control? → **Use Apex.**
4. Does the logic require a custom UI that standard components cannot provide? → **Use LWC (backed by Apex if data access is needed).**
5. Can the custom UI use Lightning Data Service for reads and standard actions for writes? → **Use LWC without Apex.**

### Step 3 — Apply future-proofing checks

- Are any IDs, thresholds, or routing values hard-coded? Move them to CMDT.
- Does this automation duplicate anything already on the object? Check Setup → Process Automation → Flows and the object's Apex triggers.
- Does the team have the skills to maintain the chosen layer? If not, choose the higher layer or plan training.

---

## Mode 2: Review an Existing Design

Use this mode when reviewing a design document, a completed build, or an inherited org for design quality.

#
## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

- [ ] **Layer appropriateness:** Is each automation in the layer that matches its complexity? (e.g., a simple field default handled by Apex when a before-save Flow would suffice)
- [ ] **Single owner per event:** Is there one canonical owner for each trigger event on each object?
- [ ] **No Process Builder or Workflow Rules in use for new logic:** Legacy automation is present only as migration backlog, not as active new development.
- [ ] **No hard-coded IDs:** Grep the org's Flows and Apex for embedded 15- or 18-character Salesforce IDs. Every one is a deployment risk.
- [ ] **Custom Metadata for config:** Routing rules, feature flags, thresholds — are they in CMDT or in hard-coded values?
- [ ] **LWC over Aura:** Any new component work uses LWC. Existing Aura components have a documented migration plan.
- [ ] **Flow interview element count:** Are any individual Flows approaching the 2,000-element interview limit? (check Flow debug logs or increase Element Count in Setup)
- [ ] **Apex trigger framework:** Are triggers bulkified? Is there a handler class pattern preventing logic from living directly in the trigger file?

---

## Mode 3: Troubleshoot an Automation Design Problem

Use this mode when an existing org has automation that behaves unexpectedly, fails intermittently, or produces governor limit errors.

### Diagnostic Questions

| Symptom | Likely cause | Where to look |
|---|---|---|
| Duplicate records created | Two automations react to the same `after insert` event | Setup → Flows + object's Apex triggers |
| Governor limit hit unexpectedly | Flow and Apex both perform SOQL in the same transaction | Debug log — check `LIMIT_USAGE_FOR_NS` entries |
| Field update from Flow overwritten by Apex | Execution order misunderstood; after-save Flow fires after Apex triggers | Review order of execution; move one to before-save |
| Automation works in sandbox but not production | Hard-coded IDs that differ between orgs | Search Flow conditions and Apex for literal record IDs |
| Process Builder action not firing | Process Builder is deprecated; active PBs may behave unpredictably | Migrate to Flow immediately |
| Intermittent timeout in Record-Triggered Flow | External callout attempted from Flow after record save | Flow cannot callout after save — move to Apex Queueable with callout |
| Config value wrong in one org | Hard-coded in Apex or Flow formula | Move to Custom Metadata Type |

---

## Design Tradeoffs Reference

| Dimension | Flow | Apex | LWC |
|---|---|---|---|
| Maintainability | High — visual, admin-friendly | Medium — requires developer + test class | Lower — requires developer, DOM knowledge |
| Flexibility | Medium — constrained to available actions | High — full Salesforce API access | High — full DOM, JavaScript, Wire adapters |
| Testability | Limited — Flow tests via debug run; no unit test framework | High — full Apex test framework with assertions | Medium — Jest for unit, manual for integration |
| Deployability | Metadata API / Change Sets | Metadata API / Change Sets | Metadata API / Change Sets |
| Governor limit transparency | Low — limits are shared, less visible | High — explicit bulkification patterns | N/A for UI layer |
| Mobile support | Full (Screen Flow on Mobile) | N/A (server-side) | Full (LWC) / Partial (Aura — legacy) |

---

## Related Skills

- `flow/` skills — for building specific Flow types (record-triggered, screen, scheduled)
- `apex/trigger-framework` — for Apex trigger architecture and bulkification
- `apex/custom-metadata-in-apex` — for CMDT-driven configuration patterns
- `apex/callouts-and-http-integrations` — for same-transaction callout design
- `lwc/` skills — for component authoring and Lightning Data Service
