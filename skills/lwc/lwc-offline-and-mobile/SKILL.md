---
name: lwc-offline-and-mobile
description: "Use when designing or reviewing Lightning Web Components for the Salesforce mobile app, mobile device capabilities, or offline-aware behavior. Triggers: 'lightning/mobileCapabilities', 'mobile lwc', 'offline lwc', 'barcode scanner lwc', 'isAvailable', 'supportedFormFactors', 'formFactor Small', 'pull to refresh not working', 'lightning/uiGraphQLApi vs lightning/graphql'. NOT for Mobile SDK or fully native app architecture unless the decision is whether LWC i — use apex/fsl-mobile-app-extensions. NOT for Briefcase Builder priming rules or offline sync conflict design — use lwc/lwc-mobile-offline-and-briefcase."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Reliability
  - Performance
triggers:
  - "how do i use lwc in the salesforce mobile app"
  - "lightning mobilecapabilities isavailable"
  - "offline behavior for lwc"
  - "barcode scanner or device api in lwc"
  - "should this be mobile sdk instead of lwc"
  - "mobile lwc isn't working"
  - "gate a barcode scanner so it degrades on desktop"
  - "scan barcodes from a lightning web component"
  - "why does the camera view stay on screen after scanning"
  - "pull to refresh does nothing in my custom lwc"
  - "choose between lightning/graphql and lightning/uiGraphQLApi for offline"
  - "detect phone vs tablet vs desktop in a lightning web component"
  - "set supportedFormFactors in the js-meta.xml"
  - "preview a lightning web component on an ios simulator"
  - "handle an offline error from a wire adapter"
  - "why is my datatable broken in the salesforce mobile app"
  - "test a mobile lwc with jest when mobileCapabilities is unavailable"
  - "scan a barcode from a lightning web component"
tags:
  - mobile-lwc
  - offline
  - mobilecapabilities
  - salesforce-mobile-app
  - device-apis
inputs:
  - "target container such as salesforce mobile app, desktop, or experience cloud"
  - "which device capabilities or offline behaviors are required"
  - "whether the component depends on apex, ui api, or local-first interaction"
outputs:
  - "mobile/offline implementation recommendation"
  - "review findings for capability checks and stale-state handling"
  - "decision on lwc in mobile app vs a different mobile architecture"
  - "a deployable bundle with js-meta.xml targets, form factors, and a jest test"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

Use this skill when a component is expected to behave well on phones or tablets and the team needs to be explicit about what the Salesforce mobile app can and cannot provide. Mobile capability APIs, offline expectations, and container-specific behavior all need to be designed intentionally instead of assumed from desktop LWC behavior.

## Before Starting

- Will the component run in the Salesforce mobile app, a mobile browser, Experience Cloud, or multiple containers?
- Does it need device hardware access such as camera, barcode scanning, or location, or is the main concern responsive rendering and limited connectivity?
- What must happen when the device is offline, regains connectivity, or resumes after the app was backgrounded?

## Questions to Ask Before Configuring

