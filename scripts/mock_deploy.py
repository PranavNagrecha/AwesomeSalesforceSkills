#!/usr/bin/env python3
"""Validate a build's artefacts against a Salesforce org WITHOUT deploying.

Automates, as a reusable CLI, what `examples/builds/case-onboarding/reports/MOCK-DEPLOY-M1.md`
did by hand: assemble the artefacts of one or more build steps into a source-format
tree, then hand that tree to `sf project deploy start --dry-run` (`checkOnly: true`)
against a real org so platform rules no skill checker encodes (required layout
fields, business-process file-stem matching, ...) get caught before anyone deploys
for real.

Contract: `standards/build-orchestration.md` (v1, 2026-09-05) — this script IS the
"validate-only command the human may run" named in section 1, and section 5's
deploy deny-list is why it never accepts a flag that could turn `--dry-run` off.
Python Tooling Rules (`CLAUDE.md`): repo-level framework script, stdlib only.

Design rules this file obeys:

* stdlib only — no third-party imports;
* `--dry-run` is hard-coded into the `sf` invocation and there is no argument
  (no `--deploy`, no `--dry-run-only` toggle) that can remove it — the CLI
  surface simply has no path to a real deploy;
* the script only ever writes inside the directory it creates for this run
  (`--out`, default `<build_dir>/reports/mock-deploy/<UTC timestamp>/`); it
  never edits `plan.json`, never edits anything under `artefacts/`, and never
  writes into the build directory itself;
* step/milestone selection, artefact copying, manifest merging and result
  parsing are all separate, unit-testable functions — see
  `tests/test_mock_deploy.py`, which mocks `subprocess.run` so no `sf` CLI is
  ever invoked by the test suite.

Typical use — validate milestone M1 of a build against a scratch/dev org::

    python3 scripts/mock_deploy.py .sfskills/builds/case-onboarding/plan.json \\
        --org-alias sfskills-dev --milestone M1

Exit codes: 0 = the org validated the deploy (`status: Succeeded`),
1 = the org rejected it (`status: Failed`), 2 = this script or the `sf` CLI
could not produce a usable result (bad plan, missing `sf`, unparseable output).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import NamedTuple
from xml.sax.saxutils import escape

METADATA_NS = "{http://soap.sforce.com/2006/04/metadata}"
DEFAULT_API_VERSION = "62.0"
DEFAULT_STATUSES = ("built", "tested", "documented")


# --------------------------------------------------------------------------
# Plan / step selection
# --------------------------------------------------------------------------

def load_plan(plan_path: Path) -> dict:
    return json.loads(plan_path.read_text(encoding="utf-8"))


def select_steps(plan: dict, milestone_ids: list[str], step_ids: list[str]) -> list[dict]:
    """Pick the steps to validate, in the order they appear in plan['steps'].

    Explicit `--milestone`/`--step` selection is a union of both filters and
    ignores step status (the human named exactly what they want validated).
    With neither given, the default is every step whose status is one of
    DEFAULT_STATUSES — the states a step reaches once its own artefacts exist.
    """
    milestone_set = set(milestone_ids or [])
    step_set = set(step_ids or [])
    steps = plan.get("steps", [])
    if milestone_set or step_set:
        return [
            s for s in steps
            if s.get("milestone") in milestone_set or s.get("id") in step_set
        ]
    return [s for s in steps if s.get("status") in DEFAULT_STATUSES]


# --------------------------------------------------------------------------
# Artefact assembly (mode: source)
# --------------------------------------------------------------------------

class CopyResult(NamedTuple):
    """Result of `copy_artefacts`.

    * copied — paths copied, relative to dest_root, in the order copied.
    * skipped — count of files under the selected steps' artefact directories
      that were deliberately excluded (package.xml, `*.md` build notes,
      dotfiles). Directories are never counted either way.
    """

    copied: list[Path]
    skipped: int


def copy_artefacts(
    build_dir: Path, artefacts_root: str, step_ids: list[str], dest_root: Path
) -> CopyResult:
    """Copy EVERY file under artefacts/<step>/ into dest_root, preserving each
    file's sub-path (objects/Case/fields/..., layouts/..., email/case_intake/...,
    lwc/foo/..., etc) and the directory structure around it — EXCEPT:

    * `package.xml` — merged separately (see `merge_package_xml` / --mode manifest);
    * `*.md` files — build notes (deploy-order.md, decision notes, runbooks),
      never deployable metadata;
    * dotfiles — editor/OS artefacts, never Salesforce source.

    A source-format component is frequently more than one file next to its
    `-meta.xml` sidecar: an EmailTemplate's `.email` body, an Apex class's
    `.cls`, a static resource's `.resource`, an LWC/Aura bundle's `.js`/
    `.html`/`.css`. Copying only `*.xml` (the previous behaviour) silently
    dropped every one of those bodies, and `sf project deploy start` then
    fails with `ExpectedSourceFilesError: ... Expected source files for
    type '<Type>'` — a defect found live against
    `.sfskills/builds/case-onboarding` (an EmailTemplate's `.email` body never
    reached the assembled tree). Copying everything except the three
    exclusions above fixes every source-format type at once, not just email.

    Returns a `CopyResult` — the paths copied (relative to dest_root) and a
    count of files skipped by the exclusion rules — for callers/tests that
    want to assert on the tree shape or report on it (see `render_summary`).
    """
    copied: list[Path] = []
    skipped = 0
    for step_id in step_ids:
        step_dir = build_dir / artefacts_root / step_id
        if not step_dir.is_dir():
            continue
        for src in sorted(step_dir.rglob("*")):
            if not src.is_file():
                continue
            if src.name == "package.xml" or src.suffix.lower() == ".md" or src.name.startswith("."):
                skipped += 1
                continue
            rel = src.relative_to(step_dir)
            dest = dest_root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            copied.append(rel)
    return CopyResult(copied=copied, skipped=skipped)


def pick_api_version(
    build_dir: Path, artefacts_root: str, step_ids: list[str], fallback: str = DEFAULT_API_VERSION
) -> str:
    """The first <version> text found in a selected step's package.xml, in
    step order; fallback (default 62.0) if none of them has one.
    """
    for step_id in step_ids:
        pkg = build_dir / artefacts_root / step_id / "package.xml"
        if not pkg.is_file():
            continue
        try:
            root = ET.parse(pkg).getroot()
        except ET.ParseError:
            continue
        version_el = root.find(f"{METADATA_NS}version")
        if version_el is not None and version_el.text and version_el.text.strip():
            return version_el.text.strip()
    return fallback


def write_sfdx_project(out_dir: Path, api_version: str) -> Path:
    payload = {
        "packageDirectories": [{"path": "force-app", "default": True}],
        "namespace": "",
        "sourceApiVersion": api_version,
    }
    path = out_dir / "sfdx-project.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


# --------------------------------------------------------------------------
# Manifest assembly (mode: manifest)
# --------------------------------------------------------------------------

def _types_from_root(root: ET.Element) -> dict[str, set[str]]:
    """Extract a {type name: {member, ...}} map from a parsed <Package> root."""
    types: dict[str, set[str]] = {}
    for t in root.findall(f"{METADATA_NS}types"):
        name_el = t.find(f"{METADATA_NS}name")
        if name_el is None or not (name_el.text and name_el.text.strip()):
            continue
        name = name_el.text.strip()
        bucket = types.setdefault(name, set())
        for m in t.findall(f"{METADATA_NS}members"):
            if m.text and m.text.strip():
                bucket.add(m.text.strip())
    return types


def _types_from_text(xml_text: str) -> dict[str, set[str]]:
    """Same as `_types_from_root` but from an in-memory package.xml string.
    An unparseable document contributes no types rather than raising, matching
    `merge_package_xml`'s tolerance of malformed/missing input files.
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return {}
    return _types_from_root(root)


