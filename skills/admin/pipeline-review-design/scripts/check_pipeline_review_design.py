#!/usr/bin/env python3
"""Lint a pipeline-review spec and the reporting artefacts it claims to produce.

A pipeline review is only reproducible if every number on the agenda has a
written definition, a field or formula that produces it, a named owner, and a
target to be measured against. This checker lints that spec (a YAML file, see
`templates/pipeline-review-spec-template.yaml`) and then cross-checks the
Report / Dashboard / ListView XML sitting beside it, so a review pack cannot
ship with a metric nobody owns or a report column the spec never declared.

Checks performed
----------------
SPEC-01  A pipeline-review spec is present and parses.
SPEC-02  Required top-level keys are present: object, cadence, fields, metrics.
SPEC-03  Every metric has id, definition, source, owner and target; ids unique.
SPEC-04  Every metric `source` names a field declared in `fields:`
         (or is marked `derived: true` and explains itself in `definition`).
SPEC-05  Every `fields:` entry declares `api_name`; `report_column` /
         `list_view_column` are optional but must be unique when present.
RPT-01   Every Report XML in the tree is well-formed and names a reportType.
RPT-02   Every Report `<columns><field>`, `<groupingsDown><field>` and
         `<chart><groupingColumn>` resolves to a `report_column` declared in
         the spec, a bucket `developerName` declared in that same report, or
         the literal `RowCount`.
RPT-03   Every `<timeFrameFilter><dateColumn>` resolves to a declared
         `report_column`, and `<filter><criteriaItems><column>` likewise.
LV-01    Every ListView `<filters><field>` and `<columns>` value resolves to a
         `list_view_column` (falling back to `report_column`/`api_name`)
         declared in the spec.

Exit codes: 0 = clean (WARN allowed), 1 = at least one ERROR, 2 = bad usage.

Usage:
    python3 check_pipeline_review_design.py --manifest-dir path/to/review-pack
    python3 check_pipeline_review_design.py --file path/to/pipeline-review.yaml

Stdlib only. The YAML reader below understands the small, explicit subset used
by the template (block mappings, block sequences of mappings or scalars, `#`
comments). Flow style (`{a: b}`, `[a, b]`), anchors and multi-line scalars are
rejected with a line number rather than silently mis-parsed.
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SPEC_GLOBS = ("*pipeline-review*.yaml", "*pipeline-review*.yml", "*review-spec*.yaml")
REPORT_GLOBS = ("*.report-meta.xml", "*.report")
LISTVIEW_GLOBS = ("*.listView-meta.xml",)
OBJECT_GLOBS = ("*.object-meta.xml", "*.object")

REQUIRED_TOP_KEYS = ("object", "cadence", "fields", "metrics")
REQUIRED_METRIC_KEYS = ("id", "definition", "source", "owner", "target")

# Report column tokens that never come from the spec.
REPORT_BUILTIN_COLUMNS = {"RowCount"}


# --------------------------------------------------------------------------
# Minimal YAML subset reader
# --------------------------------------------------------------------------


class SpecError(Exception):
    """Raised when the spec cannot be read as the documented YAML subset."""


def _strip_comment(raw: str) -> str:
    """Remove a trailing ``#`` comment that is not inside quotes."""
    out = []
    quote = ""
    for ch in raw:
        if quote:
            out.append(ch)
            if ch == quote:
                quote = ""
            continue
        if ch in ("'", '"'):
            quote = ch
            out.append(ch)
            continue
        if ch == "#":
            break
        out.append(ch)
    return "".join(out).rstrip()


def _scalar(raw: str, lineno: int):
    text = raw.strip()
    if not text:
        return ""
    if text[0] in "[{":
        raise SpecError(f"line {lineno}: flow-style YAML is not supported by this checker")
    if text[0] == "&" or text[0] == "*":
        raise SpecError(f"line {lineno}: YAML anchors/aliases are not supported by this checker")
    if text in ("|", ">"):
        raise SpecError(f"line {lineno}: multi-line block scalars are not supported by this checker")
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ("'", '"'):
        return text[1:-1]
    lowered = text.lower()
    if lowered in ("true", "false"):
        return lowered == "true"
    if lowered in ("null", "~"):
        return None
    return text


