# Well-Architected Notes — LWC Lightning Modal

## Relevant Pillars

Modals are a UX primitive, but the architectural weight comes from
how the platform's base class enforces accessibility, security, and
operational consistency that hand-rolled overlays usually fail. Four
pillars carry weight; the dominant one is Accessibility because the
default focus-trap, `aria-labelledby`, and Esc-to-close behaviors are
the difference between "ships" and "fails WCAG 2.1 Level AA."

- **Accessibility (a sub-concern of Reliability + User Experience)** —
  `LightningModal` ships with focus management per SLDS Global Focus
  Guidelines: focus moves to the first interactive element on open
  (or the first footer button if header/body have none), focus traps
  inside the modal while open, and focus returns to the trigger on
  close. The header `label` automatically becomes the `aria-labelledby`
  target; `description` becomes `aria-description` / `aria-describedby`.
  Hand-rolling these in raw `slds-modal` markup means re-implementing
  WCAG 4.1.2 (Name, Role, Value), 2.1.2 (No Keyboard Trap inverse —
  trap *correctly*), and 2.4.3 (Focus Order). Almost every team that
  tries gets at least one wrong on the first cut.
- **Security** — Modals are rendered in a portal outside the parent
  shadow tree. In Experience Cloud with strict CSP, the portal still
  needs to satisfy `script-src`, `style-src`, and `frame-ancestors`
  policies — `LightningModal` is built against the platform's CSP
  contract; a custom overlay is not, and silently fails in some
  community contexts. Additionally, modals often host
  `lightning-record-edit-form` or `lightning-record-form` — both of
  which enforce CRUD/FLS automatically when using the wired output —
  but if the modal calls Apex imperatively, the Apex must enforce FLS
  itself: `WITH USER_MODE` on the query (the read idiom from API 57.0
  up — the `WITH SECURITY_ENFORCED` clause it replaces was removed in
  67.0 and no longer compiles), or
  `Security.stripInaccessible(AccessType.READABLE, records)` operating
  on the returned decision's `.getRecords()`. The gate is the
  `apiVersion` in the controller's `.cls-meta.xml`, not the org's
  release: a class still pinned to 58.0 compiles the old clause, but
  `WITH USER_MODE` is available there too and is the migration target.
- **Reliability** — `disableClose` is the only safe way to prevent
  user dismissal during an in-flight async operation (Apex callout,
  UI API write, file upload). Without it, Esc-on-spinner orphans the
  request, leaves the parent in a half-state, and creates
  reconciliation work the next page load can't always recover from.
  Pair `disableClose: true` with a hard ceiling (the docs recommend a
  max 5-second window) so a hung request never permanently locks the
  user out — long-running work belongs in a Queueable with a
  reopen-on-finish pattern, not a blocked modal.
- **Operational Excellence** — Standardizing on one modal API across
  an org means one place to fix accessibility regressions, one focus
  behavior to QA, one set of size variants to document. Hand-rolled
  modals scattered across an org each carry their own bugs;
  consolidating on `LightningModal` lets the platform's release notes
  do regression work for free (e.g., Winter '24's improvements to
  high-contrast theme support landed in every `LightningModal`-based
  surface with zero work from app teams).

## Architectural Tradeoffs

The defining tradeoff is **which overlay primitive to use**, since
Salesforce ships four different "show a panel" mechanisms with
overlapping capabilities:

| Dimension | `LightningModal` (lightning/modal) | Quick Action (Lightning Action) | `lightning/overlayLib` (Aura) | Custom `slds-modal` markup |
|---|---|---|---|---|
| Trigger surface | Imperative `.open()` from any LWC | Object action button | Imperative from Aura component | Conditional rendering in template |
| Focus trap | Built-in | Built-in (action shell) | Built-in | Must hand-roll |
| `aria-labelledby` | Auto from header label | Auto from action label | Auto from helper | Must hand-roll |
| Esc to dismiss | Built-in, opt-out via `disableClose` | Built-in, not configurable | Built-in, configurable | Must hand-roll |
| Return value | `await open()` Promise | Limited (apex action result) | Promise via helper | Custom event (only inside same tree) |
| Size variants | `small \| medium \| large \| full` | Action-config: small/large | Modal vs Popover variants | Whatever CSS you write |
| Portal render | Yes (escapes parent stacking context) | Yes (action shell) | Yes | No (inherits parent stacking) |
| Available in LWC? | Yes (base class) | Triggered FROM LWC headless QA, but action shell is platform | No (Aura-only) | Yes, but discouraged |
| Best for | In-page workflows, wizards, confirmations | Record-context CRUD actions | Legacy Aura pages still in the org | Never the first choice |

