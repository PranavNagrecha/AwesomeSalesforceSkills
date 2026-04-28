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
version: 2.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

Use this skill when the Flow-side question is "should this component or action have a custom configuration experience in Flow Builder, and if so, what should that builder contract look like?" The purpose is to keep Flow Builder configuration clear for admins while preventing the runtime component contract and the design-time editor contract from drifting apart.

Custom Property Editors (CPEs) are the FLOW BUILDER admin UX for configuring an LWC screen component or invocable action. They are not the runtime UI the end user sees — that's a separate LWC. This distinction matters because admins frequently conflate the two, build a runtime component, and then wonder why the Flow Builder configuration experience is awkward. The CPE is the DESIGN-TIME surface; the LWC is the RUN-TIME surface; they share a data model but are separate components with separate lifecycles.

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first.

Gather if not available:
- Is the default Flow property pane actually inadequate, or is the team reaching for a custom editor too early?
- Is the custom editor for a screen component, an invocable/action-style surface, or a generic component that must inspect Flow metadata?
- Which builder inputs need validation, picklists, object awareness, or dynamic choices that the default UI cannot express well?
- Who will maintain this CPE? (CPEs are LWCs with Flow-builder-specific contracts; maintainers need LWC + Flow expertise.)
- Is this CPE shipping in a package? (Namespacing + contract stability becomes more important.)

## Core Concepts

### This Is A Builder Concern First

Flow custom property editors exist to improve Flow Builder configuration, NOT runtime execution. The first design question is whether admins truly need a guided design-time UI. If the builder experience is simple enough with standard property inputs, a custom editor is unnecessary complexity. CPEs add:
- A separate LWC to maintain (the editor).
- A `configurationEditor` entry in the target component's `.js-meta.xml`.
- A Flow-builder-specific input/output contract.
- Testing overhead (Flow Builder behavior is hard to test automatically).

All of this is worth it when the default property pane is genuinely confusing or error-prone. Not worth it when the component has 2 scalar inputs.

### The Flow Contract Must Stay Stable

The editor reads and writes the component's configuration through builder-side contracts such as `inputVariables`, `builderContext`, and related metadata. Those contracts are Flow-facing APIs. If the runtime component changes names or assumptions without the editor changing too, the Flow setup becomes misleading or broken.

| Contract | What it provides | When to use |
|---|---|---|
| `@api inputVariables` | Array of existing input values the admin has set | Always — read current state |
| `@api builderContext` | Flow metadata: variables, constants, formulas in the Flow | When editor needs to pick from Flow resources |
| `@api automaticOutputVariables` | Output variables the component will produce | Rarely; mostly for complex invocable editors |
| `@api genericTypeMappings` | Type mappings for generic sObject / collection inputs | When the runtime component is generic (typed at Flow design time) |
| `FlowAttributeChangeEvent` | Fire when admin changes a field — writes back to Flow | Every change must dispatch this; otherwise changes don't persist |

### Generic And Context-Aware Editors Need Strong Boundaries

Some editors only manage a few scalar values. Others need object metadata, generic type mapping, or awareness of what resources already exist in the Flow. The more context-aware the editor becomes, the more important it is to keep the builder logic narrowly focused and well documented.

Rule of thumb: the editor's job is "translate admin intent into `inputVariables` that the runtime component will consume correctly." If the editor is doing other things (side-effectful CRUD, complex business logic), it has escaped its lane.

### Metadata Registration Is Part Of The Design

The `.js-meta.xml` configuration is not boilerplate. The `configurationEditor` registration, targets, property definitions, and any generic type declarations are part of the Flow extensibility design. A polished editor component is useless if Flow Builder is not wired to it correctly.

