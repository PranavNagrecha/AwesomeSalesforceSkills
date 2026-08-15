---
name: lwc-performance-budgets
description: "Set and enforce performance budgets for Lightning Web Components: bundle-size limits per component, LCP/INP field targets, wire-adapter count caps, and CI-gate configuration using Lighthouse or webpagetest. Trigger keywords: lwc performance budget, bundle size limit, lcp budget, lighthouse ci, lwc size gate. NOT for runtime optimization techniques, Lightning page tuning, or general LCP causes — use lwc/lwc-performance."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Operational Excellence
triggers:
  - lwc performance budget
  - bundle size limit
  - lcp budget
  - lighthouse ci gate
  - inp budget lwc
  - "performance budget is slow"
tags:
  - lwc
  - performance
  - performance-budget
  - lighthouse-ci
  - ci-gate
inputs:
  - List of critical components and their pages
  - Current field-data LCP/INP (CrUX or monitoring)
  - CI pipeline that can fail on thresholds
outputs:
  - Budget manifest (per-component bundle cap + per-page field-data targets)
  - CI-gate wiring (Lighthouse CI config or equivalent)
  - Regression alert playbook
dependencies:
  - lwc/lwc-performance
  - devops/pipeline-secrets-management
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-08-14
---

# LWC Performance Budgets

## Budget Enforcement Triggers

- Shipping any LWC rendered above-the-fold on a high-traffic record page
  or Experience Cloud route.
- A component has a history of bloating over releases.
- CrUX field data shows LCP or INP regressing post-release and you want
  a preventive gate.

## When NOT To Use

- Internal-only admin utility components (still valuable but
  lower-priority).
- Components built into a managed package where you cannot change CI.

## Budget What You Can Actually Measure

Half the work here is deleting rows that look right and can never fail. Two
metrics that appear in almost every generated budget do not exist in a Salesforce
context:

- **Minified bundle size.** The platform compiles and serves LWC. `sf project
  deploy` sends source; there is no local build emitting a minified artefact to
  weigh. Budget **source bytes** plus **transitive import bytes** instead — both
  are stdlib-checkable in CI and stable across releases.
- **CrUX field data for an internal org.** The Chrome UX Report covers public
  origins. An authenticated Lightning org is not in it. Public Experience Cloud
  sites are the exception where CrUX genuinely applies.

## The Five Budget Types

1. **Source + transitive bytes.** Per bundle, including everything reachable
   through `from 'c/moduleName'`. Measuring only the leaf file misses the 2 KB
   component that imports 60 KB of shared utilities — the common case. Exclude
   `@salesforce/*` and `lightning/*`; they are platform-provided.
2. **Round trips.** `@wire` count is a cheap static check (≤ 3 on a top-level
   component). Calls-per-user-action needs a Jest assertion with mocked Apex and
   advanced timers — that is what catches a removed debounce; a decorator count
   never will.
3. **Rendered volume.** The published datatable guidance is **1,000 rows and
   5 columns**, fewer than 20 columns past 250 rows, and 50 rows per request.
   Make those manifest rows.
4. **Client-side collection size.** Lightning Web Security mediates
   cross-namespace access with proxies; the cost is *"negligible when there are a
   few thousand proxies"* and *"observable"* in the tens of thousands. Set a
   ceiling and enforce it as a guard that throws rather than degrades.
5. **Core Web Vitals** — LCP, INP, CLS — as a **field alert on public sites** and
   a **lab pre-release check** elsewhere. Label every number `lab_` or `field_`
   and never compare them; they are different quantities.

## Recommended Workflow

1. Inventory components and the pages hosting them, and record whether each page
   is one you fully control (LWR site, custom app page) or platform-composed. On
   platform-composed pages, budget the **component-attributable delta**, not the
   page total — most of that timeline is not yours.
2. **Measure the current distribution first.** Set initial defaults near the
   observed 75th percentile so the outliers are the failures. A default that
   forty components violate on day one gets the gate disabled, and disabled gates
   do not come back.
3. Write the manifest with an owning team on every entry, an explicit `gate`
   (`ci-blocking` / `monitor-alert` / `manual-pre-release` / `warn-only`), and a
   stated measurement method per row. A row with no gate is documentation — say
   so.
4. Wire CI to report **every** violation before exiting non-zero. Fail-fast turns
   one bad PR into five build cycles and pushes people to run the check in a
   local loop instead of reading the manifest.
5. Add expiring waivers with an id, reason, approver, and expiry — **plus a check
   that fails the build on an expired waiver.** Without it "expires" is
   decorative and every waiver is a permanent, unapproved budget increase.
6. Write the regression playbook in this order: *is it us* (compare a page with
   none of your components), then *did data volume grow*, then *did code change*.
   The first two are cheap and are usually where the answer is.
7. Put `reviewed` and `next_review` in the manifest with a check that warns once
   the date passes, and a completeness check warning on any bundle with no entry.
   Ratchet quarterly toward the observed 90th percentile.

## Official Sources Used

- Improve Performance (LWC Developer Guide) —
  https://developer.salesforce.com/docs/platform/lwc/guide/perf-intro.html
- Best Practices for Development with Lightning Web Components —
  https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
- Improve Datatable Performance —
  https://developer.salesforce.com/docs/platform/lwc/guide/data-table-performance.html
- How LWS Architecture Affects Component Performance —
  https://developer.salesforce.com/docs/platform/lightning-components-security/guide/lws-performance.html
- Core Web Vitals —
  https://web.dev/vitals/
- Lighthouse CI —
  https://github.com/GoogleChrome/lighthouse-ci
