"""Fail-closed Salesforce mutation policy for Cursor shell and MCP hooks.

Decisions are based on argv structure, not substring search. Compound commands,
nested shells, and relative ``./sf`` wrappers are denied.
"""

from __future__ import annotations

import json
import shlex
from typing import Any

# Tokens that start a nested interpreter. Always deny: the inner command is not
# a first-class argv we can audit without a full shell grammar.
_NESTED_SHELLS = {
    "bash",
    "sh",
    "zsh",
    "dash",
    "ksh",
    "fish",
    "csh",
    "tcsh",
    "busybox",
}

_PYTHON = {"python", "python3", "python3.11", "python3.12", "python3.13"}

# Product-allowed python entrypoints (basename of the script path).
_ALLOWED_PYTHON_SCRIPTS = {
    "sfskills_doctor.py",
    "install_cursor_plugin.py",
    "build_cursor_plugin.py",
    "search_knowledge.py",
    "sfskills_policy.py",
    "sfskills_precompact.py",
    "run_mcp.py",
}

_ALLOWED_PYTHON_MODULES = {"sfskills_mcp", "unittest"}

# sf project deploy <verb>
_DEPLOY_MUTATING_VERBS = {
    "start",
    "validate",
    "quick",
    "cancel",
    "resume",
    "preview",
    "reportconvert",  # defensive: unknown sibling
}

_SFDX_MUTATING = {
    "force:source:deploy",
    "force:mdapi:deploy",
    "force:source:push",
    "force:org:create",
    "force:org:delete",
    "force:user:create",
    "force:user:permset:assign",
    "force:apex:execute",
    "force:data:soql:query",  # keep query allowed via sf data query? sfdx query is read — allow report only
}

# Explicit sfdx report forms that are read-only.
_SFDX_REPORT = {
    "force:source:deploy:report",
    "force:mdapi:deploy:report",
}

_MCP_DENY_EXACT = {
    "deploy_metadata",
    "create_scratch_org",
    "delete_org",
    "assign_permission_set",
    "run_apex_test",
    "create_org_snapshot",
    "seed",  # sandbox-seed writes
}

_MCP_DENY_SUBSTRINGS = (
    "deploy start",
    "deploy_start",
    "quickdeploy",
    "quick_deploy",
    "anonymous",
    "apex_execute",
    "execute_anonymous",
)

# Read-only SfSkills MCP tools permitted in product hooks. Keep in sync with
# mcp/sfskills-mcp/tests/test_tools.py EXPECTED_TOOLS minus mutating tools.
_MCP_ALLOW_EXACT = frozenset(
    {
        # Skill library
        "search_skill",
        "get_skill",
        # Live-org core
        "describe_org",
        "list_custom_objects",
        "list_flows_on_object",
        "validate_against_org",
        # Live-org admin metadata
        "list_validation_rules",
        "list_permission_sets",
        "describe_permission_set",
        "list_record_types",
        "list_named_credentials",
        "list_approval_processes",
        "tooling_query",
        # Probes
        "probe_apex_references",
        "probe_flow_references",
        "probe_matching_rules",
        "probe_permset_shape",
        "probe_automation_graph",
        # Agents
        "list_agents",
        "get_agent",
        # Meta / session bootstrap
        "list_deprecated_redirects",
        "get_invocation_modes",
        "emit_envelope",
        # Tier C — dev-org tools
        "list_apex_classes",
        "get_apex_class",
        "list_apex_triggers",
        "list_lwc_bundles",
        "get_lwc_bundle",
        "list_custom_fields",
        "describe_object_full",
        "list_orgs",
        # Tier C — knowledge-search + routing
        "search_agents",
        "search_templates",
        "search_decision_trees",
        "get_template",
        "get_decision_tree",
        "suggest_agent",
        # Tier D — production polish
        "health",
        "get_deployment_result",
        "get_apex_test_run",
        "get_user_access_evidence",
        "get_component_dependency_evidence",
        "get_automation_inventory",
        "get_flow_test_result",
        "get_code_analysis_result",
        "get_integration_config_summary",
        "get_data_load_result",
        "get_org_snapshot_manifest",
        "get_agentforce_test_result",
        "compare_org_snapshots",
    }
)

_SF_DATA_MUTATE = {"create", "update", "delete", "upsert", "import", "export", "bulk"}


def _has_compound_operators(command: str) -> bool:
    in_single = False
    in_double = False
    i = 0
    while i < len(command):
        ch = command[i]
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
        elif not in_single and not in_double:
            if ch in ";\n":
                return True
            if ch == "&" and i + 1 < len(command) and command[i + 1] == "&":
                return True
            if ch == "|" and i + 1 < len(command) and command[i + 1] == "|":
                return True
            if ch == "|":
                return True
            if ch == "`":
                return True
            if ch == "$" and i + 1 < len(command) and command[i + 1] == "(":
                return True
        i += 1
    return False


