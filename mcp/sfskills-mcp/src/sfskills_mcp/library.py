"""Knowledge-search tools for the SfSkills MCP.

The skill library already has FTS5-backed search via ``skills.search_skill``,
but the rest of the knowledge layer — agents, templates, decision-trees —
isn't in the lexical index (the indexer walks ``skills/`` and a thin slice
of ``standards/`` only). Three small in-memory indexes here cover them:

- ``search_agents``         — score agents/<name>/AGENT.md by title + summary
                              + body keyword matches
- ``search_templates``      — score templates/<path> by path-token + body
                              keyword matches; useful for finding the right
                              canonical building block
- ``search_decision_trees`` — score standards/decision-trees/<name>.md by
                              tree title + per-section heading + body
                              keyword matches; returns the matching tree
                              plus its top section

Plus two readers for the LLM to pull the full body once it picks a result:

- ``get_template(path)``      — same as ``resources.read_template`` but
                                surfaced as a tool for clients that don't
                                speak Resources
- ``get_decision_tree(name)`` — same as ``resources.read_decision_tree``

Index size today: ~75 agents + ~72 templates + 6 trees = ~150 files. A naive
keyword scan reads the whole set on cold start (cached after) in ~10 ms.
Once the corpus crosses ~1000 files we'll move to a real FTS5 secondary
index; for now the simple scan keeps the dependency surface unchanged.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from . import paths, resources


# --------------------------------------------------------------------------- #
# Shared scoring                                                              #
# --------------------------------------------------------------------------- #


# Plain word tokens for free-text fields (titles, headings, body).
_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
# Splitter for slug/path/name-style identifiers — handles kebab-case, snake_case,
# and CamelCase. e.g. "TriggerHandler.cls" → ["trigger","handler","cls"];
# "admin-skill-builder" → ["admin","skill","builder"].
_IDENT_SPLIT_RE = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z0-9]+|[A-Z]+|[0-9]+")
# English stop words common enough to dilute body scoring without adding signal.
# Intentionally short list — corpus is technical, most terms are meaningful.
_STOP = frozenset({
    "the", "a", "an", "of", "to", "in", "for", "on", "at", "by", "and", "or",
    "is", "it", "this", "that", "with", "from", "as", "be", "are", "i", "we",
    "my", "your", "our", "you", "me", "us", "do", "how", "what", "which", "who",
    "vs", "versus", "between", "should", "would", "could", "can", "need",
    "want", "give", "any", "specific", "finalized", "given",
})


def _tokenize(s: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(s or "")]


def _ident_tokens(s: str) -> list[str]:
    """Split an identifier into atomic tokens.

    >>> _ident_tokens("admin-skill-builder")
    ['admin', 'skill', 'builder']
    >>> _ident_tokens("apex/TriggerHandler.cls")
    ['apex', 'trigger', 'handler', 'cls']
    """
    return [m.group(0).lower() for m in _IDENT_SPLIT_RE.finditer(s or "")]


# One-step suffix stripper. Conservative — only strip when the resulting stem
# is at least 4 chars, so "audit" stays "audit", "audited" → "audit",
# "consolidator" → "consolid" (matching "consolidate" → "consolid"),
# "stories" → "stori" (matching "story" → "stori" via -y → -i rule).
_STEM_RULES: tuple[tuple[str, str], ...] = (
    ("ations", "at"),
    ("ation", "at"),
    ("ators", ""),
    ("ator", ""),
    ("ings", ""),
    ("ing", ""),
    ("ers", ""),
    ("er", ""),
    ("ors", ""),
    ("or", ""),
    ("ies", "i"),
    ("ied", "i"),
    # Verb-form -ate / -ates: consolidate ↔ consolidator → consolid.
    # Length threshold (>=4 stem) prevents mangling "create" → "cre".
    ("ates", ""),
    ("ate", ""),
    ("y", "i"),
    ("ed", ""),
    ("es", ""),
    ("e", ""),
    ("s", ""),
)


def _stem(token: str) -> str:
    """Apply at most one suffix-stripping rule. Returns the stem.

    Designed for slug/query token matching, not for general English NLP.
    Empirically tuned on the agent/template/tree audit failures: the
    suffix list is the union of forms that show up in agent slugs
    (-er, -or, -ation) and the verb forms users type.
    """
    if len(token) <= 4:
        return token
    for suffix, replacement in _STEM_RULES:
        if token.endswith(suffix) and len(token) - len(suffix) + len(replacement) >= 4:
            return token[: -len(suffix)] + replacement
    return token


def _bigram_match_count(query_terms: list[str], target_tokens: list[str]) -> int:
    """Count how many adjacent query bigrams appear adjacent in target tokens.

    Rewards "admin skill" matching "admin-skill-builder" — pure single-token
    matching can't tell that apart from "admin" + "skill" appearing 200 chars
    apart in body text.
    """
    if len(query_terms) < 2 or len(target_tokens) < 2:
        return 0
    target_pairs = {(target_tokens[i], target_tokens[i + 1]) for i in range(len(target_tokens) - 1)}
    return sum(
        1
        for i in range(len(query_terms) - 1)
        if (query_terms[i], query_terms[i + 1]) in target_pairs
    )


def _score(
    query_terms: list[str],
    *,
    name_tokens: list[str] | None = None,
    title: str = "",
    headings: str = "",
    body: str = "",
) -> float:
    """Weighted token match.

    Field weights tuned 2026-05-09 against the agent/template/tree NL audit:
    - name_tokens (slug/path/basename, whole-word)  → 15x  (was untracked)
    - title (free-text H1, substring)               →  5x
    - headings (H2/H3, substring)                   →  2x
    - body (everything else, substring, stopword-filtered) → 0.3x

    The body weight dropped from 1.0 → 0.3 because long documents that mention
    the query terms incidentally were beating short, tightly-named target
    documents (e.g. ``object-designer.md`` mentions "admin" 284 times so it
    was outranking the literally-named ``admin-skill-builder.md`` for
    "admin skill builder"). Bigram bonus stacks on top to reward
    multi-word queries that match adjacent tokens in the slug or title.
    """
    if not query_terms:
        return 0.0
    filtered_terms = [t for t in query_terms if t not in _STOP]
    if not filtered_terms:
        filtered_terms = query_terms  # all-stopword query — fall back to as-is

    title_l = title.lower()
    headings_l = headings.lower()
    body_l = body.lower()
    name_set: set[str] = set(name_tokens or [])
    name_stems: set[str] = {_stem(t) for t in (name_tokens or [])}
    score = 0.0
    matched_name_tokens = 0
    for term in filtered_terms:
        term_stem = _stem(term)
        # Whole-word slug match — exact or stem-equivalent.
        if term in name_set:
            score += 15.0
            matched_name_tokens += 1
        elif term_stem in name_stems:
            score += 11.0  # Stem match — strong signal but slightly lower than exact.
            matched_name_tokens += 1
        # Substring counts on free-text fields.
        # Body counts are square-root capped per-term so a term mentioned 100
        # times contributes 10x not 100x — prevents long meta-documents (e.g.
        # apex-builder.AGENT.md mentioning "apex" 200+ times) from drowning
        # specific documents whose slug is the better match, while still
        # rewarding documents that actually mention the term repeatedly.
        score += 5.0 * title_l.count(term)
        score += 2.0 * headings_l.count(term)
        body_count = body_l.count(term)
        if body_count > 0:
            score += 0.6 * (body_count ** 0.5)

    # Slug coverage bonus: rewards documents whose ENTIRE slug is mentioned
    # in the query, breaking ties between specific docs (e.g. trigger-consolidator
    # for "consolidate my triggers" — slug-coverage 1.0) and broad docs
    # (e.g. apex-builder — slug-coverage 0.5). Without this, body matches
    # let broad docs outrank specific ones whose slug exactly describes intent.
    if name_tokens and matched_name_tokens > 0:
        coverage = matched_name_tokens / len(name_tokens)
        score += 20.0 * coverage

    # Bigram bonus on slug — meaningful if the query has 2+ tokens. Compare
    # stems so "build agentforce" matches "agentforce-action-builder" tokens
    # ("agentforce","action","builder") via stem("builder")=="build".
    if name_tokens:
        stemmed_query = [_stem(t) for t in filtered_terms]
        stemmed_name = [_stem(t) for t in name_tokens]
        bigrams = _bigram_match_count(stemmed_query, stemmed_name)
        score += 8.0 * bigrams

    return score


def _bound_limit(limit: int, ceiling: int = 50) -> int:
    return max(1, min(int(limit or 10), ceiling))


# --------------------------------------------------------------------------- #
# search_agents                                                                #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class _AgentDoc:
    name: str
    path: str
    title: str
    summary: str
    body: str


@lru_cache(maxsize=1)
def _agent_corpus() -> tuple[_AgentDoc, ...]:
    out: list[_AgentDoc] = []
    root = paths.repo_root() / "agents"
    if not root.exists():
        return ()
    for entry in sorted(root.iterdir()):
        if not entry.is_dir() or entry.name.startswith((".", "_")):
            continue
        md = entry / "AGENT.md"
        if not md.exists():
            continue
        body = md.read_text(encoding="utf-8")
        # Title = first H1 if present, else the agent name. Summary = first
        # non-empty paragraph after "## What This Agent Does", which the
        # AGENT_CONTRACT requires.
        title = entry.name
        m = re.search(r"^#\s+(.+?)\s*$", body, re.MULTILINE)
        if m:
            title = m.group(1).strip()
        summary = ""
        m = re.search(r"^##\s+What This Agent Does\s*$(.*?)^## ", body, re.MULTILINE | re.DOTALL)
        if m:
            for chunk in re.split(r"\n\s*\n", m.group(1).strip()):
                chunk = chunk.strip()
                if chunk and not chunk.startswith("#"):
                    summary = chunk
                    break
        out.append(_AgentDoc(
            name=entry.name,
            path=str(md.relative_to(paths.repo_root())),
            title=title,
            summary=summary,
            body=body,
        ))
    return tuple(out)


def search_agents(query: str, limit: int = 10) -> dict[str, Any]:
    """Rank agents by token match against title + summary + body."""
    if not isinstance(query, str) or not query.strip():
        return {"error": "query is required", "query": query, "agents": []}
    bounded = _bound_limit(limit)
    terms = _tokenize(query)
    hits: list[tuple[float, _AgentDoc]] = []
    for doc in _agent_corpus():
        # Slug ("admin-skill-builder") drives the high-weight name match.
        name_tokens = _ident_tokens(doc.name)
        score = _score(
            terms,
            name_tokens=name_tokens,
            title=doc.title,
            headings=doc.summary,
            body=doc.body,
        )
        if score > 0:
            hits.append((score, doc))
    hits.sort(key=lambda x: x[0], reverse=True)
    return {
        "query": query,
        "result_count": len(hits[:bounded]),
        "agents": [
            {
                "name": doc.name,
                "title": doc.title,
                "summary": doc.summary,
                "path": doc.path,
                "score": round(score, 3),
            }
            for score, doc in hits[:bounded]
        ],
    }


# --------------------------------------------------------------------------- #
# search_templates                                                             #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class _TemplateDoc:
    path: str               # e.g. "apex/TriggerHandler.cls"
    body: str


@lru_cache(maxsize=1)
def _template_corpus() -> tuple[_TemplateDoc, ...]:
    out: list[_TemplateDoc] = []
    root = paths.repo_root() / "templates"
    if not root.exists():
        return ()
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        try:
            body = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        out.append(_TemplateDoc(
            path=str(path.relative_to(root)).replace("\\", "/"),
            body=body,
        ))
    return tuple(out)


def search_templates(query: str, limit: int = 10) -> dict[str, Any]:
    """Rank canonical templates. Path tokens (e.g. ``apex``,
    ``TriggerHandler``) are scored as title matches — finding
    ``apex/TriggerHandler.cls`` for the query "trigger handler" is the
    primary use case."""
    if not isinstance(query, str) or not query.strip():
        return {"error": "query is required", "query": query, "templates": []}
    bounded = _bound_limit(limit)
    terms = _tokenize(query)
    hits: list[tuple[float, _TemplateDoc]] = []
    for doc in _template_corpus():
        # Path ("apex/TriggerHandler.cls") splits into tokens that also drive
        # the high-weight name match: ["apex","trigger","handler","cls"].
        name_tokens = _ident_tokens(doc.path)
        path_title = doc.path.replace("/", " ").replace(".", " ").replace("-", " ").replace("_", " ")
        score = _score(
            terms,
            name_tokens=name_tokens,
            title=path_title,
            headings="",
            body=doc.body,
        )
        if score > 0:
            hits.append((score, doc))
    hits.sort(key=lambda x: x[0], reverse=True)
    return {
        "query": query,
        "result_count": len(hits[:bounded]),
        "templates": [
            {
                "path": doc.path,
                "uri": f"sfskills://template/{doc.path.replace('/', '__')}",
                "preview": _first_n_lines(doc.body, 8),
                "score": round(score, 3),
            }
            for score, doc in hits[:bounded]
        ],
    }


def _first_n_lines(body: str, n: int) -> str:
    return "\n".join(body.splitlines()[:n])


# --------------------------------------------------------------------------- #
# search_decision_trees                                                        #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class _TreeDoc:
    name: str           # basename without .md
    title: str
    sections: tuple[tuple[str, str], ...]  # (heading, section_body) pairs
    body: str


@lru_cache(maxsize=1)
def _tree_corpus() -> tuple[_TreeDoc, ...]:
    out: list[_TreeDoc] = []
    root = paths.repo_root() / "standards" / "decision-trees"
    if not root.exists():
        return ()
    for path in sorted(root.iterdir()):
        if path.suffix != ".md" or path.stem == "README":
            continue
        body = path.read_text(encoding="utf-8")
        title = path.stem.replace("-", " ").title()
        m = re.search(r"^#\s+(.+?)\s*$", body, re.MULTILINE)
        if m:
            title = m.group(1).strip()
        # Carve sections by H2 / H3 headings — useful for "which subsection
        # answers my Flow vs Apex question".
        sections: list[tuple[str, str]] = []
        section_iter = re.finditer(r"^(#{2,3})\s+(.+?)\s*$", body, re.MULTILINE)
        last_end: int | None = None
        last_heading: str | None = None
        for m in section_iter:
            if last_heading is not None and last_end is not None:
                sections.append((last_heading, body[last_end:m.start()]))
            last_heading = m.group(2).strip()
            last_end = m.end()
        if last_heading is not None and last_end is not None:
            sections.append((last_heading, body[last_end:]))
        out.append(_TreeDoc(
            name=path.stem,
            title=title,
            sections=tuple(sections),
            body=body,
        ))
    return tuple(out)


def search_decision_trees(query: str, limit: int = 6) -> dict[str, Any]:
    """Rank decision trees by token match. For each ranked tree, also
    surface the section (H2/H3) inside it that matched best — agents are
    supposed to cite the specific branch that resolved their decision."""
    if not isinstance(query, str) or not query.strip():
        return {"error": "query is required", "query": query, "trees": []}
    bounded = _bound_limit(limit)
    terms = _tokenize(query)
    hits: list[tuple[float, _TreeDoc, str | None, float]] = []
    for doc in _tree_corpus():
        # Tree basename ("automation-selection") provides high-weight name match.
        name_tokens = _ident_tokens(doc.name)
        section_titles = " ".join(s[0] for s in doc.sections)
        tree_score = _score(
            terms,
            name_tokens=name_tokens,
            title=doc.title,
            headings=section_titles,
            body=doc.body,
        )
        if tree_score == 0:
            continue
        # Find best sub-section (no name field at section level — purely text).
        best_section: str | None = None
        best_section_score = 0.0
        for heading, content in doc.sections:
            sec_score = _score(terms, title=heading, headings="", body=content)
            if sec_score > best_section_score:
                best_section_score = sec_score
                best_section = heading
        hits.append((tree_score, doc, best_section, best_section_score))
    hits.sort(key=lambda x: x[0], reverse=True)
    return {
        "query": query,
        "result_count": len(hits[:bounded]),
        "trees": [
            {
                "name": doc.name,
                "title": doc.title,
                "uri": f"sfskills://decision-tree/{doc.name}",
                "best_section": best_heading,
                "best_section_score": round(best_score, 3),
                "score": round(tree_score, 3),
            }
            for tree_score, doc, best_heading, best_score in hits[:bounded]
        ],
    }


# --------------------------------------------------------------------------- #
# get_template / get_decision_tree                                             #
# --------------------------------------------------------------------------- #


def get_template(path: str) -> dict[str, Any]:
    """Return one canonical template's contents. Wraps
    ``resources.read_template`` so MCP clients that don't speak Resources
    still have a tool path."""
    body = resources.read_template(path)
    if body.startswith("//") and ("invalid" in body or "rejected" in body or "not found" in body):
        return {"error": body.strip().lstrip("/").strip(), "path": path}
    return {"path": path, "body": body, "byte_size": len(body)}


def get_decision_tree(name: str) -> dict[str, Any]:
    """Return one decision tree's full markdown."""
    body = resources.read_decision_tree(name)
    if body.startswith("# Decision tree not found") or body.startswith("# Invalid"):
        return {"error": body.strip().lstrip("# "), "name": name}
    return {"name": name, "body": body, "byte_size": len(body)}
