#!/usr/bin/env python3
"""Single writer for build-plan derived views and human gate records.

Implements `scripts/build_plan.py` as specified by
`standards/build-orchestration.md` (contract v1, 2026-09-05) sections 2-5
and 8: the requirements-to-build layer keeps ALL shared state in
`.sfskills/builds/<build-id>/plan.json`, and this script is the only thing
that renders the human-readable views (PLAN.md, CLARIFICATIONS.md) and the
only writer of `human_gates[]`. Agents call it; they never re-implement it.

Design rules this file obeys:

* stdlib only (contract section 8);
* every write is atomic (temp file + os.replace) and re-validates the new
  document BEFORE replacing — a failed validation leaves the file untouched
  and exits 1;
* rendered output is byte-deterministic: the only timestamps that reach a
  rendered view are ones already stored in plan.json;
* schema validation carries no third-party dependency. A small subset of
  JSON Schema draft 2020-12 is implemented here (type, required, enum,
  pattern, properties, items, additionalProperties, minItems, minLength,
  minimum, local $ref) — enough for
  `agents/_shared/schemas/build-plan.schema.json` and nothing more.

Typical loop::

    python3 scripts/build_plan.py init --build-dir .sfskills/builds/case-onboarding \\
        --title "Case intake onboarding" --requirement /tmp/requirement.md
    #  (add --org-alias <alias> for an org-connected build; the default,
    #   design-only, only allows step owners with requires_org: false)
    python3 scripts/build_plan.py set-clarifications .sfskills/builds/case-onboarding/plan.json \\
        --file /tmp/questions.json
    python3 scripts/build_plan.py render  .sfskills/builds/case-onboarding/plan.json
    #  ... human writes 'Answer:' lines in CLARIFICATIONS.md ...
    python3 scripts/build_plan.py ingest-answers .sfskills/builds/case-onboarding/plan.json
    python3 scripts/build_plan.py gate .sfskills/builds/case-onboarding/plan.json \\
        clarifications approve --by pranav
    python3 scripts/build_plan.py set-plan .sfskills/builds/case-onboarding/plan.json \\
        --file /tmp/plan-body.json
    python3 scripts/build_plan.py validate    .sfskills/builds/case-onboarding/plan.json
    python3 scripts/build_plan.py set-verification .sfskills/builds/case-onboarding/plan.json \\
        --file /tmp/verification.json --outcome verified
    python3 scripts/build_plan.py gate .sfskills/builds/case-onboarding/plan.json plan approve --by pranav
    python3 scripts/build_plan.py next .sfskills/builds/case-onboarding/plan.json
    python3 scripts/build_plan.py set-status .sfskills/builds/case-onboarding/plan.json M1-S01 running \\
        --run-agent object-designer --envelope envelopes/M1-S01/run-1.json --result started
    python3 scripts/build_plan.py check-outputs .sfskills/builds/case-onboarding/plan.json M1-S01
    python3 scripts/build_plan.py set-milestone .sfskills/builds/case-onboarding/plan.json M1 \\
        --status verified --report-path reports/MILESTONE-M1-REPORT.md
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import shlex
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "agents" / "_shared" / "schemas" / "build-plan.schema.json"
AGENT_SCHEMA_REL = Path("agents") / "_shared" / "schemas" / "agent-frontmatter.schema.json"

# --------------------------------------------------------------------------
# Contract constants — mirrored from standards/build-orchestration.md
# --------------------------------------------------------------------------

# Section 4, "Steps and step types" table. Adding a step type means adding a
# row THERE first; this list is the machine mirror of that table and the
# schema enum. Keep the three in step.
STEP_TYPES = [
    "object-model",
    "access",
    "automation",
    "validation",
    "routing",
    "sla",
    "ui",
    "data",
    "integration",
    "docs",
    "custom",
]

# Section 5, "Acceptance tests" table.
TEST_TYPES = ["checker", "xml", "manifest", "command", "manual"]

# Section 5, `scope` on a checker test. `step` (the default) runs the checker
# over the one step's artefacts; `build` runs it over the whole artefacts root,
# which is the only honest scope for a checker that cross-references metadata
# other steps produce.
TEST_SCOPES = ["step", "build"]
DEFAULT_TEST_SCOPE = "step"

# Checkers documented as cross-referential: they assert relationships BETWEEN
# components (a routing rule against the queue it targets, a milestone against
# the business hours it counts in, a permission set against the object and
# record types it grants), so a step-scoped run reads half the picture and
# reports findings the step itself cannot fix. Hard-coded rather than sniffed:
# the fact lives in each skill's checker, and guessing it from the filename
# would flag every checker whose name happens to be plural.
CROSS_REFERENTIAL_CHECKERS = {
    "check_escalation_rules.py",
    "check_omni_channel_routing_setup.py",
    "check_list_views_and_compact_layouts.py",
    "check_permission_set_architecture.py",
}

# The step types whose artefacts a cross-referential checker reaches across.
CROSS_REFERENTIAL_STEP_TYPES = {"routing", "sla", "access"}

# A checker that is still a scaffold: the plan declares a test the tester will
# run, and it will exit non-zero (or exit 0 having checked nothing) because
# nobody wrote it yet. The heuristic is deliberately blunt and deterministic —
# a real skill checker in this repo is 130-970 lines.
STUB_CHECKER_MIN_LINES = 60
STUB_CHECKER_MARKER = "todo: implement"

# Section 4: "pending -> running -> built -> tested -> documented, with
# `failed` and `blocked` as side exits." Re-running a step (section 8) is
# `documented -> running`, which appends a run rather than overwriting one.
# `failed -> pending` resets a step for a clean retry; `running -> running`
# lets a resumed runner re-claim a step it was already executing.
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "pending": {"running", "blocked"},
    "running": {"running", "built", "failed", "blocked"},
    "built": {"tested", "failed", "blocked"},
    "tested": {"documented", "failed", "blocked"},
    "documented": {"running"},
    "failed": {"pending", "running", "blocked"},
    "blocked": {"pending", "running"},
}

BUILD_STATUSES = [
    "intake", "clarifying", "planned", "verified",
    "plan-rejected", "approved", "building", "done",
]

# Section 1: the layer never deploys and never reaches the network. A build
# mode says whether a live org is available at all; design-only builds may
# only be owned by agents that declare `requires_org: false`.
BUILD_MODES = ["design-only", "org-connected"]

# Section 3.1: how much ceremony the loop spends on a build. Absent means
# `project` — every plan written before section 3.1 keeps its behaviour.
SCALES = ["ask", "feature", "project"]

# Section 3.1's sizing rule, "plan shape" row: the shape a plan is expected to
# have at each scale, checked as a WARN only (never an ERROR — a shape
# mismatch is a re-tier, not a re-plan). `project` is unbounded, so it never
# appears here.
SCALE_SHAPE_LIMITS = {
    "ask": {"milestones": 1, "steps": 1},
    "feature": {"milestones": 1, "max_steps": 5},
}

# The single milestone id an `ask`-scale plan's gates are written against
# (section 3.1: "1 milestone, 1 step").
ASK_MILESTONE_ID = "M1"

# `gate` aliases legal only when `scale == "ask"` (section 3.1). The stored
# gate names are unchanged — these are shorthand for writing more than one of
# them, under the same --by/--at/--notes, in one invocation.
GATE_ALIASES = {
    "go": ["clarifications", "plan"],
    "accept": [f"milestone:{ASK_MILESTONE_ID}"],
}

# Fallback for agents/_shared/schemas/agent-frontmatter.schema.json when that
# file cannot be read (e.g. a synthetic repo root in a test).
AGENT_STATUSES = ["stable", "beta", "deprecated"]

# Section 5: acceptance tests read; they never deploy, fetch or shell out.
# One case-insensitive deny-list, applied to every declared test command.
DENY_COMMAND_RE = re.compile(
    r"\bsf\b[^|;&]*\bdeploy\b"
    r"|\bsfdx\b"
    r"|force:(source|mdapi):deploy"
    r"|\bcurl\b"
    r"|\bwget\b"
    r"|\|\s*(ba)?sh\b"
    r"|bash\s+-c"
    r"|python3?\s+-c"
    r"|\brm\s+-rf\b"
    r"|\bgit\s+push\b",
    re.IGNORECASE,
)

# A `checker` test runs a skill-local checker, by its canonical path.
CHECKER_COMMAND_RE = re.compile(
    r"^python3 (skills/[a-z]+/[a-z0-9-]+/scripts/check_[a-z0-9_]+\.py)\b")

# The argument form every skill checker is meant to converge on. A checker that
# takes something else still runs — step-tester executes the declared command
# verbatim — but the plan says so out loud rather than looking like a typo.
CHECKER_STANDARD_ARG = "--manifest-dir"

# Build-directory-relative prefixes a `command` test may name (section 2).
BUILD_DIR_PREFIXES = ("artefacts/", "tests/", "workbook/", "reports/", "envelopes/")

GENERATED_BANNER = "<!-- Generated by scripts/build_plan.py render — never hand-edit. -->"


# --------------------------------------------------------------------------
# Tiny JSON Schema subset (no third-party dependency)
# --------------------------------------------------------------------------

def _resolve_ref(schema: Any, root: Any) -> Any:
    """Resolve local `#/...` refs. Remote refs are unsupported by design."""
    hops = 0
    while isinstance(schema, dict) and "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/"):
            raise ValueError(f"unsupported $ref (local refs only): {ref}")
        node = root
        for raw in ref[2:].split("/"):
            part = raw.replace("~1", "/").replace("~0", "~")
            node = node[part]
        schema = node
        hops += 1
        if hops > 16:
            raise ValueError(f"$ref loop at {ref}")
    return schema


def _type_matches(value: Any, name: str) -> bool:
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if name == "boolean":
        return isinstance(value, bool)
    if name == "string":
        return isinstance(value, str)
    if name == "object":
        return isinstance(value, dict)
    if name == "array":
        return isinstance(value, list)
    if name == "null":
        return value is None
    raise ValueError(f"unsupported schema type: {name}")


def schema_errors(instance: Any, schema: Any, root: Any, path: str = "$") -> list[str]:
    """Validate `instance` against the supported subset. Returns messages."""
    schema = _resolve_ref(schema, root)
    if schema is True or schema == {}:
        return []
    if schema is False:
        return [f"{path}: schema forbids any value here"]

    errors: list[str] = []

    types = schema.get("type")
    if types is not None:
        names = types if isinstance(types, list) else [types]
        if not any(_type_matches(instance, n) for n in names):
            return [f"{path}: expected type {'/'.join(names)}, got {type(instance).__name__}"]

    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: {instance!r} is not one of {schema['enum']}")

    if isinstance(instance, str):
        pattern = schema.get("pattern")
        if pattern and not re.search(pattern, instance):
            errors.append(f"{path}: {instance!r} does not match /{pattern}/")
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{path}: shorter than minLength {schema['minLength']}")
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            errors.append(f"{path}: longer than maxLength {schema['maxLength']}")

    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(f"{path}: below minimum {schema['minimum']}")
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append(f"{path}: above maximum {schema['maximum']}")

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(f"{path}: needs at least {schema['minItems']} item(s), has {len(instance)}")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            errors.append(f"{path}: at most {schema['maxItems']} item(s) allowed")
        if schema.get("uniqueItems"):
            seen: list[Any] = []
            for item in instance:
                if item in seen:
                    errors.append(f"{path}: duplicate item {item!r}")
                    break
                seen.append(item)
        item_schema = schema.get("items")
        if item_schema is not None:
            for i, item in enumerate(instance):
                errors.extend(schema_errors(item, item_schema, root, f"{path}[{i}]"))

    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                errors.append(f"{path}: missing required property '{key}'")
        props = schema.get("properties", {})
        for key, value in instance.items():
            if key in props:
                errors.extend(schema_errors(value, props[key], root, f"{path}.{key}"))
        extra = schema.get("additionalProperties", True)
        if extra is not True:
            unknown = sorted(k for k in instance if k not in props)
            if unknown and extra is False:
                errors.append(f"{path}: unexpected propert{'y' if len(unknown) == 1 else 'ies'} "
                              f"{', '.join(repr(u) for u in unknown)}")
            elif unknown:
                for key in unknown:
                    errors.extend(schema_errors(instance[key], extra, root, f"{path}.{key}"))

    return errors


def load_schema(schema_path: Path | None = None) -> dict:
    return json.loads((schema_path or SCHEMA_PATH).read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# Semantic validation (contract sections 4, 5 and 8)
# --------------------------------------------------------------------------

def _frontmatter_field(text: str, field: str) -> str | None:
    """Value of `field` in a leading YAML frontmatter block, else None."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    block = text[3:end] if end != -1 else text
    m = re.search(rf"^{re.escape(field)}:\s*(.+?)\s*$", block, re.MULTILINE)
    return m.group(1).strip().strip('"').strip("'") if m else None


def _agent_statuses(repo_root: Path) -> list[str]:
    """The `status` enum from the agent frontmatter schema in `repo_root`.

    Read at run time so this file never drifts from the schema; falls back to
    the literal list when the schema is missing or unreadable (a synthetic
    repo root, a partial checkout).
    """
    try:
        schema = json.loads((repo_root / AGENT_SCHEMA_REL).read_text(encoding="utf-8"))
        values = schema["properties"]["status"]["enum"]
        if isinstance(values, list) and all(isinstance(v, str) for v in values) and values:
            return values
    except (OSError, ValueError, KeyError, TypeError):
        pass
    return list(AGENT_STATUSES)


def _truthy(value: str | None) -> bool:
    return (value or "").strip().strip('"').strip("'").lower() in {"true", "yes", "1"}


def _agent_problem(agent_id: str, repo_root: Path, build_mode: str) -> str | None:
    """Return why `agent_id` may not own a step, or None when it may.

    Contract section 8: "The planner may only assign agents that exist with
    `class: runtime` and `status != deprecated`". Two refinements land here:

    * `status` must be one of the values the agent frontmatter schema allows
      (stable | beta | deprecated). A typo like `experimental` used to pass
      because only the literal string `deprecated` was excluded.
    * a `design-only` build has no org alias to hand anyone, so an agent that
      declares `requires_org: true` cannot own one of its steps. Only an
      `org-connected` build may assign those. (`requires_org` absent is read
      as false — the agent never asked for an org.)
    """
    agent_md = repo_root / "agents" / agent_id / "AGENT.md"
    if not agent_md.is_file():
        return f"agent '{agent_id}' has no agents/{agent_id}/AGENT.md"
    text = agent_md.read_text(encoding="utf-8", errors="replace")
    cls = _frontmatter_field(text, "class")
    status = _frontmatter_field(text, "status")
    if cls != "runtime":
        return f"agent '{agent_id}' is class '{cls}', not runtime"
    if status == "deprecated":
        return f"agent '{agent_id}' is deprecated (status: deprecated)"
    allowed = _agent_statuses(repo_root)
    if status not in allowed:
        return (f"agent '{agent_id}' has status {status!r}, which is not one of "
                f"{', '.join(allowed)} (agents/_shared/schemas/agent-frontmatter.schema.json) "
                f"— an unknown status is not an implicit 'stable'")
    if build_mode != "org-connected" and _truthy(_frontmatter_field(text, "requires_org")):
        return (f"agent '{agent_id}' declares requires_org: true, but this build is "
                f"'{build_mode}' — either re-run init with --org-alias, or give the step "
                f"to an org-free owner (metadata-builder for metadata step types)")
    return None


def _find_cycle(graph: dict[str, list[str]]) -> list[str] | None:
    """Return one cycle as a node list, or None. Iterative DFS, deterministic."""
    WHITE, GREY, BLACK = 0, 1, 2
    colour = {node: WHITE for node in graph}
    parent: dict[str, str | None] = {}
    for start in sorted(graph):
        if colour[start] != WHITE:
            continue
        stack: list[tuple[str, Iterable[str]]] = [(start, iter(sorted(graph[start])))]
        colour[start] = GREY
        parent[start] = None
        while stack:
            node, children = stack[-1]
            advanced = False
            for child in children:
                if child not in graph:
                    continue
                if colour[child] == GREY:
                    cycle = [child]
                    walk: str | None = node
                    while walk is not None and walk != child:
                        cycle.append(walk)
                        walk = parent.get(walk)
                    cycle.append(child)
                    return list(reversed(cycle))
                if colour[child] == WHITE:
                    colour[child] = GREY
                    parent[child] = node
                    stack.append((child, iter(sorted(graph[child]))))
                    advanced = True
                    break
            if not advanced:
                colour[node] = BLACK
                stack.pop()
    return None


def _test_label(test: dict) -> str:
    head = test.get("type", "?")
    # Only a declared scope is rendered. The default (`step`) is the reading a
    # reader already has, and stamping it on every row would rewrite every
    # PLAN.md for no new information.
    if test.get("scope"):
        head = f"{head} [scope: {test['scope']}]"
    bits = [head]
    if test.get("command"):
        bits.append(test["command"])
    elif test.get("description"):
        bits.append(test["description"])
    return ": ".join(bits)


def _tokens(command: str) -> list[str]:
    try:
        return shlex.split(command)
    except ValueError:
        return command.split()


def _checker_uses_standard_form(command: str) -> bool:
    """Does this checker command use the house `--manifest-dir <dir>` form?"""
    return any(token == CHECKER_STANDARD_ARG
               or token.startswith(f"{CHECKER_STANDARD_ARG}=")
               for token in _tokens(command)[1:])


