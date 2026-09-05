# Metadata Examples: Connected Apps, External Client Apps, Named + External Credentials

Deployable shapes for the four auth artefacts an admin actually owns. Every element name,
enum value, and default below comes from the Metadata API Developer Guide
(https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf) — `ConnectedApp`,
`ExternalClientApplication` and its `ExtlClntApp*` siblings, `NamedCredential`, `ExternalCredential`.

## Pick the artefact first

| Integration shape | Artefact | DX folder / suffix |
|---|---|---|
| External system calls Salesforce, no human in the loop (JWT bearer or client credentials) | `ConnectedApp` (existing orgs) or an External Client App (net-new) | `connectedApps/*.connectedApp-meta.xml` |
| Net-new inbound integration in a Spring '26+ org | `ExternalClientApplication` + `ExtlClntAppGlobalOauthSettings` + `ExtlClntAppOauthSettings` + `ExtlClntAppOauthConfigurablePolicies` | `externalClientApps/*.eca-meta.xml`, `extlClntAppGlobalOauthSets/*.ecaGlblOauth-meta.xml`, `extlClntAppOauthSettings/*.ecaOauth-meta.xml`, `extlClntAppOauthPolicies/*.ecaOauthPlcy-meta.xml` |
| A person authorises a third-party app against their own access (web server flow) | `ConnectedApp` / ECA with `callbackUrl` + PKCE | as above |
| Salesforce calls out to someone else's API | `NamedCredential` (endpoint) + `ExternalCredential` (principal) | `namedCredentials/*.namedCredential-meta.xml`, `externalCredentials/*.externalCredential-meta.xml` |
| Org-wide "only admin-approved apps may call the API" switch | `ConnectedAppSettings` | `settings/ConnectedApp.settings-meta.xml` |

The suffixes and folders are the guide's own: `ConnectedApp` components "have the suffix
`.connectedApp` and are stored in the `connectedApps` folder"; `ExternalClientApplication`
"have the suffix `.eca` and are stored in the `externalClientApps` folder";
`ExtlClntAppGlobalOauthSettings` "have the suffix `.ecaGlblOauth` and are stored in the
`extlClntAppGlobalOauthSets` folder"; `ExtlClntAppOauthSettings` → `.ecaOauth` in
`extlClntAppOauthSettings`; `ExtlClntAppOauthConfigurablePolicies` → `.ecaOauthPlcy` in
`extlClntAppOauthPolicies`; `NamedCredential` → `.namedCredential` in `namedCredentials`;
`ExternalCredential` → `.externalCredential` in `externalCredentials`.

---

## 1. Server-to-server JWT bearer connected app

`force-app/main/default/connectedApps/Billing_Sync_JWT.connectedApp-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ConnectedApp xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Billing Sync JWT</label>
    <contactEmail>integration-owner@example.com</contactEmail>
    <description>Headless sync from the billing platform. JWT bearer only; no interactive login.</description>
    <oauthConfig>
        <callbackUrl>https://example.com/oauth/callback</callbackUrl>
        <certificate>MIIFtzCCA5+gAwIBAgIUExampleCertificateBodyGoesHere...</certificate>
        <scopes>Api</scopes>
        <scopes>RefreshToken</scopes>
        <isAdminApproved>true</isAdminApproved>
        <isConsumerSecretOptional>false</isConsumerSecretOptional>
        <isIntrospectAllTokens>false</isIntrospectAllTokens>
    </oauthConfig>
    <oauthPolicy>
        <ipRelaxation>ENFORCE</ipRelaxation>
        <refreshTokenPolicy>specific_inactivity:7:DAYS</refreshTokenPolicy>
    </oauthPolicy>
    <permissionSetName>Billing_Sync_Integration</permissionSetName>
    <ipRanges>
        <description>Billing platform egress</description>
        <start>203.0.113.10</start>
        <end>203.0.113.20</end>
    </ipRanges>
</ConnectedApp>
```

**How to read it**

- `label` and `contactEmail` are the only two fields the guide marks **Required** on `ConnectedApp` itself.
- `callbackUrl` is **Required** on `ConnectedAppOauthConfig`, so it carries a value even on an
  app whose only flow is JWT bearer. Multiple values go in the *same* element separated by line
  breaks — "You must separate each callback URL with line breaks. To enter a new line
  programmatically, use the `\r` line break character."