def merge_package_xml(paths: list[Path], version: str) -> str:
    """Merge one or more package.xml files by <name> type, union-ing and
    sorting <members>, and sort the <types> blocks themselves by type name —
    matching the shape of the hand-built
    examples/builds/case-onboarding/reports/MILESTONE-M1-package.xml.
    """
    types: dict[str, set[str]] = {}
    for p in paths:
        p = Path(p)
        if not p.is_file():
            continue
        try:
            root = ET.parse(p).getroot()
        except ET.ParseError:
            continue
        for name, members in _types_from_root(root).items():
            types.setdefault(name, set()).update(members)

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<Package xmlns="http://soap.sforce.com/2006/04/metadata">',
    ]
    for name in sorted(types):
        lines.append("    <types>")
        for member in sorted(types[name]):
            lines.append(f"        <members>{escape(member)}</members>")
        lines.append(f"        <name>{escape(name)}</name>")
        lines.append("    </types>")
    lines.append(f"    <version>{escape(version)}</version>")
    lines.append("</Package>")
    return "\n".join(lines) + "\n"


def diff_manifest_types(
    report_types: dict[str, set[str]], merged_types: dict[str, set[str]]
) -> list[tuple[str, str, str]]:
    """Compare two {type: {member, ...}} maps produced by `_types_from_*`.

    Returns a sorted list of (type, member, side) triples for every member
    present on only one side — side is "report-only" or "steps-only". An
    empty list means the two manifests are equivalent (same types, same
    members per type; ordering/whitespace in the source files is irrelevant).
    """
    diffs: list[tuple[str, str, str]] = []
    for type_name in sorted(set(report_types) | set(merged_types)):
        report_members = report_types.get(type_name, set())
        merged_members = merged_types.get(type_name, set())
        for member in sorted(report_members - merged_members):
            diffs.append((type_name, member, "report-only"))
        for member in sorted(merged_members - report_members):
            diffs.append((type_name, member, "steps-only"))
    return diffs


