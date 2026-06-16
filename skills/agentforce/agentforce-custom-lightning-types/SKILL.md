---
name: agentforce-custom-lightning-types
description: "Use when overriding the default UI of an Agentforce agent action's Apex input or output with your own Lightning web components via a LightningTypeBundle (schema.json + editor.json/renderer.json, lightning__AgentforceInput / lightning__AgentforceOutput targets, the @apexClassType binding). NOT for standard agent actions with primitive inputs/outputs (only Apex-class input/output can be overridden), NOT for Flow screen custom property editors (use flow/flow-custom-property-editors), and NOT for general LWC-in-Lightning-page work (use lwc/* skills)."
category: agentforce
salesforce-version: "Summer '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "the agent renders my Apex action output as raw JSON or plain text and I want a branded card"
  - "how do I customize the input form an Agentforce agent shows for a custom action"
  - "building a LightningTypeBundle to override an agent action's input and output UI"
  - "how do editor and renderer LWCs work for a custom Lightning type"
  - "my custom Lightning type isn't overriding the agent UI even though I deployed it"
tags:
  - agentforce
  - lightning-types
  - lightningtypebundle
  - agent-action-ui
  - custom-renderer
inputs:
  - "The agent action (Apex @InvocableMethod) whose input or output UI you want to customize"
  - "The backing Apex input/output class, with fields to expose"
  - "Target channel(s): Employee agent desktop/mobile, Service agent Enhanced Chat, or Experience Builder"
  - "Desired UI behavior: display card, interactive input form, or collection/list rendering"
outputs:
  - "A LightningTypeBundle: lightningTypes/{type}/schema.json plus a channel folder with editor.json and/or renderer.json"
  - "Editor and/or renderer LWCs targeting lightning__AgentforceInput / lightning__AgentforceOutput"
  - "A deployment-ready package.xml at API 64.0+ and an Apex class annotated for projection"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-06-15
---

# Agentforce Custom Lightning Types

This skill activates when a practitioner wants to replace the generic UI an Agentforce agent shows for an action's input or output with a purpose-built Lightning web component. The mechanism is a `LightningTypeBundle` — a deployable metadata bundle of a JSON schema plus channel-scoped editor/renderer overrides — and it only applies to agent actions whose input or output is an **Apex class**.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm the action's input/output is an Apex class.** The platform can override the UI *only* for agent actions that use Apex classes as input or output. An action that takes or returns primitives (String, Integer) directly cannot be customized this way — the first step is often refactoring the invocable to use a wrapper class.
- **Decide input vs output.** An `editor` (`editor.json`) overrides the UI used to *enter/edit* data (the action's input parameter). A `renderer` (`renderer.json`) overrides the UI that *displays* data (the action's output parameter). A bundle can contain one or both.
- **Identify the target channel(s).** The override only applies on the channel whose folder you ship. A bundle with no folder for a given surface falls back to the default UI there. See the channel table in Core Concepts — `renderer.json` is not supported in `experienceBuilder`.
- **Know the API floor.** `LightningTypeBundle` requires Metadata API version **64.0 or later**. The official docs do not stamp this feature as GA or Beta — do not assert a maturity level the release notes don't state.

---

## Core Concepts

### The bundle: schema, editor, renderer

A custom Lightning type is built from three artifacts:

- **Schema** (`schema.json`, required) — defines the data structure and validation rules using the JSON Schema specification. It binds to a backing Apex class via the `lightning:type` key, which is syntactic sugar for JSON Schema's `$ref`:

  ```json
  {
    "title": "Flight Response",
    "description": "A flight result returned by the booking action",
    "lightning:type": "@apexClassType/c__Flight"
  }
  ```

  The platform introspects the referenced Apex class and projects the property list from its `@AuraEnabled` member variables — so the **Apex class is the single source of truth**. You don't hand-author the field list in `schema.json`.

