---
name: analytics-embedded-components
description: "Use this skill when embedding a CRM Analytics dashboard into a Lightning App Builder page, Experience Cloud page, or when embedding a custom LWC inside an Analytics dashboard. Trigger keywords: wave-wave-dashboard-lwc, wave-community-dashboard, analytics__Dashboard target, embed dashboard, record-id context filtering, dashboard state JSON, analytics component. NOT for standard LWC development unrelated to Analytics dashboards, NOT for designing dashboard content or datasets, NOT for CRM Analytics app creation or dataset management."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - User Experience
triggers:
  - "How do I embed a CRM Analytics dashboard on a record page in Lightning?"
  - "My dashboard isn't filtering by the current record — I'm using record-id but it's not working"
  - "What is the difference between wave-wave-dashboard-lwc and wave-community-dashboard?"
  - "How do I add a custom LWC component inside an Analytics dashboard?"
  - "The dashboard and developer-name attributes are both set and one seems to be ignored"
  - "How do I pass filters or selections to an embedded dashboard using state?"
tags:
  - crm-analytics
  - embedded
  - lwc
  - dashboard
  - architect
inputs:
  - "Target embedding surface: Lightning App Builder page, Experience Cloud page, or Analytics dashboard canvas"
  - "Dashboard identifier: 18-character dashboard ID (starts with 0FK) or developer API name"
  - "Context record ID if filtering by current record (18-character Salesforce entity ID)"
  - "Filter/selection state as a JSON string if pre-populating dashboard state"
  - "js-meta.xml target if embedding a custom LWC inside an Analytics dashboard"
outputs:
  - "LWC component markup using the correct embedding component for the target surface"
  - "Attribute configuration for dashboard, developer-name, record-id, and state"
  - "js-meta.xml configuration with analytics__Dashboard target for LWC-inside-dashboard pattern"
  - "Decision guidance on which embedding pattern to use and why"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# Analytics Embedded Components

This skill activates when a practitioner needs to embed a CRM Analytics dashboard into a Salesforce page (Lightning App Builder or Experience Cloud), or embed a custom LWC component inside an Analytics dashboard canvas. It covers component selection, attribute configuration, context passing via `record-id` and `state`, and the critical distinction between embedding a dashboard IN a page versus embedding a component INSIDE a dashboard.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Target surface**: Is the dashboard going on a Lightning record/app page (use `wave-wave-dashboard-lwc`) or an Experience Cloud page (use `wave-community-dashboard`)? Or are you embedding a custom LWC inside an Analytics dashboard (use `analytics__Dashboard` target in js-meta.xml)? These are entirely different setups.
- **Dashboard identifier**: You must use either the 18-character dashboard ID (starts with `0FK`) as the `dashboard` attribute, OR the developer API name as `developer-name`. Never both — they are mutually exclusive.
- **Context record**: If the dashboard should filter on the page's current record, you need the 18-character Salesforce record ID available (usually `{!recordId}` in App Builder). The `record-id` attribute passes this to the dashboard for dynamic filtering.
- **State requirement**: If you need to pre-populate filters or selections, the `state` attribute accepts a JSON string. Invalid JSON causes silent failure — the dashboard loads without the intended filter state.
- **CRM Analytics license**: The org must have CRM Analytics (formerly Einstein Analytics / Tableau CRM) licensed. `wave-wave-dashboard-lwc` is part of the Analytics component library, not a standard platform component.

---

## Core Concepts

### Embedding Direction: Two Completely Different Patterns

There are two fundamentally distinct embedding scenarios that practitioners routinely confuse:

**Pattern A — Dashboard embedded IN a page**: You place a CRM Analytics dashboard onto a Lightning record page, Lightning app page, or Experience Cloud page. The host page is the container; the dashboard is the embedded content. You use `wave-wave-dashboard-lwc` (Lightning) or `wave-community-dashboard` (Experience Cloud).

**Pattern B — Custom LWC embedded INSIDE a dashboard**: You author a custom LWC in VS Code/CLI and declare it as an Analytics dashboard component via the `analytics__Dashboard` target in its `js-meta.xml`. The Analytics dashboard canvas is the container; your LWC is the embedded content. This pattern involves the LWC developer registering component attributes that appear as dashboard widget properties.

Mixing up these two patterns leads to broken setups. If a practitioner asks "how do I embed my LWC in a dashboard?" they mean Pattern B. If they ask "how do I show a dashboard on a record page?" they mean Pattern A. Confirm the direction before writing any code.

### Component Selection for Pattern A: Lightning vs Experience Cloud

For Pattern A, the component used depends strictly on the **page surface**, not on the dashboard type:

- **Lightning App Builder pages** (record pages, app pages, home pages): use `wave-wave-dashboard-lwc`
- **Experience Cloud pages** (community/portal pages built in Experience Builder): use `wave-community-dashboard`

These components are not interchangeable. Using `wave-community-dashboard` on a Lightning page causes the component to fail to render. Using `wave-wave-dashboard-lwc` on an Experience Cloud page is not supported and is not available in the Experience Builder component palette.

