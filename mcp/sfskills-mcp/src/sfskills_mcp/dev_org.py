"""Developer-tier live-org tools.

Closes the gap the prototype had where the developer agents (apex-refactorer,
trigger-consolidator, code-reviewer, lwc-auditor, lwc-builder, lwc-debugger,
deployment-risk-scorer) had to fall back to ``tooling_query`` to inspect
basic Apex / LWC inventory. Eight first-class tools here, all read-only,
all routing through the existing ``_run_soql`` helper.

Tools:

- ``list_apex_classes``      — Apex class inventory + name filter
- ``get_apex_class``         — single class with optional body
- ``list_apex_triggers``     — trigger inventory + per-event flags
- ``list_lwc_bundles``       — Lightning Web Component bundle inventory
- ``get_lwc_bundle``         — bundle resources (js/html/css/meta) for one LWC
- ``list_custom_fields``     — fields on an sObject via EntityParticle
- ``describe_object_full``   — composite (fields + record types + VRs + flows)
- ``list_orgs``              — wrap ``sf org list`` for cross-org workflows
"""

from __future__ import annotations

from typing import Any

from . import admin, org as org_module, sf_cli
from ._shared import _run_soql, _validate_api_name


# Caps consistent with admin.py's pattern — clients can override via ``limit``
# but we cap to keep accidental "list everything" calls bounded.
MAX_APEX_CLASS_ROWS = 1000
MAX_APEX_TRIGGER_ROWS = 500
MAX_LWC_BUNDLE_ROWS = 1000
MAX_LWC_RESOURCE_ROWS = 200
MAX_CUSTOM_FIELD_ROWS = 1500


# --------------------------------------------------------------------------- #
# C1.1 list_apex_classes                                                      #
# --------------------------------------------------------------------------- #


