# LLM Anti-Patterns — LWC CSS and Styling

Common mistakes AI coding assistants make when styling LWC components.

---

## Anti-Pattern 1: Selector targeting an SLDS internal class

**What the LLM generates.**

```css
lightning-button .slds-button { background: red !important; }
```

**Correct pattern.** Use a styling hook:

```css
.danger-button { --slds-c-button-color-background: red; }
```

The internal `.slds-button` selector cannot pierce the shadow
DOM. Worse, it ties the override to a class name that SLDS
renames between versions.

**Detection hint.** Any CSS rule whose selector starts with a
base-component tag and contains `.slds-` further on, especially
combined with `!important`.

---

## Anti-Pattern 2: `!important` to "fix" a selector that isn't matching

**What the LLM generates.**

```css
.my-card .slds-card__body { padding: 0 !important; }
```

**Correct pattern.** `!important` does not bypass shadow DOM. If
the rule isn't applying, the selector isn't matching at all.
Use `--slds-c-card-spacing-block` (if it exists) or a slot.

**Detection hint.** Any `!important` directly attached to a
`.slds-` internal class is fighting the wrong battle.

---

## Anti-Pattern 3: Hardcoded hex colors

**What the LLM generates.**

```css
.banner { background: #1589ee; color: #ffffff; }
```

**Correct pattern.**

```css
.banner {
    background: var(--slds-g-color-brand-base-50, #1589ee);
    color: var(--slds-g-color-neutral-100, #ffffff);
}
```

Hardcoded colors break High Contrast mode, ignore brand themes,
and never participate in dark-mode-style switching.

**Detection hint.** Any 6-character hex literal (`#[0-9a-f]{6}`)
in a `.css` file in a `lwc` directory, outside of a CSS comment.

---

## Anti-Pattern 4: Light DOM for shared base components

**What the LLM generates.**

```js
export default class MyButton extends LightningElement {
    static renderMode = 'light';
}
```

**Correct pattern.** Default shadow DOM. Use styling hooks for
external customization. Light DOM is for small layout helpers,
never for components that ship across multiple consumers.

**Detection hint.** Any `static renderMode = 'light'` on a
component named `*Button`, `*Card`, `*Input`, `*Picker`, or
shipped from a base library.

---

## Anti-Pattern 5: Inline `style="..."` for static values

**What the LLM generates.**

```html
<div style="padding: 1rem; background: #fff;">...</div>
```

**Correct pattern.**

```html
<div class="content-card">...</div>
```

```css
.content-card {
    padding: var(--slds-g-spacing-medium);
    background: var(--slds-g-color-neutral-100);
}
```

Inline styles bypass tokens and cannot be overridden by the
consumer.

**Detection hint.** Any `style="..."` whose value is a literal
constant (not a `{...}` template binding).

---

## Anti-Pattern 6: Using `/deep/` or `::shadow`

**What the LLM generates.**

```css
:host /deep/ .slds-button { ... }
```

**Correct pattern.** `/deep/`, `::shadow`, and `>>>` were
deprecated in 2017 and removed from all modern browsers. Use a
styling hook or `::part()`.

**Detection hint.** Any `/deep/`, `::shadow`, or `>>>` token in
an LWC CSS file.

---

## Anti-Pattern 7: Recreating SLDS spacing values as literals

**What the LLM generates.**

```css
.row { gap: 16px; padding: 12px 24px; }
```

**Correct pattern.**

```css
.row {
    gap: var(--slds-g-spacing-medium);
    padding: var(--slds-g-spacing-small) var(--slds-g-spacing-large);
}
```

The literals will go out of sync with SLDS rhythm the next time
the design system rolls a tweak. Tokens follow.

**Detection hint.** Any `[0-9]+(px|rem|em)` literal for spacing
in an LWC CSS file.
