---
name: related-list-configuration
description: "Configure related lists on Salesforce records — column choice on Page Layouts (max 10 fields per related list), sort field selection, the Spring '24 Enhanced Related Lists component (which adds filtering, mass actions, and 10-row inline display), the choice between Related Lists / Related Lists - Single / Related List - Quick Links in Lightning App Builder, per-record-type related-list assignments, and the View All / pagination UX. NOT for FSL WorkOrderMilestone-on-Work-Order layout (use admin/fsl-sla-configuration-requirements), NOT for the Lightning page performance Related List - Single vs Full tradeoff in isolation (use admin/lightning-page-performance-tuning), NOT for Industries Timeline-as-related-list (use admin/health-cloud-timeline), NOT for offline-priming related-list caps (use admin/fsl-mobile-app-setup)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - Performance
  - Security
triggers:
  - "user complains the columns shown on the Contacts related list are wrong"
  - "how do I sort the Cases related list by CreatedDate descending instead of CaseNumber"
  - "View All button on related list shows different columns than the inline list"
  - "I need to add a filter on the Opportunities related list to show only open opportunities"
  - "should I use Related Lists, Related List - Single, or Related Lists - Quick Links on this Lightning page"
  - "related list shows different columns per record type — how is that configured"
  - "Enhanced Related Lists won't let me reorder columns the way the page layout shows them"
  - "related list on the mobile app is missing columns visible on desktop"
tags:
  - related-lists
  - page-layouts
  - lightning-app-builder
  - enhanced-related-lists
  - search-filter-fields
  - sort-fields
  - admin-configuration
inputs:
  - "parent object and child relationship name (the related list to configure)"
  - "Lightning record page layout being edited (Standard, custom record type-scoped, or a Pinned page)"
  - "record type matrix if related lists differ per record type"
  - "which fields the user population actually needs visible (inline) vs. behind the View All click"
  - "whether the org has rolled out Enhanced Related Lists (Spring '24+) or is on classic Related Lists"
outputs:
  - "per-related-list column selection (≤10 fields, ordered) with FLS impact noted"
  - "sort field + sort direction for the related list"
  - "decision on which Lightning component to use (Related Lists / Related Lists - Single / Related Lists - Quick Links / Enhanced Related Lists)"
  - "per-record-type related-list assignment plan if applicable"
  - "Search Filter Fields configuration for related lists exposed through Lightning Pages and the lookup dialog"
  - "checklist confirming FLS, sharing, and mobile-app parity hold for the configuration"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-05-21
---

# Related List Configuration

Activate when an admin is configuring, auditing, or troubleshooting a related list on a Salesforce record — what columns appear, in what order, with what sort, and which Lightning App Builder component is used to host it. This is a Page Layout + Lightning Page Builder concern; the related list rendering is driven by the **page layout** that the user's Profile + Record Type combination resolves to, even on a Lightning record page that uses the new related-list components. Getting this wrong silently changes which fields users see and which they don't.

---

## Before Starting

Gather this context before changing any related-list setting:

