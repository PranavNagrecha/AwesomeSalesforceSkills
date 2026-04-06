---
name: lightning-page-performance-tuning
description: "Use when a Lightning record page, home page, or app page is slow to load or render — covers Experienced Page Time (EPT) analysis, component count reduction, progressive disclosure via tabs and conditional rendering, Lightning Experience Insights diagnostics, and DOM/XHR minimization strategies. Triggers: 'Lightning page is slow', 'EPT is high', 'record page takes too long to load', 'too many components on page', 'Lightning Experience Insights shows slow page', 'how to optimize Lightning page performance'. NOT for Visualforce page performance (separate concern). NOT for Apex or SOQL query optimization (use apex/apex-cpu-and-heap-optimization or data/soql-query-optimization). NOT for report or dashboard performance (use admin/report-performance-tuning)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Scalability
triggers:
  - "Lightning page is slow or takes too long to load"
  - "EPT is high in Lightning Experience Insights"
  - "record page has too many components and loads slowly"
  - "how to optimize Lightning page performance and reduce load time"
  - "Lightning Experience Insights shows a high-impact slow page"
  - "home page is slow for all users after login"
tags:
  - lightning-pages
  - EPT
  - performance
  - lightning-app-builder
  - progressive-disclosure
  - component-count
  - lightning-experience-insights
inputs:
  - "The Lightning page type (record page, home page, or app page) and the object it is associated with"
  - "Current component count on the page and a list of visible components"
  - "EPT measurement or user-reported symptom (slow load, blank flash, spinner delay)"
  - "Whether Lightning Experience Insights data is available"
outputs:
  - "Component audit with recommendations to remove, defer, or consolidate components"
  - "Tab-based progressive disclosure layout recommendation"
  - "Conditional rendering strategy for heavy components"
  - "EPT baseline and target with measurement method"
  - "Review checklist for performance sign-off"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Lightning Page Performance Tuning

Use this skill when a Lightning record page, home page, or app page loads slowly. It applies component count reduction, progressive disclosure via tabs, conditional rendering, and EPT measurement to bring page load times within acceptable thresholds.

---

## Before Starting

Gather this context before working in this domain:

- **Page type and object**: Record pages, home pages, and app pages have different component compositions and caching behavior. Record pages are the most common performance concern because they load object-specific data for every component on the page.
- **Current component count**: There is no hard limit on component count, but Salesforce flags pages with unusually high component counts in Lightning Experience Insights. Every component on the page adds DOM nodes and may trigger its own server round-trip (XHR) on initial load.
- **EPT measurement**: Experienced Page Time (EPT) is the primary metric. It is measured at the P75 percentile (75th percentile of page loads) and distinguishes between first load (cold cache) and subsequent load (warm cache). EPT is available in Lightning Experience Insights (formerly Lightning Usage App).
- **Component weight**: Not all components are equal. A Related List component loading thousands of records is far heavier than a static Rich Text component. Identify which components on the page are data-heavy.
- **Org-specific factors**: Large orgs with complex sharing rules, many record types, or extensive field-level security calculations add overhead to every page load independent of component count.

---

## Core Concepts

### Experienced Page Time (EPT)

EPT measures the time from navigation start to when the page is fully interactive from the user's perspective. Salesforce calculates EPT at the **P75 percentile** — meaning 75% of page loads complete within the reported EPT value. Lightning Experience Insights surfaces EPT data in two categories:

1. **First page load EPT** — cold cache, no prior component rendering in the session. This is typically 2-4x slower than subsequent loads.
2. **Subsequent page load EPT** — warm cache, component framework already initialized. This is the more common user experience after the first page in a session.

The **High-Impact Slow-Performing Pages** view in Lightning Experience Insights identifies pages where EPT is significantly above the org average, ranked by user impact (frequency of access multiplied by EPT).

### Component Count and DOM/XHR Cost

Every component placed on a Lightning page contributes to load time through two mechanisms:

1. **DOM cost** — each component renders HTML elements into the page DOM. More components mean more DOM nodes, longer layout calculations, and more paint cycles.
2. **XHR cost** — many components fetch data from the server on initial render. A Related List component issues a query for its records. A Report Chart component fetches report data. Each XHR call adds network latency and server processing time.

