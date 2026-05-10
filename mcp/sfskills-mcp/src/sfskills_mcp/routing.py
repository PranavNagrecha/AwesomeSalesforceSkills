"""``suggest_agent`` — task-to-agent routing.

Most adoption-time failures look the same: user says "I want to refactor a
2000-line class" and the model freelances Apex instead of fetching
``apex-refactorer``'s AGENT.md. ``audit-router`` solves this for the audit
sub-domain; this tool generalises the pattern.

Approach: take the user's natural-language task, run it through
``library.search_agents`` for keyword-rank, then re-rank the top candidates
using a small set of intent rules (build / refactor / audit / debug / design)
that map verbs to tier biases. Also surface the decision-tree branches the
agent should consult before recommending a technology.

Returned shape is intentionally narrow — ranked agents + ranked trees + a
plain-English "next step" pointing the caller at ``get_agent``. The caller's
LLM still picks; this tool just narrows the field from 47 candidates to 3.
"""

from __future__ import annotations

import re
from typing import Any

from . import agents as agents_mod
from . import library


# --------------------------------------------------------------------------- #
# Intent → tier bias rules                                                     #
# --------------------------------------------------------------------------- #
#
# Each rule is (regex_over_query, [agent_substrings_to_boost], score_boost).
# Substring match is intentional — it's robust to small naming changes
# (``apex-refactorer`` and ``apex-refactor-agent`` both match ``refactor``).

_INTENT_RULES: tuple[tuple[re.Pattern[str], tuple[str, ...], float], ...] = (
    # Verb-driven: refactor, consolidate, optimise, modernise, harden
    (re.compile(r"\brefactor(?:ing)?\b", re.I),       ("refactor", "consolidat"),     20.0),
    (re.compile(r"\bconsolidat(?:e|ing)\b", re.I),    ("consolidat", "refactor"),     20.0),
    (re.compile(r"\boptimi[sz]e\b", re.I),            ("optimi", "soql"),             15.0),
    (re.compile(r"\bdeploy\b|\bdeployment\b", re.I),  ("deploy", "changeset", "release"), 15.0),
    (re.compile(r"\baudit(?:ing)?\b|\breview\b", re.I),
                                                       ("audit-router", "auditor"),   20.0),
    (re.compile(r"\bdebug(?:ging)?\b", re.I),         ("debug",),                     20.0),
    (re.compile(r"\btest(?:ing|s)?\b", re.I),         ("test-class", "gen-tests"),    15.0),
    (re.compile(r"\bsecurity\b|\bcrud\b|\bfls\b", re.I),
                                                       ("security",),                 18.0),
    (re.compile(r"\bbuild\b|\bcreate\b|\bnew\b|\bgenerate\b", re.I),
                                                       ("builder", "designer"),       12.0),
    (re.compile(r"\bdesign\b", re.I),                 ("designer", "architect"),      15.0),
    (re.compile(r"\bmigrat(?:e|ing|ion)\b", re.I),    ("migrat",),                    15.0),
    (re.compile(r"\bplan\b", re.I),                   ("planner", "designer"),        10.0),
    (re.compile(r"\bsharing\b|\bowd\b", re.I),        ("sharing", "audit-router"),    18.0),
    (re.compile(r"\bvalidation rule(?:s)?\b", re.I),  ("audit-router", "validation"), 18.0),
    (re.compile(r"\bpicklist(?:s)?\b", re.I),         ("audit-router", "picklist"),   18.0),
    (re.compile(r"\bduplicate(?:s)?\b", re.I),        ("duplicate-rule",),            18.0),
    (re.compile(r"\bpermission set(?:s)?\b|\bpermset\b|\bprofile(?:s)?\b", re.I),
                                                       ("permission-set", "profile"),  15.0),
    (re.compile(r"\bflow(?:s)?\b", re.I),             ("flow-",),                     12.0),
    (re.compile(r"\blwc\b|\blightning web", re.I),    ("lwc-",),                      18.0),
    (re.compile(r"\bagentforce\b|\bagent action\b|\beinstein", re.I),
                                                       ("agentforce",),               18.0),
    (re.compile(r"\bcsv\b", re.I),                    ("csv-to-object",),             15.0),
    (re.compile(r"\bdata model\b", re.I),             ("data-model",),                15.0),
    (re.compile(r"\bfit gap\b|\bfit-gap\b", re.I),    ("fit-gap",),                   25.0),
    (re.compile(r"\bstor(?:y|ies)\b", re.I),          ("story-drafter",),             20.0),
)


