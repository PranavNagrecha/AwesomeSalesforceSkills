# Well-Architected — Performance Budgets

## Relevant Pillars

- **Performance Efficiency** — budgets make performance a first-class
  deliverable, not a post-launch regression hunt.
- **Operational Excellence** — automated gates remove the "someone
  should have noticed" failure mode.

## Architectural Tradeoffs

- **Lab budget vs field budget:** lab catches regressions before
  release; field captures real user experience. Run both.
- **Per-component vs per-page:** per-component catches the offender
  but misses emergent compositions. Run both.
- **Hard gate vs warn-only:** hard gates enforce discipline but block
  delivery. Warn-only is ignored. Gate with a waiver process that has
  an expiry.

## Hygiene

- Budget manifest is version-controlled alongside components.
- CI gate runs on every PR touching LWC.
- CrUX field data reviewed monthly; budget tightened quarterly.
- Waiver list has expiry dates.

## Official Sources Used

- LWC Performance —
  https://developer.salesforce.com/docs/platform/lwc/guide/performance.html
- Performance Budgets (web.dev) —
  https://web.dev/performance-budgets-101/
- Lighthouse CI —
  https://github.com/GoogleChrome/lighthouse-ci
