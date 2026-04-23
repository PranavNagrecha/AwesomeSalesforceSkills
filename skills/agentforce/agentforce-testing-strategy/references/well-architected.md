# Well-Architected Notes — Agentforce Testing

## Relevant Pillars

- **Reliability** — without regression tests, every model / prompt
  change is a production experiment.
- **Security** — adversarial tests are the primary defence against
  prompt injection and PII leaks.
- **Operational Excellence** — unit + golden + adversarial + replay is
  an ongoing operating discipline, not one-time work.

## Architectural Tradeoffs

- **Deterministic routing tests vs full LLM runs:** routing tests are
  cheap and catch the bulk of regressions; LLM runs catch tone but cost
  more.
- **Small sharp golden set vs large exhaustive:** small wins — big sets
  are not run.
- **Human review vs full automation:** some dimensions (tone,
  appropriateness) still need humans.

## Hygiene

- Named owner for the eval suite.
- Dashboard visible to engineering + product.
- Quarterly prune.

## Official Sources Used

- Agentforce Overview —
  https://help.salesforce.com/s/articleView?id=sf.einstein_agent_overview.htm
- Testing Agents —
  https://help.salesforce.com/s/articleView?id=sf.einstein_agent_testing.htm
