---
name: dynamic-forms-and-actions
description: "Configure Dynamic Forms (field and section visibility on Lightning record pages) and Dynamic Actions (button and action visibility rules) in Lightning App Builder — enabling Dynamic Forms, converting page layout fields with the Upgrade Now wizard, writing field visibility rules (field value, profile, permission, record type, device), and controlling action bar visibility. NOT for page layout design or record type assignment — use admin/record-types-and-page-layouts. NOT for a full layout-to-Dynamic-Forms migration across record types or profiles — use admin/dynamic-forms-migration. Keywords: flexipage, fieldInstance, fieldItem, uiBehavior, visibilityRule, booleanFilter, UiFormulaCriterion, actionOverrides, profileActionOverrides, page activation, org default page, App Builder Upgrade Now."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Operational Excellence
  - Security
triggers:
  - "hide a field on the record page unless another field has a certain value"
  - "show a button only for certain profiles or only at a certain stage"
  - "convert an existing page layout to Dynamic Forms in Lightning App Builder"
  - "dynamic forms visibility rule not working"
  - "field section on my Lightning page does not appear until I save the record"
  - "deployed the flexipage but users still see the old record page"
  - "mark a field required on the record page without making it required in the API"
  - "cannot remove an action override with destructiveChanges.xml"
  - "work out which profile and record type sees which Lightning record page"
  - "Dynamic Forms not available for this standard object — what are my options"
  - "dynamic forms dynamic actions lightning record page visibility rules field sections flexipage"
tags:
  - dynamic-forms
  - dynamic-actions
  - lightning-app-builder
  - record-page
  - visibility-rules
  - admin-declarative
inputs:
  - "Target object API name (custom or supported standard object)"
  - "List of fields and the conditions under which each should be visible"
  - "User profiles, permission sets, or record types involved in the visibility logic"
  - "Desired actions (buttons) and the context conditions for each"
  - "Salesforce Edition (Dynamic Forms requires Enterprise Edition or higher)"
outputs:
  - "Lightning record page with Dynamic Forms field components and visibility filters configured"
  - "Dynamic Actions configuration showing conditional action bar buttons"
  - "Decision guidance on whether to use Dynamic Forms vs. multiple page layouts"
  - "Checklist verifying the configuration is complete and users can see expected fields"
dependencies:
  - record-types-and-page-layouts
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

# Dynamic Forms and Dynamic Actions

This skill activates when a practitioner needs to show or hide fields, sections, or actions on a Lightning record page based on record data, user context, or device — without maintaining multiple page layouts. It covers enablement, conversion from page layouts, writing visibility rules, and setting up Dynamic Actions.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Object support**: Dynamic Forms is available for all custom objects and a growing subset of standard objects. As of Spring '25, supported standard objects include Account, Contact, Lead, Opportunity, Case, and several others. Check the official help article for the current list before committing to this approach. **UNVERIFIED (2026-09-04):** the Metadata API Developer Guide publishes no object support matrix for Dynamic Forms, and help.salesforce.com cannot be fetched offline. The reliable test is empirical: open Lightning App Builder for the object and see whether individual fields can be placed.
- **Edition requirement**: Dynamic Forms requires Enterprise Edition or higher. Professional Edition does not support it. **UNVERIFIED (2026-09-04):** no edition requirement for Dynamic Forms appears in the Metadata API Developer Guide or the Salesforce App Limits Cheat Sheet. Confirm against your contract or the Lightning App Builder UI for the target org before quoting this to a customer.
- **Existing page layout state**: Know whether the object currently uses a classic page layout in Lightning. When you enable Dynamic Forms, the page layout fields are *not* automatically migrated — you must explicitly convert them using the "Upgrade Now" wizard in Lightning App Builder.
- **Mobile**: two switches decide what a phone renders, and neither is on the page. `DynamicFormsSettings.enableFormsOnMobile` is a single org-wide setting (API 58.0+, Beta), and the assignment's `formFactor` decides which page a phone loads at all — `Small` is the mobile app, `Large` is Lightning Experience desktop, and no value means Salesforce Classic. Get a decision on both before designing for mobile. Offline behaviour is a separate question: **UNVERIFIED (2026-09-04):** the claim that Dynamic Forms does not render in Salesforce mobile offline mode is not confirmed by any source available offline. Test on a device before promising it either way. assume nothing and test.
- **Most common wrong assumption**: Practitioners assume that once Dynamic Forms is enabled on a Lightning record page, existing page layout fields appear automatically. They do not. The page layout fields must be added individually as Dynamic Form field components, or the "Upgrade Now" wizard must be used to bulk-convert them.

