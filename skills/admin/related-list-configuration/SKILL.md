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
  - "whether the org has rolled out Enhanced Related Lists (release date UNVERIFIED) or is on classic Related Lists"
outputs:
  - "per-related-list column selection (≤10 fields per Help, cap UNVERIFIED; ordered) with FLS impact noted"
  - "sort field + sort direction for the related list"
  - "decision on which Lightning component to use (Related Lists / Related Lists - Single / Related Lists - Quick Links / Enhanced Related Lists)"
  - "per-record-type related-list assignment plan if applicable"
  - "lookup dialog, lookup filter and search filter field lists (SearchLayouts) checked for the lookups users run from the related list"
  - "checklist confirming FLS, sharing, and mobile-app parity hold for the configuration"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-21
---


# Related List Configuration

Activate when an admin is configuring, auditing, or troubleshooting a related list on a Salesforce record — what columns appear, in what order, with what sort, and which Lightning App Builder component is used to host it. This is a Page Layout + Lightning Page Builder concern: a Page Layout carries `relatedLists`, "listed in the order they appear in the user interface" (api_meta 264 L85113-85114), and the layout a user gets comes from the profile's `layoutAssignments`, optionally per record type (api_meta 264 L100698-100705). Getting this wrong silently changes which fields users see and which they don't.

UNVERIFIED (2026-10-21), applies to this file wherever it appears: the 10-column cap, the rows-shown counts (10 or 30), the "Spring '24" date and feature list for Enhanced Related Lists, the mobile ~4-column rendering, FLS-hidden fields rendering as blank cells, unsortable sort fields falling back silently, per-user column-width reset on a component swap, Quick Links counts, and the render-cost figures — all are Salesforce Help or field experience; no corpus guide documents them.

---

## Before Starting

Gather this context before changing any related-list setting:

- **Page layout assignment matrix.** Related list columns live on the Page Layout's `RelatedListItem.fields` (api_meta 264 L85859). A user whose profile + record type resolves to a different layout (`ProfileLayoutAssignments.layout` / `recordType`, api_meta 264 L100702-100705) sees different related-list columns even on the same Lightning record page. Confirm which (Profile × Record Type) combinations route to the layout you're editing.
- **Component choice on the Lightning page.** The record page renders related lists via `Related Lists` (all related lists from the layout; in metadata `force:relatedListContainer`, api_meta 264 L70339-70342), `Related List - Single`, `Related Lists - Quick Links`, or an Enhanced list view of them. UNVERIFIED (2026-10-21): the feature split between these (filter, mass actions, quick-links bar) — Help-only.
- **The 10-field cap (UNVERIFIED).** Help gives up to 10 columns per related list; the Metadata API field documents no cap (api_meta 264 L85859). Always confirm the user actually needs every field they ask for inline; the rest belong behind View All.
- **FLS and sharing.** "Field permissions control the visibility of fields in any part of the app, including related lists" (secguide 262 L621). UNVERIFIED (2026-10-21): that a hidden field renders as a blank cell rather than an error. Sharing decides which rows the user can see.
- **Mobile parity (UNVERIFIED).** The mobile app is reported to render only the first ~4 columns inline. Order matters — put the most important columns first.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Which (Profile × Record Type) combinations must see this related list? | Columns come from the layout the profile's `layoutAssignments` resolve to (api_meta 264 L100702-100705) — Gotcha 4 | The exact layouts to edit, not one of several |
| Which columns are needed inline, in what order? | The 10-column cap is Help-only (UNVERIFIED) and mobile shows ~4 — Gotchas 1 and 7 | A ranked list of at most 10, the top 4 user-critical |
| What should the default sort be, and is that field directly stored on the child? | `sortField`/`sortOrder` (Asc/Desc) are the configured default (api_meta 264 L85868-85873); unsortable-field fallback is UNVERIFIED — Gotcha 2 | A stored, sortable field and direction |
| Do users need to filter or mass-act inside the list? | Those features are Help-only and Enhanced-list only (UNVERIFIED) — Pattern 2; Gotcha 8 | Whether an Enhanced list is worth its cost |
| Should any record type not see this list at all? | A visibility filter hides the component, not the layout entry — Gotcha 5 | Per-record-type layouts instead of filters |
| Can every user who sees the list read every column field? | Field permissions govern related lists (secguide 262 L621) — Gotcha 3 | FLS fixed before the layout is blamed |
| Is the list paired with a Quick Links bar? | Quick Links counts vs filtered views is UNVERIFIED — Gotcha 8 | A note to users or no Quick Links |

