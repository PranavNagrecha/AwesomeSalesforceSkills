"""Tests for the admin-metadata MCP tools.

We stub the ``sf`` CLI by monkeypatching ``sf_cli.run_sf_json`` so the probes
return canned JSON. This keeps the admin tool surface behavior-tested without
depending on a real Salesforce org.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sfskills_mcp import admin  # noqa: E402


def _soql_payload(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {"status": 0, "result": {"records": records}}


class ApiNameValidationTest(unittest.TestCase):
    def test_rejects_unsafe_object_name(self) -> None:
        out = admin.list_validation_rules("Account; DROP TABLE")
        self.assertIn("error", out)
        self.assertIn("object_name", out["error"])

    def test_rejects_quoted_object_name(self) -> None:
        out = admin.list_validation_rules("Account'")
        self.assertIn("error", out)

    def test_accepts_custom_object_suffix(self) -> None:
        with mock.patch.object(admin.sf_cli, "run_sf_json", return_value=_soql_payload([])):
            out = admin.list_validation_rules("Acme_Custom__c")
            self.assertNotIn("error", out)


class ListValidationRulesTest(unittest.TestCase):
    def test_returns_flattened_rows(self) -> None:
        records = [
            {
                "attributes": {"type": "ValidationRule"},
                "Id": "03dX",
                "ValidationName": "Opp_CloseDate_Required",
                "Active": True,
                "Description": "Require close date",
                "ErrorMessage": "Close date required",
                "ErrorDisplayField": "CloseDate",
                "EntityDefinition": {"QualifiedApiName": "Opportunity"},
            }
        ]
        with mock.patch.object(admin.sf_cli, "run_sf_json", return_value=_soql_payload(records)) as runner:
            out = admin.list_validation_rules("Opportunity", active_only=True, limit=50)
            self.assertEqual(out["rule_count"], 1)
            self.assertEqual(out["rules"][0]["name"], "Opp_CloseDate_Required")
            self.assertEqual(out["rules"][0]["object"], "Opportunity")
            args = runner.call_args.args[0]
            soql = args[args.index("--query") + 1]
            self.assertIn("Active = true", soql)
            self.assertIn("'Opportunity'", soql)


class ListPermissionSetsTest(unittest.TestCase):
    def test_excludes_profile_owned_by_default(self) -> None:
        with mock.patch.object(admin.sf_cli, "run_sf_json", return_value=_soql_payload([])) as runner:
            admin.list_permission_sets()
            args = runner.call_args.args[0]
            soql = args[args.index("--query") + 1]
            self.assertIn("IsOwnedByProfile = false", soql)

    def test_accepts_safe_name_filter(self) -> None:
        records = [{"attributes": {}, "Id": "0PS", "Name": "Sales_SDR_Access", "Label": "SDR", "License": None}]
        with mock.patch.object(admin.sf_cli, "run_sf_json", return_value=_soql_payload(records)) as runner:
            out = admin.list_permission_sets(name_filter="Sales")
            self.assertEqual(out["permission_set_count"], 1)
            args = runner.call_args.args[0]
            soql = args[args.index("--query") + 1]
            self.assertIn("LIKE '%Sales%'", soql)

    def test_rejects_unsafe_name_filter(self) -> None:
        out = admin.list_permission_sets(name_filter="evil' OR '1'='1")
        self.assertIn("error", out)


class DescribePermissionSetTest(unittest.TestCase):
    def test_errors_when_not_found(self) -> None:
        with mock.patch.object(admin.sf_cli, "run_sf_json", return_value=_soql_payload([])):
            out = admin.describe_permission_set("Nope_PS")
            self.assertIn("error", out)
            self.assertIn("not found", out["error"])

    def test_assembles_header_and_permissions(self) -> None:
        header = [
            {
                "attributes": {},
                "Id": "0PS111",
                "Name": "SDR_Access",
                "Label": "SDR Access",
                "Description": "Access for SDRs",
                "IsCustom": True,
                "IsOwnedByProfile": False,
                "License": {"Name": "Salesforce"},
            }
        ]
        obj_perms = [
            {
                "attributes": {},
                "SObjectType": "Lead",
                "PermissionsCreate": True,
                "PermissionsRead": True,
                "PermissionsEdit": True,
                "PermissionsDelete": False,
                "PermissionsViewAllRecords": False,
                "PermissionsModifyAllRecords": False,
            }
        ]
        field_perms = [
            {"attributes": {}, "SObjectType": "Lead", "Field": "Lead.Email", "PermissionsRead": True, "PermissionsEdit": False}
        ]

        def fake_run(args: list[str], target_org: str | None = None) -> dict[str, Any]:
            soql = args[args.index("--query") + 1]
            if "FROM PermissionSet " in soql:
                return _soql_payload(header)
            if "FROM ObjectPermissions" in soql:
                return _soql_payload(obj_perms)
            if "FROM FieldPermissions" in soql:
                return _soql_payload(field_perms)
            raise AssertionError(f"unexpected soql: {soql}")

        with mock.patch.object(admin.sf_cli, "run_sf_json", side_effect=fake_run):
            out = admin.describe_permission_set("SDR_Access")
            self.assertEqual(out["name"], "SDR_Access")
            self.assertEqual(out["license"], "Salesforce")
            self.assertEqual(len(out["object_permissions"]), 1)
            self.assertEqual(len(out["field_permissions"]), 1)
            self.assertFalse(out["field_permissions_truncated"])


class ListRecordTypesTest(unittest.TestCase):
    def test_filters_by_object(self) -> None:
        with mock.patch.object(admin.sf_cli, "run_sf_json", return_value=_soql_payload([])) as runner:
            admin.list_record_types("Opportunity", active_only=True)
            args = runner.call_args.args[0]
            soql = args[args.index("--query") + 1]
            self.assertIn("SobjectType = 'Opportunity'", soql)
            self.assertIn("IsActive = true", soql)


class ListApprovalProcessesTest(unittest.TestCase):
    def test_defaults_to_active_and_approval_type(self) -> None:
        with mock.patch.object(admin.sf_cli, "run_sf_json", return_value=_soql_payload([])) as runner:
            admin.list_approval_processes("Opportunity")
            args = runner.call_args.args[0]
            soql = args[args.index("--query") + 1]
            self.assertIn("Type = 'Approval'", soql)
            self.assertIn("State = 'Active'", soql)
            self.assertIn("TableEnumOrId = 'Opportunity'", soql)

    def test_inactive_included_when_requested(self) -> None:
        with mock.patch.object(admin.sf_cli, "run_sf_json", return_value=_soql_payload([])) as runner:
            admin.list_approval_processes(active_only=False)
            args = runner.call_args.args[0]
            soql = args[args.index("--query") + 1]
            self.assertNotIn("State =", soql)


class ToolingQueryTest(unittest.TestCase):
    def test_rejects_non_select(self) -> None:
        out = admin.tooling_query("UPDATE Account SET Name = 'x'")
        self.assertIn("error", out)

    def test_rejects_dml_keywords(self) -> None:
        out = admin.tooling_query("SELECT Id FROM Account WHERE 1=1; DELETE Account")
        self.assertIn("error", out)

    def test_rejects_semicolon(self) -> None:
        out = admin.tooling_query("SELECT Id FROM Account; SELECT Id FROM Contact")
        self.assertIn("error", out)

    def test_adds_limit_when_missing(self) -> None:
        with mock.patch.object(admin.sf_cli, "run_sf_json", return_value=_soql_payload([])) as runner:
            admin.tooling_query("SELECT Id, Name FROM ApexClass")
            args = runner.call_args.args[0]
            soql = args[args.index("--query") + 1]
            self.assertIn("LIMIT 200", soql)

    def test_preserves_explicit_limit(self) -> None:
        with mock.patch.object(admin.sf_cli, "run_sf_json", return_value=_soql_payload([])) as runner:
            admin.tooling_query("SELECT Id FROM ApexClass LIMIT 10", limit=200)
            args = runner.call_args.args[0]
            soql = args[args.index("--query") + 1]
            self.assertEqual(soql.count("LIMIT "), 1)

    def test_returns_structured_output(self) -> None:
        records = [{"attributes": {}, "Id": "01p", "Name": "MyClass"}]
        with mock.patch.object(admin.sf_cli, "run_sf_json", return_value=_soql_payload(records)):
            out = admin.tooling_query("SELECT Id, Name FROM ApexClass LIMIT 10")
            self.assertTrue(out["tooling_api"])
            self.assertEqual(out["row_count"], 1)
            self.assertEqual(out["rows"][0]["Name"], "MyClass")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
