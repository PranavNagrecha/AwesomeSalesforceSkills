# Gotchas — Automated Regression Testing

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Native vs Synthetic Shadow DOM Mode Changes Test Behavior

**What happens:** Salesforce orgs have a setting controlling whether LWC uses native Shadow DOM or synthetic shadow (the legacy Aura polyfill). When an org is on synthetic shadow, `document.querySelector` can traverse into LWC component internals — tests appear to work fine. When the org switches to native shadow (which Salesforce is actively pushing), those same selectors return `null` and every test breaks simultaneously.

**When it occurs:** This typically hits teams during a Salesforce release that flips the default, during a sandbox refresh that inherits a different setting, or when an admin changes "Use Native Shadow" in Setup. The trap is that tests pass for months in synthetic mode, creating false confidence.

**How to avoid:** Always develop and run tests with native Shadow DOM enabled, even if the org currently uses synthetic. In scratch org definitions, set `"enableNativeShadowDom": true`. For UTAM-based tests, this is transparent because UTAM handles traversal correctly in both modes. For raw Selenium tests, use `element.getShadowRoot()` (Selenium 4+) or UTAM's traversal rather than `document.querySelector` chains.

---

## Gotcha 2: Lightning Locker Service Blocks Cross-Namespace DOM Access

**What happens:** Tests that attempt to read or interact with elements inside a managed package component's Shadow DOM fail with access violations. Lightning Locker Service (and its successor, Lightning Web Security) enforces namespace isolation — your test framework's JavaScript cannot reach into another namespace's shadow root even when running as an admin user in a test context.

**When it occurs:** This bites teams that install managed packages (e.g., Salesforce CPQ, nCino, Vlocity/OmniStudio) and try to automate flows that pass through managed package UI components. The test works fine for custom components in the `c` namespace but throws errors the moment it touches a managed component.

**How to avoid:** For managed package components, automate at the container level — interact with the managed component's public API or its outermost host element, not its internals. Use UTAM page objects published by the ISV if available. If no page objects exist, treat the managed component as a black box: assert on its visible output (text content, toast messages, record state via API) rather than its internal DOM structure.

---

## Gotcha 3: Salesforce Session Cookies and Concurrent Test Execution

**What happens:** Running multiple regression test browsers in parallel against the same Salesforce user account causes session invalidation. Salesforce enforces per-user session limits (configurable in Session Settings, default varies by edition). When browser #2 authenticates, browser #1's session may be invalidated, causing mid-test failures that look like random flakiness.

**When it occurs:** Teams scaling up their regression suite to run in parallel (common in CI) hit this when all browser instances log in as the same service account. The symptom is tests that pass individually but fail randomly when run concurrently — a classic flaky test pattern that wastes days of debugging.

**How to avoid:** Provision dedicated automation user accounts — one per parallel execution slot. For a pipeline running 4 parallel browsers, create 4 automation users (`regression-runner-1@org.sandbox` through `regression-runner-4@org.sandbox`). Assign them identical permission sets. Alternatively, use the Session Settings to increase the maximum number of simultaneous sessions per user, though this has security implications that require approval.

---

## Gotcha 4: Sandbox URL Instance Changes After Refresh

**What happens:** After a sandbox refresh, the sandbox instance may change (e.g., from `cs45` to `cs78`). Hard-coded base URLs in test configuration files, CI environment variables, and page object navigation methods break silently — the browser loads but lands on a login error page or a different org entirely.

**When it occurs:** Every full or partial sandbox refresh. The instance assignment is not guaranteed to be stable. Teams that set up their automation once and never revisit the URL configuration discover this after a refresh when the entire suite produces 100% failures.

**How to avoid:** Never hard-code sandbox instance URLs. Use `sf org display --target-org <alias> --json` to dynamically resolve the current instance URL at test execution time. Store the org alias in CI configuration, not the URL. The pre-release regression pipeline example in examples.md demonstrates this pattern.

---

## Gotcha 5: UTAM Page Object Version Mismatches with Salesforce Releases

**What happens:** Salesforce publishes updated UTAM page objects with each major release. If the test project pins an old version of `salesforce-pageobjects`, the pre-built page objects may not match the actual DOM structure of the current org. Tests fail with element-not-found errors even though the page visually renders correctly.

**When it occurs:** After a Salesforce release upgrades the org but the project's `package.json` or `pom.xml` still references the previous release's UTAM artifacts. The mismatch is especially common during the pre-release window when the sandbox is on version N+1 but the UTAM artifacts for N+1 have not yet been published.

**How to avoid:** Pin UTAM page object versions to match the target org's Salesforce release. After each Salesforce release, update the dependency version. During pre-release windows, check the Salesforce UTAM GitHub repository for pre-release branches or snapshot builds. If updated page objects are not available yet, build custom overrides for the specific components that changed.
