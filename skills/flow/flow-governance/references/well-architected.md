# Well-Architected Notes - Flow Governance

## Relevant Pillars

### Operational Excellence

Governance is operational excellence applied to declarative automation. Names, owners, descriptions, and lifecycle rules make the flow estate operable under change.

## Architectural Tradeoffs

- **Fast local changes vs portfolio consistency:** local speed feels good until the automation inventory becomes unreadable.
- **Many versions retained vs active retirement:** keeping everything feels safer, but ambiguity has a real operational cost.
- **Flexible naming vs enforced naming:** free-form names reduce friction initially, but they weaken incident response and maintenance later.

## Anti-Patterns

1. **`Copy of ...` in production** - the portfolio signals implementation history instead of business purpose.
2. **Activation with no owner or rollback note** - support and release teams lose operational clarity.
3. **Descriptions treated as optional** - future maintainers have no concise operational context.

## Official Sources Used

- Flow Reference - https://help.salesforce.com/s/articleView?id=sf.flow_ref.htm&type=5
- Flow Builder - https://help.salesforce.com/s/articleView?id=sf.flow.htm&type=5
- Salesforce Well-Architected Overview - https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