def _decision(permission: str, *, user_message: str, agent_message: str | None = None) -> dict[str, str]:
    out = {"permission": permission, "user_message": user_message}
    if agent_message:
        out["agent_message"] = agent_message
    return out


def _deny(reason: str) -> dict[str, str]:
    return _decision(
        "deny",
        user_message=reason,
        agent_message="SfSkills policy denied this command. Use read-only `sf project deploy report --job-id <id> --json` or a local JSON fixture.",
    )


def _allow(reason: str = "allowed read-only product operation") -> dict[str, str]:
    return _decision("allow", user_message=reason)


def _flag_map(argv: list[str]) -> dict[str, str | bool]:
    flags: dict[str, str | bool] = {}
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok.startswith("--") and "=" in tok:
            key, _, val = tok.partition("=")
            flags[key] = val
        elif tok.startswith("--"):
            if i + 1 < len(argv) and not argv[i + 1].startswith("-"):
                flags[tok] = argv[i + 1]
                i += 1
            else:
                flags[tok] = True
        elif tok.startswith("-") and len(tok) == 2:
            if i + 1 < len(argv) and not argv[i + 1].startswith("-"):
                flags[tok] = argv[i + 1]
                i += 1
            else:
                flags[tok] = True
        i += 1
    return flags


def _has_job_id(flags: dict[str, str | bool]) -> bool:
    for key in ("--job-id", "--jobid", "-i"):
        val = flags.get(key)
        if isinstance(val, str) and val.strip():
            return True
    return False


def _evaluate_sf(argv: list[str]) -> dict[str, str]:
    # argv[0] is sf or sfdx binary basename
    rest = argv[1:]
    joined = " ".join(rest).lower()
    if "use-most-recent" in joined or "--use-most-recent" in rest or "-r" in rest:
        # Product forbids guessing the latest job.
        if "deploy" in rest and "report" in rest:
            return _deny("sf project deploy report must pass an explicit --job-id; --use-most-recent is not allowed")

    # sf project deploy ...
    try:
        p = rest.index("project")
    except ValueError:
        p = -1
    if p >= 0 and p + 1 < len(rest) and rest[p + 1] == "deploy":
        verb = rest[p + 2] if p + 2 < len(rest) else ""
        if verb in _DEPLOY_MUTATING_VERBS or verb == "":
            return _deny(f"Salesforce deploy mutation '{verb or '(missing)'}' is not allowed")
        if verb == "report":
            flags = _flag_map(rest)
            if not _has_job_id(flags):
                return _deny("sf project deploy report requires --job-id")
            if "--json" not in rest and not any(t.startswith("--json") for t in rest):
                # JSON is required so the MCP wrapper can redact/normalize.
                return _deny("sf project deploy report must include --json")
            return _allow("read-only deploy report")
        return _deny(f"unsupported sf project deploy verb '{verb}'")

    # sf org / data / apex mutation
    if rest[:1] == ["org"] and rest[1:2] and rest[1] in {"create", "delete", "login", "logout", "refresh"}:
        if rest[1] in {"create", "delete", "refresh"}:
            return _deny(f"sf org {rest[1]} is not allowed")
    if rest[:1] == ["data"] and len(rest) > 1 and rest[1] in _SF_DATA_MUTATE:
        return _deny(f"sf data {rest[1]} is not allowed")
    if rest[:1] == ["apex"] and rest[1:2] and rest[1] in {"run", "execute"}:
        return _deny("anonymous / Apex execution / test start is not allowed")
    if rest[:3] == ["apex", "get", "test"] or rest[:4] == ["force", "apex", "test", "report"]:
        flags = _flag_map(rest)
        if not flags.get("--test-run-id") and not flags.get("-i"):
            return _deny("sf apex get test requires --test-run-id")
        if "--json" not in rest and not any(t.startswith("--json") for t in rest):
            return _deny("sf apex get test must include --json")
        return _allow("read-only apex test report")
    if rest[:1] == ["package"] and rest[1:2] and rest[1] in {"install", "uninstall"}:
        return _deny("package install/uninstall is not allowed")

    # Other sf commands: ask rather than silently allow (fail closed for unknown
    # mutating surface). Read-only org display / query can be asked.
    if rest[:2] == ["org", "display"] or rest[:2] == ["org", "list"]:
        return _allow("read-only org listing")
    if rest[:2] == ["data", "query"]:
        return _allow("read-only SOQL")
    if rest[:1] == ["project"] and rest[1:2] == ["retrieve"]:
        return _decision("ask", user_message="retrieve is read-only metadata; confirm before running")
    return _decision("ask", user_message="sf command is not on the product allowlist; confirm before running")


