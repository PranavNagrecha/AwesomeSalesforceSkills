---
name: navigation-and-routing
description: "URL routing, deep links, and page-reference patterns beyond basic NavigationMixin calls. Triggers: deep link LWC, page reference, URL state, c__ state key, GenerateUrl href, CurrentPageReference, standard__component, lightning__UrlAddressable, navItemPage custom tab. NOT for simple in-app navigation — use lwc/lwc-navigation-mixin."
category: lwc
salesforce-version: "Spring '25+'"
well-architected-pillars:
  - User Experience
  - Reliability
tags:
  - navigationmixin
  - pagereference
  - currentpagereference
  - experience-cloud
  - url-state
  - deep-linking
  - url-addressable
triggers:
  - "how do i navigate to a record page from lwc"
  - "pagereference state parameters are not working"
  - "should i use window.location or navigationmixin"
  - "experience cloud navigation is broken"
  - "how do i read url state in lwc"
  - "build a deep link that survives a browser refresh"
  - "generateurl returns object promise in my href"
  - "changing the url query string does not rerender my component"
  - "navigate to a custom tab from a lightning web component"
  - "cannot assign to read only property of frozen pagereference"
  - "open a url addressable lwc with standard__component"
  - "why does my c__ state key disappear from the url"
  - "test navigationmixin with jest getnavigatecalledwith"
  - "lwc navigation not working in an experience cloud site"
inputs:
  - "target destination such as record, object list, component, web page, or named site page"
  - "which container is in use: Lightning Experience, mobile, Aura site, or LWR site"
  - "whether the navigation needs deep-linkable URL state or a generated href"
outputs:
  - "navigation pattern recommendation using page references"
  - "review findings for hardcoded urls, bad state keys, or container mismatches"
  - "code guidance for Navigate, GenerateUrl, and CurrentPageReference usage"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

Use this skill when page changes are part of the component contract and those page changes need to survive container differences. Navigation in LWC is reliable only when it is expressed as a PageReference contract instead of as hardcoded Salesforce URLs.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the component navigating to a Salesforce resource, an Experience Cloud page, or an external URL?
- Does the user need a real deep link that can be bookmarked or shared, or is the navigation purely in-session?
- Which containers must support the behavior, and does the chosen page-reference type exist in all of them?

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Which containers must this run in — Lightning Experience, the mobile app, an Aura site, an LWR site, a console app? | `lightning/navigation` is supported only in Lightning Experience, Experience Builder sites and the Salesforce mobile app; it is not supported in Lightning Components for Visualforce or Lightning Out, even when those are embedded inside Lightning Experience. | Rules out whole page-reference types before any code is written, instead of after a site release. |
| Is the destination a *record*, an *object*, a *tab*, a *component*, or an off-platform URL? | Each type owns a different attribute set. `standard__objectPage` takes `home`/`list`/`new`; record-level `clone`/`edit`/`view` and `recordId` belong to `standard__recordPage`. | Fixes the page type before attributes are filled in, which is the single largest source of silently-wrong navigation. |
| Does the URL need to be bookmarkable and shareable, or is it in-session only? | A shareable URL means the state belongs in `PageReference.state`, which means every value must be a string and every custom key must carry a `c__` prefix. | Decides whether you need `CurrentPageReference` reactivity at all, or just a `Navigate` call. |
| Does anything in that state identify a person? | Including personal data in URL parameters is unsafe even over HTTPS — the state is serialized into query parameters that land in history, referrers and pasted links. | Moves the sensitive identifier out of the URL and into a wire or Apex lookup keyed on something non-identifying. |
| Does the UI need a clickable anchor, or only a button? | An anchor needs a real `href` from `GenerateUrl`, which resolves asynchronously. A button only needs `Navigate`. | Prevents the `javascript:void(0)` + onclick shape that breaks copy-link and open-in-new-tab. |
| If this navigates to a component page, who owns the target bundle, and does it already declare `lightning__UrlAddressable`? | `standard__component` resolves only against a bundle carrying that target, the name is case-sensitive, and the target is unsupported in Experience Builder sites. | Surfaces a second deployable component that must ship in the same `package.xml`, or rules the approach out for a site. |
| Will a state change re-render the page, or does something have to observe it? | The view is not rerendered when only the URL query string changes; a component must observe `CurrentPageReference` to react to its own deep link. | Turns "the URL updates but nothing happens" from a debugging session into a design decision. |

