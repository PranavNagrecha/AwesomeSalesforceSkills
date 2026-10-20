#!/usr/bin/env python3
"""Static checker for flow-http-callout-action.

Scans a metadata tree for the HTTP Callout prerequisites this skill names.
Stdlib only; never contacts an org.

Rules (grounding: Metadata API Developer Guide 264, api_meta):
  ERROR  ExternalCredential authenticationProtocol is not a documented value
         (AwsSv4, Basic, Custom, Jwt, JwtExchange, NoAuthentication, Oauth,
         Password) -- api_meta 264 L66186-66197. "OAuth" is the common slip.
  ERROR  NamedCredential uses <parameters> or puts the credential name in
         <parameterValue> -- the documented shape is <namedCredentialParameters>
         with an <externalCredential> element (api_meta 264 L93124-93135).
  WARN   Flow actionCalls with actionType externalService has no faultConnector
         (api_meta 264 L71282 for the actionType value; gotcha 3).
  WARN   NamedCredential namedCredentialType is Legacy (api_meta 264 L92875-92876).

ERROR findings exit 1 always. WARN findings exit 0 unless --strict.
An empty tree prints one WARN and exits 0. A missing path is an ERROR, exit 1.

Usage:
    python3 check_flow_http_callout_action.py --manifest-dir force-app/main/default [--strict]
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

PROTOCOLS = {"AwsSv4", "Basic", "Custom", "Jwt", "JwtExchange", "NoAuthentication", "Oauth", "Password"}


def local(el: ET.Element) -> str:
    return el.tag.split("}")[-1]


def kids(parent: ET.Element, name: str) -> list[ET.Element]:
    return [c for c in parent if local(c) == name]


def text(parent: ET.Element, name: str) -> str:
    for c in kids(parent, name):
        return (c.text or "").strip()
    return ""


def scan(root_dir: Path) -> tuple[list[str], list[str], int]:
    errors: list[str] = []
    warns: list[str] = []
    seen = 0
    for path in sorted(root_dir.rglob("*-meta.xml")):
        name = path.name
        if not name.endswith((".flow-meta.xml", ".externalCredential-meta.xml", ".namedCredential-meta.xml")):
            continue
        seen += 1
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            errors.append(f"{path}: XML does not parse ({exc})")
            continue
        if name.endswith(".externalCredential-meta.xml"):
            proto = text(root, "authenticationProtocol")
            if proto not in PROTOCOLS:
                errors.append(f"{path}: authenticationProtocol {proto!r} is not a documented value (api_meta 264 L66186-66197)")
        elif name.endswith(".namedCredential-meta.xml"):
            if kids(root, "parameters"):
                errors.append(f"{path}: <parameters> is not the documented element; use <namedCredentialParameters> (api_meta 264 L93124)")
            for p in kids(root, "namedCredentialParameters"):
                if text(p, "parameterType") == "Authentication" and not text(p, "externalCredential"):
                    errors.append(f"{path}: Authentication parameter has no <externalCredential> element (api_meta 264 L93131-93134)")
            if text(root, "namedCredentialType") == "Legacy":
                warns.append(f"{path}: namedCredentialType Legacy predates the Winter '23 schema (api_meta 264 L92875-92876)")
        else:
            for call in kids(root, "actionCalls"):
                if text(call, "actionType") == "externalService" and not kids(call, "faultConnector"):
                    warns.append(f"{path}: action {text(call, 'name') or '<unnamed>'} has no faultConnector")
    return errors, warns, seen


def main() -> int:
    parser = argparse.ArgumentParser(description="Check HTTP Callout credential and fault-path metadata.")
    parser.add_argument("--manifest-dir", default=".", help="Root of the metadata tree (default: current directory).")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on WARN findings too.")
    args = parser.parse_args()
    root_dir = Path(args.manifest_dir)
    if not root_dir.is_dir():
        print(f"ERROR: manifest directory not found: {root_dir}")
        sys.exit(1)
    errors, warns, seen = scan(root_dir)
    if seen == 0:
        print(f"WARN: no flow or credential metadata found under {root_dir}")
        return 1 if args.strict else 0
    for e in errors:
        print(f"ERROR: {e}")
    for w in warns:
        print(f"WARN: {w}")
    if not errors and not warns:
        print("No issues found.")
    if errors:
        sys.exit(1)
    return 1 if (warns and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
