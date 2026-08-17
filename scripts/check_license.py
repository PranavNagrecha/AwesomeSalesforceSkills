#!/usr/bin/env python3
"""Single-source-of-truth gate for every license declaration in the repo.

The repo previously shipped three disagreeing answers to "what license is
this?" — root ``LICENSE`` and ``.claude-plugin/*.json`` said Apache-2.0 while
``mcp/sfskills-mcp/pyproject.toml`` said MIT, and the wheel carried no license
file at all. Nothing caught it because no gate compared the surfaces to each
other. This checker is that gate.

Canonical value: ``LICENSE_ID`` below, matching the text of root ``LICENSE``.
Every other surface is asserted against it:

  - root ``LICENSE``                      -> title line + ``Required Notice:``
  - ``mcp/sfskills-mcp/LICENSE``          -> byte-identical copy of the root
  - ``mcp/sfskills-mcp/pyproject.toml``   -> PEP 639 SPDX expression, a
    ``license-files`` key, and NO ``License ::`` trove classifier (PyPI
    rejects an upload carrying both a License-Expression and a classifier)
  - ``scripts/build_plugin.py``           -> the literal the generator emits
  - ``.claude-plugin/*.json``             -> generated output agrees
  - ``README.md``                         -> badge + license section
  - ``LICENSING.md``                      -> exists (the commercial path)

The package-dir LICENSE is a *copy* because PEP 639 ``license-files`` globs
cannot reference parent directories. ``--fix`` re-copies it from the root;
everything else is reported rather than rewritten, because a stale license
string is a decision to re-make, not a typo to silently patch.

stdlib only. Run standalone (``python3 scripts/check_license.py [--fix]``) or
import ``collect_license_issues`` from validate_repo.py.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# The canonical identifier. Changing the project's license means changing this
# constant, root LICENSE, and LICENSING.md together — the checker then tells
# you every downstream surface that still disagrees.
LICENSE_ID = "PolyForm-Small-Business-1.0.0"
LICENSE_TITLE = "PolyForm Small Business License 1.0.0"
REQUIRED_NOTICE_PREFIX = "Required Notice: Copyright"

ROOT_LICENSE = ROOT / "LICENSE"
PKG_LICENSE = ROOT / "mcp" / "sfskills-mcp" / "LICENSE"
PYPROJECT = ROOT / "mcp" / "sfskills-mcp" / "pyproject.toml"
BUILD_PLUGIN = ROOT / "scripts" / "build_plugin.py"
PLUGIN_JSONS = (
    ROOT / ".claude-plugin" / "plugin.json",
    ROOT / ".claude-plugin" / "marketplace.json",
)
README = ROOT / "README.md"
LICENSING = ROOT / "LICENSING.md"

# Permissive identifiers that must no longer appear as *our* declared license.
# Matched only against license-declaring lines, never against prose, so that
# CHANGELOG history and third-party notices are free to mention them.
STALE_IDS = ("Apache-2.0", "Apache_2.0", "MIT")


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def collect_license_issues(root: Path = ROOT, fix: bool = False) -> list[str]:
    """Return a list of human-readable license-consistency problems."""
    issues: list[str] = []

    # --- root LICENSE ------------------------------------------------------
    root_license = root / "LICENSE"
    if not root_license.exists():
        return [f"{_rel(root_license)}: missing — the canonical license text"]

    root_text = root_license.read_text(encoding="utf-8")
    if LICENSE_TITLE not in root_text:
        issues.append(
            f"{_rel(root_license)}: does not contain the title {LICENSE_TITLE!r}"
        )
    if REQUIRED_NOTICE_PREFIX not in root_text:
        issues.append(
            f"{_rel(root_license)}: missing a '{REQUIRED_NOTICE_PREFIX} ...' line — "
            "the license's Notices section requires redistributors to carry it, "
            "so it has to be in the file they receive"
        )

    # --- packaged copy -----------------------------------------------------
    pkg_license = root / "mcp" / "sfskills-mcp" / "LICENSE"
    if not pkg_license.exists():
        if fix:
            shutil.copyfile(root_license, pkg_license)
        else:
            issues.append(
                f"{_rel(pkg_license)}: missing — the wheel would ship with no "
                "license file (run with --fix to copy it from the root)"
            )
    elif pkg_license.read_text(encoding="utf-8") != root_text:
        if fix:
            shutil.copyfile(root_license, pkg_license)
        else:
            issues.append(
                f"{_rel(pkg_license)}: drifted from {_rel(root_license)} — "
                "PEP 639 license-files globs cannot escape the package dir, so "
                "this copy must be kept in sync (run with --fix)"
            )

    # --- pyproject ---------------------------------------------------------
    pyproject = root / "mcp" / "sfskills-mcp" / "pyproject.toml"
    if not pyproject.exists():
        issues.append(f"{_rel(pyproject)}: missing")
    else:
        text = pyproject.read_text(encoding="utf-8")
        if not re.search(rf'^license\s*=\s*"{re.escape(LICENSE_ID)}"', text, re.MULTILINE):
            issues.append(
                f'{_rel(pyproject)}: expected `license = "{LICENSE_ID}"` '
                "(a PEP 639 SPDX expression) as a top-level key"
            )
        if not re.search(r"^license-files\s*=", text, re.MULTILINE):
            issues.append(
                f"{_rel(pyproject)}: missing a `license-files` key — without it "
                "the LICENSE is not included in the wheel or sdist"
            )
        classifier = re.search(r'^\s*"License ::.*"', text, re.MULTILINE)
        if classifier:
            issues.append(
                f"{_rel(pyproject)}: carries a trove classifier "
                f"{classifier.group(0).strip()} alongside a License-Expression — "
                "PyPI rejects uploads that declare both"
            )

    # --- plugin generator + its generated output ---------------------------
    build_plugin = root / "scripts" / "build_plugin.py"
    if build_plugin.exists():
        text = build_plugin.read_text(encoding="utf-8")
        emitted = set(re.findall(r'"license":\s*"([^"]+)"', text))
        wrong = emitted - {LICENSE_ID}
        if wrong:
            issues.append(
                f"{_rel(build_plugin)}: emits license {sorted(wrong)} — "
                f"expected {LICENSE_ID!r} (this generates .claude-plugin/*.json, "
                "which must never be hand-edited)"
            )
        if not emitted:
            issues.append(
                f"{_rel(build_plugin)}: no `\"license\": \"...\"` literal found — "
                "the generated plugin manifests would carry no license"
            )

    for plugin_json in (
        root / ".claude-plugin" / "plugin.json",
        root / ".claude-plugin" / "marketplace.json",
    ):
        if not plugin_json.exists():
            continue
        try:
            data = json.loads(plugin_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            issues.append(f"{_rel(plugin_json)}: unparseable JSON ({exc})")
            continue
        for where, value in _iter_license_values(data):
            if value != LICENSE_ID:
                issues.append(
                    f"{_rel(plugin_json)}: {where} declares {value!r}, "
                    f"expected {LICENSE_ID!r} — regenerate with "
                    "`python3 scripts/build_plugin.py`"
                )

    # --- README ------------------------------------------------------------
    readme = root / "README.md"
    if readme.exists():
        for line_no, line in enumerate(readme.read_text(encoding="utf-8").splitlines(), 1):
            if "LICENSE" not in line and "License" not in line:
                continue
            if "img.shields.io/badge/License" in line or re.match(r"^\s*(\*\*)?License", line):
                for stale in STALE_IDS:
                    if stale in line:
                        issues.append(
                            f"{_rel(readme)}:{line_no}: license line still says "
                            f"{stale!r} — expected {LICENSE_TITLE!r}"
                        )
                        break

    # --- commercial path ---------------------------------------------------
    licensing = root / "LICENSING.md"
    if not licensing.exists():
        issues.append(
            f"{_rel(licensing)}: missing — a source-available license that names "
            "no way to buy a commercial license excludes enterprises without "
            "ever collecting from them"
        )

    return issues


def _iter_license_values(node, where: str = "$"):
    """Yield ``(json_path, value)`` for every ``license`` key in the document."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "license" and isinstance(value, str):
                yield f"{where}.license", value
            else:
                yield from _iter_license_values(value, f"{where}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from _iter_license_values(value, f"{where}[{index}]")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--fix",
        action="store_true",
        help="re-copy the packaged LICENSE from the repo root (the only "
        "auto-fixable drift; every other mismatch is reported)",
    )
    args = parser.parse_args()

    issues = collect_license_issues(fix=args.fix)
    if issues:
        print(f"License consistency: {len(issues)} issue(s)\n")
        for issue in issues:
            print(f"  ERROR  {issue}")
        return 1

    print(f"License consistency: OK — every surface declares {LICENSE_ID}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
