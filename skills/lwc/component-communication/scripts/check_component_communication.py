#!/usr/bin/env python3
"""Check Lightning Web Component source for communication anti-patterns.

Stdlib only. Point --manifest-dir at a Salesforce source tree (for example
``force-app``) and the script walks every ``lwc/<bundle>/`` folder plus the
``messageChannels/`` folder beside it.

Checks, and the documented behaviour each one guards:

 1. legacy ``c/pubsub`` import — LMS is the supported cross-DOM mechanism
    (LWC Developer Guide, ``events-pubsub``).
 2. ``document.querySelector`` aimed at a ``c-*`` tag — bypasses ownership.
 3. ``.shadowRoot`` reach-through — breaks encapsulation; use a public method.
 4. custom event names: no uppercase, no spaces, no leading ``on``, no hyphen
    (``events-create-dispatch``: "No uppercase letters / No spaces / Use
    underscores to separate words / Don't prefix your event name with on").
 5. ``composed: true`` on a dispatched event — makes the event type part of every
    ancestor's public API (``events-best-practices``).
 6. ``subscribe()`` with no ``unsubscribe()``, or with no MessageContext source.
 7. a child writing through one of its own ``@api`` properties — non-primitives
    from a parent are read-only proxies (``create-components-data-flow``).
 8. bundle completeness: ``<name>.js`` needs ``<name>.html`` and
    ``<name>.js-meta.xml`` (``create-components-meta-file``).
 9. ``js-meta.xml`` must parse and carry ``apiVersion``; ``isExposed`` true needs
    at least one ``<target>`` (``reference-configuration-tags``).
10. an ``@salesforce/messageChannel/X`` import with no ``X.messageChannel-meta.xml``
    anywhere in the tree — the bundle will not save.
11. an exposed bundle with no ``__tests__`` folder containing a ``describe(``.

Exit code 1 when anything is reported.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MD_NS = "{http://soap.sforce.com/2006/04/metadata}"

PUBSUB_RE = re.compile(r"""['"]c/pubsub['"]""")
DOCUMENT_COMPONENT_RE = re.compile(r"""document\.querySelector(?:All)?\(\s*['"][^'"]*c-[^'"]*['"]""")
SHADOW_ROOT_COMPONENT_RE = re.compile(r"""\.shadowRoot\b""")
CUSTOM_EVENT_RE = re.compile(r"""new\s+CustomEvent\(\s*['"]([^'"]+)['"]""")
COMPOSED_TRUE_RE = re.compile(r"""\bcomposed\s*:\s*true\b""")
SUBSCRIBE_RE = re.compile(r"""\bsubscribe\s*\(""")
UNSUBSCRIBE_RE = re.compile(r"""\bunsubscribe\s*\(""")
MESSAGE_CONTEXT_RE = re.compile(r"""MessageContext|createMessageContext\s*\(""")
MESSAGE_CHANNEL_IMPORT_RE = re.compile(r"""['"]@salesforce/messageChannel/(?:([A-Za-z0-9_]+)__)?([A-Za-z0-9_]+__c)['"]""")
VALID_EVENT_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
DESCRIBE_RE = re.compile(r"\bdescribe\s*\(")

# `@api` on its own line (decorating a getter or method) or inline before a field.
API_FIELD_RE = re.compile(r"@api\s+(?:get\s+)?([A-Za-z_$][\w$]*)")
API_METHOD_RE = re.compile(r"@api\s+(?:get\s+)?([A-Za-z_$][\w$]*)\s*\(")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Lightning Web Components for communication-pattern issues.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce source tree, e.g. force-app (default: current directory).",
    )
    return parser.parse_args()


def line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def find_child(parent, tag: str):
    """ElementTree-safe child lookup.

    A leaf Element is falsy, so `parent.find(a) or parent.find(b)` silently
    discards a real match. Always compare against None.
    """
    if parent is None:
        return None
    found = parent.find(f"{MD_NS}{tag}")
    if found is None:
        found = parent.find(tag)
    return found


def find_all(parent, tag: str) -> list:
    if parent is None:
        return []
    found = parent.findall(f".//{MD_NS}{tag}")
    if not found:
        found = parent.findall(f".//{tag}")
    return found


def api_property_names(text: str) -> set[str]:
    """Public property names — @api fields and @api getters, excluding methods."""
    methods = set(API_METHOD_RE.findall(text))
    return {name for name in API_FIELD_RE.findall(text) if name not in methods}