_QUERY_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _query_tokens(query: str) -> set[str]:
    return {t for t in _QUERY_TOKEN_RE.findall(query.lower()) if len(t) > 2}


def _name_overlap_bonus(query_tokens: set[str], agent_name: str) -> float:
    """Tiebreaker: count agent-name tokens that also appear in the query.

    Uses prefix-stemming so simple morphology variants (``triggers`` ↔
    ``trigger``, ``migration`` ↔ ``migrate``) match. The 4-char prefix is a
    blunt instrument but works on the targeted vocabulary (Salesforce nouns
    + dev verbs); no inflection library worth depending on for this.

    "build apex SOAP callout"   + ``apex-builder``       → shares ``apex``   → +10
    "consolidate triggers"      + ``trigger-consolidator`` → ``trigger`` ↔ ``trigger`` → +20
    "migrate process builder"   + ``automation-migration-router`` → ``migrate`` ↔ ``migration`` → +10
    """
    name_tokens = {t for t in agent_name.replace("_", "-").split("-") if len(t) > 2}
    matches = 0
    for q in query_tokens:
        for n in name_tokens:
            # Prefix match — cheap stem.
            shared_prefix = min(len(q), len(n), 4)
            if q[:shared_prefix] == n[:shared_prefix] and shared_prefix >= 4:
                matches += 1
                break
    return 10.0 * matches


def _intent_rank(
    query: str,
    runtime_agents: dict[str, str],
) -> list[tuple[str, float]]:
    """Run every intent rule; return ``[(agent_name, total_boost), …]``
    sorted by boost magnitude.

    Cumulative scoring: an agent that matches multiple rules (e.g.
    ``permission-set-architect`` for both 'permission set' and 'design')
    rises higher than one that matches only one. Agents that match no
    rule are absent from the result.

    Includes a name-overlap tiebreaker: agents whose name tokens appear in
    the query get a small bonus, so "build apex" prefers ``apex-builder``
    over ``agentforce-builder`` even though both match the build rule.
    """
    boosts: dict[str, float] = {}
    for rule_re, substrings, boost in _INTENT_RULES:
        if not rule_re.search(query):
            continue
        for agent_name in runtime_agents:
            for sub in substrings:
                if sub in agent_name:
                    boosts[agent_name] = boosts.get(agent_name, 0.0) + boost
                    break
    # Apply name-overlap tiebreaker only to agents the rules already lit up.
    q_tokens = _query_tokens(query)
    for agent_name in list(boosts):
        boosts[agent_name] += _name_overlap_bonus(q_tokens, agent_name)
    return sorted(boosts.items(), key=lambda x: x[1], reverse=True)


# --------------------------------------------------------------------------- #
# Public tool                                                                  #
# --------------------------------------------------------------------------- #


#: Decision-tree score floor for inclusion in ``suggest_agent`` output.
#: Empirical (Phase 6 audit, 8 realistic queries against real corpus):
#:   - Relevant trees scored 40+ (flow-pattern-selector for "Flow vs Apex"
#:     hit 41; agentforce-capability-selector for "Agentforce action" hit 40.5)
#:   - Irrelevant noise scored 5-15 (performance-tuning kept showing up
#:     because its body matched any query containing "apex"; sharing-selection
#:     for unrelated audit queries scored 6)
#:   - One borderline case: performance-tuning matched "refactor this Apex
#:     class to use a trigger handler" at 15.3 — still noise.
#: 20 is the floor: anything below is more noise than signal on this
#: corpus. Callers can pass min_tree_score=0 to recover the v0.4.2
#: "always return top tree" behavior.
DEFAULT_MIN_TREE_SCORE = 20.0