- **Editor** (`editor.json`) — the input UI component. The LWC declares the `lightning__AgentforceInput` target.

- **Renderer** (`renderer.json`) — the output/display UI component. The LWC declares the `lightning__AgentforceOutput` target.

### Directory layout

The bundle lives under `lightningTypes/`, with channel-scoped editor/renderer files nested in a channel folder:

```
force-app/main/default/
├── lightningTypes/
│   ├── flightResponse/
│   │   ├── schema.json
│   │   └── lightningDesktopGenAi/
│   │       └── renderer.json
│   └── flightFilter/
│       ├── schema.json
│       └── lightningDesktopGenAi/
│           └── editor.json
└── lwc/
    ├── flightDetails/        (renderer LWC, target lightning__AgentforceOutput)
    └── flightFilter/         (editor LWC,   target lightning__AgentforceInput)
```

### The componentOverrides contract

Both `editor.json` and `renderer.json` map a schema scope to an LWC by name. The key `"$"` means a **top-level (whole-type) override**; a property name keys a single-field override; `"collection"` (renderer only) overrides how a list of the type renders.

```json
// renderer.json — replace the whole-type output UI with c/flightDetails
{ "renderer": { "componentOverrides": { "$": { "definition": "c/flightDetails" } } } }
```

```json
// editor.json — replace the whole-type input UI with c/flightFilter
{ "editor": { "componentOverrides": { "$": { "definition": "c/flightFilter" } } } }
```

Use the `c/` prefix for org metadata and the `isv/` prefix for components delivered in a managed package.

### Channels

The channel folder name scopes where the override applies:

| Channel folder | Where the override applies |
|---|---|
| `lightningDesktopGenAi` | Agentforce Employee agent in Lightning Experience (desktop) |
| `lightningMobileGenAi` | Employee agent on mobile; Service agent via Enhanced Chat v2 on mobile |
| `enhancedWebChat` | Agentforce Service agent via Enhanced Chat v2 |
| `experienceBuilder` | Experience Builder (`renderer.json` is **not** supported here) |

---

## Common Patterns

### Branded output card (renderer)

**When to use:** the agent returns a structured Apex result (an order, a flight, a case summary) and the default rendering shows it as raw fields or JSON.

**How it works:** annotate the output Apex class fields with `@AuraEnabled`; create a `schema.json` bound to it via `@apexClassType/c__Flight`; build a renderer LWC (`lightning__AgentforceOutput`) that reads the `@api value` payload; point `renderer.json`'s `"$"` override at it; ship it in the channel folder for the surfaces you support.

**Why not the alternative:** stuffing presentation hints into the action's `description` or returning pre-formatted strings from Apex couples your data contract to one display and defeats the agent's ability to reason over typed fields.

### Interactive input form (editor)

**When to use:** the action needs richer input than the default form — a date-range picker, dependent dropdowns, validation beyond the schema.

**How it works:** build an editor LWC (`lightning__AgentforceInput`) that exposes `@api value` and `@api schema`, and dispatches a `valuechange` event when the user edits, so the host binds the data in real time. Reference it from `editor.json`'s `"$"` override.

**Why not the alternative:** the default editor can't enforce cross-field rules or custom widgets; pushing that logic into Apex validation only surfaces errors *after* submission.

### Collection rendering

**When to use:** the action returns a list of the type (e.g. several hotels) and you want a consistent list/grid rather than per-item default cards.

**How it works:** add a `"collection"` key to the renderer's `componentOverrides` pointing at an LWC that receives the array, alongside (or instead of) the `"$"` single-item override.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Action input/output is a primitive (String/Integer) | Refactor the invocable to use an Apex wrapper class first | Only Apex-class input/output can be overridden |
| You only need to change how a *result* looks | Renderer-only bundle (`renderer.json`) | Output display is the renderer's job |
| You need a custom *input* widget or cross-field validation | Editor bundle (`editor.json`) with a `valuechange`-dispatching LWC | The editor is the design-time/input surface |
| Same type, multiple surfaces (desktop + mobile + chat) | One bundle, multiple channel folders | Overrides are channel-scoped; missing folder = default UI |
| Component ships in a managed package | Use the `isv/` definition prefix | `c/` is org metadata only |
| Need custom UI in Experience Builder output | Not available via `renderer.json` | `renderer.json` is unsupported in `experienceBuilder` |

