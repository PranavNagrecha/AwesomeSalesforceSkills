"""Discover and inspect an optional local Salesforce DX project.

SfSkills is a skill library, not a Salesforce DX project.  Product workflows
must therefore treat local metadata as optional enrichment.  This module
implements a deterministic, read-only discovery contract with three normal
outcomes:

* an explicit project (or a file inside one) was supplied;
* a project was discovered from the current directory/workspace roots; or
* no project was found and the caller should continue in standalone mode.

The module deliberately does not call Salesforce CLI, mutate files, or scan an
entire home directory.  Workspace scans are bounded and skip common generated
or dependency directories.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

DESCRIPTOR_NAME = "sfdx-project.json"
DEFAULT_MAX_SCAN_DEPTH = 4
DEFAULT_MAX_CANDIDATES = 32

_IGNORED_DIRECTORY_NAMES = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".sf",
        ".sfdx",
        ".venv",
        ".tox",
        ".idea",
        ".vscode",
        ".cursor",
        ".claude",
        "__pycache__",
        "coverage",
        "dist",
        "build",
        "node_modules",
        "target",
        "vendor",
    }
)


@dataclass(frozen=True)
class PackageDirectory:
    """One package directory declared by ``sfdx-project.json``."""

    declared_path: str
    absolute_path: str
    default: bool
    exists: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProjectDiscovery:
    """Stable result returned by :func:`discover_salesforce_project`."""

    status: str
    mode: str
    project_root: str | None = None
    descriptor_path: str | None = None
    package_directories: tuple[PackageDirectory, ...] = field(default_factory=tuple)
    namespace: str | None = None
    source_api_version: str | None = None
    candidates: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def found(self) -> bool:
        return self.status == "found" and self.project_root is not None

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["found"] = self.found
        return result


@dataclass(frozen=True)
class ComponentMatch:
    """A deterministic local path match for a Salesforce metadata component."""

    path: str
    relative_path: str
    package_directory: str
    line: int | None = None
    column: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ComponentMapping:
    """Result of mapping a metadata component to local project paths."""

    status: str
    component_type: str
    full_name: str
    project_root: str | None
    matches: tuple[ComponentMatch, ...] = field(default_factory=tuple)
    searched_patterns: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _normalise_path(value: str | os.PathLike[str]) -> Path:
    return Path(value).expanduser().resolve(strict=False)


def _is_within(path: Path, parent: Path) -> bool:
    """Return whether ``path`` is inside ``parent`` without requiring existence."""

    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _find_ancestor_project(start: Path) -> Path | None:
    """Find the nearest project root at or above ``start``."""

    current = start
    if current.name == DESCRIPTOR_NAME:
        current = current.parent
    elif current.is_file():
        current = current.parent

    for candidate in (current, *current.parents):
        descriptor = candidate / DESCRIPTOR_NAME
        if descriptor.is_file():
            return candidate
    return None


def _bounded_workspace_scan(
    workspace_root: Path,
    *,
    max_depth: int,
    max_candidates: int,
) -> tuple[Path, ...]:
    """Find project roots below one workspace root with deterministic bounds."""

    if not workspace_root.exists():
        return ()

    ancestor = _find_ancestor_project(workspace_root)
    if ancestor is not None:
        return (ancestor,)

    if not workspace_root.is_dir() or max_depth < 0 or max_candidates < 1:
        return ()

    roots: list[Path] = []
    base_parts = len(workspace_root.parts)

    for current, directory_names, file_names in os.walk(
        workspace_root, topdown=True, followlinks=False
    ):
        current_path = Path(current)
        depth = len(current_path.parts) - base_parts

        directory_names[:] = sorted(
            name
            for name in directory_names
            if name not in _IGNORED_DIRECTORY_NAMES and not name.startswith(".")
        )
        if depth >= max_depth:
            directory_names[:] = []

        if DESCRIPTOR_NAME in file_names:
            roots.append(current_path.resolve(strict=False))
            # A Salesforce project can contain package directories, but nested
            # project roots are unusual and expensive to search.  Stop below a
            # confirmed root; callers can pass another workspace root explicitly.
            directory_names[:] = []
            if len(roots) >= max_candidates:
                break

    return tuple(sorted(set(roots), key=lambda path: str(path).casefold()))


def _string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _load_project(root: Path, *, mode: str) -> ProjectDiscovery:
    descriptor = root / DESCRIPTOR_NAME
    try:
        payload = json.loads(descriptor.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return ProjectDiscovery(
            status="invalid",
            mode=mode,
            candidates=(str(root),),
            warnings=(f"Missing {DESCRIPTOR_NAME}: {descriptor}",),
        )
    except OSError as exc:
        return ProjectDiscovery(
            status="invalid",
            mode=mode,
            candidates=(str(root),),
            warnings=(f"Could not read {descriptor}: {exc}",),
        )
    except json.JSONDecodeError as exc:
        return ProjectDiscovery(
            status="invalid",
            mode=mode,
            candidates=(str(root),),
            warnings=(
                f"Invalid JSON in {descriptor} at line {exc.lineno}, column {exc.colno}",
            ),
        )

    if not isinstance(payload, Mapping):
        return ProjectDiscovery(
            status="invalid",
            mode=mode,
            candidates=(str(root),),
            warnings=(f"{descriptor} must contain a JSON object",),
        )

    warnings: list[str] = []
    package_directories: list[PackageDirectory] = []
    raw_directories = payload.get("packageDirectories", [])

    if raw_directories is None:
        raw_directories = []
    if not isinstance(raw_directories, list):
        warnings.append("packageDirectories must be an array; local mapping is disabled")
        raw_directories = []

    seen_paths: set[Path] = set()
    resolved_root = root.resolve(strict=False)

    for index, item in enumerate(raw_directories):
        if not isinstance(item, Mapping):
            warnings.append(f"packageDirectories[{index}] is not an object and was skipped")
            continue

        declared = item.get("path")
        if not isinstance(declared, str) or not declared.strip():
            warnings.append(
                f"packageDirectories[{index}].path is missing or blank and was skipped"
            )
            continue

        declared = declared.strip()
        absolute = (resolved_root / declared).resolve(strict=False)
        if not _is_within(absolute, resolved_root):
            warnings.append(
                f"packageDirectories[{index}].path escapes the project root and was skipped: "
                f"{declared}"
            )
            continue
        if absolute in seen_paths:
            warnings.append(f"Duplicate package directory was skipped: {declared}")
            continue
        seen_paths.add(absolute)

        exists = absolute.is_dir()
        if not exists:
            warnings.append(f"Package directory does not exist: {declared}")
        package_directories.append(
            PackageDirectory(
                declared_path=declared,
                absolute_path=str(absolute),
                default=bool(item.get("default", False)),
                exists=exists,
            )
        )

    if not package_directories:
        warnings.append(
            "No usable packageDirectories were declared; project discovery succeeded "
            "but component mapping is unavailable"
        )

    return ProjectDiscovery(
        status="found",
        mode=mode,
        project_root=str(resolved_root),
        descriptor_path=str(descriptor.resolve(strict=False)),
        package_directories=tuple(package_directories),
        namespace=_string_or_none(payload.get("namespace")),
        source_api_version=_string_or_none(payload.get("sourceApiVersion")),
        candidates=(str(resolved_root),),
        warnings=tuple(warnings),
    )


def discover_salesforce_project(
    *,
    explicit_path: str | os.PathLike[str] | None = None,
    cwd: str | os.PathLike[str] | None = None,
    workspace_paths: Sequence[str | os.PathLike[str]] | None = None,
    max_workspace_depth: int = DEFAULT_MAX_SCAN_DEPTH,
    max_candidates: int = DEFAULT_MAX_CANDIDATES,
) -> ProjectDiscovery:
    """Discover an optional Salesforce DX project.

    Discovery order is intentionally strict:

    1. ``explicit_path`` when supplied.  An invalid explicit path is returned as
       ``invalid`` rather than silently falling back to another project.
    2. The nearest project root at or above ``cwd``.
    3. A bounded scan of the supplied ``workspace_paths``.
    4. ``standalone`` when no project is present.

    Multiple workspace projects return ``ambiguous``.  The caller must ask the
    user to choose; selecting one arbitrarily could map evidence to the wrong
    customer or package repository.
    """

    if explicit_path is not None:
        requested = _normalise_path(explicit_path)
        if not requested.exists():
            return ProjectDiscovery(
                status="invalid",
                mode="explicit",
                candidates=(str(requested),),
                warnings=(f"Explicit project path does not exist: {requested}",),
            )
        root = _find_ancestor_project(requested)
        if root is None:
            return ProjectDiscovery(
                status="invalid",
                mode="explicit",
                candidates=(str(requested),),
                warnings=(
                    f"No {DESCRIPTOR_NAME} exists at or above the explicit path: "
                    f"{requested}",
                ),
            )
        return _load_project(root, mode="explicit")

    current = _normalise_path(cwd if cwd is not None else Path.cwd())
    current_root = _find_ancestor_project(current)
    if current_root is not None:
        return _load_project(current_root, mode="cwd")

    roots: set[Path] = set()
    missing_workspaces: list[str] = []
    for workspace in workspace_paths or ():
        candidate = _normalise_path(workspace)
        if not candidate.exists():
            missing_workspaces.append(str(candidate))
            continue
        roots.update(
            _bounded_workspace_scan(
                candidate,
                max_depth=max_workspace_depth,
                max_candidates=max_candidates,
            )
        )
        if len(roots) >= max_candidates:
            break

    ordered = tuple(sorted(roots, key=lambda path: str(path).casefold()))
    if len(ordered) == 1:
        result = _load_project(ordered[0], mode="workspace")
        if missing_workspaces:
            return replace(
                result,
                warnings=result.warnings
                + tuple(
                    f"Workspace path does not exist: {path}"
                    for path in missing_workspaces
                ),
            )
        return result

    if len(ordered) > 1:
        warnings = [
            "Multiple Salesforce DX projects were found; provide an explicit project path"
        ]
        if len(ordered) >= max_candidates:
            warnings.append(
                f"Candidate limit {max_candidates} was reached; additional projects may exist"
            )
        warnings.extend(f"Workspace path does not exist: {path}" for path in missing_workspaces)
        return ProjectDiscovery(
            status="ambiguous",
            mode="workspace",
            candidates=tuple(str(path) for path in ordered),
            warnings=tuple(warnings),
        )

    warnings = tuple(f"Workspace path does not exist: {path}" for path in missing_workspaces)
    return ProjectDiscovery(
        status="standalone",
        mode="standalone",
        warnings=warnings,
    )


def _validate_full_name(full_name: str) -> str | None:
    value = full_name.strip()
    if not value:
        return "Component full name must not be blank"
    if "\x00" in value or "/" in value or "\\" in value:
        return "Component full name contains a path separator or NUL byte"
    dot_parts = value.split(".")
    if value in {".", ".."} or any(part == ".." for part in dot_parts):
        return "Component full name contains an unsafe parent traversal segment"
    if any(part == "" for part in dot_parts):
        return "Component full name contains an empty dot-separated segment"
    return None


def _split_parent_child(full_name: str, component_type: str) -> tuple[str, str] | None:
    if "." not in full_name:
        return None
    parent, child = full_name.split(".", 1)
    if not parent or not child:
        return None
    if _validate_full_name(parent) or _validate_full_name(child):
        return None
    return parent, child


def _component_patterns(component_type: str, full_name: str) -> tuple[str, ...]:
    normalised = "".join(character for character in component_type.casefold() if character.isalnum())

    direct: dict[str, tuple[str, ...]] = {
        "apexclass": (
            f"classes/{full_name}.cls",
            f"classes/{full_name}.cls-meta.xml",
        ),
        "apextrigger": (
            f"triggers/{full_name}.trigger",
            f"triggers/{full_name}.trigger-meta.xml",
        ),
        "lightningcomponentbundle": (f"lwc/{full_name}",),
        "auradefinitionbundle": (f"aura/{full_name}",),
        "flow": (
            f"flows/{full_name}.flow-meta.xml",
            f"flows/{full_name}.flow",
        ),
        "customobject": (f"objects/{full_name}/{full_name}.object-meta.xml",),
        "permissionset": (f"permissionsets/{full_name}.permissionset-meta.xml",),
        "permissionsetgroup": (
            f"permissionsetgroups/{full_name}.permissionsetgroup-meta.xml",
        ),
        "profile": (f"profiles/{full_name}.profile-meta.xml",),
        "layout": (f"layouts/{full_name}.layout-meta.xml",),
        "flexipage": (f"flexipages/{full_name}.flexipage-meta.xml",),
        "staticresource": (
            f"staticresources/{full_name}.resource-meta.xml",
            f"staticresources/{full_name}.resource",
            f"staticresources/{full_name}",
        ),
        "custommetadata": (f"customMetadata/{full_name}.md-meta.xml",),
        "namedcredential": (
            f"namedCredentials/{full_name}.namedCredential-meta.xml",
        ),
        "externalcredential": (
            f"externalCredentials/{full_name}.externalCredential-meta.xml",
        ),
    }
    if normalised in direct:
        return direct[normalised]

    parent_child = _split_parent_child(full_name, component_type)
    if parent_child is None:
        return ()
    parent, child = parent_child

    nested: dict[str, str] = {
        "customfield": f"objects/{parent}/fields/{child}.field-meta.xml",
        "validationrule": (
            f"objects/{parent}/validationRules/{child}.validationRule-meta.xml"
        ),
        "recordtype": f"objects/{parent}/recordTypes/{child}.recordType-meta.xml",
        "businessprocess": (
            f"objects/{parent}/businessProcesses/{child}.businessProcess-meta.xml"
        ),
        "weblink": f"objects/{parent}/webLinks/{child}.webLink-meta.xml",
        "listview": f"objects/{parent}/listViews/{child}.listView-meta.xml",
        "compactlayout": (
            f"objects/{parent}/compactLayouts/{child}.compactLayout-meta.xml"
        ),
        "fieldset": f"objects/{parent}/fieldSets/{child}.fieldSet-meta.xml",
        "sharingreason": (
            f"objects/{parent}/sharingReasons/{child}.sharingReason-meta.xml"
        ),
    }
    relative = nested.get(normalised)
    return (relative,) if relative else ()


def map_component_to_local_paths(
    project: ProjectDiscovery,
    *,
    component_type: str,
    full_name: str,
    line: int | None = None,
    column: int | None = None,
) -> ComponentMapping:
    """Map a metadata component to deterministic paths in a discovered project."""

    component_type = component_type.strip()
    full_name = full_name.strip()
    unsafe = _validate_full_name(full_name)
    if unsafe:
        return ComponentMapping(
            status="invalid_component",
            component_type=component_type,
            full_name=full_name,
            project_root=project.project_root,
            warnings=(unsafe,),
        )

    if not project.found:
        return ComponentMapping(
            status="standalone" if project.status == "standalone" else "project_unavailable",
            component_type=component_type,
            full_name=full_name,
            project_root=project.project_root,
            warnings=(
                "Local component mapping was skipped because no unambiguous valid "
                "Salesforce DX project is available",
            ),
        )

    patterns = _component_patterns(component_type, full_name)
    if not patterns:
        return ComponentMapping(
            status="unsupported_type",
            component_type=component_type,
            full_name=full_name,
            project_root=project.project_root,
            warnings=(
                f"No deterministic local path rule is defined for metadata type "
                f"{component_type or '<blank>'}",
            ),
        )

    if line is not None and line < 1:
        return ComponentMapping(
            status="invalid_component",
            component_type=component_type,
            full_name=full_name,
            project_root=project.project_root,
            warnings=("Line number must be a positive integer when supplied",),
        )
    if column is not None and column < 1:
        return ComponentMapping(
            status="invalid_component",
            component_type=component_type,
            full_name=full_name,
            project_root=project.project_root,
            warnings=("Column number must be a positive integer when supplied",),
        )

    project_root = Path(project.project_root)
    matches: list[ComponentMatch] = []
    for package in project.package_directories:
        if not package.exists:
            continue
        package_root = Path(package.absolute_path)
        source_roots = [package_root]
        conventional_source_root = package_root / "main" / "default"
        if conventional_source_root.is_dir():
            source_roots.insert(0, conventional_source_root)

        for source_root in source_roots:
            for pattern in patterns:
                candidate = (source_root / pattern).resolve(strict=False)
                if not _is_within(candidate, package_root):
                    continue
                if candidate.exists():
                    matches.append(
                        ComponentMatch(
                            path=str(candidate),
                            relative_path=str(candidate.relative_to(project_root)),
                            package_directory=package.declared_path,
                            line=line,
                            column=column,
                        )
                    )

    # Deduplicate while preserving deterministic package/pattern order.
    deduplicated: list[ComponentMatch] = []
    seen: set[str] = set()
    for match in matches:
        if match.path in seen:
            continue
        seen.add(match.path)
        deduplicated.append(match)

    return ComponentMapping(
        status="mapped" if deduplicated else "not_found",
        component_type=component_type,
        full_name=full_name,
        project_root=project.project_root,
        matches=tuple(deduplicated),
        searched_patterns=patterns,
        warnings=()
        if deduplicated
        else (
            "The Salesforce DX project was found, but no matching local metadata path exists",
        ),
    )


def discovery_from_mapping(payload: Mapping[str, Any]) -> ProjectDiscovery:
    """Build a discovery object from a JSON-like mapping.

    This helper is intentionally strict enough for CLI/subagent handoffs while
    remaining backward-compatible with absent optional fields.
    """

    raw_packages = payload.get("package_directories", [])
    packages = tuple(
        PackageDirectory(
            declared_path=str(item["declared_path"]),
            absolute_path=str(item["absolute_path"]),
            default=bool(item.get("default", False)),
            exists=bool(item.get("exists", False)),
        )
        for item in raw_packages
        if isinstance(item, Mapping)
        and "declared_path" in item
        and "absolute_path" in item
    )
    return ProjectDiscovery(
        status=str(payload.get("status", "invalid")),
        mode=str(payload.get("mode", "unknown")),
        project_root=_string_or_none(payload.get("project_root")),
        descriptor_path=_string_or_none(payload.get("descriptor_path")),
        package_directories=packages,
        namespace=_string_or_none(payload.get("namespace")),
        source_api_version=_string_or_none(payload.get("source_api_version")),
        candidates=tuple(str(value) for value in payload.get("candidates", [])),
        warnings=tuple(str(value) for value in payload.get("warnings", [])),
    )
