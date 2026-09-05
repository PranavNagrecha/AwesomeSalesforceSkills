#!/usr/bin/env python3
"""Check Lightning Web Component bundles for accessibility defects.

Stdlib only. Point --manifest-dir at an LWC source root (for example
force-app/main/default/lwc) or at any tree containing LWC bundles.

Checks, and where each one comes from (Lightning Web Components Developer Guide,
https://developer.salesforce.com/docs/platform/lwc/guide/<page>.html):

  A1  <img> without an alt attribute (alt="" is fine for decorative images).
      base-components-accessibility L4964 (WCAG 1.1.1 non-text content).
  A2  <button> / <a href> with no text and no accessible name.
      create-components-accessibility-attributes L3993.
  A3  onclick on a non-interactive element (div/span) without role + tabindex +
      a key handler. create-components-focus L4043.
  A4  for / aria-labelledby / aria-describedby / aria-controls / aria-owns /
      aria-details / aria-errormessage / aria-activedescendant referencing an id
      that is not declared in the SAME template.
      create-components-accessibility-attributes L4034-L4036.
  A5  tabindex with a value other than 0 or -1 (bound expressions are allowed).
      create-components-focus L4044.
  A6  tabindex present in a bundle whose JS declares delegatesFocus.
      create-components-focus L4065.
  A7  <label> with neither a `for` attribute nor a wrapped form control.
      create-components-accessibility-attributes L3987.
  A8  aria-hidden="true" on an interactive element.
      Web standard (WAI-ARIA), not a Salesforce-guide statement.
  A9  lightning-icon / lightning-button-icon / lightning-avatar without
      alternative-text. base-components-accessibility L4964.
  B1  Incomplete bundle: <name>.html without <name>.js or <name>.js-meta.xml.
  B2  <name>.js-meta.xml that does not parse, or has no <apiVersion>.
      create-version-components L796-L797 (versioning is required from API v63.0).

Exit code 0 when clean, 1 when any issue is reported, 2 on a usage error.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

TAG_RE = re.compile(
    r"<\s*(/?)([A-Za-z][\w:.-]*)((?:\"[^\"]*\"|'[^']*'|[^>])*?)(/?)\s*>",
    re.DOTALL,
)
ATTR_RE = re.compile(
    r"""([A-Za-z_:@][-\w:.]*)\s*(?:=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'>]+)))?""",
)
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
EXPR_RE = re.compile(r"^\{[^{}]*\}$")
DELEGATES_FOCUS_RE = re.compile(r"\bdelegatesFocus\s*=\s*true\b")

ID_REF_ATTRS = (
    "for",
    "aria-labelledby",
    "aria-describedby",
    "aria-controls",
    "aria-owns",
    "aria-details",
    "aria-errormessage",
    "aria-activedescendant",
)
NON_INTERACTIVE = {"div", "span", "li", "td", "p", "article", "section"}
INTERACTIVE = {
    "a",
    "button",
    "input",
    "select",
    "textarea",
    "lightning-button",
    "lightning-button-icon",
    "lightning-button-menu",
    "lightning-button-stateful",
    "lightning-combobox",
    "lightning-input",
    "lightning-input-field",
    "lightning-radio-group",
    "lightning-select",
    "lightning-textarea",
    "lightning-checkbox-group",
}
ICON_TAGS = {"lightning-icon", "lightning-button-icon", "lightning-avatar"}
FORM_CONTROL_RE = re.compile(
    r"<\s*(?:input|select|textarea|lightning-input|lightning-combobox|"
    r"lightning-select|lightning-textarea|lightning-input-field)\b",
    re.IGNORECASE,
)
NAME_HINT_RE = re.compile(r"alternative-text\s*=|slds-assistive-text", re.IGNORECASE)


class Issue:
    __slots__ = ("path", "code", "message")

    def __init__(self, path: Path, code: str, message: str) -> None:
        self.path = path
        self.code = code
        self.message = message

    def __str__(self) -> str:
        return f"ISSUE [{self.code}] {self.path}: {self.message}"