- **Page layout assignment matrix.** Related list columns live on the Page Layout, not on the Lightning page. A user with a different Profile + Record Type lands on a different Page Layout and sees different related-list columns even on the same Lightning record page. Confirm which (Profile × Record Type) combinations route to the layout you're editing.
- **Component choice on the Lightning page.** The Lightning Record Page can render related lists via the `Related Lists` component (classic, all related lists from the layout), `Related List - Single` (one related list, custom title, no related-list quick-links bar), `Related Lists - Quick Links` (linked label list only, no row data), or `Enhanced Related Lists` (Spring '24+; per-list filter, sort, and mass actions). Each has different feature coverage and performance profile.
- **The 10-field cap.** A classic related list shows up to **10 columns** inline. The 11th field is silently dropped. The Enhanced Related Lists component raises the practical limit but still bumps against display-width constraints. Always confirm the user actually needs every field they ask for inline; the rest belong behind View All.
- **Spring '24 Enhanced Related Lists.** Filtering and mass-action support requires the Enhanced Related Lists component. Switching from the classic Related Lists component to Enhanced is org-level reversible but resets per-user column-width preferences.
- **FLS and sharing.** Related list columns honor Field-Level Security: a field hidden by FLS appears as a blank cell, not an access-denied error, which makes incorrect FLS look like a layout bug. Sharing filters the rows: a related list never reveals records the running user can't access via OWD + sharing rules + manual share + role hierarchy.
- **Mobile parity.** The Salesforce Mobile App applies the **same** related-list configuration as desktop but enforces tighter column counts (typically the first 4 columns render inline). Order matters — put the most important columns first.

---

## Core Concepts

### Page Layout owns the related-list contract

A "related list" on any page-layout-driven surface is defined inside the Page Layout XML at `<relatedLists>`. The entry carries `relatedList`, an optional `sortField` / `sortOrder`, a list of `fields` (up to 10 for classic), and a list of `customButtons` exposed at the top of the list. The Lightning record page does not store the column definitions — it stores only the **choice** of component (classic Related Lists vs. Related Lists - Single vs. Enhanced Related Lists) and which related list (by relationship name) that component should render.

The implication: editing a related list's columns is a Page Layout edit, not a Lightning App Builder edit, even when the resulting record page is 100% Lightning App Builder. Forgetting this routes admins to the wrong tool.

### Sort field + sort direction

Each related list has one sort field and one direction. Sort defaults to the parent-relationship-defined order (typically CreatedDate DESC) when not specified. Sort field must be a sortable field type — long text areas, encrypted text, formula fields that reference cross-object lookups, and base64 fields cannot sort. Picking an unsortable field silently falls back to default sort with no error.

The sort field shown when the user clicks **View All** can differ from the inline sort if the user manually re-sorts the View All grid, but the configured default sort always re-applies on first render.

### Enhanced Related Lists (Spring '24+)

The Enhanced Related Lists component on a Lightning record page adds:

- inline per-column filtering (resembling list view filtering)
- mass actions on selected rows
- inline column resizing and reordering (per user, persisted in user preferences)
- display of up to 30 rows inline (vs. the classic 5–10) before pagination
- support for displaying related lists as separate components on the page (one component per related list, not the all-in-one Related Lists block)

The cost: Enhanced Related Lists components are heavier on initial render than `Related List - Single`. On record pages with more than ~6 enhanced related lists visible above the fold, defer some to a tab to avoid First-Paint regressions.

### Per-record-type related lists

When an object has multiple record types, each record type can route to a different Page Layout via the Page Layout Assignment matrix (Setup → Object Manager → Object → Page Layouts → Page Layout Assignment). Because the related-list contract lives on the Page Layout, this means **different record types see different related lists, with different columns and sort orders**. This is a feature when intentional (e.g., a Service Request record type doesn't need the Opportunities related list) and a bug when accidental (admins forget to update layout B after editing layout A).

### Search Filter Fields (lookup dialog parity)

The Search Filter Fields on the parent object's Search Layout control which columns appear in the lookup dialog when a user is selecting a record. These are configured separately from the related list itself, in the Search Layouts area. A user can be unable to find a record in the lookup dialog because the field they're searching by isn't in the Search Filter Fields list — even when the related list happily displays it.

---

## Common Patterns

### Pattern 1: Classic Related Lists block on a small Lightning record page

**When to use:** The record page has 4–8 related lists, all relevant to most users, and the org has not yet adopted the Enhanced Related Lists component.

**How it works:**
1. Edit the Page Layout. Add the related lists in priority order (top = most important). For each, set the columns (≤10), sort field, and sort direction.
2. On the Lightning record page in Lightning App Builder, add the **Related Lists** component (singular, all-in-one) below the Activity timeline or on a dedicated tab.
3. The component renders all related lists from the page layout in the order configured.

**Why not the alternative:** Using `Related List - Single` × 8 instead requires 8 separate component placements and 8 separate filter/sort decisions, with no consolidated quick-links bar. The all-in-one block is the right default until a related list needs its own dedicated component (e.g., it lives on a different tab from the others).

### Pattern 2: Enhanced Related Lists for the one related list that needs filtering

**When to use:** Users frequently scroll a long related list looking for the subset that matters (e.g., open vs. closed Cases under an Account).

**How it works:**
1. On the Lightning record page, replace `Related Lists` (or `Related List - Single` for that one list) with the **Enhanced Related Lists** component.
2. Choose the relationship to display. The component reads the same column / sort definition from the underlying Page Layout — there is no separate column picker in App Builder.
3. Enable the filter and mass-action options the users need. Tell users to use the inline filter chip to filter by Status / Stage / Owner.

**Why not the alternative:** Building a custom list view tab on the record page (`Related List - Single` + custom List View component) duplicates configuration and breaks when the user's Page Layout assignment changes. Enhanced Related Lists tracks the Page Layout source automatically.

### Pattern 3: Per-record-type related-list divergence

**When to use:** Two record types on the same object need genuinely different related-list sets — e.g., the B2C record type doesn't expose the Opportunities related list, while B2B does.

**How it works:**
1. Maintain one Page Layout per record type (do not share a layout across divergent record types).
2. Configure related lists per layout in the intentional shape.
3. Confirm the Page Layout Assignment matrix routes each (Profile × Record Type) combination correctly — this is the silent failure point.
4. Document the divergence in the layout description so the next admin doesn't accidentally re-sync the layouts.

**Why not the alternative:** Sharing one layout across record types and using component-level visibility filters in App Builder to hide related lists works for the visible row data but does not hide the related-list **block** on the underlying Page Layout — admins editing the layout later may add columns assuming all record types see them.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Standard record page with several related lists, mostly read | Classic `Related Lists` component, one block | One place to edit, lowest render cost |
| One related list users need to filter / mass-act on | `Enhanced Related Lists` for that list only | Filter + mass actions require Enhanced; keep others classic to limit page weight |
| Related list with > 10 columns requested inline | Push secondary columns behind **View All**, keep 10 max inline | Classic related lists silently drop column 11+; inline width also breaks UX |
| Two record types need different related-list sets | Separate Page Layouts per record type, distinct Page Layout Assignment | Component visibility filters on App Builder don't hide the underlying related-list block from layout-editing admins |
| Related list needs to live on a dedicated tab in App Builder | `Related List - Single` on the tab | Single component lets you title and place independently; the all-in-one `Related Lists` block can't be split |
| Org wants users to discover related lists fast (top of page) | `Related Lists - Quick Links` near the top + full related lists on a tab | Quick Links is anchor-only; pairs with full lists for the click-through |
| Sort field is a formula referencing another object | Pick a directly stored field on the child instead | Cross-object formulas are not sortable; configuration silently falls back to default sort |
| Mobile users complain related list looks empty on phone | Reorder columns: most important first, max 4 visible inline on mobile | Mobile applies the same layout but renders fewer columns above the fold |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on a related-list configuration request:

1. Identify the **Page Layout** that the affected user's (Profile, Record Type) combination resolves to — not the Lightning record page. Confirm by reading the Page Layout Assignment matrix in Setup → Object Manager → <Object> → Page Layouts.
2. Inventory the related list in question on that Page Layout: relationship name, current columns (order + count), sort field, sort direction, custom buttons. Note any field hidden by FLS for the affected user — those show as blank cells.
3. Decide the Lightning component for hosting: classic `Related Lists` (all-in-one), `Related List - Single`, `Related Lists - Quick Links`, or `Enhanced Related Lists`. Apply the decision table above.
4. Apply the column / sort / filter changes on the Page Layout (max 10 fields for classic; choose a sortable field). If using Enhanced Related Lists, confirm filter and mass-action behavior in the App Builder component properties.
5. If different record types need different shapes, mirror the changes onto the divergent Page Layout(s) or document the intentional divergence in the layout description.
6. Validate by impersonating a user from each affected (Profile × Record Type) combination — confirm column visibility, sort default, View All behavior, and mobile parity.
7. Capture the configuration in the related-list-configuration template (see `templates/`) so the next admin reading the change knows the intent.

---

## Review Checklist

Run through these before marking related-list configuration work complete:

- [ ] The Page Layout edited is the one that the affected (Profile × Record Type) resolves to
- [ ] No related list has more than 10 columns configured (classic); secondary columns are behind View All
- [ ] Sort field is a sortable field type (not a long text area, base64, or cross-object formula)
- [ ] If Enhanced Related Lists is used, the filter + mass-action behaviors actually meet the user's need (otherwise the extra page weight is unjustified)
- [ ] Per-record-type divergence is intentional and documented in the layout description, not an accidental drift
- [ ] Search Filter Fields on the parent object's Search Layout include the fields users will type into the lookup dialog
- [ ] Mobile order is verified — the 4 most important columns are first
- [ ] FLS for the affected fields is consistent with the visibility intent (otherwise blank cells will look like a layout bug)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Classic related list silently drops the 11th column** — adding a 12th field doesn't error; it doesn't appear. Users report "field is missing" and admins waste hours debugging FLS before realizing the cap.
2. **Cross-object formula fields can't be the sort field** — the picker accepts them, but at render the sort falls back to default with no warning. The same is true of base64 and long-text-area fields.
3. **Field hidden by FLS appears as a blank cell** — not "no access." This is indistinguishable from a layout bug at a glance and is the #1 source of "column is broken" tickets.
4. **Lightning App Builder visibility filter hides the component, not the Page Layout block** — admins assume the related list is "removed" but the next admin opening the Page Layout sees it and may edit it under that assumption.
5. **Enhanced Related Lists initial render cost is non-trivial** — placing 6+ Enhanced components above the fold has been measured to add hundreds of milliseconds to First Paint on slow networks. Defer to a tab where possible.
6. **Per-record-type related lists diverge silently after a Page Layout clone** — admins clone Layout A → Layout B for a new record type, then later add a related list to A only. Layout B drifts. There is no built-in drift detector; only manual review catches it.
7. **Salesforce Mobile App ignores the inline-column count beyond ~4** — the column order on the Page Layout dictates what mobile users see. Putting an "internal" field in position 1 means the customer-facing fields fall off the mobile view.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Related-list configuration table | One row per (Page Layout × related list) with: columns (ordered), sort field, sort direction, Enhanced/classic component choice, per-record-type divergence note |
| Component placement plan | Lightning record page → which Lightning component (`Related Lists` / `Related List - Single` / `Enhanced Related Lists` / `Related Lists - Quick Links`) hosts each related list, with rationale |
| Page Layout Assignment confirmation | Profile × Record Type → Page Layout matrix snapshot for the affected layouts |
| FLS impact note | Fields on the configured related lists that are hidden by FLS for any affected Profile, with intent (blank cell is intentional vs. needs FLS grant) |
| Mobile parity note | Confirmation that the first 4 columns of each related list are the ones mobile users need most |

---

## Related Skills

- `admin/record-types-and-page-layouts` — Page Layout creation and the Page Layout Assignment matrix that drives which related-list set a user sees
- `admin/lightning-page-performance-tuning` — Tradeoff between Related List - Single vs. all-in-one when First Paint matters; use alongside this skill when the page is heavy
- `admin/global-search-configuration` — Search Layouts and lookup-dialog column choice, which interact with related-list lookups
- `admin/list-views-and-compact-layouts` — Compact layout drives the row tooltip / highlights panel and Mobile App card; related-list configuration drives the inline columns
- `admin/dynamic-forms-migration` — Dynamic Forms removes fields from the layout but **does not** remove related lists from it — relevant when migrating record pages
- `admin/fsl-sla-configuration-requirements` — FSL-specific WorkOrderMilestone-on-Work-Order configuration, which is a specialized case of related-list setup