Tests show that deferring 8 components from the initial viewport (by placing them in tabs) can save approximately **0.4 seconds and 7 XHR calls** on initial page load. The savings scale with the number and weight of deferred components.

### Progressive Disclosure via Tabs

The primary performance pattern for Lightning pages is **progressive disclosure**: placing secondary components in tab containers so they are not rendered or fetched until the user clicks the tab. Components in non-active tabs skip both DOM rendering and XHR calls on initial page load.

This is not a workaround — it is the Salesforce-recommended approach for pages with many components. The Lightning App Builder provides a native Tabs component specifically for this purpose.

### Conditional Rendering

For LWC custom components on Lightning pages, `if:true` / `lwc:if` directives defer rendering of component subtrees until a condition is met. This is useful for components that are only relevant in specific record states (e.g., show a renewal widget only when Status = "Active"). Conditional rendering eliminates both DOM and XHR costs for the hidden component until the condition evaluates to true.

---

## Common Patterns

### Pattern: Tab-Based Component Deferral

**When to use:** A record page has more than 8-10 components visible on initial load and EPT is above target.

**How it works:**
1. Identify which components users need immediately on page load (typically record detail, highlights panel, path, and primary related list).
2. Group remaining components into logical tabs (e.g., "Related", "Activity", "Analytics", "Details").
3. Place the Tabs component in the Lightning App Builder and move secondary components into non-default tabs.
4. The default (first) tab renders on load; all other tabs defer rendering until clicked.

**Why it works:** Components in non-active tabs are not rendered and do not issue XHR calls until the tab is selected. For a page with 15 components where 8 are moved to non-default tabs, initial load skips 8 component renders and their associated server calls.

### Pattern: Component Audit and Removal

**When to use:** A page has accumulated components over time and some are rarely used or redundant.

**How it works:**
1. List every component on the page with its type (standard, custom, third-party).
2. For each component, determine: (a) how many users interact with it, (b) whether it fetches data on load, (c) whether it duplicates information available elsewhere on the page.
3. Remove components that are unused, redundant, or better served by a link to a separate page.
4. Consolidate multiple small components into a single component where possible (e.g., replace three separate formula fields with one custom component that displays all three).

**Why it works:** The fastest component is the one that is not on the page. Removing a data-fetching component eliminates its DOM nodes and XHR call entirely.

### Pattern: Page Variants for Role-Based Loading

**When to use:** Different user roles need different information on the same record page, and a single page with all components is slow.

**How it works:**
1. Create multiple page variants using Lightning App Builder's component visibility filters or page assignment rules.
2. Assign lightweight variants to roles that need minimal information (e.g., a read-only variant for support agents viewing Account records).
3. Assign the full variant only to roles that genuinely need all components (e.g., account managers).

**Why it works:** Each role loads only the components relevant to their workflow. A support agent who never uses the analytics tab does not pay the rendering cost for analytics components.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Record page with 10+ components loading slowly | Tab-based progressive disclosure | Defer non-essential components from initial render |
| EPT is high but component count is moderate (5-7) | Audit component weight; check for heavy Related Lists or Report Charts | Component count is not the only factor — data-heavy components dominate |
| Page loads fast on first visit but slows after navigation | Check for memory leaks in custom LWC components; review connectedCallback/disconnectedCallback cleanup | Warm-cache degradation indicates component lifecycle issues |
| Multiple user roles share one record page with different needs | Page variants with role-based assignment | Avoid loading components irrelevant to the current user's role |
| Custom LWC component is slow but page layout is optimal | Profile the LWC independently; check wire service caching, imperative call batching | The issue is component-internal, not page-level |
| Lightning Experience Insights shows high EPT for a specific page | Start with the High-Impact Slow-Performing Pages view to identify the page and measure baseline EPT | Data-driven prioritization before making changes |
| Home page is slow for all users | Audit dashboard components and report charts on the home page; these often fetch large datasets | Home pages are shared across users and accumulate heavy components |

---

## Recommended Workflow

