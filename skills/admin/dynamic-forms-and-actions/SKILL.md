---
name: dynamic-forms-and-actions
description: "Use this skill to configure Dynamic Forms (field and section visibility on Lightning record pages) and Dynamic Actions (button/action visibility rules) using Lightning App Builder. Covers enabling Dynamic Forms, converting page layout fields to Dynamic Form components, writing field visibility rules (field value, profile, permission, record type, device), and controlling action bar visibility per record context. NOT for page layout design or record type assignment (use record-types-and-page-layouts). NOT for building custom LWC components."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Operational Excellence
  - Security
triggers:
  - "I want fields on a record page to show or hide based on field values without creating multiple page layouts"
  - "How do I make a button only visible to certain profiles or when a record meets specific criteria"
  - "Users see too many irrelevant fields on the record page and I need to simplify the view by record type or user role"
  - "How do I convert an existing page layout to Dynamic Forms in Lightning App Builder"
  - "Field visibility rules not working on my Lightning record page"
  - "Dynamic Forms not available for this standard object — what are my options"
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Dynamic Forms and Dynamic Actions

This skill activates when a practitioner needs to show or hide fields, sections, or actions on a Lightning record page based on record data, user context, or device — without maintaining multiple page layouts. It covers enablement, conversion from page layouts, writing visibility rules, and setting up Dynamic Actions.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Object support**: Dynamic Forms is available for all custom objects and a growing subset of standard objects. As of Spring '25, supported standard objects include Account, Contact, Lead, Opportunity, Case, and several others. Check the official help article for the current list before committing to this approach.
- **Edition requirement**: Dynamic Forms requires Enterprise Edition or higher. Professional Edition does not support it.
- **Existing page layout state**: Know whether the object currently uses a classic page layout in Lightning. When you enable Dynamic Forms, the page layout fields are *not* automatically migrated — you must explicitly convert them using the "Upgrade Now" wizard in Lightning App Builder.
- **Mobile offline limitation**: Dynamic Forms is not supported in Salesforce Mobile App offline mode. Fields configured as Dynamic Form components will not render when the device is offline.
- **Most common wrong assumption**: Practitioners assume that once Dynamic Forms is enabled on a Lightning record page, existing page layout fields appear automatically. They do not. The page layout fields must be added individually as Dynamic Form field components, or the "Upgrade Now" wizard must be used to bulk-convert them.

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

Visibility filters are evaluated client-side on page load and re-evaluated when field values change (for field-value filters). They do not replace FLS — a hidden field is merely not rendered; it is still accessible via API if the user has FLS access.

### Dynamic Actions

Dynamic Actions apply the same visibility-rule approach to the action bar (buttons). Instead of a static list of actions from the page layout, you configure each action as a component on the Lightning record page and attach visibility rules. Dynamic Actions must be explicitly enabled per object in the Lightning App Builder page — the option appears in the page's properties panel.

Dynamic Actions support the same filter types as Dynamic Form fields. A common use case is hiding "Approve" or "Submit for Approval" buttons until the record reaches a specific status.

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

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Confirmed the object is on the supported standard objects list or is a custom object
- [ ] Confirmed org is Enterprise Edition or higher
- [ ] Dynamic Forms enabled on the target Lightning record page and page activated for the correct profiles/app/record type combinations
- [ ] All required fields appear for each combination of user context and record state (tested manually or via test user)
- [ ] FLS is correctly set for all fields referenced in visibility rules (a field hidden by a visibility filter but inaccessible via FLS is doubly hidden — ensure no field becomes unexpectedly invisible to users who need it)
- [ ] Dynamic Actions enabled if action bar changes are required, and conflicting page layout actions are removed
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

## Related Skills

- `record-types-and-page-layouts` — For designing page layout structure, record type assignment, and profile layout mapping. Use alongside this skill when migrating from page layouts to Dynamic Forms.
- `custom-field-creation` — For creating the fields that will be placed and conditionally shown using Dynamic Forms.
