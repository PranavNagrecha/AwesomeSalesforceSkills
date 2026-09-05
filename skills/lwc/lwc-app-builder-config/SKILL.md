---
name: lwc-app-builder-config
description: "Use when an LWC needs to appear, be configured, and be constrained inside Lightning App Builder, Experience Builder, Home Page, or Flow screens via its js-meta.xml file — including isExposed, targets, targetConfigs, supportedFormFactors, objects scoping, and admin-facing design attributes. Triggers: 'lwc not appearing in app builder', 'expose lwc to record page', 'design attribute datasource picklist', 'supportedformfactors mobile small', 'targetconfigs for record page vs app page', 'masterlabel vs description', 'apex dynamic picklist for a design attribute', 'js-meta.xml deploy fails'. NOT for page-level config like visibility filters or Dynamic Forms — use admin/lightning-app-builder-advanced. NOT for a Flow custom property editor — use lwc/custom-property-editor-for-flow."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Reliability
  - Security
triggers:
  - "my lwc is not showing up in lightning app builder"
  - "how do i expose an lwc to a record page but not an app page"
  - "design attribute with a dynamic picklist of field names"
  - "restrict lwc to small form factor only on mobile"
  - "targetconfigs differ between record page and app page"
  - "masterlabel vs description on lwc meta xml"
  - "objectapiname injection on record page lwc"
  - "one lwc bundle reused across record, app, home, and experience"
  - "write a js-meta.xml that exposes one component to record, app, home, and experience pages"
  - "build an apex dynamicpicklist class for an lwc design attribute datasource"
  - "scope an lwc to only case and account record pages"
  - "add min and max to an integer design attribute so admins cannot enter 500"
  - "test a configurable lwc in jest when the default lives in the meta xml"
  - "deploy failed on my lwc meta xml supportedformfactor tag"
  - "why can admins drop my component on any object"
  - "package my lwc and now i cannot remove a target"
tags:
  - lwc-app-builder-config
  - meta-xml
  - targets
  - target-configs
  - design-attributes
  - form-factors
  - experience-builder
  - record-page
inputs:
  - "which surfaces the component must appear on (record page, app page, home page, utility bar, Experience Cloud, Flow screen)"
  - "which sObjects the component is valid against, if any"
  - "supported form factors (Large for desktop, Small for phone) per target"
  - "admin-configurable inputs needed (labels, defaults, datasources, required flags)"
  - "whether Apex-backed dynamic picklists are needed for any design attribute"
  - "whether the bundle will ship inside a managed package or land in a live Experience Cloud site"
outputs:
  - "a deploy-ready `<bundle>.js-meta.xml` with correct isExposed, targets, targetConfigs, objects, and property blocks"
  - "the `@api` property set the JS class must declare to match every `property name` in the meta file"
  - "an optional `VisualEditor.DynamicPickList` Apex class plus its test for `apex://` datasources"
  - "guidance on admin-facing labels, descriptions, and datasource wiring"
  - "checker output flagging meta-xml smells (hidden component, wrong form-factor tag, invalid types, orphan @api)"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# LWC App Builder Config

Use this skill whenever the functional behavior of the LWC is fine but the component either does not appear in a builder, appears in the wrong builder, or offers admins the wrong set of configuration knobs. The js-meta.xml file is the single source of truth that controls exposure, surface targeting, per-surface configuration, form-factor fit, and the admin UX inside App Builder, Experience Builder, Home Page, Utility Bar, and Flow.

Every component folder must include a `componentName.js-meta.xml` file; without one, a push fails (`create-components-meta-file` L715–L723).

---

## Before Starting

Gather this context before editing a `.js-meta.xml`:

- Which surfaces must this component render on — Record Page, App Page, Home Page, Experience Cloud page, Utility Bar, Custom Tab, Flow Screen, or several of these?
- Which sObjects is the component valid against? A record-page `targetConfig` with no `<objects>` supports every UI-API-supported object (`targets-lightning-record-page` L19363), which is almost always wider than intended.
- Which form factors must be supported — `Large` (desktop), `Small` (phone), or both? App and record pages support both; Home pages support only `Large` (`use-config-form-factors` L9795).
- What admin-tunable inputs does the component need, and are any of them field-name pickers, picklist-value pickers, or free-text with defaults?
- Will this bundle ship in a managed package or be placed in a live Experience Cloud site? That decision closes doors permanently — see the one-way-door table below.