Ask these before writing the first import. Each one closes a failure the mobile app reports as
"the component doesn't work" rather than as an error, and each traces to a numbered entry in
`references/gotchas.md`.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Does this have to render with **no** connection, or only survive a flaky one?" | The answer picks the GraphQL module, and the two options point in opposite directions — only `lightning/uiGraphQLApi` (v1) supports Mobile Offline, and it is the module the guide marks deprecated (Gotcha 1) | A written module decision with the offline requirement attached, so nobody "modernises" it later |
| "Which exact form factors — phone, tablet, desktop — and is the answer final?" | `<supportedFormFactor>` accepts only `Large` and `Small`, while the JS API also returns `Medium` for tablets, and once the component is live you can only add form factors, never remove one (Gotcha 8) | The `targetConfigs` block, and an explicit tablet decision instead of a `=== 'Small'` boolean |
| "If the device API is unavailable, what does the user see instead?" | Mobile capability APIs resolve only inside a supported mobile app on a mobile device; every other container needs a rendered alternative, not a dead button (Gotcha 7) | The fallback UI — manual entry, a disabled state, or a hidden section — named before the code is written |
| "What should happen when the user taps Cancel mid-scan?" | Cancel arrives in the rejection handler with a `userDismissedScanner` code, so the naive implementation shows a red error for the most common exit path (Gotcha 6) | A branch on the failure code, and the list of the other codes worth distinguishing |
| "How does the user ask for fresh data?" | Pull-to-refresh doesn't work for custom Lightning web components in the Salesforce mobile app, so the gesture users reach for first is a no-op (Gotcha 3) | An explicit refresh control in the design, and a decision not to poll |
| "Is any of this data coming from Apex?" | Apex shares no data cache with LDS, so an Apex half and a wire half disagree online and diverge permanently offline (Gotcha 10) | One data path per record, or a documented reason UI API genuinely cannot serve it |
| "Who tests this, on what, before it ships?" | Device Mode simulates screen size and network, not the mobile app runtime; and Live Preview can only put a Lightning *app*, never a single component, on a simulator (Gotcha 11) | A named test route: Jest for the capability-absent path, `sf lightning dev app --device-type ios` for the container, a real device for hardware |

What a proper configuration adds over just doing it: the component degrades to something usable in every container instead of throwing, offline reads come back from a cache instead of an unhandled rejection, the refresh affordance exists because the platform gesture does not, and the form-factor set is a decision someone made rather than a default that can never be narrowed again.

---

## Core Concepts

### Mobile Capabilities Exist Only In Supported Mobile App Contexts

Mobile capability APIs are available only when a Lightning web component runs in a supported mobile
app on a mobile device (`lwc_guide reference-lightning-mobilecapabilities L17179`). Every capability
in `lightning/mobileCapabilities` follows the same three-part shape: a factory (`getBarcodeScanner()`,
`getLocationService()`, `getBiometricsService()`), an `isAvailable()` predicate, and the operation
itself. The guide is careful that `isAvailable()` is a rendering hint, not a safety net — it says the
check isn't required and that your code should handle errors either way
(`lwc_guide reference-lightning-barcodescanner-isavailable L17337`).

### Offline Is A Module Decision Before It Is A Design Decision

An LWC is not offline-capable because it renders in the mobile app. The data module decides. Of the
two GraphQL wire modules, only `lightning/uiGraphQLApi` supports Mobile Offline use cases
(`lwc_guide reference-graphql-intro L13437`) — and Apex shares no cache with Lightning Data Service
at all (`lwc_guide data-guidelines L5364`), so an Apex-fed component has nothing to render when the
network is gone. Populating the offline cache in the first place is Briefcase Builder's job, not the
component's: see `lwc/lwc-mobile-offline-and-briefcase`.

### The Container Removes Affordances You Did Not Know You Had

Three things that work on desktop simply are not there on a phone: pull-to-refresh does not reach
custom components (`lwc_guide use-config-for-app-builder-tips L9910`), LWC quick actions do not
appear in the Salesforce mobile app (`lwc_guide use-config-for-quick-actions L10561`), and
`lightning-datatable` and `lightning-tree-grid` are not supported on mobile devices
(`lwc_guide data-table-vs-tree-grid L5600`). Each of these fails silently — nothing throws.

### Form Factor Is Two Different Vocabularies

`@salesforce/client/formFactor` returns `Large`, `Medium`, or `Small`
(`lwc_guide create-client-form-factor L3960–3962`). The configuration file's
`<supportedFormFactor type="…">` accepts only `Large` and `Small`
(`lwc_guide targets-lightning-record-action L19311–19313`). Tablets live in the gap.

### Container Choice Matters

