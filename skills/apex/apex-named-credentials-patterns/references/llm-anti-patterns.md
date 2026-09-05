# LLM Anti-Patterns — Apex Named Credentials Patterns

Common mistakes AI coding assistants make when generating or advising on Apex Named Credentials patterns.
These patterns help the consuming agent self-check its own output.

Citations use the short forms defined at the top of `references/gotchas.md`.

## Anti-Pattern 1: Using a Hardcoded Endpoint Instead of the `callout:` Prefix

**What the LLM generates:**

```apex
HttpRequest req = new HttpRequest();
req.setEndpoint('https://api.acme-corp.com/v2/customers/' + customerId);
req.setHeader('Authorization', 'Bearer ' + System.Label.Acme_Token);
```

**Why it happens:** LLMs trained on general Java/HTTP examples default to constructing full URLs with manually injected auth headers, because that is the most common pattern in general web programming. The Salesforce-specific `callout:` convention is not represented in general training data.

**Correct pattern:**

```apex
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:AcmeCorpNC/v2/customers/' + customerId);
req.setMethod('GET');
req.setTimeout(30000);
// Auth injected by the platform — see anti-pattern 6 for when Apex owns the header instead
```

**Detection hint:** Look for `req.setEndpoint('https://` — any full HTTPS URL in `setEndpoint()` is a red flag. Also look for `req.setHeader('Authorization'` whose value concatenates a `System.Label`, a Custom Setting, or a Custom Metadata read. The checker's `NC-APEX-002` rule fires on exactly that shape and treats it as an ERROR, because the credential is then in source control.

---

## Anti-Pattern 2: Using Legacy Model Syntax Assumptions in an Enhanced-Model Org

**What the LLM generates:**

```xml
<!-- WRONG: legacy fields on a SecuredEndpoint credential -->
<NamedCredential xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Acme</label>
    <namedCredentialType>SecuredEndpoint</namedCredentialType>
    <endpoint>https://api.acme-corp.com</endpoint>
    <principalType>NamedUser</principalType>
    <protocol>Oauth</protocol>
</NamedCredential>
```

Every element after `namedCredentialType` here is a legacy-only field. `endpoint`, `principalType`, `protocol`, `username`, `password`, `oauthToken`, `oauthRefreshToken`, `oauthScope`, `authProvider` and `certificate` are all documented as "valid only when NamedCredentialType is set to Legacy" and deprecated in API version 56.0 (`api_meta` L89950–90240).

**Why it happens:** Training data about Named Credentials is predominantly legacy-model documentation and blog posts written before Spring '22. The modern `namedCredentialParameters` shape is newer and less represented, so a model reaches for the old field names while correctly picking the new type value.

**Correct pattern:** In a `SecuredEndpoint` credential the URL and the auth link are both `namedCredentialParameters` entries — `parameterType` `Url` with the URL in `parameterValue`, and `parameterType` `Authentication` with the credential name in `externalCredential` (`api_meta` L90318–90354). See section 2 of `references/code-examples.md` for the full file, and the guide's own sample at `api_meta` L90386–90410.

**Detection hint:** A `<namedCredentialType>SecuredEndpoint</namedCredentialType>` file that also contains `<endpoint>`, `<protocol>` or `<principalType>` is mixing the two models. The checker's `NC-META-002` rule fires when a `SecuredEndpoint` credential has no `Authentication` parameter carrying an `externalCredential`.

---

## Anti-Pattern 3: Asserting That `{!$Credential.*}` Merge Fields Do Not Work in Apex

**What the LLM generates:**

> "`{!$Credential.OAuthToken}` is a Setup-only construct. It only resolves inside Named Credential custom header fields configured in the Setup UI and can never be used from Apex — an Apex string containing it is sent verbatim."

**Why it happens:** The advice is half-right, which makes it durable. Merge fields *are* inert when the credential's flags are off, so the model has seen real reports of literal text arriving at the endpoint and has generalised them into a rule about Apex.

**Correct pattern:** The Apex Developer Guide's section is titled "Merge Fields for Apex Callouts That Use Named Credentials" and its own examples are Apex (`apexdev` L34456–34513):

