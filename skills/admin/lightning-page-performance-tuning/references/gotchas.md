# Gotchas — Lightning Page Performance Tuning

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: EPT Is Measured at P75, Not Average or P50

**What happens:** An admin sees EPT of 4.2 seconds in Lightning Experience Insights and interprets this as the average page load time. They optimize the page and bring "most" loads under 3 seconds, but the P75 EPT barely changes because the slowest 25% of loads (often first loads, mobile users, or users with complex sharing calculations) still exceed 4 seconds.

**When it occurs:** Any time EPT data is used for performance measurement. The P75 percentile means 25% of page loads are slower than the reported value. Improvements to already-fast loads do not move the P75 metric.

**How to avoid:** Focus optimization on the factors that affect the slowest quartile of loads: first-load caching, heavy components that affect users with complex sharing models, and components that degrade on slow network connections. Measure both first-load and subsequent-load EPT separately to understand which bucket drives the P75 value.

---

## Gotcha 2: Tab-Deferred Components Still Load When Users Click the Tab

**What happens:** An admin moves 10 heavy components into tabs to improve initial load time. EPT drops significantly. But users who routinely click through all tabs on every record still experience cumulative slowness — the total time to view all tabs exceeds the original single-page load time because each tab click triggers a sequential render-and-fetch cycle.

**When it occurs:** When the user workflow requires accessing all information on every record (e.g., a data entry workflow where the user fills fields across all tabs on every record). Tab deferral optimizes initial load but shifts cost to tab clicks.

**How to avoid:** Tab deferral is most effective when users access non-default tabs infrequently (less than 30% of page views). If the workflow requires all information on every visit, consider reducing component count through consolidation or page variants instead of tab deferral. Interview users about their actual workflow before choosing the optimization strategy.

---

## Gotcha 3: Related List - Single vs. Full Related List Have Very Different Performance Profiles

**What happens:** An admin replaces a "Related List - Single" component (which shows a compact view with limited columns and rows) with a full "Related List" component to give users more data. Page load time increases noticeably because the full Related List fetches all visible rows and columns on initial render, while the Single variant fetches a minimal dataset.

**When it occurs:** When full Related List components are used for child objects with high record counts (hundreds or thousands of child records). The full Related List component renders more rows and columns by default and supports inline editing, both of which add DOM and XHR cost.

**How to avoid:** Use "Related List - Single" for child objects that users primarily scan (view a few top records) and reserve full Related List for child objects where users need to sort, filter, or inline-edit. When a full Related List is needed on a high-volume child object, place it in a non-default tab.

---

## Gotcha 4: Report Chart Components Execute the Full Report Query on Every Page Load

**What happens:** An admin places a Report Chart component on a record page. The underlying report queries a large object with broad filters. Every time any user opens a record page, the report executes — even though the chart data is the same for all users and changes infrequently. On a page viewed 500 times per day, the report runs 500 times per day.

**When it occurs:** Any Report Chart component on a record page or home page where the underlying report targets a large-volume object. The report is not cached between page loads — each page view triggers a fresh report execution.

**How to avoid:** Move Report Chart components to non-default tabs so the report only executes when the user explicitly clicks the tab. Alternatively, replace the Report Chart with a custom LWC that queries a smaller dataset or uses platform cache to avoid redundant server calls. For charts showing org-wide data (not record-specific), move them to a dedicated dashboard page instead of embedding on every record page.

---

## Gotcha 5: Dynamic Forms Improve Performance Only When Fields Are Conditionally Hidden

**What happens:** An admin converts a page layout to Dynamic Forms expecting an automatic performance improvement. The page loads at roughly the same speed because all fields are still visible — Dynamic Forms simply changed the rendering mechanism without reducing what is displayed.

**When it occurs:** When Dynamic Forms is adopted for organizational reasons (field-level visibility rules, flexible layout) without actually hiding fields using visibility conditions. The performance benefit of Dynamic Forms comes from conditionally hiding fields, which reduces the data fetched and DOM rendered — not from the conversion itself.

**How to avoid:** When converting to Dynamic Forms for performance, always pair the conversion with visibility conditions that hide fields irrelevant to the current record state. If no fields will be conditionally hidden, Dynamic Forms is still useful for layout flexibility but should not be expected to improve EPT.
