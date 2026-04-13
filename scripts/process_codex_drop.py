#!/usr/bin/env python3
"""
Process Codex-generated skill drop files.

Usage:
    python3 scripts/process_codex_drop.py                  # process all pending drops
    python3 scripts/process_codex_drop.py <file.md>        # process a specific drop file

Drop files live in _codex_drops/ and must use the format:
    === FILE: skills/<domain>/<skill-name>/path/to/file.md ===
    <file content>

    === FILE: skills/<domain>/<skill-name>/references/examples.md ===
    <file content>

After writing all files the script:
  1. Scaffolds any missing skill structure via new_skill.py
  2. Runs skill_sync.py for each skill found
  3. Adds query fixtures if declared in the drop
  4. Moves processed drop files to _codex_drops/processed/
  5. Reports success/failure per skill
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
DROP_DIR = REPO_ROOT / "_codex_drops"
PROCESSED_DIR = DROP_DIR / "processed"
FIXTURE_FILE = REPO_ROOT / "vector_index" / "query-fixtures.json"

# Regex to split on === FILE: <path> === headers
FILE_HEADER_RE = re.compile(r"^=== FILE: (.+?) ===$", re.MULTILINE)

# Regex to detect query fixture blocks in drops
FIXTURE_RE = re.compile(
    r"QUERY_FIXTURE:\s*(\{[^}]+\})", re.DOTALL
)


def parse_drop(text: str) -> dict[str, str]:
    """Return {relative_path: content} from a drop file."""
    parts = FILE_HEADER_RE.split(text)
    # parts alternates: [pre-text, path1, content1, path2, content2, ...]
    files: dict[str, str] = {}
    it = iter(parts[1:])  # skip pre-text
    for path, content in zip(it, it):
        files[path.strip()] = content.strip()
    return files


def extract_skills(files: dict[str, str]) -> list[tuple[str, str]]:
    """Extract (domain, skill-name) pairs from file paths."""
    seen: list[tuple[str, str]] = []
    for path in files:
        # skills/<domain>/<skill-name>/...
        m = re.match(r"skills/([^/]+)/([^/]+)/", path)
        if m:
            pair = (m.group(1), m.group(2))
            if pair not in seen:
                seen.append(pair)
    return seen


def scaffold_if_needed(domain: str, skill_name: str) -> bool:
    """Scaffold the skill if its directory does not exist yet."""
    skill_dir = REPO_ROOT / "skills" / domain / skill_name
    if skill_dir.exists():
        return True  # already there
    print(f"  Scaffolding {domain}/{skill_name} ...")
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "new_skill.py"), domain, skill_name],
        cwd=str(REPO_ROOT),
        input="y\n",
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  ERROR scaffolding: {result.stderr.strip()}")
        return False
    return True


def write_files(files: dict[str, str]) -> list[str]:
    """Write all file contents to disk. Returns list of written paths."""
    written = []
    for rel_path, content in files.items():
        abs_path = REPO_ROOT / rel_path
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text(content + "\n", encoding="utf-8")
        written.append(rel_path)
        print(f"  wrote  {rel_path}")
    return written


def sync_skill(domain: str, skill_name: str) -> bool:
    """Run skill_sync.py for one skill."""
    skill_path = f"skills/{domain}/{skill_name}"
    print(f"  syncing {skill_path} ...")
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "skill_sync.py"), "--skill", skill_path],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  SYNC ERROR:\n{result.stdout}\n{result.stderr}")
        return False
    print(f"  sync OK")
    return True


def add_fixture(domain: str, skill_name: str, query: str | None = None) -> None:
    """Add a query fixture entry if not already present."""
    if not FIXTURE_FILE.exists():
        return
    with open(FIXTURE_FILE, encoding="utf-8") as f:
        data = json.load(f)

    expected = f"{domain}/{skill_name}"
    existing = [q.get("expected_skill") for q in data.get("queries", [])]
    if expected in existing:
        return  # already has a fixture

    # Build a default query from the skill name if none provided
    if not query:
        readable = skill_name.replace("-", " ")
        query = f"how do I work with {readable} in Salesforce"

    data.setdefault("queries", []).append(
        {
            "query": query,
            "domain": domain,
            "expected_skill": expected,
            "top_k": 3,
        }
    )
    with open(FIXTURE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"  added fixture for {expected}")


def process_drop_file(drop_path: Path) -> bool:
    """Process one drop file. Returns True if all skills synced cleanly."""
    print(f"\n{'='*60}")
    print(f"Processing: {drop_path.name}")
    print(f"{'='*60}")

    text = drop_path.read_text(encoding="utf-8")
    files = parse_drop(text)

    if not files:
        print("  No FILE blocks found — skipping.")
        return False

    skills = extract_skills(files)
    print(f"  Skills detected: {[f'{d}/{s}' for d, s in skills]}")

    # Scaffold any new skills
    for domain, skill_name in skills:
        if not scaffold_if_needed(domain, skill_name):
            print(f"  BLOCKED: could not scaffold {domain}/{skill_name}")
            return False

    # Write all files
    write_files(files)

    # Sync each skill and add fixtures
    all_ok = True
    for domain, skill_name in skills:
        ok = sync_skill(domain, skill_name)
        if ok:
            add_fixture(domain, skill_name)
        else:
            all_ok = False

    return all_ok


def move_to_processed(drop_path: Path, success: bool) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    suffix = "" if success else ".FAILED"
    dest = PROCESSED_DIR / (drop_path.name + suffix)
    shutil.move(str(drop_path), str(dest))
    print(f"  moved to processed/{dest.name}")


def main() -> int:
    if len(sys.argv) > 1:
        targets = [Path(sys.argv[1])]
    else:
        targets = sorted(
            p for p in DROP_DIR.glob("*.md")
            if p.name != "README.md"
        )

    if not targets:
        print("No drop files found in _codex_drops/")
        return 0

    overall_ok = True
    for drop_path in targets:
        if not drop_path.exists():
            print(f"File not found: {drop_path}")
            overall_ok = False
            continue
        success = process_drop_file(drop_path)
        move_to_processed(drop_path, success)
        if not success:
            overall_ok = False

    print("\nDone. Run `python3 scripts/validate_repo.py` to confirm clean state.")
    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
