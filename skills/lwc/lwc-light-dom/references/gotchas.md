# Gotchas — LWC Light DOM

Non-obvious Salesforce platform behaviors that cause real production problems when you move a Lightning Web Component into light DOM.

## Gotcha 1: A Plain `<name>.css` File Is Global In Light DOM

**What happens:** A developer assumes that one CSS file next to a light-DOM component keeps its rules local, but those rules are compiled without any component-scoping attributes and leak to every element on the page that matches the selector. A broad rule like `button { padding: 16px }` now paints every button across the Experience Cloud site.

**When it occurs:** Any time a light-DOM component has a plain `<name>.css` file. The problem often hides in staging because only one such component exists; a second one with overlapping selectors ships later and the conflict surfaces in production.

**How to avoid:** Rename component-owned styles to `<name>.scoped.css`. The compiler injects synthesized per-component attribute selectors so the rules apply only inside this component. Reserve plain `<name>.css` for *intentional* global theming and give it distinctive selectors.

---

## Gotcha 2: Flipping An Existing Component's Render Mode Is A Breaking Change

**What happens:** A component used by many pages is switched from shadow to light (or vice versa) to unblock a single use case. Consumers see style regressions — things that were encapsulated are now inheriting page styles, or things that used to inherit no longer do — and some child interactions break.

**When it occurs:** Most often when a team retrofits light DOM onto a component that already shipped, without rolling out a new API version or parallel component.

**How to avoid:** Treat render mode as part of the public contract. Prefer creating a new variant (e.g. `faqAccordionLight`) rather than mutating the existing component in place, especially if the component is referenced across multiple pages, sites, or apps.

---

## Gotcha 3: Light DOM Does Not Disable Lightning Web Security

**What happens:** Developers assume that because the DOM is exposed, JavaScript is also "back to normal." They try to call APIs LWS blocks (certain globals, cross-realm mutations, specific third-party snippets) and the code fails silently or is rewritten by LWS.

**When it occurs:** Integrating analytics pixels, older third-party SDKs, or code that monkey-patches globals.

**How to avoid:** Confirm the library works under LWS before committing to light DOM. Render mode changes the DOM boundary, not the JS sandbox. If the library is incompatible with LWS, light DOM will not fix that.

---

## Gotcha 4: You Cannot Mix Render Modes Inside One Template

**What happens:** Someone adds `lwc:render-mode="light"` to a nested `<template>` tag (e.g. inside a `for:each`) hoping to make only one subsection light DOM. The compiler rejects it or ignores it — the root template's mode is the whole component's mode.

**When it occurs:** Attempting to partially migrate a large component, or trying to isolate a third-party integration to one slot.

**How to avoid:** Split the component. Keep the parent in whichever mode is appropriate, and create a child component whose *root* template uses the other mode. The boundary between parent and child is where render mode can change.

---

## Gotcha 5: Managed-Package Distribution Should Stay In Shadow DOM

**What happens:** An ISV ships a light-DOM component through a managed package. The package's CSS leaks into every consumer org's pages because the consumer cannot strip or rescope it after install. Support tickets accumulate across orgs.

**When it occurs:** When an ISV picks light DOM to unblock one consumer's styling request, without considering that every other consumer inherits the style leak.

**How to avoid:** Keep managed-package components in shadow DOM. Use styling hooks (CSS custom properties) across the shadow boundary to give consumers *controlled* theming access. Salesforce guidance is explicit on this point.

---

## Gotcha 6: Experience Cloud LWR vs Aura Sites Behave Differently

**What happens:** A team reads "use light DOM for Experience Cloud SEO" and applies it to an Aura-based Experience site. The crawler story is different there, the component target list is different, and the expected improvement does not show up.

**When it occurs:** Older Experience sites still built on the Aura template vs newer LWR sites.

**How to avoid:** Confirm the site template before deciding. Light DOM's strongest SEO and theming story is on LWR. For Aura-based sites, review the Experience Cloud docs for that template specifically and do not assume the same behavior.

---

## Gotcha 7: Exposed DOM Means Exposed XSS Surface If You Skip Sanitization

**What happens:** A light-DOM component binds user-supplied HTML via `lwc:dom="manual"` or by manipulating `innerHTML`, and the content is not sanitized. External tools, analytics, and accessibility helpers that now have DOM access are the same surface attackers can leverage.

**When it occurs:** Community-generated FAQ content, rich-text fields, or imported CMS HTML rendered into a light-DOM component.

**How to avoid:** Always sanitize user-provided HTML with DOMPurify (or an equivalent) before injecting it. Prefer binding plain text, not HTML, when you can. Review any place where content crosses into the component from outside the org's control.
