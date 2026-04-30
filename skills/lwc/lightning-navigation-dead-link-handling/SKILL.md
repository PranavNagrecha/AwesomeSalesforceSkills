---
name: lightning-navigation-dead-link-handling
description: "Use when an LWC navigates via NavigationMixin to records or pages that may no longer exist, lack the user's access, or be permanently moved. Triggers: 'lightning navigation 404', 'navigate to deleted record', 'NavigationMixin error toast', 'graceful fallback when target page missing', 'permission denied on navigation'. NOT for general routing within an SPA or for Experience Cloud public-facing routing."
category: lwc
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Reliability
triggers:
  - "navigation to a deleted record gives ugly toast"
  - "user has no access to target page after navigation"
  - "NavigationMixin returns blank screen instead of error"
  - "fallback navigation when target component is missing"
  - "deep link from email opens broken page"
tags:
  - lwc
  - navigation
  - error-handling
  - ux
inputs:
  - "the navigation target (recordId, pageReference, named page, URL)"
  - "expected failure modes (deleted, no access, missing component)"
  - "fallback behavior — toast, redirect, in-place message"
outputs:
  - "pre-navigation existence/access check"
  - "navigation handler with explicit failure path"
  - "user-facing fallback (toast, alternative target, contact-admin message)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-30
---

# Lightning Navigation Dead-Link Handling

Activate when an LWC's `NavigationMixin.Navigate` may target a record or page the user can't reach — deleted records, sharing-restricted records, retired Lightning pages, or component-named targets that have been removed. The skill produces a pre-navigation guard, a graceful failure path, and a user message that doesn't leave them on a blank screen.

---

## Before Starting

Gather this context before working on anything in this domain:

- The navigation target type: `recordPage`, `comm__namedPage`, `standard__webPage`, etc. Each fails in distinct ways.
- The user's expected access path. A reportable record may have been shared at one point and lost access later; a deep link from an email sent yesterday may target a record deleted today.
- The downstream UX expectation. Some teams want a toast + stay-in-place; others want a redirect to a "default" page; service console teams sometimes want to open a different subtab as fallback.

---

## Core Concepts

### Failure modes

| Failure | Surfaces as | Detection |
|---|---|---|
| Record deleted | Lightning shows "Insufficient privileges" or generic error | Pre-navigation `getRecord` returns error with `INVALID_ID` |
| User lacks access | "Insufficient privileges" toast | Pre-check via UI API; or wire `getRecord` and inspect error |
| Lightning page retired/unpublished | Blank tab, no toast | `getNavigationItems` doesn't return target — must validate before navigating |
| Component target removed | Console error in dev tools, blank surface | Caught only at the destination's `connectedCallback` |
| External URL 404 | Browser tab shows external 404 | Cannot detect from LWC; can only set `window.open` and let browser handle |

### NavigationMixin contract

`NavigationMixin.Navigate(pageReference, replace)` returns a promise that **resolves** as soon as Lightning *initiates* the navigation, not when the target finishes loading. The promise does not reject for inaccessible records — Lightning navigates, then the destination throws inside its own component lifecycle. That means catching errors with `.catch()` on the Navigate call alone is insufficient.

### Pre-navigation validation

The reliable pattern is to validate the target *before* calling Navigate. For records, use `getRecord` from `lightning/uiRecordApi` to confirm existence + access. For named pages, query `getNavigationItems` to confirm publish status. For external URLs, accept that detection isn't possible from the LWC and surface a "this may take you outside Salesforce" warning.

---

## Common Patterns

### Pattern: pre-flight `getRecord` check

**When to use:** Navigating to a record passed in via custom button, deep link, or stale tab.

**How it works:** Call `getRecord({ recordId, fields: ['Id'] })` first. If the wire returns an error, show a friendly message and don't navigate. If success, call `NavigationMixin.Navigate`.

**Why not the alternative:** Calling Navigate on a deleted record drops the user into an opaque error page with no way back to context.

