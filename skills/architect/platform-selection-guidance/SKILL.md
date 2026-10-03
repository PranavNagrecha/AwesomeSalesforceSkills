---
name: platform-selection-guidance
description: "Use when choosing which Salesforce platform capability to use for a requirement — covering metadata storage (Custom Metadata vs Custom Settings vs Custom Objects), UI framework (LWC vs Aura), integration approach (Platform Events vs Change Data Capture vs Outbound Messaging), and data extension (OmniStudio vs standard automation). Triggers: custom metadata vs custom settings, LWC vs Aura, which salesforce feature to use, platform events vs change data capture, omnistudio vs flow, choose where to store configuration. NOT for automation-specific tool selection between Flow / Apex / Workflow (use admin/process-automation-selection) or for implementing the chosen platform feature."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
tags:
  - architect
  - platform-selection
  - custom-metadata
  - lwc
  - integration-patterns
inputs:
  - Business requirement or technical constraint to evaluate
  - Org edition and available licenses/add-ons
  - Team skill set (admin vs developer)
  - Long-term maintenance expectations
outputs:
  - Platform feature recommendation with rationale
  - Tradeoff comparison for top 2-3 candidate features
  - Risk factors for the recommended option
  - References to implementation skills for the chosen option
triggers:
  - "custom metadata vs custom settings which should I use"
  - "LWC vs Aura which framework should I use"
  - "platform events vs change data capture for integration"
  - "which salesforce feature should I use for this requirement"
  - "omnistudio vs flow vs lwc decision"
  - "choosing between salesforce platform capabilities"
  - "decide where to store routing thresholds so they deploy with the release"
  - "pick an event pattern to keep our ERP in sync with Salesforce changes"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-03
---

Use this skill when the question is which Salesforce platform feature or capability class should own a requirement — not which automation tool to use within the automation surface (see `admin/process-automation-selection` for Flow vs Apex vs Workflow decisions), and not how to implement the chosen feature. This skill covers the broader platform-level choice: how to store configuration data, which UI framework to use for new components, which integration pattern fits a given sync requirement, and whether OmniStudio is appropriate vs. standard Salesforce tooling.

The decisions here tend to have long life spans. Choosing Custom Settings instead of Custom Metadata Types means you will carry that deployment gap for years. Choosing Aura instead of LWC means you are working on a legacy framework. Getting these choices right at the outset dramatically reduces future rework.

---

## Before Starting

Gather this context before working through decision guidance:

- What is the org edition and what add-ons or licenses are active? (OmniStudio requires a license. CDC allows five selected entities without an add-on, and platform event delivery to external clients defaults to 50,000 events per 24 hours in Performance and Unlimited Editions and 25,000 in Enterprise, shared with CDC; add-ons raise both.)
- Who will maintain the result? Admins can deploy Custom Metadata records via change sets; Custom Objects require data migration scripts. LWC requires JavaScript skills; Aura is familiar to legacy teams but is a strategic dead end.
- What is the expected data volume and lifecycle? High-volume configuration with relationships belongs in Custom Objects, not Custom Metadata. Configuration that ships with your package belongs in Custom Metadata, not Custom Settings.
- Is there an existing implementation that is being replaced? If so, this skill covers the upgrade path assessment (Mode 3).

---

## Questions to Ask Before Configuring

Ask these before naming a feature. Each traces to a gotcha in `references/gotchas.md`.