- `certificate` is "the PEM-encoded certificate string, if the app uses a certificate." This is
  the public half of the key pair the caller signs its JWT assertion with.
- `scopes` here is the deploy-time enum (`Api`, `RefreshToken`). The guide lists a *different*,
  shorter set of valid values "when retrieving metadata" — a round trip does not necessarily
  return the tokens you deployed.
- `isAdminApproved` set to `true` means "only users with the appropriate profile or permission
  set can access the app. These users don't have to approve the app before they can access it."
  It is the precondition for `permissionSetName` and `profileName`: "To use this field, the
  `isAdminApproved` field on the `ConnectedAppOauthConfig` subtype must be set to true."
- `permissionSetName` takes one name per line; `profileName` is a repeating element. Deploying an
  empty `<permissionSetName></permissionSetName>` **removes all** permission sets from the app.
- `ipRelaxation` is **Required** on `ConnectedAppOauthPolicy`. `ENFORCE` (the default) "enforces
  the IP restrictions configured for the org."
- `refreshTokenPolicy` is **Required**. The default is `infinite` — "the refresh token is used
  indefinitely, unless revoked by the user or Salesforce admin." `specific_inactivity:7:DAYS`
  means the token dies if it is not exchanged within seven days, and the seven-day window resets
  each time it is used.
- `ipRanges` entries need `start` and `end` (both Required); `description` is optional.
- There is deliberately no `isPkceRequired` here. The guide scopes that field to "variations of
  the OAuth 2.0 authorization code flow … including the web server flow and Authorization Code
  and Credentials Flow" — a JWT bearer app has no authorization code to protect. Set it on the
  web server app in the next example instead.

## 2. Web server flow connected app for a partner portal

`force-app/main/default/connectedApps/Partner_Portal_Web.connectedApp-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ConnectedApp xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Partner Portal Web</label>
    <contactEmail>integration-owner@example.com</contactEmail>
    <description>Partner users authorise the portal against their own Salesforce access.</description>
    <oauthConfig>
        <callbackUrl>https://portal.example.com/oauth/callback
https://portal-uat.example.com/oauth/callback</callbackUrl>
        <scopes>Api</scopes>
        <scopes>RefreshToken</scopes>
        <scopes>OpenID</scopes>
        <isAdminApproved>true</isAdminApproved>
        <isConsumerSecretOptional>false</isConsumerSecretOptional>
        <isPkceRequired>true</isPkceRequired>
        <isSecretRequiredForRefreshToken>true</isSecretRequiredForRefreshToken>
        <isRefreshTokenRotationEnabled>true</isRefreshTokenRotationEnabled>
        <idTokenConfig>
            <idTokenIncludeStandardClaims>true</idTokenIncludeStandardClaims>
            <idTokenValidity>10</idTokenValidity>
        </idTokenConfig>
    </oauthConfig>
    <oauthPolicy>
        <ipRelaxation>ENFORCE_RELAXREFRESH</ipRelaxation>
        <refreshTokenPolicy>specific_lifetime:90:DAYS</refreshTokenPolicy>
    </oauthPolicy>
    <profileName>Partner Community User</profileName>
    <sessionPolicy>
        <sessionTimeout>120</sessionTimeout>
    </sessionPolicy>
</ConnectedApp>
```

**How to read it**

- Both callback URLs live inside one `<callbackUrl>` element, separated by a raw line break.
  "At run time, Salesforce validates the callback URL specified by the app by matching it with
  one of the values."
- `isPkceRequired`: "If set to `true`, the PKCE extension is required and any authorization code
  flow variations that don't implement it fail." The guide's default for `ConnectedApp` is
  `false`, and it "always recommend[s] implementing PKCE for public clients" and "strongly
  recommend[s]" it for private clients — so this is a deliberate opt-in, not a default you inherit.
- `isRefreshTokenRotationEnabled` (API 60.0+): a new refresh token is issued on every refresh and
  the old one is invalidated. Reusing an invalidated token deletes "the current refresh token and
  its associated access tokens" — a client that caches the first token it ever saw will lock itself out.
- `idTokenValidity` accepts 1–720 minutes and defaults to 2.
- `ENFORCE_RELAXREFRESH` "enforces the IP restrictions configured for the org … However, this
  option bypasses these restrictions when the connected app uses refresh tokens to get access tokens."
