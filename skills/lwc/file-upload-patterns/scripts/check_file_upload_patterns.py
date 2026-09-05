#!/usr/bin/env python3
"""Check LWC file-upload bundles and their Apex controllers for the defects this skill exists to prevent.

Static, stdlib-only, no org connection. Point --manifest-dir at a Salesforce
source tree (for example ``force-app/main/default``) or at any ancestor of one.
LWC bundles are discovered by looking for a directory holding ``<name>.js`` and
``<name>.html``; Apex is discovered by scanning ``*.cls`` files.

Rules implemented, each mapping to a gotcha or anti-pattern in this skill:

  R1  WARN   ``<lightning-file-upload>`` with no ``record-id`` attribute and no
             comment documenting the unsaved-record strategy. The component
             uploads "a file that's associated with a record ID"
             (lwc_guide base-components-all L4603), so no record id means the
             association has to be handled some other way -- deliberately.
  R2  ERROR  Apex constructs a ``ContentVersion`` without setting
             ``FirstPublishLocationId`` and without a later ``ContentDocumentLink``
             insert in the same class. That file is created and is invisible on
             the record (object_reference L79403-L79405, L76648-L76649).
  R3  WARN   A base64 payload is sent to Apex with no client-side size guard.
             Apex heap is 6 MB synchronous (apexdev L19577) and base64 inflates
             the payload by roughly 37% (object_reference L79833).
  R4  ERROR  An ``@AuraEnabled`` upload method marked ``cacheable=true``. "To set
             cacheable=true, a method must only get data, it can't mutate
             (change) data." (lwc_guide apex-result-caching L7254).
  R5  WARN   A ``ContentDocumentLink`` constructed without ``ShareType``. The
             field is documented as Required (object_reference L77269).
  R6  ADVISORY  A bundle with an ``uploadfinished`` handler and no ``__tests__``
             directory containing a ``describe(`` block
             (lwc_guide unit-testing-using-jest-create-tests L12328-L12331).

Exit codes:
    0  clean, or only WARN/ADVISORY findings (without --strict)
    1  the manifest directory does not exist, or any ERROR was reported, or any
       finding at all when --strict is passed

Usage:
    python3 check_file_upload_patterns.py --manifest-dir force-app/main/default
    python3 check_file_upload_patterns.py --manifest-dir force-app --strict
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SKIP_DIRS = {"node_modules", ".git", ".sfdx", "__pycache__"}

FILE_UPLOAD_TAG_RE = re.compile(r"<lightning-file-upload\b[^>]*>", re.IGNORECASE | re.DOTALL)
RECORD_ID_ATTR_RE = re.compile(r"\brecord-id\s*=", re.IGNORECASE)
UPLOAD_FINISHED_RE = re.compile(r"\bonuploadfinished\s*=|\buploadfinished\b", re.IGNORECASE)
HTML_COMMENT_RE = re.compile(r"<!--(.*?)-->", re.DOTALL)
DESCRIBE_RE = re.compile(r"\bdescribe\s*\(")

# Client-side base64 signals.
BASE64_SEND_RE = re.compile(
    r"readAsDataURL\s*\(|readAsBinaryString\s*\(|\bbtoa\s*\(|base64Data\s*[:=]|base64Chunk\s*[:=]",
    re.IGNORECASE,
)
SIZE_GUARD_RE = re.compile(
    r"\.size\s*(?:>|>=|<|<=)|\bMAX_[A-Z0-9_]*(?:BYTES|SIZE)\b|\bmaxFileSize\b|\bfile\.size\b",
)

# Apex signals.
CONTENT_VERSION_NEW_RE = re.compile(r"\bnew\s+ContentVersion\s*\(")
CONTENT_DOC_LINK_NEW_RE = re.compile(r"\bnew\s+ContentDocumentLink\s*\(")
FIRST_PUBLISH_RE = re.compile(r"\bFirstPublishLocationId\b")
SHARE_TYPE_RE = re.compile(r"\bShareType\b")
AURA_ENABLED_CACHEABLE_RE = re.compile(
    r"@AuraEnabled\s*\(\s*[^)]*cacheable\s*=\s*true[^)]*\)", re.IGNORECASE
)
METHOD_SIG_RE = re.compile(
    r"\b(?:public|global)\s+static\s+[A-Za-z0-9_.<>,\[\] ]+?\s+([A-Za-z0-9_]+)\s*\(",
)
UPLOAD_METHOD_NAME_RE = re.compile(
    r"upload|attach|savefile|createfile|contentversion|appendchunk|storefile", re.IGNORECASE
)
APEX_IMPORT_RE = re.compile(r"@salesforce/apex/([A-Za-z0-9_]+)\.([A-Za-z0-9_]+)")

LEVELS = ("ERROR", "WARN", "ADVISORY")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check LWC file-upload bundles and their Apex controllers.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce source tree (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Promote WARN and ADVISORY findings to failures (exit 1).",
    )
    return parser.parse_args()


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def walk(root: Path, suffix: str):
    for path in root.rglob(f"*{suffix}"):
        if SKIP_DIRS.intersection(path.parts):
            continue
        yield path


def find_bundles(root: Path) -> list[Path]:
    """A bundle is a directory holding <dirname>.js and <dirname>.html."""
    bundles: set[Path] = set()
    for js_path in walk(root, ".js"):
        if "__tests__" in js_path.parts:
            continue
        bundle = js_path.parent
        if js_path.stem != bundle.name:
            continue
        if (bundle / f"{bundle.name}.html").exists():
            bundles.add(bundle)
    return sorted(bundles)


def strip_apex_noise(source: str) -> str:
    """Blank string literals and comments in one left-to-right pass.

    A '{' inside a string or an apostrophe inside a comment must not confuse the
    structural scans below.
    """
    out: list[str] = []
    i, n = 0, len(source)
    while i < n:
        ch = source[i]
        if ch == "'":
            j = i + 1
            while j < n and source[j] != "'":
                j += 2 if source[j] == "\\" else 1
            out.append(" ")
            i = j + 1
            continue
        if source.startswith("//", i):
            j = source.find("\n", i)
            i = n if j < 0 else j
            continue
        if source.startswith("/*", i):
            j = source.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def method_name_after(code: str, index: int) -> str:
    """Best-effort: the name of the first method signature at or after `index`."""
    match = METHOD_SIG_RE.search(code, index)
    return match.group(1) if match else ""


def check_bundle(bundle: Path, root: Path) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    name = bundle.name
    html_path = bundle / f"{name}.html"
    js_path = bundle / f"{name}.js"
    html = read(html_path)
    js = read(js_path)

    # R1 -- base component with no record id and no stated fallback.
    tags = FILE_UPLOAD_TAG_RE.findall(html)
    if tags:
        without_record_id = [t for t in tags if not RECORD_ID_ATTR_RE.search(t)]
        if without_record_id:
            comments = " ".join(HTML_COMMENT_RE.findall(html)) + " " + " ".join(
                re.findall(r"//.*|/\*.*?\*/", js, re.DOTALL)
            )
            documented = re.search(
                r"unsaved[- ]record|no record id|without a record id|record does not exist|before the record",
                comments,
                re.IGNORECASE,
            )
            if not documented:
                findings.append(
                    (
                        "WARN",
                        f"{html_path.relative_to(root)}: `<lightning-file-upload>` has no `record-id` "
                        "and no comment documenting the unsaved-record strategy. The component "
                        "uploads a file associated with a record id "
                        "(lwc_guide base-components-all L4603); say in the source how the "
                        "association happens without one.",
                    )
                )

    # R3 -- base64 leaves the browser with no size guard.
    if BASE64_SEND_RE.search(js) and not SIZE_GUARD_RE.search(js):
        findings.append(
            (
                "WARN",
                f"{js_path.relative_to(root)}: a base64 payload is built and sent to Apex with no "
                "client-side size guard. Apex heap is 6 MB synchronous (apexdev L19577) and "
                "base64 inflates the payload by about 37% (object_reference L79833).",
            )
        )

    # R6 -- an uploadfinished handler with no Jest suite.
    if UPLOAD_FINISHED_RE.search(html) or UPLOAD_FINISHED_RE.search(js):
        tests_dir = bundle / "__tests__"
        has_suite = False
        if tests_dir.is_dir():
            has_suite = any(
                DESCRIBE_RE.search(read(t)) for t in tests_dir.glob("*.js")
            )
        if not has_suite:
            findings.append(
                (
                    "ADVISORY",
                    f"{bundle.relative_to(root)}: handles `uploadfinished` but has no "
                    "`__tests__` suite with a `describe(` block. The event payload is the only "
                    "contract between the platform and this component "
                    "(lwc_guide unit-testing-using-jest-create-tests L12328-L12331).",
                )
            )

    return findings


def check_apex(cls_path: Path, root: Path) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    code = strip_apex_noise(read(cls_path))
    if not code:
        return findings

    creates_version = CONTENT_VERSION_NEW_RE.search(code)
    creates_link = CONTENT_DOC_LINK_NEW_RE.search(code)

    # R2 -- ContentVersion with no association path at all.
    if creates_version and not creates_link and not FIRST_PUBLISH_RE.search(code):
        findings.append(
            (
                "ERROR",
                f"{cls_path.relative_to(root)}: constructs `ContentVersion` but never sets "
                "`FirstPublishLocationId` and never inserts a `ContentDocumentLink`. The file "
                "is created in the running user's library and is invisible on the record; "
                "`ContentDocument` has no create() call to repair it afterwards "
                "(object_reference L79403-L79405, L76648-L76649).",
            )
        )

    # R5 -- a link with no ShareType.
    if creates_link and not SHARE_TYPE_RE.search(code):
        findings.append(
            (
                "WARN",
                f"{cls_path.relative_to(root)}: constructs `ContentDocumentLink` without "
                "`ShareType`, which the object reference documents as Required "
                "(object_reference L77269). Set it explicitly (V, C or I) rather than "
                "relying on a default.",
            )
        )

    # R4 -- a cacheable upload method.
    for match in AURA_ENABLED_CACHEABLE_RE.finditer(code):
        method = method_name_after(code, match.end())
        if method and UPLOAD_METHOD_NAME_RE.search(method):
            findings.append(
                (
                    "ERROR",
                    f"{cls_path.relative_to(root)}: `{method}` is annotated "
                    "`@AuraEnabled(cacheable=true)` but its name says it writes. A cacheable "
                    "method \"must only get data, it can't mutate (change) data\" "
                    "(lwc_guide apex-result-caching L7254). Drop cacheable and call it "
                    "imperatively (lwc_guide apex-call-imperative L7190).",
                )
            )
        elif creates_version or creates_link:
            findings.append(
                (
                    "ERROR",
                    f"{cls_path.relative_to(root)}: an `@AuraEnabled(cacheable=true)` method "
                    "lives in a class that inserts file records. A cacheable method must not "
                    "mutate data (lwc_guide apex-result-caching L7254).",
                )
            )

    return findings


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)

    if not root.exists() or not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}", file=sys.stderr)
        return 1

    bundles = find_bundles(root)
    classes = sorted(walk(root, ".cls"))

    if not bundles and not classes:
        print(
            f"WARN: no Lightning Web Component bundles and no Apex classes found under {root}; "
            "nothing to check. Point --manifest-dir at a Salesforce source tree."
        )
        return 0

    findings: list[tuple[str, str]] = []
    for bundle in bundles:
        findings.extend(check_bundle(bundle, root))
    for cls_path in classes:
        findings.extend(check_apex(cls_path, root))

    scanned = f"{len(bundles)} bundle(s) and {len(classes)} Apex class(es)"
    if not findings:
        print(f"No file-upload issues found across {scanned}.")
        return 0

    findings.sort(key=lambda f: (LEVELS.index(f[0]), f[1]))
    for level, message in findings:
        print(f"{level}: {message}")

    counts = {level: sum(1 for f in findings if f[0] == level) for level in LEVELS}
    print(
        f"\n{counts['ERROR']} error(s), {counts['WARN']} warning(s), "
        f"{counts['ADVISORY']} advisory across {scanned}."
    )

    if counts["ERROR"]:
        return 1
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
