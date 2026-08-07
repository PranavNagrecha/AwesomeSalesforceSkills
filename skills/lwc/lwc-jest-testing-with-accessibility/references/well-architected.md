# Well-Architected Notes — LWC Jest Testing with Accessibility

## Relevant Pillars

- **Operational Excellence** — Accessibility regressions are quiet — they don't crash the page, they just degrade for a subset of users. CI-enforceable a11y assertions in jest mean the team catches the regression at PR time, not after a customer complaint or a legal escalation. The Operational Excellence move is to make a11y a default test category, not a one-off audit.
- **User Experience** — A component that renders for sighted-mouse users but breaks for keyboard or screen-reader users is, by definition, a partially-broken UI. A11y assertions in unit tests are the cheapest mechanism to keep the contract consistent across that broader user surface.
- **Reliability** — Like any other contract, the a11y surface (roles, ARIA states, focus targets, keyboard handlers) drifts when nobody asserts on it. Reliability of the a11y contract over time is the same problem as reliability of a public API — assert it, run it in CI, fail the build on regression.

## Architectural Tradeoffs

| Tradeoff | Why it matters |
|---|---|
| Jest a11y assertions vs UTAM e2e a11y vs manual axe scan | Jest is fast (sub-second per test), runs in CI, catches structural regressions, but cannot evaluate computed style or screen-reader output. UTAM / Playwright + axe runs in a real browser, catches contrast and focus-indicator issues, but is slower and more brittle. Manual screen-reader QA catches semantic / announcement-order issues that automation misses. The right answer is layered: jest as the per-PR gate, UTAM / browser-axe for nightly or pre-release, manual for major UX changes. Replacing one layer with another loses coverage. |
| Explicit ARIA-attribute assertions vs `axe-core` blanket scan | Explicit assertions document *what the component is responsible for* — they read like a spec. `axe-core` catches a wider set of ARIA mistakes including ones the author didn't think to assert on, but its output is a list of violations, not a contract. Best practice is to do BOTH: explicit assertions for intentional contract, axe scan as a safety net. Don't use axe alone — when it eventually breaks (during a platform upgrade, jsdom change, or rule edit) the team has no documented contract to fall back on. |
| Snapshot tests of HTML vs targeted attribute assertions | Snapshots are tempting because they're easy to write. They are unstable for LWC because the engine emits version-dependent attributes. Targeted assertions (`getAttribute('aria-label')`) are stable across engine versions and read as documentation of intent. Avoid HTML snapshots for a11y. |
| `jest-axe` + jsdom vs real-browser axe | `jest-axe` runs in jsdom and skips layout-dependent rules. It catches ARIA structure mistakes and is fast. Real-browser axe (via Playwright, Cypress, or UTAM) runs in a real browser and catches contrast, focus indicator, layout-dependent issues. Both are valuable; treat the jest-axe result as a PR gate and the browser axe as a release gate. |
| Test the component vs test the SLDS base components it consumes | Don't re-test `lightning-input` accessibility — Salesforce owns that contract. Do test the *additional* a11y markup your template adds (custom roles, ARIA states, focus targets, keyboard handlers) and the *integration* points (does your label get propagated correctly to the consumed `lightning-input`?). The boundary is "what you wrote vs what you consumed." |

## Anti-Patterns

1. **Treating jest a11y assertions as a substitute for a real-browser audit.** jest catches structural regressions only. A green jest suite + a green real-browser axe scan + manual screen-reader spot-check is the minimum acceptable a11y signal for a customer-facing component. Skipping the latter two because jest is green is the most common trap.
2. **Snapshotting full `shadowRoot.innerHTML` as the a11y test.** Engine-emitted attributes change across releases and produce noise; the snapshot becomes a maintenance burden that the team eventually starts auto-updating without reading. Use targeted attribute assertions instead.
3. **Asserting on visual presentation in jest.** "The button looks orange" or "the focus ring is 2px" cannot be verified in jsdom — there's no rendering layer. Tests written this way produce false negatives or false positives. Move presentation assertions to a real-browser test.
4. **Skipping the second `await Promise.resolve()` and calling the test "stable."** Tests that pass 95% of the time and fail 5% are the worst case — they erode trust in the suite. Match awaits to async hops correctly the first time.
5. **Adding axe-core but not disabling `color-contrast`.** Produces hangs / false errors and convinces the team that "axe-core doesn't work in jest." It does work — just not for layout-dependent rules in jsdom.
6. **Testing the SLDS base components.** `lightning-input` already has Salesforce-maintained a11y. Re-testing it inside your component's jest suite is wasted code that breaks when SLDS updates. Test the integration (your label flows through correctly) and stop there.

## Official Sources Used

- LWC Developer Guide — Test Lightning Web Components — https://developer.salesforce.com/docs/platform/lwc/guide/unit-testing-using-jest.html
- LWC Developer Guide — Write Jest Tests for Lightning Web Components That Use the Wire Service — https://developer.salesforce.com/docs/platform/lwc/guide/unit-testing-using-jest-mock-wire.html
- LWC Component Library — Testing Introduction — https://developer.salesforce.com/docs/component-library/documentation/en/lwc/lwc.testing_introduction
- `@salesforce/sfdx-lwc-jest` repository (re-exports the wire-service-jest-util test adapters) — https://github.com/salesforce/sfdx-lwc-jest
- `wire-service-jest-util` — Migrating from version 2.x to 3.x (`register*TestWireAdapter` removed in favour of `create*TestWireAdapter`) — https://github.com/salesforce/wire-service-jest-util/blob/master/docs/migrating-from-version-2.x-to-3.x.md
- `wire-service-jest-util` README (`createTestWireAdapter`, `createLdsTestWireAdapter`, `createApexTestWireAdapter`; `emit` / `error` / `getLastConfig`) — https://github.com/salesforce/wire-service-jest-util
- LWC Developer Guide — Accessibility — https://developer.salesforce.com/docs/platform/lwc/guide/create-components-accessibility.html
- `axe-core` — accessibility rules engine — https://github.com/dequelabs/axe-core
- Salesforce Well-Architected — Operational Excellence — https://architect.salesforce.com/well-architected/operational-excellence
