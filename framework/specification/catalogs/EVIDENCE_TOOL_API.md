# Evidence-tool API reference

Generated from `mcp/tool-specs/*.json`. These are product-facing normalized contracts, not a promise to duplicate every upstream Salesforce tool.

## `compare_org_snapshots`

Deterministically compare two captured snapshot manifests.

- Version: `0.9.0`
- Read only: `true`
- Permission classes: `repository.read`
- Target pinning: `false`
- Maximum model-visible page: `32768` bytes
- Unknown-tool default: `deny`
- Upstream candidates: `local deterministic comparator`

| Argument | Type | Required |
|---|---|---|
| left_snapshot | string | True |
| right_snapshot | string | True |
| difference_policy | string | False |

Required contract tests: happy path; empty result; malformed upstream; timeout/unavailable; redaction-shaped data; pagination/truncation; target mismatch when applicable; policy denial.

## `describe_salesforce_component`

Retrieve bounded metadata/schema description for an explicit component.

- Version: `0.9.0`
- Read only: `true`
- Permission classes: `salesforce.metadata.read`
- Target pinning: `true`
- Maximum model-visible page: `32768` bytes
- Unknown-tool default: `deny`
- Upstream candidates: `official metadata/describe APIs`, `local project parser`

| Argument | Type | Required |
|---|---|---|
| component_type | string | True |
| component_name | string | True |
| target_org | string | False |

Required contract tests: happy path; empty result; malformed upstream; timeout/unavailable; redaction-shaped data; pagination/truncation; target mismatch when applicable; policy denial.

## `get_agentforce_test_result`

Retrieve or normalize an existing Agentforce testing result/definition.

- Version: `0.9.0`
- Read only: `true`
- Permission classes: `salesforce.agentforce.read`
- Target pinning: `true`
- Maximum model-visible page: `32768` bytes
- Unknown-tool default: `deny`
- Upstream candidates: `Agentforce testing metadata/API/CLI`

| Argument | Type | Required |
|---|---|---|
| agent_name | string | True |
| result_id | string | True |
| target_org | string | False |
| result_file | string | False |

Required contract tests: happy path; empty result; malformed upstream; timeout/unavailable; redaction-shaped data; pagination/truncation; target mismatch when applicable; policy denial.

## `get_apex_test_run`

Retrieve and normalize an existing Apex test run.

- Version: `0.9.0`
- Read only: `true`
- Permission classes: `salesforce.tooling.read`
- Target pinning: `true`
- Maximum model-visible page: `32768` bytes
- Unknown-tool default: `deny`
- Upstream candidates: `sf apex get test`, `official Salesforce DX MCP equivalent`

| Argument | Type | Required |
|---|---|---|
| test_run_id | string | True |
| target_org | string | False |
| method_limit | string | False |
| cursor | string | False |

Required contract tests: happy path; empty result; malformed upstream; timeout/unavailable; redaction-shaped data; pagination/truncation; target mismatch when applicable; policy denial.

## `get_automation_inventory`

Return bounded automation inventory and ordering-relevant metadata for an object/event.

- Version: `0.9.0`
- Read only: `true`
- Permission classes: `repository.read`, `salesforce.metadata.read`
- Target pinning: `true`
- Maximum model-visible page: `32768` bytes
- Unknown-tool default: `deny`
- Upstream candidates: `local source parser`, `metadata/tooling reads`

| Argument | Type | Required |
|---|---|---|
| object | string | True |
| operation | string | True |
| project_path | string | False |
| target_org | string | False |
| cursor | string | False |

Required contract tests: happy path; empty result; malformed upstream; timeout/unavailable; redaction-shaped data; pagination/truncation; target mismatch when applicable; policy denial.

## `get_code_analysis_result`

Normalize an existing or newly local-only Code Analyzer result.

- Version: `0.9.0`
- Read only: `true`
- Permission classes: `repository.read`, `shell.read_only`
- Target pinning: `false`
- Maximum model-visible page: `32768` bytes
- Unknown-tool default: `deny`
- Upstream candidates: `Salesforce Code Analyzer CLI/result file`

| Argument | Type | Required |
|---|---|---|
| result_file | string | False |
| project_path | string | False |
| rule_filter | string | False |
| cursor | string | False |

