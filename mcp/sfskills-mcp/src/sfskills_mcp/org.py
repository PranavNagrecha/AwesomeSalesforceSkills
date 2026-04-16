"""Live-org tools for the SfSkills MCP server.

Implemented on top of the Salesforce CLI (``sf``) so we inherit the user's
existing auth store — no secrets are handled in-process. Each tool returns a
structured dict; failures surface as ``{"error": ...}`` rather than raising.

Tools:

- ``describe_org`` — summary of the target org (id, instance, edition, user).
- ``list_custom_objects`` — custom sObjects with labels, optionally filtered.
- ``list_flows_on_object`` — Flow metadata rows targeting the given sObject.
- ``validate_against_org`` — category-aware probe that answers questions like
  "does a trigger framework already exist in my org?".
"""

from __future__ import annotations

from typing import Any

from . import sf_cli
from .skills import _registry_by_id, _normalize_skill_id


MAX_CUSTOM_OBJECTS = 2000
MAX_FLOW_ROWS = 200
MAX_APEX_CLASS_ROWS = 200


# --------------------------------------------------------------------------- #
# describe_org                                                                #
# --------------------------------------------------------------------------- #


def describe_org(target_org: str | None = None) -> dict[str, Any]:
    """Return a concise summary of the target Salesforce org.

    Uses ``sf org display --json`` (and ``sf org list --json`` to hint at
    available aliases when no target is set).
    """
    payload = sf_cli.run_sf_json(["org", "display"], target_org=target_org)
    if "error" in payload and "result" not in payload:
        hint = _available_orgs_hint()
        return {**payload, **({"available_orgs": hint} if hint else {})}

    result = payload.get("result", payload)
    summary = {
        "username": result.get("username"),
        "org_id": result.get("id"),
        "instance_url": result.get("instanceUrl"),
        "alias": result.get("alias"),
        "api_version": result.get("apiVersion"),
        "edition": result.get("edition"),
        "instance_name": result.get("instanceName"),
        "is_scratch_org": result.get("isScratchOrg"),
        "is_sandbox": result.get("isSandbox"),
        "connected_status": result.get("connectedStatus"),
        "access_token_preview": _redact_token(result.get("accessToken")),
    }
    return {k: v for k, v in summary.items() if v is not None}


def _available_orgs_hint() -> list[dict[str, Any]]:
    payload = sf_cli.run_sf_json(["org", "list"])
    if "error" in payload and "result" not in payload:
        return []
    result = payload.get("result", {})
    hints: list[dict[str, Any]] = []
    for bucket in ("nonScratchOrgs", "scratchOrgs", "devHubs", "sandboxes"):
        for entry in result.get(bucket, []) or []:
            hints.append(
                {
                    "alias": entry.get("alias"),
                    "username": entry.get("username"),
                    "instance_url": entry.get("instanceUrl"),
                    "is_default_username": entry.get("isDefaultUsername"),
                    "bucket": bucket,
                }
            )
    return hints


def _redact_token(token: Any) -> str | None:
    if not isinstance(token, str) or not token:
        return None
    return f"{token[:6]}\u2026{token[-4:]}" if len(token) > 12 else "***"


# --------------------------------------------------------------------------- #
# list_custom_objects                                                         #
# --------------------------------------------------------------------------- #


def list_custom_objects(
    target_org: str | None = None,
    name_filter: str | None = None,
    include_standard: bool = False,
    limit: int = 500,
) -> dict[str, Any]:
    """List custom (``__c``) sObjects in the org, optionally filtered by name.

    ``name_filter`` performs a case-insensitive substring match against the
    API name and label.
    """
    bounded = max(1, min(int(limit or 500), MAX_CUSTOM_OBJECTS))

    args = ["sobject", "list"]
    if not include_standard:
        args.extend(["--sobject", "custom"])
    payload = sf_cli.run_sf_json(args, target_org=target_org)

    if "error" in payload and "result" not in payload:
        return payload

    result = payload.get("result", [])
    names = result if isinstance(result, list) else []

    filtered: list[str] = []
    needle = (name_filter or "").strip().lower()
    for name in names:
        if not isinstance(name, str):
            continue
        if needle and needle not in name.lower():
            continue
        filtered.append(name)
        if len(filtered) >= bounded:
            break

    return {
        "object_count": len(filtered),
        "truncated": len(names) > bounded and not name_filter,
        "objects": [{"api_name": name} for name in filtered],
    }


