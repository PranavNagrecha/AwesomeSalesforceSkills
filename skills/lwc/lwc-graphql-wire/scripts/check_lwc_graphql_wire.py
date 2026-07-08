#!/usr/bin/env python3
"""Checker script for the lwc-graphql-wire skill.

Recursively scans `--manifest-dir` for `.js` files under `lwc/*` bundles and
flags GraphQL-wire anti-patterns documented in this skill's references.

Two modules ship the adapter and the checks are scoped by module:
  * `lightning/graphql` (v2) — recommended; adds optional fields, dynamic
    query construction, and `executeMutation` writes; refreshes via a `refresh`
    method on the emitted result.
  * `lightning/uiGraphQLApi` (v1) — Mobile Offline only; read-only wire;
    refreshes via `refreshGraphQL(result)`.

Checks:
  1. A `gql` literal containing JS interpolation (`${ ... }`) in a v1 file.
     Interpolation is NOT reactive on v1 — declare a query variable and pass it
     via `variables: '$vars'`. (Skipped for v2 files, where interpolation is a
     supported feature for dynamic query construction. The v2 misuse — routing
     reactive per-record filter data through interpolation instead of a `$`
     variable — cannot be told apart from legitimate dynamic queries statically,
     so it is left to review rather than false-flagged here.)
  2. A file importing a GraphQL module that calls the wrong refresh helper:
     `refreshApex` (that is for `@wire(<apexMethod>)`), or `refreshGraphQL`
     inside a v2 (`lightning/graphql`) file (v2 uses `result.refresh()`).
  3. A `gql` literal that uses `edges` but not `pageInfo` — breaks pagination.
  4. A `gql` literal containing `mutation` in a file that does NOT import
     `executeMutation`. A mutation belongs in an `executeMutation` call (v2),
     never inside the wired query. If `executeMutation` is imported the mutation
     literal is assumed legitimate and not flagged.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_lwc_graphql_wire.py [--help]
    python3 check_lwc_graphql_wire.py --manifest-dir path/to/force-app
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------- regex helpers --------------------------------------------------

# Match a `gql\` ... \`` tagged template literal. Non-greedy body, DOTALL so
# multi-line queries match. We deliberately use a simple regex here rather
# than a full JS parser — good enough to locate gql blocks for heuristic scan.
GQL_BLOCK_RE = re.compile(r"gql\s*`([^`]*)`", re.DOTALL)

JS_INTERPOLATION_RE = re.compile(r"\$\{[^}]*\}")
MUTATION_KEYWORD_RE = re.compile(r"\bmutation\b", re.IGNORECASE)
EDGES_TOKEN_RE = re.compile(r"\bedges\b")
PAGEINFO_TOKEN_RE = re.compile(r"\bpageInfo\b")

V1_IMPORT_RE = re.compile(r"from\s+['\"]lightning/uiGraphQLApi['\"]")
V2_IMPORT_RE = re.compile(r"from\s+['\"]lightning/graphql['\"]")
REFRESH_APEX_RE = re.compile(r"\brefreshApex\s*\(")
REFRESH_GRAPHQL_RE = re.compile(r"\brefreshGraphQL\s*\(")
EXECUTE_MUTATION_RE = re.compile(r"\bexecuteMutation\b")


# ---------- core scan ------------------------------------------------------

def _line_number(text: str, offset: int) -> int:
    """Return the 1-indexed line number for a character offset."""
    return text.count("\n", 0, offset) + 1


def _iter_lwc_js_files(manifest_dir: Path):
    """Yield .js files that live under any `lwc/<bundle>/` directory."""
    for js_path in manifest_dir.rglob("*.js"):
        # Skip test specs and jsconfig by looking at path parts for /lwc/.
        parts = js_path.parts
        if "lwc" not in parts:
            continue
        # Ignore minified bundles or node_modules if present.
        if "node_modules" in parts:
            continue
        yield js_path


def _check_file(js_path: Path) -> list[str]:
    """Return a list of concrete line-numbered findings for one JS file."""
    findings: list[str] = []

    try:
        source = js_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [f"{js_path}: could not read file ({exc})"]

    imports_v1 = bool(V1_IMPORT_RE.search(source))
    imports_v2 = bool(V2_IMPORT_RE.search(source))
    imports_graphql_module = imports_v1 or imports_v2
    imports_execute_mutation = bool(EXECUTE_MUTATION_RE.search(source))

    # Check 2: GraphQL file calling the wrong refresh helper.
    if imports_graphql_module:
        for match in REFRESH_APEX_RE.finditer(source):
            line = _line_number(source, match.start())
            helper = "result.refresh()" if imports_v2 else "refreshGraphQL(this.wiredResult)"
            findings.append(
                f"{js_path}:{line}: refreshApex() called in a file that imports a "
                f"GraphQL module. refreshApex is for @wire(apexMethod) — use {helper} instead."
            )
    # v2 has no refreshGraphQL — it refreshes via result.refresh().
    if imports_v2 and not imports_v1:
        for match in REFRESH_GRAPHQL_RE.finditer(source):
            line = _line_number(source, match.start())
            findings.append(
                f"{js_path}:{line}: refreshGraphQL() called in a 'lightning/graphql' (v2) "
                "file. v2 does not export refreshGraphQL — call the refresh method on the "
                "emitted result instead (await this.<wiredResult>.refresh())."
            )

    # Walk every gql`...` block and apply per-block checks (1, 3, 4).
    for block_match in GQL_BLOCK_RE.finditer(source):
        body = block_match.group(1)
        block_start_line = _line_number(source, block_match.start())

        # Check 1: JS interpolation inside a v1 gql literal (not reactive on v1).
        # Skipped for v2, where interpolation is a supported dynamic-query feature.
        if imports_v1 and not imports_v2:
            for interp in JS_INTERPOLATION_RE.finditer(body):
                rel_line = body.count("\n", 0, interp.start())
                line = block_start_line + rel_line
                findings.append(
                    f"{js_path}:{line}: gql template literal contains ${{...}} JS "
                    "interpolation in a 'lightning/uiGraphQLApi' (v1) file. Declare a "
                    "query variable and pass it via variables: '$vars' — v1 interpolation "
                    "is not reactive."
                )

        # Check 4: mutation keyword inside a wired gql literal. Skipped when the
        # file imports executeMutation, where a mutation literal is expected (v2).
        if not imports_execute_mutation:
            mutation_match = MUTATION_KEYWORD_RE.search(body)
            if mutation_match:
                rel_line = body.count("\n", 0, mutation_match.start())
                line = block_start_line + rel_line
                findings.append(
                    f"{js_path}:{line}: gql template literal contains 'mutation' but the "
                    "file does not import executeMutation. The wired query is read-only — "
                    "run writes via executeMutation (lightning/graphql v2) or UI API / "
                    "imperative Apex; never embed a mutation in the wired query."
                )

        # Check 3: edges without pageInfo in the same literal.
        if EDGES_TOKEN_RE.search(body) and not PAGEINFO_TOKEN_RE.search(body):
            # Report at the first edges occurrence for a concrete line.
            edges_match = EDGES_TOKEN_RE.search(body)
            rel_line = body.count("\n", 0, edges_match.start())
            line = block_start_line + rel_line
            findings.append(
                f"{js_path}:{line}: gql literal uses 'edges' without 'pageInfo'. "
                "Add pageInfo { endCursor hasNextPage } for reliable cursor pagination."
            )

    return findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check LWC GraphQL wire usage for common anti-patterns.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


def check_lwc_graphql_wire(manifest_dir: Path) -> list[str]:
    """Return a list of issue strings found under the manifest directory."""
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    scanned = 0
    for js_path in _iter_lwc_js_files(manifest_dir):
        scanned += 1
        issues.extend(_check_file(js_path))

    if scanned == 0:
        issues.append(
            f"No LWC .js files found under {manifest_dir}. "
            "Point --manifest-dir at a directory containing an lwc/ folder."
        )

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_lwc_graphql_wire(manifest_dir)

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
