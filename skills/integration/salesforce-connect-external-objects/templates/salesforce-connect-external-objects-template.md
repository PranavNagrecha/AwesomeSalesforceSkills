# Salesforce Connect Decision Worksheet

## Source System Fit

| Question | Answer |
|---|---|
| Source of truth must remain external? | |
| Protocol available | OData / Cross-org / Custom |
| Read-only or write requirement | |
| Latency tolerance | |
| Native reporting required | Yes / No |

## Platform Fit

- External object:
- Relationship model:
- Expected query patterns:
- Screens or reports that depend on it:
- Fallback if source unavailable:

## Guardrails

- [ ] Virtualization is justified over replication
- [ ] Feature limitations were validated
- [ ] Adapter ownership is explicit
- [ ] Page and query design respect external latency