| Question | Why it matters | What a good answer adds | What a proper design adds over just doing it |
|---|---|---|---|
| "Must this configuration arrive in every org through the release pipeline, or do people edit it in production?" | Custom settings data does not deploy; custom metadata records cannot be changed with DML (Gotchas 1 and 9) | The change path for the values, not just the schema | Configuration moves with the release, and runtime edits land in a store built for them |
| "Does any value differ by profile or user, or point at a specific record such as a queue?" | Only hierarchy custom settings vary by user; custom metadata cannot look up records (Gotcha 5) | The override levels and record references needed | No text-field IDs that break between orgs |
| "Is any value a secret?" | Unprotected custom settings are readable by every profile, including guest (Gotcha 7) | A list of values that belong in named credentials | Secrets never sit in readable configuration |
| "How do the components on the page talk to each other today?" | LWC cannot handle Aura application events; Lightning Message Service is the replacement (Gotcha 2) | The event chain to redesign before migrating | Migrations do not silently break event wiring |
| "How many external subscribers, how many events a day, and how long can each be offline?" | Retention is 24 or 72 hours for platform events and three days for CDC; delivery allocation is shared (Gotchas 3 and 10) | Event volume per subscriber against the allocation and retention | The pattern fits the limits, with a reconciliation path for long outages |
| "Is OmniStudio licensed here, and does the team know it?" | OmniStudio needs a licence and its data model differs from SOQL (Gotcha 4) | A yes/no on licence and skills | Guided processes use the tool the org can run and maintain |

What a proper selection adds over "just using the familiar feature": the choice is checked against deployment, security, test, and limit behavior that is hard to reverse later.

---

## Scope Boundary: Automation Tool Selection

This skill does **not** cover the choice between Flow, Apex, Process Builder, or Workflow Rules for automation requirements. That decision is fully covered by `admin/process-automation-selection`. If your question is "should this logic live in a Flow or an Apex trigger?" — stop here and use that skill instead.

This skill covers choices that sit *above* or *alongside* the automation layer: where to store configuration data the automation reads, which UI framework to use for the front-end surface, which integration pattern connects Salesforce to external systems, and whether OmniStudio is the right licensed add-on for a guided process.

---

## Mode 1: Feature Selection for a New Requirement

Use this mode when a new requirement is being designed and the team has not yet committed to a platform feature.

### Decision Area 1 — Metadata Storage: Custom Metadata vs Custom Settings vs Custom Objects

Use this framework when the requirement involves storing configuration data that automation, Apex, or flows will read at runtime.

| Criterion | Custom Metadata Types | Custom Settings (Hierarchy) | Custom Objects |
|---|---|---|---|
| Deployable via Metadata API / change sets | Yes — records deploy as metadata | No — data values must be seeded separately | No — requires data deployment scripts |
| Queryable in SOQL | Yes, and custom metadata queries do not count against the SOQL query limit | Yes (via `getInstance()` API; data is cached) | Yes |
| Available in formulas and validation rules | Yes | Yes (hierarchy type only) | No |
| User/profile-level overrides | No — org-level only | Yes — hierarchy types support org/profile/user overrides | No (requires relationship fields) |
| Volume ceiling | ~5,000 records per type practical limit (UNVERIFIED 2026-10-03) | ~5,000 records per list type (UNVERIFIED 2026-10-03) | Up to object storage limits (millions of rows) |
| Relationships to other objects | No lookup relationships | No lookup relationships | Full lookup and master-detail support |
| Audit trail | No (UNVERIFIED 2026-10-03) | No | Yes (if History Tracking enabled) |
| Package-able | Yes (type and records) | Yes, the setting definition (Apex Developer Guide, "Custom Settings"); corrected 2026-10-03 from "No". Records are data and are seeded separately (UNVERIFIED 2026-10-03) | Yes (object schema, not data) |
| Visible to Apex tests by default | Metadata stays accessible in tests (UNVERIFIED for custom metadata specifically) | No: needs `SeeAllData=true` or test setup | No: tests create their own data |

**Decision rule:**

1. If the configuration needs to deploy across orgs (sandboxes, production, packages) without manual data entry → **Custom Metadata Types**.
2. If the configuration needs user-level, profile-level, or org-level overrides (e.g., a default currency setting that differs by user) → **Custom Settings (Hierarchy type)**.
3. If the configuration has volume above ~5,000 rows, needs relationships to other records, needs audit trail, or requires complex CRUD → **Custom Object**.
4. If none of the above — default to **Custom Metadata Types**. They are the current strategic choice for configuration storage.

