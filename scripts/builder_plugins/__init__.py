"""builder_plugins — per-agent Gate C / inventory / grounding plugins.

Each builder agent registers a plugin implementing the BuilderPlugin protocol
in base.py. run_builder.py uses get_plugin(agent) to look up the right
plugin for the agent under validation.

To add a new builder:
    1. Create <agent>.py here with a class subclassing BuilderPlugin.
    2. Register it in REGISTRY below.
    3. Author agents/<agent>/inputs.schema.json, GATES.md, REQUIREMENTS_TEMPLATE.md.
    4. Add at least one live-green + negative-input + negative-bad-output fixture.

The harness never hard-codes Apex/LWC/Flow behavior; the plugin owns it.
"""

from __future__ import annotations

from typing import Any

from .base import BuilderPlugin, LiveCheckResult

__all__ = ["BuilderPlugin", "LiveCheckResult", "get_plugin"]


def get_plugin(agent: str) -> BuilderPlugin:
    """Return the plugin for this agent, or raise KeyError."""
    # Import lazily to avoid loading every plugin's transitive deps on every run.
    if agent == "apex-builder":
        from .apex import ApexBuilderPlugin
        return ApexBuilderPlugin()
    if agent == "lwc-builder":
        from .lwc import LwcBuilderPlugin
        return LwcBuilderPlugin()
    if agent == "flow-builder":
        from .flow import FlowBuilderPlugin
        return FlowBuilderPlugin()
    raise KeyError(f"no builder plugin registered for agent={agent!r}")
