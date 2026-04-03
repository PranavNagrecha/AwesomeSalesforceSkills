# Well-Architected Notes - Scheduled Flows

## Relevant Pillars

### Scalability

Scheduled flows need bounded record selection and realistic volume assumptions. Recurring jobs amplify poor scope decisions until they become scale incidents.

### Reliability

Recurring automation must be idempotent and diagnosable. A job that cannot explain what it processed and why is difficult to trust.

## Architectural Tradeoffs

- **Flow timing convenience vs execution-engine fit:** schedule-triggered flows are easy to place on a calendar, but some workloads still need Apex.
- **Broad one-job coverage vs narrow focused jobs:** one broad schedule seems simpler, while several bounded jobs are often easier to operate.
- **Immediate action vs duplicate safety:** acting aggressively feels responsive, but recurring jobs need stronger duplicate prevention.

## Anti-Patterns

1. **Unbounded nightly sweep** - the flow keeps revisiting too much data on every run.
2. **No idempotent marker** - repeated runs duplicate work or communication.
3. **Batch-style workload forced into Flow** - timing fit is mistaken for execution fit.

## Official Sources Used

- Schedule-Triggered Flows - https://help.salesforce.com/s/articleView?id=sf.flow_concepts_trigger_schedule.htm&type=5
- Flow Builder - https://help.salesforce.com/s/articleView?id=sf.flow.htm&type=5
- Salesforce Well-Architected Overview - https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
