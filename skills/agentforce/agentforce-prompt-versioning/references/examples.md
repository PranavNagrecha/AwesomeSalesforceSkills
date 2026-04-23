# Prompt Versioning — Examples

## Example 1: Name And Metadata

```text
force-app/main/default/genAiPromptTemplates/
  RefundStatusSummary.genAiPromptTemplate-meta.xml           # v1 (retired)
  RefundStatusSummary_v2.genAiPromptTemplate-meta.xml        # current prod
  RefundStatusSummary_v3.genAiPromptTemplate-meta.xml        # A/B variant
```

## Example 2: Changelog Entry

```markdown
## 2026-04-20 — RefundStatusSummary v3

**Breaking:** added `brand_voice` variable.

### Motivation
Regional compliance team needs brand-voice switch for EU vs APAC.

### Rollout
- 2026-04-21: 10% traffic.
- 2026-04-23: 50% traffic.
- 2026-04-25: 100% traffic.
- 2026-05-01: retire v2.

### Metrics To Watch
- Routing accuracy (target ≥ 98%).
- Refund-path completion (target ≥ v2 baseline).
- Escalation rate (alert if +20% vs v2).

### Rollback Plan
Traffic flip back to v2 via topic config deploy. ETA 5 min.
```

## Example 3: Topic A/B Config

Topic `BillingInquiry` routing config:

```yaml
prompt_variants:
  - name: RefundStatusSummary_v2
    weight: 90
  - name: RefundStatusSummary_v3
    weight: 10
```

Weights changed by metadata deploy. Emits variant tag in telemetry.

## Example 4: Model Pinning

```xml
<modelVersion>gpt-4o-2024-08-06</modelVersion>
```

Explicit pin rather than `auto`. Quarterly review against goldens.

## Example 5: Retire Old Version

Retirement is a two-step:

1. Move traffic to 0% for 7 days. Monitor for any residual.
2. Delete from repo; deploy. Keep the changelog entry.

## Example 6: Retrieve From Org After UI Edit

```bash
sf project retrieve start \
  --metadata GenAiPromptTemplate \
  --target-org prod
```

Any divergence between the org and the repo must be reconciled within
the sprint.
