# Well-Architected Notes — LWC Chart and Visualization

## Relevant Pillars

- **Performance** — Chart work has two costs that get conflated: the transport
  cost of getting data to the browser, and the render cost of drawing it. They
  differ by orders of magnitude and the transport almost always dominates. A
  server-side `GROUP BY` that returns 52 rows instead of 300,000 changes the page
  more than any renderer choice will, and it keeps the query clear of the
  50,000-record retrieval limit rather than approaching it. Measure both before
  optimising either.

- **Reliability** — Every chart component carries a lifecycle contract that is
  easy to get wrong and produces no error when you do: load the library once,
  construct the instance once, update in place, destroy on disconnect. Skipping
  any step yields a component that works in a demo and degrades under real use —
  duplicated instances, retained memory, doubled event handlers. The library is
  also an external dependency pinned into a static resource, so "the chart broke"
  can mean an org-level upgrade nobody associated with this component.

- **Operational Excellence** — Charting rules are repetitive and easy to
  re-litigate: `this.template.querySelector` not `document`, the boolean guard in
  `renderedCallback`, `lwc:dom="manual"` only for libraries that append DOM, the
  hidden data table for accessibility. Centralising them in one reviewed pattern
  is cheaper than rediscovering each in every component.

## Architectural Tradeoffs

**Canvas vs SVG.** Canvas (Chart.js, Plotly) is a single bitmap: it scales to far
more marks, and it is opaque to the accessibility tree, to CSS, and to per-element
event handlers. SVG (D3) gives you a real DOM you can style, inspect and attach
listeners to, and it degrades past a few thousand elements. Choose by mark count
first, then by how much per-element interaction the design needs. Whichever you
pick, the accessible representation is a separate artifact — canvas because it
has no structure, SVG because a pile of `<path>` elements has no meaning.

**Chart library vs no chart.** A chart is a design commitment: a static resource
to maintain, an upgrade path, an accessibility obligation, and a rendering
lifecycle. For under a dozen categories, `lightning-datatable` frequently
communicates better, needs none of that, and is accessible by default. Ask what
decision the chart supports before choosing which library draws it.

**Library size vs capability.** The single-resource ceiling is 5 MB and the org
total is 250 MB, shared with every other asset in the org. A tree-shaken bundle
of the modules you actually use is typically an order of magnitude smaller than a
vendor's full build and costs one extra build step. Taking the full build is
borrowing from an org-wide budget to save an afternoon.

**Where formatting logic lives.** Formatting on the server keeps one definition
and makes the payload display-ready; formatting in the component keeps the Apex
reusable and lets the same data feed a chart, a table and an export. Prefer
returning typed values and formatting at the edge — but decide it once per
project rather than per component.

## Anti-Patterns

1. **Constructing the chart in an unguarded `renderedCallback`.** Instances stack
   invisibly; the symptom is memory growth and multiplied event handlers, not an
   error.
2. **Loading the library from a CDN.** LWC's CSP requires a static resource; the
   failure looks like a load-order race and gets "fixed" with timeouts.
3. **Shipping data inside a static resource.** It bypasses sharing and
   field-level security entirely, and a Public cache-control setting makes it
   readable by unauthenticated internet traffic.
4. **Treating accessibility as a later pass.** Colour-only series encoding fails
   WCAG SC 1.4.1, and there is no retrofit for a canvas that never had a text
   alternative — the hidden table is nearly free at build time and expensive to
   add after.

## Official Sources Used

- LWC Developer Guide — Use Third-Party JavaScript Libraries — https://developer.salesforce.com/docs/platform/lwc/guide/js-third-party-library.html — confirms the `loadScript`/`loadStyle` imports from `lightning/platformResourceLoader` and `@salesforce/resourceUrl/<name>`, that uploading libraries as static resources is "a Lightning Web Components content security policy requirement", that `renderedCallback()` is the load site with an initialised-flag guard, that `lwc:dom="manual"` is added to "any HTML element that you want to manipulate with JavaScript", that you "Add the `lwc:dom=\"manual\"` directive to an empty native HTML element. The owner of the component calls `appendChild()` on that element to manually insert the DOM.", that "If a call to `appendChild()` manipulates the DOM, styling isn't applied to the appended element", and that under LWS "most third-party libraries work as expected without changes. However, some libraries require changes to work with LWS." (verified 2026-08-14)
- LWC Developer Guide — Static Resources — https://developer.salesforce.com/docs/platform/lwc/guide/create-resources.html — confirms "The maximum file size is 5 MB", "An org can have up to 250 MB of static resources", and the Private vs Public cache-control semantics including that a Public resource is "accessible to all Internet traffic, including unauthenticated users" (verified 2026-08-14)
- LWC Developer Guide — `renderedCallback()` — https://developer.salesforce.com/docs/platform/lwc/guide/create-lifecycle-hooks-rendered.html — confirms "A component is usually rendered many times during the lifespan of an application", the infinite-loop warning, and the prescribed `hasRendered` boolean-guard pattern (verified 2026-08-14)
- LWC Developer Guide — Access Elements the Component Owns — https://developer.salesforce.com/docs/platform/lwc/guide/create-components-dom-work.html — confirms "Don't use the `window` or `document` global properties to query for DOM elements", that shadow nodes are found via `querySelector()` on `this.template`, that "Elements not rendered to the DOM aren't returned in the `querySelector` result", and the light-DOM `this.querySelector()` caveat (verified 2026-08-14)
- Apex Developer Guide — Execution Governors and Limits — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm — confirms the 50,000-record total retrieved by SOQL queries per transaction, and the 100 (sync) / 200 (async) query counts (verified 2026-08-14)
- WCAG 2.1 — Understanding SC 1.4.1 Use of Color — https://www.w3.org/WAI/WCAG21/Understanding/use-of-color.html — confirms that colour must not be the only visual means of conveying information, which is the requirement series-by-colour charts fail (verified 2026-08-14)
