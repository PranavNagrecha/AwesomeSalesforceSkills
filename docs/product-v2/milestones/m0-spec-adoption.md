# M0 — Specification adoption

## Purpose

Establish an auditable M0 anchor for SfSkills V2: import SFAEF v0.9.0, wire repository validation and migration reconciliation, preserve inherited partial product work separately, and record baseline evidence for the final return ZIP.

M0 does **not** claim Deployment Failure Triage (P01) is complete, host-verified, live-org verified, or release-ready.

## Commits

| SHA | Message |
| --- | --- |
| `774d666d191a01682610149cb2927bcd6365fe82` | Original baseline (pre-M0) |
| `77f559923` | `chore(v2): preserve inherited pre-spec product implementation` |
| `0dce1ae721bf692e440a84e09c4f5cc3ff653ee2` | `feat(framework): adopt SFAEF v0.9.0 and establish M0 baseline` |

## Tag

- **Name:** `sfskills-v2-m0-spec-adopted`
- **Target:** `0dce1ae721bf692e440a84e09c4f5cc3ff653ee2`
- **Specification:** `0.9.0-draft`

## Files introduced (M0 commit)

- `framework/specification/` — imported specification package (539 files)
- `pipelines/framework/` — migration reconciliation
- `scripts/validate_framework.py`, `scripts/refresh_migration_ledgers.py`, `scripts/capture_m0_evidence.py`
- `tests/framework/test_validate_framework.py`
- `docs/product-v2/current-state.md`, `spec-deviations.md`, `migration-reconciliation.md`, `requirement-traceability.csv`

## Inventories (reconciled)

| Class | Live | Ledger |
| --- | ---: | ---: |
| Skills | 1034 | 1034 |
| Agents | 77 | 77 |
| Commands | 69 | 69 |
| MCP tools | 39 | 39 |

Capability classes:

- **Legacy repository** — full skill corpus + baseline agents/commands/tools
- **Inherited partial V2** — commit `77f559923` (P01 pipeline, inspector, Cursor surfaces); unqualified
- **Specification-defined** — P01–P12 definitions under `framework/specification/products/`
- **Qualified products** — none at M0

## Gates (clean tree at `0dce1ae7`)

Evidence: `.sfskills/v2-evidence/m0/gates/`

| Gate | Exit | Classification |
| --- | ---: | --- |
| `validate_framework.py` | 0 | required |
| product tests (`tests/product`) | 0 (49 tests) | required |
| framework tests (`tests/framework`) | 0 (4 tests) | required |
| `validate_repo.py --agents` | 0 | required |
| `build_plugin.py --check` | 0 | required |
| `export_skills.py --check` | 0 | advisory |
| migration reconcile | 0 | required |
| `framework/specification/scripts/run_all_checks.py` | 0 | required |
| `pack_v2_review.py --validate` (missing zip) | non-zero (expected) | required |
| python compile (new modules) | 0 | required |

## Baseline deviations

| Item | Verdict |
| --- | --- |
| Aider `CONVENTIONS.md` export drift | Unchanged vs baseline SHA `774d666d1` — see `.sfskills/v2-evidence/m0/export-drift/comparison.json` |
| `validate_repo.py --agents` warnings | 12 advisory warnings (skill-read ceilings, decision-tree unreachable questions) |
| Specification import diffs | 8 files — documented in `docs/product-v2/spec-deviations.md` |

## Inherited product work

Commit `77f559923` preserves partial P01-related implementation predating specification adoption. Status: inherited, partial, unqualified, subject to M1/M2 reconciliation.

## Unresolved risks

- Reference kernel not yet integrated into `pipelines/product/` (M1)
- No Cursor host smoke evidence bundle at M0
- Export manifest drift for Aider target remains unfixed (pre-existing)
- Cursor CLI not on PATH during evidence capture

## Deferred to M1 / M2

- **M1:** run identity, envelope v2, evidence index, replay bundle, reference-kernel conformance adapters
- **M2:** P02 Apex test triage, P01/P02 Cursor smoke, live read-only verification

## Publication

Nothing was pushed, published, opened as a pull request, or submitted to a marketplace.

Raw evidence preserved under `.sfskills/v2-evidence/m0/` (gitignored).
