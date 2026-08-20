# Core execution agents

These are framework roles, not a menu users must navigate. Default host packages expose only the subset required by shipped products.

- [`sf-intent-router`](core/sf-intent-router.md) — Route a user request to a product or catalog specialist without loading the corpus.
- [`sf-context-librarian`](core/sf-context-librarian.md) — Select the smallest relevant skill/reference set for one product stage.
- [`sf-project-inspector`](core/sf-project-inspector.md) — Discover and inspect an external Salesforce DX project as optional enrichment.
- [`sf-org-grounder`](core/sf-org-grounder.md) — Gather approved read-only Salesforce evidence and normalize it into evidence objects.
- [`sf-evidence-reviewer`](core/sf-evidence-reviewer.md) — Independently challenge draft claims, citations, contradictions, confidence, status, and unsafe advice.
- [`sf-policy-reviewer`](core/sf-policy-reviewer.md) — Validate the planned tools, authority, org/project scope, and host enforcement before execution.
- [`sf-run-resumer`](core/sf-run-resumer.md) — Rehydrate a checkpoint safely after compaction, restart, or explicit resume.
- [`sf-qa-grader`](core/sf-qa-grader.md) — Grade structured product output against versioned known truth and hard safety/evidence rules.

## Product agents


- [`deployment-failure-triager`](product/deployment-failure-triager.md) — Deployment Failure Triage
- [`apex-test-failure-triager`](product/apex-test-failure-triager.md) — Apex Test Failure Triage
- [`access-path-explainer`](product/access-path-explainer.md) — Access Path Explainer
- [`change-impact-planner`](product/change-impact-planner.md) — Change Impact Planner
- [`automation-transaction-profiler`](product/automation-transaction-profiler.md) — Automation Transaction Profiler
- [`release-readiness-reviewer`](product/release-readiness-reviewer.md) — Release Readiness Review
- [`security-posture-reviewer`](product/security-posture-reviewer.md) — Security Posture Review
- [`integration-incident-triager`](product/integration-incident-triager.md) — Integration Incident Triage
- [`data-migration-reconciler`](product/data-migration-reconciler.md) — Data Migration Reconciliation
- [`org-health-assessor-v2`](product/org-health-assessor-v2.md) — Org Health Assessment
- [`agentforce-quality-engineer`](product/agentforce-quality-engineer.md) — Agentforce Quality Engineer
- [`multi-org-drift-analyzer`](product/multi-org-drift-analyzer.md) — Multi-Org Drift Analysis

## Existing agents

The 76 current canonical agents are inventoried under `migration/catalogs/agents/`. Their migration profiles specify exposure, evidence, context, and QA expectations. Existing specialists remain catalog capabilities until a product demonstrates that native isolated execution improves quality.


## Machine authority contract

Each agent has both a human operating contract and a JSON definition. The machine definition declares:

- purpose, inputs, outputs, permissions, tools, and product ownership;
- an authority profile that cannot be expanded by user prose or another agent;
- required and prohibited evidence;
- context ceilings and the prohibition on transcript handoff;
- collaborators, failure modes, and honest default statuses;
- prompt principles and evaluation dimensions;
- whether completion requires independent review;
- recommended host exposure and the rationale for keeping the native surface small.

The generated [`CONTRACT_REFERENCE.md`](CONTRACT_REFERENCE.md) renders all 20 new framework/product agent contracts. Existing repository agents remain inventoried under `migration/catalogs/agents/` and are promoted into native execution only after a product and host test justify the isolation cost.
