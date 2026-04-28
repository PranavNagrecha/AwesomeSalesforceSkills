# Well-Architected Notes — LWC Shadow vs Light DOM Decision

This skill maps primarily to **Reliability**, **Performance**, and **Operational Excellence** in the Salesforce Well-Architected framework. The render-mode choice is a defensive-design decision: encapsulation is a load-bearing reliability property, and giving it up should be justified.

## Relevant Pillars

- **Reliability** — Shadow DOM's encapsulation is defense in depth against host-page CSS and JS regressions:
  - *Resilient* — a Shadow DOM component cannot be accidentally restyled by a global stylesheet rolled out by another team or by a Salesforce release. The component looks the same on every page it lands on. Light DOM gives that up by design — and that is the right tradeoff only when the page-wide consistency itself is the goal (LWR sites, corporate themes).
  - *Recoverable* — when a CSS regression DOES surface in production, a Shadow DOM component is easier to triage because the suspect surface is bounded (the component's own stylesheet). A Light DOM component can be impacted by any rule on any stylesheet on the page; the suspect surface is the entire CSS graph.
  - *Stable contracts* — design tokens (`--slds-*`) are an explicit theming contract: the child publishes the tokens it honours, the parent sets them. The contract survives refactors. Selector-based theming (which Light DOM enables) creates implicit dependencies that break when either side renames a class.

- **Performance** — render-mode has measurable performance characteristics:
  - *Light DOM is closer to native HTML rendering* — no shadow root attachment, no slot-resolution work at distribution time, slightly less memory per component. For a page with hundreds of small components (the LWR public-site case), this is non-trivial.
  - *Shadow DOM has slot-resolution cost* — slotted content is distributed (not moved), which involves additional bookkeeping. For a page with a few large components, this cost is invisible. For a page with dense composition, it adds up.
  - *Crawler indexing* — search-engine bots do not reliably index inside shadow roots. SEO-critical content on an LWR site that lives inside Shadow DOM components is effectively invisible. Light DOM is the corrective.

- **Operational Excellence** — the choice is operationally observable:
  - *Manageable* — a single sentence ("we are Light DOM because Bootstrap utility classes") in the component header makes the render-mode choice greppable, reviewable, and revisitable. Without that statement, the next developer either reverts the choice or duplicates it elsewhere without understanding why.
  - *Compliant* — managed-package distribution is a hard constraint (Shadow DOM only). Encoding that as a workflow step prevents discovery at packaging time, which is the worst time to discover it.
  - *Observable* — the checker flags drift between intent and implementation (Light DOM with `:host`, redundant `composed:false`, Shadow DOM components leaking global selectors). Drift is a leading indicator that the component has been edited without considering the render-mode contract.

## Architectural Tradeoffs

| Choice | Gains | Costs |
|---|---|---|
| **Shadow DOM (default)** | Encapsulation, defensive reliability, managed-package eligibility, design-token themability | Boundary blocks utility-class CSS frameworks; events need `composed: true`; ARIA cross-references don't cross roots; SEO crawlers may not index |
| **Light DOM** (`static renderMode = 'light'`) | Host CSS reaches in (utility frameworks work), DOM observable to crawlers and screen readers, simpler ARIA, events bubble naturally | No CSS encapsulation (every host-page rule can touch the component), forbidden in managed packages, requires `*.scoped.css` discipline for any component-local CSS, easier to break by a global rule rolled out by another team |
| **Hybrid (Shadow + design tokens)** | Encapsulation preserved, theme propagates through tokens, managed-package eligible | Requires upfront contract design (which tokens does the child honour); does not solve utility-framework cases; more upfront cost than either pure choice |

The Decision Guidance table in `SKILL.md` resolves these tradeoffs into per-scenario recommendations.

## Anti-Patterns

1. **"Default to Light DOM because Shadow DOM CSS is hard"** — gives up the encapsulation that was protecting the component from accidental host-page CSS regressions, and blocks future managed-packaging. The right move is to learn SLDS Styling Hooks and the design-token contract before reaching for Light DOM. Light DOM is for blockers, not for convenience.

2. **"Use Light DOM everywhere for consistency"** — turns every component into a globally-scoped CSS surface. A future global stylesheet rollout (corp re-brand, SLDS update, another team's component) can ripple across every page. The encapsulation guarantee disappears.

3. **"Mix render modes inside a single feature for taste"** — sibling LWCs in one feature using different render modes makes the CSS contract unpredictable: one is themed via tokens, the next via global selectors. Pick a stance per feature and document it.

4. **"Skip the blocker statement"** — without a single-sentence explanation in the component for why it is Light DOM, the next developer either reverts the choice (re-introducing the original blocker) or copies the choice to a new component without understanding why. The blocker statement is cheap and load-bearing.

## Official Sources Used

- **Create Light DOM Components** — <https://developer.salesforce.com/docs/platform/lwc/guide/create-light-dom-components.html> — canonical mechanics of `static renderMode = 'light'` and the template's `lwc:render-mode` attribute.
- **Style Light DOM Components** — <https://developer.salesforce.com/docs/platform/lwc/guide/style-light-dom-components.html> — defines the global-by-default behavior of Light DOM CSS and the `*.scoped.css` naming convention.
- **Migrate Shadow DOM Components to Light DOM** — <https://developer.salesforce.com/docs/platform/lwc/guide/migrate-shadow-dom-components-to-light-dom.html> — the migration playbook, including the `:host` removal step and the event-composition implications.
- **Best Practices for Development with Lightning Web Components** — <https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html> — render-mode guidance and the managed-package constraint.
- **Lightning Web Security Introduction** — <https://developer.salesforce.com/docs/platform/lwc/guide/security-lwsec-intro.html> — confirms LWS applies regardless of render mode.
- **Lightning Component Reference** — <https://developer.salesforce.com/docs/platform/lightning-component-reference/guide> — the base components used as theming targets via SLDS Styling Hooks (`--slds-c-*` tokens).
- **MDN — Shadow DOM and Custom Events `composed` flag** — <https://developer.mozilla.org/en-US/docs/Web/API/Event/composed> — the `composed: true` requirement for events to cross shadow roots, which Salesforce inherits as a Web Component standard.