**Do not use Custom Settings (List type).** List custom settings are a legacy pattern with no hierarchy support and no deployment advantage. All new configuration storage should use Custom Metadata Types or Custom Objects.

### Decision Area 2 — UI Framework: LWC vs Aura

| Criterion | Lightning Web Components (LWC) | Aura Components (Legacy) |
|---|---|---|
| Strategic direction | Current standard — the Aura Components Developer Guide says to always choose LWC unless you need a feature it does not support | Legacy — no new Aura-only platform features as of Spring '25 (UNVERIFIED 2026-10-03) |
| Performance | Better — the Aura guide says LWC performs better and is easier to develop | Lower — heavier framework overhead |
| Mobile support | Full | Limited — mobile features added after ~2021 are LWC-only (UNVERIFIED 2026-10-03) |
| Experience Cloud support | Full | Partial |
| Slack integration | Supported | Not supported (UNVERIFIED 2026-10-03) |
| Can contain the other | LWC cannot contain Aura | Aura can contain LWC children (LWC Developer Guide, "Lightning Web Components and Aura Components Working Together": "Aura components can contain Lightning web components. However, the opposite doesn't apply.") |

**Decision rule:**

- All new UI component development uses **LWC**. Correction (2026-10-03): earlier text said "No exceptions"; the Aura Components Developer Guide says to choose LWC unless you need a feature LWC does not yet support, so record the specific gap when Aura is chosen.
- Use Aura only when you are modifying an existing Aura component that cannot yet be migrated, or when you need a capability LWC lacks. For cross-component messaging, the Aura guide points application-event designs to Lightning Message Service, which LWC uses too.
- Migration path: wrap new LWC components inside the existing Aura container. Aura containers calling LWC children is a supported incremental migration pattern. Migrate the Aura shell when the project allows.

### Decision Area 3 — Integration Pattern: Platform Events vs Change Data Capture vs Outbound Messaging

| Pattern | When to Use | When Not To Use |
|---|---|---|
| Platform Events | Event-driven integration — publisher and subscriber are decoupled; high-volume event publishing; not tied to a specific record's field changes | When the subscriber needs to know which specific fields changed — use CDC instead |
| Change Data Capture (CDC) | External system must stay in sync with Salesforce record changes (inserts, updates, deletes, undeletes); CDC events include the changed field names automatically (`changedFields` in the change event header) | When you are not reacting to Salesforce record changes but publishing application-level events — use Platform Events. Without an add-on, only five entities can be selected |
| Outbound Messaging | Legacy SOAP-based pattern; the Metadata API describes outbound messages as workflow and approval actions | **Do not use for new integrations.** Workflow Rules are retired (UNVERIFIED 2026-10-03: retirement status is Help-only). Migrate to Platform Events. |

**Decision rule:**

1. Does the integration need to sync an external system with Salesforce record changes (field-level deltas)? → **Change Data Capture**.
2. Does the integration need to publish application-level events that trigger external processing, independent of any specific record save? → **Platform Events**.
3. Is there existing Outbound Messaging still in place? → Plan migration to Platform Events. Do not extend it.

**Retention windows:** High-volume Platform Events retain for 72 hours (replay window); legacy standard-volume events for 24 hours. CDC events are stored for up to three days. Correction (2026-10-03): earlier text said CDC retention extends to 7 days with Shield Event Monitoring; the Change Data Capture Developer Guide gives only the three-day window.

### Decision Area 4 — OmniStudio vs Standard Automation

