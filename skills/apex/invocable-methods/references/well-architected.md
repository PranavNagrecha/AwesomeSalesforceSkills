# Well-Architected Notes — Invocable Methods

## Relevant Pillars

### Scalability

Invocable methods must remain bulk-safe even when the first Flow that uses them seems single-record.

Tag findings as Scalability when:
- queries or DML happen per input record
- the contract assumes one-request-at-a-time behavior
- wrapper shapes force multiple actions where one batch-safe action would do

### Operational Excellence

Well-designed invocable actions are understandable to Flow builders and easy to maintain.

Tag findings as Operational Excellence when:
- labels and descriptions are unclear
- the action contract is hard to evolve
- business logic is trapped inside the annotation class

### Reliability

Reliable actions expose predictable outcomes to their calling automations.

Tag findings as Reliability when:
- error behavior is ambiguous
- partial outcomes are needed but impossible to return
- invocable methods are hard to test or reuse

## Architectural Tradeoffs

- **Throwing exceptions vs returning structured results:** fail-fast simplicity versus richer orchestration behavior.
- **Simple parameter list vs wrapper DTOs:** fewer types initially versus long-term contract clarity.
- **Logic inline vs delegated to a service:** quicker start versus sustainable reuse.

## Anti-Patterns

1. **Single-record assumption in a list contract** — eventually fails at scale.
2. **Poor Flow-facing metadata** — builders cannot use the action confidently.
3. **Invocable class as business layer** — hard to reuse and evolve.

## Official Sources Used

- Apex Developer Guide — `@InvocableMethod` contract
- Flow Reference — Apex Action usage in Flow
- Salesforce Well-Architected Overview — scalability, reliability, and operational framing
