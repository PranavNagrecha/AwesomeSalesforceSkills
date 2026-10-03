# Metadata Examples: Client Credentials External Client App and Org Flow Hardening

Deployable files for a system-to-system integration that uses the OAuth 2.0 client credentials flow through an external client app, plus the org setting that blocks the username-password and user-agent flows. Field names and allowed values come from the Metadata API Developer Guide, Version 67.0 (ExternalClientApplication, ExtlClntAppGlobalOauthSettings, ExtlClntAppOauthSettings, ExtlClntAppOauthConfigurablePolicies, OauthOidcSettings). Access to these types requires the org setting "Opt in to External Client Apps"; the OAuth plugin types also require "Allow Access to OAuth Consumer Secrets via Metadata API".

## File: `force-app/main/default/externalClientApps/Order_Sync.eca-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ExternalClientApplication xmlns="http://soap.sforce.com/2006/04/metadata">
    <contactEmail>integration-owner@example.com</contactEmail>
    <description>Middleware order sync, client credentials flow</description>
    <distributionState>Local</distributionState>
    <isProtected>false</isProtected>
    <label>Order Sync</label>
</ExternalClientApplication>
```

## File: `force-app/main/default/extlClntAppOauthSettings/Order_Sync.ecaOauth-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ExtlClntAppOauthSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <externalClientApplication>Order_Sync</externalClientApplication>
    <label>Order Sync OAuth Settings</label>
    <commaSeparatedOauthScopes>Api</commaSeparatedOauthScopes>
</ExtlClntAppOauthSettings>
```

`Api` "allows access to the logged-in user's account over the APIs". Do not add `Full`, `Web`, or `RefreshToken`: the client credentials flow filters them out of the token response anyway.

## File: `force-app/main/default/extlClntAppOauthPolicies/Order_Sync.ecaOauthPlcy-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ExtlClntAppOauthConfigurablePolicies xmlns="http://soap.sforce.com/2006/04/metadata">
    <externalClientApplication>Order_Sync</externalClientApplication>
    <label>Order Sync OAuth Policies</label>
    <isClientCredentialsFlowEnabled>true</isClientCredentialsFlowEnabled>
    <clientCredentialsFlowUser>order.sync@example.com.prod</clientCredentialsFlowUser>
    <permittedUsersPolicyType>AdminApprovedPreAuthorized</permittedUsersPolicyType>
    <commaSeparatedPermissionSet>Order_Sync_Integration</commaSeparatedPermissionSet>
    <ipRelaxationPolicyType>Enforce</ipRelaxationPolicyType>
    <refreshTokenPolicyType>Zero</refreshTokenPolicyType>
</ExtlClntAppOauthConfigurablePolicies>
```

- `clientCredentialsFlowUser`: "The execution user for the OAuth 2.0 client credentials flow. Salesforce returns access tokens on behalf of this user. This user must have the API Only permission." API 60.0+.
- `permittedUsersPolicyType` values: `AdminApprovedPreAuthorized`, `AllSelfAuthorized`. `commaSeparatedPermissionSet` is used with `AdminApprovedPreAuthorized`.
- `ipRelaxationPolicyType` values: `Enforce`, `Bypass`, `Bypass_2factor`, `Enforce_RelaxRefresh`.
- `refreshTokenPolicyType` values: `Infinite`, `SpecificInactivity`, `SpecificLifetime`, `Zero`. This flow issues no refresh token, so `Zero` states the intent.

UNVERIFIED (2026-10-03): `commaSeparatedPermissionSet` is described as "Permission set IDs in a comma-separated list", while the guide's sample uses a name (`PermSetExample`). Retrieve the policies from a sandbox after configuring them in Setup and keep whatever form the retrieve returns. The source-format file names follow the documented suffixes (`.eca`, `.ecaOauth`, `.ecaOauthPlcy`) and folders; confirm them against a retrieve.

## File kept out of source control: `ExtlClntAppGlobalOauthSettings`

The Metadata API guide says this type holds "private and sensitive OAuth consumer information that can't be packaged and must not be added to source control". Add its folder to `.forceignore` and `.gitignore`:

```text
# .forceignore and .gitignore
**/extlClntAppGlobalOauthSets/**
```

Enable the plugin-side switch (`isClientCredentialsFlowEnabled`, API 60.0+) in Setup or from a pipeline step that writes the file at deploy time and never commits it. UNVERIFIED (2026-10-03): whether a global settings file without `consumerKey` and `consumerSecret` deploys cleanly is not stated in the guide.

## File: `force-app/main/default/settings/OauthOidc.settings-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<OauthOidcSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <blockOAuthUnPwFlow>true</blockOAuthUnPwFlow>
    <blockOAuthUsrAgtFlow>true</blockOAuthUsrAgtFlow>
    <isPkceRequired>true</isPkceRequired>
    <oAuthCdCrdtFlowEnable>false</oAuthCdCrdtFlowEnable>
</OauthOidcSettings>
```

- `blockOAuthUnPwFlow` and `blockOAuthUsrAgtFlow` default to false in the type; orgs created Summer '23 or later already block username-password in Setup.
- `isPkceRequired` (API 59.0+) requires PKCE for every variation of the authorization code flow. Any web server flow client that does not send a PKCE challenge stops working.
- This file corrects the guide's sample, which uses typographic quotes and does not parse.

Blocking a flow "can break managed packages, mobile apps, and other integrations that use it." Deploy to a sandbox first and watch login history for failures.

## Manifest: `manifest/package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Order_Sync</members>
        <name>ExternalClientApplication</name>
    </types>
    <types>
        <members>*</members>
        <name>ExtlClntAppOauthSettings</name>
    </types>
    <types>
        <members>*</members>
        <name>ExtlClntAppOauthConfigurablePolicies</name>
    </types>
    <types>
        <members>OauthOidc</members>
        <name>Settings</name>
    </types>
    <version>67.0</version>
</Package>
```

## Verify

```bash
python3 skills/integration/oauth-flows-and-connected-apps/scripts/check_oauth_flows_and_connected_apps.py --manifest-dir force-app/main/default
```

Then request a token as the middleware will (see `references/examples.md`) and confirm the `id` URL in the response names the execution user.
