# Gotchas — LWC Chart and Visualization

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: `renderedCallback` fires on every render, so the chart is built many times

**What happens:** The library instance is created in `renderedCallback` without a
guard. Per the LWC docs, "A component is usually rendered many times during the
lifespan of an application," and "Updating the state of your component in
`renderedCallback()` can cause an infinite loop." Each render stacks a new Chart
instance on the same canvas: tooltips fire twice, then four times; animations
flicker; the detached instances retain their data arrays and the tab's memory
climbs until the browser stalls.

**When it occurs:** Any wire adapter refresh, any tracked property change, any
parent re-render. It is invisible on a static demo and obvious after ten minutes
of real use.

**How to avoid:** Guard with a boolean field — the docs prescribe exactly this:
"To use this hook to perform a one-time operation, use a boolean field like
`hasRendered` to track whether `renderedCallback()` has been executed." Create
the chart once behind the flag, then update data through the library's own
mutate-and-redraw API rather than reconstructing. Call the library's teardown
(`chart.destroy()` for Chart.js) in `disconnectedCallback`; without it the
instance survives navigation away from the page.

---

## Gotcha 2: The library must be a static resource, and static resources cap at 5 MB

**What happens:** Loading a chart library from a CDN fails. LWC requires
third-party libraries to be uploaded as static resources — the docs describe this
as "a Lightning Web Components content security policy requirement." Then the
upload itself fails, because "The maximum file size is 5 MB" for a single static
resource and "An org can have up to 250 MB of static resources."

**When it occurs:** Full builds of Plotly and D3 approach or exceed the
single-resource ceiling once source maps and locale data are included. Teams then
zip several libraries into one resource and hit the same wall from the other
side.

**How to avoid:** Ship a purpose-built bundle, not the vendor's kitchen-sink
build. Chart.js and D3 both support importing only the modules you use, which
typically cuts the payload by an order of magnitude; strip source maps and
unused locales from the production bundle. Track the org's 250 MB total as a
shared budget — chart libraries compete with every image, font and legacy
Visualforce asset in the org.

---

## Gotcha 3: `lwc:dom="manual"` is needed for SVG libraries and pointless for canvas ones

**What happens:** The rule gets applied by superstition rather than mechanism, in
both directions. D3 *appends* elements into the `<svg>` node, so it needs the
directive — the docs are explicit: "Add the `lwc:dom="manual"` directive to an
empty native HTML element. The owner of the component calls `appendChild()` on
that element to manually insert the DOM." Chart.js draws into a canvas 2D
context and inserts no child nodes, so the directive changes nothing there.

**When it occurs:** Migrating from a Chart.js prototype to a D3 build, where the
directive was never needed and is now silently missing, and elements appear in
the DOM but do not behave.

**How to avoid:** Apply `lwc:dom="manual"` wherever a library calls
`appendChild()` on an element the template owns, and expect the styling
consequence the docs name: "If a call to `appendChild()` manipulates the DOM,
styling isn't applied to the appended element." Scoped CSS in the component's
`.css` file will not reach D3-appended nodes. Style them from JavaScript
(`.attr('fill', ...)`) or from a stylesheet loaded via `loadStyle`, and do not
spend an afternoon wondering why the CSS class is ignored.

---

## Gotcha 4: `document.querySelector` returns nothing inside a component

**What happens:** Every chart tutorial on the open web starts with
`document.getElementById('myChart')`. In LWC that returns `null`. The docs are
direct: "Don't use the `window` or `document` global properties to query for DOM
elements." The canvas lives inside the component's shadow root and the global
document cannot see it.

**When it occurs:** Every time chart code is adapted from a non-Salesforce
example, which is essentially every time.

**How to avoid:** "To locate shadow DOM nodes, use `querySelector()` or
`querySelectorAll()` on `this.template`." Two further traps in the same area:
"Elements not rendered to the DOM aren't returned in the `querySelector`
result," so a canvas behind a falsy `if:true` is genuinely absent, not merely
un-found; and for light DOM components the method is `this.querySelector()`,
which "searches through elements outside of the immediate template, such as light
DOM children" — narrow the selector accordingly.

---

## Gotcha 5: A "Public" cache-control static resource is readable by anyone on the internet

**What happens:** Static resources carry a cache-control setting. Per the docs,
"Private: The static resource is stored in cache only for the current user's
session"; "Public: After it's cached, the resource is accessible to all Internet
traffic, including unauthenticated users." Teams flip it to Public to fix a
caching problem and, in doing so, publish whatever is in the resource.

**When it occurs:** Two shapes. A licensed commercial charting library becomes
downloadable by anyone, which is a licence violation. Or a team bundles a JSON
seed dataset into the resource "so the chart renders instantly", and that dataset
is now public.

**How to avoid:** Keep chart libraries Private unless there is a stated reason
otherwise, and never put data in a static resource — data comes from Apex or a
wire adapter, where sharing and field-level security apply. The related
operational trap is the opposite one: browsers cache these aggressively, so a
library upgrade under the same resource name can serve stale code for a long
time. Version the resource name (`chartjs_v4_4_0`) so the URL changes when the
bytes do.

---

## Gotcha 6: Rendering is rarely the bottleneck — the data pipeline is

**What happens:** A dashboard is slow, so the team swaps canvas for SVG, tunes
animation duration, and debounces resize. The actual cost is a wire adapter
returning 300,000 rows that Apex serialised, the browser parsed, and the chart
then reduced to 52 weekly bars. Apex can return at most 50,000 records per
SOQL transaction in the first place, so the pipeline is also fragile.

**When it occurs:** Time-series and trend charts, where the natural query is
row-level and the natural display is bucketed.

**How to avoid:** Aggregate on the server. A SOQL `GROUP BY` returning 52
`AggregateResult` rows is the same picture at a fraction of the payload, and it
sidesteps the 50,000-row limit rather than approaching it. Measure the transport
before touching the renderer: if the chart draws in 40 ms and the wire takes 4 s,
renderer choice is not the problem. And consider whether the answer is a chart at
all — `lightning-datatable` reads better than a 40-category bar chart and needs
no static resource.

---

## Gotcha 7: A chart with no text alternative is unusable, and the fix is not `alt`

**What happens:** Canvas is a bitmap; a screen reader gets nothing from it. SVG
is inspectable but produces an unlabelled soup of `<path>` elements. Colour-only
series encoding fails WCAG SC 1.4.1 Use of Color, which requires that colour is
"not used as the only visual means of conveying information."

**When it occurs:** Every chart, unless accessibility was scoped in. It surfaces
in a procurement accessibility review, long after the build.

**How to avoid:** Render the same data as a visually-hidden `<table>` adjacent to
the chart and point at it with `aria-describedby` — the table is the accessible
representation, and it costs almost nothing because the data is already in the
component. Encode series with shape, dash pattern or direct labels in addition to
colour, and give the canvas element a meaningful `role` and label rather than
leaving it as an anonymous graphic. Interactivity that exists only on hover needs
a keyboard equivalent, for the same reason drag-and-drop does.
