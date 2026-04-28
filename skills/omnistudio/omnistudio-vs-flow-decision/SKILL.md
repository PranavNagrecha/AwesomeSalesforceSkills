---
name: omnistudio-vs-flow-decision
description: "Use when choosing between OmniStudio (OmniScript / Integration Procedure / FlexCard / DataRaptor) and Flow / Screen Flow / Apex for a given capability. Triggers: 'omnistudio or flow', 'omniscript vs screen flow', 'integration procedure vs subflow', 'flexcard vs lightning page'. NOT for general automation selection across Workflow/Process Builder/Apex (see automation-selection tree)."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
  - Performance
triggers:
  - "should this be an omniscript or a screen flow"
  - "integration procedure or invocable apex"
  - "flexcard vs custom lwc"
  - "dataraptor extract vs soql in flow"
  - "when is omnistudio the wrong choice"
tags:
  - omnistudio
  - flow
  - tool-selection
  - decision-tree
  - architecture
inputs:
  - "capability description and user surface"
  - "licensing and product line context (Industry Cloud vs core)"
  - "team skills and operational model"
outputs:
  - "recommended tool per layer (UI, orchestration, data shaping)"
  - "risks and tradeoffs"
  - "migration notes if replacing existing implementation"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# OmniStudio vs Flow Decision

The default reflex on Industry Cloud orgs is "use OmniStudio"; the default on core orgs is "use Flow." Both reflexes are wrong about 30% of the time. The right tool depends less on product line and more on four factors: the user surface, the reuse pattern, the team's operational model, and the latency profile.

OmniStudio excels when the UI needs multi-step guidance with branching, when shaping JSON for external systems is a first-class concern, and when the same logic serves both LWC and Experience Cloud. Flow excels when the logic is record-centric (triggered by DML), when admins own the surface, and when the capability is a handful of steps rather than a multi-screen journey.

Treat this as a layered choice: UI layer (OmniScript, Screen Flow, FlexCard, LWC), orchestration layer (Integration Procedure, Flow, Apex), data layer (DataRaptor, SOQL/DML in Flow, Apex). Each layer can pick a different tool.

---

## Before Starting

- State the user surface: internal vs customer vs partner; desktop vs mobile.
- State the licensing context: Industry Cloud (OmniStudio included) vs core.
- List the reusers: other OmniScripts, Flows, LWCs, external consumers.
- List the SLAs: expected latency, scale, concurrency.

## Core Concepts

### Three Layers, Three Decisions

| Layer | OmniStudio option | Flow/core option |
|---|---|---|
| UI | OmniScript, FlexCard | Screen Flow, LWC, Record Page |
| Orchestration | Integration Procedure | Flow (autolaunched), Invocable Apex |
| Data shaping | DataRaptor | Get/Update/Create Records, Apex |

### When OmniStudio Is Right

- Multi-step guided UX with dynamic branching and complex validation.
- Reusable JSON shaping for external system integration.
- Same capability consumed by both LWC and Experience Cloud site.
- Industry Cloud licensed and team is trained.

### When Flow Is Right

- Record-triggered automation on core objects.
- Short UI interaction (1-3 screens) owned by admins.
- Logic that must run in after-save context on save.
- Team operates in Flow and has no OmniStudio depth.

### When Apex Is Right

- Governor-constrained high-volume processing.
- Complex logic that outgrows Flow's expression engine.
- Performance-critical callouts.

---

## Common Patterns

### Pattern 1: OmniScript UI + Flow Backend

OmniScript owns the user journey; a step invokes an autolaunched Flow that does record-triggered updates. Good when the UI is OmniStudio but the downstream side-effects fit naturally in Flow.

### Pattern 2: Integration Procedure For External Shaping

The external system needs a specific JSON shape. Use an IP with DataRaptor Transforms to compose it. Do not try to shape external JSON in Flow formulas.

### Pattern 3: FlexCard On Core Object

Industry Cloud orgs sometimes replace the standard record page with a FlexCard even when a Lightning Record Page would serve. Prefer the record page unless FlexCard-specific features (actions from a central designer, IP-powered save chains) are needed.

### Pattern 4: Screen Flow For Admin-Owned Capability

If the capability needs to ship monthly and the owners are admins, pick Screen Flow. OmniStudio's deployment model (DataPacks) is harder for a typical admin team to operate at cadence.

---

## Decision Guidance

| Situation | Recommended Tool | Reason |
|---|---|---|
| Multi-step branching UX, customer-facing | OmniScript | Purpose-built for this |
| 1-3 step internal UI owned by admins | Screen Flow | Lower operational cost |
| Record-triggered side-effects | Flow | Native to the trigger context |
| External JSON shaping | Integration Procedure + DataRaptor | Direct composition |
| High-volume bulk processing | Apex | Governor control |
| Reusable capability across LWC and Experience Cloud | OmniScript | Surface parity |
| Lightning Record Page replacement | Lightning Record Page (not FlexCard) unless FlexCard features specifically needed | Simpler ops |
| Industry Cloud capability already modeled in OmniStudio | OmniStudio | Match the platform |

## Review Checklist

- [ ] Decision is per-layer (UI, orchestration, data).
- [ ] Team operating model matches the tool.
- [ ] Licensing is considered.
- [ ] Reuse pattern is explicit.
- [ ] Latency profile is explicit.
- [ ] FlexCard vs Lightning Record Page has been considered separately.

## Recommended Workflow

1. Describe the capability in user surface terms.
2. Classify each layer (UI, orchestration, data).
3. Apply the decision table; record rationale per layer.
4. Sanity-check against team and licensing.
5. Call out mixed-tool boundaries and their contracts.
6. Validate against any existing decision-tree doc in the org.

---

## Salesforce-Specific Gotchas

1. OmniStudio DataPacks are not Change Set-compatible; deployment pipeline differs from Flow.
2. Managed OmniScripts can be partially overridden but cannot be branched freely.
3. FlexCard auto-generated LWCs reset on OmniStudio upgrades if customized in-place.
4. Flow with complex loop logic often outperforms a row-by-row Integration Procedure.
5. Industry Cloud licensing can include OmniStudio; confirm before designing.

## Proactive Triggers

- Admin-owned 2-screen capability being built in OmniScript → Flag High. Screen Flow likely cheaper.
- Flow with multi-callout orchestration and custom JSON shaping → Flag Medium. IP fits better.
- FlexCard used to replace a record page with no FlexCard-specific features → Flag Medium.
- OmniScript picked without considering Industry Cloud licensing → Flag Critical.

## Output Artifacts

| Artifact | Description |
|---|---|
| Per-layer tool choice | UI / orchestration / data recommendation |
| Rationale table | Why this tool at this layer |
| Boundary contracts | Interfaces between mixed tools |

## Related Skills

- `standards/decision-trees/automation-selection.md` — the full automation tree.
- `omnistudio/omniscript-design-patterns` — OmniScript-specific patterns.
- `flow/screen-flows` — Screen Flow patterns.
- `omnistudio/integration-procedures` — IP patterns.