Required contract tests: happy path; empty result; malformed upstream; timeout/unavailable; redaction-shaped data; pagination/truncation; target mismatch when applicable; policy denial.

## `get_component_dependency_evidence`

Collect direct/transitive dependency references from project and/or org.

- Version: `0.9.0`
- Read only: `true`
- Permission classes: `repository.read`, `salesforce.metadata.read`
- Target pinning: `true`
- Maximum model-visible page: `32768` bytes
- Unknown-tool default: `deny`
- Upstream candidates: `local parsers`, `MetadataComponentDependency or official equivalent`

| Argument | Type | Required |
|---|---|---|
| component | string | True |
| project_path | string | False |
| target_org | string | False |
| scope | string | False |
| cursor | string | False |

Required contract tests: happy path; empty result; malformed upstream; timeout/unavailable; redaction-shaped data; pagination/truncation; target mismatch when applicable; policy denial.

## `get_data_load_result`

Normalize data load success/error/reject files and deterministic counts.

- Version: `0.9.0`
- Read only: `true`
- Permission classes: `repository.read`
- Target pinning: `false`
- Maximum model-visible page: `32768` bytes
- Unknown-tool default: `deny`
- Upstream candidates: `local files only`

| Argument | Type | Required |
|---|---|---|
| manifest | string | True |
| result_files | string | True |
| mapping_file | string | False |

Required contract tests: happy path; empty result; malformed upstream; timeout/unavailable; redaction-shaped data; pagination/truncation; target mismatch when applicable; policy denial.

## `get_deployment_result`

Retrieve and normalize an existing deployment result.

- Version: `0.9.0`
- Read only: `true`
- Permission classes: `salesforce.metadata.read`
- Target pinning: `true`
- Maximum model-visible page: `32768` bytes
- Unknown-tool default: `deny`
- Upstream candidates: `sf project deploy report`, `official Salesforce DX MCP equivalent`

| Argument | Type | Required |
|---|---|---|
| job_id | string | True |
| target_org | string | False |
| failure_limit | string | False |
| cursor | string | False |

Required contract tests: happy path; empty result; malformed upstream; timeout/unavailable; redaction-shaped data; pagination/truncation; target mismatch when applicable; policy denial.

## `get_flow_test_result`

Retrieve or normalize an existing Flow test result.

- Version: `0.9.0`
- Read only: `true`
- Permission classes: `salesforce.tooling.read`
- Target pinning: `true`
- Maximum model-visible page: `32768` bytes
- Unknown-tool default: `deny`
- Upstream candidates: `Salesforce logic/test reporting`

| Argument | Type | Required |
|---|---|---|
| result_id | string | True |
| target_org | string | False |
| result_file | string | False |

Required contract tests: happy path; empty result; malformed upstream; timeout/unavailable; redaction-shaped data; pagination/truncation; target mismatch when applicable; policy denial.

## `get_integration_config_summary`

Retrieve a redacted configuration summary for an explicit integration.

- Version: `0.9.0`
- Read only: `true`
- Permission classes: `repository.read`, `salesforce.metadata.read`
- Target pinning: `true`
- Maximum model-visible page: `32768` bytes
- Unknown-tool default: `deny`
- Upstream candidates: `Named/External Credential metadata without secrets`, `Apex/Flow metadata`

| Argument | Type | Required |
|---|---|---|
| integration | string | True |
| target_org | string | False |
| project_path | string | False |

Required contract tests: happy path; empty result; malformed upstream; timeout/unavailable; redaction-shaped data; pagination/truncation; target mismatch when applicable; policy denial.

## `get_integration_event_summary`

Normalize bounded integration logs/events supplied or queried for a time window.

- Version: `0.9.0`
- Read only: `true`
- Permission classes: `salesforce.logs.read`, `repository.read`
- Target pinning: `true`
- Maximum model-visible page: `32768` bytes
- Unknown-tool default: `deny`
- Upstream candidates: `event/log APIs`, `sanitized files`

| Argument | Type | Required |
|---|---|---|
| integration | string | True |
| start_time | string | True |
| end_time | string | True |
| target_org | string | False |
| evidence_files | string | False |
| cursor | string | False |

