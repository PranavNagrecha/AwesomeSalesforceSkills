#!/usr/bin/env python3
"""Checker for the Case Feed Send Email quick action and its Apex defaults handler.

Validates a source-format Salesforce metadata tree against the failure modes documented in
references/gotchas.md and references/llm-anti-patterns.md. Stdlib only — no pip deps.

What it checks
--------------
QuickAction metadata (`**/quickActions/*.quickAction*`) whose `<type>` is `SendEmail`:
  * the action carries a `<label>`
  * no `fieldOverrides` target `AttachmentId` / `ContentDocumentIds` (unsupported)
  * no field is both prepopulated via `fieldOverrides` and marked read-only on the
    action layout (the value is silently dropped)
  * the action is referenced by at least one Case page layout (otherwise agents never
    see it in Case Feed). Note: if the *standard* Email action is the one missing, the
    cause is org-level (deliverability access level, Email-to-Case, "Enable Case Feed
    Actions and Feed Items") and lives outside this metadata tree.

Apex classes implementing `QuickAction.QuickActionDefaultsHandler`:
  * declared `global`
  * has an empty, parameterless constructor (required by the interface)
  * guards the cast with `instanceof QuickAction.SendEmailQuickActionDefaults`
  * filters on `getActionName()` before mutating the payload
  * no direct `defaults[0]` / `defaults.get(0)` indexing
  * no SOQL inside a `for` loop (the handler runs synchronously on every action init)

Advisories (informational; promoted to failures with --strict):
  * `apex:emailPublisher` in a Visualforce page — the Classic Case Feed surface
  * `Case.settings-meta.xml` present with no Email-to-Case reference — Email-to-Case must
    be enabled to use the Send Email quick action on Cases

Usage:
    python3 check_case_feed_send_email_action.py --manifest-dir force-app/main/default
    python3 check_case_feed_send_email_action.py --manifest-dir . --strict

Exit code 0 = no issues, 1 = issues found.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SEND_EMAIL_TYPE = "sendemail"

# Predefined-value targets the email quick action layout does not expose.
UNSUPPORTED_OVERRIDE_FIELDS = {"attachmentid", "contentdocumentids"}

# Layout elements that can reference a quick action.
LAYOUT_ACTION_ELEMENTS = {"actionname", "quickactionname"}

HANDLER_INTERFACE = re.compile(
    r"implements\s+[^{]*\bQuickAction\.QuickActionDefaultsHandler\b", re.IGNORECASE
)
CLASS_DECL = re.compile(r"\bglobal\s+(?:with\s+sharing\s+|without\s+sharing\s+|inherited\s+sharing\s+)?class\s+(\w+)", re.IGNORECASE)
ANY_CLASS_DECL = re.compile(r"\b(?:public|global|private)\s+[^;{]*\bclass\s+(\w+)", re.IGNORECASE)
DIRECT_INDEX = re.compile(r"defaults\s*(?:\[\s*0\s*\]|\.\s*get\s*\(\s*0\s*\))", re.IGNORECASE)
SOQL_START = re.compile(r"\[\s*SELECT\b", re.IGNORECASE)
FOR_LOOP = re.compile(r"\bfor\s*\(")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Case Feed Send Email quick action metadata and any "
            "QuickActionDefaultsHandler Apex class for documented failure modes."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce source metadata (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat advisories as failures.",
    )
    return parser.parse_args()


def _local(tag: str) -> str:
    """Strip the XML namespace from a tag name."""
    return tag.rsplit("}", 1)[-1]


def _parse_xml(path: Path) -> tuple[ET.Element | None, str | None]:
    try:
        return ET.parse(path).getroot(), None
    except (OSError, ET.ParseError) as exc:
        return None, str(exc)


def _text(element: ET.Element | None) -> str:
    return (element.text or "").strip() if element is not None else ""


def _find_local(parent: ET.Element, name: str) -> ET.Element | None:
    for child in parent:
        if _local(child.tag) == name:
            return child
    return None


def _iter_local(parent: ET.Element, name: str):
    for child in parent:
        if _local(child.tag) == name:
            yield child


def _action_full_name(path: Path) -> str:
    """`quickActions/Case.Reply_To_Customer.quickAction-meta.xml` -> `Case.Reply_To_Customer`."""
    name = path.name
    for suffix in (".quickAction-meta.xml", ".quickAction"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return path.stem


# ---------------------------------------------------------------------------
# QuickAction metadata
# ---------------------------------------------------------------------------


def _collect_send_email_actions(manifest_dir: Path, issues: list[str]) -> list[tuple[Path, ET.Element]]:
    actions: list[tuple[Path, ET.Element]] = []
    for qa_dir in sorted(manifest_dir.rglob("quickActions")):
        if not qa_dir.is_dir():
            continue
        for path in sorted(qa_dir.iterdir()):
            if not path.is_file() or ".quickAction" not in path.name:
                continue
            root, err = _parse_xml(path)
            if err is not None:
                issues.append(f"{path}: not valid XML ({err})")
                continue
            if root is None:
                continue
            if _text(_find_local(root, "type")).lower() == SEND_EMAIL_TYPE:
                actions.append((path, root))
    return actions


def _readonly_layout_fields(root: ET.Element) -> set[str]:
    """Fields whose uiBehavior on the action layout is read-only."""
    readonly: set[str] = set()
    for item in root.iter():
        if _local(item.tag) != "quickActionLayoutItems":
            continue
        field = _text(_find_local(item, "field"))
        behavior = _text(_find_local(item, "uiBehavior")).lower()
        if field and behavior in {"readonly", "required-readonly"}:
            readonly.add(field.lower())
    return readonly


def _check_action(path: Path, root: ET.Element, issues: list[str]) -> None:
    if not _text(_find_local(root, "label")):
        issues.append(f"{path}: SendEmail quick action has no <label>")

    readonly = _readonly_layout_fields(root)

    for override in _iter_local(root, "fieldOverrides"):
        field = _text(_find_local(override, "field"))
        if not field:
            issues.append(f"{path}: <fieldOverrides> entry has no <field>")
            continue
        if field.lower() in UNSUPPORTED_OVERRIDE_FIELDS:
            issues.append(
                f"{path}: predefined field value targets '{field}', which is not part of the "
                f"email quick action layout and is not supported"
            )
        elif field.lower() in readonly:
            issues.append(
                f"{path}: field '{field}' is prepopulated via <fieldOverrides> but is read-only "
                f"on the action layout — the value is silently dropped"
            )


def _collect_case_layout_action_names(manifest_dir: Path, issues: list[str]) -> tuple[set[str], int]:
    """Return every action name referenced by a Case layout, and how many Case layouts exist."""
    referenced: set[str] = set()
    layout_count = 0
    for layout_dir in sorted(manifest_dir.rglob("layouts")):
        if not layout_dir.is_dir():
            continue
        for path in sorted(layout_dir.iterdir()):
            if not path.is_file() or not path.name.startswith("Case-"):
                continue
            layout_count += 1
            root, err = _parse_xml(path)
            if err is not None:
                issues.append(f"{path}: not valid XML ({err})")
                continue
            if root is None:
                continue
            for node in root.iter():
                if _local(node.tag).lower() in LAYOUT_ACTION_ELEMENTS:
                    value = (node.text or "").strip()
                    if value:
                        referenced.add(value)
                        referenced.add(value.rsplit(".", 1)[-1])
    return referenced, layout_count


# ---------------------------------------------------------------------------
# Apex handler
# ---------------------------------------------------------------------------


def _soql_inside_for_loop(body: str) -> bool:
    """True if a SOQL literal appears inside the braces of a for loop."""
    for match in FOR_LOOP.finditer(body):
        open_brace = body.find("{", match.end())
        if open_brace == -1:
            continue
        depth = 0
        for index in range(open_brace, len(body)):
            char = body[index]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    if SOQL_START.search(body[open_brace:index]):
                        return True
                    break
    return False


def _check_handler(path: Path, source: str, issues: list[str]) -> None:
    global_match = CLASS_DECL.search(source)
    if global_match is None:
        issues.append(
            f"{path}: implements QuickAction.QuickActionDefaultsHandler but the class is not "
            f"declared `global`"
        )
        name_match = ANY_CLASS_DECL.search(source)
        class_name = name_match.group(1) if name_match else path.stem
    else:
        class_name = global_match.group(1)

    ctor = re.compile(rf"\bglobal\s+{re.escape(class_name)}\s*\(\s*\)", re.IGNORECASE)
    if not ctor.search(source):
        issues.append(
            f"{path}: no empty parameterless `global {class_name}()` constructor — the "
            f"QuickActionDefaultsHandler interface requires one"
        )

    if "instanceof QuickAction.SendEmailQuickActionDefaults" not in source:
        issues.append(
            f"{path}: casts to SendEmailQuickActionDefaults without an "
            f"`instanceof QuickAction.SendEmailQuickActionDefaults` guard"
        )

    if "getActionName()" not in source:
        issues.append(
            f"{path}: does not filter on getActionName() (expected 'Case.Email') before "
            f"mutating the action payload"
        )

    if DIRECT_INDEX.search(source):
        issues.append(
            f"{path}: indexes the defaults array directly (defaults[0] / defaults.get(0)) — "
            f"loop and filter on instanceof + getActionName() + getActionType() instead"
        )

    if _soql_inside_for_loop(source):
        issues.append(
            f"{path}: SOQL inside a for loop — onInitDefaults runs synchronously on every "
            f"case-feed Email action init; keep queries bounded"
        )


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def check(manifest_dir: Path) -> tuple[list[str], list[str]]:
    issues: list[str] = []
    advisories: list[str] = []

    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"], []

    actions = _collect_send_email_actions(manifest_dir, issues)
    if not actions:
        issues.append(
            f"No quick action with <type>SendEmail</type> found under {manifest_dir} — "
            f"nothing to check."
        )
        return issues, advisories

    referenced, layout_count = _collect_case_layout_action_names(manifest_dir, issues)

    for path, root in actions:
        _check_action(path, root, issues)

        full_name = _action_full_name(path)
        local_name = full_name.rsplit(".", 1)[-1]
        if layout_count == 0:
            advisories.append(
                f"{path}: no Case page layout found in this tree, so layout assignment for "
                f"'{full_name}' could not be verified — confirm it in the org"
            )
        elif full_name not in referenced and local_name not in referenced:
            issues.append(
                f"{path}: SendEmail action '{full_name}' is not referenced by any Case page "
                f"layout — agents will not see it in Case Feed"
            )

    for classes_dir in sorted(manifest_dir.rglob("classes")):
        if not classes_dir.is_dir():
            continue
        for path in sorted(classes_dir.glob("*.cls")):
            try:
                source = path.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                issues.append(f"{path}: unreadable ({exc})")
                continue
            if HANDLER_INTERFACE.search(source):
                _check_handler(path, source, issues)

    for pages_dir in sorted(manifest_dir.rglob("pages")):
        if not pages_dir.is_dir():
            continue
        for path in sorted(pages_dir.glob("*.page")):
            try:
                source = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if "apex:emailPublisher" in source:
                advisories.append(
                    f"{path}: uses apex:emailPublisher, the Visualforce-era Case Feed publisher. "
                    f"In Lightning Experience, field visibility comes from the action layout"
                )

    for settings_dir in sorted(manifest_dir.rglob("settings")):
        if not settings_dir.is_dir():
            continue
        for path in sorted(settings_dir.glob("Case.settings*")):
            try:
                source = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if "emailToCase" not in source:
                advisories.append(
                    f"{path}: no Email-to-Case reference found. Email-to-Case must be enabled "
                    f"to use the Send Email quick action on the Cases object"
                )

    return issues, advisories


def main() -> int:
    args = parse_args()
    issues, advisories = check(Path(args.manifest_dir))

    for advisory in advisories:
        print(f"{'WARN' if args.strict else 'INFO'}: {advisory}", file=sys.stderr)
    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    if issues or (args.strict and advisories):
        return 1
    print("No issues found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
