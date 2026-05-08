"""FastMCP server exposing SfSkills + live-org + agent tools.

Run with ``python -m sfskills_mcp`` (stdio transport). Three primitive
families are surfaced — Tools, Prompts, Resources — across these groups:

Skill library tools:
- ``search_skill``
- ``get_skill``

Live-org tools (core):
- ``describe_org``
- ``list_custom_objects``
- ``list_flows_on_object``
- ``validate_against_org``

Live-org tools (admin metadata):
- ``list_validation_rules``
- ``list_permission_sets``
- ``describe_permission_set``
- ``list_record_types``
- ``list_named_credentials``
- ``list_approval_processes``
- ``tooling_query`` (read-only escape hatch)

Probes (promoted from agents/_shared/probes/):
- ``probe_apex_references``
- ``probe_flow_references``
- ``probe_matching_rules``
- ``probe_permset_shape``
- ``probe_automation_graph`` (flow-builder Step 0 preflight; apex-builder
  recursion-risk check)

Agent tools:
- ``list_agents``
- ``get_agent``

Meta / session bootstrap:
- ``list_deprecated_redirects`` — retired agent ids → canonical router
- ``get_invocation_modes`` — channels this library exposes
- ``emit_envelope`` — atomic write of agent output envelope + paired markdown

Prompts: every wrapper in ``commands/*.md`` registers as an MCP prompt
(``/refactor-apex``, ``/audit-router``, …). See ``prompts.py``.

Resources: ``sfskills://catalog``, ``sfskills://skill/{id}``,
``sfskills://agent/{name}``, ``sfskills://decision-tree/{name}``,
``sfskills://template/{path}``. See ``resources.py``.

Tool counts intentionally absent from this docstring — the live count comes
from ``list_tools()`` at runtime, not from a number maintained by hand.

Each tool returns JSON-serializable dicts. Errors are returned as fields on
the response (``{"error": ...}``) rather than raised, so MCP clients can
surface actionable messages without the server crashing mid-call.
"""

from __future__ import annotations

import asyncio
import json
from functools import lru_cache
from typing import Any

from mcp.server.fastmcp import Context, FastMCP
from mcp.types import ToolAnnotations

from . import admin, agents, dev_org, library, meta, org, paths, probes, prompts, resources, routing, skills


# Reusable annotation profiles. The MCP spec lets clients (Cursor, Cline,
# Claude Desktop) auto-approve tools whose annotations match a trust profile.
# Honest annotations buy us frictionless calls without surrendering safety.
#
# Profile semantics:
#   _ANN_REPO_ONLY   — pure repo reads (no org call, no disk write).
#                      Deterministic; safe to auto-approve everywhere.
#   _ANN_ORG_READ    — read-only org calls via `sf` CLI. No DML, no deploy,
#                      but output depends on external org state — clients
#                      shouldn't cache aggressively.
#   _ANN_ENVELOPE    — emit_envelope writes paired JSON+MD into
#                      docs/reports/<agent>/<run_id>.{json,md}. Scoped,
#                      atomic, overwrite-protected by default — but it IS
#                      a write, so flag honestly.
_ANN_REPO_ONLY = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)
_ANN_ORG_READ = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=True,
)
_ANN_ENVELOPE = ToolAnnotations(
    readOnlyHint=False,
    destructiveHint=False,
    idempotentHint=False,
    openWorldHint=False,
)


SERVER_INSTRUCTIONS_TEMPLATE = """\
SfSkills — Salesforce skill library + live-org metadata + run-time agents over MCP.

Library: {skill_count} skills, {runtime_agent_count} active run-time agents,
plus {build_agent_count} build-time agents and {deprecated_agent_count}
deprecation stubs (resolve via list_deprecated_redirects).

Use search_skill/get_skill to pull grounded Salesforce guidance from the
SfSkills library (source-cited, versioned, role-tagged). Use describe_org,
list_custom_objects, list_flows_on_object, and validate_against_org to check
those recommendations against the user's real Salesforce org before writing
code. Prefer validate_against_org before scaffolding new Apex/Flow patterns
to avoid duplicating an existing framework.

For higher-level tasks (refactor this Apex class, consolidate triggers,
generate tests, audit an LWC bundle, score a deployment, detect org drift,
etc.), call list_agents to see available run-time agents and get_agent to
fetch the instruction file. The agent's AGENT.md tells your model how to
compose skills, templates, decision trees, and the live-org tools above
into a deliverable output. The MCP server does not execute agents — your
model does, with the instructions returned by get_agent.
"""


