# Well-Architected Notes — Related List Configuration

## Relevant Pillars

- **Operational Excellence** — Related-list configuration is one of the most-touched, lowest-documented admin surfaces. Per-record-type divergence, Page Layout assignment matrices, and Lightning record page component choice need explicit documentation in the Page Layout description and team-level runbooks; otherwise the next admin guesses and drift compounds.
- **Performance** — Component choice (`Related Lists` block vs. `Related List - Single` vs. `Enhanced Related Lists`) directly affects record-page First Paint. Enhanced Related Lists are richer but heavier; placing more than ~6 above the fold has been measured to add hundreds of milliseconds on slow networks.
- **Security** — FLS interacts with related-list columns silently (hidden fields render as blank cells, not access-denied errors). Sharing filters rows but does not change column choice. Misreading "missing data" as a layout bug routes admins away from the real FLS / sharing issue.

## Architectural Tradeoffs

**Centralized Page Layout per record type vs. one layout + App Builder visibility filters.** Per-record-type layouts make divergence visible in the Page Layout list (where layout-editing admins look) at the cost of N layouts to maintain. Visibility filters on the Lightning record page centralize the layout but bury divergence in App Builder filter expressions, where the next layout-editing admin will not see it. Prefer per-record-type layouts; the maintenance cost is real, but the alternative is silent drift.

**Classic Related Lists vs. Enhanced Related Lists.** Classic is one all-in-one block: low render cost, low feature surface (no filter, no mass action, 5–10 rows inline, 10-column cap). Enhanced is per-list, richer (filter, mass actions, 30 rows inline, wider column counts) but heavier per instance. Use Enhanced only where users actually need filtering or mass actions; keep the rest classic.

**Inline data vs. View All.** Inline density tempts admins to cram every field into the visible 10 columns. View All exists for the long-tail use case; relegating less-used columns there preserves inline readability without hiding the data. Mobile (which sees ~4 columns inline) makes this tradeoff even sharper.

## Anti-Patterns

1. **Editing related-list columns through Lightning App Builder instead of the Page Layout.** The Lightning component chooses *which* related list to render but not *what columns it has*. Sending users to App Builder for column changes is wrong direction and an LLM-common mistake.
2. **Hiding related lists via App Builder visibility filter instead of per-record-type Page Layouts.** The component is hidden at runtime, but the related-list block remains visible to the next layout-editing admin, who then assumes all record types see it.
3. **Treating Enhanced Related Lists as a blanket replacement for classic.** Enhanced has real per-component render cost. Use it where the filter / mass-action features pay off; not everywhere.

## Official Sources Used

- Salesforce Help — "Related Lists" feature overview and how Page Layouts drive related-list rendering — https://help.salesforce.com/s/articleView?id=sf.customize_layout.htm&type=5
- Salesforce Help — "Enhanced Related Lists" component (Spring '24 GA) and its filter / mass-action surface — https://help.salesforce.com/s/articleView?id=sf.lex_related_list_filtering.htm&type=5
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — `Layout` metadata type, specifically the `<relatedLists>` element that carries `sortField`, `sortOrder`, and the field list — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_layouts.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Help — Lightning App Builder "Related Lists" / "Related List - Single" / "Related Lists - Quick Links" component reference — https://help.salesforce.com/s/articleView?id=sf.lightning_app_builder_components_related_lists.htm&type=5
