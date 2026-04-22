# LLM Anti-Patterns — LWC Chart and Visualization

Common mistakes AI coding assistants make when building charts in LWC.

## Anti-Pattern 1: Instantiating a new Chart in every renderedCallback

**What the LLM generates:** `new Chart(ctx, config)` called directly in renderedCallback with no guard.

**Why it happens:** The model does not know renderedCallback fires on every reactive update.

**Correct pattern:**

```
Guard chart creation with `if (!this._chart) { ... }` and update via
`this._chart.data = newData; this._chart.update()` for changes.
Destroy in disconnectedCallback: `this._chart?.destroy()`. Repeated
instantiation leaks canvases and flickers the UI.
```

**Detection hint:** LWC renderedCallback containing `new Chart(` with no guard.

---

## Anti-Pattern 2: Rendering 50,000 points row-by-row

**What the LLM generates:** Apex returns row-level data; chart config has 50,000 data points.

**Why it happens:** The model optimizes neither Apex nor chart config.

**Correct pattern:**

```
Aggregate in Apex via SOQL aggregate queries (SUM, AVG, COUNT, GROUP
BY a time bucket). Return the aggregate result — hundreds of points,
not tens of thousands. Chart renders smoothly; Apex CPU stays low.
Row-level rendering is a last resort when the analyst explicitly
needs outlier inspection.
```

**Detection hint:** Apex method returning `List<SObject>` with `Limit 50000` and chart config consuming raw rows.

---

## Anti-Pattern 3: Loading Chart.js via CDN instead of Static Resource

**What the LLM generates:** `<script src="https://cdn.jsdelivr.net/npm/chart.js">` inside the LWC.

**Why it happens:** The model applies general web practice without considering Salesforce CSP.

**Correct pattern:**

```
External scripts violate CSP. Bundle the library as a Static Resource
and load via `loadScript(this, chartJsStatic)`. Static Resources are
cached, CSP-compliant, and versioned with your metadata.
```

**Detection hint:** LWC template or JS referencing an external CDN URL for a library.

---

## Anti-Pattern 4: No accessibility fallback for screen readers

**What the LLM generates:** Chart rendered to canvas with no aria attributes and no data table.

**Why it happens:** The model focuses on the visual and ignores the accessibility layer.

**Correct pattern:**

```
Every chart must have a screen-reader accessible alternative: a
hidden data table with `<caption>`, `aria-describedby` from the
canvas to a descriptive summary, and keyboard navigation for
interactive elements. Canvas is inherently opaque to screen readers.
```

**Detection hint:** LWC template with a `<canvas>` for charting and no adjacent table or aria attributes.

---

## Anti-Pattern 5: Using color alone to convey meaning

**What the LLM generates:** Bar chart with red = bad, green = good, no labels or patterns.

**Why it happens:** The model reaches for color the way a designer would without considering colorblindness.

**Correct pattern:**

```
Charts must convey meaning via at least two channels: color plus
shape/pattern/label. Build with palettes safe for colorblindness
(avoid red/green only). Add data labels or icons to reinforce.
Salesforce accessibility guidelines require this.
```

**Detection hint:** Chart config using `colors: ['red', 'green']` with no patterns, labels, or icons.
