# Examples — Apex Named Credentials Patterns

Worked scenarios. The deployable artefacts themselves — External Credential, Named
Credential, permission set, client, test, `package.xml` — are in
`references/code-examples.md`; these examples cover the decisions around them.

Citations use the short forms defined at the top of `references/gotchas.md`.

---

## Example 1: The External API Wants the Token in `X-Auth-Token`, Not `Authorization`

**Context:** A REST API expects the access token in a custom header named `X-Auth-Token`.
The org has a `SecuredEndpoint` Named Credential (`ExternalCatalogNC`) pointing at an
External Credential (`ExternalCatalogEC`). The Apex developer's job is to get the credential
value into a header the platform does not generate on its own.

**Problem:** Two wrong turns are common here, in opposite directions. One is to read the
token from a Custom Setting or Custom Label and set the header by concatenation — which puts
the secret in the database outside the credential vault, deployable to any sandbox without
rotation. The other is to believe `{!$Credential.*}` cannot be used from Apex at all, and
conclude the requirement cannot be met with a Named Credential.

**Solution:** Use the merge field in Apex, and deploy the flag that makes it resolve.

```apex
/**
 * Callout to a REST API that wants the credential in a custom header.
 *
 * Prerequisites (metadata, not Apex):
 *   Named Credential ExternalCatalogNC
 *     <allowMergeFieldsInHeader>true</allowMergeFieldsInHeader>   <- without this the
 *                                                                    literal text is sent
 *     <generateAuthorizationHeader>false</generateAuthorizationHeader>
 *   External Credential ExternalCatalogEC with a principal, granted by a permission set.
 *
 * The Apex never holds the token. The platform substitutes the merge field at callout
 * time; there is no getter that returns the resolved value.
 */
public with sharing class ProductCatalogService {

    private static final String NC_NAME = 'ExternalCatalogNC';

    public class CatalogException extends Exception {}

    /**
     * Fetch a product by its external identifier.
     * @param productId external system product identifier (not a Salesforce Id)
     * @return the product name, or null when the catalog reports 404
     */
    public static String fetchProductName(String productId) {
        if (String.isBlank(productId)) {
            throw new IllegalArgumentException('productId is required');
        }

        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:' + NC_NAME + '/products/'
            + EncodingUtil.urlEncode(productId, 'UTF-8'));
        req.setMethod('GET');
        // Documented merge field. Requires allowMergeFieldsInHeader on the credential
        // (apexdev L34456-34507). HTMLENCODE is NOT permitted on a header merge field.
        req.setHeader('X-Auth-Token', '{!$Credential.OAuthToken}');
        req.setHeader('Accept', 'application/json');
        req.setTimeout(30000);

        HttpResponse res = new Http().send(req);

        if (res.getStatusCode() == 200) {
            Map<String, Object> body =
                (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
            return (String) body.get('name');
        }
        if (res.getStatusCode() == 404) {
            return null;
        }
        if (res.getStatusCode() == 401 || res.getStatusCode() == 403) {
            throw new CatalogException(
                'Catalog rejected the credential. Check that allowMergeFieldsInHeader is '
                + 'true on ' + NC_NAME + ' and that the running user is assigned the '
                + 'permission set granting the ExternalCatalogEC principal.'
            );
        }
        throw new CatalogException('Catalog returned HTTP ' + res.getStatusCode());
    }
}
```

**Why it works:** the substitution is platform-side. Salesforce publishes the same shape in
its own sample — `request.setHeader('Authorization', 'Bearer {!$Credential.Password}')`
against a `callout:bitly/v4/shorten` endpoint (`apexrefguide` L196211–196226). The secret
stays in the vault; Apex carries only the merge field.

**How to tell it is misconfigured:** if the API rejects the call and echoes the header value
back as `{!$Credential.OAuthToken}`, the merge field did not resolve — check
`allowMergeFieldsInHeader`, which defaults to `false` (`api_meta` L89914–89940). Confirm from
the org rather than from the repo:

```soql
SELECT DeveloperName,
       CalloutOptionsAllowMergeFieldsInHeader,
       CalloutOptionsAllowMergeFieldsInBody,
       CalloutOptionsGenerateAuthorizationHeader
FROM NamedCredential
WHERE DeveloperName = 'ExternalCatalogNC'
```

---

## Example 2: Per-User OAuth — Prompting Before the Callout Instead of After the 401

**Context:** A Lightning component browses data from an external SaaS system using a
`PerUserPrincipal` External Credential. Each user authenticates individually. The component
should show "Connect your account" rather than an empty table with a stack trace behind it.

**Problem:** The tempting design is a SOQL pre-flight against `UserExternalCredential`, gated
on a row existing. Two things are wrong with treating that as the answer.

**UNVERIFIED (2026-09-05):** neither `UserExternalCredential` nor `ExternalCredential`
appears as a documented standard object in the Object Reference used to ground this skill —
the sole occurrence of `UserExternalCredential` is a value inside an unrelated picklist list
at `object_reference` L142361. Their queryability and field names are unconfirmed here, so
any query against them must be written against a describe from the target org, not from
memory or from a generated field list:

```bash
sf sobject describe --sobject UserExternalCredential --target-org myorg | \
    python3 -c "import json,sys; d=json.load(sys.stdin); print(d['queryable']); print([f['name'] for f in d['fields'] if f['filterable']])"
```

And even with a correct schema, a row is a historical fact rather than a live one: the user
completed a flow at some point, which is not the same as holding a valid token now.

**Solution:** Make the 401/403 branch the load-bearing part, and treat any pre-flight gate as
a pure UX optimisation layered on top.

