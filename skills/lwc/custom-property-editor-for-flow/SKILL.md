---
name: custom-property-editor-for-flow
description: "Use when building or reviewing an LWC Custom Property Editor for Flow screen or action configuration. Triggers: custom property editor, Flow configuration editor, builderContext, configuration_editor_input_value_changed, genericTypeMappings, elementInfo, validate() key errorString, propertyType T generic sObject. NOT for a Flow screen component with no design-time editor — use lwc/lwc-in-flow-screens. NOT for deciding whether a property editor is warranted — use flow/flow-custom-property-editors."
category: lwc
salesforce-version: "Spring '25+"
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
  - "custom property editor isn't working"
  - "we're having issues with custom property editor"
  - "build a custom property editor for a flow screen component"
  - "register a configurationEditor on an invocable action"
  - "dispatch configuration_editor_generic_type_mapping_changed from an LWC"
  - "custom property editor doesn't load in Flow Builder"
  - "flow builder shows default text boxes instead of my property editor"
  - "validate() in a custom property editor isn't blocking Done"
  - "read genericTypeMappings for a generic sObject flow input"
  - "write a Jest test for a Flow custom property editor"
  - "my property editor changes don't save in the flow"
inputs:
  - "whether the target is a Flow screen component or another Flow-exposed surface"
  - "which design-time fields must be configured in Flow Builder"
  - "validation and builder-only UX expectations"
outputs:
  - "property-editor design recommendation"
  - "review findings for metadata registration and builder contract issues"
  - "LWC pattern for editor eventing and validation"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Custom Property Editor For Flow

Use this skill when a Flow-exposed component needs a better design-time editing experience inside Flow Builder than the default property pane can provide. The key distinction is between the runtime component and the builder-only editor component. They are related, but they are not the same thing and should not be designed as if they run in the same context.

This skill owns the **LWC implementation and its tests**: the Flow Builder JavaScript
interface, the three configuration-editor events, `validate()`, the `js-meta.xml` wiring,
and the Jest assertions that pin all of it. Whether an editor is warranted at all is
`flow/flow-custom-property-editors`.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the component a Flow screen component, another Flow-exposed action, or a packaged surface with builder customization needs?
- Which fields truly need a custom editing experience instead of default Flow property inputs?
- What validation, object-awareness, or builder-context data must the editor use?

---

## Questions to Ask Before Configuring

Ask these before the first `dispatchEvent` is written. Each traces to a specific gotcha in
`references/gotchas.md` — the platform behaviour that punishes the wrong assumption is named
in the middle column.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Is the consumer a screen component, an invocable action, or both?" | Registration lives in two different places — a `targetConfig` attribute for a screen component, the `configurationEditor` modifier on `@InvocableMethod` for an action (Gotcha 4) | One registration site, decided before any code, instead of an editor declared in a file nothing reads |
| "Which inputs are generic sObject, and which are plain scalars?" | `typeName` is bare `T` for a screen component and `T__name` / `U__name` for an action; the wrong spelling fires an accepted event that changes nothing (Gotcha 6) | The exact `typeName` strings, and whether a second event type is needed at all |
| "Does the admin ever need to *clear* an input, not just change it?" | Clearing is `configuration_editor_input_value_deleted`, a different event from a change to `''` (Gotcha 8) | A change handler with a delete branch, rather than empty strings written into `reference` inputs |
| "What must Flow Builder refuse to let the admin save?" | `validate()` is a save gate that returns an array of `{ key, errorString }` and shows only the error *count* (Gotcha 7) | A written list of blocking conditions, plus who renders the strings the admin actually reads |
| "Which properties should never appear in the editor?" | `role="outputOnly"` removes a property from the CPE entirely; unset or `inputOnly` exposes it (Gotcha 5) | A `role` per property chosen deliberately, not copied from the runtime component's needs |
| "What does the editor do on a brand-new flow with no variables?" | `builderContext` arrives asynchronously and its `variables` array is absent before any resource exists (Gotcha 10) | A guard at every `builderContext` read and a Jest case that never sets it |
| "Will this editor ship in a managed package?" | `isExposed` can only move `false` → `true`, and once published you can no longer remove targets or `@api` properties (Gotcha 11) | The `@api` surface frozen deliberately before the first release, not discovered after it |