1. **Measure baseline EPT.** Open Lightning Experience Insights and locate the page in the High-Impact Slow-Performing Pages view. Record the P75 EPT for both first and subsequent page loads. If Lightning Experience Insights is not available, use browser DevTools Network tab to measure total load time as a proxy.
2. **Inventory all components.** In Lightning App Builder, list every component on the page. Categorize each as: essential (must render on initial load), secondary (can be deferred to a tab), or removable (unused or redundant).
3. **Remove unnecessary components.** Delete any component that is unused, redundant, or duplicates information available elsewhere. This is the highest-impact change with zero user experience cost.
4. **Apply tab-based progressive disclosure.** Place secondary components into a Tabs container. Keep only essential components in the initial viewport. Set the most-used tab as the default.
5. **Apply conditional rendering for custom components.** For any custom LWC component that is only relevant in specific record states, add `lwc:if` conditions to defer rendering until the condition is met.
6. **Remeasure EPT.** After changes are deployed, wait for sufficient page load volume (at least 24-48 hours of usage data), then check Lightning Experience Insights again. Compare P75 EPT against the baseline from step 1.
7. **Document the layout rationale.** Record which components are in which tabs and why, so future page editors do not undo the performance work by moving deferred components back to the initial viewport.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Baseline EPT recorded from Lightning Experience Insights or browser DevTools before changes
- [ ] Component audit completed: every component categorized as essential, secondary, or removable
- [ ] Unused or redundant components removed from the page
- [ ] Secondary components placed in non-default tabs using the Tabs component
- [ ] Custom LWC components use conditional rendering (`lwc:if`) where applicable
- [ ] No more than 8-10 components render on initial page load (before tab click)
- [ ] Post-change EPT measured and compared against baseline
- [ ] Layout rationale documented for future page editors

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **There is no hard component count limit** — Salesforce does not enforce a maximum number of components per page. Pages with 20+ components will still save and deploy. The degradation is gradual — each additional component adds incremental load time. Lightning Experience Insights flags pages as slow based on measured EPT, not component count, so the symptom surfaces only after users experience slowness.
2. **Components in non-active tabs still count toward metadata limits** — While non-active tabs defer rendering and XHR calls, all components on the page count toward the page's metadata definition. This means the FlexiPage XML file grows with every component regardless of tab placement. Extremely large FlexiPage definitions can slow page metadata retrieval itself, though this is rare in practice.
3. **EPT distinguishes first vs. subsequent load** — First page load EPT includes framework initialization, component definition downloads, and cold cache costs. Subsequent page load EPT benefits from cached component definitions and warm Aura/LWC framework state. Optimizing for subsequent load EPT (the more common user experience) may not improve first load EPT, and vice versa. Always measure both.
4. **Related List components are disproportionately expensive** — A Related List component that returns hundreds or thousands of child records is one of the heaviest standard components. Moving it to a non-default tab is high-impact. Replacing a full Related List with a Related List - Single component (which shows fewer columns and rows) is an alternative when tab deferral is not possible.
5. **Report Chart components fetch report data on every page load** — Report Chart components embedded on record pages execute the underlying report query each time the page loads. If the report is complex or targets a large-volume object, this single component can dominate page load time. These are strong candidates for tab deferral or removal.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Component audit table | List of all components on the page with categorization (essential / secondary / removable) and data weight assessment |
| Tab layout recommendation | Which components go in which tabs, with the default tab identified |
| EPT baseline and target | Measured P75 EPT before and after changes, with target threshold |
| Conditional rendering plan | Which custom components get `lwc:if` guards and what conditions trigger rendering |
| Performance sign-off checklist | Completed checklist confirming all criteria are met before handoff |

---

## Related Skills

- admin/lightning-app-builder-advanced — for Lightning App Builder configuration patterns beyond performance tuning
- admin/dynamic-forms-and-actions — for converting page layouts to dynamic forms, which can also improve page performance by conditionally showing fields
- lwc/lwc-performance — for component-internal LWC performance optimization (wire caching, imperative call batching, render cycle reduction)
- admin/report-performance-tuning — when a Report Chart component on the page is slow due to the underlying report's performance
