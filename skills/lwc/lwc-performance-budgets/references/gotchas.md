# Gotchas — Performance Budgets

## 1. Synthetic vs Field Data

Lighthouse lab runs are synthetic. CrUX is field data from real users.
A budget based only on lab values misses real-world variability. Use
both: Lighthouse for CI gate, CrUX for monitoring.

## 2. Salesforce Record Page Overhead Is Not Yours

A component's LCP is measured on the page it lives on, which is mostly
platform-controlled. You can only influence the part of the bundle you
ship. Scope the budget to the component-attributable portion when
possible.

## 3. Minified Size ≠ Runtime Cost

A 40 KB minified bundle with 200 KB of worker data loaded at runtime is
still a heavy component. Budget for runtime memory and network payload
separately, not just JS bytes.

## 4. Wire Adapters Cache But Still Cost

`@wire` uses the Lightning Data Service cache. First render still
incurs a round-trip; the cache hit is a subsequent render. A 4-wire
component pays 4 round-trips on first paint.

## 5. Lighthouse CI In A Pipeline Needs A Real Render Context

Lighthouse running against `localhost` of a stripped-down harness is
not your Salesforce page. Use a preview sandbox with representative
data, or a tool that renders in the actual org context.

## 6. Budgets Tighten Silently Over Time

If nobody reviews the budget and it stays at the install value, teams
treat it as ceiling-not-target. Mark a quarterly review and reduce the
cap toward the 90th-percentile observed value.

## 7. Failing The Gate Without A Waiver Process Blocks Releases

CI gates need an explicit waiver mechanism (e.g. an issue referenced in
the PR that grants a one-off override with an expiry). Otherwise teams
disable the gate.

## 8. Component Bundle Size Is Not The Whole Story

A small component that imports 10 shared utilities can be heavier than
a larger self-contained one. Budget must include transitive imports,
not just the leaf file.
