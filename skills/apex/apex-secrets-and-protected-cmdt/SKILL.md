---
name: apex-secrets-and-protected-cmdt
description: "Storing API keys, signing secrets, and third-party tokens that Apex must consume — Protected Custom Metadata in a managed package, Protected Custom Settings, Encrypted Custom Fields, Apex Crypto, and what to NEVER do (hardcode, unprotected CMDT, System.debug). NOT for callout authentication — use apex/apex-named-credentials-patterns. NOT for computing the HMAC or signature itself — use apex/apex-encoding-and-crypto. NOT for record-level Shield data encryption — use security/platform-encryption."
category: apex
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
triggers:
  - "where do I store an API key that apex needs to call a third party"
  - "protected custom metadata type secret salesforce admin cannot read"
  - "namespaceaccessible getter for hmac signing key apex"
  - "should I put a secret in custom setting or custom metadata"
  - "rotate webhook signing secret without code deploy"
  - "subscriber org admin can see my protected cmdt values"
inputs:
  - Type of secret (callout auth, signing key, symmetric crypto key, lookup token)
  - Whether the code lives in a managed package or unmanaged DX project
  - Rotation cadence and operational ownership
  - Subscriber-vs-source-org threat model
outputs:
  - Storage decision (Named/External Credential, Protected CMDT, Protected Custom Setting, Encrypted Field, off-platform vault)
  - Apex retrieval pattern with @NamespaceAccessible where required
  - Documented rotation procedure
  - Source-control exclusion rules for `customMetadata/*-md.xml`
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
tags:
  - apex
  - secrets
  - cmdt
  - encryption
  - protected
  - named-credentials
  - security
---

# Apex Secrets and Protected Custom Metadata

Activate when Apex needs to consume a secret value — API key, HMAC signing key, third-party token, per-tenant credential — and the engineer is reaching for `String API_KEY = '...';` or a plain Custom Setting. The platform offers a small set of correct mechanisms; pick the one that matches the secret's purpose and the deployment shape (managed package vs unmanaged DX), then document a rotation procedure.

## Before Starting

- Identify the secret's **purpose**: callout authentication, signature verification, symmetric encryption, or lookup token. The right storage differs.
- Confirm whether the consuming Apex ships in a **managed package** (with a namespace) or an unmanaged DX project. "Protected" Custom Metadata and "Protected" Custom Settings are only protected against **subscribers** — they offer zero protection in the source org.
- Decide who owns **rotation** and on what cadence. A secret with no rotation procedure is a future incident.

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Does the Apex ship in a managed package installed in subscriber orgs? | Gotcha 1: protection applies only there | Whether Protected CMDT/settings protect anything at all |
| Is the secret used as callout authentication? | Decision tree: Named Credentials own that case | Removes Apex from the secret path entirely |
| Must your own org's admins be unable to read it? | Gotcha 1: the source org always sees it | Forces an off-platform vault decision early |
| Will several 2GP packages share the namespace? | Gotcha 3: `@NamespaceAccessible` crosses packages | Which getters need the annotation, and who can call them |
| Are developers working in scratch orgs with the shared namespace? | Gotcha 1: secrets are visible there | Keeps real values out of scratch orgs |
| Who rotates the value, and is a deploy acceptable? | Gotcha 2: records in git defeat rotation | A runbook and a `.forceignore` rule on day one |
| Will anyone debug the integration in production? | Gotcha 5: debug logs keep what you print | A hash-only logging rule before the incident |

A proper configuration decides the threat model first, so the storage choice is defensible, where "just doing it" stores a key wherever the first tutorial put it.

## Core Concepts

### The canonical decision tree

| Secret purpose | Correct storage |
|---|---|
| Callout authentication (Authorization header, OAuth, mTLS) | Named Credential / External Credential — always. Apex never sees the credential. |
| HMAC signing / webhook verification key | Protected Custom Metadata in a managed package, retrieved via `@NamespaceAccessible` Apex |
| Symmetric encryption key (AES) | `Crypto.generateAesKey(256)` at install time, store ciphertext via Protected CMDT or off-platform vault — never hardcode |
| Per-tenant lookup token / config secret | Protected Custom Setting (Hierarchy) in a managed package |
| Field-level data encryption at rest | Shield Platform Encryption (Encrypted Custom Fields) |
| Anything that needs admin-invisibility in the source org | Off-platform vault (HashiCorp, AWS KMS) — Salesforce cannot hide a value from a System Admin in the org that owns the metadata |

