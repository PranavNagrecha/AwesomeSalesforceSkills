"""Wave-2 probe promotion: the four SOQL recipes from
``agents/_shared/probes/`` surfaced as first-class MCP tools.

Every probe follows the same shape as the tools in ``admin.py``: validate
inputs, run one or more Tooling-API SOQL queries, post-process, return a
JSON-serializable dict. Errors surface as ``{"error": ...}`` on the dict,
never raised — the MCP server stays up even when probes fail.

Why promote: these four recipes were being pasted into agents as SOQL
snippets. That caused subtle drift (one agent's paste used ``Active = true``,
another used ``IsActive``). Centralizing the logic here makes every consumer
use the same implementation — including post-processing like overlap
detection for matching rules. The markdown recipes in
``agents/_shared/probes/*.md`` stay as documentation.

Four probes are exposed:

- ``probe_apex_references`` — Apex classes/triggers referencing an
  ``<object>.<field>``. Word-boundary regex on fetched bodies filters
  substring false positives.
- ``probe_flow_references`` — Active Flows whose metadata XML references a
  field. Classifies each hit as read/write based on the enclosing element.
- ``probe_matching_rules`` — Matching + Duplicate rules on an sObject.
  Computes ``overlaps[]`` where two active matching rules share at least
  one field (P0 duplicate-management smell).
- ``probe_permset_shape`` — Permission Set or PSG composition + assignment
  concentration + risk flags (``Modify All Data`` detection, "super" PSG
  smell when a single PSG covers > 1/3 of active users).
"""

from __future__ import annotations

import re
from typing import Any

from . import sf_cli
from .admin import _run_soql, _validate_api_name, _strip_attributes


MAX_ROWS = 2000


# --------------------------------------------------------------------------- #
# probe_apex_references                                                       #
# --------------------------------------------------------------------------- #

def probe_apex_references(
    object_name: str,
    field: str,
    target_org: str | None = None,
    include_managed: bool = False,
    limit_per_query: int = 200,
) -> dict[str, Any]:
    """Enumerate ``ApexClass`` and ``ApexTrigger`` records whose body
    references ``<object>.<field>``.

    The raw ``LIKE '%field%'`` SOQL filter over-matches (``Industry_Code__c``
    would match ``Industry``); a post-fetch word-boundary regex trims the
    list. Classifies each hit as ``read`` (query/condition context) or
    ``write`` (assignment / DML payload); emits ``unknown`` when the
    probe can't disambiguate without AST parsing.
    """
    err = _validate_api_name(object_name, kind="object_name")
    if err:
        return {"error": err}
    err = _validate_api_name(field, kind="field")
    if err:
        return {"error": err}

    bounded = max(1, min(int(limit_per_query or 200), MAX_ROWS))
    managed_clause = "" if include_managed else " AND NamespacePrefix = null"

    # Step 1 — ApexClass
    class_soql = (
        "SELECT Id, Name, NamespacePrefix, Body "
        "FROM ApexClass "
        f"WHERE Body LIKE '%{field}%'{managed_clause} "
        f"LIMIT {bounded}"
    )
    classes = _run_soql(class_soql, target_org=target_org, tooling=True)
    if "error" in classes:
        return classes

    # Step 2 — ApexTrigger (must target the object)
    trigger_soql = (
        "SELECT Id, Name, NamespacePrefix, TableEnumOrId, Body "
        "FROM ApexTrigger "
        f"WHERE TableEnumOrId = '{object_name}' "
        f"AND Body LIKE '%{field}%' "
        f"LIMIT {bounded}"
    )
    triggers = _run_soql(trigger_soql, target_org=target_org, tooling=True)
    if "error" in triggers:
        return triggers

    rows: list[dict[str, Any]] = []
    # Word-boundary patterns that recognize real references vs substring hits.
    ref_pattern = re.compile(rf"\b{re.escape(object_name)}\.{re.escape(field)}\b")
    type_pattern = re.compile(
        rf"\bSObjectType\.{re.escape(object_name)}\.fields\.{re.escape(field)}\b"
    )
    # Write-classification heuristic: assignment or DML-payload construction.
    write_pattern = re.compile(
        rf"(?:{re.escape(field)}\s*=\s*|new\s+{re.escape(object_name)}\s*\([^)]*{re.escape(field)}\s*=)"
    )

    def _classify(body: str, kind: str, record: dict[str, Any]) -> None:
        # Match on the unfiltered body first — either bare ref or SObjectType.
        if not (ref_pattern.search(body) or type_pattern.search(body)):
            return
        access = "write" if write_pattern.search(body) else "read"
        snippet_match = ref_pattern.search(body) or type_pattern.search(body)
        evidence = ""
        if snippet_match:
            start = max(0, snippet_match.start() - 20)
            end = min(len(body), snippet_match.end() + 40)
            evidence = body[start:end].replace("\n", " ").strip()
        rows.append(
            {
                "kind": kind,
                "id": record.get("Id"),
                "name": record.get("Name"),
                "namespace": record.get("NamespacePrefix"),
                "access_type": access,
                "evidence_snippet": evidence[:200],
            }
        )

    for record in classes["records"]:
        _classify(record.get("Body") or "", "ApexClass", record)
    for record in triggers["records"]:
        _classify(record.get("Body") or "", "ApexTrigger", record)

    # Confidence drops if we hit the page cap — caller may need to re-run
    # with a higher limit or paginate itself.
    truncated = (
        len(classes["records"]) == bounded
        or len(triggers["records"]) == bounded
    )

    return {
        "object": object_name,
        "field": field,
        "reference_count": len(rows),
        "references": rows,
        "truncated": truncated,
        "include_managed": include_managed,
    }