- `sessionPolicy/sessionTimeout` is the app's own session length; "If you don't set a value,
  Salesforce uses the timeout value in the connected app user's profile."

## 3. The same JWT integration as an External Client App

Salesforce's own wording, in the `ConnectedApp` section: "Connected apps creation is restricted as
of Spring '26. You can use existing connected apps during and after Spring '26. However, we
recommend using external client apps instead. If you must continue creating connected apps,
contact Salesforce Support." An ECA is four files, not one: a header, the global OAuth settings
(secrets), the developer OAuth settings (scopes, trusted IPs), and the admin policies.

Access is gated in Setup: `ExternalClientApplication` "requires orgs to enable the **Opt in to
External Client Apps** permission", the OAuth plugin types require the **Allow Access to OAuth
Consumer Secrets via Metadata API** permission, and the policy types require the **View all
External Client Apps, view their settings, and edit their policies** user permission.

`force-app/main/default/externalClientApps/Billing_Sync_ECA.eca-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ExternalClientApplication xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Billing Sync ECA</label>
    <contactEmail>integration-owner@example.com</contactEmail>
    <description>Headless sync from the billing platform, JWT bearer.</description>
    <distributionState>Local</distributionState>
    <isProtected>false</isProtected>
</ExternalClientApplication>
```

`force-app/main/default/extlClntAppGlobalOauthSets/Billing_Sync_ECA_glbl.ecaGlblOauth-meta.xml`
— the guide says this type holds "private and sensitive OAuth consumer information that can't be
packaged and **must not be added to source control**". Treat the block below as the shape, not as
a file you commit.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ExtlClntAppGlobalOauthSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Billing Sync ECA Global OAuth</label>
    <externalClientApplication>Billing_Sync_ECA</externalClientApplication>
    <callbackUrl>https://example.com/oauth/callback</callbackUrl>
    <certificate>MIIFtzCCA5+gAwIBAgIUExampleCertificateBodyGoesHere...</certificate>
    <isPkceRequired>true</isPkceRequired>
    <isConsumerSecretOptional>false</isConsumerSecretOptional>
    <isIntrospectAllTokens>false</isIntrospectAllTokens>
    <isSecretRequiredForRefreshToken>true</isSecretRequiredForRefreshToken>
    <shouldRotateConsumerKey>false</shouldRotateConsumerKey>
    <shouldRotateConsumerSecret>false</shouldRotateConsumerSecret>
</ExtlClntAppGlobalOauthSettings>
```

`force-app/main/default/extlClntAppOauthSettings/Billing_Sync_ECA_oauth.ecaOauth-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ExtlClntAppOauthSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Billing Sync ECA OAuth</label>
    <externalClientApplication>Billing_Sync_ECA</externalClientApplication>
    <commaSeparatedOauthScopes>Api, RefreshToken</commaSeparatedOauthScopes>
    <trustedIpRanges>
        <description>Billing platform egress</description>
        <startIpAddress>203.0.113.10</startIpAddress>
        <endIpAddress>203.0.113.20</endIpAddress>
    </trustedIpRanges>
</ExtlClntAppOauthSettings>
```

`force-app/main/default/extlClntAppOauthPolicies/Billing_Sync_ECA_plcy.ecaOauthPlcy-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ExtlClntAppOauthConfigurablePolicies xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Billing Sync ECA Policies</label>
    <externalClientApplication>Billing_Sync_ECA</externalClientApplication>
    <permittedUsersPolicyType>AdminApprovedPreAuthorized</permittedUsersPolicyType>
    <commaSeparatedPermissionSet>Billing_Sync_Integration</commaSeparatedPermissionSet>
    <ipRelaxationPolicyType>Enforce</ipRelaxationPolicyType>
    <refreshTokenPolicyType>SpecificInactivity</refreshTokenPolicyType>
    <refreshTokenValidityPeriod>7</refreshTokenValidityPeriod>
    <refreshTokenValidityUnit>Days</refreshTokenValidityUnit>
    <requiredSessionLevel>STANDARD</requiredSessionLevel>
