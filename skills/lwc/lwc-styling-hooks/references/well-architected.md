# Well-Architected Notes — LWC Styling Hooks

## Relevant Pillars

- **Operational Excellence** — SLDS Styling Hooks are Salesforce's public theming API. Using them instead of raw class overrides keeps theming predictable through SLDS releases, SLDS 2 migrations, and org-wide rebranding efforts, and keeps change management focused on one surface (the hook values) rather than scattered CSS rules.
- **Reliability** — Because hooks are a stable contract, themed UI keeps rendering correctly when Salesforce refactors base-component internals. Raw `.slds-*` class overrides do the opposite: they depend on private implementation details and fail silently on upgrade.
- **Performance** — Hook-based theming avoids DOM inspection workarounds (MutationObservers, querySelectorAll loops to restyle shadow-DOM descendants, repeated style injection) that accumulate runtime cost. A CSS custom property inherited through the tree costs essentially nothing compared to those patterns.

## Architectural Tradeoffs

The main tradeoff is between local control and theme cohesion. Setting a component hook on `:host` gives you precise control over one component's look, but if every LWC does that, the app loses a unified theme and rebranding becomes a codebase-wide CSS change. The healthier architecture sets global hooks (`--slds-g-*`) at the highest scope that carries brand intent — the site root, the app root, or the top-level page LWC — and uses component hooks (`--slds-c-*`) only for deliberate local deviations. That way a rebrand touches a small number of global declarations, and component-level overrides remain legible exceptions instead of the norm.

A second tradeoff is coverage vs. stability. Not every internal property is exposed as a hook; the set is deliberately smaller than "everything SLDS renders." Trying to push past the hook surface means re-entering the class-override trap. Accept the coverage limit, raise the gap to Salesforce when it matters, and keep theming inside the public API.

## Anti-Patterns

1. **Overriding raw `.slds-*` internal class names** — those class names are implementation detail, not a public API. Shadow DOM often blocks the selector, and when it doesn't, the next SLDS release (especially SLDS 2) can rename the class and silently break the theme.
2. **Hardcoded hex values inside LWC CSS instead of tokens** — a literal `#0b5cab` works until the brand changes, dark mode ships, or the site moves to Experience Cloud with a branded theme. Reference a `--slds-g-color-*` or `--slds-c-*` hook so the value travels with the theme.
3. **`!important` on hook declarations as a general override strategy** — this fights the cascade instead of using it, and blocks downstream deliberate overrides. Solve specificity problems by scoping the hook correctly, not by escalating priority.

## Official Sources Used

- LWC Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
- LWC CSS Custom Properties — https://developer.salesforce.com/docs/platform/lwc/guide/create-components-css-custom-properties.html
- LWC Theming — https://developer.salesforce.com/docs/platform/lwc/guide/create-components-theming.html
- SLDS Styling Hooks — https://lightningdesignsystem.com/platforms/lightning/styling-hooks/
- SLDS 2 (2e) — https://lightningdesignsystem.com/2e/
- SLDS Validator / SLDS Linter — https://developer.salesforce.com/docs/platform/lwc/guide/reference-slds-validator.html
- Lightning Component Reference — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide
