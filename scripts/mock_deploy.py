#!/usr/bin/env python3
"""Validate a build's artefacts against a Salesforce org WITHOUT deploying.

Automates, as a reusable CLI, what `examples/builds/case-onboarding/reports/MOCK-DEPLOY-M1.md`
did by hand: assemble the artefacts of one or more build steps into a source-format
tree, then hand that tree to `sf project deploy start --dry-run` (`checkOnly: true`)
against a real org so platform rules no skill checker encodes (required layout
fields, business-process file-stem matching, ...) get caught before anyone deploys
for real.

Contract: `standards/build-orchestration.md` (v1, 2026-09-05) — this script IS the
"validate-only command the human may run" named in section 1, and section 5's
deploy deny-list is why it never accepts a flag that could turn `--dry-run` off.
Python Tooling Rules (`CLAUDE.md`): repo-level framework script, stdlib only.

Design rules this file obeys:

* stdlib only — no third-party imports;
* `--dry-run` is hard-coded into the `sf` invocation and there is no argument
  (no `--deploy`, no `--dry-run-only` toggle) that can remove it — the CLI
  surface simply has no path to a real deploy;
* the script only ever writes inside the directory it creates for this run
  (`--out`, default `<build_dir>/reports/mock-deploy/<UTC timestamp>/`); it
  never edits `plan.json`, never edits anything under `artefacts/`, and never
  writes into the build directory itself;
* step/milestone selection, artefact copying, manifest merging and result
  parsing are all separate, unit-testable functions — see
  `tests/test_mock_deploy.py`, which mocks `subprocess.run` so no `sf` CLI is
  ever invoked by the test suite.

Apex test execution (S2-F-06, 2026-09-12): every dry run of this script before
this fix ran with `runTestsEnabled: false` / `testLevel: null` — 13 Apex
classes in the tier2-webhook build were compiled by the validation but never
executed, and the fact was invisible because nothing in `summary.md` said so.
Confirmed against `sf project deploy start --help` (`@salesforce/cli/2.149.9`
darwin-arm64): the TEST FLAGS group is `-l, --test-level=<option>` with
options `NoTestRun|RunSpecifiedTests|RunLocalTests|RunAllTestsInOrg|RunRelevantTests`,
and `-t, --tests=<value>...` ("Apex tests to run when --test-level is
RunSpecifiedTests"); `--dry-run`'s own help text is "Validate deploy and run
Apex tests but don't save to the org" — tests genuinely execute in the org as
part of validation, nothing about that runs locally or is skipped by
`--dry-run`. This script exposes `--test-level` restricted to
`NoTestRun|RunSpecifiedTests|RunLocalTests` (default `NoTestRun`, i.e.
unchanged behaviour); `RunAllTestsInOrg` is deliberately not offered — it is
org-wide and far slower than validating one build's own artefacts, and
`RunRelevantTests` is Salesforce-computed relevance the CLI itself calls
best-effort, not deterministic like the other levels this script offers. For
`RunSpecifiedTests` with no `--tests` override, every `.cls` under the
selected steps' assembled artefacts whose class is annotated `@IsTest`/
`@isTest` is used (see `find_test_classes`).

Typical use — validate milestone M1 of a build against a scratch/dev org::

    python3 scripts/mock_deploy.py .sfskills/builds/case-onboarding/plan.json \\
        --org-alias sfskills-dev --milestone M1

API version: `sfdx-project.json` and, in `--mode manifest`, the merged
`package.xml`, use the HIGHEST `<version>` found across the selected steps'
own `package.xml` files (see `pick_api_version`) — not the first one seen —
because later steps legitimately raise the version a build was cut at
(a property the org rejects below some release, a newer Apex target). Pass
`--api-version X.Y` to override the scan outright. The chosen version and
where it came from are recorded in `summary.md` and `result.json`.

Exit codes: 0 = the org validated the deploy (`status: Succeeded`),
1 = the org rejected it (`status: Failed`), 2 = this script or the `sf` CLI
could not produce a usable result (bad plan, missing `sf`, unparseable output).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import NamedTuple
from xml.sax.saxutils import escape

METADATA_NS = "{http://soap.sforce.com/2006/04/metadata}"
DEFAULT_API_VERSION = "62.0"
DEFAULT_STATUSES = ("built", "tested", "documented")
TEST_LEVELS = ("NoTestRun", "RunSpecifiedTests", "RunLocalTests")
DEFAULT_TEST_LEVEL = "NoTestRun"


# --------------------------------------------------------------------------
# Probe mode — type → source-format path map (types seen in the four
# committed example builds only; unknown types refuse before the org is hit)
# --------------------------------------------------------------------------

class ProbeAlteration(NamedTuple):
    """What a --probe run changed on the temporary copy before assembly."""

    without: list[str]  # TYPE:Member specs, as given
    patched: list[str]  # "relpath=source" specs, as given
    copy_dir: str


class WithoutResolution(NamedTuple):
    """Resolved --without TYPE:Member: files to delete (relative path
    suffixes under any artefacts/<step>/) and (type, member) pairs to strip
    from every package.xml in the probe copy.
    """

    spec: str
    file_suffixes: list[str]
    manifest_removals: list[tuple[str, str]]


# Singular deploy-result type → (package.xml container type, directory, suffix).
# Deploy JSON reports AutoResponseRule Case.Case_Acknowledgement; source format
# ships the container AutoResponseRules file autoResponseRules/Case.…-meta.xml
# and package.xml names the object member under AutoResponseRules.
_RULE_CONTAINER: dict[str, tuple[str, str, str]] = {
    "AutoResponseRule": ("AutoResponseRules", "autoResponseRules", ".autoResponseRules-meta.xml"),
    "AssignmentRule": ("AssignmentRules", "assignmentRules", ".assignmentRules-meta.xml"),
    "EscalationRule": ("EscalationRules", "escalationRules", ".escalationRules-meta.xml"),
}

# Flat types: member is the file stem (no Object. prefix).
_FLAT_META: dict[str, tuple[str, str]] = {
    "ApexClass": ("classes", ".cls"),
    "ApexTrigger": ("triggers", ".trigger"),
    "AssignmentRules": ("assignmentRules", ".assignmentRules-meta.xml"),
    "AutoResponseRules": ("autoResponseRules", ".autoResponseRules-meta.xml"),
    "CustomPermission": ("customPermissions", ".customPermission-meta.xml"),
    "EntitlementProcess": ("entitlementProcesses", ".entitlementProcess-meta.xml"),
    "EscalationRules": ("escalationRules", ".escalationRules-meta.xml"),
    "ExternalCredential": ("externalCredentials", ".externalCredential-meta.xml"),
    "Flow": ("flows", ".flow-meta.xml"),
    "FlowTest": ("flowtests", ".flowtest-meta.xml"),
    "Group": ("groups", ".group-meta.xml"),
    "Layout": ("layouts", ".layout-meta.xml"),
    "MilestoneType": ("milestoneTypes", ".milestoneType-meta.xml"),
    "NamedCredential": ("namedCredentials", ".namedCredential-meta.xml"),
    "PermissionSet": ("permissionsets", ".permissionset-meta.xml"),
    "PermissionSetGroup": ("permissionsetgroups", ".permissionsetgroup-meta.xml"),
    "Profile": ("profiles", ".profile-meta.xml"),
    "Queue": ("queues", ".queue-meta.xml"),
    "Settings": ("settings", ".settings-meta.xml"),
    "SharingRules": ("sharingRules", ".sharingRules-meta.xml"),
    "StandardValueSet": ("standardValueSets", ".standardValueSet-meta.xml"),
}

# Object.Child types under objects/<Object>/<subdir>/<Child>.<suffix>
_OBJECT_CHILD: dict[str, tuple[str, str]] = {
    "BusinessProcess": ("businessProcesses", ".businessProcess-meta.xml"),
    "CompactLayout": ("compactLayouts", ".compactLayout-meta.xml"),
    "CustomField": ("fields", ".field-meta.xml"),
    "ListView": ("listViews", ".listView-meta.xml"),
    "RecordType": ("recordTypes", ".recordType-meta.xml"),
    "ValidationRule": ("validationRules", ".validationRule-meta.xml"),
}


def _split_type_member(spec: str) -> tuple[str, str]:
    if ":" not in spec:
        raise ValueError(
            f"invalid --without {spec!r}: expected TYPE:Member (e.g. "
            "AutoResponseRule:Case.Case_Acknowledgement)"
        )
    type_name, member = spec.split(":", 1)
    type_name, member = type_name.strip(), member.strip()
    if not type_name or not member:
        raise ValueError(
            f"invalid --without {spec!r}: expected TYPE:Member (e.g. "
            "AutoResponseRule:Case.Case_Acknowledgement)"
        )
    return type_name, member


def component_file_suffixes(type_name: str, member: str) -> list[str]:
    """Relative path suffixes (under artefacts/<step>/) for TYPE:Member.

    Covers every metadata type that appears in the four committed example
    builds. Raises ValueError when the type is unknown to this map.
    """
    if type_name in _RULE_CONTAINER:
        _container, directory, suffix = _RULE_CONTAINER[type_name]
        obj = member.split(".", 1)[0]
        return [f"{directory}/{obj}{suffix}"]

    if type_name in _FLAT_META:
        directory, suffix = _FLAT_META[type_name]
        paths = [f"{directory}/{member}{suffix}"]
        if type_name == "ApexClass":
            paths.append(f"{directory}/{member}.cls-meta.xml")
        elif type_name == "ApexTrigger":
            paths.append(f"{directory}/{member}.trigger-meta.xml")
        return paths

    if type_name in _OBJECT_CHILD:
        if "." not in member:
            raise ValueError(
                f"unmappable --without {type_name}:{member}: expected Object.Name member"
            )
        obj, name = member.split(".", 1)
        subdir, suffix = _OBJECT_CHILD[type_name]
        return [f"objects/{obj}/{subdir}/{name}{suffix}"]

    if type_name == "CustomObject":
        return [
            f"objects/{member}.object-meta.xml",
            f"objects/{member}/{member}.object-meta.xml",
        ]

    if type_name == "EmailFolder":
        return [f"email/{member}.emailFolder-meta.xml"]

    if type_name == "EmailTemplate":
        if "/" not in member:
            raise ValueError(
                f"unmappable --without EmailTemplate:{member}: expected Folder/Name"
            )
        folder, name = member.split("/", 1)
        return [
            f"email/{folder}/{name}.email",
            f"email/{folder}/{name}.email-meta.xml",
        ]

    if type_name == "Report":
        if "/" in member:
            folder, name = member.split("/", 1)
            return [f"reports/{folder}/{name}.report-meta.xml"]
        return [f"reports/{member}-meta.xml"]

    raise ValueError(
        f"unmappable metadata type {type_name!r}: --without cannot map this type "
        "(supported: types that appear in the four committed example builds)"
    )


def resolve_without_spec(spec: str) -> WithoutResolution:
    """Parse TYPE:Member into file suffixes + package.xml removals."""
    type_name, member = _split_type_member(spec)
    suffixes = component_file_suffixes(type_name, member)
    removals: list[tuple[str, str]] = [(type_name, member)]
    if type_name in _RULE_CONTAINER:
        container, _, _ = _RULE_CONTAINER[type_name]
        obj = member.split(".", 1)[0]
        removals.append((container, obj))
        if member != obj:
            # Also drop an exact Object.Rule member under the container type if present.
            removals.append((container, member))
    return WithoutResolution(spec=spec, file_suffixes=suffixes, manifest_removals=removals)


def package_xml_from_types(types: dict[str, set[str]], version: str) -> str:
    """Serialize a {type: {members}} map to a package.xml document."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<Package xmlns="http://soap.sforce.com/2006/04/metadata">',
    ]
    for name in sorted(types):
        if not types[name]:
            continue
        lines.append("    <types>")
        for member in sorted(types[name]):
            lines.append(f"        <members>{escape(member)}</members>")
        lines.append(f"        <name>{escape(name)}</name>")
        lines.append("    </types>")
    lines.append(f"    <version>{escape(version)}</version>")
    lines.append("</Package>")
    return "\n".join(lines) + "\n"


