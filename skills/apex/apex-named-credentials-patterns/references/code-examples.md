# Code Examples — Apex Named Credentials Patterns

A complete, deployable slice: External Credential → Named Credential → Permission Set →
Apex client → Apex test → manifest → verification. Every XML element name and enum value
below is taken from the Metadata API Developer Guide (Summer '26 / v62) sections cited
inline. Every Apex idiom is taken from the Apex Developer Guide or Apex Reference Guide.

Scenario: an Apex service calls a partner order API at `https://orders.partner.example.com`.
Authentication is a bearer-style token the partner issues; all Salesforce users share one
identity in the partner system (a named principal); the token must not appear in source.

---

## 1. `ExternalCredential` — the authentication half

`ExternalCredential` components have the suffix `.externalCredential` and live in the
`externalCredentials` folder; available in API version 56.0 and later
(`api_meta` L63614–63619).

`authenticationProtocol` is **required**. The guide enumerates exactly these values:
`AwsSv4`, `Basic`, `Custom`, `Jwt` (reserved for future use), `JwtExchange` (reserved),
`NoAuthentication` (reserved), `Oauth`, `Password` (reserved) (`api_meta` L63641–63657).
`Custom` is described as "User-created authentication. Specify the permission set, sequence
number, and authentication parameters" — which is exactly this scenario.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ExternalCredential xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Partner Orders Credential</label>
    <description>Auth for the partner order API. Secret values are entered in Setup, never in this file.</description>
    <authenticationProtocol>Custom</authenticationProtocol>

    <!-- The principal. parameterName here is the principal NAME that a permission set grants. -->
    <externalCredentialParameters>
        <parameterName>PartnerOrdersNamedPrincipal</parameterName>
        <parameterType>NamedPrincipal</parameterType>
        <sequenceNumber>1</sequenceNumber>
        <description>Single shared identity for all Salesforce users.</description>
    </externalCredentialParameters>

    <!-- The Authorization header the platform adds at callout time. -->
    <externalCredentialParameters>
        <parameterName>Authorization</parameterName>
        <parameterType>AuthHeader</parameterType>
        <parameterValue>{!'Bearer ' &amp; $Credential.Partner_Orders_EC.ApiToken}</parameterValue>
        <sequenceNumber>1</sequenceNumber>
        <description>Header sent on every callout through a Named Credential that references this EC.</description>
    </externalCredentialParameters>

    <!-- Non-secret tuning knob carried with the credential. -->
    <externalCredentialParameters>
        <parameterName>ApiVersionHeaderValue</parameterName>
        <parameterType>AuthParameter</parameterType>
        <parameterValue>2024-06-01</parameterValue>
    </externalCredentialParameters>
</ExternalCredential>
```

**How to read it**

- `label` is required; it is the name shown in the Salesforce UI (`api_meta` L63670–63673).
- `externalCredentialParameters` is `ExternalCredentialParameter[]` — "one or more sets of
  parameters that further configure the external credential" (`api_meta` L63665–63668).
- `parameterType` `NamedPrincipal` = "the parameter uses the same set of user credentials
  for all users who access the external system"; `PerUserPrincipal` = "provides access
  control at the individual user level" (`api_meta` L63806–63808). Those two are the
  principal types; every other `parameterType` in the enum configures something else.
- `parameterType` `AuthHeader`: "Allows the user to specify custom authentication headers to
  be added to the callout at run time. When using AuthHeader, the `parameterName` field must
  be the header name as a string, and `parameterValue` must be a formula of a header value
  that is evaluated at run time. `sequenceNumber` determines the order in which headers are
  sent out in the callout. Headers with lower numbers are sent out first."
  (`api_meta` L63757–63764).
- `sequenceNumber` has a second, different meaning on a principal parameter: it "specifies
  the order of principals to apply when a user participates in more than one principal…
  Priority is from lower to higher numbers. You can set this field only when `parameterType`
  is `NamedPrincipal`" (`api_meta` L63846–63852).
- **UNVERIFIED (2026-09-05):** the exact merge-field grammar inside an `AuthHeader`
  `parameterValue` — the `{!'Bearer ' & $Credential.<ExternalCredential>.<ParameterName>}`
  shape above. The Metadata API guide states the field is "a formula of a header value that
  is evaluated at run time" (`api_meta` L63760–63761) but publishes no formula grammar for
  it, and the External-Credential-scoped `$Credential.<EC>.<Param>` form appears nowhere in
  the Metadata API guide, the Apex Developer Guide, or the Apex Reference Guide. The
  documented `$Credential` merge fields (section 5 below) are the *un-scoped* ones. Confirm
  the scoped form against Salesforce Help "Create an External Credential" before deploying,
  or build the header in Apex instead (section 5).
- The secret itself is **not in this file.** Nothing in `ExternalCredential` holds a token
  value: the guide's note on the type says "All credentials stored within this entity are
  encrypted… Salesforce encrypts your credentials by auto-creating org-specific keys"
  (`api_meta` L63604–63608), and the credential values are entered against the principal in
  Setup after the metadata is deployed.
- **`ApiToken` is not declared anywhere in this file, and that is deliberate.** It is the name
  given to an **authentication parameter**, created in **Setup → Named Credentials → External
  Credentials → Partner Orders Credential → Principals → PartnerOrdersNamedPrincipal → New
  (Authentication Parameter)** — a step that happens only after this `ExternalCredential`
  deploys, never inside its metadata. The formula above and the Setup-created parameter simply
  have to agree on the same name; nothing in the deploy cross-checks them for you (gotcha 14).
  A deploy of this file with the formula in place can validate cleanly while the `ApiToken`
  parameter itself is still unset in Setup — the deploy checks the formula's shape, not that
  the value behind it exists yet. Get the parameter's name from the requester before writing
  the formula; do not guess it.

The guide's own sample uses `AwsSv4` with a `NamedPrincipal` and two `AuthParameter`
entries (`api_meta` L63856–63875) — the same skeleton with a different protocol.

---

## 2. `NamedCredential` — the endpoint half

`NamedCredential` components have the suffix `.namedCredential` and live in the
`namedCredentials` folder; available in API version 33.0 and later, and as of Spring '20
"only users with the View Setup and Configuration permission can access this type"
(`api_meta` L89899–89912).

`namedCredentialType` valid values are `Legacy`, `PrivateEndpoint`, `SecuredEndpoint`, and
`Standard` (reserved for internal use); available in API version 56.0 and later
(`api_meta` L90140–90152). `SecuredEndpoint` is "extensible and uses external credentials to
control authentication and permissions" — that is the modern model.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<NamedCredential xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Partner Orders API</label>
    <namedCredentialType>SecuredEndpoint</namedCredentialType>

    <!-- The endpoint. Same API name in every org; different parameterValue per org. -->
    <namedCredentialParameters>
        <parameterName>Url</parameterName>
        <parameterType>Url</parameterType>
        <parameterValue>https://orders.partner.example.com</parameterValue>
        <description>Root URL. Sandbox deploys a different value under the same API name.</description>
    </namedCredentialParameters>

    <!-- The link to the External Credential above. -->
    <namedCredentialParameters>
        <parameterName>PartnerOrdersAuth</parameterName>
        <parameterType>Authentication</parameterType>
        <externalCredential>Partner_Orders_EC</externalCredential>
    </namedCredentialParameters>

    <!-- A non-auth header every callout should carry. -->
    <namedCredentialParameters>
        <parameterName>Accept</parameterName>
        <parameterType>HttpHeader</parameterType>
        <parameterValue>{!'application/json'}</parameterValue>
        <sequenceNumber>1</sequenceNumber>
    </namedCredentialParameters>

    <calloutStatus>Enabled</calloutStatus>
    <allowMergeFieldsInHeader>true</allowMergeFieldsInHeader>
    <allowMergeFieldsInBody>false</allowMergeFieldsInBody>
    <generateAuthorizationHeader>false</generateAuthorizationHeader>
</NamedCredential>
```

**How to read it**

- `parameterType` `Url`: "Specifies that this parameter configures the URL of the endpoint.
  Store the actual URL in the `parameterValue` field" (`api_meta` L90352–90354). In a
  `SecuredEndpoint` credential the URL lives here, **not** in the top-level `<endpoint>`
  element — that element "is valid only when NamedCredentialType is set to Legacy" and "is
  deprecated in API version 56.0" (`api_meta` L90022–90030). Get the real host and path from
  the requester before writing this file — including whether sandbox and production share a
  host — the same way you get the `AuthHeader` parameter name in section 1; both are inputs
  the metadata cannot supply on its own (gotcha 14).
- `parameterType` `Authentication`: "Specifies that this parameter configures authentication
  using the credentials specified in the external credential, referenced by the
  `externalCredential` field" (`api_meta` L90318–90321). `externalCredential` is a field of
  `NamedCredentialParameter`, not a top-level field of `NamedCredential`
  (`api_meta` L90272–90278) — a very common hand-authoring mistake.
- `parameterType` `HttpHeader`: "the `parameterName` field must be the header name as a
  string, and `parameterValue` must be a formula of a header value that is evaluated at run
  time"; `sequenceNumber` is "used to order HttpHeader parameters"
  (`api_meta` L90326–90330, L90368–90369).
- Other `NamedCredentialParamType` values the guide enumerates and you may need:
  `AllowedManagedPackageNamespaces` ("Allows managed packages identified by specified
  namespaces to use the named credential and make callouts through it"), `ClientCertificate`
  (references the `certificate` field), `ManagedByNamespace` (subscriber- vs
  developer-controlled manageability for a packaged credential), and
  `OutboundNetworkConnection` (used when `namedCredentialType` is `PrivateEndpoint`).
  `ConnectionStatus`, `CreatedByNamespace`, `CustomParameter`, `ManagedByComponent`,
  `ManagedByFeature`, `NamedCredentialOptions`, `SfHttpRequestExtensionName`, and
  `StandardNamedCredentialType` are marked reserved for internal use
  (`api_meta` L90310–90355).
- `calloutStatus` (`Enabled` | `Disabled`) is available in API version 59.0 and later
  (`api_meta` L90000–90007). Deploying `Disabled` is how you ship a credential that is not
  yet usable.
- `generateAuthorizationHeader` defaults to **true**: "Specifies whether Salesforce generates
  an authorization header and applies it to each callout that references the named
  credential" (`api_meta` L90039–90046). It is set to `false` here because the External
  Credential's `AuthHeader` parameter supplies `Authorization` instead. The Apex Developer
  Guide states the deselect criteria: "The remote endpoint doesn't support authorization
  headers" or "The authorization headers are provided by other means. For example, in Apex
  callouts, the developer can have the code construct a custom authorization header for each
  callout" — and warns that "This option is required if you reference the named credential
  from an external data source" (`apexdev` L34429–34440).
- `allowMergeFieldsInHeader` / `allowMergeFieldsInBody` both default to **false**
  (`api_meta` L89914–89940). Apex merge fields (section 5) are inert unless the matching
  flag is on: "a Salesforce admin must enable Allow Merge Fields in HTTP Header and Allow
  Merge Fields in HTTP Body on the named credential" (`apexdev` L34505–34507). They are also
  "not available if you reference the named credential from an external data source"
  (`apexdev` L34446–34448).

---

## 3. `PermissionSet` — who may use the principal

A principal is inert until a permission set grants it. `externalCredentialPrincipalAccesses`
"Indicates which external credential principals are available to users assigned to this
permission set. Available in API version 59.0 and later" (`api_meta` L94794–94796).

`PermissionSetExternalCredentialPrincipalAccess` has exactly two fields: `enabled`
(required) and `externalCredentialPrincipal` (required) — "The name of the external
credential and principal, separated by a dash. For example,
`myExternalCredential-myPrincipal`" (`api_meta` L94986–95004).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Partner Orders API Caller</label>
    <description>Grants use of the Partner Orders named principal. Assign to any user whose transaction makes the callout.</description>
    <hasActivationRequired>false</hasActivationRequired>
    <externalCredentialPrincipalAccesses>
        <enabled>true</enabled>
        <externalCredentialPrincipal>Partner_Orders_EC-PartnerOrdersNamedPrincipal</externalCredentialPrincipal>
    </externalCredentialPrincipalAccesses>
</PermissionSet>
```

**How to read it**

- The value is `<ExternalCredential API name>-<principal parameterName>`. Both halves come
  from section 1: `Partner_Orders_EC` is the file stem, `PartnerOrdersNamedPrincipal` is the
  `parameterName` of the `NamedPrincipal` parameter. A dash, not an underscore, joins them.
  This grant fails in the same deploy as an `ExternalCredential` whose `AuthHeader` parameter
  has no `parameterValue` — the checker's `NC-PS-01` treats that as a deploy-order dependency
  to confirm, not a defect in this file (gotcha 14).
- Packaged credentials prefix the namespace with two underscores:
  `namespacePrefix__myExternalCredential-myPrincipal` (`api_meta` L94999–95003).
- Before API 58.0 the link ran the other way: `ExternalCredentialParameter.principal`
  "points to a permission set… First available in API version 56.0, this field is removed in
  API version 58.0 and later" (`api_meta` L63822–63831). If you inherit an org whose EC XML
  still carries `<principal>`, the grant has moved to the permission set.
- The permission set must be assigned to **the user the transaction runs as**, which for
  Batch, Queueable, Scheduled and `@future` Apex is not necessarily the user who started the
  work. See gotcha 6.

---

## 4. The Apex client

Build on `templates/apex/HttpClient.cls` (`namedCredential(...)` / `path(...)` builder — it
composes `'callout:' + namedCredential + path` internally) rather than assembling
`HttpRequest` by hand. `ApplicationLogger` is `templates/apex/ApplicationLogger.cls`.

```apex
/**
 * PartnerApiClient — reads orders from the partner order API.
 *
 * Deployed prerequisites (see references/code-examples.md sections 1-3):
 *   ExternalCredential  Partner_Orders_EC   (Custom, NamedPrincipal PartnerOrdersNamedPrincipal)
 *   NamedCredential     Partner_Orders_NC   (SecuredEndpoint -> Partner_Orders_EC)
 *   PermissionSet       Partner_Orders_API_Caller (externalCredentialPrincipalAccesses)
 *
 * The Apex never sees the token. It names the NAMED CREDENTIAL, never the external
 * credential: "A named credential URL contains the scheme callout:, the name of the named
 * credential, and an optional path" (apexdev L34332-34334).
 */
public with sharing class PartnerApiClient {

    /** Named Credential API name. Identical in every org; the URL parameter differs. */
    @TestVisible
    private static final String NAMED_CREDENTIAL = 'Partner_Orders_NC';

    public class PartnerApiException extends Exception {}

    public class OrderSummary {
        public String orderNumber;
        public String status;
        public Decimal amount;
    }

    /**
     * Fetch one order.
     *
     * @param externalOrderId partner-side identifier, not a Salesforce Id
     * @return the parsed summary, or null when the partner reports 404
     */
    public static OrderSummary fetchOrder(String externalOrderId) {
        if (String.isBlank(externalOrderId)) {
            throw new PartnerApiException('externalOrderId is required');
        }

        HttpClient.Response res = new HttpClient()
            .namedCredential(NAMED_CREDENTIAL)
            .path('/v2/orders/' + EncodingUtil.urlEncode(externalOrderId, 'UTF-8'))
            .method('GET')
            .header('Accept', 'application/json')
            // Default 10 s is almost always too short; hard ceiling is 120000 ms
            // and the whole transaction shares a 120 s cumulative budget
            // (apexdev L35853-35857).
            .timeoutMs(20000)
            // Deliberately OFF. HttpClient.sleep() is a busy-wait loop, which burns
            // Apex CPU time against the governor limit while it waits. Retry a failed
            // callout from a Queueable instead — see integration/retry-and-backoff-patterns.
            .retryOnTransient(false)
            .send();

        if (res.statusCode == 404) {
            return null;
        }
        if (res.statusCode == 401 || res.statusCode == 403) {
            // Auth-layer failure: principal not granted, credential unset, or token rejected.
            ApplicationLogger.warn(
                'PartnerApiClient.fetchOrder',
                'Auth failure ' + res.statusCode + ' for ' + NAMED_CREDENTIAL
            );
            throw new PartnerApiException(
                'Not authorized to call ' + NAMED_CREDENTIAL
                + '. Confirm the running user has the Partner_Orders_API_Caller permission set.'
            );
        }
        if (!res.isSuccess()) {
            throw new PartnerApiException(
                'Partner API returned HTTP ' + res.statusCode + ': ' + res.status
            );
        }

        Map<String, Object> body =
            (Map<String, Object>) JSON.deserializeUntyped(res.body);
        OrderSummary out = new OrderSummary();
        out.orderNumber = (String) body.get('orderNumber');
        out.status = (String) body.get('status');
        Object amt = body.get('amount');
        out.amount = (amt == null) ? null : Decimal.valueOf(String.valueOf(amt));
        return out;
    }
}
```

`PartnerApiClient.cls-meta.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ApexClass xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>67.0</apiVersion>
    <status>Active</status>
</ApexClass>
```

---

## 5. When the endpoint needs a hand-built header: `$Credential` merge fields

The platform's merge fields *are* usable from Apex — this is the point most often gotten
backwards. The Apex Developer Guide's own examples set them in `setHeader` and `setBody`:

```apex
// apexdev L34496-34497 — non-standard authentication
req.setHeader('X-Username', '{!$Credential.Username}');
req.setHeader('X-Password', '{!$Credential.Password}');

// apexdev L34501 — OAuth
req.setHeader('Authorization', '{!$Credential.OAuthToken}');

// apexdev L34512-34513 — request body, escaped
req.setBody('Username:{!HTMLENCODE($Credential.Username)}');
```

A complete Salesforce-published example that combines a `callout:` endpoint, a merge-field
`Authorization` header, and a merge field inside a JSON body
(`apexrefguide` L196211–196226):

```apex
// excerpt — Salesforce's SurveyInvitationLinkShortener sample
HttpRequest request = new HttpRequest();
request.setEndpoint('callout:bitly/v4/shorten');
request.setMethod('POST');
request.setHeader('Authorization', 'Bearer {!$Credential.Password}');
request.setHeader('Accept', 'application/json');
request.setHeader('Content-Type', 'application/json');
request.setBody(JSON.serialize(new Map<String, Object>{
    'group_guid' => '{!$Credential.UserName}',
    'long_url' => invitationURL
}));
```

The documented merge fields, verbatim from `apexdev` L34459–34492:

| Merge field | Resolves to | Availability |
|---|---|---|
| `{!$Credential.Username}` | Username of the running user | Password authentication only |
| `{!$Credential.Password}` | Password of the running user | Password authentication only |
| `{!$Credential.OAuthToken}` | OAuth token of the running user | OAuth authentication only |
| `{!$Credential.AuthorizationMethod}` | `Basic` (password), `Bearer` (OAuth 2.0), `null` (no auth) | Depends on protocol |
| `{!$Credential.AuthorizationHeaderValue}` | Base-64 username:password (password), OAuth token (OAuth 2.0), `null` (no auth) | Depends on protocol |
| `{!$Credential.OAuthConsumerKey}` | Consumer key | OAuth authentication only |

Considerations the guide attaches to them (`apexdev` L34504–34518):

- The admin must enable **Allow Merge Fields in HTTP Header** and **Allow Merge Fields in
  HTTP Body** on the named credential — i.e. `allowMergeFieldsInHeader` /
  `allowMergeFieldsInBody` in section 2. Both default to `false`.
- In request **bodies** you may wrap a merge field in `HTMLENCODE` to escape special
  characters. "The formula must start with HTMLENCODE, and other formula functions aren't
  supported. HTMLENCODE can't be used on merge fields in HTTP headers."
- "When you use these merge fields in SOAP API calls, OAuth access tokens aren't refreshed."
- To read or write custom headers programmatically, use Connect REST API's Named Credentials
  resources.

**UNVERIFIED (2026-09-05):** whether these six merge fields resolve unchanged against a
`SecuredEndpoint` credential whose `ExternalCredential.authenticationProtocol` is `Custom` or
`AwsSv4`. The guide describes their availability in the legacy protocol vocabulary
("password authentication", "OAuth authentication"), which maps onto the legacy
`NamedCredential.protocol` enum (`api_meta` L90212–90240), not onto the
`ExternalCredential.authenticationProtocol` enum. Test the resolution in a scratch org
before depending on it.

---

## 6. The test

Callouts are not executed in tests; you must install a mock. "By default, test methods don't
support HTTP callouts, so tests that perform callouts fail. Enable HTTP callout testing by
instructing Apex to generate mock responses in tests, using `Test.setMock`"
(`apexdev` L35384–35388). Signature: `public static Void setMock(Type interfaceType, Object
instance)` (`apexrefguide` L240953). `HttpCalloutMock.respond(HttpRequest)` "is called by the
Apex runtime to send a fake response when an HTTP callout is made after `Test.setMock` has
been called" (`apexrefguide` L216190–216205).

Use `templates/apex/tests/MockHttpResponseGenerator.cls` — it already routes by path
substring and can queue a response sequence.

```apex
@IsTest
private class PartnerApiClientTest {

    private static final String OK_BODY =
        '{"orderNumber":"SO-1001","status":"Shipped","amount":249.95}';

    @IsTest
    static void fetchOrder_parsesSuccessfulResponse() {
        Test.setMock(
            HttpCalloutMock.class,
            new MockHttpResponseGenerator().withResponse(200, OK_BODY)
        );

        Test.startTest();
        PartnerApiClient.OrderSummary summary = PartnerApiClient.fetchOrder('SO-1001');
        Test.stopTest();

        Assert.isNotNull(summary, 'A 200 response should produce a summary');
        Assert.areEqual('SO-1001', summary.orderNumber, 'orderNumber should be parsed');
        Assert.areEqual('Shipped', summary.status, 'status should be parsed');
        Assert.areEqual(249.95, summary.amount, 'amount should be parsed as Decimal');
    }

    @IsTest
    static void fetchOrder_returnsNullOnNotFound() {
        Test.setMock(
            HttpCalloutMock.class,
            new MockHttpResponseGenerator().withResponse(404, '{"error":"not found"}')
        );

        Test.startTest();
        PartnerApiClient.OrderSummary summary = PartnerApiClient.fetchOrder('SO-NOPE');
        Test.stopTest();

        Assert.isNull(summary, '404 should map to null, not an exception');
    }

    @IsTest
    static void fetchOrder_surfacesPrincipalProblemOn401() {
        Test.setMock(
            HttpCalloutMock.class,
            new MockHttpResponseGenerator().withResponse(401, '')
        );

        Test.startTest();
        try {
            PartnerApiClient.fetchOrder('SO-1001');
            Assert.fail('401 should raise PartnerApiException');
        } catch (PartnerApiClient.PartnerApiException e) {
            Assert.isTrue(
                e.getMessage().contains('permission set'),
                'The 401 message should point the reader at the principal grant, got: '
                    + e.getMessage()
            );
        }
        Test.stopTest();
    }

    @IsTest
    static void fetchOrder_rejectsBlankId() {
        Test.startTest();
        try {
            PartnerApiClient.fetchOrder('   ');
            Assert.fail('Blank id should raise before any callout');
        } catch (PartnerApiClient.PartnerApiException e) {
            Assert.isTrue(
                e.getMessage().contains('required'),
                'Guard clause message expected, got: ' + e.getMessage()
            );
        }
        Test.stopTest();
    }
}
```

Two things this test deliberately does **not** assert:

- It does not assert on `req.getEndpoint()` inside the mock.
  **UNVERIFIED (2026-09-05):** whether the `HttpRequest` handed to `respond()` still carries
  the literal `callout:Partner_Orders_NC/v2/orders/...` string or an endpoint the platform
  has already resolved. Neither the Apex Developer Guide's mock section
  (`apexdev` L35384–35410) nor `HttpCalloutMock` in the Apex Reference Guide
  (`apexrefguide` L216168–216210) states it. If you route mock responses by path substring,
  match on the path (`/v2/orders`), which is present either way.
- It does not assert that the named credential exists. Nothing in the corpus states whether a
  `callout:` endpoint naming a missing named credential fails at compile time, at
  `send()` time, or is swallowed by the mock. **UNVERIFIED (2026-09-05).** The checker in
  `scripts/check_apex_named_credentials_patterns.py` covers this statically instead.

---

## 7. `package.xml` and deploy order

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Partner_Orders_EC</members>
        <name>ExternalCredential</name>
    </types>
    <types>
        <members>Partner_Orders_NC</members>
        <name>NamedCredential</name>
    </types>
    <types>
        <members>Partner_Orders_API_Caller</members>
        <name>PermissionSet</name>
    </types>
    <types>
        <members>PartnerApiClient</members>
        <members>PartnerApiClientTest</members>
        <name>ApexClass</name>
    </types>
    <version>67.0</version>
</Package>
```

Both types support the `*` wildcard in the manifest (`api_meta` L63877–63886 for
`ExternalCredential`, L90412–90425 for `NamedCredential`).

Deploy in dependency order. Each artifact names the one before it, so a single combined
deploy can succeed, but deploying in four steps gives you a readable failure when a
reference is wrong:

```bash
# 1. Auth first — nothing references anything yet.
sf project deploy start --metadata ExternalCredential:Partner_Orders_EC

# 2. Endpoint — its Authentication parameter names Partner_Orders_EC.
sf project deploy start --metadata NamedCredential:Partner_Orders_NC

# 3. Access — externalCredentialPrincipal names Partner_Orders_EC-PartnerOrdersNamedPrincipal.
sf project deploy start --metadata PermissionSet:Partner_Orders_API_Caller

# 4. Code — setEndpoint names Partner_Orders_NC.
sf project deploy start --manifest manifest/package.xml --test-level RunSpecifiedTests \
  --tests PartnerApiClientTest
```

Between step 3 and step 4, a human enters the credential values against the principal in
**Setup → Named Credentials → External Credentials → Partner Orders Credential →
Principals**. Secrets are never in the repo, so this step cannot be automated by a deploy.
**UNVERIFIED (2026-09-05):** the exact Setup navigation path — help.salesforce.com is not
in the corpus.

Assign the permission set to the callout's running user:

```bash
sf org assign permset --name Partner_Orders_API_Caller
```

Retrieve what the org actually has, to diff against source:

```bash
sf project retrieve start \
  --metadata ExternalCredential:Partner_Orders_EC,NamedCredential:Partner_Orders_NC
```

---

## 8. Verification

**a. The named credential is present and its callout options are what you deployed.** The
`NamedCredential` object supports `describeSObjects()`, `query()` and `retrieve()`, and "As
of Spring '20 and later, only users with the View Setup and Configuration permission can
access this object" (`object_reference` L185778–185803).

```soql
SELECT DeveloperName, MasterLabel, NamespacePrefix,
       CalloutOptionsGenerateAuthorizationHeader,
       CalloutOptionsAllowMergeFieldsInHeader,
       CalloutOptionsAllowMergeFieldsInBody
FROM NamedCredential
WHERE DeveloperName = 'Partner_Orders_NC'
```

Expect `CalloutOptionsGenerateAuthorizationHeader = false` and
`CalloutOptionsAllowMergeFieldsInHeader = true`, matching section 2. Those three fields are
documented on the object at `object_reference` L185851–185877 and are available in API
version 35.0 and later. `Endpoint` and `PrincipalType` are also on the object but are "only
valid for legacy named credentials" and "deprecated in API version 56.0"
(`object_reference` L185910–185918, L186028–186038) — a `SecuredEndpoint` credential returns
nothing useful in them, which is itself a fast way to tell the two models apart.

```bash
sf data query --query "SELECT DeveloperName, CalloutOptionsGenerateAuthorizationHeader FROM NamedCredential WHERE DeveloperName = 'Partner_Orders_NC'"
```

**b. The tests pass.**

```bash
sf apex run test --tests PartnerApiClientTest --result-format human --wait 10
```

**c. The static checks pass.**

```bash
python3 skills/apex/apex-named-credentials-patterns/scripts/check_apex_named_credentials_patterns.py \
    --manifest-dir force-app --strict
```

**d. A live smoke call, from a user who holds the permission set.** Run this in Execute
Anonymous — and note that this specific act needs an extra permission. The Apex Developer
Guide's permission table for anonymous blocks lists: "User permissions needed if an anonymous
Apex callout references a named credential as the endpoint: **Customize Application**"
(`apexdev` L14757–14758).

```apex
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:Partner_Orders_NC/v2/health');
req.setMethod('GET');
req.setTimeout(20000);
HttpResponse res = new Http().send(req);
System.debug(res.getStatusCode() + ' ' + res.getBody());
```

**UNVERIFIED (2026-09-05):** SOQL against `ExternalCredential` or `UserExternalCredential`
as a verification step. Neither object appears as a documented standard object in the Object
Reference extraction used here (the only occurrence of `UserExternalCredential` is inside an
unrelated picklist value list at `object_reference` L142361), so their queryability, field
names, and filterability are unconfirmed. `ExternalCredential` is confirmed only as a
**metadata type** (`api_meta` L63601). Verify with `sf sobject describe` or
`describeSObjects()` in the target org before writing Apex that queries either one.
