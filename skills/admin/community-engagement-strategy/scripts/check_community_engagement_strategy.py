#!/usr/bin/env python3
"""Checker script for the Community Engagement Strategy skill.

Lints the engagement-strategy artefact described in
``references/worked-examples.md`` section 8, and — when a metadata directory is
supplied — the ``Network`` and ``ManagedTopics`` files it deploys as.

Stdlib only. No pip dependencies.

Strategy YAML checks (``--file``, or every ``*.yaml`` / ``*.yml`` under
``--manifest-dir``):

1. Every goal carries ``id``, ``statement``, ``owner`` and ``status``; ids are
   unique; ``status`` sits in the allowed set. Every goal has a ``metric`` with
   a ``soql``, a ``source_object`` and a ``target``.
2. No metric asks the platform for something it refuses: an aggregate function
   over ``FeedItem`` ("The FeedItem object doesn't support aggregate functions
   in queries") or a ``NetworkScope`` filter ("You can't filter a feed item on
   the NetworkScope field"). A ``ChatterActivity`` query with no ``ParentId``
   filter is rejected too ("To query ChatterActivity, you must provide the
   ParentId"). ``TopicAssignment`` queries must carry a bound.
3. The reputation ladder is monotonic: ``lower_threshold`` strictly increasing,
   no duplicates, first level at 0, and every level explicitly ``label``-ed
   (an omitted label deploys as one of ten ``Level N`` defaults).
4. Every ``points_rules`` entry names a documented ``eventType``, and any entry
   whose ``points`` differ from the platform default carries a ``reason``.
5. Every content-calendar item has an ``owner``, a ``goal`` that exists, and a
   ``topic`` that appears in ``managed_topics``. The managed-topic list stays
   within the documented maximum of 25 navigational-or-featured topics.
6. The moderation block names an ``escalation_queue`` and an owner.
7. Repo paths under ``consumed_by`` / ``rules_owned_by`` resolve on disk.

Metadata checks (``--manifest-dir``):

8. Every ``*.network-meta.xml`` / ``*.network`` parses. Its ``reputationLevels``
   are monotonic and labelled, its ``pointsRule`` event types are documented,
   and ``enableReputation`` is consistent with the presence of levels/rules.
   ``enableKnowledgeable`` must be true if either endorsement event is weighted.
9. When a strategy YAML is also supplied, the deployed ladder must match the
   designed ladder label-for-label and threshold-for-threshold.
10. Every ``*.managedTopics`` file parses, ``managedTopicType`` sits in the
    documented enum, ``position`` is between 0 and 24, ``parentName`` is only
    used on navigational topics, and the file holds at most 25 topics.

Exit codes: 0 clean, 1 findings, 2 usage error.

Usage:
    python3 check_community_engagement_strategy.py --file acme-engagement-strategy.yaml
    python3 check_community_engagement_strategy.py --manifest-dir force-app/main/default
    python3 check_community_engagement_strategy.py --file s.yaml --manifest-dir force-app/main/default

Grounding (Summer '26 / v62 PDF text):
    Metadata API Developer Guide  — Network, ReputationLevel(Definitions),
        ReputationPointsRule(s), ManagedTopics/ManagedTopic
    Object Reference for Salesforce — FeedItem, ChatterActivity, NetworkMember,
        ReputationLevel, Topic, TopicAssignment
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MD_NS = "{http://soap.sforce.com/2006/04/metadata}"

ALLOWED_STATUS = {"draft", "proposed", "approved", "deferred", "rejected"}

# Metadata API Developer Guide, ReputationPointsRule.eventType — the 16
# documented values, with the platform default point value for each.
EVENT_TYPE_DEFAULTS = {
    "FeedItemWriteAPost": 1,
    "FeedItemWriteAComment": 1,
    "FeedItemReceiveAComment": 5,
    "FeedItemLikeSomething": 1,
    "FeedItemReceiveALike": 5,
    "FeedItemMentionSomeone": 1,
    "FeedItemSomeoneMentionsYou": 5,
    "FeedItemShareAPost": 1,
    "FeedItemSomeoneSharesYourPost": 5,
    "FeedItemPostAQuestion": 1,
    "FeedItemAnswerAQuestion": 5,
    "FeedItemReceiveAnAnswer": 5,
    "FeedItemMarkAnswerAsBest": 5,
    "FeedItemYourAnswerMarkedBest": 20,
    "FeedItemEndorseSomeoneForKnowledgeOnATopic": 5,
    "FeedItemEndorsedForKnowledgeOnATopic": 20,
}

# Both depend on Network.enableKnowledgeable, which "Determines if members can
# see who's knowledgeable on topics and endorse people for their knowledge on a
# topic". Weighting them without it rewards an action nobody can perform.
ENDORSEMENT_EVENTS = {
    "FeedItemEndorseSomeoneForKnowledgeOnATopic",
    "FeedItemEndorsedForKnowledgeOnATopic",
}

# ManagedTopic.managedTopicType — "The topic type: 'Navigational' or 'Featured'".
MANAGED_TOPIC_TYPES = {"Navigational", "Featured"}

# ManagedTopic.position — "Enter a number between 0 and 24. (The maximum amount
# of navigational or featured topics is 25.)"
MAX_MANAGED_TOPICS = 25
MAX_TOPIC_POSITION = 24

# The default label set the platform substitutes when <label> is omitted.
GENERIC_LABEL = re.compile(r"^\s*level\s*\d+\s*$", re.IGNORECASE)

AGGREGATE_FN = re.compile(r"\b(count|sum|avg|min|max|count_distinct)\s*\(", re.IGNORECASE)
FROM_OBJECT = re.compile(r"\bfrom\s+([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE)

REPO_PATH_KEYS = ("consumed_by", "rules_owned_by", "network_file", "file")


# ---------------------------------------------------------------------------
# Minimal YAML subset reader
# ---------------------------------------------------------------------------

class YamlError(Exception):
    """Raised when the document uses YAML this reader deliberately does not."""


def _strip_comment(line: str) -> str:
    """Remove a trailing ``#`` comment that is not inside quotes."""
    out = []
    quote = ""
    for i, ch in enumerate(line):
        if quote:
            out.append(ch)
            if ch == quote:
                quote = ""
            continue
        if ch in "\"'":
            quote = ch
            out.append(ch)
            continue
        if ch == "#" and (i == 0 or line[i - 1] in " \t"):
            break
        out.append(ch)
    return "".join(out).rstrip()