</ExtlClntAppOauthConfigurablePolicies>
```

**How to read it — where the ECA is not a rename of the connected app**

| Connected app | External Client App | Why it matters |
|---|---|---|
| `<scopes>Api</scopes>` repeated | `<commaSeparatedOauthScopes>Api, RefreshToken</commaSeparatedOauthScopes>` — one string | A search-and-replace migration produces invalid XML |
| `isPkceRequired` default `false` | `isPkceRequired` default **`true`** ("If set to `true` (default) Proof Key for Code for Exchange (PKCE) is required") | Silently omitting the element flips behaviour between the two containers |
| `ipRelaxation` values `ENFORCE` / `BYPASS` / `BYPASS_2FACTOR` / `ENFORCE_RELAXREFRESH` | `ipRelaxationPolicyType` values `Enforce` / `Bypass` / `Bypass_2factor` / `Enforce_RelaxRefresh` | Different casing; the connected-app spelling is rejected |
| `refreshTokenPolicy` one packed string (`specific_inactivity:7:DAYS`) | `refreshTokenPolicyType` + `refreshTokenValidityPeriod` + `refreshTokenValidityUnit` (`SpecificInactivity` / `7` / `Days`) | Three elements, different vocabulary |
| `isAdminApproved` boolean + `permissionSetName` | `permittedUsersPolicyType` = `AdminApprovedPreAuthorized` + `commaSeparatedPermissionSet` | The boolean has no ECA counterpart |
| `oauthClientCredentialUser` | `clientCredentialsFlowUser` | Both require a user with the **API Only** permission |
| Everything in one file | Secrets split into `ExtlClntAppGlobalOauthSettings`, which "can't be packaged and must not be added to source control" | The split is the point: policy is committable, secrets are not |

## 4. Named Credential + External Credential for an outbound callout

`force-app/main/default/externalCredentials/Billing_API_Cred.externalCredential-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ExternalCredential xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Billing API Cred</label>
    <description>OAuth principal used for all outbound calls to the billing platform.</description>
    <authenticationProtocol>Oauth</authenticationProtocol>
    <externalCredentialParameters>
        <parameterName>BillingServicePrincipal</parameterName>
        <parameterType>NamedPrincipal</parameterType>
        <sequenceNumber>1</sequenceNumber>
    </externalCredentialParameters>
    <externalCredentialParameters>
        <parameterName>AuthProviderUrl</parameterName>
        <parameterType>AuthProviderUrl</parameterType>
        <parameterValue>https://auth.billing.example.com/oauth2/token</parameterValue>
    </externalCredentialParameters>
    <externalCredentialParameters>
        <parameterName>Scope</parameterName>
        <parameterType>AuthParameter</parameterType>
        <parameterValue>invoices.write</parameterValue>
    </externalCredentialParameters>
</ExternalCredential>
```

`force-app/main/default/namedCredentials/Billing_API.namedCredential-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<NamedCredential xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Billing API</label>
    <namedCredentialType>SecuredEndpoint</namedCredentialType>
    <calloutStatus>Enabled</calloutStatus>
    <generateAuthorizationHeader>true</generateAuthorizationHeader>
    <allowMergeFieldsInBody>false</allowMergeFieldsInBody>
    <allowMergeFieldsInHeader>false</allowMergeFieldsInHeader>
    <namedCredentialParameters>
        <description>Billing platform base URL</description>
        <parameterName>DefaultEndpoint</parameterName>
        <parameterType>Url</parameterType>
        <parameterValue>https://api.billing.example.com</parameterValue>
    </namedCredentialParameters>
    <namedCredentialParameters>
        <description>Auth via the shared billing principal</description>
        <parameterName>DefaultAuth</parameterName>
        <parameterType>Authentication</parameterType>
        <externalCredential>Billing_API_Cred</externalCredential>
    </namedCredentialParameters>
