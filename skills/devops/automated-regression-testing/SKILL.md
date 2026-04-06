---
name: automated-regression-testing
description: "Use when building or maintaining automated end-to-end regression tests for Salesforce UI (Lightning, LWC, Aura, Flows), selecting a testing framework (UTAM, Provar, Selenium), handling Shadow DOM challenges, or scheduling regression suites against pre-release orgs. Triggers: 'UTAM page objects', 'Shadow DOM testing', 'Salesforce E2E regression', 'Provar test automation', 'pre-release regression window'. NOT for Apex unit testing, LWC Jest component testing, manual UAT planning, or Agentforce conversational testing."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
  - Scalability
triggers:
  - "how do I automate end-to-end regression tests for Salesforce Lightning pages"
  - "Selenium cannot find elements inside Lightning Web Components Shadow DOM"
  - "what is UTAM and how do I use it for Salesforce UI testing"
  - "how do I run regression tests against a Salesforce pre-release sandbox"
  - "which framework should I use for automated Salesforce UI testing"
tags:
  - automated-regression-testing
  - utam
  - shadow-dom
  - e2e-testing
  - selenium
  - provar
  - pre-release-testing
  - ui-automation
inputs:
  - "testing framework preference or constraint (UTAM, Provar, Selenium, Playwright)"
  - "Salesforce edition and org type (sandbox, scratch, pre-release)"
  - "UI technology in use (LWC, Aura, Visualforce, hybrid)"
  - "CI/CD platform and pipeline configuration"
  - "critical business processes that require regression coverage"
outputs:
  - "regression test framework selection rationale and setup guide"
  - "page object model architecture for Salesforce Lightning pages"
  - "pre-release regression schedule aligned to Salesforce tri-annual release cycle"
  - "CI pipeline configuration for headless browser regression execution"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-05
---

# Automated Regression Testing

Use this skill when Salesforce UI changes, tri-annual platform releases, or deployment pipelines require automated browser-based regression testing rather than manual click-through verification. The objective is a sustainable regression suite that survives Shadow DOM encapsulation, adapts to Salesforce's three-release-per-year cadence, and integrates into CI/CD pipelines for continuous confidence.

---

## Before Starting

Gather this context before working on anything in this domain:

- **What UI technology dominates the org?** Lightning Web Components use native Shadow DOM, Aura uses a synthetic shadow polyfill (being deprecated), and Visualforce uses standard HTML. Each requires a fundamentally different locator strategy — mixing them in one suite without abstraction causes mass test breakage.
- **Is the team already invested in a commercial tool?** Provar and Copado Robotic Testing have Salesforce-native metadata awareness that eliminates Shadow DOM piercing work. Switching mid-project is expensive. If there is no existing investment, UTAM (open-source, Salesforce-maintained) is the recommended starting point.
- **What is the Salesforce release cadence impact?** Salesforce ships three major releases per year (Spring, Summer, Winter). Pre-release sandboxes open roughly 5 weeks before GA. Teams that do not run regression suites against pre-release orgs discover breakage in production.

---

## Core Concepts

### Shadow DOM and Locator Fragility

Lightning Web Components render inside native Shadow DOM boundaries. Standard Selenium `By.cssSelector` and `By.xpath` locators cannot penetrate these boundaries — `document.querySelector` returns `null` for elements inside a shadow root. This is the single most common reason Salesforce UI automation projects fail in their first month.

UTAM (UI Test Automation Model) solves this by generating page objects from JSON descriptors that understand shadow root traversal. Each page object knows how to pierce into the correct shadow host, locate the target element, and expose it as a typed method. Salesforce publishes 727+ pre-built UTAM page objects covering standard Lightning components.

For teams using raw Selenium or Playwright, the alternative is manual `shadowRoot` traversal chains like `driver.executeScript("return document.querySelector('one-app-nav-bar').shadowRoot.querySelector('...')")` — brittle, unreadable, and unmaintainable beyond a handful of tests.

