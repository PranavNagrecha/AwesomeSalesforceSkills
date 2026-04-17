# LLM Anti-Patterns — Agent Rate Limit Strategy

1. Trusting Agentforce to rate-limit for you — it only fails loudly on hard limits.
2. Hard-coded tokens/minute without per-persona CMDT — cannot respond to traffic shifts.
3. Synchronous ledger DML per turn — blows DML limits.
4. No fallback UX — users see 503s.
5. No dashboard — SRE is blind to exhaustion until a user complains.
