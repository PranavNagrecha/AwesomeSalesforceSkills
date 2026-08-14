---
name: flow-open-a-page-action
description: "Use when a Screen Flow needs to send the user to another page — the native Open a Page action (Summer '26) that opens a Salesforce record or an external URL directly from a flow. NOT for launching/embedding a flow ( — use flow/screen-flows. NOT for building a custom navigation LWC screen component ( — use flow/flow-screen-lwc-components."
category: flow
salesforce-version: "Summer '26+"
well-architected-pillars:
  - Security
  - Operational Excellence
triggers:
  - "navigate the user to the record their screen flow just created"
  - "open a Salesforce record or external URL from a screen flow without writing a custom LWC"
  - "redirect users when a screen flow finishes instead of using the retURL URL hack"
  - "configuring the Open a Page action's Where to Open Page input"
  - "make a screen flow send the user to a page in a new browser tab after saving"
tags:
  - flow-open-a-page-action
  - screen-flow
  - navigation
  - open-a-page
  - flow-actions
inputs:
  - "The Screen Flow that should navigate the user somewhere (post-save redirect or mid-flow jump)"
  - "The navigation target: a Salesforce record (Id) or an external web page (URL)"
  - "Desired open location (how/where the page should open) for the Where to Open Page input"
outputs:
  - "A configured Open a Page action in a Screen Flow, or a recommendation to use it"
  - "A migration plan replacing a legacy redirect (custom LWC / Redirect local action / retURL) with the native action"
  - "A navigation-design decision (native action vs. finish behavior vs. custom component)"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-07-08
---

# Flow Open A Page Action

This skill activates when a Screen Flow needs to move the user to another page — most often to the record it just created or updated, or to an external URL. Salesforce shipped a native **Open a Page** action in the Summer '26 release (release note: *"Simplify the User Workflow with the Open a Page Action"*) so this common navigation no longer requires a custom Lightning web component, a Redirect local action, or a URL hack. Use it to design that navigation, or to migrate an existing homegrown redirect onto the supported action.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Confirm it's a Screen Flow.** Open a Page is introduced as a **Screen Flow** action ("Screen Flows now support the new Open a Page action"). Navigation needs a running UI surface to act on, so an autolaunched, record-triggered, scheduled, or platform-event flow has nowhere to send the user. If the requirement is "after this automation, send the user somewhere," the automation must ultimately run inside a Screen Flow the user is interacting with.
- **Know the two destinations.** The action opens either a **Salesforce record** or an **external web page (URL)**. Decide which you need and where the target value comes from — a record variable/`recordId` for the former, a text/URL resource for the latter.
- **Decide where the page should open.** The action exposes a **Where to Open Page** input that controls the open location. Nail this down with the requester: opening in a new browser tab behaves very differently from replacing the current view.
- **Maturity and verification status (read this).** The Summer '26 release-note title for this action carries no "(Beta)" or "(Pilot)" label — unlike some sibling Summer '26 features that are explicitly stamped "(Generally Available)" — but the retrievable official pages did **not** state a GA/Beta/Pilot maturity for this action, and the full Help reference article renders only as a client-side app shell to automated fetchers. **Do not assert a GA/Beta/Pilot status this action's release notes don't state.** Before you lock a build, open the action in Flow Builder (or read its in-product help panel) in a Summer '26 org to confirm the **exact input labels, the available Where to Open Page options, and edition/license availability** — those specifics are not fully pinned by a citable official quote here.

---

## Core Concepts

### The action: a supported replacement for redirect hacks

Before Summer '26, "when this Screen Flow finishes, take the user to the new record" had no first-class control. Admins reached for one of three workarounds, all of which this action is meant to retire:

- a **custom LWC** screen component calling `NavigationMixin` / `lightning/navigation`,
- the **Redirect Flow Users with a Local Action** pattern (the `c:navigateToUrl` / `force:navigateToURL` local action), or
- a **retURL URL hack** — customizing the flow's finish URL so the runtime lands somewhere specific.

