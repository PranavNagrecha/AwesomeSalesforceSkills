---
name: lightning-app-builder-advanced
description: "Advanced Lightning App Builder usage: component visibility filters, custom page templates, Dynamic Forms, Dynamic Actions, page performance optimization, LWC targetConfig for record pages. Use when building complex record pages or custom app templates. NOT for basic page layout configuration. NOT for LWC component development (use lwc/* skills). NOT for Dynamic Forms basics (use dynamic-forms-and-actions)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Security
triggers:
  - "How do I add up to 10 visibility conditions per component on a Lightning record page using AND and OR logic"
  - "I want to create a custom app page template with Aura or LWC for Lightning App Builder"
  - "My Lightning record page loads too slowly on mobile — how do I optimize component count and visibility rules"
  - "How do I move the action bar to Lightning App Builder so I can control button visibility without code"
  - "I need per-tab visibility in the Tabs component on a Lightning page (Summer 24)"
tags:
  - lightning-app-builder
  - visibility-filters
  - dynamic-forms
  - dynamic-actions
  - flexipage
  - page-performance
inputs:
  - "Target object API name and whether Dynamic Forms is supported for it"
  - "List of components and the conditional logic (AND/OR, up to 10 conditions) for each"
  - "Profiles, permission sets, record types, field values, and device types used in filter conditions"
  - "Whether Dynamic Actions is being combined with page-layout actions (duplicate risk)"
  - "For custom templates: Aura component implementing lightning:template with flexipage:region nodes"
  - "LWC targetConfig targets (lightning__RecordPage, lightning__AppPage, etc.) in .js-meta.xml"
outputs:
  - "Lightning record page or app page with correctly configured component visibility filters"
  - "Custom app page template Aura component skeleton with flexipage:region node definitions"
  - "Performance audit checklist for mobile (8 or fewer visible components per region)"
  - "Decision guidance on when to use formula fields instead of complex inline visibility filter conditions"
  - "Dynamic Actions configuration that avoids duplication with page-layout actions"
dependencies:
  - dynamic-forms-and-actions
  - record-types-and-page-layouts
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Lightning App Builder — Advanced Configuration

This skill activates when a practitioner needs to go beyond basic drag-and-drop page layout in Lightning App Builder (LAB). It covers component visibility filter logic, custom page templates, Dynamic Forms and Dynamic Actions at depth, LWC targetConfig constraints, and page performance optimization. Use it alongside `dynamic-forms-and-actions` when the task involves the full LAB canvas rather than just field-level visibility basics.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the org edition: Dynamic Forms and Dynamic Actions require Enterprise Edition or higher. Group and Professional editions cannot use these features.
- Identify the target object: Dynamic Forms supports most custom objects and a growing subset of standard objects (check the current Salesforce release notes — the supported list expands each release). Objects not yet supported will not show the "Upgrade Now" option in LAB.
- Check whether existing page-layout actions are present on the record page: enabling Dynamic Actions while page-layout actions are still assigned causes duplicate action buttons unless you remove the page-layout actions from assignments first.

---

## Core Concepts

### Component Visibility Filters

Every component on a Lightning record page, app page, or home page can have up to 10 visibility conditions. Conditions use AND or OR logic (not a mix of both in one component rule — you pick one operator for the whole set). Filter criteria types include field value (evaluated client-side at page load and on change), record type, profile, custom permission, device form factor (Desktop, Phone, Tablet), and user attribute. Summer '24 extended per-condition visibility to individual tabs inside the Tabs standard component, so each tab can be shown or hidden independently without requiring separate page variants.

Important security note: visibility filters are cosmetic. A component hidden by a filter is not rendered in the DOM for the current user under most circumstances, but FLS (Field-Level Security) must independently enforce data access. Do not use visibility filters as a security gate.

### Dynamic Forms

Dynamic Forms moves individual field components and field section components onto the LAB canvas and assigns per-component visibility rules. This replaces the monolithic field section derived from the page layout. When Dynamic Forms is enabled for a record page, the page layout's fields are no longer injected automatically — they must be explicitly placed as components. Migrating via the "Upgrade Now" wizard converts existing layout sections to Dynamic Form components, but any fields not in the layout at migration time must be added manually.

Not all standard objects support Dynamic Forms. For unsupported objects, the workaround is to use multiple page layouts assigned per profile/record type, or to create formula fields that expose calculated values in supported ways.

### Dynamic Actions

Dynamic Actions moves the action bar to the LAB canvas and adds per-action filter conditions using the same visibility criteria available for components. Once you enable Dynamic Actions for a record page, the action bar is no longer controlled by the page layout's action section. If the page layout still has actions and is assigned to users, those actions will show in addition to the Dynamic Actions bar — causing duplicates. Remove the page-layout action assignments before or immediately after enabling.

### Custom App Page Templates

A custom app page template is an Aura component that implements `lightning:template`. The component's `.cmp` file defines `flexipage:region` nodes with `name`, `defaultWidth`, and optional `maxComponents` attributes. These regions become drop zones in the LAB canvas. LWC cannot directly implement the `lightning:template` interface, so custom templates must be Aura. However, LWC components can be placed inside template regions as content components. LWC components targeting `lightning__RecordPage` in their `.js-meta.xml` `targetConfigs` cannot expose `recordId` in the `<targetConfig>` design resource — `recordId` is injected automatically by the framework; exposing it in design causes a metadata validation error.

---

## Common Patterns

### Complex Visibility Using Formula Fields

