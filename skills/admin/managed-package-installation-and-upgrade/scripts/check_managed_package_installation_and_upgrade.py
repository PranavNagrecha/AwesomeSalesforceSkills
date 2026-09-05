#!/usr/bin/env python3
"""Static checker for subscriber-side managed package install hygiene.

Reads a Salesforce project tree plus a package inventory artefact and reports
what will bite on the next install, upgrade, or uninstall.

Checks
------
1. installedPackage files      file base name is a usable namespace prefix;
                               versionNumber is present and well formed;
                               securityType and activateRSS are explicit, not
                               left to their (opposite) defaults.
2. install manifests           a package.xml naming InstalledPackage must name
                               nothing else, and at most 20 members.
3. package inventory           config/package-inventory.json linted for expired
                               or over-allocated licences, version drift between
                               environments, and packages with no owner.
4. permission set namespaces   a PermissionSet that grants a namespaced object,
                               field, class, or tab whose namespace is not in the
                               inventory (stale grant, or an undocumented package).
5. subscriber code references  Apex / Flow references to each managed namespace,
                               the pre-uninstall reference audit.
6. profile-baked grants        profiles granting namespaced field access, the
                               signature of an "Install for All Users" install.

Grounding for the rules is in ../references/metadata-examples.md and
../references/gotchas.md. Stdlib only.

Exit status: 1 if any ERROR was reported, otherwise 0 (WARN and INFO do not fail).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MD_NS = "{http://soap.sforce.com/2006/04/metadata}"

# api_meta.txt L22290-22294: a namespace prefix is a 1-15 character alphanumeric
# identifier. Underscores are accepted here; see the UNVERIFIED note in
# ../references/metadata-examples.md.
NAMESPACE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,14}$")

# api_meta.txt L81434-81439: majorNumber.minorNumber.patchNumber, e.g. 2.1.3.
# The guide's own sample uses a two-part "1.0", so both shapes are accepted.
VERSION_RE = re.compile(r"^\d+\.\d+(\.\d+)?$")

# api_meta.txt L81428-81432: securityType is AdminsOnly or AllUsers.
SECURITY_TYPES = {"AdminsOnly", "AllUsers"}

# api_meta.txt L81392-81393: at most 20 first-generation packages per deployment.
MAX_PACKAGES_PER_DEPLOY = 20

# Namespace-prefixed API name, e.g. acme_rev__Revenue_Schedule__c.
NS_PREFIX_RE = re.compile(r"\b([a-z][a-z0-9_]{0,14})__([A-Z][A-Za-z0-9_]+)\b")

# Salesforce-shipped prefixes and common false positives that are not
# third-party managed packages.
BUILTIN_PREFIXES = {
    "force", "lightning", "ui", "schema", "system", "apex", "auraenabled",
    "salesforce", "test", "console", "sf", "c",
}

INVENTORY_CANDIDATES = (
    "config/package-inventory.json",
    "package-inventory.json",
    "manifest/package-inventory.json",
)


class Report:
    """Collects findings at three severities."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warns: list[str] = []
        self.infos: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warns.append(msg)

    def info(self, msg: str) -> None:
        self.infos.append(msg)

    def emit(self) -> int:
        for m in self.errors:
            print(f"ERROR: {m}", file=sys.stderr)
        for m in self.warns:
            print(f"WARN:  {m}", file=sys.stderr)
        for m in self.infos:
            print(f"INFO:  {m}")
        if not (self.errors or self.warns or self.infos):
            print("[managed-package-installation-and-upgrade] no findings")
        else:
            print(
                f"[managed-package-installation-and-upgrade] "
                f"{len(self.errors)} error(s), {len(self.warns)} warning(s), "
                f"{len(self.infos)} note(s)"
            )
        return 1 if self.errors else 0


def child_text(element, tag: str) -> str | None:
    """Text of a direct child, namespaced or not.

    Never rely on the truthiness of an Element: a leaf Element with no children
    is falsy even when it exists, so `el.find(a) or el.find(b)` silently skips
    real nodes. Test `is not None` explicitly.
    """
    if element is None:
        return None
    found = element.find(f"{MD_NS}{tag}")
    if found is None:
        found = element.find(tag)
    if found is None:
        return None
    text = found.text
    return text.strip() if text else ""