def _scalar(raw: str) -> object:
    raw = raw.strip()
    if not raw:
        return ""
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1]
    low = raw.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    if low in ("null", "~"):
        return None
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    return raw


def _lines(text: str) -> list[tuple[int, int, str]]:
    """Return (line_no, indent, content) for every significant line.

    Multi-line scalars introduced with ``>`` or ``|`` are collapsed to a marker
    so the strategy file can carry a wrapped SOQL string without confusing the
    block parser.
    """
    out: list[tuple[int, int, str]] = []
    block_indent: int | None = None
    for n, raw in enumerate(text.splitlines(), start=1):
        if block_indent is not None:
            if raw.strip() and (len(raw) - len(raw.lstrip(" "))) > block_indent:
                continue
            block_indent = None
        stripped = _strip_comment(raw)
        if not stripped.strip():
            continue
        indent = len(stripped) - len(stripped.lstrip(" "))
        content = stripped.strip()
        if content.endswith((": >", ": |", ": >-", ": |-", ": |+", ": >+")):
            block_indent = indent
            key = content.split(":", 1)[0]
            content = f"{key}: <block>"
        out.append((n, indent, content))
    return out


def _parse_block(rows: list[tuple[int, int, str]], pos: int, indent: int) -> tuple[object, int]:
    """Parse a mapping or a sequence at ``indent``; return (value, next_pos)."""
    if pos >= len(rows):
        return {}, pos
    if rows[pos][2].startswith("- "):
        items: list[object] = []
        while pos < len(rows) and rows[pos][1] == indent and rows[pos][2].startswith("- "):
            line_no, _, content = rows[pos]
            head = content[2:].strip()
            pos += 1
            if ":" in head and not head.startswith(("\"", "'")):
                key, _, rest = head.partition(":")
                item: dict[str, object] = {"__line__": line_no}
                child_indent = indent + 2
                if rest.strip():
                    item[key.strip()] = _scalar(rest)
                elif pos < len(rows) and rows[pos][1] > child_indent:
                    nested, pos = _parse_block(rows, pos, rows[pos][1])
                    item[key.strip()] = nested
                else:
                    item[key.strip()] = ""
                while pos < len(rows) and rows[pos][1] >= child_indent and not rows[pos][2].startswith("- "):
                    if rows[pos][1] != child_indent:
                        raise YamlError(
                            f"line {rows[pos][0]}: unexpected indentation inside a list item"
                        )
                    k, _, v = rows[pos][2].partition(":")
                    pos += 1
                    if v.strip():
                        item[k.strip()] = _scalar(v)
                    elif pos < len(rows) and rows[pos][1] > child_indent:
                        nested, pos = _parse_block(rows, pos, rows[pos][1])
                        item[k.strip()] = nested
                    else:
                        item[k.strip()] = ""
                items.append(item)
            else:
                items.append(_scalar(head))
        return items, pos

    mapping: dict[str, object] = {}
    while pos < len(rows) and rows[pos][1] == indent:
        line_no, _, content = rows[pos]
        if content.startswith("- "):
            break
        if ":" not in content:
            raise YamlError(f"line {line_no}: expected 'key: value', got {content!r}")
        key, _, rest = content.partition(":")
        pos += 1
        if rest.strip():
            mapping[key.strip()] = _scalar(rest)
        elif pos < len(rows) and rows[pos][1] > indent:
            nested, pos = _parse_block(rows, pos, rows[pos][1])
            mapping[key.strip()] = nested
        else:
            mapping[key.strip()] = ""
    return mapping, pos


