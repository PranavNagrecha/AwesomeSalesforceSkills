#!/usr/bin/env python3
"""Build SKILL-level embeddings (one vector per skill, ~1000 vectors).

The chunk-level embedding pipeline in pipelines/embedding_backends.py encodes
all 126K chunks of the corpus — that takes ~3 hours of CPU on M-series. For
retrieval the skill is the right granularity anyway: the user is asking for
"which skill applies", not "which paragraph of which skill". One vector per
skill, encoded from a curated summary text (name + tags + description +
first 5 triggers), gives the same retrieval signal in 1/100th the time.

Output: vector_index/skill_embeddings.jsonl (one JSON per line)
    {"skill_id": "apex/foo", "backend": "fastembed", "dimension": 384,
     "content_hash": "...", "vector": [...], "summary_text": "..."}

Usage:
    python3 scripts/build_skill_embeddings.py
    python3 scripts/build_skill_embeddings.py --force   # ignore cache

Reuses pipelines.embedding_backends so the model singleton + content-hash
cache work the same way as chunk-level embeddings.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _read_skill_frontmatter(skill_md: Path) -> dict:
    """Quick YAML-ish frontmatter parse for the fields we care about.

    Only handles the subset we need: scalar strings, scalar lists. Uses
    PyYAML if available, else a minimal fallback parser.
    """
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    fm = text[4:end]
    try:
        import yaml  # type: ignore[import-not-found]
        loaded = yaml.safe_load(fm) or {}
        return loaded if isinstance(loaded, dict) else {}
    except ImportError:
        pass
    # Minimal fallback: scalar strings + simple `- "..."` lists.
    out: dict = {}
    current_key: str | None = None
    current_list: list | None = None
    for line in fm.splitlines():
        if not line.strip():
            continue
        m = re.match(r"^([a-zA-Z_][\w-]*):\s*(.*)$", line)
        if m and not line.startswith(" "):
            if current_key and current_list is not None:
                out[current_key] = current_list
            current_key = m.group(1)
            value = m.group(2).strip()
            if value:
                # Strip optional quotes
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                out[current_key] = value
                current_key = None
                current_list = None
            else:
                current_list = []
        elif line.lstrip().startswith("- "):
            if current_list is None:
                current_list = []
            item = line.lstrip()[2:].strip()
            if item.startswith('"') and item.endswith('"'):
                item = item[1:-1]
            current_list.append(item)
    if current_key and current_list is not None:
        out[current_key] = current_list
    return out


def _build_summary_text(skill_id: str, fm: dict) -> str:
    """Compose the text a skill embeds against.

    Order chosen so the most discriminative tokens come first (some encoders
    weight earlier tokens slightly higher even with positional embeddings):
      1. Skill id (slug) — explicit name match
      2. Tags — short keyword bursts
      3. Description — full sentence context
      4. First 5 triggers — practitioner phrasings
    """
    parts: list[str] = []
    parts.append(skill_id.replace("/", " ").replace("-", " "))
    name = fm.get("name", "")
    if name:
        parts.append(str(name).replace("-", " "))
    tags = fm.get("tags", [])
    if isinstance(tags, list):
        parts.append(" ".join(str(t).replace("-", " ") for t in tags))
    desc = fm.get("description", "")
    if desc:
        parts.append(str(desc))
    triggers = fm.get("triggers", [])
    if isinstance(triggers, list):
        parts.append(" ".join(str(t) for t in triggers[:5]))
    return "  ".join(p for p in parts if p)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--force", action="store_true", help="Ignore content-hash cache, re-encode every skill.")
    p.add_argument("--out", default=str(REPO / "vector_index" / "skill_embeddings.jsonl"))
    args = p.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Cache: existing embeddings keyed by (skill_id, content_hash)
    cache: dict[tuple[str, str], dict] = {}
    if not args.force and out_path.exists():
        for line in out_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            sid = item.get("skill_id")
            ch = item.get("content_hash")
            if sid and ch:
                cache[(sid, ch)] = item

    # Walk skills/
    skills_root = REPO / "skills"
    skill_summaries: list[tuple[str, str, str]] = []  # (skill_id, summary, content_hash)
    for skill_md in sorted(skills_root.rglob("SKILL.md")):
        skill_id = "/".join(skill_md.parent.relative_to(skills_root).parts)
        fm = _read_skill_frontmatter(skill_md)
        summary = _build_summary_text(skill_id, fm)
        if not summary:
            continue
        skill_summaries.append((skill_id, summary, _content_hash(summary)))

    print(f"discovered {len(skill_summaries)} skills", file=sys.stderr)

    # Split into cached and to-encode
    to_encode: list[tuple[int, str]] = []  # (index, summary)
    output: list[dict | None] = [None] * len(skill_summaries)
    for i, (sid, summary, ch) in enumerate(skill_summaries):
        cached = cache.get((sid, ch))
        if cached is not None:
            output[i] = cached
        else:
            to_encode.append((i, summary))

    cached_count = len(skill_summaries) - len(to_encode)
    print(f"  cached: {cached_count}, to encode: {len(to_encode)}", file=sys.stderr)

    if to_encode:
        from fastembed import TextEmbedding
        model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        t0 = time.time()
        texts = [t for _, t in to_encode]
        for slot_idx, vector in zip([i for i, _ in to_encode], model.embed(texts)):
            sid, summary, ch = skill_summaries[slot_idx]
            output[slot_idx] = {
                "skill_id": sid,
                "backend": "fastembed",
                "dimension": 384,
                "content_hash": ch,
                "vector": [round(float(v), 6) for v in vector],
                "summary_text": summary,
            }
        elapsed = time.time() - t0
        print(f"  encoded {len(to_encode)} in {elapsed:.1f}s ({len(to_encode)/elapsed:.0f}/sec)", file=sys.stderr)

    # Stream-write to keep memory low
    with out_path.open("w", encoding="utf-8") as fh:
        for item in output:
            if item is None:
                continue
            fh.write(json.dumps(item, sort_keys=True))
            fh.write("\n")

    print(f"wrote {sum(1 for o in output if o is not None)} embeddings to {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