What a proper configuration adds over just doing it: the event names, the `detail` keys, the
`typeName` spelling and the `validate()` return shape all become Jest assertions, so the
next change that quietly breaks the builder contract fails a test instead of failing an
admin in Flow Builder with an unexplained error count.

---

## Core Concepts

### Runtime Component And Editor Component Are Separate

The screen component that runs in Flow and the custom property editor that runs in Flow Builder are distinct LWCs. Keep that boundary clear so runtime assumptions do not leak into the builder experience.

### Metadata Registration Drives The Builder Hook

The component metadata must point Flow Builder to the custom property editor through the `configurationEditor` relationship. If that registration is wrong, the editor never becomes part of the design-time experience.

| Consumer | Where `configurationEditor` goes | Shape |
|---|---|---|
| Flow **screen** component | `js-meta.xml`, as an attribute of `<targetConfig>` | `<targetConfig targets="lightning__FlowScreen" configurationEditor="c-volume-editor">` (lwc_guide L9187, L19104) |
| Flow **action** component (LWC) | `js-meta.xml`, as an attribute of `<targetConfig>` | `<targetConfig targets="lightning__FlowAction" configurationEditor="c-my-editor">` (lwc_guide L19071) |
| Invocable **Apex** action | the `@InvocableMethod` annotation — no XML | `@InvocableMethod(configurationEditor='c-html-email-editor')` (apexdev L5413; lwc_guide L9046) |

The value is a kebab-case module reference namespaced `c`, unless the org has its own
namespace (lwc_guide L9046, L9187).

### Builder APIs Are Design-Time Contracts

Custom property editors work with Flow Builder-facing APIs such as `inputVariables`, `builderContext`, `elementInfo`, and `validate()`. These are builder contracts, not general-purpose runtime APIs.

| Interface | Shape | What it is for |
|---|---|---|
| `inputVariables` | array of `{ name, value, dataType }` | current values of the consumer's inputs (lwc_guide L9676–9678) |
| `builderContext` | object of flow elements and resources; the guide's examples read `variables` | offering the admin resources that exist in this flow (lwc_guide L9680–9682) |
| `elementInfo` | `{ apiName, type }`, `type` ∈ `Screen` \| `Action` | disambiguating two instances of the same component (lwc_guide L9726–9733) |
| `genericTypeMappings` | array of `{ typeName, typeValue }` | the object chosen for a generic sObject input (lwc_guide L9754–9756) |
| `validate()` | `@api`, returns array of `{ key, errorString }` | blocking **Done** in the screen editor (lwc_guide L9731–9735) |

`automaticOutputVariables` is **not** part of this interface — the name appears nowhere in
the 676-page Lightning Web Components Developer Guide.

### Editor Events Are How Values Change

The editor communicates changes back to Flow Builder through the documented configuration-editor event pattern. A visually correct editor that never dispatches the right event is still broken.

| Event | `detail` keys | Fires when |
|---|---|---|
| `configuration_editor_input_value_changed` | `name`, `newValue`, `newValueDataType` | an input value changes |
| `configuration_editor_input_value_deleted` | `name` | a value is removed from an input |
| `configuration_editor_generic_type_mapping_changed` | `typeName`, `typeValue` | a generic sObject input's object changes |

All three require `bubbles: true` and `composed: true`; the guide's examples also set
`cancelable: false` (lwc_guide L9736–9762).

---

## Common Patterns

### Scalar Design-Time Editor

**When to use:** A component needs better labels, validation, or UX for a few configuration fields.

**How it works:** Expose a focused editor LWC that reads `inputVariables`, updates fields through the configuration-editor event, and implements `validate()` when builder-side validation matters.

**Why not the alternative:** For simple cases, default Flow property inputs are cheaper and clearer.

### Builder-Context-Aware Editor

**When to use:** The design-time experience depends on Flow metadata or available resources.

