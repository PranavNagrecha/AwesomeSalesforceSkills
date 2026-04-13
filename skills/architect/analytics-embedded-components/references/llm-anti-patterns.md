# LLM Anti-Patterns — Analytics Embedded Components

Common mistakes AI coding assistants make when generating or advising on Analytics Embedded Components.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Conflating Embedding Direction — Dashboard-in-Page vs LWC-in-Dashboard

**What the LLM generates:** When asked "how do I embed analytics in my LWC," the LLM generates markup using `wave-wave-dashboard-lwc` inside a custom LWC component registered with `analytics__Dashboard` target — conflating the two distinct patterns. Or when asked "how do I add my LWC to an Analytics dashboard," the LLM advises adding `wave-wave-dashboard-lwc` to the LWC markup, which is wrong for the Pattern B scenario.

**Why it happens:** The word "embed" appears in documentation for both directions. LLMs index on surface-level keyword similarity and do not distinguish between "embedding a dashboard in a page" (using `wave-wave-dashboard-lwc`) and "embedding a custom LWC inside a dashboard canvas" (using `analytics__Dashboard` target in js-meta.xml). These are entirely separate implementation paths with no overlapping setup steps.

**Correct pattern:**

Pattern A — Dashboard embedded IN a Lightning page:
```html
<!-- Use wave-wave-dashboard-lwc on a Lightning record/app page -->
<wave-wave-dashboard-lwc
    developer-name="My_Dashboard"
    record-id={recordId}>
</wave-wave-dashboard-lwc>
```

Pattern B — Custom LWC embedded INSIDE an Analytics dashboard canvas:
```xml
<!-- In myCustomWidget.js-meta.xml — no wave-wave-dashboard-lwc involved -->
<targets>
    <target>analytics__Dashboard</target>
</targets>
```

**Detection hint:** Flag any output that uses `analytics__Dashboard` target AND `wave-wave-dashboard-lwc` in the same component, or that suggests using `wave-wave-dashboard-lwc` as a widget inside a dashboard. These cannot coexist.

---

## Anti-Pattern 2: Using `wave-community-dashboard` on a Lightning App Builder Page

**What the LLM generates:** Code or instructions that use `wave-community-dashboard` to embed a dashboard on a Lightning record page or Lightning app page, often because documentation for both components is indexed together.

**Why it happens:** `wave-community-dashboard` and `wave-wave-dashboard-lwc` have similar attribute signatures (both accept `developer-name`, `record-id`, `show-title`, etc.). LLMs conflate them or pick one arbitrarily. Documentation for Experience Cloud and Lightning pages often appears in the same search results.

**Correct pattern:**

```html
<!-- WRONG for Lightning App Builder pages: -->
<!-- <wave-community-dashboard developer-name="My_Dashboard" /> -->

<!-- CORRECT for Lightning App Builder pages: -->
<wave-wave-dashboard-lwc
    developer-name="My_Dashboard"
    record-id={recordId}>
</wave-wave-dashboard-lwc>

<!-- wave-community-dashboard is ONLY for Experience Cloud (Experience Builder) pages -->
```

**Detection hint:** Any markup using `wave-community-dashboard` in a component with `lightning__RecordPage`, `lightning__AppPage`, or `lightning__HomePage` targets in js-meta.xml is wrong. Similarly, `wave-wave-dashboard-lwc` in a component targeting `comm__Page` or `lightning__CommunityPage` is suspect.

---

## Anti-Pattern 3: Setting Both `dashboard` and `developer-name` on the Same Component

**What the LLM generates:** Component markup that sets both the `dashboard` attribute (18-char ID) and `developer-name` on `wave-wave-dashboard-lwc`, sometimes as a "fallback" pattern or because the LLM does not know which is correct.

**Why it happens:** LLMs infer from similar APIs in other frameworks that providing multiple identifiers creates a fallback chain. In this component, both attributes are recognized but they are mutually exclusive — `dashboard` (ID) silently wins when both are present, with no error.

**Correct pattern:**

```html
<!-- WRONG — both set, dashboard ID silently wins, developer-name ignored -->
<!--
<wave-wave-dashboard-lwc
    dashboard="0FKxx000000xxxxx"
    developer-name="My_Dashboard">
</wave-wave-dashboard-lwc>
-->

<!-- CORRECT — use exactly one identifier; prefer developer-name for portability -->
<wave-wave-dashboard-lwc
    developer-name="My_Dashboard"
    record-id={recordId}>
</wave-wave-dashboard-lwc>
```

