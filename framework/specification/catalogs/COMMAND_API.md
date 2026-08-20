# Command API reference

Generated from `commands/specs/*.json`. Do not edit manually.

## `/assess-org-health`

Produce an evidence-backed, prioritized Salesforce health roadmap across Trusted, Easy, and Adaptable dimensions without reducing the org to a superficial score.

- Product: `P10`
- Version: `0.9.0`
- Agents: `sf-context-librarian`, `sf-project-inspector`, `sf-org-grounder`, `org-health-assessor-v2`, `sf-evidence-reviewer`
- Tools: `get_org_snapshot_manifest`, `get_automation_inventory`, `get_user_access_evidence`, `get_code_analysis_result`, `get_limits_snapshot`
- Permissions: `repository.read`, `knowledge.read`, `local_reports.write`, `salesforce.read`
- Terminal statuses: `completed`, `partial`, `refused`, `failed`

| Argument | Type | Required | Description |
|---|---|---|---|
| target_org | string | False | Explicit read-only org |
| assessment_scope | string | False | Full or selected architecture dimensions |
| evidence_bundle | string | False | Captured snapshot for offline mode |
| business_context | string | False | Critical processes, compliance, release cadence |

## `/compare-orgs`

Compare two explicit Salesforce org snapshots and distinguish expected environmental differences from dangerous deployment or configuration drift.

- Product: `P12`
- Version: `0.9.0`
- Agents: `sf-context-librarian`, `sf-project-inspector`, `sf-org-grounder`, `multi-org-drift-analyzer`, `sf-evidence-reviewer`
- Tools: `get_org_snapshot_manifest`, `compare_org_snapshots`, `describe_salesforce_component`, `get_component_dependency_evidence`
- Permissions: `repository.read`, `knowledge.read`, `local_reports.write`, `salesforce.read`
- Terminal statuses: `completed`, `partial`, `refused`, `failed`

| Argument | Type | Required | Description |
|---|---|---|---|
| left_org_or_snapshot | string | True | Explicit org alias or captured snapshot |
| right_org_or_snapshot | string | True | Explicit org alias or captured snapshot |
| scope | string | False | Metadata types, packages, settings, permissions, or components |
| difference_policy | string | False | Expected-difference rules |

## `/plan-metadata-change`

Before I change or retire Salesforce metadata, identify direct and transitive impact, deployment order, tests, permissions, data implications, and rollback constraints.

- Product: `P04`
- Version: `0.9.0`
- Agents: `sf-context-librarian`, `sf-project-inspector`, `sf-org-grounder`, `change-impact-planner`, `sf-evidence-reviewer`
- Tools: `get_component_dependency_evidence`, `describe_salesforce_component`, `get_org_snapshot_manifest`, `get_code_analysis_result`
- Permissions: `repository.read`, `knowledge.read`, `local_reports.write`, `salesforce.read`
- Terminal statuses: `completed`, `partial`, `refused`, `failed`

| Argument | Type | Required | Description |
|---|---|---|---|
| component | string | True | Canonical metadata component identity |
| proposed_change | string | True | Typed change such as add/rename/delete/type-change/activate/deactivate |
| project_path | string | False | Salesforce DX project |
| target_org | string | False | Read-only org for deployed-state evidence |
| scope | string | False | Package, application, or explicit roots |

## `/profile-automation`

Show what Salesforce automation executes for an object operation, in what order, where recursion/DML/limit risk exists, and which automation should be consolidated.

- Product: `P05`
- Version: `0.9.0`
- Agents: `sf-context-librarian`, `sf-project-inspector`, `sf-org-grounder`, `automation-transaction-profiler`, `sf-evidence-reviewer`
- Tools: `get_automation_inventory`, `get_component_dependency_evidence`, `describe_salesforce_component`, `get_apex_test_run`
- Permissions: `repository.read`, `knowledge.read`, `local_reports.write`, `salesforce.read`
- Terminal statuses: `completed`, `partial`, `refused`, `failed`

| Argument | Type | Required | Description |
|---|---|---|---|
| object | string | True | Object API name |
| operation | string | True | insert/update/delete/undelete or supported business event |
| scenario | string | False | Changed fields, entry conditions, user context, volume |
| project_path | string | False | Local project |
| target_org | string | False | Read-only org |

## `/reconcile-data-load`

Explain whether a Salesforce data migration reconciled, where records or relationships were lost/changed, and which deterministic checks should be performed next.

- Product: `P09`
- Version: `0.9.0`
- Agents: `sf-context-librarian`, `sf-project-inspector`, `sf-org-grounder`, `data-migration-reconciler`, `sf-evidence-reviewer`
- Tools: `get_data_load_result`, `run_bounded_read_query`, `get_org_identity`, `describe_salesforce_component`
- Permissions: `repository.read`, `knowledge.read`, `local_reports.write`, `salesforce.read`
- Terminal statuses: `completed`, `partial`, `refused`, `failed`