A proper configuration puts each column, sort and per-record-type decision in the layout the users actually resolve to, where "just doing it" edits whichever layout opened first and leaves the other record types drifting.

## Core Concepts

### Page Layout owns the related-list contract

A related list on a page-layout-driven surface is a `RelatedListItem` inside the Layout: `relatedList` (Required, the list's name), `fields`, `sortField`, `sortOrder`, `customButtons`, `excludeButtons` and `quickActions` (api_meta 264 L85851-85873). Retrieved standard fields use aliases — "the Fax, Mobile, and Home Phone fields are retrieved as Phone2, Phone3, and Phone4" (L85860-85862). The Lightning record page stores the component choice; the guide's FlexiPage sample shows `force:relatedListContainer` with only a `relatedListComponentOverride` property (api_meta 264 L70339-70342). UNVERIFIED (2026-10-21): that no Lightning related-list component can carry its own column list.

The implication: editing a related list's columns is a Page Layout edit, not a Lightning App Builder edit, even when the resulting record page is 100% Lightning App Builder.

### Sort field + sort direction

Each `RelatedListItem` has one configured `sortField`; "If the sortField is set, the sortOrder field determines the sort order" — `Asc` or `Desc` (api_meta 264 L85868-85873). Separately, `UserInterfaceSettings.multiColumnSortRL` lets users sort related lists by multiple columns, default true, API 63.0+ (api_meta 264 L131893-131895). UNVERIFIED (2026-10-21): the default order when no sort field is set, which field types cannot sort, and silent fallback on an unsortable field.

### Enhanced Related Lists (UNVERIFIED feature set)

Help describes an Enhanced list type that adds per-column filtering, mass actions on selected rows, per-user column resizing, and more rows inline before pagination. UNVERIFIED (2026-10-21): every item in that list, the release it arrived in, the row counts (this skill's frontmatter says 10, older text said 30), and the render cost of many Enhanced lists above the fold. None of these is in the Metadata API, Object Reference or LWC corpus.

### Per-record-type related lists

When an object has multiple record types, each profile × record type pair can route to a different layout (`ProfileLayoutAssignments`, api_meta 264 L100698-100705). Because the related-list contract lives on the Layout, **different record types can see different related lists, with different columns and sort orders**. This is a feature when intentional and a bug when accidental (admins forget to update layout B after editing layout A). The Layout type has no description field (field table api_meta 264 L85051-85153), so record intent in the layout name or the change record, not "in the layout description".

### Search layouts (lookup dialog parity)

The parent object's `SearchLayouts` carry three different lists: `lookupDialogsAdditionalFields` — "The list of fields displayed in a lookup dialog" (api_meta 264 L47528); `lookupFilterFields` — fields that "can be used to filter enhanced lookups" (L47550-47552); and `searchFilterFields` — fields that "can be used to filter a search for the object" (L47574-47575). They are configured separately from the related list. A user can fail to find a record in a lookup because the column or filter they expect is not in the matching list, even when the related list displays it.

---

## Common Patterns

### Pattern 1: Classic Related Lists block on a small Lightning record page

**When to use:** The record page has 4–8 related lists, all relevant to most users, and no list needs filtering.

**How it works:**
1. Edit the Page Layout. Add the related lists in priority order — the array order is the UI order (api_meta 264 L85113-85114). For each, set the columns (≤10, UNVERIFIED cap), sort field, and sort direction.
2. On the Lightning record page in Lightning App Builder, add the **Related Lists** component below the Activity timeline or on a dedicated tab.
3. The component renders the related lists from the page layout in the order configured.

**Why not the alternative:** Using `Related List - Single` × 8 instead requires 8 separate component placements. The all-in-one block is the right default until a related list needs its own dedicated component (e.g., it lives on a different tab from the others).

### Pattern 2: An Enhanced list for the one related list that needs filtering

**When to use:** Users frequently scroll a long related list looking for the subset that matters (e.g., open vs. closed Cases under an Account).

**How it works (UNVERIFIED (2026-10-21): Help-only component properties):**
1. On the Lightning record page, host that one list in a `Related List - Single` set to the Enhanced list type.
2. Choose the relationship to display; columns and sort come from the Page Layout.
3. Enable the filter and mass-action options the users need.

**Why not the alternative:** Building a custom list view tab on the record page duplicates configuration and breaks when the user's Page Layout assignment changes.

### Pattern 3: Per-record-type related-list divergence

**When to use:** Two record types on the same object need genuinely different related-list sets — e.g., the B2C record type doesn't expose the Opportunities related list, while B2B does.

**How it works:**
1. Maintain one Page Layout per record type (do not share a layout across divergent record types).
2. Configure related lists per layout in the intentional shape.
3. Confirm each profile's `layoutAssignments` route every (Profile × Record Type) combination correctly (api_meta 264 L100702-100705) — this is the silent failure point.
4. Record the divergence where the next admin will look — the layout name, the change record, or the config workbook (the Layout type has no description field).

**Why not the alternative:** Sharing one layout across record types and using component-level visibility filters in App Builder hides the component at runtime but leaves the related list on the underlying Page Layout — admins editing the layout later may add columns assuming all record types see them.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Standard record page with several related lists, mostly read | Classic `Related Lists` component, one block | One place to edit |
| One related list users need to filter / mass-act on | Enhanced list type for that list only | Filter + mass actions are Enhanced-only per Help (UNVERIFIED); keep others classic |
| Related list with > 10 columns requested inline | Push secondary columns behind **View All**, keep 10 max inline | Help's 10-column cap (UNVERIFIED); inline width also breaks UX |
| Two record types need different related-list sets | Separate Page Layouts per record type, distinct `layoutAssignments` | Component visibility filters don't remove the related list from the layout |
| Related list needs to live on a dedicated tab in App Builder | `Related List - Single` on the tab | Single component lets you place it independently |
| Org wants users to discover related lists fast (top of page) | `Related Lists - Quick Links` near the top + full related lists on a tab | Quick Links is anchor-style (UNVERIFIED, Help-only) |
| Sort field is a formula referencing another object | Pick a directly stored field on the child instead | Cross-object sort behaviour is UNVERIFIED; a stored field avoids the question |
| Mobile users complain related list looks empty on phone | Reorder columns: most important first | Mobile shows fewer columns inline (UNVERIFIED ~4) |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on a related-list configuration request:

1. Identify the **Page Layout** that the affected user's (Profile, Record Type) combination resolves to — not the Lightning record page. Read the profile's `layoutAssignments` (api_meta 264 L100702-100705) or the Page Layout Assignment screen.
2. Inventory the related list on that Page Layout: `relatedList`, `fields` (order + count), `sortField`, `sortOrder`, `customButtons`. Expect standard-field aliases such as `Phone2` in retrieved XML (api_meta 264 L85860-85862).
3. Decide the Lightning component for hosting with the decision table above.
4. Apply the column / sort changes on the Page Layout (≤10 fields, Help-only cap; a directly stored sort field).
5. If different record types need different shapes, mirror the changes onto the divergent Page Layout(s) or record the intentional divergence outside the layout.
6. Run `python3 skills/admin/related-list-configuration/scripts/check_related_list_configuration.py --manifest-dir force-app/main/default` (add `--strict` in CI), then validate by impersonating a user from each affected (Profile × Record Type) combination — column visibility, sort default, View All, mobile.
7. Capture the configuration in `templates/related-list-configuration-template.md` so the next admin knows the intent.

---

## Review Checklist

Run through these before marking related-list configuration work complete:

- [ ] The Page Layout edited is the one that the affected (Profile × Record Type) resolves to
- [ ] No related list has more than 10 columns configured (Help-only cap, UNVERIFIED); secondary columns are behind View All
- [ ] Sort field is a directly stored field on the child (unsortable-type list UNVERIFIED)
- [ ] If an Enhanced list is used, the filter + mass-action behaviors actually meet the user's need
- [ ] Per-record-type divergence is intentional and recorded outside the layout (Layout has no description field)
- [ ] The parent object's `lookupDialogsAdditionalFields` / `lookupFilterFields` / `searchFilterFields` include what users need in lookups and searches
- [ ] Mobile order is verified — the most important columns are first
- [ ] FLS for the affected fields is consistent with the visibility intent (secguide 262 L621)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems (UNVERIFIED items per the note at the top):

1. **Columns past the 10th may not render (UNVERIFIED cap)** — the Metadata API accepts any `fields` list (api_meta 264 L85859); the cap is Help-only.
2. **Cross-object formula sort fields (UNVERIFIED fallback)** — the configured sort is one `sortField` (api_meta 264 L85868); what happens on an unsortable type is Help-only.
3. **FLS governs related-list columns** — "including related lists" (secguide 262 L621); the blank-cell rendering is UNVERIFIED.
4. **Lightning App Builder visibility filter hides the component, not the Page Layout entry** — the next admin opening the Page Layout sees the related list and may edit it under the wrong assumption.
5. **Enhanced list render cost (UNVERIFIED)** — no corpus guide measures it; defer heavy lists to a tab and measure.
6. **Per-record-type related lists diverge silently after a Page Layout clone** — admins clone Layout A → Layout B, then later add a related list to A only. There is no description field on Layout to warn them (api_meta 264 L85051-85153); the checker reports the divergence.
7. **Mobile shows fewer columns (UNVERIFIED ~4)** — the column order on the Page Layout (api_meta 264 L85113-85114) dictates what mobile users see first.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Related-list configuration table | One row per (Page Layout × related list) with: columns (ordered), sort field, sort direction, Enhanced/classic choice, per-record-type divergence note |
| Component placement plan | Lightning record page → which component (`Related Lists` / `Related List - Single` / Enhanced list type / `Related Lists - Quick Links`) hosts each related list, with rationale |
| Page Layout Assignment confirmation | Profile × Record Type → Page Layout matrix snapshot for the affected layouts |
| FLS impact note | Fields on the configured related lists that field permissions hide for any affected Profile, with intent |
| Mobile parity note | Confirmation that the first columns of each related list are the ones mobile users need most |

---

## Related Skills

- `admin/record-types-and-page-layouts` — Page Layout creation and the Page Layout Assignment matrix that drives which related-list set a user sees
- `admin/lightning-page-performance-tuning` — Tradeoff between Related List - Single vs. all-in-one when First Paint matters; use alongside this skill when the page is heavy
- `admin/global-search-configuration` — Search Layouts and lookup-dialog column choice, which interact with related-list lookups
- `admin/list-views-and-compact-layouts` — Compact layout drives the highlights panel and Mobile App card; related-list configuration drives the inline columns
- `admin/dynamic-forms-migration` — Dynamic Forms moves fields off the layout but **does not** remove related lists from it — relevant when migrating record pages
- `admin/fsl-sla-configuration-requirements` — FSL-specific WorkOrderMilestone-on-Work-Order configuration, which is a specialized case of related-list setup
