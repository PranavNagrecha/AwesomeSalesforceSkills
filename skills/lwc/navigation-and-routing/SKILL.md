---
name: navigation-and-routing
description: "Use when implementing or reviewing Lightning Web Component navigation with `NavigationMixin`, PageReference objects, URL state, and `CurrentPageReference` across Lightning Experience, mobile, and Experience Cloud. Triggers: 'navigate to record page from LWC', 'PageReference state not working', 'should I use window.location', 'Experience Cloud navigation issue'. NOT for component-to-component messaging or data-loading strategy when navigation is only a side effect."
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
triggers:
  - "how do i navigate to a record page from lwc"
  - "pagereference state parameters are not working"
  - "should i use window.location or navigationmixin"
  - "experience cloud navigation is broken"
  - "how do i read url state in lwc"
inputs:
  - "target destination such as record, object list, component, web page, or named site page"
  - "which container is in use: Lightning Experience, mobile, Aura site, or LWR site"
  - "whether the navigation needs deep-linkable URL state or a generated href"
outputs:
  - "navigation pattern recommendation using page references"
  - "review findings for hardcoded urls, bad state keys, or container mismatches"
  - "code guidance for Navigate, GenerateUrl, and CurrentPageReference usage"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

Use this skill when page changes are part of the component contract and those page changes need to survive container differences. Navigation in LWC is reliable only when it is expressed as a PageReference contract instead of as hardcoded Salesforce URLs.

---

## Before Starting

Gather this context before working on anything in this domain:

- Is the component navigating to a Salesforce resource, an Experience Cloud page, or an external URL?
- Does the user need a real deep link that can be bookmarked or shared, or is the navigation purely in-session?
- Which containers must support the behavior, and does the chosen page-reference type exist in all of them?

---

## Core Concepts

PageReference is the platform contract for navigation. It separates intent from concrete URL shape so Salesforce can translate the same request for Lightning Experience, mobile, and supported site containers. The moment a component falls back to `/lightning/...` or `/s/...` string building, it starts owning routing details the framework already knows better.

### Use `NavigationMixin` Instead Of Hardcoded URLs

`NavigationMixin.Navigate` is for moving the user. `NavigationMixin.GenerateUrl` is for building stable href values when the component needs a clickable anchor, copyable link, or preview. Both work from a PageReference object rather than a guessed URL.

### Page Type And Attributes Matter

`standard__recordPage`, `standard__objectPage`, `standard__webPage`, `standard__component`, and Experience Cloud page types all have different required attributes and support boundaries. Many bugs are not "navigation is broken"; they are "the wrong page-reference type was chosen for the container."

### URL State Is Part Of The Contract

When a component needs deep-linkable filters or modes, the state belongs in the PageReference. Custom state keys must be namespaced, such as `c__view` or `c__filter`. If the component reads URL state, it should do so through `CurrentPageReference` instead of parsing browser globals directly.

### Experience Cloud Requires Container Awareness

Some PageReference types differ by site technology and supported target. A navigation pattern that works in Lightning Experience can still fail in an Aura or LWR site if the destination type is not supported there. Site-safe navigation must be chosen deliberately rather than inherited from internal-app assumptions.

---

## Common Patterns

### Record-Oriented Navigation

**When to use:** After save, select, or row action, the component needs to open a record or object list page.

**How it works:** Build a record or object PageReference with explicit `recordId`, `objectApiName`, and `actionName`, then call `Navigate`.

**Why not the alternative:** Hardcoded Lightning URLs couple the component to one runtime and are easy to break.

### Generated Links For Stable Hrefs

**When to use:** The component needs an anchor tag, copy link action, or a preview URL before navigation happens.

**How it works:** Call `GenerateUrl` from the same PageReference the component would use for navigation and bind the result into the UI.

**Why not the alternative:** Duplicating one shape for `href` and another for `Navigate` usually causes drift.

### Deep-Linkable State With `CurrentPageReference`

**When to use:** The component needs URL-driven filters, tabs, or modes that should survive refresh and sharing.

**How it works:** Write state through the PageReference, read it through `CurrentPageReference`, and keep custom keys namespaced.

**Why not the alternative:** Parsing raw URL strings makes the component brittle and less portable across containers.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Open an existing record, related list entry point, or object home | `NavigationMixin` with `standard__recordPage` or `standard__objectPage` | Uses the supported Salesforce contract for internal destinations |
| Need a clickable internal link in markup | `GenerateUrl` from a PageReference | Keeps the href aligned with the real navigation contract |
| Need deep-linkable component state | PageReference `state` plus `CurrentPageReference` | URL state stays explicit and sharable |
| Need to open an external site | `standard__webPage` | External URLs should still flow through a clear page-reference type |
| Current implementation concatenates `/lightning/` or `/s/` paths | Refactor to PageReference | Hardcoded routes do not scale across containers |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Navigation uses a PageReference instead of a hardcoded internal URL.
- [ ] The chosen page type is valid for the target container and user experience.
- [ ] Required attributes such as `recordId` or `actionName` are explicit.
- [ ] Custom URL state keys are namespaced.
- [ ] `CurrentPageReference` is used for reading URL state instead of manual parsing.
- [ ] `GenerateUrl` is used when the UI needs a durable href rather than immediate navigation.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Hardcoded internal URLs are container assumptions** - they often work until the component is reused in mobile or Experience Cloud.
2. **Custom state keys need a namespace prefix** - unnamespaced keys do not form a stable custom URL-state contract.
3. **PageReference support varies by destination and container** - choosing the right page type matters as much as using NavigationMixin at all.
4. **Navigation and generated URLs should come from the same contract** - separate implementations drift quickly and confuse users.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Navigation design | Recommendation for page type, attributes, and state handling |
| Routing review | Findings on hardcoded URLs, missing attributes, and unsupported container assumptions |
| Refactor snippet | Concrete `Navigate`, `GenerateUrl`, and `CurrentPageReference` examples |

---

## Related Skills

- `lwc/component-communication` - use when an event or LMS message is the real issue and navigation is only downstream behavior.
- `lwc/lifecycle-hooks` - use when navigation setup or cleanup is happening at the wrong lifecycle boundary.
- `lwc/lwc-offline-and-mobile` - use when mobile container behavior changes the expectations for navigation and user flow.
