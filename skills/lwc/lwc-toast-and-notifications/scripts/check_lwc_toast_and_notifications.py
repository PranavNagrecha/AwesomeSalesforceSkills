#!/usr/bin/env python3
"""check_lwc_toast_and_notifications.py — audit a Salesforce source tree for notification defects.

Stdlib only. Reads a source tree (``--manifest-dir``) containing LWC bundles and/or Apex classes
and reports the notification-surface mistakes that deploy cleanly and then misbehave — or, in the
worst case, render nothing at all and throw nothing.

Every rule cites the crawled Lightning Web Components Developer Guide page and line, or the Apex
Reference Guide line, that supports it, so a reviewer can check the claim rather than trust the
checker. Where the Developer Guide does not publish a fact (the accepted values of ``variant`` and
``mode``, the ``Toast.show`` signature, ``messageData``), this checker deliberately does NOT
enforce a rule — an ungrounded lint is worse than no lint.

Rules
-----
ERROR     ``window.alert`` / ``window.confirm`` / ``window.prompt`` called in any .js file
          outside ``__tests__`` (base-components-patterns L4768: the HTML specification has
          deprecated these in third-party contexts; use-dialog-alert L10401: not supported for
          cross-origin iframes in Chrome and Safari)
WARN      ``lightning/platformShowToastEvent`` imported in a bundle whose ``.js-meta.xml``
          declares a ``lightningCommunity__*`` target — the module renders nothing in LWR sites
          (use-toast L10449; base-components-all L4649; base-components-patterns L4773)
WARN      a bundle importing ``lightning/toast`` whose ``.js-meta.xml`` declares an ``apiVersion``
          below 59.0 — the module is first available in API 59.0 (base-components-all L4651)
WARN      ``Messaging.CustomNotification`` in an Apex class that calls ``send()`` without an
          evident non-empty recipient set, or that never sets a target (Apex Reference Guide
          L166573: send() throws when targetId and targetPageRef are both omitted; L166775:
          the recipient set is required and caps at 500 values)
ADVISORY  a ``variant: 'error'`` toast whose message reads ``error.message`` in a file that also
          references ``error.body`` — the guide's own samples read ``error.body.message``
          (data-table-inline-edit L5703, L5745)
ADVISORY  a toast carrying both ``mode: 'sticky'`` and ``variant: 'success'`` in the same config
          (heuristic: a routine confirmation that outlives the user's attention)
ADVISORY  a toast ``message`` or ``title`` built by concatenating or interpolating a variable into
          a string literal with no ``@salesforce/label`` import in the file (heuristic: deferred to
          lwc/lwc-internationalization, which owns the label contract)

Exit codes
----------
1  ``--manifest-dir`` does not exist, or any ERROR was reported
0  otherwise. WARN and ADVISORY alone do not fail. ``--strict`` promotes WARN to ERROR;
   ADVISORY stays advisory because its rules are heuristics, not documented platform behaviour.

Usage
-----
    python3 check_lwc_toast_and_notifications.py --manifest-dir force-app/main/default
    python3 check_lwc_toast_and_notifications.py --manifest-dir force-app --strict
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

META_NS = "{http://soap.sforce.com/2006/04/metadata}"

# --------------------------------------------------------------------------------- patterns --

BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
LINE_COMMENT_RE = re.compile(r"//[^\n]*")

WINDOW_DIALOG_RE = re.compile(r"\bwindow\s*\.\s*(alert|confirm|prompt)\s*\(")
TOAST_EVENT_IMPORT_RE = re.compile(r"""from\s+['"]lightning/platformShowToastEvent['"]""")
TOAST_MODULE_IMPORT_RE = re.compile(r"""from\s+['"]lightning/toast['"]""")
LWR_TARGET_RE = re.compile(r"^lightningCommunity__")

# A toast config object: the body between `new ShowToastEvent({` (or `Toast.show({`) and its
# matching close brace. Located by brace balance rather than by regex so nested objects survive.
TOAST_CALL_RE = re.compile(r"(new\s+ShowToastEvent\s*\(\s*\{)|(Toast\s*\.\s*show\s*\(\s*\{)")

