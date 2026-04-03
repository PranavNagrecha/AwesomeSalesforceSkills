# OAuth Flow Decision Worksheet

## Identity Model

| Question | Answer |
|---|---|
| Inbound, outbound, or delegated? | |
| Human user context required? | Yes / No |
| Candidate flow | |
| Integration principal | |
| Scope set | |

## Operations

- Token lifetime:
- Rotation owner:
- Revoke runbook:
- IP/session policy:
- Monitoring signal:

## Guardrails

- [ ] Flow matches actor model
- [ ] No weak legacy fallback was accepted by habit
- [ ] Scopes are least privilege
- [ ] Principal permissions were reviewed separately from OAuth scopes
