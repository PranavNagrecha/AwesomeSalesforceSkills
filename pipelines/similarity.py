"""Pairwise similarity primitives for skill duplicate detection.

Used by:
  - scripts/audit_duplicates.py — on-demand top-N report over the full corpus
  - pipelines/validators.py     — validator gate that flags near-duplicates at
                                  commit time (WARN-level on the existing corpus)
  - scripts/new_skill.py        — `--strict` flag blocks scaffolding when the
                                  proposed skill name + description would
                                  produce a near-duplicate

Design notes
------------
- Stdlib only. ``difflib.SequenceMatcher`` is the heaviest primitive.
- The score is normalized to ``[0.0, 1.0]`` so the threshold reads naturally.
- Three signals — description text, tag set, trigger phrases — combined as a
  weighted sum with weights from ``config/retrieval-config.yaml``.
- Pairwise scan is O(N^2) but a cheap tag/domain prefilter keeps the heavy
  ``SequenceMatcher.ratio()`` calls bounded. On a 926-skill corpus the audit
  runs in ~10–20 s wall-clock.

Why the existing ``skill_graph.find_related`` is not reused directly:
That function returns an integer score with human-readable reasons, intended
for the related-skills navigator. Duplicate detection wants a normalized
[0,1] similarity with per-component breakdown. The small primitives below
(``normalize_tags``, ``tokenize_triggers``) are shared; the higher-level
scoring intentionally diverges.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .frontmatter import parse_markdown_with_frontmatter


# Default weights — sum to 1.0. Description is the most discriminating signal
# (full sentence, including the "NOT for ..." scope exclusion); tags and
# triggers are coarser.
DEFAULT_WEIGHTS: dict[str, float] = {
    "description": 0.5,
    "tags": 0.25,
    "triggers": 0.25,
}

# Default threshold above which a pair is flagged as a near-duplicate. Tuned
# empirically against the existing 926-skill corpus on 2026-05-01:
#   0.65 → 0 pairs   (too aggressive; misses every real case in the corpus)
#   0.55 → 2 pairs   (only the most extreme; misses the parallel-pattern cases)
#   0.50 → 4 pairs   (the sweet spot — genuine overlaps surface, intentional
#                     parallels like bitbucket/gitlab/github-actions stay out)
#   0.45 → 8 pairs   (starts including intentional-parallel cross-vendor skills)
DEFAULT_THRESHOLD: float = 0.50

# Trigger words shorter than this length are stop-wordy ("is", "and", "for",
# "with"). The same threshold ``skill_graph.find_related`` uses.
TRIGGER_WORD_MIN_LENGTH: int = 5


@dataclass(frozen=True)
class SkillFingerprint:
    """Pre-computed normalized signals for one skill. Building these once and
    reusing them across the pairwise scan avoids re-tokenizing on every pair.
    """
    skill_id: str
    domain: str
    description: str
    tags: frozenset[str]
    trigger_words: frozenset[str]
    path: Path


@dataclass(frozen=True)
class SimilarityScore:
    """Pairwise similarity result. ``total`` is the weighted combined score
    in [0, 1]; the per-component fields explain why."""
    total: float
    description: float
    tags: float
    triggers: float
    shared_tags: tuple[str, ...]
    shared_trigger_words: tuple[str, ...]


# ---------------------------------------------------------------------------
# Normalizers — small primitives, also used by skill_graph.py
# ---------------------------------------------------------------------------

def normalize_tags(tags: Iterable[str]) -> frozenset[str]:
    """Lowercase + strip. Returns a frozenset for cheap set ops."""
    return frozenset(t.strip().lower() for t in tags if t and t.strip())


def tokenize_triggers(triggers: Iterable[str]) -> frozenset[str]:
    """Extract content words (>= TRIGGER_WORD_MIN_LENGTH) from trigger phrases.
    Lowercased, deduplicated. Mirrors the tokenization in
    ``skill_graph.find_related`` so the two stay aligned."""
    joined = " ".join(triggers).lower()
    pattern = re.compile(rf"\b\w{{{TRIGGER_WORD_MIN_LENGTH},}}\b")
    return frozenset(pattern.findall(joined))


def normalize_description(desc: str) -> str:
    """Lowercase, collapse whitespace. Keeps punctuation since ``NOT for ...``
    clauses carry the discriminating signal."""
    return re.sub(r"\s+", " ", desc.lower()).strip()


# ---------------------------------------------------------------------------
# Per-component scorers — each returns a value in [0, 1]
# ---------------------------------------------------------------------------

def tag_jaccard(tags_a: frozenset[str], tags_b: frozenset[str]) -> float:
    """Jaccard similarity over normalized tag sets."""
    if not tags_a and not tags_b:
        return 0.0
    union = tags_a | tags_b
    if not union:
        return 0.0
    return len(tags_a & tags_b) / len(union)


def trigger_jaccard(words_a: frozenset[str], words_b: frozenset[str]) -> float:
    """Jaccard similarity over tokenized trigger word sets."""
    if not words_a and not words_b:
        return 0.0
    union = words_a | words_b
    if not union:
        return 0.0
    return len(words_a & words_b) / len(union)


def description_ratio(desc_a: str, desc_b: str) -> float:
    """SequenceMatcher.ratio() on normalized descriptions. Returns [0, 1]."""
    if not desc_a or not desc_b:
        return 0.0
    return difflib.SequenceMatcher(
        None, normalize_description(desc_a), normalize_description(desc_b),
        autojunk=False,
    ).ratio()


# ---------------------------------------------------------------------------
# Combined scorer
# ---------------------------------------------------------------------------

def compute_similarity(
    a: SkillFingerprint,
    b: SkillFingerprint,
    weights: dict[str, float] = DEFAULT_WEIGHTS,
) -> SimilarityScore:
    """Compute weighted similarity between two skill fingerprints. Returns a
    ``SimilarityScore`` whose ``total`` is in [0, 1]."""
    desc_score = description_ratio(a.description, b.description)
    tag_score = tag_jaccard(a.tags, b.tags)
    trig_score = trigger_jaccard(a.trigger_words, b.trigger_words)

    total = (
        desc_score * weights["description"]
        + tag_score * weights["tags"]
        + trig_score * weights["triggers"]
    )

    return SimilarityScore(
        total=total,
        description=desc_score,
        tags=tag_score,
        triggers=trig_score,
        shared_tags=tuple(sorted(a.tags & b.tags)),
        shared_trigger_words=tuple(sorted(a.trigger_words & b.trigger_words)),
    )


# ---------------------------------------------------------------------------
# Corpus loader + pairwise scanner
# ---------------------------------------------------------------------------

def fingerprint_skill(skill_md: Path, root: Path) -> SkillFingerprint | None:
    """Build a fingerprint for one skill. Returns None when the SKILL.md is
    unparseable — caller decides whether to log + skip or error."""
    try:
        parsed = parse_markdown_with_frontmatter(skill_md)
    except Exception:
        return None
    meta = parsed.metadata
    name = meta.get("name") or skill_md.parent.name
    category = meta.get("category") or skill_md.parent.parent.name
    return SkillFingerprint(
        skill_id=f"{category}/{name}",
        domain=str(category),
        description=str(meta.get("description") or ""),
        tags=normalize_tags(meta.get("tags") or []),
        trigger_words=tokenize_triggers(meta.get("triggers") or []),
        path=skill_md,
    )


def fingerprint_corpus(root: Path) -> list[SkillFingerprint]:
    """Walk skills/<domain>/<name>/SKILL.md and return fingerprints. Skips any
    skill whose SKILL.md fails to parse — those failures surface elsewhere
    (frontmatter validation), so we don't double-report here."""
    out: list[SkillFingerprint] = []
    for skill_md in sorted((root / "skills").rglob("SKILL.md")):
        fp = fingerprint_skill(skill_md, root)
        if fp is not None:
            out.append(fp)
    return out


