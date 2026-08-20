# Disposable scratch-org behavioral QA lab

## Components

```text
qa/scratch/
  project/                   minimal versioned SFDX fixture project
  scenarios/<id>/            metadata/data/setup and truth manifest
  scripts/create.py          guarded creation
  scripts/setup.py           scenario mutation, never model-exposed
  scripts/capture.py         existing result IDs/evidence
  scripts/run_product.py     actual adapter/product invocation
  scripts/grade.py           deterministic hard grading
  scripts/destroy.py         unconditional cleanup
```

## Guard sequence

1. Verify protected CI context or explicit local opt-in.
2. Verify Dev Hub against allowlist.
3. Create scratch org with one-day expiration and unique marker.
4. Verify org type, marker, and username before setup mutation.
5. Deploy only versioned scenario fixture.
6. Generate the known failure/test/access condition.
7. Capture IDs and switch to product-read-only authority.
8. Run actual product through the host or labelled harness.
9. Grade claim/evidence result.
10. Sanitize artifacts.
11. Destroy scratch org in `finally`/unconditional job.
12. Verify deletion and record proof.

## Never do

- use a sandbox/production/customer org as a scenario target;
- expose scratch setup commands as model tools;
- omit cleanup because grading failed;
- upload auth URLs or tokens;
- call a fixture run “live behavioral QA.”
