# Well-Architected Notes — LWC CSS and Styling

## Relevant Pillars

- **Operational Excellence** — SLDS styling hooks
  (`--slds-c-*`) and design tokens (`--slds-g-*`) are the
  contract Salesforce maintains across SLDS versions. Consuming
  components stay correct through version upgrades. Hand-rolled
  selectors against internal class names break silently every
  major release. Choosing hooks over selectors is the single
  largest reduction in styling-related regression bugs after an
  SLDS bump.
- **Performance** — CSS custom properties cascade through shadow
  DOM with no perceptible cost. `::part()` is similarly cheap.
  Light DOM forfeits the shadow-DOM optimizations that LWC's
  rendering layer relies on; only opt out when the styling
  capability is irreplaceable.

## Architectural Tradeoffs

The main tradeoff is **encapsulation vs styling reach**. Default
shadow DOM gives you encapsulation: nobody else's CSS can break
your component. Light DOM gives you reach: the consumer's global
CSS (and your own global CSS) can style your internals freely.

Specifically:

- **Reusable base component (Button, Card, Input)**: shadow DOM,
  styling hooks for variants.
- **App-internal layout helper**: light DOM is acceptable when
  styling is the dominant concern.
- **Page-level component embedded in Lightning Experience**:
  shadow DOM with `:host` + design tokens for the on-page theme.

When a styling need has no hook and no `::part()` exposure, the
escape hatch is a slot — let the consumer pass in the styled
element. This is cleaner than forcing into light DOM.

## Anti-Patterns

1. **Selectors against `.slds-*` internal classes.** Doesn't
   pierce shadow DOM; brittle across SLDS versions.
2. **`!important` to fight specificity battles.** Almost always
   the wrong tool.
3. **Hardcoded hex colors and pixel values.** Break themes and
   the SLDS rhythm.

## Official Sources Used

- SLDS Styling Hooks (CSS custom properties for base components) — https://www.lightningdesignsystem.com/platforms/lightning/styling-hooks/
- SLDS Design Tokens — https://www.lightningdesignsystem.com/design-tokens/
- LWC CSS (Lightning Web Components Developer Guide) — https://developer.salesforce.com/docs/platform/lwc/guide/create-components-css.html
- Light DOM (lwc:render-mode) — https://developer.salesforce.com/docs/platform/lwc/guide/create-light-dom.html
- ::part() (CSS Shadow Parts spec) — https://www.w3.org/TR/css-shadow-parts-1/
- Salesforce Well-Architected: Adaptable — https://architect.salesforce.com/well-architected/adaptable/composable
