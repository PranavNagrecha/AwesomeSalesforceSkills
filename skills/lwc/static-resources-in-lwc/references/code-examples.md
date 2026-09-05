# Code Examples - Static Resources In LWC

A complete, deployable bundle: one component that loads a JavaScript library **and** its
stylesheet out of a single zip static resource, hands the library an `lwc:dom="manual"`
container, renders an image from a second resource, and ships with the `StaticResource`
metadata, the manifest, and a Jest test.

Every claim below is grounded in the Lightning Web Components Developer Guide (page slug
plus the extracted-text line) or the Metadata API / Object Reference guides. Sources are
listed with their claims in `well-architected.md`.

---

## 1. What gets deployed

```text
force-app/main/default/
├── lwc/
│   └── revenueChart/
│       ├── revenueChart.html
│       ├── revenueChart.js
│       ├── revenueChart.css
│       ├── revenueChart.js-meta.xml
│       └── __tests__/
│           └── revenueChart.test.js
└── staticresources/
    ├── chartjs_4_4.zip                    ← dist/chart.umd.min.js + dist/chart.min.css
    ├── chartjs_4_4.resource-meta.xml
    ├── brand_assets.zip                   ← illustrations/*.svg
    └── brand_assets.resource-meta.xml
```

**How to read it**

- The static resource **name** is the identifier the component imports, not the file name.
  A name may contain only letters, digits, and underscores; it must begin with a letter,
  must not end with an underscore, and must not contain two consecutive underscores
  (`create-resources` L3646). `chartjs_4_4` is legal; `chartjs__4_4` and `chartjs_` are not.
- `staticresources/` is a flat folder — "You can't create subdirectories of
  `staticresources`" (`create-resources` L3663). Nesting lives *inside* the archive, not
  beside it.
- Every content file needs an accompanying `<name>.resource-meta.xml`; the suffix is
  `.resource` for the template file and the metadata file is `resource-meta.xml`
  (Metadata API Developer Guide, StaticResource, api_meta.txt L130909-L130910).
- The `__tests__` folder is never saved to Salesforce; add it to `.forceignore`
  (`unit-testing-using-jest-create-tests` L12329).

---

## 2. StaticResource metadata — and the `cacheControl` decision

```xml
<?xml version="1.0" encoding="UTF-8"?>
<StaticResource xmlns="http://soap.sforce.com/2006/04/metadata">
    <cacheControl>Public</cacheControl>
    <contentType>application/zip</contentType>
    <description>Chart.js 4.4 UMD build and stylesheet. Archive layout: dist/chart.umd.min.js, dist/chart.min.css. Consumers concatenate that path onto the resource URL - treat it as versioned API.</description>
</StaticResource>
```

Shaped from the guide's own sample definition, which carries `contentType` and
`description` (api_meta.txt L130954-L130959), extended with the required `cacheControl`.

| Field | Required? | Notes |
|---|---|---|
| `cacheControl` | Required (API 14.0+) | `StaticResourceCacheControl` enum: `Private` or `Public` only (api_meta.txt L130929-L130933) |
| `contentType` | Required | The MIME type, e.g. `text/plain` in the guide's sample; `application/zip` for an archive (api_meta.txt L130941). Label is Mime Type, limit 120 characters (object_reference.txt L273934-L273940) |
| `description` | Optional | Limit 255 characters (object_reference.txt L273941-L273947). Use it for the archive path contract — it is the only place the layout is documented next to the artifact |
| `content` | Inherited | Base64 binary, supplied by the file itself; you never hand-write it (api_meta.txt L130935-L130937) |
| `fullName` | Inherited | The resource name; same character rules as above (api_meta.txt L130945-L130947) |

**Choosing the value — this is a data-exposure decision, not a performance knob:**

