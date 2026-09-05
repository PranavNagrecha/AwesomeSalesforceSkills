# Gotchas — LWC Offline And Mobile

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.
Cites of the form `lwc_guide <page-slug> L<n>` refer to the crawled Lightning Web Components
Developer Guide; the page URL is
`https://developer.salesforce.com/docs/platform/lwc/guide/<page-slug>.html`.

Briefcase priming, sync conflicts, and picklist/record-type gaps in the offline cache are covered
by `lwc/lwc-mobile-offline-and-briefcase` and are not repeated here.

---

## Gotcha 1: The Only Mobile-Offline-Capable GraphQL Module Is The One The Guide Marks Deprecated

**What happens:** A developer follows the guide's migration advice, swaps
`lightning/uiGraphQLApi` for `lightning/graphql`, and the component stops returning data on a
device with no connection — while working perfectly in every desktop test.

**When it occurs:** Any "modernisation" pass over a component that was built for Mobile Offline.
The comparison page states that `lightning/uiGraphQLApi` supports Mobile Offline use cases and
`lightning/graphql` doesn't (`lwc_guide reference-graphql-intro L13437`, restated on the v2 pages
at `reference-lightning-graphql-module L13458` and `reference-graphql-wire L13470`). The
`refreshGraphQL` page simultaneously declares `lightning/uiGraphQLApi` deprecated and tells you to
use `lightning/graphql` instead (`lwc_guide reference-refreshgraphql L13651`). Both statements are
current, and they point in opposite directions.

**How to avoid:** Let the offline requirement decide, not the recency of the module, and write the
reason into the import's comment block so the next reader does not undo it. v1 also lacks optional
fields, dynamic query construction, and mutations (`lwc_guide reference-graphql L13634–13638`), so
if the component needs those *and* offline, that is a design conflict to escalate, not a code
problem to solve.

---

## Gotcha 2: `lightning-datatable` Is Not Supported On Mobile Devices At All

**What happens:** A table that renders correctly in Chrome's device-mode emulator behaves
unpredictably — or not at all — in the Salesforce mobile app on a real phone.

**When it occurs:** Whenever a desktop component is reused on a mobile-visible page. The guide's
statement is categorical: `lightning-datatable` and `lightning-tree-grid` aren't supported on mobile
devices (`lwc_guide data-table-vs-tree-grid L5600`). This is a support boundary, not a styling
complaint, so "it looked fine in Device Mode" is not evidence — Device Mode simulates screen size,
orientation, location, CPU and network constraints (`lwc_guide debug-mobile L12214–12219`), not the
mobile app's component runtime.

**How to avoid:** On any page that can render at the `Small` form factor, replace the table with an
iterated card or list layout. If both surfaces need the same data, branch on
`@salesforce/client/formFactor` rather than shipping one table to both.

---

## Gotcha 3: Pull-To-Refresh Silently Does Nothing For Custom Components

**What happens:** Users report that the component "never updates". They are pulling down on the
page, seeing the platform's refresh animation, and getting stale content back.

**When it occurs:** In the Salesforce mobile app, on any custom Lightning web component. The guide
states plainly that pull to refresh doesn't work for custom Lightning web components in the
Salesforce mobile app (`lwc_guide use-config-for-app-builder-tips L9910`). Nothing errors; the
gesture is simply not wired to your component's data.

**How to avoid:** Ship an explicit refresh affordance — a button that calls `refreshGraphQL(result)`
(v1) or the `refresh` method on the emitted data (v2). Do not substitute a timer: the guide directs
you to refresh once after a mutating operation, or to give the user an explicit refresh action,
rather than polling with `setTimeout`/`setInterval`
(`lwc_guide reference-refreshgraphql L13657`).

---

## Gotcha 4: An Offline Error Has A Different Body Shape Than The Errors You Tested Against

**What happens:** The error reducer that works for every FLS and bad-Id case throws or renders
`[object Object]` the first time the device loses connection.

**When it occurs:** Whenever the component goes offline with a record that isn't cached. LDS returns
an error if the record isn't in the cache and the server is offline (`lwc_guide data-error L6511`).
But the *shape* differs by origin: UI API read operations return `error.body` as an array of
objects, while network errors — including an offline error — return `error.body` as an object
(`lwc_guide data-error L6568–6571`). A reducer written with `.map()` over an assumed array meets an
object and fails.

