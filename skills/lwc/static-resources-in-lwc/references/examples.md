# Examples - Static Resources In LWC

## Example 1: One-Time Chart Library Load From A Zipped Static Resource

**Context:** A dashboard component needs Chart.js and its bundled assets.

**Problem:** The first implementation tries to inject a CDN script tag from the template and reinitializes the chart on every rerender.

**Solution:**

Package the library as a zip resource and load it once from `renderedCallback()`.

```javascript
import { LightningElement } from 'lwc';
import chartJs from '@salesforce/resourceUrl/chartjs_4_4';
import { loadScript } from 'lightning/platformResourceLoader';

export default class RevenueChart extends LightningElement {
    chartInitialized = false;

    renderedCallback() {
        if (this.chartInitialized) {
            return;
        }
        this.chartInitialized = true;

        loadScript(this, `${chartJs}/chart.umd.min.js`)
            .then(() => this.initializeChart())
            .catch((error) => {
                this.chartInitialized = false;
                this.loadError = error;
            });
    }
}
```

**Why it works:** The library is delivered through a supported Salesforce path, and the component avoids duplicate loading during rerender.

---

## Example 2: Reusable Asset Pack For Brand Images

**Context:** Several components need the same set of branded SVG files and icons.

**Problem:** Teams start uploading each image as a separate static resource with inconsistent names and no shared convention.

**Solution:**

Store the assets in one resource and construct URLs from a stable base path.

```javascript
import brandAssets from '@salesforce/resourceUrl/brand_assets';

export default class CaseEmptyState extends LightningElement {
    heroUrl = `${brandAssets}/illustrations/case-empty.svg`;
}
```

```html
<template>
    <img src={heroUrl} alt="No open cases" />
</template>
```

**Why it works:** Consumers share one versioned asset package and one internal path contract.

---

## Example 3: The Resource Metadata Is Where The Contract Lives

**Context:** Three components import `chartjs_4_4`. Two of them break after a routine
library bump because the vendor moved the UMD build from the archive root into `dist/`.

**Problem:** The archive layout was known only to whoever last uploaded the zip. Nothing in
the repo said where `chart.umd.min.js` sat, so the reviewer had no way to see that the
consumer paths were now wrong.

**Solution:**

Pin the layout in the resource's own metadata file, where it travels with the artifact and
shows up in every deploy diff.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<StaticResource xmlns="http://soap.sforce.com/2006/04/metadata">
    <cacheControl>Public</cacheControl>
    <contentType>application/zip</contentType>
    <description>Chart.js 4.4.1 UMD. Layout: dist/chart.umd.min.js, dist/chart.min.css. Consumers: revenueChart, pipelineTrend, forecastGauge. Bump the resource name on any layout change.</description>
</StaticResource>
```

**Why it works:** `description` is a real `StaticResource` field (255-character limit), so
the layout, the consumer list, and the version rule become part of the reviewed metadata
rather than tribal knowledge. A layout change now shows up as a diff on a file someone has
to approve.

---

## Anti-Pattern: Remote Script Tags In LWC

**What practitioners do:** They add a script tag that points to a public CDN because that is how the library is documented for generic websites.

```html
<!-- Never does anything in an LWC template -->
<template>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <canvas class="chart"></canvas>
</template>
```

**What goes wrong:** CSP, deployment control, and supportability all get worse. The component depends on a resource Salesforce is not packaging or governing. Adding the CDN host to Trusted URLs does not rescue it — a Trusted URL permits API calls, not JavaScript loading from a third-party site.

**Correct approach:** Package the dependency as a static resource and load it through the supported LWC resource APIs.

```javascript
import { loadScript } from 'lightning/platformResourceLoader';
import CHARTJS from '@salesforce/resourceUrl/chartjs_4_4';

await loadScript(this, `${CHARTJS}/dist/chart.umd.min.js`);
```