def _tokenize(text: str) -> list[tuple[int, int, str]]:
    """Return (lineno, indent, content) for every significant line."""
    lines: list[tuple[int, int, str]] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        if raw.lstrip().startswith("#"):
            continue
        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            raise SpecError(f"line {lineno}: tab indentation is not valid YAML")
        content = _strip_comment(raw)
        if not content.strip():
            continue
        indent = len(content) - len(content.lstrip(" "))
        lines.append((lineno, indent, content.strip()))
    return lines


def _split_key(content: str, lineno: int) -> tuple[str, str]:
    if ":" not in content:
        raise SpecError(f"line {lineno}: expected `key: value`, got {content!r}")
    key, _, value = content.partition(":")
    return key.strip(), value.strip()


def _parse_block(lines: list[tuple[int, int, str]], pos: int, indent: int):
    """Parse one block at `indent`. Returns (value, next_pos)."""
    if pos >= len(lines):
        return None, pos
    if lines[pos][2].startswith("- "):
        return _parse_sequence(lines, pos, indent)
    return _parse_mapping(lines, pos, indent)


def _parse_mapping(lines: list[tuple[int, int, str]], pos: int, indent: int):
    result: dict = {}
    while pos < len(lines):
        lineno, line_indent, content = lines[pos]
        if line_indent < indent:
            break
        if line_indent > indent:
            raise SpecError(f"line {lineno}: unexpected indentation")
        if content.startswith("- "):
            break
        key, value = _split_key(content, lineno)
        pos += 1
        if value:
            result[key] = _scalar(value, lineno)
            continue
        if pos < len(lines) and lines[pos][1] > indent:
            child, pos = _parse_block(lines, pos, lines[pos][1])
            result[key] = child
        elif pos < len(lines) and lines[pos][1] == indent and lines[pos][2].startswith("- "):
            child, pos = _parse_sequence(lines, pos, indent)
            result[key] = child
        else:
            result[key] = None
    return result, pos


def _parse_sequence(lines: list[tuple[int, int, str]], pos: int, indent: int):
    result: list = []
    while pos < len(lines):
        lineno, line_indent, content = lines[pos]
        if line_indent < indent or not content.startswith("- "):
            break
        if line_indent > indent:
            raise SpecError(f"line {lineno}: unexpected indentation in sequence")
        item_text = content[2:].strip()
        pos += 1
        if ":" in item_text and not (item_text[0] in ("'", '"')):
            key, value = _split_key(item_text, lineno)
            item: dict = {}
            if value:
                item[key] = _scalar(value, lineno)
            else:
                if pos < len(lines) and lines[pos][1] > indent:
                    child, pos = _parse_block(lines, pos, lines[pos][1])
                    item[key] = child
                else:
                    item[key] = None
            # Sibling keys of the same mapping item are indented past the dash.
            item_indent = indent + 2
            while pos < len(lines) and lines[pos][1] == item_indent and not lines[pos][2].startswith("- "):
                sub_lineno, _, sub_content = lines[pos]
                sub_key, sub_value = _split_key(sub_content, sub_lineno)
                pos += 1
                if sub_value:
                    item[sub_key] = _scalar(sub_value, sub_lineno)
                elif pos < len(lines) and lines[pos][1] > item_indent:
                    child, pos = _parse_block(lines, pos, lines[pos][1])
                    item[sub_key] = child
                else:
                    item[sub_key] = None
            result.append(item)
        else:
            result.append(_scalar(item_text, lineno))
    return result, pos


def load_spec(path: Path) -> dict:
    lines = _tokenize(path.read_text(encoding="utf-8"))
    if not lines:
        raise SpecError("spec file is empty")
    value, _ = _parse_block(lines, 0, lines[0][1])
    if not isinstance(value, dict):
        raise SpecError("top level of the spec must be a mapping")
    return value


# --------------------------------------------------------------------------
# XML helpers — a leaf Element is falsy, so every lookup tests `is not None`
# --------------------------------------------------------------------------


def local_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


def children_named(element: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in element if local_name(child.tag) == name]