---

## Questions to Ask Before Configuring

Ask these before you write the file. Each one traces to a gotcha in `references/gotchas.md`; skipping them produces a meta.xml that deploys and then cannot be changed.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which surfaces, and does each one need its own set of admin knobs — or the same set?" | `<targets>` decides where the component appears; `<targetConfigs>` decides what admins can tune there. They are separate lists and one target can carry a different property set than another. | The exact `targetConfig` split, so admins never see a Utility Bar knob on a record page |
| "For record pages, which objects — and can you name them, or is 'all of them' the real answer?" | Omitting `<objects>` is not a neutral default: the component becomes droppable on every UI-API-supported object (L19363). Once placed on an object's page, that object tag can no longer be removed (L9905). | The `<object>` list, and an explicit decision recorded when it is deliberately unscoped |
| "Phone, desktop, or both — per surface?" | `<supportedFormFactors>` is per `targetConfig`, and once the component is in use you can only *increase* the set, never shrink it (L9806, L9909). Home pages cannot take `Small` at all (L9795). | The correct form-factor set on day one, chosen while it is still reversible |
| "For each admin input: what type, what default, and what is the legal range?" | `type` is limited to `Boolean`/`Integer`/`String` on App Builder targets; `min`/`max` apply only to `Integer`; `placeholder` and `datasource` only to `String` (L18972–L18983). Required properties with no default make the component show as invalid the moment it is dropped (L9899). | A property table that App Builder can actually render, with defaults that keep placements valid |
| "Do any of those inputs depend on org schema — field names, record types, values that change after ship?" | A static CSV `datasource` freezes the list at deploy time. `datasource="apex://Class"` calls a `VisualEditor.DynamicPickList` at design time and can read `DesignTimePageContext.entityName`/`pageType` to vary by page. | The Apex class (and its test), or a documented decision that the static list is genuinely stable |
| "Is this going into a managed package, or onto a page in a published Experience Cloud site?" | Both close doors: `isExposed` can only go `false → true` in a released package, and an exposed packaged component can never drop a target or an `@api` property (L7812, L7818). Sites forbid adding `required=true` or tightening `min`/`max` (L8128–L8137). | The list of decisions that must be right now because they cannot be undone later |
| "How will we know the component is configured correctly — before an admin finds out?" | App Builder validates shape, not intent: it will not tell you that `<objects>` is missing, that a `property name` has no matching `@api` field, or that the Apex datasource class was never deployed. | A run of `scripts/check_lwc_app_builder_config.py` in CI and a Jest test that pins the defaults |

What a proper configuration adds over just exposing the component: admins see only the knobs that make sense on the surface they are editing, the component cannot be dropped where its data model does not apply, and every irreversible choice (packaging exposure, form factors, min/max) is made deliberately instead of discovered later.

---

## Core Concepts

The meta.xml file is small, but every element changes how the builder treats the bundle. Six concepts cover almost every real situation.

### `isExposed` Controls Builder Visibility

`<isExposed>false</isExposed>` means the component is not exposed in the builders. To use it in a builder, set `isExposed` to `true` **and** define at least one `<target>` (`reference-configuration-tags` L18711–L18712). Both halves are required — `isExposed=true` with an empty `<targets>` gets you nothing.

### `targets` Enumerate The Surfaces

`<targets>` holds one `<target>` per surface. The guide enumerates these values (L18721–L18749):