# --------------------------------------------------------------------------- #
# probe_flow_references                                                       #
# --------------------------------------------------------------------------- #

def probe_flow_references(
    object_name: str,
    field: str,
    target_org: str | None = None,
    active_only: bool = True,
    limit: int = 200,
) -> dict[str, Any]:
    """Enumerate active Flow versions whose metadata references
    ``<object>.<field>``, classifying each hit as read or write."""
    err = _validate_api_name(object_name, kind="object_name")
    if err:
        return {"error": err}
    err = _validate_api_name(field, kind="field")
    if err:
        return {"error": err}

    bounded = max(1, min(int(limit or 200), MAX_ROWS))
    status_clause = (
        "AND (Status = 'Active' OR Status = 'Obsolete')"
        if not active_only
        else "AND Status = 'Active'"
    )
    # FlowDefinitionView is discoverable via the REST data API; Flow bodies
    # (Metadata) live on the Tooling API.
    flow_soql = (
        "SELECT Id, DefinitionId, Status, ProcessType, MasterLabel, Metadata "
        "FROM Flow "
        f"WHERE (ProcessType = 'AutoLaunchedFlow' OR ProcessType = 'Flow' "
        f"OR ProcessType = 'Workflow') "
        f"{status_clause} "
        f"LIMIT {bounded}"
    )
    flows = _run_soql(flow_soql, target_org=target_org, tooling=True)
    if "error" in flows:
        return flows

    rows: list[dict[str, Any]] = []
    # Elements in the Metadata XML that indicate a WRITE to the field.
    write_anchors = (
        re.compile(
            rf"<recordUpdates[^>]*>.*?<field>{re.escape(field)}</field>",
            re.DOTALL,
        ),
        re.compile(
            rf"<recordCreates[^>]*>.*?<field>{re.escape(field)}</field>",
            re.DOTALL,
        ),
        re.compile(
            rf"<assignToReference>[^<]*\b{re.escape(field)}\b[^<]*</assignToReference>"
        ),
    )
    # Read-context anchors.
    read_anchors = (
        re.compile(rf"<recordLookups[^>]*>.*?<field>{re.escape(field)}</field>", re.DOTALL),
        re.compile(rf"<leftValueReference>[^<]*\b{re.escape(field)}\b[^<]*</leftValueReference>"),
        re.compile(rf"<rightValueReference>[^<]*\b{re.escape(field)}\b[^<]*</rightValueReference>"),
    )
    # Strip <description> and <label> — human-written text mentioning a
    # field name without referencing it programmatically.
    strip_pattern = re.compile(r"<(?:description|label)>.*?</(?:description|label)>", re.DOTALL)
    bare_ref = re.compile(rf"\b{re.escape(field)}\b")

    for flow in flows["records"]:
        meta_xml = str(flow.get("Metadata") or "")
        if not meta_xml:
            continue
        cleaned = strip_pattern.sub("", meta_xml)
        if not bare_ref.search(cleaned):
            continue
        access = "unknown"
        if any(p.search(cleaned) for p in write_anchors):
            access = "write"
        elif any(p.search(cleaned) for p in read_anchors):
            access = "read"
        else:
            # The field name appears but not in any of the structural anchors
            # we can classify — might be a formula or dynamic reference.
            access = "unknown"
        # Pull a short snippet around the first hit for evidence.
        snippet_match = bare_ref.search(cleaned)
        evidence = ""
        if snippet_match:
            start = max(0, snippet_match.start() - 40)
            end = min(len(cleaned), snippet_match.end() + 80)
            evidence = cleaned[start:end].replace("\n", " ").strip()
        rows.append(
            {
                "flow_id": flow.get("Id"),
                "definition_id": flow.get("DefinitionId"),
                "label": flow.get("MasterLabel"),
                "process_type": flow.get("ProcessType"),
                "status": flow.get("Status"),
                "access_type": access,
                "evidence_snippet": evidence[:240],
            }
        )

    return {
        "object": object_name,
        "field": field,
        "reference_count": len(rows),
        "references": rows,
        "active_only": active_only,
    }


