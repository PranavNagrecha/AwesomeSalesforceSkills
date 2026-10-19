#!/usr/bin/env bash
# The single release gate. Runs every check in order, stops at the first failure.
#
#   bash scripts/release_gate.sh                 # whole gate
#   GATE_ONLY="6 9" bash scripts/release_gate.sh # only the listed step numbers
#
# Env:
#   RELEASE_MIN_HIT1 / RELEASE_MIN_HIT3   held-out retrieval floors (fractions, step 7)
#   RELEASE_MIN_ROUTING_HIT1 / _HIT3      optional floors for saved model-routing runs (step 8)
#   RELEASE_GRADER=1                      also grade the golden evals with scripts/eval_grader.sh (step 9; needs `claude`)
#
# Step 10 compares generated files to HEAD, so run the gate after committing
# regenerated artifacts (publish-mcp.yml enforces the same thing on the tag).
# Never runs scripts/generate_docs.py (starts the 3-hour embedding pass).
set -euo pipefail
cd "$(dirname "$0")/.."

# Defaults = main 3f1853d48 measured 2026-10-20 on a freshly built lexical index (n=154): Hit@1 0.4091, Hit@3 0.5000.
# (An earlier 0.4026/0.5130 came from a stale Oct-2 index; release/1.4.0 with 57 changed skills measures identically.)
: "${RELEASE_MIN_HIT1:=0.4090}"
: "${RELEASE_MIN_HIT3:=0.4999}"
GATE_ONLY="${GATE_ONLY:-}"
passed=()

step() { # step <n> <name> <command...>
  local n="$1" name="$2"; shift 2
  if [[ -n "$GATE_ONLY" && " $GATE_ONLY " != *" $n "* ]]; then return 0; fi
  echo
  echo "=== [$n/10] $name"
  echo "+ $*"
  if "$@"; then
    passed+=("$n $name")
  else
    local rc=$?
    summary "$n $name" "$rc"
  fi
}

summary() {
  echo
  echo "----- release gate -----"
  for p in ${passed[@]+"${passed[@]}"}; do echo "PASS  $p"; done
  if [[ -n "${1:-}" ]]; then echo "FAIL  $1 (exit $2)"; echo "RELEASE GATE: FAIL"; exit 1; fi
  if [[ -n "$GATE_ONLY" ]]; then echo "PARTIAL RUN (steps: $GATE_ONLY) - not a release verdict"; exit 0; fi
  echo "RELEASE GATE: PASS"
}

mcp_suite() { (cd mcp/sfskills-mcp && python3 -m unittest discover -s tests -t tests -v); }
plugin_build_and_check() { python3 scripts/build_plugin.py && python3 scripts/build_plugin.py --check; }
counts_versions_routing() {
  python3 scripts/check_doc_counts.py && python3 scripts/check_release_versions.py && python3 scripts/check_routing_acceptance.py
}
heldout() {
  python3 evals/measurement/run_heldout.py --check &&
  python3 evals/measurement/run_heldout.py --no-embeddings --min-hit1 "$RELEASE_MIN_HIT1" --min-hit3 "$RELEASE_MIN_HIT3" >/dev/null
}
model_routing() { # scores SAVED runs; offline, no API key
  local args=()
  [[ -n "${RELEASE_MIN_ROUTING_HIT1:-}" ]] && args+=(--min-hit1 "$RELEASE_MIN_ROUTING_HIT1")
  [[ -n "${RELEASE_MIN_ROUTING_HIT3:-}" ]] && args+=(--min-hit3 "$RELEASE_MIN_ROUTING_HIT3")
  python3 evals/measurement/run_model_routing.py ${args[@]+"${args[@]}"} >/dev/null
}
evals() {
  python3 evals/scripts/run_evals.py --structure || return
  if [[ "${RELEASE_GRADER:-}" == "1" ]]; then
    python3 evals/scripts/run_evals.py --grader-cmd scripts/eval_grader.sh --output "${TMPDIR:-/tmp}/eval-report.json"
  else
    echo "SKIP  graded evals (set RELEASE_GRADER=1)"
  fi
}

step 1  "skill_sync"                 python3 scripts/skill_sync.py --all --skip-embeddings
step 2  "plugin build + drift check" plugin_build_and_check
step 3  "validate_repo --all"        python3 scripts/validate_repo.py --all
step 4  "pytest tests"               python3 -m pytest tests -q
step 5  "mcp suite"                  mcp_suite
step 6  "doc counts, versions, routing acceptance" counts_versions_routing
step 7  "held-out retrieval floors"  heldout
step 8  "saved model-routing runs"   model_routing
step 9  "golden evals"               evals
step 10 "generated files fresh"      git diff --exit-code -- registry vector_index docs/SKILLS.md .claude-plugin .claude/skills

summary