def _checker_stub_reason(path: Path) -> str | None:
    """Why this checker file reads as a scaffold stub, or None if it looks real.

    Two signals, both cheap and both stable across runs: an explicit
    `TODO: Implement` left by the scaffolder, and a file too short to contain
    finding logic. A checker that is a stub is a test the step-tester will
    fail (or, worse, one that exits 0 having checked nothing), so the plan
    should say so before a human signs the plan gate.
    """
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if STUB_CHECKER_MARKER in text.lower():
        return "it still carries a 'TODO: Implement' marker"
    lines = len(text.splitlines())
    if lines < STUB_CHECKER_MIN_LINES:
        return (f"it is only {lines} line(s) long — under the "
                f"{STUB_CHECKER_MIN_LINES}-line floor a real checker clears")
    return None


def _command_script_path(command: str) -> str | None:
    """First non-flag argument after `python3`, or None if there is none."""
    tokens = _tokens(command)
    for token in tokens[1:]:
        if token.startswith("-"):
            continue
        return token
    return None


def _acceptance_issues(tests: list, owner: str, repo_root: Path,
                       artefacts_root: str = "artefacts",
                       step_type: str | None = None) -> list[tuple[str, str]]:
    """Per-test checks from contract section 5.

    `step_type` is the owning step's type when the tests belong to a step, and
    None for a milestone's tests (a milestone test is build-scoped already).
    """
    issues: list[tuple[str, str]] = []
    prefixes = tuple(sorted(set(BUILD_DIR_PREFIXES + (f"{artefacts_root.rstrip('/')}/",))))
    for i, test in enumerate(tests or []):
        if not isinstance(test, dict):
            continue
        ttype = test.get("type")
        where = f"{owner} acceptance_tests[{i}]"
        scope = test.get("scope") or DEFAULT_TEST_SCOPE
        if scope not in TEST_SCOPES:
            issues.append(("ERROR", f"{where}: unknown scope {test.get('scope')!r} "
                                    f"(contract section 5: {', '.join(TEST_SCOPES)})"))
        if test.get("scope") and ttype != "checker":
            issues.append(("WARN", f"{where}: 'scope' only means anything on a 'checker' test "
                                   f"— type {ttype!r} ignores it"))
        if ttype not in TEST_TYPES:
            issues.append(("ERROR", f"{where}: unknown test type {ttype!r} "
                                    f"(contract section 5: {', '.join(TEST_TYPES)})"))
            continue
        command = (test.get("command") or "").strip()
        if ttype in {"checker", "command"} and not command:
            issues.append(("ERROR", f"{where}: type '{ttype}' requires a 'command'"))
        if ttype == "manual" and not (test.get("description") or "").strip():
            issues.append(("ERROR", f"{where}: type 'manual' requires a 'description' "
                                    f"— it is the line the human ticks at the gate"))
        if command and DENY_COMMAND_RE.search(command):
            issues.append(("ERROR", f"{where}: acceptance tests never deploy, never fetch and "
                                    f"never shell out (contract sections 1 and 5) — this command "
                                    f"matches the deny-list: {command}"))
        if ttype == "checker" and command:
            m = CHECKER_COMMAND_RE.match(command)
            if not m:
                issues.append(("ERROR", f"{where}: a 'checker' test must run a skill-local "
                                        f"checker as 'python3 skills/<domain>/<slug>/scripts/"
                                        f"check_<name>.py ...' — got: {command}"))
            elif not (repo_root / m.group(1)).is_file():
                issues.append(("ERROR", f"{where}: checker {m.group(1)} does not exist — a plan "
                                        f"may not declare a test that cannot run (deepen the "
                                        f"skill first, or use a different test type)"))
            else:
                if not _checker_uses_standard_form(command):
                    # Not every skill checker takes --manifest-dir: a few take a
                    # positional path or --file/--workbook. Rewriting the command
                    # to the house form would break them, so this is a WARN and
                    # the step-tester runs what the plan declares (section 5).
                    issues.append(("WARN", f"{where}: checker declares a non-standard argument "
                                           f"form; step-tester will run it verbatim"))
                stub = _checker_stub_reason(repo_root / m.group(1))
                if stub:
                    issues.append(("WARN", f"{where}: checker looks like a scaffold stub — the "
                                           f"tester will fail this step ({m.group(1)}: {stub}); "
                                           f"deepen the skill's checker, or declare a test type "
                                           f"that can actually run"))
                name = m.group(1).rsplit("/", 1)[-1]
                # Section 5: `scope` is declared intent; the literal --manifest-dir governs.
                # The two must name the same tree.
                md = re.search(r"--manifest-dir(?:=|\s+)(\S+)", command or "")
                if md and test.get("scope"):
                    target = md.group(1).strip("'\"").rstrip("/")
                    looks_step = bool(re.search(r"artefacts/M\d+-S\d+", target))
                    looks_build = target in {"artefacts", "./artefacts", "artefacts/"} or target.endswith("/artefacts")
                    if (scope == "build" and looks_step) or (scope == "step" and looks_build):
                        issues.append(("WARN", f"{where}: declared scope '{scope}' disagrees with the command's "
                                               f"--manifest-dir {target} — the tester runs the command verbatim, "
                                               f"so make the two name the same tree"))
                if (name in CROSS_REFERENTIAL_CHECKERS
                        and step_type in CROSS_REFERENTIAL_STEP_TYPES
                        and scope == "step"):
                    issues.append(("WARN", f"{where}: {name} is cross-referential — it asserts "
                                           f"relationships across components a single "
                                           f"'{step_type}' step does not own, so a step-scoped "
                                           f"run reports findings this step cannot fix; declare "
                                           f'"scope": "build" on this test or drop it and rely '
                                           f"on the milestone acceptance test"))
        if ttype == "command" and command:
            if not command.startswith("python3 "):
                issues.append(("ERROR", f"{where}: a 'command' test must start with 'python3 ' "
                                        f"(stdlib-only, contract section 8): {command}"))
            else:
                script = _command_script_path(command)
                if script is None:
                    issues.append(("ERROR", f"{where}: 'command' test names no script path "
                                            f"after python3: {command}"))
                elif not (repo_root / script).exists() and not script.startswith(prefixes):
                    issues.append(("ERROR", f"{where}: 'command' test runs {script!r}, which is "
                                            f"neither a path in the repo nor under the build "
                                            f"directory ({', '.join(prefixes)})"))
    return issues


# A decision-tree step id: Q3, Q12, Q3a.
BRANCH_ID_RE = re.compile(r"^Q[0-9]+[a-z]?$")

# How the seven trees under standards/decision-trees/ actually head their steps.
# The dominant form is a flat `Q3. <question>` line at column 0 inside the tree's
# fenced block (automation-selection, sharing-selection, async-selection,
# flow-pattern-selector, integration-pattern-selection, agentforce-capability-
# selector); performance-tuning additionally groups steps under `## Q2–Q4 — ...`
# markdown headings. The bold and anchor forms are accepted so a tree may be
# reformatted without invalidating every plan that cites it.
#
# Every form is anchored at the start of a line on purpose. automation-selection
# says "(Same gate as Q3 — the ...)" mid-paragraph; matching a branch id
# anywhere in the prose would let a plan cite a step that only ever appears as
# a cross-reference, which is the citation this check exists to catch.
_BRANCH_FORMS = (
    r"^[ \t]*#{{1,6}}[ \t]*{b}(?![0-9A-Za-z])",          # ## Q3   /  ### Q3a — ...
    r"^[ \t]*(?:[-*+][ \t]+)?[*_]{{1,2}}{b}(?![0-9A-Za-z])",  # **Q3** / - **Q3**
    r"^[ \t]*(?:[-*+][ \t]+)?{b}[ \t]*[.):—–-]",  # Q3. ... / Q3) ... / - Q3 — ...
    r"(?i)\{{#[ \t]*{b}[ \t]*\}}",                       # {#q3} anchor
    r"(?i)<a[ \t][^>]*\b(?:id|name)[ \t]*=[ \t]*[\"']#?{b}[\"']",   # <a id="q3">
)


def _branch_in_tree(text: str, branch: str) -> bool:
    """Does `text` head a decision step called `branch`?"""
    escaped = re.escape(branch)
    return any(re.search(form.format(b=escaped), text, re.MULTILINE)
               for form in _BRANCH_FORMS)


def _decision_issues(decision: dict, where: str, repo_root: Path) -> list[tuple[str, str]]:
    """Grounding rule (build-planner Step 4): a decision cites a branch that is really in the tree.

    The failure this exists to catch is a plausible-looking citation: a real
    tree path plus a branch id the tree does not have, or a branch id with no
    tree at all. Neither can be checked by reading the plan alone, and both
    read as grounded work until someone opens the file.
    """
    issues: list[tuple[str, str]] = []
    tree = (decision.get("decision_tree") or "").strip()
    branch = (decision.get("branch") or "").strip()
    source_reference = (decision.get("source_reference") or "").strip()

    if tree:
        tree_path = repo_root / tree
        if not tree_path.is_file():
            issues.append(("ERROR", f"{where}: decision_tree '{tree}' does not exist — a "
                                    f"decision may not cite a tree that is not in the repo"))
        elif branch:
            if not BRANCH_ID_RE.match(branch):
                issues.append(("ERROR", f"{where}: branch {branch!r} is not a tree step id "
                                        f"(expected Q3, Q12, Q3a …)"))
            else:
                try:
                    text = tree_path.read_text(encoding="utf-8", errors="replace")
                except OSError as exc:  # pragma: no cover - unreadable file
                    issues.append(("ERROR", f"{where}: cannot read decision_tree '{tree}': {exc}"))
                    text = None
                if text is not None and not _branch_in_tree(text, branch):
                    issues.append(("ERROR", f"{where}: {tree} has no step {branch!r} — the tree "
                                            f"heads its steps as '{branch}. <question>', "
                                            f"'## {branch}', '**{branch}**' or an anchor. Cite "
                                            f"the branch that actually resolved the choice, or "
                                            f"drop the tree and record source_reference "
                                            f"with adr_required: true"))
    elif branch:
        issues.append(("ERROR", f"{where}: branch {branch!r} with no decision_tree — a branch id "
                                f"is unverifiable without the tree it belongs to"))

    if source_reference and not (repo_root / source_reference).exists():
        issues.append(("ERROR", f"{where}: source_reference '{source_reference}' does not exist"))

    if not tree and not source_reference:
        issues.append(("WARN", f"{where}: cites neither a decision_tree nor a source_reference — "
                               f"record where the choice came from (build-planner Step 4; schema decisions[].source_reference)"))
    return issues


def semantic_issues(plan: dict, repo_root: Path) -> list[tuple[str, str]]:
    """Contract checks the JSON Schema cannot express. (level, message)."""
    issues: list[tuple[str, str]] = []
    steps = plan.get("steps", []) or []
    milestones = plan.get("milestones", []) or []
    build_mode = plan.get("build_mode") or "design-only"
    artefacts_root = (plan.get("artefacts_root") or "artefacts").rstrip("/")

    # --- build mode -------------------------------------------------------
    if build_mode == "org-connected" and not ((plan.get("org") or {}).get("alias") or "").strip():
        issues.append(("ERROR", "build_mode 'org-connected' requires org.alias — the alias is "
                                "the only thing an org-requiring agent can read metadata "
                                "through (re-run init with --org-alias)"))

    # --- scale vs. plan shape (§ 3.1's sizing rule) — WARN only ------------
    # An ERROR here would turn a re-tier into a re-plan (§ 3.1, "CLI deltas").
    # `project` (including absent `scale`) is the unbounded shape and is never
    # checked.
    scale = plan.get("scale")
    limits = SCALE_SHAPE_LIMITS.get(scale)
    # Nothing to check before the planner has written a single milestone —
    # every build is briefly shapeless between `init` and its first
    # `set-plan`, and that is not a sizing-rule disagreement.
    if limits and milestones:
        n_milestones = len(milestones)
        n_steps = len(steps)
        if "steps" in limits:  # ask: exactly one milestone, exactly one step
            if n_milestones != limits["milestones"] or n_steps != limits["steps"]:
                issues.append(("WARN", f"scale 'ask' expects {limits['milestones']} milestone and "
                                       f"{limits['steps']} step (§ 3.1's sizing rule: 'ask' plan "
                                       f"shape is 1 milestone, 1 step) — this plan has "
                                       f"{n_milestones} milestone(s) and {n_steps} step(s); "
                                       f"re-tier to 'feature' or 'project', or re-init --scale"))
        elif n_milestones != limits["milestones"] or n_steps > limits["max_steps"]:
            issues.append(("WARN", f"scale 'feature' expects {limits['milestones']} milestone and "
                                   f"at most {limits['max_steps']} steps (§ 3.1's sizing rule: "
                                   f"'feature' plan shape is 1 milestone, ≤ 5 steps) — this plan "
                                   f"has {n_milestones} milestone(s) and {n_steps} step(s); "
                                   f"re-tier to 'project', or re-init --scale"))
    if scale == "ask":
        for step in steps:
            if step.get("human_gate"):
                issues.append(("WARN", f"step {step.get('id')}: human_gate: true at scale 'ask' — "
                                       f"§ 3.1's single-step ask plan is written human_gate: "
                                       f"false; `ensure-gates` still adds no step: gate at this "
                                       f"scale, so this flag has no effect"))

    # --- milestones: ids ordered M1..Mn -----------------------------------
    for i, milestone in enumerate(milestones):
        expected = f"M{i + 1}"
        if milestone.get("id") != expected:
            issues.append(("ERROR", f"milestones[{i}]: id {milestone.get('id')!r} out of order — "
                                    f"milestone ids must run {expected} in sequence"))
    milestone_ids = [m.get("id") for m in milestones]
    milestone_index = {mid: i for i, mid in enumerate(milestone_ids)}
    if len(set(milestone_ids)) != len(milestone_ids):
        issues.append(("ERROR", "duplicate milestone id(s)"))

    # --- steps: unique ids, valid type, real agent, resolvable citations ---
    step_ids = [s.get("id") for s in steps]
    duplicates = sorted({sid for sid in step_ids if step_ids.count(sid) > 1})
    for sid in duplicates:
        issues.append(("ERROR", f"duplicate step id {sid!r}"))
    by_id = {s.get("id"): s for s in steps}

    agent_cache: dict[str, str | None] = {}
    for step in steps:
        sid = step.get("id", "<no id>")
        stype = step.get("type")
        if stype not in STEP_TYPES:
            issues.append(("ERROR", f"step {sid}: type {stype!r} is not in the contract "
                                    f"section 4 table ({', '.join(STEP_TYPES)})"))

        agent = step.get("agent")
        if agent:
            if agent not in agent_cache:
                agent_cache[agent] = _agent_problem(agent, repo_root, build_mode)
            problem = agent_cache[agent]
            if problem:
                issues.append(("ERROR", f"step {sid}: {problem}"))

        skills = step.get("skills") or []
        for skill in skills:
            if not (repo_root / "skills" / skill / "SKILL.md").is_file():
                issues.append(("ERROR", f"step {sid}: skill '{skill}' does not resolve to "
                                        f"skills/{skill}/SKILL.md"))
        if not skills:
            issues.append(("WARN", f"step {sid}: no skills[] — a step that reads no skill is "
                                   f"freestyling Salesforce knowledge (contract section 8)"))

        for template in step.get("templates") or []:
            if not (repo_root / template).exists():
                issues.append(("ERROR", f"step {sid}: template '{template}' does not exist"))
        for tree in step.get("decision_trees") or []:
            if not (repo_root / tree).exists():
                issues.append(("ERROR", f"step {sid}: decision tree '{tree}' does not exist"))

        # --- milestone membership ----------------------------------------
        mid = step.get("milestone")
        if mid not in milestone_index:
            issues.append(("ERROR", f"step {sid}: milestone {mid!r} is not defined in milestones[]"))
        elif isinstance(sid, str) and not sid.startswith(f"{mid}-"):
            issues.append(("ERROR", f"step {sid}: id does not carry its milestone prefix '{mid}-'"))

        # --- acceptance tests --------------------------------------------
        tests = step.get("acceptance_tests") or []
        if not tests:
            issues.append(("ERROR", f"step {sid}: needs at least one acceptance test "
                                    f"(contract section 5)"))
        issues.extend(_acceptance_issues(tests, f"step {sid}", repo_root, artefacts_root,
                                         step_type=stype))

        # --- status bookkeeping -------------------------------------------
        if step.get("status") == "blocked" and not (step.get("blocked_reason") or "").strip():
            issues.append(("ERROR", f"step {sid}: status 'blocked' requires a blocked_reason"))
        if step.get("status") != "blocked" and step.get("blocked_reason"):
            issues.append(("WARN", f"step {sid}: blocked_reason left over from an earlier block"))

        outputs = step.get("outputs") or []
        if not outputs:
            issues.append(("WARN", f"step {sid}: declares no outputs[]"))
        root_dir = plan.get("artefacts_root", "artefacts").rstrip("/")
        for out in outputs:
            if not out.startswith(f"{root_dir}/{sid}/"):
                issues.append(("WARN", f"step {sid}: output '{out}' is not under "
                                       f"{root_dir}/{sid}/ (contract section 4)"))

    # --- decisions: the cited branch is really in the cited tree ----------
    for i, decision in enumerate(plan.get("decisions") or []):
        if not isinstance(decision, dict):
            continue
        issues.extend(_decision_issues(
            decision, f"decision {decision.get('id') or f'[{i}]'}", repo_root))

    # --- dependency graph -------------------------------------------------
    graph: dict[str, list[str]] = {}
    for step in steps:
        sid = step.get("id")
        deps = [d for d in (step.get("depends_on") or [])]
        graph[sid] = deps
        for dep in deps:
            if dep not in by_id:
                issues.append(("ERROR", f"step {sid}: depends_on '{dep}' which does not exist"))
            elif dep == sid:
                issues.append(("ERROR", f"step {sid}: depends on itself"))
            else:
                here = milestone_index.get(step.get("milestone"), -1)
                there = milestone_index.get(by_id[dep].get("milestone"), -1)
                if there > here:
                    issues.append(("ERROR", f"step {sid}: depends on '{dep}' in a later "
                                            f"milestone — dependencies must be ordered"))
    graph = {k: [d for d in v if d in graph] for k, v in graph.items()}
    cycle = _find_cycle(graph)
    if cycle:
        issues.append(("ERROR", f"depends_on cycle: {' -> '.join(cycle)}"))

    # --- milestone.steps lists exactly its steps + milestone tests --------
    for milestone in milestones:
        mid = milestone.get("id")
        listed = list(milestone.get("steps") or [])
        actual = [s.get("id") for s in steps if s.get("milestone") == mid]
        if sorted(listed) != sorted(actual):
            missing = sorted(set(actual) - set(listed))
            extra = sorted(set(listed) - set(actual))
            detail = []
            if missing:
                detail.append(f"missing {', '.join(missing)}")
            if extra:
                detail.append(f"lists unknown/foreign {', '.join(extra)}")
            issues.append(("ERROR", f"milestone {mid}: steps[] must list exactly its steps — "
                                    f"{'; '.join(detail)}"))
        elif listed != actual:
            issues.append(("WARN", f"milestone {mid}: steps[] order differs from steps[] order "
                                   f"in the plan"))
        if not (milestone.get("acceptance_tests") or []):
            issues.append(("ERROR", f"milestone {mid}: needs at least one acceptance test "
                                    f"(contract section 5)"))
        issues.extend(_acceptance_issues(milestone.get("acceptance_tests") or [],
                                         f"milestone {mid}", repo_root, artefacts_root))
        if not actual:
            issues.append(("WARN", f"milestone {mid}: has no steps"))

    # --- human gates ------------------------------------------------------
    gate_names = [g.get("name") for g in plan.get("human_gates", []) or []]
    duplicates = sorted({g for g in gate_names if gate_names.count(g) > 1})
    for name in duplicates:
        issues.append(("ERROR", f"duplicate human gate {name!r}"))
    for required in required_gate_names(plan):
        if required not in gate_names:
            issues.append(("ERROR", f"missing human gate {required!r} — "
                                    f"run `build_plan.py ensure-gates` to add it as pending"))

    # --- clarifications ---------------------------------------------------
    # One question with a broken record is per-question news; N unanswered
    # blocking questions is a single fact about the gate. A real clarifier
    # emits ~100 of them, and a WARN per question buried the ERRORs that
    # matter under a wall of text saying the same thing.
    open_blocking = 0
    for clar in plan.get("clarifications", []) or []:
        if clar.get("status") == "answered" and not (clar.get("answer") or "").strip():
            issues.append(("ERROR", f"clarification {clar.get('id')}: status 'answered' "
                                    f"with an empty answer"))
        if clar.get("kind") == "blocking" and clar.get("status") == "open":
            open_blocking += 1
    if open_blocking:
        issues.append(("WARN", f"{open_blocking} blocking question(s) still open — G1 cannot "
                               f"pass until they are answered or deferred"))

    return issues


