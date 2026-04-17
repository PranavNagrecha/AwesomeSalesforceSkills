# LLM Anti-Patterns — Agent Action Error Handling

1. Rethrowing exceptions from an @InvocableMethod — the LLM cannot reason about framework errors.
2. Putting `ex.getMessage()` directly into user_message — leaks internals and breaks deterministic topic routing.
3. Using boolean `success` instead of a reason_code enum — the agent cannot distinguish retryable from terminal failures.
4. Writing one 'catch-all' branch and skipping per-exception-type classification — every error becomes SYSTEM_ERROR/UNKNOWN.
5. Omitting tests for each catch branch — coverage says 100% but failure paths were never asserted.