```apex
req.setHeader('X-Username', '{!$Credential.Username}');
req.setHeader('X-Password', '{!$Credential.Password}');
req.setHeader('Authorization', '{!$Credential.OAuthToken}');
req.setBody('Password:{!HTMLENCODE($Credential.Password)}');
```

What actually gates them is the pair of flags on the credential: `allowMergeFieldsInHeader` and `allowMergeFieldsInBody`, both defaulting to `false` (`api_meta` L89914–89940). The real constraints worth stating are narrower: `HTMLENCODE` is the only supported formula function, and it works in bodies but not headers; and OAuth tokens are not refreshed when these merge fields are used in SOAP API calls (`apexdev` L34508–34518).

**Detection hint:** Any generated prose containing "only in the Setup UI", "never available to Apex", or "sent as literal text" about `$Credential` is asserting the wrong rule. Rewrite it as a statement about the two flags.

---

## Anti-Pattern 4: Confusing Named Credential API Name With External Credential API Name in `callout:` Syntax

**What the LLM generates:**

```apex
// LLM uses the External Credential developer name in the callout: prefix
req.setEndpoint('callout:MyExternalCredential_EC/api/v1/data');
```

**Why it happens:** In the enhanced model there are two related records — the External Credential and the Named Credential. LLMs sometimes confuse the two names, especially when the developer's question is about auth configuration (External Credential), and then generate a `callout:` prefix using the External Credential name.

**Correct pattern:**

```apex
// callout: ALWAYS references the Named Credential API name, never the External Credential
req.setEndpoint('callout:MyServiceNC/api/v1/data');
```

The Named Credential API name is what appears in the Setup > Named Credentials list. The External Credential name is in Setup > External Credentials. They are typically different values. The External Credential name appears in exactly two places in a deployment: the `externalCredential` child of the Named Credential's `Authentication` parameter, and the left half of a permission set's `externalCredentialPrincipal` value (`api_meta` L90272–90278, L94995–94999).

**Detection hint:** Ask the developer to confirm the named credential API name explicitly from Setup > Named Credentials. If the `callout:` value ends in `_EC` or `EC`, that is a red flag — External Credential naming conventions typically include `EC`. The checker's `NC-APEX-003` rule resolves every `callout:Name` against the `*.namedCredential-meta.xml` files in the tree and errors on a name it cannot find.

---

## Anti-Pattern 5: Declaring the Continuation Framework Incompatible With Named Credentials

**What the LLM generates:**

> "The `callout:` prefix is not supported by the Continuation framework. Use a full HTTPS endpoint URL in the Continuation and handle authentication manually."

**Why it happens:** Continuation and Named Credentials are each strongly associated with a "recommended pattern" in training data, and the model has absorbed a widely repeated community claim about their incompatibility. The second sentence is the damaging half: it walks a developer from a false constraint into a hardcoded secret.

**Correct pattern:** The Apex Developer Guide's Continuation controller sample names a Named Credential URL as the first option for the endpoint field — "Callout endpoint as a named credential URL or, as shown here, as the long-running service URL" (`apexdev` L36006–36018). The one documented restriction is Private Connect: "Asynchronous callouts, including callouts that specify named credentials as the callout endpoint, aren't supported over Private Connect" (`apexdev` L36069–36070).

```apex
// excerpt — Continuation with a callout: endpoint
Continuation con = new Continuation(40);
con.continuationMethod = 'processResponse';
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:ExternalServiceNC/api/data');
req.setMethod('GET');
this.requestLabel = con.addHttpRequest(req);
return con;
```

Mock it with `Test.setContinuationResponse()` and `Test.invokeContinuationMethod()`, not `Test.setMock` (`apexdev` L36198–36199).

**Detection hint:** Generated text claiming Continuation "requires a fully qualified HTTPS URL", or code that switches from `callout:` to a literal URL specifically because a Continuation is involved. If the integration genuinely must not traverse the public internet, the answer is `namedCredentialType` `PrivateEndpoint` plus a Queueable — not a hardcoded URL.

---

## Anti-Pattern 6: Setting an `Authorization` Header in Apex Without Deciding Who Owns It

**What the LLM generates:**

```apex
// LLM adds a "safe" auth header on top of a Named Credential callout
req.setEndpoint('callout:PartnerNC/v2/orders');
req.setHeader('Authorization', 'Bearer ' + token);
```