def required_gate_names(plan: dict) -> list[str]:
    """Gates the contract (section 3) requires for this plan, in order.

    Lifecycle order: G1, G2, then per milestone the `step:<id>` gates of its
    human-gated steps (they are reached before the milestone closes) followed
    by that milestone's own G3.

    Section 3.1: at `scale: ask` the single step is expected `human_gate:
    false`, and no `step:` gate is added even if it is — a step gate is
    ceremony `ask` does not spend (`ensure-gates` deltas).
    """
    names = ["clarifications", "plan"]
    steps = plan.get("steps", []) or []
    ask = plan.get("scale") == "ask"
    for milestone in plan.get("milestones", []) or []:
        mid = milestone.get("id")
        if not mid:
            continue
        if not ask:
            for step in steps:
                if step.get("milestone") == mid and step.get("human_gate") and step.get("id"):
                    names.append(f"step:{step['id']}")
        names.append(f"milestone:{mid}")
    return names


def validate_plan(plan: Any, repo_root: Path, schema: dict) -> list[tuple[str, str]]:
    """Schema + semantic issues, schema first (semantics assume a shape)."""
    errors = [("ERROR", msg) for msg in schema_errors(plan, schema, schema)]
    if errors:
        return errors
    return semantic_issues(plan, repo_root)


# --------------------------------------------------------------------------
# Plan IO
# --------------------------------------------------------------------------