def iter_children(element, tag: str):
    if element is None:
        return []
    nodes = element.findall(f"{MD_NS}{tag}")
    if not nodes:
        nodes = element.findall(tag)
    return nodes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit subscriber-side managed package install hygiene.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce project (default: current directory).",
    )
    parser.add_argument(
        "--inventory",
        default=None,
        help=(
            "Path to package-inventory.json. Default: the first of "
            + ", ".join(INVENTORY_CANDIDATES)
            + " that exists under --manifest-dir."
        ),
    )
    parser.add_argument(
        "--today",
        default=None,
        help="Override today's date (YYYY-MM-DD) for licence-expiry checks.",
    )
    return parser.parse_args()


# --------------------------------------------------------------------------
# Check 1 — installedPackage files
# --------------------------------------------------------------------------

def check_installed_packages(root: Path, report: Report) -> set[str]:
    """Validate every installedPackages/*.installedPackage[-meta.xml] file."""
    declared: set[str] = set()
    files = sorted(
        p for p in root.rglob("*.installedPackage*")
        if p.is_file() and p.suffix in (".installedPackage", ".xml")
    )
    if not files:
        report.info(
            "no installedPackages/*.installedPackage file found under "
            f"{root} — the install is not tracked as source"
        )
        return declared

    for path in files:
        base = path.name
        for suffix in (".installedPackage-meta.xml", ".installedPackage"):
            if base.endswith(suffix):
                base = base[: -len(suffix)]
                break
        declared.add(base.lower())

        if not NAMESPACE_RE.match(base):
            report.error(
                f"{path}: file base name `{base}` is not a valid namespace prefix "
                "(1-15 chars, starts with a letter) — the file must be named after "
                "the package's namespace prefix, not its package name or 04t id"
            )

        try:
            elem = ET.parse(path).getroot()
        except (ET.ParseError, OSError) as exc:
            report.error(f"{path}: cannot parse ({exc})")
            continue

        version = child_text(elem, "versionNumber")
        if version is None:
            report.error(f"{path}: required element <versionNumber> is missing")
        elif not VERSION_RE.match(version):
            report.error(
                f"{path}: versionNumber `{version}` is not "
                "majorNumber.minorNumber[.patchNumber] (e.g. 2.1.3)"
            )

        security = child_text(elem, "securityType")
        if security is None:
            report.warn(
                f"{path}: <securityType> is absent, so this deploy installs for "
                "AllUsers (Metadata API default) while `sf package install` would "
                "default to AdminsOnly — state it explicitly"
            )
        elif security not in SECURITY_TYPES:
            report.error(
                f"{path}: securityType `{security}` is not one of "
                + " / ".join(sorted(SECURITY_TYPES))
            )

        rss = child_text(elem, "activateRSS")
        if rss is None:
            report.warn(
                f"{path}: <activateRSS> is required and defaults to false — any "
                "Remote Site Setting or CSP Trusted Site the package ships will "
                "arrive inactive and its callouts will fail on first use"
            )
        elif rss.lower() not in ("true", "false"):
            report.error(f"{path}: activateRSS `{rss}` is not true or false")

        if child_text(elem, "password") not in (None, ""):
            report.warn(
                f"{path}: <password> holds the installation key in plain text — "
                "source it from a CI variable at build time instead of committing it"
            )

    return declared


# --------------------------------------------------------------------------
# Check 2 — install manifests
# --------------------------------------------------------------------------

def check_install_manifests(root: Path, report: Report) -> None:
    """An InstalledPackage manifest must be single-type and <= 20 members."""
    for path in sorted(root.rglob("package.xml")):
        try:
            elem = ET.parse(path).getroot()
        except (ET.ParseError, OSError):
            continue

        type_names: list[str] = []
        pkg_members: list[str] = []
        for types_el in iter_children(elem, "types"):
            name = child_text(types_el, "name")
            if name is None:
                continue
            type_names.append(name)
            if name == "InstalledPackage":
                for member in iter_children(types_el, "members"):
                    pkg_members.append((member.text or "").strip())

        if "InstalledPackage" not in type_names:
            continue

        others = sorted({n for n in type_names if n != "InstalledPackage"})
        if others:
            report.error(
                f"{path}: manifest names InstalledPackage alongside "
                f"{', '.join(others)} — when you deploy InstalledPackage it must "
                "be the only metadata type in the manifest; split the install "
                "into its own deployment"
            )

        concrete = [m for m in pkg_members if m and m != "*"]
        if len(concrete) > MAX_PACKAGES_PER_DEPLOY:
            report.error(
                f"{path}: {len(concrete)} InstalledPackage members — at most "
                f"{MAX_PACKAGES_PER_DEPLOY} first-generation managed packages can "
                "be installed in a single deployment"
            )