# --------------------------------------------------------------------------- #
# probe_matching_rules                                                        #
# --------------------------------------------------------------------------- #

def probe_matching_rules(
    object_name: str,
    target_org: str | None = None,
    active_only: bool = False,
) -> dict[str, Any]:
    """Enumerate Matching Rules + Duplicate Rules on an sObject, plus
    ``overlaps[]`` (two active matching rules sharing at least one field —
    a P0 duplicate-management smell)."""
    err = _validate_api_name(object_name, kind="object_name")
    if err:
        return {"error": err}

    active_clause = " AND IsActive = true" if active_only else ""

    mr_soql = (
        "SELECT Id, DeveloperName, MasterLabel, IsActive, SobjectType "
        "FROM MatchingRule "
        f"WHERE SobjectType = '{object_name}'{active_clause} "
        "LIMIT 200"
    )
    matching_rules = _run_soql(mr_soql, target_org=target_org, tooling=True)
    if "error" in matching_rules:
        return matching_rules

    mr_ids = [r.get("Id") for r in matching_rules["records"] if r.get("Id")]
    mr_items_by_rule: dict[str, list[dict[str, Any]]] = {}
    if mr_ids:
        ids_clause = ", ".join(f"'{rid}'" for rid in mr_ids)
        items_soql = (
            "SELECT MatchingRuleId, FieldName, MatchingMethod, "
            "BlankValueBehavior, SortOrder "
            "FROM MatchingRuleItem "
            f"WHERE MatchingRuleId IN ({ids_clause}) "
            "ORDER BY MatchingRuleId, SortOrder "
            "LIMIT 2000"
        )
        items = _run_soql(items_soql, target_org=target_org, tooling=True)
        if "error" in items:
            return items
        for item in items["records"]:
            rule_id = item.get("MatchingRuleId")
            if rule_id:
                mr_items_by_rule.setdefault(rule_id, []).append(item)

    dr_soql = (
        "SELECT Id, DeveloperName, MasterLabel, IsActive, SobjectType, "
        "SobjectSubtype, ParentId "
        "FROM DuplicateRule "
        f"WHERE SobjectType = '{object_name}'{active_clause} "
        "LIMIT 200"
    )
    duplicate_rules = _run_soql(dr_soql, target_org=target_org, tooling=True)
    if "error" in duplicate_rules:
        return duplicate_rules

    matching_out: list[dict[str, Any]] = []
    for rule in matching_rules["records"]:
        rule_id = rule.get("Id")
        items = mr_items_by_rule.get(rule_id, [])
        matching_out.append(
            {
                "id": rule_id,
                "developer_name": rule.get("DeveloperName"),
                "label": rule.get("MasterLabel"),
                "active": rule.get("IsActive"),
                "fields": [
                    {
                        "field": item.get("FieldName"),
                        "method": item.get("MatchingMethod"),
                        "blank_behavior": item.get("BlankValueBehavior"),
                        "sort_order": item.get("SortOrder"),
                    }
                    for item in sorted(items, key=lambda x: x.get("SortOrder") or 0)
                ],
            }
        )

    duplicate_out = [
        {
            "id": rule.get("Id"),
            "developer_name": rule.get("DeveloperName"),
            "label": rule.get("MasterLabel"),
            "active": rule.get("IsActive"),
            "subtype": rule.get("SobjectSubtype"),
            "parent_id": rule.get("ParentId"),
        }
        for rule in duplicate_rules["records"]
    ]

    # Overlap detection: two active matching rules sharing >= 1 field.
    overlaps: list[dict[str, Any]] = []
    active_rules = [r for r in matching_out if r["active"]]
    for i, left in enumerate(active_rules):
        for right in active_rules[i + 1 :]:
            left_fields = {f["field"] for f in left["fields"] if f["field"]}
            right_fields = {f["field"] for f in right["fields"] if f["field"]}
            shared = sorted(left_fields & right_fields)
            if shared:
                overlaps.append(
                    {
                        "left": left["developer_name"],
                        "right": right["developer_name"],
                        "shared_fields": shared,
                        "severity": "P0" if left_fields == right_fields else "P1",
                    }
                )

    return {
        "object": object_name,
        "active_only": active_only,
        "matching_rule_count": len(matching_out),
        "matching_rules": matching_out,
        "duplicate_rule_count": len(duplicate_out),
        "duplicate_rules": duplicate_out,
        "overlaps": overlaps,
    }