def first_child(element: ET.Element, name: str):
    for child in element:
        if local_name(child.tag) == name:
            return child
    return None


def child_text(element: ET.Element, name: str) -> str:
    node = first_child(element, name)
    if node is None:
        return ""
    return (node.text or "").strip()


def descendants_named(root: ET.Element, name: str) -> list[ET.Element]:
    return [el for el in root.iter() if local_name(el.tag) == name]


# --------------------------------------------------------------------------
# Discovery
# --------------------------------------------------------------------------


def discover(root: Path, globs: tuple[str, ...]) -> list[Path]:
    found: list[Path] = []
    for pattern in globs:
        found.extend(p for p in root.rglob(pattern) if p.is_file())
    return sorted(set(found))


# --------------------------------------------------------------------------
# Spec checks
# --------------------------------------------------------------------------


def check_spec(spec: dict, path: Path, findings: list[str]) -> tuple[set[str], set[str]]:
    """Validate the spec. Returns (report_column_tokens, list_view_tokens)."""
    for key in REQUIRED_TOP_KEYS:
        if key not in spec or spec.get(key) in (None, "", []):
            findings.append(f"ERROR SPEC-02 {path}: missing or empty top-level key `{key}`")

    fields = spec.get("fields") or []
    if not isinstance(fields, list):
        findings.append(f"ERROR SPEC-05 {path}: `fields` must be a list of mappings")
        fields = []

    api_names: set[str] = set()
    report_columns: set[str] = set()
    list_view_columns: set[str] = set()
    seen_report: dict[str, str] = {}

    for index, entry in enumerate(fields, start=1):
        if not isinstance(entry, dict):
            findings.append(f"ERROR SPEC-05 {path}: fields[{index}] is not a mapping")
            continue
        api_name = str(entry.get("api_name") or "").strip()
        if not api_name:
            findings.append(f"ERROR SPEC-05 {path}: fields[{index}] has no `api_name`")
            continue
        if api_name in api_names:
            findings.append(f"ERROR SPEC-05 {path}: duplicate field `api_name` `{api_name}`")
        api_names.add(api_name)

        report_column = str(entry.get("report_column") or "").strip()
        if report_column:
            if report_column in seen_report and seen_report[report_column] != api_name:
                findings.append(
                    f"ERROR SPEC-05 {path}: report_column `{report_column}` is claimed by both "
                    f"`{seen_report[report_column]}` and `{api_name}`"
                )
            seen_report[report_column] = api_name
            report_columns.add(report_column)

        list_view_column = str(entry.get("list_view_column") or "").strip()
        if list_view_column:
            list_view_columns.add(list_view_column)

    metrics = spec.get("metrics") or []
    if not isinstance(metrics, list):
        findings.append(f"ERROR SPEC-03 {path}: `metrics` must be a list of mappings")
        metrics = []

    seen_ids: set[str] = set()
    for index, metric in enumerate(metrics, start=1):
        if not isinstance(metric, dict):
            findings.append(f"ERROR SPEC-03 {path}: metrics[{index}] is not a mapping")
            continue
        label = str(metric.get("id") or f"metrics[{index}]")
        for key in REQUIRED_METRIC_KEYS:
            if not str(metric.get(key) or "").strip():
                findings.append(f"ERROR SPEC-03 {path}: metric `{label}` has no `{key}`")
        metric_id = str(metric.get("id") or "").strip()
        if metric_id:
            if metric_id in seen_ids:
                findings.append(f"ERROR SPEC-03 {path}: duplicate metric id `{metric_id}`")
            seen_ids.add(metric_id)

        source = str(metric.get("source") or "").strip()
        if source and not metric.get("derived"):
            unresolved = [
                token
                for token in _source_tokens(source)
                if token not in api_names and token not in report_columns
            ]
            if unresolved:
                findings.append(
                    f"ERROR SPEC-04 {path}: metric `{label}` sources {unresolved} which are not "
                    f"declared in `fields:` — declare the field or set `derived: true`"
                )

    if not metrics:
        findings.append(f"WARN SPEC-03 {path}: spec declares no metrics — the review has no agenda")

    # `list_view_column` is optional; fall back so LV-01 stays usable.
    return report_columns, (list_view_columns or set()) | report_columns | api_names