def list_apex_classes(
    target_org: str | None = None,
    name_filter: str | None = None,
    include_managed: bool = False,
    status_filter: str | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    """List ``ApexClass`` rows. Status filter (``Active`` / ``Deleted`` /
    ``Inactive``) is applied verbatim to the SOQL ``Status`` column.

    name_filter does a SOQL ``LIKE '%name_filter%'``; rejects unsafe chars.
    """
    bounded = max(1, min(int(limit or 200), MAX_APEX_CLASS_ROWS))
    clauses: list[str] = []
    if not include_managed:
        clauses.append("NamespacePrefix = null")
    if name_filter:
        # Validate as an API-name fragment to keep LIKE safe from injection.
        if _validate_api_name(name_filter, kind="name_filter"):
            return {"error": "name_filter must match /^[A-Za-z][A-Za-z0-9_]*$/"}
        clauses.append(f"Name LIKE '%{name_filter}%'")
    if status_filter:
        if status_filter not in ("Active", "Deleted", "Inactive"):
            return {"error": "status_filter must be 'Active', 'Deleted', or 'Inactive'"}
        clauses.append(f"Status = '{status_filter}'")

    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    soql = (
        "SELECT Id, Name, ApiVersion, Status, NamespacePrefix, "
        "LengthWithoutComments, IsValid, CreatedDate, LastModifiedDate "
        f"FROM ApexClass{where} "
        "ORDER BY Name "
        f"LIMIT {bounded}"
    )
    probe = _run_soql(soql, target_org=target_org, tooling=True)
    if "error" in probe:
        return probe
    return {
        "class_count": probe["record_count"],
        "classes": probe["records"],
        "include_managed": include_managed,
    }


# --------------------------------------------------------------------------- #
# C1.2 get_apex_class                                                         #
# --------------------------------------------------------------------------- #


def get_apex_class(
    name: str,
    target_org: str | None = None,
    include_body: bool = True,
) -> dict[str, Any]:
    """Fetch a single ``ApexClass`` by name. Body is optional because some
    classes are large; pass ``include_body=False`` for a header-only call."""
    err = _validate_api_name(name, kind="name")
    if err:
        return {"error": err}

    fields = (
        "Id, Name, ApiVersion, Status, NamespacePrefix, IsValid, "
        "LengthWithoutComments, CreatedDate, LastModifiedDate"
    )
    if include_body:
        fields += ", Body"
    soql = f"SELECT {fields} FROM ApexClass WHERE Name = '{name}' LIMIT 1"
    probe = _run_soql(soql, target_org=target_org, tooling=True)
    if "error" in probe:
        return probe
    if not probe["records"]:
        return {"error": f"ApexClass '{name}' not found in target org"}
    record = probe["records"][0]
    return {
        "name": record.get("Name"),
        "id": record.get("Id"),
        "api_version": record.get("ApiVersion"),
        "status": record.get("Status"),
        "namespace": record.get("NamespacePrefix"),
        "is_valid": record.get("IsValid"),
        "length_without_comments": record.get("LengthWithoutComments"),
        "created_date": record.get("CreatedDate"),
        "last_modified_date": record.get("LastModifiedDate"),
        "body": record.get("Body") if include_body else None,
    }


# --------------------------------------------------------------------------- #
# C1.3 list_apex_triggers                                                     #
# --------------------------------------------------------------------------- #


def list_apex_triggers(
    target_org: str | None = None,
    object_name: str | None = None,
    active_only: bool = False,
    include_managed: bool = False,
    limit: int = 100,
) -> dict[str, Any]:
    """List ``ApexTrigger`` rows. Optional ``object_name`` scopes to one
    sObject — typical use from trigger-consolidator."""
    if object_name is not None:
        err = _validate_api_name(object_name, kind="object_name")
        if err:
            return {"error": err}

    bounded = max(1, min(int(limit or 100), MAX_APEX_TRIGGER_ROWS))
    clauses: list[str] = []
    if object_name:
        clauses.append(f"TableEnumOrId = '{object_name}'")
    if active_only:
        clauses.append("Status = 'Active'")
    if not include_managed:
        clauses.append("NamespacePrefix = null")

    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    soql = (
        "SELECT Id, Name, TableEnumOrId, Status, ApiVersion, NamespacePrefix, "
        "UsageBeforeInsert, UsageBeforeUpdate, UsageBeforeDelete, "
        "UsageAfterInsert, UsageAfterUpdate, UsageAfterDelete, UsageAfterUndelete "
        f"FROM ApexTrigger{where} "
        "ORDER BY TableEnumOrId, Name "
        f"LIMIT {bounded}"
    )
    probe = _run_soql(soql, target_org=target_org, tooling=True)
    if "error" in probe:
        return probe

    rows: list[dict[str, Any]] = []
    for rec in probe["records"]:
        events: list[str] = []
        for flag, label in (
            ("UsageBeforeInsert", "BeforeInsert"),
            ("UsageBeforeUpdate", "BeforeUpdate"),
            ("UsageBeforeDelete", "BeforeDelete"),
            ("UsageAfterInsert",  "AfterInsert"),
            ("UsageAfterUpdate",  "AfterUpdate"),
            ("UsageAfterDelete",  "AfterDelete"),
            ("UsageAfterUndelete", "AfterUndelete"),
        ):
            if rec.get(flag):
                events.append(label)
        rows.append(
            {
                "id": rec.get("Id"),
                "name": rec.get("Name"),
                "object": rec.get("TableEnumOrId"),
                "status": rec.get("Status"),
                "api_version": rec.get("ApiVersion"),
                "namespace": rec.get("NamespacePrefix"),
                "events": events,
            }
        )
    return {"trigger_count": len(rows), "triggers": rows}


# --------------------------------------------------------------------------- #
# C1.4 list_lwc_bundles                                                       #
# --------------------------------------------------------------------------- #


def list_lwc_bundles(
    target_org: str | None = None,
    name_filter: str | None = None,
    include_managed: bool = False,
    limit: int = 200,
) -> dict[str, Any]:
    """List ``LightningComponentBundle`` rows."""
    bounded = max(1, min(int(limit or 200), MAX_LWC_BUNDLE_ROWS))
    clauses: list[str] = []
    if not include_managed:
        clauses.append("NamespacePrefix = null")
    if name_filter:
        if _validate_api_name(name_filter, kind="name_filter"):
            return {"error": "name_filter must match /^[A-Za-z][A-Za-z0-9_]*$/"}
        clauses.append(f"DeveloperName LIKE '%{name_filter}%'")
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    soql = (
        "SELECT Id, DeveloperName, MasterLabel, ApiVersion, Description, "
        "NamespacePrefix, IsExposed, TargetConfigs "
        f"FROM LightningComponentBundle{where} "
        "ORDER BY DeveloperName "
        f"LIMIT {bounded}"
    )
    probe = _run_soql(soql, target_org=target_org, tooling=True)
    if "error" in probe:
        return probe
    return {
        "bundle_count": probe["record_count"],
        "bundles": probe["records"],
        "include_managed": include_managed,
    }


# --------------------------------------------------------------------------- #
# C1.5 get_lwc_bundle                                                         #
# --------------------------------------------------------------------------- #


def get_lwc_bundle(
    name: str,
    target_org: str | None = None,
    include_resources: bool = True,
) -> dict[str, Any]:
    """Fetch one bundle plus (optionally) every resource (js/html/css/meta) it owns."""
    err = _validate_api_name(name, kind="name")
    if err:
        return {"error": err}

    bundle_soql = (
        "SELECT Id, DeveloperName, MasterLabel, ApiVersion, Description, "
        "NamespacePrefix, IsExposed, TargetConfigs "
        f"FROM LightningComponentBundle WHERE DeveloperName = '{name}' LIMIT 1"
    )
    bundle_probe = _run_soql(bundle_soql, target_org=target_org, tooling=True)
    if "error" in bundle_probe:
        return bundle_probe
    if not bundle_probe["records"]:
        return {"error": f"LightningComponentBundle '{name}' not found in target org"}

    bundle = bundle_probe["records"][0]
    out: dict[str, Any] = {
        "name": bundle.get("DeveloperName"),
        "label": bundle.get("MasterLabel"),
        "id": bundle.get("Id"),
        "api_version": bundle.get("ApiVersion"),
        "description": bundle.get("Description"),
        "namespace": bundle.get("NamespacePrefix"),
        "is_exposed": bundle.get("IsExposed"),
        "target_configs": bundle.get("TargetConfigs"),
    }

    if include_resources:
        resources_soql = (
            "SELECT Id, FilePath, Format, Source "
            f"FROM LightningComponentResource "
            f"WHERE LightningComponentBundleId = '{bundle['Id']}' "
            "ORDER BY FilePath "
            f"LIMIT {MAX_LWC_RESOURCE_ROWS}"
        )
        res_probe = _run_soql(resources_soql, target_org=target_org, tooling=True)
        if "error" in res_probe:
            out["resources_error"] = res_probe.get("error")
            out["resources"] = []
        else:
            out["resources"] = [
                {
                    "id": r.get("Id"),
                    "path": r.get("FilePath"),
                    "format": r.get("Format"),
                    "source": r.get("Source"),
                }
                for r in res_probe["records"]
            ]
            out["resource_count"] = len(out["resources"])
    return out


# --------------------------------------------------------------------------- #
# C1.6 list_custom_fields                                                     #
# --------------------------------------------------------------------------- #


# EntityParticle returns rows for system-managed pseudo-fields like ``Id``,
# ``IsDeleted``, ``SystemModstamp``, ``CreatedById``, etc. Filter them out
# unless the caller explicitly opts in — most consumers (object-designer,
# field-impact-analyzer) don't want them.
_PSEUDO_FIELDS = frozenset(
    {
        "Id", "IsDeleted", "MasterRecordId",
        "CreatedById", "CreatedDate", "LastModifiedById", "LastModifiedDate",
        "SystemModstamp", "LastViewedDate", "LastReferencedDate",
        "LastActivityDate", "OwnerId",
    }
)


def list_custom_fields(
    object_name: str,
    target_org: str | None = None,
    include_standard: bool = False,
    include_pseudo_fields: bool = False,
    limit: int = 500,
) -> dict[str, Any]:
    """List fields on an sObject via ``EntityParticle``.

    Default behaviour returns custom fields only (``__c`` suffix). Pass
    ``include_standard=True`` to also get standard fields — useful for
    field-impact-analyzer when the target field is something like
    ``Account.Industry``. ``include_pseudo_fields`` controls whether
    EntityParticle's system-managed rows (``Id``, ``IsDeleted``,
    ``SystemModstamp``, etc.) appear; default off because consumers
    usually want only fields a developer wrote.
    """
    err = _validate_api_name(object_name, kind="object_name")
    if err:
        return {"error": err}
    bounded = max(1, min(int(limit or 500), MAX_CUSTOM_FIELD_ROWS))

    # EntityParticle is queryable on the standard REST API (not Tooling). We
    # cannot use ``IsCustom`` on the WHERE clause for every Salesforce edition,
    # so we filter by the ``__c`` suffix when ``include_standard=False``.
    name_clause = "" if include_standard else " AND QualifiedApiName LIKE '%\\_\\_c' ESCAPE '\\\\'"
    soql = (
        "SELECT QualifiedApiName, DataType, Label, Length, Precision, "
        "Scale, IsNillable, IsCalculated, IsHtmlFormatted, ReferenceTo, "
        "RelationshipName "
        "FROM EntityParticle "
        f"WHERE EntityDefinition.QualifiedApiName = '{object_name}'{name_clause} "
        "ORDER BY QualifiedApiName "
        f"LIMIT {bounded}"
    )
    probe = _run_soql(soql, target_org=target_org, tooling=False)
    if "error" in probe:
        return probe

    rows = []
    pseudo_dropped = 0
    for rec in probe["records"]:
        name = rec.get("QualifiedApiName")
        if not include_pseudo_fields and name in _PSEUDO_FIELDS:
            pseudo_dropped += 1
            continue
        ref = rec.get("ReferenceTo")
        ref_to: list[str] = []
        if isinstance(ref, dict):
            inner = ref.get("referenceTo") or []
            ref_to = [str(x) for x in inner if x]
        rows.append(
            {
                "name": name,
                "label": rec.get("Label"),
                "type": rec.get("DataType"),
                "length": rec.get("Length"),
                "precision": rec.get("Precision"),
                "scale": rec.get("Scale"),
                "nillable": rec.get("IsNillable"),
                "calculated": rec.get("IsCalculated"),
                "html_formatted": rec.get("IsHtmlFormatted"),
                "reference_to": ref_to,
                "relationship_name": rec.get("RelationshipName"),
            }
        )
    return {
        "object": object_name,
        "include_standard": include_standard,
        "include_pseudo_fields": include_pseudo_fields,
        "field_count": len(rows),
        "pseudo_fields_dropped": pseudo_dropped,
        "fields": rows,
    }


# --------------------------------------------------------------------------- #
# C1.7 describe_object_full (composite)                                       #
# --------------------------------------------------------------------------- #


def describe_object_full(
    object_name: str,
    target_org: str | None = None,
    include_fields: bool = True,
    include_record_types: bool = True,
    include_validation_rules: bool = True,
    include_active_flows: bool = True,
) -> dict[str, Any]:
    """One-call replacement for ``list_custom_fields`` + ``list_record_types``
    + ``list_validation_rules`` + ``list_flows_on_object`` against a single
    sObject. Saves 4 round-trips for object-designer / field-impact-analyzer.

    Each sub-section is silently skipped if its include flag is ``False``.
    Per-section errors are surfaced under ``<section>_error`` rather than
    failing the whole call — that way object-designer can still get RTs
    even if VRs blow up on a Tooling-API quirk."""
    err = _validate_api_name(object_name, kind="object_name")
    if err:
        return {"error": err}

    out: dict[str, Any] = {"object": object_name}

    if include_fields:
        fields_payload = list_custom_fields(
            object_name=object_name,
            target_org=target_org,
            include_standard=False,
            limit=MAX_CUSTOM_FIELD_ROWS,
        )
        if "error" in fields_payload:
            out["fields_error"] = fields_payload["error"]
        else:
            out["fields"] = fields_payload["fields"]
            out["field_count"] = fields_payload["field_count"]

    if include_record_types:
        rt_payload = admin.list_record_types(
            object_name=object_name,
            target_org=target_org,
            active_only=False,
        )
        if "error" in rt_payload:
            out["record_types_error"] = rt_payload["error"]
        else:
            out["record_types"] = rt_payload.get("record_types", [])
            out["record_type_count"] = rt_payload.get("record_type_count", 0)

    if include_validation_rules:
        vr_payload = admin.list_validation_rules(
            object_name=object_name,
            target_org=target_org,
            active_only=False,
        )
        if "error" in vr_payload:
            out["validation_rules_error"] = vr_payload["error"]
        else:
            out["validation_rules"] = vr_payload.get("rules", [])
            out["validation_rule_count"] = vr_payload.get("rule_count", 0)

    if include_active_flows:
        flow_payload = org_module.list_flows_on_object(
            object_name=object_name,
            target_org=target_org,
            active_only=True,
        )
        if "error" in flow_payload:
            out["flows_error"] = flow_payload["error"]
        else:
            # list_flows_on_object returns ``flows`` and ``flow_count``.
            out["active_flows"] = flow_payload.get("flows", [])
            out["active_flow_count"] = flow_payload.get("flow_count", 0)

    return out


# --------------------------------------------------------------------------- #
# C1.8 list_orgs                                                              #
# --------------------------------------------------------------------------- #


def list_orgs() -> dict[str, Any]:
    """List every Salesforce org the user is currently authenticated to via
    ``sf org list``. No target_org input — this is the discovery tool that
    tells the LLM what the valid ``target_org`` values are.

    Returns a normalized shape with ``orgs[]`` (alias, username, instance
    URL, edition, status, type), so the agent can pick a target without
    parsing the raw ``sf`` JSON."""
    payload = sf_cli.run_sf_json(["org", "list"])
    if "error" in payload and "result" not in payload:
        return payload

    result = payload.get("result", {}) or {}

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()  # dedupe by username (sf reports same org under nonScratchOrgs and scratchOrgs)
    for bucket_name in ("devHubs", "nonScratchOrgs", "scratchOrgs", "sandboxes", "other"):
        bucket = result.get(bucket_name) or []
        for entry in bucket:
            username = entry.get("username") or ""
            if username and username in seen:
                continue
            seen.add(username)
            rows.append(
                {
                    "alias": entry.get("alias"),
                    "username": username,
                    "instance_url": entry.get("instanceUrl"),
                    "edition": entry.get("edition"),
                    "is_default": bool(entry.get("isDefaultUsername") or entry.get("isDefaultDevHubUsername")),
                    "is_scratch": bucket_name == "scratchOrgs",
                    "is_sandbox": bucket_name == "sandboxes",
                    "is_devhub": bucket_name == "devHubs",
                    "status": entry.get("status"),
                    "expiration_date": entry.get("expirationDate"),
                }
            )
    return {"org_count": len(rows), "orgs": rows}
