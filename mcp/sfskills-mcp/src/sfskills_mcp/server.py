"""FastMCP server exposing SfSkills + live-org + agent tools.

Run with ``python -m sfskills_mcp`` (stdio transport). The server registers
eight tools:

- ``search_skill``
- ``get_skill``
- ``describe_org``
- ``list_custom_objects``
- ``list_flows_on_object``
- ``validate_against_org``
- ``list_agents``
- ``get_agent``

Each tool returns JSON-serializable dicts. Errors are returned as fields on
the response (``{"error": ...}``) rather than raised, so MCP clients can
surface actionable messages without the server crashing mid-call.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from . import agents, org, skills


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
