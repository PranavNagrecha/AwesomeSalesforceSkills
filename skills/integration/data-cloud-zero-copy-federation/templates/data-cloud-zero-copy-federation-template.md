# Data Cloud Zero Copy Federation — Work Template

Use this template when designing or troubleshooting a Lakehouse Federation against Snowflake, Databricks, BigQuery, or Redshift.

## Scope

**Skill:** `data-cloud-zero-copy-federation`

**Request summary:** (fill in what the user asked for)

## Context Gathered

- Source platform (Snowflake / Databricks / BigQuery / Redshift):
- Source object(s) and approximate row count / size:
- Source-side governance in scope (RLS, masking, authorized views):
- Latency tolerance (sub-second / minutes / hours):
- Source-warehouse cost ceiling and billing owner:
- Identity-resolution participation expected (yes / no):
- Schema-change SLA agreed with source-team owner (yes / no):

## Decision

| Question | Decision | Rationale |
|---|---|---|
| Federation vs physical ingestion? |  |  |
| Acceleration cache? |  |  |
| Cache refresh cadence? |  |  |
| IR keys to materialize? |  |  |
| Cross-connector joins involved? |  |  |

## Configuration Plan

- [ ] Source-side share / recipient / IAM / DB user provisioned with least-privilege grant
- [ ] Network path verified (PrivateLink / VPC peering / public endpoint)
- [ ] Lakehouse connector created in Data Cloud Setup
- [ ] External DLO(s) created and column scope reviewed
- [ ] DLO → DMO mapping documented
- [ ] Acceleration cache definition (filter, refresh) recorded
- [ ] Source-warehouse cost dashboard linked
- [ ] Auth-rotation entry added to credential calendar

## Review Checklist

(See SKILL.md "Review Checklist". Mirror items here and tick as you complete them.)

- [ ] Federation-vs-ingestion decision documented
- [ ] Source-side grant uses least privilege
- [ ] External DLO column scope minimized
- [ ] Cross-connector joins identified and resolved
- [ ] IR participation explicit (materialized keys vs full ingestion)
- [ ] Acceleration cache scope and refresh aligned to freshness need
- [ ] Source-warehouse cost ceiling and alerts set
- [ ] Source-side governance verified to enforce after federation
- [ ] Auth rotation runbook documented
- [ ] Schema-change protocol agreed with source team

## Operational Runbook

- Where is the federation principal's source-warehouse query log?
- Who owns the source share / recipient / IAM grant?
- What is the credential expiry date and rotation procedure?
- What is the procedure when the source-team announces a schema change?
- How is cache hit-rate monitored?

## Notes

(Record any deviations from the standard pattern and why.)
