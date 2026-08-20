# Legacy surface V2 disposition ledger

These generated ledgers give every artifact in the uploaded SfSkills snapshot an explicit V2 posture. They prevent implementation work from silently deleting, flattening, auto-exporting, or duplicating the existing system.

## Snapshot

- Uploaded archive SHA-256: `not supplied`
- Skills: 1034
- Canonical agents: 76
- Commands: 67
- MCP tools: 38

## Binding migration rules

1. `retain-knowledge-substrate` means preserve the skill package and load it progressively; it does not become an always-on host rule.
2. Legacy runtime agents are not automatically exported as native subagents.
3. Deprecated agents remain redirects until replacement parity and migration tests pass.
4. Legacy commands remain compatible until evidence supports migration or deprecation.
5. Raw/broad query tools remain broker-internal; products receive typed read-only evidence operations.
6. A mapping to a V2 product is an integration input, not proof that the legacy artifact already satisfies the V2 contract.
7. Cursor must update the corresponding ledger row, traceability, and tests when it changes a legacy artifact's disposition.

## Files

- `current-skills.csv` — all skill packages and preservation policy.
- `current-agents.csv` — all canonical agent definitions and product alignment.
- `current-commands.csv` — all command wrappers and compatibility posture.
- `current-mcp-tools.csv` — all registered MCP tools and broker posture.
