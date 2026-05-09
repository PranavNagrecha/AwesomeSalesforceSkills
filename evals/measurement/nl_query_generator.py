#!/usr/bin/env python3
"""Generate ~3,000 natural-language query / expected-skill pairs.

For each skill in the registry, emit 3-4 phrasings derived deterministically
from its description, tags, and triggers. Phrasings cover four natural-
language modes a Salesforce professional uses:

1. Question form  — "how do I X"
2. Symptom form   — "X isn't working" / "users can't Y"
3. Goal form      — "I want to Z"
4. Error form     — pasted error message (only for skills tagged for it)

Output: a JSON list shaped like `vector_index/query-fixtures.json` so
`retrieval_eval.py` can consume it as-is.

Pure stdlib. Deterministic — same input produces same output, so the
fixture set is stable across runs.

Usage:
    python3 evals/measurement/nl_query_generator.py \\
        --out evals/measurement/nl_generated.json \\
        --target-per-skill 3
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


# ---- helpers ----

def primary_noun(tag_list: list[str]) -> str:
    """Pick the most domain-specific tag as the primary noun."""
    if not tag_list:
        return ""
    # Drop tags that are domain-meta (the skill's own slug as a tag, etc.)
    candidates = [t for t in tag_list if "-" in t and not t.endswith("design") and len(t) > 6]
    return candidates[0] if candidates else (tag_list[0] if tag_list else "")


def slug_to_phrase(slug: str) -> str:
    """`flow-bulkification` → `flow bulkification`."""
    return slug.replace("-", " ").replace("_", " ")


def first_sentence(text: str, max_chars: int = 200) -> str:
    """Take the first sentence of a description (up to max_chars)."""
    if not text:
        return ""
    text = text.strip().strip('"').strip("'")
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return sentences[0][:max_chars] if sentences else text[:max_chars]


def normalize_for_dedup(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", s.lower())).strip()


# ---- templates ----

# Template 1: question form
QUESTION_OPENERS = [
    "how do I",
    "what's the best way to",
    "can someone help with",
    "tell me about",
    "I need to understand",
]

# Template 2: symptom forms — varied per skill type so we don't over-generate
# the "X is slow" anti-pattern that biases performance-tuning skills.
# Each function returns (template_str, format_keys) so the generator picks
# domain-appropriate phrasing.
SYMPTOM_PATTERNS_GENERIC = [
    "{noun} isn't working",
    "we're having issues with {noun}",
    "{noun} keeps failing intermittently",
    "{noun} stopped working after the last release",
    "I need help with {noun}",
    "what's the right way to handle {noun}",
    "we're struggling with {noun} in production",
]
SYMPTOM_PATTERNS_PERF = [
    "{noun} is slow",
    "{noun} hits the timeout",
    "we're seeing performance issues with {noun}",
]
SYMPTOM_PATTERNS_VISIBILITY = [
    "users can't see {noun}",
    "{noun} sharing is broken for some users",
    "wrong users are seeing {noun}",
]
SYMPTOM_PATTERNS_AUTOMATION = [
    "{noun} is firing twice",
    "{noun} isn't firing at all",
    "{noun} fires at the wrong time",
    "we're getting infinite recursion in {noun}",
]
SYMPTOM_PATTERNS_DATA = [
    "{noun} has duplicate records",
    "{noun} import keeps failing",
    "data quality on {noun} is poor",
    "{noun} migration broke",
]
SYMPTOM_PATTERNS_INTEGRATION = [
    "{noun} integration is failing",
    "{noun} webhook is timing out",
    "{noun} callout is hitting the limit",
    "{noun} sync is missing records",
]
SYMPTOM_PATTERNS_DEPLOYMENT = [
    "{noun} deployment is failing",
    "{noun} change set won't validate",
    "{noun} broke after the last release",
]
SYMPTOM_PATTERNS_AGENT = [
    "{noun} agent is hallucinating",
    "{noun} agent isn't grounding correctly",
    "{noun} agent action returns access denied",
]


def _pick_symptom_patterns(skill: dict) -> list[str]:
    """Return symptom templates appropriate for this skill's tags."""
    tags = set(skill.get("tags", []))
    domain = skill.get("category", "")
    pats = list(SYMPTOM_PATTERNS_GENERIC)
    if any(t in tags for t in ("performance", "performance-tuning", "lightning-page", "page-load")):
        pats = SYMPTOM_PATTERNS_PERF
    elif any(t in tags for t in ("sharing", "visibility", "fls", "owd", "permission-set", "profile",
                                  "record-access", "permission")):
        pats += SYMPTOM_PATTERNS_VISIBILITY
    if any(t in tags for t in ("flow", "trigger", "automation", "process-builder", "approval-process",
                               "scheduled-flow", "record-triggered-flow", "validation-rule")):
        pats += SYMPTOM_PATTERNS_AUTOMATION
    if any(t in tags for t in ("data", "data-loader", "import", "duplicate", "data-quality", "csv")):
        pats += SYMPTOM_PATTERNS_DATA
    if any(t in tags for t in ("integration", "callout", "rest-api", "soap-api", "webhook",
                               "platform-event", "sync", "etl")):
        pats += SYMPTOM_PATTERNS_INTEGRATION
    if any(t in tags for t in ("deployment", "change-set", "metadata-api", "dx", "release",
                                "ci-cd", "package")):
        pats += SYMPTOM_PATTERNS_DEPLOYMENT
    if domain == "agentforce" or any(t in tags for t in ("agentforce", "agent", "einstein", "genai",
                                                           "trust-layer", "prompt-template")):
        pats += SYMPTOM_PATTERNS_AGENT
    return pats