---

## Questions to Ask Before Configuring

Ask these before opening App Builder. Each one maps to a gotcha in `references/gotchas.md`; skipping them produces a page that demos perfectly and behaves differently in production.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Does this condition change *while* the user is editing, or is it fixed for the whole session?" | Field rules re-evaluate live; field **section** rules are evaluated only after save | The choice between per-field rules and a section rule — the single most common design error here |
| "Who is allowed to see this, and is hiding it enough?" | A visibility rule renders; only FLS authorises. Hidden fields stay readable in reports, list views, and the API | Either an FLS/permission-set change, or an explicit written decision that this is cosmetic |
| "Which app, record type, and profile combinations must land on this page?" | None of that lives in the `.flexipage`; it lives in `CustomObject.actionOverrides` and `CustomApplication.profileActionOverrides`, and the narrowest match wins | The activation matrix, and the second and third metadata files the change actually needs |
| "Do phone users need this page, and does the org have the mobile setting on?" | `formFactor` on the assignment picks the page; `DynamicFormsSettings.enableFormsOnMobile` is org-wide and Beta | A `Small` assignment row, or a documented decision that mobile keeps the old experience |
| "Is 'required' about this screen, or about the data?" | `uiBehavior` = `Required` binds to one field instance on one page and never reaches the save path | A validation rule where the data must be clean, and `uiBehavior` only where the prompt is a UI nicety |
| "How many fields, and are they going in one region?" | A Lightning page region is documented as holding up to 100 components, and conversion turns one detail component into one item per field | A section-and-facet structure decided before conversion, not after the ceiling is hit |
| "Which actions move to Dynamic Actions, and are they coming off the page layout in the same change?" | Actions surviving in both places duplicate or override each other | A per-action list with a removal step, rather than a half-migrated action bar |

What a proper configuration adds over just placing fields in App Builder: the page is reachable by the right users because its assignment metadata shipped with it, the rules fire when the business expects them to rather than only after a save, and the "required" and "hidden" decisions land on the layer that actually enforces them.

---

## Core Concepts

### Dynamic Forms vs. Classic Page Layouts

Classic page layouts control which fields appear for a record type/profile combination. They are static: every user with the same record type and profile sees the same layout. Dynamic Forms replace the monolithic "Fields" section on a Lightning record page with individually placed field components, each of which can carry its own visibility filter.

The key distinction: Dynamic Forms operate at the Lightning record page level, while page layouts operate at the record type + profile assignment level. When a Lightning record page uses Dynamic Forms, the page layout's field arrangement is bypassed for that page — only FLS (Field-Level Security) continues to be enforced by the platform regardless.

### Visibility Filters

Each Dynamic Form field or section component can have one or more visibility filter conditions. Conditions can be combined with AND or OR logic. Supported filter types:

| Filter Type | What It Checks |
|---|---|
| Field Value | A field on the current record equals, contains, starts with, or is blank/not blank |
| Profile | The viewing user's profile matches one of the specified profiles |
| Permission | The viewing user has a specific custom permission |
| Record Type | The record's record type matches the specified type |
| Device | Desktop, phone, or tablet |
| Advanced (formula) | Formula evaluates to true (available on select objects) |

Visibility filters are evaluated client-side on page load, but **field components and Field Section components re-evaluate on different schedules**. Rules on a *field* are assessed live: "Changes a user makes while editing a record can make fields appear and disappear as visibility rules are evaluated." Rules on a *Field Section* are not: "Visibility rules on field sections aren't dynamic and don't react to what a user does while editing. Field section visibility rules are evaluated only after a record is saved." Progressive-disclosure UX ("reveal the Shipping section once Type = Physical") must therefore be built from per-field rules — a section rule leaves the section hidden until the user saves. Field Section rules suit conditions that are stable for the whole edit session (record type, profile, custom permission, device).