def scrub_package_xml(path: Path, removals: set[tuple[str, str]]) -> bool:
    """Drop matching <members> from a package.xml; drop empty <types> blocks.

    Returns True when the file was rewritten. Malformed/missing files are left
    alone (returns False).
    """
    if not path.is_file() or not removals:
        return False
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return False
    types = _types_from_root(root)
    version_el = root.find(f"{METADATA_NS}version")
    version = (
        version_el.text.strip()
        if version_el is not None and version_el.text and version_el.text.strip()
        else DEFAULT_API_VERSION
    )
    changed = False
    for type_name, member in removals:
        bucket = types.get(type_name)
        if bucket and member in bucket:
            bucket.discard(member)
            changed = True
            if not bucket:
                del types[type_name]
    if not changed:
        return False
    path.write_text(package_xml_from_types(types, version), encoding="utf-8")
    return True


def delete_component_files(copy_dir: Path, file_suffixes: list[str]) -> list[Path]:
    """Delete every file under copy_dir whose path ends with one of the
    source-format suffixes (matched on the relative posix path).
    """
    deleted: list[Path] = []
    suffix_set = {s.replace("\\", "/") for s in file_suffixes}
    for path in sorted(copy_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(copy_dir).as_posix()
        if any(rel == s or rel.endswith("/" + s) for s in suffix_set):
            path.unlink()
            deleted.append(path)
    return deleted


def iter_package_xml_files(copy_dir: Path) -> list[Path]:
    """Every package.xml under the probe copy — step manifests (`package.xml`)
    and milestone reports (`reports/MILESTONE-*-package.xml`), plus any other
    path whose name ends in `package.xml`.
    """
    return sorted(
        p for p in copy_dir.rglob("*package.xml")
        if p.is_file() and p.name.endswith("package.xml")
    )


def apply_probe_without(copy_dir: Path, specs: list[str]) -> list[WithoutResolution]:
    """Resolve and apply every --without on the probe copy (files + manifests)."""
    resolved = [resolve_without_spec(s) for s in specs]
    removals: set[tuple[str, str]] = set()
    for item in resolved:
        removals.update(item.manifest_removals)
        delete_component_files(copy_dir, item.file_suffixes)
    for pkg in iter_package_xml_files(copy_dir):
        scrub_package_xml(pkg, removals)
    return resolved


def apply_probe_patches(copy_dir: Path, specs: list[str]) -> list[tuple[str, str]]:
    """Apply every --patch relpath=localfile on the probe copy.

    Returns the list of (relpath, source) pairs applied. Raises ValueError on
    a bad spec or a missing source/destination.
    """
    applied: list[tuple[str, str]] = []
    for spec in specs:
        if "=" not in spec:
            raise ValueError(
                f"invalid --patch {spec!r}: expected <relative artefact path>=<local file>"
            )
        rel, src = spec.split("=", 1)
        rel, src = rel.strip(), src.strip()
        if not rel or not src:
            raise ValueError(
                f"invalid --patch {spec!r}: expected <relative artefact path>=<local file>"
            )
        source = Path(src).expanduser().resolve()
        if not source.is_file():
            raise ValueError(f"--patch source not found: {source}")
        dest = (copy_dir / rel).resolve()
        try:
            dest.relative_to(copy_dir.resolve())
        except ValueError as exc:
            raise ValueError(f"--patch path escapes probe copy: {rel}") from exc
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        applied.append((rel, str(source)))
    return applied


def _probe_copy_ignore(source_root: Path):
    """Ignore envelopes/ and reports/mock-deploy/ when cloning a build for --probe."""

    source_root = source_root.resolve()

    def _ignore(directory: str, names: list[str]) -> set[str]:
        ignored: set[str] = set()
        dir_path = Path(directory).resolve()
        name_set = set(names)
        if dir_path == source_root:
            if "envelopes" in name_set:
                ignored.add("envelopes")
            if ".git" in name_set:
                ignored.add(".git")
        if dir_path.name == "reports" and "mock-deploy" in name_set:
            ignored.add("mock-deploy")
        return ignored

    return _ignore


def create_probe_copy(build_dir: Path, probe_dir: Path | None) -> Path:
    """Copy the build into a temporary (or chosen) directory for --probe."""
    build_dir = build_dir.resolve()
    if probe_dir is None:
        dest = Path(tempfile.mkdtemp(prefix="sfskills-mock-deploy-probe-"))
    else:
        dest = probe_dir.resolve()
        if dest.exists():
            if any(dest.iterdir()):
                raise ValueError(
                    f"--probe-dir is not empty: {dest} (pass an empty or new directory)"
                )
        else:
            dest.mkdir(parents=True, exist_ok=True)
    # mkdtemp / mkdir leave an empty dest; copytree needs dirs_exist_ok.
    shutil.copytree(
        build_dir, dest, dirs_exist_ok=True, ignore=_probe_copy_ignore(build_dir)
    )
    return dest


# --------------------------------------------------------------------------
# Plan / step selection
# --------------------------------------------------------------------------

def load_plan(plan_path: Path) -> dict:
    return json.loads(plan_path.read_text(encoding="utf-8"))


def select_steps(plan: dict, milestone_ids: list[str], step_ids: list[str]) -> list[dict]:
    """Pick the steps to validate, in the order they appear in plan['steps'].

    Explicit `--milestone`/`--step` selection is a union of both filters and
    ignores step status (the human named exactly what they want validated).
    With neither given, the default is every step whose status is one of
    DEFAULT_STATUSES — the states a step reaches once its own artefacts exist.
    """
    milestone_set = set(milestone_ids or [])
    step_set = set(step_ids or [])
    steps = plan.get("steps", [])
    if milestone_set or step_set:
        return [
            s for s in steps
            if s.get("milestone") in milestone_set or s.get("id") in step_set
        ]
    return [s for s in steps if s.get("status") in DEFAULT_STATUSES]


# --------------------------------------------------------------------------
# Artefact assembly (mode: source)
# --------------------------------------------------------------------------

class CopyResult(NamedTuple):
    """Result of `copy_artefacts`.

    * copied — paths copied, relative to dest_root, in the order copied.
    * skipped — count of files under the selected steps' artefact directories
      that were deliberately excluded (package.xml, `*.md` build notes,
      dotfiles). Directories are never counted either way.
    """

    copied: list[Path]
    skipped: int


def copy_artefacts(
    build_dir: Path, artefacts_root: str, step_ids: list[str], dest_root: Path
) -> CopyResult:
    """Copy EVERY file under artefacts/<step>/ into dest_root, preserving each
    file's sub-path (objects/Case/fields/..., layouts/..., email/case_intake/...,
    lwc/foo/..., etc) and the directory structure around it — EXCEPT:

    * `package.xml` — merged separately (see `merge_package_xml` / --mode manifest);
    * `*.md` files — build notes (deploy-order.md, decision notes, runbooks),
      never deployable metadata;
    * dotfiles — editor/OS artefacts, never Salesforce source.

    A source-format component is frequently more than one file next to its
    `-meta.xml` sidecar: an EmailTemplate's `.email` body, an Apex class's
    `.cls`, a static resource's `.resource`, an LWC/Aura bundle's `.js`/
    `.html`/`.css`. Copying only `*.xml` (the previous behaviour) silently
    dropped every one of those bodies, and `sf project deploy start` then
    fails with `ExpectedSourceFilesError: ... Expected source files for
    type '<Type>'` — a defect found live against
    `.sfskills/builds/case-onboarding` (an EmailTemplate's `.email` body never
    reached the assembled tree). Copying everything except the three
    exclusions above fixes every source-format type at once, not just email.

    Returns a `CopyResult` — the paths copied (relative to dest_root) and a
    count of files skipped by the exclusion rules — for callers/tests that
    want to assert on the tree shape or report on it (see `render_summary`).
    """
    copied: list[Path] = []
    skipped = 0
    for step_id in step_ids:
        step_dir = build_dir / artefacts_root / step_id
        if not step_dir.is_dir():
            continue
        for src in sorted(step_dir.rglob("*")):
            if not src.is_file():
                continue
            if src.name == "package.xml" or src.suffix.lower() == ".md" or src.name.startswith("."):
                skipped += 1
                continue
            rel = src.relative_to(step_dir)
            dest = dest_root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            copied.append(rel)
    return CopyResult(copied=copied, skipped=skipped)


TEST_CLASS_RE = re.compile(r"@isTest\b[^;{]*?\bclass\s+(\w+)", re.IGNORECASE | re.DOTALL)

# Modifiers/annotation-args that can legally sit between an `@isTest`
# occurrence and the token that tells us whether it annotates the *class*
# or a *method* inside it. Deliberately the same style of best-effort regex
# scan as TEST_CLASS_RE — not a full Apex parser.
_APEX_MODIFIER_RE = (
    r"(?:private|public|protected|global|static|virtual|abstract|override|"
    r"testMethod|with\s+sharing|without\s+sharing|inherited\s+sharing)"
)
_ISTEST_HEAD_RE = re.compile(
    r"@isTest\b\s*(?:\([^)]*\))?\s*(?:" + _APEX_MODIFIER_RE + r"\s+)*(\w+)",
    re.IGNORECASE | re.DOTALL,
)
TEST_METHOD_KEYWORD_RE = re.compile(r"\btestMethod\b", re.IGNORECASE)


def _has_test_method(text: str) -> bool:
    """True when `text` (one `.cls` file's source) contains at least one
    `@IsTest`/`testMethod` *method*, not only the class-level `@IsTest`
    annotation that marks the whole class as test-only (S2-F-19).

    Two independent signals, either is sufficient:

    * the legacy `static testMethod void foo() { ... }` modifier, anywhere
      in the file (`TEST_METHOD_KEYWORD_RE`);
    * an `@isTest` occurrence whose next significant token — after any
      `(...)` annotation args and any Apex modifiers — is not `class`.
      `_ISTEST_HEAD_RE` walks the same modifier list Apex allows on a class
      or method declaration; when what follows is `class`, that occurrence
      is the class-level annotation, not a method.

    A class-level `@isTest` with no test method inside it (`TestDataFactory`,
    `MockHttpResponseGenerator` — idiomatic shared test utilities, excluded
    from Apex code-size limits but declaring no tests of their own) returns
    False, so `find_test_classes` no longer offers it to `--tests`.
    """
    if TEST_METHOD_KEYWORD_RE.search(text):
        return True
    for match in _ISTEST_HEAD_RE.finditer(text):
        if match.group(1).lower() != "class":
            return True
    return False


def find_test_classes(root: Path) -> list[str]:
    """Every Apex class under `root` whose *class* carries an `@IsTest`/
    `@isTest` annotation AND declares at least one test method — the
    automatic `--tests` list for `--test-level RunSpecifiedTests` (S2-F-06)
    when no `--tests` override is given.

    `TEST_CLASS_RE` matches `@isTest`, then only visibility/sharing modifiers
    (no `;` or `{`), then `class <Name>`. A `@isTest` annotating a single test
    *method* — `@isTest static void itWorks() { ... }` — does not match: the
    method's parameter list and opening `{` are reached before any `class`
    keyword, and the non-greedy `[^;{]*?` cannot cross that `{`. A class with
    no `@isTest` anywhere (an ordinary, non-test `.cls`) never matches at
    all. `_has_test_method` (S2-F-19) then requires the file to also declare
    at least one test *method* before the class name is offered to
    `--tests` — a class-level `@IsTest` utility with no test methods of its
    own (`TestDataFactory`, `MockHttpResponseGenerator`) no longer produces
    the org's "no test methods" noise.

    `root` must be the already-assembled `force-app/main/default` tree —
    i.e. `copy_artefacts`'s *output*, the exact directory the `sf` command
    is later pointed at (`--source-dir force-app` / the manifest's implicit
    package directory) — not a selected step's raw `artefacts/<step>/`
    directory. Scanning anything else can miss test classes that reach a
    manifest-mode run only through another step's artefacts merged into the
    same package.xml (S2-F-20: `--milestone M5`'s Apex lived in step
    `M4-S05`, reachable only through the build-level manifest). Returns
    names sorted alphabetically and de-duplicated; an empty/missing `root`
    or a `.cls` file that fails to decode as UTF-8 contributes nothing
    rather than raising.
    """
    names: set[str] = set()
    if not root.is_dir():
        return []
    for path in sorted(root.rglob("*.cls")):
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if not _has_test_method(text):
            continue
        for match in TEST_CLASS_RE.finditer(text):
            names.add(match.group(1))
    return sorted(names)


class ApiVersionResolution(NamedTuple):
    """Result of `pick_api_version`.

    * version — the API version text to use, exactly as found in whichever
      step's package.xml declared it (not the parsed float), e.g. "63.0".
    * source — human-readable provenance, written into summary.md's
      `- api version:` line and result.json's `api_version` key: either
      "highest of: M1-S01=62.0, M1-S02=63.0, ..." (one entry per selected
      step that had a usable <version>, in step order) or, when none did,
      "fallback (no step declared a <version>; default X.Y)".
    """

    version: str
    source: str


def pick_api_version(
    build_dir: Path, artefacts_root: str, step_ids: list[str], fallback: str = DEFAULT_API_VERSION
) -> ApiVersionResolution:
    """The HIGHEST <version> found across the selected steps' package.xml
    files — not the first in step order.

    A build assembled from steps authored at different times legitimately
    mixes package.xml versions: an earlier milestone's manifest can still
    say 62.0 while a later step needs 64.0+ for a property the org rejects
    below that (or a later Apex step targets 67.0). Picking the first or the
    lowest version found would silently downgrade the merged deploy below
    what a later step requires and reproduce exactly that failure. Falls
    back to `fallback` (default 62.0) when none of the selected steps' has a
    usable <version> element.

    Versions are compared numerically (parsed as float) so "9.0" would beat
    "62.0" if that were ever a real Salesforce API version; the returned
    text is the original string from the winning step's package.xml, not a
    reformatted float.
    """
    found: list[tuple[str, str]] = []  # (step_id, version_text), in step order
    for step_id in step_ids:
        pkg = build_dir / artefacts_root / step_id / "package.xml"
        if not pkg.is_file():
            continue
        try:
            root = ET.parse(pkg).getroot()
        except ET.ParseError:
            continue
        version_el = root.find(f"{METADATA_NS}version")
        if version_el is not None and version_el.text and version_el.text.strip():
            found.append((step_id, version_el.text.strip()))

    if not found:
        return ApiVersionResolution(
            version=fallback,
            source=f"fallback (no step declared a <version>; default {fallback})",
        )

    def _numeric(pair: tuple[str, str]) -> float:
        try:
            return float(pair[1])
        except ValueError:
            return float("-inf")

    _, best_version = max(found, key=_numeric)
    source = "highest of: " + ", ".join(f"{sid}={ver}" for sid, ver in found)
    return ApiVersionResolution(version=best_version, source=source)


def write_sfdx_project(out_dir: Path, api_version: str) -> Path:
    payload = {
        "packageDirectories": [{"path": "force-app", "default": True}],
        "namespace": "",
        "sourceApiVersion": api_version,
    }
    path = out_dir / "sfdx-project.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    # The standard SFDX .forceignore. Without it the org compiles an LWC bundle's
    # __tests__/*.test.js as a module and rejects every `getRecord.emit(...)` with
    # LWC1503 — northwind-sales M3 run 3 (2026-09-19) failed a correct bundle on
    # thirteen such lines. Same list `sf project generate` writes.
    (out_dir / ".forceignore").write_text(
        "package.xml\n**/jsconfig.json\n**/.eslintrc.json\n**/__tests__/**\n", encoding="utf-8")
    return path


# --------------------------------------------------------------------------
# Manifest assembly (mode: manifest)
# --------------------------------------------------------------------------

def _types_from_root(root: ET.Element) -> dict[str, set[str]]:
    """Extract a {type name: {member, ...}} map from a parsed <Package> root."""
    types: dict[str, set[str]] = {}
    for t in root.findall(f"{METADATA_NS}types"):
        name_el = t.find(f"{METADATA_NS}name")
        if name_el is None or not (name_el.text and name_el.text.strip()):
            continue
        name = name_el.text.strip()
        bucket = types.setdefault(name, set())
        for m in t.findall(f"{METADATA_NS}members"):
            if m.text and m.text.strip():
                bucket.add(m.text.strip())
    return types


def _types_from_text(xml_text: str) -> dict[str, set[str]]:
    """Same as `_types_from_root` but from an in-memory package.xml string.
    An unparseable document contributes no types rather than raising, matching
    `merge_package_xml`'s tolerance of malformed/missing input files.
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return {}
    return _types_from_root(root)


def merge_package_xml(paths: list[Path], version: str) -> str:
    """Merge one or more package.xml files by <name> type, union-ing and
    sorting <members>, and sort the <types> blocks themselves by type name —
    matching the shape of the hand-built
    examples/builds/case-onboarding/reports/MILESTONE-M1-package.xml.
    """
    types: dict[str, set[str]] = {}
    for p in paths:
        p = Path(p)
        if not p.is_file():
            continue
        try:
            root = ET.parse(p).getroot()
        except ET.ParseError:
            continue
        for name, members in _types_from_root(root).items():
            types.setdefault(name, set()).update(members)

    return package_xml_from_types(types, version)


def diff_manifest_types(
    report_types: dict[str, set[str]], merged_types: dict[str, set[str]]
) -> list[tuple[str, str, str]]:
    """Compare two {type: {member, ...}} maps produced by `_types_from_*`.

    Returns a sorted list of (type, member, side) triples for every member
    present on only one side — side is "report-only" or "steps-only". An
    empty list means the two manifests are equivalent (same types, same
    members per type; ordering/whitespace in the source files is irrelevant).
    """
    diffs: list[tuple[str, str, str]] = []
    for type_name in sorted(set(report_types) | set(merged_types)):
        report_members = report_types.get(type_name, set())
        merged_members = merged_types.get(type_name, set())
        for member in sorted(report_members - merged_members):
            diffs.append((type_name, member, "report-only"))
        for member in sorted(merged_members - report_members):
            diffs.append((type_name, member, "steps-only"))
    return diffs


MAX_DRIFT_ITEMS_SHOWN = 10


class ManifestResolution(NamedTuple):
    """Result of `resolve_manifest_text`.

    * source — description of what `xml_text` came from ("merged:<ids>" or
      the milestone report path when --prefer-report-manifest was honoured).
    * xml_text — the manifest text to write to package.xml.
    * warning — a one-line WARN string to print to stderr, or None when there
      was nothing to warn about (no report to compare, or no drift found).
    * drift_note — markdown body for summary.md's "Manifest drift" heading,
      or "" when there is nothing to say (no milestone report was found).
    """

    source: str
    xml_text: str
    warning: str | None = None
    drift_note: str = ""


def resolve_manifest_text(
    build_dir: Path,
    artefacts_root: str,
    milestone_ids: list[str],
    step_ids_arg: list[str],
    selected_ids: list[str],
    version: str,
    prefer_report_manifest: bool = False,
) -> ManifestResolution:
    """Manifest mode's source of truth is always the type-merged manifest
    freshly built from the selected steps' package.xml files (F-18: the
    milestone verifier's report can go stale the moment a step's own
    package.xml is rebuilt after the report was written).

    When exactly one milestone was named (and no --step mixed in) and the
    milestone verifier's own reports/MILESTONE-<id>-package.xml exists on
    disk, that file is additionally compared against the fresh merge:

    * identical (same types, same members per type) — the merge is used;
      summary.md notes the match under "Manifest drift" and nothing is
      printed to stderr.
    * different — a WARN is printed naming up to MAX_DRIFT_ITEMS_SHOWN of the
      differing members, summary.md records the full drift, and the steps'
      merge is used UNLESS `prefer_report_manifest` is set, in which case the
      report's own text is used instead (the WARN is still printed either
      way — this flag reproduces the old, stale-prone behaviour on purpose).

    When no milestone report exists on disk, the merge is used silently: no
    warning, no drift note (there's nothing to compare against).
    """
    package_paths = [build_dir / artefacts_root / sid / "package.xml" for sid in selected_ids]
    merged_xml = merge_package_xml(package_paths, version)
    merged_source = "merged:" + ",".join(selected_ids)

    single_milestone = bool(milestone_ids) and len(milestone_ids) == 1 and not step_ids_arg
    if not single_milestone:
        return ManifestResolution(source=merged_source, xml_text=merged_xml)

    report_path = build_dir / "reports" / f"MILESTONE-{milestone_ids[0]}-package.xml"
    if not report_path.is_file():
        return ManifestResolution(source=merged_source, xml_text=merged_xml)

    report_xml = report_path.read_text(encoding="utf-8")
    report_rel = report_path.relative_to(build_dir)

    diff = diff_manifest_types(_types_from_text(report_xml), _types_from_text(merged_xml))
    if not diff:
        drift_note = f"None — the steps' merge matches `{report_rel}`.\n"
        return ManifestResolution(
            source=merged_source, xml_text=merged_xml, warning=None, drift_note=drift_note
        )

    milestone_id = milestone_ids[0]
    shown = diff[:MAX_DRIFT_ITEMS_SHOWN]
    shown_text = ", ".join(f"{t}:{m} ({side})" for t, m, side in shown)
    if len(diff) > MAX_DRIFT_ITEMS_SHOWN:
        shown_text += f", … ({len(diff) - MAX_DRIFT_ITEMS_SHOWN} more)"

    if prefer_report_manifest:
        action = "using the milestone report (--prefer-report-manifest)"
        used_source = str(report_path)
        used_xml = report_xml
    else:
        action = "using the steps' merge"
        used_source = merged_source
        used_xml = merged_xml

    warning = (
        f"WARN: milestone manifest {report_rel} differs from the steps' "
        f"package.xml files — {len(diff)} member(s) differ: {shown_text}; "
        f"{action}. Re-run milestone-verifier {milestone_id} to refresh the report."
    )

    drift_lines = "\n".join(f"- {t}:{m} ({side})" for t, m, side in shown)
    shown_suffix = f" (showing first {MAX_DRIFT_ITEMS_SHOWN})" if len(diff) > MAX_DRIFT_ITEMS_SHOWN else ""
    used_label = "milestone report (--prefer-report-manifest)" if prefer_report_manifest else "steps' merge"
    drift_note = (
        f"`{report_rel}` differs from the steps' merge — {len(diff)} member(s) differ"
        f"{shown_suffix}:\n\n"
        f"{drift_lines}\n\n"
        f"Used: {used_label}.\n"
    )

    return ManifestResolution(
        source=used_source, xml_text=used_xml, warning=warning, drift_note=drift_note
    )


def _assembled_file_stems(source_root: Path) -> set[str]:
    """Every candidate "name" a file under `source_root` could correspond to
    in a package.xml `<members>` entry — used by `find_missing_manifest_members`.

    Not type-aware (this script doesn't carry a metadata-type-to-path map),
    so each file contributes two stems: `Path.stem` (strips one extension,
    e.g. `Foo.cls-meta.xml` -> `Foo.cls-meta`) and, after stripping a
    trailing `-meta.xml` and then one more extension, the "component name"
    shape most member text actually takes (`Foo.cls-meta.xml` -> `Foo`;
    `Case-Case Support Layout.layout-meta.xml` -> `Case-Case Support
    Layout`). Deliberately permissive: a false "present" costs nothing (the
    org dry run is the real check) while a false "missing" would print a
    misleading WARN.
    """
    stems: set[str] = set()
    for f in source_root.rglob("*"):
        if not f.is_file():
            continue
        stems.add(f.stem)
        name = f.name
        if name.endswith("-meta.xml"):
            name = name[: -len("-meta.xml")]
        stems.add(Path(name).stem if "." in name else name)
    return stems


def find_missing_manifest_members(manifest_xml: str, source_root: Path) -> list[tuple[str, str]]:
    """Members named in `manifest_xml` with no matching file anywhere under
    the assembled `source_root` (S2-F-22: `--milestone M5` alone selects
    only M5's own steps, but a build-level manifest step can list members —
    Apex classes, in the observed case — that physically live in an
    unselected step and were never copied into the assembled tree; the org
    then reports the deploy missing files with no earlier warning).

    Matching is by filename stem, not metadata type (see
    `_assembled_file_stems`): a member's last `.`- or `/`-separated segment
    must appear as some file's stem under `source_root`. Returns
    `(type, member)` pairs sorted by type then member; empty when every
    member has a matching file, or trivially every member when `source_root`
    does not exist at all (nothing was assembled to check against).
    """
    types = _types_from_text(manifest_xml)
    all_members = sorted((t, m) for t, members in types.items() for m in sorted(members))
    if not source_root.is_dir():
        return all_members

    stems = _assembled_file_stems(source_root)
    missing: list[tuple[str, str]] = []
    for type_name, member in all_members:
        last_segment = member.split(".")[-1].split("/")[-1]
        if last_segment in stems or member in stems:
            continue
        missing.append((type_name, member))
    return missing


# --------------------------------------------------------------------------
# sf CLI invocation + result handling
# --------------------------------------------------------------------------

def build_sf_command(
    mode: str,
    org_alias: str,
    manifest_name: str = "package.xml",
    test_level: str = DEFAULT_TEST_LEVEL,
    tests: list[str] | None = None,
) -> list[str]:
    """The `sf` command line. --dry-run is always present — there is no
    parameter anywhere in this script that can remove it.

    Test flags confirmed via `sf project deploy start --help`
    (`@salesforce/cli/2.149.9`): `-l, --test-level=<option>` and
    `-t, --tests=<value>...` (one `--tests <name>` pair per class; `sf`
    accepts the flag repeated). `test_level="NoTestRun"` (the default) adds
    neither flag, so the command is byte-for-byte what it was before this
    parameter existed — `tests` is silently ignored in that case too, exactly
    as `sf` itself ignores `--tests` outside `RunSpecifiedTests`.
    """
    cmd = ["sf", "project", "deploy", "start"]
    if mode == "manifest":
        cmd += ["--manifest", manifest_name]
    else:
        cmd += ["--source-dir", "force-app"]
    cmd += ["--dry-run", "--target-org", org_alias, "--wait", "10", "--json"]
    if test_level != "NoTestRun":
        cmd += ["--test-level", test_level]
        if test_level == "RunSpecifiedTests":
            for name in tests or []:
                cmd += ["--tests", name]
    return cmd


class TestSummary(NamedTuple):
    """Apex test results extracted from the `sf` CLI's deploy JSON (S2-F-06).

    Populated for every `--test-level`, including `NoTestRun` — where `run`,
    `passed` and `failed` are legitimately 0 and `coverage_pct` is `None`.
    Rendering that all-zero case explicitly (instead of omitting the line)
    is the point: every dry run before this fix silently carried
    `runTestsEnabled: false` and nothing in `summary.md` said so.

    * requested_tests — the explicit `--tests` override or the auto-scanned
      `@IsTest` class list, only when `level == "RunSpecifiedTests"`; `None`
      for `RunLocalTests`/`NoTestRun`.
    * coverage_pct — aggregate percentage across every entry in
      `result.details.runTestResult.codeCoverage`:
      `100 * (sum(numLocations) - sum(numLocationsNotCovered)) / sum(numLocations)`,
      rounded to 1 decimal; `None` when there are no coverage entries at all
      (`NoTestRun`, or a CLI/org response that omits the field).
    * failures — `(class, method, message, stack_first_line)` tuples from
      `result.details.runTestResult.failures`, sorted by `(class, method)`.
    * coverage_warnings — `(name, message)` tuples from
      `result.details.runTestResult.codeCoverageWarnings` (S2-F-21): the
      platform enforces its 75% floor PER CLASS in `RunSpecifiedTests`/
      `RunLocalTests`, not only on the aggregate `coverage_pct` above — a
      run can show a healthy aggregate and still fail because one class
      individually falls short, and that reason previously lived only in
      the raw `result.json`, never in `summary.md`.
    * per_class — `(name, type, locations, not_covered, pct)` per
      `codeCoverage` entry, sorted by `pct` ascending then name; `pct` is
      `None` when `numLocations` is 0 (those rows sort last). Surfaced in
      `summary.md` and `result.json` so an operator can see which class is
      under the 75% floor without reading the raw CLI payload.
    """

    level: str
    requested_tests: list[str] | None
    run: int
    passed: int
    failed: int
    coverage_pct: float | None
    failures: list[tuple[str, str, str, str]]
    coverage_warnings: list[tuple[str, str]]
    per_class: list[tuple[str, str, int, int, float | None]]


def extract_test_summary(
    parsed: dict | None, level: str, requested_tests: list[str] | None
) -> TestSummary:
    """Read `numberTestsCompleted`, `numberTestErrors` and the code-coverage
    figures out of `sf project deploy start --json`'s `result` object.
    Tolerant of every shape seen so far — a `NoTestRun` response with no
    `details.runTestResult` at all, and one with an all-zeros
    `runTestResult` — both parse to the same all-zero `TestSummary` rather
    than raising. Also reads `codeCoverageWarnings` (S2-F-21) — field names
    `name`/`id` and `message`/`problem`, matching the tolerant extraction
    `pipelines/product/deploy_result.py`'s `_coverage_row` already uses for
    the same CLI shape.
    """
    result = parsed.get("result") if isinstance(parsed, dict) else None
    result = result if isinstance(result, dict) else {}

    run = result.get("numberTestsCompleted") or 0
    failed = result.get("numberTestErrors") or 0
    passed = max(run - failed, 0)

    details = result.get("details")
    details = details if isinstance(details, dict) else {}
    run_test_result = details.get("runTestResult")
    run_test_result = run_test_result if isinstance(run_test_result, dict) else {}

    coverage_pct: float | None = None
    code_coverage = run_test_result.get("codeCoverage") or []
    total_locations = sum(int(c.get("numLocations") or 0) for c in code_coverage)
    if total_locations > 0:
        not_covered = sum(int(c.get("numLocationsNotCovered") or 0) for c in code_coverage)
        coverage_pct = round(100.0 * (total_locations - not_covered) / total_locations, 1)

    per_class: list[tuple[str, str, int, int, float | None]] = []
    for c in code_coverage:
        name = str(c.get("name") or "")
        typ = str(c.get("type") or "")
        locations = int(c.get("numLocations") or 0)
        not_covered_n = int(c.get("numLocationsNotCovered") or 0)
        pct = (
            None
            if locations == 0
            else round(100.0 * (locations - not_covered_n) / locations, 1)
        )
        per_class.append((name, typ, locations, not_covered_n, pct))
    per_class.sort(
        key=lambda t: (t[4] is None, t[4] if t[4] is not None else 0.0, t[0])
    )

    failures: list[tuple[str, str, str, str]] = []
    for f in run_test_result.get("failures") or []:
        stack = f.get("stackTrace") or ""
        stack_first = stack.splitlines()[0] if stack else ""
        failures.append(
            (f.get("name", ""), f.get("methodName", ""), f.get("message", ""), stack_first)
        )
    failures.sort(key=lambda t: (t[0], t[1]))

    coverage_warnings: list[tuple[str, str]] = []
    for w in run_test_result.get("codeCoverageWarnings") or []:
        name = str(w.get("name") or w.get("id") or "")
        message = str(w.get("message") or w.get("problem") or "")
        coverage_warnings.append((name, message))

    return TestSummary(
        level=level,
        requested_tests=requested_tests,
        run=run,
        passed=passed,
        failed=failed,
        coverage_pct=coverage_pct,
        failures=failures,
        coverage_warnings=coverage_warnings,
        per_class=per_class,
    )


def strip_json_prefix(text: str) -> str:
    """The `sf` CLI sometimes prints an update-available warning (or other
    plain-text noise) before its --json payload. Return the text starting at
    the first line that looks like the start of a JSON object.
    """
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.lstrip().startswith("{"):
            return "\n".join(lines[i:])
    raise ValueError("no JSON object found in CLI output")


def exit_code_for_status(status: str | None) -> int:
    if status == "Succeeded":
        return 0
    if status == "Failed":
        return 1
    return 2


def render_summary(
    parsed: dict | None,
    mode: str,
    org_alias: str,
    manifest_resolution: ManifestResolution | None = None,
    plan_only: bool = False,
    copy_result: CopyResult | None = None,
    api_version: str | None = None,
    api_version_source: str | None = None,
    tests: TestSummary | None = None,
    planned_test_level: str | None = None,
    planned_tests: list[str] | None = None,
    probe: ProbeAlteration | None = None,
) -> str:
    lines = ["# Mock deploy result", ""]
    if probe is not None:
        lines.append(
            f"- PROBE: {len(probe.without)} component(s) removed, {len(probe.patched)} "
            "file(s) patched — this run validated an altered copy; it is not evidence "
            "for a gate"
        )
        for spec in probe.without:
            lines.append(f"- removed: `{spec}`")
        for spec in probe.patched:
            lines.append(f"- patched: `{spec}`")
        lines.append("")
    lines += [f"- org: `{org_alias}`", f"- mode: `{mode}`"]

    if api_version is not None:
        lines.append(f"- api version: `{api_version}` ({api_version_source})")

    if copy_result is not None:
        lines.append(
            f"- files: {len(copy_result.copied)} file(s) copied, {copy_result.skipped} "
            "skipped (package.xml/notes)"
        )

    if plan_only:
        lines.append("- status: **not run (--plan-only)**")
        if planned_test_level is not None:
            if planned_test_level == "NoTestRun":
                lines.append(f"- tests: level {planned_test_level} (not run — --plan-only)")
            else:
                names = ", ".join(planned_tests) if planned_tests else "(none)"
                count = len(planned_tests) if planned_tests else 0
                lines.append(
                    f"- tests: level {planned_test_level} · planned {count} test(s): "
                    f"{names} (not run — --plan-only)"
                )
    else:
        result = parsed.get("result") if isinstance(parsed, dict) else None
        result = result if isinstance(result, dict) else {}

        status = result.get("status", "Unknown")
        check_only = result.get("checkOnly", True)
        details = result.get("details") if isinstance(result.get("details"), dict) else {}
        successes = details.get("componentSuccesses") or []
        failures = details.get("componentFailures") or []
        total = result.get("numberComponentsTotal", len(successes) + len(failures))
        errors = result.get("numberComponentErrors", len(failures))

        rows: list[tuple[str, str, str]] = []
        for c in successes:
            rows.append((c.get("componentType", ""), c.get("fullName", ""), "ok"))
        for c in failures:
            problem = c.get("problem", "unknown error")
            rows.append((c.get("componentType", ""), c.get("fullName", ""), f"FAIL — {problem}"))
        rows.sort(key=lambda r: (r[0], r[1]))

        lines += [
            f"- status: **{status}**",
            f"- checkOnly: `{check_only}`",
            f"- components: {total} total, {len(successes)} ok, {errors} error(s)",
            "",
            "| Type | Component | Result |",
            "|---|---|---|",
        ]
        for component_type, name, outcome in rows:
            lines.append(f"| {component_type} | {name} | {outcome} |")

        if tests is not None:
            coverage_str = f"{tests.coverage_pct}%" if tests.coverage_pct is not None else "n/a"
            lines.append("")
            lines.append(
                f"- tests: level {tests.level} · run {tests.run} · passed {tests.passed} "
                f"· failed {tests.failed} · coverage {coverage_str}"
            )
            if tests.failures:
                lines += [
                    "",
                    "## Test failures",
                    "",
                    "| Class | Method | Message | Stack (first line) |",
                    "|---|---|---|---|",
                ]
                for cls, method, message, stack_first in tests.failures:
                    lines.append(f"| {cls} | {method} | {message} | {stack_first} |")

            if tests.coverage_warnings:
                lines += ["", "## Coverage warnings", ""]
                for name, message in tests.coverage_warnings:
                    label = f"{name} — {message}" if name else message
                    lines.append(f"- {label}")

            if tests.per_class:
                lines += [
                    "",
                    "## Coverage by class",
                    "",
                    "| Class | Type | Lines | Uncovered | Coverage | |",
                    "|---|---|---|---|---|---|",
                ]
                under_75 = 0
                for name, typ, locations, not_covered_n, pct in tests.per_class:
                    if pct is not None and pct < 75.0:
                        under_75 += 1
                        flag = "UNDER 75%"
                    else:
                        flag = ""
                    cov = f"{pct}%" if pct is not None else "n/a"
                    lines.append(
                        f"| {name} | {typ} | {locations} | {not_covered_n} | {cov} | {flag} |"
                    )
                if under_75 > 0:
                    lines.append(
                        f"- classes under 75%: {under_75} (RunSpecifiedTests and "
                        "RunLocalTests require every class at 75% — see Coverage warnings)"
                    )
                else:
                    lines.append("- classes under 75%: 0")

            # S2-F-21: a run with zero component errors and zero test
            # failures can still report `status: Failed` on coverage alone
            # (the org's 75% floor, aggregate or per-class) — a reason that,
            # before this, lived only in the raw result.json.
            success = result.get("success")
            org_rejected = (success is False) or (success is None and status == "Failed")
            if org_rejected and errors == 0 and tests.failed == 0:
                under_floor = tests.coverage_pct is not None and tests.coverage_pct < 75
                if tests.coverage_warnings or under_floor:
                    lines.append(
                        "- reason: no component errors and no test failures — the org "
                        "refused on coverage (see Coverage warnings / the coverage line "
                        "above)"
                    )
                else:
                    lines.append("- reason: see result.json — not a component or test failure")

    if manifest_resolution is not None and manifest_resolution.drift_note:
        lines += ["", "## Manifest drift", "", manifest_resolution.drift_note.rstrip("\n")]

    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mock_deploy.py",
        description=(
            "Validation only. Assembles one or more build steps' artefacts into a "
            "source-format tree and runs `sf project deploy start --dry-run` "
            "(checkOnly) against an org — nothing is ever deployed. There is no "
            "flag to disable --dry-run and no --deploy option; that is by design."
        ),
    )
    parser.add_argument("plan", help="Path to the build's plan.json")
    parser.add_argument(
        "--org-alias", required=True,
        help="sf CLI org alias to validate against (the org is read, never written to)",
    )
    parser.add_argument(
        "--milestone", action="append", default=[], metavar="ID",
        help="Milestone id to validate (repeatable). Default: every step whose "
             "status is built, tested or documented.",
    )
    parser.add_argument(
        "--step", action="append", default=[], metavar="ID",
        help="Step id to validate (repeatable). Combines with --milestone.",
    )
    parser.add_argument(
        "--mode", choices=["source", "manifest"], default="source",
        help="source (default) = --source-dir force-app. manifest = --manifest "
             "package.xml, always freshly merged from the selected steps' "
             "package.xml files by type; when exactly one milestone is given "
             "and reports/MILESTONE-<id>-package.xml exists, it is compared "
             "against that merge and a WARN is printed on drift (see "
             "--prefer-report-manifest).",
    )
    parser.add_argument(
        "--prefer-report-manifest", action="store_true",
        help="--mode manifest only. On drift between the milestone verifier's "
             "reports/MILESTONE-<id>-package.xml and the steps' package.xml "
             "files, use the report's text anyway (to reproduce a report "
             "exactly) instead of the steps' merge. The drift WARN is still "
             "printed either way. Has no effect when the two already match "
             "or when no milestone report exists.",
    )
    parser.add_argument(
        "--api-version", default=None, metavar="X.Y",
        help="Force this API version (sfdx-project.json sourceApiVersion and, "
             "in --mode manifest, the merged package.xml's <version>) instead "
             "of scanning the selected steps' package.xml files. Wins over "
             "the scan outright; use it when a step you're validating needs a "
             "version none of its own artefacts declare yet.",
    )
    parser.add_argument(
        "--out", default=None,
        help="Output directory. Default: <build_dir>/reports/mock-deploy/<UTC "
             "timestamp>/. Nothing is ever written outside this directory.",
    )
    parser.add_argument(
        "--test-level", choices=TEST_LEVELS, default=DEFAULT_TEST_LEVEL, metavar="LEVEL",
        help="Apex test level for the `sf` dry run (choices: "
             f"{'|'.join(TEST_LEVELS)}). Default: NoTestRun — today's "
             "behaviour, unchanged; every dry run before this flag existed "
             "compiled Apex without ever executing it (S2-F-06). "
             "RunSpecifiedTests runs every @IsTest class found under the "
             "selected steps' assembled artefacts unless --tests overrides "
             "that list. RunLocalTests runs every test not in a managed "
             "package. RunAllTestsInOrg is deliberately not offered here "
             "(org-wide and far slower than validating one build). Tests "
             "run IN THE ORG as part of `--dry-run` validation and nothing "
             "still ever deploys or saves — `--dry-run` stays hard-coded "
             "regardless of --test-level.",
    )
    parser.add_argument(
        "--tests", default=None, metavar="A,B",
        help="Comma-separated Apex test class names to run. Only used with "
             "--test-level RunSpecifiedTests, where it overrides the "
             "automatic @IsTest scan of the selected steps' artefacts; "
             "ignored (with a WARN on stderr) for any other --test-level.",
    )
    parser.add_argument(
        "--plan-only", action="store_true",
        help="Do everything except invoke the `sf` CLI: assemble the source "
             "tree, write the manifest (--mode manifest), and write "
             "summary.md with 'status: not run (--plan-only)'. Useful to "
             "inspect manifest drift without contacting an org.",
    )
    parser.add_argument(
        "--probe", action="store_true",
        help="Validate an altered temporary copy of the build (never writes "
             "into the real build; summary is not gate evidence). Use with "
             "--without / --patch.",
    )
    parser.add_argument(
        "--without", action="append", default=[], metavar="TYPE:Member",
        help="--probe only. Remove TYPE:Member from the copy before assembly "
             "(repeatable). Deletes the source-format file(s) and strips the "
             "member from every package.xml in the copy.",
    )
    parser.add_argument(
        "--patch", action="append", default=[], metavar="PATH=FILE",
        help="--probe only. Replace <relative artefact path> in the copy with "
             "the contents of <local file> before assembly (repeatable).",
    )
    parser.add_argument(
        "--probe-dir", default=None, metavar="DIR",
        help="--probe only. Directory for the temporary build copy "
             "(must be new or empty). Default: a fresh directory under the "
             "system temp dir.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if not args.probe and (args.without or args.patch or args.probe_dir):
        parser.error("--without/--patch/--probe-dir require --probe")

    plan_path = Path(args.plan).resolve()
    if not plan_path.is_file():
        print(f"error: plan not found: {plan_path}", file=sys.stderr)
        return 2
    try:
        plan = load_plan(plan_path)
    except json.JSONDecodeError as exc:
        print(f"error: could not parse plan.json: {exc}", file=sys.stderr)
        return 2

    real_build_dir = plan_path.parent
    build_dir = real_build_dir
    artefacts_root = plan.get("artefacts_root", "artefacts")
    probe_alteration: ProbeAlteration | None = None

    if args.probe:
        # Resolve --without before touching the copy or the org so an
        # unmappable type fails fast with no subprocess.run call.
        try:
            for spec in args.without:
                resolve_without_spec(spec)
            for spec in args.patch:
                if "=" not in spec or not spec.split("=", 1)[0].strip() or not spec.split("=", 1)[1].strip():
                    raise ValueError(
                        f"invalid --patch {spec!r}: expected "
                        "<relative artefact path>=<local file>"
                    )
                src = Path(spec.split("=", 1)[1].strip()).expanduser().resolve()
                if not src.is_file():
                    raise ValueError(f"--patch source not found: {src}")
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

        try:
            probe_dir = create_probe_copy(
                real_build_dir,
                Path(args.probe_dir) if args.probe_dir else None,
            )
            apply_probe_without(probe_dir, args.without)
            patched = apply_probe_patches(probe_dir, args.patch)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

        probe_alteration = ProbeAlteration(
            without=list(args.without),
            patched=[f"{rel}={src}" for rel, src in patched],
            copy_dir=str(probe_dir),
        )
        build_dir = probe_dir

    selected = select_steps(plan, args.milestone, args.step)
    if not selected:
        print(
            "error: no steps selected — check --milestone/--step, or that some "
            "step's status is built, tested or documented",
            file=sys.stderr,
        )
        return 2
    step_ids = [s["id"] for s in selected]

    if args.out:
        out_dir = Path(args.out).resolve()
        if probe_alteration is not None:
            try:
                out_dir.relative_to(real_build_dir.resolve())
            except ValueError:
                pass  # out_dir is outside the real build — fine
            else:
                print(
                    f"error: --probe refuses --out under the real build ({out_dir}); "
                    "omit --out to use the copy's reports/mock-deploy/, or pass a "
                    "path outside the build",
                    file=sys.stderr,
                )
                return 2
    else:
        timestamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
        out_dir = build_dir / "reports" / "mock-deploy" / timestamp
    out_dir.mkdir(parents=True, exist_ok=True)

    force_app_dir = out_dir / "force-app" / "main" / "default"
    force_app_dir.mkdir(parents=True, exist_ok=True)
    copy_result = copy_artefacts(build_dir, artefacts_root, step_ids, force_app_dir)

    if args.api_version:
        api_version = args.api_version
        api_version_source = "override"
    else:
        version_resolution = pick_api_version(build_dir, artefacts_root, step_ids)
        api_version = version_resolution.version
        api_version_source = version_resolution.source
    write_sfdx_project(out_dir, api_version)

    manifest_name = "package.xml"
    manifest_resolution: ManifestResolution | None = None
    missing_members: list[tuple[str, str]] = []
    if args.mode == "manifest":
        manifest_resolution = resolve_manifest_text(
            build_dir, artefacts_root, args.milestone, args.step, step_ids, api_version,
            prefer_report_manifest=args.prefer_report_manifest,
        )
        (out_dir / manifest_name).write_text(manifest_resolution.xml_text, encoding="utf-8")
        if manifest_resolution.warning:
            print(manifest_resolution.warning, file=sys.stderr)

        # S2-F-22: under-copy check — the manifest can name more than the
        # selected steps' artefacts actually put in the assembled tree.
        missing_members = find_missing_manifest_members(manifest_resolution.xml_text, force_app_dir)
        if missing_members:
            first_type, first_member = missing_members[0]
            print(
                f"WARN: {len(missing_members)} manifest member(s) have no file in the "
                f"assembled tree (first: {first_type}:{first_member}) — select the steps "
                "that own them (default selection = every built step)",
                file=sys.stderr,
            )

    test_level = args.test_level
    tests_override = (
        [t.strip() for t in args.tests.split(",") if t.strip()] if args.tests else None
    )
    resolved_tests: list[str] | None = None
    if test_level == "RunSpecifiedTests":
        resolved_tests = tests_override if tests_override else find_test_classes(force_app_dir)
        if not resolved_tests:
            print(
                "error: --test-level RunSpecifiedTests requires at least one Apex "
                "test class — none found under the assembled tree (no @IsTest class "
                "with a test method) and no --tests override given",
                file=sys.stderr,
            )
            return 2
    elif tests_override:
        print(
            f"WARN: --tests given but --test-level is {test_level}; ignoring --tests "
            "(only used with --test-level RunSpecifiedTests)",
            file=sys.stderr,
        )

    cmd = build_sf_command(
        args.mode, args.org_alias, manifest_name, test_level=test_level, tests=resolved_tests
    )
    assert "--dry-run" in cmd  # hard invariant: this script never deploys

    if args.plan_only:
        summary = render_summary(
            None, args.mode, args.org_alias, manifest_resolution, plan_only=True,
            copy_result=copy_result, api_version=api_version, api_version_source=api_version_source,
            planned_test_level=test_level,
            planned_tests=resolved_tests if test_level == "RunSpecifiedTests" else None,
            probe=probe_alteration,
        )
        summary_path = out_dir / "summary.md"
        summary_path.write_text(summary, encoding="utf-8")
        print(summary)
        if probe_alteration is not None:
            print(f"probe copy: {probe_alteration.copy_dir}")
            print(f"summary: {summary_path}")
        print(f"output: {out_dir}")
        return 0

    try:
        proc = subprocess.run(cmd, cwd=str(out_dir), capture_output=True, text=True)
    except FileNotFoundError:
        print("error: `sf` CLI not found on PATH", file=sys.stderr)
        return 2

    raw_stdout = proc.stdout or ""
    raw_stderr = proc.stderr or ""
    api_version_record = {"value": api_version, "source": api_version_source}

    try:
        parsed = json.loads(strip_json_prefix(raw_stdout))
    except (ValueError, json.JSONDecodeError) as exc:
        (out_dir / "result.json").write_text(
            json.dumps(
                {
                    "error": str(exc),
                    "raw_stdout": raw_stdout,
                    "raw_stderr": raw_stderr,
                    "api_version": api_version_record,
                    **(
                        {
                            "probe": {
                                "without": probe_alteration.without,
                                "patched": probe_alteration.patched,
                                "copy_dir": probe_alteration.copy_dir,
                            }
                        }
                        if probe_alteration is not None
                        else {}
                    ),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"error: could not parse `sf` CLI output as JSON: {exc}", file=sys.stderr)
        if raw_stderr:
            print(raw_stderr, file=sys.stderr)
        return 2

    test_summary = extract_test_summary(parsed, test_level, resolved_tests)
    tests_record = {
        "level": test_summary.level,
        "requested_tests": test_summary.requested_tests,
        "run": test_summary.run,
        "passed": test_summary.passed,
        "failed": test_summary.failed,
        "coverage_pct": test_summary.coverage_pct,
        "failures": [
            {"class": c, "method": m, "message": msg, "stack_first_line": s}
            for c, m, msg, s in test_summary.failures
        ],
        "coverage_warnings": [
            {"name": n, "message": msg} for n, msg in test_summary.coverage_warnings
        ],
        "per_class": [
            {
                "name": n,
                "type": t,
                "locations": loc,
                "not_covered": nc,
                "pct": pct,
            }
            for n, t, loc, nc, pct in test_summary.per_class
        ],
    }

    if isinstance(parsed, dict):
        # `parsed` is this run's own in-memory copy of the sf CLI's JSON — safe
        # to extend before we serialize it. "api_version"/"tests"/
        # "missing_members"/"probe" are not keys `sf` itself ever emits, so none
        # can collide with or shadow one of its existing keys (status, result,
        # warnings, ...).
        parsed["api_version"] = api_version_record
        parsed["tests"] = tests_record
        parsed["missing_members"] = [
            {"type": t, "member": m} for t, m in missing_members
        ]
        if probe_alteration is not None:
            parsed["probe"] = {
                "without": probe_alteration.without,
                "patched": probe_alteration.patched,
                "copy_dir": probe_alteration.copy_dir,
            }

    (out_dir / "result.json").write_text(json.dumps(parsed, indent=2) + "\n", encoding="utf-8")

    result = parsed.get("result") if isinstance(parsed, dict) else None
    status = result.get("status") if isinstance(result, dict) else None

    summary = render_summary(
        parsed, args.mode, args.org_alias, manifest_resolution, copy_result=copy_result,
        api_version=api_version, api_version_source=api_version_source, tests=test_summary,
        probe=probe_alteration,
    )
    summary_path = out_dir / "summary.md"
    summary_path.write_text(summary, encoding="utf-8")
    print(summary)
    if probe_alteration is not None:
        print(f"probe copy: {probe_alteration.copy_dir}")
        print(f"summary: {summary_path}")
    print(f"output: {out_dir}")

    return exit_code_for_status(status)


if __name__ == "__main__":
    raise SystemExit(main())
