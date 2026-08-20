# M1 — Deterministic core

## Purpose

Integrate the SFAEF reference kernel as a behavioral oracle and wire a thin deterministic core used by P01 and P02 without replacing working `pipelines/product/` modules.

## M0 anchor

- Tag: `sfskills-v2-m0-spec-adopted` → `0dce1ae721bf692e440a84e09c4f5cc3ff653ee2`
- Baseline SHA: `774d666d1`

## Delivered

- `pipelines/framework/core/` — kernel bridge, run session, envelope v2, run bundle, review contract, product adapters
- `tests/framework/test_core.py` — conformance tests aligned with reference kernel invariants
- Inherited product lint preserved; kernel `lint_claims` layered when draft includes typed claims/evidence

## Not in M1

- General workflow engine, capability graph, or full P02 product implementation (M2)
- Cursor host smoke or live org verification

## Gates (clean tree)

| Gate | Result |
| --- | --- |
| `python3 scripts/validate_framework.py` | pass |
| `python3 -m unittest discover -s tests/framework -p 'test_*.py'` | 13 pass |
| `python3 -m unittest discover -s tests/product -p 'test_*.py'` | 49 pass |
| reference-kernel tests (via `run_all_checks.py`) | pass |

Evidence: `.sfskills/v2-evidence/m1/gates/`

## Commit and tag

- **Commit:** (recorded after local commit)
- **Tag:** `sfskills-v2-m1-deterministic-core`

## Evidence

`.sfskills/v2-evidence/m1/` (gitignored)
