from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
import shlex
from typing import Iterable


class Decision(str, Enum):
    ALLOW="allow"
    DENY="deny"
    ASK="ask"


@dataclass(frozen=True)
class PolicyResult:
    decision: Decision
    reason_code: str
    message: str


@dataclass
class ProductPolicy:
    allowed_tools: set[str]
    denied_tools: set[str] | None = None
    default_decision: Decision = Decision.DENY
    allowed_orgs: set[str] | None = None

    def evaluate_tool(self, tool_id: str, target_org: str | None = None) -> PolicyResult:
        denied=self.denied_tools or set()
        if tool_id in denied:
            return PolicyResult(Decision.DENY,"tool_explicitly_denied",tool_id)
        if tool_id not in self.allowed_tools:
            return PolicyResult(self.default_decision,"tool_not_allowlisted",tool_id)
        if self.allowed_orgs is not None:
            if not target_org:
                return PolicyResult(Decision.DENY,"target_org_required",tool_id)
            if target_org not in self.allowed_orgs:
                return PolicyResult(Decision.DENY,"target_org_not_allowed",target_org)
        return PolicyResult(Decision.ALLOW,"allowlisted_read_only_tool",tool_id)


_COMPOUND=re.compile(r"(?:;|&&|\|\||(?<!\|)\|(?!\|)|`|\$\(|\n|\r|>|<)")
_FORBIDDEN_WRAPPERS={"bash","sh","zsh","fish","cmd","powershell","pwsh","eval","env","xargs"}


def _has_option(tokens: list[str], name: str) -> bool:
    return name in tokens or any(t.startswith(name+"=") for t in tokens)


def evaluate_salesforce_shell(command: str) -> PolicyResult:
    if not command.strip():
        return PolicyResult(Decision.DENY,"empty_command","empty")
    if _COMPOUND.search(command):
        return PolicyResult(Decision.DENY,"compound_or_redirection","Compound shell syntax is not allowed")
    try:
        tokens=shlex.split(command,posix=True)
    except ValueError as exc:
        return PolicyResult(Decision.DENY,"shell_parse_error",str(exc))
    if not tokens:
        return PolicyResult(Decision.DENY,"empty_command","empty")
    if tokens[0].lower() in _FORBIDDEN_WRAPPERS:
        return PolicyResult(Decision.DENY,"shell_wrapper_denied",tokens[0])
    if tokens[0] not in {"sf","sfdx"}:
        return PolicyResult(Decision.DENY,"non_salesforce_command",tokens[0])
    if tokens[0]=="sfdx":
        return PolicyResult(Decision.DENY,"legacy_cli_not_allowlisted","Use brokered sf operations")

    words=[t for t in tokens[1:] if not t.startswith("-")]
    # Exact read-only references permitted for the reference policy.
    if words[:3]==["project","deploy","report"]:
        if _has_option(tokens,"--use-most-recent"):
            return PolicyResult(Decision.DENY,"implicit_job_selection","Explicit --job-id required")
        if not _has_option(tokens,"--job-id") or not _has_option(tokens,"--json"):
            return PolicyResult(Decision.DENY,"deployment_report_flags","--job-id and --json required")
        return PolicyResult(Decision.ALLOW,"read_only_deployment_report","ok")
    if words[:3]==["apex","get","test"]:
        if not (_has_option(tokens,"--test-run-id") or _has_option(tokens,"--test-run-id=")) or not _has_option(tokens,"--json"):
            return PolicyResult(Decision.DENY,"apex_test_report_flags","explicit test run ID and --json required")
        return PolicyResult(Decision.ALLOW,"read_only_apex_test_report","ok")
    if words[:2]==["org","display"]:
        if not _has_option(tokens,"--json"):
            return PolicyResult(Decision.DENY,"org_display_requires_json","--json required")
        return PolicyResult(Decision.ALLOW,"read_only_org_identity","ok")
    return PolicyResult(Decision.DENY,"sf_command_not_allowlisted"," ".join(words[:4]))