```xml
<!-- Runtime component's .js-meta.xml -->
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>60.0</apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <target>lightning__FlowScreen</target>
    </targets>
    <targetConfigs>
        <targetConfig targets="lightning__FlowScreen" configurationEditor="c-myEditorLwc">
            <property name="recordId" type="String" />
            <property name="fieldApiName" type="String" />
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

The `configurationEditor` attribute points to the EDITOR LWC (which is a separate bundle). If that attribute is missing or wrong, Flow Builder falls back to the default property pane — and the custom editor never fires.

## Common Patterns

### Pattern 1: Guided Scalar Editor

**When to use:** The component exposes a small set of values that need better labels, help text, or validation than the default Flow property pane provides.

**Structure:** Register a custom editor, read `inputVariables`, write changes via `FlowAttributeChangeEvent`, keep the UI limited to design-time concerns (labels, help text, validation rules).

### Pattern 2: Context-Aware Resource Picker

**When to use:** Admins must choose Flow resources, objects, or generic types that depend on builder context.

**Structure:** Use `@api builderContext` to read the Flow's existing variables/constants. Filter them by type. Present as a picklist. Write the admin's selection back as a variable reference (e.g., `{!MyVar}`) — not a raw value.

### Pattern 3: Generic Component Type Mapper

**When to use:** Runtime component accepts generic `@api sobject` input (e.g. "works on any object") — admin needs to specify which object type at Flow design time.

**Structure:** Use `@api genericTypeMappings` in the editor to propagate the selected type to the runtime component's metadata. Validate that the chosen object is accessible + has the required fields.

### Pattern 4: Runtime And Editor Contract Pairing

**When to use:** The same component is expected to be reused in many Flows and needs durable design-time governance.

**Structure:** Define a clear input model once (e.g. `MyComponentConfig` DTO), mirror it intentionally in the editor, and treat metadata + editor UI + runtime expectations as one contract. Version the contract together; never change only one side.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Simple scalar inputs only | Default Flow property pane | Lowest maintenance cost |
| Admins need guided setup, validation, or dynamic choices | Custom Property Editor (Pattern 1) | Better design-time UX |
| Flow config depends on object/resource context | Builder-context-aware editor (Pattern 2) | Default pane too weak |
| Runtime component is generic over sObject | Type mapper editor (Pattern 3) | Required for generic Flow input |
| Cross-Flow reuse at scale | Contract pairing (Pattern 4) with versioning | Reuse + governance |
| The real problem is runtime LWC implementation | Use `lwc/custom-property-editor-for-flow` | Builder and runtime are separate concerns |

## Review Checklist

- [ ] The team proved a custom editor is needed instead of default Flow properties.
- [ ] Metadata targets and `configurationEditor` registration are correct.
- [ ] Builder-side values map cleanly to the runtime component contract.
- [ ] The editor dispatches `FlowAttributeChangeEvent` on every change.
- [ ] Validation is implemented where Flow admins could otherwise save broken configuration.
- [ ] Generic or context-aware behavior stays builder-only and does not leak runtime assumptions.
- [ ] CPE and runtime component versioned together.
- [ ] `configurationEditor` attribute points to the correct editor LWC.

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, runtime component shape, admin UX needs
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Common Patterns above; keep editor scope narrow
4. Validate — run the skill's checker script and verify against the Review Checklist above
5. Document — record any deviations from standard patterns; pair the editor + runtime contracts explicitly

---

## Salesforce-Specific Gotchas

1. **A working runtime component can still have a broken Flow Builder experience** — design-time and runtime are separate surfaces with separate failure modes.
2. **`configurationEditor` registration is part of the contract** — if metadata is wrong, Flow Builder never invokes the editor no matter how good the LWC code is.
3. **Builder context is not a runtime API** — editors that assume runtime behavior instead of Flow Builder behavior become fragile fast.
4. **Visual polish is irrelevant if the editor never emits `FlowAttributeChangeEvent`** — Flow Builder configuration stays stale until the event contract is correct.
5. **CPEs can't access user data at design time** — they run in the admin's builder context, not in a user context. Don't assume record access; use `builderContext` for Flow metadata only.
6. **CPE bugs can corrupt Flow metadata** — an editor that writes malformed values can leave the Flow in an unrecoverable state. Test destructive edits in sandbox.
7. **Flow Builder caches CPE LWC** — changes to the editor may not appear without a hard refresh. Document this for admin testers.
8. **Namespaced CPE components in packages are opaque to consumers** — if the package is managed, consumers can't customize the editor. Plan the stable contract carefully.
9. **Lightning Web Security affects CPE DOM access** — modern LWS enforces stricter shadow-DOM boundaries; older CPEs may break silently after LWS rollout.
10. **The Property Editor view does not auto-resize** — complex editors may overflow the default Flow Builder panel. Use `slds-scrollable_y` and test at multiple screen sizes.

## Proactive Triggers

Surface these WITHOUT being asked:

- **CPE without `FlowAttributeChangeEvent` dispatch on input changes** → Flag as Critical. Changes don't persist.
- **Runtime component changed without updating CPE** → Flag as High. Contract drift invariant violated.
- **CPE accessing user data at design time** → Flag as High. Wrong lane; CPE lives in builder context.
- **Default property pane would suffice** → Flag as Medium. Unnecessary complexity; remove the CPE.
- **Missing `configurationEditor` attribute in `.js-meta.xml`** → Flag as Critical. CPE never fires.
- **CPE in managed package without documented stable contract** → Flag as High. Upgrade risk for consumers.
- **CPE missing validation on required inputs** → Flag as Medium. Admin can save broken configuration.
- **CPE and runtime LWC version mismatch** → Flag as High. Governance gap.

## Output Artifacts

| Artifact | Description |
|---|---|
| Flow extensibility review | Findings on when a custom editor is justified and how the builder contract should work |
| Property-editor contract | Mapping of Flow inputs, builder-side validation, runtime fields |
| Metadata registration checklist | Required `.js-meta.xml` + eventing decisions for the Flow-facing surface |
| Versioning plan | How CPE + runtime pair evolves across releases |

## Related Skills

- `lwc/custom-property-editor-for-flow` — implementation details inside the editor LWC.
- `flow/screen-flows` — if the CPE is for a screen-flow component, consult both.
- `admin/flow-for-admins` — when the better answer may be a simpler declarative Flow design with no CPE.
- `lwc/lifecycle-hooks` — when the editor LWC itself has general component lifecycle issues.
- `lwc/lwc-in-flow-screens` — for the runtime LWC side of the contract.
