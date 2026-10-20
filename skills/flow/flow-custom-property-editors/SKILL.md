---
name: flow-custom-property-editors
description: "Decide whether a Flow screen component or invocable action needs a Custom Property Editor at all, and if it does, what the design-time contract owes the admin: which configuration fields are genuinely unmanageable in the default property pane, how generic sObject type mapping gets declared, and how the design-time editor is kept from drifting away from the runtime component it configures. Routing and design review, not implementation. Triggers: 'do we need a flow custom property editor', 'flow custom property editor builder context validate', 'Flow Builder admin configuration UX', 'design-time surface vs runtime surface'. NOT for authoring the editor LWC itself — use lwc/custom-property-editor-for-flow. NOT for the runtime screen component it configures — use flow/flow-screen-lwc-components."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Operational Excellence
triggers:
  - "when should I build a flow custom property editor"
  - "configurationEditor not working in flow builder"
  - "builderContext and inputVariables in flow"
  - "custom property editor for a flow screen component"
  - "how do I validate flow builder inputs for an lwc"
  - "flow custom property editor builder context validate"
tags:
  - flow-custom-property-editor
  - flow-builder
  - flow-extensibility
  - design-time-vs-runtime
  - admin-configuration-ux
inputs:
  - "whether the target is a screen component or flow action"
  - "which configuration fields are hard to manage in the default property pane"
  - "whether generic sObject or builder-context-aware behavior is required"
outputs:
  - "flow extensibility recommendation"
  - "review findings for builder-side contracts and metadata registration"
  - "property-editor design plan aligned to flow builder behavior"
dependencies: []
version: 2.0.2
author: Pranav Nagrecha
updated: 2026-10-20
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

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Which inputs does the default property pane handle badly? | Core Concepts: a CPE is a separate LWC to maintain; without a named pain, use the default | A named input list or a decision to skip the CPE |
| Is the target a screen component or an invocable action? | Registration differs: `targetConfig` attribute versus `@InvocableMethod` modifier (apexdev 264 L5467-5468) | The right registration path |
| Which events does the editor dispatch for each input? | Gotcha 4: Flow Builder is told only by `configuration_editor_*` events (lwcguide use-flow-custom-property-editor-interface) | An event table per input |
| Does any input need validation before Done? | `validate()` runs on Done and Flow Builder shows an error count only (lwcguide use-flow-custom-property-editor-interface) | Validation rules and in-editor error text |
| Is the component generic over sObject? | Pattern 3: `genericTypeMappings` and `typeName` / `typeValue` (lwcguide use-flow-custom-property-editor-interface) | A type-mapping design |
| Will the editor ship in a managed package? | Gotcha 8: contract stability for consumers (UNVERIFIED, 2026-10-20) | A versioning plan for editor and runtime |
| Could a partial CPE replace a full one for an action? | Pattern 4: new parameters need no CPE change with partial CPEs (apexdev 264 L27576-27578) | A smaller editor surface |

A proper configuration adds a justified editor, a paired contract and a test that reopens the saved configuration; just building an LWC gives you none of them.

---

## Core Concepts

### This Is A Builder Concern First

Flow custom property editors exist to improve Flow Builder configuration, NOT runtime execution. The first design question is whether admins truly need a guided design-time UI. If the builder experience is simple enough with standard property inputs, a custom editor is unnecessary complexity. CPEs add:
- A separate LWC to maintain (the editor).
- A `configurationEditor` attribute on the target component's `targetConfig` in `.js-meta.xml` (lwcguide use-flow-custom-property-editor-lwc-example: `<targetConfig targets="lightning__FlowScreen" configurationEditor="c-volume-editor">`), or for an invocable action the `configurationEditor` modifier of `@InvocableMethod`, where omitting it means "Flow Builder uses the standard property editor" (apexdev 264 L5467-5468).
- A Flow-builder-specific input/output contract.
- Testing overhead (Flow Builder behavior is hard to test automatically).

