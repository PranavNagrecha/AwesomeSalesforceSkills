# Healthcare API Examples: Scope Metadata and Requests

Deployable OAuth custom scope metadata for the Salesforce Healthcare API, plus the request shapes for each of the three Health Cloud API layers. Scope names come from the Healthcare API guide's Authorization page. Metadata fields come from the Metadata API Developer Guide, Version 67.0 (OauthCustomScope, ExtlClntAppOauthSettings, ExtlClntAppOauthConfigurablePolicies).

## File: `force-app/main/default/oauthcustomscopes/system_condition_read.oauthcustomscope-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<OauthCustomScope xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Read Condition resources in the Healthcare API</description>
    <developerName>system_condition_read</developerName>
    <isProtected>false</isProtected>
    <isPublic>false</isPublic>
    <masterLabel>system_condition_read</masterLabel>
</OauthCustomScope>
```

## File: `force-app/main/default/oauthcustomscopes/system_bundle_write.oauthcustomscope-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<OauthCustomScope xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Write Bundle requests in the Healthcare API</description>
    <developerName>system_bundle_write</developerName>
    <isProtected>false</isProtected>
    <isPublic>false</isPublic>
    <masterLabel>system_bundle_write</masterLabel>
</OauthCustomScope>
```

Notes from the Metadata API guide: `masterLabel` "can include only alphanumeric characters and underscores" and "can't contain spaces", which fits the Healthcare API scope names. The guide also says `description` "can only include alphanumeric characters", yet its own sample description contains spaces. UNVERIFIED (2026-10-03): whether spaces are accepted in `description`; if a deploy rejects it, remove the spaces. Whether the Healthcare API matches the scope on `developerName` or on `masterLabel` is not stated, so this example sets both to the same value.

## File: `force-app/main/default/extlClntAppOauthSettings/Healthcare_Feed.ecaOauth-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ExtlClntAppOauthSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <externalClientApplication>Healthcare_Feed</externalClientApplication>
    <label>Healthcare Feed OAuth Settings</label>
    <commaSeparatedOauthScopes>RefreshToken</commaSeparatedOauthScopes>
</ExtlClntAppOauthSettings>
```

## File: `force-app/main/default/extlClntAppOauthPolicies/Healthcare_Feed.ecaOauthPlcy-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ExtlClntAppOauthConfigurablePolicies xmlns="http://soap.sforce.com/2006/04/metadata">
    <externalClientApplication>Healthcare_Feed</externalClientApplication>
    <label>Healthcare Feed OAuth Policies</label>
    <commaSeparatedCustomScopes>system_condition_read,system_bundle_write</commaSeparatedCustomScopes>
    <permittedUsersPolicyType>AdminApprovedPreAuthorized</permittedUsersPolicyType>
    <commaSeparatedPermissionSet>Healthcare_Feed_Integration</commaSeparatedPermissionSet>
    <ipRelaxationPolicyType>Enforce</ipRelaxationPolicyType>
</ExtlClntAppOauthConfigurablePolicies>
```

These two files assume an `ExternalClientApplication` named `Healthcare_Feed` already exists (see `integration/oauth-flows-and-connected-apps` for the header file) and a permission set `Healthcare_Feed_Integration`. `commaSeparatedCustomScopes` requires API 61.0 or later. UNVERIFIED (2026-10-03): the source-format file names above follow the documented suffixes (`.ecaOauth`, `.ecaOauthPlcy`) and folders; retrieve once from a sandbox and keep whatever names the retrieve returns.

## Manifest: `manifest/package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>system_bundle_write</members>
        <members>system_condition_read</members>
        <name>OauthCustomScope</name>
    </types>
    <types>
        <members>*</members>
        <name>ExtlClntAppOauthSettings</name>
    </types>
    <types>
        <members>*</members>
        <name>ExtlClntAppOauthConfigurablePolicies</name>
    </types>
    <version>67.0</version>
