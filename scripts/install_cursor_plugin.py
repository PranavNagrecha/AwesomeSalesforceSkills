#!/usr/bin/env python3
"""Install or uninstall the native SfSkills Cursor plugin locally.

Usage:
  python3 scripts/install_cursor_plugin.py --link
  python3 scripts/install_cursor_plugin.py --link --dry-run
  python3 scripts/install_cursor_plugin.py --uninstall
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_NAME = "awesome-salesforce-skills"
DIST = ROOT / "dist" / "cursor" / PLUGIN_NAME


def default_plugin_parent() -> Path:
    """Cursor's local (non-Marketplace) plugin directory.

    Current Cursor docs: ``~/.cursor/plugins/local/<plugin-name>``.
    Override with ``SFSKILLS_CURSOR_PLUGIN_DIR`` for older app versions.
    """
    return Path.home() / ".cursor" / "plugins" / "local"


def legacy_plugin_parent() -> Path:
    """Pre-review default (``~/.cursor/plugins`` without ``local/``)."""
    return Path.home() / ".cursor" / "plugins"


def detect_plugin_parent() -> Path:
    override = os.environ.get("SFSKILLS_CURSOR_PLUGIN_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return default_plugin_parent()


def install_path(parent: Path) -> Path:
    return parent / PLUGIN_NAME


def _is_our_install(target: Path) -> bool:
    manifest = target / ".cursor-plugin" / "plugin.json"
    if not manifest.is_file():
        return False
    try:
        name = json.loads(manifest.read_text(encoding="utf-8")).get("name")
    except json.JSONDecodeError:
        return False
    return name == PLUGIN_NAME


def build() -> None:
    from subprocess import check_call

    check_call([sys.executable, str(ROOT / "scripts" / "build_cursor_plugin.py")])


def _remove_install(target: Path) -> None:
    if target.is_symlink() or target.is_file():
        target.unlink()
    elif target.is_dir():
        shutil.rmtree(target)


def cmd_link(*, dry_run: bool, copy: bool) -> int:
    if not dry_run:
        build()
    elif not DIST.is_dir():
        print("ERROR: dist package missing; run without --dry-run to build", file=sys.stderr)
        return 1
    parent = detect_plugin_parent()
    target = install_path(parent)
    print(f"Repo:    {ROOT}")
    print(f"Built:   {DIST}")
    print(f"Install: {target}")
    if target.exists() or target.is_symlink():
        if not _is_our_install(target):
            print(
                "ERROR: refusing to replace an unrelated install at "
                f"{target}. Uninstall it yourself or set SFSKILLS_CURSOR_PLUGIN_DIR.",
                file=sys.stderr,
            )
            return 2
        print("Existing SfSkills plugin install will be replaced.")
    if dry_run:
        print("Dry-run: no files changed.")
        _print_after()
        return 0
    parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink() or target.exists():
        _remove_install(target)
    legacy = install_path(legacy_plugin_parent())
    if legacy != target and (legacy.exists() or legacy.is_symlink()) and _is_our_install(legacy):
        print(f"Removing legacy install at {legacy}")
        if not dry_run:
            _remove_install(legacy)
    if copy:
        shutil.copytree(DIST, target)
        pointer = {"repo_root": str(ROOT)}
        (target / "repo-root.json").write_text(json.dumps(pointer, indent=2) + "\n", encoding="utf-8")
        print("Copied plugin (wrote repo-root.json).")
    else:
        target.symlink_to(DIST, target_is_directory=True)
        pointer = {"repo_root": str(ROOT)}
        (DIST / "repo-root.json").write_text(json.dumps(pointer, indent=2) + "\n", encoding="utf-8")
        print("Linked plugin.")
    _print_after()
    return 0


def cmd_uninstall() -> int:
    removed = 0
    candidates = [install_path(detect_plugin_parent()), install_path(legacy_plugin_parent())]
    seen: set[Path] = set()
    for target in candidates:
        resolved = target
        if resolved in seen:
            continue
        seen.add(resolved)
        if not target.exists() and not target.is_symlink():
            continue
        if not _is_our_install(target):
            print(f"ERROR: {target} is not this plugin. Refusing to delete.", file=sys.stderr)
            return 2
        _remove_install(target)
        print(f"Removed {target}")
        removed += 1
    if removed == 0:
        print(f"Nothing installed at {install_path(detect_plugin_parent())}")
        return 0
    print("Reload Cursor.")
    return 0


def _print_after() -> None:
    print()
    print("Next:")
    print("  1. Reload Cursor (Developer: Reload Window).")
    print("  2. Confirm Customize / plugins lists awesome-salesforce-skills")
    print("     (local plugins live under ~/.cursor/plugins/local/).")
    print("  3. Run /sfskills-doctor then try /triage-deployment on a fixture.")
    print("Uninstall: python3 scripts/install_cursor_plugin.py --uninstall")
    print()
    print("This helper does not publish to the Cursor Marketplace.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Install the SfSkills Cursor plugin locally")
    parser.add_argument(
        "--link",
        action="store_true",
        help="copy dist into ~/.cursor/plugins/local (Cursor-loadable install)",
    )
    parser.add_argument("--copy", action="store_true", help="same as --link")
    parser.add_argument(
        "--symlink",
        action="store_true",
        help="symlink dist; Cursor may reject targets outside ~/.cursor/plugins/local",
    )
    parser.add_argument("--uninstall", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--check", action="store_true", help="print paths and overwrite protection only")
    args = parser.parse_args()
    if args.check:
        parent = detect_plugin_parent()
        target = install_path(parent)
        print(
            json.dumps(
                {
                    "parent": str(parent),
                    "target": str(target),
                    "dist": str(DIST),
                    "docs_path": "~/.cursor/plugins/local/<plugin-name>",
                },
                indent=2,
            )
        )
        return 0
    if args.uninstall:
        return cmd_uninstall()
    if args.symlink:
        return cmd_link(dry_run=args.dry_run, copy=False)
    if args.link or args.copy:
        return cmd_link(dry_run=args.dry_run, copy=True)
    parser.error("specify --link, --copy, --symlink, --uninstall, or --check")


if __name__ == "__main__":
    raise SystemExit(main())