MAX_DRIFT_ITEMS_SHOWN = 10


class ManifestResolution(NamedTuple):
    """Result of `resolve_manifest_text`.

    * source — description of what `xml_text` came from ("merged:<ids>" or
      the milestone report path when --prefer-report-manifest was honoured).
    * xml_text — the manifest text to write to package.xml.
    * warning — a one-line WARN string to print to stderr, or None when there
      was nothing to warn about (no report to compare, or no drift found).
    * drift_note — markdown body for summary.md's "Manifest drift" heading,
      or "" when there is nothing to say (no milestone report was found).
    """

    source: str
    xml_text: str
    warning: str | None = None
    drift_note: str = ""


def resolve_manifest_text(
    build_dir: Path,
    artefacts_root: str,
    milestone_ids: list[str],
    step_ids_arg: list[str],
    selected_ids: list[str],
    version: str,
    prefer_report_manifest: bool = False,
) -> ManifestResolution:
    """Manifest mode's source of truth is always the type-merged manifest
    freshly built from the selected steps' package.xml files (F-18: the
    milestone verifier's report can go stale the moment a step's own
    package.xml is rebuilt after the report was written).

    When exactly one milestone was named (and no --step mixed in) and the
    milestone verifier's own reports/MILESTONE-<id>-package.xml exists on
    disk, that file is additionally compared against the fresh merge:

    * identical (same types, same members per type) — the merge is used;
      summary.md notes the match under "Manifest drift" and nothing is
      printed to stderr.
    * different — a WARN is printed naming up to MAX_DRIFT_ITEMS_SHOWN of the
      differing members, summary.md records the full drift, and the steps'
      merge is used UNLESS `prefer_report_manifest` is set, in which case the
      report's own text is used instead (the WARN is still printed either
      way — this flag reproduces the old, stale-prone behaviour on purpose).

    When no milestone report exists on disk, the merge is used silently: no
    warning, no drift note (there's nothing to compare against).
    """
    package_paths = [build_dir / artefacts_root / sid / "package.xml" for sid in selected_ids]
    merged_xml = merge_package_xml(package_paths, version)
    merged_source = "merged:" + ",".join(selected_ids)

    single_milestone = bool(milestone_ids) and len(milestone_ids) == 1 and not step_ids_arg
    if not single_milestone:
        return ManifestResolution(source=merged_source, xml_text=merged_xml)

    report_path = build_dir / "reports" / f"MILESTONE-{milestone_ids[0]}-package.xml"
    if not report_path.is_file():
        return ManifestResolution(source=merged_source, xml_text=merged_xml)

    report_xml = report_path.read_text(encoding="utf-8")
    report_rel = report_path.relative_to(build_dir)

    diff = diff_manifest_types(_types_from_text(report_xml), _types_from_text(merged_xml))
    if not diff:
        drift_note = f"None — the steps' merge matches `{report_rel}`.\n"
        return ManifestResolution(
            source=merged_source, xml_text=merged_xml, warning=None, drift_note=drift_note
        )

    milestone_id = milestone_ids[0]
    shown = diff[:MAX_DRIFT_ITEMS_SHOWN]
    shown_text = ", ".join(f"{t}:{m} ({side})" for t, m, side in shown)
    if len(diff) > MAX_DRIFT_ITEMS_SHOWN:
        shown_text += f", … ({len(diff) - MAX_DRIFT_ITEMS_SHOWN} more)"

    if prefer_report_manifest:
        action = "using the milestone report (--prefer-report-manifest)"
        used_source = str(report_path)
        used_xml = report_xml
    else:
        action = "using the steps' merge"
        used_source = merged_source
        used_xml = merged_xml

    warning = (
        f"WARN: milestone manifest {report_rel} differs from the steps' "
        f"package.xml files — {len(diff)} member(s) differ: {shown_text}; "
        f"{action}. Re-run milestone-verifier {milestone_id} to refresh the report."
    )

    drift_lines = "\n".join(f"- {t}:{m} ({side})" for t, m, side in shown)
    shown_suffix = f" (showing first {MAX_DRIFT_ITEMS_SHOWN})" if len(diff) > MAX_DRIFT_ITEMS_SHOWN else ""
    used_label = "milestone report (--prefer-report-manifest)" if prefer_report_manifest else "steps' merge"
    drift_note = (
        f"`{report_rel}` differs from the steps' merge — {len(diff)} member(s) differ"
        f"{shown_suffix}:\n\n"
        f"{drift_lines}\n\n"
        f"Used: {used_label}.\n"
    )

    return ManifestResolution(
        source=used_source, xml_text=used_xml, warning=warning, drift_note=drift_note
    )