All of this is worth it when the default property pane is genuinely confusing or error-prone. Not worth it when the component has 2 scalar inputs.

### The Flow Contract Must Stay Stable

The editor reads and writes the component's configuration through builder-side contracts such as `inputVariables`, `builderContext`, and related metadata. Those contracts are Flow-facing APIs. If the runtime component changes names or assumptions without the editor changing too, the Flow setup becomes misleading or broken.

| Contract | What it provides | When to use |
|---|---|---|
| `@api inputVariables` | Name, value and data type of each input variable (lwcguide use-flow-custom-property-editor-interface) | Always — read current state |
| `@api builderContext` | Data about the flow's elements and resources, for example `variables`, `screens`, `actionCalls` (lwcguide use-flow-custom-property-editor-interface) | When editor needs to pick from Flow resources |
| `@api automaticOutputVariables` | UNVERIFIED (2026-10-20): not in either corpus or the LWC guide pages read | Do not rely on it |
| `@api genericTypeMappings` | `typeName` and `typeValue` for each generic sObject input (lwcguide use-flow-custom-property-editor-interface; the name appears in apexdev 264 L27601-27602) | When the runtime component is generic (typed at Flow design time) |
| `@api elementInfo` and `validate()` | The invoking screen or action element, and custom validation run when the admin clicks Done; Flow Builder shows only the number of errors (lwcguide use-flow-custom-property-editor-interface) | When the editor needs per-instance logic or validation |
| `configuration_editor_input_value_changed` (also `_deleted`, `configuration_editor_generic_type_mapping_changed`) | `CustomEvent`s, with `bubbles` and `composed` true, that report changes to Flow Builder (lwcguide use-flow-custom-property-editor-interface) | Every change must dispatch one; otherwise Flow Builder is not told |

The earlier text named `FlowAttributeChangeEvent` as the editor's change event: CONTRADICTED by the interface page, which lists the three `configuration_editor_*` events. `FlowAttributeChangeEvent` is not a Flow Builder editor event.

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

The `configurationEditor` attribute points to the EDITOR LWC (which is a separate bundle); use the `c` namespace unless the org has its own (lwcguide use-flow-custom-property-editor-lwc-example). For invocable actions, "if you don't specify this modifier, Flow Builder uses the standard property editor" (apexdev 264 L5467-5468); the same fallback for a screen component with a missing or wrong attribute is UNVERIFIED (2026-10-20).

## Common Patterns

### Pattern 1: Guided Scalar Editor

**When to use:** The component exposes a small set of values that need better labels, help text, or validation than the default Flow property pane provides.

**Structure:** Register a custom editor, read `inputVariables`, report changes by dispatching `configuration_editor_input_value_changed` (lwcguide use-flow-custom-property-editor-interface), keep the UI limited to design-time concerns (labels, help text, validation rules).

### Pattern 2: Context-Aware Resource Picker

**When to use:** Admins must choose Flow resources, objects, or generic types that depend on builder context.

**Structure:** Use `@api builderContext` to read the Flow's existing variables/constants. Filter them by type. Present as a picklist. Write the admin's selection back as a variable reference (e.g., `{!MyVar}`) — not a raw value. UNVERIFIED (2026-10-20): the reference syntax; the guide's example builds options from `builderContext.variables` and dispatches the chosen value (lwcguide use-flow-custom-property-editor-interface).

### Pattern 3: Generic Component Type Mapper

**When to use:** Runtime component accepts generic `@api sobject` input (e.g. "works on any object") — admin needs to specify which object type at Flow design time.

**Structure:** Read `@api genericTypeMappings` and report a changed type with `configuration_editor_generic_type_mapping_changed`; `typeName` is the `<property type="{T}">` name for a screen component (`{T[]}` for a collection) and `T__param1` / `U__param1` style for an action's inputs and outputs (lwcguide use-flow-custom-property-editor-interface). Validate that the chosen object is accessible + has the required fields.

### Pattern 4: Runtime And Editor Contract Pairing

**When to use:** The same component is expected to be reused in many Flows and needs durable design-time governance.