def parse_attrs(blob: str) -> dict[str, str | None]:
    """Return {lowercased attribute name: value or None for boolean attributes}."""
    attrs: dict[str, str | None] = {}
    for match in ATTR_RE.finditer(blob):
        name = match.group(1).lower()
        value = match.group(2)
        if value is None:
            value = match.group(3)
        if value is None:
            value = match.group(4)
        attrs[name] = value
    return attrs


def strip_markup(fragment: str) -> str:
    return TAG_RE.sub(" ", fragment).replace("&nbsp;", " ").strip()


def inner_html(text: str, tag: str, open_end: int) -> str:
    """Best-effort inner markup between an open tag and its matching close tag."""
    close = re.compile(rf"<\s*/\s*{re.escape(tag)}\s*>", re.IGNORECASE)
    match = close.search(text, open_end)
    return text[open_end : match.start()] if match else ""


def is_expression(value: str | None) -> bool:
    return value is not None and bool(EXPR_RE.match(value.strip()))


def check_template(path: Path, raw: str, delegates_focus: bool) -> list[Issue]:
    issues: list[Issue] = []
    text = COMMENT_RE.sub(" ", raw)

    declared_ids = {
        m.group(1)
        for m in re.finditer(r"""\bid\s*=\s*["']([^"'{}]+)["']""", text)
    }

    for match in TAG_RE.finditer(text):
        closing, tag_raw, attr_blob, _self_close = match.groups()
        if closing:
            continue
        tag = tag_raw.lower()
        attrs = parse_attrs(attr_blob)

        # A1 -----------------------------------------------------------------
        if tag == "img" and "alt" not in attrs:
            issues.append(
                Issue(path, "A1", "<img> has no alt attribute; use alt=\"\" for decorative images")
            )

        # A2 -----------------------------------------------------------------
        if tag == "button" or (tag == "a" and "href" in attrs):
            body = inner_html(text, tag_raw, match.end())
            named = any(
                attrs.get(k) for k in ("aria-label", "aria-labelledby", "title")
            )
            if not named and not strip_markup(body) and not NAME_HINT_RE.search(body):
                issues.append(
                    Issue(
                        path,
                        "A2",
                        f"<{tag}> has no text content and no aria-label/aria-labelledby/title",
                    )
                )

        # A3 -----------------------------------------------------------------
        if tag in NON_INTERACTIVE and "onclick" in attrs:
            missing = []
            if "role" not in attrs:
                missing.append("role")
            if "tabindex" not in attrs:
                missing.append("tabindex")
            if not any(k in attrs for k in ("onkeydown", "onkeyup", "onkeypress")):
                missing.append("a key handler (onkeydown/onkeyup/onkeypress)")
            if missing:
                issues.append(
                    Issue(
                        path,
                        "A3",
                        f"<{tag}> has onclick but is missing {', '.join(missing)}; "
                        "prefer a <button> or a lightning-button instead",
                    )
                )

        # A4 -----------------------------------------------------------------
        for attr in ID_REF_ATTRS:
            value = attrs.get(attr)
            if not value or is_expression(value):
                continue
            for token in value.split():
                if "{" in token or "}" in token:
                    continue
                if token not in declared_ids:
                    issues.append(
                        Issue(
                            path,
                            "A4",
                            f"<{tag} {attr}=\"{value}\"> references id '{token}' that no element "
                            "in this template declares; ids do not cross the shadow boundary",
                        )
                    )

        # A5 -----------------------------------------------------------------
        tabindex = attrs.get("tabindex")
        if tabindex is not None and not is_expression(tabindex):
            if tabindex.strip() not in {"0", "-1"}:
                issues.append(
                    Issue(
                        path,
                        "A5",
                        f"<{tag} tabindex=\"{tabindex}\">; LWC supports only 0 and -1",
                    )
                )

        # A6 -----------------------------------------------------------------
        if delegates_focus and "tabindex" in attrs:
            issues.append(
                Issue(
                    path,
                    "A6",
                    f"<{tag}> uses tabindex in a bundle that declares delegatesFocus; "
                    "the two must not be combined",
                )
            )

        # A7 -----------------------------------------------------------------
        if tag == "label" and "for" not in attrs:
            body = inner_html(text, tag_raw, match.end())
            if not FORM_CONTROL_RE.search(body):
                issues.append(
                    Issue(
                        path,
                        "A7",
                        "<label> has no for attribute and wraps no form control, so it labels nothing",
                    )
                )

        # A8 -----------------------------------------------------------------
        if attrs.get("aria-hidden") == "true":
            body = inner_html(text, tag_raw, match.end())
            nested = re.search(
                r"<\s*(" + "|".join(sorted(INTERACTIVE, key=len, reverse=True)) + r")\b",
                body,
                re.IGNORECASE,
            )
            if tag in INTERACTIVE:
                issues.append(
                    Issue(path, "A8", f"aria-hidden=\"true\" on interactive <{tag}>")
                )
            elif nested is not None:
                issues.append(
                    Issue(
                        path,
                        "A8",
                        f"aria-hidden=\"true\" on <{tag}> that contains interactive "
                        f"<{nested.group(1).lower()}>",
                    )
                )

        # A9 -----------------------------------------------------------------
        if tag in ICON_TAGS and "alternative-text" not in attrs:
            issues.append(
                Issue(
                    path,
                    "A9",
                    f"<{tag}> has no alternative-text; add one or confirm the icon is decorative",
                )
            )

    return issues


