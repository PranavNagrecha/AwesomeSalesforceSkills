#!/usr/bin/env python3
"""Review local email template files for hardcoded addresses and missing merge context.

Scope
-----
Only real email-template artefacts are linted:

  * any file whose name ends `.email` or `.email-meta.xml`, wherever it sits;
  * body files (`.html`, `.htm`, `.txt`, `.email`) that live under an `email/`
    directory — the Metadata API layout for EmailFolder / EmailTemplate.

Everything else in the tree is left alone. In particular `*.md` notes that sit
beside the templates (a sender-identity note, a deploy-order note) are NOT
templates and are never linted: doing so produced three phantom REVIEW findings
per note ("no merge fields", "subject line is not documented", and the
org-wide sender address read as a hardcoded address).

Severities and exit codes
-------------------------
  ERROR   the paths matched no email-template artefact at all, or a
          `.email-meta.xml` that will not parse
  REVIEW  a question for a human: hardcoded sender address, no merge fields in
          a body, no `<subject>` on a template's meta XML

  0 -- no ERROR (and no REVIEW when --strict is passed)
  1 -- at least one ERROR, or at least one REVIEW under --strict

stdlib only.

Usage:
    python3 check_email_templates.py force-app/main/default/email
    python3 check_email_templates.py --manifest-dir artefacts/M3-S02
    python3 check_email_templates.py --manifest-dir artefacts/M3-S02 --strict
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


BODY_SUFFIXES = (".html", ".htm", ".txt", ".email")
META_SUFFIX = ".email-meta.xml"
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
SEVERITY_WEIGHTS = {"CRITICAL": 20, "ERROR": 20, "HIGH": 10, "MEDIUM": 5, "LOW": 1, "REVIEW": 0}
ERROR_SEVERITIES = {"ERROR", "CRITICAL"}


def is_template_artefact(path: Path) -> bool:
    """True when `path` is an email template body or its meta XML."""
    name = path.name.lower()
    if name.endswith(META_SUFFIX):
        return True
    if name.endswith(".email"):
        return True
    if name.endswith(".md"):
        # Notes that sit beside templates are documentation, not templates.
        return False
    if path.suffix.lower() in BODY_SUFFIXES:
        # A body file only counts inside the Metadata API `email/` layout.
        return any(part.lower() == "email" for part in path.parts[:-1])
    return False


def iter_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            for candidate in path.rglob("*"):
                if candidate.is_file() and is_template_artefact(candidate):
                    files.append(candidate)
        elif path.is_file() and is_template_artefact(path):
            files.append(path)
    return sorted(set(files))


def normalize_finding(finding: str) -> dict[str, str]:
    severity, _, remainder = finding.partition(" ")
    location = ""
    message = remainder
    if ": " in remainder:
        location, message = remainder.split(": ", 1)
    return {"severity": severity or "INFO", "location": location, "message": message}


def emit_result(findings: list[str], summary: str, strict: bool) -> int:
    normalized = [normalize_finding(finding) for finding in findings]
    score = max(0, 100 - sum(SEVERITY_WEIGHTS.get(item["severity"], 0) for item in normalized))
    print(json.dumps({"score": score, "findings": normalized, "summary": summary}, indent=2))

    errors = [item for item in normalized if item["severity"] in ERROR_SEVERITIES]
    reviews = [item for item in normalized if item["severity"] not in ERROR_SEVERITIES]

    if errors:
        print(f"ERROR: {len(errors)} blocking finding(s) detected", file=sys.stderr)
    if reviews:
        print(f"REVIEW: {len(reviews)} finding(s) to answer", file=sys.stderr)

    if errors:
        return 1
    if strict and reviews:
        print("--strict: failing on REVIEW findings.", file=sys.stderr)
        return 1
    return 0


def audit_meta_xml(path: Path) -> list[str]:
    """Lint an EmailTemplate meta XML: subject present, sender not hardcoded."""
    findings: list[str] = []
    content = path.read_text(encoding="utf-8", errors="ignore")

    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as exc:
        findings.append(f"ERROR {path}: template meta XML will not parse ({exc})")
        return findings

    subject = ""
    for element in root:
        if element.tag.rsplit("}", 1)[-1] == "subject":
            subject = (element.text or "").strip()
    if not subject:
        findings.append(f"REVIEW {path}: template has no <subject>; the subject line is not documented")

    for address in sorted(set(EMAIL_RE.findall(content))):
        if not address.lower().startswith("example") and ".example" not in address.lower():
            findings.append(
                f"REVIEW {path}: hardcoded email address `{address}` found in template metadata"
            )
    return findings


def audit_body(path: Path) -> list[str]:
    """Lint an email template body: merge fields present, sender not hardcoded."""
    findings: list[str] = []
    content = path.read_text(encoding="utf-8", errors="ignore")

    for address in sorted(set(EMAIL_RE.findall(content))):
        if not address.lower().startswith("example") and ".example" not in address.lower():
            findings.append(
                f"REVIEW {path}: hardcoded email address `{address}` found in template content"
            )

    if "{!" not in content and "{{" not in content:
        findings.append(f"REVIEW {path}: no obvious merge fields found")

    return findings


def audit_file(path: Path) -> list[str]:
    if path.name.lower().endswith(META_SUFFIX):
        return audit_meta_xml(path)
    return audit_body(path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check email template files for hardcoded addresses and missing merge context."
    )
    parser.add_argument("paths", nargs="*", help="Files or directories to scan")
    parser.add_argument(
        "--manifest-dir",
        action="append",
        default=[],
        dest="manifest_dirs",
        help="Directory to scan — an alias of the positional paths; may be repeated.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 on REVIEW findings as well as errors.",
    )
    args = parser.parse_args()

    targets = [Path(value) for value in list(args.paths) + list(args.manifest_dirs)]
    if not targets:
        parser.error("give at least one path, either positionally or with --manifest-dir")

    files = iter_files(targets)
    if not files:
        return emit_result(
            [
                "ERROR "
                + ", ".join(str(target) for target in targets)
                + ": no email template artefact found — expected `*.email`, "
                "`*.email-meta.xml`, or a body file under an `email/` directory"
            ],
            "Scanned 0 email template file(s); no files matched the provided paths.",
            args.strict,
        )

    findings: list[str] = []
    for path in files:
        findings.extend(audit_file(path))

    summary = f"Scanned {len(files)} email template file(s); {len(findings)} finding(s) detected."
    return emit_result(findings, summary, args.strict)


if __name__ == "__main__":
    sys.exit(main())
