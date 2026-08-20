# SFAEF v0.9.0 specification import deviations

The imported tree lives at `framework/specification/`. Normative requirement text was not edited. The following files differ from the supplied package at `SfSkills_Salesforce_AI_Engineering_Framework_Spec_v0.9.0` after import.

| File | Reason |
| --- | --- |
| `migration/catalogs/current-agents.csv` | Live reconciliation added explicit rows for inherited V2 agents (`deployment-failure-triager`). Count 76 → 77. |
| `migration/catalogs/current-commands.csv` | Live reconciliation added explicit rows for inherited V2 commands (`triage-deployment`, `sfskills-doctor`). Count 67 → 69. |
| `migration/catalogs/current-mcp-tools.csv` | Live reconciliation added `get_deployment_result`. Count 38 → 39. |
| `migration/catalogs/V2_DISPOSITION_LEDGER.md` | Regenerated summary counts after ledger refresh. |
| `FRAMEWORK_MANIFEST.json` | Regenerated manifest after ledger refresh. |
| `scripts/validate_framework_package.py` | Updated expected ledger row counts to match reconciled live repository (required for package self-check). |
| `tests/test_framework_package.py` | Updated expected ledger row counts to match reconciled live repository. |

No files under `spec/` numbered requirements were modified.

Repository-specific implementation notes remain under `docs/product-v2/` and `pipelines/framework/`.

Evidence: `.sfskills/v2-evidence/m0/spec-package-checksum.json`