# --------------------------------------------------------------------------
# Check 3 — package inventory
# --------------------------------------------------------------------------

def load_inventory(root: Path, explicit: str | None, report: Report):
    if explicit:
        path = Path(explicit)
        if not path.is_absolute():
            path = root / explicit
        if not path.exists():
            report.error(f"--inventory {path} does not exist")
            return None, None
    else:
        path = None
        for candidate in INVENTORY_CANDIDATES:
            trial = root / candidate
            if trial.exists():
                path = trial
                break
        if path is None:
            report.warn(
                "no package inventory found (looked for "
                + ", ".join(INVENTORY_CANDIDATES)
                + ") — licence, drift, and ownership checks are skipped; see "
                "references/metadata-examples.md section 7 for the shape"
            )
            return None, None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        report.error(f"{path}: cannot parse inventory ({exc})")
        return None, None
    if not isinstance(data, dict) or not isinstance(data.get("packages"), list):
        report.error(f"{path}: expected an object with a `packages` array")
        return None, None
    return path, data


def check_inventory(path: Path, data: dict, today: dt.date, report: Report) -> set[str]:
    namespaces: set[str] = set()
    environments = data.get("environments")
    if not isinstance(environments, list) or not environments:
        environments = None

    for index, entry in enumerate(data.get("packages", [])):
        if not isinstance(entry, dict):
            report.error(f"{path}: packages[{index}] is not an object")
            continue
        ns = (entry.get("namespace") or "").strip()
        label = ns or f"packages[{index}]"
        if not ns:
            report.error(f"{path}: {label} has no `namespace`")
        elif not NAMESPACE_RE.match(ns):
            report.error(
                f"{path}: namespace `{ns}` is not a valid namespace prefix "
                "(1-15 chars, starts with a letter)"
            )
        else:
            namespaces.add(ns.lower())

        owner = entry.get("owner")
        if not owner or not str(owner).strip():
            report.warn(
                f"{path}: package `{label}` has no owner — nobody is accountable "
                "for its renewal, its release notes, or its push-upgrade posture"
            )

        lic = entry.get("licenses")
        if isinstance(lic, dict):
            allowed = lic.get("allowed")
            used = lic.get("used")
            if isinstance(allowed, int) and isinstance(used, int):
                if used > allowed:
                    report.error(
                        f"{path}: package `{label}` has {used} seats used against "
                        f"{allowed} allowed — further UserPackageLicense inserts "
                        "fail with LICENSE_LIMIT_EXCEEDED"
                    )
                elif allowed > 0 and used == allowed:
                    report.warn(
                        f"{path}: package `{label}` has consumed every seat "
                        f"({used}/{allowed}) — the next new user is locked out"
                    )
                elif allowed > 0 and used == 0:
                    report.warn(
                        f"{path}: package `{label}` is installed with 0 of "
                        f"{allowed} seats assigned — permissions without a seat "
                        "still lock users out"
                    )
            status = lic.get("status")
            if status is not None and status not in ("Active", "Expired", "Free", "Trial"):
                report.error(
                    f"{path}: package `{label}` licence status `{status}` is not "
                    "one of Active / Expired / Free / Trial"
                )
            if status == "Expired":
                report.error(
                    f"{path}: package `{label}` licence status is Expired — "
                    "users lose access regardless of permission sets"
                )
            expiry = lic.get("expirationDate")
            if isinstance(expiry, str) and expiry:
                try:
                    when = dt.date.fromisoformat(expiry[:10])
                except ValueError:
                    report.error(
                        f"{path}: package `{label}` expirationDate `{expiry}` is "
                        "not an ISO date (YYYY-MM-DD)"
                    )
                else:
                    days = (when - today).days
                    if days < 0:
                        report.error(
                            f"{path}: package `{label}` licence expired "
                            f"{-days} day(s) ago ({expiry})"
                        )
                    elif days <= 60:
                        report.warn(
                            f"{path}: package `{label}` licence expires in "
                            f"{days} day(s) ({expiry}) — renew before the next "
                            "release train, not after"
                        )
        elif lic is not None:
            report.error(f"{path}: package `{label}` `licenses` is not an object")

        versions = entry.get("versions")
        if isinstance(versions, dict) and versions:
            for env, ver in sorted(versions.items()):
                if isinstance(ver, str) and ver and not VERSION_RE.match(ver):
                    report.error(
                        f"{path}: package `{label}` version `{ver}` in `{env}` is "
                        "not majorNumber.minorNumber[.patchNumber]"
                    )
            distinct = {str(v) for v in versions.values() if v}
            if len(distinct) > 1:
                pairs = ", ".join(f"{k}={v}" for k, v in sorted(versions.items()))
                report.error(
                    f"{path}: package `{label}` version drift across environments "
                    f"({pairs}) — a sandbox that does not match production is not "
                    "a rehearsal of the upgrade"
                )
            if environments:
                missing = [e for e in environments if e not in versions]
                if missing:
                    report.warn(
                        f"{path}: package `{label}` has no recorded version for "
                        + ", ".join(missing)
                    )
        elif versions is not None:
            report.error(f"{path}: package `{label}` `versions` is not an object")

        sec = entry.get("securityType")
        if sec is not None and sec not in SECURITY_TYPES:
            report.error(
                f"{path}: package `{label}` securityType `{sec}` is not "
                + " / ".join(sorted(SECURITY_TYPES))
            )
        elif sec == "AllUsers":
            report.warn(
                f"{path}: package `{label}` was installed for AllUsers — the grant "
                "sits in profile settings and is reversible only per profile"
            )

    return namespaces


