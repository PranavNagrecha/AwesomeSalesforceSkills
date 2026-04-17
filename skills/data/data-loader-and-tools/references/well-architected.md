# Well-Architected: Data Loader and Tools

## WAF Pillar Mapping

### Operational Excellence

**Tool selection discipline** is the primary Operational Excellence concern. Using the wrong tool for a data operation creates operational overhead: failed jobs, partial loads, manual cleanup, and re-runs. The decision tree in this skill's `SKILL.md` Recommended Workflow section implements the SF Well-Architected principle of using the right capability at the right scale.

Key practices:
- Use Data Import Wizard for <50K supported-object loads — lower operational surface, guided field mapping, no installation.
- Use Data Loader Bulk API 2.0 for large or automated loads — job status is visible in Setup > Bulk Data Load Jobs, errors are captured in a structured CSV.
- Prefer Salesforce CLI for scripted/CI loads — outputs are deterministic, pipelines are auditable.
- Do not depend on sunset tools (Workbench) for production workflows — operational continuity risk.

**Automation and repeatability**: Data Loader's headless `process.sh`/`process.bat` mode with a `process-conf.xml` file enables repeatable, scheduled data operations. This reduces manual intervention and human error in recurring migration or seeding jobs.

**Monitoring**: Bulk API 2.0 jobs expose status via Setup > Bulk Data Load Jobs. Integrate this into change management processes — always retain success and error CSVs as evidence for audit and rollback planning.

### Reliability

**Batch sizing and error isolation** directly affect reliability. Bulk API 2.0 manages batching automatically, which removes a common source of misconfigured batch sizes that caused partial failures in v1. SOAP mode's 200-record batch limit is a reliability boundary — exceeding it requires switching modes.

Key practices:
- Always run a sample load (1,000 records) before full-scale execution. This surfaces field mapping errors and permission issues before they affect the full dataset.
- Capture and resolve all error CSV rows before closing the migration window. Partially loaded data creates referential integrity issues and reconciliation debt.
- Use upsert (not insert) when re-running after a partial failure — idempotent operations are more reliable under retry conditions.
- Hard delete is irreversible. The **Bulk API Hard Delete** permission gate is a reliability safeguard — it should not be granted broadly. Verify with the data owner before any hard delete operation.

**Workbench reliability note**: Workbench is on a sunset trajectory. Any workflow that depends on Workbench for production data access is a reliability risk. Migrate to Salesforce CLI or VS Code Extensions.

### Security (Contributing Pillar)

While not a primary WAF pillar for this skill, security hygiene in data tool configuration has direct reliability implications:

- Plaintext credentials in `process-conf.xml` committed to version control represent both a security and compliance failure. Use encrypted passwords or OAuth JWT.
- Salesforce Inspector and third-party extensions are outside Salesforce's security boundary. Their use in regulated or high-compliance orgs should go through a security review.
- The Bulk API Hard Delete permission should follow least-privilege. Audit it via: `SELECT PermissionsAuthorApex FROM PermissionSet` is insufficient — use `SELECT PermissionsHardDelete FROM PermissionSet WHERE PermissionsHardDelete = true`.

## Official Sources Used

- https://help.salesforce.com/s/articleView?id=sf.loader_when_to_use.htm&type=5
- https://help.salesforce.com/s/articleView?id=sf.loader_configuring_bulk_api.htm&type=5
- https://help.salesforce.com/s/articleView?id=platform.replacement_workbench_tools.htm&type=5
- https://help.salesforce.com/s/articleView?id=sf.data_import_wizard.htm&type=5
- https://developer.salesforce.com/docs/atlas.en-us.api_asynch.meta/api_asynch/asynch_api_concepts_limits.htm
