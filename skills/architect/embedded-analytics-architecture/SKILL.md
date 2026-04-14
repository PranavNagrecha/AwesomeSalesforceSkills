---
name: embedded-analytics-architecture
description: "Use this skill to architect CRM Analytics dashboard embedding in Lightning pages, Experience Cloud, or Visualforce — covering dashboard context strategy, filter/state management, cross-dashboard context propagation, performance optimization, and LWC vs Aura component selection. Trigger keywords: embed CRM Analytics dashboard, embedded analytics Lightning page, analytics dashboard filter, wave dashboard LWC, analytics state attribute. NOT for CRM Analytics dashboard design/building (use analytics skills), standard Lightning report embedding, or Data Cloud analytics."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
  - Security
triggers:
  - "need to embed a CRM Analytics dashboard on a Lightning record page with the current record context"
  - "embedded dashboard filters are not working or not applying the expected filters to the charts"
  - "need to pass context from one embedded dashboard to another or to an LWC component"
  - "deciding whether to use the LWC wave-wave-dashboard or legacy Aura wave:waveDashboard component"
  - "embedded dashboard performance is slow or causes page load delays in Lightning Experience"
tags:
  - crm-analytics
  - embedded-analytics
  - architect
  - lightning-pages
  - embedded-analytics-architecture
inputs:
  - "Target embedding context (Lightning record page, App page, Experience Cloud, Visualforce)"
  - "Dashboard developer name or 18-char ID"
  - "Filter requirements and record context fields to pass"
  - "Multi-dashboard context propagation requirements"
outputs:
  - "Embedded analytics architecture decision record"
  - "LWC wave-wave-dashboard or Aura wave:waveDashboard component configuration"
  - "Dashboard state attribute JSON schema for filtering and context"
  - "Performance optimization recommendations"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-14
---

# Embedded Analytics Architecture

This skill activates when an architect needs to design the strategy for embedding CRM Analytics dashboards in Lightning Experience, Experience Cloud, or Visualforce — including dashboard context wiring, filter state management, cross-component context propagation, and performance optimization. It produces architecture decisions and configuration specs that developers use to implement embedded analytics correctly.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm the target embedding context: Lightning record page (most common), Lightning App page, Experience Cloud authenticated page, Experience Cloud guest page, or Visualforce. Each context has different component availability and permission requirements.
- The LWC `wave-wave-dashboard` component (Spring '25+) and the Aura `wave:waveDashboard` component have fundamentally different filtering APIs — the `state` attribute in LWC replaces the full dashboard state as a JSON object, while the `filter` attribute in the legacy Aura component adds incremental filter selections. Using the wrong filtering approach produces silent failures.
- Dashboard state is a structured JSON object managed via `getState()`/`setState()` component methods — it enables cross-dashboard context propagation and dynamic filter updates without full re-renders.
- The most critical gotcha: hard-coding a `dashboardDevName` attribute breaks when dashboards are promoted across sandboxes or renamed. Always resolve `dashboardDevName` at runtime using an Apex method or a Custom Setting.

---

## Core Concepts

### LWC vs Aura Component Selection

Two component options for embedding CRM Analytics dashboards:

**LWC `wave-wave-dashboard` (recommended for Lightning Experience):**
- Uses `state` attribute — a full JSON object that replaces the entire dashboard state
- `record-id` attribute automatically passes the current Lightning record context
- `dashboardDevName` attribute (preferred) or `dashboardId` (18-char 0FK ID)
- Works in Lightning Experience and Experience Cloud (authenticated pages)

**Aura `wave:waveDashboard` (legacy, Visualforce pages only):**
- Uses `filter` attribute — adds incremental selection filters on top of existing state
- Different syntax than LWC `state` — cannot use Filter and Selection Syntax JSON in LWC's `state` attribute as-is
- Still required for Visualforce embedding contexts

**Mixing these up is the most common embedded analytics mistake.** Using the `filter` attribute against the LWC component silently has no effect; the `state` attribute must be used.

### Dashboard State and Filter Architecture

The `state` attribute in the LWC component is a JSON object matching the Filter and Selection Syntax spec:
```json
{
  "filters": [
    {
      "field": "Opportunity.OwnerId",
      "operator": "in",
      "value": ["005xxxxxxxxxxxx"]
    }
  ]
}
```

State management patterns:
- **Record-context filter** — `record-id` attribute passes the current Salesforce record ID to the dashboard; the dashboard must have a binding that uses the record ID as a filter
- **Dynamic state via JavaScript** — get and set `state` via the LWC component's `getState()`/`setState()` API to update filters without re-rendering the full dashboard
- **Cross-dashboard propagation** — a selection event in Dashboard A can be caught in the parent LWC and used to update the `state` attribute of Dashboard B

### dashboardDevName Runtime Resolution

Hard-coding `dashboardDevName` causes failures when:
- The dashboard is renamed in any org
- The dashboard is deployed with a different developer name in sandbox vs production
- Multiple dashboards serve different audiences and the selection is user-context-dependent

Architecture pattern: store dashboard dev names in a Custom Setting or Custom Metadata Type; retrieve them in Apex and pass to the embedding component. Never hard-code in Lightning component markup.

---

## Common Patterns

### Pattern: Record-Context Embedded Dashboard

**When to use:** When a dashboard on a Lightning record page should automatically filter to the current record's data (e.g., Account dashboard showing that account's opportunities).

