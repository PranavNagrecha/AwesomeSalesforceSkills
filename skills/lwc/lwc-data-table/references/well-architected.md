# Well-Architected Notes - LWC Data Table

## Relevant Pillars

### Performance

Datatables concentrate rendering and interaction cost in one component. Stable keys, bounded page sizes, and controlled loading are essential to keep the browser responsive.

### User Experience

Users notice table quality immediately. Clear row actions, predictable selection, and trustworthy inline edit behavior make the table feel dependable instead of fragile.

## Architectural Tradeoffs

- **Inline edit speed vs save complexity:** in-grid editing is efficient for small changes, but it introduces draft-state and failure-path complexity.
- **One big result set vs progressive loading:** loading everything simplifies state at first, but it degrades responsiveness as volume grows.
- **Highly custom cells vs maintainability:** custom cell types can improve UX, but they add code paths and testing surface quickly.

## Anti-Patterns

1. **Index-based row identity** - the grid cannot maintain stable state across refresh or sort.
2. **Inline edit without a save contract** - users think data saved because the table changed locally.
3. **Infinite loading with no stop condition** - the component keeps accumulating rows until the page slows down.

## Official Sources Used

- lightning-datatable - https://developer.salesforce.com/docs/platform/lightning-component-reference/guide/lightning-datatable.html
- Best Practices for Development with Lightning Web Components - https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
- Data Guidelines - https://developer.salesforce.com/docs/platform/lwc/guide/data-guidelines.html
