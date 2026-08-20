# Legacy command migration

The current repository's 67 commands remain supported compatibility entrypoints. Do not bulk-convert all of them solely for schema completeness.

Migrate a legacy command when:

1. it becomes a V2 product entrypoint;
2. a host adapter needs typed arguments;
3. safety or ambiguity requires deterministic validation;
4. repeated drift exists across host copies;
5. usage data justifies product ownership.

Each migration must identify the current agent, aliases, behavior changes, permissions, reduced modes, output schema, and compatibility redirect.
