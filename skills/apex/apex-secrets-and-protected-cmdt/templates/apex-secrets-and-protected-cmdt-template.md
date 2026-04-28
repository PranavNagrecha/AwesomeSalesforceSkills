# Apex Secrets and Protected CMDT — Work Template

Use this template when adding, rotating, or refactoring secret storage in Apex.

## Scope

**Skill:** `apex-secrets-and-protected-cmdt`

**Request summary:** (fill in what the user asked for — e.g. "store outbound webhook signing key", "rotate Stripe API key", "remove hardcoded credential")

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- **Secret purpose:** (callout auth | signing key | symmetric crypto key | per-tenant lookup token | record-data encryption)
- **Packaging shape:** (managed package with namespace `___` | unmanaged 2GP | unmanaged DX | bare org)
- **Threat model:** (subscriber-invisible only | source-org-admin-invisible required | regulated record data)
- **Rotation owner:** (team / individual)
- **Rotation cadence:** (e.g. 90 days, on demand)
- **Known constraints:** (governor limits, integration partner SDK, Shield licensing, Salesforce edition)

## Decision Matrix

Pick the row that matches the secret purpose AND the packaging shape. If no row matches, escalate.

| Secret purpose | Managed package | Unmanaged DX |
|---|---|---|
| Callout authentication (HTTP Authorization, OAuth, mTLS) | Named Credential / External Credential | Named Credential / External Credential |
| HMAC signing key (outbound) | Protected CMDT + `@NamespaceAccessible` getter | Off-platform vault via Named Credential |
| Inbound webhook shared secret (per-tenant) | Protected Hierarchy Custom Setting + `@NamespaceAccessible` | Off-platform vault via Named Credential |
| Symmetric AES key | `Crypto.generateAesKey(256)` at install, ciphertext in Protected CMDT or off-platform KMS | Off-platform KMS only |
| Field-level data at rest (PII, regulated) | Shield Platform Encryption | Shield Platform Encryption |
| Source-org-admin-invisible | Off-platform vault | Off-platform vault |

## Apex Retrieval Pattern

The canonical secret-retrieval shape inside a managed-package namespace:

```apex
public with sharing class SecretsProvider {

    public class SecretsException extends Exception {}

    @NamespaceAccessible
    public static String getSecret(String key) {
        if (String.isBlank(key)) {
            throw new SecretsException('Secret key required');
        }
        Secret_Config__mdt cfg = Secret_Config__mdt.getInstance(key);
        if (cfg == null || String.isBlank(cfg.Value__c)) {
            throw new SecretsException('No secret configured for key=' + key);
        }
        return cfg.Value__c;
    }

    @NamespaceAccessible
    public static Blob getSecretBlob(String key) {
        return EncodingUtil.base64Decode(getSecret(key));
    }
}
```

Callers inside the same namespace:

```apex
Blob signingKey = SecretsProvider.getSecretBlob('Outbound_Webhook_Signing_Key');
Blob mac = Crypto.generateMac('HmacSHA256', payload, signingKey);
```

## Source-Control Hygiene

Add to `.forceignore` the day the type is created:

```
# Secret-bearing CMDT records — values created post-deploy, never committed
**/customMetadata/Secret_Config.*.md-meta.xml
**/customMetadata/Webhook_Signing_Key.*.md-meta.xml
```

## Rotation Runbook (template — fill in per secret)

1. Generate new secret value (`Crypto.generateAesKey(256)` for symmetric, vendor portal for third-party).
2. Insert new CMDT row with `Active__c = false`, new `Key_Version__c`.
3. Sync with downstream consumer (vendor dashboard / receiving service).
4. Flip `Active__c = true` on new row, `Active__c = false` on old row in same deploy.
5. Monitor for 24h; if no errors, retire old row (set `RetiredOn__c`).
6. Audit `customMetadata/` directory in repo to confirm no records committed.

## Verification

Before marking work complete:

- [ ] No `String API_KEY = '...'`, `String SECRET = '...'`, etc. in any `.cls` (run checker script)
- [ ] No `customMetadata/*.md-meta.xml` containing fields named `Api_Key__c`, `Secret__c`, `Token__c`, `Password__c` with values (run checker script)
- [ ] No `System.debug` of secret-named variables (run checker script)
- [ ] `@NamespaceAccessible` annotation present on all secret-getter methods
- [ ] CMDT type confirmed Protected in metadata (`<protected>true</protected>`)
- [ ] Custom Setting confirmed Protected in metadata (`<visibility>Protected</visibility>`)
- [ ] `.forceignore` rule added for secret-bearing CMDT records
- [ ] Rotation runbook written, owner assigned, first rotation date scheduled
- [ ] Subscriber-vs-source-org threat model documented in the secret-storage decision record

## Notes

Record any deviations from the standard pattern and why (e.g. third-party SDK that requires a raw `String` and cannot accept Named Credential injection).