Visibility filters do not replace FLS — a hidden field is merely not rendered; it is still accessible via API if the user has FLS access.

### Dynamic Actions

Dynamic Actions apply the same visibility-rule approach to the action bar (buttons). Instead of a static list of actions from the page layout, you configure each action as a component on the Lightning record page and attach visibility rules. Dynamic Actions must be explicitly enabled per object in the Lightning App Builder page — the option appears in the page's properties panel.

Dynamic Actions support the same filter types as Dynamic Form fields. A common use case is hiding "Approve" or "Submit for Approval" buttons until the record reaches a specific status.

The visibility rule is a property of a **component instance**, not of the action list. The FlexiPage's `platformActionlist` holds the ordered action bar (`PlatformActionList` with `actionListContext` = `Flexipage`, and `platformActionListItems` carrying `actionName`, `actionType`, `sortOrder`, `subtype`); the per-action *rule* rides on the component that renders the button. `references/metadata-examples.md` §1 shows the shape.

### Where the Page Lives, and Where the Assignment Lives

These are two different metadata types, and shipping only the first is the most common way a correct page reaches nobody.

| What | Metadata type | DX path |
|---|---|---|
| The page and all its rules | `FlexiPage` | `flexipages/<Name>.flexipage-meta.xml` |
| Org default for View | `CustomObject` → `actionOverrides` (`type` = `flexipage`, View action only) | `objects/<Obj>/<Obj>.object-meta.xml` |
| App default, and app + record type + profile | `CustomApplication` → `actionOverrides` and `profileActionOverrides` | `applications/<App>.app-meta.xml` |

Precedence runs narrowest-wins: a matching `ProfileActionOverride` takes precedence over the `ActionOverride` for the same page. There is no permission-set dimension anywhere in the assignment metadata — only `profile`. Full XML, the deletion procedure (which is *not* `destructiveChanges.xml`), and the verification steps are in `references/metadata-examples.md`.

---

## Common Patterns

### Pattern 1: Replace Multiple Page Layouts With Field Visibility Rules

**When to use:** The org has 3+ page layouts for an object where the only difference is which fields are shown for each record type. Maintaining multiple layouts creates drift as fields are added to some layouts but not others.

**How it works:**
1. Open Lightning App Builder for the relevant Lightning record page.
2. In the page properties, click "Upgrade Now" to convert existing page layout fields to Dynamic Form components. This creates a Fields component for each section on the existing page layout.
3. After conversion, select individual field components and add a visibility filter: Filter by Record Type, then select the record types for which that field should appear.
4. Remove unused fields from record types that should not see them by deleting those components from the canvas or setting them to invisible via filter.
5. Save and activate the updated page.

**Why not the alternative:** Maintaining separate page layouts requires opening each layout individually when a new field is added. It also means the same page-level components (related lists, highlights panel) must be duplicated across multiple page assignments.

### Pattern 2: User-Context-Sensitive Action Bar With Dynamic Actions

**When to use:** Certain actions (e.g., "Mark as Reviewed", "Escalate") should only appear for users in a specific profile or with a custom permission, or only when the record is in a specific stage.

**How it works:**
1. In Lightning App Builder, open the record page and enable Dynamic Actions in the page Properties panel.
2. Remove any existing action overrides from the page layout to avoid conflicts.
3. Drag individual action components (standard and custom) onto the page canvas.
4. For each action, open its visibility settings and add a filter. For stage-based visibility: Filter by Field Value, select `Status` (or the relevant field), set the condition (e.g., `equals Pending Review`).
5. For profile-based visibility: Filter by Profile, select the relevant profiles.
6. Combine conditions with AND where both must be true (e.g., correct stage AND correct profile).
7. Save and activate.

