---
name: agentforce-prompt-versioning
description: "Version Prompt Templates and agent topic prompts: source-control shape, change review, model-version pinning, A/B, and rollback. Trigger keywords: prompt template versioning, prompt changelog, prompt rollback, A/B prompt test, agentforce prompt release. Does NOT cover: prompt engineering tips, general LLM fine-tuning, or Classify / Einstein Generate studio UI walkthroughs."
category: agentforce
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "version prompt templates"
  - "prompt template source control"
  - "prompt a/b test"
  - "prompt rollback plan"
  - "model version pinning agent"
tags:
  - agentforce
  - prompts
  - versioning
  - devops
inputs:
  - Prompt template inventory
  - Agent topic prompts
  - Model-version strategy (auto / pinned)
outputs:
  - Prompt versioning convention (naming, changelog)
  - Rollback plan per prompt
  - A/B harness for prompt variants
dependencies:
  - agentforce/agentforce-testing-strategy
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-23
---

# Agentforce Prompt Versioning

## Why Version Prompts

A prompt is executable config. Unversioned prompts produce unreproducible
behaviour, missed regressions, and "works for me" debugging.

## Source Of Truth

- Prompt Templates live as metadata. They can and should be
  source-controlled via SFDX retrieve.
- Store the templates under `force-app/main/default/genAiPromptTemplates/`
  (or the current metadata folder) in the repo.
- The repo is authoritative. UI edits are either imported back
  immediately or reverted.

## Naming And Version Strategy

- Base name reflects purpose: `RefundStatusSummary`.
- Version as a suffix on the Developer Name when the contract changes:
  `RefundStatusSummary_v2`.
- Backwards-compatible changes (prose tightening, minor tone) bump only
  the **Revision** field in metadata, not the name.
- Contract-breaking changes (variables added/renamed, expected JSON
  output shape altered) bump the name suffix.

## Changelog Convention

Keep a `PROMPTS_CHANGELOG.md` at repo root:

```text
## 2026-04-20 — RefundStatusSummary v3
- Added `brand_voice` variable for regional brand compliance.
- Removed filler "As an AI assistant..." preamble.
- Regenerated golden set (see evals PR #482).
- Rollout: ramp 10% → 50% → 100% over 5 days.
```

## Model Version Pinning

- Agentforce supports default and pinned model versions.
- For critical topics, **pin**. Auto-updates move behavior; pinning
  trades model improvements for reproducibility.
- Schedule quarterly re-evaluation: run goldens + adversarial against
  the newer model; upgrade once it meets the bar.

## A/B Strategy

- Prompt A/B works only when traffic distribution is controllable. Use
  topic fan-out: topic receives 10% to `_v3`, 90% to `_v2` for 48h.
- Metrics: routing accuracy, action precision, refund path completion,
  escalation rate.
- Kill switch: single metadata deploy flips all traffic back.

## Rollback

- Retain the last 2-3 prior versions as activated variants, even if
  traffic is 0%. Restoring is a traffic-split edit, not a redeploy.
- Post-incident, append to the changelog what rolled back and why.

## Recommended Workflow

1. Inventory prompt templates and assign owners.
2. Source-control under `force-app/.../genAiPromptTemplates/`.
3. Define naming convention and changelog format.
4. Pin model versions for critical topics.
5. Build A/B harness (topic-level traffic split).
6. Retain prior versions; document rollback procedure.
7. Review prompt/model quarterly against goldens.

## Official Sources Used

- Prompt Templates —
  https://help.salesforce.com/s/articleView?id=sf.prompt_builder_overview.htm
- Model Configuration —
  https://help.salesforce.com/s/articleView?id=sf.generative_ai_models.htm
- Agentforce Topics —
  https://help.salesforce.com/s/articleView?id=sf.einstein_agent_topics.htm
