#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONDONTWRITEBYTECODE=1

printf '== Specification validation ==\n'
python3 "$ROOT/tools/validate_spec_package.py" "$ROOT"

printf '\n== Validator unit tests ==\n'
(
  cd "$ROOT"
  PYTHONPATH=. python3 -m unittest discover -s tools/tests -p 'test_*.py' -v
)

printf '\n== Reference kernel tests ==\n'
(
  cd "$ROOT/reference-kernel"
  PYTHONPATH=. python3 -m unittest discover -s tests -p 'test_*.py' -v
)

printf '\n== Project inspector reference tests ==\n'
(
  cd "$ROOT/reference-components/project-inspector/repo-files"
  PYTHONPATH=. python3 -m unittest discover -s tests/product -p 'test_*.py' -v
)

printf '\nPASS: all package checks completed\n'
