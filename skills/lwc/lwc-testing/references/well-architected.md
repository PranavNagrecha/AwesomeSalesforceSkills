# Well-Architected Notes - Lwc Testing

## Relevant Pillars

### Reliability

Reliable components need reliable tests. Jest coverage for happy paths, error states, and interaction contracts catches regressions before they escape to users.

### Operational Excellence

A healthy Jest setup reduces change risk, accelerates refactoring, and makes LWC delivery repeatable in CI instead of dependent on manual browser checks.

### User Experience

Unit tests that verify loading, error, empty, and success states directly protect the user experience because those states are where regressions usually surface first.

## Architectural Tradeoffs

- **Fast isolated tests vs full environment realism:** Jest is intentionally isolated and fast. It should prove component behavior, while other test layers handle broader integration.
- **Behavioral assertions vs snapshots:** Snapshots are cheap to add, but they do not cover user flows well without targeted assertions.
- **More mocks vs more confidence:** Mocking adds setup cost, but it allows meaningful coverage of failure paths that are hard to reproduce manually.

## Anti-Patterns

1. **Render-only tests with no behavior assertions** - the component can still break for users while the suite remains green.
2. **Flaky async guesses** - arbitrary `setTimeout` use produces brittle tests and hides real rerender boundaries.
3. **No project-level Jest governance** - missing scripts, dependencies, or cleanup patterns make test adoption inconsistent across components.

## Official Sources Used

Line citations are to the crawled Lightning Web Components Developer Guide, page
`https://developer.salesforce.com/docs/platform/lwc/guide/<slug>.html`.

- LWC Developer Guide — **Write Jest Tests** (`unit-testing-using-jest-create-tests`, L12325–L12506) — that Jest tests are local-only and never saved to Salesforce (L12325); the `__tests__` folder and the `.forceignore` glob (L12328–L12330); the shared-jsdom `afterEach` cleanup loop (L12336–L12341, L12362–L12363); `element.shadowRoot` as a test-only API (L12379); the `lightning/navigation` mock and the sample `moduleNameMapper` / `setupFiles` / `testTimeout` config (L12382, L12430–L12458); the `@salesforce/apex` `moduleNameMapper` route and `mockResolvedValue` example (L12461–L12490); and the "set before `appendChild` renders synchronously" rule (L12494–L12506).
- LWC Developer Guide — **Write Jest Tests for Wire Service** (`unit-testing-using-wire-utility`, L12518–L12562) — the three adapter kinds, generic / LDS / Apex (L12521–L12524); import the same adapter as the component and `emit()` after the component is connected to the DOM (L12533, L12548); resolve a promise before asserting the rerender (L12549, L12556); and that registering the adapter under test was the Spring '21-and-earlier shape and "isn't recommended" (L12562) — the basis for the checker's legacy-API WARN.
- LWC Developer Guide — **Jest Test Patterns and Mock Dependencies** (`unit-testing-using-jest-patterns`, L12590–L12655) — `Promise.resolve()` for property-change rerenders (L12590–L12604); `Object.assign` before `appendChild` (L12606–L12613); the `lightning-stubs` base-component mocks, that they fire no events but accept `dispatchEvent()`, and that base-component properties aren't always reflected as attributes (L12622, L12626–L12627); `moduleNameMapper` stub overrides (L12637, L12646–L12647); merging `setupFilesAfterEnv` (L12648); and the `jest.mock(..., { virtual: true })` label mock (L12650–L12655).
- LWC Developer Guide — **Install Jest** and **Run Jest Tests** (`unit-testing-using-jest-installation` L12244–L12253, `unit-testing-using-jest-run-tests` L12262–L12272) — that `sfdx-lwc-jest` works in DX projects only; that `sf force lightning lwc test setup` creates the config, installs the package and adds the `package.json` scripts; `sf force lightning lwc test run`; the `--watch` parameter; and `moduleNameMapper` as the fix for slow cross-folder resolution.
- LWC Developer Guide — **Configure Event Propagation** (`events-propagation`, L5113–L5126) — `Event.bubbles` and `Event.composed` both default to `false`, and event retargeting at the shadow boundary; this is what makes a `document.body` listener the wrong place to assert a component's custom event.
- LWC Developer Guide — **Light DOM** (`create-light-dom`, L3266–L3274) — `LightningElement.prototype.template` returns `null` in light DOM, `this.template.querySelector` becomes `this.querySelector`, and events are not retargeted so `event.target` differs; the basis for the light-DOM gotcha.
- LWC Developer Guide — **Wire Apex Methods** (`apex-wire-method`, L7104–L7107) — `data` and `error` are hardcoded property names that must be used verbatim, and an `undefined` parameter means the adapter is not invoked; this is what the missing-`recordId` negative test asserts.
- LWC Developer Guide — **Anti-Patterns for Component Styling** (`create-components-css-antipatterns`, L1915–L1920) — LWC's scoping attributes and classes are internal implementation details, obfuscated as `lwc-<hashstring>` from API version 59.0, and must not be relied on "in your code or tests"; the reason the example bundle selects on `data-id`.
- LWC Developer Guide — **Salesforce Releases and LWC API Versions** / **Versioning Considerations** (`create-version-alignment` L855–L863, `create-version-considerations` L872–L873) — Spring '25 maps to LWC API version 63.0; versioning began at 58.0 and lower values are treated as 58.0; a future version fails on save. Used for the `.js-meta.xml` `apiVersion` and its UNVERIFIED note.
- LWC Developer Guide — **End-to-End Tests** (`testing-dom-api`, L12571–L12578) — HTML/CSS/DOM in Lightning Experience are not a stable API; use Jest for unit tests and WebDriver only for end-to-end. The boundary between this skill and `devops/automated-regression-testing`.
- `wire-service-jest-util` — Migrating from version 2.x to 3.x (`register*TestWireAdapter` removed; use `create*TestWireAdapter`; verified 2026-08-01) - https://github.com/salesforce/wire-service-jest-util/blob/master/docs/migrating-from-version-2.x-to-3.x.md — **UNVERIFIED (2026-09-05) against the Developer Guide: neither `register*TestWireAdapter` nor `create*TestWireAdapter` is named anywhere in the crawled guide.** The guide describes the generation change in prose only (L12562) and its examples call `emit()` on the directly imported adapter. The specific function names come from this npm README.
- `wire-service-jest-util` README (`createTestWireAdapter` / `createLdsTestWireAdapter` / `createApexTestWireAdapter`; `emit` / `error` / `getLastConfig`) - https://github.com/salesforce/wire-service-jest-util — **UNVERIFIED (2026-09-05): the crawled guide documents only `emit()`.** `error()`, `emitError`, and `getLastConfig()` are not in it, so the wire-error test in `references/code-examples.md` carries a marker beside the `.error(...)` call.
- `sfdx-lwc-jest` README (re-exports the wire-service-jest-util adapters, so no extra dependency is needed) - https://github.com/salesforce/sfdx-lwc-jest — **UNVERIFIED (2026-09-05): not stated in the guide.** The guide says only that you *may* import adapters from `@salesforce/wire-service-jest-util` but that `sfdx-lwc-jest` is recommended (L12525). Command-line flags beyond `--watch` and `--debug` — `--coverage`, `--skipApiVersionCheck` — are likewise README-only.