@lru_cache(maxsize=1)
def _registry_skill_count() -> int:
    """Return ``len(registry.skills)``; falls back to 0 if the file is missing."""
    try:
        path = paths.registry_skills_json()
        payload = json.loads(path.read_text(encoding="utf-8"))
        return len(payload.get("skills", []))
    except (OSError, ValueError):
        return 0


def _server_instructions() -> str:
    classes = agents._agent_classes()
    return SERVER_INSTRUCTIONS_TEMPLATE.format(
        skill_count=_registry_skill_count() or "950+",
        runtime_agent_count=sum(1 for v in classes.values() if v == "runtime"),
        build_agent_count=sum(1 for v in classes.values() if v == "build"),
        deprecated_agent_count=sum(1 for v in classes.values() if v == "deprecated"),
    )


def build_server() -> FastMCP:
    mcp = FastMCP("sfskills", instructions=_server_instructions())

    _skill_count = _registry_skill_count() or "950+"

    @mcp.tool(
        name="search_skill",
        annotations=_ANN_REPO_ONLY,
        description=(
            f"Lexical search over the SfSkills library ({_skill_count} Salesforce "
            "skills spanning admin, apex, flow, lwc, integration, security, data, "
            "architect, devops, omnistudio, agentforce). Returns ranked skill "
            "ids plus top matching chunks. Use this before proposing a pattern."
        ),
    )
    def search_skill(query: str, domain: str | None = None, limit: int = 10) -> dict[str, Any]:
        return skills.search_skill(query=query, domain=domain, limit=limit)

    @mcp.tool(
        name="get_skill",
        annotations=_ANN_REPO_ONLY,
        description=(
            "Fetch a skill by id (e.g. 'apex/trigger-framework'). Returns the "
            "registry metadata and the full SKILL.md body. Set "
            "include_references=true to also pull references/*.md files."
        ),
    )
    def get_skill(
        skill_id: str,
        include_markdown: bool = True,
        include_references: bool = False,
    ) -> dict[str, Any]:
        return skills.get_skill(
            skill_id=skill_id,
            include_markdown=include_markdown,
            include_references=include_references,
        )

    @mcp.tool(
        name="describe_org",
        annotations=_ANN_ORG_READ,
        description=(
            "Describe the user's target Salesforce org via 'sf org display' — "
            "org id, instance URL, edition, API version, sandbox/scratch status. "
            "Use this to ground recommendations in the actual org context."
        ),
    )
    def describe_org(target_org: str | None = None) -> dict[str, Any]:
        return org.describe_org(target_org=target_org)

    @mcp.tool(
        name="list_custom_objects",
        annotations=_ANN_ORG_READ,
        description=(
            "List custom sObjects in the target org. Set include_standard=true "
            "to include standard objects. name_filter does a case-insensitive "
            "substring match on the API name."
        ),
    )
    def list_custom_objects(
        target_org: str | None = None,
        name_filter: str | None = None,
        include_standard: bool = False,
        limit: int = 500,
    ) -> dict[str, Any]:
        return org.list_custom_objects(
            target_org=target_org,
            name_filter=name_filter,
            include_standard=include_standard,
            limit=limit,
        )

    @mcp.tool(
        name="list_flows_on_object",
        annotations=_ANN_ORG_READ,
        description=(
            "List Flows (record-triggered, scheduled-triggered, or "
            "platform-event-triggered) targeting the given sObject, via the "
            "Tooling API. Use this to check for existing automation before "
            "recommending a new Flow."
        ),
    )
    def list_flows_on_object(
        object_name: str,
        target_org: str | None = None,
        active_only: bool = False,
        limit: int = 50,
    ) -> dict[str, Any]:
        return org.list_flows_on_object(
            object_name=object_name,
            target_org=target_org,
            active_only=active_only,
            limit=limit,
        )

    @mcp.tool(
        name="validate_against_org",
        annotations=_ANN_ORG_READ,
        description=(
            "Category-aware probe that checks whether a skill's guidance "
            "already has analogs in the org. E.g. for apex skills it lists "
            "existing *TriggerHandler*/*Handler classes; for flow skills it "
            "lists Flows targeting object_name. Returns probe output and a "
            "summary of hit counts the agent can reason over."
        ),
    )
    def validate_against_org(
        skill_id: str,
        target_org: str | None = None,
        object_name: str | None = None,
    ) -> dict[str, Any]:
        return org.validate_against_org(
            skill_id=skill_id,
            target_org=target_org,
            object_name=object_name,
        )

    @mcp.tool(
        name="list_validation_rules",
        annotations=_ANN_ORG_READ,
        description=(
            "List Validation Rules on an sObject via the Tooling API. Returns "
            "rule name, active state, error message, error display field, and "
            "id. Use this as the entry point for validation-rule-auditor."
        ),
    )
    def list_validation_rules(
        object_name: str,
        target_org: str | None = None,
        active_only: bool = False,
        limit: int = 100,
    ) -> dict[str, Any]:
        return admin.list_validation_rules(
            object_name=object_name,
            target_org=target_org,
            active_only=active_only,
            limit=limit,
        )

    @mcp.tool(
        name="list_permission_sets",
        annotations=_ANN_ORG_READ,
        description=(
            "List Permission Sets in the org. By default excludes the "
            "profile-owned shadow PSes Salesforce creates per profile. Pass "
            "include_owned_by_profile=true when auditing legacy custom "
            "profiles. name_filter does a SOQL LIKE match on Name."
        ),
    )
    def list_permission_sets(
        target_org: str | None = None,
        name_filter: str | None = None,
        include_owned_by_profile: bool = False,
        limit: int = 200,
    ) -> dict[str, Any]:
        return admin.list_permission_sets(
            target_org=target_org,
            name_filter=name_filter,
            include_owned_by_profile=include_owned_by_profile,
            limit=limit,
        )

    @mcp.tool(
        name="describe_permission_set",
        annotations=_ANN_ORG_READ,
        description=(
            "Describe a single Permission Set by API name — header metadata, "
            "ObjectPermissions, and (optionally) FieldPermissions. Use this "
            "inside permission-set-architect to audit what a PSG actually "
            "grants. Set include_field_permissions=false for broad PSes where "
            "the field-perm row count would explode."
        ),
    )
    def describe_permission_set(
        name: str,
        target_org: str | None = None,
        include_field_permissions: bool = True,
    ) -> dict[str, Any]:
        return admin.describe_permission_set(
            name=name,
            target_org=target_org,
            include_field_permissions=include_field_permissions,
        )

    @mcp.tool(
        name="list_record_types",
        annotations=_ANN_ORG_READ,
        description=(
            "List Record Types on an sObject — developer name, label, active "
            "flag, and description. Use this in record-type-and-layout-auditor "
            "and object-designer."
        ),
    )
    def list_record_types(
        object_name: str,
        target_org: str | None = None,
        active_only: bool = False,
        limit: int = 100,
    ) -> dict[str, Any]:
        return admin.list_record_types(
            object_name=object_name,
            target_org=target_org,
            active_only=active_only,
            limit=limit,
        )

    @mcp.tool(
        name="list_named_credentials",
        annotations=_ANN_ORG_READ,
        description=(
            "List Named Credentials in the org. Includes endpoint and "
            "principal type. Source of truth for integration-catalog-builder."
        ),
    )
    def list_named_credentials(
        target_org: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        return admin.list_named_credentials(target_org=target_org, limit=limit)

    @mcp.tool(
        name="list_approval_processes",
        annotations=_ANN_ORG_READ,
        description=(
            "List Approval ProcessDefinitions, optionally filtered by object. "
            "By default returns only active approvals. Source of truth for "
            "automation-migration-router --source-type=approval_process."
        ),
    )
    def list_approval_processes(
        object_name: str | None = None,
        target_org: str | None = None,
        active_only: bool = True,
        limit: int = 100,
    ) -> dict[str, Any]:
        return admin.list_approval_processes(
            object_name=object_name,
            target_org=target_org,
            active_only=active_only,
            limit=limit,
        )

    @mcp.tool(
        name="tooling_query",
        annotations=_ANN_ORG_READ,
        description=(
            "Escape-hatch read-only SOQL against the Tooling or REST API. "
            "Refuses any statement that is not a SELECT or that contains DML "
            "keywords / semicolons. Applies an automatic LIMIT if missing. "
            "Prefer the specialized list_* tools where they exist. Default "
            "subprocess timeout is 90s — see the SFSKILLS_TIMEOUT_SECONDS "
            "env var to raise it for slow queries."
        ),
    )
    def tooling_query(
        soql: str,
        target_org: str | None = None,
        tooling: bool = True,
        limit: int = 200,
    ) -> dict[str, Any]:
        return admin.tooling_query(
            soql=soql,
            target_org=target_org,
            tooling=tooling,
            limit=limit,
        )

    # ----------------------------------------------------------------- #
    # Probes — promoted from agents/_shared/probes/ in Wave 2.            #
    # Centralizing the SOQL + post-processing here eliminates subtle     #
    # drift across agents that used to paste the recipes inline.         #
    # ----------------------------------------------------------------- #

    @mcp.tool(
        name="probe_apex_references",
        annotations=_ANN_ORG_READ,
        description=(
            "Enumerate Apex classes and triggers referencing an "
            "<object>.<field>. Uses word-boundary regex on fetched bodies to "
            "filter substring false positives. Classifies each hit as "
            "read/write/unknown. Primary consumer: field-impact-analyzer."
        ),
    )
    async def probe_apex_references(
        object_name: str,
        field: str,
        ctx: Context,
        target_org: str | None = None,
        include_managed: bool = False,
        limit_per_query: int = 200,
    ) -> dict[str, Any]:
        await ctx.report_progress(
            0.0, total=1.0,
            message=f"Probing Apex references to {object_name}.{field}…",
        )
        result = await asyncio.to_thread(
            probes.probe_apex_references,
            object_name=object_name,
            field=field,
            target_org=target_org,
            include_managed=include_managed,
            limit_per_query=limit_per_query,
        )
        count = result.get("reference_count", 0) if isinstance(result, dict) else 0
        await ctx.report_progress(
            1.0, total=1.0,
            message=f"Found {count} reference(s)",
        )
        return result

    @mcp.tool(
        name="probe_flow_references",
        annotations=_ANN_ORG_READ,
        description=(
            "Enumerate active Flow versions whose metadata XML references "
            "<object>.<field>. Classifies each hit as read (lookup/"
            "condition context) or write (recordCreates / recordUpdates / "
            "assignToReference). Strips <description>/<label> text to avoid "
            "label-based false positives."
        ),
    )
    async def probe_flow_references(
        object_name: str,
        field: str,
        ctx: Context,
        target_org: str | None = None,
        active_only: bool = True,
        limit: int = 200,
    ) -> dict[str, Any]:
        await ctx.report_progress(
            0.0, total=1.0,
            message=f"Probing Flow references to {object_name}.{field}…",
        )
        result = await asyncio.to_thread(
            probes.probe_flow_references,
            object_name=object_name,
            field=field,
            target_org=target_org,
            active_only=active_only,
            limit=limit,
        )
        count = result.get("reference_count", 0) if isinstance(result, dict) else 0
        await ctx.report_progress(
            1.0, total=1.0,
            message=f"Found {count} reference(s)",
        )
        return result

    @mcp.tool(
        name="probe_matching_rules",
        annotations=_ANN_ORG_READ,
        description=(
            "List MatchingRule + DuplicateRule records on an sObject with "
            "their field items. Computes overlaps[] (pairs of active "
            "matching rules sharing >= 1 field — a P0 duplicate-management "
            "smell). Primary consumer: duplicate-rule-designer."
        ),
    )
    async def probe_matching_rules(
        object_name: str,
        ctx: Context,
        target_org: str | None = None,
        active_only: bool = False,
    ) -> dict[str, Any]:
        await ctx.report_progress(
            0.0, total=1.0,
            message=f"Probing matching + duplicate rules on {object_name}…",
        )
        result = await asyncio.to_thread(
            probes.probe_matching_rules,
            object_name=object_name,
            target_org=target_org,
            active_only=active_only,
        )
        if isinstance(result, dict):
            mr = result.get("matching_rule_count", 0)
            dr = result.get("duplicate_rule_count", 0)
            ov = len(result.get("overlaps", []))
            summary = f"Found {mr} matching, {dr} duplicate, {ov} overlap(s)"
        else:
            summary = "Done"
        await ctx.report_progress(1.0, total=1.0, message=summary)
        return result

    @mcp.tool(
        name="probe_permset_shape",
        annotations=_ANN_ORG_READ,
        description=(
            "Summarize a Permission Set / Permission Set Group / user "
            "scope. scope argument is psg:<DeveloperName>, ps:<Name>, or "
            "user:<username>. Emits assignment counts, concentration ratio "
            "vs active standard users, and risk_flags (super-PSG smell + "
            "ModifyAllData detection). Primary consumer: "
            "permission-set-architect."
        ),
    )
    def probe_permset_shape(
        scope: str,
        target_org: str | None = None,
    ) -> dict[str, Any]:
        return probes.probe_permset_shape(scope=scope, target_org=target_org)

    @mcp.tool(
        name="list_agents",
        annotations=_ANN_REPO_ONLY,
        description=(
            "List SfSkills agents available to the caller. Each agent is an "
            "AGENT.md instruction file that tells an LLM how to compose the "
            "skill library, templates, decision-trees, and live-org tools into "
            "a concrete deliverable (refactor, audit, migration plan, etc.). "
            "Filters: kind='runtime' (active user-facing agents), "
            "kind='build' (skill-factory agents), kind='deprecated' (retired "
            "stubs that redirect — pair with list_deprecated_redirects to "
            "find the canonical replacement), or unset for all."
        ),
    )
    def list_agents(kind: str | None = None) -> dict[str, Any]:
        return agents.list_agents(kind=kind)

    @mcp.tool(
        name="get_agent",
        annotations=_ANN_REPO_ONLY,
        description=(
            "Fetch the full AGENT.md body for a named agent (e.g. "
            "'apex-refactorer', 'security-scanner', 'deployment-risk-scorer'). "
            "Returns the markdown instructions plus metadata. The caller's LLM "
            "executes the agent; the MCP server only surfaces the instructions."
        ),
    )
    def get_agent(agent_name: str) -> dict[str, Any]:
        return agents.get_agent(agent_name=agent_name)

    # --- Meta / session-bootstrap tools ----------------------------------- #

    @mcp.tool(
        name="health",
        annotations=_ANN_REPO_ONLY,
        description=(
            "Server diagnostic snapshot — server / SDK / sf-CLI versions, "
            "registry skill count + build timestamp, lexical-index "
            "freshness + size, agent counts by class (runtime / build / "
            "deprecated), and the resolved repo root. Never touches the "
            "org. Use this to verify the MCP is wired up correctly."
        ),
    )
    def health() -> dict[str, Any]:
        return meta.health()

    @mcp.tool(
        name="list_deprecated_redirects",
        annotations=_ANN_REPO_ONLY,
        description=(
            "Return the map of retired agent ids → canonical router + flag. "
            "Call this once per session; before get_agent, check whether the "
            "requested id is in this map and redirect. Example: "
            "'validation-rule-auditor' → {'router': 'audit-router', "
            "'flag': '--domain=validation_rule'}. Prevents routing to a "
            "deprecation stub."
        ),
    )
    def list_deprecated_redirects() -> dict[str, Any]:
        return meta.list_deprecated_redirects()

    @mcp.tool(
        name="get_invocation_modes",
        annotations=_ANN_REPO_ONLY,
        description=(
            "Return docs/agent-invocation-modes.md — the 15 channels this "
            "library can be consumed through (MCP, slash commands, bundle "
            "export, informal chat, CI harness, subagents, etc.) plus a "
            "Quick Picker. MCP is Channel 1 and the canonical channel. "
            "Call this once at session start to match the user's situation "
            "to the right channel."
        ),
    )
    def get_invocation_modes() -> dict[str, Any]:
        return meta.get_invocation_modes()

    @mcp.tool(
        name="emit_envelope",
        annotations=_ANN_ENVELOPE,
        description=(
            "Atomically write an agent's output envelope JSON + paired "
            "markdown report to docs/reports/<agent>/<run_id>.{json,md} per "
            "docs/consumer-responsibilities.md. Use this at the END of any "
            "runtime agent run so the deliverable persists beyond the chat "
            "session. Overwrite protection is ON by default. Returns the "
            "written paths; returns {error, partial_write} on failure."
        ),
    )
    def emit_envelope(
        agent: str,
        run_id: str,
        envelope: dict[str, Any],
        markdown_report: str,
        overwrite: bool = False,
    ) -> dict[str, Any]:
        return meta.emit_envelope(
            agent=agent,
            run_id=run_id,
            envelope=envelope,
            markdown_report=markdown_report,
            overwrite=overwrite,
        )

    # --- Extra probe ------------------------------------------------------ #

    @mcp.tool(
        name="probe_automation_graph",
        annotations=_ANN_ORG_READ,
        description=(
            "Enumerate every active automation on a given sObject: "
            "record-triggered flows (grouped by trigger context), legacy "
            "Process Builders, active Apex triggers (with event usage), "
            "validation rules, workflow rules, and approval processes. "
            "Returns a flags[] block with codes like "
            "MULTIPLE_RECORD_TRIGGERED_FLOWS, PROCESS_BUILDER_PRESENT, "
            "TRIGGER_AND_FLOW_COEXIST. flow-builder Step 0 preflight; "
            "apex-builder recursion-risk check."
        ),
    )
    async def probe_automation_graph(
        object_name: str,
        ctx: Context,
        target_org: str | None = None,
        include_managed: bool = False,
    ) -> dict[str, Any]:
        await ctx.report_progress(
            0.0, total=1.0,
            message=f"Probing automation graph on {object_name}…",
        )
        result = await asyncio.to_thread(
            probes.probe_automation_graph,
            object_name=object_name,
            target_org=target_org,
            include_managed=include_managed,
        )
        if isinstance(result, dict):
            active = result.get("active", {}) or {}
            n_rt = len(active.get("record_triggered_flows", []) or [])
            n_tr = len(active.get("triggers", []) or [])
            n_flags = len(result.get("flags", []) or [])
            summary = f"{n_rt} RT flows · {n_tr} triggers · {n_flags} flag(s)"
        else:
            summary = "Done"
        await ctx.report_progress(1.0, total=1.0, message=summary)
        return result

    # ----------------------------------------------------------------- #
    # Tier-C dev-org tools — Apex / LWC / object-shape inventory the     #
    # developer-tier agents (apex-refactorer, trigger-consolidator,      #
    # lwc-builder/auditor/debugger, deployment-risk-scorer) need to      #
    # answer "does this already exist in the org?".                      #
    # ----------------------------------------------------------------- #

    @mcp.tool(
        name="list_apex_classes",
        annotations=_ANN_ORG_READ,
        description=(
            "List Apex classes in the org via the Tooling API. Excludes "
            "managed-package classes by default (NamespacePrefix = null). "
            "name_filter does a SOQL LIKE on Name; status_filter is "
            "'Active' / 'Deleted' / 'Inactive'. Primary consumer: "
            "apex-refactorer, code-reviewer, deployment-risk-scorer."
        ),
    )
    def list_apex_classes(
        target_org: str | None = None,
        name_filter: str | None = None,
        include_managed: bool = False,
        status_filter: str | None = None,
        limit: int = 200,
    ) -> dict[str, Any]:
        return dev_org.list_apex_classes(
            target_org=target_org,
            name_filter=name_filter,
            include_managed=include_managed,
            status_filter=status_filter,
            limit=limit,
        )

    @mcp.tool(
        name="get_apex_class",
        annotations=_ANN_ORG_READ,
        description=(
            "Fetch one ApexClass by name. include_body defaults True; "
            "pass False for a header-only call when the class is large "
            "or you only need metadata."
        ),
    )
    def get_apex_class(
        name: str,
        target_org: str | None = None,
        include_body: bool = True,
    ) -> dict[str, Any]:
        return dev_org.get_apex_class(
            name=name, target_org=target_org, include_body=include_body,
        )

    @mcp.tool(
        name="list_apex_triggers",
        annotations=_ANN_ORG_READ,
        description=(
            "List ApexTrigger rows. object_name scopes to one sObject. "
            "Returns events[] (BeforeInsert / AfterUpdate / etc.) per "
            "trigger so trigger-consolidator can spot multi-trigger "
            "anti-patterns immediately."
        ),
    )
    def list_apex_triggers(
        target_org: str | None = None,
        object_name: str | None = None,
        active_only: bool = False,
        include_managed: bool = False,
        limit: int = 100,
    ) -> dict[str, Any]:
        return dev_org.list_apex_triggers(
            target_org=target_org,
            object_name=object_name,
            active_only=active_only,
            include_managed=include_managed,
            limit=limit,
        )

    @mcp.tool(
        name="list_lwc_bundles",
        annotations=_ANN_ORG_READ,
        description=(
            "List Lightning Web Component bundles via the Tooling API. "
            "Excludes managed-package bundles by default. Primary consumer: "
            "lwc-auditor, lwc-builder."
        ),
    )
    def list_lwc_bundles(
        target_org: str | None = None,
        name_filter: str | None = None,
        include_managed: bool = False,
        limit: int = 200,
    ) -> dict[str, Any]:
        return dev_org.list_lwc_bundles(
            target_org=target_org,
            name_filter=name_filter,
            include_managed=include_managed,
            limit=limit,
        )

    @mcp.tool(
        name="get_lwc_bundle",
        annotations=_ANN_ORG_READ,
        description=(
            "Fetch one LightningComponentBundle by DeveloperName + (by "
            "default) every resource in the bundle (js, html, css, "
            "meta-xml). Pass include_resources=False for a header-only "
            "call. Primary consumer: lwc-debugger, lwc-auditor."
        ),
    )
    def get_lwc_bundle(
        name: str,
        target_org: str | None = None,
        include_resources: bool = True,
    ) -> dict[str, Any]:
        return dev_org.get_lwc_bundle(
            name=name, target_org=target_org, include_resources=include_resources,
        )

    @mcp.tool(
        name="list_custom_fields",
        annotations=_ANN_ORG_READ,
        description=(
            "List fields on an sObject via EntityParticle (REST API). "
            "Default returns custom fields only (__c suffix); pass "
            "include_standard=True for standard fields too, or "
            "include_pseudo_fields=True to also surface system-managed "
            "rows (Id, IsDeleted, SystemModstamp, …). Returns type, "
            "length, precision, reference_to, relationship_name per field."
        ),
    )
    def list_custom_fields(
        object_name: str,
        target_org: str | None = None,
        include_standard: bool = False,
        include_pseudo_fields: bool = False,
        limit: int = 500,
    ) -> dict[str, Any]:
        return dev_org.list_custom_fields(
            object_name=object_name,
            target_org=target_org,
            include_standard=include_standard,
            include_pseudo_fields=include_pseudo_fields,
            limit=limit,
        )

    @mcp.tool(
        name="describe_object_full",
        annotations=_ANN_ORG_READ,
        description=(
            "Composite read: fields + record types + validation rules + "
            "active flows for one sObject in a single call. Saves four "
            "round-trips object-designer / field-impact-analyzer would "
            "otherwise make. Per-section errors surface as "
            "<section>_error so partial responses still useful."
        ),
    )
    def describe_object_full(
        object_name: str,
        target_org: str | None = None,
        include_fields: bool = True,
        include_record_types: bool = True,
        include_validation_rules: bool = True,
        include_active_flows: bool = True,
    ) -> dict[str, Any]:
        return dev_org.describe_object_full(
            object_name=object_name,
            target_org=target_org,
            include_fields=include_fields,
            include_record_types=include_record_types,
            include_validation_rules=include_validation_rules,
            include_active_flows=include_active_flows,
        )

    @mcp.tool(
        name="list_orgs",
        annotations=_ANN_ORG_READ,
        description=(
            "List every Salesforce org the user is authenticated to. "
            "Wraps 'sf org list'. Use this when the user hasn't told you "
            "which target_org to use — the response gives you valid "
            "aliases / usernames to choose from."
        ),
    )
    def list_orgs() -> dict[str, Any]:
        return dev_org.list_orgs()

    # ----------------------------------------------------------------- #
    # Tier-C knowledge-search tools — symmetric with search_skill but    #
    # over the rest of the knowledge layer (agents / templates /         #
    # decision-trees). All read-only, no org call.                       #
    # ----------------------------------------------------------------- #

    @mcp.tool(
        name="search_agents",
        annotations=_ANN_REPO_ONLY,
        description=(
            "Rank SfSkills agents by relevance to a natural-language query. "
            "Useful when you know what you want to do (e.g. 'audit picklists') "
            "but don't know which agent owns it. Title and 'What This Agent "
            "Does' summary weighted heavier than body."
        ),
    )
    def search_agents(query: str, limit: int = 10) -> dict[str, Any]:
        return library.search_agents(query=query, limit=limit)

    @mcp.tool(
        name="search_templates",
        annotations=_ANN_REPO_ONLY,
        description=(
            "Rank canonical building blocks under templates/ by relevance "
            "(TriggerHandler, ApplicationLogger, BaseService, TestDataFactory, "
            "LWC skeleton, Flow fault-path, etc.). Use this BEFORE writing "
            "boilerplate to avoid reinventing what already exists."
        ),
    )
    def search_templates(query: str, limit: int = 10) -> dict[str, Any]:
        return library.search_templates(query=query, limit=limit)

    @mcp.tool(
        name="search_decision_trees",
        annotations=_ANN_REPO_ONLY,
        description=(
            "Rank standards/decision-trees/ by relevance and return the "
            "best matching section per tree (e.g. 'flow vs apex' → "
            "automation-selection.md → '## Flow vs Apex'). MUST be "
            "consulted BEFORE choosing a technology when the user's task "
            "spans more than one option."
        ),
    )
    def search_decision_trees(query: str, limit: int = 6) -> dict[str, Any]:
        return library.search_decision_trees(query=query, limit=limit)

    @mcp.tool(
        name="get_template",
        annotations=_ANN_REPO_ONLY,
        description=(
            "Fetch one canonical template by relative path under templates/ "
            "(e.g. 'apex/TriggerHandler.cls'). Returns the full body."
        ),
    )
    def get_template(path: str) -> dict[str, Any]:
        return library.get_template(path=path)

    @mcp.tool(
        name="get_decision_tree",
        annotations=_ANN_REPO_ONLY,
        description=(
            "Fetch one decision tree by basename without .md (e.g. "
            "'automation-selection'). Returns the full markdown — agents "
            "should cite the specific branch they followed."
        ),
    )
    def get_decision_tree(name: str) -> dict[str, Any]:
        return library.get_decision_tree(name=name)

    @mcp.tool(
        name="suggest_agent",
        annotations=_ANN_REPO_ONLY,
        description=(
            "Take a free-text task description ('I want to refactor a "
            "2000-line Apex class', 'audit my picklists', 'design a "
            "permission set for the marketing team') and return ranked "
            "candidate agents + decision-tree branches the chosen agent "
            "should consult before recommending a technology. Top pick "
            "comes back ready for get_agent. Excludes deprecated stubs."
        ),
    )
    def suggest_agent(
        task: str,
        limit: int = 3,
        include_decision_trees: bool = True,
    ) -> dict[str, Any]:
        return routing.suggest_agent(
            task=task, limit=limit, include_decision_trees=include_decision_trees,
        )

    # --- Prompts (commands/*.md → MCP slash commands) --------------------- #
    # Every wrapper file in ``commands/`` becomes a prompt the client can
    # invoke as ``/<name>``. The wrapper body is the prompt's render output;
    # the client's model executes the wrapper interactively from there.
    prompts.register_all(mcp)

    # --- Resources (skills, agents, decision trees, templates) ------------ #
    # MCP clients can pre-list these and pull on demand without a tool call.
    # Five URI shapes:
    #   sfskills://catalog
    #   sfskills://skill/{id}
    #   sfskills://agent/{name}
    #   sfskills://decision-tree/{name}
    #   sfskills://template/{path}
    resources.register_all(mcp)

    return mcp


def run(transport: str = "stdio") -> None:
    """Entry point used by ``python -m sfskills_mcp`` and the console script."""
    build_server().run(transport=transport)