| Family | Values |
|---|---|
| Lightning pages | `lightning__AppPage`, `lightning__HomePage`, `lightning__RecordPage`, `lightning__Tab`, `lightning__UtilityBar`, `lightning__UrlAddressable`, `lightning__VoiceExtension` |
| Actions | `lightning__RecordAction`, `lightning__GlobalAction` |
| Flow | `lightning__FlowScreen`, `lightning__FlowAction` |
| Experience Cloud | `lightningCommunity__Default`, `lightningCommunity__Page`, `lightningCommunity__Page_Layout`, `lightningCommunity__Theme_Layout` |
| Embedded Service Chat | `lightningSnapin__ChatHeader`, `lightningSnapin__ChatMessage`, `lightningSnapin__MessagingPreChat`, `lightningSnapin__MessagingHeader`, `lightningSnapin__Minimized`, `lightningSnapin__PreChat` |
| Other surfaces | `analytics__Dashboard`, `lightningStatic__Email`, `lightning__Inbox`, `lightning__ECSFSApp`, `lightning__EnablementProgram`, `lightning__ServiceDocument`, `lightning__PropertyEditor`, `lightning__AgentforceInput`, `lightning__AgentforceOutput` |

### `capabilities` Declare What The Component Can Do

A capability is something a component can *do*, as opposed to a target, which is where it can be *used* (L18701). `<capabilities>` holds one `<capability>` per value; the guide documents five (L18704–L18709):

| Value | What it enables |
|---|---|
| `lightningCommunity__RelaxedCSP` | A managed-package component may run in an Experience Builder site with Lightning Locker disabled. Without it, such components are disabled in the Components panel for those sites — and nested components need the tag too. |
| `lightning__dynamicComponent` | The component may dynamically instantiate other components (`<lwc:component lwc:is={…}>`). |
| `lightning__ServerRenderable` | Server-side rendering with islands architecture; LWR Experience Builder sites only. |
| `lightning__ServerRenderableWithHydration` | SSR with hydration; LWR Experience Builder sites only. |
| `lightning__ServiceCloudVoiceToolkitApi` | Required by any component using `lightning-service-cloud-voice-toolkit-api`. |

### `targetConfigs` Customize Per-Surface Behavior

A `<targetConfig targets="…">` block configures one or more targets and defines their properties. Its `targets` attribute takes a comma-separated list, and every value must match a page type listed under `<targets>` (L18769, L18966). Inside a block go `<property>` elements, `<supportedFormFactors>`, and — for record pages only — `<objects>`.

Which subtags a `targetConfig` accepts depends on the target, and the differences are real:

| Target | `property` | `objects` | `supportedFormFactors` | Target-only attributes |
|---|---|---|---|---|
| `lightning__RecordPage` | yes | yes (L19363) | yes | — |
| `lightning__AppPage` | yes | no | yes | `event` + `schema` for Dynamic Interactions (L18984–L18992) |
| `lightning__HomePage` | yes | no | yes (`Large` only in practice, L9795) | — |
| `lightning__UtilityBar` | yes | no | not documented | — |
| `lightning__Tab` | **no** | no | **no** (L7987) | — |
| `lightning__RecordAction` | **no** (L19307) | no | yes, but `Small` is unsupported (L19313) | `actionType` = `ScreenAction` \| `Action` |
| `lightning__FlowScreen` | yes | no | no | `configurationEditor`, `propertyType`, `stylingHook`, `role`, `flowRole` |
| `lightningCommunity__Default` | yes | no | no | `filter`, `exposedTo`, `screenResponsive`, `translatable` |

### Design Attributes Give Admins Typed Inputs

`<property>` takes `name` (must match the `@api` property in the JS class), `type`, `label`, `description`, `default`, `required`, and — depending on type — `datasource`, `min`, `max`, `placeholder`.

The valid `type` set is **per target**, not global:

| Target | Documented `type` values |
|---|---|
| `lightning__RecordPage`, `lightning__AppPage`, `lightning__HomePage`, `lightning__Inbox`, `lightning__UtilityBar`, `lightning__VoiceExtension` | `Boolean`, `Integer`, `String` (L18972–L18975, L19197–L19199, L19351–L19353) |
| `lightningCommunity__Default` | `Boolean`, `Integer`, `String`, `Color`, `ContentReference` (L18775–L18779), plus custom Lightning types |
| `lightningStatic__Email` | `Boolean`, `Integer`, `String`, `Color`, `HorizontalAlignment`, `VerticalAlignment` (L18870–L18876) |
| `lightning__FlowScreen` | `Boolean`, `Integer`, `String`, `Double`, `Date`, `DateTime`, `apex://ns.Class`, `@salesforce/schema/Object` (L19110–L19117) |
| `analytics__Dashboard` | the common types plus `Measure` and `Dimension` when `<hasStep>true</hasStep>` (L7872) |