# Template 3: goal form
GOAL_OPENERS = [
    "I want to",
    "we need to",
    "looking for the right way to",
    "trying to figure out how to",
    "need help to",
]

# Template 4: error form — only for skills with error-related tags
ERROR_TAGS = {
    "governor-limits",
    "exception",
    "error-handling",
    "runtime-error",
    "deployment-error",
    "validation-rule",
    "soql-101",
    "cpu-time-limit",
    "heap-size",
    "mixed-dml",
    "unable-to-lock-row",
    "insufficient-access",
}


def gen_question_form(skill: dict, idx: int) -> str | None:
    triggers = skill.get("triggers", [])
    if not triggers:
        return None
    # Pick a trigger and rewrite as a different phrasing of the same intent.
    # Aim for SHORTER + slightly differently-worded versions to avoid being a
    # byte-identical copy of the trigger itself.
    t = triggers[idx % len(triggers)].rstrip(".?!").strip()
    lower = t.lower()
    # If trigger is already a question, drop the opener to vary phrasing
    for opener in ("how do i ", "how can i ", "what is ", "what's ", "why does ", "why is ",
                   "can i ", "where do ", "where is "):
        if lower.startswith(opener):
            stub = t[len(opener):].strip()
            if 5 < len(stub) < 100:
                # Wrap with a DIFFERENT opener to vary
                new_opener = QUESTION_OPENERS[(idx + 1) % len(QUESTION_OPENERS)]
                return f"{new_opener} {stub.lower()}"
            return None
    # Trigger isn't a question — wrap with opener (only if trigger is short enough)
    if len(t) > 100:
        return None
    opener = QUESTION_OPENERS[idx % len(QUESTION_OPENERS)]
    return f"{opener} {t.lower()}"


def gen_symptom_form(skill: dict, idx: int) -> str | None:
    noun = primary_noun(skill.get("tags", []))
    if not noun:
        noun = slug_to_phrase(skill.get("name", "") or skill.get("slug", ""))
    if not noun:
        return None
    noun = slug_to_phrase(noun)
    patterns = _pick_symptom_patterns(skill)
    pattern = patterns[idx % len(patterns)]
    state = ("slow", "broken", "missing", "wrong", "delayed")[idx % 5]
    failing = ("failing", "throwing errors", "timing out", "missing data", "stuck")[idx % 5]
    try:
        return pattern.format(noun=noun, state=state, failing=failing)
    except KeyError:
        return None