| Choose | When | What the platform then does |
|---|---|---|
| `Public` | The bytes are safe for anyone on the internet: a vendor library build, a public brand logo, a web font | "accessible after caching to all internet traffic, including unauthenticated users. The resource is stored on the Salesforce server in a shared cache, which results in faster load times" (object_reference.txt L273930-L273932; same wording in `create-resources` L3651) |
| `Private` | The bytes are org-specific or customer-identifying: an internal price list, a seeded JSON dataset, an unreleased brand asset | "accessible to all authenticated users. The static resource is stored on the Salesforce server in a user's individual cache for the duration of the session" (object_reference.txt L273927-L273929; `create-resources` L3650) |

Same file for `brand_assets`, with a description that pins its own layout:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<StaticResource xmlns="http://soap.sforce.com/2006/04/metadata">
    <cacheControl>Public</cacheControl>
    <contentType>application/zip</contentType>
    <description>Brand illustrations. Archive layout: illustrations/case-empty.svg, illustrations/no-results.svg.</description>
</StaticResource>
```

---

## 3. The template — a manual-DOM container plus a resourceUrl image

```html
<template>
    <lightning-card title="Revenue" icon-name="standard:opportunity">
        <div class="slds-var-p-around_medium">
            <!--
              lwc:dom="manual" goes on an EMPTY native element. The component calls
              appendChild() on it to insert DOM the library owns; the engine then
              preserves encapsulation (js-third-party-library L2669-L2670).
            -->
            <div class="chart-host" lwc:dom="manual"></div>

            <template lwc:if={loadFailed}>
                <p class="slds-text-color_error" role="alert">
                    Chart library could not be loaded. Refresh to retry.
                </p>
                <img src={emptyStateUrl} alt="Revenue chart unavailable" />
            </template>
        </div>
    </lightning-card>
</template>
```

`{emptyStateUrl}` is plain property syntax — "To reference a resource in a template, use
`{property}` syntax, which is the same syntax you use to reference any JavaScript
property" (`create-resources` L3661).

---

## 4. The JavaScript

```javascript
import { LightningElement } from 'lwc';
import { loadScript, loadStyle } from 'lightning/platformResourceLoader';
import CHARTJS from '@salesforce/resourceUrl/chartjs_4_4';
import BRAND_ASSETS from '@salesforce/resourceUrl/brand_assets';

// A packaged resource is namespaced: import from '@salesforce/resourceUrl/ns__name'.
// (create-resources L3657: "namespace - If the static resource is in a managed package,
// this value is the namespace of the managed package.")

export default class RevenueChart extends LightningElement {
    // Archive paths are concatenated onto the resource URL. The internal layout of the
    // zip is part of the resource's contract (create-resources L3660).
    emptyStateUrl = `${BRAND_ASSETS}/illustrations/no-results.svg`;

    chartLoaded = false;
    loadFailed = false;
    chart;

    // renderedCallback() runs on EVERY render, so a one-time operation needs a boolean
    // field (create-lifecycle-hooks-rendered L4136). Loading here - rather than in
    // connectedCallback() - also guarantees the .chart-host element already exists
    // (js-third-party-library L2680).
    async renderedCallback() {
        if (this.chartLoaded) {
            return;
        }
        this.chartLoaded = true;

        try {
            // Both calls return promises; Promise.all aggregates them so the callback
            // runs only after both files resolve (js-third-party-library L2681).
            await Promise.all([
                loadScript(this, `${CHARTJS}/dist/chart.umd.min.js`),
                loadStyle(this, `${CHARTJS}/dist/chart.min.css`)
            ]);
            this.renderChart();
        } catch (error) {
            // catch() handles any error during the load process (L2681). Reset the guard
            // so a later render can retry rather than sitting silently broken.
            this.chartLoaded = false;
            this.loadFailed = true;
            // eslint-disable-next-line no-console
            console.error('Static resource load failed', error);
        }
    }