def load_yaml(text: str) -> dict:
    rows = _lines(text)
    if not rows:
        return {}
    value, _ = _parse_block(rows, 0, rows[0][1])
    if not isinstance(value, dict):
        raise YamlError("the document's top level must be a mapping")
    return value


# ---------------------------------------------------------------------------
# XML helpers
# ---------------------------------------------------------------------------

def child(element: ET.Element, tag: str) -> ET.Element | None:
    """First ``tag`` child, namespaced or not, or None.

    Written as an explicit ``is not None`` walk: an ElementTree element with no
    children is falsy, so ``element.find(a) or element.find(b)`` silently
    discards a real leaf element.
    """
    found = element.find(f"{MD_NS}{tag}")
    if found is None:
        found = element.find(tag)
    if found is None:
        return None
    return found


def child_text(element: ET.Element, tag: str) -> str | None:
    found = child(element, tag)
    if found is None:
        return None
    return (found.text or "").strip()


def children(element: ET.Element, tag: str) -> list[ET.Element]:
    found = element.findall(f"{MD_NS}{tag}")
    if not found:
        found = element.findall(tag)
    return found


def parse_xml(path: Path) -> tuple[ET.Element | None, str | None]:
    try:
        return ET.parse(path).getroot(), None
    except ET.ParseError as exc:
        return None, str(exc)
    except OSError as exc:
        return None, str(exc)


# ---------------------------------------------------------------------------
# Shared ladder validation
# ---------------------------------------------------------------------------

def check_ladder(
    levels: list[tuple[str | None, object, str]],
    where: str,
) -> list[str]:
    """Validate a reputation ladder given (label, threshold, position-label) rows."""
    issues: list[str] = []
    seen: dict[float, str] = {}
    previous: float | None = None

    for label, raw_threshold, at in levels:
        if label is None or not str(label).strip():
            issues.append(
                f"{where}: level {at} has no label. ReputationLevel.label is optional, and "
                f"an omitted label does not stay blank — the platform substitutes one of ten "
                f"defaults, 'Level 1' through 'Level 10'. Name every level explicitly."
            )
        elif GENERIC_LABEL.match(str(label)):
            issues.append(
                f"{where}: level {at} is labelled {str(label)!r}. That is the platform's "
                f"fallback label, not a design decision. Give it a domain-meaningful name."
            )

        try:
            threshold = float(raw_threshold)
        except (TypeError, ValueError):
            issues.append(
                f"{where}: level {at} has a non-numeric lowerThreshold "
                f"({raw_threshold!r}). It is a required double."
            )
            continue

        if threshold < 0:
            issues.append(f"{where}: level {at} has a negative lowerThreshold ({threshold:g}).")

        if threshold in seen:
            issues.append(
                f"{where}: level {at} repeats lowerThreshold {threshold:g}, already used by "
                f"level {seen[threshold]}. Only the lower bound is authored — the application "
                f"derives each band's upper value — so a duplicate deploys cleanly and produces "
                f"a ladder nobody designed."
            )
        else:
            seen[threshold] = at

        if previous is not None and threshold <= previous:
            issues.append(
                f"{where}: level {at} has lowerThreshold {threshold:g}, which is not greater "
                f"than the previous level's {previous:g}. Thresholds must be strictly "
                f"increasing in the order the levels are listed."
            )
        previous = threshold

    if levels:
        first_label, first_threshold, first_at = levels[0]
        try:
            if float(first_threshold) != 0:
                issues.append(
                    f"{where}: the first level ({first_at}, {first_label!r}) starts at "
                    f"{float(first_threshold):g}, not 0. Members below the lowest threshold "
                    f"have no level to sit in."
                )
        except (TypeError, ValueError):
            pass

    return issues


