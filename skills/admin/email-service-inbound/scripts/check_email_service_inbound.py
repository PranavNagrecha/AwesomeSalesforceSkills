#!/usr/bin/env python3
"""Static checks for an Email Service package (metadata + Apex handler).

Run against a Salesforce DX metadata root, e.g. force-app/main/default:

    python3 check_email_service_inbound.py --manifest-dir force-app/main/default

Metadata checks (emailservices/*.xml):
  M1. The EmailServicesFunction file is well-formed XML with the expected
      root element.
  M2. `apexClass` names a class that exists under classes/ in the same
      manifest directory.
  M3. `isActive` is present and true (an inactive service routes mail by
      `functionInactiveAction`, not to Apex).
  M4. At least one `emailServicesAddresses` entry exists, and every entry
      carries `runAsUser`, `localPart` and `developerName` (all Required
      per the Metadata API guide's EmailServicesAddress field table).
  M5. `errorRoutingAddress` is present whenever `isErrorRoutingEnabled`
      is true, otherwise failures notify the sender instead of the team.
  M6. `overLimitAction` / `functionInactiveAction` are not left on
      `UseSystemDefault`, and no fabricated `maxEmailSize` element is
      present.

Apex checks (classes/*.cls, only for InboundEmailHandler implementations):
  A1. `handleInboundEmail` returns a Messaging.InboundEmailResult on at
      least one path (a handler that never builds one cannot report
      failure).
  A2. No DML statement inside a loop over email attachments.
  A3. No stack trace assigned to an InboundEmailResult `message` field —
      that string is mailed to the original sender.
  A4. No synchronous Http().send(...) inside the handler.
  A5. No Map-style `email.headers.get(...)`; and a nudge toward the
      first-class `inReplyTo` / `references` / `messageId` properties.
  A6. A `global` class must declare `handleInboundEmail` `global` too.
      (`public` classes are fine — the Apex Developer Guide's own samples
      are `public with sharing`; see references/gotchas.md section 1.)

Stdlib only.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MDAPI_NS = "http://soap.sforce.com/2006/04/metadata"

# ---------------------------------------------------------------------------
# XML helpers.  A leaf ElementTree Element is falsy, so `a.find(x) or a.find(y)`
# silently discards a real, empty element.  Always compare against None.
# ---------------------------------------------------------------------------


def child(parent, tag):
    """Return the first direct child named `tag`, namespaced or not, or None."""
    if parent is None:
        return None
    found = parent.find(f"{{{MDAPI_NS}}}{tag}")
    if found is None:
        found = parent.find(tag)
    return found


def children(parent, tag):
    """Return all direct children named `tag`, namespaced or not."""
    if parent is None:
        return []
    found = parent.findall(f"{{{MDAPI_NS}}}{tag}")
    if not found:
        found = parent.findall(tag)
    return found


def text_of(parent, tag):
    """Return the stripped text of child `tag`, or None if absent/empty."""
    node = child(parent, tag)
    if node is None or node.text is None:
        return None
    value = node.text.strip()
    return value or None


def is_true(parent, tag):
    value = text_of(parent, tag)
    return value is not None and value.lower() == "true"


def local_name(tag: str) -> str:
    return tag.split("}", 1)[-1]


# ---------------------------------------------------------------------------
# Metadata checks
# ---------------------------------------------------------------------------

_SYSTEM_DEFAULT_FIELDS = ("overLimitAction", "functionInactiveAction")


def check_email_services(manifest_dir: Path) -> list[str]:
    findings: list[str] = []
    svc_dir = manifest_dir / "emailservices"
    if not svc_dir.is_dir():
        return findings

    xml_files = sorted(p for p in svc_dir.glob("*.xml"))
    if not xml_files:
        return findings

    class_names = {
        p.stem for p in (manifest_dir / "classes").glob("*.cls")
    } if (manifest_dir / "classes").is_dir() else set()

    for xml_file in xml_files:
        rel = xml_file.relative_to(manifest_dir)

        # M1 — well-formed, right root.
        try:
            root = ET.parse(xml_file).getroot()
        except ET.ParseError as exc:
            findings.append(f"{rel}: not well-formed XML — {exc}")
            continue
        if local_name(root.tag) != "EmailServicesFunction":
            findings.append(
                f"{rel}: root element is <{local_name(root.tag)}>, expected "
                "<EmailServicesFunction> (references/metadata-examples.md)"
            )
            continue

        name = text_of(root, "functionName") or rel.name

        # M2 — apexClass resolves.
        apex_class = text_of(root, "apexClass")
        if apex_class is None:
            findings.append(
                f"{rel}: <apexClass> is missing — it is Required on "
                "EmailServicesFunction and the deploy will fail"
            )
        elif class_names and apex_class not in class_names:
            findings.append(
                f"{rel}: apexClass '{apex_class}' has no classes/{apex_class}.cls "
                "in this manifest — deploy it in the same payload or before "
                "this file (references/metadata-examples.md, Retrieve and deploy)"
            )

        # M3 — active.
        if not is_true(root, "isActive"):
            findings.append(
                f"{rel}: service '{name}' has isActive != true — inbound mail is "
                "handled by functionInactiveAction, not by Apex "
                "(references/gotchas.md section 10)"
            )

        # M4 — addresses.
        addresses = children(root, "emailServicesAddresses")
        if not addresses:
            findings.append(
                f"{rel}: service '{name}' declares no <emailServicesAddresses> — "
                "an email service only processes messages received at one of "
                "its addresses"
            )
        for idx, addr in enumerate(addresses, start=1):
            dev_name = text_of(addr, "developerName") or f"#{idx}"
            for required in ("developerName", "localPart", "runAsUser"):
                if text_of(addr, required) is None:
                    findings.append(
                        f"{rel}: address {dev_name} is missing Required "
                        f"<{required}> (references/gotchas.md section 6)"
                    )
            if not is_true(addr, "isActive"):
                findings.append(
                    f"{rel}: address {dev_name} has isActive != true — mail sent "
                    "to it is handled by the service's inactive-address action"
                )

        # M5 — error routing.
        if is_true(root, "isErrorRoutingEnabled") and text_of(
            root, "errorRoutingAddress"
        ) is None:
            findings.append(
                f"{rel}: isErrorRoutingEnabled is true but <errorRoutingAddress> "
                "is empty — error notifications fall back to the sender and no "
                "one internal learns intake is broken"
            )
        if not is_true(root, "isErrorRoutingEnabled") and text_of(
            root, "errorRoutingAddress"
        ) is not None:
            findings.append(
                f"{rel}: <errorRoutingAddress> is set but isErrorRoutingEnabled "
                "is not true — the address is ignored"
            )

        # M6 — deliberate failure actions, and no invented elements.
        for field in _SYSTEM_DEFAULT_FIELDS:
            value = text_of(root, field)
            if value is None:
                findings.append(
                    f"{rel}: <{field}> is missing — it is Required on "
                    "EmailServicesFunction"
                )
            elif value == "UseSystemDefault":
                findings.append(
                    f"{rel}: {field} is UseSystemDefault — decide Bounce, "
                    "Discard or Requeue explicitly for a business-critical "
                    "intake (references/gotchas.md section 10)"
                )
        if child(root, "maxEmailSize") is not None:
            findings.append(
                f"{rel}: <maxEmailSize> is not a field on EmailServicesFunction — "
                "the ~25 MB ceiling is a platform limit, not configuration "
                "(references/gotchas.md section 4)"
            )

    return findings


# ---------------------------------------------------------------------------
# Apex checks
# ---------------------------------------------------------------------------

_IMPL_RE = re.compile(
    r"\b(public|global)\s+(?:virtual\s+|abstract\s+|with\s+sharing\s+|"
    r"without\s+sharing\s+|inherited\s+sharing\s+)*class\s+(\w+)"
    r"[^\{]*?implements[^\{]*?Messaging\.InboundEmailHandler",
    re.IGNORECASE,
)
_METHOD_RE = re.compile(
    r"\b(public|global|private|protected)\s+Messaging\.InboundEmailResult\s+"
    r"handleInboundEmail\s*\(",
    re.IGNORECASE,
)
_RESULT_RETURN_RE = re.compile(
    r"\bnew\s+Messaging\.InboundEmailResult\s*\(", re.IGNORECASE
)
_STACK_TRACE_LEAK_RE = re.compile(
    r"\.message\s*=\s*[^;]*getStackTraceString\s*\(", re.IGNORECASE
)
_SYNC_HTTP_RE = re.compile(r"\bnew\s+Http\s*\(\s*\)\s*\.send\s*\(", re.IGNORECASE)
_HEADERS_GET_RE = re.compile(r"\bemail\.headers\.get\s*\(", re.IGNORECASE)
_ATTACHMENT_LOOP_RE = re.compile(
    r"\bfor\s*\([^)]*\b(?:binaryAttachments|textAttachments)\b[^)]*\)\s*\{",
    re.IGNORECASE,
)
_DML_RE = re.compile(
    r"^\s*(insert|update|upsert|delete|undelete)\s+(?!as\s+system\b)"
    r"(?:as\s+user\s+)?[A-Za-z_]",
    re.IGNORECASE | re.MULTILINE,
)
_HEADER_HUNT_RE = re.compile(
    r"['\"](?:in-reply-to|message-id|references)['\"]", re.IGNORECASE
)


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _block_end(text: str, open_brace_pos: int) -> int:
    """Index just past the matching close brace for the brace at the given pos."""
    depth = 0
    for i in range(open_brace_pos, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
    return len(text)


def _scan_apex(path: Path, rel: Path) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {rel}: {exc}"]

    impl = _IMPL_RE.search(text)
    is_handler = impl is not None

    # A6 — a global class needs a global interface method.
    if is_handler and impl.group(1).lower() == "global":
        method = _METHOD_RE.search(text)
        if method is not None and method.group(1).lower() != "global":
            findings.append(
                f"{rel}:{_line_no(text, method.start())}: class "
                f"`{impl.group(2)}` is global but handleInboundEmail is "
                f"`{method.group(1).lower()}` — raise the method to global or "
                "drop the class to public (references/gotchas.md section 1)"
            )

    # A1 — the handler must be able to build a result.
    if is_handler and not _RESULT_RETURN_RE.search(text):
        findings.append(
            f"{rel}:{_line_no(text, impl.start())}: handler never constructs a "
            "Messaging.InboundEmailResult — it cannot report failure, and a "
            "null result is treated as success"
        )

    # A2 — DML inside an attachment loop.
    if is_handler:
        for loop in _ATTACHMENT_LOOP_RE.finditer(text):
            brace = text.index("{", loop.start())
            body = text[brace:_block_end(text, brace)]
            dml = _DML_RE.search(body)
            if dml is not None:
                findings.append(
                    f"{rel}:{_line_no(text, brace + dml.start())}: "
                    f"`{dml.group(1).lower()}` DML inside a loop over email "
                    "attachments — collect the records and issue one DML "
                    "statement after the loop (email services get a 50 MB heap "
                    "but the ordinary DML governor limits still apply, "
                    "references/gotchas.md section 11)"
                )

    # A3 — stack trace leak.
    for m in _STACK_TRACE_LEAK_RE.finditer(text):
        findings.append(
            f"{rel}:{_line_no(text, m.start())}: getStackTraceString() assigned "
            "to an InboundEmailResult.message — that string is mailed to the "
            "(possibly anonymous) sender (references/gotchas.md section 3)"
        )

    # A4 — synchronous callout.
    if is_handler:
        for m in _SYNC_HTTP_RE.finditer(text):
            findings.append(
                f"{rel}:{_line_no(text, m.start())}: synchronous `Http().send(...)` "
                "in an inbound email handler — publish a Platform Event and do "
                "the callout in a subscriber (references/gotchas.md section 9)"
            )

    # A5 — headers misuse.
    for m in _HEADERS_GET_RE.finditer(text):
        findings.append(
            f"{rel}:{_line_no(text, m.start())}: `email.headers.get(...)` — "
            "headers is InboundEmail.Header[], not a Map "
            "(references/gotchas.md section 2)"
        )
    if is_handler and "email.headers" in text.lower():
        for m in _HEADER_HUNT_RE.finditer(text):
            findings.append(
                f"{rel}:{_line_no(text, m.start())}: hunting for "
                f"{m.group(0)} in email.headers — the platform already parses "
                "it onto email.inReplyTo / email.messageId / email.references "
                "(references/gotchas.md section 2)"
            )

    return findings


def check_apex(manifest_dir: Path) -> list[str]:
    classes_dir = manifest_dir / "classes"
    roots = [classes_dir] if classes_dir.is_dir() else [manifest_dir]
    findings: list[str] = []
    seen: set[Path] = set()
    for root in roots:
        for apex in sorted(list(root.rglob("*.cls")) + list(root.rglob("*.trigger"))):
            if apex in seen:
                continue
            seen.add(apex)
            try:
                rel = apex.relative_to(manifest_dir)
            except ValueError:
                rel = apex
            findings.extend(_scan_apex(apex, rel))
    return findings


# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check an Email Service package: EmailServicesFunction metadata "
            "and its Messaging.InboundEmailHandler Apex class."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help=(
            "Root of the Salesforce metadata directory, e.g. "
            "force-app/main/default (default: current directory)."
        ),
    )
    args = parser.parse_args()

    manifest_dir = Path(args.manifest_dir)
    if not manifest_dir.exists():
        print(f"ERROR: --manifest-dir does not exist: {manifest_dir}", file=sys.stderr)
        return 2
    if not manifest_dir.is_dir():
        print(f"ERROR: --manifest-dir is not a directory: {manifest_dir}", file=sys.stderr)
        return 2

    findings = check_email_services(manifest_dir) + check_apex(manifest_dir)

    if not findings:
        print("OK: no Email Service configuration or handler issues detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