    renderChart() {
        // Never document.querySelector - "In a Lightning web component, you can't use
        // document to query for DOM elements. Instead, use this.template."
        // (js-third-party-library L2744)
        const host = this.template.querySelector('.chart-host');
        const canvas = document.createElement('canvas');
        host.appendChild(canvas);

        // Chart is a global the UMD build attached to window; it exists only because the
        // promise above already resolved.
        // eslint-disable-next-line no-undef
        this.chart = new Chart(canvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['Q1', 'Q2', 'Q3', 'Q4'],
                datasets: [{ label: 'Closed Won', data: [120, 190, 140, 220] }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }

    disconnectedCallback() {
        // The library owns DOM and timers the engine did not create, so the component
        // has to tear them down itself.
        if (this.chart) {
            this.chart.destroy();
            this.chart = undefined;
        }
    }
}
```

**UNVERIFIED (2026-09-05):** `Chart#destroy()` is Chart.js library API, not a platform
API — it is not documented in any Salesforce guide. The *pattern* (clean up what the
library created) is grounded; the exact method name comes from the vendor's docs.

---

## 5. The component stylesheet

```css
/*
 * Styles for the host element and the container. Rules here are scoped to this
 * component in shadow DOM (create-components-css L1809).
 *
 * They do NOT reach the nodes the library appended inside lwc:dom="manual" when the
 * component renders in light DOM: "Light DOM scoped styles don't apply to content
 * that's manually injected into the template inside of lwc:dom='manual'"
 * (create-light-dom L3483). The library's own stylesheet, loaded with loadStyle,
 * is what styles those nodes.
 */
.chart-host {
    position: relative;
    height: 20rem;
    width: 100%;
}
```

---

## 6. The component configuration file

```xml
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <isExposed>true</isExposed>
    <masterLabel>Revenue Chart</masterLabel>
    <description>Bar chart of closed-won revenue, rendered by a charting library packaged as a static resource.</description>
    <targets>
        <target>lightning__RecordPage</target>
        <target>lightning__AppPage</target>
        <target>lightning__HomePage</target>
    </targets>
</LightningComponentBundle>
```

`apiVersion`, `isExposed`, `masterLabel`, `description`, and `targets` are all
`LightningComponentBundle` fields (api_meta.txt L84011-L84053). Versioning is not
optional: "Beginning in Spring '25, versioning is required for all custom components …
Attempting to save an unversioned component to Salesforce results in an error"
(`get-started-api-versioning` L143). See `templates/lwc/component-skeleton/` for the
canonical bundle shape and `templates/lwc/jest.config.js` for the Jest configuration this
test assumes.

---

## 7. The Jest test

```javascript
import { createElement } from 'lwc';
import RevenueChart from 'c/revenueChart';
import { loadScript, loadStyle } from 'lightning/platformResourceLoader';

// UNVERIFIED (2026-09-05): the LWC Developer Guide documents jest mocks for
// lightning/navigation, lightning/uiRecordApi, @salesforce/apex and @salesforce/label
// (unit-testing-using-jest-create-tests L12434-L12453, L12650) but shows no mock for
// lightning/platformResourceLoader or @salesforce/resourceUrl. sfdx-lwc-jest ships
// lightning-stubs for lightning/* modules (unit-testing-using-jest-patterns L12622), so
// the import resolves; jest.mock() below replaces the stub with resolving spies. Verify
// against your sfdx-lwc-jest version before relying on the return shape.
jest.mock(
    'lightning/platformResourceLoader',
    () => ({
        loadScript: jest.fn(() => Promise.resolve()),
        loadStyle: jest.fn(() => Promise.resolve())
    }),
    { virtual: true }
);

// The resourceUrl import resolves to a string in Jest. Pinning it makes the assertion
// on the archive path meaningful.
jest.mock('@salesforce/resourceUrl/chartjs_4_4', () => '/resource/chartjs_4_4', {
    virtual: true
});
jest.mock('@salesforce/resourceUrl/brand_assets', () => '/resource/brand_assets', {
    virtual: true
});

// The library global the UMD build would have attached to window.
global.Chart = jest.fn().mockImplementation(() => ({ destroy: jest.fn() }));

describe('c-revenue-chart', () => {
    afterEach(() => {
        // The jsdom instance is shared across test cases in a single file, so reset the
        // DOM (unit-testing-using-jest-create-tests L12336-L12337).
        while (document.body.firstChild) {
            document.body.removeChild(document.body.firstChild);
        }
        jest.clearAllMocks();
    });

    function flush() {
        return Promise.resolve();
    }

    it('loads the script and the stylesheet from the archive paths', async () => {
        const element = createElement('c-revenue-chart', { is: RevenueChart });
        document.body.appendChild(element);
        await flush();

        expect(loadScript).toHaveBeenCalledWith(
            expect.anything(),
            '/resource/chartjs_4_4/dist/chart.umd.min.js'
        );
        expect(loadStyle).toHaveBeenCalledWith(
            expect.anything(),
            '/resource/chartjs_4_4/dist/chart.min.css'
        );
    });

    it('loads the library exactly once across repeated renders', async () => {
        const element = createElement('c-revenue-chart', { is: RevenueChart });
        document.body.appendChild(element);
        await flush();

        // Force additional render passes.
        element.title = 'again';
        await flush();
        element.title = 'and again';
        await flush();

        expect(loadScript).toHaveBeenCalledTimes(1);
    });

    it('renders the fallback and resets the guard when the load fails', async () => {
        loadScript.mockImplementationOnce(() => Promise.reject(new Error('404')));

        const element = createElement('c-revenue-chart', { is: RevenueChart });
        document.body.appendChild(element);
        await flush();
        await flush();

        const alert = element.shadowRoot.querySelector('[role="alert"]');
        expect(alert).not.toBeNull();

        const img = element.shadowRoot.querySelector('img');
        expect(img.src).toContain('/resource/brand_assets/illustrations/no-results.svg');
    });
});
```

Run it with `npm run test:unit -- revenueChart`. Jest tests are local only and never
reach the org (`unit-testing-using-jest-create-tests` L12326).

---

## 8. Manifest

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>chartjs_4_4</members>
        <members>brand_assets</members>
        <name>StaticResource</name>
    </types>
    <types>
        <members>revenueChart</members>
        <name>LightningComponentBundle</name>
    </types>
    <version>67.0</version>
</Package>
```

`StaticResource` supports the `*` wildcard in `package.xml` (api_meta.txt L130963-L130965),
so `<members>*</members>` retrieves every resource in the org — useful once, punishing
afterwards if the org holds hundreds of megabytes of them.

---

## 9. Retrieve, deploy, verify

```bash
# Pull the current definitions before editing anything
sf project retrieve start \
  --metadata "StaticResource:chartjs_4_4" \
  --metadata "StaticResource:brand_assets" \
  --metadata "LightningComponentBundle:revenueChart" \
  --target-org myOrg

# Dry run: validate without saving anything to the org
sf project deploy start --manifest manifest/package.xml --dry-run --target-org myOrg

# Unit tests run locally; they neither need nor touch the org
npm run test:unit -- revenueChart

# Static analysis over the bundle and the resource folder
python3 scripts/check_static_resources_in_lwc.py --manifest-dir force-app

# Deploy for real
sf project deploy start --manifest manifest/package.xml --target-org myOrg
```

**Verification — confirm the resource landed with the caching policy you intended:**

```sql
SELECT Name, ContentType, CacheControl, BodyLength, NamespacePrefix, LastModifiedDate
FROM StaticResource
WHERE Name IN ('chartjs_4_4', 'brand_assets')
ORDER BY Name
```

`StaticResource` supports `query()` and exposes `Name`, `ContentType`, `CacheControl`,
`BodyLength`, and `Description` (object_reference.txt L273887-L273953; Supported Calls including query() at L273891-L273892). Two things to read
off the result:

- `CacheControl` — a resource that silently came back `Public` is readable by
  unauthenticated internet traffic once cached. Fix it before anyone links to it.
- `BodyLength` — the per-resource ceiling is 5 MB and the org ceiling is 250 MB
  (`create-resources` L3648; restated in `create-use-third-party-components` L4190). Sum
  `BodyLength` across the org to see how close you are:

```sql
SELECT SUM(BodyLength) total FROM StaticResource
```

Then confirm the load path in the browser: open the component with Debug Mode on and
check the Network panel for one request per file per page load, not one per render.