`datasource` renders the field as a picklist and is supported only when `type` is `String`. It takes either static values (`datasource="value1,value2,value3"`) or an Apex class (`datasource="apex://MyCustomPickList"`) — L18976. Lightning App Builder does not support the `Map`, `Object`, or `java://` complex types (L9908).

### Record-Page Scoping And Auto-Injected Context

`<objects>` limits the component to a set of objects and **works only inside a `targetConfig` configured for `lightning__RecordPage`**; specify it once per `targetConfig`; it does not support external objects; and if you omit it the component supports all supported objects (L19363–L19368).

Three public properties are populated by the platform rather than by an admin, and none of them is declared in the meta file — you declare them with `@api` in the JS class:

- `recordId` — set to the 18-character record ID when the component is placed in an explicit record context; unset everywhere else, so the component must not depend on it (L7888, L7893).
- `objectApiName` — set to the API name of the record's object in the same circumstances (L7912–L7913).
- `flexipageRegionWidth` — receives the width of the App Builder region; CSS class values are `SMALL`, `MEDIUM`, `LARGE` (L7925–L7931).

Experience Builder does **not** auto-bind `recordId` or `objectApiName`; an admin types `{!recordId}` into the component's Record ID property field (L7894, L7900, L7914).

### One-Way Doors

These changes cannot be reversed once the component is in use. Decide them before the first deploy that matters.

| Door | Rule | Source |
|---|---|---|
| Packaged exposure | `isExposed` can only change from `false` to `true` after a package is released | L7812 |
| Packaged surface area | An exposed component in a published managed package cannot drop a configuration target or an `@api` property — even one added after the last publish | L7818 |
| Form factors | Once in use on a Lightning page you can only increase supported form factors, never decrease them | L9806, L9909 |
| Object scope | You cannot remove an `<object>` tag while the component is in use on a record page for that object | L9905 |
| Page type support | You cannot remove page-type support while the component is in use on that page type | L9906 |
| Numeric range | You cannot change `min` or `max` while the component is in use on a Lightning page | L9907 |
| Action type | `actionType` cannot change between `Action` and `ScreenAction` after deploy | L19323 |
| Site property rules | In a site or managed package you cannot add a `required=true` property, remove a property, tighten `min`, or lower `max` | L8128–L8137 |

---

## Common Patterns

### Multi-Surface Reusable Bundle

**When to use:** One component should appear on Case and Account record pages, on a custom App Page, on the Home page, and on an Experience Cloud page.

**How it works:** List every target in `<targets>` (including both `lightningCommunity__Page` and `lightningCommunity__Default` for Experience Cloud), then create one `<targetConfig>` per surface. Scope the record-page target with `<objects>`, give the App Page target its own property set, and keep Home at `Large` only. The full bundle is in `references/code-examples.md`.

**Why not the alternative:** Cloning the bundle per surface multiplies maintenance cost and drifts admin UX. A single bundle with per-surface `targetConfig` keeps behavior consistent.

### Apex-Backed Dynamic Picklist

**When to use:** Admins need to pick a field name, record-type developer name, or any other list that depends on org schema.

**How it works:** Extend `VisualEditor.DynamicPickList` in Apex, override `getValues()` and `getDefaultValue()`, and reference it as `datasource="apex://MyPicklistProvider"`. Add a `VisualEditor.DesignTimePageContext` constructor parameter when the list must differ by page type or object — the context exposes `pageType` and `entityName` (Apex Reference Guide L247696–L247782).

**Why not the alternative:** A static CSV datasource cannot reflect org-specific schema, and hardcoding the values inside the LWC forces a deploy for every change. The cost is one Apex invocation when the property panel opens, plus a 200-value display ceiling (L248023).

### Experience Cloud Pairing

**When to use:** The component must be draggable in Experience Builder *and* expose editable properties.

