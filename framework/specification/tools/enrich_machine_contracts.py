#!/usr/bin/env python3
"""Generate the full machine-readable command, tool, and agent contracts.

The human specifications remain authoritative for prose. This generator makes the
non-negotiable runtime parts deterministic so host adapters and validators do not
reinterpret them independently.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.9.0"

PRODUCT_STAGES = [
    "validate_input",
    "resolve_targets",
    "authorize_run",
    "plan_context",
    "collect_evidence",
    "synthesize_findings",
    "deterministic_lint",
    "independent_review",
    "persist_run_bundle",
]

COMMON_PRODUCT_ERRORS = [
    {
        "code": "invalid_input",
        "status": "refused",
        "description": "The request does not satisfy the typed command contract.",
        "recovery": "Correct the named fields and invoke the command again.",
    },
    {
        "code": "ambiguous_target",
        "status": "refused",
        "description": "More than one org, project, job, user, record, or component could be selected safely.",
        "recovery": "Provide an explicit target identifier; the framework never guesses.",
    },
    {
        "code": "policy_denied",
        "status": "refused",
        "description": "The requested operation exceeds the active authority profile or read-only product boundary.",
        "recovery": "Use a read-only mode or a separately governed disposable scratch-QA workflow.",
    },
    {
        "code": "evidence_unavailable",
        "status": "partial",
        "description": "Required evidence could not be retrieved, parsed, or proven fresh.",
        "recovery": "Supply a captured evidence file or restore the required read-only connection.",
    },
    {
        "code": "context_overflow",
        "status": "partial",
        "description": "The bounded context or tool-page ceiling was reached.",
        "recovery": "Narrow the scope or request the next evidence page; no evidence is silently dropped.",
    },
    {
        "code": "host_unsupported",
        "status": "partial",
        "description": "The active host cannot enforce or execute a required stage exactly as specified.",
        "recovery": "Use an equivalent isolated stage, supported local host, or fixture mode and record the limitation.",
    },
    {
        "code": "runtime_failure",
        "status": "failed",
        "description": "An unexpected deterministic parser, tool, host, or persistence failure occurred.",
        "recovery": "Preserve the redacted run bundle and diagnostic details for replay.",
    },
]

CORE_ERRORS = [
    {
        "code": "invalid_input",
        "status": "failed",
        "description": "The command arguments are invalid.",
        "recovery": "Correct the arguments shown by the validator.",
    },
    {
        "code": "artifact_unavailable",
        "status": "partial",
        "description": "A requested local artifact, index, plugin, run bundle, or host capability is unavailable.",
        "recovery": "Follow the command-specific diagnostic or bootstrap instruction.",
    },
    {
        "code": "policy_denied",
        "status": "refused",
        "description": "The requested lane or refresh exceeds the active policy.",
        "recovery": "Use an allowed lane or obtain the explicitly required QA authorization.",
    },
    {
        "code": "runtime_failure",
        "status": "failed",
        "description": "The deterministic operation failed unexpectedly.",
        "recovery": "Retain logs and rerun after correcting the reported cause.",
    },
]

ALIASES: dict[str, list[str]] = {
    "sfskills-capabilities": ["capabilities", "list-salesforce-capabilities"],
    "sfskills-doctor": ["doctor", "sf-doctor"],
    "sfskills-explain-route": ["explain-route", "route-salesforce-request"],
    "sfskills-qa-run": ["qa-run", "run-salesforce-qa"],
    "sfskills-replay": ["replay-run", "replay-salesforce-analysis"],
    "sfskills-validate-run": ["validate-run", "verify-salesforce-analysis"],
    "triage-deployment": ["deployment-failure", "analyze-deployment"],
    "triage-apex-tests": ["apex-test-failures", "analyze-apex-tests"],
    "why-cant-user": ["explain-access", "access-path"],
    "plan-metadata-change": ["change-impact", "metadata-impact"],
    "profile-automation": ["automation-profile", "transaction-automation"],
    "review-release-readiness": ["release-readiness", "pre-release-review"],
    "review-security-posture": ["security-review", "salesforce-security-posture"],
    "triage-integration": ["integration-incident", "analyze-integration"],
    "reconcile-data-load": ["data-load-reconciliation", "migration-reconciliation"],
    "assess-org-health": ["org-health", "salesforce-health-assessment"],
    "review-agentforce-agent": ["agentforce-review", "review-agentforce"],
    "compare-orgs": ["org-drift", "compare-salesforce-orgs"],
}

EXAMPLE_VALUES: dict[str, Any] = {
    "job_id": "0Af000000000001",
    "target_org": "qa-sandbox",
    "result_file": "fixtures/deployment-result.json",
    "project_path": "/workspace/customer-salesforce",
    "failure_limit": 100,
    "test_run_id": "707000000000001",
    "method_limit": 100,
    "user": "005000000000001",
    "action": "edit Account.AnnualRevenue on record 001000000000001",
    "object": "Account",
    "record_id": "001000000000001",
    "component": "CustomField:Account.Legacy_Status__c",
    "proposed_change": "retire field after dependency analysis",
    "scope": "force-app/main/default",
    "operation": "update",
    "scenario": "200 Account updates changing AnnualRevenue and OwnerId",
    "release_scope": "git:main...release/2026.08",
    "risk_tolerance": "conservative",
    "policy_profile": "default",
    "incident_window": "2026-08-19T14:00:00Z/2026-08-19T15:00:00Z",
    "integration": "ERP_Order_Sync",
    "supplied_logs": "evidence/erp-sync-errors.jsonl",
    "migration_manifest": "migration/manifest.json",
    "result_files": "migration/results/",
    "mapping_file": "migration/field-map.csv",
    "assessment_scope": "trusted,easy,adaptable",
    "evidence_bundle": "snapshots/qa-org-health.json",
    "business_context": "customer service release train",
    "agent_metadata_path": "force-app/main/default/aiAuthoringBundles/Support_Agent",
    "agent_developer_name": "Support_Agent",
    "review_depth": "full",
    "left_org_or_snapshot": "qa-sandbox",
    "right_org_or_snapshot": "production-snapshot-2026-08-18.json",
    "difference_policy": "config/expected-org-differences.json",
    "filter": "status:qualified domain:devops",
    "request": "Why did deployment 0Af000000000001 fail?",
    "lane": "hermetic",
    "scenario": "DEP-MISSING-DEPENDENCY",
    "run_bundle": ".sfskills/runs/RUN-EXAMPLE",
    "live_refresh": False,
}

TOOL_EVIDENCE_TYPES: dict[str, list[str]] = {
    "get_deployment_result": ["salesforce.deployment.result", "salesforce.deployment.component-failure", "salesforce.deployment.test-failure"],
    "get_apex_test_run": ["salesforce.apex.test-run", "salesforce.apex.test-method-failure", "salesforce.apex.code-coverage"],
    "get_org_identity": ["salesforce.org.identity"],
    "describe_salesforce_component": ["salesforce.metadata.description", "salesforce.schema.description"],
    "get_code_analysis_result": ["repository.code-analysis.finding"],
    "get_user_access_evidence": ["salesforce.access.user", "salesforce.access.permission", "salesforce.access.object-field-record-type"],
    "get_record_access_evidence": ["salesforce.access.record"],
    "get_component_dependency_evidence": ["salesforce.metadata.dependency", "repository.metadata.reference"],
    "get_automation_inventory": ["salesforce.automation.inventory", "salesforce.automation.ordering"],
    "get_flow_test_result": ["salesforce.flow.test-result"],
    "get_org_snapshot_manifest": ["salesforce.org.snapshot-manifest"],
    "compare_org_snapshots": ["salesforce.org.snapshot-diff"],
    "get_integration_config_summary": ["salesforce.integration.configuration"],
    "get_integration_event_summary": ["salesforce.integration.event-summary"],
    "get_data_load_result": ["salesforce.data-load.result", "salesforce.data-load.reject"],
    "run_bounded_read_query": ["salesforce.data.query-result"],
    "get_limits_snapshot": ["salesforce.org.limits-snapshot"],
    "get_agentforce_test_result": ["salesforce.agentforce.test-result", "salesforce.agentforce.definition"],
}

LOCAL_ANALYSIS_TOOLS = {
    "compare_org_snapshots",
    "get_code_analysis_result",
    "get_data_load_result",
}

TOOL_SENSITIVE: dict[str, list[str]] = {
    "get_user_access_evidence": ["org-identifiers", "user-identifiers", "permission-data"],
    "get_record_access_evidence": ["org-identifiers", "user-identifiers", "record-identifiers", "org-business-data"],
    "run_bounded_read_query": ["org-identifiers", "org-business-data"],
    "get_data_load_result": ["record-identifiers", "org-business-data", "local-file-content"],
    "get_integration_event_summary": ["org-identifiers", "endpoint-identifiers", "log-content"],
    "get_integration_config_summary": ["org-identifiers", "endpoint-identifiers", "configuration-identifiers"],
    "get_code_analysis_result": ["repository-source", "local-file-paths"],
    "get_org_identity": ["org-identifiers", "user-identifiers"],
}

TOOL_SPECIFIC_NORMALIZATION: dict[str, list[str]] = {
    "get_deployment_result": [
        "Separate component failures, Apex test failures, coverage findings, warnings, and general messages.",
        "Group duplicate symptoms without losing source counts or evidence locators.",
        "Bind the deployment job to the attested target org and return target_mismatch instead of continuing on disagreement.",
    ],
    "get_apex_test_run": [
        "Normalize suite, class, method, outcome, message, stack trace, duration, queue item, and coverage records.",
        "Preserve one evidence item per failing method before any shared-root-cause clustering.",
        "Bind the run to the attested target org when live retrieval is used.",
    ],
    "get_user_access_evidence": [
        "Represent additive and muting access separately; never collapse them into a single guessed effective permission.",
        "Preserve license, profile, permission-set, group, object, field, record-type, and restriction evidence as distinct facts.",
    ],
    "get_record_access_evidence": [
        "Separate direct record access from inferred sharing mechanisms.",
        "Use minimal bounded reads and never include unrelated record fields.",
    ],
    "compare_org_snapshots": [
        "Compare only manifests with compatible schema versions and explicit expected-difference policy.",
        "Classify additions, removals, modifications, expected differences, unknown comparisons, and dangerous drift separately.",
    ],
    "run_bounded_read_query": [
        "Accept only allowlisted SELECT/aggregate query shapes; reject subqueries or fields outside the declared plan.",
        "Enforce row, field, object, and byte limits before returning model-visible content.",
    ],
}

AGENT_ROLE: dict[str, str] = {
    "sf-intent-router": "orchestrator",
    "sf-context-librarian": "selector",
    "sf-project-inspector": "inspector",
    "sf-org-grounder": "evidence-broker",
    "sf-evidence-reviewer": "reviewer",
    "sf-policy-reviewer": "policy-control",
    "sf-run-resumer": "recovery",
    "sf-qa-grader": "qa-control",
}

AGENT_COLLABORATORS: dict[str, list[str]] = {
    "sf-intent-router": ["sf-context-librarian", "sf-policy-reviewer"],
    "sf-context-librarian": ["sf-intent-router", "sf-project-inspector", "sf-org-grounder"],
    "sf-project-inspector": ["sf-context-librarian", "sf-evidence-reviewer"],
    "sf-org-grounder": ["sf-policy-reviewer", "sf-context-librarian", "sf-evidence-reviewer"],
    "sf-evidence-reviewer": ["sf-policy-reviewer", "sf-qa-grader"],
    "sf-policy-reviewer": ["sf-org-grounder", "sf-evidence-reviewer"],
    "sf-run-resumer": ["sf-context-librarian", "sf-policy-reviewer"],
    "sf-qa-grader": ["sf-evidence-reviewer", "sf-policy-reviewer"],
}

HOST_EXPOSURE: dict[str, str] = {
    "sf-intent-router": "top-level",
    "sf-context-librarian": "subagent",
    "sf-project-inspector": "subagent",
    "sf-org-grounder": "subagent",
    "sf-evidence-reviewer": "subagent",
    "sf-policy-reviewer": "internal-stage",
    "sf-run-resumer": "internal-stage",
    "sf-qa-grader": "qa-only",
}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def update_file(path: Path, expected: Any, write: bool) -> bool:
    rendered = dump(expected)
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    if current == rendered:
        return True
    if write:
        path.write_text(rendered, encoding="utf-8")
        return True
    print(f"DRIFT: {path.relative_to(ROOT)}", file=sys.stderr)
    return False


def extract_section(path: Path, heading: str) -> str:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(rf"^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def bullets(text: str) -> list[str]:
    return [m.group(1).strip() for m in re.finditer(r"^-\s+(.+)$", text, re.MULTILINE)]


def command_modes(command: dict[str, Any], products: dict[str, dict[str, Any]]) -> list[str]:
    product_id = command.get("product_id")
    if product_id:
        return products[product_id]["supported_modes"]
    return {
        "sfskills-capabilities": ["offline"],
        "sfskills-doctor": ["offline", "local-host", "live-read-only"],
        "sfskills-explain-route": ["offline"],
        "sfskills-qa-run": ["hermetic", "live-read-only", "scratch-qa"],
        "sfskills-replay": ["offline", "live-read-only"],
        "sfskills-validate-run": ["offline"],
    }[command["id"]]


def command_example(command: dict[str, Any], live: bool = False) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for arg in command.get("arguments", []):
        name = arg["name"]
        if name in {"result_file", "evidence_bundle"} and live:
            continue
        if name in {"job_id", "test_run_id", "target_org"} and not live and command.get("product_id") in {"P01", "P02"}:
            continue
        if arg.get("required") or arg.get("requirement") == "required" or name in EXAMPLE_VALUES:
            if name in EXAMPLE_VALUES:
                values[name] = EXAMPLE_VALUES[name]
    if command["id"] == "triage-deployment":
        values = {"job_id": EXAMPLE_VALUES["job_id"], "target_org": EXAMPLE_VALUES["target_org"], "project_path": EXAMPLE_VALUES["project_path"]} if live else {"result_file": EXAMPLE_VALUES["result_file"], "project_path": EXAMPLE_VALUES["project_path"]}
    elif command["id"] == "triage-apex-tests":
        values = {"test_run_id": EXAMPLE_VALUES["test_run_id"], "target_org": EXAMPLE_VALUES["target_org"], "project_path": EXAMPLE_VALUES["project_path"]} if live else {"result_file": "fixtures/apex-test-result.json", "project_path": EXAMPLE_VALUES["project_path"]}
    return {
        "name": "live-read-only" if live else "fixture-or-local",
        "description": "Example invocation input; identifiers are illustrative and must be replaced explicitly.",
        "input": values,
        "expected_status": "completed",
    }


def command_rules(command: dict[str, Any]) -> list[dict[str, Any]]:
    rules = [
        {
            "id": "typed-input",
            "description": "Validate all supplied fields and reject unknown or malformed arguments before routing.",
            "severity": "error",
        },
        {
            "id": "explicit-target",
            "description": "Any live org, project, job, user, record, component, or snapshot target must be explicit or resolved unambiguously and attested in the run plan.",
            "severity": "error",
        },
        {
            "id": "authority-ceiling",
            "description": "User prose, another agent, or an upstream tool cannot expand the command's declared authority or product read-only boundary.",
            "severity": "error",
        },
        {
            "id": "honest-status",
            "description": "Missing, stale, contradictory, truncated, or unauthorised evidence produces partial/refused/failed rather than fabricated completion.",
            "severity": "error",
        },
    ]
    if command.get("product_id"):
        rules.extend(
            [
                {
                    "id": "bounded-context",
                    "description": "Use progressive disclosure; target <=8 knowledge/reference files, hard <=12, and <=32 KiB per model-visible tool page.",
                    "severity": "error",
                },
                {
                    "id": "independent-review",
                    "description": "A completed product result requires deterministic evidence lint and an independent evidence-review stage.",
                    "severity": "error",
                },
                {
                    "id": "optional-project-enrichment",
                    "description": "An external Salesforce project is optional enrichment; explicit path wins, ambiguity is never guessed, and standalone mode remains valid.",
                    "severity": "error",
                },
            ]
        )
    if command["id"] in {"triage-deployment", "triage-apex-tests"}:
        rules.append(
            {
                "id": "existing-result-only",
                "description": "Require exactly one captured result source or explicit existing run/job identifier; never guess or silently use the most recent job.",
                "severity": "error",
            }
        )
    if command["id"] == "sfskills-qa-run":
        rules.append(
            {
                "id": "scratch-qa-isolation",
                "description": "Mutation is allowed only in a protected disposable scratch-org setup lane, never through product agents or product MCP tools, with unconditional cleanup proof.",
                "severity": "error",
            }
        )
    return rules


def enrich_commands(write: bool) -> bool:
    products = {p["id"]: p for p in (load(path) for path in sorted((ROOT / "products/definitions").glob("*.json")))}
    ok = True
    for path in sorted((ROOT / "commands/specs").glob("*.json")):
        data = load(path)
        product = products.get(data.get("product_id"))
        data["aliases"] = ALIASES[data["id"]]
        data["supported_modes"] = command_modes(data, products)
        data["validation_rules"] = command_rules(data)
        if product:
            data["errors"] = copy.deepcopy(COMMON_PRODUCT_ERRORS)
        else:
            allowed = set(data["allowed_statuses"])
            status_preference = {
                "invalid_input": ["refused", "failed", "partial"],
                "artifact_unavailable": ["partial", "failed", "refused"],
                "policy_denied": ["refused", "failed", "partial"],
                "runtime_failure": ["failed", "partial", "refused"],
            }
            data["errors"] = copy.deepcopy(CORE_ERRORS)
            for error in data["errors"]:
                error["status"] = next(status for status in status_preference[error["code"]] if status in allowed)
        data["examples"] = [command_example(data, live=False)]
        if product and "live-read-only" in product["supported_modes"]:
            data["examples"].append(command_example(data, live=True))
        data["orchestration_stages"] = PRODUCT_STAGES if product else {
            "sfskills-capabilities": ["validate_input", "read_definitions", "render_result"],
            "sfskills-doctor": ["validate_input", "inspect_environment", "render_diagnostics"],
            "sfskills-explain-route": ["validate_input", "classify_intent", "explain_candidates"],
            "sfskills-qa-run": ["validate_input", "authorize_qa_lane", "execute_scenario", "grade_result", "persist_qa_bundle"],
            "sfskills-replay": ["validate_input", "validate_run_bundle", "rehydrate_checkpoint", "replay_or_refresh", "compare_result"],
            "sfskills-validate-run": ["validate_input", "validate_schemas", "validate_evidence_graph", "validate_policy", "render_result"],
        }[data["id"]]
        data["requires_independent_review"] = bool(product)
        data["host_visibility"] = "maintainer-command" if data.get("maintainer_only") else "user-command"
        if product:
            salesforce_effect = "read-only"
            local_effect = "report-write"
            network = True
        elif data["id"] == "sfskills-qa-run":
            salesforce_effect = "qa-disposable-only"
            local_effect = "qa-artifacts"
            network = True
        elif data["id"] == "sfskills-doctor":
            salesforce_effect = "read-only"
            local_effect = "read-only"
            network = True
        elif data["id"] == "sfskills-replay":
            salesforce_effect = "read-only-if-explicit-refresh"
            local_effect = "report-write"
            network = True
        else:
            salesforce_effect = "none"
            local_effect = "read-only"
            network = False
        data["side_effects"] = {
            "salesforce": salesforce_effect,
            "local_files": local_effect,
            "network_access": network,
            "notes": "No Salesforce mutation is available to product commands. Disposable scratch-QA mutation is a separate guarded setup authority.",
        }
        ok = update_file(path, data, write) and ok
    return ok


def tool_error_codes(requires_target: bool) -> list[dict[str, Any]]:
    errors = [
        {"code": "invalid_input", "status": "error", "retryable": False, "description": "Arguments failed deterministic validation."},
        {"code": "policy_denied", "status": "denied", "retryable": False, "description": "The tool or requested scope is not allowed by the active policy."},
        {"code": "authentication_unavailable", "status": "error", "retryable": False, "description": "Required local authentication is unavailable; no credential is returned."},
        {"code": "upstream_unavailable", "status": "partial", "retryable": True, "description": "The official upstream CLI/API/tool is temporarily unavailable or timed out."},
        {"code": "malformed_upstream", "status": "error", "retryable": False, "description": "Upstream output could not be normalized safely."},
        {"code": "result_too_large", "status": "partial", "retryable": False, "description": "The bounded page was returned with truncation and a continuation cursor where supported."},
        {"code": "redaction_failure", "status": "error", "retryable": False, "description": "Model-visible output was withheld because the redaction contract could not be proven."},
        {"code": "rate_limited", "status": "partial", "retryable": True, "description": "The per-run or upstream call budget was reached."},
    ]
    if requires_target:
        errors.insert(2, {"code": "target_mismatch", "status": "denied", "retryable": False, "description": "Observed org/job/run identity does not match the explicit target binding."})
        errors.insert(2, {"code": "ambiguous_target", "status": "denied", "retryable": False, "description": "The target cannot be resolved unambiguously and the tool will not guess."})
    return errors


def enrich_tools(write: bool) -> bool:
    ok = True
    for path in sorted((ROOT / "mcp/tool-specs").glob("*.json")):
        data = load(path)
        tool_id = data["id"]
        local = tool_id in LOCAL_ANALYSIS_TOOLS
        data["operation_type"] = "local-analysis" if local else "observation"
        data["result_schema"] = "tool-result.schema.json"
        data["evidence_types"] = TOOL_EVIDENCE_TYPES.get(tool_id, [f"salesforce.{tool_id}"])
        rules = [
            "Normalize timestamps to UTC ISO 8601 while preserving the original locator and upstream version.",
            "Generate stable evidence IDs from tool, target binding, source locator, canonical record identity, and redacted content digest.",
            "Preserve source_count and retained_count; never silently discard records or contradictions.",
            "Remove credentials, access tokens, auth URLs, session identifiers, and disallowed fields before model-visible serialization.",
            "Sort deterministic collections by canonical identity so repeated captures are diffable.",
            "Store raw redacted evidence outside the prompt when practical and return only the bounded normalized page.",
        ] + TOOL_SPECIFIC_NORMALIZATION.get(tool_id, [])
        data["normalization_rules"] = rules
        singleton = tool_id in {"get_org_identity", "get_limits_snapshot"}
        data["pagination"] = {
            "strategy": "none" if singleton else "opaque-cursor",
            "default_limit": 1 if singleton else 100,
            "max_limit": 1 if singleton else 500,
            "max_page_bytes": data["max_page_bytes"],
            "must_report_truncation": True,
        }
        data["timeout_seconds"] = 60
        data["retry_policy"] = {
            "max_attempts": 2,
            "retryable_errors": ["upstream_unavailable", "rate_limited"],
            "never_retry_errors": ["invalid_input", "policy_denied", "authentication_unavailable", "ambiguous_target", "target_mismatch", "malformed_upstream", "redaction_failure"],
            "backoff": "bounded-exponential-with-jitter",
        }
        max_calls = 3 if tool_id in {"run_bounded_read_query", "get_org_snapshot_manifest", "get_integration_event_summary"} else 5
        data["rate_limit"] = {
            "max_calls_per_run": max_calls,
            "max_concurrent": 1,
            "on_limit": "partial",
            "notes": "A continuation request consumes the same run budget unless an explicit reviewed run plan grants a larger deterministic budget.",
        }
        data["cache_policy"] = {
            "scope": "run",
            "ttl_seconds": 0 if tool_id in {"get_org_identity", "get_deployment_result", "get_apex_test_run", "get_limits_snapshot"} else 300,
            "cross_target": False,
            "cache_key_fields": ["tool_id", "target_binding", "normalized_arguments", "upstream_version"],
        }
        data["sensitive_data_classes"] = TOOL_SENSITIVE.get(tool_id, ["org-identifiers", "metadata-names"] if not local else ["local-file-paths", "repository-content"])
        data["error_codes"] = tool_error_codes(bool(data["requires_target_pinning"]))
        data["redaction_profile"] = "salesforce-sensitive-data-v1" if tool_id in {"get_user_access_evidence", "get_record_access_evidence", "run_bounded_read_query", "get_data_load_result", "get_integration_event_summary"} else "salesforce-evidence-default-v1"
        data["audit_events"] = [
            "tool.requested",
            "tool.policy_evaluated",
            "tool.target_attested",
            "tool.started",
            "tool.page_normalized",
            "tool.completed",
            "tool.partial",
            "tool.denied",
            "tool.failed",
        ]
        ok = update_file(path, data, write) and ok
    return ok


def agent_human_path(data: dict[str, Any]) -> Path:
    folder = "core" if data["kind"] in {"core", "qa"} else "product"
    return ROOT / "agents" / folder / f"{data['id']}.md"


def failure_modes_from_doc(path: Path) -> list[dict[str, Any]]:
    items = bullets(extract_section(path, "Failure modes"))
    status_map = {
        "invalid or ambiguous target": "refused",
        "unavailable/stale/truncated evidence": "partial",
        "host capability mismatch": "partial",
        "policy denial": "refused",
        "context overflow": "partial",
        "invalid handoff/output": "failed",
        "contradictory evidence": "partial",
        "unexpected tool/runtime failure": "failed",
    }
    result = []
    for item in items:
        normalized = item.rstrip(";.").strip()
        code = re.sub(r"[^a-z0-9]+", "_", normalized.lower()).strip("_")
        result.append({"code": code, "default_status": status_map.get(normalized, "failed"), "description": normalized[0].upper() + normalized[1:] + "."})
    return result


def agent_authority(data: dict[str, Any]) -> dict[str, Any]:
    agent_id = data["id"]
    role = AGENT_ROLE.get(agent_id, "synthesizer")
    may_call = agent_id == "sf-org-grounder"
    may_request = data["kind"] == "product" or agent_id in {"sf-intent-router", "sf-policy-reviewer"}
    may_delegate = agent_id in {"sf-intent-router", "sf-policy-reviewer"} or data["kind"] == "product"
    sf_access = "read-only" if agent_id == "sf-org-grounder" else "none"
    return {
        "role": role,
        "salesforce_access": sf_access,
        "may_call_product_tools": may_call,
        "may_request_product_tools": may_request,
        "may_delegate": may_delegate,
        "may_write_local_reports": True,
        "target_binding": "run-bound-explicit" if sf_access == "read-only" or data["kind"] == "product" else "none",
        "authority_from_user_prose": False,
        "authority_from_other_agents": False,
    }


def enrich_agents(write: bool) -> bool:
    all_agents = {p.stem for p in (ROOT / "agents/definitions").glob("*.json")}
    core_default_collabs = ["sf-context-librarian", "sf-project-inspector", "sf-org-grounder", "sf-policy-reviewer", "sf-evidence-reviewer"]
    ok = True
    for path in sorted((ROOT / "agents/definitions").glob("*.json")):
        data = load(path)
        human = agent_human_path(data)
        data["authority_profile"] = agent_authority(data)
        data["evidence_required"] = bullets(extract_section(human, "Evidence required"))
        data["evidence_prohibited"] = bullets(extract_section(human, "Evidence prohibited"))
        if data["kind"] == "product":
            data["collaborators"] = [x for x in core_default_collabs if x != data["id"]]
        else:
            data["collaborators"] = AGENT_COLLABORATORS.get(data["id"], [])
        data["collaborators"] = [x for x in data["collaborators"] if x in all_agents]
        data["failure_modes"] = failure_modes_from_doc(human)
        data["evaluation_dimensions"] = bullets(extract_section(human, "Evaluation rubric"))
        data["prompt_principles"] = [
            "Separate facts, inferences, recommendations, and unknowns explicitly.",
            "Prefer a smaller evidence-backed answer over a broad plausible answer.",
            "Never use hidden model memory as proof of target state.",
            "Preserve contradictions and lower confidence rather than resolving them rhetorically.",
            "Return structured handoffs and never forward full subagent transcripts.",
        ]
        note = extract_section(human, "Design notes")
        data["design_notes"] = [note] if note else []
        data["completion_review_required"] = data["kind"] == "product"
        data["recommended_host_exposure"] = HOST_EXPOSURE.get(data["id"], "internal-stage")
        data["host_exposure_rationale"] = (
            "Commands are the stable user surface. Expose this role as a host subagent only when isolated context materially improves quality and host smoke tests prove tool and policy behavior."
            if data["kind"] == "product"
            else "This exposure keeps the host surface small while preserving isolation for noisy or independently verifiable work."
        )
        ok = update_file(path, data, write) and ok
    return ok


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="Rewrite contracts deterministically")
    mode.add_argument("--check", action="store_true", help="Fail if generated contracts drift")
    args = parser.parse_args()
    write = bool(args.write)
    ok = enrich_commands(write)
    ok = enrich_tools(write) and ok
    ok = enrich_agents(write) and ok
    if not ok:
        return 1
    print("Machine contracts are current." if args.check else "Machine contracts enriched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
