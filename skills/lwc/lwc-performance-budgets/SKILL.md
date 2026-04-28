---
name: lwc-performance-budgets
description: "Set and enforce performance budgets for Lightning Web Components: bundle-size limits per component, LCP/INP field targets, wire-adapter count caps, and CI-gate configuration using Lighthouse or webpagetest. Trigger keywords: lwc performance budget, bundle size limit, lcp budget, lighthouse ci, lwc size gate. Does NOT cover runtime optimization techniques, Lightning page tuning, or general LCP causes (see lwc-performance)."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
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

## The Four Budget Types

1. **Bundle size.** Raw JS + template size per component, pre- and
   post-minification, with a hard cap. Typical starting cap: 50 KB
   minified per top-level LWC, 10 KB per shared helper module.
2. **Wire adapter count.** Each wire adapter is a network round-trip
   and a reactive dependency. Target: ≤ 3 wires per top-level
   component, ≤ 1 imperative Apex round-trip per user action.
3. **LCP (Largest Contentful Paint).** p75 field-data budget per page
   template. Typical: ≤ 2.5 s on record pages, ≤ 1.8 s on
   Experience Cloud landing pages.
4. **INP (Interaction to Next Paint).** p75 budget per page. Typical:
   ≤ 200 ms.

## Recommended Workflow

1. Inventory the components shipping and their hosting pages.
2. Capture baseline: bundle size from build output; field data from
   CrUX for LCP/INP.
3. Write the budget manifest (see template). One row per component
   and one row per hosting page.
4. Wire CI: block the deploy when a component bundle exceeds cap or
   the wire-adapter count increases.
5. Wire a monitoring alert: page LCP/INP p75 crosses the budget for N
   consecutive days.
6. Document the escalation path: who owns raising a cap, who signs off,
   how often budgets are reviewed.
7. Review the manifest quarterly. Budgets should tighten over time as
   the team gets used to them.

## Official Sources Used

- LWC Performance Best Practices —
  https://developer.salesforce.com/docs/platform/lwc/guide/performance.html
- Core Web Vitals —
  https://web.dev/vitals/
- Lighthouse CI —
  https://github.com/GoogleChrome/lighthouse-ci