**When to use:** When your visibility condition requires logic that cannot be expressed in a single filter (e.g., "show only when Stage is Closed Won AND Amount > 10000 AND account billing country is US"). LAB visibility filters cannot do cross-field arithmetic or multi-level expressions.

**How it works:** Create a formula checkbox field (e.g., `Show_Contract_Section__c`) whose formula encodes the full logic. Then use that single checkbox field as the one visibility filter condition on the component. This keeps the LAB filter simple (one condition: `Show_Contract_Section__c = True`) and offloads complexity to the formula engine.

**Why not the alternative:** Attempting to chain 10 conditions in LAB for complex cross-field logic becomes brittle and hard to maintain. Formula fields are versioned, testable, and reusable across multiple page components.

### Mobile-Optimized Page Variant

**When to use:** Record pages that perform well on desktop become slow on mobile due to component count and heavy LWC components loading simultaneously.

**How it works:** Create a separate page variant for Phone form factor using the "New Page" > "Form Factor" option in LAB. Limit visible components to 8 or fewer per region (Salesforce-documented mobile performance guideline). Use visibility filters with `Device = Phone` to hide non-essential components on the shared variant instead of fully duplicating the page.

**Why not the alternative:** Assigning the same desktop page to mobile users without optimization causes cascade loading delays because all components — even those below the fold — begin loading simultaneously.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Object supports Dynamic Forms, need per-field visibility | Enable Dynamic Forms, use field component visibility filters | Native, declarative, no code |
| Object does NOT support Dynamic Forms | Formula fields + component-level visibility or multiple page layouts | Dynamic Forms unavailable; formula field visibility is next best |
| Need to show/hide entire action bar buttons per record context | Enable Dynamic Actions, remove page-layout action bar assignment | Avoids duplicates; gives declarative per-action control |
| Need visibility logic beyond 10 conditions or cross-field math | Formula checkbox field as single filter proxy | LAB filter limit is 10 per component |
| Building reusable page template for multiple app types | Custom Aura template component with flexipage:region | Only Aura can implement lightning:template |
| Performance issue on mobile | Create Phone form-factor variant, cap to 8 components per region | Official mobile component count guideline |
| Per-tab visibility in Tabs component (Summer '24+) | Use per-tab visibility settings in Tabs component properties | Available since Summer '24; no need for multiple page variants |

---

## Recommended Workflow

1. Confirm org edition (Enterprise+), target object Dynamic Forms eligibility, and whether existing page-layout actions are assigned (Dynamic Actions duplicate risk).
2. Open Lightning App Builder for the target record page. Review the current component structure and identify which components need visibility rules, which need Dynamic Forms, and whether Dynamic Actions is required.
3. For each component requiring visibility: add filter conditions (up to 10, AND or OR), using formula fields where the required logic exceeds what inline filters can express.
4. If enabling Dynamic Forms: use the "Upgrade Now" wizard, verify all layout fields migrated correctly, then assign field-level visibility rules to each field component.
5. If enabling Dynamic Actions: confirm page-layout action assignments are removed to prevent duplicates, then add per-action filter conditions in LAB.
6. If building a custom template: scaffold an Aura component implementing `lightning:template`, define `flexipage:region` nodes, deploy to org, then reference the template in LAB New App/Page.
7. Validate using the Preview (Desktop and Phone form factors), check the Review Checklist below, and activate the page.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] All visibility filter conditions are confirmed cosmetic only — FLS enforces actual data access independently.
- [ ] Component count per region is 8 or fewer on mobile form-factor variant.
- [ ] Dynamic Actions enabled pages have page-layout action bar assignments removed from all affected profiles/record types to avoid duplicates.
- [ ] Dynamic Forms migration verified: all expected fields appear on the canvas; no fields silently dropped.
- [ ] Custom template Aura component does not expose `recordId` in `targetConfig` design resource (causes metadata validation error).
- [ ] Formula fields used as visibility proxies are documented so future admins understand why the field exists.
- [ ] Page is saved and activated (changes are draft until explicitly activated).

---

## Salesforce-Specific Gotchas

1. **Visibility filters are cosmetic, not security** — A component hidden by a visibility filter is not a security control. FLS and object permissions are the only enforced data access gates. Users with direct API access or SOQL tools will still see field data regardless of visibility filters on the page.
2. **Dynamic Actions + page-layout actions = duplicates** — Enabling Dynamic Actions does not automatically remove the page layout's action section from the page. If that layout is still assigned to users, both the Dynamic Actions bar and the page-layout actions render simultaneously, duplicating buttons.
3. **Dynamic Forms Upgrade Now can silently miss fields** — The migration wizard only migrates fields that are currently on the page layout at the time of migration. Fields added to the layout after the migration, or fields not in the layout at migration time, must be manually added to the canvas as individual field components.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Configured Lightning record page | LAB-activated page with component visibility filters, Dynamic Forms fields, and Dynamic Actions set up |
| Custom page template Aura component | `.cmp` file implementing `lightning:template` with named `flexipage:region` nodes, ready for LAB registration |
| Visibility formula field | Formula checkbox field used as a single-condition visibility proxy for complex cross-field logic |
| Performance audit notes | List of components per region on desktop and phone form factors, flagging regions exceeding 8 |

---

## Related Skills

- dynamic-forms-and-actions — Use for foundational Dynamic Forms and Dynamic Actions configuration; this skill covers the broader LAB advanced surface including custom templates and visibility filter architecture.
- record-types-and-page-layouts — Use when Dynamic Forms is unavailable for the target object and multiple page layouts remain the only option.
- lwc/component-configuration-for-app-builder — Use when developing the LWC components placed on the page; this skill covers the LAB canvas configuration side only.