def check_bundle(html_path: Path) -> list[Issue]:
    """Bundle-level checks keyed off the entry template <name>/<name>.html."""
    issues: list[Issue] = []
    bundle = html_path.parent
    if html_path.stem != bundle.name:
        return issues  # secondary template (custom datatable type, multi-template)

    js_path = bundle / f"{bundle.name}.js"
    meta_path = bundle / f"{bundle.name}.js-meta.xml"

    if not js_path.exists():
        issues.append(Issue(bundle, "B1", f"missing {js_path.name}"))
    if not meta_path.exists():
        issues.append(Issue(bundle, "B1", f"missing {meta_path.name}"))
        return issues

    try:
        root = ET.parse(meta_path).getroot()
    except ET.ParseError as exc:
        issues.append(Issue(meta_path, "B2", f"does not parse as XML: {exc}"))
        return issues

    # A leaf Element is falsy, so every lookup is compared against None explicitly.
    api_version = root.find("{http://soap.sforce.com/2006/04/metadata}apiVersion")
    if api_version is None:
        api_version = root.find("apiVersion")
    if api_version is None:
        issues.append(
            Issue(
                meta_path,
                "B2",
                "no <apiVersion>; versioning custom components is required from API v63.0",
            )
        )
    return issues


def read_delegates_focus(html_path: Path) -> bool:
    js_path = html_path.parent / f"{html_path.parent.name}.js"
    if not js_path.exists():
        return False
    try:
        return bool(DELEGATES_FOCUS_RE.search(js_path.read_text(encoding="utf-8", errors="ignore")))
    except OSError:
        return False


def run(manifest_dir: Path) -> list[Issue]:
    if not manifest_dir.exists():
        return [Issue(manifest_dir, "B1", "manifest directory not found")]

    issues: list[Issue] = []
    for html_path in sorted(manifest_dir.rglob("*.html")):
        if "__tests__" in html_path.parts or "node_modules" in html_path.parts:
            continue
        try:
            raw = html_path.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            issues.append(Issue(html_path, "B1", f"unreadable: {exc}"))
            continue
        issues.extend(check_bundle(html_path))
        issues.extend(check_template(html_path, raw, read_delegates_focus(html_path)))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check Lightning Web Components for accessibility defects.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the LWC source tree (default: current directory).",
    )
    args = parser.parse_args()

    issues = run(Path(args.manifest_dir))
    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(issue)
    print(f"\n{len(issues)} issue(s) found.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