Required contract tests: happy path; empty result; malformed upstream; timeout/unavailable; redaction-shaped data; pagination/truncation; target mismatch when applicable; policy denial.

## `get_limits_snapshot`

Retrieve a bounded current limits/usage summary.

- Version: `0.9.0`
- Read only: `true`
- Permission classes: `salesforce.org_limits.read`
- Target pinning: `true`
- Maximum model-visible page: `32768` bytes
- Unknown-tool default: `deny`
- Upstream candidates: `official limits APIs`

| Argument | Type | Required |
|---|---|---|
| target_org | string | False |
| scope | string | False |

Required contract tests: happy path; empty result; malformed upstream; timeout/unavailable; redaction-shaped data; pagination/truncation; target mismatch when applicable; policy denial.

## `get_org_identity`

Resolve and attest an explicitly allowed org identity without secrets.

- Version: `0.9.0`
- Read only: `true`
- Permission classes: `salesforce.org_identity.read`
- Target pinning: `true`
- Maximum model-visible page: `32768` bytes
- Unknown-tool default: `deny`
- Upstream candidates: `sf org display --json`

| Argument | Type | Required |
|---|---|---|
| target_org | string | False |

Required contract tests: happy path; empty result; malformed upstream; timeout/unavailable; redaction-shaped data; pagination/truncation; target mismatch when applicable; policy denial.

## `get_org_snapshot_manifest`

Build a bounded metadata/configuration snapshot manifest without secrets.

- Version: `0.9.0`
- Read only: `true`
- Permission classes: `salesforce.metadata.read`, `salesforce.security.read`
- Target pinning: `true`
- Maximum model-visible page: `32768` bytes
- Unknown-tool default: `deny`
- Upstream candidates: `official metadata/tooling APIs`

| Argument | Type | Required |
|---|---|---|
| target_org | string | False |
| scope | string | False |
| cursor | string | False |

Required contract tests: happy path; empty result; malformed upstream; timeout/unavailable; redaction-shaped data; pagination/truncation; target mismatch when applicable; policy denial.

## `get_record_access_evidence`

Retrieve record-level access signals for an explicit user and record.

- Version: `0.9.0`
- Read only: `true`
- Permission classes: `salesforce.security.read`, `salesforce.data.minimal_read`
- Target pinning: `true`
- Maximum model-visible page: `32768` bytes
- Unknown-tool default: `deny`
- Upstream candidates: `UserRecordAccess and bounded supporting reads`

| Argument | Type | Required |
|---|---|---|
| user | string | True |
| record_id | string | True |
| operation | string | True |
| target_org | string | False |

Required contract tests: happy path; empty result; malformed upstream; timeout/unavailable; redaction-shaped data; pagination/truncation; target mismatch when applicable; policy denial.

## `get_user_access_evidence`

Retrieve normalized user/license/profile/permission/object/field/record-type access evidence.

- Version: `0.9.0`
- Read only: `true`
- Permission classes: `salesforce.security.read`
- Target pinning: `true`
- Maximum model-visible page: `32768` bytes
- Unknown-tool default: `deny`
- Upstream candidates: `bounded Tooling/Metadata/SOQL reads`

| Argument | Type | Required |
|---|---|---|
| user | string | True |
| resource | string | True |
| operation | string | True |
| target_org | string | False |

Required contract tests: happy path; empty result; malformed upstream; timeout/unavailable; redaction-shaped data; pagination/truncation; target mismatch when applicable; policy denial.

## `run_bounded_read_query`

Run an allowlisted aggregate/minimal SOQL query with row/field limits.

- Version: `0.9.0`
- Read only: `true`
- Permission classes: `salesforce.data.minimal_read`
- Target pinning: `true`
- Maximum model-visible page: `32768` bytes
- Unknown-tool default: `deny`
- Upstream candidates: `official Salesforce DX MCP run_soql_query or CLI`

| Argument | Type | Required |
|---|---|---|
| query | string | True |
| target_org | string | False |
| purpose | string | True |
| limit | string | False |

Required contract tests: happy path; empty result; malformed upstream; timeout/unavailable; redaction-shaped data; pagination/truncation; target mismatch when applicable; policy denial.