The handoff rule that works in practice: **use `LightningModal` by
default for any in-page modal triggered by user interaction. Use a
Quick Action when the user's mental model is "act on a record" and
the modal needs to surface from the record header bar. Use
`lightning/overlayLib` only when the host page is still Aura and
won't be migrated soon. Never use raw `slds-modal` markup in new
work.**

A second tradeoff: **`Modal.open()` vs in-template panel**. Practitioners
sometimes want a "modal-like" panel that lives inside the parent's
template so they can bind to it with `@api` getters and bidirectional
events. The platform's answer is: that's a *panel*, not a modal —
use the SLDS panel utility classes inside a regular LWC. Reserve
`LightningModal` for the case where the panel needs to be modal
(blocks the rest of the page, traps focus, escapes parent stacking
context). Conflating the two leads to either modals that don't
actually block (in-template attempts) or panels that block when they
shouldn't.

A third tradeoff: **size variants — fixed enum vs custom CSS**.
`LightningModal` exposes `small | medium | large | full` and silently
falls back to `medium` for any other value. Practitioners who want
"600px wide" reach for CSS overrides via `:host` styling and find
that the portal-rendered modal isn't inside the parent's shadow tree,
so `:host` selectors don't reach it. The correct posture is to design
within the four sizes — they map to SLDS layout primitives — and if
a use case truly needs a non-standard size, it's almost always
better redesigned as a full-page Lightning page or a side-panel
component, not a custom-sized modal.

## Anti-Patterns

1. **Building a modal out of raw `slds-modal` markup.** Loses focus
   trap, `aria-labelledby`, Esc-to-close, portal rendering, and
   `disableClose` semantics. See `examples.md` anti-pattern.
2. **Returning values via `dispatchEvent` instead of `this.close(value)`.**
   The parent has no listener attached (modal is in a portal, not in
   the parent's tree). The Promise from `Modal.open()` never resolves
   with the data. Use `this.close(payload)`.
3. **Omitting the `label` option in `Modal.open()`.** Required for
   accessible naming, even when you're not rendering a
   `lightning-modal-header`. Missing-label is the single most
   common LightningModal accessibility finding in audits.
4. **Holding `disableClose: true` for the whole modal lifetime.**
   Locks the user out of canceling even before they've started work.
   Toggle it reactively (`get disableClose() { return this.isSubmitting; }`)
   so it's only true during in-flight async operations, and cap the
   blocked window per the docs' 5-second guideline.
5. **Trying to nest a `LightningModal` inside a Quick Action, an Aura
   component, or a CSP-restricted surface.** The Quick Action IS the
   modal shell — don't double-wrap. Aura cannot extend
   `LightningModal` (LWC-only base class). Strict-CSP Experience
   Cloud sites need pre-promotion validation since portal rendering
   can fail silently.

## Official Sources Used

- LightningModal API Reference (component library):
  https://developer.salesforce.com/docs/component-library/bundle/lightning-modal/documentation
- lightning-modal-header API Reference:
  https://developer.salesforce.com/docs/component-library/bundle/lightning-modal-header/documentation
- lightning-modal-body API Reference:
  https://developer.salesforce.com/docs/component-library/bundle/lightning-modal-body/documentation
- lightning-modal-footer API Reference:
  https://developer.salesforce.com/docs/component-library/bundle/lightning-modal-footer/documentation
- SLDS Global Focus Guidelines (referenced from the LightningModal
  accessibility section):
  https://www.lightningdesignsystem.com/guidelines/focus/
- The WITH SECURITY_ENFORCED SOQL Clause Is Removed (Summer '26 / API 67.0):
  https://help.salesforce.com/s/articleView?id=release-notes.rn_apex_removed_withSecurityEnforced.htm&type=5
  — grounds the API-version gate on the Apex controller idiom above.
