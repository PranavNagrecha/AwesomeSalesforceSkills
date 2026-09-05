# Gotchas - Static Resources In LWC

Grounding: `lwc_guide` = Lightning Web Components Developer Guide (page slug + extracted
line); `api_meta` = Metadata API Developer Guide; `object_reference` = Object Reference.

## `renderedCallback()` Replays Unless You Guard It

**What happens:** The same library loads and initializes multiple times.

**When it occurs:** `loadScript()` or `loadStyle()` is called from `renderedCallback()`
without a one-time flag. "A component is usually rendered many times during the lifespan
of an application. To use this hook to perform a one-time operation, use a boolean field
like `hasRendered`" (lwc_guide `create-lifecycle-hooks-rendered` L4136).

**How to avoid:** Use a clear initialization guard and reset it only if the load fails and
needs a retry. `check_static_resources_in_lwc.py` reports this as SR003.

---

## Zip Internal Paths Become Part Of The Contract

**What happens:** A library or asset suddenly fails to load after a resource refresh even
though the resource name stayed the same.

**When it occurs:** The internal zip structure changed, but consumer code still appends the
old file path. The platform gives you a base URL and nothing else — "To reference an item
in an archive, concatenate a string to create the path to the item" (lwc_guide
`create-resources` L3660). Nothing validates that the path exists until the browser 404s.

**How to avoid:** Treat the internal archive layout as part of the versioned interface,
record it in the resource's `<description>`, and version the resource name when the layout
moves.

---

## CDN Instructions Usually Mislead Salesforce Teams

**What happens:** A third-party library guide says to paste a script tag from a CDN, and it
never loads.

**When it occurs:** Teams follow generic web instructions. Uploading the library as a
static resource "is a Lightning Web Components content security policy requirement"
(lwc_guide `js-third-party-library` L2655), and adding the CDN to Trusted URLs does not
help: "Although you can call a third-party API through a trusted URL, you can't load
JavaScript resources from a third-party site, even from a trusted URL" (lwc_guide
`js-api-calls`).

**How to avoid:** Repackage the library into a static resource and load it through
`lightning/platformResourceLoader`.

---

## Trust Escalation Is A Review Trigger

**What happens:** A library only works after extra trust or global access allowances are
added.

**When it occurs:** The dependency expects direct control over browser globals or DOM
behavior. Under Lightning Locker the specific blockers are named: strict mode "disallows
variables from becoming global variables"; `eval()`, `new Function()`, and `<script>` tags
are CSP violations; and libraries "are blocked if they attempt to do broad scans of the
DOM instead of manipulating only the elements passed to their APIs" (lwc_guide
`js-third-party-guidance` L2770-L2777).

**How to avoid:** Document the trust requirement explicitly and challenge whether the
library is a good Salesforce UI fit before normalizing the exception.

---

## `loadScript` Does Not Load ES Modules

**What happens:** The file downloads with a 200, then nothing is defined — or the console
shows a bare `SyntaxError: Cannot use import statement outside a module`.