| Criterion | OmniStudio (OmniScript + DataRaptors + Integration Procedures) | Standard Flow + LWC |
|---|---|---|
| License required | Yes — OmniStudio license (included in Salesforce Industries clouds) | No additional license |
| Guided multi-step wizard UI | Excellent — OmniScript is purpose-built for this | Achievable with Screen Flow or custom LWC, but requires more build effort |
| Complex data transformations across multiple objects | DataRaptors handle multi-source read/transform/write | Requires Apex or multi-step Flow |
| Declarative integration orchestration | Integration Procedures — declarative HTTP callout orchestration | Requires Apex for same complexity |
| Team profile | Typically used by Salesforce Industries/Vlocity-trained consultants | Standard Salesforce admin and developer teams |
| Strategic positioning | Strategic for Industries clouds | Strategic for all non-Industries use cases |

**Decision rule:**

1. Is an OmniStudio license included (Salesforce Industries cloud, Health Cloud, Financial Services Cloud, etc.)? And is the use case a guided multi-step wizard or complex multi-source data operation? → **OmniStudio**.
2. No OmniStudio license, or the use case is automation-only without a guided UI? → **Standard Flow + LWC (+ Apex where needed)**.
3. OmniStudio license is present but the use case is a simple single-page form or record update? → **Standard Flow** — do not add OmniStudio overhead to simple use cases.

---

## Mode 2: Review an Existing Implementation for Better Platform Fit

Use this mode when reviewing a design document, inherited org, or completed build to identify mismatched platform choices.

Work through the Review Checklist below against the inherited design, then use Mode 3 for any item that needs a migration.

---

## Recommended Workflow

1. Ask the six questions in "Questions to Ask Before Configuring" and write down the answers; they decide most of the tables in Mode 1.
2. Confirm the routing tree first: for automation-tool questions go to `admin/process-automation-selection`, and for integration patterns read `standards/decision-trees/integration-pattern-selection.md` before using Decision Area 3.
3. Score the top two or three candidates in the relevant Mode 1 table and check each against the limits in `references/gotchas.md` (deployment, secrets, test visibility, event retention and allocation).
4. Record the choice as a decision record using `references/examples.md` Example 4 as the shape: requirement, candidates, decision, rejected options with the platform fact that ruled them out, and the deployable components.
5. Run `python3 skills/architect/platform-selection-guidance/scripts/check_platform_selection_guidance.py --project-dir <retrieved-project>` to flag Aura components without LWC equivalents, outbound messages, custom metadata fields storing raw record IDs, active workflow rules, and custom settings used in Apex.
6. Hand implementation to the skill listed under Related Skills for the chosen feature.

---

## Review Checklist

- [ ] **Configuration storage audit:** Are routing rules, feature flags, thresholds, or integration endpoints stored in Custom Settings (List type) or hardcoded in Apex/Flow? If yes → candidate for migration to Custom Metadata Types.
- [ ] **Custom Settings hierarchy usage:** Are Custom Settings being used only at the org level (no profile/user records)? If yes → migrate to Custom Metadata Types; the hierarchy feature is unused and Custom Settings carry a deployment liability.
- [ ] **Aura component inventory:** Are new components being built in Aura? Is there a documented migration plan for existing Aura components? Any Aura-only component with active development investment is a liability.
- [ ] **Outbound Messaging in use:** Is there any active Outbound Messaging configuration in Setup > Workflow > Outbound Messages? These are Workflow Rule-coupled and should be migrated to Platform Events.
- [ ] **OmniStudio adoption match:** Is OmniStudio deployed in an org that lacks an OmniStudio-inclusive license? Or is OmniStudio absent from an org that has a Salesforce Industries license and is building complex guided journeys with Screen Flow workarounds?
- [ ] **CDC vs Platform Events confusion:** Is the integration pattern using Platform Events to replicate individual field changes (a CDC use case)? Or using CDC when the events are application-level with no direct field-change relationship (a Platform Events use case)?

---

## Mode 3: Evaluate an Upgrade Path

Use this mode when the team has identified a legacy feature and needs a migration path assessment.

### Aura to LWC Migration

