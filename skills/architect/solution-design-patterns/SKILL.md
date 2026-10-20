---
name: solution-design-patterns
description: "Use when selecting the right automation layer (Flow, Apex, LWC) for a new feature, reviewing an existing design for technical debt, or troubleshooting a mismatched automation architecture. Triggers: 'should I use Flow or Apex', 'declarative vs programmatic', 'which layer should handle this', 'automation design review', 'should I use LWC or standard components', 'is this over-engineered'. NOT for picking before-save Flow vs trigger vs invocable Apex on one record-save requirement — use admin/process-automation-selection. NOT for Custom Metadata vs Custom Settings, LWC vs Aura or Platform Events vs CDC — use architect/platform-selection-guidance."
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
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

Use this skill when choosing the right automation layer for a Salesforce requirement, reviewing an existing design for hidden complexity or technical debt, or troubleshooting a system that mixes automation tools in conflicting or redundant ways. This skill covers the structural decision-making layer — it does not replace role-specific skills for building individual features.

---

## Before Starting

- **What is the trigger type?** User-initiated action, record save (before/after), scheduled time, or external platform event?
- **Does the use case call an external system on record save?** "By default, callouts aren't allowed after DML operations in the same transaction" (apexdev 264 L35611) — in Apex as well as Flow; Apex triggers must make the callout asynchronously (L15104-15106). Corrected 2026-10-20: the old text said this "alone forces Apex" for a same-transaction callout, which no layer can make.
- **What automation already exists on this object?** Overlapping record-triggered Flows and Apex triggers on the same object execute in a defined order (apexdev 264 L15643-15673); that they share one set of governor limits is UNVERIFIED (2026-10-20). Know what is already there.
- **Who will maintain this?** A team of admins maintaining Flow is a different risk profile from a developer team owning Apex. The right tool depends partly on who will own it.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Does any step call an external system when a record saves? | Gotcha 2: no callout after uncommitted DML | An async path (Queueable/`@future`) designed in |
| What already runs on this object, in Flow and Apex? | Gotcha 3: both draw on the same transaction | One owner per event, a combined query budget |
| How many records can one loop in the Flow touch? | Gotcha 5: per-interview element ceiling | Loop sizing, or a move to Apex |
| Is configuration read repeatedly in one transaction? | Gotcha 4: caching behaviour is unverified | One read, held in memory |
| Are Process Builders or workflow rules still active? | Gotcha 6: they still fire | A migration list before new build |
| Who maintains the result — admins or developers? | Layered model: maintainability first | The layer the team can own |
| Are any IDs or thresholds hard-coded? | Future-proofing principle 1 | CMDT or labels instead |

A proper configuration picks the layer from the requirement and the owning team, where "just doing it" picks the layer the builder knows and pays for it at the first callout or limit.

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
- A single Flow interview can execute up to 2,000 elements (UNVERIFIED (2026-10-20): no Flow limits table in the corpus).
- An org can have up to 50 active autolaunched Flows (not including Screen Flows) (UNVERIFIED (2026-10-20)).
- Record-Triggered Flows run in the same transaction as the triggering DML operation — before-save Flows run before the record is committed; after-save Flows run after.
- No layer can call out after the record's uncommitted DML (apexdev 264 L35611); move the callout to an asynchronous path.

### When to Use Apex

Escalate to Apex when Flow cannot satisfy the requirement:

- **Callouts with custom handling:** a callout triggered by a save must be asynchronous in Apex too (apexdev 264 L15104-15106); Apex `@future(callout=true)` or Queueable Apex runs it in a later transaction — not the same one.
- **Complex data transformation:** Multi-step conditional logic involving more than a few objects, especially if intermediate values cannot be easily expressed in Flow formulas, is cleaner and more testable in Apex.
- **Bulk processing:** Apex is designed with bulkification in mind. While Flow handles bulk scenarios, Apex gives explicit control over collection processing, chunked DML, and SOQL optimization.
- **Bypass record trigger limits:** Apex triggers can set static boolean flags to prevent re-entrant execution — a common pattern when the same record is touched multiple times in one transaction.
- **Cross-object logic that exceeds Flow's subflow depth:** Deeply nested subflow hierarchies become hard to debug. If the logic requires the same level of composition as a class hierarchy, use Apex.
- **Custom metadata-driven routing:** Flow can read Custom Metadata, but complex branching based on CMDT values (routing rules with nested conditions) is easier to unit test in Apex.

