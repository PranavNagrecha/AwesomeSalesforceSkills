"""Tests for the developer-tier live-org MCP tools.

Stubs ``sf`` via ``unittest.mock.patch.object`` on ``dev_org._run_soql``
(and ``dev_org.sf_cli.run_sf_json`` for the org-list path). No real
Salesforce CLI required.
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

from sfskills_mcp import dev_org  # noqa: E402


def _soql_result(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Match the shape ``_run_soql`` returns on success."""
    return {"record_count": len(records), "records": records}


# --------------------------------------------------------------------------- #
# list_apex_classes                                                           #
# --------------------------------------------------------------------------- #


class ListApexClassesTest(unittest.TestCase):
    def test_filters_managed_by_default(self) -> None:
        with mock.patch.object(dev_org, "_run_soql") as run:
            run.return_value = _soql_result([])
            dev_org.list_apex_classes()
            soql = run.call_args.args[0]
            self.assertIn("NamespacePrefix = null", soql)

    def test_include_managed_drops_namespace_clause(self) -> None:
        with mock.patch.object(dev_org, "_run_soql") as run:
            run.return_value = _soql_result([])
            dev_org.list_apex_classes(include_managed=True)
            soql = run.call_args.args[0]
            self.assertNotIn("NamespacePrefix = null", soql)

    def test_name_filter_appears_in_like_clause(self) -> None:
        with mock.patch.object(dev_org, "_run_soql") as run:
            run.return_value = _soql_result([])
            dev_org.list_apex_classes(name_filter="Account")
            self.assertIn("Name LIKE '%Account%'", run.call_args.args[0])

    def test_unsafe_name_filter_rejected(self) -> None:
        out = dev_org.list_apex_classes(name_filter="bad'name")
        self.assertIn("error", out)

    def test_status_filter_validated(self) -> None:
        out = dev_org.list_apex_classes(status_filter="DroppedTable")
        self.assertIn("error", out)

    def test_returns_class_count(self) -> None:
        rows = [{"Id": "01p", "Name": "Acct", "Status": "Active"}]
        with mock.patch.object(dev_org, "_run_soql", return_value=_soql_result(rows)):
            out = dev_org.list_apex_classes()
            self.assertEqual(out["class_count"], 1)
            self.assertEqual(out["classes"][0]["Name"], "Acct")


# --------------------------------------------------------------------------- #
# get_apex_class                                                              #
# --------------------------------------------------------------------------- #


class GetApexClassTest(unittest.TestCase):
    def test_unsafe_name_rejected(self) -> None:
        out = dev_org.get_apex_class(name="Foo;Bar")
        self.assertIn("error", out)

    def test_includes_body_by_default(self) -> None:
        with mock.patch.object(dev_org, "_run_soql") as run:
            run.return_value = _soql_result([{"Id": "01p", "Name": "Foo", "Body": "public class Foo{}"}])
            out = dev_org.get_apex_class(name="Foo")
            self.assertEqual(out["body"], "public class Foo{}")
            self.assertIn("Body", run.call_args.args[0])

    def test_skip_body_drops_field(self) -> None:
        with mock.patch.object(dev_org, "_run_soql") as run:
            run.return_value = _soql_result([{"Id": "01p", "Name": "Foo"}])
            dev_org.get_apex_class(name="Foo", include_body=False)
            self.assertNotIn(", Body", run.call_args.args[0])

    def test_missing_class_returns_error(self) -> None:
        with mock.patch.object(dev_org, "_run_soql", return_value=_soql_result([])):
            out = dev_org.get_apex_class(name="Nope")
            self.assertIn("error", out)


# --------------------------------------------------------------------------- #
# list_apex_triggers                                                          #
# --------------------------------------------------------------------------- #