```apex
public with sharing class SaasDataController {

    public class NotConnectedException extends Exception {}

    @AuraEnabled
    public static List<Object> fetchItems() {
        HttpRequest req = new HttpRequest();
        req.setEndpoint('callout:SaasSystemNC/api/v1/items');
        req.setMethod('GET');
        req.setTimeout(30000);

        HttpResponse res = new Http().send(req);

        if (res.getStatusCode() == 401 || res.getStatusCode() == 403) {
            // The single reliable signal that this user has no usable credential.
            // Works whether the pre-flight gate exists or not.
            throw new AuraHandledException(
                'Connect your SaaS System account to view this data.'
            );
        }
        if (res.getStatusCode() != 200) {
            throw new AuraHandledException('SaaS System error: HTTP ' + res.getStatusCode());
        }
        return (List<Object>) JSON.deserializeUntyped(res.getBody());
    }
}
```

**Why it works:** the component renders the connect prompt from a signal the platform
actually produces, on every request, for every reason the credential might be unusable —
never authenticated, token expired, refresh failed, principal grant revoked. A pre-flight
query can suppress one avoidable callout on a first page load; it cannot replace this branch.
See gotcha 12 and LLM anti-pattern 7.

---

## Example 3: Migrating a Remote Site Setting and a Custom Label Token

**Context:** An inherited class calls `https://api.acme-corp.com` directly with a bearer token
read from a Custom Label. A Remote Site Setting exists for the host. Nothing is broken; the
secret is simply in source control and in every sandbox refresh.

**What practitioners inherit:**

```apex
// WRONG: literal endpoint + credential assembled in Apex
HttpRequest req = new HttpRequest();
req.setEndpoint('https://api.acme-corp.com/v2/orders/' + orderId);
req.setMethod('GET');
req.setHeader('Authorization', 'Bearer ' + System.Label.Acme_OAuth_Token);
HttpResponse res = new Http().send(req);
```

**What goes wrong:**

- The token sits in a Custom Label: readable in Setup, included in exports, and copied into
  every sandbox without rotation.
- Rotation is a code-adjacent deployment rather than a Setup change, so nobody does it.
- The base URL is environment-specific, which forces either an `isSandbox` branch or a second
  Custom Label to hold the URL.
- The Remote Site Setting must be maintained by hand for the host.

**Correct approach — the Apex side is one line:**

```apex
// CORRECT: endpoint and auth both leave the source tree
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:Acme_Orders_NC/v2/orders/' + orderId);
req.setMethod('GET');
req.setTimeout(30000);
HttpResponse res = new Http().send(req);
```

**The migration, in order:**

```bash
# 1-3. Metadata first. Shapes in references/code-examples.md sections 1-3.
sf project deploy start --metadata ExternalCredential:Acme_Orders_EC
sf project deploy start --metadata NamedCredential:Acme_Orders_NC
sf project deploy start --metadata PermissionSet:Acme_Orders_API_Caller

# 4. A human enters the token against the principal in Setup. No deploy can do this.
# 5. Grant it to whoever the callout runs as.
sf org assign permset --name Acme_Orders_API_Caller

# 6. Now the one-line Apex change, with its tests.
sf project deploy start --manifest manifest/package.xml \
  --test-level RunSpecifiedTests --tests AcmeOrderServiceTest

# 7. Prove nothing still calls the host directly, THEN delete the remote site setting.
python3 skills/apex/apex-named-credentials-patterns/scripts/check_apex_named_credentials_patterns.py \
    --manifest-dir force-app --strict

# 8. Delete the Custom Label and rotate the token. It was in git history; it is compromised.
```

Step 7 is the one teams skip. The checker's `NC-RSS-001` advisory fires while a Remote Site
Setting still covers the same host as a Named Credential's `Url` parameter — usually because
one code path was missed. Deleting the setting before that is clean turns a working
integration into a runtime failure.

---

## Example 4: Shipping the Credential in a Managed Package

**Context:** An ISV package calls a partner API. Two distribution choices exist, and they use
different `NamedCredentialParameter` types.

**Subscriber creates the credential; packaged code calls through it.** The subscriber's
credential must name the package's namespace, or packaged Apex is not among the callers it
permits. `AllowedManagedPackageNamespaces` "Allows managed packages identified by specified
namespaces to use the named credential and make callouts through it"
(`api_meta` L90315–90317):

```xml
<namedCredentialParameters>
    <parameterName>AllowedNamespaces</parameterName>
    <parameterType>AllowedManagedPackageNamespaces</parameterType>
    <parameterValue>acmeisv</parameterValue>
    <description>Lets the acmeisv package call through this credential.</description>
</namedCredentialParameters>
```

**ISV ships the credential; the subscriber may or may not edit it.** `ManagedByNamespace`
"Specifies the manageability capabilities for a packaged named credential. The
`parameterValue` indicates whether the named credential uses subscriber-controlled or
developer-controlled manageability" (`api_meta` L90342–90346). Decide it explicitly rather
than defaulting — it determines whether a subscriber can repoint the endpoint at their own
sandbox.

The permission set that grants the principal changes shape when packaged too. Unpackaged, the
value is `Acme_Orders_EC-AcmeOrdersPrincipal`; packaged, it gains a namespace prefix and two
underscores: `acmeisv__Acme_Orders_EC-AcmeOrdersPrincipal` (`api_meta` L94999–95003). The
packaged permission set and its development twin therefore do not carry identical XML, which
is worth a comment in the repo before someone "fixes" the difference.

**UNVERIFIED (2026-09-05):** whether the `AllowedManagedPackageNamespaces` allowlist is empty
by default, and therefore whether packaged code is blocked without it. The guide states what
the parameter permits, not what happens in its absence. Confirm against a real subscriber org
before writing setup instructions that depend on the answer.