**How to avoid:** Normalise before reducing — `Array.isArray(err) ? err : [err]` — and unit-test the
object-shaped branch, not just the array one. Do not rely on `refresh()` to rescue the state either:
offline behavior for `refresh()` is undefined and the guide says not to rely on any specific
behavior when the client is offline (`lwc_guide reference-state-managers-use L14157`).

---

## Gotcha 5: The OS Scanner Interface Stays On Screen Until You Call `dismiss()`

**What happens:** The user scans a code, your handler runs, and the camera view sits on top of the
app. The user's only exit is to force-quit.

**When it occurs:** Every time `scan()` settles without a paired `dismiss()`. The guide is explicit
that the mobile OS scanner interface remains displayed after a successful scan *or* an error, and
that `dismiss()` is what closes it and returns the user to your component
(`lwc_guide reference-lightning-barcodescanner-scan L17366`). It also directs you to handle final
cleanup in a `finally` clause (`same page L17367`) — because the error path strands the UI just as
readily as the success path.

**How to avoid:** Always `.finally(() => scanner.dismiss())`. Treat a `scan()` call with no
`dismiss()` anywhere in the chain as a defect, not a style preference.

---

## Gotcha 6: A User Tapping Cancel Arrives In `.catch()`, Not `.then()`

**What happens:** The component shows a red "Scan failed" banner every time a user changes their
mind and taps Cancel.

**When it occurs:** On the normal exit path. When the user clicks the Cancel button during a scan,
the promise is rejected with a `BarcodeScannerFailure.code` value of `userDismissedScanner`
(`lwc_guide reference-lightning-barcodescanner-scan L17365`), and the guide names this the normal
method of terminating a scanning session, suggesting you treat it differently from, for example,
permissions errors (`lwc_guide reference-lightning-barcodescanner-data-types L17319`).

**How to avoid:** Branch on the failure code before rendering anything as an error. Note that the
guide prints the code as `USER_DISMISSED_SCANNER` in the failure-code table
(`reference-lightning-barcodescanner-data-types L17313`) and as `userDismissedScanner` in the prose
on the same page and on the `scan()` page — compare case-insensitively rather than betting on one
spelling. The other codes worth branching on are `USER_DENIED_PERMISSION`,
`USER_DISABLED_PERMISSION`, `INVALID_BARCODE_TYPE_REQUESTED`, `SERVICE_NOT_ENABLED`, and
`UNKNOWN_REASON` (`same page L17313–17318`).

---

## Gotcha 7: `isAvailable()` Is Neither Required Nor Sufficient

**What happens:** A reviewer approves a component because it has an `isAvailable()` guard, and the
component still throws on a device where the capability exists but the operation fails.

**When it occurs:** On permission denial, an unsupported barcode type, or a disabled service — all
of which are documented failure codes returned from the *call*, not from the availability check. The
guide states that `isAvailable()` is useful to avoid entering complicated logic when a scan is
guaranteed to fail, but that it isn't required to check before attempting a scan, and that either
way your code should handle errors such as attempting a scan on an unsupported device
(`lwc_guide reference-lightning-barcodescanner-isavailable L17337`).

**How to avoid:** Treat the guard and the error handler as two separate obligations. The guard
decides what UI to render; the `catch` decides what happens when a rendered affordance fails anyway.
A component with one and not the other is half-built.

---

## Gotcha 8: The Form Factor Your JavaScript Sees And The One The Config File Accepts Are Different Sets

**What happens:** A tablet user gets the desktop layout while the component's `-meta.xml` claims it
supports the device — or a component that was correct on phones renders nothing on tablets.

**When it occurs:** As soon as tablets enter the picture. `@salesforce/client/formFactor` returns
one of `Large` (desktop), `Medium` (tablet), or `Small` (phone)
(`lwc_guide create-client-form-factor L3960–3962`). The `<supportedFormFactor type="…">` attribute
accepts only `Large` and `Small` (`lwc_guide targets-lightning-record-action L19311–19313`). There
is no `Medium` in the configuration file, so a tablet is admitted by the `Large` declaration while
the JavaScript reports `Medium` — and any `FORM_FACTOR === 'Small'` branch skips it.

**How to avoid:** Write the tablet case explicitly as its own getter rather than folding it into
"mobile" or "desktop". And decide the form-factor set before the component goes live: once a
component is in use on a Lightning page you can only *increase* the supported form factors, not
decrease them (`lwc_guide use-config-form-factors L9806`, repeated at
`use-config-for-app-builder-tips L9909`).