| Argument | Type | Required | Description |
|---|---|---|---|
| migration_manifest | string | True | Source/transform/load definitions and expected counts |
| result_files | string | True | Load success/error/reject outputs |
| target_org | string | False | Read-only count/sample queries |
| mapping_file | string | False | Field/object mapping |

## `/review-agentforce-agent`

Review an Agentforce agent, topics/subagents, actions, grounding, guardrails, tests, and implementation dependencies for correctness, safety, and release readiness.

- Product: `P11`
- Version: `0.9.0`
- Agents: `sf-context-librarian`, `sf-project-inspector`, `sf-org-grounder`, `agentforce-quality-engineer`, `sf-evidence-reviewer`
- Tools: `get_agentforce_test_result`, `describe_salesforce_component`, `get_code_analysis_result`, `get_flow_test_result`
- Permissions: `repository.read`, `knowledge.read`, `local_reports.write`, `salesforce.read`
- Terminal statuses: `completed`, `partial`, `refused`, `failed`

| Argument | Type | Required | Description |
|---|---|---|---|
| agent_metadata_path | string | True | Retrieved Agentforce metadata path |
| agent_developer_name | string | True | Explicit agent identity |
| target_org | string | False | Read-only org for action implementations/test results |
| review_depth | string | False | overview/topics/actions/full |

## `/review-release-readiness`

Given a release scope, tell me whether it is ready, what blocks it, what should be tested or sequenced, and what evidence is still missing.

- Product: `P06`
- Version: `0.9.0`
- Agents: `sf-context-librarian`, `sf-project-inspector`, `sf-org-grounder`, `release-readiness-reviewer`, `sf-evidence-reviewer`
- Tools: `get_deployment_result`, `get_apex_test_run`, `get_code_analysis_result`, `get_component_dependency_evidence`, `get_org_snapshot_manifest`, `get_flow_test_result`
- Permissions: `repository.read`, `knowledge.read`, `local_reports.write`, `salesforce.read`
- Terminal statuses: `completed`, `partial`, `refused`, `failed`

| Argument | Type | Required | Description |
|---|---|---|---|
| release_scope | string | True | Manifest, Git diff/range, package directory, or structured change list |
| project_path | string | False | Salesforce DX project |
| target_org | string | False | Read-only validation target |
| risk_tolerance | string | False | Conservative/default/aggressive with explicit policy |

## `/review-security-posture`

Assess a Salesforce scope for evidence-backed access, code, session, integration, data, and configuration risks, prioritized by exploitability and business impact.

- Product: `P07`
- Version: `0.9.0`
- Agents: `sf-context-librarian`, `sf-project-inspector`, `sf-org-grounder`, `security-posture-reviewer`, `sf-evidence-reviewer`
- Tools: `get_code_analysis_result`, `get_user_access_evidence`, `get_org_snapshot_manifest`, `get_integration_config_summary`, `describe_salesforce_component`
- Permissions: `repository.read`, `knowledge.read`, `local_reports.write`, `salesforce.read`
- Terminal statuses: `completed`, `partial`, `refused`, `failed`

| Argument | Type | Required | Description |
|---|---|---|---|
| scope | string | True | Org, project, package, object set, or security domain |
| project_path | string | False | Local project |
| target_org | string | False | Read-only org |
| policy_profile | string | False | Framework default or approved organization policy |

## `/sfskills-capabilities`

List products, modes, hosts, prerequisites, and qualification status from canonical definitions.

- Product: `framework`
- Version: `0.9.0`
- Agents: none
- Tools: none
- Permissions: `repository.read`
- Terminal statuses: `completed`, `failed`

| Argument | Type | Required | Description |
|---|---|---|---|
| filter | string | False |  |

## `/sfskills-doctor`

Inspect local framework, host, plugin, MCP, Salesforce CLI, org aliases, index, schemas, and generated-artifact health.

- Product: `framework`
- Version: `0.9.0`
- Agents: none
- Tools: none
- Permissions: `repository.read`, `shell.read_only`
- Terminal statuses: `completed`, `partial`, `failed`

## `/sfskills-explain-route`

Explain which product or specialist would handle a request and why, without executing it.

- Product: `framework`
- Version: `0.9.0`
- Agents: none
- Tools: none
- Permissions: `repository.read`, `knowledge.read`
- Terminal statuses: `completed`, `partial`, `refused`

| Argument | Type | Required | Description |
|---|---|---|---|
| request | string | True |  |

## `/sfskills-qa-run`

Run fixture or protected scratch QA for selected products/scenarios.

- Product: `framework`
- Version: `0.9.0`
- Agents: none
- Tools: none
- Permissions: `repository.read`, `local_reports.write`
- Terminal statuses: `completed`, `partial`, `refused`, `failed`

| Argument | Type | Required | Description |
|---|---|---|---|
| lane | enum | True |  |
| scenario | string | False |  |

## `/sfskills-replay`

