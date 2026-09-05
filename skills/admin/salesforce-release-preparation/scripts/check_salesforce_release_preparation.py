#!/usr/bin/env python3
"""Checker for the Salesforce Release Preparation skill.

Two modes, both stdlib-only.

**Run-sheet mode** (``--file``) lints the release run sheet artefact whose shape
is demonstrated in ``references/worked-examples.md`` section 1.  This is the
artefact the skill actually produces, and it rots in specific ways:

1. ``release_run_sheet`` header  -- id, release, production_upgrade_date, owner,
                                    and a status from the allowed set.
2. ``preview_sandbox``           -- name, a real sandbox type, an explicit
                                    opt-in decision, an owner and a status.
3. ``release_updates``           -- unique ids, a name, an enforcement_release,
                                    a test_owner, and an allowed status.
4. Metadata grounding            -- a row claiming ``metadata_backed: true`` must
                                    name a Settings type AND a field that appear
                                    in the documented inventory embedded below,
                                    and must carry a ``source`` citation.  A row
                                    claiming ``metadata_backed: false`` must say
                                    why in ``not_in_metadata_reason``.
5. Referential integrity         -- every ``reads`` repo path exists under
                                    --repo-root, when one is given.

**Metadata mode** (``--manifest-dir``) scans a Salesforce source directory for
release-preparation risk signals, and also picks up any run sheet YAML it finds
there so a single invocation covers a project.

Usage:
    python3 check_salesforce_release_preparation.py --file release-run-sheet.yaml
    python3 check_salesforce_release_preparation.py --file release-run-sheet.yaml --repo-root .
    python3 check_salesforce_release_preparation.py --manifest-dir force-app/main/default

Exit code 0 when clean, 1 when any ISSUE is reported.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MD_NS = {"sf": "http://soap.sforce.com/2006/04/metadata"}

ALLOWED_RUN_SHEET_STATUS = {"planned", "in-progress", "blocked", "complete", "cancelled"}

ALLOWED_UPDATE_STATUS = {
    "planned",
    "in-sandbox",
    "tested-in-sandbox",
    "activated-in-production",
    "enforced",
    "postponed",
    "not-applicable",
}

ALLOWED_SANDBOX_TYPE = {"Developer", "DeveloperPro", "PartialCopy", "Full", "ScratchOrg"}

# Settings types whose fields the Metadata API Developer Guide explicitly ties to
# a named Release Update or Critical Update.  Line numbers are into the extracted
# text of api_meta.pdf (v62 / Summer '26):
# https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
#
# This inventory is deliberately conservative: a field belongs here only when the
# guide's own description names the update.  A run sheet row that cites a
# Settings field outside this list is asserting a correspondence the guide does
# not make, which is exactly the claim this checker exists to catch.
RELEASE_UPDATE_SETTINGS: dict[str, dict[str, str]] = {
    "ApexSettings": {
        "enableApexCtrlImplicitWithSharingPref": "Use with sharing for @AuraEnabled Apex Controllers with Implicit Sharing (api_meta.txt L110736-110741)",
        "enableApexPropertyGetterPref": "Enforce Access Modifiers on Apex Properties in Lightning Component Markup (api_meta.txt L110742-110746)",
        "enableAuraApexCtrlAuthUserAccessCheckPref": "Restrict Access to @AuraEnabled Apex Methods for Authenticated Users Based on User Profile (api_meta.txt L110747-110752)",
        "enableAuraApexCtrlGuestUserAccessCheckPref": "Restrict Access to @AuraEnabled Apex Methods for Guest and Portal Users Based on User Profile (api_meta.txt L110753-110758)",
        "enableMngdCtrlActionAccessPref": "Disable Access to Non-global Apex Controller Methods in Managed Packages (api_meta.txt L110807-110811)",
        "enableSecureNoArgConstructorPref": "Restrict Reflective Access to Non-Global Constructors in Packages - INERT, automatically enforced (api_meta.txt L110831-110833)",
    },
    "FlowSettings": {
        "doesEnforceApexCpuTimeLimit": "Accurately Measure the CPU Time Consumption of Flows and Processes (api_meta.txt L116849-116853)",
        "doesFormulaEnforceDataAccess": "Enforce Data Access in Flow Formulas (api_meta.txt L116855-116858)",
        "enableFlowBREncodedFixEnabled": "Use the BR() Function in Flows and Processes (api_meta.txt L116865-116869)",
        "enableFlowFormulasFixEnabled": "Check for Null Record Variables or Null Values of Lookup Relationship Fields in Process and Flow Formulas (api_meta.txt L116910-116917)",
        "enableFlowNullPreviousValueFix": "Evaluate Criteria Based on Original Record Values in the Process Builder (api_meta.txt L116926-116934)",
        "enableFlowViaRestUsesUserCtxt": "Run Flows in User Context via REST API (api_meta.txt L116968-116973)",
        "enableInvocableFlowFixEnabled": "Execute All Flow Interviews When Invoked in Bulk - REMOVED in API 50.0 and later (api_meta.txt L116974-116981)",
        "isAccessToInvokedApexRequired": "Require User Access to Apex Classes Invoked by Flow - deprecated in API 59.0 and later (api_meta.txt L116988-116995)",
        "isApexPluginAccessModifierRespected": "Make Flows Respect Access Modifiers for Legacy Apex Actions (api_meta.txt L116996-117020)",
        "isFlowApexContextRetired": "Disable Rules for Enforcing Explicit Access to Apex Classes - deprecated in API 59.0 and later (api_meta.txt L117027-117033)",
        "isTimeResumedInSameRunContext": "Make Paused Flow Interviews Resume in the Same Context with the Same User Access (api_meta.txt L117048-117054)",
    },
    "LightningExperienceSettings": {
        "enableApiUserLtngOutAccessPref": "API Only Users Can Access Only Salesforce APIs - deprecated in API 48.0 and later (api_meta.txt L121359-121366)",
        "enableAuraSecStaticResCRUCPref": "Enable Secure Static Resources for Lightning Components (api_meta.txt L121395-121401)",
        "enableStackedModalManagerEnabled": "Enable LWC Stacked Modals (api_meta.txt L121509-121514)",
    },
    "MyDomainSettings": {
        "useStabilizedSandboxMyDomainHostnames": "Stabilize the Hostname for My Domain URLs in Sandboxes - INERT, always true as of API 49.0 (api_meta.txt L122427-122440)",
    },
}

# Fields the guide documents as inert once enforced: setting them has no effect.
INERT_FIELDS = {
    ("ApexSettings", "enableSecureNoArgConstructorPref"),
    ("MyDomainSettings", "useStabilizedSandboxMyDomainHostnames"),
}

RUN_SHEET_GLOBS = (
    "*release-run-sheet*.yaml",
    "*release-run-sheet*.yml",
    "*release-readiness*.yaml",
)

ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")


# --------------------------------------------------------------------------- #
# Minimal YAML-subset parser (block maps, block lists of maps and of scalars)
# --------------------------------------------------------------------------- #


def _scalar(raw: str):
    """Convert a bare or quoted YAML scalar to a Python value."""
    text = raw.strip()
    if text[:1] in ("'", '"'):
        closing = text.find(text[0], 1)
        if closing != -1:
            return text[1:closing]
        return text[1:]
    text = re.split(r"\s+#", text, maxsplit=1)[0].strip()
    if text in ("null", "~", ""):
        return None
    if text in ("true", "false"):
        return text == "true"
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    return text


def _significant_lines(text: str) -> list[tuple[int, str, int]]:
    """Return (indent, content, line_number) for non-blank, non-comment lines."""
    out: list[tuple[int, str, int]] = []
    for number, raw in enumerate(text.splitlines(), start=1):
        if "\t" in raw:
            raw = raw.replace("\t", "  ")
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        out.append((indent, stripped, number))
    return out


def _parse_block(lines: list[tuple[int, str, int]], idx: int, indent: int):
    """Parse one block starting at lines[idx]; return (value, next_index)."""
    if idx >= len(lines):
        return None, idx

    if lines[idx][1].startswith("- ") or lines[idx][1] == "-":
        items: list = []
        while idx < len(lines):
            line_indent, content, _ = lines[idx]
            if line_indent != indent:
                break
            if not (content.startswith("- ") or content == "-"):
                break
            inner = content[2:].strip() if content.startswith("- ") else ""
            child_indent = indent + 2
            if inner == "":
                idx += 1
                if idx < len(lines) and lines[idx][0] > indent:
                    value, idx = _parse_block(lines, idx, lines[idx][0])
                else:
                    value = None
                items.append(value)
            elif ":" in inner and inner[0] not in ("'", '"'):
                sub: list[tuple[int, str, int]] = [(child_indent, inner, lines[idx][2])]
                idx += 1
                while idx < len(lines) and lines[idx][0] >= child_indent:
                    sub.append(lines[idx])
                    idx += 1
                value, _ = _parse_block(sub, 0, child_indent)
                items.append(value)
            else:
                items.append(_scalar(inner))
                idx += 1
        return items, idx

    mapping: dict = {}
    line_numbers: dict = {}
    while idx < len(lines):
        line_indent, content, number = lines[idx]
        if line_indent < indent:
            break
        if line_indent > indent:
            idx += 1
            continue
        if content.startswith("- ") or content == "-":
            break
        if ":" not in content:
            idx += 1
            continue
        key, _, rest = content.partition(":")
        key = key.strip()
        rest = rest.strip()
        line_numbers[key] = number
        idx += 1
        if rest:
            mapping[key] = _scalar(rest)
        elif idx < len(lines) and lines[idx][0] > line_indent:
            value, idx = _parse_block(lines, idx, lines[idx][0])
            mapping[key] = value
        else:
            mapping[key] = None
    mapping["__lines__"] = line_numbers
    return mapping, idx


def parse_yaml_subset(text: str) -> dict:
    lines = _significant_lines(text)
    if not lines:
        return {}
    value, _ = _parse_block(lines, 0, lines[0][0])
    return value if isinstance(value, dict) else {}


# --------------------------------------------------------------------------- #
# Small helpers
# --------------------------------------------------------------------------- #


def _text(row, key: str) -> str:
    """Return a stripped string for row[key], or '' when absent or empty."""
    if not isinstance(row, dict):
        return ""
    value = row.get(key)
    if value is None or isinstance(value, bool):
        return ""
    return str(value).strip()


def _mapping(document: dict, key: str) -> dict:
    value = document.get(key)
    return value if isinstance(value, dict) else {}


def _rows(document: dict, key: str) -> list[dict]:
    value = document.get(key)
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, dict)]


def _find(element, tag: str):
    """Namespace-tolerant single-child lookup.

    An ElementTree element with no children is falsy, so ``a.find(x) or
    a.find(y)`` silently discards a real leaf match.  Always test ``is not
    None`` instead.
    """
    if element is None:
        return None
    found = element.find(tag)
    if found is None:
        found = element.find(f"sf:{tag}", MD_NS)
    return found


def _find_all(element, tag: str) -> list:
    if element is None:
        return []
    return element.findall(f".//{tag}") + element.findall(f".//sf:{tag}", MD_NS)


def _child_text(element, tag: str, default: str = "") -> str:
    found = _find(element, tag)
    if found is None or found.text is None:
        return default
    return found.text.strip()


# --------------------------------------------------------------------------- #
# Run-sheet checks
# --------------------------------------------------------------------------- #


def check_run_sheet_header(document: dict, label: str) -> list[str]:
    issues: list[str] = []
    header = _mapping(document, "release_run_sheet")
    if not header:
        return [f"{label}: no 'release_run_sheet:' block. The run sheet shape is in references/worked-examples.md section 1."]

    for field in ("id", "release", "production_upgrade_date", "owner"):
        if not _text(header, field):
            issues.append(f"{label}: release_run_sheet is missing '{field}'.")

    status = _text(header, "status")
    if status not in ALLOWED_RUN_SHEET_STATUS:
        issues.append(
            f"{label}: release_run_sheet.status is '{status or '(empty)'}'; "
            f"allowed: {', '.join(sorted(ALLOWED_RUN_SHEET_STATUS))}."
        )

    run_id = _text(header, "id")
    if run_id and not ID_RE.match(run_id):
        issues.append(f"{label}: release_run_sheet.id '{run_id}' is not a plain identifier.")

    return issues


def check_preview_sandbox(document: dict, label: str) -> list[str]:
    issues: list[str] = []
    sandbox = _mapping(document, "preview_sandbox")
    if not sandbox:
        return [
            f"{label}: no 'preview_sandbox:' block. Record the preview decision even when it is "
            "'no sandbox opted in' - an undocumented skip is indistinguishable from an oversight."
        ]

    for field in ("name", "owner", "opt_in_decision"):
        if not _text(sandbox, field):
            issues.append(f"{label}: preview_sandbox is missing '{field}'.")

    sandbox_type = _text(sandbox, "type")
    if sandbox_type not in ALLOWED_SANDBOX_TYPE:
        issues.append(
            f"{label}: preview_sandbox.type is '{sandbox_type or '(empty)'}'; "
            f"allowed: {', '.join(sorted(ALLOWED_SANDBOX_TYPE))}."
        )

    if not isinstance(sandbox.get("opt_in"), bool):
        issues.append(f"{label}: preview_sandbox.opt_in must be true or false, not a prose value.")

    status = _text(sandbox, "status")
    if status not in ALLOWED_RUN_SHEET_STATUS:
        issues.append(
            f"{label}: preview_sandbox.status is '{status or '(empty)'}'; "
            f"allowed: {', '.join(sorted(ALLOWED_RUN_SHEET_STATUS))}."
        )

    if sandbox.get("opt_in") is True and not _text(sandbox, "refresh_freeze_from"):
        issues.append(
            f"{label}: preview_sandbox opts in but sets no 'refresh_freeze_from'. A refresh after the "
            "preview upgrade returns the sandbox to the source org's release and discards the preview "
            "- see references/gotchas.md Gotcha 11."
        )

    return issues


def check_release_update_rows(document: dict, label: str) -> list[str]:
    issues: list[str] = []
    rows = _rows(document, "release_updates")
    if not rows:
        return [
            f"{label}: no 'release_updates:' rows. Even a release with nothing pending needs the "
            "inventory recorded, or next cycle cannot tell 'reviewed, none pending' from 'never looked'."
        ]

    seen_ids: dict[str, int] = {}
    for index, row in enumerate(rows, start=1):
        row_id = _text(row, "id") or f"(row {index})"

        if not _text(row, "id"):
            issues.append(f"{label}: release_updates row {index} has no 'id'.")
        else:
            seen_ids[row_id] = seen_ids.get(row_id, 0) + 1

        for field in ("name", "enforcement_release", "test_owner"):
            if not _text(row, field):
                issues.append(f"{label}: release update '{row_id}' is missing '{field}'.")

        status = _text(row, "status")
        if status not in ALLOWED_UPDATE_STATUS:
            issues.append(
                f"{label}: release update '{row_id}' status is '{status or '(empty)'}'; "
                f"allowed: {', '.join(sorted(ALLOWED_UPDATE_STATUS))}."
            )

        backed = row.get("metadata_backed")
        if not isinstance(backed, bool):
            issues.append(
                f"{label}: release update '{row_id}' must set metadata_backed to true or false. "
                "It decides whether the update is deployable settings or Setup-only."
            )
            continue

        if backed:
            issues.extend(_check_metadata_backed_row(row, row_id, label))
        elif not _text(row, "not_in_metadata_reason"):
            issues.append(
                f"{label}: release update '{row_id}' is metadata_backed: false but gives no "
                "'not_in_metadata_reason'. Say why Setup is the only surface."
            )

    for row_id, count in seen_ids.items():
        if count > 1:
            issues.append(f"{label}: release update id '{row_id}' appears {count} times; ids must be unique.")

    return issues


def _check_metadata_backed_row(row: dict, row_id: str, label: str) -> list[str]:
    issues: list[str] = []
    settings_type = _text(row, "settings_type")
    settings_field = _text(row, "settings_field")

    if not settings_type:
        issues.append(f"{label}: release update '{row_id}' claims metadata_backed but names no 'settings_type'.")
        return issues

    known_fields = RELEASE_UPDATE_SETTINGS.get(settings_type)
    if known_fields is None:
        issues.append(
            f"{label}: release update '{row_id}' cites settings_type '{settings_type}', which is not in "
            "the documented release-update Settings inventory. Known types: "
            f"{', '.join(sorted(RELEASE_UPDATE_SETTINGS))}. If the guide really does tie a field on this "
            "type to a named release update, add it to RELEASE_UPDATE_SETTINGS with its line citation."
        )
        return issues

    if not settings_field:
        issues.append(f"{label}: release update '{row_id}' names settings_type but no 'settings_field'.")
        return issues

    if settings_field not in known_fields:
        issues.append(
            f"{label}: release update '{row_id}' cites {settings_type}.{settings_field}, which the "
            "Metadata API guide does not tie to a named release update. Documented fields on "
            f"{settings_type}: {', '.join(sorted(known_fields))}."
        )
        return issues

    if not _text(row, "source"):
        issues.append(
            f"{label}: release update '{row_id}' is metadata_backed but carries no 'source' citation. "
            f"Expected something like: {known_fields[settings_field]}"
        )

    if (settings_type, settings_field) in INERT_FIELDS and _text(row, "status") != "enforced":
        issues.append(
            f"{label}: release update '{row_id}' cites {settings_type}.{settings_field}, which the guide "
            "documents as inert once enforced - setting it has no effect. Its status should be 'enforced', "
            f"not '{_text(row, 'status')}'. See references/gotchas.md Gotcha 10."
        )

    return issues


def check_reads_paths(document: dict, label: str, repo_root: Path | None) -> list[str]:
    if repo_root is None:
        return []
    issues: list[str] = []
    for row in _rows(document, "release_updates"):
        reads = _text(row, "reads")
        if not reads:
            continue
        if not (repo_root / reads).exists():
            issues.append(
                f"{label}: release update '{_text(row, 'id') or '(no id)'}' reads "
                f"'{reads}', which does not resolve under {repo_root}."
            )
    return issues


def check_run_sheet_file(path: Path, repo_root: Path | None) -> list[str]:
    label = path.name
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"{label}: cannot be read ({exc})."]

    document = parse_yaml_subset(text)
    if not document:
        return [f"{label}: parsed as empty. Expected a YAML run sheet - see references/worked-examples.md section 1."]

    issues: list[str] = []
    issues.extend(check_run_sheet_header(document, label))
    issues.extend(check_preview_sandbox(document, label))
    issues.extend(check_release_update_rows(document, label))
    issues.extend(check_reads_paths(document, label, repo_root))
    return issues


# --------------------------------------------------------------------------- #
# Metadata-directory checks
# --------------------------------------------------------------------------- #


def find_files(root: Path, suffix: str) -> list[Path]:
    return list(root.rglob(f"*{suffix}")) if root.exists() else []


def parse_xml(path: Path):
    try:
        return ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return None


def check_settings_release_updates(manifest_dir: Path) -> list[str]:
    """Flag release-update booleans sitting in deployable .settings files.

    Many Settings fields are documented as corresponding to a named Release
    Update, so a settings deploy changes the org's release-update posture.  The
    file is not wrong; it is under-reviewed.  See references/gotchas.md Gotcha 9.
    """
    issues: list[str] = []
    for settings_path in find_files(manifest_dir, ".settings-meta.xml") + find_files(manifest_dir, ".settings"):
        root = parse_xml(settings_path)
        if root is None:
            continue
        settings_type = root.tag.split("}")[-1]
        known_fields = RELEASE_UPDATE_SETTINGS.get(settings_type)
        if not known_fields:
            continue
        for child in root:
            field = child.tag.split("}")[-1]
            if field not in known_fields:
                continue
            value = (child.text or "").strip()
            if (settings_type, field) in INERT_FIELDS:
                issues.append(
                    f"{settings_path.name}: {settings_type}.{field} is set to '{value}' but the guide "
                    "documents this field as inert once enforced - the deploy will succeed and change "
                    "nothing. Remove it or annotate it. See references/gotchas.md Gotcha 10."
                )
            else:
                issues.append(
                    f"{settings_path.name}: {settings_type}.{field}='{value}' will move a Release Update "
                    f"on deploy - {known_fields[field]}. Confirm it is a reviewed change and that the "
                    "run sheet has a row for it, not incidental drift from a full-org retrieve."
                )
    return issues


def check_flow_null_comparisons(manifest_dir: Path) -> list[str]:
    """Warn about Flow Decision conditions that use literal null comparisons."""
    issues: list[str] = []
    for flow_path in find_files(manifest_dir, ".flow-meta.xml"):
        root = parse_xml(flow_path)
        if root is None:
            continue
        for decision in _find_all(root, "decisions"):
            for condition in _find_all(decision, "conditions"):
                right_val = _find(condition, "rightValue")
                if right_val is None:
                    continue
                string_val = _find(right_val, "stringValue")
                if string_val is None:
                    continue
                if (string_val.text or "").strip() in ("null", "NULL", ""):
                    label = _child_text(decision, "label", "unknown")
                    issues.append(
                        f"Flow {flow_path.name}: Decision '{label}' compares against a literal null. "
                        "Flow null handling has moved by release update more than once "
                        "(FlowSettings.enableFlowFormulasFixEnabled, .enableFlowNullPreviousValueFix). "
                        "Use ISNULL() or $GlobalConstant.EmptyString."
                    )
    return issues


def check_deprecated_api_versions(manifest_dir: Path) -> list[str]:
    """Report the spread of pinned API versions and flag very old ones.

    A pinned class keeps the semantics of the version it was saved with even
    after the org upgrades (apexdev.txt L6876-6881), so the version spread is a
    release-preparation input, not a tidy-up item.  See gotchas.md Gotcha 12.
    """
    issues: list[str] = []
    minimum_recommended = 50.0  # API 50.0 = Winter '21
    versions: dict[str, list[str]] = {}

    for meta_path in find_files(manifest_dir, "-meta.xml"):
        root = parse_xml(meta_path)
        if root is None:
            continue
        api_el = _find(root, "apiVersion")
        if api_el is None or not api_el.text:
            continue
        try:
            api_version = float(api_el.text.strip())
        except ValueError:
            continue
        versions.setdefault(api_el.text.strip(), []).append(meta_path.name)
        if api_version < minimum_recommended:
            issues.append(
                f"{meta_path.name}: API version {api_el.text.strip()} is below {minimum_recommended:.1f}. "
                "Salesforce recommends versions released in the past three years "
                "(apexdev.txt L6905-6910). List what this component skips before the upgrade."
            )

    if len(versions) > 3:
        spread = ", ".join(f"{ver} ({len(names)})" for ver, names in sorted(versions.items()))
        issues.append(
            f"{len(versions)} distinct API versions pinned across this source tree: {spread}. "
            "Each version is a separate behaviour contract to regress. Salesforce's guidance is to "
            "consolidate to the minimal number, ideally one (apexdev.txt L6905-6910)."
        )

    return issues


def check_scheduled_apex_without_comment(manifest_dir: Path) -> list[str]:
    """Flag Schedulable Apex with no release-testing note.

    Scheduled jobs run unattended, so upgrade breakage in them surfaces late.
    """
    issues: list[str] = []
    keywords = ("release", "upgrade", "schedule", "cron", "post-upgrade")
    for cls_path in find_files(manifest_dir, ".cls"):
        try:
            source = cls_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if "implements schedulable" not in source.lower():
            continue
        if not any(kw in source.lower() for kw in keywords):
            issues.append(
                f"{cls_path.name}: implements Schedulable with no comment referencing release, upgrade "
                "or post-upgrade behaviour. Confirm it is on the regression checklist - scheduled jobs "
                "are the least-watched surface after an upgrade."
            )
    return issues


def check_flows_without_fault_paths(manifest_dir: Path) -> list[str]:
    """Flag active Flows whose record operations have no fault connector."""
    issues: list[str] = []
    for flow_path in find_files(manifest_dir, ".flow-meta.xml"):
        root = parse_xml(flow_path)
        if root is None:
            continue
        status_el = _find(root, "status")
        if status_el is None or (status_el.text or "").strip().lower() != "active":
            continue
        record_ops = (
            _find_all(root, "recordCreates")
            + _find_all(root, "recordUpdates")
            + _find_all(root, "recordDeletes")
        )
        for op in record_ops:
            if _find(op, "faultConnector") is not None:
                continue
            label = _child_text(op, "label", "unknown element")
            issues.append(
                f"Flow {flow_path.name}: record operation '{label}' has no fault connector. If the "
                "operation starts failing after an upgrade or a release-update activation, the error "
                "reaches the user as an unhandled exception. Add a fault path."
            )
    return issues


def check_manifest_dir(manifest_dir: Path, repo_root: Path | None) -> list[str]:
    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    issues: list[str] = []
    issues.extend(check_settings_release_updates(manifest_dir))
    issues.extend(check_flow_null_comparisons(manifest_dir))
    issues.extend(check_deprecated_api_versions(manifest_dir))
    issues.extend(check_scheduled_apex_without_comment(manifest_dir))
    issues.extend(check_flows_without_fault_paths(manifest_dir))

    run_sheets: list[Path] = []
    for pattern in RUN_SHEET_GLOBS:
        run_sheets.extend(sorted(manifest_dir.rglob(pattern)))
    if run_sheets:
        for sheet in run_sheets:
            issues.extend(check_run_sheet_file(sheet, repo_root))
    else:
        issues.append(
            f"No release run sheet found under {manifest_dir} (looked for {', '.join(RUN_SHEET_GLOBS)}). "
            "Create one from references/worked-examples.md section 1 so the cycle's Release Update "
            "inventory, owners and preview decision are recorded rather than remembered."
        )

    return issues


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Lint a Salesforce release run sheet (--file), or scan a metadata source tree "
            "for release-preparation risk signals (--manifest-dir)."
        )
    )
    parser.add_argument("--file", help="Path to a release run sheet YAML artefact.")
    parser.add_argument(
        "--manifest-dir",
        help="Root of the Salesforce metadata source tree (for example force-app/main/default).",
    )
    parser.add_argument(
        "--repo-root",
        help="Repo root used to resolve 'reads:' skill paths in the run sheet.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root) if args.repo_root else None

    if not args.file and not args.manifest_dir:
        print("ISSUE: pass --file <run-sheet.yaml> or --manifest-dir <metadata dir>.")
        return 1

    issues: list[str] = []

    if args.file:
        sheet = Path(args.file)
        if not sheet.exists():
            issues.append(f"Run sheet not found: {sheet}")
        else:
            issues.extend(check_run_sheet_file(sheet, repo_root))

    if args.manifest_dir:
        issues.extend(check_manifest_dir(Path(args.manifest_dir), repo_root))

    if not issues:
        print("No release-preparation issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")
    print(f"\n{len(issues)} issue(s) found.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