**Why not the alternative:** Static action bar entries from page layouts cannot be conditionally shown without code. Previously, this required a custom LWC or Aura component to wrap the action. Dynamic Actions is the no-code path.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Object is a standard object not yet supported by Dynamic Forms | Keep using page layouts; check release notes each cycle for expanding support | Dynamic Forms cannot be enabled on unsupported standard objects |
| Need to hide fields but only for Salesforce Classic users | Page layout assignment only | Dynamic Forms only apply to Lightning Experience |
| 3+ page layouts with field overlap by record type | Enable Dynamic Forms and use Record Type visibility filters | Eliminates layout maintenance drift |
| Need to show different fields based on a field value (not record type) | Dynamic Forms with Field Value filters | Page layouts cannot conditionally show fields based on field values |
| Need to hide an action button until a record reaches a certain status | Dynamic Actions with Field Value filter on Status | No code required |
| org is Professional Edition | Not supported; use page layout variants or LWC workarounds | Dynamic Forms requires Enterprise Edition or higher |
| Users work offline on mobile | Retain classic page layouts as fallback or document the limitation | Dynamic Forms fields do not render offline |

---


## Recommended Workflow

1. Answer the questions above into `templates/dynamic-forms-and-actions-template.md`. The Field Visibility Matrix and Action Visibility Matrix are the design; a rule you cannot write as a row is a rule you cannot express in `UiFormulaCriterion`.
2. Decide per row whether the condition is **live** or **post-save**. Conditions that change during editing (a picklist the user is about to set) must be per-field rules; conditions fixed for the session (record type, profile, custom permission, form factor) can sit on a `flexipage:fieldSection`. Getting this backwards is the failure the Core Concepts section describes and no checker can catch.
3. Convert with the "Upgrade Now" wizard in Lightning App Builder rather than hand-authoring, then retrieve the page and read the real XML. `references/metadata-examples.md` gives the shape to compare against — `fieldInstance` / `fieldItem` / `fieldInstanceProperties` with `uiBehavior`, and `visibilityRule` / `criteria` / `booleanFilter` with the closed operator set `CONTAINS`, `EQUAL`, `NE`, `GT`, `GE`, `LE`, `LT`.
4. Write the **assignment** in the same change set: `CustomObject.actionOverrides` for the org default, `CustomApplication.profileActionOverrides` for app + record type + profile, one row per `formFactor` you support. A page deployed without its assignment is inert.
5. Run `python3 scripts/check_dynamic_forms_and_actions.py --manifest-dir force-app/main/default` and clear every finding or record why it is accepted. It catches duplicated fields, rules pointing at fields that are not in the object folder, expressions spanning more than five fields, orphaned action-override targets, and region sizes past the documented ceiling.
6. Deploy with `--dry-run` first, then verify against a **real record**, not the App Builder preview: change the driving field without saving (field rules fire, section rules do not), save (section rules fire), and repeat as a user in each profile in the activation matrix. The verification table in `references/metadata-examples.md` §7 lists the four checks worth doing.
7. Record the activation matrix and any rule you could not express declaratively in the template's Notes and Deviations section, then hand a wide or slow page to `admin/lightning-page-performance-tuning` before rollout.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Confirmed the object is on the supported standard objects list or is a custom object
- [ ] Confirmed org is Enterprise Edition or higher
- [ ] Dynamic Forms enabled on the target Lightning record page and page activated for the correct profiles/app/record type combinations
- [ ] All required fields appear for each combination of user context and record state (tested manually or via test user)
- [ ] FLS is correctly set for all fields referenced in visibility rules (a field hidden by a visibility filter but inaccessible via FLS is doubly hidden — ensure no field becomes unexpectedly invisible to users who need it)
- [ ] Dynamic Actions enabled if action bar changes are required, and conflicting page layout actions are removed
- [ ] Assignment metadata shipped in the same change as the page — `CustomObject.actionOverrides` for the org default and/or `CustomApplication.actionOverrides` / `profileActionOverrides` for app, record type, and profile, with one row per `formFactor` supported
- [ ] Every rule tested for *timing*, not just outcome: field rules verified mid-edit before saving, field-section rules verified after saving
- [ ] `python3 scripts/check_dynamic_forms_and_actions.py --manifest-dir <source dir>` run and every finding cleared or explicitly accepted
- [ ] Mobile behavior documented and communicated to users if the object is used on the Salesforce Mobile App

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Page layout fields are not auto-migrated when Dynamic Forms is enabled** — Enabling Dynamic Forms on a Lightning record page removes the monolithic "Fields" section from the page. If fields were placed there by a page layout, they will disappear. Use the "Upgrade Now" wizard in Lightning App Builder to bulk-migrate fields to individual Dynamic Form components before activating the page. Skipping this step causes fields to vanish for all users on that page.