**When it occurs:** The vendor's default build is an ES module (`*.esm.js`, `"type":
"module"`) and that is the file that got zipped. "`loadScript` doesn't currently support
ECMAScript Modules (ESM). For example, `<script type="module">` isn't supported"
(lwc_guide `create-use-third-party-components` L4207).

**How to avoid:** Package the IIFE or UMD build the vendor also ships (`chart.umd.min.js`,
`d3.min.js`), and check the file's first lines for `import`/`export` before you zip it.

---

## `cacheControl: Public` Publishes The Bytes To The Internet

**What happens:** A resource intended for internal users is served to unauthenticated
traffic once it has been cached.

**When it occurs:** `Public` is chosen for load-time reasons without reading what it means:
"Public specifies that the static resource is accessible after caching to all internet
traffic, including unauthenticated users" (object_reference L273930-L273932; identical
wording at lwc_guide `create-resources` L3651). `Private` is the constrained one —
"accessible to all authenticated users … stored on the Salesforce server in a user's
individual cache for the duration of the session" (object_reference L273927-L273929).

**How to avoid:** Decide per resource by content sensitivity, not by page speed. Vendor
library builds and public brand assets are fine as `Public`; seeded data, price lists, and
unreleased artwork are not. Verify what actually deployed:
`SELECT Name, CacheControl FROM StaticResource`.

---

## CSS Loaded With `loadStyle` Is Not Scoped To Your Component

**What happens:** A library stylesheet restyles unrelated components elsewhere on the page,
or the component's own rules stop winning.

**When it occurs:** In synthetic shadow — the default in Lightning Experience and Experience
Builder — "all the styles injected at the page level (for example, using `loadStyle` from
`lightning/platformResourceLoader`) leak into components" (lwc_guide `get-started` L127).
The guide states it as the intended mechanism: `loadStyle` "apply[s] the styles globally in
synthetic shadow … similar to SLDS in Lightning Experience as SLDS isn't scoped to your
component" (lwc_guide `create-dom-synthetic` L3165). Specificity order is component CSS
file, then `@import`ed CSS, then `loadStyle` CSS last (L3169-L3171).

**How to avoid:** Load only the library's own stylesheet this way, prefix or namespace its
selectors if the vendor ships broad ones, and keep component styling in the bundle's `.css`
file where shadow scoping still applies.

---

## Component CSS Cannot Reach Inside `lwc:dom="manual"`

**What happens:** The chart or editor renders but ignores every rule you wrote for it.

**When it occurs:** The library inserted its nodes itself. "If a call to `appendChild()`
manipulates the DOM, styling isn't applied to the appended element" (lwc_guide
`js-third-party-library` L2668), and in light DOM, "scoped styles don't apply to content
that's manually injected into the template inside of `lwc:dom="manual"`" (lwc_guide
`create-light-dom` L3483).

**How to avoid:** Style the container (which you do own) and let the library's own
stylesheet — loaded via `loadStyle` from the same resource — style its interior. Do not
try to reach in from the component stylesheet.

---

## A Packaged Resource Needs Its Namespace Prefix

**What happens:** The import compiles in the developer's org and fails in the org that has
the managed package installed, or vice versa.

**When it occurs:** The resource ships inside a managed package. The import path takes a
namespace segment — "namespace — If the static resource is in a managed package, this value
is the namespace of the managed package" (lwc_guide `create-resources` L3657), so it is
`@salesforce/resourceUrl/ns__myResource`, not `@salesforce/resourceUrl/myResource`.

**How to avoid:** Decide up front whether the resource is packaged. If the component and
the resource ship in the same package the local name is right; if the component consumes
someone else's package, the prefix is mandatory and belongs in a documented constant.

---

## The Size Ceilings Fail The Deploy, Not The Page

**What happens:** A deploy that worked yesterday is rejected after someone adds source maps
or a second vendor build to the archive.

**When it occurs:** "The maximum file size is 5 MB. An org can have up to 250 MB of static
resources" (lwc_guide `create-resources` L3648; restated at `create-use-third-party-components`
L4190). The org-wide ceiling is the one nobody watches, because every team spends against
it independently.

**How to avoid:** Zip only the production build — no `node_modules`, `test/`, `examples/`,
or `.map` files. Track headroom with `SELECT SUM(BodyLength) FROM StaticResource` before a
release that adds resources.

---

## Static Resources Are Org-Local, Not A CDN

**What happens:** Someone proposes hosting a shared logo or a JS bundle in Salesforce and
linking to it from the marketing site.

**When it occurs:** `Public` caching makes the URL reachable, so it looks like it works.
But the Metadata API is explicit: "Static resources can be used only within your Salesforce
org, so you can't host content here for other apps or websites" (api_meta L130903-L130905).

**How to avoid:** Use a real asset host for cross-property assets. Keep static resources
for what Salesforce UI itself loads.

---

## Loading In `connectedCallback()` Beats The DOM To The Punch

**What happens:** The library initializes, reaches for its container, and gets `null`.

**When it occurs:** `loadScript` was moved to `connectedCallback()` to "load earlier". The
guide picks the other hook deliberately: "invoke `loadStyle` and `loadScript` in
`renderedCallback()` on the first render. Using `renderedCallback()` ensures that the page
loads and renders the container before the graph is created" (lwc_guide
`js-third-party-library` L2680).

**How to avoid:** Keep the load in `renderedCallback()` behind the one-time guard. If the
library genuinely needs no DOM, it still costs nothing to load it there. SR002 in the
checker flags loader calls outside `renderedCallback()`.