# --------------------------------------------------------------------------- #
# list_flows_on_object                                                        #
# --------------------------------------------------------------------------- #


_FLOW_SOQL = (
    "SELECT Id, DeveloperName, ApiVersion, ProcessType, TriggerType, "
    "TriggerObjectOrEvent.QualifiedApiName, Status, LastModifiedDate, "
    "Description "
    "FROM Flow "
    "WHERE TriggerObjectOrEvent.QualifiedApiName = '{obj}' "
    "ORDER BY LastModifiedDate DESC "
    "LIMIT {limit}"
)


def list_flows_on_object(
    object_name: str,
    target_org: str | None = None,
    active_only: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    """List Flows whose trigger target is ``object_name`` (e.g. ``Account``).

    Uses the Tooling API via ``sf data query --use-tooling-api``. The Flow
    metadata returned includes record-triggered flows, scheduled-triggered
    flows, and platform-event-triggered flows.
    """
    obj = (object_name or "").strip()
    if not obj.replace("_", "").isalnum():
        return {"error": "object_name must be a single sObject API name (e.g. 'Account' or 'My_Obj__c')."}

    bounded = max(1, min(int(limit or 50), MAX_FLOW_ROWS))
    soql = _FLOW_SOQL.format(obj=obj, limit=bounded)

    payload = sf_cli.run_sf_json(
        ["data", "query", "--use-tooling-api", "--query", soql],
        target_org=target_org,
    )
    if "error" in payload and "result" not in payload:
        return payload

    records = (payload.get("result", {}) or {}).get("records", []) or []
    rows: list[dict[str, Any]] = []
    for record in records:
        status = record.get("Status")
        if active_only and status != "Active":
            continue
        trigger_object = (record.get("TriggerObjectOrEvent") or {}).get("QualifiedApiName") if isinstance(
            record.get("TriggerObjectOrEvent"), dict
        ) else None
        rows.append(
            {
                "id": record.get("Id"),
                "developer_name": record.get("DeveloperName"),
                "process_type": record.get("ProcessType"),
                "trigger_type": record.get("TriggerType"),
                "trigger_object": trigger_object,
                "status": status,
                "api_version": record.get("ApiVersion"),
                "last_modified": record.get("LastModifiedDate"),
                "description": record.get("Description"),
            }
        )

    return {
        "object": obj,
        "flow_count": len(rows),
        "active_only": active_only,
        "flows": rows,
    }


# --------------------------------------------------------------------------- #
# validate_against_org                                                        #
# --------------------------------------------------------------------------- #


_CATEGORY_TO_PROBES = {
    "apex": ("apex_handler_classes",),
    "flow": ("flows_for_object",),
    "integration": ("named_credentials", "remote_sites"),
    "security": ("permission_sets",),
    "data": ("object_presence",),
    "architect": ("object_presence", "apex_handler_classes"),
    "devops": ("apex_handler_classes",),
    "admin": ("object_presence",),
    "lwc": ("lwc_components",),
    "omnistudio": ("apex_handler_classes",),
    "agentforce": ("flows_for_object",),
}


def validate_against_org(
    skill_id: str,
    target_org: str | None = None,
    object_name: str | None = None,
) -> dict[str, Any]:
    """Answer "does the guidance in this skill already have analogs in my org?".

    Routes based on the skill's ``category``:

    - apex / devops / omnistudio → look for matching handler/service classes.
    - flow / agentforce → list Flows targeting ``object_name`` (required).
    - integration → list Named Credentials + Remote Site Settings.
    - security → list Permission Sets.
    - data / admin / architect → confirm ``object_name`` exists + any handler classes.
    - lwc → list deployed LWC components.

    Returns structured probe output; the MCP client (and the human reviewing
    it) decides what to do with the evidence.
    """
    normalized = _normalize_skill_id(skill_id)
    record = _registry_by_id().get(normalized)
    if record is None:
        return {"error": f"skill not found: {normalized}"}

    category = (record.get("category") or "").lower()
    probe_names = _CATEGORY_TO_PROBES.get(category, ("object_presence",))

    probes: dict[str, Any] = {}
    for probe_name in probe_names:
        probes[probe_name] = _run_probe(probe_name, target_org=target_org, object_name=object_name)

    return {
        "skill_id": normalized,
        "category": category,
        "target_org": target_org,
        "object_name": object_name,
        "probes": probes,
        "summary": _summarize_probes(probes),
    }


def _run_probe(name: str, *, target_org: str | None, object_name: str | None) -> dict[str, Any]:
    if name == "apex_handler_classes":
        return _probe_apex_handler_classes(target_org)
    if name == "flows_for_object":
        if not object_name:
            return {"skipped": "object_name is required for flows_for_object probe"}
        return list_flows_on_object(object_name, target_org=target_org)
    if name == "named_credentials":
        return _probe_soql(
            target_org,
            "SELECT DeveloperName, Endpoint, PrincipalType FROM NamedCredential LIMIT 200",
            tooling=False,
        )
    if name == "remote_sites":
        return _probe_soql(
            target_org,
            "SELECT DeveloperName, EndpointUrl, IsActive FROM RemoteProxy LIMIT 200",
            tooling=True,
        )
    if name == "permission_sets":
        return _probe_soql(
            target_org,
            "SELECT Name, Label, IsOwnedByProfile, IsCustom FROM PermissionSet "
            "WHERE IsOwnedByProfile = false ORDER BY Name LIMIT 200",
            tooling=False,
        )
    if name == "object_presence":
        if not object_name:
            return {"skipped": "object_name is required for object_presence probe"}
        payload = sf_cli.run_sf_json(
            ["sobject", "describe", "--sobject", object_name],
            target_org=target_org,
        )
        if "error" in payload and "result" not in payload:
            return {"present": False, **payload}
        result = payload.get("result", payload)
        return {
            "present": True,
            "api_name": result.get("name"),
            "label": result.get("label"),
            "custom": result.get("custom"),
            "queryable": result.get("queryable"),
            "createable": result.get("createable"),
        }
    if name == "lwc_components":
        return _probe_soql(
            target_org,
            "SELECT MasterLabel, DeveloperName, NamespacePrefix, ApiVersion "
            "FROM LightningComponentBundle ORDER BY DeveloperName LIMIT 200",
            tooling=True,
        )
    return {"skipped": f"unknown probe: {name}"}


def _probe_apex_handler_classes(target_org: str | None) -> dict[str, Any]:
    soql = (
        "SELECT Id, Name, ApiVersion, Status, NamespacePrefix "
        "FROM ApexClass "
        "WHERE Name LIKE '%TriggerHandler%' "
        "   OR Name LIKE '%Trigger_Handler%' "
        "   OR Name LIKE '%Handler' "
        f"LIMIT {MAX_APEX_CLASS_ROWS}"
    )
    return _probe_soql(target_org, soql, tooling=True)


def _probe_soql(target_org: str | None, soql: str, *, tooling: bool) -> dict[str, Any]:
    args = ["data", "query", "--query", soql]
    if tooling:
        args.append("--use-tooling-api")
    payload = sf_cli.run_sf_json(args, target_org=target_org)
    if "error" in payload and "result" not in payload:
        return payload
    records = (payload.get("result", {}) or {}).get("records", []) or []
    for record in records:
        record.pop("attributes", None)
    return {
        "record_count": len(records),
        "records": records,
    }


def _summarize_probes(probes: dict[str, Any]) -> dict[str, Any]:
    hits: dict[str, int] = {}
    notes: list[str] = []
    for name, probe in probes.items():
        if not isinstance(probe, dict):
            continue
        if "skipped" in probe:
            notes.append(f"{name}: {probe['skipped']}")
            continue
        if "error" in probe:
            notes.append(f"{name}: {probe['error']}")
            continue
        count = (
            probe.get("record_count")
            or probe.get("flow_count")
            or probe.get("object_count")
            or (1 if probe.get("present") else 0)
        )
        hits[name] = int(count or 0)
    return {"hit_counts": hits, "notes": notes}