2. **Dynamic Forms bypass the page layout but not FLS** — A field with an "always visible" Dynamic Forms rule will still not appear if the user lacks FLS read access. Conversely, a field that is "hidden" by a Dynamic Forms filter is still accessible to the user through the API if they have FLS access. Do not rely on Dynamic Forms for security enforcement — use FLS and sharing rules for that.

3. **Visibility filters referencing formula fields or cross-object fields have constraints** — Not all field types can be used as filter conditions. Formula fields and certain cross-object fields are not available as filter targets. If your visibility logic depends on a calculated value, consider using a helper checkbox field that is updated via a Flow or formula field on a supported field type.

4. **Dynamic Actions conflicts with page layout action overrides** — If you enable Dynamic Actions on a Lightning record page but the underlying page layout still has action overrides configured, the behavior can be inconsistent depending on context (related list vs. record detail). Always audit and clean page layout action configurations when enabling Dynamic Actions.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Updated Lightning record page | The `.flexipage` metadata file containing Dynamic Form field components and Dynamic Action components with visibility filter conditions |
| Activation configuration | Page assignment settings (app, profile, record type) controlling which users see the updated page |
| Field visibility matrix | (optional) A table mapping each field to its visibility conditions, used to verify coverage during testing |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing deployable `FlexiPage` XML, the `actionOverrides` / `profileActionOverrides` that activate it, the `package.xml`, the retrieve/deploy commands, how to *remove* an assignment, and the four post-deploy verification checks |
| `references/gotchas.md` | Ten platform behaviours that make a correct-looking page wrong — the missing org switch, per-instance `Required`, undeletable assignments, the mobile Beta toggle, and the 100-component region ceiling |
| `references/examples.md` | Working through a real conversion: the six-layout field matrix with its record-type rules, and the AND/OR truth table for a two-criteria action rule |
| `references/llm-anti-patterns.md` | Reviewing generated Dynamic Forms advice, especially AND-versus-OR filter logic and the field-section progressive-disclosure trap |
| `references/well-architected.md` | Framing the design against User Experience, Operational Excellence, and Security, and for the source list behind every claim here |
| `templates/dynamic-forms-and-actions-template.md` | Before touching App Builder — the visibility matrices are the design artifact step 1 produces |

---

## Related Skills

- `admin/record-types-and-page-layouts` — Owns page layout structure, record type assignment, profile layout mapping, and the `Layout` XML. Read it for the layout side of a conversion; do not expect layout XML here.
- `admin/dynamic-forms-migration` — Owns the multi-record-type, multi-profile conversion *project*: sequencing, impersonation test plans, and which layouts can be retired. This skill covers configuring one page; that one covers migrating an object.
- `admin/lightning-record-page-configuration` — Owns the general FlexiPage anatomy: templates, tabs, facets, regions, and the Tooling API audit queries. Read it first if the question is about page structure rather than conditional visibility.
- `admin/lightning-app-builder-advanced` — Component-level App Builder technique beyond field and action visibility.
- `admin/lightning-page-performance-tuning` — Where to take a page that is slow or wide, and how to measure it rather than guess.
- `admin/global-actions-and-quick-actions` — Defining the actions themselves (action layout, predefined values, object-specific versus global) before Dynamic Actions decides when to show them.
- `admin/custom-field-creation` — Creating the fields that will be placed and conditionally shown, including whether a field should be required at the API rather than on one page.
