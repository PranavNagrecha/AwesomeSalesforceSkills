# Well-Architected Notes - Navigation And Routing

## Relevant Pillars

### User Experience

Navigation is a direct user-experience concern. A component that routes predictably and preserves sharable state reduces friction and confusion.

### Reliability

PageReference-based routing is more reliable than hardcoded URLs because it delegates route translation to the platform rather than to each component author.

## Architectural Tradeoffs

- **Hardcoded simplicity vs container safety:** String URLs are quick to write, but they push route knowledge into every component.
- **Rich URL state vs clean shareable links:** Too much state in the URL can be noisy, but too little makes flows impossible to bookmark or restore.
- **One internal-app pattern vs site-aware routing:** Reusing internal navigation assumptions in Experience Cloud creates hidden failure modes.

## Anti-Patterns

1. **Mixed routing contracts** - some handlers use `window.location`, others use PageReference objects, and the UI becomes inconsistent.
2. **Unnamespaced custom state** - deep links become brittle because the state model is not using the supported convention.
3. **Ignoring container support** - a page type that works internally is assumed to work everywhere else without verification.

## Official Sources Used

- Use the Navigation Service - https://developer.salesforce.com/docs/platform/lwc/guide/use-navigate
- Navigate to Different Page Types - https://developer.salesforce.com/docs/platform/lwc/guide/reference-page-reference-type
- CurrentPageReference - https://developer.salesforce.com/docs/platform/lwr/references/csr-reference/currentpagereference.html