Some requirements fit well inside the Salesforce mobile app with LWC. Others require deeper mobile platform control or a different channel strategy. Choosing between LWC in the mobile app and a more specialized mobile architecture should happen before the implementation grows around the wrong container.

## Common Patterns

### Capability-Gated Device Access

**When to use:** The component needs camera, location, barcode, or another mobile capability.

**How it works:** Call the factory once in `connectedCallback`, store the `isAvailable()` result, render the capability path only when it is true, and still wrap the operation in `.catch()` and `.finally()`. Reference implementation: `references/code-examples.md` §2.

**Why not the alternative:** Assuming every device or container supports the API causes broken buttons and dead-end UX — and a guard with no error handler still throws on a permission denial.

### Offline-Tolerant Read And Resume Pattern

**When to use:** Users may lose connectivity while viewing or collecting information.

**How it works:** Hold the last successfully provisioned snapshot, render it behind a staleness banner when the wire errors, keep draft input in component state with a visible "unsaved" marker, and expose an explicit refresh control.

**Why not the alternative:** Desktop-style refresh assumptions produce confusing behavior after reconnect or app resume, and the platform's own refresh gesture never reaches the component.

### Mobile-First Simplification

**When to use:** The same business task must work on desktop and mobile, but the mobile surface has less space and less tolerance for heavy UI.

**How it works:** Reduce fields, favor clear primary actions, and replace unsupported components — notably the datatable — with iterated card layouts on the `Small` branch.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Need supported device APIs inside Salesforce mobile | LWC plus mobile capability modules | Best fit when the supported app container is enough |
| Must work in desktop and mobile | Capability-gated LWC with graceful fallback | Keep one component contract while respecting container differences |
| Must render with no connection | `lightning/uiGraphQLApi` (v1) plus a Briefcase priming rule | v2 does not support Mobile Offline; a component cannot prime its own records |
| Needs v2-only features (optional fields, dynamic queries, mutations) *and* offline | Escalate as a requirements conflict | No module satisfies both today |
| Interaction must be a quick action on a phone | Put it on the record page instead, or use `lightning__Tab` | LWC quick actions do not appear in the Salesforce mobile app |
| Needs deeper native platform control than the mobile app provides | Reconsider architecture, possibly Mobile SDK or another mobile approach | LWC in Salesforce mobile has deliberate boundaries |

## Recommended Workflow

1. **Answer the seven questions above** and write down two decisions before any code: the GraphQL module (v1 if offline is real), and the exact `supportedFormFactor` set — the second one is effectively irreversible once the component is on a Lightning page.
2. **Build the bundle** from `references/code-examples.md` §2, starting from `templates/lwc/component-skeleton/` and `templates/lwc/patterns/graphqlWirePattern.js`. Every capability call gets the factory / `isAvailable()` / `.catch()` / `.finally(dismiss)` shape; every wire handler holds a last-good snapshot.
3. **Write the `-meta.xml` deliberately**, not by copying the skeleton's three targets. §2 explains why `lightning__HomePage` and `lightning__RecordAction` are omitted and why `lightning__Tab` is present.
4. **Write the Jest test before deploying** — `references/code-examples.md` §3. Mock `lightning/mobileCapabilities` through `moduleNameMapper` so the default is *capability absent*, and assert the desktop fallback, the offline error shape, and that `dismiss()` runs on the cancel path.
5. **Run the checker**: `python3 skills/lwc/lwc-offline-and-mobile/scripts/check_lwc_offline_and_mobile.py --manifest-dir force-app/main/default`. It flags an ungated capability call, a scan with no teardown, the legacy scanning API, Apex or `lightning/graphql` in a bundle documented as offline, browser storage, `document.querySelector`, viewport sniffing, an invalid `supportedFormFactor` type, a datatable on a `Small`-capable bundle, `isExposed` false with targets, `recordId` with no record-page target, and a missing `__tests__`.
6. **Deploy and verify on a device** using `references/code-examples.md` §5–§6 — including the two checks that only fail on hardware: the airplane-mode staleness banner, and the scanner interface actually closing after Cancel.
7. **Fill in `templates/lwc-offline-and-mobile-template.md`** with the decisions you made, and record any deviation — especially a component that needs both offline and v2-only GraphQL features.

