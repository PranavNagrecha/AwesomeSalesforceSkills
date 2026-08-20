# Uploaded repository baseline — 2026-08-19

The baseline was executed from the uploaded repository snapshot before generating this specification.

| Check | Result |
|---|---|
| `python3 -m unittest discover -s tests -p 'test_*.py' -v` | 272 passed |
| `python3 scripts/validate_repo.py --agents` | 76 agents; 0 errors; 12 warnings |
| `python3 scripts/build_plugin.py --check` | 121 plugin artifacts match |
| `python3 scripts/export_skills.py --check` | 1,034 skills and export manifest match |

Notable warnings include four runtime agents with more than 40 numbered skill references and unreachable questions in three Markdown decision trees. Exact logs are in `baseline/logs/`.

This baseline is evidence for migration, not a guarantee about the user's current working branch.