def _source_tokens(source: str) -> list[str]:
    """Split a `source` expression into candidate field tokens.

    `Amount`, `SUM(Amount) / Quota__c`, `LastStageChangeInDays > 30` all
    reduce to the identifier-ish words that could be field names.
    """
    token = ""
    tokens: list[str] = []
    for ch in source:
        if ch.isalnum() or ch in "_.":
            token += ch
        else:
            if token:
                tokens.append(token)
            token = ""
    if token:
        tokens.append(token)
    out = []
    for candidate in tokens:
        if candidate.replace(".", "").isdigit():
            continue
        if candidate.upper() in ("SUM", "AVG", "COUNT", "MIN", "MAX", "AND", "OR", "NOT"):
            continue
        out.append(candidate)
    return out


# --------------------------------------------------------------------------
# Report / ListView checks
# --------------------------------------------------------------------------


def check_report(path: Path, report_columns: set[str], findings: list[str]) -> None:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        findings.append(f"ERROR RPT-01 {path}: report XML is not well-formed ({exc})")
        return

    if local_name(root.tag) != "Report":
        findings.append(f"WARN RPT-01 {path}: root element is `{local_name(root.tag)}`, not `Report`")
        return

    if not child_text(root, "reportType"):
        findings.append(f"ERROR RPT-01 {path}: report has no `<reportType>`")

    known = set(report_columns) | REPORT_BUILTIN_COLUMNS
    for bucket in children_named(root, "buckets"):
        developer_name = child_text(bucket, "developerName")
        if developer_name:
            known.add(developer_name)
            if not developer_name.startswith("BucketField_"):
                findings.append(
                    f"ERROR RPT-02 {path}: bucket developerName `{developer_name}` must start with "
                    f"`BucketField_` (api_meta.txt:104302-104305)"
                )
        source_column = child_text(bucket, "sourceColumnName")
        if source_column and source_column not in report_columns:
            findings.append(
                f"ERROR RPT-02 {path}: bucket `{developer_name or '<unnamed>'}` sources column "
                f"`{source_column}`, which the spec does not declare"
            )
    for aggregate in children_named(root, "aggregates"):
        developer_name = child_text(aggregate, "developerName")
        if developer_name:
            known.add(developer_name)

    def _check(token: str, where: str) -> None:
        if token and token not in known:
            findings.append(
                f"ERROR RPT-02 {path}: {where} `{token}` is not declared as a `report_column` "
                f"in the spec (and is not a bucket or summary formula in this report)"
            )

    for column in children_named(root, "columns"):
        _check(child_text(column, "field"), "column")
    for grouping in children_named(root, "groupingsDown") + children_named(root, "groupingsAcross"):
        _check(child_text(grouping, "field"), "grouping")

    chart = first_child(root, "chart")
    if chart is not None:
        _check(child_text(chart, "groupingColumn"), "chart groupingColumn")
        for summary in children_named(chart, "chartSummaries"):
            _check(child_text(summary, "column"), "chart summary column")

    time_frame = first_child(root, "timeFrameFilter")
    if time_frame is not None:
        date_column = child_text(time_frame, "dateColumn")
        if not date_column:
            findings.append(f"ERROR RPT-03 {path}: `<timeFrameFilter>` has no `<dateColumn>`")
        else:
            _check(date_column, "timeFrameFilter dateColumn")
        if not child_text(time_frame, "interval"):
            findings.append(f"ERROR RPT-03 {path}: `<timeFrameFilter>` has no `<interval>` (required)")

    report_filter = first_child(root, "filter")
    if report_filter is not None:
        for criteria in children_named(report_filter, "criteriaItems"):
            _check(child_text(criteria, "column"), "filter column")


