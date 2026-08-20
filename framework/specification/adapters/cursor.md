# Cursor adapter

## Native package

```text
.cursor-plugin/plugin.json
skills/                  bounded top-level Salesforce/domain/product skills
agents/                  small proven execution subagent set
commands/                typed V2 product commands
hooks/hooks.json         shell/MCP/telemetry hooks where supported
mcp.json                 restricted SfSkills evidence broker
```

## Default discovery surface

- one Salesforce top-level router;
- bounded domain/product router skills;
- core execution subagents needed by shipped products;
- product commands;
- restricted evidence broker.

Do not install 1,034 `.mdc` rules as the recommended path and do not expose all existing agents as subagents. Preserve flat rules as explicit legacy compatibility.

## Context

Use native skills for progressive loading and separate subagent contexts for noisy exploration and independent review. Measure actual context and do not assume isolation alone solves rot.

## Safety

Use `beforeShellExecution` and local MCP hooks when supported. Security-critical hooks fail closed. In environments where MCP interception is unavailable, connect Cursor only to the restricted broker server, not the unrestricted official Salesforce MCP surface.

## Verification

Actual Cursor smoke must prove plugin discovery, command visibility, subagent invocation, MCP tool use, evidence reviewer behavior, fixture run, local install/uninstall, and capability report. File presence is not enough.