def gen_goal_form(skill: dict, idx: int) -> str | None:
    desc = first_sentence(skill.get("description", ""))
    if not desc:
        return None
    # Pull the part of the description after "Use when" / "Use this skill when"
    m = re.search(r"[Uu]se (?:this skill )?when ([^.,;:—\-]+)", desc)
    if not m:
        return None
    intent = m.group(1).strip().rstrip(",;:")
    # Filter on length and grammar quality
    intent = re.sub(r"\s+", " ", intent)
    if len(intent.split()) < 4 or len(intent) > 120:
        return None
    # If intent starts with a verb in -ing form, "I want to <verb-ing>" is grammatically off.
    # Detect and skip.
    first_word = intent.split()[0]
    if first_word.endswith("ing") and len(first_word) > 5:
        return None
    opener = GOAL_OPENERS[idx % len(GOAL_OPENERS)]
    return f"{opener} {intent}"


def gen_error_form(skill: dict) -> str | None:
    tags = set(skill.get("tags", []))
    if not (tags & ERROR_TAGS):
        return None
    # Pick the error message hinted at by tags
    if "soql-101" in tags or "Too many SOQL" in str(skill.get("description", "")):
        return "System.LimitException: Too many SOQL queries: 101"
    if "cpu-time-limit" in tags:
        return "System.LimitException: Apex CPU time limit exceeded"
    if "heap-size" in tags:
        return "System.LimitException: Apex heap size too large"
    if "mixed-dml" in tags:
        return "MIXED_DML_OPERATION: DML operation on setup object is not permitted after you have updated a non-setup object"
    if "unable-to-lock-row" in tags:
        return "UNABLE_TO_LOCK_ROW row lock contention"
    if "insufficient-access" in tags:
        return "INSUFFICIENT_ACCESS_OR_READONLY"
    if "validation-rule" in tags:
        return "Validation rule fired but I cannot find which one"
    if "deployment-error" in tags:
        return "Deployment failed with INVALID_FIELD on a field that exists in production"
    return None


# ---- generator ----

def generate(registry: dict, target_per_skill: int = 3) -> list[dict]:
    skills = registry.get("skills", [])
    output: list[dict] = []
    seen_norm: set[str] = set()
    by_template: defaultdict = defaultdict(int)

    for skill in skills:
        category = skill.get("category", "")
        name = skill.get("name") or skill.get("slug", "")
        if not category or not name:
            continue
        skill_id = f"{category}/{name}"

        candidates: list[tuple[str, str]] = []

        # Template 1 — question form (mandatory)
        for i in range(2):
            q = gen_question_form(skill, i)
            if q:
                candidates.append(("question", q))

        # Template 2 — symptom form (up to 2 variants per skill, picked from
        # domain-appropriate template pool for diversity)
        for i in range(2):
            s = gen_symptom_form(skill, i)
            if s:
                candidates.append(("symptom", s))

        # Template 3 — goal form
        g = gen_goal_form(skill, 0)
        if g:
            candidates.append(("goal", g))

        # Template 4 — error form (optional)
        e = gen_error_form(skill)
        if e:
            candidates.append(("error", e))

        # Dedup against already-emitted queries (cross-skill)
        kept = 0
        for template, q in candidates:
            if kept >= target_per_skill + (1 if e else 0):
                break
            n = normalize_for_dedup(q)
            if not n or len(n.split()) < 4:
                continue
            if n in seen_norm:
                continue
            seen_norm.add(n)
            output.append({
                "query": q,
                "expected_skill": skill_id,
                "domain": category,
                "top_k": 3,
                "template": template,
            })
            by_template[template] += 1
            kept += 1

    print(f"Generated {len(output)} queries", file=sys.stderr)
    print(f"By template: {dict(by_template)}", file=sys.stderr)
    return output


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--registry", default=str(REPO / "registry" / "skills.json"))
    p.add_argument("--out", required=True)
    p.add_argument("--target-per-skill", type=int, default=3)
    args = p.parse_args()

    reg = json.loads(Path(args.registry).read_text())
    queries = generate(reg, args.target_per_skill)

    Path(args.out).write_text(json.dumps({"queries": queries}, indent=2))
    print(f"Wrote {len(queries)} queries to {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
