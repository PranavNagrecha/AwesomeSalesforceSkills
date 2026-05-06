# Gotchas — LWC CSS and Styling

Non-obvious LWC styling behaviors that cause real production problems.

---

## Gotcha 1: Component CSS does not pierce the shadow DOM

```css
/* myComponent.css — does NOT work */
lightning-button .slds-button { background: red; }
```

`.slds-button` lives inside `lightning-button`'s shadow DOM. The
selector matches nothing. Use a styling hook
(`--slds-c-button-color-background`).

---

## Gotcha 2: `!important` does not bypass shadow DOM

A common false hope. `!important` only affects specificity within
the same stylesheet/scope. It does not let a parent's CSS reach
into a child's shadow DOM. The selector still doesn't match.

---

## Gotcha 3: Styling hooks cascade through shadow boundaries

CSS custom properties (`--slds-c-*`) are *inherited*, so they
cross the shadow boundary even though selectors don't. This is
the only sanctioned way to style base-component internals.

---

## Gotcha 4: `::part()` exposure is component-specific

Not every base component exposes parts. `lightning-button`
doesn't (yet). Check the Component Library's "Styling Hooks" tab
— if a component has parts, they're documented. Trying to use a
non-existent part name does nothing silently.

---

## Gotcha 5: Light DOM components forfeit encapsulation

`static renderMode = 'light'` lets external CSS reach in but
also lets external CSS *break* the component. A `.row` rule from
elsewhere in the app will hit yours. Use light DOM only for
small layout components; never for shared base components.

---

## Gotcha 6: Internal SLDS class names change between versions

Selectors like `.slds-modal__container.slds-modal__container_large`
or `.lightning-button-icon-stateful_button` are brittle — every
SLDS major version renames or restructures internal classes.
Hard-coded selectors silently stop working after a release.

---

## Gotcha 7: `:host` matches the host element, not the host's parent

`:host(.danger)` matches when the *consumer* adds
`class="danger"` on the component tag (`<c-card class="danger">`).
It does *not* match when an ancestor has the class. Use
`:host-context(.danger)` for ancestor matching — but be aware
that `:host-context` is not supported in every browser
(specifically Safari before 16.4).

---

## Gotcha 8: Inline `style="..."` bypasses the token cascade

Inline styles win the specificity battle but lose theme
participation. A user in High Contrast mode keeps your hardcoded
hex; a styling-hook would have switched to the high-contrast
variant. Reserve inline styles for runtime-computed values
(`style={dynamicWidth}`) only.

---

## Gotcha 9: Some base components ship CSS that overrides your host styles

Setting `:host { padding: 0; }` and then nesting a
`lightning-card` resets the card's internal padding. The card's
own CSS does not target `:host`, but the layout you imposed at
host level affects the card's box. Test in isolation and in
context.
