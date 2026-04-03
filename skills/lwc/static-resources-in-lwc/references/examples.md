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

## Anti-Pattern: Remote Script Tags In LWC

**What practitioners do:** They add a script tag that points to a public CDN because that is how the library is documented for generic websites.

**What goes wrong:** CSP, deployment control, and supportability all get worse. The component depends on a resource Salesforce is not packaging or governing.

**Correct approach:** Package the dependency as a static resource and load it through the supported LWC resource APIs.
