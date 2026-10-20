# Gotchas — Apex Secrets and Protected CMDT

Non-obvious Salesforce platform behaviors that cause real production secret leaks.

## Gotcha 1: Protected CMDT only protects against subscribers, never against the source-org admin

**What happens:** A team marks a Custom Metadata Type "Protected", believes the values are now hidden, and stores production credentials in the source org. Outside a managed package, protected types "behave like public custom metadata types", which "are readable for all profiles, including the guest user" (apexref 262 L170826-170827; custom settings: apexdev 264 L13709-13711). The exact permission set a source-org user needs to read rows (View All Custom Settings + Customize Application) is UNVERIFIED (2026-10-20). The "Protected" promise applies only when the type ships INSIDE a managed package installed in a subscriber org.

**When it occurs:** Unlocked packages, DX projects, unmanaged orgs, and the packaging org itself. Also scratch orgs: when several second-generation packages share a namespace, protected values are "visible to any of your developers that are working in a scratch org with a shared namespace" — workaround: none (sfdx 264 L18905-18912).

**How to avoid:** If the threat model includes the source-org admin, do not store the secret in Salesforce metadata at all — use an off-platform vault accessed via Named Credential. If the threat model is only subscribers, ship the type inside a managed package with a namespace and verify protection by testing read access from a subscriber sandbox.

---

## Gotcha 2: Custom Metadata records are source-controlled by default

**What happens:** A developer creates `Webhook_Signing_Key__mdt` and adds a real signing key as a record. `sf project retrieve --metadata CustomMetadata` pulls `force-app/main/default/customMetadata/Webhook_Signing_Key.Outbound.md-meta.xml` into the working tree. They commit "wire up webhook signing" and push. The signing key is now in git history forever.

**When it occurs:** Any time a developer uses `sf project retrieve` or scratch-org pull workflows after typing a real value into a CMDT row in their dev environment.

**How to avoid:** The day you create a secret-bearing CMDT, add this to `.forceignore`:

```
**/customMetadata/Webhook_Signing_Key.*.md-meta.xml
```

Treat secret CMDT records as runtime-only configuration that is created post-deploy via a controlled procedure, not retrieved-and-committed. Run a pre-commit hook that scans staged `customMetadata/*.md-meta.xml` for fields named like `*Key*`, `*Secret*`, `*Token*`, `*Password*`.

---

## Gotcha 3: `global` on a secret getter hands it to subscriber code; `public` was already enough

**What happens:** Corrected 2026-10-20 — this gotcha used to say `public` "only allows callers from the same class file". The guide says `public` means "accessible by all Apex within a specific package" (apexdev 264 L3661). A developer who believes the old claim switches the getter to `global`, and "Apex that is declared global is always available across all namespaces" (pkg2 264 L17989-17990) — subscriber Apex can now call it.

**When it occurs:** When a namespace is split across several 2GP packages and a getter in one package must be called from another.

**How to avoid:** Keep the getter `public`. Add `@NamespaceAccessible` only for cross-package callers in the same namespace: it "makes public Apex in a package available to other packages that use the same namespace" (pkg2 264 L17987).

```apex
public class SecretsProvider {
    @NamespaceAccessible
    public static String getSecret(String key) { /* ... */ }
}
```

---

## Gotcha 4: Shield Platform Encryption has indexing and SOQL caveats that surprise teams

**What happens:** A team encrypts `Account.External_Id__c` with Shield, then their integration breaks because case-insensitive search returns no results, `LIKE` queries don't work, ORDER BY orders by ciphertext, and indexed lookups slow down. Some operators (`<`, `>`, `STARTS WITH`) are unsupported on encrypted fields. UNVERIFIED (2026-10-20): the Shield query restrictions are help-only; the corpus security guide documents only Classic encrypted text fields (no filters, reports criteria or search — secguide 262 L2523-2525).

**When it occurs:** Most often during the first integration after enabling Shield on a previously-unencrypted field, especially when external systems sync via Bulk API filtering on the now-encrypted column.

**How to avoid:** Read the "Which Salesforce Functions Don't Work with Encrypted Data" help article BEFORE encrypting. For external IDs, prefer hashing or HMAC-ing the value into a separate non-encrypted lookup column rather than encrypting the column itself. Test SOQL filters and report behavior in a sandbox with Shield enabled.

---

## Gotcha 5: `System.debug` of a secret variable stays readable for the log's whole retention window

**What happens:** "System debug logs are retained for 24 hours. Monitoring debug logs are retained for seven days" (apexdev 264 L38605). A `System.debug('key=' + apiKey)` line written for a single bug investigation leaks the secret to every developer with debug-log access for that window. Who may download logs (View All Data) and any Event Monitoring archive are UNVERIFIED (2026-10-20).

**When it occurs:** During incident triage, when a developer enables a TraceFlag and adds debug statements to figure out why a callout is failing 401.

**How to avoid:** Never `System.debug` a variable whose name matches `*key*`, `*secret*`, `*token*`, `*password*`, `*credential*`. The checker script in this skill flags this. For incident investigation, log a hash of the secret (`EncodingUtil.convertToHex(Crypto.generateDigest('SHA-256', Blob.valueOf(apiKey)))`) so you can compare values without leaking them.
