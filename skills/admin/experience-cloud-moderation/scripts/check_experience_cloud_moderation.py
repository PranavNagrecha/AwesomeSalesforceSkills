#!/usr/bin/env python3
"""Checker script for Experience Cloud Moderation skill.

Scans a Salesforce metadata directory (--manifest-dir) for:

- ModerationRule files, suffix `.rule` or `.rule-meta.xml` (api_meta 264 L92203-92384)
    ERROR  unparseable XML; missing Required action / active / masterLabel; an invalid
           action or type value; an entitiesAndFields entry missing Required entityName
    WARN   a rule with neither entitiesAndFields nor userCriteria (nothing to match on);
           more than three distinct keywordList references in one rule (L92219);
           more than 30 rules in the tree (the org limit, L92218)
    INFO   inactive rules; the reserved FreezeAndNotify action
- KeywordList files, suffix `.keywords` or `.keywords-meta.xml` (api_meta 264 L84916-84990)
    ERROR  unparseable XML; missing Required masterLabel; a <keyword> that is empty
    WARN   no keywords; more than 2,000 keywords; a keyword over 100 characters; a keyword
           containing `*` (wildcards are not supported, L84967); more than 30 lists
- Network files (reputation, api_meta 264 L93597-93603, L94391-94448)
    ERROR  a pointsRule eventType outside the documented 16 events; a level missing the
           Required lowerThreshold
- Permission sets: INFO if none of the permission sets or profiles contains a moderation
  permission, using names that are UNVERIFIED (2026-10-20): `ModerateNetworkFeeds` is the
  Help-sourced API name of Moderate Experiences Feeds and is not in the corpus.

Removed from the earlier version: the `.moderationRule` / `.keywordList` suffixes (the guide
gives `.rule` and `.keywords`), the `criteriaItems` element (not a ModerationRule field), and
the heuristic that Flag/Review rules without a Block rule are a gap.

Exit codes: ERROR findings exit 1 always; WARN and INFO findings exit 0 unless --strict; a
directory with nothing to check prints one WARN and exits 0; a missing path is an ERROR and
exits 1. Stdlib only.

Usage:
    python3 check_experience_cloud_moderation.py --manifest-dir path/to/metadata [--strict]
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ACTIONS = {"Block", "Review", "Replace", "Flag", "FreezeAndNotify"}  # L92250-92254
RULE_TYPES = {"Content", "Rate"}  # L92318-92319
EVENT_TYPES = {  # L94414-94429
    "FeedItemWriteAPost", "FeedItemWriteAComment", "FeedItemReceiveAComment", "FeedItemLikeSomething",
    "FeedItemReceiveALike", "FeedItemMentionSomeone", "FeedItemSomeoneMentionsYou", "FeedItemShareAPost",
    "FeedItemSomeoneSharesYourPost", "FeedItemPostAQuestion", "FeedItemAnswerAQuestion",
    "FeedItemReceiveAnAnswer", "FeedItemMarkAnswerAsBest", "FeedItemYourAnswerMarkedBest",
    "FeedItemEndorseSomeoneForKnowledgeOnATopic", "FeedItemEndorsedForKnowledgeOnATopic",
}
MODERATE_PERMISSION_NAMES = ("ModerateNetworkFeeds",)  # UNVERIFIED 2026-10-20: Help-sourced name


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check Experience Cloud moderation metadata for common configuration issues.",
    )
    parser.add_argument("--manifest-dir", default=".", help="Root directory of the Salesforce metadata project (default: current directory).")
    parser.add_argument("--strict", action="store_true", help="exit 1 on WARN and INFO findings too")
    return parser.parse_args()


def files_with(root: Path, *suffixes: str) -> list[Path]:
    return sorted(p for p in root.rglob("*") if p.is_file() and any(p.name.endswith(s) for s in suffixes))


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def kids(el: ET.Element, name: str) -> list[ET.Element]:
    return [c for c in el if local(c.tag) == name]


def text_of(el: ET.Element, name: str) -> str | None:
    found = kids(el, name)
    return (found[0].text or "").strip() if found else None


def check_rules(root: Path) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    rules = files_with(root, ".rule", ".rule-meta.xml")
    if len(rules) > 30:
        out.append(("WARN", f"{len(rules)} moderation rule files; the org limit is 30 rules, content and rate together (api_meta 264 L92218)"))
    for path in rules:
        try:
            el = ET.parse(path).getroot()
        except (ET.ParseError, OSError) as exc:
            out.append(("ERROR", f"{path.name}: XML does not parse ({exc})"))
            continue
        for field in ("action", "active", "masterLabel"):
            if not text_of(el, field):
                out.append(("ERROR", f"{path.name}: <{field}> is Required (api_meta 264 L92248-92266)"))
        action = text_of(el, "action")
        if action and action not in ACTIONS:
            out.append(("ERROR", f"{path.name}: action '{action}' is not one of {sorted(ACTIONS)}"))
        if action == "FreezeAndNotify":
            out.append(("INFO", f"{path.name}: FreezeAndNotify is reserved for future use (L92254)"))
        rtype = text_of(el, "type")
        if rtype and rtype not in RULE_TYPES:
            out.append(("ERROR", f"{path.name}: type '{rtype}' is not one of {sorted(RULE_TYPES)}"))
        if (text_of(el, "active") or "").lower() == "false":
            out.append(("INFO", f"{path.name}: rule is inactive (verify intentional)"))
        entries = kids(el, "entitiesAndFields")
        if not entries and not text_of(el, "userCriteria"):
            out.append(("WARN", f"{path.name}: no <entitiesAndFields> and no <userCriteria>; the rule has nothing to match on"))
        lists = set()
        for entry in entries:
            if not text_of(entry, "entityName"):
                out.append(("ERROR", f"{path.name}: an <entitiesAndFields> entry is missing Required <entityName> (L92296)"))
            kl = text_of(entry, "keywordList")
            if kl:
                lists.add(kl)
        if len(lists) > 3:
            out.append(("WARN", f"{path.name}: {len(lists)} distinct keyword lists; a rule can have up to three keyword criteria (L92219)"))
    return out


def check_keywords(root: Path) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    lists = files_with(root, ".keywords", ".keywords-meta.xml")
    if len(lists) > 30:
        out.append(("WARN", f"{len(lists)} keyword list files; the org limit is 30 (api_meta 264 L84924)"))
    for path in lists:
        try:
            el = ET.parse(path).getroot()
        except (ET.ParseError, OSError) as exc:
            out.append(("ERROR", f"{path.name}: XML does not parse ({exc})"))
            continue
        if not text_of(el, "masterLabel"):
            out.append(("ERROR", f"{path.name}: <masterLabel> is Required (L84956)"))
        words = [text_of(k, "keyword") for k in kids(el, "keywords")]
        if not words:
            out.append(("WARN", f"{path.name}: no keywords; rules referencing this list will match nothing"))
        if len(words) > 2000:
            out.append(("WARN", f"{path.name}: {len(words)} keywords; a list can have up to 2,000 (L84925)"))
        for word in words:
            if not word:
                out.append(("ERROR", f"{path.name}: a <keyword> is empty; it is Required (L84964)"))
            elif len(word) > 100:
                out.append(("WARN", f"{path.name}: keyword over 100 characters (L84965-84966)"))
            elif "*" in word:
                out.append(("WARN", f"{path.name}: keyword '{word}' contains '*'; wildcard characters aren't supported (L84967)"))
    return out


def check_networks(root: Path) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for path in files_with(root, ".network", ".network-meta.xml"):
        try:
            el = ET.parse(path).getroot()
        except (ET.ParseError, OSError) as exc:
            out.append(("ERROR", f"{path.name}: XML does not parse ({exc})"))
            continue
        for rules in kids(el, "reputationPointsRules"):
            for rule in kids(rules, "pointsRule"):
                event = text_of(rule, "eventType")
                if event not in EVENT_TYPES:
                    out.append(("ERROR", f"{path.name}: pointsRule eventType '{event}' is not a documented event (L94412-94429); logging in is not one"))
                if text_of(rule, "points") in (None, ""):
                    out.append(("ERROR", f"{path.name}: pointsRule is missing Required <points> (L94431)"))
        for defs in kids(el, "reputationLevels"):
            for level in kids(defs, "level"):
                if text_of(level, "lowerThreshold") in (None, ""):
                    out.append(("ERROR", f"{path.name}: reputation level is missing Required <lowerThreshold> (L94384)"))
    return out


def check_permissions(root: Path) -> list[tuple[str, str]]:
    files = files_with(root, ".permissionset", ".permissionset-meta.xml", ".profile", ".profile-meta.xml")
    if not files:
        return []
    for path in files:
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if any(name.lower() in content.lower() for name in MODERATE_PERMISSION_NAMES):
            return []
    return [("INFO", "no permission set or profile contains a moderation permission by the name 'ModerateNetworkFeeds' "
                     "(UNVERIFIED 2026-10-20: that name is Help-sourced and not in the corpus; compare with a .permissionset retrieved "
                     "from the org that is known to grant Moderate Experiences Feeds)")]


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    if not root.exists():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)
    scanned = files_with(root, ".rule", ".rule-meta.xml", ".keywords", ".keywords-meta.xml", ".network", ".network-meta.xml")
    if not scanned:
        print(f"WARN: no ModerationRule, KeywordList or Network files under {root}; nothing to check")
        return 1 if args.strict else 0
    findings = check_rules(root) + check_keywords(root) + check_networks(root) + check_permissions(root)
    if not findings:
        print("No issues found.")
        return 0
    for sev, msg in findings:
        print(f"{sev}: {msg}")
    if any(sev == "ERROR" for sev, _ in findings):
        return 1
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
