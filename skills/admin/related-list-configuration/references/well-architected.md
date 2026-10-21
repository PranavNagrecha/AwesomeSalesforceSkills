# Well-Architected Notes — Related List Configuration

UNVERIFIED (2026-10-21), applies to this file: the render-cost figures, the Enhanced filter / mass-action feature set and the mobile column count are Help or field reports, not corpus facts.

## Relevant Pillars

- **Operational Excellence** — Related-list configuration is one of the most-touched, lowest-documented admin surfaces. Per-record-type divergence, Page Layout assignment matrices, and Lightning record page component choice need explicit documentation in team-level runbooks or the change record — the Layout type has no description field (api_meta 264 L85051-85153) — otherwise the next admin guesses and drift compounds.
- **Performance** — Component choice (`Related Lists` block vs. `Related List - Single` vs. Enhanced list type) affects record-page render. UNVERIFIED (2026-10-21): that more than ~6 Enhanced lists above the fold add hundreds of milliseconds; measure the page.
- **Security** — Field permissions "control the visibility of fields in any part of the app, including related lists" (secguide 262 L621). Sharing filters rows but does not change column choice. Misreading "missing data" as a layout bug routes admins away from the real FLS / sharing issue.

## Architectural Tradeoffs

**Centralized Page Layout per record type vs. one layout + App Builder visibility filters.** Per-record-type layouts (routed by `ProfileLayoutAssignments`, api_meta 264 L100698-100705) make divergence visible in the Page Layout list at the cost of N layouts to maintain. Visibility filters on the Lightning record page centralize the layout but bury divergence in App Builder filter expressions, where the next layout-editing admin will not see it. Prefer per-record-type layouts; the maintenance cost is real, but the alternative is silent drift.

**Classic Related Lists vs. Enhanced Related Lists.** Classic is one all-in-one block with a lower feature surface; Enhanced adds filter and mass actions per list (Help-only, UNVERIFIED). Use Enhanced only where users actually need filtering or mass actions; keep the rest classic.

**Inline data vs. View All.** Inline density tempts admins to cram every field into the visible columns. View All exists for the long-tail use case; relegating less-used columns there preserves inline readability without hiding the data. Mobile (fewer columns inline, UNVERIFIED count) makes this tradeoff sharper.

## Architectural Anti-Patterns

1. **Editing related-list columns through Lightning App Builder instead of the Page Layout.** Columns are `RelatedListItem.fields` on the Layout (api_meta 264 L85859); the guide's FlexiPage sample stores only the component and a `relatedListComponentOverride` property (L70339-70342). Sending users to App Builder for column changes is the wrong direction for the layout-driven lists and an LLM-common mistake. UNVERIFIED (2026-10-21): whether an Enhanced `Related List - Single` can hold its own columns — Help-only.
2. **Hiding related lists via App Builder visibility filter instead of per-record-type Page Layouts.** The component is hidden at runtime, but the related list remains on the layout for the next layout-editing admin, who then assumes all record types see it.
3. **Treating Enhanced Related Lists as a blanket replacement for classic.** Use it where the filter / mass-action features pay off; not everywhere.

## Official Sources Used

- Metadata API Developer Guide — `Layout.relatedLists`, "listed in the order they appear in the user interface" (api_meta 264 L85113-85114); `RelatedListItem` fields, standard-field aliases, `sortField`, `sortOrder` Asc/Desc (L85851-85873); the Layout field table, which has no description field (L85051-85153) — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_layouts.htm
- Metadata API Developer Guide — `ProfileLayoutAssignments.layout` and optional `recordType` (api_meta 264 L100698-100705); `SearchLayouts.lookupDialogsAdditionalFields`, `lookupFilterFields`, `searchFilterFields` (L47528, L47550-47552, L47574-47575); `UserInterfaceSettings.multiColumnSortRL` (L131893-131895); FlexiPage `force:relatedListContainer` sample (L70339-70342).
- Security Implementation Guide — field permissions apply to related lists (secguide 262 L621).
- Salesforce Help (not corpus) — "Related Lists" overview, Enhanced Related Lists, and the Lightning App Builder related-list components — https://help.salesforce.com/s/articleView?id=sf.customize_layout.htm&type=5 ; https://help.salesforce.com/s/articleView?id=sf.lex_related_list_filtering.htm&type=5 ; https://help.salesforce.com/s/articleView?id=sf.lightning_app_builder_components_related_lists.htm&type=5
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