**Why it happens:** The model treats an explicit `Authorization` header as unconditionally good practice, and does not model the credential's `generateAuthorizationHeader` flag as state that the Apex is interacting with. Both halves of the collision look correct in isolation.

**Correct pattern:** Decide the owner and encode the decision in metadata. `generateAuthorizationHeader` "Defaults to true" (`api_meta` L90039–90046), and the Apex Developer Guide lists building the header in Apex as an explicit reason to deselect it (`apexdev` L34429–34440). So:

```apex
// Platform owns it (generateAuthorizationHeader = true, the default):
req.setEndpoint('callout:PartnerNC/v2/orders');
// ...and Apex sets no Authorization header at all.
```

```apex
// Apex owns it (generateAuthorizationHeader = false, allowMergeFieldsInHeader = true):
req.setEndpoint('callout:PartnerNC/v2/orders');
req.setHeader('Authorization', 'Bearer {!$Credential.Password}');
```

The second form is the shape Salesforce publishes in its own `SurveyInvitationLinkShortener` sample (`apexrefguide` L196211–196226) — the secret still never appears in Apex; only the merge field does.

**Detection hint:** Any `setHeader('Authorization', ...)` on a `callout:` request where the corresponding `*.namedCredential-meta.xml` does not carry `<generateAuthorizationHeader>false</generateAuthorizationHeader>`. The checker's `NC-XREF-001` rule flags this as a WARN heuristic. A value built by concatenation rather than a merge field is the more serious version — that is `NC-APEX-002`, an ERROR.

---

## Anti-Pattern 7: Writing a `UserExternalCredential` Pre-Flight Gate as Though the Object's Schema Were Known

**What the LLM generates:**

```apex
// LLM invents field names and treats the result as a token-validity signal
List<UserExternalCredential> uecs = [
    SELECT Id, PrincipalType
    FROM UserExternalCredential
    WHERE UserId = :UserInfo.getUserId()
      AND ExternalCredentialId = :ecId
      AND PrincipalType = 'PerUserPrincipal'
];
return !uecs.isEmpty();   // "the user is authenticated"
```

**Why it happens:** The object name is plausible and appears in community writing, so the model completes a schema for it — `UserId`, `ExternalCredentialId`, `PrincipalType` — and then completes the semantics too, treating a row's existence as proof of a live token.

**Correct pattern:** Two separate corrections. The field list is not something to generate: neither `UserExternalCredential` nor `ExternalCredential` appears as a documented standard object in the Object Reference used here, so query it only after `sf sobject describe --sobject UserExternalCredential` has told you what the org actually exposes. And the semantics are wrong even if the schema is right — a row records that a flow completed once, not that a token is valid now. Handle 401 and 403 in the callout path regardless of any gate, so the user gets a re-authentication prompt rather than a stack trace.

**Detection hint:** SOQL against `UserExternalCredential` or `ExternalCredential` with no accompanying describe step, or a `return !uecs.isEmpty()` whose caller has no 401 branch. See gotcha 12.

---

## Anti-Pattern 8: Deploying the Metadata and Calling the Integration Done

**What the LLM generates:** A four-file change set — External Credential, Named Credential, Apex class, test class — and a closing summary saying the integration is ready.

**Why it happens:** The model optimises for a self-contained, deployable diff, and a permission set that grants a principal does not look like part of the integration. Nothing in the four files fails without it, so no test catches the omission.

**Correct pattern:** The principal is inert until a permission set grants it and that permission set is assigned to the user the callout runs as. `externalCredentialPrincipalAccesses` "Indicates which external credential principals are available to users assigned to this permission set" (`api_meta` L94794–94796), and the value is `<ExternalCredential>-<principal parameterName>` (`api_meta` L94995–94999). Deploy order is External Credential → Named Credential → Permission Set → Apex, followed by two steps no deploy can perform: a human entering the credential values against the principal in Setup, and `sf org assign permset`.

**Detection hint:** A change set containing an `*.externalCredential-meta.xml` and no `externalCredentialPrincipalAccesses` anywhere. The checker's `NC-PERM-001` rule reports this as an ADVISORY, since the permission set may legitimately live in a different repository.