def _pairwise_candidates(
    fingerprints: list[SkillFingerprint],
) -> Iterable[tuple[SkillFingerprint, SkillFingerprint]]:
    """Yield candidate pairs — those sharing at least one tag OR sharing the
    same domain plus at least one trigger word. Cuts the heavy
    ``SequenceMatcher.ratio()`` work to a small fraction of N^2."""
    by_tag: dict[str, list[int]] = {}
    by_domain: dict[str, list[int]] = {}
    for i, fp in enumerate(fingerprints):
        for tag in fp.tags:
            by_tag.setdefault(tag, []).append(i)
        by_domain.setdefault(fp.domain, []).append(i)

    seen: set[tuple[int, int]] = set()

    # Tag co-occurrence
    for indices in by_tag.values():
        for i in range(len(indices)):
            for j in range(i + 1, len(indices)):
                a, b = indices[i], indices[j]
                pair = (a, b) if a < b else (b, a)
                if pair in seen:
                    continue
                seen.add(pair)
                yield fingerprints[pair[0]], fingerprints[pair[1]]

    # Same domain + shared trigger word
    for indices in by_domain.values():
        for i in range(len(indices)):
            fp_i = fingerprints[indices[i]]
            for j in range(i + 1, len(indices)):
                fp_j = fingerprints[indices[j]]
                if not fp_i.trigger_words & fp_j.trigger_words:
                    continue
                a, b = indices[i], indices[j]
                pair = (a, b) if a < b else (b, a)
                if pair in seen:
                    continue
                seen.add(pair)
                yield fp_i, fp_j


