# Gotchas — Apex Named Credentials Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

Line citations are to the Summer '26 / v62 PDFs: `apexdev` =
[Apex Developer Guide](https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf),
`apexrefguide` = Apex Reference Guide, `api_meta` =
[Metadata API Developer Guide](https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf),
`object_reference` =
[Object Reference](https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf).

## Gotcha 1: Enhanced Model Separates External Credential From Named Credential — They Are Not the Same Record

**What happens:** Developers look for the auth configuration (OAuth client ID, client secret, principal type) on the Named Credential record and cannot find it. In the enhanced model (Spring '22+), the Named Credential only holds the endpoint URL; all auth configuration lives on the linked External Credential record.

**When it occurs:** Any time a developer or admin tries to inspect or modify OAuth settings for a Named Credential in an enhanced-model org. Also happens when Apex developers try to reference the External Credential API name directly in code — the correct reference is always the Named Credential API name with the `callout:` prefix, not the External Credential name.

**How to avoid:** In enhanced-model orgs, always navigate to **Setup > External Credentials** to view or modify auth configuration. The Named Credential record is only for endpoint URL and HTTP headers. The `callout:` syntax in Apex always references the Named Credential API name, never the External Credential name. In metadata this is the `Authentication` parameter's `externalCredential` child (`api_meta` L90318–90321); in Apex it is the sole documented shape: "A named credential URL contains the scheme `callout:`, the name of the named credential, and an optional path" (`apexdev` L34332–34334).

---

## Gotcha 2: `{!$Credential.*}` Merge Fields Are an Apex-Side Feature, But They Are Inert Until an Admin Turns Them On

**What happens:** A developer writes `req.setHeader('X-Api-Key', '{!$Credential.Password}')` and the external system receives the literal text `{!$Credential.Password}` rather than the secret. **UNVERIFIED (2026-09-05):** that the platform stays silent rather than raising — the guide states the flags gate the substitution but does not say what a callout does when a merge field is present and the flag is off. The reverse error is just as common: a developer is told merge fields "only work in Setup" and refactors a working callout into a hardcoded token.

**When it occurs:** Whenever `allowMergeFieldsInHeader` (for `setHeader`) or `allowMergeFieldsInBody` (for `setBody`) is `false` on the Named Credential. Both fields "default to false" (`api_meta` L89914–89940). The guide is unambiguous that the feature itself is Apex-side: "To construct the HTTP headers and request bodies of callouts to endpoints that are specified as named credentials, use these merge fields **in your Apex code**", with `req.setHeader('X-Username', '{!$Credential.Username}')` as its own example (`apexdev` L34456–34497). Salesforce ships a full sample doing exactly this — `request.setHeader('Authorization', 'Bearer {!$Credential.Password}')` against a `callout:bitly/v4/shorten` endpoint (`apexrefguide` L196211–196226).

**How to avoid:** Treat the flag as part of the contract, not an afterthought — deploy `<allowMergeFieldsInHeader>true</allowMergeFieldsInHeader>` in the same change as the Apex that depends on it, and assert on it in your post-deploy verification query (`CalloutOptionsAllowMergeFieldsInHeader` on the `NamedCredential` object, `object_reference` L185860–185868). If the callout returns 401 with a body echoing your header, the flag is off.

---

## Gotcha 3: `HTMLENCODE` Is the Only Formula Function Allowed Around a Merge Field, and It Works in Bodies Only

**What happens:** A password containing `&` or `<` breaks the XML or JSON body the callout sends, so the developer reaches for a formula function to escape it — `URLENCODE`, `JSENCODE`, or a nested expression — and the callout starts sending the literal formula text. Or they apply `HTMLENCODE` to a *header* merge field and the header value arrives unsubstituted.

**When it occurs:** On any password- or token-carrying merge field placed in a request body with special characters in the credential value. The guide's rule: "you can apply the HTMLENCODE formula function to escape special characters. The formula must start with HTMLENCODE, and other formula functions aren't supported. HTMLENCODE can't be used on merge fields in HTTP headers" (`apexdev` L34508–34513).

**How to avoid:** Bodies get `req.setBody('Password:{!HTMLENCODE($Credential.Password)}')`; headers get the bare `{!$Credential.Password}` with no wrapper. If the endpoint needs a differently-escaped value, escape it on the endpoint's side or pick a credential value that avoids the characters — there is no second formula function to reach for.

---

## Gotcha 4: `generateAuthorizationHeader` Defaults to True, So Apex That Builds Its Own `Authorization` Header Is Fighting the Platform

**What happens:** A developer sets `req.setHeader('Authorization', ...)` on a `callout:` request against a credential that is still generating its own authorization header. The endpoint sees a header it did not expect — or two candidate values — and rejects the call with a 401 that looks like a credential problem rather than a configuration collision.

**When it occurs:** Whenever `generateAuthorizationHeader` is left at its default. The field "Specifies whether Salesforce generates an authorization header and applies it to each callout that references the named credential… Defaults to true" (`api_meta` L90039–90046). The Apex Developer Guide names the only two reasons to deselect it: "The remote endpoint doesn't support authorization headers" or "The authorization headers are provided by other means. For example, in Apex callouts, the developer can have the code construct a custom authorization header for each callout" (`apexdev` L34429–34440).

**How to avoid:** Pick one owner of the `Authorization` header per credential and deploy it explicitly. Apex builds it → `<generateAuthorizationHeader>false</generateAuthorizationHeader>`. Platform builds it → Apex must not touch `Authorization` at all. Do not leave it implicit. One hard constraint on the choice: the same table states the option "is required if you reference the named credential from an external data source" — so a credential shared with Salesforce Connect cannot hand the header to Apex. **UNVERIFIED (2026-09-05):** which value wins when both are present. The guide states the two are alternatives but never publishes the precedence, so the failure is nondeterministic from the docs alone; deploy the flag rather than relying on an override.

---

## Gotcha 5: In a `SecuredEndpoint` Credential the URL Lives in a Parameter, Not in `<endpoint>` — and the Wrong One Deploys Cleanly

**What happens:** A developer hand-writes a modern Named Credential by copying an older file, keeps `<endpoint>https://…</endpoint>`, and sets `<namedCredentialType>SecuredEndpoint</namedCredentialType>`. The credential ends up with no URL, because the deployed `<endpoint>` is a legacy-only field. **UNVERIFIED (2026-09-05):** that the deploy itself succeeds rather than rejecting the element — the guide marks `endpoint` legacy-only and deprecated but does not state the validation behaviour on a `SecuredEndpoint` file, so treat a clean deploy as possible, not guaranteed.

**When it occurs:** On any hand-authored or LLM-generated `SecuredEndpoint` file. `endpoint` "is valid only when NamedCredentialType is set to Legacy" and "is deprecated in API version 56.0" (`api_meta` L90022–90030). The modern location is a `namedCredentialParameters` entry with `parameterType` `Url`: "Specifies that this parameter configures the URL of the endpoint. Store the actual URL in the `parameterValue` field" (`api_meta` L90352–90354). The same trap applies to `externalCredential`, which is a field of `NamedCredentialParameter` reached through a `parameterType` of `Authentication` (`api_meta` L90272–90278) — not a top-level element of `NamedCredential`.

**How to avoid:** Diff any hand-written credential against the guide's own sample definition (`api_meta` L90386–90410), which shows `Url`, `Authentication` and `ClientCertificate` parameters side by side. Faster field check: query the org. `Endpoint` and `PrincipalType` on the `NamedCredential` object are both flagged "only valid for legacy named credentials" and deprecated at 56.0 (`object_reference` L185910–185918, L186028–186038), so a modern credential returns nothing meaningful in them — and a credential that returns a populated `Endpoint` is not the modern model no matter what its `namedCredentialType` says.

---

## Gotcha 6: The Principal Grant Moved From the External Credential to the Permission Set at API 58.0

**What happens:** A developer copies a working External Credential from a Winter '23-era org, keeps its `<principal>My_Perm_Set</principal>` element, and deploys at API 61.0. Either the deploy rejects the element or it is dropped silently, and every callout returns 401 — because nothing now grants any user access to the principal.

**When it occurs:** On any credential authored against API 56.0–57.0 and redeployed later. `ExternalCredentialParameter.principal` "points to a permission set. That value then determines the set of users that are allowed to use credentials provided by the credential provider… First available in API version 56.0, this field is removed in API version 58.0 and later" (`api_meta` L63822–63831). The replacement lives on the other side of the relationship: `PermissionSet.externalCredentialPrincipalAccesses` "Indicates which external credential principals are available to users assigned to this permission set. Available in API version 59.0 and later" (`api_meta` L94794–94796).

**How to avoid:** In any org on API 59.0 or later, the External Credential declares the principal and the Permission Set grants it — two files, two deploys, in that order. Treat a `<principal>` element inside an `externalCredentialParameters` block as a migration marker, not as a working grant. **UNVERIFIED (2026-09-05):** how a credential is granted at exactly API 58.0, where the guide has removed `principal` but not yet introduced `externalCredentialPrincipalAccesses`. If your project is pinned at 58.0, verify against the org before assuming either mechanism.

---

## Gotcha 7: `externalCredentialPrincipal` Is Dash-Joined, and Packaging Silently Changes Its Shape

**What happens:** A permission set deploys with `<externalCredentialPrincipal>Partner_Orders_EC_PartnerOrdersNamedPrincipal</externalCredentialPrincipal>` (underscore) or with just the External Credential name. Callouts continue to fail with an authorization error that names no malformed reference. **UNVERIFIED (2026-09-05):** whether a malformed `externalCredentialPrincipal` is rejected at deploy time or accepted and ignored — the guide specifies the required format but not the validation.

**When it occurs:** Whenever the two halves are concatenated by hand. The field is "The name of the external credential and principal, separated by a **dash**. For example, `myExternalCredential-myPrincipal`" (`api_meta` L94995–94999). Packaging changes it again: "If the external credential and principal are part of a package, include the package's namespace prefix with the principal's name using this format: `namespacePrefix__myExternalCredential-myPrincipal`. Use two underscores (`__`) between the namespace prefix and the external credential principal's name" (`api_meta` L94999–95003).

**How to avoid:** Build the value from the two authoritative sources rather than from memory: the External Credential's file stem, a dash, and the `parameterName` of the `NamedPrincipal` or `PerUserPrincipal` parameter inside it. When the same permission set ships in a managed package, the value gains a namespace prefix and two underscores — so a packaged permission set and its unpackaged development twin do not carry identical XML.

---

## Gotcha 8: A Managed Package's Apex Cannot Use a Subscriber's Named Credential Unless the Namespace Is Listed on It

**What happens:** An ISV ships Apex that calls `callout:Subscriber_Config_NC`, documented for the subscriber to create themselves. The subscriber creates it correctly, with the right API name and a working principal, and the package's callouts still fail.

**When it occurs:** When the subscriber's Named Credential does not carry an `AllowedManagedPackageNamespaces` parameter naming the package. That `parameterType` "Allows managed packages identified by specified namespaces to use the named credential and make callouts through it" (`api_meta` L90315–90317) — an allowlist of namespaces permitted to call through the credential. **UNVERIFIED (2026-09-05):** that the allowlist is empty by default and that packaged code is therefore blocked without it. The guide states what the parameter allows, not what happens in its absence; confirm against a subscriber org before writing setup instructions that depend on it. The mirror-image case is a credential the ISV ships: `ManagedByNamespace` "Specifies the manageability capabilities for a packaged named credential. The `parameterValue` indicates whether the named credential uses subscriber-controlled or developer-controlled manageability" (`api_meta` L90342–90346).

**How to avoid:** Make the namespace allowlist part of the subscriber-facing setup instructions, not an afterthought, and validate it in the package's post-install check alongside the credential's existence. Ship credentials with an explicit `ManagedByNamespace` decision rather than defaulting, so subscribers know whether they may edit the endpoint.

---

## Gotcha 9: Running a `callout:` in Execute Anonymous Needs Customize Application, Which Most Developers Do Not Have in Production

**What happens:** A developer reproduces a production callout failure by pasting the callout into Execute Anonymous. It fails for them with a permission error, and they conclude the credential itself is broken — when the credential is fine and only their own access to run that block is not.

**When it occurs:** In any org where the developer holds Author Apex and API Enabled but not Customize Application. The Apex Developer Guide's permission table for anonymous blocks lists the requirement separately from the ordinary ones: "User permissions needed if an anonymous Apex callout references a named credential as the endpoint: **Customize Application**" (`apexdev` L14761–14762).

**How to avoid:** Reproduce through a test class with a mock, or through the deployed class invoked by a user who holds the permission set, rather than through Execute Anonymous. When Execute Anonymous is the only option, confirm Customize Application first so a permission failure is not misread as a credential failure.

---

## Gotcha 10: Editing a Named Credential Field Can Silently Invalidate Every User's Existing Authentication

**What happens:** An admin corrects a typo in a Named Credential — a path, a label, a URL — during business hours. Users who had been authenticated for months start getting auth failures, and nothing in the change log looks like a credential reset.

**When it occurs:** On per-user authentication in particular. The Object Reference's usage note on `NamedCredential` states it plainly: "Some named credential fields rely on per-user authentication to connect with an external system. If an admin edits one of these fields, then the previously authenticated credentials can get invalidated, requiring individual users to reauthenticate" (`object_reference` L186048–186050).

**How to avoid:** Treat edits to a per-user credential as a user-visible change with a re-authentication comms plan, not a config tweak — and schedule them like a deployment. Where the integration must keep running, the alternative is `calloutStatus` (`Enabled` | `Disabled`, API version 59.0 and later, `api_meta` L90000–90007): deploy the replacement credential `Disabled`, migrate, then flip. **UNVERIFIED (2026-09-05):** exactly which fields trigger the invalidation — the guide says "some" and does not enumerate them.

---

## Gotcha 11: Named Credentials Do Work With Continuations — the Real Restriction Is Private Connect

**What happens:** A team abandons a Continuation-based Visualforce or Lightning design because they believe `callout:` is unsupported there, and hardcodes an endpoint URL plus a manually built `Authorization` header into the Continuation controller — trading a working pattern for a credential in source.

**When it occurs:** Whenever the (false) incompatibility is taken as given. The Apex Developer Guide's own Continuation controller sample comments its endpoint field as "Callout endpoint as a named credential URL or, as shown here, as the long-running service URL", and the surrounding text repeats the `callout:My_Named_Credential/some_path` scheme in that context (`apexdev` L36006–36018). The restriction the guide *does* state is narrower: "Asynchronous callouts, including callouts that specify named credentials as the callout endpoint, aren't supported over Private Connect" (`apexdev` L36069–36070).

**How to avoid:** Use `callout:` in the Continuation's `HttpRequest` like anywhere else, and mock it with `Test.setContinuationResponse()` and `Test.invokeContinuationMethod()` (`apexdev` L36198–36199) rather than `Test.setMock`. The one design question that matters is whether traffic must traverse a private connection — i.e. whether `namedCredentialType` is `PrivateEndpoint` (`api_meta` L90143–90146). If it is, the Continuation is out and the callout belongs in a Queueable. Continuation limits apply either way: three parallel callouts per continuation, 120-second maximum timeout (`apexdev` L36299, L36303).

---

## Gotcha 12: A `UserExternalCredential` SOQL Gate Is Not a Documented Contract, and Its Presence Was Never a Token-Validity Signal

**What happens:** An Apex pre-flight check queries `UserExternalCredential` to decide whether the running user has authenticated, gets `true`, makes the callout, and still receives a 401 — because the access token expired and the refresh failed or was never issued.

**When it occurs:** In per-user OAuth flows. Two separate problems stack here. First, existence is a historical fact rather than a live one: a record says the user completed a flow at some point, not that a token is valid now. Second, and more fundamental for a coding agent: **UNVERIFIED (2026-09-05)** — neither `UserExternalCredential` nor `ExternalCredential` appears as a documented standard object in the Object Reference used for this skill (the sole occurrence of `UserExternalCredential` is a value inside an unrelated picklist list at `object_reference` L142361). Their queryability, field names, filterability, and even their availability by org configuration are unconfirmed here. `ExternalCredential` is confirmed only as a **metadata** type (`api_meta` L63601).

**How to avoid:** Do not let a pre-flight query be the only thing standing between the user and a confusing error. Handle 401 and 403 in the callout path itself and turn them into a re-authentication prompt, which works whether or not the gate query is available. If you do want the gate, run `sf sobject describe --sobject UserExternalCredential` against the target org first and code against what the describe actually returns, rather than against an assumed field list — and keep the callout's own 401 handling regardless.

---

## Gotcha 13: Named Credential Metadata Is Invisible to Users Without View Setup and Configuration

**What happens:** A CI job or a low-privilege integration user runs a retrieve or a drift-detection query over Named Credentials and gets an empty result, which downstream tooling reads as "no credentials exist" rather than "you cannot see them."

**When it occurs:** Since Spring '20, on both surfaces. The metadata type: "As of Spring '20 and later, only users with the View Setup and Configuration permission can access this type" (`api_meta` L89909). The SObject: the same sentence, applied to the object (`object_reference` L185801–185803). The `AuthProviderId` field is tighter still — "Only users with the 'Customize Application' and 'Manage AuthProviders' permissions can view this field" (`object_reference` L185815–185816).

**How to avoid:** Give the deployment and audit identity View Setup and Configuration explicitly, and make the tooling distinguish an empty result from a permission-denied one. A drift check that cannot tell those apart will report a clean org right up until the day a credential goes missing.

---

## Gotcha 14: An `AuthHeader` Parameter Without `parameterValue` Fails Deploy Validation — and the Failure Cascades to Every Permission Set Naming Its Principal

**What happens:** An `ExternalCredential`'s `AuthHeader` parameter carries `parameterName`, `parameterType`, `sequenceNumber` and `description` but no `parameterValue` — typically because the plan never captured the two facts the header formula needs: the endpoint URL and the name of the authentication parameter the API key is stored under in Setup. `sf project deploy start --dry-run` rejects the credential outright, verbatim:

```
The parameter type "AuthHeader" requires these fields: ParameterValue.
```

Any `PermissionSet` in the same deploy whose `externalCredentialPrincipalAccesses` names a principal on the failed credential fails in the same request, verbatim:

```
The <principal> parameter value doesn't exist or you may not have permission to access it.
```

Nothing is wrong with the permission set — it cannot resolve a principal that never validated because the credential ahead of it in the deploy order rejected first.

**When it occurs:** Whenever an `AuthHeader` `externalCredentialParameters` entry is authored — by hand or generated — with its `parameterValue` left empty or omitted, most often because the header formula's own inputs (the endpoint URL; the name of the Setup-entered authentication parameter it merges in, e.g. `ApiKey` or `ApiToken`) were never asked for before the file was written. **UNVERIFIED (2026-09-12): proven live in a dry-run (error text verbatim), not stated in the guide** — the Metadata API Developer Guide documents that an `AuthHeader`'s `parameterValue` "must be a formula of a header value that is evaluated at run time" (`api_meta` L63757–63764) but never states that the field is mandatory or names the deploy-time error; the requirement surfaced only from `sf project deploy start --dry-run` (API 67.0) against a real org, not from any corpus text cited in this skill.

**How to avoid:** Before authoring the `ExternalCredential`, get both facts from the requester: the endpoint URL (host + path, and whether sandbox and production share a host) and the name of the authentication parameter the header formula will merge in. Write the formula as `{!$Credential.<ExternalCredentialDeveloperName>.<ParameterName>}` (or a concatenation such as `{!'Bearer ' & $Credential.<EC>.<ParameterName>}`) and never leave `parameterValue` empty on an `AuthHeader` parameter. The parameter the formula references (`ApiKey`, `ApiToken`, or whatever name is agreed) is created in **Setup → Named Credentials → External Credentials → \<credential> → Principals → \<principal> → New (Authentication Parameter)**, after the metadata deploys — it is never declared in the `ExternalCredential` XML itself. That gap is also why a validate-only deploy of the credential can pass cleanly with the parameter's formula in place while the actual key value in Setup is still empty: the deploy checks shape, not the secret. The first real proof the key works is a runtime 401 on a live callout, not a green deploy. Run the checker's `NC-AUTH-01` (empty `parameterValue`) and `NC-AUTH-02` (a formula scoped to a different External Credential than the file it lives in) before deploying, and expect a `NC-PS-01` finding on the permission set to be a deploy-order artifact, not a defect, once the credential itself validates.
