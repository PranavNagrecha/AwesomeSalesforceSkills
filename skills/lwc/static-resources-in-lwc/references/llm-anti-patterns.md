# LLM Anti-Patterns — Static Resources in LWC

Common mistakes AI coding assistants make when generating or advising on loading static resources in LWC.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Loading a script via document.createElement instead of platformResourceLoader

**What the LLM generates:**

```javascript
connectedCallback() {
    const script = document.createElement('script');
    script.src = 'https://cdn.example.com/chart.js';
    document.head.appendChild(script);
}
```

**Why it happens:** LLMs use the standard web pattern for dynamic script loading. In Salesforce, uploading the library as a static resource "is a Lightning Web Components content security policy requirement" (`js-third-party-library` L2655), and a Trusted URL does not help: "you can't load JavaScript resources from a third-party site, even from a trusted URL" (`js-api-calls`).

**Correct pattern:**

```javascript
import { loadScript } from 'lightning/platformResourceLoader';
import CHARTJS from '@salesforce/resourceUrl/chartjs';

async renderedCallback() {
    if (this._chartLoaded) return;
    try {
        await loadScript(this, CHARTJS + '/chart.min.js');
        this._chartLoaded = true;
        this.initChart();
    } catch (error) {
        this.error = 'Failed to load Chart.js';
    }
}
```

**Detection hint:** `document.createElement('script')` or CDN URLs in LWC files.

---

## Anti-Pattern 2: Wrong path inside a zipped static resource

**What the LLM generates:**

```javascript
import MY_LIB from '@salesforce/resourceUrl/myLibrary';

await loadScript(this, MY_LIB + '/myLibrary.js');
// Fails — the zip root folder name does not match the resource name
```

**Why it happens:** LLMs assume the zip extracts to the resource name. In reality, the path must match the actual folder structure inside the zip. If the zip was created from a folder called `dist`, the path is `/dist/myLibrary.js`.

**Correct pattern:**

```javascript
// Check the actual zip contents — the path is relative to the zip root
await loadScript(this, MY_LIB + '/dist/myLibrary.min.js');
```

**Detection hint:** `loadScript` or `loadStyle` calls that fail at runtime — check that the path after the resource URL matches the actual zip folder structure.

---

## Anti-Pattern 3: Not guarding against double-loading in renderedCallback

**What the LLM generates:**

```javascript
renderedCallback() {
    loadScript(this, MY_LIB + '/lib.js').then(() => {
        this.initLibrary();
    });
    // Runs on every render — loads the script multiple times
}
```

**Why it happens:** LLMs place the `loadScript` call in `renderedCallback` without a guard. Since `renderedCallback` fires on every render cycle, the script loads repeatedly.

**Correct pattern:**

```javascript
_libLoaded = false;

async renderedCallback() {
    if (this._libLoaded) return;
    this._libLoaded = true;
    try {
        await loadScript(this, MY_LIB + '/lib.js');
        this.initLibrary();
    } catch (error) {
        this._libLoaded = false; // Allow retry on failure
        this.error = 'Library load failed';
    }
}
```

**Detection hint:** `loadScript` or `loadStyle` inside `renderedCallback` without a boolean guard flag.

---

## Anti-Pattern 4: Not loading CSS with loadStyle for library stylesheets

**What the LLM generates:**

```javascript
// Loads the JS but forgets the companion CSS
await loadScript(this, CHARTJS + '/chart.min.js');
// Chart renders without proper styling
```

**Why it happens:** LLMs focus on the JavaScript. Many third-party libraries require companion CSS files that must be loaded separately via `loadStyle`.

**Correct pattern:**

```javascript
import { loadScript, loadStyle } from 'lightning/platformResourceLoader';
import CHARTJS from '@salesforce/resourceUrl/chartjs';

async renderedCallback() {
    if (this._loaded) return;
    this._loaded = true;
    await Promise.all([
        loadScript(this, CHARTJS + '/chart.min.js'),
        loadStyle(this, CHARTJS + '/chart.min.css')
    ]);
    this.initChart();
}
```

**Detection hint:** `loadScript` for a library known to have CSS (D3, Chart.js, FullCalendar) without a companion `loadStyle` call.

---

## Anti-Pattern 5: Using import for the resource URL but passing a string literal to loadScript

**What the LLM generates:**

```javascript
import MY_LIB from '@salesforce/resourceUrl/myLibrary';

// Then later in code:
await loadScript(this, '/resource/myLibrary/lib.js'); // Hardcoded path — ignores versioning
```

**Why it happens:** LLMs import the resource URL correctly but then hardcode the path string instead of using the imported reference. The scoped import is the only form the platform validates and the only one that carries a namespace prefix when the resource ships in a managed package (LWC Developer Guide, `create-resources` L3657).

**UNVERIFIED (2026-09-05):** an earlier revision of this file claimed the imported URL includes a cache-busting version hash. No Salesforce guide in the local corpus states the shape of the URL that `@salesforce/resourceUrl` resolves to, so that claim has been removed rather than restated.

**Correct pattern:**

```javascript
import MY_LIB from '@salesforce/resourceUrl/myLibrary';

await loadScript(this, MY_LIB + '/lib.js');
```

Always concatenate paths with the imported resource URL constant.

**Detection hint:** `loadScript` or `loadStyle` with a string path starting with `/resource/` instead of using the imported `@salesforce/resourceUrl` reference.

---

## Anti-Pattern 6: Uploading a massive unminified library as a static resource

**What the LLM generates:**

```
// Instructions: upload the full node_modules/d3 folder as a static resource
```

**Why it happens:** LLMs suggest uploading the entire library folder. "The maximum file size is 5 MB. An org can have up to 250 MB of static resources" (LWC Developer Guide, `create-resources` L3648; restated at `create-use-third-party-components` L4190). Both are deploy-time ceilings. Unminified or bundled libraries waste that budget and load slowly.

**Correct pattern:**

Upload only the minified production build:

```text
static-resources/
  d3/
    d3.min.js       (minified, ~90KB)
```

Do not upload source maps, test files, examples, or the full `node_modules` tree.

**Detection hint:** Static resource size exceeding 500 KB for a single library, or resource containing `node_modules`, `test`, or `.map` files.

---

## Anti-Pattern 7: Packaging the ESM build and calling loadScript on it

**What the LLM generates:**

```javascript
// Instructions: zip node_modules/chart.js/dist/chart.js and upload it
await loadScript(this, CHARTJS + '/chart.js');
new Chart(ctx, config); // ReferenceError: Chart is not defined
```

**Why it happens:** `chart.js`, `d3`, and most modern libraries ship an ES module as the
package default, and that is the file an LLM reaches for. The platform will not run it:
"`loadScript` doesn't currently support ECMAScript Modules (ESM). For example,
`<script type="module">` isn't supported. Import third-party web components using
pre-bundled JavaScript files with custom elements in a legacy format such as IIFE
(Immediately-Invoked Function Expression) or UMD (Universal Module Definition)"
(LWC Developer Guide, `create-use-third-party-components` L4207). Nothing fails at deploy
time — the resource uploads, the network request returns 200, and the global is simply
never defined.

**Correct pattern:**

```javascript
// Package the UMD/IIFE build the vendor also publishes
await loadScript(this, CHARTJS + '/dist/chart.umd.min.js');
```

**Detection hint:** a packaged file whose first lines contain `import ` or `export `, a
filename containing `.esm.` or `.mjs`, or a `loadScript` path pointing at a package's
`module`/`exports.import` entry point.
