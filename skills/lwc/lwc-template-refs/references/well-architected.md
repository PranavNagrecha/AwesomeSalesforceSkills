# Well-Architected Notes — LWC Template Refs

## Relevant Pillars

- **Reliability** — `lwc:ref` removes an entire class of flaky bugs where a CSS class rename or a lifecycle race silently broke a `querySelector`. Named refs make the DOM contract explicit in the template, and the compiler can enforce name presence far earlier than a runtime `null` check.
- **Performance** — A ref lookup is a direct name-to-element map resolved during render, not a CSS-selector walk of the shadow tree. For components that call into refs on every input event or render, that is measurably cheaper than `querySelector('.some-class')`. It also encourages keeping DOM access out of `connectedCallback`, which reduces first-paint work.
- **Operational Excellence** — Named refs give code reviewers and future maintainers a single grep-able vocabulary for "which elements does this component care about?" That turns tribal knowledge into observable structure. Combined with a checker script that flags refs-in-iterators and refs-in-`connectedCallback`, teams can run the migration across large component libraries with confidence.

## Architectural Tradeoffs

The main tradeoff is scope: `lwc:ref` intentionally covers only single, owned, non-iterated elements. Teams sometimes reach for one unified pattern across every DOM access — that is not what refs are for, and forcing them into iterators or cross-shadow reads creates worse bugs than the ones they replaced. The right architecture mixes: refs for single known elements, `data-*` + event delegation for per-row interactions inside `for:each`, and `@api`/events for cross-component contracts. Migration plans should preserve existing `querySelector` calls where refs cannot apply and focus the change on the high-value single-element cases.

The second tradeoff is lifecycle discipline: adopting refs pushes DOM work out of `connectedCallback` into `renderedCallback`, which is the correct LWC lifecycle but requires a small mental model shift for teams coming from React or older LWC codebases. The payoff is that the rest of the framework's guarantees (render batching, template diffing, reactive tracking) start working with you instead of against you.

## Anti-Patterns

1. **Ref inside a `for:each` or `iterator` template** — the framework does not support this. Using `data-*` attributes with event delegation (or `querySelectorAll` when a bulk read is truly needed) is the documented alternative.
2. **Accessing `this.refs` in `constructor` or `connectedCallback`** — refs are only populated after the first render. Move the access to `renderedCallback` and guard one-shot actions with a boolean flag.
3. **Mixing `lwc:ref` and a class-based `querySelector` for the same element during migration** — half-migrated components double the surface area a future maintainer has to understand. Finish the migration for that element or revert it; do not leave both pointing at the same node.

## Official Sources Used

- Create Components with Refs — https://developer.salesforce.com/docs/platform/lwc/guide/create-components-refs.html
- Reference Directives (`lwc:ref`) — https://developer.salesforce.com/docs/component-library/documentation/en/lwc/lwc.reference_directives
- Query Elements Owned By the Component — https://developer.salesforce.com/docs/platform/lwc/guide/create-components-dom-queries.html
- LWC Best Practices — https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
- Lightning Component Reference — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide
- LWC Data Guidelines — https://developer.salesforce.com/docs/platform/lwc/guide/data-guidelines.html