---

## Recommended Workflow

1. **Confirm eligibility** — verify the agent action's input or output parameter is an Apex class (refactor to a wrapper class if it isn't).
2. **Prepare the Apex type** — annotate every field to expose with `@AuraEnabled`; mark the class `global` and top-level; add `@JsonAccess(serializable='always' deserializable='always')`.
3. **Author `schema.json`** — set `title`/`description` and bind to the Apex class with `"lightning:type": "@apexClassType/c__ClassName"`. Do not duplicate the field list; the platform projects it.
4. **Build the LWC(s)** — a renderer LWC (`lightning__AgentforceOutput`) for output and/or an editor LWC (`lightning__AgentforceInput`) for input, exposing `@api value` (and `@api schema`); editors dispatch `valuechange`.
5. **Wire the override** — create the channel folder (e.g. `lightningDesktopGenAi/`) and add `editor.json` and/or `renderer.json` with a `"$"` (or `"collection"`) override pointing at `c/<lwc>`.
6. **Deploy and verify** — deploy the `LightningTypeBundle` and `lwc` at API 64.0+; open the agent on each targeted channel and confirm the custom UI renders (and falls back gracefully where no folder exists).

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] The action's input/output is an Apex class, not a primitive
- [ ] Every exposed Apex field has `@AuraEnabled`; the class is `global`, top-level, with `@JsonAccess`
- [ ] `schema.json` binds via `@apexClassType/` and does **not** re-declare the projected fields
- [ ] The LWC declares the correct target (`lightning__AgentforceInput` for editor, `lightning__AgentforceOutput` for renderer)
- [ ] `componentOverrides` uses the right scope key (`"$"`, a property name, or `"collection"`) and the `c/` or `isv/` prefix
- [ ] A channel folder exists for every surface that needs the override; no `renderer.json` placed under `experienceBuilder`
- [ ] `package.xml` targets API `64.0` or later; the bundle has a `masterLabel`

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Only Apex-class actions are overridable** — a custom Lightning type silently has no effect on an action whose input/output is a primitive or a standard type. The fix is upstream in the Apex signature, not in the bundle.
2. **Channel-scoped fallback is silent** — if you ship `lightningDesktopGenAi/` but the agent also runs on mobile, the mobile surface quietly uses the default UI. There's no error; the override just doesn't appear.
3. **`renderer.json` is unsupported in `experienceBuilder`** — placing one there does not customize the output; only editor overrides apply on that surface.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| `lightningTypes/{type}/schema.json` | JSON-Schema type bound to the backing Apex class via `@apexClassType/` |
| `lightningTypes/{type}/{channel}/editor.json` / `renderer.json` | Channel-scoped `componentOverrides` mapping a scope to an LWC |
| Editor / renderer LWC bundle | `lightning__AgentforceInput` / `lightning__AgentforceOutput` component exposing `@api value` |
| `package.xml` | Deployment manifest with `<name>LightningTypeBundle</name>` at version `64.0`+ |

---

## Related Skills

- `agentforce/custom-agent-actions-apex` — design the `@InvocableMethod` and the Apex input/output classes this skill overrides the UI for.
- `lwc/lwc-app-builder-config` — declare the component `targets` (including `lightning__Agentforce*`) and `@api` properties in the LWC `js-meta.xml`.
- `flow/flow-custom-property-editors` — the *different* mechanism for customizing a Flow screen/action config UI; do not confuse it with LightningTypeBundle.
