# Adversarial security suite

Required attack classes:

- shell compound operators, pipes, substitutions, nested shells, aliases, reordered flags, and legacy `sfdx` forms;
- unknown MCP tools and misleading tool names;
- prompt injection in metadata descriptions, record text, Apex comments, logs, filenames, and error messages;
- wrong-org default changes during a run;
- job ID from another org;
- path traversal and symlink escape during project inspection;
- secret-shaped tokens in stdout/stderr/JSON;
- oversized recursive JSON and pagination abuse;
- scratch setup pointed at a sandbox/production/non-marked org;
- reviewer manipulation embedded in draft/evidence.

Security-critical checks fail closed where the host provides enforcement. Where it does not, the adapter must restrict the exposed server/tool surface and disclose the limitation.
