# Well-Architected Notes — LWC Debugging DevTools

## Relevant Pillars

- **Operational Excellence** — Runtime debugging is an operational capability: the faster and more deterministic the path from "a user reports a blank component" to "root cause identified," the less downtime and guesswork the team absorbs. A documented devtools workflow with Debug Mode, Inspector, and wire network tracing replaces folklore-driven triage.
- **Reliability** — Silent render failures, swallowed throws, and Proxy-obscured logs all erode trust in the UI. A repeatable diagnostic workflow catches these failure modes before they become recurring production incidents and gives responders a concrete checklist instead of improvised console work.
- **Security** — Lightning Web Security and Experience Cloud CSP are security features that change what debugging can do; a responsible debugging workflow respects those boundaries (no "disable LWS to make debugging easier") and treats the Proxy wrapping of platform objects as a feature, not an obstacle.

## Architectural Tradeoffs

- **Debug Mode vs. perceived performance.** Debug Mode serves un-minified bundles and source maps. That makes the app noticeably slower. The tradeoff is: enable it scoped to the acting user for the duration of the investigation, disable it when done. Never leave it on org-wide.
- **`debugger;` statements vs. Sources breakpoints.** `debugger;` is fast to drop in and survives rebuilds, but it must never be committed. Sources breakpoints are cleaner but do not survive a browser restart unless you use persistent breakpoints. Prefer Sources breakpoints during investigation; only use `debugger;` when the code path is hard to reach from the Sources tree.
- **Inspector vs. logging.** The Inspector reads live component state without code changes. `console.log` requires edits, redeploys, and under LWS requires unwrapping. Reach for the Inspector first; use logging only when you need a timeline of state changes that the Inspector cannot snapshot.
- **Breakpoints vs. log-points in `renderedCallback`.** Breakpoints pause on every render cycle and are unusable at scale. Log-points (conditional, non-pausing) capture a timeline without freezing the app.

## Anti-Patterns

1. **Leaving Debug Mode on org-wide "because it was useful once."** End users experience degraded perceived performance and analytics are skewed. Debug Mode is a per-user, per-session capability; turn it off when the session ends.
2. **Relying on `console.log(obj)` without unwrapping under LWS.** The log prints a Proxy handle, the developer concludes the data "isn't there," and hours are spent chasing a phantom data-loading bug. Always use `JSON.parse(JSON.stringify(...))` or `structuredClone` when logging platform-wrapped objects.
3. **Skipping source maps and stepping through minified code.** Without Debug Mode, the Sources panel shows single-line minified blobs and framework wrapper code; breakpoints land in the wrong place and the call stack is unreadable. Always confirm Debug Mode before setting breakpoints.

## Official Sources Used

- LWC Debugging Overview — https://developer.salesforce.com/docs/platform/lwc/guide/debug-intro.html
- Debugging LWC in Chrome — https://developer.salesforce.com/docs/platform/lwc/guide/debug-chrome.html
- LWC Debug Mode — https://developer.salesforce.com/docs/platform/lwc/guide/debug-mode.html
- Lightning Component Inspector (Chrome Extension) — https://developer.salesforce.com/docs/platform/lwc/guide/debug-inspector.html
- Enable Debug Mode for Lightning Components (Help) — https://help.salesforce.com/s/articleView?id=sf.enable_debug_mode.htm&type=5
- Lightning Web Security Overview — https://developer.salesforce.com/docs/platform/lwc/guide/security-lwsec-intro.html
- LWC Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
