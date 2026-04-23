# Agentforce Cost Optimization — Gotchas

## 1. Trust Layer Adds Tokens

Masking, citation, and guardrail passes all consume tokens. Measure total cost, not just model cost.

## 2. Grounding Boilerplate

Knowledge article footers, legal disclaimers, templated headers all get indexed and retrieved. Strip them before indexing.

## 3. Tool Output Is Always Counted

The agent paying for tool output tokens even if it ignores them. Project the fields you need.

## 4. Managed Topic Opacity

Managed-package topics may have opaque instruction length. Audit via runtime logs, not via the UI.

## 5. Model Tier Changes Quality

Switching tiers without A/B evaluation is risky. Quality regressions are subtle and discovered slowly.
