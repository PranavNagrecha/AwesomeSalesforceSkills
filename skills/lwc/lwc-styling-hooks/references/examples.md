# Examples — LWC Styling Hooks

## Example 1: Theming A `lightning-button-group` At Component Scope

**Context:** A custom LWC renders a `lightning-button-group` for a toolbar. Product design wants this one toolbar's buttons to use an accent color that differs from the app-wide brand, without changing any other button on the page.

**Problem:** The developer's first instinct is to target `.slds-button_brand` or `.slds-button` with a CSS selector. In a shadow-DOM LWC those selectors never reach inside `lightning-button`, so nothing happens; in a rare light-DOM case they might apply, but they break silently when SLDS renames the internal class.

**Solution:**

```css
/* myToolbar.css — shadow-DOM LWC */
:host {
    --slds-c-button-color-background: var(--slds-g-color-accent-info-base-50);
    --slds-c-button-text-color: var(--slds-g-color-on-accent-info-base-50);
    --slds-c-button-color-background-hover: var(--slds-g-color-accent-info-base-60);
}
```

```html
<!-- myToolbar.html -->
<template>
    <lightning-button-group>
        <lightning-button variant="brand" label="Save"></lightning-button>
        <lightning-button variant="brand" label="Submit"></lightning-button>
    </lightning-button-group>
</template>
```

**Why it works:** CSS custom properties inherit through the shadow DOM. The `lightning-button` implementation reads `--slds-c-button-color-background` from its own root, and because the value is set on the parent LWC's `:host`, it inherits in. The base component's internal class names never get referenced, so the theme survives SLDS upgrades and SLDS 2 migration unchanged.

---

## Example 2: Experience Cloud Brand Override At The Site Root

**Context:** An Experience Cloud site needs a brand color that propagates to every base component — buttons, cards, inputs, badges — without per-component CSS and without hand-editing the theme file for each variant.

**Problem:** Teams often branch into per-component hook overrides (`--slds-c-button-color-background` here, `--slds-c-card-color-background` there) and end up with dozens of scattered declarations that drift out of sync when the brand tweaks.

**Solution:**

```css
/* siteRoot.css — applied at the highest LWC scope in the site */
:host {
    /* Global brand anchor and semantic neighbors */
    --slds-g-color-brand-base-50: #0b5cab;
    --slds-g-color-brand-base-60: #094a8a;
    --slds-g-color-brand-base-40: #2e7ed0;

    /* On-brand text for contrast on brand surfaces */
    --slds-g-color-on-brand: #ffffff;

    /* Semantic border neighbor so borders pick up the brand hue */
    --slds-g-color-border-brand-1: var(--slds-g-color-brand-base-50);
}
```

**Why it works:** `--slds-g-*` hooks are the documented public API for brand and semantic color. Setting them at the site root cascades through every descendant base component that consumes those tokens. There is no per-component CSS, no hardcoded hex inside any individual LWC, and the brand can be swapped by editing one block.

---

## Anti-Pattern: Overriding Internal SLDS Classes

**What practitioners do:**

```css
/* DO NOT DO THIS */
.my-btn .slds-button_brand {
    background: #123456 !important;
    color: #ffffff !important;
}
```

**What goes wrong:**

- In shadow-DOM LWCs the selector never crosses the shadow boundary, so the rule silently does nothing.
- Even when it does apply, `.slds-button_brand` is an internal SLDS implementation detail, not a public API. A later SLDS release can rename or restructure that class and the override disappears.
- `!important` on a raw-class override fights the cascade instead of using it; when you later try to add a hook-based theme on top, the `!important` rule blocks it and you're stuck debugging specificity.
- SLDS 2 (2e) is specifically calling out this pattern — SLDS Validator / SLDS Linter flag it because raw class overrides are the single biggest source of migration breakage.

**Correct approach:** Replace the class override with the corresponding styling hook:

```css
:host {
    --slds-c-button-color-background: #123456;
    --slds-c-button-text-color: #ffffff;
}
```

Better still, reference a semantic token so the color stays in sync with the rest of the theme:

```css
:host {
    --slds-c-button-color-background: var(--slds-g-color-brand-base-50);
    --slds-c-button-text-color: var(--slds-g-color-on-brand);
}
```
