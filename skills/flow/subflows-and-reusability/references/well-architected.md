# Well-Architected Notes - Subflows And Reusability

## Relevant Pillars

### Operational Excellence

Subflows reduce duplicated maintenance when they encapsulate one clear reusable behavior. Good contracts make change safer and easier to reason about across the automation portfolio.

### Scalability

Reusable flow design helps only when the extracted child logic is also safe under load. Shared logic that is not bulk-safe merely spreads the same scale risk everywhere.

### Reliability

A stable child-flow contract improves predictability, while wide hidden side effects do the opposite. Failure handling at the parent boundary is part of reliability, not an optional add-on.

## Architectural Tradeoffs

- **Reuse vs indirection:** extracting common behavior improves consistency, but too much decomposition makes the end-to-end flow harder to follow.
- **Flow reuse vs Apex reuse:** Flow is approachable for declarative shared logic, while complex reusable behavior may need a more structured code boundary.
- **Narrow contracts vs future-proof flexibility:** exposing too many variables for hypothetical callers weakens the design today.

## Anti-Patterns

1. **Subflow as a hidden side-effect bundle** - the child flow mutates too much state to stay reusable.
2. **Contract sprawl through many generic variables** - callers cannot tell what the child flow really needs.
3. **Reuse used to dodge architectural review** - bulk, error, and transaction problems are merely moved, not solved.

## Official Sources Used

- Subflows - https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_subflow.htm&type=5
- Flow Builder - https://help.salesforce.com/s/articleView?id=sf.flow.htm&type=5
- Salesforce Well-Architected Overview - https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