# --------------------------------------------------------------------------
# Check 4 — permission sets referencing unknown namespaces
# --------------------------------------------------------------------------

def namespaces_in_permission_sets(root: Path) -> dict[str, dict[str, set[str]]]:
    """namespace -> {permission set path -> referenced API names}."""
    found: dict[str, dict[str, set[str]]] = {}
    patterns = ("*.permissionset-meta.xml", "*.permissionset")
    seen: set[Path] = set()
    for pattern in patterns:
        for path in root.rglob(pattern):
            if path in seen or not path.is_file():
                continue
            seen.add(path)
            try:
                elem = ET.parse(path).getroot()
            except (ET.ParseError, OSError):
                continue
            refs: list[str] = []
            for parent, tag in (
                ("objectPermissions", "object"),
                ("fieldPermissions", "field"),
                ("classAccesses", "apexClass"),
                ("tabSettings", "tab"),
                ("pageAccesses", "apexPage"),
                ("recordTypeVisibilities", "recordType"),
                ("applicationVisibilities", "application"),
            ):
                for node in iter_children(elem, parent):
                    value = child_text(node, tag)
                    if value:
                        refs.append(value)
            for value in refs:
                for match in NS_PREFIX_RE.finditer(value):
                    ns = match.group(1).lower()
                    if ns in BUILTIN_PREFIXES:
                        continue
                    found.setdefault(ns, {}).setdefault(str(path), set()).add(value)
    return found


def check_permission_set_namespaces(
    root: Path, known: set[str], have_inventory: bool, report: Report
) -> None:
    refs = namespaces_in_permission_sets(root)
    if not refs:
        return
    for ns, by_file in sorted(refs.items()):
        if not have_inventory:
            report.info(
                f"permission sets grant namespace `{ns}__` in "
                f"{len(by_file)} file(s) — no inventory to check it against"
            )
            continue
        if ns in known:
            continue
        files = sorted(by_file)
        sample_names = sorted({n for names in by_file.values() for n in names})[:3]
        report.error(
            f"permission set(s) {', '.join(files[:3])}"
            f"{' (and more)' if len(files) > 3 else ''} grant components in "
            f"namespace `{ns}__` ({', '.join(sample_names)}) but no package with "
            "that namespace is in the inventory — either the package is "
            "undocumented, or the grant is stale from an uninstalled package"
        )


# --------------------------------------------------------------------------
# Check 5 — subscriber code references
# --------------------------------------------------------------------------

