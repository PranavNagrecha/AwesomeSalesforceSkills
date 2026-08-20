# SfSkills V2 — current repository state

Living document for branch `product/sfskills-v2-local`. Updated at M6 local RC packaging.

## Git

| Field | Value |
| --- | --- |
| Branch | `product/sfskills-v2-local` |
| Original baseline SHA | `774d666d191a01682610149cb2927bcd6365fe82` |
| Inherited product commit | `77f559923` — `chore(v2): preserve inherited pre-spec product implementation` |
| M0 tag | `sfskills-v2-m0-spec-adopted` → `70637852430a5f519efe4e5e64db4a2e091ba3c4` |
| M1 tag | `sfskills-v2-m1-deterministic-core` → `b4fcbeae948f17601677ba1b9985d2566028129f` |
| M2 tag | `sfskills-v2-m2-triage` → `bbd9dfd0bcc621958a65bcfa6f846e9c3bdcbf07` |
| M3 tag | `sfskills-v2-m3-behavioral-qa` |
| M4 tag | `sfskills-v2-m4-flagship` |
| M5 tag | `sfskills-v2-m5-beta-portfolio` |
| RC tag | `sfskills-v2-rc1-local` |

## Inventory (committed tree)

| Artifact class | Live | Ledger | Notes |
| --- | ---: | ---: | --- |
| Skill packages | 1034 | 1034 | legacy knowledge substrate |
| Canonical agents | 88 | 88 | includes P01–P12 product agents |
| Slash commands | 80 | 80 | includes P01–P12 product commands |
| MCP tools | 50 | 50 | includes product evidence broker tools |

Reconciliation report: `docs/product-v2/migration-reconciliation.md`

## Product qualification (truthful)

| Product | Status | Qualification |
| --- | --- | --- |
| P01 Deployment Failure Triage | implemented | fixture-qualified (M2); host smoke `not_run` |
| P02 Apex Test Failure Triage | implemented | fixture-qualified (M2); host smoke `not_run` |
| P03 Access Path Explainer | implemented | fixture-beta; scratch `not_run` |
| P04 Change Impact Planner | implemented | fixture-beta |
| P05 Automation Transaction Profiler | implemented | fixture-beta |
| P06 Release Readiness Review | implemented | fixture-beta |
| P07 Security Posture Review | implemented | fixture-beta |
| P08 Integration Incident Triage | implemented | fixture-beta |
| P09 Data Migration Reconciliation | implemented | fixture-beta |
| P10 Org Health Assessment | implemented | fixture-beta |
| P11 Agentforce Quality Engineer | implemented | fixture-beta |
| P12 Multi-Org Drift Analysis | implemented | fixture-beta |

Overall release posture: **local RC (beta)** — fixture gates pass; Cursor host smoke, live read-only org, and scratch-org behavioral QA recorded as `not_run`.

## Framework core

- Spec: `framework/specification/` (SFAEF 0.9.0-draft)
- Deterministic core: `pipelines/framework/core/`
- Validator: `python3 scripts/validate_framework.py`
- Review ZIP: `python3 scripts/capture_v2_rc_evidence.py`

## Baseline deviations

| Check | Classification | Notes |
| --- | --- | --- |
| `export_skills.py --check` | advisory | Aider hash drift unchanged vs baseline |
| Cursor host smoke | not_run | checklist at `docs/product-v2/cursor-smoke-checklist.md` |
| Scratch-org QA | not_run | guards tested; `qa/scratch/` |

## Not in this release

- V2.1 Change Studio
- V2.2 Governed Operations
- Public Cursor Marketplace publication
- Push / PR / remote mutation
