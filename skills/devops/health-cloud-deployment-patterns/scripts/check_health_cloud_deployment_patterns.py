#!/usr/bin/env python3
"""Checker script for Health Cloud Deployment Patterns skill.

Validates a Salesforce metadata directory for Health Cloud deployment readiness.
Checks for common issues that cause Health Cloud deployments to fail or produce
partially functional orgs, based on the gotchas and patterns in this skill.

Uses stdlib only — no pip dependencies.

Usage:
    python3 check_health_cloud_deployment_patterns.py [--manifest-dir path/to/metadata]
    python3 check_health_cloud_deployment_patterns.py --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check a Salesforce metadata directory for Health Cloud deployment issues. "
            "Detects anti-patterns that cause failed or partially functional Health Cloud orgs."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_direct_careplan_dml(manifest_dir: Path) -> list[str]:
    """Detect Apex classes that perform direct DML on CarePlanTemplate__c objects.

    Direct DML on HealthCloudGA CarePlanTemplate__c objects bypasses the required
    invocable action and produces malformed templates that fail in the Care Plan wizard.
    """
    issues: list[str] = []
    apex_dir = manifest_dir / "classes"
    if not apex_dir.exists():
        return issues

    # Patterns that indicate direct DML on CarePlanTemplate namespace objects
    dml_pattern = re.compile(
        r"\b(insert|update|upsert|delete)\s+"
        r"[\w\s,\[\]]*"
        r"HealthCloudGA__CarePlanTemplate",
        re.IGNORECASE,
    )

    for cls_file in apex_dir.glob("*.cls"):
        try:
            content = cls_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if dml_pattern.search(content):
            issues.append(
                f"Direct DML on HealthCloudGA__CarePlanTemplate detected in {cls_file.name}. "
                "Care plan templates must be created via the HealthCloud.CreateCarePlanTemplate "
                "invocable action, not direct DML. Direct DML produces malformed templates."
            )

    return issues


def check_missing_hc_namespace_reference(manifest_dir: Path) -> list[str]:
    """Detect metadata that references HealthCloudGA namespace objects.

    This check identifies that the deployment package depends on the HealthCloudGA
    managed package and reminds the deployer that the package must be installed first.
    Emits a warning (not an error) to prompt verification.
    """
    issues: list[str] = []
    hcga_pattern = re.compile(r"HealthCloudGA__", re.IGNORECASE)

    # Search in common metadata file types
    extensions = [".xml", ".cls", ".trigger", ".flow-meta.xml", ".permissionset-meta.xml"]
    found_reference = False

    for ext in extensions:
        for f in manifest_dir.rglob(f"*{ext}"):
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if hcga_pattern.search(content):
                found_reference = True
                break
        if found_reference:
            break

    if found_reference:
        issues.append(
            "HealthCloudGA__ namespace references found in metadata. "
            "The HealthCloudGA managed package MUST be installed in the target org before "
            "deploying this metadata. Deploy will fail with namespace resolution errors if "
            "the package is not installed. Verify with: Setup > Installed Packages."
        )

    return issues


def check_permission_set_hc_objects(manifest_dir: Path) -> list[str]:
    """Detect permission sets that grant access to Health Cloud objects.

    These permission sets require a Health Cloud Permission Set License (PSL)
    to be assigned to the user before the permission set functions at runtime.
    Emits a warning to remind deployers to assign PSLs post-deploy.
    """
    issues: list[str] = []
    ps_dir = manifest_dir / "permissionsets"
    if not ps_dir.exists():
        return issues

    hc_object_pattern = re.compile(
        r"HealthCloudGA__",
        re.IGNORECASE,
    )

    hc_ps_files: list[str] = []
    for ps_file in ps_dir.glob("*.permissionset-meta.xml"):
        try:
            content = ps_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if hc_object_pattern.search(content):
            hc_ps_files.append(ps_file.name)

    if hc_ps_files:
        issues.append(
            f"Permission set(s) reference HealthCloudGA objects: {', '.join(hc_ps_files)}. "
            "Users must have a Health Cloud Permission Set License (PSL) assigned BEFORE "
            "these permission sets function at runtime. PSL assignment is a manual post-deploy "
            "step. Verify in Setup > Users > Permission Set License Assignments."
        )

    return issues


def check_encryption_policy_reminder(manifest_dir: Path) -> list[str]:
    """Remind deployers to verify Shield Encryption is configured for clinical fields.

    If the metadata directory contains Health Cloud namespace references and no
    encryption policy metadata is found, emit a reminder about Shield Encryption.
    This is a soft warning — Shield Encryption configuration is not captured in
    standard metadata and must be verified manually.
    """
    issues: list[str] = []
    hcga_pattern = re.compile(r"HealthCloudGA__", re.IGNORECASE)

    found_hc_ref = False
    for f in manifest_dir.rglob("*.xml"):
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if hcga_pattern.search(content):
            found_hc_ref = True
            break

    if found_hc_ref:
        # Check if any encryption policy metadata is present
        encryption_dirs = [
            manifest_dir / "encryptionKeySettings",
            manifest_dir / "platformEncryptionSettings",
        ]
        has_encryption_config = any(d.exists() for d in encryption_dirs)

        if not has_encryption_config:
            issues.append(
                "Health Cloud namespace references found but no Shield Platform Encryption "
                "metadata detected in this deployment package. If this org stores PHI, "
                "ensure Shield Platform Encryption policies are configured for all clinical "
                "fields BEFORE importing PHI data. Encryption policies apply to new writes only — "
                "data imported before policy activation is not retroactively encrypted."
            )

    return issues


def check_careplan_callback_reminder(manifest_dir: Path) -> list[str]:
    """Remind deployers to register CarePlanProcessorCallback post-deploy.

    If an Apex class implementing CarePlanProcessorCallbackInterface is detected,
    emit a reminder that the class must be manually registered in Health Cloud Setup
    after deployment — this registration is not captured in deployable metadata.
    """
    issues: list[str] = []
    apex_dir = manifest_dir / "classes"
    if not apex_dir.exists():
        return issues

    callback_interface_pattern = re.compile(
        r"implements\s+[\w\.]*CarePlanProcessorCallbackInterface",
        re.IGNORECASE,
    )

    for cls_file in apex_dir.glob("*.cls"):
        try:
            content = cls_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if callback_interface_pattern.search(content):
            issues.append(
                f"Apex class {cls_file.name} implements CarePlanProcessorCallbackInterface. "
                "REQUIRED POST-DEPLOY STEP: After deploying this class, manually register it in "
                "Setup > Health Cloud Setup > Care Plan Settings > CarePlan Processor Callback. "
                "This registration is not captured in any deployable metadata artifact and must be "
                "repeated after every deployment to a new org and after every sandbox refresh."
            )

    return issues


def check_scratch_org_hc_features(manifest_dir: Path) -> list[str]:
    """Warn if scratch org definition file lacks Health Cloud features.

    If a project-scratch-def.json is found and references are made to
    Health Cloud namespace but 'HealthCloud' is not in the features list,
    emit a warning.
    """
    issues: list[str] = []

    # Look for scratch org definition file
    scratch_def_candidates = list(manifest_dir.parent.rglob("project-scratch-def.json"))
    scratch_def_candidates += list(manifest_dir.rglob("project-scratch-def.json"))

    for scratch_def in scratch_def_candidates[:1]:  # check first match only
        try:
            content = scratch_def.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        has_hc_feature = re.search(r'"HealthCloud"', content, re.IGNORECASE)
        has_hc_namespace_ref = re.search(r"HealthCloudGA__", content, re.IGNORECASE)

        # Also search the broader metadata dir for HealthCloudGA refs
        hcga_in_metadata = False
        for f in manifest_dir.rglob("*.xml"):
            try:
                if re.search(r"HealthCloudGA__", f.read_text(encoding="utf-8", errors="ignore")):
                    hcga_in_metadata = True
                    break
            except OSError:
                continue

        if hcga_in_metadata and not has_hc_feature:
            issues.append(
                f"Scratch org definition file {scratch_def.name} may be missing Health Cloud "
                "feature declarations. Metadata in this project references HealthCloudGA__ namespace "
                "objects. Ensure 'HealthCloud' is included in the 'features' array of the scratch "
                "org definition and that the HealthCloudGA package is installed post-creation. "
                "Health Cloud scratch org support is limited — prefer full sandboxes for "
                "end-to-end Care Plan and HIPAA configuration testing."
            )

    return issues


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def check_health_cloud_deployment_patterns(manifest_dir: Path) -> list[str]:
    """Run all Health Cloud deployment pattern checks.

    Returns a list of issue strings. Empty list means no issues detected.
    """
    issues: list[str] = []

    if not manifest_dir.exists():
        issues.append(f"Manifest directory not found: {manifest_dir}")
        return issues

    issues.extend(check_direct_careplan_dml(manifest_dir))
    issues.extend(check_missing_hc_namespace_reference(manifest_dir))
    issues.extend(check_permission_set_hc_objects(manifest_dir))
    issues.extend(check_encryption_policy_reminder(manifest_dir))
    issues.extend(check_careplan_callback_reminder(manifest_dir))
    issues.extend(check_scratch_org_hc_features(manifest_dir))

    return issues


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)
    issues = check_health_cloud_deployment_patterns(manifest_dir)

    if not issues:
        print("No Health Cloud deployment pattern issues detected.")
        return 0

    for issue in issues:
        print(f"WARN: {issue}", file=sys.stderr)

    print(
        f"\n{len(issues)} issue(s) found. Review the Health Cloud Deployment Patterns skill "
        "for remediation guidance.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