### Page Object Model for Salesforce

The Page Object Model (POM) pattern is non-negotiable for Salesforce UI automation at scale. Without POM, locator changes from a single Salesforce release can require updating hundreds of test methods.

UTAM enforces POM by design: each page object is a JSON file that compiles to a Java or JavaScript class. The JSON declares the component's shadow root structure, child elements, and actions. Tests interact with page object methods (`loginPage.setUsername(...)`) rather than raw selectors.

For Provar, page objects are auto-generated from org metadata — Provar reads the object model, page layouts, and component tree to build its locator abstractions. This metadata-awareness is Provar's primary advantage over generic Selenium approaches.

### Tri-Annual Release Regression Windows

Salesforce's release cycle creates a predictable but firm regression testing cadence. The critical timeline is:

1. **Pre-release sandbox signup** opens roughly 5 weeks before GA (exact dates published on the Salesforce Trust site).
2. **Sandbox preview** window: the pre-release sandbox runs the upcoming version while production remains on the current version.
3. **GA cutover**: all instances upgrade on a rolling schedule over a release weekend.

Teams must run their full regression suite against a pre-release sandbox during the preview window. Tests that fail in preview but pass in the current sandbox indicate release-specific regressions that need workarounds before GA day.

---

## Common Patterns

### Mode 1: UTAM-Based Open-Source Regression Suite

**When to use:** Greenfield automation project, LWC-heavy org, team comfortable with Java or JavaScript, budget-constrained.

**How it works:**

1. Install UTAM compiler (`@salesforce/utam-compiler` for JS or Maven dependency for Java).
2. Add Salesforce's pre-built page object dependencies (`salesforce-pageobjects` NPM package or Maven artifact).
3. Write custom page objects for org-specific custom LWC components using UTAM JSON grammar.
4. Compose test methods that chain page object actions: navigate to record, fill fields, save, assert toast message.
5. Execute in CI with headless Chrome via WebDriverManager or Playwright launcher.

**Why not the alternative:** Raw Selenium without UTAM requires manual shadow root traversal that breaks every time Salesforce restructures component internals (which happens frequently during major releases).

### Mode 2: Provar or Commercial Metadata-Aware Suite

**When to use:** Enterprise teams with license budget, existing Provar investment, complex page layouts with many custom objects, Visualforce/Aura/LWC hybrid orgs.

**How it works:**

1. Connect Provar to the target Salesforce org via OAuth.
2. Provar reads org metadata (objects, fields, page layouts, record types) and auto-generates locator abstractions.
3. Record or author test cases using Provar's IDE — each step maps to a metadata-backed element rather than a CSS path.
4. Export test results as JUnit XML for CI integration.
5. Schedule nightly runs against pre-release sandboxes during preview windows.

**Why not the alternative:** Provar's metadata connection means locator updates for layout changes are often automatic. With UTAM, you maintain page objects manually for every custom component.

### Mode 3: Hybrid Playwright/UTAM for Modern Stacks

**When to use:** Teams already using Playwright for non-Salesforce testing, want a single framework, willing to write custom shadow DOM piercing utilities.

**How it works:**

1. Use Playwright's `page.evaluateHandle` to traverse shadow roots programmatically.
2. Wrap traversal in page object classes that mirror UTAM's abstraction.
3. Import UTAM's published locator data (available in JSON) as reference for standard component selectors.
4. Run with Playwright Test runner; benefit from auto-wait, tracing, and parallel execution.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| LWC-heavy org, no existing automation investment | UTAM + Selenium/WebDriver (Mode 1) | Salesforce-maintained, free, Shadow DOM solved natively |
| Enterprise with budget, hybrid Aura/LWC/VF org | Provar (Mode 2) | Metadata-aware locators handle mixed tech stack automatically |
| Team already using Playwright for other web apps | Playwright + custom shadow piercing (Mode 3) | Unified framework reduces maintenance, but requires custom shadow work |
| Only Apex/API testing needed, no UI | Do NOT use this skill | Use continuous-integration-testing skill instead |
| Testing Agentforce conversational agents | Do NOT use this skill | Use agent-testing-and-evaluation skill instead |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner building a regression suite:

