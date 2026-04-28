---
name: apex-secrets-and-protected-cmdt
description: "Storing API keys, signing secrets, and third-party tokens that Apex must consume — Protected Custom Metadata in a managed package, Protected Custom Settings, Encrypted Custom Fields, Apex Crypto, and what to NEVER do (hardcode, unprotected CMDT, System.debug). NOT for callout authentication — see apex-named-credentials-patterns; NOT for record-level data encryption — see Shield Platform Encryption."
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
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

Protected Custom Metadata Types and Protected Custom Settings expose values **only to Apex code in the same managed-package namespace**. In the subscriber org, the admin cannot read them via UI, SOQL, Workbench, the Tooling API, or anonymous Apex. In the **packaging org** (or any unmanaged project) the System Admin retains full visibility — protection is a **packaging boundary**, not a cryptographic one.

Implication: shipping "Protected" CMDT in an unmanaged 2GP or DX project gives you **none** of the protection you may have read about. The values land in `force-app/main/default/customMetadata/MySecret.Foo.md-meta.xml` and ride your git history forever.

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

The `@NamespaceAccessible` annotation lets other classes in the same namespace call `getSecret`; subscriber code cannot. Combined with Protected CMDT, this is the platform-canonical pattern for shipping a signing key.

### Custom Settings, Hierarchy, Protected

A Hierarchy Custom Setting marked **Protected** behaves like Protected CMDT: only managed-package code can read it. Hierarchy is preferable to List for secrets because per-org values don't bloat the schema. Same caveat: only protected against subscribers.

### Shield Platform Encryption is for record data, not configuration

Encrypted Custom Fields exist for PII and regulated record data — encryption-at-rest with key management (BYOK or platform-managed). They are not the right home for a webhook signing key; the value still appears in screens, reports (with permission), and Apex SOQL results. Use Shield for "the customer's tax ID," not for "our outbound HMAC secret."

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
4. Implement Apex retrieval with `@NamespaceAccessible` for managed-package secret getters; never read into a `static final String` constant.
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

1. **Protected does not protect against the source-org admin.** The promise applies only to subscribers of a managed package. In your own org, every System Admin can query, view, and export every "Protected" CMDT row.
2. **Custom Metadata records are source-controlled by default.** `sf project retrieve` pulls `customMetadata/*.md-meta.xml` into git — including secret values someone typed in once. Add a `.forceignore` rule the day you create the type.
3. **`@NamespaceAccessible` is required to expose secret-getters across classes inside a managed package** while keeping subscriber code locked out. Without it, either the method is private (unreachable from sibling classes) or global (callable by subscriber code).
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
- `security/shield-platform-encryption` — record-data encryption-at-rest
- `apex/apex-crypto-patterns` — `Crypto.generateAesKey`, signing, hashing
- `devops/source-control-hygiene` — `.forceignore` patterns and secret-leak scanning