---

## Gotcha 9: An LWC Quick Action Never Appears In The Salesforce Mobile App

**What happens:** A quick action built as an LWC works on desktop and is simply absent from the
record page in the mobile app. No error, no placeholder.

**When it occurs:** Any `lightning__RecordAction` component on a mobile-visible record page. Using a
Lightning web component as a quick action isn't supported in the Salesforce mobile app
(`lwc_guide use-config-for-quick-actions L10561`), and the configuration reference records the
consequence: `Small` isn't a supported `supportedFormFactor` value for `lightning__RecordAction`
because LWC quick actions don't appear in the Salesforce mobile app
(`lwc_guide targets-lightning-record-action L19313`). The Field Service org is the exception —
those actions appear only in the Field Service mobile app, not in Lightning Experience on mobile or
desktop (`lwc_guide use-quick-actions L10526`).

**How to avoid:** If the interaction must exist on a phone, put the component on the record page
itself with a `lightning__RecordPage` target, or make it reachable as a custom tab via
`lightning__Tab` — the target the guide describes as enabling a custom tab in Lightning Experience
or the Salesforce mobile app (`lwc_guide reference-configuration-tags L18746`).

---

## Gotcha 10: Mixing Apex And LDS In One Component Produces Inconsistent Data — Offline And Online

**What happens:** The card shows a value fetched by Apex while a sibling GraphQL query on the same
record returns `null` or a different value for the same field.

**When it occurs:** In any component that reads part of its data imperatively from Apex and part
through a wire adapter. Apex doesn't share a data cache or data store with LDS, so data fetched
using Apex can be inconsistent with data fetched using LDS wire adapters in both online and offline
conditions (`lwc_guide data-guidelines L5364`). Offline simply makes the divergence permanent
instead of transient, because the Apex half has no cache to fall back on at all.

**How to avoid:** Pick one data path per record. The guide's own advice is to use the GraphQL wire
adapter consistently for both the fetch and the search when you would otherwise reach for SOQL
(`same page L5365`). Reserve Apex for what UI API genuinely cannot do — unsupported objects,
transactional multi-record writes, and criteria-based list loads (`lwc_guide data-guidelines
L5357–5360`).

---

## Gotcha 11: You Cannot Preview A Single Component On A Simulator

**What happens:** A developer runs `sf lightning dev component --device-type ios`, gets an error or
a browser window, and concludes mobile preview is broken.

**When it occurs:** Any time the mobile check is scoped to one component. Live Preview supports
previewing only Lightning *apps* in a mobile environment — specifically an iOS simulator or an
Android emulator (`lwc_guide get-started-test-components L467`). The `--device-type` flag, which
accepts `desktop`, `ios`, or `android`, belongs to `sf lightning dev app`
(`same page L459`, flag table at `L464`). The single-component preview is a browser experience.

**How to avoid:** Add the component to a Lightning app page first, then preview the app:
`sf lightning dev app --device-type ios`. Reserve `sf lightning dev component` for layout iteration
in the browser, and remember that even a real-device preview is not a substitute for testing
mobile-specific features on hardware (`lwc_guide debug-mobile L12213`).

---

## Gotcha 12: `scan()` And The Legacy `beginCapture()` Return Different Shapes

**What happens:** Code adapted from an older sample does `result.value` on what is now an array, and
gets `undefined`.

**When it occurs:** During the migration the guide itself asks for. `scan()` returns a promise that
resolves as an **array** of `Barcode` objects
(`lwc_guide reference-lightning-barcodescanner-scan L17345`), while `beginCapture()` resolves as a
single `Barcode` (`lwc_guide reference-lightning-barcodescanner-begincapture L17397`). The legacy
`beginCapture()`, `resumeCapture()`, and `endCapture()` are still available but will be retired in a
future release; the recommendation is the modern `scan()` and `dismiss()` pair
(`same page L17394`).

**How to avoid:** When you migrate, change the result handling and the teardown call in the same
edit — `endCapture()` becomes `dismiss()`, and `result.value` becomes `results.map(r => r.value)`.
Also switch the option values to the enumerated constants: `barcodeTypes` values are enumerated on
the instance as `BarcodeScanner.barcodeTypes`, for example
`[myScanner.barcodeTypes.EAN_13, myScanner.barcodeTypes.QR]`
(`lwc_guide reference-lightning-barcodescanner-data-types L17286`).