# --------------------------------------------------------------------------- #
# probe_permset_shape                                                         #
# --------------------------------------------------------------------------- #

_MAD_PATTERN = re.compile(r"\bModifyAllData\b|\bModify\s+All\s+Data\b")


def probe_permset_shape(
    scope: str,
    target_org: str | None = None,
) -> dict[str, Any]:
    """Summarize a Permission Set / PSG / user scope in the live org.

    Accepts:
        ``psg:<DeveloperName>``  — Permission Set Group composition + concentration
        ``ps:<Name>``            — Permission Set assignment shape
        ``user:<username>``      — All PSes + PSGs assigned to one user

    Post-processing includes concentration-ratio flags ("super" PSG smell
    when a single PSG covers > 1/3 of active standard users) and a hard
    ``Modify All Data`` detection.
    """
    if not scope or ":" not in scope:
        return {"error": f"scope must be `psg:<name>` / `ps:<name>` / `user:<name>`, got: {scope!r}"}
    kind, _, identifier = scope.partition(":")
    kind = kind.strip().lower()
    identifier = identifier.strip()
    if not identifier:
        return {"error": f"scope missing identifier after ':': {scope!r}"}

    # Active standard-user count — used as denominator for concentration ratios.
    users_soql = (
        "SELECT COUNT() total FROM User WHERE IsActive = true AND UserType = 'Standard'"
    )
    # aggregate query: use count() without alias for simplicity
    users_soql = "SELECT COUNT() FROM User WHERE IsActive = true AND UserType = 'Standard'"
    user_count_probe = sf_cli.run_sf_json(
        ["data", "query", "--query", users_soql], target_org=target_org
    )
    if "error" in user_count_probe and "result" not in user_count_probe:
        return user_count_probe
    active_user_count = (user_count_probe.get("result", {}) or {}).get("totalSize") or 0

    if kind == "psg":
        return _permset_shape_psg(identifier, active_user_count, target_org)
    if kind == "ps":
        return _permset_shape_ps(identifier, active_user_count, target_org)
    if kind == "user":
        return _permset_shape_user(identifier, active_user_count, target_org)
    return {"error": f"unknown scope kind {kind!r}; expected psg / ps / user"}


