# Well-Architected Notes — Agentforce PII Redaction

## Relevant Pillars

- **Security** — PII exposure in model context is the #1 Agentforce
  incident shape.
- **Operational Excellence** — centralised redaction + audit is an
  ongoing process, not a one-time config.
- **Reliability** — reproducible redaction is part of making agent
  behaviour predictable.

## Architectural Tradeoffs

- **Drop vs summarise:** drop is safest; summarise preserves useful
  signal at the cost of a new transformation to maintain.
- **Central boundary vs per-caller:** central is the only maintainable
  option at scale. Per-caller drift.
- **Input-side refuse vs redact:** refuse is safest; redact keeps the
  conversation flowing at slightly higher risk.

## Hygiene

- Field classification register in source control.
- Weekly audit review.
- Adversarial PII cases in eval suite.

## Official Sources Used

- Einstein Trust Layer —
  https://help.salesforce.com/s/articleView?id=sf.einstein_trust_layer.htm
- Data Masking For Generative AI —
  https://help.salesforce.com/s/articleView?id=sf.einstein_generative_ai_masking.htm