**Detection hint:** Flag any markup that contains both `dashboard="0FK` (starts with 0FK) and `developer-name=` attributes on the same component element.

---

## Anti-Pattern 4: Building `state` JSON by String Concatenation

**What the LLM generates:** JavaScript that constructs the `state` attribute value by string concatenation rather than using `JSON.stringify()`. Example: `` `{"myStep": {"selections": ["${this.selectedId}"]}}` `` — which breaks if `selectedId` contains quotes or special characters.

**Why it happens:** LLMs frequently generate template-literal or string-concatenation approaches for dynamic JSON, especially in JavaScript contexts where the correct `JSON.stringify()` pattern is slightly more verbose. Invalid JSON passed to `state` causes silent failure — the dashboard loads in its default state with no error.

**Correct pattern:**

```javascript
// WRONG — string concatenation, breaks on special characters, no validation
// this.dashboardState = `{"myStep": {"selections": ["${this.selectedId}"]}}`;

// CORRECT — always use JSON.stringify() to build state objects
const stateObj = {
    myStep: {
        selections: [this.selectedId]
    }
};
this.dashboardState = JSON.stringify(stateObj);
```

**Detection hint:** Flag any JavaScript that assigns to a `state` binding using template literals (backticks with `${...}`) or string concatenation (`+`) to build JSON. Any state string construction that does not call `JSON.stringify()` is suspect.

---

## Anti-Pattern 5: Assuming `record-id` Automatically Filters the Dashboard

**What the LLM generates:** Guidance that says "pass `record-id` to the component and the dashboard will automatically show data for the current record." This is incorrect — the `record-id` attribute delivers the ID to the dashboard runtime, but the dashboard must be explicitly designed with bindings that consume it.

**Why it happens:** LLMs infer by analogy from other record-context patterns in Salesforce (like `@wire` adapters that use `recordId`) that `record-id` creates an automatic data scope. In the Analytics embedding context, `record-id` is a pass-through — the dashboard designer must configure the binding.

**Correct pattern:**

```
The record-id attribute passes the 18-character record ID to the dashboard at render time.
The dashboard MUST have a filter step or binding in Analytics Studio that reads this value.
Without that dashboard-side configuration, the attribute is silently ignored and the dashboard
shows its default global data view.

Verification step: confirm with the dashboard designer that the dashboard has an explicit
filter binding for the incoming record-id before relying on context filtering in production.
```

**Detection hint:** Any generated content that describes `record-id` as "automatically filtering" or "scoping the dashboard to the record" without mentioning the required dashboard-side binding configuration is presenting an incomplete and misleading picture of how the attribute works.

---

## Anti-Pattern 6: Advising `analytics__Dashboard` Target to Place a Dashboard on a Lightning Page

**What the LLM generates:** Instructions to add `analytics__Dashboard` to a component's `js-meta.xml` targets as a way to make the component appear in Lightning App Builder so a dashboard can be shown on a record page.

**Why it happens:** LLMs sometimes confuse the `analytics__Dashboard` target (which registers an LWC as a widget inside an Analytics dashboard) with a mechanism for exposing a component to App Builder pages. The target has nothing to do with Lightning App Builder availability — it is exclusively for the Analytics dashboard canvas widget picker.

**Correct pattern:**

```xml
<!-- analytics__Dashboard target is ONLY for LWCs that go INSIDE an Analytics dashboard canvas -->
<!-- It does NOT make the component available in Lightning App Builder -->

<!-- To embed a dashboard on a Lightning record page, use wave-wave-dashboard-lwc -->
<!-- in a component registered for lightning__RecordPage: -->
<targets>
    <target>lightning__RecordPage</target>
</targets>

<!-- analytics__Dashboard target is for Pattern B — LWC-inside-dashboard — only -->
```

**Detection hint:** Flag any js-meta.xml that includes `analytics__Dashboard` as a target alongside `lightning__RecordPage` or `lightning__AppPage` in the same component, unless the component is genuinely intended to serve both as a Lightning page component and as a dashboard widget (rare and distinct use cases).