What a proper configuration adds over just doing it: a routing contract that is asserted in Jest against the PageReference object, so a wrong `actionName`, a dropped `c__` prefix or a container-unsupported page type fails in CI rather than in a user's Experience Cloud session.

---

## Core Concepts

PageReference is the platform contract for navigation. It separates intent from concrete URL shape so Salesforce can translate the same request for Lightning Experience, mobile, and supported site containers. The moment a component falls back to `/lightning/...` or `/s/...` string building, it starts owning routing details the framework already knows better.

### The Three Parts Of A PageReference

| Property | Required | What it is |
|---|---|---|
| `type` | Yes | Generates the URL format and defines which attributes apply. |
| `attributes` | Yes | Name-value pairs that determine the target page. The type defines the legal names. |
| `state` | No | String keys to string values, serialized to query parameters. Custom keys need a `<namespace>__` prefix. |

### Use `NavigationMixin` Instead Of Hardcoded URLs

`NavigationMixin.Navigate(pageReference, [replace])` is for moving the user; `replace` defaults to `false` and rewrites the current history entry when set to `true`. `NavigationMixin.GenerateUrl(pageReference)` returns a **promise** that resolves to the URL, for anchors, copy-link actions and `window.open`. Both are added to the class by applying the mixin — `extends NavigationMixin(LightningElement)` — not by importing it.

### Page Type And Attributes Matter