VARIANT_RE = re.compile(r"""\bvariant\s*:\s*['"]([^'"]*)['"]""")
MODE_RE = re.compile(r"""\bmode\s*:\s*['"]([^'"]*)['"]""")
RAW_ERROR_MESSAGE_RE = re.compile(r"\berror\s*(?:\?)?\.\s*message\b")
ERROR_BODY_RE = re.compile(r"\berror\s*(?:\?)?\.\s*body\b")
LABEL_IMPORT_RE = re.compile(r"""from\s+['"]@salesforce/label/""")
# `message: \`... ${x} ...\`` or `message: 'a' + b`
INTERPOLATED_RE = re.compile(r"(?:message|title|label)\s*:\s*(?:`[^`]*\$\{|['\"][^'\"]*['\"]\s*\+)")

CUSTOM_NOTIFICATION_RE = re.compile(r"\bMessaging\s*\.\s*CustomNotification\b")
SEND_CALL_RE = re.compile(r"\.\s*send\s*\(")
EMPTY_SET_LITERAL_RE = re.compile(r"^new\s+Set\s*<\s*String\s*>\s*\(\s*\)$")
SET_TARGET_RE = re.compile(r"\.\s*setTarget(?:Id|PageRef)\s*\(")


# ---------------------------------------------------------------------------------- finding --

class Finding:
    __slots__ = ("level", "where", "message")

    def __init__(self, level: str, where: str, message: str) -> None:
        self.level = level
        self.where = where
        self.message = message

    def render(self) -> str:
        return f"{self.level}: {self.where}: {self.message}"


_LEVEL_ORDER = {"ERROR": 0, "WARN": 1, "ADVISORY": 2}


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def _blank_comments(src: str) -> str:
    """Blank comment bodies but keep their length so offsets stay line-accurate."""

    def blank(match: re.Match) -> str:
        return re.sub(r"[^\n]", " ", match.group(0))

    return LINE_COMMENT_RE.sub(blank, BLOCK_COMMENT_RE.sub(blank, src))


# ------------------------------------------------------------------------------- bundle meta --

