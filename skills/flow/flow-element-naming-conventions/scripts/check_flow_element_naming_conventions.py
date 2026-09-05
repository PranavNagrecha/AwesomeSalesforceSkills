#!/usr/bin/env python3
"""Lint Flow element, resource, and outcome API Names against this skill's conventions.

Every rule below is transcribed from this skill package -- nothing is invented here.
The skill documents a full **prefix table** (SKILL.md "Decision Guidance",
L202-223) plus a resource-prefix table (SKILL.md "Concept 2", L81-91), so both are
encoded literally. Where a rule is a hard platform constraint (80-char cap,
alphanumeric + underscore, reserved words) it is an ERROR; where it is this skill's
house style (the verb prefix on an element, ``LogFault_<Parent>`` on a fault target)
it is a WARN, because sibling at-bar Flow skills in this repo ship metadata examples
that are legal, readable, and still diverge from the verb table -- failing a build on
house style would make the checker unusable across the library.

Rules encoded
-------------
ERROR (platform constraint or an anti-pattern the skill calls out by name)
  E-CHARSET       API Name has a space/hyphen/other non-``[A-Za-z0-9_]`` char, or does
                  not start with a letter.        SKILL.md L52; gotchas.md Gotcha 3;
                  llm-anti-patterns.md AP2 detection hint L78-80.
  E-LENGTH        API Name > 80 characters.       SKILL.md L52, L257; gotchas.md Gotcha 6.
  E-RESERVED      API Name is a reserved word (``null``/``true``/``false``/``Id``/``Name``).
                                                  SKILL.md L52; gotchas.md Gotcha 4.
  E-AUTONAME      API Name ends ``_<digits>`` or is a ``my<Type>_<n>`` PB-migration
                  leftover.                       llm-anti-patterns.md AP1 L42-43;
                  gotchas.md Gotcha 5; well-architected.md L71 ("regex-grep Flow XML
                  for ``_\\d+$`` element names and fail the build").
  E-LABEL-DEFAULT ``<label>`` is a Flow Builder default ("Get Records", "Decision",
                  "Decision 1", ...).             examples.md L12-24 BAD column;
                  llm-anti-patterns.md AP1 L18-21.
  E-LABEL-DUP     Two elements in one flow share a ``<label>``.
                                                  llm-anti-patterns.md AP4 detection
                  hint L165-166 ("group elements by <label> and flag any group with
                  size > 1").
  E-VAR-PREFIX    A resource carries none of the documented type tokens.
                                                  SKILL.md Concept 2 L81-91;
                  llm-anti-patterns.md AP6 detection hint L237-239.
  E-OUTCOME-WEAK  A Decision outcome is bare ``Yes``/``No``/``Match<n>``/``Outcome<n>``.
                                                  SKILL.md Pattern 3 L156;
                  llm-anti-patterns.md AP3 detection hint L124.
  E-OUTCOME-BLANK A Decision with rules has a blank/absent ``<defaultConnectorLabel>``.
                                                  SKILL.md Pattern 3 L151-155;
                  llm-anti-patterns.md AP3 L99, L125-126.

WARN (this skill's house style; never fails a run unless ``--strict``)
  W-VERB-PREFIX   Element API Name does not open with the verb token its element type
                  maps to (``Get_``/``Update_``/``Create_``/``Delete_``/``Decision_``/
                  ``Loop_``/``Assignment_``/``Screen_``/``Action_``/``Subflow_``).
                                                  SKILL.md Decision Guidance L202-223.
  W-LENGTH-60     API Name > 60 characters.       gotchas.md Gotcha 6 L126-127
                  ("Aim for <= 60 chars in practice"); SKILL.md L257.
  W-IO-PREFIX     A variable flagged ``isInput``/``isOutput`` does not open with
                  ``input``/``output``.           SKILL.md Pattern 4 L166-180.
                  ``in``/``out`` are reported as the abbreviated form, not as missing.
  W-COLL-SHAPE    ``isCollection`` is true but the name lacks the ``coll`` prefix, or a
                  ``coll`` name's noun is singular.
                                                  SKILL.md L84, L216 (``coll<NounPlural>``).
  W-VAR-CASE      The noun after a resource prefix does not start uppercase (the
                  documented shape is prefix + camelCase).
                                                  llm-anti-patterns.md AP2 L73-76;
                  SKILL.md L215-220.
  W-FAULT-TARGET  A ``<faultConnector>`` points at an element not named
                  ``LogFault_<ParentElementName>``.
                                                  SKILL.md Pattern 5 L184-196.
  W-ORCH-PREFIX   An orchestration stage/step is not ``Stage_<Process>`` /
                  ``Step_<Stage>_<Action>``.      SKILL.md L221-222, Review Checklist L250.
  W-LABEL-EMPTY   Element has no ``<label>``, or it is blank. WARN rather than ERROR
                  because SKILL.md L51 is explicit that "the Label is throwaway; the API
                  Name is the contract", and Salesforce refuses the save regardless.
  W-NOT-FLOW      A ``*.flow-meta.xml`` whose root is not ``<Flow>``; skipped.

INFO (worth a human look; never affects the exit code)
  I-ABBREV        API Name contains an abbreviation the skill rejects by example
                  (``Acct``, ``Upd``, ``Opp``, ...).
                                                  examples.md L15-17 BAD column
                  ("No abbreviations; reads in a diff").
  I-SENSITIVE     API Name looks like it encodes PII / sensitive business logic that
                  will appear in fault emails.    well-architected.md L27-31.
  I-LABEL-ECHO    ``<label>`` is the API Name with underscores swapped for spaces, so
                  the two carry no independent information (only reported for names of
                  4+ tokens, where a real label would have added something).
                                                  well-architected.md Anti-Pattern 4 L82-86.

Not enforceable by this checker (see the skill for the human judgement)
  - Whether the noun in ``Get_<Object>`` names the object actually queried, and whether
    a Decision is genuinely framed as a yes/no question (SKILL.md Concept 1).
  - Whether a rename is safe: the cross-flow contract risk in Gotcha 1 / Gotcha 2 lives
    in parent flows and installed packages, not in the file under test.
  - Whether an outcome name states the *affirmative* condition its rule tests
    (SKILL.md Pattern 3) -- that requires reading the ``<conditions>`` semantics.

Stdlib only. Exit 0 clean (or WARN/INFO only), 1 on any ERROR, 2 when --manifest-dir
does not exist.

Usage:
    python3 check_flow_element_naming_conventions.py --manifest-dir path/to/metadata
    python3 check_flow_element_naming_conventions.py --manifest-dir force-app --strict
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

EXIT_OK = 0
EXIT_ERRORS = 1
EXIT_BAD_INPUT = 2

# SKILL.md Decision Guidance L202-223 -- element container tag -> canonical verb prefix.
ELEMENT_VERB_PREFIX: dict[str, str] = {
    "recordLookups": "Get_",
    "recordUpdates": "Update_",
    "recordCreates": "Create_",
    "recordDeletes": "Delete_",
    "decisions": "Decision_",
    "loops": "Loop_",
    "assignments": "Assignment_",
    "screens": "Screen_",
    "actionCalls": "Action_",
    "apexPluginCalls": "Action_",
    "subflows": "Subflow_",
}

# Element containers that are named but carry no canonical verb in the table.
OTHER_ELEMENT_TAGS = {
    "collectionProcessors",
    "customErrors",
    "recordRollbacks",
    "transforms",
    "waits",
}

# SKILL.md Concept 2 L81-91 + llm-anti-patterns.md AP6 detection hint L237-239.
# Longest-first so `input` wins over `in` and `constant` over `coll`.
RESOURCE_PREFIXES: tuple[str, ...] = (
    "decisionOutcome",
    "constant",
    "formula",
    "output",
    "choice",
    "screen",
    "input",
    "stage",
    "coll",
    "map",
    "var",
)

# Not documented by this skill, but used by sibling at-bar Flow skills for subflow
# contracts. Accepted at WARN as the abbreviated form of Pattern 4's input/output.
ABBREVIATED_IO_PREFIXES: tuple[str, ...] = ("input", "output", "in", "out")

RESOURCE_TAGS = {
    "variables",
    "formulas",
    "constants",
    "choices",
    "dynamicChoiceSets",
    "textTemplates",
}

# SKILL.md L52; gotchas.md Gotcha 4 L74-91.
RESERVED_WORDS = {"null", "true", "false", "id", "name"}

MAX_API_NAME = 80  # SKILL.md L52 -- hard platform cap.
SOFT_API_NAME = 60  # gotchas.md Gotcha 6 L126 -- practice cap.

VALID_API_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
AUTO_NAME = re.compile(r"_\d+$")
PB_AUTO_NAME = re.compile(r"^my[A-Z][A-Za-z]*(_\d+)?(_[A-Z]\d+)?$")
WEAK_OUTCOME = re.compile(r"^(yes|no|y|n|match\d*|outcome\d*|rule\d*|default_?\d+)$", re.I)

# examples.md L12-24 BAD column -- Flow Builder's own default labels.
DEFAULT_LABEL = re.compile(
    r"^(?:(?:get|update|create|delete)\s+records"
    r"|decision|assignment|loop|screen|subflow|action|pause|sort|filter"
    r"|get\s+element|new\s+resource)"
    r"(?:\s+\d+)?$",
    re.I,
)

# examples.md L15-17: "No abbreviations; reads in a diff".
ABBREVIATIONS = ("Acct", "Oppty", "Opp", "Upd", "Ctct", "Cse", "Amt", "Qty", "Desc", "Num")

# well-architected.md L27-31 -- names that leak into fault emails.
SENSITIVE_TOKENS = (
    "DoNotMarket",
    "SSN",
    "SocialSecurity",
    "DateOfBirth",
    "Dob",
    "Salary",
    "CreditCard",
    "Passport",
    "Diagnosis",
)

SEVERITY_ORDER = {"ERROR": 0, "WARN": 1, "INFO": 2}


class Finding:
    """One naming problem, tagged with the rule code the docstring documents."""

    def __init__(self, severity: str, code: str, path: Path, message: str) -> None:
        self.severity = severity
        self.code = code
        self.path = path
        self.message = message

    def render(self) -> str:
        pad = "ERROR" if self.severity == "ERROR" else self.severity.ljust(5)
        return f"{pad} [{self.code}] {self.path}: {self.message}"

    def key(self) -> tuple:
        return (self.severity, self.code, str(self.path), self.message)


# --------------------------------------------------------------------------- XML helpers
# Every one of these tests `is not None` explicitly. A leaf ElementTree Element is
# falsy, so `find_child(el, "x") or default` silently discards an element that exists
# but has no children -- exactly the bug that makes naming linters miss empty tags.


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def find_child(element: ET.Element, name: str) -> ET.Element | None:
    for child in element:
        if local_name(child.tag) == name:
            return child
    return None


def has_child(element: ET.Element, name: str) -> bool:
    return find_child(element, name) is not None


def child_text(element: ET.Element, name: str) -> str:
    found = find_child(element, name)
    if found is not None and found.text is not None:
        return found.text.strip()
    return ""


def children(element: ET.Element, name: str) -> list[ET.Element]:
    return [c for c in element if local_name(c.tag) == name]


def is_true(element: ET.Element, name: str) -> bool:
    return child_text(element, name).lower() == "true"


# --------------------------------------------------------------------------- name rules


def split_tokens(api_name: str) -> list[str]:
    """Split `Update_OpportunityStageToClosedWon` into readable tokens."""
    parts: list[str] = []
    for chunk in api_name.split("_"):
        if chunk:
            parts.extend(re.findall(r"[A-Z]+(?![a-z])|[A-Z]?[a-z0-9]+|\d+", chunk) or [chunk])
    return parts


def check_api_name_shape(api_name: str, kind: str, path: Path, out: list[Finding]) -> None:
    """Rules that apply to every API Name in the file, element or resource alike."""
    if not VALID_API_NAME.match(api_name):
        out.append(
            Finding(
                "ERROR",
                "E-CHARSET",
                path,
                f"{kind} API Name `{api_name}` is not alphanumeric-plus-underscore starting "
                f"with a letter. Flow Builder silently rewrites spaces and special "
                f"characters to `_` (gotchas.md Gotcha 3), so the saved name stops matching "
                f"the one you typed.",
            )
        )
    if len(api_name) > MAX_API_NAME:
        out.append(
            Finding(
                "ERROR",
                "E-LENGTH",
                path,
                f"{kind} API Name `{api_name}` is {len(api_name)} characters; the platform "
                f"cap is {MAX_API_NAME} (SKILL.md 'Before Starting').",
            )
        )
    elif len(api_name) > SOFT_API_NAME:
        out.append(
            Finding(
                "WARN",
                "W-LENGTH-60",
                path,
                f"{kind} API Name `{api_name}` is {len(api_name)} characters; gotchas.md "
                f"Gotcha 6 targets <= {SOFT_API_NAME} because external tooling truncates. "
                f"If the qualifier needs this much room, move the logic into a subflow.",
            )
        )
    if api_name.lower() in RESERVED_WORDS:
        out.append(
            Finding(
                "ERROR",
                "E-RESERVED",
                path,
                f"{kind} API Name `{api_name}` is a reserved word. It either refuses to save "
                f"or silently shadows the built-in (gotchas.md Gotcha 4).",
            )
        )
    if AUTO_NAME.search(api_name) or PB_AUTO_NAME.match(api_name):
        out.append(
            Finding(
                "ERROR",
                "E-AUTONAME",
                path,
                f"{kind} API Name `{api_name}` is a Flow Builder / Process Builder auto-name. "
                f"It carries no information in a fault email (well-architected.md "
                f"Anti-Pattern 1) and this skill treats the rename pass as required, not "
                f"deferred (gotchas.md Gotcha 5).",
            )
        )
    # Token-wise, so `Opportunity` is not flagged for containing `Opp` and
    # `AccountNumber` is not flagged for containing `Num`.
    name_tokens = {t.lower().rstrip("s") for t in split_tokens(api_name)}
    for abbrev in ABBREVIATIONS:
        if abbrev.lower() in name_tokens:
            out.append(
                Finding(
                    "INFO",
                    "I-ABBREV",
                    path,
                    f"{kind} API Name `{api_name}` contains the abbreviation `{abbrev}`. "
                    f"examples.md Example 1 rejects `UpdAcct` in favour of the full word so "
                    f"the name reads in a metadata diff.",
                )
            )
            break
    for token in SENSITIVE_TOKENS:
        if token.lower() in api_name.lower():
            out.append(
                Finding(
                    "INFO",
                    "I-SENSITIVE",
                    path,
                    f"{kind} API Name `{api_name}` encodes `{token}`. Element names appear in "
                    f"fault emails, which may go to a broad alias -- prefer a functional name "
                    f"(well-architected.md 'Security').",
                )
            )
            break


def check_label(element: ET.Element, api_name: str, kind: str, path: Path, out: list[Finding]) -> str:
    label = child_text(element, "label")
    if not label:
        # WARN, not ERROR: SKILL.md L51 is explicit that "the Label is throwaway; the API
        # Name is the contract", and Salesforce rejects a label-less element at save time
        # anyway. The label problems this skill DOES treat as defects are the *default*
        # label and the *duplicate* label, both below.
        out.append(
            Finding(
                "WARN",
                "W-LABEL-EMPTY",
                path,
                f"{kind} `{api_name}` has no <label>. The API Name is the contract (SKILL.md "
                f"'Concept 3'), but the Label is what the canvas and debug log render.",
            )
        )
        return ""
    if DEFAULT_LABEL.match(label):
        out.append(
            Finding(
                "ERROR",
                "E-LABEL-DEFAULT",
                path,
                f"{kind} `{api_name}` keeps the Flow Builder default Label \"{label}\". "
                f"examples.md Example 1 lists this as the BAD column: the label must say what "
                f"the element does, not what type it is.",
            )
        )
        return label
    tokens = split_tokens(api_name)
    if len(tokens) >= 4 and label.replace(" ", "_").lower() == api_name.lower():
        out.append(
            Finding(
                "INFO",
                "I-LABEL-ECHO",
                path,
                f"{kind} `{api_name}` has Label \"{label}\", which is the API Name with "
                f"underscores swapped for spaces. well-architected.md Anti-Pattern 4 calls "
                f"this two parallel sources of truth -- the Label can carry a human sentence.",
            )
        )
    return label


def check_element_verb(tag: str, api_name: str, path: Path, out: list[Finding]) -> None:
    prefix = ELEMENT_VERB_PREFIX.get(tag)
    if prefix is None or api_name.startswith(prefix):
        return
    out.append(
        Finding(
            "WARN",
            "W-VERB-PREFIX",
            path,
            f"<{tag}> element `{api_name}` does not start with `{prefix}`. SKILL.md's Decision "
            f"Guidance table maps this element type to `{prefix}<Object>[_<Qualifier>]` so a "
            f"fault email names the verb and the noun without opening Flow Builder.",
        )
    )


def check_resource_prefix(
    element: ET.Element, tag: str, api_name: str, path: Path, out: list[Finding]
) -> None:
    is_input = is_true(element, "isInput")
    is_output = is_true(element, "isOutput")
    is_collection = is_true(element, "isCollection")

    matched: str | None = None
    for prefix in RESOURCE_PREFIXES:
        if api_name.startswith(prefix) and len(api_name) > len(prefix):
            matched = prefix
            break

    if matched is None:
        abbreviated = next(
            (
                p
                for p in ABBREVIATED_IO_PREFIXES
                if api_name.startswith(p)
                and len(api_name) > len(p)
                and api_name[len(p)].isupper()
            ),
            None,
        )
        if abbreviated is not None and (is_input or is_output):
            out.append(
                Finding(
                    "WARN",
                    "W-IO-PREFIX",
                    path,
                    f"<{tag}> `{api_name}` uses `{abbreviated}` where SKILL.md Pattern 4 "
                    f"documents the full `input` / `output` prefix. The abbreviation still "
                    f"communicates direction, but the published contract should match the "
                    f"skill's table verbatim so parent-flow authors read one shape.",
                )
            )
            matched = abbreviated
        else:
            out.append(
                Finding(
                    "ERROR",
                    "E-VAR-PREFIX",
                    path,
                    f"<{tag}> `{api_name}` carries no resource type prefix. SKILL.md Concept 2 "
                    f"requires one of {', '.join(RESOURCE_PREFIXES)}; without it a formula "
                    f"reading `{{!{api_name}}}` cannot tell a single value from a collection "
                    f"(llm-anti-patterns.md Anti-Pattern 6).",
                )
            )
            return

    remainder = api_name[len(matched) :]
    if remainder and not remainder[0].isupper() and not remainder[0].isdigit():
        out.append(
            Finding(
                "WARN",
                "W-VAR-CASE",
                path,
                f"<{tag}> `{api_name}` continues in lowercase after the `{matched}` prefix. "
                f"The documented shape is prefix + camelCase noun (`varAccountId`, "
                f"`collOpenCases`) -- llm-anti-patterns.md Anti-Pattern 2.",
            )
        )

    if (is_input or is_output) and matched not in ("input", "output", "in", "out"):
        direction = "input" if is_input else "output"
        out.append(
            Finding(
                "WARN",
                "W-IO-PREFIX",
                path,
                f"<{tag}> `{api_name}` is marked available for {direction} but is prefixed "
                f"`{matched}`. SKILL.md Pattern 4 puts `{direction}` on the public contract so "
                f"direction is obvious at the parent-flow call site.",
            )
        )

    if is_collection and matched != "coll":
        out.append(
            Finding(
                "WARN",
                "W-COLL-SHAPE",
                path,
                f"<{tag}> `{api_name}` sets <isCollection>true</isCollection> but is prefixed "
                f"`{matched}`. SKILL.md Concept 2 reserves `coll` for List-shaped resources.",
            )
        )
    elif matched == "coll" and remainder and not remainder.endswith("s"):
        out.append(
            Finding(
                "WARN",
                "W-COLL-SHAPE",
                path,
                f"<{tag}> `{api_name}` uses the `coll` prefix with a singular noun. SKILL.md's "
                f"Decision Guidance row is `coll<NounPlural>` (`collOpenCases`).",
            )
        )


def check_decision(element: ET.Element, api_name: str, path: Path, out: list[Finding]) -> None:
    rules = children(element, "rules")
    for rule in rules:
        outcome = child_text(rule, "name")
        outcome_label = child_text(rule, "label")
        for candidate, what in ((outcome, "API Name"), (outcome_label, "Label")):
            if candidate and WEAK_OUTCOME.match(candidate):
                out.append(
                    Finding(
                        "ERROR",
                        "E-OUTCOME-WEAK",
                        path,
                        f"Decision `{api_name}` has an outcome {what} \"{candidate}\". SKILL.md "
                        f"Pattern 3 forbids bare Yes/No/Match<n>: outcomes surface in fault "
                        f"diagnostics detached from their Decision, and re-ordering two "
                        f"identically weak outcomes silently changes routing (Gotcha 7).",
                    )
                )
    if not rules:
        return
    default_label = child_text(element, "defaultConnectorLabel")
    if not default_label:
        out.append(
            Finding(
                "ERROR",
                "E-OUTCOME-BLANK",
                path,
                f"Decision `{api_name}` has {len(rules)} outcome(s) but a blank or absent "
                f"<defaultConnectorLabel>. SKILL.md Pattern 3: the Default outcome always gets "
                f"an explicit name (`Default`, `NoMatch`, `<NegativeCondition>_Default`) or it "
                f"shows as `outcome2` in fault diagnostics.",
            )
        )
    elif WEAK_OUTCOME.match(default_label):
        out.append(
            Finding(
                "ERROR",
                "E-OUTCOME-WEAK",
                path,
                f"Decision `{api_name}` names its default outcome \"{default_label}\". "
                f"SKILL.md Pattern 3 prefers `<NegativeCondition>_Default` so the next reader "
                f"does not have to inspect every other outcome to learn what it catches.",
            )
        )


def check_orchestration(root: ET.Element, path: Path, out: list[Finding]) -> None:
    """SKILL.md L221-222 + Review Checklist L250 -- Stage_<Process> / Step_<Stage>_<Action>."""
    for stage in children(root, "orchestratedStages") + children(root, "stages"):
        name = child_text(stage, "name")
        if name and not name.startswith("Stage_"):
            out.append(
                Finding(
                    "WARN",
                    "W-ORCH-PREFIX",
                    path,
                    f"Orchestration stage `{name}` is not `Stage_<BusinessProcessName>`. The "
                    f"stage name is what the stage tracker renders to the end user "
                    f"(SKILL.md Decision Guidance; Review Checklist bans `S1`).",
                )
            )
        for step in children(stage, "stageSteps"):
            step_name = child_text(step, "name")
            if step_name and not step_name.startswith("Step_"):
                out.append(
                    Finding(
                        "WARN",
                        "W-ORCH-PREFIX",
                        path,
                        f"Orchestration step `{step_name}` is not "
                        f"`Step_<Stage>_<Action>` (SKILL.md Decision Guidance).",
                    )
                )


def check_fault_targets(root: ET.Element, path: Path, out: list[Finding]) -> None:
    """SKILL.md Pattern 5 -- a fault target is named after the element that faulted."""
    for element in root.iter():
        fault = find_child(element, "faultConnector")
        if fault is None:
            continue
        parent_name = child_text(element, "name")
        target = child_text(fault, "targetReference")
        if not parent_name or not target:
            continue
        expected = f"LogFault_{parent_name}"
        if target != expected:
            out.append(
                Finding(
                    "WARN",
                    "W-FAULT-TARGET",
                    path,
                    f"Element `{parent_name}` routes its fault to `{target}`; SKILL.md "
                    f"Pattern 5 names the target `{expected}` so two faults in one interview "
                    f"stay distinguishable instead of re-converging on a shared blob.",
                )
            )


# --------------------------------------------------------------------------- per-file


def check_flow_file(path: Path, out: list[Finding]) -> None:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        out.append(Finding("ERROR", "E-PARSE", path, f"unable to parse flow metadata ({exc})."))
        return

    if local_name(root.tag) != "Flow":
        out.append(
            Finding(
                "WARN",
                "W-NOT-FLOW",
                path,
                f"root element is <{local_name(root.tag)}>, not <Flow>; skipped.",
            )
        )
        return

    labels: dict[str, list[str]] = {}

    element_tags = set(ELEMENT_VERB_PREFIX) | OTHER_ELEMENT_TAGS
    for child in root:
        tag = local_name(child.tag)
        if tag not in element_tags:
            continue
        api_name = child_text(child, "name")
        if not api_name:
            out.append(
                Finding("ERROR", "E-CHARSET", path, f"<{tag}> element has no <name>.")
            )
            continue
        check_api_name_shape(api_name, f"<{tag}>", path, out)
        check_element_verb(tag, api_name, path, out)
        label = check_label(child, api_name, f"<{tag}>", path, out)
        if label:
            labels.setdefault(label, []).append(api_name)
        if tag == "decisions":
            check_decision(child, api_name, path, out)

    for child in root:
        tag = local_name(child.tag)
        if tag not in RESOURCE_TAGS:
            continue
        api_name = child_text(child, "name")
        if not api_name:
            out.append(Finding("ERROR", "E-CHARSET", path, f"<{tag}> resource has no <name>."))
            continue
        check_api_name_shape(api_name, f"<{tag}>", path, out)
        check_resource_prefix(child, tag, api_name, path, out)

    for label, owners in sorted(labels.items()):
        if len(owners) > 1:
            out.append(
                Finding(
                    "ERROR",
                    "E-LABEL-DUP",
                    path,
                    f"Label \"{label}\" is shared by {len(owners)} elements "
                    f"({', '.join(sorted(owners))}). llm-anti-patterns.md Anti-Pattern 4: Flow "
                    f"Builder allows duplicate Labels, so a fault email naming the Label alone "
                    f"cannot tell the reader which element failed.",
                )
            )

    check_orchestration(root, path, out)
    check_fault_targets(root, path, out)


def check_manifest(manifest_dir: Path) -> tuple[list[Finding], int | None]:
    """Return (findings, forced_exit_code). forced_exit_code is set only for bad input."""
    if not manifest_dir.exists():
        return (
            [
                Finding(
                    "ERROR",
                    "E-NO-DIR",
                    manifest_dir,
                    "manifest directory not found.",
                )
            ],
            EXIT_BAD_INPUT,
        )
    if not manifest_dir.is_dir():
        return (
            [Finding("ERROR", "E-NO-DIR", manifest_dir, "--manifest-dir is not a directory.")],
            EXIT_BAD_INPUT,
        )

    flow_files = sorted(manifest_dir.rglob("*.flow-meta.xml"))
    if not flow_files:
        return (
            [
                Finding(
                    "WARN",
                    "W-EMPTY",
                    manifest_dir,
                    "no *.flow-meta.xml files found; nothing to lint. Retrieve the flows first "
                    "(`sf project retrieve start --metadata Flow`) or point --manifest-dir at "
                    "the package directory that holds them.",
                )
            ],
            None,
        )

    findings: list[Finding] = []
    for path in flow_files:
        check_flow_file(path, findings)
    return findings, None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Lint Flow element / resource / outcome API Names against the conventions in "
            "skills/flow/flow-element-naming-conventions."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the Salesforce metadata (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat WARN findings as failures too (INFO never fails).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    findings, forced = check_manifest(Path(args.manifest_dir))

    seen: set[tuple] = set()
    unique: list[Finding] = []
    for finding in findings:
        if finding.key() in seen:
            continue
        seen.add(finding.key())
        unique.append(finding)

    unique.sort(key=lambda f: (SEVERITY_ORDER[f.severity], str(f.path), f.code, f.message))

    if forced is not None:
        for finding in unique:
            print(finding.render(), file=sys.stderr)
        return forced

    if not unique:
        print("No issues found.")
        return EXIT_OK

    for finding in unique:
        print(finding.render())

    errors = sum(1 for f in unique if f.severity == "ERROR")
    warns = sum(1 for f in unique if f.severity == "WARN")
    infos = sum(1 for f in unique if f.severity == "INFO")
    print(f"\n{errors} error(s), {warns} warning(s), {infos} info.")

    if errors:
        return EXIT_ERRORS
    if args.strict and warns:
        return EXIT_ERRORS
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
