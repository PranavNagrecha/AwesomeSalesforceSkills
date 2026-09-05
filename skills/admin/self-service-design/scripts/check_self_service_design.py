#!/usr/bin/env python3
"""Checker script for the Self-Service Design skill.

Lints the self-service design artefact described in
``references/worked-examples.md`` section 9, and — when a metadata directory is
supplied — the ``Network`` files that the design deploys as.

Stdlib only. No pip dependencies.

Design YAML checks (``--file``, or every ``*.yaml`` / ``*.yml`` under
``--manifest-dir``):

1. Every journey carries ``id``, ``persona``, ``entry``, ``success_metric``,
   ``owner`` and ``status``; ids are unique; ``status`` sits in the allowed set.
2. Every journey's ``persona`` resolves to a persona declared in ``personas``.
3. Every ``exposed_objects`` row names a ``sharing_mechanism`` from the
   documented set. ``case-isvisibleinselfservice`` is rejected by name: the
   Object Reference says of ``Case.IsVisibleInSelfService`` that "the field does
   not alter sharing and will not prevent usage of a direct URL to a case if a
   portal user has read or write access".
4. ``article_visibility`` flags are consistent with their channel
   (pkb -> IsVisibleInPkb, csp -> IsVisibleInCsp, prm -> IsVisibleInPrm), no row
   tries to set ``IsVisibleInApp`` (Required, but its properties list carries no
   Create and no Update), and any persona served by a journey has a channel
   opened for it.
5. ``self_registration.enabled`` true requires both ``self_reg_profile`` and
   ``account_assignment``: self-registering users "are required to be associated
   with an account, which the admin must specify" (NetworkSelfRegistration).
6. Repo paths in ``built_by`` / ``downstream`` / ``upstream_requirements``
   resolve on disk.
7. Every ``acceptance_tests`` row names a journey that exists, plus an ``expect``
   and an ``owner``.

Network XML checks (``--manifest-dir``):

8. Every ``*.network-meta.xml`` / ``*.network`` parses, and ``selfRegistration``
   / ``selfRegProfile`` are consistent in both directions: ``selfRegistration``
   true with no ``selfRegProfile`` is a clean deploy and a broken registration
   form; ``selfRegProfile`` with ``selfRegistration`` absent or false is dead
   configuration.
9. ``Network`` carries its two required elements, ``site`` and ``status``, and
   ``status`` sits in the documented enum.

Exit codes: 0 clean, 1 findings, 2 usage error.

Usage:
    python3 check_self_service_design.py --file acme-self-service-design.yaml
    python3 check_self_service_design.py --manifest-dir force-app/main/default
    python3 check_self_service_design.py --file design.yaml --manifest-dir force-app/main/default
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MD_NS = "{http://soap.sforce.com/2006/04/metadata}"

ALLOWED_STATUS = {"draft", "proposed", "approved", "deferred", "rejected"}

# Mechanisms a design may name. Each is a real Salesforce access path with a
# metadata type behind it; see references/worked-examples.md section 4.
ALLOWED_SHARING_MECHANISMS = {
    "ownership",
    "sharing-set",
    "guest-sharing-rule",
    "criteria-sharing-rule",
    "owner-sharing-rule",
    "data-category-visibility",
    "parent-record-controlled",
    "role-hierarchy",
    "account-role-hierarchy",
    "apex-managed-sharing",
    "external-owd-public-read",
    "manual-share",
}

# Named and rejected on purpose rather than merely absent from the set above,
# so the finding can say why.
REJECTED_SHARING_MECHANISMS = {
    "case-isvisibleinselfservice": (
        "Case.IsVisibleInSelfService is a legacy display filter, not a sharing "
        "mechanism: 'The field does not alter sharing and will not prevent usage "
        "of a direct URL to a case if a portal user has read or write access.' "
        "(Object Reference, Case, L62512-L62513). Name the sharing mechanism that "
        "actually grants the access."
    ),
    "portal-shows-it": (
        "'The portal shows it' is not a mechanism. Name one of: "
        + ", ".join(sorted(ALLOWED_SHARING_MECHANISMS))
    ),
}

CHANNEL_FLAGS = {
    "pkb": "IsVisibleInPkb",
    "csp": "IsVisibleInCsp",
    "prm": "IsVisibleInPrm",
}

# Required (so it always has a value) but its property list carries neither
# Create nor Update, so no deploy or load can set it.
UNSETTABLE_FLAGS = {"IsVisibleInApp": "app"}

NETWORK_STATUS_VALUES = {"Live", "DownForMaintenance", "UnderConstruction"}

REPO_PATH_KEYS = ("built_by", "downstream", "upstream_requirements", "owned_by")


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
    """Return (line_no, indent, content) for every significant line."""
    out: list[tuple[int, int, str]] = []
    block_indent: int | None = None
    for n, raw in enumerate(text.splitlines(), start=1):
        if block_indent is not None:
            if raw.strip() and (len(raw) - len(raw.lstrip(" "))) > block_indent:
                continue  # folded/literal continuation, already consumed
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
                else:
                    nested, pos = _parse_block(rows, pos, child_indent + 2) \
                        if pos < len(rows) and rows[pos][1] > child_indent else ({}, pos)
                    item[key.strip()] = nested
                while pos < len(rows) and rows[pos][1] >= child_indent and not rows[pos][2].startswith("- "):
                    if rows[pos][1] != child_indent:
                        raise YamlError(f"line {rows[pos][0]}: unexpected indentation inside a list item")
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

def child_text(element: ET.Element, tag: str) -> str | None:
    """Text of the first ``tag`` child, or None.

    Written as an explicit ``is not None`` walk: an ElementTree element with no
    children is falsy, so ``element.find(a) or element.find(b)`` silently
    discards a real leaf element.
    """
    found = element.find(f"{MD_NS}{tag}")
    if found is None:
        found = element.find(tag)
    if found is None:
        return None
    return (found.text or "").strip()


def parse_xml(path: Path) -> tuple[ET.Element | None, str | None]:
    try:
        return ET.parse(path).getroot(), None
    except ET.ParseError as exc:
        return None, str(exc)
    except OSError as exc:
        return None, str(exc)


# ---------------------------------------------------------------------------
# Design YAML checks
# ---------------------------------------------------------------------------

def _rows(doc: dict, key: str) -> list[dict]:
    value = doc.get(key)
    if isinstance(value, list):
        return [row for row in value if isinstance(row, dict)]
    return []


def _at(row: dict) -> str:
    line = row.get("__line__")
    return f" (line {line})" if line else ""


def check_design(path: Path, repo_root: Path) -> list[str]:
    issues: list[str] = []
    try:
        doc = load_yaml(path.read_text(encoding="utf-8"))
    except YamlError as exc:
        return [f"{path}: {exc}"]
    except OSError as exc:
        return [f"{path}: {exc}"]

    journeys = _rows(doc, "journeys")
    if not journeys:
        return [
            f"{path}: no 'journeys:' list found. A self-service design without journeys "
            f"cannot be reviewed; see references/worked-examples.md section 9 for the shape."
        ]

    personas = _rows(doc, "personas")
    persona_ids = {str(p.get("id", "")).strip() for p in personas if p.get("id")}
    persona_ids |= {str(p.get("name", "")).strip() for p in personas if p.get("name")}
    persona_ids.discard("")

    # 1 + 2 — journeys
    seen_journeys: dict[str, int] = {}
    required = ("id", "persona", "entry", "success_metric", "owner", "status")
    for row in journeys:
        label = str(row.get("id") or row.get("name") or "<unnamed journey>")
        for field in required:
            if not str(row.get(field, "")).strip():
                issues.append(
                    f"{path}: journey '{label}'{_at(row)} is missing '{field}'. Every journey "
                    f"needs a persona, an entry point, an observable success metric, an owner "
                    f"and a status."
                )
        jid = str(row.get("id", "")).strip()
        if jid:
            if jid in seen_journeys:
                issues.append(
                    f"{path}: duplicate journey id '{jid}'{_at(row)}; first seen on line "
                    f"{seen_journeys[jid]}."
                )
            else:
                seen_journeys[jid] = row.get("__line__", 0)
        status = str(row.get("status", "")).strip().lower()
        if status and status not in ALLOWED_STATUS:
            issues.append(
                f"{path}: journey '{label}'{_at(row)} has status '{status}'; allowed: "
                f"{', '.join(sorted(ALLOWED_STATUS))}."
            )
        persona = str(row.get("persona", "")).strip()
        if persona and persona_ids and persona not in persona_ids:
            issues.append(
                f"{path}: journey '{label}'{_at(row)} names persona '{persona}', which is not "
                f"declared under 'personas:'. Declared: {', '.join(sorted(persona_ids)) or '(none)'}."
            )
        elif persona and not persona_ids:
            issues.append(
                f"{path}: journey '{label}'{_at(row)} names a persona but the file declares no "
                f"'personas:' list, so the licence model behind the journey is undocumented."
            )

    # 3 — exposed objects
    exposed = _rows(doc, "exposed_objects")
    if not exposed:
        issues.append(
            f"{path}: no 'exposed_objects:' list. Every record the site shows must name the "
            f"mechanism that grants access; see references/worked-examples.md section 4."
        )
    for row in exposed:
        obj = str(row.get("object", "") or "<unnamed object>")
        mech = str(row.get("sharing_mechanism", "")).strip().lower()
        if not mech:
            issues.append(
                f"{path}: exposed object '{obj}'{_at(row)} names no 'sharing_mechanism'. "
                f"Allowed: {', '.join(sorted(ALLOWED_SHARING_MECHANISMS))}."
            )
        elif mech in REJECTED_SHARING_MECHANISMS:
            issues.append(
                f"{path}: exposed object '{obj}'{_at(row)} uses '{mech}'. "
                f"{REJECTED_SHARING_MECHANISMS[mech]}"
            )
        elif mech not in ALLOWED_SHARING_MECHANISMS:
            issues.append(
                f"{path}: exposed object '{obj}'{_at(row)} names sharing mechanism '{mech}', "
                f"which is not one of: {', '.join(sorted(ALLOWED_SHARING_MECHANISMS))}."
            )
        if not str(row.get("audience", "")).strip():
            issues.append(
                f"{path}: exposed object '{obj}'{_at(row)} names no 'audience'; a record is "
                f"exposed to somebody in particular or it is not exposed."
            )

    # 4 — article visibility
    visibility = _rows(doc, "article_visibility")
    open_channels: set[str] = set()
    audiences_served: set[str] = set()
    for row in visibility:
        channel = str(row.get("channel", "")).strip().lower()
        flag = str(row.get("flag", "")).strip()
        value = row.get("value")
        if flag in UNSETTABLE_FLAGS:
            issues.append(
                f"{path}: article_visibility row{_at(row)} sets '{flag}'. That field is Required "
                f"on Knowledge__kav but its properties are 'Defaulted on create, Filter, Group, "
                f"Sort' — no Create, no Update — so no deploy or data load can set it "
                f"(Object Reference L160929-L160935). Remove the row."
            )
            continue
        if channel not in CHANNEL_FLAGS:
            issues.append(
                f"{path}: article_visibility row{_at(row)} names channel '{channel}'; allowed: "
                f"{', '.join(sorted(CHANNEL_FLAGS))}."
            )
            continue
        expected = CHANNEL_FLAGS[channel]
        if flag != expected:
            issues.append(
                f"{path}: article_visibility row{_at(row)} pairs channel '{channel}' with flag "
                f"'{flag or '(none)'}'; the Knowledge__kav field for that channel is "
                f"'{expected}'. The channel and the flag are one decision, not two."
            )
        if value is True:
            open_channels.add(channel)
            aud = str(row.get("audience", "")).strip()
            if aud and aud.lower() != "none":
                audiences_served.add(aud)
        elif value is not False:
            issues.append(
                f"{path}: article_visibility row{_at(row)} for channel '{channel}' has value "
                f"'{value}'; it must be true or false."
            )

    if visibility:
        journey_personas = {
            str(j.get("persona", "")).strip()
            for j in journeys
            if str(j.get("persona", "")).strip()
        }
        for persona in sorted(journey_personas - audiences_served):
            issues.append(
                f"{path}: persona '{persona}' has at least one journey but no article_visibility "
                f"row opens a channel for it. An article is invisible to a channel until that "
                f"channel's flag is true (Object Reference L160929-L160955)."
            )
    elif journeys:
        issues.append(
            f"{path}: no 'article_visibility:' matrix. Knowledge visibility is three independent "
            f"boolean fields, each defaulting to false; a design that does not state them has not "
            f"decided them."
        )

    # 5 — self-registration
    selfreg = doc.get("self_registration")
    if isinstance(selfreg, dict):
        if selfreg.get("enabled") is True:
            if not str(selfreg.get("self_reg_profile", "")).strip():
                issues.append(
                    f"{path}: self_registration.enabled is true but no 'self_reg_profile' is set. "
                    f"Network.selfRegProfile is 'the profile assigned to users who self-register' "
                    f"(Metadata API Guide, Network L91035-L91038); without it the registration "
                    f"form cannot create a user."
                )
            if not str(selfreg.get("account_assignment", "")).strip():
                issues.append(
                    f"{path}: self_registration.enabled is true but no 'account_assignment' is "
                    f"recorded. Self-registering users 'are required to be associated with an "
                    f"account, which the admin must specify' (Object Reference, "
                    f"NetworkSelfRegistration L188832-L188838), and only one account per site "
                    f"may be used."
                )
    elif selfreg is not None:
        issues.append(f"{path}: 'self_registration:' must be a mapping, not {type(selfreg).__name__}.")

    # 6 — repo paths resolve
    def walk(node: object) -> None:
        if isinstance(node, dict):
            for key, val in node.items():
                if key in REPO_PATH_KEYS and isinstance(val, str) and val.startswith("skills/"):
                    if not (repo_root / val).exists():
                        issues.append(
                            f"{path}: '{key}: {val}' does not resolve under {repo_root}. "
                            f"Every cited skill path must be a real package."
                        )
                else:
                    walk(val)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(doc)

    # 7 — acceptance tests
    tests = _rows(doc, "acceptance_tests")
    if not tests:
        issues.append(
            f"{path}: no 'acceptance_tests:' list. Each journey needs a test that an external-user "
            f"session can run; see references/worked-examples.md section 8."
        )
    for row in tests:
        tid = str(row.get("id", "") or "<unnamed test>")
        for field in ("journey", "expect", "owner"):
            if not str(row.get(field, "")).strip():
                issues.append(f"{path}: acceptance test '{tid}'{_at(row)} is missing '{field}'.")
        jref = str(row.get("journey", "")).strip()
        if jref and seen_journeys and jref not in seen_journeys:
            issues.append(
                f"{path}: acceptance test '{tid}'{_at(row)} refers to journey '{jref}', which is "
                f"not declared. Declared: {', '.join(sorted(seen_journeys))}."
            )

    return issues


# ---------------------------------------------------------------------------
# Network XML checks
# ---------------------------------------------------------------------------

def check_network(path: Path) -> list[str]:
    issues: list[str] = []
    root, err = parse_xml(path)
    if root is None:
        return [f"{path}: does not parse as XML ({err})."]

    self_reg = child_text(root, "selfRegistration")
    self_reg_profile = child_text(root, "selfRegProfile")
    enabled = (self_reg or "").lower() == "true"

    if enabled and not self_reg_profile:
        issues.append(
            f"{path}: <selfRegistration>true</selfRegistration> with no <selfRegProfile>. "
            "This deploys clean and produces a registration form that cannot create a user: "
            "selfRegProfile is 'the profile assigned to users who self-register' and 'is used "
            "only if selfRegistration is enabled' (Metadata API Guide, Network L91035-L91041). "
            "Set the profile, and record the account assignment in the design YAML."
        )
    if self_reg_profile and not enabled:
        issues.append(
            f"{path}: <selfRegProfile>{self_reg_profile}</selfRegProfile> is set but "
            f"selfRegistration is {self_reg or 'absent'}. The profile 'is used only if "
            "selfRegistration is enabled for the site', so this element is inert — either turn "
            "self-registration on or drop the profile so the file states the real intent."
        )

    site = child_text(root, "site")
    if not site:
        issues.append(
            f"{path}: no <site> element. Network.site is 'Required. The CustomSite associated "
            "with the Experience Cloud site' (Metadata API Guide, Network L91049-L91051)."
        )

    status = child_text(root, "status")
    if not status:
        issues.append(
            f"{path}: no <status> element. Network.status is required and takes "
            f"{', '.join(sorted(NETWORK_STATUS_VALUES))}."
        )
    elif status not in NETWORK_STATUS_VALUES:
        issues.append(
            f"{path}: <status>{status}</status> is not one of "
            f"{', '.join(sorted(NETWORK_STATUS_VALUES))}."
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
            "Lint a self-service design artefact (YAML) and, when a metadata directory is "
            "given, the Network files it deploys as."
        ),
    )
    parser.add_argument(
        "--file",
        default=None,
        help="Path to a self-service design YAML. See references/worked-examples.md section 9.",
    )
    parser.add_argument(
        "--manifest-dir",
        default=None,
        help=(
            "Salesforce metadata directory. Scanned for *.network-meta.xml / *.network, and "
            "for *.yaml / *.yml design artefacts when --file is not given."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.file and not args.manifest_dir:
        print(
            "usage error: pass --file <design.yaml> and/or --manifest-dir <metadata dir>.",
            file=sys.stderr,
        )
        return 2

    issues: list[str] = []
    checked = 0

    repo_root = find_repo_root(Path(__file__).resolve().parent)

    design_files: list[Path] = []
    if args.file:
        candidate = Path(args.file)
        if not candidate.is_file():
            print(f"usage error: --file not found: {candidate}", file=sys.stderr)
            return 2
        design_files.append(candidate)

    manifest_dir: Path | None = None
    if args.manifest_dir:
        manifest_dir = Path(args.manifest_dir)
        if not manifest_dir.is_dir():
            print(f"usage error: --manifest-dir not found: {manifest_dir}", file=sys.stderr)
            return 2
        if not design_files:
            design_files.extend(sorted(manifest_dir.rglob("*.yaml")))
            design_files.extend(sorted(manifest_dir.rglob("*.yml")))

    for design in design_files:
        checked += 1
        issues.extend(check_design(design, repo_root))

    if manifest_dir is not None:
        networks = sorted(manifest_dir.rglob("*.network-meta.xml"))
        networks += sorted(manifest_dir.rglob("*.network"))
        for network in networks:
            checked += 1
            issues.extend(check_network(network))

    if checked == 0:
        print(
            "No self-service design YAML and no Network metadata found. Nothing to check.",
            file=sys.stderr,
        )
        return 0

    if not issues:
        print(f"No self-service design issues found ({checked} file(s) checked).")
        return 0

    for issue in issues:
        print(f"ERROR: {issue}", file=sys.stderr)
    print(f"\n{len(issues)} finding(s) across {checked} file(s) checked.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