### Why "Protected" only protects against subscribers

Protection "only applies to custom settings that are marked protected and installed to a subscriber organization as part of a managed package"; otherwise they are public and "readable for all profiles, including the guest user" (apexdev 264 L13709-13711). Protected custom metadata types behave the same way outside a managed package (apexref 262 L170826-170828). The specific list of subscriber channels that are blocked (UI, SOQL, Workbench, Tooling API, anonymous Apex) is UNVERIFIED (2026-10-20); the packaging guide notes the package developer, logged in to a subscriber org as a user, can view and edit protected custom settings data (pkg2 264 L22831). Protection is a **packaging boundary**, not a cryptographic one. For custom metadata types, Metadata API also offers `<visibility>PackageProtected</visibility>` (API 47.0+): "only accessible by the custom Apex code in the package. Use this value to secure secrets such as API access keys" (api_meta 264 L44593-44594).

Implication: shipping "Protected" CMDT in an unlocked package or DX project gives you **none** of the protection you may have read about; outside a managed package the guide says to use named credentials or encrypted custom fields for secrets (apexdev 264 L13712-13713). The values land in `force-app/main/default/customMetadata/MySecret.Foo.md-meta.xml` and ride your git history forever.

### `@NamespaceAccessible` and the secret-getter pattern

Inside the managed package, the secret retrieval method is annotated:

```apex
global class SecretsProvider {
    @NamespaceAccessible
    public static String getSecret(String key) {
        Secret_Config__mdt cfg = Secret_Config__mdt.getInstance(key);
        return cfg?.Value__c;
    }
}
```

Corrected 2026-10-20: `public` alone already makes `getSecret` "accessible by all Apex within a specific package" (apexdev 264 L3661). `@NamespaceAccessible` widens that to other 2GP packages sharing the namespace (apexdev 264 L3661-3663; pkg2 264 L17987-17990); `global` is available across all namespaces (pkg2 264 L17989-17990), which is what lets subscriber code call it. `getInstance(developerName)` returns null when no record matches (apexref 262 L204618-204620), hence the `?.`. `getInstance()` and `getAll()` return "only the first 255 characters of any field" — a Long Text Area secret longer than that is silently truncated; read it with SOQL instead (apexref 262 L204570-204571, L204645-204647).

### Custom Settings, Hierarchy, Protected

A Hierarchy Custom Setting marked **Protected** behaves like Protected CMDT: only managed-package code can read it. Hierarchy `getInstance()` returns the record for the current user, merged from the lowest level defined (apexref 262 L205082-205084). "Hierarchy is preferable to List because per-org values don't bloat the schema" is UNVERIFIED (2026-10-20). Same caveat: only protected against subscribers.

### Shield Platform Encryption is for record data, not configuration

Shield Platform Encryption exists for PII and regulated record data — encryption-at-rest with key management. That a Shield-encrypted value "still appears in screens, reports and Apex SOQL results" is UNVERIFIED (2026-10-20). Do not confuse it with Classic **encrypted custom fields** (Text (Encrypted)), which the Apex guide names as a secret store outside managed packages (apexdev 264 L13712-13713): only users with View Encrypted Data can see them, and they are limited to 175 characters (secguide 262 L2486, L2522) — too short for some keys.

## Common Patterns

### Pattern: HMAC signing key in Protected CMDT

Define `Webhook_Secret__mdt` with `Value__c` (Long Text Area), mark the type **Protected**, ship inside a managed package. Apex:

```apex
@NamespaceAccessible
public static Blob signingKey() {
    return Blob.valueOf(Webhook_Secret__mdt.getInstance('Outbound').Value__c);
}
```

### Pattern: Custom-supplied per-tenant API key

Subscriber needs to plug in their own third-party key. Store it in a **Protected Hierarchy Custom Setting** with one record per packaging-namespace install, with a setup screen the admin uses to enter the value. Apex reads via `Tenant_Config__c.getInstance().Api_Key__c` from inside the namespace. The admin enters but cannot read back from outside the package.

### Pattern: Symmetric crypto with rotated key material