1. **Inventory the UI technology stack** — Determine the ratio of LWC vs Aura vs Visualforce pages in the critical business processes. Shadow DOM strategy depends entirely on this.
2. **Select the framework** — Use the Decision Guidance table. If LWC-dominant and budget-constrained, default to UTAM. If hybrid or enterprise, evaluate Provar.
3. **Establish page object architecture** — Create a page object for each screen in the critical path. For UTAM, write JSON descriptors; for Provar, connect to the org and let metadata auto-generate. Never put raw locators in test methods.
4. **Build smoke-level regression suite first** — Automate the 5-10 most critical happy-path business processes (login, create record, edit, approval, report). Prove the framework works before scaling.
5. **Integrate into CI pipeline** — Configure headless browser execution (Chrome headless via WebDriverManager or Playwright). Produce JUnit XML output. Fail the build on regression failures.
6. **Schedule pre-release runs** — When Salesforce announces each release, sign up for a pre-release sandbox and schedule nightly regression runs during the preview window. Log failures and triage before GA.
7. **Maintain page objects per release** — After each Salesforce release, review failed tests, update page objects for changed component structures, and re-run until green.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Page objects exist for every screen in the critical regression path — no raw selectors in test methods
- [ ] Shadow DOM traversal is handled by the framework (UTAM page objects or Provar metadata), not by inline JavaScript hacks
- [ ] Tests produce JUnit XML or equivalent machine-readable output for CI consumption
- [ ] Headless browser execution is confirmed working (not just headed/local)
- [ ] Pre-release sandbox regression schedule is documented and calendar-blocked for the next Salesforce release
- [ ] Test data setup is independent — tests create their own data or use a seeded dataset, not production data copies
- [ ] Flaky test quarantine process exists — intermittent failures are isolated, not ignored or force-retried indefinitely

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Aura shadow polyfill deprecation** — Salesforce is migrating from synthetic shadow (Aura polyfill) to native Shadow DOM for LWC. Tests built against the polyfill's quirks (e.g., `document.querySelector` penetrating synthetic shadow) will break when the org flips to native shadow. Check the org's LWC Shadow DOM configuration in Setup and test against native mode proactively.
2. **Lightning Experience URL instability** — Salesforce Lightning URLs contain instance-specific hashes and state tokens that change between sessions. Hard-coding URLs like `/lightning/r/Account/001.../view` works, but navigation via `lightning/o/Account/list` may redirect through intermediate states. Use page object navigation methods (e.g., UTAM's `NavigationMixin` patterns) instead of `driver.get(url)`.
3. **Sandbox refresh resets test configuration** — Full sandbox refreshes overwrite Connected App configurations, named credentials, and custom settings used by automation frameworks to authenticate. Post-refresh runbooks must include re-provisioning automation service accounts and re-authorizing OAuth flows.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Regression test framework setup guide | Framework selection rationale, installation steps, and initial page object scaffold |
| Pre-release regression schedule | Calendar-aligned plan mapping Salesforce release dates to sandbox signup, test execution, and triage windows |
| CI pipeline regression stage | Pipeline configuration (YAML or equivalent) for headless browser test execution with JUnit output |
| Page object inventory | Catalog of page objects covering critical business process screens with maintenance ownership |

---

## Related Skills

- continuous-integration-testing — Use alongside when integrating Apex test execution into the same CI pipeline as UI regression tests
- destructive-changes-deployment — Use when deployment pipelines must handle metadata removal that can break UI regression targets
- org-shape-and-scratch-definition — Use when scratch orgs serve as regression test targets and need consistent shape configuration