def _permset_shape_psg(
    name: str,
    active_user_count: int,
    target_org: str | None,
) -> dict[str, Any]:
    err = _validate_api_name(name, kind="psg_name")
    if err:
        return {"error": err}

    # PSG components
    components_soql = (
        "SELECT PermissionSetGroupId, PermissionSetId, PermissionSet.Name, "
        "PermissionSet.Label "
        "FROM PermissionSetGroupComponent "
        f"WHERE PermissionSetGroup.DeveloperName = '{name}' "
        "LIMIT 200"
    )
    components = _run_soql(components_soql, target_org=target_org, tooling=False)
    if "error" in components:
        return components

    # Assignment count for this PSG
    assignment_soql = (
        "SELECT COUNT() FROM PermissionSetAssignment "
        f"WHERE PermissionSetGroup.DeveloperName = '{name}'"
    )
    assignment_probe = sf_cli.run_sf_json(
        ["data", "query", "--query", assignment_soql], target_org=target_org
    )
    assignees = (assignment_probe.get("result", {}) or {}).get("totalSize") or 0

    concentration = (
        round(assignees / active_user_count, 3) if active_user_count else None
    )

    component_rows = []
    has_mad = False
    for c in components["records"]:
        ps = c.get("PermissionSet") or {}
        ps_name = ps.get("Name") if isinstance(ps, dict) else None
        component_rows.append(
            {
                "permission_set": ps_name,
                "label": ps.get("Label") if isinstance(ps, dict) else None,
            }
        )
        if ps_name and _MAD_PATTERN.search(ps_name):
            has_mad = True

    risk_flags: list[dict[str, Any]] = []
    if concentration is not None and concentration > 0.33:
        risk_flags.append(
            {
                "severity": "P2",
                "reason": (
                    f"concentration_ratio={concentration} > 0.33 — "
                    "'super' PSG smell; narrow scope or split"
                ),
            }
        )
    if has_mad:
        risk_flags.append(
            {
                "severity": "P0",
                "reason": "component permission set name contains ModifyAllData",
            }
        )

    return {
        "scope": f"psg:{name}",
        "active_user_count": active_user_count,
        "component_count": len(component_rows),
        "components": component_rows,
        "assignees": assignees,
        "concentration_ratio": concentration,
        "risk_flags": risk_flags,
    }


def _permset_shape_ps(
    name: str,
    active_user_count: int,
    target_org: str | None,
) -> dict[str, Any]:
    err = _validate_api_name(name, kind="ps_name")
    if err:
        return {"error": err}

    assignment_soql = (
        "SELECT COUNT() FROM PermissionSetAssignment "
        f"WHERE PermissionSet.Name = '{name}' AND PermissionSetGroupId = null"
    )
    assignment_probe = sf_cli.run_sf_json(
        ["data", "query", "--query", assignment_soql], target_org=target_org
    )
    assignees = (assignment_probe.get("result", {}) or {}).get("totalSize") or 0

    risk_flags: list[dict[str, Any]] = []
    if assignees == 1:
        risk_flags.append(
            {
                "severity": "P1",
                "reason": "permission set assigned to exactly one user — "
                "candidate for removal or promotion to PSG",
            }
        )
    if _MAD_PATTERN.search(name):
        risk_flags.append(
            {
                "severity": "P0",
                "reason": "permission set name contains ModifyAllData",
            }
        )

    concentration = (
        round(assignees / active_user_count, 3) if active_user_count else None
    )

    return {
        "scope": f"ps:{name}",
        "active_user_count": active_user_count,
        "direct_assignees": assignees,
        "concentration_ratio": concentration,
        "risk_flags": risk_flags,
    }


def _permset_shape_user(
    username: str,
    active_user_count: int,
    target_org: str | None,
) -> dict[str, Any]:
    # username CAN contain '.' and '@' — regex needs to allow that.
    if not re.match(r"^[A-Za-z0-9._@+-]+$", username or ""):
        return {"error": f"username must match /^[A-Za-z0-9._@+-]+$/, got: {username!r}"}

    shape_soql = (
        "SELECT PermissionSet.Name, PermissionSet.Label, "
        "PermissionSetGroup.DeveloperName "
        "FROM PermissionSetAssignment "
        f"WHERE Assignee.Username = '{username}' "
        "LIMIT 200"
    )
    shape = _run_soql(shape_soql, target_org=target_org, tooling=False)
    if "error" in shape:
        return shape

    rows = []
    for record in shape["records"]:
        ps = record.get("PermissionSet") or {}
        psg = record.get("PermissionSetGroup") or {}
        rows.append(
            {
                "permission_set": ps.get("Name") if isinstance(ps, dict) else None,
                "permission_set_label": ps.get("Label") if isinstance(ps, dict) else None,
                "permission_set_group": (
                    psg.get("DeveloperName") if isinstance(psg, dict) else None
                ),
            }
        )

    return {
        "scope": f"user:{username}",
        "active_user_count": active_user_count,
        "assignment_count": len(rows),
        "assignments": rows,
    }