def suggest_agent(
    task: str,
    limit: int = 3,
    include_decision_trees: bool = True,
    min_tree_score: float = DEFAULT_MIN_TREE_SCORE,
) -> dict[str, Any]:
    """Rank agents + decision trees for a free-text task description.

    Returns:
      ``agents``         — top-N runtime agents with relevance scores
      ``decision_trees`` — top decision-tree branches the agent should
                           consult BEFORE recommending a technology.
                           Filtered by ``min_tree_score`` (default 15);
                           below threshold the field is an empty list
                           and the next_step skips the tree-citation
                           sentence.
      ``next_step``      — one-line instruction pointing the caller at
                           ``get_agent`` for the top pick
    """
    if not isinstance(task, str) or not task.strip():
        return {
            "error": "task description is required",
            "agents": [],
            "decision_trees": [],
        }

    bounded = max(1, min(int(limit or 3), 10))

    classes = agents_mod._agent_classes()
    runtime_agents = {n: c for n, c in classes.items() if c == "runtime"}

    # Step 1 — intent-rank against the runtime roster. Verb / domain rules
    # are deterministic and strongly indicative; if any fire, they dominate
    # keyword frequency.
    intent_hits = _intent_rank(task, runtime_agents)

    if intent_hits:
        # Pull summaries for the top hits via the agent corpus index. We
        # already cache it in ``library``, so this is essentially free.
        agent_index = {d.name: d for d in library._agent_corpus()}
        top: list[dict[str, Any]] = []
        for name, score in intent_hits[:bounded]:
            doc = agent_index.get(name)
            top.append(
                {
                    "name": name,
                    "title": doc.title if doc else name,
                    "summary": doc.summary if doc else "",
                    "path": doc.path if doc else f"agents/{name}/AGENT.md",
                    "score": round(score, 3),
                }
            )
    else:
        # Step 2 fallback — no intent rule fired (rare; the rule set is
        # broad). Use keyword search and filter to runtime.
        keyword_payload = library.search_agents(query=task, limit=10)
        if "error" in keyword_payload:
            return keyword_payload
        keyword_hits = keyword_payload["agents"]
        top = [
            a for a in keyword_hits
            if classes.get(a["name"]) == "runtime"
        ][:bounded]

    # Step 3 — surface the decision trees that apply, when requested.
    # Filter by min_tree_score so the model isn't asked to cite a tree
    # that scored 5 (essentially irrelevant). Empirical: relevant trees
    # score 30+, irrelevant ones 5-15. See DEFAULT_MIN_TREE_SCORE.
    trees: list[dict[str, Any]] = []
    if include_decision_trees:
        tree_payload = library.search_decision_trees(query=task, limit=3)
        trees = [
            t for t in tree_payload.get("trees", [])
            if float(t.get("score", 0)) >= min_tree_score
        ]

    next_step = ""
    if top:
        first = top[0]
        if trees:
            next_step = (
                f"Call get_agent('{first['name']}') for the AGENT.md, then follow its "
                "Plan section. Cite the decision-tree branches above when picking a "
                "technology."
            )
        else:
            # No tree cleared the relevance threshold — drop the citation
            # instruction so the LLM doesn't go hunting for a tree that
            # doesn't apply.
            next_step = (
                f"Call get_agent('{first['name']}') for the AGENT.md, then follow its "
                "Plan section."
            )

    return {
        "task": task,
        "agents": top,
        "decision_trees": trees,
        "min_tree_score": min_tree_score,
        "next_step": next_step,
    }