def check_points_rules(
    rules: list[tuple[str, object, str | None, str]],
    where: str,
    enable_knowledgeable: bool | None,
    require_reason: bool = True,
) -> list[str]:
    """Validate (eventType, points, reason, position-label) rows.

    ``require_reason`` is off for the ``Network`` XML pass: the metadata has
    nowhere to record why a weight deviates from the platform default, so that
    finding belongs to the strategy YAML only.
    """
    issues: list[str] = []
    seen: set[str] = set()
    weighted_endorsements: list[str] = []

    for event_type, raw_points, reason, at in rules:
        event_type = str(event_type).strip()
        if event_type not in EVENT_TYPE_DEFAULTS:
            issues.append(
                f"{where}: points rule {at} names eventType {event_type!r}, which is not one of "
                f"the 16 documented values. Valid values: "
                f"{', '.join(sorted(EVENT_TYPE_DEFAULTS))}."
            )
            continue
        if event_type in seen:
            issues.append(f"{where}: eventType {event_type!r} appears more than once ({at}).")
        seen.add(event_type)

        try:
            points = int(raw_points)
        except (TypeError, ValueError):
            issues.append(
                f"{where}: points rule {at} ({event_type}) has non-integer points "
                f"({raw_points!r}). ReputationPointsRule.points is a required int."
            )
            continue

        default = EVENT_TYPE_DEFAULTS[event_type]
        if require_reason and points != default and not (reason and str(reason).strip()):
            issues.append(
                f"{where}: {event_type} is set to {points} against the platform default of "
                f"{default} with no 'reason'. Every deviation is a claim that this community "
                f"differs from the baseline — write it down where the next admin will read it."
            )

        if event_type in ENDORSEMENT_EVENTS and points > 0:
            weighted_endorsements.append(event_type)

    if weighted_endorsements and enable_knowledgeable is False:
        issues.append(
            f"{where}: {', '.join(sorted(weighted_endorsements))} carry points, but "
            f"enableKnowledgeable is false. Endorsement events reward an action members "
            f"cannot perform unless Network.enableKnowledgeable is on."
        )

    return issues


# ---------------------------------------------------------------------------
# Strategy YAML checks
# ---------------------------------------------------------------------------

def _rows(doc: dict, key: str) -> list[dict]:
    value = doc.get(key)
    if isinstance(value, list):
        return [row for row in value if isinstance(row, dict)]
    return []


def _at(row: dict) -> str:
    line = row.get("__line__")
    return f" (line {line})" if line else ""