def find_duplicate_pairs(
    fingerprints: list[SkillFingerprint],
    threshold: float = DEFAULT_THRESHOLD,
    weights: dict[str, float] = DEFAULT_WEIGHTS,
    *,
    full_scan: bool = False,
) -> list[tuple[SkillFingerprint, SkillFingerprint, SimilarityScore]]:
    """Score every candidate pair, return those above ``threshold`` sorted
    descending by ``total``.

    ``full_scan=True`` skips the prefilter and scores every N*(N-1)/2 pair —
    use only for one-off audits where you want to see everything; on the
    926-skill corpus the prefiltered scan already finds every meaningful
    duplicate (because true duplicates always share at least one tag)."""
    out: list[tuple[SkillFingerprint, SkillFingerprint, SimilarityScore]] = []

    if full_scan:
        n = len(fingerprints)
        for i in range(n):
            fp_i = fingerprints[i]
            for j in range(i + 1, n):
                score = compute_similarity(fp_i, fingerprints[j], weights)
                if score.total >= threshold:
                    out.append((fp_i, fingerprints[j], score))
    else:
        for fp_a, fp_b in _pairwise_candidates(fingerprints):
            score = compute_similarity(fp_a, fp_b, weights)
            if score.total >= threshold:
                out.append((fp_a, fp_b, score))

    out.sort(key=lambda t: t[2].total, reverse=True)
    return out


def find_nearest_neighbours(
    target: SkillFingerprint,
    corpus: list[SkillFingerprint],
    top_k: int = 5,
    weights: dict[str, float] = DEFAULT_WEIGHTS,
) -> list[tuple[SkillFingerprint, SimilarityScore]]:
    """Score one fingerprint against every other in the corpus, return the
    top K by total similarity. Used by the ``--strict`` scaffold gate."""
    scored: list[tuple[SkillFingerprint, SimilarityScore]] = []
    for other in corpus:
        if other.skill_id == target.skill_id:
            continue
        score = compute_similarity(target, other, weights)
        scored.append((other, score))
    scored.sort(key=lambda t: t[1].total, reverse=True)
    return scored[:top_k]


# ---------------------------------------------------------------------------
# Config loader — reads duplicate_threshold from retrieval-config.yaml
# ---------------------------------------------------------------------------

def load_threshold_from_config(root: Path) -> tuple[float, dict[str, float]]:
    """Return (threshold, weights). Falls back to DEFAULT_* on any error so
    callers don't need to special-case missing config."""
    try:
        import yaml  # type: ignore
    except ImportError:
        return DEFAULT_THRESHOLD, DEFAULT_WEIGHTS
    cfg_path = root / "config" / "retrieval-config.yaml"
    if not cfg_path.exists():
        return DEFAULT_THRESHOLD, DEFAULT_WEIGHTS
    try:
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return DEFAULT_THRESHOLD, DEFAULT_WEIGHTS
    block = cfg.get("duplicate_threshold") or {}
    threshold = float(block.get("score", DEFAULT_THRESHOLD))
    weights_block = block.get("weights") or {}
    weights = {**DEFAULT_WEIGHTS}
    for k in ("description", "tags", "triggers"):
        if k in weights_block:
            try:
                weights[k] = float(weights_block[k])
            except (TypeError, ValueError):
                pass
    return threshold, weights
