# Scratch-org behavioral QA (M3)

This directory is a **skeleton**. Disposable scratch-org behavioral QA is **not run** in this milestone.

See `NOT_RUN.json` and `docs/product-v2/milestones/m3-behavioral-qa.md`.

## Intended layout (future)

```text
qa/scratch/
  project/                   minimal versioned SFDX fixture project
  scenarios/<id>/            metadata/data/setup and truth manifest
  scripts/create.py          guarded creation (opt-in + Dev Hub allowlist)
  scripts/setup.py           scenario mutation, never model-exposed
  scripts/capture.py         existing result IDs/evidence
  scripts/run_product.py     actual adapter/product invocation
  scripts/grade.py           deterministic hard grading
  scripts/destroy.py         unconditional cleanup
```

## Guards (already required)

1. Protected CI context **or** explicit local opt-in (`SFSKILLS_SCRATCH_OPT_IN=1`).
2. Dev Hub against an allowlist — never implied from the user's default org.
3. One-day scratch expiration and a unique marker.
4. Product-read-only authority **after** capture.
5. Destroy in `finally`.
6. Never expose scratch setup commands as MCP tools.

No Dev Hub is required to validate this skeleton.
