# V2 product portfolio

A product is a versioned user job with typed evidence, context, agents, tools, safety, output, and QA. The portfolio is deliberately smaller than the skill catalog.

| ID | Product | Stage | Command | Behavioral target |
|---|---|---|---|---|
| `P01` | [Deployment Failure Triage](P01-deployment-failure-triage.md) | release-candidate target | `/triage-deployment` | first-three scratch-qualified |
| `P02` | [Apex Test Failure Triage](P02-apex-test-failure-triage.md) | release-candidate target | `/triage-apex-tests` | first-three scratch-qualified |
| `P03` | [Access Path Explainer](P03-access-path-explainer.md) | release-candidate target | `/why-cant-user` | first-three scratch-qualified |
| `P04` | [Change Impact Planner](P04-change-impact-planner.md) | beta target | `/plan-metadata-change` | host-ready fixture-qualified |
| `P05` | [Automation Transaction Profiler](P05-automation-transaction-profiler.md) | beta target | `/profile-automation` | host-ready fixture-qualified |
| `P06` | [Release Readiness Review](P06-release-readiness-review.md) | beta target | `/review-release-readiness` | host-ready fixture-qualified |
| `P07` | [Security Posture Review](P07-security-posture-review.md) | beta portfolio | `/review-security-posture` | beta fixture-qualified |
| `P08` | [Integration Incident Triage](P08-integration-incident-triage.md) | beta portfolio | `/triage-integration` | beta fixture-qualified |
| `P09` | [Data Migration Reconciliation](P09-data-migration-reconciliation.md) | beta portfolio | `/reconcile-data-load` | beta fixture-qualified |
| `P10` | [Org Health Assessment](P10-org-health-assessment.md) | beta portfolio | `/assess-org-health` | beta fixture-qualified |
| `P11` | [Agentforce Quality Engineer](P11-agentforce-quality-engineer.md) | beta portfolio | `/review-agentforce-agent` | beta fixture-qualified |
| `P12` | [Multi-Org Drift Analysis](P12-multi-org-drift-analysis.md) | beta portfolio | `/compare-orgs` | beta fixture-qualified |

## Release cohorts

- **Release cohort:** P01–P03 must pass actual host and scratch-org known-truth QA before V2 stable.
- **Flagship expansion:** P04–P06 must be host-ready and fixture-qualified for the V2 release candidate.
- **Beta portfolio:** P07–P12 may ship as clearly labelled beta when end-to-end fixture paths and safety gates pass.

A product must not be promoted because its Markdown exists. Promotion requires the gates in its definition and SFAEF-190.
