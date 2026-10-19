#!/usr/bin/env bash
# Grader for evals/scripts/run_evals.py --grader-cmd. Reads one JSON payload on
# stdin ({skill, case_name, priority, case_markdown}), asks headless Claude to
# score the case's rubric, prints {"rubric": {...}, "notes": "..."} on stdout.
# Exit 3 if the `claude` binary is missing. Any other failure exits non-zero,
# which run_evals.py counts as a failed case.
set -euo pipefail

command -v claude >/dev/null 2>&1 || { echo "eval_grader: 'claude' not on PATH" >&2; exit 3; }

payload="$(cat)"
prompt="$(printf '%s' "$payload" | python3 -c '
import json, sys
p = json.load(sys.stdin)
print("You are an eval grader. Score the rubric items in the eval case below, each 1-5,")
print("judging the reference answer and MUST/MUST NOT lists as the standard a good answer meets.")
print("Reply with ONLY strict JSON, no prose, no code fence:")
print("{\"rubric\": {\"<rubric item>\": <1-5>}, \"notes\": \"<one sentence>\"}")
print()
print(p["case_markdown"])
')"

out="$(claude -p --model sonnet --tools "" --disable-slash-commands --no-session-persistence \
  --output-format text "$prompt")"

# Tolerate a stray code fence; keep the outermost {...}. Validity is checked by run_evals.py.
printf '%s' "$out" | python3 -c '
import sys
t = sys.stdin.read()
print(t[t.index("{"): t.rindex("}") + 1])
'