</NamedCredential>
```

**How to read it**

- `namedCredentialType` `SecuredEndpoint` is the modern shape: "The named credential is extensible
  and uses external credentials to control authentication and permissions." `Legacy` "doesn't use
  the schema introduced in the Winter '23 release. Used for backward compatibility" — and every
  `Legacy`-only field (`endpoint`, `username`, `password`, `protocol`, `principalType`,
  `oauthToken`, `jwt*`, `aws*`) is marked deprecated in API version 56.0.
- Because those fields are `Legacy`-only, the endpoint URL is *not* an `<endpoint>` element on a
  `SecuredEndpoint` credential — it is a `namedCredentialParameters` entry of `parameterType` `Url`.
- The link from Named Credential to External Credential is the `Authentication` parameter's
  `<externalCredential>` child. A Named Credential with no such parameter has no principal.
- `NamedPrincipal` "specifies that the parameter uses the same set of user credentials for all
  users who access the external system"; `PerUserPrincipal` "provides access control at the
  individual user level." Who may *use* a principal is granted through a permission set — for the
  step-by-step principal setup, read `integration/named-credentials-setup`.
- `sequenceNumber` only applies to `NamedPrincipal` and decides "the order of principals to apply
  when a user participates in more than one principal. … Priority is from lower to higher numbers."
- Apex references the endpoint by name, never by URL: `req.setEndpoint('callout:Billing_API/invoices')`.
- Salesforce "stores third-party access and refresh tokens of up to 10,000 characters in length"
  (Salesforce Developer Limits and Allocations Quick Reference) — a provider issuing longer tokens
  will not round-trip through an External Credential.

## 5. Org-wide switch: admin-approved apps only

`force-app/main/default/settings/ConnectedApp.settings-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ConnectedAppSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableAdminApprovedAppsOnly>true</enableAdminApprovedAppsOnly>
    <enableAdminApprovedAppsOnlyForExternalUser>true</enableAdminApprovedAppsOnlyForExternalUser>
</ConnectedAppSettings>
```

`enableAdminApprovedAppsOnly`: "If `false` (default), any connected app can call the Salesforce
API. If `true`, only apps that have been approved or installed by the admin can call the
Salesforce API." Both fields carry the same caveat: "To access this field, you must contact
Salesforce Customer Support to enable API Access Control." Flipping this is an org-wide change —
inventory first (see the OAuth Usage pass in `SKILL.md`), then deploy.

---

## package.xml

Connected app plus the outbound pair:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Billing_Sync_JWT</members>
        <members>Partner_Portal_Web</members>
        <name>ConnectedApp</name>
    </types>
    <types>
        <members>Billing_API_Cred</members>
        <name>ExternalCredential</name>
    </types>
    <types>
        <members>Billing_API</members>
        <name>NamedCredential</name>
    </types>
    <types>
        <members>ConnectedApp</members>
        <name>Settings</name>
    </types>
    <version>64.0</version>
</Package>
```

The External Client App set — the guide ships all five types together in its own sample manifests,
because an ECA is incomplete without its plugins:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Billing_Sync_ECA</members>
        <name>ExternalClientApplication</name>
    </types>
    <types>
        <members>Billing_Sync_ECA_oauth</members>
        <name>ExtlClntAppOauthSettings</name>
    </types>
    <types>
        <members>Billing_Sync_ECA_glbl</members>
        <name>ExtlClntAppGlobalOauthSettings</name>
    </types>
    <types>
        <members>Billing_Sync_ECA_plcy</members>
        <name>ExtlClntAppOauthConfigurablePolicies</name>
    </types>
    <version>60.0</version>
</Package>
```

`ExternalClientApplication`, `ExtlClntAppOauthSettings` and `ExtlClntAppGlobalOauthSettings` are
"available in API version 59.0 and later"; `ExtlClntAppOauthConfigurablePolicies` is 59.0+ and
`ExtlClntAppConfigurablePolicies` is 60.0+. The `<version>` in this manifest — and
`sourceApiVersion` in `sfdx-project.json` — must clear that floor, or a Spring '26 org still
rejects the deploy.

---

## Retrieve and deploy

```bash
# Retrieve what already exists, before you change anything
sf project retrieve start -m "ConnectedApp:Billing_Sync_JWT" -o prod-audit
sf project retrieve start -m "NamedCredential:Billing_API" -m "ExternalCredential:Billing_API_Cred" -o prod-audit

# Validate against production without committing the deploy
sf project deploy start -x manifest/package.xml -o prod --dry-run

