#!/usr/bin/env python3
"""Generate NL queries for non-skill corpora (agents, templates, decision-trees).

Mirrors evals/measurement/nl_query_generator.py but targets the three secondary
corpora that the MCP server exposes via search_agents / search_templates /
search_decision_trees. Each corpus needs its own phrasing strategy because
practitioners describe them differently:

- agents     — task-form ("refactor my apex class", "audit my flows")
- templates  — pattern-form ("trigger handler skeleton", "lwc jest config")
- trees      — choice-form ("flow vs apex for X", "how should I do async")

Output schema matches retrieval_eval_corpora.py expectations:
    [
      {"query": "...", "expected": "<corpus-specific-id>", "corpus": "agents"},
      ...
    ]

Pure stdlib. Deterministic.

Usage:
    python3 evals/measurement/nl_query_generator_corpora.py \\
        --corpus agents --out /tmp/nl_agents.json --target-per-doc 4
    python3 evals/measurement/nl_query_generator_corpora.py \\
        --corpus templates --out /tmp/nl_templates.json --target-per-doc 3
    python3 evals/measurement/nl_query_generator_corpora.py \\
        --corpus decision-trees --out /tmp/nl_trees.json --target-per-doc 5
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


# --- shared helpers ---

def slug_to_phrase(slug: str) -> str:
    return slug.replace("-", " ").replace("_", " ")


def normalize_for_dedup(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", s.lower())).strip()


# --- agents corpus ---

AGENT_TASK_OPENERS = [
    "I need to",
    "help me",
    "can you",
    "want to",
    "looking to",
]

AGENT_OUTCOME_OPENERS = [
    "give me",
    "produce",
    "draft",
    "generate",
]


def parse_agent_md(path: Path) -> dict:
    """Pull title (H1), what-this-does paragraph, and any task verbs from AGENT.md.

    AGENT.md has a leading body section, then frontmatter delimited by ---.
    """
    text = path.read_text(encoding="utf-8")
    title = path.parent.name
    m = re.search(r"^#\s+(.+?)\s*$", text, re.MULTILINE)
    if m:
        title = m.group(1).strip().lstrip("/").strip()
    summary = ""
    m = re.search(r"^##\s+What This Agent Does\s*$(.*?)(?=^##\s)", text, re.MULTILINE | re.DOTALL)
    if m:
        for chunk in re.split(r"\n\s*\n", m.group(1).strip()):
            chunk = chunk.strip()
            if chunk and not chunk.startswith("#") and not chunk.startswith("-"):
                summary = chunk
                break
    return {
        "id": path.parent.name,
        "title": title,
        "summary": summary,
        "body": text,
    }


def gen_agent_queries(agent: dict, target: int) -> list[str]:
    """Generate phrasings for an agent. Mix of imperative + outcome forms."""
    name = agent["id"]
    title = agent["title"]
    summary = agent["summary"]
    queries: list[str] = []

    # Form 1: bare title — "apex refactorer", "agent forecast" — what someone might just type
    queries.append(slug_to_phrase(name))

    # Form 2: imperative phrasing derived from the agent name's action verb
    name_phrase = slug_to_phrase(name)
    # Map common name patterns: "apex-refactorer" → "refactor apex"
    parts = name.split("-")
    if len(parts) >= 2 and parts[-1].endswith("er") and len(parts[-1]) > 3:
        verb = parts[-1].rstrip("er").rstrip("e")
        # Drop the trailing "er" for a verb form
        rest = " ".join(parts[:-1])
        if verb and rest:
            queries.append(f"{AGENT_TASK_OPENERS[0]} {verb} my {rest}")
            queries.append(f"{AGENT_TASK_OPENERS[1]} {verb} my {rest}")

    # Form 3: derived from summary — first imperative-ish sentence
    if summary:
        # Pick first sentence
        first = summary.split(".")[0].strip()
        # Use a 6-12 word slice of it as a query
        words = first.split()
        if 6 <= len(words) <= 25:
            queries.append(first.lower())
        elif len(words) > 25:
            queries.append(" ".join(words[:12]).lower())

    # Form 4: outcome-form ("give me X")
    if name.endswith("-builder") or name.endswith("-generator"):
        thing = "-".join(name.split("-")[:-1])
        queries.append(f"{AGENT_OUTCOME_OPENERS[0]} a new {slug_to_phrase(thing)}")
    elif name.endswith("-auditor") or name.endswith("-reviewer"):
        thing = "-".join(name.split("-")[:-1])
        queries.append(f"audit my {slug_to_phrase(thing)}")
        queries.append(f"review my {slug_to_phrase(thing)} setup")
    elif name.endswith("-designer") or name.endswith("-planner"):
        thing = "-".join(name.split("-")[:-1])
        queries.append(f"design a {slug_to_phrase(thing)} for me")

    # Dedupe + cap
    seen: set[str] = set()
    out: list[str] = []
    for q in queries:
        n = normalize_for_dedup(q)
        if not n or n in seen:
            continue
        seen.add(n)
        out.append(q)
        if len(out) >= target:
            break
    return out


def build_agent_queries(target_per_doc: int) -> list[dict]:
    out: list[dict] = []
    root = REPO / "agents"
    if not root.exists():
        return out
    for entry in sorted(root.iterdir()):
        if not entry.is_dir() or entry.name.startswith((".", "_")):
            continue
        md = entry / "AGENT.md"
        if not md.exists():
            continue
        agent = parse_agent_md(md)
        for q in gen_agent_queries(agent, target_per_doc):
            out.append({"query": q, "expected": agent["id"], "corpus": "agents"})
    return out


# --- templates corpus ---

TEMPLATE_FORMS = [
    "{phrase} template",
    "{phrase} skeleton",
    "{phrase} starter",
    "give me a {phrase}",
    "I need a {phrase}",
    "canonical {phrase}",
    "how do I structure {phrase}",
]


def build_template_queries(target_per_doc: int) -> list[dict]:
    out: list[dict] = []
    root = REPO / "templates"
    if not root.exists():
        return out
    seen_paths: set[str] = set()
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in (".cls", ".js", ".html", ".json", ".md", ".xml"):
            continue
        if path.name.lower() in ("readme.md",):
            continue
        rel = path.relative_to(root)
        rel_str = str(rel)
        if rel_str in seen_paths:
            continue
        seen_paths.add(rel_str)

        # Phrase from filename + parent dir
        stem = path.stem
        parent = rel.parent.name if rel.parent.name else ""
        phrase_parts = []
        if parent and parent != ".":
            phrase_parts.append(slug_to_phrase(parent))
        phrase_parts.append(slug_to_phrase(stem.replace("_", "-")))
        phrase = " ".join(phrase_parts).lower()

        queries: list[str] = []
        for tmpl in TEMPLATE_FORMS:
            queries.append(tmpl.format(phrase=phrase))

        # Dedupe + cap
        seen: set[str] = set()
        for q in queries:
            n = normalize_for_dedup(q)
            if not n or n in seen:
                continue
            seen.add(n)
            out.append({"query": q, "expected": rel_str, "corpus": "templates"})
            if sum(1 for o in out if o["expected"] == rel_str) >= target_per_doc:
                break
    return out


# --- decision trees corpus ---

# Tree-specific templates. Decision trees branch on choice questions, so the
# natural-language form is "X vs Y", "should I use X for Y", "when to use X".
TREE_QUERY_PATTERNS = {
    "automation-selection": [
        "flow vs apex for {topic}",
        "should I use flow or apex for {topic}",
        "what automation tool for {topic}",
        "agentforce vs flow",
        "approval process or flow",
        "platform event vs custom api",
        "which automation should I pick",
        "declarative vs apex",
    ],
    "async-selection": [
        "queueable vs batch",
        "future method vs queueable",
        "how should I do async apex",
        "schedulable vs platform event",
        "which async pattern for {topic}",
        "async apex selection",
        "batch apex vs queueable for {topic}",
    ],
    "integration-pattern-selection": [
        "rest api vs bulk api",
        "platform event vs change data capture",
        "pub sub api vs platform events",
        "which integration pattern for {topic}",
        "salesforce connect vs rest",
        "mulesoft vs apex callout",
        "how should I integrate with {topic}",
    ],
    "sharing-selection": [
        "owd vs sharing rules",
        "manual share vs apex managed",
        "role hierarchy vs sharing rules",
        "team vs sharing rule for {topic}",
        "which sharing model for {topic}",
        "restriction rule vs sharing rule",
    ],
    "agentforce-capability-selector": [
        "topic vs action in agentforce",
        "prompt template vs flex prompt",
        "atlas vs deep reasoning",
        "agentforce capability for {topic}",
        "which agentforce feature for {topic}",
    ],
    "flow-pattern-selector": [
        "screen flow vs autolaunched",
        "record-triggered vs scheduled flow",
        "subflow vs invocable",
        "which flow type for {topic}",
        "flow pattern for {topic}",
    ],
    "performance-tuning": [
        "performance tuning for {topic}",
        "how to optimize {topic}",
        "soql performance for {topic}",
        "lightning page slow",
    ],
}


def build_tree_queries(target_per_doc: int) -> list[dict]:
    out: list[dict] = []
    root = REPO / "standards" / "decision-trees"
    if not root.exists():
        return out

    topics = ["high volume", "compliance", "real time", "external system", "bulk load"]

    for tree_path in sorted(root.glob("*.md")):
        name = tree_path.stem
        if name == "README":
            continue
        patterns = TREE_QUERY_PATTERNS.get(name, [])
        if not patterns:
            patterns = [
                f"how do I choose between options in {slug_to_phrase(name)}",
                f"{slug_to_phrase(name)} guidance",
            ]
        seen: set[str] = set()
        n_per = 0
        for i, pattern in enumerate(patterns):
            topic = topics[i % len(topics)]
            q = pattern.format(topic=topic)
            normq = normalize_for_dedup(q)
            if not normq or normq in seen:
                continue
            seen.add(normq)
            out.append({"query": q, "expected": name, "corpus": "decision-trees"})
            n_per += 1
            if n_per >= target_per_doc:
                break
    return out


# --- driver ---

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--corpus", required=True, choices=["agents", "templates", "decision-trees"])
    p.add_argument("--out", required=True)
    p.add_argument("--target-per-doc", type=int, default=4)
    args = p.parse_args()

    if args.corpus == "agents":
        queries = build_agent_queries(args.target_per_doc)
    elif args.corpus == "templates":
        queries = build_template_queries(args.target_per_doc)
    elif args.corpus == "decision-trees":
        queries = build_tree_queries(args.target_per_doc)
    else:
        print(f"unknown corpus {args.corpus}", file=sys.stderr)
        return 2

    Path(args.out).write_text(json.dumps(queries, indent=2), encoding="utf-8")
    print(f"Generated {len(queries)} queries for corpus={args.corpus}", file=sys.stderr)
    by_expected: defaultdict = defaultdict(int)
    for q in queries:
        by_expected[q["expected"]] += 1
    print(f"unique expected: {len(by_expected)}", file=sys.stderr)
    print(f"avg queries per doc: {sum(by_expected.values())/max(1,len(by_expected)):.1f}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
