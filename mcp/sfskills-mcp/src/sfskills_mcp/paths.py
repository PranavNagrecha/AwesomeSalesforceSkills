"""Repo-root + key artifact path resolution for the SfSkills MCP server.

Resolution order for the repo root:

1. ``SFSKILLS_REPO_ROOT`` environment variable (explicit override).
2. Walk upward from this file until a directory containing
   ``registry/skills.json`` is found.

Raising a ``RuntimeError`` early with an actionable message is preferred over
silently returning wrong paths — MCP clients will surface the error to the user.
"""

from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path


REGISTRY_SENTINEL = Path("registry") / "skills.json"


class RepoRootNotFoundError(RuntimeError):
    """Raised when the SfSkills repo root cannot be located."""


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

    here = Path(__file__).resolve()
    for parent in (here, *here.parents):
        if (parent / REGISTRY_SENTINEL).exists():
            return parent

    raise RepoRootNotFoundError(
        "Could not locate the SfSkills repo root. Set the SFSKILLS_REPO_ROOT "
        "environment variable to the absolute path of your SfSkills checkout."
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