class ListApexTriggersTest(unittest.TestCase):
    def test_object_filter_validated(self) -> None:
        out = dev_org.list_apex_triggers(object_name="bad' name")
        self.assertIn("error", out)

    def test_events_flattened_from_usage_flags(self) -> None:
        rec = {
            "Id": "01q", "Name": "AccountTrg", "TableEnumOrId": "Account",
            "Status": "Active", "ApiVersion": 60.0,
            "UsageBeforeInsert": True, "UsageAfterUpdate": True,
            "UsageAfterInsert": False,
        }
        with mock.patch.object(dev_org, "_run_soql", return_value=_soql_result([rec])):
            out = dev_org.list_apex_triggers(object_name="Account")
            self.assertEqual(out["trigger_count"], 1)
            self.assertEqual(out["triggers"][0]["events"], ["BeforeInsert", "AfterUpdate"])

    def test_active_only_appends_status_clause(self) -> None:
        with mock.patch.object(dev_org, "_run_soql") as run:
            run.return_value = _soql_result([])
            dev_org.list_apex_triggers(active_only=True)
            self.assertIn("Status = 'Active'", run.call_args.args[0])


# --------------------------------------------------------------------------- #
# list_lwc_bundles + get_lwc_bundle                                           #
# --------------------------------------------------------------------------- #


class ListLwcBundlesTest(unittest.TestCase):
    def test_returns_bundle_count(self) -> None:
        rows = [{"Id": "0Rb", "DeveloperName": "myComp", "MasterLabel": "My Comp"}]
        with mock.patch.object(dev_org, "_run_soql", return_value=_soql_result(rows)):
            out = dev_org.list_lwc_bundles()
            self.assertEqual(out["bundle_count"], 1)


class GetLwcBundleTest(unittest.TestCase):
    def test_unsafe_name_rejected(self) -> None:
        out = dev_org.get_lwc_bundle(name="bad-name")
        self.assertIn("error", out)

    def test_returns_resources_when_requested(self) -> None:
        bundle_call_count = {"n": 0}

        def fake_run(soql, *, target_org, tooling):
            bundle_call_count["n"] += 1
            if bundle_call_count["n"] == 1:
                return _soql_result([{"Id": "0Rb", "DeveloperName": "myComp",
                                      "MasterLabel": "My Comp", "ApiVersion": 60.0}])
            return _soql_result([
                {"Id": "0RR1", "FilePath": "myComp/myComp.js", "Format": "js", "Source": "// js"},
                {"Id": "0RR2", "FilePath": "myComp/myComp.html", "Format": "html", "Source": "<template></template>"},
            ])

        with mock.patch.object(dev_org, "_run_soql", side_effect=fake_run):
            out = dev_org.get_lwc_bundle(name="myComp")
            self.assertEqual(out["resource_count"], 2)
            self.assertEqual(out["resources"][0]["format"], "js")

    def test_missing_bundle_returns_error(self) -> None:
        with mock.patch.object(dev_org, "_run_soql", return_value=_soql_result([])):
            out = dev_org.get_lwc_bundle(name="Nope")
            self.assertIn("error", out)


# --------------------------------------------------------------------------- #
# list_custom_fields                                                          #
# --------------------------------------------------------------------------- #