**How it works:** List `lightningCommunity__Page` (drag-and-drop into the Components panel) and `lightningCommunity__Default` (editable properties) as two targets, and put the `<property>` elements in a `targetConfig` whose `targets` is `lightningCommunity__Default` (L8106–L8110, L18811–L18812). `lightningCommunity__Page` on its own supports no properties.

**Why not the alternative:** Declaring only `lightningCommunity__Page` produces a component admins can place but cannot configure; declaring only `lightningCommunity__Default` produces properties on a component that never appears in the Components panel.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Expose on record pages only, for a specific sObject | `lightning__RecordPage` target + `<objects>` with that object | Without it the component supports every UI-API object (L19363) |
| Expose everywhere the component is generic | Multiple `<target>` entries, each with its own `<targetConfig>` | One bundle, per-surface admin UX |
| Admin needs to pick a field at design time | `<property type="String" datasource="apex://FieldPickProvider"/>` | `Picklist` is not a documented type; `String` + `datasource` is the supported shape |
| Admin needs a fixed small list (High/Medium/Low) | `<property type="String" datasource="high,medium,low" default="medium"/>` | Static CSV needs no Apex (L18976) |
| Admin needs a bounded number | `<property type="Integer" min="1" max="50" default="10"/>` | `min`/`max` apply only to `Integer` (L18980–L18981) — and freeze once placed (L9907) |
| Component must work on phone as well as desktop | `<supportedFormFactors><supportedFormFactor type="Small"/><supportedFormFactor type="Large"/></supportedFormFactors>` inside the relevant `targetConfig` | The child tag is `supportedFormFactor` with a `type` attribute (L18994–L18998), and the set is per target |
| Component belongs on the Home page | Omit `Small` from the Home `targetConfig` | Home pages support only the `Large` form factor (L9795) |
| Admin needs a colour picker | Only on `lightningCommunity__Default` or `lightningStatic__Email` | `Color` is not in the documented type list for App Builder targets |
| Admin config outgrows typed properties in Flow | `configurationEditor` on the Flow `targetConfig` | Owned by `lwc/custom-property-editor-for-flow` |

---

## Recommended Workflow

1. Answer the seven questions above and write the surface × property matrix down — one row per target, one column per admin input, plus the object list and form factors. That matrix *is* the meta file.
2. Copy the bundle skeleton from `templates/lwc/component-skeleton/` and the worked multi-target file from `references/code-examples.md`; set `apiVersion` (63.0 is the latest release mapped in `create-version-alignment` L856 — an org can accept up to its own current release, L813).
3. Declare an `@api` field in the JS class for every `property name` in the meta file, plus `recordId` / `objectApiName` / `flexipageRegionWidth` if the component uses record or region context. Give each one a JS-side initializer — Jest never reads the meta file (`unit-testing-using-jest-create-tests` L12326).
4. If any property needs a schema-driven list, write the `VisualEditor.DynamicPickList` class and its test alongside the bundle (both are in `references/code-examples.md`), and remember the Apex class must be in the same deploy or the property panel breaks.
5. Run `python3 skills/lwc/lwc-app-builder-config/scripts/check_lwc_app_builder_config.py --manifest-dir force-app/main/default` and fix every ERROR; add `--strict` in CI to fail on WARNs too.
6. Run the Jest suite (`npm run test:unit`) to pin the property defaults and setter behaviour, then deploy Apex before the bundle and drop the component from each configured surface in App Builder / Experience Builder.
7. Before the change ships to a package or a live site, re-read the one-way-door table and confirm nothing in this deploy is a door you did not mean to close.

---

## Review Checklist

- [ ] `<isExposed>true</isExposed>` is present **and** `<targets>` is non-empty.
- [ ] `<apiVersion>` is set — Spring '25 and later require it to save changes (L796–L798).
- [ ] Every `targetConfig targets="…"` value also appears inside `<targets>`.
- [ ] Every `<property name="x">` has a matching `@api x` in the JS class.
- [ ] `<property type="…">` uses only the values documented for that target — no `Color` on App Builder targets, no `Picklist` anywhere.
- [ ] `<objects>` appears only inside a `lightning__RecordPage` `targetConfig`, and record-page exposure is either scoped or scoped-by-decision.
- [ ] Form factors use `<supportedFormFactor type="…"/>`, live inside a `targetConfig`, and omit `Small` for Home pages.
- [ ] Every `required="true"` property also has a `default` (L9899).
- [ ] Every `apex://` datasource names a class present in the same deployment.
- [ ] `<masterLabel>` and `<description>` are filled in and read well in the builder.