| Type | Key attributes | Container notes |
|---|---|---|
| `standard__recordPage` | `recordId`, `actionName` (`clone`/`edit`/`view`), `objectApiName` | `objectApiName` required in LWR sites; sites do not support `clone` or `edit`. |
| `standard__objectPage` | `objectApiName`, `actionName` (`home`/`list`/`new`) | `state.filterName` selects the list view, default `Recent`; in sites `list` and `home` are the same. |
| `standard__recordRelationshipPage` | `recordId`, `relationshipApiName`, `objectApiName`, `actionName` (`view` only) | Related lists only. |
| `standard__navItemPage` | `apiName` (the tab *name*) | Target component needs the `lightning__Tab` target. |
| `standard__component` | `componentName` as `namespace__componentName`, case-sensitive | Target needs `lightning__UrlAddressable`; not supported in Experience Builder sites. |
| `standard__namedPage` | `pageName` (`home`, `chatter`, `today`, `dataAssessment`, `filePreview`) | Experience Builder sites use a *separate* named-page type keyed on `name` (the page's API Name), not `pageName`. |
| `standard__webPage` | `url` | In Aura sites some Salesforce URLs get site-specific processing. |

### URL State Is Part Of The Contract

When a component needs deep-linkable filters or modes, the state belongs in the PageReference. Custom state keys must be namespaced, such as `c__view` or `c__filter`, and every value must be a string. If the component reads URL state, it should do so through `CurrentPageReference` instead of parsing browser globals directly — and it must, because a query-string-only change does not trigger a rerender on its own.

### Experience Cloud Requires Container Awareness

**UNVERIFIED (2026-09-05):** the literal type tokens for the Experience-Builder-only page types (`comm__namedPage`, `comm__loginPage`) and for `standard__app` and `standard__recordRelationshipPage` are not printed in the extracted `reference-page-reference-type` text — the attribute tables are grounded (L22133–22156, L22200–22208) but the code samples carrying the token strings were stripped. Confirm each token against the live PageReference Types page before shipping code that uses it.


Some PageReference types differ by site technology and supported target. A navigation pattern that works in Lightning Experience can still fail in an Aura or LWR site if the destination type is not supported there. Site-safe navigation must be chosen deliberately rather than inherited from internal-app assumptions.

---

## Common Patterns

### Record-Oriented Navigation

**When to use:** After save, select, or row action, the component needs to open a record or object list page.

**How it works:** Build a record or object PageReference with explicit `recordId`, `objectApiName`, and `actionName`, then call `Navigate`.

**Why not the alternative:** Hardcoded Lightning URLs couple the component to one runtime and are easy to break.

### Generated Links For Stable Hrefs

**When to use:** The component needs an anchor tag, copy link action, or a preview URL before navigation happens.

**How it works:** Call `GenerateUrl` from the same PageReference the component would use for navigation, resolve the promise into a field, and bind that field into the template.

**Why not the alternative:** Duplicating one shape for `href` and another for `Navigate` usually causes drift.

### Deep-Linkable State With `CurrentPageReference`

**When to use:** The component needs URL-driven filters, tabs, or modes that should survive refresh and sharing.

**How it works:** Read state through a getter over the `CurrentPageReference` wire, and write it by copying the frozen page reference with `Object.assign` and navigating to the copy with `replace: true`.

**Why not the alternative:** Parsing raw URL strings makes the component brittle and less portable across containers.

### Navigation From A Modal Or Quick Action

**When to use:** A screen quick action or `LightningModal` subclass needs to send the user somewhere on confirm.

**How it works:** Build the PageReference in a child component, dispatch it on a custom event, and call `Navigate` in the parent that opened the modal.

**Why not the alternative:** The mixin cannot be applied to a class that extends `LightningModal`, so the obvious fix does not compile into working navigation.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Open an existing record, related list entry point, or object home | `NavigationMixin` with `standard__recordPage` or `standard__objectPage` | Uses the supported Salesforce contract for internal destinations |
| Need a clickable internal link in markup | `GenerateUrl` from a PageReference, resolved via `.then` | Keeps the href aligned with the real navigation contract |
| Need deep-linkable component state | PageReference `state` plus `CurrentPageReference` | URL state stays explicit and sharable |
| Need to open an external site | `standard__webPage` | External URLs should still flow through a clear page-reference type |
| Need a deep link straight to a custom UI in Lightning Experience | `standard__component` plus `lightning__UrlAddressable` on the target | The only supported way to address a component by URL — and it stops at the site boundary |
| Same requirement, but inside an Experience Cloud site | The Experience Builder named-page type, keyed on the page's API Name | `standard__component` does not resolve in Experience Builder sites |
| Need to reach a custom tab | `standard__navItemPage` with the tab's api name | Tabs are addressed by name, not by the component behind them |
| Current implementation concatenates `/lightning/` or `/s/` paths | Refactor to PageReference | Hardcoded routes do not scale across containers |
| Console app re-opens a duplicate tab for the same component | Pass a `uid` value in `state` | Documented way to make the console recognise an already-open tab |

---

## Recommended Workflow

1. **Classify the destination and the container.** Answer the Questions table above, then pick the row from the Page Type table in Core Concepts. Do not fill in attributes before the type is settled.
2. **Model the PageReference on paper first** using `templates/navigation-and-routing-template.md` — destination type, container, whether a shareable URL is needed, and which `c__` state keys form the contract.
3. **Build the bundle from `references/code-examples.md`.** Copy the `navHub` shape for the navigating component and the `caseDashboardHost` shape for a URL-addressable target. Take the bundle skeleton from `templates/lwc/component-skeleton/` and the Jest `moduleNameMapper` from `templates/lwc/jest.config.js`.
4. **Write the navigation tests before deploying.** Use the `lightning/navigation` mock and assert the PageReference itself with `getNavigateCalledWith()` / `getGenerateUrlCalledWith()` — type, `actionName`, and that every custom state key matches `/^[a-zA-Z0-9]+__/` and every value is a string.
5. **Run the static check** over the source tree: `python3 skills/lwc/navigation-and-routing/scripts/check_navigation_and_routing.py --manifest-dir force-app/main/default/lwc`. It flags browser navigation APIs, hardcoded internal URLs, an unapplied mixin, a synchronously-consumed `GenerateUrl`, un-namespaced state keys, missing `actionName`, incomplete bundles and missing `__tests__`.
6. **Deploy the whole routing unit together.** The `package.xml` in `references/code-examples.md` ships the navigating bundle, the URL-addressable target and the `CustomTab` in one payload — a `navItemPage` or `standard__component` reference deployed without its destination is a dead link.
7. **Verify in the real container.** Open the component and read the browser URL: the query string must carry the `c__` keys. Then repeat in every container from step 1, because per-type support is where the pattern actually breaks.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Navigation uses a PageReference instead of a hardcoded internal URL.
- [ ] The chosen page type is valid for the target container and user experience.
- [ ] Required attributes such as `recordId` or `actionName` are explicit.
- [ ] `objectApiName` is present on record page references even where it is optional today.
- [ ] Custom URL state keys are namespaced and every state value is a string.
- [ ] No personal or sensitive identifier is carried in `state`.
- [ ] `CurrentPageReference` is used for reading URL state instead of manual parsing.
- [ ] `GenerateUrl` is used when the UI needs a durable href, and its promise is resolved.
- [ ] `replace: true` is used for state-only navigations so Back is not spammed.
- [ ] A `standard__component` target declares `lightning__UrlAddressable` and ships in the same manifest.
- [ ] `__tests__` asserts the PageReference object, not just that a click happened.
- [ ] `scripts/check_navigation_and_routing.py` reports no issues.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems (full detail with grounding in `references/gotchas.md`):

1. **Hardcoded internal URLs are container assumptions** - they often work until the component is reused in mobile or Experience Cloud, and the `window` fallback is unavailable under Locker in LWR sites.
2. **Custom state keys need a namespace prefix followed by two underscores** - and every value must be a string.
3. **`GenerateUrl` returns a promise** - assigning it straight to a field binds a Promise object into the template.
4. **A query-string-only change does not rerender the view** - only observing `CurrentPageReference` makes the component react.
5. **The PageReference you receive is frozen** - copy it with `Object.assign` before changing state.
6. **`standard__objectPage` has no `view` or `edit` action** - record-level actions live on `standard__recordPage`.
7. **`navItemPage.apiName` is the tab name, not the label** - "Case Console" is `Case_Console`.
8. **`standard__component` and `lightning__UrlAddressable` stop at the site boundary** - both are unsupported in Experience Builder sites.
9. **`NavigationMixin` cannot be applied to a `LightningModal` subclass** - navigate from the parent that opened the modal.
10. **PageReference support varies by destination and container** - choosing the right page type matters as much as using NavigationMixin at all.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Navigation design | Recommendation for page type, attributes, and state handling |
| Routing review | Findings on hardcoded URLs, missing attributes, and unsupported container assumptions |
| Component bundle | `navHub` / `caseDashboardHost` shape from `references/code-examples.md`, with `-meta.xml` and `package.xml` |
| Jest suite | PageReference assertions using the `lightning/navigation` mock |
| Checker output | `scripts/check_navigation_and_routing.py --manifest-dir <lwc source>` |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/code-examples.md` | You are writing the component. Full `navHub` + `caseDashboardHost` bundles, the `lightning/navigation` Jest mock, `jest.config.js`, `-meta.xml`, `package.xml`, and the deploy/verify commands. |
| `references/gotchas.md` | Navigation "works" but does something unexpected — a state change that does not rerender, a frozen page reference, a tab that resolves to nothing, a site that behaves differently from Lightning Experience. |
| `references/llm-anti-patterns.md` | You are reviewing generated code, or self-checking your own. Eight failure shapes with their detection hints, each mapped to a checker rule. |
| `references/examples.md` | You are choosing between page types, or need worked examples of post-save navigation and deep-linkable filter state. |
| `references/well-architected.md` | You are justifying the routing design, weighing URL state against privacy, or need the official source list. |
| `templates/navigation-and-routing-template.md` | Before writing code — fill in the destination, container, state keys and validation notes as a design worksheet. |

---

## Related Skills

- `lwc/lwc-navigation-mixin` - use for a straightforward `NavigationMixin.Navigate` call; come back here when the URL, its state, or cross-container support is the actual problem.
- `lwc/lightning-navigation-dead-link-handling` - use when the page reference is correct but the destination is deleted, moved, or invisible to the user.
- `lwc/lwc-console-workspace-api` - use when the destination is a console workspace tab or subtab rather than a page, via `lightning/platformWorkspaceApi`.
- `lwc/experience-cloud-lwc-components` - use when the component itself is being built for Experience Builder and the site's targets and guest-user context are in play.
- `lwc/component-communication` - use when an event or LMS message is the real issue and navigation is only downstream behavior.
- `lwc/lifecycle-hooks` - use when navigation setup or cleanup is happening at the wrong lifecycle boundary.
- `lwc/lwc-offline-and-mobile` - use when mobile container behavior changes the expectations for navigation and user flow.