# Deploy
sf project deploy start -x manifest/package.xml -o prod
```

**What does not survive a round trip — read this before you trust a retrieved file**

| Field | Guide's statement | Consequence |
|---|---|---|
| `oauthConfig/consumerSecret` | "When set, the value isn't returned in Metadata API requests." | A retrieved `.connectedApp-meta.xml` has no secret. Redeploying it into a second org creates an app whose secret nobody holds. |
| `oauthConfig/consumerKey` | "In API version 32.0 and later, you can set this field's value only during creation. After you define and save the value, it can't be edited." Alphanumeric, 8–256 characters, "Consumer keys must be globally unique." | You cannot repoint an existing app at a new key by editing the file. Key rotation is a new app (or, for an ECA, `shouldRotateConsumerKey`). |
| `oauthConfig/scopes` | The guide publishes one enum list for deploying and a shorter one for retrieving. | Deployed scope names may not be the names you get back. Diff against intent, not against the last retrieve. |
| ECA consumer key / secret | `shouldRotateConsumerKey` and `shouldRotateConsumerSecret`: "To maintain security, if this field is set to `true`, you must include the ignore warnings attribute in the deploy command." | An ECA rotation deploy fails unless warnings are ignored — by design, not by accident. |
| `ExtlClntAppGlobalOauthSettings` (whole file) | "These settings include private and sensitive OAuth consumer information that can't be packaged and must not be added to source control." | Keep it out of the repo; deploy it out of band or configure it in Setup. |
| Connected app in a 2GP package | Retrieval of a packaged connected app is not supported: `sf project retrieve start` and the Metadata API `retrieve()` call don't work on it (see `well-architected.md`). | A packaging pipeline that assumes retrieve-then-redeploy will not work for connected apps. |

Migration of an existing connected app to an ECA is a Setup action, not a metadata edit: the
**Migrate to External Client App** button in App Manager, which "preserves your consumer key and
secret." Its eligibility rules are in `SKILL.md`.

---

## Verify after deploy

`ConnectedApplication` is the read-only view of what actually landed — "Represents a connected app
and its details; all fields are read-only", supporting `describeSObjects()`, `query()`, `retrieve()`.

```sql
SELECT Name, OptionsAllowAdminApprovedUsersOnly, OptionsHasSessionLevelPolicy,
       RefreshTokenValidityPeriod, OptionsRefreshTokenValidityMetric,
       StartUrl, MobileStartUrl
FROM ConnectedApplication
ORDER BY Name
```

- `OptionsAllowAdminApprovedUsersOnly` must be `true` for every app you deployed with
  `isAdminApproved`. It "indicates whether access is limited to users granted approval to use the
  connected app by an administrator."
- `RefreshTokenValidityPeriod` is "the duration of an authorization token until it expires in
  hours, months, or days as set in the connected app management page", and
  `OptionsRefreshTokenValidityMetric` tells you which reading applies: "If `true`, the token
  validity is measured based on the last use of the token; otherwise, it's based on the token
  duration." A row with a validity period and no metric flag is a *lifetime*, not an inactivity window.

Then confirm who is actually holding tokens for the app:

```sql
SELECT AppName, UserId, LastUsedDate, UseCount
FROM OauthToken
WHERE AppName = 'Billing Sync JWT'
ORDER BY LastUsedDate DESC
```

`OauthToken` "represents an OAuth access token for connected app authentication", available in API
version 32.0 and later, and supports only `describeSObjects()` and `query()`. Two constraints the
guide states outright:

- "Users with the Customize Application permission see all tokens for all users in the org.
  Otherwise, you see only your own tokens." An empty result from an under-privileged user is not
  evidence that nobody has authorised the app.
- "If you try to use Apex DML operations and then query this object in the same call, you get an
  `UncommittedWork` error. … To avoid this error, execute DML operations and queries in separate,
  asynchronous calls." A post-deploy verification script that writes a log record and then queries
  `OauthToken` in the same transaction fails on the query, not the write.

A row whose `AppName` you cannot attribute to an owner is the finding. `DeleteToken` on the same
object is "a token that can be used at the revoke OAuth token endpoint to remove this token" — the
revocation handle for a single grant.

---

## Related reading

| Question | Skill |
|---|---|
| The OAuth error code is already on screen | `admin/connected-app-troubleshooting` |
| Choosing between OAuth flows in depth, incl. device flow and token lifecycle | `integration/oauth-flows-and-connected-apps` |
| External Credential principal types, per-user vs per-org setup steps | `integration/named-credentials-setup` |
| Rotating secrets, PKCE and session policy as a security programme | `security/connected-app-security-policies` |
| Token issue, refresh, rotation, revocation, introspection | `security/oauth-token-management` |
| Callback URL and My Domain / Enhanced Domains strategy | `security/oauth-redirect-and-domain-strategy` |
| SAML / OpenID SSO configuration rather than API auth | `security/sso-configuration` |