**How it works:** Read `builderContext` or related builder APIs and shape the editor UI around what Flow Builder already knows.

### Generic sObject Editor

**When to use:** One component must serve Account, Case and Lead without three bundles.

**How it works:** Declare `<propertyType name="T" .../>` and `type="{T}"` on the screen
component (or a generic `SObject` `@InvocableVariable` on the action), read the current
object from `genericTypeMappings`, and dispatch
`configuration_editor_generic_type_mapping_changed` when the admin picks one. See
`references/code-examples.md` § 2 and § 6.

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
| One component must serve several objects | Generic sObject input + `genericTypeMappings` | One bundle, one `typeName` contract |
| Editor is shared by a screen component and an action | Branch on `elementInfo.type` | `typeName` is spelled differently on the two surfaces |
| The question is whether an editor is warranted at all | `flow/flow-custom-property-editors` | That skill owns the design-time routing decision |

---

## Recommended Workflow

1. **Name the consumer and the registration site.** Screen component, LWC flow action, or
   Apex invocable action — the answer decides whether `configurationEditor` is a
   `<targetConfig>` attribute or an `@InvocableMethod` modifier. Fill in
   `templates/custom-property-editor-for-flow-template.md`; it is the worksheet the rest of
   the steps read from.
2. **Write down the four inbound payloads before any getter.** `inputVariables`,
   `genericTypeMappings`, `elementInfo`, `builderContext` — the shapes are tabulated in
   *Builder APIs Are Design-Time Contracts* above and shown as a concrete payload in
   `references/examples.md` § 3. Every read is a `find()`, never dot access.
3. **Build both bundles from `references/code-examples.md`.** § 1 is the runtime component
   with its `configurationEditor` wiring and `propertyType`, § 2 is the editor with the
   getter/setter interface, the three event dispatchers, the `builderContext` guard and the
   `{ key, errorString }` `validate()`. § 6 is the same editor wired to an
   `@InvocableMethod`. Reuse `templates/lwc/component-skeleton/` for the runtime component's
   loading and error states.
4. **Pin the contract with the six Jest tests in `references/code-examples.md` § 4** — the
   `detail` shape plus `bubbles`/`composed` on the value-changed event, the type-mapping
   event, the deletion event, `validate()` returning `[]`, `validate()` returning
   `{ key, errorString }` entries, and the missing-`builderContext` case. Use
   `templates/lwc/jest.config.js`. These are the tests that fail when someone renames an
   event or reshapes `validate()`.
5. **Run the checker over the source tree**:
   `python3 scripts/check_custom_property_editor_for_flow.py --manifest-dir force-app`
   (add `--strict` in CI). It flags a value-changed event whose `detail` is missing `name`,
   `newValue` or `newValueDataType`; a CPE with no `@api validate()`; a CPE bundle carrying
   page targets; a `configurationEditor` reference with no bundle in the tree;
   `inputVariables` written to in place; and a `builderContext` read with no guard.
6. **Verify in Flow Builder itself, in the order in `references/code-examples.md` § 5.**
   Drag the component onto a screen (does the editor render, or the default text boxes?),
   then click **Done** with a required field empty (does Flow Builder refuse?). Nothing
   short of those two clicks proves the registration and the save gate.
7. **Walk `references/gotchas.md` 4–12 before calling it done.** Each one looks correct in a
   two-component sandbox and fails on a real flow: the two registration sites, the two
   `typeName` spellings, the delete-versus-change event, the shadow-boundary flags, the
   empty `builderContext`, and the packaging one-way door.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] The runtime component and editor component are treated as separate LWCs.
