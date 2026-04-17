# Designer Inventory Probes

Common audit-mode probe patterns shared across designers inheriting `designer_base`. Domain-specific probes live in each designer's AGENT.md Plan — this document only covers the patterns that most designers use.

## Frame the org

Every audit-mode run starts with `describe_org(target_org)` to record edition, API version, sandbox/prod flag. The result is carried into Process Observations as context (e.g. "Design recommendations gated to manual-review because this is prod"). This is NOT itself a finding.

## Object / metadata inventory

Designers touching a specific sObject should include:

- `list_custom_objects(target_org=..., name_filter=<object>)` — confirm object exists + record edition-gated fields.
- `list_record_types(<object>)` — when the design/audit needs to reason about record-type proliferation.
- `list_validation_rules(<object>)` — when the design interacts with validation surface.
- `list_flows_on_object(<object>, active_only=true)` — when the design touches automation.

These are MCP-tool calls — no raw SOQL needed.

## Permission inventory

Designers that emit or audit a permission set / permission set group should include:

- `list_permission_sets(target_org=..., name_filter=<pattern>)` — sweep matching PSes.
- `describe_permission_set(<name>, include_field_permissions=true)` — per-PS detail.
- `probe_permset_shape(scope="psg:<name>")` — Wave-2 promoted probe for PSG composition + concentration.

## Approval / Queue inventory

Designers that touch approvals, routing, or escalations:

- `list_approval_processes(object_name=<object>, active_only=true)`.
- `tooling_query("SELECT Id, DeveloperName, Type FROM Group WHERE Type = 'Queue' AND Related = '<object>'")`.
- `tooling_query("SELECT GroupId, COUNT(Id) FROM GroupMember WHERE Group.Type = 'Queue' GROUP BY GroupId")` — queue-member counts.

## Named Credentials (when integration-adjacent)

- `list_named_credentials(target_org=...)` — integration-aware designers (e.g. sandbox-strategy-designer considering CI/CD credentials) cite this.

## Tooling-query escape hatch

For domain-specific probes not covered by a dedicated MCP tool: `tooling_query("<SOQL>", target_org=..., tooling=true)`. The designer's Plan must quote the exact SOQL so reviewers can reproduce the probe.

## Probe-result handling

1. **Pagination** — any tool that reports it paginated downgrades confidence to MEDIUM unless the designer explicitly runs a subsequent narrower query.
2. **Truncation** — any tool returning a truncated result (e.g. > `limit` rows) emits a Process Observation and caps `confidence` at MEDIUM.
3. **Empty results** — an empty inventory in audit mode doesn't mean "healthy". It means "not yet using <feature>". Call that out explicitly; do NOT silently return an all-green audit.
4. **Managed package** — artifacts with `NamespacePrefix` set are audited read-only; designer output must NOT propose edits to managed metadata. Refusal code: `REFUSAL_MANAGED_PACKAGE`.

## What this doc does NOT cover

- Domain-specific SOQL (e.g. the exact `BusinessHours` / `EscalationRule` queries case-escalation uses) — lives in the designer's AGENT.md Plan.
- Probe promotion criteria — see `agents/_shared/probes/README.md`.
- Cost estimates (recalc cost, storage) — each designer owns its own estimation method if needed.