**Steps:**
1. Audit the Aura component's event model. If it uses Aura application events with no LWC equivalent, identify what triggers those events and whether the pattern can be redesigned.
2. Build the LWC equivalent as a new component. Do not try to convert Aura markup to LWC line-by-line.
3. Insert the LWC into the Aura container. Aura containers can hold LWC children — this is the safe incremental pattern.
4. Retire the Aura component shell when all dependent pages have migrated.

**Risk:** Aura application events broadcast to all registered handlers. LWC uses a DOM event model. Designs that rely on cross-component Aura application events require redesign — not just rewrite.

### Custom Settings to Custom Metadata Types Migration

**Steps:**
1. Document all existing Custom Setting fields and their values across all org levels (org, profile, user).
2. Create the equivalent Custom Metadata Type with matching fields.
3. Create CMT records in the target org (or via Metadata API) for each configuration value.
4. Update Apex, Flow, and formula references to point to the new CMT type.
5. Keep the old Custom Setting active during parallel run. Remove only after full validation.

**Risk:** Profile-level and user-level Custom Setting overrides have no direct equivalent in Custom Metadata Types. If these hierarchy levels are in active use, evaluate whether Custom Settings should remain for that specific use case. Do not migrate blindly.

### Outbound Messaging to Platform Events Migration

**Steps:**
1. Map each Outbound Message to its triggering Workflow Rule and the fields it sends.
2. Design a Platform Event with equivalent fields.
3. Build an after-save Record-Triggered Flow (or Apex trigger) to publish the event on the same conditions as the old Workflow Rule.
4. Migrate the external subscriber from the SOAP endpoint to the Platform Events Pub/Sub API or CometD.
5. Deactivate the Workflow Rule and remove the Outbound Message.

**Risk:** Outbound Messaging retries on failure for up to 24 hours (extendable to seven days through Support), per *Integration Patterns and Practices*. Platform Events have a 72-hour replay window (high-volume) but are published once with no Salesforce-side retry to external endpoints. If the external subscriber goes offline, you must implement replay logic.

---

## Design Tradeoffs Reference

| Dimension | Custom Metadata Types | Custom Settings | Custom Objects |
|---|---|---|---|
| Deployment simplicity | High | Low | Medium (schema deploys; data doesn't) |
| Hierarchy / per-user config | No | Yes | No (requires code) |
| Large volume (1M+ rows) | No | No | Yes |
| Formula access | Yes | Yes (hierarchy type) | No |

| Dimension | LWC | Aura |
|---|---|---|
| Strategic investment | Active | Maintenance only |
| Performance | Higher | Lower |
| Mobile / Slack | Full | Partial / None |

| Dimension | Platform Events | CDC | Outbound Messaging |
|---|---|---|---|
| Trigger | Application-level publish | Record save (any change) | Workflow Rule (retired) |
| Field delta included | No | Yes | Partial (configured fields) |
| Retention | 72 hours (high-volume); 24 hours (legacy standard-volume) | Up to three days (corrected 2026-10-03 from "72h (7d with Shield)") | Retries up to 24 hours |

---

## Related Skills

- `admin/process-automation-selection` — use when the decision is between Flow, Apex, Workflow Rules, or Process Builder for automation logic. That skill covers the automation tool boundary; this skill covers the broader platform feature selection.
- `admin/custom-metadata-types` — use when Custom Metadata Types has been chosen and the design question shifts to type structure, field design, and deployment patterns.
- `apex/custom-metadata-in-apex` — use when the storage decision is made and the question is Apex access and caching patterns for Custom Metadata.
- `lwc/aura-to-lwc-migration` and `lwc/message-channel-patterns`: use after the UI framework decision, for the migration and the Lightning Message Service channel design.
- `omnistudio/omniscript-design-patterns` — use when OmniStudio has been selected and OmniScript design specifics are needed.
- `integration/platform-events-integration` — use when Platform Events has been chosen and design specifics are needed.
- `integration/change-data-capture-integration`: use when CDC has been chosen.
- `standards/decision-trees/integration-pattern-selection.md`: read before Decision Area 3.