def _evaluate_sfdx(argv: list[str]) -> dict[str, str]:
    rest = argv[1:]
    topic = rest[0] if rest else ""
    if topic in _SFDX_REPORT:
        flags = _flag_map(rest)
        if not _has_job_id(flags) and "--jobid" not in flags:
            return _deny("legacy sfdx deploy report requires a job id")
        return _allow("read-only legacy deploy report")
    if topic in _SFDX_MUTATING or topic.startswith("force:source:deploy") or topic.startswith("force:mdapi:deploy"):
        if topic not in _SFDX_REPORT:
            return _deny(f"legacy sfdx mutation '{topic}' is not allowed")
    return _decision("ask", user_message="legacy sfdx command is not on the product allowlist")


def _evaluate_python(argv: list[str]) -> dict[str, str]:
    rest = argv[1:]
    if not rest:
        return _deny("bare python interpreter is not allowed")
    if rest[0] in {"-c", "-cc"} or rest[0].startswith("-c"):
        return _deny("python -c is not allowed")
    if rest[0] == "-m":
        mod = rest[1] if len(rest) > 1 else ""
        root = mod.split(".", 1)[0]
        if root in _ALLOWED_PYTHON_MODULES:
            return _allow(f"python -m {mod}")
        return _deny(f"python module '{mod}' is not on the product allowlist")
    script = rest[0]
    if script.startswith("-"):
        # skip flags until script
        for tok in rest:
            if not tok.startswith("-"):
                script = tok
                break
        else:
            return _deny("python invocation has no script")
    normalized = script.replace("\\", "/")
    base = normalized.rsplit("/", 1)[-1]
    if base in _ALLOWED_PYTHON_SCRIPTS:
        return _allow(f"product script {base}")
    # Authoring CLIs in this checkout are not Salesforce mutations.
    if base.endswith(".py") and (
        normalized.startswith("scripts/") or "/scripts/" in normalized
    ):
        return _allow(f"repo script {base}")
    return _deny(f"python script '{base}' is not on the product allowlist")


def evaluate_shell_command(command: str) -> dict[str, str]:
    if not command or not command.strip():
        return _deny("empty command")
    if _has_compound_operators(command):
        return _deny("compound shell syntax (; | && || ` $() ) is not allowed")
    try:
        argv = shlex.split(command, posix=True)
    except ValueError:
        return _deny("command could not be parsed")
    if not argv:
        return _deny("empty argv")
    first = argv[0]
    # Relative wrappers like ./sf or path/sf are a common bypass.
    if "/" in first or first.startswith("."):
        return _deny("relative or path-qualified binaries are not allowed; call `sf` on PATH")
    base = first.rsplit("/", 1)[-1]
    if base in _NESTED_SHELLS or base in {"env", "xargs", "nice", "nohup", "timeout", "stdbuf"}:
        if base == "env":
            # env VAR=x sf ... — still a wrapper. Deny.
            return _deny("env/wrapper invocation is not allowed")
        return _deny("nested shells and command wrappers are not allowed")
    if base in {"alias", "eval", "source", "."}:
        return _deny("shell alias/eval is not allowed")
    if base in {"sf"}:
        return _evaluate_sf(argv)
    if base in {"sfdx"}:
        return _evaluate_sfdx(argv)
    if base in _PYTHON:
        return _evaluate_python(argv)
    if base == "git":
        return _allow("repository git")
    return _decision("ask", user_message=f"non-Salesforce command '{base}' requires confirmation")


def evaluate_mcp_call(tool_name: str, tool_input: Any = None) -> dict[str, str]:
    name = (tool_name or "").strip()
    if not name:
        return _deny("missing MCP tool name")
    lowered = name.lower()
    if name in _MCP_DENY_EXACT or lowered in _MCP_DENY_EXACT:
        return _deny(f"MCP tool '{name}' is a mutating Salesforce operation")
    for needle in _MCP_DENY_SUBSTRINGS:
        if needle in lowered:
            return _deny(f"MCP tool '{name}' looks like a mutating operation")
    if "deploy" in lowered and name != "get_deployment_result":
        return _deny(f"MCP tool '{name}' is not the read-only deployment result tool")
    # get_deployment_result must include job_id
    if name == "get_deployment_result":
        payload = tool_input
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                payload = {}
        if not isinstance(payload, dict) or not str(payload.get("job_id") or "").strip():
            return _deny("get_deployment_result requires job_id")
        return _allow("read-only get_deployment_result")
    if name in _MCP_ALLOW_EXACT:
        return _allow(f"read-only MCP tool '{name}'")
    return _deny("unknown MCP tool is not on the product allowlist")


def evaluate_hook_payload(payload: dict[str, Any]) -> dict[str, str]:
    """Dispatch Cursor hook stdin JSON."""
    if "command" in payload and "tool_name" not in payload:
        return evaluate_shell_command(str(payload.get("command") or ""))
    if "tool_name" in payload:
        return evaluate_mcp_call(str(payload.get("tool_name") or ""), payload.get("tool_input"))
    # Ambiguous: some MCP payloads also include a server command string.
    if payload.get("command") and payload.get("url"):
        return evaluate_mcp_call(str(payload.get("tool_name") or ""), payload.get("tool_input"))
    return _deny("unrecognized hook payload")