### Pattern: navigation-items existence check

**When to use:** Navigating to a `comm__namedPage` or a navigation menu item that may have been retired.

**How it works:** Wire `getNavigationItems` (or call it imperatively) at component connect time. Cache the available targets. Validate the requested target against the cache before each Navigate. If absent, show a "this destination is no longer available" message and (optionally) navigate to a default page.

### Pattern: console-aware fallback

**When to use:** In Service Console, the user clicked a link that should open a subtab; the target record is gone.

**How it works:** Use `lightning/platformWorkspaceApi` to detect console context. On dead link, instead of opening a broken subtab, open a "lookup the right record" search subtab keyed by the original record name (if known) so the user has a recovery path.

---

## Decision Guidance

| Target type | Recommended pre-check | Failure UX |
|---|---|---|
| Record (recordPage) | `getRecord` wire | Toast + stay in place; offer search-by-name |
| Standard named page | None (always available) | n/a |
| `comm__namedPage` (Experience Cloud) | `getNavigationItems` | Toast + redirect to community home |
| `standard__webPage` (external) | None possible | Open in new tab + warning |
| Component-named (`standard__component`) | `getNavigationItems` doesn't cover; document expected components in source | Stay in place |

---

## Recommended Workflow

1. Identify the navigation target type and the most likely failure mode for the calling context (deep link from email, in-app button, console subtab, etc.).
2. Add a pre-navigation check appropriate to the target type. For records, wire `getRecord` and only enable the navigate trigger when the wire returns success.
3. Wrap the actual `NavigationMixin.Navigate` call in a try/catch with an error path, even though most failures don't surface there — defense in depth.
4. Define the fallback UX. A toast is always table-stakes; for high-value journeys, define a recovery route (alternative page, search-by-name, contact-admin link).
5. Log the failure (custom event to a parent logger, or a Lightning Platform Event publish for analytics) so the team learns where dead links cluster.
6. Test by manually deleting a record between page-load and click, confirming the user lands on the fallback rather than the broken page.

---

## Review Checklist

- [ ] Pre-navigation existence/access check appropriate to the target type
- [ ] `Navigate` call wrapped in try/catch with explicit failure path
- [ ] Fallback UX defined (toast, redirect, in-place message) — not silent
- [ ] Failure logged or eventized so dead-link patterns are observable
- [ ] Console-context detection if relevant
- [ ] Tests cover both success and failure paths

---

## Salesforce-Specific Gotchas

1. **`Navigate` resolves before the destination loads** — A `.then()` on Navigate runs before the destination decides it can't render. Don't put success logic in the `.then()` of Navigate.
2. **`getRecord` error semantics differ for deleted vs. no-access** — Deleted gives `INVALID_ID`; no-access gives `INSUFFICIENT_ACCESS_OR_READONLY`. Distinguish in your error UX.
3. **Experience Cloud guest user navigation may silently no-op** — Guest users without access to a target get no toast at all. Always pre-check.
4. **`NavigationMixin` is not available in headless Aura sites** — Confirm host context; fall back to `window.location.assign` only when truly necessary and origin-checked.
5. **Console workspace navigation is not the same as page navigation** — Use the workspace API for subtab actions; mixing the two leads to subtabs opening as new tabs instead.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Navigation handler module | Pre-check + Navigate + fallback flow as a reusable LWC module |
| Failure UX components | Toast, "page no longer available" placeholder, contact-admin link |
| Telemetry event | Custom event or Platform Event documenting dead-link occurrence for observability |

---

## Related Skills

- lwc/lwc-imperative-apex — for cases where the pre-check needs an Apex SOQL rather than `getRecord`
- lwc/common-lwc-runtime-errors — for the broader catalog of runtime failures including those that surface after navigation
- lwc/headless-experience-cloud — for navigation in headless contexts where `NavigationMixin` is partially unavailable
