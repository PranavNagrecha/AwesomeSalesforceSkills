# Platform Events Design Worksheet

## Event Decision

| Question | Answer |
|---|---|
| Is this a business event or a row-change event? | |
| Platform Event or CDC? | |
| Publisher | |
| Consumer(s) | |
| Replay-aware external subscriber needed? | Yes / No |

## Payload Design

- Event fields:
- Required identifiers:
- Correlation ID strategy:
- PII or sensitive data excluded:

## Guardrails

- [ ] Publishers bulk-publish rather than publishing in loops
- [ ] Publish results are checked and logged
- [ ] Apex subscriber trigger is thin
- [ ] External replay responsibility is documented when applicable
- [ ] Event schema represents business intent, not an accidental object snapshot
