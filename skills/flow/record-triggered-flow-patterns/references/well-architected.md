# Well-Architected Notes — Record Triggered Flow Patterns

## Relevant Pillars

### Reliability

Choosing the right record-triggered pattern keeps transactions predictable and reduces accidental recursion or hidden side effects.

### Scalability

Before-save and after-save have very different scale characteristics, and the trigger model needs to fit the real record volume.

### Operational Excellence

Well-scoped entry criteria and explicit trigger context make record-triggered automation easier to reason about, debug, and hand over.

## Architectural Tradeoffs

- **Before-save efficiency vs after-save flexibility:** Before-save is cheaper, but after-save is necessary for committed side effects and related-record work.
- **Declarative speed vs code-level control:** Flow is easier to maintain for moderate logic, while Apex provides tighter orchestration for complex transaction behavior.
- **Broad starts vs explicit business events:** Broad starts are quicker to configure, but field-change-aware criteria produce more reliable automation.

## Anti-Patterns

1. **After-save used for simple same-record updates** — wastes DML and creates avoidable recursion risk.
2. **Record-triggered flows that run on every edit** — operationally noisy and harder to troubleshoot.
3. **Ignoring mixed automation on the same object** — the flow design fails because validation rules or Apex still shape the transaction.

## Official Sources Used

- Flow Reference — https://help.salesforce.com/s/articleView?id=sf.flow_ref.htm&type=5
- Flow Builder — https://help.salesforce.com/s/articleView?id=sf.flow.htm&type=5
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