### Dashboard Attribute: `dashboard` vs `developer-name`

The `wave-wave-dashboard-lwc` component (and `wave-community-dashboard`) accepts two mutually exclusive identifiers:

- **`dashboard`**: The 18-character Salesforce record ID of the dashboard, beginning with `0FK`. This is the ID visible in the URL when you open the dashboard in Analytics Studio.
- **`developer-name`**: The API name of the dashboard as defined in the Analytics app. This is the human-readable string like `Account_Revenue_Overview`.

Setting both attributes causes a **silent fallback** — the component uses one and ignores the other without throwing an error. The `dashboard` (ID) attribute takes precedence when both are present. To avoid ambiguity and silent failures, always use exactly one of the two.

### Context Passing: `record-id` and `state`

**`record-id`**: Accepts the 18-character Salesforce record ID of the page's current record. In App Builder, bind it to `{!recordId}`. The dashboard must be designed to consume this value — it does not automatically filter unless the dashboard's dataset has a binding configured to use the passed record ID. The `record-id` attribute simply makes the ID available; the dashboard designer controls whether and how it is used.

**`state`**: Accepts a JSON string encoding filters and selections to apply when the dashboard loads. The format matches the Analytics Dashboard REST API state structure. Example: `{"myStep": {"selections": ["AccountA"]}}`. The string must be valid JSON. Invalid JSON causes silent failure — the dashboard renders in its default state with no indication that the state was rejected. When building the state string dynamically, always validate JSON before passing it.

---

## Common Patterns

### Pattern A1: Dashboard on a Lightning Record Page with Record Context

**When to use:** You want a CRM Analytics dashboard to appear on an Account, Opportunity, or other record page in Lightning and have it automatically scope to the current record.

**How it works:**

1. In App Builder, drag the "CRM Analytics Dashboard" component onto the record page layout.
2. Set the `Dashboard` property to the 18-character dashboard ID (0FK...) or the developer API name.
3. Set the `Record ID` property to `{!recordId}` — App Builder binds this to the current record's ID at runtime.
4. In the dashboard itself (built in Analytics Studio), configure a step or filter binding that references the passed `record-id` value.
5. Save and activate the page.

In markup (if building a wrapper LWC):

```html
<wave-wave-dashboard-lwc
    developer-name="Account_Revenue_Overview"
    record-id={recordId}
    show-sharing-button="false">
</wave-wave-dashboard-lwc>
```

**Why not iframe:** An iframe embedding loses the `record-id` context binding and action/selection callbacks. It also does not respond to App Builder property bindings.

### Pattern A2: Dashboard on an Experience Cloud Page

**When to use:** You are building an Experience Cloud portal or community and need a CRM Analytics dashboard visible to external users or partners.

**How it works:**

In Experience Builder, use the `wave-community-dashboard` component. The attribute surface is similar to `wave-wave-dashboard-lwc` but the component is registered for the Experience Cloud runtime.

```html
<wave-community-dashboard
    developer-name="Partner_Pipeline_Dashboard"
    show-title="true"
    show-sharing-button="false">
</wave-community-dashboard>
```

**Why not wave-wave-dashboard-lwc:** `wave-wave-dashboard-lwc` is not available in the Experience Builder component palette. Attempting to use it in an Experience Cloud page requires a custom LWC wrapper, which still must use `wave-community-dashboard` internally for Experience Cloud surfaces.

### Pattern B: Custom LWC Inside an Analytics Dashboard

**When to use:** You want a custom-built LWC to appear as a widget inside an Analytics dashboard canvas — for example, a custom action button, a specialized visualization, or a form component that writes back to Salesforce.

**How it works:**

1. Create the LWC with standard tooling (`sf generate component`).
2. In the component's `js-meta.xml`, add `analytics__Dashboard` to the `<targets>` block:

```xml
<targets>
    <target>analytics__Dashboard</target>
</targets>
```

3. Optionally expose `<targetConfig>` properties for the `analytics__Dashboard` target so dashboard designers can configure the component from the widget property panel.
4. Deploy the component to the org.
5. In Analytics Studio, open the dashboard in edit mode. The custom LWC appears in the widget picker under "Custom Components."
6. Drag it onto the canvas and configure exposed properties.