class ListCustomFieldsTest(unittest.TestCase):
    def test_object_name_validated(self) -> None:
        out = dev_org.list_custom_fields(object_name="Account; DROP TABLE")
        self.assertIn("error", out)

    def test_default_filters_to_custom_only(self) -> None:
        # Pre-v0.4.4: SOQL had `LIKE '%\_\_c' ESCAPE '\\\\'` (broken).
        # v0.4.4: SOQL has NO LIKE filter; custom-only is enforced
        # client-side by post-fetch suffix check. Verify the
        # standard fields a mixed response returns get pruned.
        rec_custom = {"QualifiedApiName": "MyField__c", "DataType": "double", "Label": "My Field"}
        rec_std = {"QualifiedApiName": "Industry", "DataType": "picklist", "Label": "Industry"}
        with mock.patch.object(dev_org, "_run_soql") as run:
            run.return_value = _soql_result([rec_custom, rec_std])
            out = dev_org.list_custom_fields(object_name="Account")
            names = [f["name"] for f in out["fields"]]
            self.assertIn("MyField__c", names)
            self.assertNotIn("Industry", names)
            self.assertEqual(out["field_count"], 1)

    def test_include_standard_returns_both(self) -> None:
        # When include_standard=True, the suffix filter is skipped so
        # both __c and standard fields appear in the response.
        rec_custom = {"QualifiedApiName": "MyField__c", "DataType": "double", "Label": "My Field"}
        rec_std = {"QualifiedApiName": "Industry", "DataType": "picklist", "Label": "Industry"}
        with mock.patch.object(dev_org, "_run_soql") as run:
            run.return_value = _soql_result([rec_custom, rec_std])
            out = dev_org.list_custom_fields(object_name="Account", include_standard=True)
            names = [f["name"] for f in out["fields"]]
            self.assertIn("MyField__c", names)
            self.assertIn("Industry", names)
            self.assertEqual(out["field_count"], 2)

    def test_soql_omits_legacy_escape_clause(self) -> None:
        # P0-B regression guard: SOQL does NOT support ESCAPE; the
        # v0.4.3 query had it and every server-side call failed with
        # MALFORMED_QUERY. Pin that the clause is gone.
        with mock.patch.object(dev_org, "_run_soql") as run:
            run.return_value = _soql_result([])
            dev_org.list_custom_fields(object_name="Account")
            soql = run.call_args.args[0]
            self.assertNotIn("ESCAPE", soql)

    def test_reference_to_flattened(self) -> None:
        rec = {
            "QualifiedApiName": "Account__c",
            "DataType": "reference",
            "Label": "Account",
            "ReferenceTo": {"referenceTo": ["Account"]},
        }
        with mock.patch.object(dev_org, "_run_soql", return_value=_soql_result([rec])):
            out = dev_org.list_custom_fields(object_name="Custom__c")
            self.assertEqual(out["fields"][0]["reference_to"], ["Account"])

    def test_pseudo_fields_dropped_by_default(self) -> None:
        # ``include_standard=True`` to let standard rows through; the pseudo
        # filter should still strip Id / SystemModstamp / IsDeleted.
        records = [
            {"QualifiedApiName": "Id", "DataType": "id"},
            {"QualifiedApiName": "IsDeleted", "DataType": "boolean"},
            {"QualifiedApiName": "SystemModstamp", "DataType": "datetime"},
            {"QualifiedApiName": "Industry", "DataType": "picklist"},
        ]
        with mock.patch.object(dev_org, "_run_soql", return_value=_soql_result(records)):
            out = dev_org.list_custom_fields(object_name="Account", include_standard=True)
            names = [f["name"] for f in out["fields"]]
            self.assertEqual(names, ["Industry"])
            self.assertEqual(out["pseudo_fields_dropped"], 3)

    def test_pseudo_fields_kept_with_opt_in(self) -> None:
        records = [
            {"QualifiedApiName": "Id", "DataType": "id"},
            {"QualifiedApiName": "Industry", "DataType": "picklist"},
        ]
        with mock.patch.object(dev_org, "_run_soql", return_value=_soql_result(records)):
            out = dev_org.list_custom_fields(
                object_name="Account",
                include_standard=True,
                include_pseudo_fields=True,
            )
            names = [f["name"] for f in out["fields"]]
            self.assertIn("Id", names)
            self.assertIn("Industry", names)
            self.assertEqual(out["pseudo_fields_dropped"], 0)


# --------------------------------------------------------------------------- #
# describe_object_full                                                        #
# --------------------------------------------------------------------------- #