def read_plan(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        _die(f"no plan file at {path}")
    except json.JSONDecodeError as exc:
        _die(f"{path} is not valid JSON: {exc}")
    raise AssertionError("unreachable")


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp{os.getpid()}")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def plan_json(plan: dict) -> str:
    return json.dumps(plan, indent=2, ensure_ascii=False) + "\n"


def write_plan(path: Path, plan: dict, repo_root: Path, schema: dict,
               allow_semantic_errors: bool = False) -> int:
    """Re-validate then replace atomically. Returns a process exit code.

    `allow_semantic_errors` is for the *reject* gate paths only: a human
    rejecting a plan or a set of clarifications must be recordable even when
    the plan they are rejecting is the reason validation fails. Schema errors
    still block — an off-schema document is not a plan.
    """
    hard = schema_errors(plan, schema, schema)
    if hard:
        print(f"refusing to write {path} — the result would be off-schema:", file=sys.stderr)
        for msg in hard:
            print(f"  ERROR {msg}", file=sys.stderr)
        return 1
    issues = semantic_issues(plan, repo_root)
    errors = [msg for level, msg in issues if level == "ERROR"]
    if errors and not allow_semantic_errors:
        print(f"refusing to write {path} — the result would be invalid:", file=sys.stderr)
        for msg in errors:
            print(f"  ERROR {msg}", file=sys.stderr)
        return 1
    for level, msg in issues:
        if level == "WARN":
            print(f"WARN {msg}")
    for msg in errors:
        print(f"WARN written anyway (rejection path): {msg}")
    _atomic_write(path, plan_json(plan))
    return 0


# --------------------------------------------------------------------------
# Outputs and test results on disk (contract sections 4 and 5)
# --------------------------------------------------------------------------

def check_outputs(plan: dict, step: dict, build_dir: Path) -> dict:
    """Do the step's declared outputs[] actually exist, non-empty and parseable?

    Returns `{ok, step, missing[], empty[], malformed[]}`. A step that declares
    no outputs has nothing to check and is `ok` — `validate` already WARNs
    about it, and some steps (a manual checklist) legitimately write nothing.
    """
    missing: list[str] = []
    empty: list[str] = []
    malformed: list[str] = []
    for out in step.get("outputs") or []:
        target = build_dir / out
        if not target.is_file():
            missing.append(out)
            continue
        try:
            raw = target.read_bytes()
        except OSError as exc:
            malformed.append(f"{out}: cannot read ({exc})")
            continue
        if not raw.strip():
            empty.append(out)
            continue
        if target.suffix.lower() == ".xml":
            try:
                ElementTree.fromstring(raw)
            except ElementTree.ParseError as exc:
                malformed.append(f"{out}: {exc}")
    return {
        "ok": not (missing or empty or malformed),
        "step": step.get("id"),
        "missing": missing,
        "empty": empty,
        "malformed": malformed,
    }


def _results_path(plan: dict, step_id: str, build_dir: Path) -> Path:
    tests_dir = (plan.get("docs") or {}).get("tests") or "tests/"
    return build_dir / tests_dir.rstrip("/") / step_id / "results.json"


def _results_problem(plan: dict, step_id: str, build_dir: Path) -> str | None:
    """Why `tests/<step-id>/results.json` does not license status 'tested'."""
    path = _results_path(plan, step_id, build_dir)
    if not path.is_file():
        return (f"no test results at {path} — status 'tested' means step-tester ran and "
                f"wrote results.json (contract section 5)")
    try:
        results = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return f"{path} is not readable JSON: {exc}"
    if results.get("passed") is not True:
        return (f"{path} records passed={results.get('passed')!r} — only a passing test run "
                f"moves a step to 'tested'")
    return None


def read_plan_on_schema(path: Path, schema: dict) -> dict:
    """Read a plan and refuse to touch it if it is off-schema.

    The mutating subcommands walk milestones[], steps[] and human_gates[]
    before they validate anything. A corrupted plan should exit 1 with a
    readable message, not a traceback from halfway through a mutation.
    """
    plan = read_plan(path)
    errors = schema_errors(plan, schema, schema)
    if errors:
        for msg in errors:
            print(f"ERROR {msg}", file=sys.stderr)
        _die(f"refusing to touch an off-schema plan at {path}")
    return plan


def _die(message: str) -> None:
    print(f"ERROR {message}", file=sys.stderr)
    raise SystemExit(1)


def _now(explicit: str | None = None) -> str:
    if explicit:
        return explicit
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------
# Rendering helpers
# --------------------------------------------------------------------------

def _cell(value: Any) -> str:
    if value is None or value == "":
        return "—"
    if isinstance(value, (list, tuple)):
        if not value:
            return "—"
        return "<br>".join(_cell(v) for v in value)
    text = str(value).replace("|", "\\|")
    return " ".join(text.split())


def _bullets(items: Iterable[str], empty: str = "_None recorded._") -> str:
    items = list(items)
    if not items:
        return empty
    return "\n".join(f"- {item}" for item in items)


def render_plan_md(plan: dict) -> str:
    out: list[str] = []
    out.append(f"# {plan['title']}")
    out.append("")
    out.append(GENERATED_BANNER)
    out.append("")
    out.append("| Field | Value |")
    out.append("| --- | --- |")
    out.append(f"| Build id | `{plan['build_id']}` |")
    out.append(f"| Status | `{plan['status']}` |")
    out.append(f"| Plan version | {plan['version']} |")
    out.append(f"| Created | {_cell(plan['created'])} |")
    out.append(f"| Requirement | `{plan['requirement']['source_path']}` |")
    out.append(f"| Artefacts root | `{plan['artefacts_root']}/` |")
    out.append("")
    out.append("## Requirement")
    out.append("")
    out.append(plan["requirement"]["summary"].strip())
    out.append("")

    out.append("## Scope")
    out.append("")
    out.append("### In scope")
    out.append("")
    out.append(_bullets(plan["scope"]["in"]))
    out.append("")
    out.append("### Out of scope")
    out.append("")
    out.append(_bullets(plan["scope"]["out"]))
    out.append("")
    out.append("### Fit / gap")
    out.append("")
    fit_gap = plan["scope"]["fit_gap"]
    if fit_gap:
        out.append("| Requirement | Verdict | Note |")
        out.append("| --- | --- | --- |")
        for row in fit_gap:
            out.append(f"| {_cell(row.get('requirement'))} | `{row.get('verdict')}` "
                       f"| {_cell(row.get('note'))} |")
    else:
        out.append("_No fit-gap rows recorded._")
    out.append("")

    out.append("## Assumptions")
    out.append("")
    assumptions = plan.get("assumptions") or []
    if assumptions:
        out.append("| Id | Assumption | Because |")
        out.append("| --- | --- | --- |")
        for row in assumptions:
            out.append(f"| `{row.get('id')}` | {_cell(row.get('text'))} "
                       f"| {_cell(row.get('because'))} |")
    else:
        out.append("_No assumptions recorded._")
    out.append("")

    out.append("## Decisions")
    out.append("")
    decisions = plan.get("decisions") or []
    if decisions:
        out.append("| Id | Decision | Decision tree | Branch | ADR | Rationale |")
        out.append("| --- | --- | --- | --- | --- | --- |")
        for row in decisions:
            tree = row.get("decision_tree")
            out.append(f"| `{row.get('id')}` | {_cell(row.get('decision'))} "
                       f"| {('`' + tree + '`') if tree else '—'} | {_cell(row.get('branch'))} "
                       f"| {'✔' if row.get('adr_required') else ''} "
                       f"| {_cell(row.get('rationale'))} |")
        # The evidence a reader needs to check a decision without opening the
        # tree: what the branch actually said, what was turned down, what it
        # costs. Sub-bullets rather than columns — a quoted branch does not fit
        # in a table cell.
        detail: list[str] = []
        for row in decisions:
            lines: list[str] = []
            if row.get("branch_quote"):
                lines.append(f"  - Branch quote: {_cell(row['branch_quote'])}")
            if row.get("source_reference"):
                lines.append(f"  - Source reference: `{row['source_reference']}`")
            if row.get("alternatives_rejected"):
                rejected = "; ".join(_cell(alt) for alt in row["alternatives_rejected"])
                lines.append(f"  - Alternatives rejected: {rejected}")
            if row.get("consequences"):
                lines.append(f"  - Consequences: {_cell(row['consequences'])}")
            if lines:
                detail.append(f"- `{row.get('id')}`")
                detail.extend(lines)
        if detail:
            out.append("")
            out.extend(detail)
    else:
        out.append("_No decisions recorded._")
    out.append("")

    out.append("## Milestones")
    out.append("")
    steps_by_milestone: dict[str, list[dict]] = {}
    for step in plan.get("steps") or []:
        steps_by_milestone.setdefault(step.get("milestone"), []).append(step)
    milestones = plan.get("milestones") or []
    if not milestones:
        out.append("_No milestones planned yet._")
        out.append("")
    for milestone in milestones:
        mid = milestone["id"]
        out.append(f"### {mid} — {milestone['title']}")
        out.append("")
        if milestone.get("goal"):
            out.append(f"Goal: {milestone['goal']}")
            out.append("")
        out.append(f"Status: `{milestone.get('status', 'pending')}` · "
                   f"Gate: `milestone:{mid}` = `{gate_status(plan, f'milestone:{mid}')}`")
        out.append("")
        out.append("| Step | Title | Type | Agent | Status | Depends on | Outputs | Acceptance tests |")
        out.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
        for step in steps_by_milestone.get(mid, []):
            tests = [_test_label(t) for t in step.get("acceptance_tests") or []]
            status_cell = f"`{step.get('status')}`"
            if step.get("status") == "blocked" and step.get("blocked_reason"):
                status_cell += f" ({_cell(step['blocked_reason'])})"
            out.append(
                f"| `{step.get('id')}` | {_cell(step.get('title'))} | `{step.get('type')}` "
                f"| `{step.get('agent')}` | {status_cell} "
                f"| {_cell(step.get('depends_on'))} | {_cell(step.get('outputs'))} "
                f"| {_cell(tests)} |"
            )
        if not steps_by_milestone.get(mid):
            out.append("| — | _no steps_ | — | — | — | — | — | — |")
        out.append("")
        amended = [s for s in steps_by_milestone.get(mid, []) if s.get("amendments")]
        if amended:
            out.append("Amended (via `build_plan.py amend-step`):")
            out.append("")
            for s in amended:
                for a in s["amendments"]:
                    field_list = ", ".join(a.get("fields") or [])
                    out.append(f"- `{s.get('id')}` — {field_list} "
                               f"by {_cell(a.get('by'))} at {_cell(a.get('at'))}: "
                               f"{_cell(a.get('reason'))}")
            out.append("")
        out.append("Milestone acceptance tests:")
        out.append("")
        out.append(_bullets(
            f"`{t.get('type')}`"
            + (f" [scope: `{t['scope']}`]" if t.get("scope") else "")
            + f" — {_cell(t.get('command') or t.get('description'))}"
            for t in milestone.get("acceptance_tests") or []))
        out.append("")

    out.append("## Human gates")
    out.append("")
    out.append("| Gate | Status | By | At | Notes |")
    out.append("| --- | --- | --- | --- | --- |")
    for gate in plan.get("human_gates") or []:
        out.append(f"| `{gate.get('name')}` | `{gate.get('status')}` | {_cell(gate.get('by'))} "
                   f"| {_cell(gate.get('at'))} | {_cell(gate.get('notes'))} |")
    if not (plan.get("human_gates") or []):
        out.append("| — | — | — | — | — |")
    out.append("")
    out.append(f"Clarifications view: `{plan['docs']['clarifications']}` · "
               f"decisions log: `{plan['docs']['decisions']}` · "
               f"traceability: `{plan['docs']['traceability']}`")
    out.append("")
    return "\n".join(out)


# The heading a clarification with no `group` lands under. Last, so a plan
# that groups nothing still renders one predictable section.
UNGROUPED_HEADING = "Other"


def group_clarifications(clarifications: list[dict]) -> list[tuple[str, list[dict]]]:
    """Group a kind's questions by their optional `group`, deterministically.

    Groups come out in first-appearance order — the clarifier controls the
    order by the order it writes clarifications[], and nothing sorts behind its
    back — with the ungrouped questions last under `Other`. Ordering depends
    only on plan.json, which is what keeps `render` byte-deterministic.
    """
    order: list[str] = []
    buckets: dict[str, list[dict]] = {}
    for clar in clarifications:
        raw = clar.get("group")
        name = raw.strip() if isinstance(raw, str) and raw.strip() else UNGROUPED_HEADING
        if name not in buckets:
            buckets[name] = []
            order.append(name)
        buckets[name].append(clar)
    named = [n for n in order if n != UNGROUPED_HEADING]
    if UNGROUPED_HEADING in buckets:
        named.append(UNGROUPED_HEADING)
    return [(name, buckets[name]) for name in named]


def render_clarifications_md(plan: dict) -> str:
    out: list[str] = []
    out.append(f"# Clarifications — {plan['title']}")
    out.append("")
    out.append(GENERATED_BANNER)
    out.append("")
    out.append(f"Build `{plan['build_id']}` · plan version {plan['version']} · "
               f"status `{plan['status']}` · gate `clarifications` = "
               f"`{gate_status(plan, 'clarifications')}`")
    out.append("")
    out.append("Fill in each `Answer:` line — the answer may run over several lines, up to the "
               "next heading (`### <group>` or `#### Q<n>`) or a `---` rule — then run:")
    out.append("")
    out.append("```bash")
    out.append(f"python3 scripts/build_plan.py ingest-answers <build-dir>/plan.json")
    out.append("```")
    out.append("")
    out.append("Accepting a proposed default: copy it onto the `Answer:` line. Deferring a "
               "blocking question: write `DEFER: <reason>` and pass `--allow-deferred`.")
    out.append("")
    clarifications = plan.get("clarifications") or []
    for kind, heading, empty in (
        ("blocking", "## Blocking", "_No blocking questions._"),
        ("informational", "## Informational", "_No informational questions._"),
    ):
        out.append(heading)
        out.append("")
        of_kind = [c for c in clarifications if c.get("kind") == kind]
        if not of_kind:
            out.append(empty)
            out.append("")
            continue
        for group_name, members in group_clarifications(of_kind):
            out.append(f"### {group_name}")
            out.append("")
            for clar in members:
                out.append(f"#### {clar['id']} — status: {clar.get('status', 'open')}")
                out.append("")
                out.append(f"**Question:** {clar.get('question', '').strip()}")
                out.append("")
                if clar.get("why"):
                    out.append(f"**Why it matters:** {clar['why'].strip()}")
                    out.append("")
                if clar.get("owner_role"):
                    out.append(f"**Who can answer:** {clar['owner_role'].strip()}")
                    out.append("")
                if clar.get("answer_shape"):
                    out.append(f"**Answer shape:** {clar['answer_shape'].strip()}")
                    out.append("")
                if clar.get("source_skill"):
                    out.append(f"**From skill:** `{clar['source_skill']}`")
                    out.append("")
                if clar.get("proposed_default"):
                    out.append(f"**Proposed default:** {clar['proposed_default'].strip()}")
                    out.append("")
                answer = (clar.get("answer") or "").strip()
                out.append(f"Answer: {answer}".rstrip())
                out.append("")
    return "\n".join(out)


def gate_status(plan: dict, name: str) -> str:
    for gate in plan.get("human_gates") or []:
        if gate.get("name") == name:
            return gate.get("status", "pending")
    return "absent"


def render_run_md(plan: dict, build_dir: Path) -> str:
    """§ 3.1: the `scale: ask` rendered view — RUN.md at the build root.

    Only called when `scale == "ask"`. Byte-deterministic like PLAN.md and
    CLARIFICATIONS.md: every line comes from plan.json content, or from
    whether a declared path exists on disk right now (a fact checked fresh
    each render, not a timestamp) — the wall clock never reaches it.
    """
    out: list[str] = []
    out.append(f"# {plan['title']}")
    out.append("")
    out.append(GENERATED_BANNER)
    out.append("")
    req_summary = ((plan.get("requirement") or {}).get("summary") or "").strip()
    out.append(req_summary.splitlines()[0].strip() if req_summary
               else "_No requirement summary recorded._")
    out.append("")

    steps = plan.get("steps") or []
    out.append("## Step")
    out.append("")
    if not steps:
        out.append("_No step planned yet._")
        out.append("")
    for s in steps:
        sid = s.get("id")
        out.append(f"### {sid} — {_cell(s.get('title'))}")
        out.append("")
        out.append(f"- Agent: `{s.get('agent')}`")
        out.append(f"- Skills: {_cell(s.get('skills'))}")
        out.append(f"- Status: `{s.get('status')}`")
        out.append("")

        out.append("Outputs:")
        out.append("")
        outputs = s.get("outputs") or []
        if outputs:
            for path in outputs:
                exists = (build_dir / path).is_file()
                out.append(f"- `{path}` — {'exists' if exists else 'missing'}")
        else:
            out.append("_No outputs declared._")
        out.append("")

        out.append("Acceptance tests:")
        out.append("")
        tests = s.get("acceptance_tests") or []
        if tests:
            for t in tests:
                out.append(f"- {_test_label(t)}")
        else:
            out.append("_No acceptance tests declared._")
        if sid:
            results_path = _results_path(plan, sid, build_dir)
            if results_path.is_file():
                try:
                    results = json.loads(results_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    results = None
                if isinstance(results, dict):
                    tests_root = (plan.get("docs") or {}).get("tests") or "tests/"
                    rel = f"{tests_root.rstrip('/')}/{sid}/results.json"
                    out.append("")
                    out.append(f"Latest test run (`{rel}`): passed={json.dumps(results.get('passed'))}")
        out.append("")

    clarifications = plan.get("clarifications") or []
    out.append("## Defaults applied")
    out.append("")
    defaults = [c for c in clarifications if (c.get("default_source") or "").strip()]
    out.append(_bullets(
        (f"`{c.get('id')}` — {_cell(c.get('question'))}: "
         f"{_cell(c.get('answer') or c.get('proposed_default'))} "
         f"(source: {_cell(c.get('default_source'))})")
        for c in defaults))
    out.append("")

    out.append("## Deferred questions")
    out.append("")
    deferred = [c for c in clarifications if c.get("status") == "deferred"]
    out.append(_bullets(
        f"`{c.get('id')}` — {_cell(c.get('question'))}: {_cell(c.get('answer'))}"
        for c in deferred))
    out.append("")

    out.append("## Manual acceptance")
    out.append("")
    manual = [
        _cell(t.get("description"))
        for owner in (steps, plan.get("milestones") or [])
        for holder in owner
        for t in (holder.get("acceptance_tests") or [])
        if t.get("type") == "manual"
    ]
    out.append(_bullets(manual))
    out.append("")

    out.append("## Gates")
    out.append("")
    gate_lines = []
    for gate in plan.get("human_gates") or []:
        line = f"`{gate.get('name')}`: `{gate.get('status')}`"
        if gate.get("by"):
            line += f" by {gate['by']}"
        if gate.get("at"):
            line += f" at {gate['at']}"
        gate_lines.append(line)
    out.append(_bullets(gate_lines))
    out.append("")

    out.append("## Next")
    out.append("")
    out.append("Printed, never run:")
    out.append("")
    out.append("```bash")
    alias = (plan.get("org") or {}).get("alias") or "<alias>"
    out.append(f"python3 scripts/mock_deploy.py plan.json --org-alias {alias} "
              f"--milestone {ASK_MILESTONE_ID}")
    out.append("```")
    out.append("")
    return "\n".join(out)


# --------------------------------------------------------------------------
# Subcommands
# --------------------------------------------------------------------------

def _ensure_skills_link(build_dir: Path, repo_root: Path) -> None:
    """Give the build directory a `skills` symlink to the repo's skills/.

    Contract section 5: acceptance-test commands are declared as
    `python3 skills/<domain>/<slug>/scripts/check_x.py --manifest-dir artefacts/<step-id>`
    and the tester runs them verbatim. Both halves resolve only from a directory
    that holds BOTH `skills/` and `artefacts/` — the build directory, once it
    carries this link. The build directory is gitignored, so the link is local
    state, recreated by `init` (and by `ensure-gates`) whenever it is missing.
    """
    link = build_dir / "skills"
    target = (repo_root / "skills").resolve()
    if link.is_symlink() or link.exists():
        return
    try:
        link.symlink_to(os.path.relpath(target, build_dir.resolve()), target_is_directory=True)
    except OSError:
        link.symlink_to(target, target_is_directory=True)


def cmd_init(args: argparse.Namespace) -> int:
    build_dir = Path(args.build_dir)
    requirement_src = Path(args.requirement)
    if not requirement_src.is_file():
        _die(f"requirement file not found: {requirement_src}")
    build_id = args.build_id or build_dir.resolve().name
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", build_id):
        _die(f"build id {build_id!r} must be kebab-case (pass --build-id to override "
             f"the directory name)")
    plan_path = build_dir / "plan.json"
    if plan_path.exists() and not args.force:
        _die(f"{plan_path} already exists — pass --force to re-initialise")

    # Section 2 layout.
    for sub in ("workbook", "artefacts", "tests", "envelopes", "reports"):
        (build_dir / sub).mkdir(parents=True, exist_ok=True)
    _ensure_skills_link(build_dir, Path(args.repo_root))
    requirement_dst = build_dir / "requirement.md"
    # `init --force` re-initialising a build in place may be pointed at the
    # build's OWN requirement.md (the human re-runs init against the file
    # init itself wrote last time) — src and dst are then the same file on
    # disk, and shutil.copyfile() raises SameFileError trying to open it for
    # both reading and writing at once. There is nothing to copy in that
    # case: the destination already holds the requirement text.
    same_file = requirement_dst.exists() and requirement_src.resolve() == requirement_dst.resolve()
    if not same_file:
        shutil.copyfile(requirement_src, requirement_dst)

    text = (build_dir / "requirement.md").read_text(encoding="utf-8", errors="replace")
    summary = next((line.strip() for line in text.splitlines()
                    if line.strip() and not line.lstrip().startswith("#")), "")
    if not summary:
        summary = f"See {build_dir.name}/requirement.md — no prose paragraph found."
    if len(summary) > 400:
        summary = summary[:397].rstrip() + "..."

    plan = {
        "build_id": build_id,
        "title": args.title,
        "version": 1,
        "status": "intake",
        "created": _now(args.now),
        "build_mode": "org-connected" if args.org_alias else "design-only",
        "requirement": {"source_path": "requirement.md", "summary": summary},
        "clarifications": [],
        "assumptions": [],
        "scope": {"in": [], "out": [], "fit_gap": []},
        "decisions": [],
        "milestones": [],
        "steps": [],
        "human_gates": [
            {"name": "clarifications", "status": "pending"},
            {"name": "plan", "status": "pending"},
        ],
        "artefacts_root": "artefacts",
        "docs": {
            "plan": "PLAN.md",
            "clarifications": "CLARIFICATIONS.md",
            "decisions": "decisions.md",
            "traceability": "traceability.md",
            "workbook": "workbook/",
            "reports": "reports/",
            "tests": "tests/",
            "envelopes": "envelopes/",
        },
        "history": [],
    }
    if args.org_alias:
        plan["org"] = {"alias": args.org_alias}
    if args.scale:
        plan["scale"] = args.scale
    schema = load_schema(args.schema)
    rc = write_plan(plan_path, plan, Path(args.repo_root), schema)
    if rc:
        return rc
    for name, header in (("decisions", "# Decisions log\n\nAppend-only. Written by the "
                                       "build doc keeper.\n"),
                         ("traceability", "# Traceability — REQ → step → artefact → test\n\n"
                                          "Written by the build doc keeper.\n")):
        target = build_dir / plan["docs"][name]
        if not target.exists():
            _atomic_write(target, header)
    _render(build_dir, plan)
    print(f"initialised build '{build_id}' at {build_dir}")
    print(f"  build mode:     {plan['build_mode']}"
          + (f" (org alias: {args.org_alias})" if args.org_alias
             else " — steps may only be owned by agents with requires_org: false"))
    # Section 3.1: `scale` is optional at init — absent leaves it unset, and
    # the clarifier's first pass sets it from the printed sizing rule. When a
    # human passes --scale here, that IS the override the contract describes;
    # the schema is `additionalProperties: false` (no room for a stored
    # `scale_override` flag), so this printed line is the only record of it —
    # `status` later has no on-disk way to know whether `scale` was set by a
    # human or by the clarifier.
    print(f"  scale:          " + (f"{args.scale} (human override: init --scale)" if args.scale
                                   else "(unset — the clarifier's Step 1 sets it from the "
                                        "printed sizing rule)"))
    print(f"  plan:           {plan_path}")
    print(f"  requirement:    {build_dir / 'requirement.md'}")
    print(f"  rendered views: {build_dir / plan['docs']['plan']}, "
          f"{build_dir / plan['docs']['clarifications']}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    plan_path = Path(args.plan)
    plan = read_plan(plan_path)
    schema = load_schema(args.schema)
    issues = validate_plan(plan, Path(args.repo_root), schema)
    errors = [m for lvl, m in issues if lvl == "ERROR"]
    warns = [m for lvl, m in issues if lvl == "WARN"]
    for msg in warns:
        print(f"WARN {msg}")
    for msg in errors:
        print(f"ERROR {msg}")
    if errors:
        print(f"{len(errors)} error(s), {len(warns)} warning(s) — plan is not valid.")
        return 1
    print(f"OK {plan_path}: {len(plan.get('milestones') or [])} milestone(s), "
          f"{len(plan.get('steps') or [])} step(s), {len(warns)} warning(s).")
    return 0


def _render(build_dir: Path, plan: dict) -> list[Path]:
    plan_md = build_dir / plan["docs"]["plan"]
    clar_md = build_dir / plan["docs"]["clarifications"]
    _atomic_write(plan_md, render_plan_md(plan))
    _atomic_write(clar_md, render_clarifications_md(plan))
    written = [plan_md, clar_md]
    if plan.get("scale") == "ask":
        # § 3.1: RUN.md is a rendered view, not part of docs{} (which is
        # `additionalProperties: false` — a docs.run key is a separate schema
        # change, not made here), so its path is fixed at the build root.
        run_md = build_dir / "RUN.md"
        _atomic_write(run_md, render_run_md(plan, build_dir))
        written.append(run_md)
    return written


def cmd_render(args: argparse.Namespace) -> int:
    plan_path = Path(args.plan)
    plan = read_plan(plan_path)
    schema = load_schema(args.schema)
    errors = schema_errors(plan, schema, schema)
    if errors:
        for msg in errors:
            print(f"ERROR {msg}", file=sys.stderr)
        print("refusing to render an off-schema plan.", file=sys.stderr)
        return 1
    written = _render(plan_path.parent, plan)
    for path in written:
        print(f"wrote {path}")
    return 0


_ANSWER_RE = re.compile(r"^Answer:(?P<text>.*)$")
# `### Q1` is the pre-grouping heading shape and `#### Q1` the grouped one;
# both are accepted so a view rendered before grouping still ingests.
_QUESTION_RE = re.compile(r"^#{3,6}\s+(?P<id>Q\d+)\b")
_HEADING_RE = re.compile(r"^#{1,6}\s")
_HRULE_RE = re.compile(r"^-{3,}\s*$")


def parse_clarification_answers(markdown: str) -> dict[str, str]:
    """Map question id -> answer text from a rendered CLARIFICATIONS.md.

    An answer may run over several lines: everything after `Answer:` up to the
    next heading (`#### Q2`, `### <group>`, `## Informational`, ...) or a `---`
    rule belongs to it, joined with newlines and trimmed. That is what a human
    actually does when the answer is a list, so parsing only the first line
    silently dropped the rest of their intent.
    """
    answers: dict[str, str] = {}
    current: str | None = None
    collecting: list[str] | None = None

    def flush() -> None:
        nonlocal collecting
        if collecting is not None and current is not None and current not in answers:
            answers[current] = "\n".join(collecting).strip()
        collecting = None

    for line in markdown.splitlines():
        header = _QUESTION_RE.match(line)
        if header:
            flush()
            current = header.group("id")
            continue
        if _HEADING_RE.match(line) or _HRULE_RE.match(line):
            flush()
            continue
        if collecting is not None:
            collecting.append(line)
            continue
        match = _ANSWER_RE.match(line)
        if match and current and current not in answers:
            collecting = [match.group("text")]
    flush()
    return answers


def cmd_ingest_answers(args: argparse.Namespace) -> int:
    plan_path = Path(args.plan)
    plan = read_plan(plan_path)
    build_dir = plan_path.parent
    clar_path = build_dir / plan.get("docs", {}).get("clarifications", "CLARIFICATIONS.md")
    if not clar_path.is_file():
        _die(f"no rendered clarifications at {clar_path} — run `render` first")
    answers = parse_clarification_answers(clar_path.read_text(encoding="utf-8"))

    problems: list[str] = []
    changed = 0
    for clar in plan.get("clarifications") or []:
        cid = clar.get("id")
        if cid not in answers:
            if clar.get("kind") == "blocking" and clar.get("status") == "open":
                problems.append(f"{cid}: blocking question has no '### {cid}' section in "
                                f"{clar_path.name} — the view is stale, re-run `render`")
            continue
        text = answers[cid].strip()
        if not text:
            if clar.get("kind") == "blocking":
                if (clar.get("answer") or "").strip():
                    problems.append(f"{cid}: blocking question was answered "
                                    f"({clar['answer'].splitlines()[0][:60]!r}) and the "
                                    f"Answer: line is now blank — blanking is not a way to "
                                    f"withdraw an answer; write 'DEFER: <reason>' and pass "
                                    f"--allow-deferred instead")
                else:
                    problems.append(f"{cid}: blocking question left with an empty Answer: line")
            continue
        if text.startswith("DEFER:"):
            reason = text[len("DEFER:"):].strip()
            if not args.allow_deferred:
                problems.append(f"{cid}: answered with a deferral — pass --allow-deferred "
                                f"to accept it")
                continue
            if not reason:
                problems.append(f"{cid}: 'DEFER:' needs a reason — write 'DEFER: <reason>'")
                continue
            new_status = "deferred"
        else:
            new_status = "answered"
        if clar.get("answer") != text or clar.get("status") != new_status:
            changed += 1
        clar["answer"] = text
        clar["status"] = new_status

    if problems:
        for msg in problems:
            print(f"ERROR {msg}", file=sys.stderr)
        print(f"refusing to ingest: {len(problems)} unanswered/undeferred blocking question(s).",
              file=sys.stderr)
        return 1

    schema = load_schema(args.schema)
    rc = write_plan(plan_path, plan, Path(args.repo_root), schema)
    if rc:
        return rc
    print(f"ingested {len(answers)} answer(s) from {clar_path.name}; {changed} clarification(s) "
          f"updated.")
    return 0


def _gate_blocker(plan: dict, milestone_id: str) -> str | None:
    """Why this milestone cannot start yet, or None. Contract section 3."""
    ids = [m.get("id") for m in plan.get("milestones") or []]
    if milestone_id not in ids:
        return f"milestone {milestone_id} is not in the plan"
    index = ids.index(milestone_id)
    needed = ["clarifications", "plan"]
    if index > 0:
        needed.append(f"milestone:{ids[index - 1]}")
    for name in needed:
        status = gate_status(plan, name)
        if status != "approved":
            return (f"gate '{name}' is '{status}', not 'approved' — the build refuses to start "
                    f"{milestone_id} until a human approves it")
    return None


def _step_gate_blocker(plan: dict, step: dict) -> str | None:
    """Why a human-gated step may not run yet, or None. Contract section 3."""
    if not step.get("human_gate"):
        return None
    name = f"step:{step.get('id')}"
    status = gate_status(plan, name)
    if status != "approved":
        return (f"step {step.get('id')} carries human_gate: true and gate '{name}' is "
                f"'{status}', not 'approved' — a human signs this step off before it runs "
                f"(`build_plan.py gate <plan> {name} approve --by <who>`)")
    return None


def cmd_next(args: argparse.Namespace) -> int:
    plan = read_plan(Path(args.plan))
    steps = plan.get("steps") or []
    by_id = {s.get("id"): s for s in steps}
    milestones = plan.get("milestones") or []

    if args.milestone:
        target = args.milestone
        if target not in [m.get("id") for m in milestones]:
            print("[]")
            print(f"reason: milestone {target} is not in the plan", file=sys.stderr)
            return 0
    else:
        if not milestones:
            print("[]")
            print("reason: the plan has no milestones yet — nothing to run", file=sys.stderr)
            return 0
        target = None
        for milestone in milestones:
            mid = milestone.get("id")
            mine = [s for s in steps if s.get("milestone") == mid]
            undocumented = [s for s in mine if s.get("status") != "documented"]
            if not undocumented:
                continue
            # A milestone whose only undocumented steps are `blocked` — with
            # its own gate already `approved` (a human has accepted that the
            # blocked step(s) go no further right now) — is not "next"; it is
            # done being actionable. Without this, `next` traps here forever
            # even though a later milestone is runnable (contract § 3 doesn't
            # require milestones to run in strict step-completion order, only
            # gate order via `_gate_blocker`).
            if all(s.get("status") == "blocked" for s in undocumented) \
                    and gate_status(plan, f"milestone:{mid}") == "approved":
                blocked_ids = ", ".join(s.get("id") for s in undocumented)
                print(f"reason: milestone {mid} skipped — its gate is approved and its "
                      f"only undocumented step(s) are blocked ({blocked_ids})",
                      file=sys.stderr)
                continue
            target = mid
            break
        if target is None:
            print("[]")
            print("reason: every milestone is fully documented — nothing left to run",
                  file=sys.stderr)
            return 0

    blocker = _gate_blocker(plan, target)
    if blocker:
        print("[]")
        print(f"reason: {blocker}", file=sys.stderr)
        return 0

    runnable = []
    waiting = 0
    gated: list[str] = []
    for step in steps:
        if step.get("milestone") != target or step.get("status") != "pending":
            continue
        deps = step.get("depends_on") or []
        if not all(by_id.get(d, {}).get("status") == "documented" for d in deps):
            waiting += 1
            continue
        blocked_by_gate = _step_gate_blocker(plan, step)
        if blocked_by_gate:
            gated.append(blocked_by_gate)
            continue
        runnable.append(step)
    print(json.dumps(runnable, indent=2, ensure_ascii=False))
    for reason in gated:
        print(f"reason: {reason}", file=sys.stderr)
    if not runnable and not gated:
        if waiting:
            print(f"reason: {waiting} step(s) in {target} are still waiting on depends_on",
                  file=sys.stderr)
        else:
            print(f"reason: no pending steps in {target}", file=sys.stderr)
    return 0


def cmd_set_status(args: argparse.Namespace) -> int:
    plan_path = Path(args.plan)
    schema = load_schema(args.schema)
    plan = read_plan_on_schema(plan_path, schema)
    step = next((s for s in plan.get("steps") or [] if s.get("id") == args.step_id), None)
    if step is None:
        _die(f"no step {args.step_id!r} in {plan_path}")
    current = step.get("status")
    new = args.status
    if new not in ALLOWED_TRANSITIONS:
        _die(f"unknown status {new!r}")
    if new not in ALLOWED_TRANSITIONS.get(current, set()):
        allowed = ", ".join(sorted(ALLOWED_TRANSITIONS.get(current, set()))) or "nothing"
        _die(f"illegal transition {current} -> {new} for {args.step_id} "
             f"(contract section 4 allows: {allowed})")
    if new == "blocked" and not (args.blocked_reason or step.get("blocked_reason")):
        _die("status 'blocked' requires --blocked-reason (contract section 8: use "
             "'skill-gap' when no skill covers the knowledge the step needs)")

    build_dir = plan_path.parent
    if new == "running":
        # Section 3: a step never starts ahead of its milestone's gates, and a
        # human-gated step never starts before its own sign-off.
        blocker = _gate_blocker(plan, step.get("milestone")) or _step_gate_blocker(plan, step)
        if blocker:
            _die(f"{args.step_id} may not start: {blocker}")
    if new in {"built", "tested"}:
        report = check_outputs(plan, step, build_dir)
        if not report["ok"]:
            detail = "; ".join(
                f"{label} {', '.join(report[label])}"
                for label in ("missing", "empty", "malformed") if report[label])
            _die(f"{args.step_id} may not move to '{new}': its declared outputs[] are not on "
                 f"disk under {build_dir} — {detail} "
                 f"(run `build_plan.py check-outputs {plan_path} {args.step_id}`)")
    if new == "tested":
        problem = _results_problem(plan, args.step_id, build_dir)
        if problem:
            _die(f"{args.step_id} may not move to 'tested': {problem}")

    step["status"] = new
    if new == "blocked":
        step["blocked_reason"] = args.blocked_reason or step.get("blocked_reason")
    else:
        step.pop("blocked_reason", None)

    # A milestone is building the moment one of its steps starts — including
    # rework after a rejected gate, or a re-run after a verification. An
    # 'accepted' milestone is left alone: only the human undoes their own G3.
    if new == "running":
        for milestone in plan.get("milestones") or []:
            if milestone.get("id") == step.get("milestone") \
                    and milestone.get("status", "pending") in {"pending", "rejected", "verified"}:
                milestone["status"] = "building"

    run_agent = args.run_agent
    if args.run_agent or args.envelope or args.started:
        run_agent = args.run_agent or step.get("agent")
        envelopes_dir = (plan.get("docs") or {}).get("envelopes") or "envelopes/"
        envelope = args.envelope or f"{envelopes_dir.rstrip('/')}/{args.step_id}/{new}.json"
        step.setdefault("runs", []).append({
            "agent": run_agent,
            "started": _now(args.started),
            "envelope_path": envelope,
            "result": args.result or new,
        })

    rc = write_plan(plan_path, plan, Path(args.repo_root), schema)
    if rc:
        return rc
    print(f"{args.step_id}: {current} -> {new}"
          + (f" (run appended: {run_agent})" if run_agent else ""))
    return 0


def _archive_rejected_plan(plan: dict, snapshot: dict, at: str, by: str | None,
                           reason: str) -> int:
    """Freeze a rejected plan body into history[] and return its version.

    Contract section 3 splits the two halves of "re-planning is a new plan
    version": the body is archived at the REJECTION (both routes — `gate plan
    reject` and `set-verification --outcome plan-rejected`), and `version` is
    incremented at the RE-PLAN (`set-plan` from status 'plan-rejected'). Doing
    both here would mint a v<n+1> that no planner ever wrote, and would bump
    twice when a plan is rejected by the verifier and then by the human.

    `snapshot` must already have had `history` popped — history never nests.
    """
    plan.setdefault("history", []).append({
        "version": snapshot["version"],
        "status": snapshot.get("status"),
        "superseded_at": at,
        "superseded_by": by or "unknown",
        "reason": reason,
        "plan": snapshot,
    })
    return int(snapshot["version"])


def _approval_refusal(plan: dict, name: str) -> tuple[str | None, list[str]]:
    """Why this gate may not be approved yet, plus lines worth printing.

    Contract section 3. A gate is a human's signature on a claim; the script
    refuses to collect one where the claim is not yet true.
    """
    notes: list[str] = []
    if name == "clarifications":
        still_open = [c.get("id") for c in plan.get("clarifications") or []
                      if c.get("kind") == "blocking" and c.get("status") == "open"]
        if still_open:
            return (f"blocking clarification(s) {', '.join(str(q) for q in still_open)} are "
                    f"still open — answer them (or defer with 'DEFER: <reason>' and "
                    f"`ingest-answers --allow-deferred`) before G1", notes)
    elif name == "plan":
        status = plan.get("status")
        if status != "verified":
            return (f"the build status is '{status}', not 'verified' — G2 signs off a plan the "
                    f"plan-verifier has passed (`set-verification --outcome verified`)", notes)
    elif name.startswith("milestone:"):
        mid = name.split(":", 1)[1]
        blocker = _gate_blocker(plan, mid)
        if blocker:
            return blocker, notes
        unfinished: list[str] = []
        for step in plan.get("steps") or []:
            if step.get("milestone") != mid:
                continue
            status = step.get("status")
            if status == "documented":
                continue
            if status == "blocked" and (step.get("blocked_reason") or "").strip():
                notes.append(f"  blocked (recorded): {step.get('id')} — {step['blocked_reason']}")
                continue
            unfinished.append(f"{step.get('id')} [{status}]")
        if unfinished:
            return (f"{mid} still has step(s) that are neither documented nor blocked with a "
                    f"recorded reason: {', '.join(unfinished)}", notes)
    return None, notes


def _gate_precondition(plan: dict, gate_name: str, decision: str) -> tuple[str | None, list[str]]:
    """Whether `decision` may be recorded for `gate_name` against `plan` right now.

    Returns `(refusal_message_or_None, informational_notes)`. `refusal_message`
    is already the full text a caller can hand straight to `_die()` — either
    "no gate ..." (the name does not exist in this plan's human_gates[]) or
    the `_approval_refusal()` claim wrapped for an 'approve' decision. A
    'reject' decision has no precondition (contract section 3: a human's
    rejection of an invalid plan must always be recordable).

    Factored out of `_gate_once` so `cmd_gate`'s `go`/`accept` aliases (§ 3.1)
    can check every member's precondition against ONE plan snapshot before
    writing any of them — the atomicity rule: an alias is all-or-nothing, so
    a later member's refusal must never be discovered only after an earlier
    member has already been written to disk.
    """
    gate = next((g for g in plan.get("human_gates") or [] if g.get("name") == gate_name), None)
    if gate is None:
        return (f"no gate {gate_name!r} in this plan — required gates are "
                f"{', '.join(required_gate_names(plan))}; run `ensure-gates` to add the missing ones",
                [])
    if decision == "approve":
        refusal, notes = _approval_refusal(plan, gate_name)
        if refusal:
            return f"gate {gate_name} cannot be approved: {refusal}", notes
        return None, notes
    return None, []


def _gate_once(plan_path: Path, schema: dict, repo_root: Path, gate_name: str,
              decision: str, by: str, notes: str | None, at: str) -> int:
    """Record one human gate decision. The body `cmd_gate` used to inline.

    Factored out so § 3.1's `go`/`accept` aliases can apply more than one real
    gate name, under the same --by/--at/--notes, in a single CLI invocation:
    each alias member is applied with this exact function, in order. By the
    time this runs, `cmd_gate` has already verified every member's
    precondition against one shared snapshot (see `_gate_precondition` and
    the atomicity pass in `cmd_gate`), so the refusal check below is a
    same-answer re-check against a fresh read, not the first time it runs.
    """
    plan = read_plan_on_schema(plan_path, schema)
    refusal, refusal_notes = _gate_precondition(plan, gate_name, decision)
    for line in refusal_notes:
        print(line)
    if refusal:
        _die(refusal)
    gate = next(g for g in plan.get("human_gates") or [] if g.get("name") == gate_name)
    approving = decision == "approve"
    snapshot = copy.deepcopy(plan)
    snapshot.pop("history", None)

    gate["status"] = "approved" if approving else "rejected"
    gate["by"] = by
    gate["at"] = at
    if notes:
        gate["notes"] = notes

    milestone_ids = [m.get("id") for m in plan.get("milestones") or []]
    name = gate_name
    note = ""
    if approving:
        if name == "plan":
            plan["status"] = "approved"
            note = "build status -> approved"
        elif name.startswith("milestone:"):
            mid = name.split(":", 1)[1]
            for milestone in plan.get("milestones") or []:
                if milestone.get("id") == mid:
                    milestone["status"] = "accepted"
            if milestone_ids and mid == milestone_ids[-1]:
                plan["status"] = "done"
                note = "last milestone accepted — build status -> done"
            else:
                plan["status"] = "building"
                note = "build status -> building"
    else:
        if name == "plan":
            # Contract section 3: "re-planning is a new plan version".
            # Archiving happens HERE, at the rejection — the rejected body is
            # frozen into history[] so the planner's re-plan cannot overwrite
            # it in place. The version bump happens at the RE-PLAN
            # (`set-plan` from status 'plan-rejected'), not here: a plan that
            # is rejected and then abandoned never gets a v2 that no agent
            # ever wrote.
            _archive_rejected_plan(plan, snapshot, at, by,
                                   notes or "plan gate rejected")
            plan["status"] = "plan-rejected"
            note = (f"build status -> plan-rejected (v{snapshot['version']} archived in "
                    f"history[]); the planner's next `set-plan` becomes "
                    f"v{int(snapshot['version']) + 1}")
        elif name.startswith("milestone:"):
            mid = name.split(":", 1)[1]
            for milestone in plan.get("milestones") or []:
                if milestone.get("id") == mid:
                    milestone["status"] = "rejected"
            plan["status"] = "building"
            note = (f"milestone {mid} -> rejected; build stays in 'building' — rework the "
                    f"milestone and re-request the gate")
        elif name == "clarifications":
            plan["status"] = "clarifying"
            note = "build status -> clarifying — ask the follow-up questions"

    # A rejection is a human's verdict ON an invalid plan; refusing to record
    # it because the plan is invalid would trap the build. Schema errors still
    # block — see write_plan().
    lenient = not approving and name in {"plan", "clarifications"}
    rc = write_plan(plan_path, plan, repo_root, schema,
                    allow_semantic_errors=lenient)  # schema was checked on read
    if rc:
        return rc
    print(f"gate {name}: {gate['status']} by {by} at {at}" + (f" — {note}" if note else ""))
    return 0


def cmd_gate(args: argparse.Namespace) -> int:
    plan_path = Path(args.plan)
    schema = load_schema(args.schema)
    repo_root = Path(args.repo_root)
    alias = args.gate

    if alias in GATE_ALIASES:
        # § 3.1: 'go' and 'accept' are shorthand for more than one real gate
        # name, legal only at scale 'ask'. One schema-checked read up front:
        # every member's precondition is checked against this SAME snapshot
        # before any of them is written. This is what makes the alias
        # atomic — without it, an early member (e.g. 'clarifications') could
        # be written to disk and only then would a later member (e.g.
        # 'plan', which requires build status 'verified') refuse, leaving a
        # half-applied alias on disk with no way to tell from the CLI's exit
        # code that only part of 'go' landed.
        # Absent `scale` is 'project' by contract (§ 3.1), so the message
        # names the plan's real effective tier rather than Python's `None`.
        plan = read_plan_on_schema(plan_path, schema)
        scale = plan.get("scale") or "project"
        if scale != "ask":
            _die(f"gate '{alias}' is legal only when scale is 'ask' (this plan's scale is "
                 f"{scale!r}) — § 3.1's go/accept aliases exist for a single-step ask build; "
                 f"use the real gate name(s) instead: "
                 f"{', '.join(GATE_ALIASES[alias])}")
        real_names = GATE_ALIASES[alias]
        for real_name in real_names:
            refusal, _notes = _gate_precondition(plan, real_name, args.decision)
            if refusal:
                _die(f"gate '{alias}' refused atomically — {refusal} — nothing was written "
                     f"(every member of '{alias}' is checked before any of them is written)")
        at = _now(args.at)  # one timestamp, shared by every record 'go'/'accept' writes
        for real_name in real_names:
            rc = _gate_once(plan_path, schema, repo_root, real_name, args.decision,
                            args.by, args.notes, at)
            if rc:
                return rc
        return 0

    return _gate_once(plan_path, schema, repo_root, alias, args.decision,
                      args.by, args.notes, _now(args.at))


def _ensure_gates(plan: dict) -> list[str]:
    """Add every missing required gate as pending, in lifecycle order."""
    existing = [g.get("name") for g in plan.get("human_gates") or []]
    gates = plan.setdefault("human_gates", [])
    added = []
    for name in required_gate_names(plan):
        if name not in existing:
            gates.append({"name": name, "status": "pending"})
            added.append(name)
    order = {name: i for i, name in enumerate(required_gate_names(plan))}
    gates.sort(key=lambda g: order.get(g.get("name"), len(order)))
    return added


def cmd_ensure_gates(args: argparse.Namespace) -> int:
    plan_path = Path(args.plan)
    plan = read_plan(plan_path)
    _ensure_skills_link(plan_path.parent, Path(args.repo_root))
    added = _ensure_gates(plan)
    gates = plan.get("human_gates") or []
    schema = load_schema(args.schema)
    rc = write_plan(plan_path, plan, Path(args.repo_root), schema)
    if rc:
        return rc
    print(f"gates: {len(gates)} present" + (f", added {', '.join(added)}" if added else
                                            ", nothing to add"))
    return 0


def cmd_check_outputs(args: argparse.Namespace) -> int:
    plan_path = Path(args.plan)
    plan = read_plan(plan_path)
    step = next((s for s in plan.get("steps") or [] if s.get("id") == args.step_id), None)
    if step is None:
        _die(f"no step {args.step_id!r} in {plan_path}")
    report = check_outputs(plan, step, plan_path.parent)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1


# --------------------------------------------------------------------------
# Structured writers — the agents' alternative to hand-editing plan.json
# --------------------------------------------------------------------------

def _read_json_file(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        _die(f"no such file: {path}")
    except json.JSONDecodeError as exc:
        _die(f"{path} is not valid JSON: {exc}")
    raise AssertionError("unreachable")


# Keys `set-plan` may replace. The planner owns exactly these; everything else
# in the plan belongs to another writer (gates to `gate`, statuses to
# `set-status`, verification to `set-verification`).
PLAN_KEYS = ("scope", "fit_gap", "assumptions", "decisions", "milestones", "steps")

# Statuses in which re-planning is refused: the plan has already been signed
# off or built against (contract section 3).
PLAN_FROZEN_STATUSES = {"verified", "approved", "building", "done"}


def cmd_set_plan(args: argparse.Namespace) -> int:
    plan_path = Path(args.plan)
    plan = read_plan(plan_path)
    doc = _read_json_file(Path(args.file))
    if not isinstance(doc, dict):
        _die(f"{args.file} must be a JSON object with any of: {', '.join(PLAN_KEYS)}")
    unknown = sorted(set(doc) - set(PLAN_KEYS))
    if unknown:
        _die(f"{args.file}: set-plan writes only {', '.join(PLAN_KEYS)} — refusing "
             f"{', '.join(unknown)} (gates, statuses and verification have their own writers)")
    status = plan.get("status")
    if status in PLAN_FROZEN_STATUSES:
        _die(f"refusing to replace the plan while the build status is '{status}' — re-planning "
             f"is allowed from intake/clarifying/planned/plan-rejected only (reject the plan "
             f"gate first if the human wants a new plan)")
    # § 3.1's worked example for scale 'ask' is answer -> planner -> verifier
    # -> `gate go` -> build: the planner runs while status is still
    # 'clarifying' and gate 'clarifications' is still 'pending' — 'go' signs
    # both G1 and G2 together only after the verifier passes the plan, so
    # there is no earlier point at which G1 gets approved on its own. That is
    # fine PROVIDED every blocking clarification already has an answer (or an
    # accepted DEFER) — the planner must never plan around a blocking
    # question nobody has answered yet just because the formal 'clarifications'
    # gate hasn't been signed. This check exists only at scale 'ask', where
    # planning-before-G1 is the documented flow; at 'feature'/'project' scale
    # today's rule stands unchanged (PLAN_FROZEN_STATUSES above is the only
    # gate `set-plan` applies there — planning ahead of gate 'clarifications'
    # being signed is a workflow matter for those scales, not one this script
    # enforces).
    if (plan.get("scale") or "project") == "ask" and status == "clarifying":
        still_open = [c.get("id") for c in plan.get("clarifications") or []
                      if c.get("kind") == "blocking" and c.get("status") == "open"]
        if still_open:
            _die(f"refusing to plan at scale 'ask' — blocking clarification(s) "
                 f"{', '.join(str(q) for q in still_open)} are still open — answer them (or "
                 f"defer with 'DEFER: <reason>' and `ingest-answers --allow-deferred`) before "
                 f"planning; § 3.1's ask flow lets the planner run before gate 'clarifications' "
                 f"is formally approved, but not before every blocking question has an answer")
    if "fit_gap" in doc:
        scope = dict(doc.get("scope") or plan.get("scope") or {"in": [], "out": [], "fit_gap": []})
        scope["fit_gap"] = doc.pop("fit_gap")
        doc["scope"] = scope
    for key, value in doc.items():
        plan[key] = value
    # Contract section 3: "re-planning is a new plan version". The rejection
    # already archived the superseded body into history[] (`gate plan reject`
    # or `set-verification --outcome plan-rejected`); this — the re-plan
    # itself — is the only place `version` moves. Re-planning from
    # intake/clarifying/planned is still the FIRST plan of that version, so it
    # leaves the number alone.
    replanned = status == "plan-rejected"
    if replanned:
        plan["version"] = int(plan.get("version") or 1) + 1
    plan["status"] = "planned"
    # A new body has not been verified; the previous round's verdict belongs
    # to the archived body in history[], not to this one (dry-run v4 W06).
    plan.pop("verification", None)
    summary = (getattr(args, "summary", None) or "").strip()
    if summary:
        # The planner is the second agent to restate the requirement, and the
        # first to have done the fit-gap: it can sharpen the clarifier's
        # paragraph (scope in, scope out, what the platform will not do). Same
        # single-writer rule as `set-clarifications --summary`; nothing else
        # may touch requirement.summary.
        plan["requirement"] = dict(plan.get("requirement") or {})
        plan["requirement"]["summary"] = summary
    added = _ensure_gates(plan)
    schema = load_schema(args.schema)
    rc = write_plan(plan_path, plan, Path(args.repo_root), schema)
    if rc:
        return rc
    print(f"plan written: {len(plan.get('milestones') or [])} milestone(s), "
          f"{len(plan.get('steps') or [])} step(s), status -> planned"
          + (f"; re-plan after rejection — plan version -> {plan['version']}"
             if replanned else "")
          + (f"; gates added: {', '.join(added)}" if added else "")
          + ("; requirement.summary updated" if summary else ""))
    print("next: `build_plan.py render` then hand the plan to the plan-verifier.")
    return 0


# Fields `amend-step` may replace on one step. Deliberately a subset of the
# step object: `id`, `milestone`, `type`, `agent`, `status`, `depends_on`,
# `runs`, `human_gate` and `blocked_reason` stay off-limits — those are
# structural (id/milestone/type/agent), owned by another writer (`status` and
# `runs` by `set-status`, `blocked_reason` alongside it), or would let an
# amendment silently rewire the DAG (`depends_on`) or the gate a human already
# saw (`human_gate`). Only the declarative content a runner/tester actually
# reads is amendable.
AMENDABLE_STEP_FIELDS = (
    "inputs", "outputs", "acceptance_tests", "skills", "templates",
    "decision_trees", "notes", "title",
)

# Build statuses `amend-step` accepts. Contract § 3: a plan not yet approved is
# still a draft and is corrected with `set-plan`; one that is `verified` is
# corrected the same way (re-planning discards no gate yet); `done` has no
# pending steps left to correct. `building` and `approved` are the window
# where steps exist, some are still `pending`/`blocked`, and `set-plan` is
# refused (`PLAN_FROZEN_STATUSES`) because rewriting the whole plan would
# discard recorded gates — that is exactly the gap `amend-step` fills.
AMEND_STEP_PLAN_STATUSES = {"building", "approved"}

# Step statuses `amend-step` accepts: the step has not started running yet
# (contract § 4's `pending`), or was parked without having run
# (`blocked`). Anything from `running` on has already produced runs, artefacts
# or test results an amendment would silently orphan.
AMEND_STEP_STATUSES = {"pending", "blocked"}

# Fields `--prose-only` may touch: text that *describes* a test, never what
# the test runs. A subset of AMENDABLE_STEP_FIELDS.
PROSE_ONLY_FIELDS = ("notes", "acceptance_tests")

# acceptanceTest keys that change what the test DOES, not how it reads.
# `--prose-only` refuses any amendment that changes one of these; only
# `description` may differ between the current and amended test at the same
# index.
_ACCEPTANCE_TEST_STRUCTURAL_FIELDS = ("type", "command", "expected", "scope")


def _prose_only_violation(current_tests: list, new_tests: list) -> str | None:
    """None if new_tests differs from current_tests only in `description`.

    Otherwise a human-readable reason `--prose-only` must refuse the write.
    """
    if len(new_tests) != len(current_tests):
        return (f"acceptance_tests has {len(new_tests)} entr{'y' if len(new_tests) == 1 else 'ies'} "
                f"but the step currently has {len(current_tests)} — --prose-only may reword "
                f"existing test descriptions, not add or remove tests")
    for i, (old, new) in enumerate(zip(current_tests, new_tests)):
        if not isinstance(new, dict):
            return f"acceptance_tests[{i}] must be an object"
        for field in _ACCEPTANCE_TEST_STRUCTURAL_FIELDS:
            old_val = old.get(field)
            new_val = new.get(field)
            if old_val != new_val:
                return (f"acceptance_tests[{i}].{field} differs ({old_val!r} -> {new_val!r}) — "
                        f"--prose-only may change only `description`; drop --prose-only if this "
                        f"field genuinely needs to change")
    return None


def cmd_amend_step(args: argparse.Namespace) -> int:
    plan_path = Path(args.plan)
    schema = load_schema(args.schema)
    plan = read_plan_on_schema(plan_path, schema)
    prose_only = bool(getattr(args, "prose_only", False))

    status = plan.get("status")
    if status not in AMEND_STEP_PLAN_STATUSES:
        _die(f"refusing to amend a step while the build status is '{status}' — amend-step only "
             f"corrects a pending/blocked step's declared fields mid-build (status 'building' or "
             f"'approved'); a '{status}' plan has no in-flight steps to correct this way — "
             f"re-plan it with `set-plan` instead")

    step = next((s for s in plan.get("steps") or [] if s.get("id") == args.step_id), None)
    if step is None:
        _die(f"no step {args.step_id!r} in {plan_path}")

    step_status = step.get("status")
    if prose_only:
        # Prose does not change what ran — only what a human reads about it —
        # so every status is fair game except mid-run, where the step object
        # itself may still be mutating.
        if step_status == "running":
            _die(f"{args.step_id} is 'running' — --prose-only cannot correct a step while it is "
                 f"mid-run; wait for it to reach a resting status (documented/tested/built/"
                 f"failed/blocked/pending), then reword its test descriptions")
    elif step_status not in AMEND_STEP_STATUSES:
        if step_status == "documented":
            _die(f"{args.step_id} is 'documented' — amend-step only corrects a step that has not "
                 f"run yet; rebuild it first (`build_plan.py set-status {args.plan} "
                 f"{args.step_id} running` — contract § 8's documented -> running rebuild path), "
                 f"then amend the re-opened step (or pass --prose-only if you are only "
                 f"correcting a test's `description`/`notes` text)")
        if step_status == "failed":
            _die(f"{args.step_id} is 'failed' — reset it first (`build_plan.py set-status "
                 f"{args.plan} {args.step_id} pending`), then amend it (or pass --prose-only if "
                 f"you are only correcting a test's `description`/`notes` text)")
        _die(f"{args.step_id} is '{step_status}' — amend-step only corrects a step that has not "
             f"started running yet (status 'pending' or 'blocked'), unless --prose-only is "
             f"passed to reword a test's `description`/`notes` text")

    gate_name = f"step:{args.step_id}"
    gate_already_approved = gate_status(plan, gate_name) == "approved"
    if gate_already_approved and not prose_only:
        _die(f"gate '{gate_name}' is already approved — amending {args.step_id} would "
             f"invalidate what the human signed off; reject it first (`build_plan.py gate "
             f"{args.plan} {gate_name} reject --by <who>`), then amend {args.step_id} "
             f"(or pass --prose-only: prose does not invalidate a signature, so an approved "
             f"gate does not block it)")

    doc = _read_json_file(Path(args.file))
    if not isinstance(doc, dict):
        allowed = PROSE_ONLY_FIELDS if prose_only else AMENDABLE_STEP_FIELDS
        _die(f"{args.file} must be a JSON object with any of: {', '.join(allowed)}")

    if prose_only:
        unknown = sorted(set(doc) - set(PROSE_ONLY_FIELDS))
        if unknown:
            _die(f"{args.file}: --prose-only writes only {', '.join(PROSE_ONLY_FIELDS)} — "
                 f"refusing {', '.join(unknown)} (a prose-only amendment may reword text, not "
                 f"change a structural field; drop --prose-only to amend {', '.join(unknown)})")
        if not doc:
            _die(f"{args.file} names neither of {', '.join(PROSE_ONLY_FIELDS)} — nothing to amend")
        if "notes" in doc and not isinstance(doc["notes"], str):
            _die(f"{args.file}: notes must be a string under --prose-only")
        if "acceptance_tests" in doc:
            new_tests = doc["acceptance_tests"]
            if not isinstance(new_tests, list):
                _die(f"{args.file}: acceptance_tests must be an array under --prose-only")
            current_tests = step.get("acceptance_tests") or []
            violation = _prose_only_violation(current_tests, new_tests)
            if violation:
                _die(f"{args.file}: {violation}")
    else:
        unknown = sorted(set(doc) - set(AMENDABLE_STEP_FIELDS))
        if unknown:
            _die(f"{args.file}: amend-step writes only {', '.join(AMENDABLE_STEP_FIELDS)} — "
                 f"refusing {', '.join(unknown)} (id/milestone/type/agent are structural; "
                 f"status/runs/blocked_reason belong to set-status; depends_on and human_gate "
                 f"are not amendable)")
        if not doc:
            _die(f"{args.file} names none of the amendable fields "
                 f"({', '.join(AMENDABLE_STEP_FIELDS)}) — nothing to amend")

    before = {field: copy.deepcopy(step[field]) for field in doc if field in step}
    for field, value in doc.items():
        step[field] = value
    fields = sorted(doc)
    amendment_record = {
        "at": _now(args.at),
        "by": args.by,
        "reason": args.reason,
        "fields": fields,
        "before": before,
    }
    if prose_only:
        amendment_record["prose_only"] = True
    step.setdefault("amendments", []).append(amendment_record)

    # Mirrors write_plan()'s validate-then-atomic-write, but the printed
    # warnings are scoped to this step: a plan-wide WARN dump on every
    # amendment would bury the one line the human who typed --reason needs.
    # ERRORs still block on the WHOLE plan — an amendment that leaves some
    # other step's declaration invalid is not this step's business, but it is
    # still a plan the layer must refuse to write (contract § 8: "the plan
    # must stay valid").
    hard = schema_errors(plan, schema, schema)
    if hard:
        print(f"refusing to write {plan_path} — the result would be off-schema:", file=sys.stderr)
        for msg in hard:
            print(f"  ERROR {msg}", file=sys.stderr)
        return 1
    issues = semantic_issues(plan, Path(args.repo_root))
    errors = [msg for level, msg in issues if level == "ERROR"]
    if errors:
        print(f"refusing to amend {args.step_id} — the plan would become invalid:",
              file=sys.stderr)
        for msg in errors:
            print(f"  ERROR {msg}", file=sys.stderr)
        return 1
    step_warnings = [msg for level, msg in issues if level == "WARN" and args.step_id in msg]
    for msg in step_warnings:
        print(f"WARN {msg}")
    _atomic_write(plan_path, plan_json(plan))
    gate_note = (f" (gate '{gate_name}' stays approved — prose does not invalidate a signature)"
                 if prose_only and gate_already_approved else "")
    print(f"step {args.step_id}: amended {', '.join(fields)} by {args.by}"
          f"{' (prose-only)' if prose_only else ''} — "
          f"{len(step_warnings)} warning(s){gate_note}")
    print("next: `build_plan.py render`")
    return 0


# Statuses `set-scale` accepts. Contract § 3.1: the tier is chosen at `init`
# or by the clarifier's first pass, before `set-plan` has written a body
# (scope/milestones/steps) on top of it — 'planned' onward, re-tiering is a
# re-plan (reject the plan gate, then `set-plan` from 'plan-rejected'), not a
# scale change, so this writer refuses everywhere else, naming the status.
SET_SCALE_STATUSES = {"intake", "clarifying"}


def cmd_set_scale(args: argparse.Namespace) -> int:
    plan_path = Path(args.plan)
    plan = read_plan(plan_path)
    status = plan.get("status")
    if status not in SET_SCALE_STATUSES:
        _die(f"refusing to set scale while the build status is '{status}' — scale may be "
             f"recorded only while status is 'intake' or 'clarifying', before `set-plan` has "
             f"written a body; re-tiering a planned build is a re-plan (reject the plan gate, "
             f"then re-run `set-plan`), not a scale change")
    current = plan.get("scale")
    if current and current != args.scale and not args.force:
        _die(f"plan already has scale {current!r} -> {args.scale!r} — refusing to change it "
             f"without --force")
    old = current
    plan["scale"] = args.scale
    schema = load_schema(args.schema)
    rc = write_plan(plan_path, plan, Path(args.repo_root), schema)
    if rc:
        return rc
    if old and old != args.scale:
        print(f"scale: {old} -> {args.scale} (set by {args.by})")
    else:
        print(f"scale: {args.scale} (set by {args.by})")
    print(f"next: `build_plan.py set-clarifications {plan_path} --file <file>`.")
    return 0


def cmd_set_clarifications(args: argparse.Namespace) -> int:
    plan_path = Path(args.plan)
    plan = read_plan(plan_path)
    doc = _read_json_file(Path(args.file))
    if isinstance(doc, dict) and "clarifications" in doc:
        doc = doc["clarifications"]
    if not isinstance(doc, list):
        _die(f"{args.file} must be a JSON array of clarification objects (or an object with a "
             f"'clarifications' array)")
    plan["clarifications"] = doc
    plan["status"] = "clarifying"
    summary = (getattr(args, "summary", None) or "").strip()
    if summary:
        # `init` can only take the requirement's first prose line, truncated at
        # 400 chars. The clarifier is the first agent that has actually read the
        # requirement, so this is where the schema's "one-paragraph restatement"
        # gets written — and until now nothing could write it without a hand
        # edit of plan.json, which section 2 forbids.
        plan["requirement"] = dict(plan.get("requirement") or {})
        plan["requirement"]["summary"] = summary

    # § 3.1: at `scale: ask` the informational rows are never put to the human
    # in a round — they "land pre-filled from their proposed_default with
    # default_source set" (contract, § 3.1). This is the writer, so it is the
    # one place that guarantee holds regardless of what the clarifier passed
    # in. A blocking row is never touched here — it always waits for a human
    # or an explicit `DEFER:`. Only `open` rows with nothing already answered
    # are filled, so re-running set-clarifications never clobbers a human's
    # (or a later ingest-answers') edit.
    defaults_filled = 0
    if plan.get("scale") == "ask":
        for clar in doc:
            if not isinstance(clar, dict):
                continue
            if clar.get("kind") != "informational":
                continue
            if clar.get("status") not in (None, "open"):
                continue
            if (clar.get("answer") or "").strip():
                continue
            default = (clar.get("proposed_default") or "").strip()
            if not default:
                continue
            clar["answer"] = default
            clar["status"] = "answered"
            if not (clar.get("default_source") or "").strip():
                clar["default_source"] = "proposed_default (scale: ask)"
            defaults_filled += 1

    schema = load_schema(args.schema)
    rc = write_plan(plan_path, plan, Path(args.repo_root), schema)
    if rc:
        return rc
    blocking = sum(1 for c in doc if isinstance(c, dict) and c.get("kind") == "blocking")
    print(f"clarifications written: {len(doc)} question(s), {blocking} blocking; "
          f"status -> clarifying" + ("; requirement.summary updated" if summary else "")
          + (f"; {defaults_filled} informational default(s) applied (scale: ask)"
             if defaults_filled else ""))
    print("next: `build_plan.py render`, then the human answers CLARIFICATIONS.md.")
    return 0


def cmd_set_verification(args: argparse.Namespace) -> int:
    plan_path = Path(args.plan)
    plan = read_plan(plan_path)
    if plan.get("status") in {"approved", "building", "done"}:
        _die(f"refusing to re-verify a plan whose build status is '{plan.get('status')}' — "
             f"the human has already signed it off at G2")
    doc = _read_json_file(Path(args.file))
    if not isinstance(doc, dict):
        _die(f"{args.file} must be a JSON object (lenses[], blockers[], notes)")
    verification = dict(doc)
    verification["status"] = args.outcome
    if args.by:
        verification["by"] = args.by
    verification.setdefault("verified_at", _now(args.at))
    archived = None
    if args.outcome == "plan-rejected":
        # Contract § 3. This is the second route to plan-rejected (the first is
        # `gate plan reject`); both archive the rejected body so the planner's
        # re-plan never overwrites v<n> in place, and neither bumps `version`
        # — `set-plan` does that when the re-plan actually arrives.
        snapshot = copy.deepcopy(plan)
        snapshot.pop("history", None)
        # The archived body carries the verdict that rejected IT, not the one
        # it inherited from the previous round (dry-run v4 finding W06).
        snapshot["verification"] = verification
        archived = _archive_rejected_plan(
            plan, snapshot, verification["verified_at"], args.by or "plan-verifier",
            "plan-verifier outcome plan-rejected")
    plan["verification"] = verification
    plan["status"] = args.outcome
    schema = load_schema(args.schema)
    rc = write_plan(plan_path, plan, Path(args.repo_root), schema)
    if rc:
        return rc
    lenses = ", ".join(f"{l.get('lens')}={l.get('verdict')}"
                       for l in verification.get("lenses") or []) or "no lenses recorded"
    tail = (f" (v{archived} archived in history[]; the planner's next `set-plan` "
            f"becomes v{archived + 1})") if archived else ""
    print(f"verification written ({lenses}); build status -> {args.outcome}{tail}")
    return 0


def cmd_set_milestone(args: argparse.Namespace) -> int:
    plan_path = Path(args.plan)
    plan = read_plan(plan_path)
    milestone = next((m for m in plan.get("milestones") or []
                      if m.get("id") == args.milestone), None)
    if milestone is None:
        _die(f"no milestone {args.milestone!r} in {plan_path}")
    report = plan_path.parent / args.report_path
    if not report.is_file():
        print(f"WARN report {args.report_path} does not exist under {plan_path.parent} — "
              f"the milestone verifier writes MILESTONE-<id>-REPORT.md before recording it")
    # F-12 (dry-run v2 report): an 'accepted' milestone is the human's G3 record.
    # A re-verification records its report but never moves the status away from
    # accepted; only `gate milestone:<id> reject` undoes a human's approval.
    if milestone.get("status") == "accepted" and args.status != "accepted":
        milestone["report_path"] = args.report_path
        milestone.setdefault("reverifications", []).append(
            {"at": _now(getattr(args, "at", None)), "verdict": args.status, "report_path": args.report_path})
        schema = load_schema(args.schema)
        rc = write_plan(plan_path, plan, Path(args.repo_root), schema)
        if rc:
            return rc
        print(f"milestone {args.milestone}: status stays 'accepted' (human gate on record); "
              f"re-verification '{args.status}' recorded with report -> {args.report_path}. "
              f"To withdraw the approval: `build_plan.py gate {plan_path} milestone:{args.milestone} reject --by <who>`")
        return 0
    milestone["status"] = args.status
    milestone["report_path"] = args.report_path
    schema = load_schema(args.schema)
    rc = write_plan(plan_path, plan, Path(args.repo_root), schema)
    if rc:
        return rc
    print(f"milestone {args.milestone}: status -> {args.status}, report -> {args.report_path}")
    if args.status == "verified":
        print(f"next: the human decides — `build_plan.py gate {plan_path} "
              f"milestone:{args.milestone} approve --by <who>`")
    return 0


# Never worth exporting: the atomic-write temp files this script leaves behind
# if a process dies mid-write, and editor/interpreter droppings.
_EXPORT_IGNORE_PATTERNS = shutil.ignore_patterns(".*.tmp*", "__pycache__", "*.pyc", ".DS_Store")


def EXPORT_IGNORE(directory: str, names: list[str]) -> set[str]:
    """Never export the build directory's `skills` symlink (contract section 5):
    it points back into the repo, and copying through it would drag every skill
    package into the example (7,608 files in the first dry-run export)."""
    ignored = set(_EXPORT_IGNORE_PATTERNS(directory, names))
    for name in names:
        if name == "skills" and os.path.islink(os.path.join(directory, name)):
            ignored.add(name)
    return ignored


def cmd_export(args: argparse.Namespace) -> int:
    """Copy a whole build directory out of gitignored .sfskills/ (contract § 9).

    A build lives under `.sfskills/builds/<id>/`, which is not committed. The
    committed example under `examples/builds/` has to be *produced by the loop*,
    not written by hand — so there has to be one command that moves a finished
    build across, and it must refuse to move a build that does not validate.
    """
    plan_path = Path(args.plan)
    plan = read_plan(plan_path)
    build_dir = plan_path.parent.resolve()
    dest = Path(args.dest).resolve()

    schema = load_schema(args.schema)
    issues = validate_plan(plan, Path(args.repo_root), schema)
    for level, msg in issues:
        if level == "WARN":
            print(f"WARN {msg}")
    errors = [msg for level, msg in issues if level == "ERROR"]
    if errors:
        for msg in errors:
            print(f"ERROR {msg}", file=sys.stderr)
        print(f"refusing to export {build_dir.name}: {len(errors)} validation error(s) — "
              f"an exported build is an example other builds are copied from.", file=sys.stderr)
        return 1

    if dest == build_dir or build_dir in dest.parents:
        _die(f"destination {dest} is the build directory or lives inside it")
    if dest.exists():
        if not args.force:
            _die(f"{dest} already exists — pass --force to replace it")
        if not dest.is_dir():
            _die(f"{dest} exists and is not a directory")
        # Replace, don't merge: a merged export silently keeps files the build
        # no longer produces, and the export would then not be the build.
        shutil.rmtree(dest)

    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(build_dir, dest, ignore=EXPORT_IGNORE, symlinks=True)
    files = sorted(path for path in dest.rglob("*") if path.is_file())
    print(f"exported {build_dir} -> {dest}")
    print(f"  {len(files)} file(s)")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    plan = read_plan(Path(args.plan))
    steps = plan.get("steps") or []
    print(f"{plan['title']}  [{plan['build_id']}]")
    print(f"status: {plan['status']}  ·  plan version: {plan['version']}  ·  "
          f"created: {plan['created']}")
    mode = plan.get("build_mode", "design-only")
    alias = (plan.get("org") or {}).get("alias")
    scale = plan.get("scale")
    # § 3.1: absent `scale` means 'project' by contract, so the effective tier
    # is printed either way. The contract also asks for '(override)' here when
    # a human set `scale`, but the schema is `additionalProperties: false` —
    # there is no field this command could read that field back from, so no
    # on-disk signal distinguishes a human's `init --scale` from the
    # clarifier's own first pass. That distinction is recorded only in the
    # transient `init` summary line (see cmd_init); it is not printed here.
    scale_cell = scale or "project (default — no scale recorded)"
    print(f"build mode: {mode}  ·  scale: {scale_cell}"
          + (f"  ·  org alias: {alias}" if alias else ""))
    print(f"steps: {len(steps)}  ·  milestones: {len(plan.get('milestones') or [])}")
    print("")
    order = ["pending", "running", "built", "tested", "documented", "failed", "blocked"]
    print("milestone   " + "  ".join(f"{s[:4]:>5}" for s in order) + "   gate")
    for milestone in plan.get("milestones") or []:
        mid = milestone.get("id")
        mine = [s for s in steps if s.get("milestone") == mid]
        counts = [sum(1 for s in mine if s.get("status") == st) for st in order]
        print(f"{mid:<11} " + "  ".join(f"{c:>5}" for c in counts)
              + f"   {gate_status(plan, f'milestone:{mid}')}")
    print("")
    print("gates:")
    for gate in plan.get("human_gates") or []:
        line = f"  {gate.get('name'):<18} {gate.get('status')}"
        if gate.get("by"):
            line += f"  by {gate['by']}"
        if gate.get("at"):
            line += f" at {gate['at']}"
        print(line)
    blockers = [s for s in steps if s.get("status") in {"blocked", "failed"}]
    open_blocking = [c for c in plan.get("clarifications") or []
                     if c.get("kind") == "blocking" and c.get("status") == "open"]
    print("")
    print("blockers:")
    if not blockers and not open_blocking:
        print("  none")
    for step in blockers:
        print(f"  {step.get('id')} [{step.get('status')}] "
              f"{step.get('blocked_reason') or step.get('title')}")
    for clar in open_blocking:
        print(f"  {clar.get('id')} [blocking question unanswered] {clar.get('question')}")
    return 0


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

EPILOG = """\
The plan file is the only shared state (standards/build-orchestration.md § 2).
This script renders every human-readable view from it and is the ONLY writer of
human gate records. Never hand-edit PLAN.md or CLARIFICATIONS.md.

Walkthrough:

  1. init                create .sfskills/builds/<id>/ + plan.json (status: intake).
                         Design-only unless --org-alias is given.
  1a. set-scale          record/change the § 3.1 ceremony tier (ask|feature|project)
                         while status is intake/clarifying — for a build `init` already
                         created without --scale; refused once `set-plan` has run.
  2. set-clarifications  the clarifier's questions (status → clarifying)
  3. render              (re)write PLAN.md + CLARIFICATIONS.md from plan.json
  4. ingest-answers      read the human's 'Answer:' lines back into plan.json
                         (an answer may span several lines)
  5. gate clarifications approve --by <who>      G1 — refused while a blocking
                         question is still open
  6. set-plan            the planner's scope, fit_gap, assumptions, decisions,
                         milestones and steps (status → planned). --summary also
                         sharpens requirement.summary now the fit-gap is done.
  7. validate            schema + contract checks (agents, skills, DAG, tests, gates)
  8. set-verification    the verifier's lenses (status → verified | plan-rejected)
  9. gate plan approve --by <who>                G2 — refused unless status is
                         'verified'; sets build status 'approved'
 10. next                JSON list of steps runnable right now (gates + depends_on)
 11. set-status          pending → running → built → tested → documented
                         ('built' needs the outputs on disk; 'tested' needs a
                         passing tests/<step>/results.json)
 12. check-outputs       do this step's declared outputs[] exist, non-empty, parseable?
 11a. amend-step         correct a pending/blocked step's declared fields mid-build
                         (inputs/outputs/acceptance_tests/skills/templates/decision_trees/
                         notes/title) without a re-plan; refused once the step has a run,
                         or its own step:<id> gate is approved
 13. set-milestone       the milestone verifier's verdict + report path
 14. gate milestone:M1 approve --by <who>        G3 — refused until every step is
                         documented (or blocked with a reason); last milestone → 'done'
 15. status              one-screen summary: step counts per milestone, gates, blockers
 16. export              copy the finished build out of gitignored .sfskills/ into a
                         committable directory (validate must pass first)

Every mutating subcommand re-validates the resulting document and writes it
atomically; if validation fails the file on disk is left exactly as it was and
the exit code is 1. WARN lines never fail a command; ERROR lines always do. The
one exception is `gate plan|clarifications reject`, which records a human's
rejection of an invalid plan (schema errors still block).

Plan versions (§ 3, "re-planning is a new plan version") have two halves, and
they happen at different moments. A rejection — `gate plan reject` or
`set-verification --outcome plan-rejected` — ARCHIVES the rejected body into
history[] and leaves `version` alone. The RE-PLAN — `set-plan` while the status
is 'plan-rejected' — increments `version`. So a plan rejected and then
abandoned never leaves behind a version no planner wrote, and a plan rejected
by the verifier and then by the human is still one re-plan, not two.

No agent hand-edits plan.json. Every field has a writer here.
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="build_plan.py",
        description="Read, validate, render and advance a build plan "
                    "(.sfskills/builds/<id>/plan.json).",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--repo-root", default=str(ROOT),
                        help="repo root used to resolve agents/, skills/, templates/ and "
                             "standards/ citations (default: this checkout)")
    common.add_argument("--schema", default=None,
                        help="override the build-plan JSON Schema path")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", parents=[common], help="create a build directory + minimal plan",
                       description="Create the § 2 build directory layout, copy the requirement "
                                   "in verbatim, and write a minimal valid plan.json "
                                   "(status: intake, version: 1, build_mode: design-only).")
    p.add_argument("--build-dir", required=True, help="e.g. .sfskills/builds/case-onboarding")
    p.add_argument("--title", required=True, help="one-line human title for the build")
    p.add_argument("--requirement", required=True,
                   help="path to the human's requirement markdown. `--force` re-initialising a "
                        "build in place may point this at the build's own requirement.md "
                        "(the file a prior `init` already wrote there) — that is a no-op, not "
                        "an error.")
    p.add_argument("--build-id", default=None, help="kebab-case id (default: build dir name)")
    p.add_argument("--org-alias", default=None,
                   help="sf CLI alias of the org this build may read. Sets build_mode to "
                        "'org-connected' and stores org.alias, which is what lets a step be "
                        "owned by an agent with requires_org: true. Omit for a design-only "
                        "build (the default): every step must then be owned by an org-free "
                        "agent such as metadata-builder. The layer still never deploys.")
    p.add_argument("--now", default=None, help="ISO timestamp for 'created' (default: UTC now)")
    p.add_argument("--force", action="store_true", help="overwrite an existing plan.json")
    p.add_argument("--scale", default=None, choices=SCALES,
                   help="§ 3.1: how much ceremony this build spends — 'ask' (1 milestone, 1 "
                        "step, two gates), 'feature' (1 milestone, ≤ 5 steps) or 'project' (the "
                        "full § 3-5 pass). Optional; omit and the requirements-clarifier's "
                        "printed sizing rule sets it on its first pass. Passing it here IS a "
                        "human override, echoed on the 'scale:' summary line below.")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("validate", parents=[common], help="schema + contract validation",
                       description="Validate a plan against the schema and the contract: real "
                                   "runtime agents eligible for this build_mode (an agent with "
                                   "requires_org: true may not own a step in a design-only "
                                   "build), resolvable skills/templates/trees, known step types, "
                                   "an acyclic depends_on graph, acceptance tests that are "
                                   "runnable and on the allow-list (no deploy, fetch or shell), "
                                   "milestone membership and ordering, and the required human "
                                   "gates (including step:<id> for every human-gated step). "
                                   "§ 3.1: a `scale` that disagrees with the plan's shape (e.g. "
                                   "'ask' with more than 1 milestone/step, 'feature' with more "
                                   "than 5 steps) is a WARN, never an ERROR — it names the "
                                   "sizing rule and never blocks. Exit 1 on any ERROR.")
    p.add_argument("plan", help="path to plan.json")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("render", parents=[common], help="write PLAN.md + CLARIFICATIONS.md",
                       description="Render the human-readable views from plan.json. Output is "
                                   "byte-deterministic: nothing but plan.json content reaches it. "
                                   "§ 3.1: also writes RUN.md at the build root when scale is "
                                   "'ask'.")
    p.add_argument("plan", help="path to plan.json")
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("ingest-answers", parents=[common],
                       help="parse CLARIFICATIONS.md 'Answer:' lines back into plan.json",
                       description="Round-trip the human's answers. An answer may span several "
                                   "lines: everything after 'Answer:' up to the next heading or "
                                   "a '---' rule belongs to it. Refuses when a blocking question "
                                   "is left with an empty Answer: line, including when that "
                                   "blanks an answer given earlier — withdraw an answer with "
                                   "'DEFER: <reason>', which is accepted only with "
                                   "--allow-deferred.")
    p.add_argument("plan", help="path to plan.json")
    p.add_argument("--allow-deferred", action="store_true",
                   help="accept 'DEFER: <reason>' answers on blocking questions")
    p.set_defaults(func=cmd_ingest_answers)

    p = sub.add_parser("next", parents=[common], help="JSON list of runnable steps",
                       description="Print the steps that may run right now: pending steps in the "
                                   "current milestone whose depends_on are all documented and "
                                   "whose own step:<id> gate is approved if they carry "
                                   "human_gate: true. The current milestone is the first one not "
                                   "fully documented, skipping any milestone whose only "
                                   "undocumented step(s) are 'blocked' once its own "
                                   "milestone:<id> gate is approved (that milestone is done "
                                   "being actionable, not next); it runs only if its "
                                   "predecessor gate is approved. Prints [] on stdout and the "
                                   "reason on stderr when blocked or skipped.")
    p.add_argument("plan", help="path to plan.json")
    p.add_argument("--milestone", default=None, help="force a milestone id, e.g. M2")
    p.set_defaults(func=cmd_next)

    p = sub.add_parser("set-status", parents=[common], help="advance one step's status",
                       description="Move a step along the § 4 state machine "
                                   "(pending → running → built → tested → documented; failed and "
                                   "blocked are side exits; documented → running re-runs a step; "
                                   "failed → pending resets one for a clean retry; running → "
                                   "running re-claims one on resume). 'running' is refused while "
                                   "the milestone's gates or the step's own step:<id> gate are "
                                   "unapproved; 'built' is refused unless check-outputs passes; "
                                   "'tested' additionally needs tests/<step-id>/results.json with "
                                   "\"passed\": true. Illegal transitions exit 1 and change "
                                   "nothing.")
    p.add_argument("plan", help="path to plan.json")
    p.add_argument("step_id", metavar="step-id", help="e.g. M1-S01")
    p.add_argument("status", choices=sorted(ALLOWED_TRANSITIONS))
    p.add_argument("--run-agent", default=None,
                   help="agent id to append to runs[] (default: the step's own agent)")
    p.add_argument("--envelope", default=None,
                   help="envelope path for the appended run "
                        "(default: envelopes/<step-id>/<status>.json)")
    p.add_argument("--result", default=None, help="run result text (default: the new status)")
    p.add_argument("--started", default=None,
                   help="ISO start time (default: UTC now). Any of --run-agent/--envelope/"
                        "--started appends a run entry; the other two take their defaults.")
    p.add_argument("--blocked-reason", default=None,
                   help="required with status 'blocked'; 'skill-gap' is the reserved value")
    p.set_defaults(func=cmd_set_status)

    p = sub.add_parser("gate", parents=[common], help="record a human gate decision",
                       description="The ONLY writer of human_gates[]. Approval is refused where "
                                   "the claim is not yet true: 'clarifications' while a blocking "
                                   "question is open; 'plan' unless the build status is "
                                   "'verified'; 'milestone:Mk' unless the plan gate and "
                                   "milestone:M(k-1) are approved and every step in Mk is "
                                   "documented or blocked with a recorded reason. Approving "
                                   "'plan' sets the build status to approved; approving the last "
                                   "'milestone:<id>' sets it to done; rejecting 'milestone:<id>' "
                                   "marks that milestone rejected and leaves the build building; "
                                   "rejecting 'plan' archives the rejected body in history[] "
                                   "and sets the build status to plan-rejected — the version "
                                   "number moves at the re-plan, when `set-plan` runs. § 3.1: "
                                   "'go' and 'accept' are aliases legal only when the plan's "
                                   "scale is 'ask' — 'go' writes the 'clarifications' and 'plan' "
                                   "records in this one invocation, under the same --by/--at/"
                                   "--notes. Atomic: every member's precondition (clarifications "
                                   "first, then plan) is checked against one snapshot before any "
                                   "of them is written — if either would refuse, NOTHING is "
                                   "written and the error names the failing record; 'plan' is "
                                   "legal only once the build status is 'verified', which at "
                                   "scale 'ask' the planner reaches without a prior G1 approval "
                                   "(the human's answers to the blocking clarifications ARE G1 "
                                   "in substance — 'go' signs the paperwork for both once the "
                                   "verifier has passed the plan). 'accept' writes "
                                   "'milestone:M1'. The stored gate names are unchanged; using "
                                   "either alias on a non-'ask' plan is an error naming the "
                                   "plan's actual scale.")
    p.add_argument("plan", help="path to plan.json")
    p.add_argument("gate", help="clarifications | plan | milestone:M1 | step:M1-S01 | "
                                "go | accept (go/accept: scale 'ask' only, see description)")
    p.add_argument("decision", choices=["approve", "reject"])
    p.add_argument("--by", required=True, help="the human who decided")
    p.add_argument("--notes", default=None)
    p.add_argument("--at", default=None, help="ISO timestamp (default: UTC now)")
    p.set_defaults(func=cmd_gate)

    p = sub.add_parser("export", parents=[common],
                       help="copy a validated build directory somewhere committable",
                       description="Copy the whole build directory — plan.json, the rendered "
                                   "views, requirement.md, decisions.md, traceability.md and "
                                   "the artefacts/, tests/, envelopes/, reports/ and workbook/ "
                                   "trees — into <dest-dir>. Runs `validate` first and refuses "
                                   "to export a plan with any ERROR. Refuses an existing "
                                   "destination unless --force, which replaces it outright "
                                   "(a merge would keep files the build no longer produces). "
                                   "This is how a build under gitignored .sfskills/ becomes a "
                                   "committed example such as examples/builds/case-onboarding "
                                   "(contract § 9). Prints the file count.")
    p.add_argument("plan", help="path to plan.json")
    p.add_argument("dest", metavar="dest-dir", help="e.g. examples/builds/case-onboarding")
    p.add_argument("--force", action="store_true",
                   help="replace dest-dir if it already exists")
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("status", parents=[common], help="one-screen build summary",
                       description="One-screen summary: step counts per milestone, gates, "
                                   "blockers. § 3.1: the build-mode line also prints "
                                   "'scale: <tier>' (absent scale reads as 'project', its "
                                   "contract default).")
    p.add_argument("plan", help="path to plan.json")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("ensure-gates", parents=[common],
                       help="add missing gate records as pending",
                       description="Add 'clarifications', 'plan', one 'milestone:<id>' gate per "
                                   "milestone and one 'step:<step-id>' gate per step carrying "
                                   "human_gate: true, each as pending, then sort them into "
                                   "lifecycle order. Never changes an existing gate. § 3.1: at "
                                   "scale 'ask' this adds 'milestone:M1' and no 'step:' record "
                                   "at all — the single step is expected human_gate: false, and "
                                   "even when it is true no step gate is added (validate WARNs "
                                   "instead).")
    p.add_argument("plan", help="path to plan.json")
    p.set_defaults(func=cmd_ensure_gates)

    p = sub.add_parser("check-outputs", parents=[common],
                       help="are a step's declared outputs actually on disk?",
                       description="Check every path in the step's outputs[]: it must exist "
                                   "under the build directory, be non-empty, and — for .xml — "
                                   "parse. Prints {ok, step, missing[], empty[], malformed[]} as "
                                   "JSON and exits 1 when not ok. `set-status <step> built` runs "
                                   "the same check, so a runner that wrote nothing cannot "
                                   "advance. A step that declares no outputs has nothing to "
                                   "check and is ok (validate WARNs about it separately).")
    p.add_argument("plan", help="path to plan.json")
    p.add_argument("step_id", metavar="step-id", help="e.g. M1-S01")
    p.set_defaults(func=cmd_check_outputs)

    p = sub.add_parser("set-scale", parents=[common],
                       help="record the § 3.1 ceremony tier before a plan body exists",
                       description="Write plan.scale (ask|feature|project) for a build already "
                                   "initialised — mirrors `init --scale` for the common case "
                                   "where the requirements-clarifier computes the tier after "
                                   "`init` already ran. Allowed only while status is 'intake' "
                                   "or 'clarifying', before `set-plan` has written scope/"
                                   "milestones/steps; refused everywhere else, naming the "
                                   "status, because re-tiering a planned build is a re-plan, "
                                   "not a scale change. If the plan already carries a different "
                                   "scale, refused unless --force, which prints the old -> new "
                                   "change. Writes only `scale` — the schema is "
                                   "additionalProperties: false, so --reason and --at are not "
                                   "persisted anywhere (there is no field for them); they exist "
                                   "for the caller's own log.")
    p.add_argument("plan", help="path to plan.json")
    p.add_argument("scale", choices=SCALES, help="ask | feature | project")
    p.add_argument("--by", required=True, help="who is setting the scale")
    p.add_argument("--reason", default=None,
                   help="why this tier (not persisted, see description)")
    p.add_argument("--at", default=None,
                   help="ISO timestamp (not persisted, see description)")
    p.add_argument("--force", action="store_true",
                   help="change an already-set scale to a different tier")
    p.set_defaults(func=cmd_set_scale)

    p = sub.add_parser("set-clarifications", parents=[common],
                       help="replace clarifications[] from a JSON file",
                       description="The requirements-clarifier's writer. --file holds a JSON "
                                   "array of clarification objects (or an object with a "
                                   "'clarifications' array); it REPLACES clarifications[] and "
                                   "sets the build status to 'clarifying'. Use this instead of "
                                   "editing plan.json — the write is validated, atomic, and "
                                   "leaves the file untouched if the result would be invalid. "
                                   "At scale 'ask' (contract § 3.1), an 'open' informational "
                                   "row with a proposed_default and no answer is written "
                                   "answered from that default (default_source stamped "
                                   "'proposed_default (scale: ask)' if not already set); "
                                   "blocking rows and anything already answered are untouched, "
                                   "and 'ingest-answers' can still overwrite a filled default.")
    p.add_argument("plan", help="path to plan.json")
    p.add_argument("--file", required=True, help="JSON array of clarification objects")
    p.add_argument("--summary", default=None,
                   help="replace requirement.summary with this one-paragraph restatement. "
                        "`init` can only lift the requirement's first prose line; the "
                        "clarifier is the first agent that has read the whole requirement, "
                        "and this is the only writer of that field.")
    p.set_defaults(func=cmd_set_clarifications)

    p = sub.add_parser("set-plan", parents=[common],
                       help="replace scope/decisions/milestones/steps from a JSON file",
                       description="The build-planner's writer. --file is a JSON object with any "
                                   "of scope, fit_gap (merged into scope), assumptions, "
                                   "decisions, milestones, steps; each named key REPLACES its "
                                   "field. Sets the build status to 'planned' and adds any "
                                   "missing human gates. Refused once the plan is verified, "
                                   "approved, building or done — re-planning starts from a "
                                   "rejected plan gate. Re-planning (status 'plan-rejected') "
                                   "increments `version`; this is the only command that does. "
                                   "§ 3.1: at scale 'ask', also allowed while status is "
                                   "'clarifying' (gate 'clarifications' still pending) PROVIDED "
                                   "no blocking clarification is open — the ask flow is answer -> "
                                   "planner -> verifier -> `gate go`, with G1 signed together "
                                   "with G2 at the end; refused if a blocking question is still "
                                   "unanswered. At 'feature'/'project' scale this adds nothing — "
                                   "the frozen-status rule above is the only check.")
    p.add_argument("plan", help="path to plan.json")
    p.add_argument("--file", required=True, help="JSON object of planner-owned fields")
    p.add_argument("--summary", default=None,
                   help="replace requirement.summary with this one-paragraph restatement. "
                        "The planner is the first agent to have done the fit-gap, so it may "
                        "sharpen the clarifier's paragraph; omit the flag to leave the stored "
                        "summary alone.")
    p.set_defaults(func=cmd_set_plan)

    p = sub.add_parser("amend-step", parents=[common],
                       help="correct one pending/blocked step's declared fields mid-build",
                       description="Replace one or more of a step's amendable fields "
                                   f"({', '.join(AMENDABLE_STEP_FIELDS)}) from a JSON object in "
                                   "--file; each named key REPLACES that field wholesale (no "
                                   "merge). Refused unless the build status is 'building' or "
                                   "'approved' (a 'planned'/'verified' plan is corrected with "
                                   "set-plan; 'done' has no pending steps left), the step's own "
                                   "status is 'pending' or 'blocked' (a step already run is "
                                   "rebuilt via documented -> running, or reset via failed -> "
                                   "pending, not amended), and the step's own step:<id> gate, if "
                                   "any, is not yet approved (reject it first — an amendment "
                                   "invalidates what the human signed). Records who/when/why/"
                                   "which-fields/prior-values in the step's amendments[], "
                                   "re-validates the whole plan, and refuses the write (leaving "
                                   "the file untouched) if any ERROR results. Never touches "
                                   "gates, statuses or runs[]. --prose-only relaxes all of the "
                                   f"above for text that only describes a test: --file may then "
                                   f"hold only {', '.join(PROSE_ONLY_FIELDS)}; an acceptance_tests "
                                   "array must keep the same length with the same type/command/"
                                   "expected/scope at every index (only description may change); "
                                   "the step may be at any status except 'running'; and an "
                                   "already-approved step gate does not block it.")
    p.add_argument("plan", help="path to plan.json")
    p.add_argument("step_id", metavar="step-id", help="e.g. M1-S01")
    p.add_argument("--file", required=True,
                   help=f"JSON object of amendable step fields ({', '.join(AMENDABLE_STEP_FIELDS)}"
                        f"; with --prose-only, only {', '.join(PROSE_ONLY_FIELDS)})")
    p.add_argument("--by", required=True, help="who is making the correction")
    p.add_argument("--reason", required=True, help="why the step is being amended")
    p.add_argument("--at", default=None, help="ISO timestamp (default: UTC now)")
    p.add_argument("--prose-only", action="store_true",
                   help="restrict --file to notes/acceptance_tests[].description text that "
                        "does not change what runs; in exchange, allow any step status except "
                        "'running' and do not block on an already-approved step gate")
    p.set_defaults(func=cmd_amend_step)

    p = sub.add_parser("set-verification", parents=[common],
                       help="record the plan verifier's outcome",
                       description="The plan-verifier's writer. --file holds the verification "
                                   "body (lenses[], blockers[], notes); --outcome sets both "
                                   "verification.status and the build status. 'verified' is what "
                                   "lets the human approve the plan gate; 'plan-rejected' sends "
                                   "the plan back to the planner, archiving the rejected body "
                                   "into history[] without bumping `version` — the planner's "
                                   "next `set-plan` does that.")
    p.add_argument("plan", help="path to plan.json")
    p.add_argument("--file", required=True, help="JSON object: lenses[], blockers[], notes")
    p.add_argument("--outcome", required=True, choices=["verified", "plan-rejected"])
    p.add_argument("--by", default=None, help="the verifier identity to record")
    p.add_argument("--at", default=None,
                   help="ISO timestamp for verified_at (default: UTC now)")
    p.set_defaults(func=cmd_set_verification)

    p = sub.add_parser("set-milestone", parents=[common],
                       help="record a milestone verdict + report path",
                       description="The milestone-verifier's writer: sets the milestone's status "
                                   "and report_path. 'verified' means the cross-step checks "
                                   "passed and the human may now be asked for G3; 'rejected' "
                                   "records a failed verification. The milestone's own status "
                                   "moves to 'building' automatically when its first step starts, "
                                   "and to 'accepted' when the human approves its gate.")
    p.add_argument("plan", help="path to plan.json")
    p.add_argument("milestone", metavar="milestone-id", help="e.g. M1")
    p.add_argument("--status", required=True, choices=["verified", "rejected"])
    p.add_argument("--report-path", required=True,
                   help="build-dir-relative path the verifier wrote, e.g. "
                        "reports/MILESTONE-M1-REPORT.md")
    p.set_defaults(func=cmd_set_milestone)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