**How it works:**
1. Use LWC `wave-wave-dashboard` with `record-id="{recordId}"` binding
2. In the dashboard, create a binding that uses the record ID as a filter parameter
3. Test that the `record-id` value flows through to the dashboard binding correctly
4. Do NOT hard-code the dashboard ID — use `dashboardDevName` resolved from metadata

### Pattern: Cross-Dashboard Context Propagation

**When to use:** When a selection in one embedded dashboard should update the view in an adjacent embedded dashboard on the same page.

**How it works:**
1. Add a selection event listener on Dashboard A's LWC component wrapper
2. Catch the selection event in the parent Lightning Web Component
3. Build the updated `state` JSON from the selection value
4. Call `setState()` on Dashboard B's LWC component reference to update its filters without full re-render

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Lightning record page embedding | LWC wave-wave-dashboard, record-id attribute | Native record context; best performance |
| Visualforce embedding | Aura wave:waveDashboard | LWC wave-wave-dashboard not available in Visualforce |
| Multiple dashboards on one page sharing context | JavaScript getState/setState cross-component | Avoids full re-render; maintains filter state across dashboards |
| Dashboard dev name varies by environment | Store in Custom Metadata, resolve at runtime | Hard-coded dev names break on rename or cross-env promotion |
| Experience Cloud guest user access to analytics | Confirm Guest User profile analytics permission | Guest users require explicit analytics permission and dashboard sharing |
| Filtering based on current user attributes | $User.Id or $UserAttribute binding in dashboard | Do not pass user attributes via URL parameters — security risk |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. Determine the embedding context (Lightning record page, App page, Experience Cloud, Visualforce) and select the appropriate component (LWC for Lightning/Experience Cloud, Aura for Visualforce).
2. Confirm the dashboard developer name is not hard-coded — design a runtime resolution mechanism (Custom Metadata or Apex) to retrieve it.
3. Design the filter/state strategy: identify what record or user context should be passed as dashboard filters; specify the `state` JSON structure for each filter.
4. Identify any cross-dashboard context propagation requirements: design the event listener and setState pattern for updating adjacent dashboards on selection events.
5. Plan the Experience Cloud permission model if applicable: confirm Guest User profile has analytics access and the dashboard is shared to the correct community profile.
6. Performance planning: specify whether the dashboard should load eagerly or lazily (defer load until user scrolls to the component); identify any heavy datasets that should be pre-filtered before embedding.
7. Document the architecture decision record: component choice, state management approach, dev name resolution strategy, and permission model.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Component type chosen (LWC wave-wave-dashboard vs Aura wave:waveDashboard) with rationale
- [ ] dashboardDevName resolved at runtime — not hard-coded
- [ ] Filter/state JSON schema documented for each embedded dashboard
- [ ] record-id binding confirmed for record-page contexts
- [ ] Cross-dashboard context propagation design documented if applicable
- [ ] Experience Cloud guest user permissions verified if applicable
- [ ] Performance strategy specified (eager vs lazy load)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Using `filter` attribute syntax on the LWC component silently has no effect** — The `filter` attribute is a legacy Aura `wave:waveDashboard` property. Using it on the LWC `wave-wave-dashboard` component silently does nothing — no error, no filter applied. The correct LWC attribute is `state`, which takes a JSON object using the Filter and Selection Syntax spec. This is the single most common embedded analytics configuration mistake.
2. **Hard-coded `dashboardDevName` breaks on rename or cross-env promotion** — If a dashboard is renamed in any org, or if the developer name differs between sandbox and production, the embedding component silently shows a "dashboard not found" error or renders nothing. Architecture must include a runtime dev name resolution mechanism.
3. **Dashboard state from `getState()` may return null after Salesforce maintenance** — The Replay ID mechanism for Platform Events (analogous issue exists with dashboard state) can be stale after org maintenance. For embedded dashboards, the state should be treated as ephemeral and the embedding component should initialize state fresh from application context on each page load rather than relying on cached state.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Embedded analytics architecture decision record | Component choice, state management approach, dev name resolution, permission model |
| Dashboard state JSON schema | Filter and Selection Syntax JSON structure for each embedded dashboard |
| LWC embedding configuration spec | Attribute bindings, event listeners, setState call patterns |

---

## Related Skills

- `admin/analytics-requirements-gathering` — upstream requirements skill for CRM Analytics data source and audience needs
- `admin/analytics-kpi-definition` — KPI definition skill upstream of dashboard design
- `architect/platform-selection-guidance` — broader platform selection guidance
