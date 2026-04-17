# LLM Anti-Patterns — Prompt Injection Defense

1. Relying on Trust Layer alone — it handles toxicity/PII, not business-policy bypass via tool coercion.
2. Adding ad-hoc instructions after incidents instead of maintaining a test suite.
3. Using a privileged user for agent execution — scope creep becomes a data-exposure vector.
4. Trusting agent-supplied arguments to Invocables — the attacker controls the agent's belief state.
5. Shipping multi-lingual agents tested only in English.
