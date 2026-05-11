"""Admin-land metadata probes for the SfSkills MCP server.

These tools power the Tier-1 / Tier-2 admin run-time agents. They are built on
the same Salesforce CLI foundation as ``org.py`` — we do not handle secrets in
this process; the user's existing ``sf`` auth is the source of truth.

All tools return a structured ``dict`` and surface failures as ``{"error": ...}``
without raising. The surface intentionally mirrors ``org.py`` so agents see a
consistent shape across every live-org probe.

Tools exposed:

- ``list_validation_rules`` — Validation Rules on an object (active/all).
- ``list_permission_sets`` — Permission Sets (with optional filter).
- ``describe_permission_set`` — contents of a single PS (object + field perms).
- ``list_record_types`` — Record Types on an object.
- ``list_named_credentials`` — Named Credentials in the org.
- ``list_approval_processes`` — approval ProcessDefinitions for an object.
- ``tooling_query`` — escape-hatch read-only SOQL via the Tooling API.
"""

from __future__ import annotations

import re
from typing import Any

from . import sf_cli
from ._shared import _API_NAME_PATTERN, _run_soql, _strip_attributes, _validate_api_name


# Re-export so existing ``from .admin import _run_soql`` callers in the rest
# of the package keep working.
__all__ = [
    "_API_NAME_PATTERN",
    "_run_soql",
    "_strip_attributes",
    "_validate_api_name",
    "list_validation_rules",
    "list_permission_sets",
    "describe_permission_set",
    "list_record_types",
    "list_named_credentials",
    "list_approval_processes",
    "tooling_query",
]


MAX_VALIDATION_RULE_ROWS = 500
MAX_PERMISSION_SET_ROWS = 500
MAX_RECORD_TYPE_ROWS = 200
MAX_NAMED_CREDENTIAL_ROWS = 200
MAX_APPROVAL_PROCESS_ROWS = 200
MAX_TOOLING_QUERY_ROWS = 2000


# --------------------------------------------------------------------------- #
# list_validation_rules                                                       #
# --------------------------------------------------------------------------- #


def list_validation_rules(
    object_name: str,
    target_org: str | None = None,
    active_only: bool = False,
    limit: int = 100,
) -> dict[str, Any]:
    """List Validation Rules on an sObject.

    Uses the Tooling API ``ValidationRule`` entity. Returns rule name, active
    flag, error message, error display field, and the raw error condition
    formula — enough for ``validation-rule-auditor`` to classify each rule.
    """
    err = _validate_api_name(object_name, kind="object_name")
    if err:
        return {"error": err}

    bounded = max(1, min(int(limit or 100), MAX_VALIDATION_RULE_ROWS))
    active_clause = " AND Active = true" if active_only else ""
    soql = (
        "SELECT Id, ValidationName, Active, Description, ErrorMessage, "
        "ErrorDisplayField, EntityDefinition.QualifiedApiName "
        "FROM ValidationRule "
        f"WHERE EntityDefinition.QualifiedApiName = '{object_name}'{active_clause} "
        "ORDER BY ValidationName "
        f"LIMIT {bounded}"
    )
    probe = _run_soql(soql, target_org=target_org, tooling=True)
    if "error" in probe:
        return probe

    rows: list[dict[str, Any]] = []
    for record in probe["records"]:
        entity = record.get("EntityDefinition") or {}
        entity_api = entity.get("QualifiedApiName") if isinstance(entity, dict) else None
        rows.append(
            {
                "id": record.get("Id"),
                "name": record.get("ValidationName"),
                "active": record.get("Active"),
                "description": record.get("Description"),
                "error_message": record.get("ErrorMessage"),
                "error_display_field": record.get("ErrorDisplayField"),
                "object": entity_api,
            }
        )
    return {
        "object": object_name,
        "active_only": active_only,
        "rule_count": len(rows),
        "rules": rows,
    }


# --------------------------------------------------------------------------- #
# list_permission_sets                                                        #
# --------------------------------------------------------------------------- #


