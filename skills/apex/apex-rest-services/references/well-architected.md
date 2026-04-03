# Well-Architected Notes — Apex REST Services

## Relevant Pillars

### Security

Custom REST endpoints expose Salesforce behavior to external callers, so sharing, CRUD/FLS, and contract design all carry security consequences.

Tag findings as Security when:
- the endpoint lacks explicit sharing or secure data access
- raw exceptions or sensitive fields are exposed
- caller identity assumptions are undocumented

### Reliability

Reliable REST contracts use explicit status codes, stable payloads, and clear versioning.

Tag findings as Reliability when:
- error handling is ambiguous
- incompatible changes are introduced without versioning
- resource classes perform too much logic inline

### Operational Excellence

APIs must be supportable. Stable contracts and clear logs reduce client-side confusion and operational toil.

Tag findings as Operational Excellence when:
- endpoint behavior is hard to diagnose
- resource classes are hard to test because of mixed concerns
- versioning and deprecation are undocumented

## Architectural Tradeoffs

- **Custom Apex REST vs standard APIs:** custom endpoints offer control but add maintenance and security surface.
- **Typed DTOs vs dynamic JSON:** typed requests are clearer and safer, but dynamic payloads can be flexible when contracts vary.
- **Inline logic vs service delegation:** inline code is faster to start and slower to operate later.

## Anti-Patterns

1. **Business logic embedded in the resource class** — transport and domain concerns become inseparable.
2. **No versioned contract** — external consumers become fragile.
3. **Status-code ambiguity** — clients cannot recover intelligently.

## Official Sources Used

- Apex Developer Guide — Apex REST and `@RestResource`
- REST API Developer Guide — API contract framing and HTTP semantics
- Salesforce Well-Architected Overview — security, reliability, and operational framing
