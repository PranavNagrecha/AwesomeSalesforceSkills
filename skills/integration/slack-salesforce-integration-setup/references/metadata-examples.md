# Metadata Examples: Connection Plan and Slack Permission Set

Two artifacts make the Slack connection repeatable: a connection plan that records the decisions the platform constrains (checked by `scripts/check_slack_salesforce_integration_setup.py`), and a permission set that grants the Connect Salesforce with Slack system permission. Constraints come from the Slack Help Center article Connect Salesforce and Slack and the Slack Integrations guide, Spring '26.

## File: `docs/slack/slack-connection-plan.json`

```json
{
  "salesforce_org_url": "https://acme.my.salesforce.com",
  "government_cloud": false,
  "compliance_requirements": ["SOC2"],
  "slack_plan": "Business+",
  "integration": "salesforce-built",
  "additional_orgs_connected": 2,
  "request_by_role": "Workspace Owner",
  "approve_by_role": "Salesforce System Admin",
  "activate_by_role": "Owner",
  "account_mapping_field": "Email",
  "automatic_account_mapping": true,
  "unified_employee_license_users": false,
  "users_have_connect_permission": true,
  "salesforce_ip_restrictions": false,
  "unfurl_option": "Name, Type, and Preview Button",
  "sensitive_objects": ["Opportunity", "Contract"],
  "slack_record_layouts_for_sensitive_objects": true
}
```

| Field | Constraint it records |
|---|---|
| `government_cloud` | Slack cannot connect to Government Cloud orgs; apps are unsupported in Government Cloud and Government Cloud Plus |
| `compliance_requirements` | Salesforce for Slack is not FedRAMP or HIPAA certified and cannot be used within Blackjack |
| `additional_orgs_connected` | Pro, Business+, and Enterprise plans can connect up to 20 additional orgs |
| `activate_by_role` | Activation: Owners or people with the Salesforce Admin system role in Slack |
| `automatic_account_mapping` | Unified Employee license users can only be mapped automatically |
| `users_have_connect_permission` | Every Slack user, including the installing owner, needs Connect Salesforce with Slack |
| `salesforce_ip_restrictions` | Features may not work with Salesforce IP restrictions enabled |
| `unfurl_option` | One of the six documented data sharing options |

This file is a planning artifact for the skill's checker, not Salesforce metadata.

## File: `force-app/main/default/permissionsets/Slack_Connected_User.permissionset-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Grants Connect Salesforce with Slack to every user who uses Salesforce apps in Slack, including the workspace owner who installs them.</description>
    <hasActivationRequired>false</hasActivationRequired>
    <label>Slack Connected User</label>
    <userPermissions>
        <enabled>true</enabled>
        <name>ConnectSalesforceWithSlack</name>
    </userPermissions>
</PermissionSet>
```

UNVERIFIED (2026-10-03): the API name `ConnectSalesforceWithSlack` for the Connect Salesforce with Slack system permission is not printed in the fetched guides. Enable the permission on a permission set in a sandbox, retrieve it (`sf project retrieve start --metadata PermissionSet:Slack_Connected_User`), and keep the name the retrieve returns. The guide warns that some licenses do not support the permission, so assignment fails for those users.

## Manifest: `manifest/package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Slack_Connected_User</members>
        <name>PermissionSet</name>
    </types>
    <version>67.0</version>
</Package>
```

## Verify

```bash
python3 skills/integration/slack-salesforce-integration-setup/scripts/check_slack_salesforce_integration_setup.py --plan docs/slack/slack-connection-plan.json
```

Then, after the three-step connection, sign in to Slack as a mapped low-access user and confirm the Salesforce app appears and a shared Opportunity link shows only the name, type, and preview button.