**Structure:** Define a clear input model once (e.g. `MyComponentConfig` DTO), mirror it intentionally in the editor, and treat metadata + editor UI + runtime expectations as one contract. Version the contract together; never change only one side. For an invocable action, a partial CPE lowers this cost: "With partial CPEs, you can add new input parameters to your action without updating the CPE code", while "full CPEs require code updates whenever you modify the action's parameters" (apexdev 264 L27576-27578), and each parameter can belong to only one partial CPE (L27657). The action-side registration is `CpeName` and `ConfiguredBy` in InvocableActionExtension, API 65.0+ (api_meta 264 L84654, L84734-84737).

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
- [ ] The editor dispatches `configuration_editor_input_value_changed` (or `_deleted` / generic-type-mapping) on every change.
- [ ] Validation is implemented where Flow admins could otherwise save broken configuration.
- [ ] Generic or context-aware behavior stays builder-only and does not leak runtime assumptions.
- [ ] CPE and runtime component versioned together.
- [ ] `configurationEditor` attribute points to the correct editor LWC.

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. **Prove the need** — list the inputs the default property pane handles badly; if there are two scalar inputs, stop and recommend the default pane.
2. **Pick the surface** — screen component (`configurationEditor` attribute on `targetConfig`), or invocable action (`configurationEditor` modifier, or a partial CPE through InvocableActionExtension `CpeName` / `ConfiguredBy`, api_meta 264 L84734-84737).
3. **Write the contract table** — each input, its data type, who owns validation (`validate()`) and which event reports it (`configuration_editor_input_value_changed`).
4. **Review the metadata** — `configurationEditor` points at the editor bundle with the right namespace; `lightning__FlowScreen` or `lightning__FlowAction` is in `targets`.
5. **Run the checker** — `python3 scripts/check_flow_custom_property_editors.py --manifest-dir <project>`; fix unresolved editors and editors that never dispatch a change event.
6. **Test in Flow Builder** — configure, save, close, reopen, and run the Flow; record versioning of editor and runtime together.

---

## Salesforce-Specific Gotchas

1. **A working runtime component can still have a broken Flow Builder experience** — design-time and runtime are separate surfaces with separate failure modes.
2. **`configurationEditor` registration is part of the contract** — if metadata is wrong, Flow Builder never invokes the editor no matter how good the LWC code is.
3. **Builder context is not a runtime API** — editors that assume runtime behavior instead of Flow Builder behavior become fragile fast.
4. **Visual polish is irrelevant if the editor never dispatches `configuration_editor_input_value_changed`** — Flow Builder configuration stays stale until the event contract is correct (lwcguide use-flow-custom-property-editor-interface).
5. **CPEs can't access user data at design time** — UNVERIFIED (2026-10-20): not in either corpus or the LWC guide pages read. Treat `builderContext` as Flow metadata only (lwcguide use-flow-custom-property-editor-interface).
6. **CPE bugs can corrupt Flow metadata** — UNVERIFIED (2026-10-20): not in either corpus or the LWC guide pages read. Test destructive edits in sandbox.
7. **Flow Builder caches CPE LWC** — UNVERIFIED (2026-10-20): not in either corpus or the LWC guide pages read. Document a hard refresh for admin testers as a precaution.
8. **Namespaced CPE components in packages are opaque to consumers** — UNVERIFIED (2026-10-20): not in either corpus or the LWC guide pages read. Plan the stable contract carefully.
9. **Lightning Web Security affects CPE DOM access** — UNVERIFIED (2026-10-20): not in either corpus or the LWC guide pages read. Retest older CPEs after an LWS change.
10. **The Property Editor view does not auto-resize** — UNVERIFIED (2026-10-20): not in either corpus or the LWC guide pages read. Test complex editors at several panel sizes.

## Proactive Triggers

Surface these WITHOUT being asked:

- **CPE without a `configuration_editor_input_value_changed` dispatch on input changes** → Flag as Critical. Flow Builder is never told.
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