def list_permission_sets(
    target_org: str | None = None,
    name_filter: str | None = None,
    include_owned_by_profile: bool = False,
    limit: int = 200,
) -> dict[str, Any]:
    """List Permission Sets in the org.

    By default excludes profile-owned permission sets (the synthetic shadow
    PSes Salesforce creates per profile). Set ``include_owned_by_profile=True``
    to see them — useful when auditing legacy custom profiles.
    """
    bounded = max(1, min(int(limit or 200), MAX_PERMISSION_SET_ROWS))
    clauses: list[str] = []
    if not include_owned_by_profile:
        clauses.append("IsOwnedByProfile = false")
    if name_filter and _API_NAME_PATTERN.match(name_filter):
        clauses.append(f"Name LIKE '%{name_filter}%'")
    elif name_filter:
        return {"error": "name_filter must match /^[A-Za-z][A-Za-z0-9_]*$/"}

    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    soql = (
        "SELECT Id, Name, Label, Description, IsCustom, IsOwnedByProfile, "
        "NamespacePrefix, License.Name "
        f"FROM PermissionSet{where} "
        "ORDER BY Name "
        f"LIMIT {bounded}"
    )
    probe = _run_soql(soql, target_org=target_org, tooling=False)
    if "error" in probe:
        return probe

    rows: list[dict[str, Any]] = []
    for record in probe["records"]:
        license_name = None
        license_obj = record.get("License")
        if isinstance(license_obj, dict):
            license_name = license_obj.get("Name")
        rows.append(
            {
                "id": record.get("Id"),
                "name": record.get("Name"),
                "label": record.get("Label"),
                "description": record.get("Description"),
                "custom": record.get("IsCustom"),
                "owned_by_profile": record.get("IsOwnedByProfile"),
                "namespace_prefix": record.get("NamespacePrefix"),
                "license": license_name,
            }
        )
    return {
        "permission_set_count": len(rows),
        "permission_sets": rows,
    }


# --------------------------------------------------------------------------- #
# describe_permission_set                                                     #
# --------------------------------------------------------------------------- #


def describe_permission_set(
    name: str,
    target_org: str | None = None,
    include_field_permissions: bool = True,
) -> dict[str, Any]:
    """Describe a single Permission Set — header + object + field permissions.

    ``include_field_permissions`` defaults to True but can be disabled for PSes
    that grant broad access (field-perm rows can explode past a few thousand).
    """
    err = _validate_api_name(name, kind="name")
    if err:
        return {"error": err}

    header_probe = _run_soql(
        "SELECT Id, Name, Label, Description, IsCustom, IsOwnedByProfile, "
        "NamespacePrefix, License.Name "
        f"FROM PermissionSet WHERE Name = '{name}' LIMIT 1",
        target_org=target_org,
        tooling=False,
    )
    if "error" in header_probe:
        return header_probe
    if not header_probe["records"]:
        return {"error": f"Permission Set '{name}' not found in target org"}

    header = header_probe["records"][0]
    license_name = None
    license_obj = header.get("License")
    if isinstance(license_obj, dict):
        license_name = license_obj.get("Name")

    object_perms_probe = _run_soql(
        "SELECT SObjectType, PermissionsCreate, PermissionsRead, "
        "PermissionsEdit, PermissionsDelete, PermissionsViewAllRecords, "
        "PermissionsModifyAllRecords "
        f"FROM ObjectPermissions WHERE ParentId = '{header['Id']}' "
        "ORDER BY SObjectType LIMIT 500",
        target_org=target_org,
        tooling=False,
    )

    field_perms: list[dict[str, Any]] = []
    if include_field_permissions:
        field_perms_probe = _run_soql(
            "SELECT SObjectType, Field, PermissionsRead, PermissionsEdit "
            f"FROM FieldPermissions WHERE ParentId = '{header['Id']}' "
            "ORDER BY SObjectType, Field LIMIT 2000",
            target_org=target_org,
            tooling=False,
        )
        if "error" not in field_perms_probe:
            field_perms = field_perms_probe["records"]

    return {
        "name": header.get("Name"),
        "label": header.get("Label"),
        "description": header.get("Description"),
        "custom": header.get("IsCustom"),
        "owned_by_profile": header.get("IsOwnedByProfile"),
        "license": license_name,
        "object_permissions": object_perms_probe.get("records", []),
        "field_permissions": field_perms,
        "field_permissions_truncated": include_field_permissions and len(field_perms) >= 2000,
    }


# --------------------------------------------------------------------------- #
# list_record_types                                                           #
# --------------------------------------------------------------------------- #


