#!/usr/bin/env python3
"""Static checks for Experience Cloud CI/CD pipelines.

Scans pipeline definitions and helper scripts for the high-confidence
anti-patterns documented in this skill:

  1. Pipeline deploys ExperienceBundle / DigitalExperienceBundle but
     has NO `assign permset` step nearby — guest user not reconciled.
  2. Pipeline single-step `sf project deploy start --source-dir force-app`
     against a project that contains experiences/ or digitalExperiences/
     — likely missing metadata-ordering rules.
  3. Pipeline references `experiences/` (Aura) source path when the
     project clearly contains `digitalExperiences/` (LWR), or vice
     versa.
  4. Pipeline mentions `CustomDomain` deploy without any DNS / CNAME
     coordination step (artifact emit / manual approval).

Stdlib only. Heuristic; signal tool not parser.

Usage:
    python3 check_cicd_for_experience_cloud.py --src-root .
    python3 check_cicd_for_experience_cloud.py --help
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_BUNDLE_DEPLOY_RE = re.compile(
    r"sf\s+project\s+deploy\s+start.+?(?:experiences|digitalExperiences)",
    re.IGNORECASE | re.DOTALL,
)
_PERMSET_ASSIGN_RE = re.compile(
    r"sf\s+org\s+assign\s+permset|assign-guest-permsets|assignPermset",
    re.IGNORECASE,
)
_PROJECT_WIDE_DEPLOY_RE = re.compile(
    r"sf\s+project\s+deploy\s+start\s+--source-dir\s+force-app(?:/main(?:/default)?)?\s",
    re.IGNORECASE,
)
_CUSTOM_DOMAIN_RE = re.compile(r"\bCustomDomain\b|customDomains", re.IGNORECASE)
_DNS_COORDINATION_RE = re.compile(
    r"\b(dns-targets|cname|dns_team|cname_target|emit-dns|dns confirmation)\b",
    re.IGNORECASE,
)


def _line_no(text: str, pos: int) -> int:
    return text[:pos].count("\n") + 1


def _scan_pipeline(path: Path, project_has_lwr: bool, project_has_aura: bool) -> list[str]:
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError as exc:
        return [f"could not read {path}: {exc}"]

    has_bundle_deploy = bool(_BUNDLE_DEPLOY_RE.search(text))
    has_permset_assign = bool(_PERMSET_ASSIGN_RE.search(text))

    # Smell 1: bundle deploy without permset assign
    if has_bundle_deploy and not has_permset_assign:
        m = _BUNDLE_DEPLOY_RE.search(text)
        findings.append(
            f"{path}:{_line_no(text, m.start())}: pipeline deploys an Experience Cloud bundle "
            "but has no `sf org assign permset` step nearby — guest user will not be "
            "reconciled, anonymous access likely to fail post-deploy "
            "(references/llm-anti-patterns.md § 3)"
        )

    # Smell 2: project-wide deploy in a project with Experience Cloud bundles
    if (project_has_lwr or project_has_aura) and _PROJECT_WIDE_DEPLOY_RE.search(text):
        m = _PROJECT_WIDE_DEPLOY_RE.search(text)
        findings.append(
            f"{path}:{_line_no(text, m.start())}: project-wide `sf project deploy --source-dir "
            "force-app` against a project with Experience Cloud bundles — likely missing "
            "the metadata-ordering rules (foundation → Network → bundle → BrandingSet) "
            "(references/llm-anti-patterns.md § 1)"
        )

    # Smell 3: wrong bundle path for the project type
    if project_has_lwr and not project_has_aura:
        for m in re.finditer(
            r"--source-dir\s+\S*?/experiences(?:/|\b)",
            text,
            re.IGNORECASE,
        ):
            findings.append(
                f"{path}:{_line_no(text, m.start())}: pipeline deploys from `experiences/` "
                "(Aura) but the project contains `digitalExperiences/` (LWR) — wrong "
                "bundle path for this site type "
                "(references/llm-anti-patterns.md § 4)"
            )
    if project_has_aura and not project_has_lwr:
        for m in re.finditer(
            r"--source-dir\s+\S*?/digitalExperiences(?:/|\b)",
            text,
            re.IGNORECASE,
        ):
            findings.append(
                f"{path}:{_line_no(text, m.start())}: pipeline deploys from "
                "`digitalExperiences/` (LWR) but the project contains `experiences/` "
                "(Aura) — wrong bundle path for this site type "
                "(references/llm-anti-patterns.md § 4)"
            )

    # Smell 4: custom-domain deploy with no DNS coordination
    if _CUSTOM_DOMAIN_RE.search(text) and not _DNS_COORDINATION_RE.search(text):
        m = _CUSTOM_DOMAIN_RE.search(text)
        findings.append(
            f"{path}:{_line_no(text, m.start())}: pipeline deploys CustomDomain metadata "
            "but has no DNS-coordination step (CNAME emit, dns-targets artifact, manual "
            "approval gate) — site likely unreachable post-deploy "
            "(references/llm-anti-patterns.md § 5)"
        )

    return findings


def scan_tree(root: Path) -> list[str]:
    if not root.exists():
        return [f"src-root does not exist: {root}"]
    if not root.is_dir():
        return [f"src-root is not a directory: {root}"]

    # Probe project for bundle types present.
    project_has_lwr = bool(list(root.rglob("digitalExperiences"))) or bool(
        list(root.rglob("digitalExperiences/**"))
    )
    project_has_aura = bool(list(root.rglob("experiences"))) and not project_has_lwr

    findings: list[str] = []
    pipeline_globs = [
        "**/.github/workflows/*.yml",
        "**/.github/workflows/*.yaml",
        "**/Jenkinsfile",
        "**/.gitlab-ci.yml",
        "**/azure-pipelines.yml",
        "**/.circleci/config.yml",
    ]
    for pattern in pipeline_globs:
        for f in root.glob(pattern):
            findings.extend(_scan_pipeline(f, project_has_lwr, project_has_aura))

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Scan Experience Cloud CI/CD pipelines for known "
            "anti-patterns (missing guest-user reconciliation, "
            "project-wide deploy without ordering, wrong bundle path, "
            "custom-domain deploy without DNS coordination)."
        ),
    )
    parser.add_argument(
        "--src-root", default=".",
        help="Root of the project tree (default: current directory).",
    )
    args = parser.parse_args()

    findings = scan_tree(Path(args.src_root))

    if not findings:
        print("OK: no Experience Cloud CI/CD anti-patterns detected.")
        return 0

    for f in findings:
        print(f"WARN: {f}", file=sys.stderr)
    print(f"\n{len(findings)} finding(s).", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