- [ ] Metadata registration points Flow Builder to the custom editor correctly.
- [ ] `configurationEditor` is an attribute of `<targetConfig>` (screen/action LWC) or the `@InvocableMethod` modifier (Apex action) — not a child element, and not the component's own name.
- [ ] The editor reads and writes the intended builder-side contract.
- [ ] Configuration-change events are dispatched intentionally, with `bubbles: true` and `composed: true`.
- [ ] Clearing an input dispatches `configuration_editor_input_value_deleted`, not a change to `''`.
- [ ] `genericTypeMappings` uses `T` for a screen component and `T__` / `U__` for an action.
- [ ] `validate()` is `@api` and returns an array of `{ key, errorString }`; error strings are rendered by the editor, not left to Flow Builder.
- [ ] Every `builderContext` read is guarded, and a Jest case covers the unset case.
- [ ] The CPE bundle carries `apiVersion` + `isExposed` only — no page targets.
- [ ] `role="outputOnly"` was chosen deliberately for any property missing from the editor.
- [ ] The team rejected default Flow property inputs for a real UX reason.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **A valid runtime component can still have a broken builder experience** - the editor is a separate surface with separate failure modes.
2. **`configurationEditor` metadata is not optional once you choose a custom editor** - a missing link leaves the builder unaware of the LWC.
3. **Builder contracts are not generic runtime APIs** - `inputVariables` and `builderContext` belong to the editor context.
4. **An editor that never fires the change event is functionally inert** - visual polish does not matter if Flow Builder never receives the update.
5. **A property with `role="outputOnly"` never reaches the editor at all** - the same attribute that shapes runtime direction also controls CPE visibility.
6. **`validate()` blocks the admin but explains nothing** - Flow Builder renders the error count; the strings are the editor's job.

The full set with **What happens / When it occurs / How to avoid** and line cites is in
`references/gotchas.md`.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Editor design review | Findings on metadata hookup, builder APIs, and validation |
| Builder contract pattern | LWC design-time event and API guidance |
| Runtime/editor pairing plan | Mapping between runtime component inputs and editor controls |
| Deployable bundle pair | Runtime component + CPE, both `js-meta.xml` files, Jest suite, `package.xml` |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/code-examples.md` | You are about to write the bundles: runtime component + CPE, both `js-meta.xml` files, the event contract table, the six Jest tests, the `@InvocableMethod` variant, `package.xml`, deploy order and the three verification steps |
| `references/gotchas.md` | The editor does not load, values do not stick, `validate()` does not block, the object choice does not persist, or the editor throws on a new flow |
| `references/llm-anti-patterns.md` | Reviewing generated CPE code — the seven shapes assistants produce most often, with a detection hint each |
| `references/examples.md` | You want the short walk-throughs and a concrete view of the four inbound payloads before committing to getters |
| `references/well-architected.md` | Justifying the editor in a design review, or you need the official source behind a specific claim |
| `templates/custom-property-editor-for-flow-template.md` | Step 1 of the workflow — the worksheet that becomes the written contract |
| `scripts/check_custom_property_editor_for_flow.py` | Step 5 — static checks over a source tree, `--strict` in CI |

---

## Related Skills

Ownership split, so the two property-editor skills do not duplicate each other:
**this skill owns the LWC implementation and its testing** — the Flow Builder JavaScript
interface, the events, `validate()`, the `js-meta.xml` and Jest. **`flow/flow-custom-property-editors`
owns when to build one at all** — whether the default pane is genuinely insufficient, and
what the design-time contract owes the admin.

- `flow/flow-custom-property-editors` - read first, when the question is still "do we need a CPE?"; come back here to build it.
- `apex/invocable-methods` - owns the `@InvocableMethod` contract, including the `configurationEditor` modifier and the rest of the modifier list; read it before changing the Apex side.
- `lwc/lwc-in-flow-screens` - owns the runtime `lightning__FlowScreen` component itself: `FlowAttributeChangeEvent`, runtime `validate()`, flow navigation.
- `lwc/component-communication` - owns event propagation itself: why `bubbles` and `composed` matter and how they interact with the shadow boundary.
- `lwc/lwc-testing` - use to go beyond the six contract tests in this skill's code examples.
- `lwc/lwc-app-builder-config` - use when the surface is Lightning App Builder design attributes rather than a Flow CPE.
- `lwc/lifecycle-hooks` - use when the editor or runtime component has general LWC lifecycle issues.
- `admin/flow-for-admins` - use when the better answer may be a simpler declarative Flow design with no custom LWC.
