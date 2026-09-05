# Well-Architected Notes - Navigation And Routing

## Relevant Pillars

### User Experience

Navigation is a direct user-experience concern. A component that routes predictably and preserves sharable state reduces friction and confusion. Two mechanics carry most of that weight: a real `href` on the anchor (so copy-link and open-in-new-window behave), and `replace: true` on state-only navigations (so a filter toggle does not turn the Back button into a rewind through every click).

### Reliability

PageReference-based routing is more reliable than hardcoded URLs because it delegates route translation to the platform rather than to each component author. The guide states the mechanism plainly: a PageReference insulates the component from future changes to URL formats and lets one component serve applications that use different URL formats.

### Operational Excellence

Routing is testable without an org. The `lightning/navigation` Jest mock turns "did this button navigate to the right place?" into an assertion on the PageReference object, which means a wrong `actionName` or a dropped namespace prefix fails in CI rather than in UAT.

## Architectural Tradeoffs

- **Hardcoded simplicity vs container safety:** String URLs are quick to write, but they push route knowledge into every component — and in an LWR site under Lightning Locker the `window` fallback is not available at all.
- **Rich URL state vs clean shareable links:** Too much state in the URL can be noisy, but too little makes flows impossible to bookmark or restore. The guide adds a hard constraint on top of taste: including personal data in URL parameters is unsafe even over HTTPS, so identifiers that are sensitive do not belong in `state`.
- **One internal-app pattern vs site-aware routing:** Reusing internal navigation assumptions in Experience Cloud creates hidden failure modes — `standard__component` does not resolve in a site, and `standard__recordPage` loses the `clone` and `edit` actions there.
- **Component page vs named site page:** A URL-addressable component gives a clean `/lightning/cmp/` deep link inside Lightning Experience, at the cost of a destination that cannot follow the component into an Experience Builder site.

## Anti-Patterns

1. **Mixed routing contracts** - some handlers use `window.location`, others use PageReference objects, and the UI becomes inconsistent.
2. **Unnamespaced custom state** - deep links become brittle because the state model is not using the supported convention.
3. **Ignoring container support** - a page type that works internally is assumed to work everywhere else without verification.
4. **Sensitive identifiers in URL state** - state is serialized into query parameters that land in browser history, referrer headers and shared links.
5. **Untested navigation** - the PageReference is never asserted, so a typo in `actionName` ships silently.

## Official Sources Used

- Lightning Web Components Developer Guide — **Navigate to Pages, Records, and Lists** (`use-navigate`), https://developer.salesforce.com/docs/platform/lwc/guide/use-navigate.html (which containers support `lightning/navigation` at all; the Lightning Out / LWC-for-Visualforce exclusions cited in gotchas and anti-pattern 2)
- Lightning Web Components Developer Guide — **Basic Navigation** (`use-navigate-basic`), https://developer.salesforce.com/docs/platform/lwc/guide/use-navigate-basic.html (the PageReference `type`/`attributes`/`state` contract, `Navigate(pageReference, [replace])`, and `GenerateUrl` returning a promise — the "GenerateUrl Hands Back A Promise" gotcha and anti-pattern 5)
- Lightning Web Components Developer Guide — **Add Query Parameters** (`use-navigate-add-params-url`), https://developer.salesforce.com/docs/platform/lwc/guide/use-navigate-add-params-url.html (the `c__` namespace rule, string-only values, frozen PageReference, `undefined` to delete a key, and the "query string alone does not rerender" behaviour behind three gotchas)
- Lightning Web Components Developer Guide — **PageReference Types** (`reference-page-reference-type`), https://developer.salesforce.com/docs/platform/lwc/guide/reference-page-reference-type.html (per-type attribute and container tables: record / object / navItem / webPage / component / recordRelationship / comm named page and login page — the Decision Guidance table and the objectPage action-name gotcha)
- Lightning Web Components Developer Guide — **Navigate to a URL-Addressable Component** (`use-navigate-url-addressable`) and **lightning__UrlAddressable Target** (`targets-lightning-url-addressable`), https://developer.salesforce.com/docs/platform/lwc/guide/use-navigate-url-addressable.html and https://developer.salesforce.com/docs/platform/lwc/guide/targets-lightning-url-addressable.html (the `standard__component` prerequisite, the `/lightning/cmp/c__MyComponent?c__mystate=value` URL shape, the console `uid` trick, and the Experience-Builder exclusion)
- Lightning Web Components Developer Guide — **Configure Custom Tabs** (`use-config-custom-tab`), https://developer.salesforce.com/docs/platform/lwc/guide/use-config-custom-tab.html (the `lightning__Tab` target and the tab-label-to-tab-name rule behind the `navItemPage.apiName` gotcha)
- Lightning Web Components Developer Guide — **Write Jest Tests** (`unit-testing-using-jest-create-tests`), https://developer.salesforce.com/docs/platform/lwc/guide/unit-testing-using-jest-create-tests.html (the `lightning/navigation` mock with `getNavigateCalledWith` / `getGenerateUrlCalledWith` and the `moduleNameMapper` entry used in references/code-examples.md)
- Lightning Web Components Developer Guide — **Navigate From a Modal** (`use-navigate-modal`) and **Quick Action Navigation** (`use-navigate-quick-action`), https://developer.salesforce.com/docs/platform/lwc/guide/use-navigate-modal.html and https://developer.salesforce.com/docs/platform/lwc/guide/use-navigate-quick-action.html (the `LightningModal` restriction and modal-stacking behaviour of `replace`)
