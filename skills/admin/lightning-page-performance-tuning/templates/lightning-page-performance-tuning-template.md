# Lightning Page Performance Tuning — Work Template

Use this template when diagnosing or resolving a slow Lightning record page, home page, or app page. Fill in every section before recommending a solution.

---

## Scope

**Skill:** `lightning-page-performance-tuning`

**Request summary:** (describe what the user reported — e.g., "Account record page takes 6+ seconds to load")

---

## Context Gathered

Answer these before proceeding. Do not skip — the correct fix depends on the answers.

| Question | Answer |
|---|---|
| Page type (record / home / app) | |
| Object (if record page) | |
| Total component count on the page | |
| Components on initial viewport (before any tab click) | |
| Does the page use Tabs for progressive disclosure? | |
| EPT from Lightning Experience Insights (P75, first load) | |
| EPT from Lightning Experience Insights (P75, subsequent load) | |
| Number of Related List components | |
| Number of Report Chart components | |
| Any custom LWC/Aura components on the page? | |
| Do users access all information on every record, or only some tabs? | |

**Most common wrong assumption:** There is no hard component count limit. Salesforce flags slow pages via EPT measurement, not component count. Focus on measured EPT, not arbitrary component thresholds.

---

## Component Audit

List every component on the page and categorize:

| Component | Type | Category | Data Weight | Action |
|---|---|---|---|---|
| (e.g., Highlights Panel) | Standard | Essential | Light | Keep on initial viewport |
| (e.g., Pipeline Report Chart) | Standard | Secondary | Heavy | Defer to tab |
| (e.g., Custom Renewal Widget) | Custom LWC | Removable | Heavy | Add lwc:if guard |

Categories:
- **Essential** — must render on initial page load (record detail, highlights, path)
- **Secondary** — can be deferred to a non-default tab
- **Removable** — unused, redundant, or better served by a link to another page

---

## Root Cause Assessment

Check each item and mark the likely root cause:

- [ ] **Too many components on initial viewport** — more than 8-10 components render before any tab click
- [ ] **No progressive disclosure** — page does not use Tabs component; all components render on load
- [ ] **Heavy Related Lists** — full Related List components on high-volume child objects
- [ ] **Report Charts on page** — Report Chart components executing complex reports on every page load
- [ ] **Custom component without conditional rendering** — LWC makes expensive calls regardless of record state
- [ ] **No page variants** — all roles share one page with components only some roles need
- [ ] **Dynamic Forms not leveraged** — fields visible that could be conditionally hidden

---

## Approach

**Pattern selected:** (choose one or more)

- [ ] Tab-based progressive disclosure — group secondary components into tabs
- [ ] Component removal — delete unused or redundant components
- [ ] Page variants — create role-specific page assignments
- [ ] Conditional rendering — add lwc:if to custom components
- [ ] Related List optimization — switch to Related List - Single or defer to tab
- [ ] Report Chart deferral — move Report Charts to non-default tab or replace with cached LWC

**Rationale:** (why this pattern fits the context gathered above)

---

## Proposed Layout

**Initial viewport (renders on load):**
1.
2.
3.

**Tab 1 — "[name]" (default tab):**
1.
2.

**Tab 2 — "[name]":**
1.
2.

**Tab 3 — "[name]":**
1.
2.

**Removed components:**
- (component name) — reason for removal

---

## EPT Targets

| Metric | Baseline (before) | Target (after) | Actual (after) |
|---|---|---|---|
| First load EPT (P75) | | | |
| Subsequent load EPT (P75) | | | |
| XHR calls on initial load | | | |

---

## Sign-Off

- [ ] Baseline EPT recorded before changes
- [ ] Component audit completed
- [ ] Unused components removed
- [ ] Secondary components deferred to tabs
- [ ] Custom components use conditional rendering where applicable
- [ ] Post-change EPT measured (allow 24-48 hours for data)
- [ ] Layout rationale documented for future editors
