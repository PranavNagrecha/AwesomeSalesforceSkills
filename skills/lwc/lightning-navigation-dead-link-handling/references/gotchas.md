# Gotchas — Lightning Navigation Dead-Link Handling

Non-obvious behaviors that cause real production problems in this domain.

## Gotcha 1: `Navigate` resolves before the destination renders

**What happens:** `.then()` after `NavigationMixin.Navigate` runs; logic placed there assumes success. Then the destination tab shows "Insufficient privileges."

**When it occurs:** Always — `Navigate` is a fire-and-forget dispatch, not an arrival promise.

**How to avoid:** Validate the target before calling Navigate. Don't rely on the Navigate promise to indicate success.

---

## Gotcha 2: Deleted-vs-no-access produces different `getRecord` errors

**What happens:** Generic "could not load" message hides whether the user lacks access (admin can grant) or the record is gone (user must search).

**When it occurs:** Any pre-check that doesn't distinguish error codes.

**How to avoid:** Inspect `error.body[0].errorCode` (or `error.statusText`). `INVALID_ID` = deleted; `INSUFFICIENT_ACCESS_OR_READONLY` = sharing/permissions. Surface different recovery paths.

---

## Gotcha 3: Experience Cloud guest user navigation silently no-ops

**What happens:** Guest user clicks a link to a record they can't see. No toast, no error — the URL changes but the page renders blank.

**When it occurs:** Any guest-user navigation to a record outside the guest sharing rule.

**How to avoid:** Pre-check is non-optional for guest contexts. If the wire returns no data, never call Navigate.

---

## Gotcha 4: Console workspace navigation differs from page navigation

**What happens:** Calling `NavigationMixin.Navigate` inside a console subtab opens a *new* primary tab instead of navigating in place.

**When it occurs:** When the LWC isn't workspace-aware.

**How to avoid:** Detect console context with `IsConsoleNavigation` (`lightning/platformWorkspaceApi`) and use `openSubtab` / `focusSubtab` instead.

---

## Gotcha 5: `getNavigationItems` returns only menu items, not all destinations

**What happens:** Pre-checking against `getNavigationItems` for a `comm__namedPage` returns false even though the page exists; the page just isn't in the navigation menu.

**When it occurs:** Pages exist in Experience Cloud but aren't in the active navigation menu.

**How to avoid:** Use `getNavigationItems` only to validate menu-bound destinations. For arbitrary `namedPage` checks, accept that pre-validation isn't possible and design fallback UX accordingly.