def check_list_view(path: Path, element: ET.Element, list_view_columns: set[str], findings: list[str]) -> None:
    label = child_text(element, "fullName") or child_text(element, "label") or "<unnamed>"
    if not child_text(element, "filterScope"):
        findings.append(f"ERROR LV-01 {path}: list view `{label}` has no `<filterScope>` (required)")

    for column in children_named(element, "columns"):
        token = (column.text or "").strip()
        if token and token not in list_view_columns:
            findings.append(
                f"ERROR LV-01 {path}: list view `{label}` column `{token}` is not declared in the spec"
            )

    for filter_item in children_named(element, "filters"):
        field_node = first_child(filter_item, "field")
        if field_node is None:
            findings.append(
                f"ERROR LV-01 {path}: list view `{label}` has a `<filters>` entry with no `<field>` "
                f"(the guide's field table calls it `filter`; the deployable element is `field`, "
                f"api_meta.txt:44374 vs api_meta.txt:44468-44478)"
            )
            continue
        token = (field_node.text or "").strip()
        if token and token not in list_view_columns:
            findings.append(
                f"ERROR LV-01 {path}: list view `{label}` filters on `{token}`, which the spec does "
                f"not declare"
            )
        if not child_text(filter_item, "operation"):
            findings.append(
                f"ERROR LV-01 {path}: list view `{label}` filter on `{token or '<unknown>'}` has no "
                f"`<operation>` (required)"
            )


def collect_list_views(root: Path) -> list[tuple[Path, ET.Element]]:
    out: list[tuple[Path, ET.Element]] = []
    for path in discover(root, LISTVIEW_GLOBS):
        try:
            element = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        out.append((path, element))
    for path in discover(root, OBJECT_GLOBS):
        try:
            element = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        for view in descendants_named(element, "listViews"):
            out.append((path, view))
    return out


# --------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint a pipeline-review spec and its report pack.")
    parser.add_argument("--manifest-dir", dest="manifest_dir", help="Directory holding the spec and its XML")
    parser.add_argument("--file", dest="spec_file", help="Path to a single pipeline-review spec YAML")
    parser.add_argument("manifest_dir_pos", nargs="?", help=argparse.SUPPRESS)
    args = parser.parse_args()

    findings: list[str] = []
    spec_path: Path | None = None
    root: Path

    if args.spec_file:
        spec_path = Path(args.spec_file).resolve()
        if not spec_path.is_file():
            print(f"ERROR: --file does not exist: {spec_path}", file=sys.stderr)
            return 2
        root = spec_path.parent
    else:
        target = args.manifest_dir or args.manifest_dir_pos or "."
        root = Path(target).resolve()
        if not root.is_dir():
            print(f"ERROR: --manifest-dir does not exist: {root}", file=sys.stderr)
            return 2
        candidates = discover(root, SPEC_GLOBS)
        if len(candidates) > 1:
            findings.append(
                f"WARN SPEC-01 {root}: {len(candidates)} spec files found; linting "
                f"{candidates[0].name}. Pass --file to choose."
            )
        if candidates:
            spec_path = candidates[0]

    report_columns: set[str] = set()
    list_view_columns: set[str] = set()

    if spec_path is None:
        findings.append(
            f"ERROR SPEC-01 {root}: no pipeline-review spec found "
            f"(looked for {', '.join(SPEC_GLOBS)}) — copy "
            f"templates/pipeline-review-spec-template.yaml into the pack"
        )
    else:
        try:
            spec = load_spec(spec_path)
        except (SpecError, OSError) as exc:
            findings.append(f"ERROR SPEC-01 {spec_path}: {exc}")
        else:
            report_columns, list_view_columns = check_spec(spec, spec_path, findings)

    reports = discover(root, REPORT_GLOBS)
    for path in reports:
        check_report(path, report_columns, findings)

    list_views = collect_list_views(root)
    for path, element in list_views:
        check_list_view(path, element, list_view_columns, findings)

    errors = [f for f in findings if f.startswith("ERROR")]
    print(
        json.dumps(
            {
                "spec": str(spec_path) if spec_path else None,
                "scanned_root": str(root),
                "reports_scanned": len(reports),
                "list_views_scanned": len(list_views),
                "findings": findings,
                "summary": f"{len(errors)} error(s), {len(findings) - len(errors)} advisory finding(s).",
            },
            indent=2,
        )
    )

    if errors:
        print(f"ERROR: {len(errors)} finding(s) must be fixed before the review pack ships", file=sys.stderr)
        return 1
    if findings:
        print(f"WARN: {len(findings)} advisory finding(s)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
