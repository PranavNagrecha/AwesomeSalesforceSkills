# Official Salesforce DX MCP integration

The official Salesforce DX MCP server is the preferred upstream for many Salesforce operations. It has a broad tool surface, explicit toolsets, individual-tool configuration, and both observational and mutating operations.

## Framework policy

1. Configure explicit org aliases/usernames where practical; do not use `ALLOW_ALL_ORGS`.
2. Do not enable the `all` toolset.
3. Enable only product-required read operations.
4. Do not assume experimental dynamic tool loading works in every host.
5. Pass every call through SFAEF authority and target checks when the host allows interception.
6. Where the host cannot intercept MCP, expose only a restricted broker server rather than the unrestricted upstream server.
7. Preserve upstream server/tool version and original operation in evidence provenance.
8. Never map a mutating upstream tool into a read-only product name.

## Why an SfSkills broker still exists

The broker stabilizes schemas, evidence IDs, pagination, redaction, target pinning, and error semantics across CLI/MCP versions. The value is not another list of raw Salesforce tools; it is a trustworthy product evidence surface.
