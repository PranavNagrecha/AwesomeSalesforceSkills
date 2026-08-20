# Exact Cursor return-package contract

## Required artifact

Cursor must return one ZIP named:

```text
sfskills-v2-cursor-return-YYYYMMDD-HHMMSS.zip
```

The ZIP must contain a single top-level directory of the same name without `.zip`.

## Required tree

```text
REVIEW.md
MANIFEST.json
SHA256SUMS.txt

spec/
  specification-version.txt
  applicable-requirements.csv
  deviations.md

git/
  repository.bundle
  baseline.txt
  head.txt
  branch.txt
  commit-log.txt
  status.txt
  diff.patch
  diff-stat.txt
  tags.txt
  bundle-verify.txt
  offline-reconstruction.txt

source/
  repository-head.tar.gz
  changed-files.txt
  changed-files/                 # exact files changed in reviewed range
  tree-digest.txt

tests/
  test-index.json
  <test-id>.stdout.txt
  <test-id>.stderr.txt
  baseline-comparison.md

builds/
  cursor-plugin.zip
  cursor-plugin-tree.txt
  cursor-plugin-manifest.json
  generated-drift-checks.txt
  install-dry-run.txt
  install-host-path.txt
  uninstall-dry-run.txt

host-smoke/
  cursor/
    capability.json
    discovery.md
    fixture-run.md
    screenshots/                 # screenshots or equivalent host evidence
    raw-session-export/          # sanitized if host supports export
  claude/                        # when milestone requires
  copilot-or-vibes/              # when milestone requires

runs/
  P01/<run-id>/...
  P02/<run-id>/...
  ...
  Each representative run contains input, plan, context manifests,
  checkpoints, evidence index, redacted evidence, handoffs, claims,
  deterministic lint, independent review, output envelope, report, metrics.

qa/
  scenario-index.json
  results/<scenario-id>.json
  benchmark-summary.json
  benchmark-report.md
  context-rot-report.md
  scratch-org-report.md
  scratch-org-cleanup-proof/     # required if scratch lane ran

security/
  policy-matrix.md
  shell-bypass-results.json
  mcp-bypass-results.json
  prompt-injection-results.json
  target-identity-tests.json
  secret-scan.txt
  redaction-report.md
  dependency-report.txt

traceability/
  requirements.csv
  acceptance-matrix.md
  product-status.json
  known-limitations.md

integrity/
  review-package-validator.txt
  checksum-verification.txt
  archive-list.txt
```

## MANIFEST requirements

`MANIFEST.json` must validate against `review-manifest.schema.json` and include:

- branch, baseline SHA, head SHA, local-only confirmation, clean-tree confirmation;
- exact local commits and tags in the reviewed range;
- every test command, working directory, start/end time, duration, real exit code, stdout/stderr paths, required/optional status;
- build and run artifact paths;
- unrun checks and reasons;
- known limitations;
- Git bundle, checksum, offline reconstruction, and secret-scan results.

## Reproducibility

Before packaging, the builder must:

1. create a Git bundle containing the baseline, head, and milestone tags;
2. clone/reconstruct the reviewed head into a fresh temporary directory from that bundle;
3. verify the reconstructed tree digest matches the source archive and original head;
4. run the review-package validator;
5. verify all checksums;
6. scan for secrets;
7. fail packaging if required evidence is absent.

## Test truth

A test is “passed” only when the ZIP contains its exact command, cwd, stdout, stderr, exit code, and duration. Manual host checks must be labelled manual and include actual host evidence. A fixture run is not a live-org run. A read-only org smoke is not scratch known-truth QA.

## Failure packages

If Cursor stops at a P0 blocker, it must still produce the same structure to the extent possible, set the milestone/product status to blocked, include failing logs and exact head, and never claim completion.

## Prohibited contents

- credentials, auth URLs, access tokens, private keys, session IDs;
- unsanitized customer data;
- hidden chain-of-thought;
- fabricated screenshots/logs;
- files claimed in `REVIEW.md` but omitted from the archive.

## Completion versus blocked packaging

The review-package builder MUST expose two unambiguous modes:

- **Completion mode** refuses to package when the tree is dirty, any required test failed, a required artifact is absent, generated output is stale, reconstruction/checksums fail, or a secret is detected.
- **Blocked mode** is allowed solely to preserve and review a real blocker. It sets `MANIFEST.json.status` to `blocked` or `failed`, includes every failing log, reports the last passing milestone and product qualification, and does not claim later acceptance criteria. Git reconstruction, package checksums, tree cleanliness, source integrity, and secret scanning still MUST pass.

A failed required test in a `completed` or `partial` package is invalid. A blocked package is evidence for diagnosis, not a release candidate.

## Required MANIFEST fields

`MANIFEST.json` MUST validate against the supplied `schemas/review-manifest.schema.json`. In addition to repository identity and integrity, it records:

- specification version, phase, package status, milestones, commits, and tags;
- product-by-product status, highest qualification, representative run paths, and blockers;
- each test's exact command, working directory, UTC start/end, duration, exit code, required flag, stdout, stderr, and relevant environment versions;
- actual host smoke status and evidence paths;
- structured unrun checks with reason and release impact;
- requirement traceability and deviation paths.

The test index and manifest MUST agree. Every referenced relative path MUST exist in the archive.