---

## Salesforce-Specific Gotchas

The full set, with what happens / when it occurs / how to avoid, is in `references/gotchas.md`. In one line each:

1. `supportedFormFactor` — not `supported` — is the child tag, and the attribute is `type`.
2. `Color` is not a documented App Builder property type; it is an Experience Cloud and Email Builder type.
3. `<objects>` outside a record-page `targetConfig` scopes nothing.
4. Omitting `<objects>` opens the component to every UI-API-supported object.
5. `lightning__Tab` accepts neither `property` nor `supportedFormFactor`.
6. Form factors, object tags, page-type support and `min`/`max` all freeze once the component is placed.
7. A packaged, exposed component can never drop a target or an `@api` property.
8. Experience Builder does not auto-bind `recordId`; an admin must type `{!recordId}`.
9. A dynamic picklist displays only its first 200 values unless `containsAllRows` says otherwise.
10. Jest never reads the meta file, so a green test proves nothing about a meta-file default.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Deploy-ready meta.xml | `<bundle>.js-meta.xml` with correct `isExposed`, `targets`, `targetConfigs`, `objects`, form factors, and `property` blocks |
| Matching JS class | `@api` field per design attribute, plus `recordId` / `objectApiName` / `flexipageRegionWidth` where used |
| Apex datasource + test | `VisualEditor.DynamicPickList` subclass and its Apex test class, when a property needs a schema-driven list |
| Jest suite | Tests that pin property defaults, setter coercion, and per-region rendering |
| Admin UX plan | The set of labels, descriptions, defaults, and datasources the builder will show |
| Checker report | Findings on hidden components, wrong form-factor tags, invalid property types, orphan `@api` names, missing datasource classes |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/code-examples.md` | You are building: the complete `pipelineSummary` bundle (html/js/js-meta.xml), the `VisualEditor.DynamicPickList` class and its Apex test, the Jest suite, `package.xml`, deploy order, and what App Builder does and does not validate |
| `references/gotchas.md` | The component deploys but is invisible, unconfigurable, droppable everywhere, or a change is suddenly refused |
| `references/llm-anti-patterns.md` | Reviewing a generated `js-meta.xml`, or self-checking your own before it ships |
| `references/examples.md` | You want one scenario end to end — the multi-surface bundle, the Apex datasource, or the Swiss-army-knife failure mode |
| `references/well-architected.md` | Mapping the choice to pillars, or checking which official source backs a claim |
| `templates/lwc-app-builder-config-template.md` | Filling in the surface × property matrix before you write the meta file |
| `scripts/check_lwc_app_builder_config.py` | Auditing an LWC tree: `--manifest-dir <dir>`, add `--strict` in CI |

---

## Related Skills

- `lwc/lwc-base-component-recipes` — once the component is exposed, use base components inside it for standard admin UX.
- `lwc/custom-property-editor-for-flow` — owns custom property editors; use when Flow-side config outgrows typed design attributes.
- `lwc/experience-cloud-lwc-components` — owns Experience Cloud specifics: CSP levels, LWR, theming, custom property types.
- `lwc/lwc-in-flow-screens` — owns Flow-screen component design: `role`, `propertyType`, output attributes, `FlowAttributeChangeEvent`.
- `lwc/lwc-quick-actions` — owns `lightning__RecordAction` components: headless vs screen actions, `CloseActionScreenEvent`, `invoke()`.
- `lwc/lwc-offline-and-mobile` — owns what actually happens on the `Small` form factor at runtime.
- `lwc/component-communication` — owns the `event` / `schema` payload design once Dynamic Interactions are declared here.
- `lwc/lwc-testing` — owns Jest depth beyond the default-pinning tests in this skill.
