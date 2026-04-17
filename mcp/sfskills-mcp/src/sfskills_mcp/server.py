"""FastMCP server exposing SfSkills + live-org + agent tools.

Run with ``python -m sfskills_mcp`` (stdio transport). The server registers
nineteen tools:

Skill library:
- ``search_skill``
- ``get_skill``

Live-org (core):
- ``describe_org``
- ``list_custom_objects``
- ``list_flows_on_object``
- ``validate_against_org``

Live-org (admin metadata):
- ``list_validation_rules``
- ``list_permission_sets``
- ``describe_permission_set``
- ``list_record_types``
- ``list_named_credentials``
- ``list_approval_processes``
- ``tooling_query`` (read-only escape hatch)

Probes (promoted from agents/_shared/probes/ in Wave 2):
- ``probe_apex_references``
- ``probe_flow_references``
- ``probe_matching_rules``
- ``probe_permset_shape``

Agents:
- ``list_agents``
- ``get_agent``

Each tool returns JSON-serializable dicts. Errors are returned as fields on
the response (``{"error": ...}``) rather than raised, so MCP clients can
surface actionable messages without the server crashing mid-call.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from . import admin, agents, org, probes, skills


SERVER_INSTRUCTIONS = """\
SfSkills — Salesforce skill library + live-org metadata + run-time agents over MCP.

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


def build_server() -> FastMCP:
    mcp = FastMCP("sfskills", instructions=SERVER_INSTRUCTIONS)

    @mcp.tool(
        name="search_skill",
        description=(
            "Lexical search over the SfSkills library (686+ Salesforce skills "
            "spanning admin, apex, flow, lwc, integration, security, data, "
            "architect, devops, omnistudio, agentforce). Returns ranked skill "
            "ids plus top matching chunks. Use this before proposing a pattern."
        ),
    )
    def search_skill(query: str, domain: str | None = None, limit: int = 10) -> dict[str, Any]:
        return skills.search_skill(query=query, domain=domain, limit=limit)

    @mcp.tool(
        name="get_skill",
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
        description=(
            "List Approval ProcessDefinitions, optionally filtered by object. "
            "By default returns only active approvals. Source of truth for "
            "approval-to-flow-orchestrator-migrator."
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
        description=(
            "Escape-hatch read-only SOQL against the Tooling or REST API. "
            "Refuses any statement that is not a SELECT or that contains DML "
            "keywords / semicolons. Applies an automatic LIMIT if missing. "
            "Prefer the specialized list_* tools where they exist."
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
        description=(
            "Enumerate Apex classes and triggers referencing an "
            "<object>.<field>. Uses word-boundary regex on fetched bodies to "
            "filter substring false positives. Classifies each hit as "
            "read/write/unknown. Primary consumer: field-impact-analyzer."
        ),
    )
    def probe_apex_references(
        object_name: str,
        field: str,
        target_org: str | None = None,
        include_managed: bool = False,
        limit_per_query: int = 200,
    ) -> dict[str, Any]:
        return probes.probe_apex_references(
            object_name=object_name,
            field=field,
            target_org=target_org,
            include_managed=include_managed,
            limit_per_query=limit_per_query,
        )

    @mcp.tool(
        name="probe_flow_references",
        description=(
            "Enumerate active Flow versions whose metadata XML references "
            "<object>.<field>. Classifies each hit as read (lookup/"
            "condition context) or write (recordCreates / recordUpdates / "
            "assignToReference). Strips <description>/<label> text to avoid "
            "label-based false positives."
        ),
    )
    def probe_flow_references(
        object_name: str,
        field: str,
        target_org: str | None = None,
        active_only: bool = True,
        limit: int = 200,
    ) -> dict[str, Any]:
        return probes.probe_flow_references(
            object_name=object_name,
            field=field,
            target_org=target_org,
            active_only=active_only,
            limit=limit,
        )

    @mcp.tool(
        name="probe_matching_rules",
        description=(
            "List MatchingRule + DuplicateRule records on an sObject with "
            "their field items. Computes overlaps[] (pairs of active "
            "matching rules sharing >= 1 field — a P0 duplicate-management "
            "smell). Primary consumer: duplicate-rule-designer."
        ),
    )
    def probe_matching_rules(
        object_name: str,
        target_org: str | None = None,
        active_only: bool = False,
    ) -> dict[str, Any]:
        return probes.probe_matching_rules(
            object_name=object_name,
            target_org=target_org,
            active_only=active_only,
        )

    @mcp.tool(
        name="probe_permset_shape",
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
        description=(
            "List SfSkills run-time agents available to the caller. These are "
            "instruction files (AGENT.md) that tell an LLM how to compose the "
            "skill library, templates, decision-trees, and live-org tools into "
            "a concrete deliverable (refactor, audit, migration plan, etc.). "
            "Pass kind='runtime' for user-facing agents, kind='build' for the "
            "skill-factory agents, or leave unset for all."
        ),
    )
    def list_agents(kind: str | None = None) -> dict[str, Any]:
        return agents.list_agents(kind=kind)

    @mcp.tool(
        name="get_agent",
        description=(
            "Fetch the full AGENT.md body for a named agent (e.g. "
            "'apex-refactorer', 'security-scanner', 'deployment-risk-scorer'). "
            "Returns the markdown instructions plus metadata. The caller's LLM "
            "executes the agent; the MCP server only surfaces the instructions."
        ),
    )
    def get_agent(agent_name: str) -> dict[str, Any]:
        return agents.get_agent(agent_name=agent_name)

    return mcp


def run(transport: str = "stdio") -> None:
    """Entry point used by ``python -m sfskills_mcp`` and the console script."""
    build_server().run(transport=transport)