def check_js_file(path: Path, text: str, issues: list[str]) -> None:
    for match in PUBSUB_RE.finditer(text):
        issues.append(
            f"{path}:{line_number(text, match.start())}: imports legacy `c/pubsub`; "
            "Lightning Message Service is the supported cross-DOM mechanism unless the container cannot host it."
        )

    for match in DOCUMENT_COMPONENT_RE.finditer(text):
        issues.append(
            f"{path}:{line_number(text, match.start())}: queries a component with `document.querySelector`; "
            "this bypasses ownership boundaries — use `this.template.querySelector` on a component you own, or an event."
        )

    for match in SHADOW_ROOT_COMPONENT_RE.finditer(text):
        issues.append(
            f"{path}:{line_number(text, match.start())}: reaches into `shadowRoot`; "
            "expose a narrow `@api` method on the child instead of depending on its internal DOM."
        )

    for match in CUSTOM_EVENT_RE.finditer(text):
        event_name = match.group(1)
        if event_name.startswith("on") or not VALID_EVENT_NAME_RE.match(event_name):
            issues.append(
                f"{path}:{line_number(text, match.start())}: custom event `{event_name}` breaks the documented "
                "naming rules (lowercase, no spaces, underscores to separate words, never an `on` prefix)."
            )

    for match in COMPOSED_TRUE_RE.finditer(text):
        issues.append(
            f"{path}:{line_number(text, match.start())}: dispatches with `composed: true`; "
            "the event type becomes part of every ancestor's public API and can collide at the document root — "
            "justify it in a comment or drop back to the default."
        )

    if SUBSCRIBE_RE.search(text):
        if not MESSAGE_CONTEXT_RE.search(text):
            issues.append(
                f"{path}: uses `subscribe()` with no `MessageContext` or `createMessageContext()` source."
            )
        if not UNSUBSCRIBE_RE.search(text):
            issues.append(
                f"{path}: subscribes to Lightning Message Service with no `unsubscribe()`; "
                "a cached page is never destroyed and keeps receiving."
            )

    for name in sorted(api_property_names(text)):
        # `this.name = ...` or `this.name.field = ...`, but not inside the
        # property's own setter (which assigns to a backing field) and not the
        # declaration itself (`@api name = false`).
        write_re = re.compile(rf"this\.{re.escape(name)}(?:\.[\w$]+)*\s*=(?!=)")
        setter_re = re.compile(rf"\bset\s+{re.escape(name)}\s*\(")
        for match in write_re.finditer(text):
            ln = line_number(text, match.start())
            if setter_re.search(text):
                continue
            issues.append(
                f"{path}:{ln}: writes to its own `@api` property `{name}`; "
                "after initialisation only the owner sets a public property, and a non-primitive "
                "from a parent is a read-only proxy that raises an invalid-mutation error."
            )


def check_meta_file(path: Path, issues: list[str]) -> bool:
    """Returns True when the bundle is exposed to the builders."""
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        issues.append(f"{path}: is not well-formed XML ({exc}).")
        return False

    api_version = find_child(root, "apiVersion")
    if api_version is None or not (api_version.text or "").strip():
        issues.append(
            f"{path}: has no `<apiVersion>`; every component must specify an API version to save changes back to Salesforce."
        )

    is_exposed = find_child(root, "isExposed")
    exposed = is_exposed is not None and (is_exposed.text or "").strip().lower() == "true"
    if is_exposed is None:
        issues.append(f"{path}: has no `<isExposed>` element.")

    targets = find_all(root, "target")
    if exposed and not targets:
        issues.append(
            f"{path}: `isExposed` is true but declares no `<target>`; "
            "the component will not appear in Lightning App Builder or Experience Builder."
        )
    return exposed


def check_component_communication(manifest_dir: Path) -> list[str]:
    issues: list[str] = []

    if not manifest_dir.exists():
        return [f"Manifest directory not found: {manifest_dir}"]

    channels = {p.name.split(".")[0] for p in manifest_dir.rglob("*.messageChannel-meta.xml")}

    js_paths = sorted(
        p
        for p in manifest_dir.rglob("*")
        if p.suffix in {".js", ".ts"} and "__pycache__" not in p.parts
    )
    for path in js_paths:
        text = path.read_text(encoding="utf-8", errors="ignore")
        in_tests = "__tests__" in path.parts

        if not in_tests:
            check_js_file(path, text, issues)

        for match in MESSAGE_CHANNEL_IMPORT_RE.finditer(text):
            namespace, channel = match.group(1), match.group(2)
            if namespace:
                continue  # a packaged channel from another namespace is not in this tree
            if channel not in channels:
                issues.append(
                    f"{path}:{line_number(text, match.start())}: imports message channel `{channel}` "
                    f"but no `{channel}.messageChannel-meta.xml` exists under {manifest_dir}; "
                    "deploy the channel in the same request or the bundle will not save."
                )

    # Bundle-level structure. A bundle is any folder directly under an `lwc` folder.
    bundles = sorted(
        {
            p.parent
            for p in manifest_dir.rglob("*.js")
            if p.parent.parent.name == "lwc" and p.stem == p.parent.name
        }
    )
    for bundle in bundles:
        name = bundle.name
        if not (bundle / f"{name}.html").exists():
            issues.append(f"{bundle}: bundle has no `{name}.html`.")

        meta = bundle / f"{name}.js-meta.xml"
        if not meta.exists():
            issues.append(
                f"{bundle}: bundle has no `{name}.js-meta.xml`; every component must have a configuration file."
            )
            continue

        exposed = check_meta_file(meta, issues)
        if exposed:
            tests = bundle / "__tests__"
            has_describe = tests.is_dir() and any(
                DESCRIBE_RE.search(p.read_text(encoding="utf-8", errors="ignore"))
                for p in tests.glob("*.js")
            )
            if not has_describe:
                issues.append(
                    f"{bundle}: exposed component has no `__tests__` file containing a `describe(` block; "
                    "the event or message contract is unpinned."
                )

    return issues


def main() -> int:
    args = parse_args()
    issues = check_component_communication(Path(args.manifest_dir))

    if not issues:
        print("No issues found.")
        return 0

    for issue in issues:
        print(f"ISSUE: {issue}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
