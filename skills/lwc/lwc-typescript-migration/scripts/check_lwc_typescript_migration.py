#!/usr/bin/env python3
"""Inspect an SFDX project for high-confidence LWC TypeScript migration issues."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Finding:
    level: str
    code: str
    message: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit an LWC TypeScript migration.")
    parser.add_argument("--project", required=True, help="Salesforce DX project root")
    parser.add_argument("--strict", action="store_true", help="Fail on warnings as well as errors")
    return parser.parse_args()


def load_json(path: Path, findings: list[Finding]) -> dict:
    if not path.is_file():
        findings.append(Finding("ERROR", "MISSING_FILE", f"missing {path.relative_to(path.parent.parent) if len(path.parents) > 1 else path}"))
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        findings.append(Finding("ERROR", "INVALID_JSON", f"cannot parse {path}: {exc}"))
        return {}
    if not isinstance(data, dict):
        findings.append(Finding("ERROR", "INVALID_JSON_ROOT", f"{path} root must be an object"))
        return {}
    return data


def iter_lwc_roots(project: Path, sfdx: dict) -> Iterable[Path]:
    for item in sfdx.get("packageDirectories", []):
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            continue
        package = project / item["path"]
        for root in package.glob("**/lwc"):
            if root.is_dir():
                yield root


def scan_sources(lwc_roots: Iterable[Path]) -> tuple[list[Path], list[Path], list[Finding]]:
    ts_files: list[Path] = []
    js_files: list[Path] = []
    findings: list[Finding] = []
    for root in lwc_roots:
        ts_files.extend(path for path in root.rglob("*.ts") if not path.name.endswith(".d.ts"))
        js_files.extend(path for path in root.rglob("*.js") if "__tests__" not in path.parts)
        by_parent_stem: dict[tuple[Path, str], set[str]] = {}
        for path in [*root.rglob("*.ts"), *root.rglob("*.js")]:
            if path.name.endswith(".d.ts") or "__tests__" in path.parts:
                continue
            by_parent_stem.setdefault((path.parent, path.stem), set()).add(path.suffix)
        for (parent, stem), suffixes in sorted(by_parent_stem.items(), key=lambda item: str(item[0])):
            if {".js", ".ts"}.issubset(suffixes):
                findings.append(Finding(
                    "ERROR", "SAME_STEM_COLLISION",
                    f"{parent / stem} has both .js and .ts implementation sources; declare generated ownership or remove one",
                ))
    return ts_files, js_files, findings


def scan_unsafe_types(paths: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    patterns = (
        ("EXPLICIT_ANY", re.compile(r"\bany\b"), "explicit any requires review"),
        ("TS_IGNORE", re.compile(r"@ts-ignore"), "@ts-ignore suppresses a compiler error"),
        ("DOUBLE_CAST", re.compile(r"\bas\s+unknown\s+as\b"), "double assertion bypasses type compatibility"),
    )
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        for code, pattern, message in patterns:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                findings.append(Finding("WARN", code, f"{path}:{line}: {message}"))
    return findings


def main() -> int:
    args = parse_args()
    project = Path(args.project).resolve()
    if not project.is_dir():
        print(f"ERROR: project directory not found: {project}")
        return 2

    findings: list[Finding] = []
    sfdx_path = project / "sfdx-project.json"
    sfdx = load_json(sfdx_path, findings)
    package = load_json(project / "package.json", findings)

    lwc_roots = sorted(set(iter_lwc_roots(project, sfdx)))
    if not lwc_roots:
        findings.append(Finding("ERROR", "NO_LWC_ROOT", "no LWC directory found under declared package directories"))
    ts_files, js_files, source_findings = scan_sources(lwc_roots)
    findings.extend(source_findings)

    if ts_files:
        if not (project / "tsconfig.json").is_file() and not any((root / "tsconfig.json").is_file() for root in lwc_roots):
            findings.append(Finding("ERROR", "MISSING_TSCONFIG", "TypeScript sources exist but no project or LWC tsconfig.json was found"))
        dev_deps = package.get("devDependencies", {}) if isinstance(package.get("devDependencies"), dict) else {}
        if "typescript" not in dev_deps:
            findings.append(Finding("ERROR", "MISSING_TYPESCRIPT_DEP", "TypeScript sources exist but typescript is not a devDependency"))
        if "@salesforce/lightning-types" not in dev_deps:
            findings.append(Finding("WARN", "MISSING_LIGHTNING_TYPES", "@salesforce/lightning-types is not a devDependency"))
        scripts = package.get("scripts", {}) if isinstance(package.get("scripts"), dict) else {}
        script_text = " ".join(str(value) for value in scripts.values())
        if "tsc" not in script_text and sfdx.get("defaultLwcLanguage") != "typescript":
            findings.append(Finding("ERROR", "UNDECLARED_STRATEGY", "TypeScript exists but neither a tsc build script nor defaultLwcLanguage=typescript declares the deployment strategy"))
        findings.extend(scan_unsafe_types(ts_files))

    settings_path = project / ".vscode" / "settings.json"
    if settings_path.is_file():
        settings_text = settings_path.read_text(encoding="utf-8", errors="replace")
        if "preview.typeScriptSupport" in settings_text:
            findings.append(Finding("WARN", "DEPRECATED_PREVIEW_FLAG", f"{settings_path} uses the deprecated TypeScript preview setting"))

    language = sfdx.get("defaultLwcLanguage")
    if language not in (None, "javascript", "typescript"):
        findings.append(Finding("ERROR", "INVALID_DEFAULT_LANGUAGE", f"defaultLwcLanguage has unsupported value: {language!r}"))
    if ts_files and language is None:
        findings.append(Finding("WARN", "DEFAULT_LANGUAGE_UNSET", "TypeScript sources exist but defaultLwcLanguage is not declared"))

    for finding in findings:
        print(f"{finding.level} [{finding.code}] {finding.message}")
    print(f"SUMMARY ts_files={len(ts_files)} js_files={len(js_files)} errors={sum(f.level == 'ERROR' for f in findings)} warnings={sum(f.level == 'WARN' for f in findings)}")

    errors = any(f.level == "ERROR" for f in findings)
    warnings = any(f.level == "WARN" for f in findings)
    return 1 if errors or (args.strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
