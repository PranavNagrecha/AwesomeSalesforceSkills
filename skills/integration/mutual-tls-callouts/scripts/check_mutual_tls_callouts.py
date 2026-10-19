#!/usr/bin/env python3
"""Checker for the mutual-tls-callouts skill.

Scans a metadata source directory (SFDX package directory or a retrieve).

Certificates (certs/<Name>.crt-meta.xml):
  ERROR  expirationDate in the past
  WARN   expirationDate within --warn-days (default 60)
  WARN   privateKeyExportable true or not specified (defaults to true)
Named Credentials (namedCredentials/*.namedCredential-meta.xml):
  ERROR  a ClientCertificate parameter naming a certificate that isn't in source,
         when certificates are present in source
  WARN   the legacy top-level <certificate> field (deprecated in API 56.0)
Apex (.cls, comments and strings ignored):
  ERROR  HttpRequest.setClientCertificate( — deprecated; key store and password in code
  WARN   setClientCertificateName( — works, but a Named Credential binding is preferred

Exit 1 on ERROR (or WARN with --strict) and when --manifest-dir is missing. Stdlib only.

Usage:
    python3 check_mutual_tls_callouts.py --manifest-dir force-app
    python3 check_mutual_tls_callouts.py --manifest-dir cert-check --warn-days 90 --strict
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"


def _child(elem: ET.Element, tag: str) -> ET.Element | None:
    found = elem.find(NS + tag)
    if found is not None:
        return found
    return elem.find(tag)


def _children(elem: ET.Element, tag: str) -> list[ET.Element]:
    return elem.findall(NS + tag) + elem.findall(tag)


def _text(elem: ET.Element, tag: str) -> str | None:
    node = _child(elem, tag)
    return None if node is None else (node.text or "").strip()


def strip_code(src: str) -> str:
    src = re.sub(r"/\*.*?\*/", lambda m: re.sub(r"[^\n]", " ", m.group(0)), src, flags=re.S)
    src = re.sub(r"//[^\n]*", "", src)
    return re.sub(r"'(?:\\.|[^'\\])*'", "''", src)


def check_certs(root: Path, warn_days: int, today: dt.date, out: list[tuple[str, str]]) -> set[str]:
    names: set[str] = set()
    for path in sorted(root.rglob("*.crt-meta.xml")):
        names.add(path.name[: -len(".crt-meta.xml")])
        try:
            xml = ET.parse(path).getroot()
        except ET.ParseError as exc:
            out.append(("ERROR", f"{path}: not well-formed XML ({exc})"))
            continue
        exp = _text(xml, "expirationDate")
        if exp:
            try:
                day = dt.date.fromisoformat(exp[:10])
                left = (day - today).days
                if left < 0:
                    out.append(("ERROR", f"{path}: certificate expired on {day}"))
                elif left <= warn_days:
                    out.append(("WARN", f"{path}: certificate expires in {left} day(s) ({day}); start renewal"))
            except ValueError:
                out.append(("WARN", f"{path}: unreadable expirationDate '{exp}'"))
        exportable = _text(xml, "privateKeyExportable")
        if exportable is None or exportable.lower() == "true":
            out.append(("WARN", f"{path}: privateKeyExportable is {exportable or 'unspecified (defaults to true)'}; create mTLS keys with export off"))
    return names


def check_named_credentials(root: Path, certs: set[str], out: list[tuple[str, str]]) -> int:
    n = 0
    for path in sorted(root.rglob("*.namedCredential-meta.xml")):
        n += 1
        try:
            xml = ET.parse(path).getroot()
        except ET.ParseError as exc:
            out.append(("ERROR", f"{path}: not well-formed XML ({exc})"))
            continue
        legacy = _child(xml, "certificate")
        if legacy is not None and (legacy.text or "").strip():
            out.append(("WARN", f"{path}: legacy <certificate> field (deprecated in API 56.0); use a ClientCertificate parameter"))
        for param in _children(xml, "namedCredentialParameters"):
            if (_text(param, "parameterType") or "") != "ClientCertificate":
                continue
            cert = _text(param, "certificate") or ""
            if certs and cert not in certs:
                out.append(("ERROR", f"{path}: ClientCertificate parameter names '{cert}', which isn't in source certificates {sorted(certs)}"))
            elif not certs:
                out.append(("WARN", f"{path}: ClientCertificate '{cert}' can't be verified; no certs/*.crt-meta.xml in source"))
    return n


def check_apex(root: Path, out: list[tuple[str, str]]) -> int:
    n = 0
    for path in sorted(root.rglob("*.cls")):
        code = strip_code(path.read_text(encoding="utf-8", errors="ignore"))
        if "setClientCertificate" not in code:
            continue
        n += 1
        for m in re.finditer(r"\.setClientCertificate(Name)?\s*\(", code):
            line = code.count("\n", 0, m.start()) + 1
            if m.group(1):
                out.append(("WARN", f"{path}:{line}: setClientCertificateName works, but binding the certificate on a Named Credential keeps it out of code"))
            else:
                out.append(("ERROR", f"{path}:{line}: setClientCertificate is deprecated and puts key material in code; use a Named Credential ClientCertificate parameter"))
    return n


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check mTLS certificates, Named Credentials, and Apex.")
    parser.add_argument("--manifest-dir", required=True, type=Path, help="Metadata source directory to scan.")
    parser.add_argument("--warn-days", type=int, default=60, help="Warn when a certificate expires within this many days.")
    parser.add_argument("--today", help="Override today's date (YYYY-MM-DD) for reproducible runs.")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on WARN as well as ERROR.")
    args = parser.parse_args(argv)
    root = args.manifest_dir
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    out: list[tuple[str, str]] = []
    certs = check_certs(root, args.warn_days, today, out)
    ncs = check_named_credentials(root, certs, out)
    apex = check_apex(root, out)
    if not certs and not ncs and not apex:
        print(f"WARN: no certificates, Named Credentials, or client-certificate Apex under {root}; nothing to check")
        return 0
    for level, msg in out:
        print(f"{level}: {msg}")
    errors = sum(1 for lvl, _ in out if lvl == "ERROR")
    warns = len(out) - errors
    print(f"Checked {len(certs)} certificate(s), {ncs} Named Credential(s), {apex} Apex file(s): {errors} error(s), {warns} warning(s).")
    return 1 if errors or (args.strict and warns) else 0


if __name__ == "__main__":
    sys.exit(main())