Replay a redacted run bundle offline or validate whether live refresh is required.

- Product: `framework`
- Version: `0.9.0`
- Agents: none
- Tools: none
- Permissions: `repository.read`, `local_reports.write`
- Terminal statuses: `completed`, `partial`, `refused`, `failed`

| Argument | Type | Required | Description |
|---|---|---|---|
| run_bundle | path | True |  |
| live_refresh | boolean | False |  |

## `/sfskills-validate-run`

Validate schemas, evidence links, policy, status, and review integrity for a run bundle.

- Product: `framework`
- Version: `0.9.0`
- Agents: none
- Tools: none
- Permissions: `repository.read`
- Terminal statuses: `completed`, `failed`

| Argument | Type | Required | Description |
|---|---|---|---|
| run_bundle | path | True |  |

## `/triage-apex-tests`

Explain why an existing Apex test run failed, identify shared root causes across methods, and propose the smallest evidence-backed fix and regression plan.

- Product: `P02`
- Version: `0.9.0`
- Agents: `sf-context-librarian`, `sf-project-inspector`, `sf-org-grounder`, `apex-test-failure-triager`, `sf-evidence-reviewer`
- Tools: `get_apex_test_run`, `get_org_identity`, `describe_salesforce_component`, `get_automation_inventory`, `get_code_analysis_result`
- Permissions: `repository.read`, `knowledge.read`, `local_reports.write`, `salesforce.read`
- Terminal statuses: `completed`, `partial`, `refused`, `failed`

| Argument | Type | Required | Description |
|---|---|---|---|
| test_run_id | string | False | Existing Apex test run ID |
| target_org | string | False | Explicit org alias/username for live retrieval |
| result_file | string | False | Captured test-result JSON |
| project_path | string | False | External Salesforce DX project |
| method_limit | string | False | Bounded page size |

## `/triage-deployment`

Tell me why this Salesforce deployment failed, group downstream symptoms under likely shared causes, and give me the safest remediation order.

- Product: `P01`
- Version: `0.9.0`
- Agents: `sf-context-librarian`, `sf-project-inspector`, `sf-org-grounder`, `deployment-failure-triager`, `sf-evidence-reviewer`
- Tools: `get_deployment_result`, `get_org_identity`, `describe_salesforce_component`, `get_code_analysis_result`
- Permissions: `repository.read`, `knowledge.read`, `local_reports.write`, `salesforce.read`
- Terminal statuses: `completed`, `partial`, `refused`, `failed`

| Argument | Type | Required | Description |
|---|---|---|---|
| job_id | string | False | Existing Salesforce deployment job ID; never guessed |
| target_org | string | False | Explicit org alias/username; required with live retrieval unless safely resolved and confirmed |
| result_file | string | False | Captured Salesforce CLI/API deployment-result JSON |
| project_path | string | False | External Salesforce DX project for source mapping |
| failure_limit | string | False | Bounded page size, default 100 |

## `/triage-integration`

Correlate Salesforce and supplied integration evidence to classify an incident, identify the likely failing boundary, and propose safe verification and recovery steps.

- Product: `P08`
- Version: `0.9.0`
- Agents: `sf-context-librarian`, `sf-project-inspector`, `sf-org-grounder`, `integration-incident-triager`, `sf-evidence-reviewer`
- Tools: `get_integration_config_summary`, `get_integration_event_summary`, `get_org_identity`, `describe_salesforce_component`, `get_code_analysis_result`
- Permissions: `repository.read`, `knowledge.read`, `local_reports.write`, `salesforce.read`
- Terminal statuses: `completed`, `partial`, `refused`, `failed`

| Argument | Type | Required | Description |
|---|---|---|---|
| integration | string | True | Named integration/interface identifier |
| time_window | string | True | Explicit bounded window |
| target_org | string | False | Read-only org |
| evidence_files | string | False | Sanitized logs/events/response samples |
| project_path | string | False | Local project |

## `/why-cant-user`

Explain why a specific Salesforce user can or cannot see, create, edit, delete, or invoke an object, field, record, record type, or action.

- Product: `P03`
- Version: `0.9.0`
- Agents: `sf-context-librarian`, `sf-project-inspector`, `sf-org-grounder`, `access-path-explainer`, `sf-evidence-reviewer`
- Tools: `get_user_access_evidence`, `get_record_access_evidence`, `get_org_identity`, `describe_salesforce_component`
- Permissions: `repository.read`, `knowledge.read`, `local_reports.write`, `salesforce.read`
- Terminal statuses: `completed`, `partial`, `refused`, `failed`

| Argument | Type | Required | Description |
|---|---|---|---|
| user | string | True | User ID, username, or explicit fixture identity |
| resource | string | True | Object, field, record, record type, action, or capability |
| operation | string | True | read/create/edit/delete/transfer/execute/assign or product-defined action |
| target_org | string | False | Explicit org alias/username |
| record_id | string | False | Record for record-level explanation |