---

## Review Checklist

- [ ] Every mobile capability call has a factory, an `isAvailable()` guard, a `.catch()`, and a `.finally()` teardown.
- [ ] The user-cancel failure code is branched on and is not rendered as an error.
- [ ] Unsupported containers render a real alternative, not a hidden or dead control.
- [ ] The GraphQL module matches the offline requirement, with the reason recorded in the file.
- [ ] The component renders a last-known-good snapshot plus a staleness signal when the wire errors.
- [ ] An explicit refresh control exists; no polling timer does its job.
- [ ] `supportedFormFactors` is declared, uses only `Large`/`Small`, and the tablet case is handled in JS.
- [ ] No `lightning-datatable` or `lightning-tree-grid` on a `Small`-capable bundle.
- [ ] Jest covers the capability-absent path and the object-shaped offline error.
- [ ] The team verified that LWC in the Salesforce mobile app is the right container choice.

## Salesforce-Specific Gotchas

Twelve grounded platform behaviours live in `references/gotchas.md`. The four that break builds most often:

1. **The Mobile-Offline module is the deprecated one** — `lightning/uiGraphQLApi`, not `lightning/graphql`. Gotcha 1.
2. **The scanner UI does not close itself** — `scan()` leaves the OS camera view up until `dismiss()`. Gotcha 5.
3. **Pull-to-refresh is a no-op for custom components** — ship a button. Gotcha 3.
4. **Offline errors arrive with a different body shape** than the FLS and bad-Id errors you tested. Gotcha 4.

## Output Artifacts

| Artifact | Description |
|---|---|
| Component bundle | `.js`, `.html`, `.js-meta.xml` with deliberate targets and form factors |
| Jest suite | Capability-absent, offline-error, and cancel-path coverage |
| Mobile/offline fit assessment | Decision on whether the LWC and container fit the mobile requirement |
| Capability review | Findings on device API checks, unsupported environments, and fallback behavior |
| Offline behavior plan | Guidance on stale-state handling, reconnect, and mobile-first interaction design |

## Reference Files

| File | Read it when |
|---|---|
| `references/code-examples.md` | You are building it — the full bundle, `-meta.xml`, `package.xml`, Jest test with the wire and capability mocks, deploy order, and device verification |
| `references/gotchas.md` | Something behaves strangely on a phone and you need the grounded platform behaviour behind it |
| `references/llm-anti-patterns.md` | Reviewing mobile LWC code an assistant generated, before it reaches a PR |
| `references/examples.md` | You want worked scenarios with the reasoning attached |
| `references/well-architected.md` | Justifying the trade-offs, or you need the official source behind a claim |
| `templates/lwc-offline-and-mobile-template.md` | Recording the container, capability, and offline decisions for this specific component |

---

## Related Skills

- `lwc/lwc-mobile-offline-and-briefcase` — use when the problem is Briefcase priming rules, sync conflicts, or what the offline cache does and does not hold.
- `lwc/lwc-graphql-wire` — use when the GraphQL query itself is the problem: cursors, `{value, displayValue}`, fragments, relationship depth.
- `lwc/wire-service-patterns` — use when the core issue is data provisioning and refresh rather than mobile behavior itself.
- `lwc/lwc-error-boundaries` — use when a mobile failure should be contained to one card instead of blanking the page.
- `lwc/lifecycle-hooks` — use when app resume, cleanup, or render timing issues dominate the bug.
- `lwc/lwc-testing` — use when the Jest setup itself, not the mobile behaviour, is what is failing.
- `lwc/headless-experience-cloud` — use when the requirement may fit a different channel rather than the Salesforce mobile app.
