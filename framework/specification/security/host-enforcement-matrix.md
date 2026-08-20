# Host enforcement matrix

| Control | Cursor local | Cursor cloud | Claude Code local | VS Code/Copilot | Agentforce Vibes |
|---|---|---|---|---|---|
| Progressive skills | native | native/host dependent | native | native | adapter/project guidance |
| Isolated subagents | native | available/host version | native | custom agent/handoff support | Agentforce/Vibes concepts differ |
| MCP | native | available with host constraints | native | native | official Salesforce integration |
| Before-shell policy hook | native | host-dependent | hook/permission model | host-dependent | host/native policy |
| Before/after MCP hook | local support | not equivalent; verify current host | plugin/hook path varies | host-dependent | adapter/broker required |
| Compaction notification | `preCompact` observation | verify | host-specific | host-specific | not assumed |
| Guaranteed fail-closed interception | only where hook actually runs | not assumed | only where supported | not assumed | broker/server restriction |

Every adapter must generate an actual capability record during smoke testing. Documentation cannot substitute for host verification.
