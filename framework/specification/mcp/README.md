# V2 evidence tool catalog

These are stable product-oriented evidence contracts. Implementations may use official Salesforce DX MCP, Salesforce CLI/APIs, existing SfSkills MCP tools, or deterministic local parsers behind the broker.

| Tool | Authority | Mutation | Purpose |
|---|---|---:|---|
| `get_deployment_result` | `salesforce.metadata.read` | no | Retrieve and normalize an existing deployment result. |
| `get_apex_test_run` | `salesforce.tooling.read` | no | Retrieve and normalize an existing Apex test run. |
| `get_org_identity` | `salesforce.org_identity.read` | no | Resolve and attest an explicitly allowed org identity without secrets. |
| `describe_salesforce_component` | `salesforce.metadata.read` | no | Retrieve bounded metadata/schema description for an explicit component. |
| `get_user_access_evidence` | `salesforce.security.read` | no | Retrieve normalized user/license/profile/permission/object/field/record-type access evidence. |
| `get_record_access_evidence` | `salesforce.security.read`, `salesforce.data.minimal_read` | no | Retrieve record-level access signals for an explicit user and record. |
| `get_component_dependency_evidence` | `repository.read`, `salesforce.metadata.read` | no | Collect direct/transitive dependency references from project and/or org. |
| `get_automation_inventory` | `repository.read`, `salesforce.metadata.read` | no | Return bounded automation inventory and ordering-relevant metadata for an object/event. |
| `get_code_analysis_result` | `repository.read`, `shell.read_only` | no | Normalize an existing or newly local-only Code Analyzer result. |
| `get_flow_test_result` | `salesforce.tooling.read` | no | Retrieve or normalize an existing Flow test result. |
| `get_agentforce_test_result` | `salesforce.agentforce.read` | no | Retrieve or normalize an existing Agentforce testing result/definition. |
| `get_integration_config_summary` | `repository.read`, `salesforce.metadata.read` | no | Retrieve a redacted configuration summary for an explicit integration. |
| `get_integration_event_summary` | `salesforce.logs.read`, `repository.read` | no | Normalize bounded integration logs/events supplied or queried for a time window. |
| `get_data_load_result` | `repository.read` | no | Normalize data load success/error/reject files and deterministic counts. |
| `run_bounded_read_query` | `salesforce.data.minimal_read` | no | Run an allowlisted aggregate/minimal SOQL query with row/field limits. |
| `get_org_snapshot_manifest` | `salesforce.metadata.read`, `salesforce.security.read` | no | Build a bounded metadata/configuration snapshot manifest without secrets. |
| `compare_org_snapshots` | `repository.read` | no | Deterministically compare two captured snapshot manifests. |
| `get_limits_snapshot` | `salesforce.org_limits.read` | no | Retrieve a bounded current limits/usage summary. |

## Broker posture

- Prefer official Salesforce tools for raw operations.
- Expose only the smallest product-specific evidence contract.
- Pin explicit org identity and prohibit `ALLOW_ALL_ORGS` in product mode.
- Treat tool annotations as hints, never enforcement.
- Normalize and redact before model exposure.
- Deny unknown tools.
- Keep QA mutation in a separate non-model authority.


## Full evidence-tool contract

Every tool specification in `mcp/tool-specs/` defines more than a name and argument list. It includes:

- operation class and authority;
- target-pinning rules and upstream candidates;
- stable result schema and evidence types;
- deterministic normalization and evidence-ID rules;
- pagination, byte ceilings, timeout, retry, rate, and cache policy;
- sensitive-data classes and mandatory redaction profile;
- stable error taxonomy and audit events;
- required fixture, failure, policy, target-mismatch, and truncation tests.

The generated [`TOOL_REFERENCE.md`](TOOL_REFERENCE.md) is the complete implementation reference for all 18 normalized evidence contracts.

These contracts intentionally sit above raw Salesforce CLI/API/MCP operations. The upstream tool performs the observation; the SfSkills broker enforces least privilege, explicit target identity, bounded output, provenance, redaction, replayability, and product-specific normalization.
