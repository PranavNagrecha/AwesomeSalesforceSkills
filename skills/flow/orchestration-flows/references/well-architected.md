# Well-Architected Notes — Orchestration Flows

## Relevant Pillars

### Reliability

Long-running business processes need recoverability, clear ownership, and predictable step transitions. Orchestration helps only when those concerns are designed deliberately.

### Scalability

Flow Orchestration supports scaling a process across users and time, but too much human interaction or too many tiny stages can become its own scalability problem.

### Operational Excellence

Monitoring, reassignment, and stuck-instance handling are central to the value of orchestration. This is an operations-heavy design surface.

## Architectural Tradeoffs

- **Operational visibility vs implementation overhead:** Orchestration provides monitoring value, but only for processes complex enough to justify it.
- **More interactive work vs more automation:** Human steps improve control, but they also create backlog and queue-management needs.
- **Stage granularity vs clarity:** Too many stages make monitoring noisy, while too few hide ownership transitions.

## Anti-Patterns

1. **Using orchestration for ordinary synchronous automation** — unnecessary complexity when a standard Flow would do.
2. **Stage explosion** — every tiny action becomes a milestone, making monitoring harder instead of easier.
3. **Launching human work with no operational owner** — the orchestration is technically running but no team is accountable.

## Official Sources Used

- Flow Reference — https://help.salesforce.com/s/articleView?id=sf.flow_ref.htm&type=5
- Flow Builder — https://help.salesforce.com/s/articleView?id=sf.flow.htm&type=5
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