**Apex trigger order of execution (simplified, per record save — apexdev 264 L15643-15681):**
1. System validation (required fields, field formats)
2. Before-save record-triggered Flows (step 3)
3. Before Apex triggers (step 4)
4. System validation again plus custom validation rules (step 5), duplicate rules (step 6)
5. Record saved to database, not yet committed (step 7)
6. After Apex triggers (step 8)
7. Assignment, auto-response, workflow rules (steps 9-11), escalation rules (step 12), Process Builder (step 13)
8. After-save record-triggered Flows (step 14), then entitlement rules (step 15)

Corrected 2026-10-20: the old list put escalation rules after after-save Flows and omitted custom validation and duplicate rules.

This ordering matters when both Flow and Apex handle the same object: a before-save Flow fires before an Apex before trigger, so Flow field writes are visible to the Apex before trigger.

### When to Use LWC

Add LWC when the standard Salesforce UI cannot deliver the user experience the requirement demands:

- **Rich interactive UI:** Real-time data refresh without page reload, drag-and-drop interfaces, custom data visualizations.
- **Reusable components:** A validated input widget, a shared layout, or a record card used across multiple pages.
- **Mobile support:** LWC is fully supported on Salesforce Mobile. Aura components are legacy and do not reliably support mobile features introduced after ~2021 (UNVERIFIED (2026-10-20)).
- **Integration with external APIs from the UI layer:** Display data from external systems without creating Salesforce records (data virtualization, mashups).

**LWC vs. Aura:** Aura is legacy. Do not create new Aura components. All net-new custom UI work should use LWC. Aura components and LWC can coexist — Aura can contain LWC, but LWC cannot contain Aura (UNVERIFIED (2026-10-20): the LWC guide is not in the corpus).

### Future-Proofing Principles

Regardless of layer chosen, apply these principles to avoid design rot:

1. **No hard-coded IDs.** Record IDs, user IDs, profile IDs, and queue IDs change between sandboxes and orgs. Store configurable values in Custom Labels or Custom Metadata Types (CMDT).
2. **Use Custom Metadata Types for configuration.** CMDT records are deployable and version-controllable; "All custom metadata is exposed in the application cache, which allows access without repeated queries to the database" (apexref 262 L204514-204515). Whether SOQL on CMDT counts against the SOQL limit is UNVERIFIED (2026-10-20). Use them for routing rules, threshold values, and feature flags.
3. **Do not use Process Builder for new automation.** Process Builder is scheduled for deprecation (UNVERIFIED (2026-10-20): retirement dates are Help/release-note only). Migrate existing Process Builders to Flow using the Migration Tool in Setup.
4. **Do not use Workflow Rules for new automation.** "Deprecated in Summer '23" and "no new Workflow Rules can be activated" are UNVERIFIED (2026-10-20); migrate remaining ones to Flow.
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
2. Does the logic require an HTTP callout on record save? → **Use Apex, asynchronously** (Queueable / `@future(callout=true)`; no layer calls out after uncommitted DML, apexdev 264 L35611).
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

## Recommended Workflow

1. Answer the Questions table and Mode 1 Step 1 (trigger type) for the requirement.
2. Inventory existing automation on the object (Flows, triggers, Process Builder, workflow) and map it to the order-of-execution steps above.
3. Apply the escalation criteria (Mode 1 Step 2); any save-time callout goes to an asynchronous path.
4. Run `python3 scripts/check_solution_design.py --manifest-dir force-app` (add `--strict` in CI) to find hard-coded IDs and legacy automation.
5. Record the decision in `templates/solution-design-patterns-template.md` and tick the Review Checklist.

