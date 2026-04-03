# Well-Architected Notes — Callouts And HTTP Integrations

## Relevant Pillars

### Security

This skill directly affects secret management, endpoint governance, and remote-system identity. Named Credentials and External Credentials are security controls as much as convenience features.

Tag findings as Security when:
- tokens or endpoints are embedded in Apex
- org-wide versus per-user identity is unclear or misapplied
- outbound requests bypass the configured authentication boundary

### Reliability

Remote systems fail in ways Salesforce code cannot control. Timeout management, response classification, and post-commit boundaries are reliability concerns, not optional polish.

Tag findings as Reliability when:
- callout failures are silently swallowed
- triggers or save transactions perform fragile outbound work inline
- non-200 responses or malformed payloads are not classified explicitly

## Architectural Tradeoffs

- **Synchronous lookup vs async sync:** inline callouts can improve immediacy, but they increase user latency and transaction fragility.
- **Per-user identity vs org identity:** per-user auth can match the remote system more accurately, but it is operationally more complex.
- **Simple wrapper vs richer retry framework:** not every integration needs exponential backoff, but every integration needs explicit failure classification.

## Anti-Patterns

1. **Hardcoded endpoint and token management** — breaks environment portability and secret hygiene.
2. **Trigger-based direct callouts** — fragile and difficult to operate under transaction constraints.
3. **Happy-path-only integration code** — assumes success and treats non-200 or malformed responses as impossible.

## Official Sources Used

- Apex Developer Guide — HTTP request/response patterns and Named Credential callout guidance
- Named Credentials Help — external credential and identity model overview
- Salesforce Well-Architected Overview — security and reliability framing for integrations