def _mapping(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def check_soql(soql: str, label: str, where: str) -> list[str]:
    """Reject metric queries the platform will not run."""
    issues: list[str] = []
    text = " ".join(str(soql).split())
    if not text:
        return issues

    match = FROM_OBJECT.search(text)
    obj = match.group(1) if match else ""
    obj_lower = obj.lower()

    if obj_lower == "feeditem":
        if AGGREGATE_FN.search(text) or re.search(r"\bcount\s*\(\s*\)", text, re.IGNORECASE):
            issues.append(
                f"{where}: metric '{label}' aggregates over FeedItem. The Object Reference is "
                f"explicit: \"The FeedItem object doesn't support aggregate functions in "
                f"queries.\" Page the rows and count client-side, or move the metric onto "
                f"NetworkMember or Case."
            )
        if re.search(r"networkscope\s*(=|!=|\bin\b|\blike\b)", text, re.IGNORECASE):
            issues.append(
                f"{where}: metric '{label}' filters FeedItem on NetworkScope. \"You can't "
                f"filter a feed item on the NetworkScope field.\" Scope by the parent Group or "
                f"User that belongs to the site, or by NetworkMember membership."
            )

    if obj_lower == "chatteractivity" and not re.search(r"parentid\s*(=|\bin\b)", text, re.IGNORECASE):
        issues.append(
            f"{where}: metric '{label}' queries ChatterActivity without a ParentId filter. "
            f"\"To query ChatterActivity, you must provide the ParentId.\" There is no "
            f"site-wide sweep; take the denominator from NetworkMember instead."
        )

    if obj_lower == "topicassignment":
        bounded = re.search(r"\blimit\s+\d+", text, re.IGNORECASE) or re.search(
            r"\bwhere\b[^|]*\b(id|entityid)\s*=", text, re.IGNORECASE
        )
        if not bounded:
            issues.append(
                f"{where}: metric '{label}' queries TopicAssignment unbounded. The guide asks "
                f"for a \"LIMIT clause of 1,100 records or fewer\" or a '=' filter on Id or "
                f"Entity. Add one, or build a report type instead."
            )

    return issues


def check_strategy(path: Path, repo_root: Path) -> tuple[list[str], dict]:
    issues: list[str] = []
    try:
        doc = load_yaml(path.read_text(encoding="utf-8"))
    except YamlError as exc:
        return [f"{path}: {exc}"], {}
    except OSError as exc:
        return [f"{path}: {exc}"], {}

    goals = _rows(doc, "goals")
    if not goals:
        return (
            [
                f"{path}: no 'goals:' list found. An engagement strategy without goals cannot "
                f"be reviewed; see references/worked-examples.md section 8 for the shape."
            ],
            {},
        )

    # 1 — goals and their metrics
    seen_goals: dict[str, int] = {}
    for row in goals:
        label = str(row.get("id") or row.get("statement") or "<unnamed goal>")
        for field in ("id", "statement", "owner", "status"):
            if not str(row.get(field, "")).strip():
                issues.append(
                    f"{path}: goal '{label}'{_at(row)} is missing '{field}'. Every goal needs an "
                    f"id, a statement, a named owner and a status."
                )
        status = str(row.get("status", "")).strip().lower()
        if status and status not in ALLOWED_STATUS:
            issues.append(
                f"{path}: goal '{label}'{_at(row)} has status {status!r}; allowed: "
                f"{', '.join(sorted(ALLOWED_STATUS))}."
            )
        gid = str(row.get("id", "")).strip()
        if gid:
            if gid in seen_goals:
                issues.append(
                    f"{path}: goal id '{gid}'{_at(row)} is already used at line "
                    f"{seen_goals[gid]}. Ids must be unique."
                )
            else:
                seen_goals[gid] = int(row.get("__line__") or 0)

        metric = _mapping(row.get("metric"))
        if not metric:
            issues.append(
                f"{path}: goal '{label}'{_at(row)} has no 'metric'. A goal with no metric is a "
                f"wish; give it a name, a SOQL source and a target."
            )
            continue
        for field in ("name", "soql", "source_object"):
            if not str(metric.get(field, "")).strip():
                issues.append(
                    f"{path}: goal '{label}'{_at(row)} metric is missing '{field}'."
                )
        if str(metric.get("target", "")).strip() == "":
            issues.append(
                f"{path}: goal '{label}'{_at(row)} metric has no 'target'. A metric with no "
                f"target cannot pass or fail at the quarterly review."
            )
        # 2 — metrics the platform refuses
        soql = str(metric.get("soql", ""))
        issues.extend(check_soql(soql, str(metric.get("name", label)), str(path)))

    # 3 + 4 — the ladder
    reputation = _mapping(doc.get("reputation"))
    ladder_rows = [row for row in (reputation.get("ladder") or []) if isinstance(row, dict)]
    designed_ladder: list[tuple[str, float]] = []
    if reputation.get("enabled") is True and not ladder_rows:
        issues.append(
            f"{path}: reputation.enabled is true but no 'ladder' is defined. With "
            f"enableReputation on and no levels supplied, \"the default values are used\" — "
            f"which is how a site ends up displaying 'Level 1' through 'Level 10'."
        )
    if ladder_rows:
        rows = [
            (
                row.get("label"),
                row.get("lower_threshold"),
                str(row.get("level") or row.get("label") or "?"),
            )
            for row in ladder_rows
        ]
        issues.extend(check_ladder(rows, f"{path} (strategy ladder)"))
        for row in ladder_rows:
            try:
                designed_ladder.append(
                    (str(row.get("label", "")).strip(), float(row.get("lower_threshold")))
                )
            except (TypeError, ValueError):
                pass

    rule_rows = [row for row in (reputation.get("points_rules") or []) if isinstance(row, dict)]
    if rule_rows:
        enable_knowledgeable = reputation.get("enable_knowledgeable")
        issues.extend(
            check_points_rules(
                [
                    (
                        str(row.get("event_type", "")),
                        row.get("points"),
                        row.get("reason"),
                        f"line {row.get('__line__', '?')}",
                    )
                    for row in rule_rows
                ],
                f"{path} (strategy points rules)",
                enable_knowledgeable if isinstance(enable_knowledgeable, bool) else None,
            )
        )

    # 5 — managed topics and the content calendar
    managed = _mapping(doc.get("managed_topics"))
    topic_rows = [row for row in (managed.get("topics") or []) if isinstance(row, dict)]
    topic_names = {str(row.get("name", "")).strip() for row in topic_rows}
    topic_names.discard("")

    if len(topic_rows) > MAX_MANAGED_TOPICS:
        issues.append(
            f"{path}: managed_topics lists {len(topic_rows)} topics. The guide caps navigational "
            f"and featured topics at {MAX_MANAGED_TOPICS} (position accepts 0-{MAX_TOPIC_POSITION}). "
            f"Retire before adding."
        )
    for row in topic_rows:
        name = str(row.get("name", "")).strip()
        ttype = str(row.get("type", "")).strip()
        if ttype and ttype not in MANAGED_TOPIC_TYPES:
            issues.append(
                f"{path}: topic '{name}'{_at(row)} has type {ttype!r}; managedTopicType is "
                f"'Navigational' or 'Featured'."
            )
        if not str(row.get("owner", "")).strip():
            issues.append(
                f"{path}: topic '{name}'{_at(row)} has no owner. A topic with no owner has no "
                f"one to retire it at the quarterly review."
            )
        parent = str(row.get("parent", "")).strip()
        if parent:
            if ttype == "Featured":
                issues.append(
                    f"{path}: topic '{name}'{_at(row)} is Featured and names a parent. \"Only "
                    f"navigational topics support parent-child relationships.\""
                )
            elif parent not in topic_names:
                issues.append(
                    f"{path}: topic '{name}'{_at(row)} names parent {parent!r}, which is not in "
                    f"the topic list."
                )

    calendar = _rows(doc, "content_calendar")
    if not calendar:
        issues.append(
            f"{path}: no 'content_calendar:' list. A strategy with a ladder and no calendar "
            f"rewards behaviour nobody has been given a reason to perform."
        )
    seen_items: set[str] = set()
    for row in calendar:
        label = str(row.get("id") or row.get("item") or "<unnamed item>")
        if not str(row.get("owner", "")).strip():
            issues.append(f"{path}: calendar item '{label}'{_at(row)} has no owner.")
        item_id = str(row.get("id", "")).strip()
        if item_id:
            if item_id in seen_items:
                issues.append(f"{path}: calendar item id '{item_id}'{_at(row)} is not unique.")
            seen_items.add(item_id)
        topic = str(row.get("topic", "")).strip()
        if not topic:
            issues.append(
                f"{path}: calendar item '{label}'{_at(row)} names no topic. An item with no "
                f"managed topic has no navigation path, no TopicAssignment row, and no "
                f"Topic.TalkingAbout reading afterwards."
            )
        elif topic_names and topic not in topic_names:
            issues.append(
                f"{path}: calendar item '{label}'{_at(row)} names topic {topic!r}, which is not "
                f"in the managed_topics list. Add the topic, or point the item at one that exists."
            )
        goal = str(row.get("goal", "")).strip()
        if goal and seen_goals and goal not in seen_goals:
            issues.append(
                f"{path}: calendar item '{label}'{_at(row)} names goal {goal!r}, which is not "
                f"declared in 'goals'."
            )

    # 6 — moderation and escalation
    moderation = _mapping(doc.get("moderation"))
    if not moderation:
        issues.append(
            f"{path}: no 'moderation:' block. The strategy owns the escalation policy even "
            f"though admin/experience-cloud-moderation owns the rules."
        )
    else:
        if not str(moderation.get("escalation_queue", "")).strip():
            issues.append(
                f"{path}: moderation names no 'escalation_queue'. A ladder rewards answering "
                f"and does nothing for the questions nobody answers — name where those go."
            )
        if not str(moderation.get("escalation_owner", "")).strip():
            issues.append(f"{path}: moderation names no 'escalation_owner'.")

    # 7 — repo paths resolve
    def walk_paths(value: object, key: str) -> None:
        if isinstance(value, str):
            candidate = value.strip()
            if candidate.startswith(("skills/", "agents/", "templates/", "standards/")):
                if not (repo_root / candidate).exists():
                    issues.append(
                        f"{path}: '{key}' points at {candidate!r}, which does not exist under "
                        f"{repo_root}."
                    )
        elif isinstance(value, list):
            for entry in value:
                walk_paths(entry, key)

    for key in REPO_PATH_KEYS:
        walk_paths(doc.get(key), key)
        walk_paths(moderation.get(key), key)

    return issues, {"ladder": designed_ladder, "path": path}


# ---------------------------------------------------------------------------
# Network metadata checks
# ---------------------------------------------------------------------------

def check_network(path: Path, designed: dict) -> list[str]:
    issues: list[str] = []
    root, error = parse_xml(path)
    if root is None:
        return [f"{path}: does not parse as XML ({error})."]

    enable_reputation = child_text(root, "enableReputation")
    enable_knowledgeable = child_text(root, "enableKnowledgeable")

    levels_parent = child(root, "reputationLevels")
    level_elements: list[ET.Element] = []
    if levels_parent is not None:
        level_elements = children(levels_parent, "level")

    rules_parent = child(root, "reputationPointsRules")
    rule_elements: list[ET.Element] = []
    if rules_parent is not None:
        rule_elements = children(rules_parent, "pointsRule")

    if enable_reputation is not None and enable_reputation.lower() == "false":
        if level_elements or rule_elements:
            issues.append(
                f"{path}: enableReputation is false but reputationLevels/reputationPointsRules "
                f"are present. That is dead configuration — nothing is calculated or displayed."
            )
        return issues

    if enable_reputation is None and (level_elements or rule_elements):
        issues.append(
            f"{path}: reputation levels or points rules are present with no enableReputation "
            f"element. Set it explicitly rather than relying on whatever the org already has."
        )

    if enable_reputation is not None and enable_reputation.lower() == "true" and not level_elements:
        issues.append(
            f"{path}: enableReputation is true with no reputationLevels. \"If no "
            f"reputationLevels or reputationPointsRules are defined in the data file, the "
            f"default values are used\" — including the 'Level 1' … 'Level 10' labels."
        )

    deployed: list[tuple[str, float]] = []
    if level_elements:
        rows: list[tuple[str | None, object, str]] = []
        for index, level in enumerate(level_elements, start=1):
            label = child_text(level, "label")
            threshold = child_text(level, "lowerThreshold")
            if threshold is None:
                issues.append(
                    f"{path}: level {index} has no lowerThreshold. It is a required field."
                )
                continue
            rows.append((label, threshold, str(index)))
            try:
                deployed.append((label or "", float(threshold)))
            except ValueError:
                pass
        issues.extend(check_ladder(rows, f"{path} (Network)"))

    if rule_elements:
        issues.extend(
            check_points_rules(
                [
                    (
                        child_text(rule, "eventType") or "",
                        child_text(rule, "points"),
                        None,  # the XML has nowhere to record a reason; the YAML does
                        f"pointsRule {index}",
                    )
                    for index, rule in enumerate(rule_elements, start=1)
                ],
                f"{path} (Network)",
                False if (enable_knowledgeable or "").lower() == "false" else None,
                require_reason=False,
            )
        )
        weighted = [
            child_text(rule, "eventType")
            for rule in rule_elements
            if (child_text(rule, "eventType") or "") in ENDORSEMENT_EVENTS
            and (child_text(rule, "points") or "0").lstrip("-").isdigit()
            and int(child_text(rule, "points") or "0") > 0
        ]
        if weighted and enable_knowledgeable is None:
            issues.append(
                f"{path}: {', '.join(w for w in weighted if w)} carry points but the file does "
                f"not set enableKnowledgeable. Endorsement events depend on it; set it "
                f"explicitly so the reward is not silently unreachable."
            )

    # 9 — deployed ladder must match the designed ladder
    design_ladder = designed.get("ladder") or []
    if design_ladder and deployed:
        if len(design_ladder) != len(deployed):
            issues.append(
                f"{path}: the deployed ladder has {len(deployed)} levels; the strategy at "
                f"{designed.get('path')} designs {len(design_ladder)}. One of the two was "
                f"edited without the other."
            )
        else:
            for index, ((d_label, d_threshold), (x_label, x_threshold)) in enumerate(
                zip(design_ladder, deployed), start=1
            ):
                if d_label != x_label or d_threshold != x_threshold:
                    issues.append(
                        f"{path}: level {index} deploys as ({x_label!r}, {x_threshold:g}) but "
                        f"the strategy designs ({d_label!r}, {d_threshold:g}). Reconcile before "
                        f"deploying — the site shows the XML, the review reads the YAML."
                    )

    return issues


# ---------------------------------------------------------------------------
# ManagedTopics metadata checks
# ---------------------------------------------------------------------------

def check_managed_topics(path: Path) -> list[str]:
    issues: list[str] = []
    root, error = parse_xml(path)
    if root is None:
        return [f"{path}: does not parse as XML ({error})."]

    topics = children(root, "ManagedTopic")
    if len(topics) > MAX_MANAGED_TOPICS:
        issues.append(
            f"{path}: {len(topics)} managed topics. \"The maximum amount of navigational or "
            f"featured topics is 25.\""
        )

    names = {(child_text(t, "name") or "").strip() for t in topics}
    names.discard("")
    positions: dict[tuple[str, int], str] = {}

    for index, topic in enumerate(topics, start=1):
        name = (child_text(topic, "name") or "").strip() or f"<topic {index}>"
        ttype = (child_text(topic, "managedTopicType") or "").strip()
        if not ttype:
            issues.append(f"{path}: topic '{name}' has no managedTopicType.")
        elif ttype not in MANAGED_TOPIC_TYPES:
            issues.append(
                f"{path}: topic '{name}' has managedTopicType {ttype!r}. The metadata guide "
                f"documents 'Navigational' or 'Featured' for this field."
            )

        raw_position = child_text(topic, "position")
        if raw_position is None or raw_position == "":
            issues.append(f"{path}: topic '{name}' has no position.")
        else:
            try:
                position = int(raw_position)
            except ValueError:
                issues.append(f"{path}: topic '{name}' has non-integer position {raw_position!r}.")
            else:
                if position < 0 or position > MAX_TOPIC_POSITION:
                    issues.append(
                        f"{path}: topic '{name}' has position {position}. \"Enter a number "
                        f"between 0 and {MAX_TOPIC_POSITION}.\""
                    )
                parent = (child_text(topic, "parentName") or "").strip()
                key = (f"{ttype}|{parent}", position)
                if key in positions:
                    issues.append(
                        f"{path}: topic '{name}' repeats position {position} within "
                        f"{ttype or '<no type>'} under parent {parent or '<top level>'}, already "
                        f"used by '{positions[key]}'. Ordering becomes arbitrary."
                    )
                else:
                    positions[key] = name

        parent = (child_text(topic, "parentName") or "").strip()
        if parent:
            if ttype == "Featured":
                issues.append(
                    f"{path}: topic '{name}' is Featured and sets parentName. \"Only "
                    f"navigational topics support parent-child relationships.\""
                )
            elif parent not in names:
                issues.append(
                    f"{path}: topic '{name}' names parentName {parent!r}, which is not a topic "
                    f"in this file."
                )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "skills").is_dir() and (candidate / "standards").is_dir():
            return candidate
    return start


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Lint a community engagement-strategy artefact (YAML) and, when a metadata "
            "directory is given, the Network and ManagedTopics files it deploys as."
        ),
    )
    parser.add_argument(
        "--file",
        default=None,
        help="Path to an engagement-strategy YAML. See references/worked-examples.md section 8.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help=(
            "Salesforce metadata directory. Scanned for *.network-meta.xml / *.network and "
            "*.managedTopics, and for *.yaml / *.yml strategy artefacts when --file is absent."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.file and not args.manifest_dir:
        print(
            "usage error: pass --file <strategy.yaml> and/or --manifest-dir <metadata dir>.",
            file=sys.stderr,
        )
        return 2

    issues: list[str] = []
    checked = 0
    repo_root = find_repo_root(Path(__file__).resolve().parent)

    strategy_files: list[Path] = []
    if args.file:
        candidate = Path(args.file)
        if not candidate.is_file():
            print(f"usage error: --file not found: {candidate}", file=sys.stderr)
            return 2
        strategy_files.append(candidate)

    manifest_dir: Path | None = None
    if args.manifest_dir:
        manifest_dir = Path(args.manifest_dir)
        if not manifest_dir.is_dir():
            print(f"usage error: --manifest-dir not found: {manifest_dir}", file=sys.stderr)
            return 2
        if not strategy_files:
            strategy_files.extend(sorted(manifest_dir.rglob("*.yaml")))
            strategy_files.extend(sorted(manifest_dir.rglob("*.yml")))

    designed: dict = {}
    for strategy in strategy_files:
        checked += 1
        found, parsed = check_strategy(strategy, repo_root)
        issues.extend(found)
        if parsed.get("ladder") and not designed:
            designed = parsed

    if manifest_dir is not None:
        networks = sorted(manifest_dir.rglob("*.network-meta.xml"))
        networks += sorted(manifest_dir.rglob("*.network"))
        for network in networks:
            checked += 1
            issues.extend(check_network(network, designed))

        for topics in sorted(manifest_dir.rglob("*.managedTopics")):
            checked += 1
            issues.extend(check_managed_topics(topics))

    if checked == 0:
        print(
            "No engagement-strategy YAML, Network or ManagedTopics metadata found. "
            "Nothing to check.",
            file=sys.stderr,
        )
        return 0

    if not issues:
        print(f"No community engagement issues found ({checked} file(s) checked).")
        return 0

    for issue in issues:
        print(f"ERROR: {issue}", file=sys.stderr)
    print(f"\n{len(issues)} finding(s) across {checked} file(s) checked.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
