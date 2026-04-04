---
name: custom-property-editor-for-flow
description: "Use when building or reviewing an LWC Custom Property Editor for Flow screen or action configuration, including the `configurationEditor` metadata hook, builder-side APIs, validation, and value-change events. Triggers: 'custom property editor', 'Flow configuration editor', 'builderContext', 'inputVariables', 'configurationEditor'. NOT for ordinary runtime screen-component behavior when no Flow Builder design-time customization is involved."
category: lwc
salesforce-version: "Spring '25+'"
well-architected-pillars:
  - User Experience
  - Operational Excellence
tags:
  - custom-property-editor
  - flow-builder
  - configurationeditor
  - inputvariables
  - buildercontext
triggers:
  - "how do I build a custom property editor for Flow"
  - "configurationEditor in js-meta.xml"
  - "Flow builderContext and inputVariables"
  - "custom property editor validate method"
  - "configuration_editor_input_value_changed event"
inputs:
  - "whether the target is a Flow screen component or another Flow-exposed surface"
  - "which design-time fields must be configured in Flow Builder"
  - "validation and builder-only UX expectations"
outputs:
  - "property-editor design recommendation"
  - "review findings for metadata registration and builder contract issues"
  - "LWC pattern for editor eventing and validation"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

# Custom Property Editor For Flow

Use this skill when a Flow-exposed component needs a better design-time editing experience inside Flow Builder than the default property pane can provide. The key distinction is between the runtime component and the builder-only editor component. They are related, but they are not the same thing and should not be designed as if they run in the same context.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the component a Flow screen component, another Flow-exposed action, or a packaged surface with builder customization needs?
- Which fields truly need a custom editing experience instead of default Flow property inputs?
- What validation, object-awareness, or builder-context data must the editor use?

---

## Core Concepts

### Runtime Component And Editor Component Are Separate

The screen component that runs in Flow and the custom property editor that runs in Flow Builder are distinct LWCs. Keep that boundary clear so runtime assumptions do not leak into the builder experience.

### Metadata Registration Drives The Builder Hook

The component metadata must point Flow Builder to the custom property editor through the `configurationEditor` relationship. If that registration is wrong, the editor never becomes part of the design-time experience.

### Builder APIs Are Design-Time Contracts

Custom property editors work with Flow Builder-facing APIs such as `inputVariables`, `builderContext`, `elementInfo`, and `validate()`. These are builder contracts, not general-purpose runtime APIs.

### Editor Events Are How Values Change

The editor communicates changes back to Flow Builder through the documented configuration-editor event pattern. A visually correct editor that never dispatches the right event is still broken.

---

## Common Patterns

### Scalar Design-Time Editor

**When to use:** A component needs better labels, validation, or UX for a few configuration fields.

**How it works:** Expose a focused editor LWC that reads `inputVariables`, updates fields through the configuration-editor event, and implements `validate()` when builder-side validation matters.

**Why not the alternative:** For simple cases, default Flow property inputs are cheaper and clearer.

### Builder-Context-Aware Editor

**When to use:** The design-time experience depends on Flow metadata or available resources.

**How it works:** Read `builderContext` or related builder APIs and shape the editor UI around what Flow Builder already knows.

### Runtime And Editor Contract Pairing

**When to use:** A screen component has multiple configurable inputs and is meant to be reused by admins.

**How it works:** Keep the runtime component API and editor field names aligned so the editor is simply a safer builder for the same contract.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Default Flow property pane is sufficient | Use default editor | Lower complexity |
| Admins need guided design-time UX or validation | Custom Property Editor | Better builder experience |
| Editor needs Flow metadata context | Use builder-side APIs such as `inputVariables` and `builderContext` | Design-time context belongs in the editor |
| Runtime logic is being copied into the editor | Split responsibilities again | Builder and runtime concerns are different |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] The runtime component and editor component are treated as separate LWCs.
- [ ] Metadata registration points Flow Builder to the custom editor correctly.
- [ ] The editor reads and writes the intended builder-side contract.
- [ ] Configuration-change events are dispatched intentionally.
- [ ] `validate()` exists where builder-side validation matters.
- [ ] The team rejected default Flow property inputs for a real UX reason.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **A valid runtime component can still have a broken builder experience** - the editor is a separate surface with separate failure modes.
2. **`configurationEditor` metadata is not optional once you choose a custom editor** - a missing link leaves the builder unaware of the LWC.
3. **Builder contracts are not generic runtime APIs** - `inputVariables` and `builderContext` belong to the editor context.
4. **An editor that never fires the change event is functionally inert** - visual polish does not matter if Flow Builder never receives the update.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Editor design review | Findings on metadata hookup, builder APIs, and validation |
| Builder contract pattern | LWC design-time event and API guidance |
| Runtime/editor pairing plan | Mapping between runtime component inputs and editor controls |

---

## Related Skills

- `flow/flow-custom-property-editors` - use when the Flow-side extensibility model is the main focus rather than the LWC implementation details.
- `lwc/lifecycle-hooks` - use when the editor or runtime component has general LWC lifecycle issues.
- `admin/flow-for-admins` - use when the better answer may be a simpler declarative Flow design with no custom LWC.