</Package>
```

The wildcard follows the Metadata API guide's own samples for the external client app types. The `refresh_token` requirement comes from the Healthcare API guide: "You must assign the refresh_token scope to the external client app."

## Request: Healthcare API Condition read (layer 3)

```http
GET /clinical-summary/fhir-r4/v1/Condition HTTP/1.1
Host: api.healthcloud.salesforce.com
Authorization: Bearer <token issued to Healthcare_Feed>
```

Sandbox: `api.healthcloud.salesforce.com/sandBox/clinical-summary/fhir-r4/v1/Condition`. EU, CA, and AU orgs use `eu.`, `ca.`, and `au.` prefixed hosts.

## Request: Healthcare API batch Bundle with a dependency (layer 3)

```http
POST /bundle/fhir-r4/v1/Bundle HTTP/1.1
Host: api.healthcloud.salesforce.com
Authorization: Bearer <token issued to Healthcare_Feed>
Content-Type: application/json
```

```json
{
  "resourceType": "Bundle",
  "type": "batch",
  "entry": [
    {
      "fullUrl": "urn:uuid:4d3c2b1a-0000-4000-8000-000000000001",
      "resource": {
        "resourceType": "Goal",
        "lifecycleStatus": "proposed",
        "description": { "text": "HbA1c below 7 percent" },
        "subject": { "reference": "Patient/<patient id>" }
      },
      "request": { "method": "POST", "url": "Goal" }
    },
    {
      "fullUrl": "urn:uuid:4d3c2b1a-0000-4000-8000-000000000002",
      "resource": {
        "resourceType": "CarePlan",
        "status": "active",
        "intent": "plan",
        "subject": { "reference": "Patient/<patient id>" },
        "goal": [ { "reference": "urn:uuid:4d3c2b1a-0000-4000-8000-000000000001" } ]
      },
      "request": { "method": "POST", "url": "CarePlan" }
    }
  ]
}
```

If the Goal entry fails, the CarePlan entry depends on it through the `urn:uuid:` reference, so the API cancels it and returns 424 for that entry. Resend both after fixing the Goal.

UNVERIFIED (2026-10-03): the `/bundle/fhir-r4/v1/Bundle` path is derived from the documented URL format (`<Domain>/<FHIR module>/<FHIR version>/<API version>/<Resource type>`, module `bundle`) rather than copied from a fetched example. Whether the token also needs `system_goal_write` and `system_carePlan_write` for resources inside the Bundle, and which Goal and CarePlan elements the Salesforce mapping requires, are not stated in the fetched pages.

## Request: Business API medication statement (layer 2)

```http
POST /services/data/v67.0/connect/health/clinical/patients/001RM000005Il81YAC/medication-statement HTTP/1.1
Host: MyDomainName.my.salesforce.com
Authorization: Bearer <org access token>
Content-Type: application/json
```

```json
{
  "medicationStatement": {
    "identifier": [
      {
        "type": { "text": "Pharmacy reference", "coding": [ { "display": "Pharmacy reference", "code": "PHR", "isActive": true, "use": "Identifier" } ] },
        "value": "RX-20261003-0001",
        "use": "Official",
        "sourceSystem": "https://pharmacy.example.com",
        "sourceSystemId": "RX-20261003-0001"
      }
    ]
  }
}
```

The resource path, `Available version 54.0`, and the `identifier` element structure come from the Agentforce Health Developer Guide, Medication Statements (POST). UNVERIFIED (2026-10-03): the guide's example body is much longer, and which other elements (medication, status, dates) are required for a successful create is not stated in the excerpt read; start from the guide's full JSON example.

## Verify

```bash
python3 skills/apex/health-cloud-apis/scripts/check_health_cloud_apis.py --manifest-dir force-app/main/default
```

No `HC-*` ERROR should remain: no `/services/data/.../fhir` paths, no `healthcare` scope, no `transaction` bundles.
