# Well-Architected Notes — Lightning Navigation Dead-Link Handling

## Relevant Pillars

- **User Experience** — A blank page or generic "Insufficient privileges" toast is the worst-shaped failure: the user has no signal about what to do next. Pre-checks let the LWC produce an actionable failure (search, redirect, contact admin).
- **Reliability** — Email deep links and pinned tabs outlive the records they reference. Treating dead-link handling as a first-class concern instead of an afterthought makes the system resilient to data lifecycle, not just to network failure.

## Architectural Tradeoffs

- **Pre-check cost vs. UX cost:** A `getRecord` wire is cheap (cached in UI API); the user-experience cost of a dead navigation is high. Always pre-check.
- **Generic vs. context-specific recovery:** A single "page unavailable" toast is consistent but unhelpful. Context-specific recovery (search-by-name, redirect to home, request-access link) costs more design effort but pays back in user satisfaction.
- **Console-aware code vs. platform-portable code:** Detecting console context branches code paths. The alternative — pretending console doesn't exist — produces wrong behavior in console (subtabs opening as new primary tabs).

## Anti-Patterns

1. **`.catch()` as the only failure handler** — Doesn't fire for the failures users hit. Pre-check before navigating.
2. **`window.location.assign` fallback** — Bypasses Lightning routing and breaks deep links. Use a known-good `Navigate` call.
3. **Single toast for all errors** — Surfaces no useful next action. Distinguish deleted from no-access from retired-page.

## Official Sources Used

- LWC Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
- Lightning Component Reference — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide
- LWC Data Guidelines — https://developer.salesforce.com/docs/platform/lwc/guide/data-guidelines.html
- NavigationMixin Reference — https://developer.salesforce.com/docs/platform/lwc/guide/use-navigate.html
- Workspace API Reference — https://developer.salesforce.com/docs/platform/lwc/guide/use-workspace-api.html
