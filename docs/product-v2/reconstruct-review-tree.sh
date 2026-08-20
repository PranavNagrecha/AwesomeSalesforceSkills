#!/usr/bin/env bash
# Rebuild a product review tree from baseline + the review ZIP diff.
# Usage:
#   git clone <sfskills> review-tree && cd review-tree
#   git checkout d5f068887
#   git apply /path/to/unzipped/AGAINST_BASELINE.diff
set -euo pipefail
ROOT="${1:?path to a checkout of baseline d5f068887}"
DIFF="${2:?path to AGAINST_BASELINE.diff from the review ZIP}"
cd "$ROOT"
git apply "$DIFF"
echo "Applied diff. Run: python3 -m unittest tests.product.test_phase1 tests.product.test_phase2 tests.product.test_project_discover"
