---
name: lwc-app-builder-config
description: "Use when an LWC needs to appear, be configured, and be constrained inside Lightning App Builder, Experience Builder, Home Page, or Flow screens via its js-meta.xml file — including isExposed, targets, targetConfigs, supportedFormFactors, objects scoping, and admin-facing design attributes. Triggers: 'lwc not appearing in app builder', 'expose lwc to record page', 'design attribute datasource picklist', 'supportedformfactors mobile small', 'targetconfigs for record page vs app page', 'masterlabel vs description'. NOT for custom property editors for Flow (see `custom-property-editor-for-flow`), and NOT for Experience Cloud theming at the page level."
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
outputs:
  - "a deploy-ready `<bundle>.js-meta.xml` with correct isExposed, targets, targetConfigs, objects, and property blocks"
  - "guidance on admin-facing labels, descriptions, and datasource wiring"
  - "checker output flagging meta-xml smells (hidden component, misplaced formFactors, invalid types)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# LWC App Builder Config

Use this skill whenever the functional behavior of the LWC is fine but the component either does not appear in a builder, appears in the wrong builder, or offers admins the wrong set of configuration knobs. The js-meta.xml file is the single source of truth that controls exposure, surface targeting, per-surface configuration, form-factor fit, and the admin UX inside App Builder, Experience Builder, Home Page, Utility Bar, and Flow.

---

## Before Starting

Gather this context before editing a `.js-meta.xml`:

- Which surfaces must this component render on — Record Page, App Page, Home Page, Experience Cloud page, Utility Bar, Flow Screen, or several of these?
- Which sObjects is the component valid against? Record-page exposure without an `<objects>` element lets admins drop it on any object's page, which is almost always wrong.
- Which form factors must be supported — Large (desktop) only, Small (phone) only, or both? Form factors are declared inside `targetConfig`, not at the root.
- What admin-tunable inputs does the component need, and are any of them field-name pickers, picklist-value pickers, or free-text with defaults?
- Is translation of the admin-facing `masterLabel` and `description` required? That constrains your approach because `masterLabel` cannot be a Custom Label reference.

---

## Core Concepts

The meta.xml file is small, but every element changes how the builder treats the bundle. Five concepts cover almost every real situation.

### `isExposed` Controls Builder Visibility

Setting `<isExposed>true</isExposed>` is the gate: without it, the bundle is pure JS runtime and cannot be placed in App Builder, Experience Builder, Home Page, Utility Bar, or Flow. A missing or `false` value hides the component silently — there is no validation error — so admins open a ticket wondering where the component went.

### `targets` Enumerate The Surfaces

Inside `<targets>`, each `<target>` child names a surface the component supports: `lightning__RecordPage`, `lightning__AppPage`, `lightning__HomePage`, `lightning__UtilityBar`, `lightning__Tab`, `lightning__FlowScreen`, `lightningCommunity__Default`, `lightningCommunity__Page`, and a handful of device and app-specific targets. A single bundle may appear on many surfaces when its public API is generic enough.

### `targetConfigs` Customize Per-Surface Behavior

`targets` alone produces a component with no admin-configurable inputs. To add per-surface configuration, wrap the target name in a `<targetConfig targets="…">` block under `<targetConfigs>`. Inside each block go `<property>` elements (design attributes), `<supportedFormFactors>`, and — for record pages — the `<objects>` restriction. If a target name appears in `<targets>` but has no matching `<targetConfig>`, admins still see the component but with no configurable properties.

### Design Attributes Give Admins Typed Inputs

`<property>` elements are the admin UX. Each takes a `name`, `type` (`String`, `Integer`, `Boolean`, `Color`), `label`, `description`, optional `default`, optional `placeholder`, `required` flag, and — for `String` — an optional `datasource`. The `datasource` can be a static CSV (`"low,medium,high"`) for a fixed picklist, or `apex://MyPicklistProvider` to bind to an Apex class that implements `VisualEditor.DynamicPickList`, producing dynamic options such as field names or record-type values.

### Record-Page Scoping And Auto-Injected Context

Inside a `lightning__RecordPage` `targetConfig`, the `<objects>` element restricts where admins can drop the component (for example, Account and Opportunity only). Salesforce also auto-injects `@api recordId` and `@api objectApiName` public properties at runtime — you declare them in JS, but you do not declare them in meta.xml. Community targets behave differently: `lightningCommunity__Default` uses `propertyValues` internally, and some `property` types (such as `ContentReference`) are only valid in community targets.

---

## Common Patterns

### Multi-Surface Reusable Bundle

**When to use:** One component should appear on a Record Page for Account and Opportunity, on a custom App Page, and on an Experience Cloud page.

**How it works:** List all three targets in `<targets>`, then create one `<targetConfig>` per target. Scope the record-page target with `<objects>`, expose a `title` design attribute on the App Page with a default, and let the community target define its own distinct set of admin-facing properties.