class DescribeObjectFullTest(unittest.TestCase):
    def test_object_name_validated(self) -> None:
        out = dev_org.describe_object_full(object_name="bad'name")
        self.assertIn("error", out)

    def test_includes_each_subsection_when_requested(self) -> None:
        with mock.patch.object(dev_org, "list_custom_fields", return_value={"fields": [{"name": "X__c"}], "field_count": 1}), \
             mock.patch.object(dev_org.admin, "list_record_types", return_value={"record_types": [{"DeveloperName": "RT"}], "record_type_count": 1}), \
             mock.patch.object(dev_org.admin, "list_validation_rules", return_value={"rules": [{"name": "V"}], "rule_count": 1}), \
             mock.patch.object(dev_org.org_module, "list_flows_on_object", return_value={"flows": [{"label": "F"}], "flow_count": 1}):
            out = dev_org.describe_object_full(object_name="Account")
            self.assertEqual(out["field_count"], 1)
            self.assertEqual(out["record_type_count"], 1)
            self.assertEqual(out["validation_rule_count"], 1)
            self.assertEqual(out["active_flow_count"], 1)

    def test_per_section_errors_isolated(self) -> None:
        # If validation_rules fails, the rest should still come through with
        # a validation_rules_error block.
        with mock.patch.object(dev_org, "list_custom_fields", return_value={"fields": [], "field_count": 0}), \
             mock.patch.object(dev_org.admin, "list_record_types", return_value={"record_types": [], "record_type_count": 0}), \
             mock.patch.object(dev_org.admin, "list_validation_rules", return_value={"error": "VR section blew up"}), \
             mock.patch.object(dev_org.org_module, "list_flows_on_object", return_value={"flows": [], "flow_count": 0}):
            out = dev_org.describe_object_full(object_name="Account")
            self.assertIn("validation_rules_error", out)
            self.assertEqual(out["validation_rules_error"], "VR section blew up")
            self.assertEqual(out["field_count"], 0)


# --------------------------------------------------------------------------- #
# list_orgs                                                                   #
# --------------------------------------------------------------------------- #


class ListOrgsTest(unittest.TestCase):
    def test_dedupes_and_normalizes_buckets(self) -> None:
        payload = {
            "status": 0,
            "result": {
                "nonScratchOrgs": [
                    {"alias": "prod", "username": "user@example.com",
                     "instanceUrl": "https://example.my.salesforce.com",
                     "isDefaultUsername": True},
                ],
                "scratchOrgs": [
                    {"alias": "scratch", "username": "scr@scratch.com",
                     "expirationDate": "2026-12-31"},
                    # Duplicate of nonScratchOrgs entry — should NOT appear twice.
                    {"alias": "prod-dup", "username": "user@example.com"},
                ],
                "devHubs": [],
                "sandboxes": [],
                "other": [],
            },
        }
        with mock.patch.object(dev_org.sf_cli, "run_sf_json", return_value=payload):
            out = dev_org.list_orgs()
            self.assertEqual(out["org_count"], 2)
            usernames = {o["username"] for o in out["orgs"]}
            self.assertEqual(usernames, {"user@example.com", "scr@scratch.com"})
            scratch = next(o for o in out["orgs"] if o["username"] == "scr@scratch.com")
            self.assertTrue(scratch["is_scratch"])
            self.assertEqual(scratch["expiration_date"], "2026-12-31")
            prod = next(o for o in out["orgs"] if o["username"] == "user@example.com")
            self.assertTrue(prod["is_default"])
            self.assertFalse(prod["is_scratch"])

    def test_sf_error_surfaced(self) -> None:
        # When sf reports a hard failure, dev_org.list_orgs should pass it
        # through unchanged so the MCP client sees the original message.
        bad = {"status": 1, "error": "sf not authenticated", "args": ["org", "list"]}
        with mock.patch.object(dev_org.sf_cli, "run_sf_json", return_value=bad):
            out = dev_org.list_orgs()
            self.assertEqual(out["error"], "sf not authenticated")


if __name__ == "__main__":
    unittest.main()