def subscriber_namespace_refs(root: Path, known: set[str]) -> dict[str, set[str]]:
    """Namespace -> files. Catches both `ns__Api_Name__c` and, for namespaces we
    already know about, the dotted Apex form `ns.ClassName`. The dotted form is
    only matched against known namespaces: `foo.Bar` is otherwise indistinguishable
    from any local variable dereference."""
    refs: dict[str, set[str]] = {}
    dotted = None
    if known:
        alternation = "|".join(re.escape(ns) for ns in sorted(known))
        dotted = re.compile(rf"\b({alternation})\.([A-Z][A-Za-z0-9_]*)\b", re.IGNORECASE)
    patterns = ("*.cls", "*.trigger", "*.flow-meta.xml", "*.flow")
    for pattern in patterns:
        for path in root.rglob(pattern):
            if "installedPackages" in path.parts or not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for match in NS_PREFIX_RE.finditer(text):
                ns = match.group(1).lower()
                if ns in BUILTIN_PREFIXES:
                    continue
                refs.setdefault(ns, set()).add(str(path))
            if dotted is not None:
                for match in dotted.finditer(text):
                    refs.setdefault(match.group(1).lower(), set()).add(str(path))
    return refs


def check_subscriber_refs(
    root: Path, known: set[str], have_inventory: bool, report: Report
) -> None:
    refs = subscriber_namespace_refs(root, known)
    for ns, files in sorted(refs.items()):
        sample = sorted(files)[:3]
        more = " (and more)" if len(files) > len(sample) else ""
        message = (
            f"subscriber code references managed namespace `{ns}__` in "
            f"{len(files)} file(s): {', '.join(sample)}{more} — every one blocks "
            "an uninstall and breaks on a publisher rename"
        )
        if have_inventory and ns not in known:
            report.error(message + "; and `" + ns + "` is not in the inventory")
        else:
            report.info(message)


# --------------------------------------------------------------------------
# Check 6 — profile-baked grants
# --------------------------------------------------------------------------

def check_profiles(root: Path, report: Report) -> None:
    by_profile: dict[str, set[str]] = {}
    seen: set[Path] = set()
    for pattern in ("*.profile-meta.xml", "*.profile"):
        for path in root.rglob(pattern):
            if path in seen or not path.is_file():
                continue
            seen.add(path)
            try:
                elem = ET.parse(path).getroot()
            except (ET.ParseError, OSError):
                continue
            for node in iter_children(elem, "fieldPermissions"):
                field = child_text(node, "field")
                if not field:
                    continue
                editable = (child_text(node, "editable") or "").lower() == "true"
                readable = (child_text(node, "readable") or "").lower() == "true"
                if not (editable or readable):
                    continue
                for match in NS_PREFIX_RE.finditer(field):
                    if match.group(1).lower() in BUILTIN_PREFIXES:
                        continue
                    by_profile.setdefault(str(path), set()).add(field)
                    break
    for profile, fields in sorted(by_profile.items()):
        sample = sorted(fields)[:3]
        more = " (and more)" if len(fields) > len(sample) else ""
        report.warn(
            f"profile `{profile}` grants access to packaged field(s) "
            f"{', '.join(sample)}{more} — the signature of an AllUsers install; "
            "move the grant to a subscriber-owned permission set so it is "
            "reversible and survives uninstall"
        )


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ERROR: --manifest-dir {root} does not exist", file=sys.stderr)
        return 1

    if args.today:
        try:
            today = dt.date.fromisoformat(args.today)
        except ValueError:
            print(f"ERROR: --today {args.today} is not YYYY-MM-DD", file=sys.stderr)
            return 1
    else:
        today = dt.date.today()

    report = Report()

    declared = check_installed_packages(root, report)
    check_install_manifests(root, report)

    inv_path, inv_data = load_inventory(root, args.inventory, report)
    known: set[str] = set()
    have_inventory = inv_data is not None
    if have_inventory:
        known = check_inventory(inv_path, inv_data, today, report)
        undeclared = sorted(known - declared) if declared else []
        if declared:
            for ns in sorted(declared - known):
                report.error(
                    f"installedPackages/{ns}.installedPackage exists but `{ns}` is "
                    "not in the inventory — the install is not tracked"
                )
            for ns in undeclared:
                report.info(
                    f"inventory lists `{ns}` with no installedPackage file — "
                    "expected for 2GP and unlocked packages, which install through "
                    "`sf package install`"
                )

    check_permission_set_namespaces(root, known, have_inventory, report)
    check_subscriber_refs(root, known, have_inventory, report)
    check_profiles(root, report)

    return report.emit()


if __name__ == "__main__":
    sys.exit(main())