The Open a Page action packages the common cases (open a record, open a URL) as a configurable, clicks-not-code action, so the flow's navigation is declarative metadata instead of a component or a URL string that breaks on the next runtime change.

### The two navigation targets

| Target | What it opens | Typical source of the value |
|---|---|---|
| Salesforce record | The record's page (its default view) | A record variable / `recordId` produced earlier in the flow |
| External web page | An arbitrary URL | A text/formula resource holding the URL |

When it opens a record, you choose **View** or **Edit** mode via the action's **View Mode** input; either way the user lands on the record's main page — there is no built-in way to target a specific related list / related tab. (A live IdeaExchange request, *"Provision to navigate to a related tab from Open a Page action in Flow,"* exists precisely because the shipped action opens the record's main page, not a chosen tab.)

### The "Where to Open Page" input

`Where to Open Page` is the input that controls **how/where** the page opens. Treat it as the highest-risk configuration choice, because it changes whether the flow "hands off" the user or opens the page alongside where they are. Two documented constraints frame it:

- There is currently **no "Current Page" option** — a live IdeaExchange request, *"Open a Page Flow Action - Add 'Current Page' as Where to Open Page Option,"* asks Salesforce to add one. So you cannot (yet) tell the action to reuse/refresh the exact page the user is on.
- The exact set of open-location option labels is not pinned by a citable official quote in this skill's sources — **confirm them in Flow Builder** before you promise a specific behavior (e.g. "opens in a new tab").

### Navigation is not the flow's finish behavior

The Open a Page action is a step you place **inside** the flow's canvas, distinct from the older *finish behavior* mechanisms ("Understanding When a Screen Flow Finishes," the retURL customization). Because it's an action, you can branch to it, run it conditionally, or place it before a final screen — you are not limited to what happens only when the interview completes.

---

## Common Patterns

### Post-create redirect to the new record

**When to use:** a Screen Flow creates a record (Case, Opportunity, custom object) and the user should land on that record immediately afterward.

**How it works:** Create Records → store the new `recordId` → add an **Open a Page** action, set the target to that record, and set **Where to Open Page** to the location the user expects. Place it after the Create so the Id exists.

**Why not the alternative:** a custom `NavigationMixin` LWC works but is code you now own, test, and version; the native action is declarative and upgrade-safe.

### Open an external URL from a screen

**When to use:** the flow must send the user to an external system (a payment page, a partner portal, a document) using a URL the flow computed or fetched.

**How it works:** build the URL in a text/formula resource, then point an Open a Page action's target at it as an external web page and choose the open location.

**Why not the alternative:** the `force:navigateToURL` local action / retURL hack still works, but it's undocumented-feeling glue; the action is the supported path and keeps the URL logic in a named resource.

### Migrate a legacy redirect onto the native action

**When to use:** you find an existing Screen Flow that redirects via a custom LWC, a `navigateToUrl` local action, or a retURL formula.

**How it works:** confirm the flow is a Screen Flow, drop in an Open a Page action pointing at the same record/URL, verify the open location matches the old behavior, then remove the custom component/local action/URL hack and its now-dead variables.

**Why not the alternative:** keeping the homegrown redirect means maintaining code or a fragile URL string that the native action already covers.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Screen Flow should open a record or URL for the user | Native **Open a Page** action | Supported, declarative, no code to maintain |
| Need to land the user on a **specific related tab** of a record | Not available in the action today | It opens the record's default view (see IdeaExchange) — use a targeted URL/custom component if the related tab is mandatory |
| Need to **reuse/refresh the current page** (same view) | Not available today (no "Current Page" option) | Where to Open Page has no current-page option yet (IdeaExchange) — verify options in-org |
| Navigation needed from an autolaunched / record-triggered flow | Redesign so a **Screen Flow** owns the hand-off | Open a Page is a Screen Flow action; background flows have no UI to navigate |
| Rich, conditional, or reactive in-screen navigation UX | Custom LWC screen component (`NavigationMixin`) | The action covers common cases, not bespoke component behavior — see `flow/flow-screen-lwc-components` |
| Only need behavior when the interview **finishes** | Native action late in the flow, or documented finish-behavior | The action can run mid-flow; finish-URL/retURL only fires at completion |

---

## Recommended Workflow

1. **Confirm the surface.** Verify the flow is (or will be) a Screen Flow the user actively runs. If the trigger is background automation, redesign so a Screen Flow owns the navigation — the action can't fire without a UI.
2. **Pin the target.** Decide record vs. external URL, and make sure the value exists at that point in the flow (e.g. the record Id is populated after a Create). Store URLs in a named text/formula resource.
3. **Choose the open location.** Set **Where to Open Page** deliberately, and open the action in Flow Builder to read the actual option labels for your org — do not assume a "current page" / same-tab option exists.
4. **Place and (optionally) branch the action.** Add the Open a Page action where the navigation should occur; use a Decision before it if navigation is conditional.
5. **Retire any legacy redirect.** If you're migrating, remove the custom LWC / `navigateToUrl` local action / retURL formula and delete the variables it required, so two mechanisms don't fight.
6. **Validate against org constraints.** Test the record-access behavior (below), the open location on each surface the flow runs, and confirm the maturity/edition assumptions in a real Summer '26 org before promoting.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] The flow is a Screen Flow (it has screens); the action isn't sitting in a background flow that can't navigate
- [ ] The navigation target (record Id or URL) is guaranteed to be populated at the point the action runs
- [ ] **Where to Open Page** is set intentionally and its behavior was confirmed against the action's in-Builder options, not assumed
- [ ] Record-access reality is tested: navigating a user to a record they can't see shows an insufficient-access page, not the data
- [ ] Any legacy redirect (custom LWC / local action / retURL) being replaced is fully removed, along with its dead variables
- [ ] No GA/Beta/Pilot maturity claim is made that the action's release notes don't state
- [ ] The open location was verified on every surface the flow runs (desktop, and any Experience Cloud / mobile / console context)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **It's a Screen Flow action, not a universal navigator** — dropping the intent into an autolaunched or record-triggered flow gives the user nowhere to go; navigation requires a Screen Flow the user is running.
2. **It opens the record's default view only** — you can't target a specific related list / related tab, so "take them straight to the Contacts tab" is not achievable with the action alone (live IdeaExchange request).
3. **No "Current Page" open option (yet)** — Where to Open Page has no option to reuse the exact current page, so you can't declaratively "just refresh where the user already is" (live IdeaExchange request); verify the actual option set in Flow Builder.
4. **Navigation doesn't override record access** — opening a record only routes the browser; the record page still enforces sharing/FLS, so a user sent to a record they can't see gets an insufficient-access screen. Don't treat the action as a way to expose data.
5. **Maturity/edition specifics aren't fully pinned here** — the retrievable official pages didn't state GA/Beta/Pilot or edition availability for this action, and the Help reference renders as an app shell to fetchers; confirm in a Summer '26 org before committing.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Configured Open a Page action | A Screen Flow action set to open a record/URL with a deliberate Where to Open Page value |
| Navigation-design recommendation | Native action vs. custom LWC vs. finish behavior, with the reason from Decision Guidance |
| Legacy-redirect migration plan | Steps to replace a custom LWC / `navigateToUrl` local action / retURL hack and remove dead variables |
| `scripts/check_flow_open_a_page_action.py` output | Heuristic scan of Flow metadata flagging navigation in non-screen flows and legacy-redirect migration candidates |

---

## Related Skills

- `flow/screen-flows` — designing the Screen Flow itself (screens, navigation, validation, finish behavior) that this action lives inside.
- `flow/flow-screen-lwc-components` — the custom `NavigationMixin` screen component this action replaces for common cases; use it when you need bespoke or reactive navigation the action can't express.
- `flow/flow-for-experience-cloud` — runtime-surface differences and guest/external-user data-access safety to verify before relying on the action in an Experience site.
- `flow/flow-runtime-context-and-sharing` — the sharing/FLS boundary that still governs whether the user can actually see the record you navigate them to.