# --------------------------------------------------------------------------
# sf CLI invocation + result handling
# --------------------------------------------------------------------------

def build_sf_command(mode: str, org_alias: str, manifest_name: str = "package.xml") -> list[str]:
    """The `sf` command line. --dry-run is always present — there is no
    parameter anywhere in this script that can remove it.
    """
    cmd = ["sf", "project", "deploy", "start"]
    if mode == "manifest":
        cmd += ["--manifest", manifest_name]
    else:
        cmd += ["--source-dir", "force-app"]
    cmd += ["--dry-run", "--target-org", org_alias, "--wait", "10", "--json"]
    return cmd


def strip_json_prefix(text: str) -> str:
    """The `sf` CLI sometimes prints an update-available warning (or other
    plain-text noise) before its --json payload. Return the text starting at
    the first line that looks like the start of a JSON object.
    """
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.lstrip().startswith("{"):
            return "\n".join(lines[i:])
    raise ValueError("no JSON object found in CLI output")


def exit_code_for_status(status: str | None) -> int:
    if status == "Succeeded":
        return 0
    if status == "Failed":
        return 1
    return 2


def render_summary(
    parsed: dict | None,
    mode: str,
    org_alias: str,
    manifest_resolution: ManifestResolution | None = None,
    plan_only: bool = False,
    copy_result: CopyResult | None = None,
) -> str:
    lines = ["# Mock deploy result", "", f"- org: `{org_alias}`", f"- mode: `{mode}`"]

    if copy_result is not None:
        lines.append(
            f"- files: {len(copy_result.copied)} file(s) copied, {copy_result.skipped} "
            "skipped (package.xml/notes)"
        )

    if plan_only:
        lines.append("- status: **not run (--plan-only)**")
    else:
        result = parsed.get("result") if isinstance(parsed, dict) else None
        result = result if isinstance(result, dict) else {}

        status = result.get("status", "Unknown")
        check_only = result.get("checkOnly", True)
        details = result.get("details") if isinstance(result.get("details"), dict) else {}
        successes = details.get("componentSuccesses") or []
        failures = details.get("componentFailures") or []
        total = result.get("numberComponentsTotal", len(successes) + len(failures))
        errors = result.get("numberComponentErrors", len(failures))

        rows: list[tuple[str, str, str]] = []
        for c in successes:
            rows.append((c.get("componentType", ""), c.get("fullName", ""), "ok"))
        for c in failures:
            problem = c.get("problem", "unknown error")
            rows.append((c.get("componentType", ""), c.get("fullName", ""), f"FAIL — {problem}"))
        rows.sort(key=lambda r: (r[0], r[1]))

        lines += [
            f"- status: **{status}**",
            f"- checkOnly: `{check_only}`",
            f"- components: {total} total, {len(successes)} ok, {errors} error(s)",
            "",
            "| Type | Component | Result |",
            "|---|---|---|",
        ]
        for component_type, name, outcome in rows:
            lines.append(f"| {component_type} | {name} | {outcome} |")

    if manifest_resolution is not None and manifest_resolution.drift_note:
        lines += ["", "## Manifest drift", "", manifest_resolution.drift_note.rstrip("\n")]

    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mock_deploy.py",
        description=(
            "Validation only. Assembles one or more build steps' artefacts into a "
            "source-format tree and runs `sf project deploy start --dry-run` "
            "(checkOnly) against an org — nothing is ever deployed. There is no "
            "flag to disable --dry-run and no --deploy option; that is by design."
        ),
    )
    parser.add_argument("plan", help="Path to the build's plan.json")
    parser.add_argument(
        "--org-alias", required=True,
        help="sf CLI org alias to validate against (the org is read, never written to)",
    )
    parser.add_argument(
        "--milestone", action="append", default=[], metavar="ID",
        help="Milestone id to validate (repeatable). Default: every step whose "
             "status is built, tested or documented.",
    )
    parser.add_argument(
        "--step", action="append", default=[], metavar="ID",
        help="Step id to validate (repeatable). Combines with --milestone.",
    )
    parser.add_argument(
        "--mode", choices=["source", "manifest"], default="source",
        help="source (default) = --source-dir force-app. manifest = --manifest "
             "package.xml, always freshly merged from the selected steps' "
             "package.xml files by type; when exactly one milestone is given "
             "and reports/MILESTONE-<id>-package.xml exists, it is compared "
             "against that merge and a WARN is printed on drift (see "
             "--prefer-report-manifest).",
    )
    parser.add_argument(
        "--prefer-report-manifest", action="store_true",
        help="--mode manifest only. On drift between the milestone verifier's "
             "reports/MILESTONE-<id>-package.xml and the steps' package.xml "
             "files, use the report's text anyway (to reproduce a report "
             "exactly) instead of the steps' merge. The drift WARN is still "
             "printed either way. Has no effect when the two already match "
             "or when no milestone report exists.",
    )
    parser.add_argument(
        "--out", default=None,
        help="Output directory. Default: <build_dir>/reports/mock-deploy/<UTC "
             "timestamp>/. Nothing is ever written outside this directory.",
    )
    parser.add_argument(
        "--plan-only", action="store_true",
        help="Do everything except invoke the `sf` CLI: assemble the source "
             "tree, write the manifest (--mode manifest), and write "
             "summary.md with 'status: not run (--plan-only)'. Useful to "
             "inspect manifest drift without contacting an org.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    plan_path = Path(args.plan).resolve()
    if not plan_path.is_file():
        print(f"error: plan not found: {plan_path}", file=sys.stderr)
        return 2
    try:
        plan = load_plan(plan_path)
    except json.JSONDecodeError as exc:
        print(f"error: could not parse plan.json: {exc}", file=sys.stderr)
        return 2

    build_dir = plan_path.parent
    artefacts_root = plan.get("artefacts_root", "artefacts")

    selected = select_steps(plan, args.milestone, args.step)
    if not selected:
        print(
            "error: no steps selected — check --milestone/--step, or that some "
            "step's status is built, tested or documented",
            file=sys.stderr,
        )
        return 2
    step_ids = [s["id"] for s in selected]

    if args.out:
        out_dir = Path(args.out).resolve()
    else:
        timestamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
        out_dir = build_dir / "reports" / "mock-deploy" / timestamp
    out_dir.mkdir(parents=True, exist_ok=True)

    force_app_dir = out_dir / "force-app" / "main" / "default"
    force_app_dir.mkdir(parents=True, exist_ok=True)
    copy_result = copy_artefacts(build_dir, artefacts_root, step_ids, force_app_dir)

    api_version = pick_api_version(build_dir, artefacts_root, step_ids)
    write_sfdx_project(out_dir, api_version)

    manifest_name = "package.xml"
    manifest_resolution: ManifestResolution | None = None
    if args.mode == "manifest":
        manifest_resolution = resolve_manifest_text(
            build_dir, artefacts_root, args.milestone, args.step, step_ids, api_version,
            prefer_report_manifest=args.prefer_report_manifest,
        )
        (out_dir / manifest_name).write_text(manifest_resolution.xml_text, encoding="utf-8")
        if manifest_resolution.warning:
            print(manifest_resolution.warning, file=sys.stderr)

    cmd = build_sf_command(args.mode, args.org_alias, manifest_name)
    assert "--dry-run" in cmd  # hard invariant: this script never deploys

    if args.plan_only:
        summary = render_summary(
            None, args.mode, args.org_alias, manifest_resolution, plan_only=True,
            copy_result=copy_result,
        )
        (out_dir / "summary.md").write_text(summary, encoding="utf-8")
        print(summary)
        print(f"output: {out_dir}")
        return 0

    try:
        proc = subprocess.run(cmd, cwd=str(out_dir), capture_output=True, text=True)
    except FileNotFoundError:
        print("error: `sf` CLI not found on PATH", file=sys.stderr)
        return 2

    raw_stdout = proc.stdout or ""
    raw_stderr = proc.stderr or ""
    try:
        parsed = json.loads(strip_json_prefix(raw_stdout))
    except (ValueError, json.JSONDecodeError) as exc:
        (out_dir / "result.json").write_text(
            json.dumps(
                {"error": str(exc), "raw_stdout": raw_stdout, "raw_stderr": raw_stderr},
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"error: could not parse `sf` CLI output as JSON: {exc}", file=sys.stderr)
        if raw_stderr:
            print(raw_stderr, file=sys.stderr)
        return 2

    (out_dir / "result.json").write_text(json.dumps(parsed, indent=2) + "\n", encoding="utf-8")

    result = parsed.get("result") if isinstance(parsed, dict) else None
    status = result.get("status") if isinstance(result, dict) else None

    summary = render_summary(
        parsed, args.mode, args.org_alias, manifest_resolution, copy_result=copy_result
    )
    (out_dir / "summary.md").write_text(summary, encoding="utf-8")
    print(summary)
    print(f"output: {out_dir}")

    return exit_code_for_status(status)


if __name__ == "__main__":
    raise SystemExit(main())
