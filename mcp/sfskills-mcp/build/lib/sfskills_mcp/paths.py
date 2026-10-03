"""Repo-root + key artifact path resolution for the SfSkills MCP server.

Resolution order for the repo root:

1. ``SFSKILLS_REPO_ROOT`` environment variable (explicit override).
2. Walk upward from this file until a directory containing
   ``registry/skills.json`` is found (development install).
3. ``~/.cache/sfskills-mcp/current`` if populated by ``sfskills-mcp-init``
   (PyPI install path).
4. Override the cache location via ``SFSKILLS_CACHE_DIR``.

Raising a ``RuntimeError`` early with an actionable message is preferred over
silently returning wrong paths — MCP clients will surface the error to the user.
"""

from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path


REGISTRY_SENTINEL = Path("registry") / "skills.json"
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "sfskills-mcp"


class RepoRootNotFoundError(RuntimeError):
    """Raised when the SfSkills repo root cannot be located."""


def _cache_root() -> Path:
    override = os.environ.get("SFSKILLS_CACHE_DIR")
    return Path(override).expanduser() if override else DEFAULT_CACHE_DIR


@lru_cache(maxsize=1)
def repo_root() -> Path:
    env_value = os.environ.get("SFSKILLS_REPO_ROOT")
    if env_value:
        candidate = Path(env_value).expanduser().resolve()
        if not (candidate / REGISTRY_SENTINEL).exists():
            raise RepoRootNotFoundError(
                f"SFSKILLS_REPO_ROOT is set to {candidate} but "
                f"{REGISTRY_SENTINEL} does not exist there."
            )
        return candidate

    # Walk upward from this file (development install — sfskills_mcp lives
    # inside the repo itself).
    here = Path(__file__).resolve()
    for parent in (here, *here.parents):
        if (parent / REGISTRY_SENTINEL).exists():
            return parent

    # PyPI install path: sfskills-mcp-init populated the cache.
    cache_current = _cache_root() / "current"
    if cache_current.exists():
        # ``current`` may be a symlink (POSIX) or a pointer file
        # (Windows fallback).
        if cache_current.is_symlink() or cache_current.is_dir():
            resolved = cache_current.resolve()
        else:
            try:
                resolved = Path(cache_current.read_text(encoding="utf-8").strip()).resolve()
            except OSError:
                resolved = None  # type: ignore[assignment]
        if resolved and (resolved / REGISTRY_SENTINEL).exists():
            return resolved

    raise RepoRootNotFoundError(
        "Could not locate the SfSkills data root. Three options:\n"
        "  1. Set SFSKILLS_REPO_ROOT to your SfSkills checkout (developer install).\n"
        "  2. Run `sfskills-mcp-init` to download the registry into "
        f"{_cache_root()} (PyPI install).\n"
        "  3. If you ran sfskills-mcp-init already, set SFSKILLS_CACHE_DIR "
        "to its output directory."
    )


def registry_skills_json() -> Path:
    return repo_root() / "registry" / "skills.json"


def registry_skill_dir() -> Path:
    return repo_root() / "registry" / "skills"


def skills_dir() -> Path:
    return repo_root() / "skills"


def lexical_index_path() -> Path:
    return repo_root() / "vector_index" / "lexical.sqlite"


def chunks_jsonl_path() -> Path:
    return repo_root() / "vector_index" / "chunks.jsonl"


def ensure_pipelines_on_path() -> None:
    """Expose the in-repo ``pipelines`` package to ``import`` statements."""
    root = str(repo_root())
    if root not in sys.path:
        sys.path.insert(0, root)