Store key version metadata in Protected CMDT (`Key_Version__c`, `Active__c`, `RetiredOn__c`); store the actual ciphertext key in an off-platform vault retrieved via Named Credential at use time. Rotate by inserting a new active version and deprecating the prior one — old ciphertext still decrypts via version lookup.

## Decision Guidance

| Situation | Correct mechanism | Why |
|---|---|---|
| Apex needs to call a SaaS REST API with bearer token | Named Credential + External Credential | Apex never sees the secret; framework injects it |
| Verifying inbound webhook signatures | Protected CMDT in managed package | Symmetric secret, retrieved by namespace-only Apex |
| Encrypting a value for storage in a custom field | Shield Platform Encryption (BYOK preferred) | Platform handles key lifecycle and access control |
| Per-tenant integration credential | Protected Hierarchy Custom Setting (managed) | Per-org configurable; admin writes but cannot read |
| Secret you must hide from your own org's admin | Off-platform vault | Salesforce cannot hide metadata from a source-org admin |

## Recommended Workflow

1. Classify the secret by purpose using the decision tree; reject hardcoding outright.
2. Confirm packaging shape — managed (namespace) vs unmanaged (DX). If unmanaged and the secret needs subscriber-invisibility, escalate to managed packaging or off-platform vault.
3. Pick storage: Named Credential (callouts), Protected CMDT or Protected Custom Setting (managed package), Encrypted Field (record data), or off-platform vault (admin-invisible).
4. Implement Apex retrieval as a `public` getter (add `@NamespaceAccessible` only when other 2GP packages in the namespace must call it; never `global`); never read into a `static final String` constant.
5. Add a `.forceignore` rule (or explicit absence from `package.xml`) so `customMetadata/Secret_Config.*.md-meta.xml` records do not get committed with values.
6. Document a rotation procedure: who rotates, on what cadence, the runbook to update the CMDT row, and how dependent integrations re-sync.
7. Run `scripts/check_apex_secrets_and_protected_cmdt.py` against the repo to detect hardcoded literals, unprotected secret-named CMDT fields, and `System.debug` of secret-named variables.

## Review Checklist

- [ ] No `String API_KEY = '...'` or equivalent in any `.cls`
- [ ] Callout secrets use Named Credential; Apex never holds the value
- [ ] CMDT used for secrets is marked Protected AND ships in a managed package
- [ ] Custom Settings used for secrets are Hierarchy + Protected, in managed package
- [ ] `customMetadata/*.md-meta.xml` for secret types is excluded from source control
- [ ] No `System.debug` of variables named like a secret
- [ ] Rotation procedure documented and assigned an owner
- [ ] Subscriber-vs-source-org threat model documented

## Salesforce-Specific Gotchas

1. **Protected does not protect outside a managed package installed in a subscriber org.** There, protected settings are "readable for all profiles, including the guest user" (apexdev 264 L13709-13711).
2. **Custom Metadata records are source-controlled by default.** `sf project retrieve` pulls `customMetadata/*.md-meta.xml` into git — including secret values someone typed in once. Add a `.forceignore` rule the day you create the type.
3. **`public` already reaches every class in the package** (apexdev 264 L3661) — corrected 2026-10-20; the old text said `@NamespaceAccessible` is required inside one package. The annotation is for other 2GP packages sharing the namespace (pkg2 264 L17987-17990); never make a secret getter `global`.
4. **Rotation must be planned upfront.** CMDT updates are deployable, but a rotation runbook that requires a deploy each time is operationally fragile — design the type so a manual record edit (by a controlled admin) is the rotation step.

## Output Artifacts

| Artifact | Description |
|---|---|
| Secret-storage decision record | One-pager mapping each secret to mechanism, owner, rotation cadence |
| Protected CMDT definition | XML for `Secret_Config__mdt` with `Value__c` Long Text Area |
| `@NamespaceAccessible` getter | Apex helper class shipped inside the managed namespace |
| `.forceignore` snippet | Excludes `customMetadata/Secret_Config.**` from retrieve/deploy |
| Rotation runbook | Step-by-step doc for the on-call rotation owner |

## Related Skills

- `apex/apex-named-credentials-patterns` — callout authentication (the most common reason engineers reach for "store an API key")
- `security/platform-encryption` — record-data encryption-at-rest
- `apex/apex-encoding-and-crypto` — `Crypto.generateAesKey`, signing, hashing
- `devops/pipeline-secrets-management` — keeping secrets out of source and CI