class BundleMeta:
    """What the ``.js-meta.xml`` says. Parse failures are reported, never swallowed."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.exists = path.exists()
        self.parse_error: str | None = None
        self.targets: list[str] = []
        self.api_version: float | None = None
        if not self.exists:
            return
        try:
            root = ET.fromstring(_read(path).encode("utf-8"))
        except ET.ParseError as exc:
            self.parse_error = str(exc)
            return
        for tag in (f"{META_NS}target", "target"):
            for el in root.iter(tag):
                text = (el.text or "").strip()
                if text:
                    self.targets.append(text)
        version_el = _find_first(root, f"{META_NS}apiVersion", "apiVersion")
        if version_el is not None and (version_el.text or "").strip():
            try:
                self.api_version = float(version_el.text.strip())
            except ValueError:
                self.api_version = None

    @property
    def is_experience_site_component(self) -> bool:
        return any(LWR_TARGET_RE.match(t) for t in self.targets)


def _find_first(parent, *tag_names):
    """Return the first matching child Element, or None.

    Never write ``parent.find(a) or parent.find(b)`` — an Element with no children is falsy,
    so a real match would be silently discarded. Test ``is not None`` explicitly.
    """
    for tag in tag_names:
        found = parent.find(tag)
        if found is not None:
            return found
    return None


# ------------------------------------------------------------------------ toast config slicing --

def toast_configs(js: str) -> list[tuple[int, str]]:
    """Return (start_index, config_body) for every ShowToastEvent / Toast.show config literal."""
    out: list[tuple[int, str]] = []
    for match in TOAST_CALL_RE.finditer(js):
        open_brace = js.index("{", match.start())
        depth = 0
        end = None
        for i in range(open_brace, len(js)):
            ch = js[i]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        if end is None:
            continue
        out.append((match.start(), js[open_brace + 1 : end]))
    return out


# ----------------------------------------------------------------------------------- checks --

def check_native_dialogs(path: Path, js: str) -> list[Finding]:
    out: list[Finding] = []
    for match in WINDOW_DIALOG_RE.finditer(js):
        out.append(Finding(
            "ERROR",
            f"{path}:{_line_of(js, match.start())}",
            f"window.{match.group(1)}() is not the platform primitive. The HTML specification "
            f"has deprecated window.alert/confirm/prompt in third-party contexts and Chrome and "
            f"Safari do not support them in cross-origin iframes; use lightning/alert, "
            f"lightning/confirm, or lightning/prompt, whose .open() returns a promise rather "
            f"than blocking (base-components-patterns L4768-L4769; use-dialog-alert L10401).",
        ))
    return out


def check_toast_module_for_targets(path: Path, js: str, meta: BundleMeta) -> list[Finding]:
    out: list[Finding] = []
    event_import = TOAST_EVENT_IMPORT_RE.search(js)
    if event_import and meta.is_experience_site_component:
        targets = ", ".join(t for t in meta.targets if LWR_TARGET_RE.match(t))
        out.append(Finding(
            "WARN",
            f"{path}:{_line_of(js, event_import.start())}",
            f"imports lightning/platformShowToastEvent while {meta.path.name} declares "
            f"{targets}. The module \"isn't supported on login pages in Aura sites, LWR sites "
            f"for Experience Cloud, and standalone apps\" and fails silently there — no toast, "
            f"no error. Use lightning/toast (use-toast L10449, L10452; base-components-all "
            f"L4649; base-components-patterns L4773).",
        ))

    module_import = TOAST_MODULE_IMPORT_RE.search(js)
    if module_import and meta.api_version is not None and meta.api_version < 59.0:
        out.append(Finding(
            "WARN",
            f"{path}:{_line_of(js, module_import.start())}",
            f"imports lightning/toast but {meta.path.name} declares apiVersion "
            f"{meta.api_version:g}. lightning/toast is first available in API version 59.0 "
            f"(base-components-all L4651). Raise the bundle's apiVersion deliberately, or keep "
            f"the event module and do not expose this bundle to an LWR site.",
        ))
    return out


def check_toast_configs(path: Path, js: str) -> list[Finding]:
    out: list[Finding] = []
    file_has_error_body = bool(ERROR_BODY_RE.search(js))
    file_has_labels = bool(LABEL_IMPORT_RE.search(js))

    for start, body in toast_configs(js):
        line = _line_of(js, start)
        variant_match = VARIANT_RE.search(body)
        mode_match = MODE_RE.search(body)
        variant = variant_match.group(1) if variant_match else None
        mode = mode_match.group(1) if mode_match else None

        if variant == "error" and RAW_ERROR_MESSAGE_RE.search(body) and file_has_error_body:
            out.append(Finding(
                "ADVISORY",
                f"{path}:{line}",
                "an error toast reads error.message while this file also handles error.body. "
                "The guide's own samples read error.body.message for Apex and LDS failures "
                "(data-table-inline-edit L5703, L5745); error.message is usually the wrapper, "
                "not the server's sentence. Normalise it once — lwc/lwc-error-boundaries owns "
                "that utility.",
            ))

        if mode == "sticky" and variant == "success":
            out.append(Finding(
                "ADVISORY",
                f"{path}:{line}",
                "a success toast declares mode: 'sticky'. A routine confirmation that the user "
                "must dismiss by hand spends attention you need for messages that carry an "
                "action. Heuristic, not a documented rule: the Developer Guide names `mode` as "
                "a property but never prints its values (use-toast L10456).",
            ))

        if INTERPOLATED_RE.search(body) and not file_has_labels:
            out.append(Finding(
                "ADVISORY",
                f"{path}:{line}",
                "the toast text is assembled from a template literal or string concatenation "
                "and this file imports no @salesforce/label. User-facing strings built in code "
                "cannot be translated. Deferred to lwc/lwc-internationalization, which owns the "
                "custom label contract.",
            ))
    return out


def _call_argument(src: str, open_paren: int) -> str | None:
    """Return the argument text between a call's parentheses, balancing nested ones.

    ``send(new Set<String>())`` must yield ``new Set<String>()``, not ``new Set<String>(``,
    so a plain ``[^)]*`` regex is not good enough here.
    """
    depth = 0
    for i in range(open_paren, len(src)):
        if src[i] == "(":
            depth += 1
        elif src[i] == ")":
            depth -= 1
            if depth == 0:
                return " ".join(src[open_paren + 1 : i].split())
    return None


def check_custom_notification(path: Path, apex: str) -> list[Finding]:
    out: list[Finding] = []
    if not CUSTOM_NOTIFICATION_RE.search(apex):
        return out

    if not SET_TARGET_RE.search(apex):
        out.append(Finding(
            "WARN",
            str(path),
            "builds a Messaging.CustomNotification but never calls setTargetId() or "
            "setTargetPageRef(). \"Neither attribute is required, but if both are omitted, "
            "send() throws an exception\" (Apex Reference Guide L166573). Where there is no "
            "natural target, set a dummy id such as 000000000000000AAA on purpose (L166574).",
        ))

    for match in SEND_CALL_RE.finditer(apex):
        argument = _call_argument(apex, match.end() - 1)
        if argument is None:
            continue
        if not argument:
            out.append(Finding(
                "WARN",
                f"{path}:{_line_of(apex, match.start())}",
                "send() is called with no recipient set. The users parameter is required and "
                "each value is a UserId, AccountId, OpportunityId, GroupId, or QueueId "
                "(Apex Reference Guide L166768-L166774).",
            ))
        elif EMPTY_SET_LITERAL_RE.match(argument):
            out.append(Finding(
                "WARN",
                f"{path}:{_line_of(apex, match.start())}",
                "send() is called with an empty Set<String> literal, so the notification "
                "reaches nobody. Build the recipient set first and chunk it at the documented "
                "maximum of 500 values (Apex Reference Guide L166775).",
            ))
    return out


# ------------------------------------------------------------------------------ tree walking --

def component_bundles(root: Path) -> list[Path]:
    """A bundle is a directory holding <dirname>.js next to <dirname>.js-meta.xml."""
    bundles: list[Path] = []
    for meta in sorted(root.rglob("*.js-meta.xml")):
        bundle = meta.parent
        if (bundle / f"{bundle.name}.js").exists():
            bundles.append(bundle)
    return bundles


def _is_test_js(path: Path) -> bool:
    return "__tests__" in path.parts or path.name.endswith((".test.js", ".spec.js"))


def run(root: Path) -> tuple[list[Finding], int, int]:
    findings: list[Finding] = []
    bundles = component_bundles(root)
    seen_js: set[Path] = set()

    for bundle in bundles:
        meta = BundleMeta(bundle / f"{bundle.name}.js-meta.xml")
        if meta.parse_error:
            findings.append(Finding(
                "ERROR", str(meta.path), f"could not be parsed as XML — {meta.parse_error}",
            ))
        for js_path in sorted(bundle.rglob("*.js")):
            seen_js.add(js_path.resolve())
            if _is_test_js(js_path):
                continue
            js = _blank_comments(_read(js_path))
            findings.extend(check_native_dialogs(js_path, js))
            findings.extend(check_toast_module_for_targets(js_path, js, meta))
            findings.extend(check_toast_configs(js_path, js))

    # Loose .js outside a recognised bundle still gets the container-independent rules.
    loose = 0
    for js_path in sorted(root.rglob("*.js")):
        if js_path.resolve() in seen_js or _is_test_js(js_path):
            continue
        if "node_modules" in js_path.parts:
            continue
        loose += 1
        js = _blank_comments(_read(js_path))
        findings.extend(check_native_dialogs(js_path, js))
        findings.extend(check_toast_configs(js_path, js))

    classes = 0
    for cls_path in sorted(root.rglob("*.cls")):
        classes += 1
        findings.extend(check_custom_notification(cls_path, _read(cls_path)))

    return findings, len(bundles), loose + classes


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Audit a Salesforce source tree for notification-surface defects: the event toast "
            "module on Experience Cloud targets, lightning/toast below its API floor, native "
            "browser dialogs, and Apex custom notifications with no target or no recipients."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the source tree (for example force-app/main/default).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Promote every WARN to an ERROR (use in CI). ADVISORY findings stay advisory.",
    )
    args = parser.parse_args()

    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: --manifest-dir not found: {root}")
        return 1

    findings, bundle_count, other_count = run(root)

    if bundle_count == 0 and other_count == 0:
        print(f"WARN: {root}: no LWC bundles, loose JavaScript, or Apex classes found — nothing to check.")
        return 0

    if args.strict:
        for finding in findings:
            if finding.level == "WARN":
                finding.level = "ERROR"

    for finding in sorted(findings, key=lambda f: (_LEVEL_ORDER[f.level], f.where)):
        print(finding.render())

    errors = sum(1 for f in findings if f.level == "ERROR")
    warns = sum(1 for f in findings if f.level == "WARN")
    advisories = sum(1 for f in findings if f.level == "ADVISORY")
    print(
        f"\n{bundle_count} bundle(s), {other_count} other file(s) scanned — "
        f"{errors} ERROR, {warns} WARN, {advisories} ADVISORY"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
