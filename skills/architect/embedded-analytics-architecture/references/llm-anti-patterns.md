# LLM Anti-Patterns — Embedded Analytics Architecture

Common mistakes AI coding assistants make when generating or advising on embedded CRM Analytics dashboard architecture. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using `filter` Attribute on LWC wave-wave-dashboard Component

**What the LLM generates:**
```html
<c-wave-dashboard dashboard-dev-name="MyDashboard" filter={filterJson}></c-wave-dashboard>
```

**Why it happens:** LLMs are trained on a mix of Aura `wave:waveDashboard` and LWC `wave-wave-dashboard` documentation and examples. They conflate the two components' APIs. The `filter` attribute is prominently documented for the Aura component.

**Correct pattern:**
```html
<!-- LWC wave-wave-dashboard uses state attribute, NOT filter -->
<c-wave-dashboard
  dashboard-dev-name="MyDashboard"
  record-id={recordId}
  state={dashboardStateJson}>
</c-wave-dashboard>
```

**Detection hint:** Any `wave-wave-dashboard` component usage with a `filter` attribute binding.

---

## Anti-Pattern 2: Hard-Coding dashboardDevName in Component Markup

**What the LLM generates:**
```html
<c-wave-dashboard dashboard-dev-name="AccountSummaryDashboard_v2"></c-wave-dashboard>
```

**Why it happens:** LLMs default to the simplest code pattern. Hard-coding a string value in component markup is the most direct approach and appears in many documentation examples.

**Correct pattern:**
```javascript
// Apex controller retrieves from Custom Metadata
@AuraEnabled(cacheable=true)
public static String getDashboardDevName(String context) {
  Analytics_Config__mdt config = [
    SELECT Dashboard_Dev_Name__c FROM Analytics_Config__mdt WHERE Context__c = :context LIMIT 1
  ];
  return config?.Dashboard_Dev_Name__c;
}
```

**Detection hint:** Literal string in `dashboard-dev-name` attribute in component markup rather than a JavaScript property.

---

## Anti-Pattern 3: Assuming record-id Auto-Filters the Dashboard

**What the LLM generates:** "Add `record-id={recordId}` to the component and the dashboard will automatically show data for the current record."

**Why it happens:** `record-id` sounds like it would automatically filter the dashboard to the current record context. LLMs don't model the two-step requirement: (1) pass record-id to component, (2) configure dashboard binding to consume the record ID as a filter.

**Correct pattern:**
```
record-id passes the context to the dashboard.
The dashboard MUST have a binding configured in Dashboard Designer that uses the record ID:
- Create a step parameter in the dashboard
- Bind the step parameter to the record-id using the Dashboard Designer binding panel
- The step's SAQL filter uses the parameter value
Without the dashboard binding, record-id is silently ignored.
```

**Detection hint:** Instructions that say "add record-id and the dashboard filters automatically" without mentioning dashboard binding configuration.

---

## Anti-Pattern 4: Using Aura wave:waveDashboard on Lightning Experience Pages

**What the LLM generates:** Code using `<wave:waveDashboard>` for embedding in Lightning Experience record pages.

**Why it happens:** The Aura component has more documentation and examples in older training data. LLMs don't consistently recommend the newer LWC component for Lightning Experience contexts.

**Correct pattern:**
```
Component selection:
- Lightning Experience pages (record, app, home): LWC wave-wave-dashboard
- Experience Cloud authenticated pages: LWC wave-wave-dashboard
- Visualforce pages only: Aura wave:waveDashboard (LWC not available in VF)
```

**Detection hint:** `<wave:waveDashboard>` in a Lightning Web Component or Aura component targeting a Lightning Experience page context.

---

## Anti-Pattern 5: No Performance Strategy for Multiple Embedded Dashboards

**What the LLM generates:** A Lightning page design with 3-4 embedded CRM Analytics dashboards, all loaded eagerly on page open, with no performance consideration.

**Why it happens:** LLMs don't model the performance impact of multiple dashboard loads. Each dashboard triggers multiple API calls to the CRM Analytics engine on load.

**Correct pattern:**
```
Performance architecture for multiple embedded dashboards:
1. Only one dashboard should be visible above the fold — load eagerly
2. Additional dashboards below the fold: use a tab panel or accordion to load lazily
3. For dashboards in a side panel: load only when the panel is opened
4. Pre-filter dashboards with record context before rendering to reduce dataset scan
```

**Detection hint:** Page design with 2+ embedded dashboards without any mention of lazy loading or tab-based organization.
