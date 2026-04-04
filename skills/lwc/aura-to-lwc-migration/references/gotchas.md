# Gotchas — Aura to LWC Migration

Non-obvious Salesforce platform behaviors that cause real production problems during Aura-to-LWC migration.

## Gotcha 1: LWC Cannot Natively Contain Aura Components

**What happens:** A developer migrates a parent component to LWC but the child component is still Aura. They add the Aura child tag (e.g., `<c-legacy-panel>`) directly to the LWC HTML template. The component deploys without error, but the Aura child never renders — it appears as an empty unknown HTML element in the DOM.

**When it occurs:** Any time a developer attempts to reference an Aura component from inside an LWC template. There is no compile-time warning; the failure is a silent runtime rendering omission.

**How to avoid:** Use the Aura wrapper pattern. Create a thin Aura component that wraps the legacy Aura child, and use the LWC-as-child-of-Aura direction (supported) to maintain communication. Alternatively, use Lightning Message Service for the LWC parent to communicate with the Aura component operating in a sibling slot on the same page. Plan to eliminate wrappers as part of the full migration.

---

## Gotcha 2: Shadow DOM Blocks Aura-Style Cross-Boundary Event Bubbling

**What happens:** A migrated LWC dispatches a `CustomEvent` with `bubbles: true` but without `composed: true`. The event bubbles up within the LWC's shadow tree but is stopped at the shadow root boundary and never reaches the parent Aura component or a higher LWC ancestor. Components that relied on Aura's tree-wide event propagation stop receiving events after migration.

**When it occurs:** Any `CustomEvent` dispatched from inside a child LWC component's shadow DOM that needs to be handled by a component outside the shadow root. This is particularly common when an Aura parent is still listening for bubbled child events during a partial migration.

**How to avoid:** Explicitly set `composed: true` on any `CustomEvent` that needs to cross shadow DOM boundaries: `new CustomEvent('myevent', { bubbles: true, composed: true, detail: payload })`. Document which events require `composed: true` in the migration audit. Be aware that `composed: true` also means the event propagates beyond the LWC's shadow boundary into the global DOM — validate that this is intentional.

---

## Gotcha 3: renderedCallback Fires on Every Re-Render, Not Just Initial Mount

**What happens:** A developer migrates Aura's `afterRender` hook to LWC's `renderedCallback` and places third-party library initialization (e.g., a charting library, a drag-and-drop library) directly inside it. The library initializes correctly on first render, but every subsequent reactive property change triggers `renderedCallback` again, causing duplicate initialization, multiple event listener registrations, and DOM corruption.

**When it occurs:** Any time `renderedCallback` contains imperative DOM manipulation or library setup without a guard against repeated execution.

**How to avoid:** Guard with a boolean flag:
```javascript
hasRendered = false;

renderedCallback() {
    if (this.hasRendered) return;
    this.hasRendered = true;
    // one-time initialization here
}
```
Also note: unlike Aura's `afterRender`, LWC's `renderedCallback` is called even during server-side rendering (SSR) in some contexts. Use `this.template.querySelector` defensively.

---

## Gotcha 4: Aura Value Providers Have No LWC Equivalent

**What happens:** Aura components access global value providers like `$Browser`, `$Label`, `$Resource`, `$ContentAsset`, and `$Locale` directly in component expressions (e.g., `{!$Browser.isPhone}`). After migration, developers attempt to use the same value provider syntax in LWC templates. LWC template expressions do not support `$` value providers — the syntax is simply not parsed, and expressions render blank or throw template compilation errors.

**When it occurs:** Any Aura component that uses `$Browser`, `$Label`, `$Resource`, or `$ContentAsset` in its markup or controller.

**How to avoid:** Use LWC-native equivalents:
- `$Label.c.MyLabel` → `import LABEL from '@salesforce/label/c.MyLabel'`
- `$Resource.myResource` → `import RESOURCE from '@salesforce/resourceUrl/myResource'`
- `$Browser.isPhone` → `import { CurrentPageReference } from 'lightning/navigation'` or use `window.navigator.userAgent` / `formFactor` from `@salesforce/client/formFactor`
- `$ContentAsset.myAsset` → `import ASSET from '@salesforce/contentAssetUrl/myAsset'`

---

## Gotcha 5: Component Event Payload Access Differs Between Aura and LWC

**What happens:** In Aura, event parameters are accessed via `event.getParam('paramName')`. After migration, the developer copies this pattern into LWC event handler code. `event.getParam` is undefined in LWC's standard DOM events and throws a TypeError, silently breaking the handler in some cases or causing an unhandled exception in others.

**When it occurs:** Any event handler method that reads Aura-style event parameters using `event.getParam()` or `event.getParams()`.

**How to avoid:** In LWC, `CustomEvent` payloads live on `event.detail`. Replace all `event.getParam('fieldName')` with `event.detail.fieldName`. When migrating, search the entire codebase for `.getParam(` and `.getParams(` as a migration completeness check.

---

## Gotcha 6: Aura Component Events Require Explicit Registration — LWC Does Not

**What happens:** Aura requires explicit `<aura:registerEvent>` declarations in component markup before a component can fire a component event. Developers sometimes carry this habit into LWC and add comment blocks or attempt to declare event types in the HTML template. LWC requires no event registration — `dispatchEvent` works without any declaration. However, this also means there is no compile-time enforcement of the event contract. Typos in event names (`onAccountSelected` vs `onaccountselected`) are the leading cause of silent handler failures after migration.

**When it occurs:** Every LWC migration where the developer forgets that LWC event names in template attributes must be all lowercase.

**How to avoid:** LWC event names must be lowercase in both the `CustomEvent` constructor string and the template `on<eventname>` attribute. `new CustomEvent('accountSelected')` and `onaccountSelected` in the template will NOT work — only `new CustomEvent('accountselected')` and `onaccountselected` are valid. Add a linting rule or grep for camelCase event names in CustomEvent constructors as a post-migration quality gate.