def list_record_types(
    object_name: str,
    target_org: str | None = None,
    active_only: bool = False,
    limit: int = 100,
) -> dict[str, Any]:
    """List Record Types on an sObject."""
    err = _validate_api_name(object_name, kind="object_name")
    if err:
        return {"error": err}

    bounded = max(1, min(int(limit or 100), MAX_RECORD_TYPE_ROWS))
    active_clause = " AND IsActive = true" if active_only else ""
    soql = (
        "SELECT Id, DeveloperName, Name, Description, IsActive, "
        "BusinessProcessId, SobjectType, NamespacePrefix "
        "FROM RecordType "
        f"WHERE SobjectType = '{object_name}'{active_clause} "
        "ORDER BY DeveloperName "
        f"LIMIT {bounded}"
    )
    probe = _run_soql(soql, target_org=target_org, tooling=False)
    if "error" in probe:
        return probe

    return {
        "object": object_name,
        "active_only": active_only,
        "record_type_count": probe["record_count"],
        "record_types": probe["records"],
    }


# --------------------------------------------------------------------------- #
# list_named_credentials                                                      #
# --------------------------------------------------------------------------- #


def list_named_credentials(
    target_org: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """List Named Credentials in the org.

    Includes endpoint + principal type. Returned in the order stored by
    Salesforce (typically alphabetical by DeveloperName).
    """
    bounded = max(1, min(int(limit or 100), MAX_NAMED_CREDENTIAL_ROWS))
    soql = (
        "SELECT Id, DeveloperName, MasterLabel, Endpoint, PrincipalType, "
        "NamespacePrefix "
        "FROM NamedCredential "
        "ORDER BY DeveloperName "
        f"LIMIT {bounded}"
    )
    probe = _run_soql(soql, target_org=target_org, tooling=False)
    if "error" in probe:
        return probe
    return {
        "named_credential_count": probe["record_count"],
        "named_credentials": probe["records"],
    }


# --------------------------------------------------------------------------- #
# list_approval_processes                                                     #
# --------------------------------------------------------------------------- #


def list_approval_processes(
    object_name: str | None = None,
    target_org: str | None = None,
    active_only: bool = True,
    limit: int = 100,
) -> dict[str, Any]:
    """List Approval ``ProcessDefinition`` records, optionally filtered by object.

    Approval Processes are stored as ``ProcessDefinition`` rows with
    ``Type = 'Approval'``. This is what ``automation-migration-router``
    reads (with ``--source-type=approval_process``) to plan a migration to Flow Orchestrator.
    """
    if object_name is not None:
        err = _validate_api_name(object_name, kind="object_name")
        if err:
            return {"error": err}

    bounded = max(1, min(int(limit or 100), MAX_APPROVAL_PROCESS_ROWS))
    clauses = ["Type = 'Approval'"]
    if object_name:
        clauses.append(f"TableEnumOrId = '{object_name}'")
    if active_only:
        clauses.append("State = 'Active'")
    where = " AND ".join(clauses)

    soql = (
        "SELECT Id, DeveloperName, Name, Description, TableEnumOrId, Type, "
        "State, LockType, CreatedDate, LastModifiedDate "
        "FROM ProcessDefinition "
        f"WHERE {where} "
        "ORDER BY DeveloperName "
        f"LIMIT {bounded}"
    )
    probe = _run_soql(soql, target_org=target_org, tooling=False)
    if "error" in probe:
        return probe

    return {
        "object": object_name,
        "active_only": active_only,
        "approval_process_count": probe["record_count"],
        "approval_processes": probe["records"],
    }


# --------------------------------------------------------------------------- #
# tooling_query                                                               #
# --------------------------------------------------------------------------- #


_TOOLING_QUERY_BLOCKLIST = (
    "INSERT ",
    "UPDATE ",
    "DELETE ",
    "UPSERT ",
    "MERGE ",
    ";",
)


_AGGREGATE_FN_RE = re.compile(
    r"\b(COUNT|COUNT_DISTINCT|SUM|AVG|MIN|MAX)\s*\(",
    re.IGNORECASE,
)


def _is_non_grouped_aggregate(upper_soql: str) -> bool:
    """Return True if the SOQL uses an aggregate function in SELECT
    without GROUP BY.

    Used by tooling_query to skip auto-LIMIT injection for queries
    Salesforce rejects with "Non-grouped query that uses overall
    aggregate functions cannot also use LIMIT".
    """
    if not _AGGREGATE_FN_RE.search(upper_soql):
        return False
    if " GROUP BY " in upper_soql:
        return False
    return True


def _strip_soql_string_literals(soql: str) -> str:
    """Remove the content of single- and double-quoted string literals so
    the DML-keyword scan only sees statement tokens.

    SOQL string literals use ``\\'`` to escape an embedded apostrophe.
    This is a small state machine; the regex approach is fragile when
    escapes appear at the end of a literal. Returns the SOQL with each
    literal replaced by an empty literal (``''`` or ``""``) so column
    positions stay close to the original for error messages.
    """
    out: list[str] = []
    i = 0
    n = len(soql)
    while i < n:
        ch = soql[i]
        if ch in ("'", '"'):
            quote = ch
            out.append(quote)
            i += 1
            while i < n:
                c = soql[i]
                if c == "\\" and i + 1 < n:
                    # Skip the escaped char entirely (could be \\, \', \", etc.).
                    i += 2
                    continue
                if c == quote:
                    out.append(quote)
                    i += 1
                    break
                i += 1
            else:
                # Unterminated literal — keep what we consumed; caller's
                # blocklist check below will either pass (no DML kw outside)
                # or fail with the existing message, and Salesforce will
                # ultimately reject the malformed SOQL with a clearer error.
                pass
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def tooling_query(
    soql: str,
    target_org: str | None = None,
    tooling: bool = False,
    limit: int = 200,
) -> dict[str, Any]:
    """Escape hatch — run a read-only SOQL query against the org.

    Default routes through the **Standard SOQL API** (``tooling=False``)
    because that's what users querying ``Account``, ``Contact``,
    ``Opportunity``, etc. — the vast majority of cases — need. Pass
    ``tooling=True`` to query Tooling-API-only entities like
    ``ApexClass``, ``Flow``, ``MetadataContainer``,
    ``CustomObject`` (definitions, not records), ``ApexTrigger``, etc.

    Guardrails:
    - Refuses any statement that looks like DML (``INSERT``, ``UPDATE``,
      ``DELETE``, ``UPSERT``, ``MERGE``) or contains a ``;``.
      DML-keyword detection only looks at statement tokens, not at
      string-literal content — so ``WHERE Name = 'foo INSERT bar'`` is
      legitimate and runs.
    - Refuses queries that do not start with ``SELECT``.
    - Bounds the returned row count at ``MAX_TOOLING_QUERY_ROWS``.

    Agents should prefer the specialized tools above when they exist. Use this
    only when a specialized tool does not cover the lookup.
    """
    raw = (soql or "").strip()
    upper = raw.upper()
    if not raw:
        return {"error": "soql is required"}
    # `SELECT` followed by ANY whitespace (newline, tab, space) starts a
    # legit SOQL statement. Previously we checked startswith("SELECT ")
    # which rejected multi-line SOQL formatted with `SELECT\n  Id …`.
    if not re.match(r"^\s*SELECT\b", raw, re.IGNORECASE):
        return {"error": "tooling_query only supports SELECT statements"}
    # Strip string literals before scanning for DML — otherwise a literal
    # like ``'foo INSERT bar'`` falsely matches the blocklist.
    scrubbed_upper = _strip_soql_string_literals(upper)
    for banned in _TOOLING_QUERY_BLOCKLIST:
        if banned in scrubbed_upper:
            return {"error": f"tooling_query refuses statements containing {banned.strip()!r}"}

    bounded = max(1, min(int(limit or 200), MAX_TOOLING_QUERY_ROWS))
    # Auto-LIMIT, but skip aggregates. Salesforce SOQL forbids LIMIT on
    # non-grouped queries that use overall aggregate functions
    # (``SELECT COUNT()``, ``SUM()``, ``AVG()``, ``MIN()``, ``MAX()`` without
    # GROUP BY) — server returns
    # ``"Non-grouped query that uses overall aggregate functions cannot
    # also use LIMIT"``. Detect aggregate-in-SELECT and skip the limit.
    # GROUP BY queries CAN use LIMIT, so the presence of GROUP BY in the
    # statement is treated as a grouped-aggregate and the LIMIT is kept.
    if " LIMIT " not in upper:
        if _is_non_grouped_aggregate(scrubbed_upper):
            pass  # don't auto-LIMIT; server would reject
        else:
            raw = f"{raw.rstrip()} LIMIT {bounded}"

    probe = _run_soql(raw, target_org=target_org, tooling=bool(tooling))
    if "error" in probe:
        return probe

    return {
        "tooling_api": bool(tooling),
        "row_count": probe["record_count"],
        "rows": probe["records"],
    }