**Why not the embedding approach:** You cannot use `wave-wave-dashboard-lwc` inside an Analytics dashboard. The dashboard canvas requires components registered via `analytics__Dashboard` target, not standard Lightning page components.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Show a dashboard on a Lightning record/app/home page | `wave-wave-dashboard-lwc` | Only component supported in Lightning App Builder for this purpose |
| Show a dashboard on an Experience Cloud page | `wave-community-dashboard` | Required component for Experience Cloud surfaces; `wave-wave-dashboard-lwc` is not available there |
| Pass the current record's ID for dynamic filtering | `record-id` attribute on embedding component | Standard context-passing mechanism; binds to `{!recordId}` in App Builder |
| Pre-populate dashboard filters/selections on load | `state` attribute with valid JSON string | Encodes initial filter/selection state per Analytics Dashboard state schema |
| Add a custom LWC as a widget inside an Analytics dashboard | `analytics__Dashboard` target in `js-meta.xml` | Registers the LWC with the Analytics dashboard runtime so it appears in the widget picker |
| Identify dashboard by its API name instead of record ID | `developer-name` attribute | Portable across orgs and sandboxes; do not combine with `dashboard` attribute |
| Embed dashboard in a third-party or non-Salesforce page | iframe with dashboard public URL | Last resort: loses action bindings, context passing, and session-aware filtering |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Confirm the embedding direction.** Ask: is a dashboard going INTO a page (Pattern A), or is a custom LWC going INSIDE a dashboard (Pattern B)? These require completely different implementations. Do not proceed until this is clear.
2. **For Pattern A, confirm the target surface.** Lightning App Builder pages require `wave-wave-dashboard-lwc`. Experience Cloud pages require `wave-community-dashboard`. Confirm the page type before writing any markup.
3. **Identify the dashboard reference.** Retrieve either the 18-character dashboard ID (0FK...) from Analytics Studio's URL, or the developer API name. Choose one — do not set both `dashboard` and `developer-name` on the same component.
4. **Configure context passing.** If the dashboard must scope to the current record, set `record-id` to the 18-char record ID (bind to `{!recordId}` in App Builder). If filters/selections must be pre-loaded, build a valid JSON string for the `state` attribute and validate it before use.
5. **For Pattern B, configure js-meta.xml.** Add `analytics__Dashboard` to the `<targets>` block. Define any `<targetConfig>` properties the dashboard designer will need. Deploy the LWC to the org.
6. **Verify the dashboard renders with expected context.** After deployment, open the page, confirm the dashboard loads, verify record-context filtering works as expected, and check browser console for silent state errors.
7. **Review the gotchas checklist** in `references/gotchas.md` — specifically the mutual-exclusivity rule for `dashboard`/`developer-name` and the JSON validity requirement for `state`.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Embedding direction confirmed: dashboard-in-page (Pattern A) or LWC-in-dashboard (Pattern B)
- [ ] Correct component selected for surface: `wave-wave-dashboard-lwc` for Lightning, `wave-community-dashboard` for Experience Cloud
- [ ] Only one of `dashboard` (0FK ID) or `developer-name` is set — never both
- [ ] `record-id` is bound correctly (`{!recordId}` in App Builder) if record-context filtering is required
- [ ] `state` attribute value is valid JSON — validated before deployment
- [ ] For Pattern B: `analytics__Dashboard` target is present in `js-meta.xml`
- [ ] Dashboard renders on target page and context filtering works as expected

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **`dashboard` and `developer-name` are mutually exclusive** — Setting both on `wave-wave-dashboard-lwc` does not throw an error. The component silently uses `dashboard` (the 18-char ID) and ignores `developer-name`. This causes hard-to-debug issues where a dashboard appears to work in one org but points to the wrong dashboard in another where IDs differ.
2. **`wave-wave-dashboard-lwc` vs `wave-community-dashboard` are NOT interchangeable** — `wave-wave-dashboard-lwc` is only available in the Lightning App Builder component palette. `wave-community-dashboard` is only available in Experience Builder. Using the wrong component on the wrong surface results in the component not appearing or rendering broken — with no clear error message.
3. **Invalid `state` JSON causes silent failure** — If the JSON string passed to `state` is malformed, the dashboard loads in its default state. There is no warning in the UI or console. Always validate JSON before passing it to `state`.
4. **`record-id` passes context but does not auto-filter** — Passing a record ID via `record-id` does not automatically scope the dashboard to that record. The dashboard must be designed with explicit bindings that consume the passed record ID. If the dashboard designer has not configured those bindings, the attribute is silently ignored.
5. **Pattern A and Pattern B share no setup steps** — Practitioners sometimes try to use `analytics__Dashboard` target in `js-meta.xml` to add a dashboard to a Lightning page, or try to drag `wave-wave-dashboard-lwc` into an Analytics dashboard canvas. Neither works. The target registration and the page component are for entirely separate embedding directions.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| LWC markup with correct embedding component | `wave-wave-dashboard-lwc` or `wave-community-dashboard` with correct attribute configuration |
| `js-meta.xml` with `analytics__Dashboard` target | For Pattern B (custom LWC inside Analytics dashboard canvas) |
| Dashboard attribute configuration | Chosen dashboard reference (ID or developer-name), record-id binding, state JSON |
| Embedding decision rationale | Written explanation of why the chosen pattern and component are correct for the surface |

---

## Related Skills

- `admin/crm-analytics-app-creation` — for creating the CRM Analytics app and dashboard that will be embedded
- `admin/analytics-dashboard-design` — for designing the dashboard content, steps, and filters before embedding
- `architect/org-limits-monitoring` — if embedding dashboards that surface org limit data
