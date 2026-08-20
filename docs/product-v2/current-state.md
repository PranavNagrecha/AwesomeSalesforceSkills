# SfSkills V2 — current repository state

Living document for branch `product/sfskills-v2-local`. Updated at M1 deterministic core integration.

## Git

| Field | Value |
| --- | --- |
| Branch | `product/sfskills-v2-local` |
| Original baseline SHA | `774d666d191a01682610149cb2927bcd6365fe82` |
| Inherited product commit | `77f559923` — `chore(v2): preserve inherited pre-spec product implementation` |
| M0 specification commit | `0dce1ae721bf692e440a84e09c4f5cc3ff653ee2` — see `docs/product-v2/milestones/m0-spec-adoption.md` |
| M0 tag | `sfskills-v2-m0-spec-adopted` |
| M1 deterministic core | `336ab80ce3edf304ed12516a1dd2ed9540de116c` — see `docs/product-v2/milestones/m1-deterministic-core.md` |
| M1 tag | `sfskills-v2-m1-deterministic-core` |

## Temporary script disposition (M0 cleanup)

All six `scripts/_tmp_*.py` files were **deleted** as disposable scratch. None contained unique logic absent from canonical modules.

| File | Decision |
| --- | --- |
| `_tmp_cherry.py` | Deleted — git cherry-pick helper only |
| `_tmp_commit_inspector.py` | Deleted — one-off staging helper superseded by selective commits |
| `_tmp_copy_inspector_addon.py` | Deleted — copy helper; canonical files already in tree |
| `_tmp_isolate_test_phase1.py` | Deleted — test isolation scratch |
| `_tmp_pack_inspector_review.py` | Deleted — ad-hoc review ZIP builder; superseded by `pack_v2_review.py` |
| `_tmp_restore_p1.py` | Deleted — stash restore helper only |

## Inventory (committed M0 tree)

| Artifact class | Live | Ledger | Notes |
| --- | ---: | ---: | --- |
| Skill packages | 1034 | 1034 | legacy knowledge substrate |
| Canonical agents | 77 | 77 | includes inherited `deployment-failure-triager` |
| Slash commands | 69 | 69 | includes inherited `triage-deployment`, `sfskills-doctor` |
| MCP tools | 39 | 39 | includes inherited `get_deployment_result` |

Reconciliation report: `docs/product-v2/migration-reconciliation.md`

### Capability classes (not product completion)

- **Legacy repository capabilities** — 1034 skills, 67 legacy commands, 38 baseline MCP tools, 76 baseline agents
- **Inherited partial V2 capabilities** — P01 pipeline, project inspector, Cursor plugin surfaces (commit `77f559923`); **partial, unqualified**
- **Specification-defined future capabilities** — P02–P12 product definitions under `framework/specification/products/`
- **Implemented and qualified products** — none at M0

## Inherited product work (commit `77f559923`)

Status: **inherited; partial; unqualified; subject to M1/M2 reconciliation.**

Includes `pipelines/product/`, project inspector, deployment triager agent/command, Cursor integrations, `pack_v2_review.py`, and 49 product tests. Does **not** claim P01 completion, host smoke, live-org verification, or release readiness.

## M0 specification adoption

- Imported SFAEF **0.9.0-draft** under `framework/specification/`
- Deliberate import deviations: `docs/product-v2/spec-deviations.md`
- Repo validator: `python3 scripts/validate_framework.py`
- Traceability: `docs/product-v2/requirement-traceability.csv`
- Evidence: `.sfskills/v2-evidence/m0/`

## M1 deterministic core

- `pipelines/framework/core/` — kernel bridge, run session, envelope v2, run bundle, review contract, product adapters
- Reference kernel path: `framework/specification/reference-kernel/` (imported with M0 spec)
- Tests: 13 framework tests (4 validate + 9 core conformance); 49 product tests unchanged
- Evidence: `.sfskills/v2-evidence/m1/`

## Baseline deviations (documented, not hidden)

| Check | Classification | Notes |
| --- | --- | --- |
| `export_skills.py --check` | advisory | Aider `CONVENTIONS.md` hash drift; verified unchanged vs baseline SHA `774d666d1` — see `.sfskills/v2-evidence/m0/export-drift/` |
| `validate_repo.py --agents` | advisory | 12 warnings (skill-read ceilings, decision-tree unreachable questions) |

## Deferred

- **M2** — P02 Apex test triage, Cursor host smoke for P01/P02, P01 qualification path
- **M3–M6** — additional products, scratch QA, flagship products, RC
