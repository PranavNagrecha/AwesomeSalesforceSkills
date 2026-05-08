"""``sfskills-mcp-init`` — one-time data fetcher for the PyPI install path.

The wheel ships small (~50 KB of Python) and intentionally does NOT bundle
the 160 MB registry + lexical index. This script downloads the latest
artefact bundle from a GitHub Release and caches it under
``~/.cache/sfskills-mcp/``, after which the server resolves
``SFSKILLS_REPO_ROOT`` to the cache directory automatically.

Usage:

    sfskills-mcp-init                 # download latest
    sfskills-mcp-init --force         # re-download even if cache populated
    sfskills-mcp-init --release vX.Y  # pin to a specific release tag

The script is intentionally narrow:
  - One HTTPS GET to GitHub's release-asset URL (no API key required).
  - Atomic extract into ``~/.cache/sfskills-mcp/<release>/``.
  - Updates ``~/.cache/sfskills-mcp/current`` symlink so the server can
    resolve a stable path regardless of which release is active.

Failure cases (no network, GitHub down, bad signature) surface a clear
error and exit non-zero. The user can always fall back to cloning the
repo and setting ``SFSKILLS_REPO_ROOT`` manually.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
from pathlib import Path


CACHE_ENV_VAR = "SFSKILLS_CACHE_DIR"
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "sfskills-mcp"
GITHUB_RELEASES = "https://github.com/PranavNagrecha/AwesomeSalesforceSkills/releases"
ASSET_NAME = "sfskills-data.tar.gz"


def _cache_dir() -> Path:
    override = os.environ.get(CACHE_ENV_VAR)
    return Path(override).expanduser() if override else DEFAULT_CACHE_DIR


def _release_url(release_tag: str | None) -> str:
    if release_tag:
        return f"{GITHUB_RELEASES}/download/{release_tag}/{ASSET_NAME}"
    return f"{GITHUB_RELEASES}/latest/download/{ASSET_NAME}"


def _download(url: str, dest: Path) -> None:
    """Stream-download ``url`` to ``dest``. Atomic via temp + rename."""
    print(f"sfskills-mcp-init: downloading {url}")
    tmp = dest.with_suffix(".tmp")
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:  # noqa: S310 — fixed GitHub URL
            total = int(resp.headers.get("Content-Length") or 0)
            chunk_size = 1024 * 1024
            with tmp.open("wb") as out:
                downloaded = 0
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    out.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = 100.0 * downloaded / total
                        print(
                            f"\r  {downloaded / 1_000_000:.1f} MB / "
                            f"{total / 1_000_000:.1f} MB ({pct:.0f}%)",
                            end="",
                            flush=True,
                        )
                print()
        tmp.replace(dest)
    except urllib.error.HTTPError as e:
        if tmp.exists():
            tmp.unlink()
        raise SystemExit(
            f"sfskills-mcp-init: HTTP {e.code} fetching {url}\n"
            "  Verify the release tag exists: "
            f"{GITHUB_RELEASES}"
        )
    except urllib.error.URLError as e:
        if tmp.exists():
            tmp.unlink()
        raise SystemExit(
            f"sfskills-mcp-init: network error: {e.reason}\n"
            "  Check your internet connection or proxy settings."
        )


def _extract(archive: Path, target: Path) -> None:
    """Extract ``sfskills-data.tar.gz`` into ``target/``. Strips the top
    directory if the tarball wraps everything in a single root folder."""
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    print(f"sfskills-mcp-init: extracting into {target}")
    with tarfile.open(archive, "r:gz") as tar:
        members = tar.getmembers()
        # Detect single-root pattern.
        roots = {m.name.split("/", 1)[0] for m in members}
        strip_prefix = roots.pop() + "/" if len(roots) == 1 else None
        for member in members:
            if strip_prefix and member.name.startswith(strip_prefix):
                member.name = member.name[len(strip_prefix):]
                if not member.name:
                    continue
            # Refuse path traversal in tarball entries.
            if member.name.startswith(("/", "..")) or "/.." in member.name:
                continue
            tar.extract(member, target, filter="data")


def _link_current(target: Path, cache: Path) -> None:
    """Point ``cache/current`` at ``target``. Symlink on POSIX, junction
    fallback (a plain copy of the path string) on Windows."""
    current = cache / "current"
    if current.exists() or current.is_symlink():
        if current.is_symlink() or current.is_dir():
            current.unlink() if current.is_symlink() else shutil.rmtree(current)
        else:
            current.unlink()
    try:
        current.symlink_to(target, target_is_directory=True)
    except (OSError, NotImplementedError):
        # Windows without symlink permission — write a pointer file instead.
        with current.open("w", encoding="utf-8") as fh:
            fh.write(str(target))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sfskills-mcp-init",
        description=(
            "Download the SfSkills registry + lexical index into "
            f"{DEFAULT_CACHE_DIR}. Run once after `pip install sfskills-mcp`."
        ),
    )
    parser.add_argument(
        "--release",
        default=None,
        help="Pin to a specific release tag (default: latest)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if the cache is already populated",
    )
    parser.add_argument(
        "--cache-dir",
        default=None,
        help=f"Override the cache directory (default: {DEFAULT_CACHE_DIR}). "
             f"Equivalent to setting {CACHE_ENV_VAR}.",
    )
    args = parser.parse_args(argv)

    cache = Path(args.cache_dir).expanduser() if args.cache_dir else _cache_dir()
    cache.mkdir(parents=True, exist_ok=True)
    release_label = args.release or "latest"
    target = cache / release_label

    if target.exists() and not args.force:
        print(
            f"sfskills-mcp-init: cache already populated at {target}\n"
            "  Pass --force to re-download."
        )
        _link_current(target, cache)
        _print_setup(cache)
        return 0

    archive = cache / ASSET_NAME
    _download(_release_url(args.release), archive)
    _extract(archive, target)
    archive.unlink(missing_ok=True)
    _link_current(target, cache)
    _print_setup(cache)
    return 0


def _print_setup(cache: Path) -> None:
    current = cache / "current"
    print()
    print("sfskills-mcp-init: done.")
    print()
    print("Set this in your MCP client config (or shell environment):")
    print(f"  SFSKILLS_REPO_ROOT={current}")
    print()
    print("Then start the server:")
    print("  sfskills-mcp")


if __name__ == "__main__":
    sys.exit(main())
