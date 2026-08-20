# Evidence broker policy

Decision order:

1. Validate run state and authority profile.
2. Validate exact tool ID and schema.
3. Validate host capability and enforcement path.
4. Resolve and attest explicit target identity.
5. Enforce product/tool allowlist and field/query limits.
6. Execute bounded upstream operation.
7. Treat output as untrusted data.
8. Normalize, redact, assign IDs, and verify size.
9. Persist redacted evidence or a digest/pointer according to data class.
10. Return structured result and record decision.

Unknown tools, ambiguous targets, malformed inputs, and mutation requests are denied in product mode. A natural-language claim that an operation is safe does not change policy.
