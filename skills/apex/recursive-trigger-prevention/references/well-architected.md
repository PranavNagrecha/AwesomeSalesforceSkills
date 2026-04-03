# Well-Architected Notes — Recursive Trigger Prevention

## Relevant Pillars

### Reliability

Recursion bugs commonly surface as rollbacks, duplicate actions, or silently skipped work. Preventing them is primarily a reliability concern.

Tag findings as Reliability when:
- the same logical work executes multiple times unexpectedly
- an overbroad guard skips required processing
- trigger re-entry causes data corruption or duplicate side effects

### Scalability

Recursive behavior multiplies transaction cost and can explode SOQL, DML, and CPU usage.

Tag findings as Scalability when:
- self-DML amplifies limit consumption
- a broad guard was chosen because the volume behavior was not understood
- multi-record transactions behave unpredictably under recursion

### Operational Excellence

Teams need a shared, explainable recursion pattern instead of ad hoc static flags.

Tag findings as Operational Excellence when:
- recursion prevention logic is duplicated or inconsistent
- frameworks and handlers use different guard rules
- support teams cannot explain why some records were skipped

## Architectural Tradeoffs

- **Broad static guard vs narrow record-aware guard:** broad is quick, narrow is usually correct.
- **Delta check vs explicit recursion state:** delta checks remove unnecessary work, while guard state protects genuine self-DML loops.
- **Local fix vs framework fix:** centralized guards help large teams when a framework already exists.

## Anti-Patterns

1. **Global static Boolean** — suppresses more than the bug.
2. **Guard installed before root cause is known** — may hide the wrong issue.
3. **No distinction between valid re-entry and accidental loops** — correctness suffers.

## Official Sources Used

- Apex Developer Guide — trigger behavior and best-practice guidance
- Salesforce Well-Architected Overview — reliability, scalability, and operational framing
