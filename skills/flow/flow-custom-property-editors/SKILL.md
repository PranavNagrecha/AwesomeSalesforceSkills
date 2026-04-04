---
name: flow-custom-property-editors
description: "Use when designing or reviewing Flow custom property editor patterns for screen components or actions, including when Flow Builder needs guided design-time configuration, generic type mapping, or builder-context-aware validation. Triggers: 'Flow custom property editor', 'configurationEditor', 'builderContext', 'inputVariables', 'Flow screen component setup'. NOT for general LWC runtime behavior when Flow Builder customization is not involved."
category: flow
salesforce-version: "Spring '25+'"
well-architected-pillars:
  - User Experience
  - Operational Excellence
triggers:
  - "when should I build a flow custom property editor"
  - "configurationEditor not working in flow builder"
  - "builderContext and inputVariables in flow"
  - "custom property editor for a flow screen component"
  - "how do I validate flow builder inputs for an lwc"
tags:
  - flow-custom-property-editor
  - flow-builder
  - configurationeditor
  - buildercontext
  - inputvariables
inputs:
  - "whether the target is a screen component or flow action"
  - "which configuration fields are hard to manage in the default property pane"
  - "whether generic sObject or builder-context-aware behavior is required"
outputs:
  - "flow extensibility recommendation"
  - "review findings for builder-side contracts and metadata registration"
  - "property-editor design plan aligned to flow builder behavior"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

Use this skill when the Flow-side question is "should this component or action have a custom configuration experience in Flow Builder, and if so, what should that builder contract look like?" The purpose is to keep Flow Builder configuration clear for admins while preventing the runtime component contract and the design-time editor contract from drifting apart.

## Before Starting

- Is the default Flow property pane actually inadequate, or is the team reaching for a custom editor too early?
- Is the custom editor for a screen component, an invocable/action-style surface, or a generic component that must inspect Flow metadata?
- Which builder inputs need validation, picklists, object awareness, or dynamic choices that the default UI cannot express well?

## Core Concepts

### This Is A Builder Concern First

Flow custom property editors exist to improve Flow Builder configuration, not runtime execution. The first design question is whether admins truly need a guided design-time UI. If the builder experience is simple enough with standard property inputs, a custom editor is unnecessary complexity.

### The Flow Contract Must Stay Stable

The editor reads and writes the component's configuration through builder-side contracts such as `inputVariables`, `builderContext`, and related metadata. Those contracts are Flow-facing APIs. If the runtime component changes names or assumptions without the editor changing too, the Flow setup becomes misleading or broken.

### Generic And Context-Aware Editors Need Strong Boundaries

Some editors only manage a few scalar values. Others need object metadata, generic type mapping, or awareness of what resources already exist in the Flow. The more context-aware the editor becomes, the more important it is to keep the builder logic narrowly focused and well documented.

### Metadata Registration Is Part Of The Design

The `.js-meta.xml` configuration is not boilerplate. The `configurationEditor` registration, targets, property definitions, and any generic type declarations are part of the Flow extensibility design. A polished editor component is useless if Flow Builder is not wired to it correctly.

## Common Patterns

### Guided Scalar Editor

**When to use:** The component exposes a small set of values that need better labels, help text, or validation than the default Flow property pane provides.

**How it works:** Register a custom editor, read `inputVariables`, write changes through the documented event contract, and keep the UI limited to design-time concerns.

**Why not the alternative:** If all fields are simple text or booleans, the default Flow property pane is usually cheaper and clearer.

### Context-Aware Resource Picker

**When to use:** Admins must choose Flow resources, objects, or generic types that depend on builder context.

**How it works:** Use builder-side context to shape the editor UI, validate selections, and write normalized values back to Flow Builder.

**Why not the alternative:** Hard-coded text fields create brittle Flow configuration and increase admin error rates.

### Runtime And Editor Contract Pairing

**When to use:** The same component is expected to be reused in many Flows and needs durable design-time governance.

**How it works:** Define a clear input model once, mirror it intentionally in the editor, and treat metadata, editor UI, and runtime expectations as one contract.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Simple scalar inputs only | Default Flow property pane | Lowest maintenance cost |
| Admins need guided setup, validation, or dynamic choices | Custom Property Editor | Better design-time UX |
| Flow config depends on object/resource context | Builder-context-aware editor | Default property pane is too weak |
| The real problem is runtime LWC implementation | Use the LWC-side skill instead | Builder and runtime are separate concerns |


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

- [ ] The team proved a custom editor is needed instead of default Flow properties.
- [ ] Metadata targets and `configurationEditor` registration are correct.
- [ ] Builder-side values map cleanly to the runtime component contract.
- [ ] The editor dispatches the documented change events intentionally.
- [ ] Validation is implemented where Flow admins could otherwise save broken configuration.
- [ ] Generic or context-aware behavior stays builder-only and does not leak runtime assumptions.

## Salesforce-Specific Gotchas

1. **A working runtime component can still have a broken Flow Builder experience** — design-time and runtime are separate surfaces with separate failure modes.
2. **`configurationEditor` registration is part of the contract** — if metadata is wrong, Flow Builder never invokes the editor no matter how good the LWC code is.
3. **Builder context is not a runtime API** — editors that assume runtime behavior instead of Flow Builder behavior become fragile fast.
4. **Visual polish is irrelevant if the editor never emits the right change event** — Flow Builder configuration stays stale until the event contract is correct.

## Output Artifacts

| Artifact | Description |
|---|---|
| Flow extensibility review | Findings on when a custom editor is justified and how the builder contract should work |
| Property-editor contract | Mapping of Flow inputs, builder-side validation, and runtime fields |
| Metadata registration checklist | Required `.js-meta.xml` and eventing decisions for the Flow-facing surface |

## Related Skills

- `lwc/custom-property-editor-for-flow` — use when the implementation details inside the LWC editor are the primary concern.
- `admin/flow-for-admins` — use when the better answer may be a simpler declarative Flow design with no custom editor.
- `lwc/lifecycle-hooks` — use when the editor LWC itself has general component lifecycle or rendering issues.
