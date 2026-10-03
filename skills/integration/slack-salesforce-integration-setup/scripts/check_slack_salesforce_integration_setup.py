#!/usr/bin/env python3
"""Check a Slack and Salesforce connection plan against documented platform constraints.

Stdlib only. The plan is a JSON file (see references/metadata-examples.md) that records
the decisions the platform constrains. Rules are grounded on the Slack Help Center
article Connect Salesforce and Slack (slack.com/help/articles/30754346665747) and the
Slack Integrations guide, Spring '26 (slack_apps.pdf), both fetched 2026-10-03.

Correction (2026-10-03): the previous stub required a permission set named
SlackStandardUser and capped connections at 20 orgs. Neither name nor cap appears in
the fetched sources as stated; the documented requirement is the Connect Salesforce with
Slack system permission for every Slack user, and the documented allowance is "up to 20
additional Salesforce orgs" on Pro, Business+, and Enterprise plans.

Rules
  SSI-GOV-01     ERROR  government_cloud is true (Slack cannot connect; apps unsupported in
                        Government Cloud and Government Cloud Plus).
  SSI-COMP-01    ERROR  compliance_requirements include FedRAMP, HIPAA, or Blackjack (not certified).
  SSI-ORGS-01    ERROR  additional_orgs_connected above 20, or above 0 on a plan other than Pro,
                        Business+, or Enterprise (multiple orgs are documented for those plans).
  SSI-ROLE-01    WARN   activate_by_role is not Owner or Salesforce Admin system role; approve_by_role
                        is not Salesforce System Admin.
  SSI-MAP-01     ERROR  unified_employee_license_users is true and automatic_account_mapping is false.
  SSI-PERM-01    ERROR  users_have_connect_permission is false.
  SSI-IP-01      WARN   salesforce_ip_restrictions is true (features may not work as expected).
  SSI-UNFURL-01  ERROR  unfurl_option is not one of the six documented options.
  SSI-UNFURL-02  WARN   a data-viewable unfurl option is used with sensitive objects and no Slack Record
                        Layouts for them.
  SSI-LEGACY-01  WARN   integration names the Slack-built legacy app (no new installations).

Usage
  python3 check_slack_salesforce_integration_setup.py --plan docs/slack/slack-connection-plan.json [--strict]
  python3 check_slack_salesforce_integration_setup.py --manifest-dir <folder with *slack*plan*.json>
  python3 check_slack_salesforce_integration_setup.py --self-test

Exit codes: 0 clean (WARN allowed unless --strict); 1 on ERROR, a missing file, or WARN with --strict.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

UNFURL_OPTIONS = {
    "Do Not Share Data",
    "Preview Button Only",
    "Object Type and Preview Button",
    "Name, Type, and Preview Button",
    "Data Viewable by Slack Default Render User",
    "Data Viewable by User Sharing the Link",
}
DATA_VIEWABLE = {"Data Viewable by Slack Default Render User", "Data Viewable by User Sharing the Link"}
MULTI_ORG_PLANS = {"pro", "business+", "enterprise", "enterprise grid"}
ACTIVATION_ROLES = {"owner", "workspace owner", "org owner", "salesforce admin system role"}


def check_plan(path: Path) -> list[str]:
    try:
        plan = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"ERROR SSI-PLAN-00 {path}: cannot read plan ({exc})"]
    f: list[str] = []
    if plan.get("government_cloud") is True:
        f.append(f"ERROR SSI-GOV-01 {path}: Slack can't connect to Government Cloud orgs, and Salesforce for Slack apps "
                 f"aren't supported in Government Cloud or Government Cloud Plus")
    blocked = {c for c in plan.get("compliance_requirements", []) if str(c).strip().lower() in {"fedramp", "hipaa", "blackjack"}}
    if blocked:
        f.append(f"ERROR SSI-COMP-01 {path}: {sorted(blocked)} required; Salesforce for Slack isn't FedRAMP or HIPAA "
                 f"certified and can't be used within Blackjack")
    extra = int(plan.get("additional_orgs_connected", 0) or 0)
    plan_name = str(plan.get("slack_plan", "")).strip().lower()
    if extra > 20:
        f.append(f"ERROR SSI-ORGS-01 {path}: {extra} additional orgs; the documented allowance is up to 20 additional orgs")
    elif extra > 0 and plan_name not in MULTI_ORG_PLANS:
        f.append(f"ERROR SSI-ORGS-01 {path}: additional orgs on plan '{plan.get('slack_plan')}'; multiple orgs are "
                 f"documented for Pro, Business+, and Enterprise plans")
    if str(plan.get("activate_by_role", "")).strip().lower() not in ACTIVATION_ROLES:
        f.append(f"WARN SSI-ROLE-01 {path}: activation by '{plan.get('activate_by_role')}'; Owners and people with the "
                 f"Salesforce Admin system role in Slack can activate")
    if str(plan.get("approve_by_role", "")).strip().lower() != "salesforce system admin":
        f.append(f"WARN SSI-ROLE-01 {path}: approval by '{plan.get('approve_by_role')}'; a Salesforce System Admin approves")
    if plan.get("unified_employee_license_users") is True and plan.get("automatic_account_mapping") is not True:
        f.append(f"ERROR SSI-MAP-01 {path}: Unified Employee license users can only be mapped automatically; turn on "
                 f"automatic account mapping")
    if plan.get("users_have_connect_permission") is False:
        f.append(f"ERROR SSI-PERM-01 {path}: every Slack user, including the installing owner, needs a permission set "
                 f"with Connect Salesforce with Slack")
    if plan.get("salesforce_ip_restrictions") is True:
        f.append(f"WARN SSI-IP-01 {path}: Salesforce IP restrictions can stop Slack features from working as expected")
    option = plan.get("unfurl_option")
    if option not in UNFURL_OPTIONS:
        f.append(f"ERROR SSI-UNFURL-01 {path}: unfurl_option '{option}' is not a documented data sharing option")
    elif option in DATA_VIEWABLE and plan.get("sensitive_objects") and not plan.get("slack_record_layouts_for_sensitive_objects"):
        f.append(f"WARN SSI-UNFURL-02 {path}: '{option}' shows record data in the channel; add URL Unfurling Slack Record "
                 f"Layouts for {plan.get('sensitive_objects')} or use a preview-button option")
    if "legacy" in str(plan.get("integration", "")).lower() or "slack-built" in str(plan.get("integration", "")).lower():
        f.append(f"WARN SSI-LEGACY-01 {path}: the Slack-built Salesforce app no longer supports new installations; use "
                 f"the Salesforce-built integrations")
    return f


def find_plans(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.json") if "slack" in p.name.lower() and "plan" in p.name.lower())


def self_test() -> int:
    here = Path(__file__).resolve().parent / "fixtures"
    good = [x for p in find_plans(here / "good") for x in check_plan(p)]
    bad = [x for p in find_plans(here / "bad") for x in check_plan(p)]
    expected = {"SSI-GOV-01", "SSI-COMP-01", "SSI-ORGS-01", "SSI-ROLE-01", "SSI-MAP-01", "SSI-PERM-01",
                "SSI-IP-01", "SSI-UNFURL-01", "SSI-UNFURL-02", "SSI-LEGACY-01"}
    seen = {x.split()[1] for x in bad}
    print(f"good fixtures: {len(good)} finding(s) (expected 0)")
    for x in good:
        print(f"  unexpected: {x}")
    print(f"bad fixtures: rules seen {sorted(seen)}; missing {sorted(expected - seen)}")
    return 0 if not good and expected <= seen else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Check a Slack and Salesforce connection plan against documented constraints.")
    ap.add_argument("--plan", help="Path to a connection plan JSON file.")
    ap.add_argument("--manifest-dir", default=None, help="Folder to search for *slack*plan*.json files.")
    ap.add_argument("--strict", action="store_true", help="Exit 1 on WARN as well as ERROR.")
    ap.add_argument("--self-test", action="store_true", help="Run the bundled fixtures and exit.")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.plan:
        plans = [Path(args.plan)]
        if not plans[0].exists():
            print(f"ERROR SSI-PLAN-00 {plans[0]}: file not found")
            return 1
    else:
        root = Path(args.manifest_dir or ".")
        if not root.exists():
            print(f"ERROR SSI-PLAN-00 {root}: folder not found")
            return 1
        plans = find_plans(root)
    findings = [x for p in plans for x in check_plan(p)]
    for x in findings:
        print(x)
    errors = [x for x in findings if x.startswith("ERROR")]
    warns = [x for x in findings if x.startswith("WARN")]
    print(f"Checked {len(plans)} plan(s): {len(errors)} error(s), {len(warns)} warning(s).")
    return 1 if errors or (args.strict and warns) else 0


if __name__ == "__main__":
    sys.exit(main())