**Why not the alternative:** Cloning the bundle per surface multiplies maintenance cost and drifts admin UX. A single bundle with per-surface `targetConfig` keeps behavior consistent.

### Apex-Backed Dynamic Picklist

**When to use:** Admins need to pick a field name, record-type developer name, or any other dynamic list.

**How it works:** Implement `VisualEditor.DynamicPickList` in Apex, then reference it from the design attribute as `<property type="String" datasource="apex://MyPicklistProvider" />`. App Builder calls the Apex class when the admin opens the property panel.

**Why not the alternative:** A static CSV datasource cannot reflect org-specific schema. Hardcoding the values inside the LWC hides configuration in code and forces a deploy for every change.

### Form-Factor Restriction Inside `targetConfig`

**When to use:** The App Page layout works only on phone, or an Experience page should appear on desktop only.

**How it works:** Add `<supportedFormFactors><supported formFactor="Small"/></supportedFormFactors>` inside the relevant `<targetConfig>`. Declaring it at the root has no effect.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Expose on record pages only, for a specific sObject | `lightning__RecordPage` target + `<objects>` with that object | Prevents admins from dropping it on unrelated records |
| Expose everywhere the component is generic | Multiple `<target>` entries, each with its own `<targetConfig>` | One bundle, per-surface admin UX |
| Admin needs to pick a field at design time | `<property type="String" datasource="apex://FieldPickProvider" />` | `Picklist` is not a valid type; use `String` + datasource |
| Admin needs a fixed small list (High/Medium/Low) | `<property type="String" datasource="high,medium,low" default="medium"/>` | No Apex needed for a static list |
| Component must work on mobile phone only | `<supportedFormFactors><supported formFactor="Small"/></supportedFormFactors>` inside the relevant `targetConfig` | Form factors are per-target, not global |

---

## Recommended Workflow

1. List every surface the component must appear on and, for record pages, the exact sObjects allowed.
2. Decide which admin inputs the component needs and whether any of them require a dynamic datasource (Apex) versus a static CSV.
3. Draft the meta.xml with `isExposed=true`, the full `<targets>` list, and a matching `<targetConfig>` block per configurable target, including `<objects>` on record-page targets and `<supportedFormFactors>` where needed.
4. Set `<masterLabel>` and `<description>` for the builder-side label and tooltip — remember `masterLabel` cannot be a Custom Label reference.
5. Run `python3 skills/lwc/lwc-app-builder-config/scripts/check_lwc_app_builder_config.py <path>` and fix any reported issues.
6. Deploy to a scratch org, drop the component from every configured surface in App Builder / Experience Builder, and verify each design attribute renders correctly.

---

## Review Checklist

- [ ] `<isExposed>true</isExposed>` is present; the component actually appears in the intended builders.
- [ ] Every target that needs configurable inputs has a matching `<targetConfig>`.
- [ ] Every `<targetConfig targets="lightning__RecordPage">` either restricts `<objects>` or has a documented reason not to.
- [ ] `<supportedFormFactors>` lives inside a `<targetConfig>`, never at the root.
- [ ] `<property>` types are limited to `String`, `Integer`, `Boolean`, `Color` (plus community-specific types where applicable) — no `Picklist`.
- [ ] `<masterLabel>` and `<description>` are filled in and read well in the builder.
- [ ] Default values are parsed or cast on read in JS (meta.xml defaults arrive as strings).

---

## Salesforce-Specific Gotchas

1. **`isExposed=false` fails silently** — the component never appears in any builder and the deploy succeeds. Admins see nothing, devs see no error.
2. **`supportedFormFactors` at the root is ignored** — it only takes effect inside a `<targetConfig>`.
3. **`masterLabel` is not translatable via Custom Labels** — use Translation Workbench for localization; Custom Label references do not resolve here.
4. **`objects` only scopes record-page targets** — it is irrelevant on App Page, Home Page, and Experience targets.
5. **Changes to `targetConfigs` can break existing admin placements** — when a required property is added or a type changes, admins may need to re-place or re-save the component on affected pages.
6. **Design-attribute defaults arrive as strings** — even `type="Integer"` default `"5"` is handed to JS as a string, so cast on read.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Deploy-ready meta.xml | `<bundle>.js-meta.xml` with correct `isExposed`, `targets`, `targetConfigs`, `objects`, and `property` blocks |
| Admin UX plan | The set of labels, descriptions, defaults, and datasources the builder will show |
| Checker report | File-level findings on hidden components, misplaced formFactors, invalid property types, and missing masterLabel |

---

## Related Skills

- `lwc/lwc-base-component-recipes` — once the component is exposed, use base components inside it for standard admin UX.
- `lwc/custom-property-editor-for-flow` — use when the builder-side UX goes beyond design attributes and needs a custom LWC editor (Flow-specific).
- `lwc/experience-cloud-lwc-components` — use for Experience Cloud-specific property types, CSP, and theming concerns.
- `lwc/lwc-in-flow-screens` — use when the component is also placed inside Flow Screens and needs Flow-specific input/output wiring.
