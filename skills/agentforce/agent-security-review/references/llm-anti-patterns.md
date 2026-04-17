# LLM Anti-Patterns — Agent Security Review

1. Running the agent as the invoking user by default — privileged reviewers leak permissions upward.
2. Generic 'UpdateRecord' actions — any field becomes attack surface.
3. Skipping DMO classification — grounding becomes a data-leak vector.
4. No conversation retention — GDPR and eDiscovery gap.
5. Review as a PowerPoint, not a CMDT-backed checklist — drift is inevitable.