---

## Review Checklist

- [ ] **Layer appropriateness:** Is each automation in the layer that matches its complexity? (e.g., a simple field default handled by Apex when a before-save Flow would suffice)
- [ ] **Single owner per event:** Is there one canonical owner for each trigger event on each object?
- [ ] **No Process Builder or Workflow Rules in use for new logic:** Legacy automation is present only as migration backlog, not as active new development.
- [ ] **No hard-coded IDs:** Grep the org's Flows and Apex for embedded 15- or 18-character Salesforce IDs. Every one is a deployment risk.
- [ ] **Custom Metadata for config:** Routing rules, feature flags, thresholds — are they in CMDT or in hard-coded values?
- [ ] **LWC over Aura:** Any new component work uses LWC. Existing Aura components have a documented migration plan.
- [ ] **Flow interview element count:** Are any individual Flows approaching the 2,000-element interview limit (UNVERIFIED (2026-10-20))? (check Flow debug logs or increase Element Count in Setup)
- [ ] **Apex trigger framework:** Are triggers bulkified? Is there a handler class pattern preventing logic from living directly in the trigger file?

---

## Mode 3: Troubleshoot an Automation Design Problem

Use this mode when an existing org has automation that behaves unexpectedly, fails intermittently, or produces governor limit errors.

### Diagnostic Questions

| Symptom | Likely cause | Where to look |
|---|---|---|
| Duplicate records created | Two automations react to the same `after insert` event | Setup → Flows + object's Apex triggers |
| Governor limit hit unexpectedly | Flow and Apex both perform SOQL in the same transaction | Debug log — check `LIMIT_USAGE_FOR_NS` entries (apexdev 264 L39324) |
| Field update from Flow overwritten by Apex | Before-save Flow (step 3) runs before the before trigger (step 4), so the trigger's write wins (apexdev 264 L15643-15644) | Give the field one owner. Corrected 2026-10-20: the old cause, "after-save Flow fires after Apex triggers", would make the Flow win |
| Automation works in sandbox but not production | Hard-coded IDs that differ between orgs | Search Flow conditions and Apex for literal record IDs |
| Process Builder action not firing | Process Builder is deprecated; active PBs may behave unpredictably | Migrate to Flow immediately |
| Callout error in Record-Triggered Flow | External callout attempted after the record's uncommitted DML (apexdev 264 L35611) | Move the callout to an async path (Queueable with callout) |
| Config value wrong in one org | Hard-coded in Apex or Flow formula | Move to Custom Metadata Type |

---

## Design Tradeoffs Reference

| Dimension | Flow | Apex | LWC |
|---|---|---|---|
| Maintainability | High — visual, admin-friendly | Medium — requires developer + test class | Lower — requires developer, DOM knowledge |
| Flexibility | Medium — constrained to available actions | High — full Salesforce API access | High — full DOM, JavaScript, Wire adapters |
| Testability | Medium — Flow tests (`FlowTest` metadata) verify record-triggered and autolaunched flows before activation (api_meta 264 L76698-76700); corrected 2026-10-20 from "no unit test framework" | High — full Apex test framework with assertions | Medium — Jest for unit, manual for integration |
| Deployability | Metadata API / Change Sets | Metadata API / Change Sets | Metadata API / Change Sets |
| Governor limit transparency | Low — limits drawn in the same transaction as Apex (sharing UNVERIFIED (2026-10-20)), less visible | High — explicit bulkification patterns | N/A for UI layer |
| Mobile support | Full (Screen Flow on Mobile) | N/A (server-side) | Full (LWC) / Partial (Aura — legacy) |

---

## Related Skills

- `flow/` skills — for building specific Flow types (record-triggered, screen, scheduled)
- `apex/trigger-framework` — for Apex trigger architecture and bulkification
- `apex/custom-metadata-in-apex` — for CMDT-driven configuration patterns
- `apex/callouts-and-http-integrations` — for asynchronous callout design
- `lwc/` skills — for component authoring and Lightning Data Service
