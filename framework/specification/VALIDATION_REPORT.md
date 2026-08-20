# Salesforce AI Engineering Framework specification validation report

**Specification version:** `0.9.0-draft`  
**Research freeze:** 2026-08-19  
**Validation environment:** containerized Linux with Python 3.13  
**Package status:** passed all package-level gates

## Final package gates

The final clean-generation and drift-check workflow completed successfully.

| Gate | Result |
|---|---|
| Requirement extraction and catalog | Passed; 266 unique normative requirements |
| Product/catalog generation | Passed |
| Machine agent/command/tool contract enrichment | Passed |
| Generated API-reference check | Passed |
| Primary package validator | Passed; 0 errors, 0 warnings |
| Independent strict package validator | Passed |
| JSON Schema validation | Passed; 194 JSON instances validated |
| Root framework contract tests | 12 passed |
| Return-package and validator tests | 6 passed |
| Deterministic reference-kernel tests | 34 passed |
| Optional project-inspector reference tests | 19 passed |
| Python compilation | Passed with isolated bytecode cache |
| Framework manifest drift check | Passed |
| Independent package-check script | Passed |

**Executable package tests:** 71 passed, 0 failed, 0 errors.

The primary validator reported these contract counts:

- 12 product definitions;
- 20 core/product agents;
- 18 typed commands;
- 18 read-only evidence tools;
- 12 context packs;
- 74 known-truth QA scenarios;
- 266 normative requirements;
- 37 external research source records;
- 1,034 baseline skills, 76 canonical agents, 67 commands, and 38 MCP tools covered by artifact-level migration ledgers.

Exact commands, stdout/stderr, exit codes, and structured results are under `validation/`:

- `package-check-generation.log`, `package-check-generation.json`, `package-check-generation.exit`;
- `independent-package-checks.log`, `independent-package-checks.exit`.

The framework manifest intentionally excludes volatile validation logs, `VALIDATION_REPORT.md`, and `SHA256SUMS.txt`; the final archive checksum file covers all packaged files.

## Uploaded SfSkills repository baseline

The uploaded repository snapshot was independently exercised before the specification was sealed:

| Check | Result |
|---|---|
| Repository unit-test discovery | 272 passed |
| Agent validator | 76 agents; 0 errors; 12 warnings |
| Claude/plugin build drift check | 121 artifacts match |
| Multi-host export drift check | 1,034 skills and export manifest match |

The 12 agent-validator warnings are preserved in `baseline/logs/validate-agents.log`: four broad runtime agents exceed the advisory 40-skill-read ceiling and eight questions are unreachable across three Markdown decision trees. These are migration evidence, not hidden failures.

## Deliberately not claimed

This specification package has **not** itself performed:

- Cursor IDE/plugin execution;
- an authenticated Salesforce CLI or live-org product run;
- disposable scratch-org known-truth scenarios;
- Claude Code, Copilot, Agentforce Vibes, or other host execution;
- real-user adoption or outcome benchmarking;
- implementation of the complete framework in the source repository.

Those are mandatory Cursor implementation-return gates. The package designs the product, contracts, architecture, reference behavior, QA truth, migration posture, and review protocol; it does not misrepresent design conformance as shipped product behavior.
