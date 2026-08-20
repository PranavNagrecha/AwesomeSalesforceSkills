# Product risk register

| Risk | Impact | Mitigation |
|---|---|---|
| Framework becomes another unimplemented specification | High | Reference kernel, requirement traceability, product-first milestones, delete unused schemas |
| Too many products reduce quality | High | Release cohorts; behavioral qualification for first three; beta labels for later products |
| Official Salesforce tooling overlaps product | Medium | Broker and interpret official tools; do not duplicate raw capabilities |
| Context packs become broad mandatory lists again | High | Hard budgets, telemetry, distractor tests, selection reasons |
| Subagents create latency without quality | Medium | Require isolated-context justification and compare against single-agent baseline |
| MCP annotations mistaken for security | Critical | Independent deny-by-default broker and host-specific enforcement |
| Wrong org or project selected | Critical | Explicit identity, pinning, ambiguity states, no silent defaults |
| Captured evidence leaks secrets/customer data | Critical | Classification, redaction, local retention defaults, secret scanning |
| Scratch QA mutates non-disposable org | Critical | Separate authority, Dev Hub guard, scratch-org identity proof, unconditional cleanup |
| Benchmark is gamed | High | Hidden scenarios, scenario rotation, hard evidence facts, external contribution review |
| Model/host updates silently change quality | High | Version capture, scheduled benchmark, regression thresholds |
| License blocks distribution strategy | High | Explicit licensing ADR before Marketplace/public package claims |
| Existing contributors reject new complexity | Medium | Preserve legacy paths; type on touch; simple contribution templates |
| Product claims exceed evidence | High | Independent reviewer, deterministic claim lint, public methodology |
