# Gotchas — Apex Secrets and Protected CMDT

Non-obvious Salesforce platform behaviors that cause real production secret leaks.

## Gotcha 1: Protected CMDT only protects against subscribers, never against the source-org admin

**What happens:** A team marks a Custom Metadata Type "Protected", believes the values are now hidden, and stores production credentials in the source org. Any System Administrator (or any user with View All Custom Settings + Customize Application) can still read every row via Setup, Workbench, the Tooling API, and anonymous Apex. The "Protected" promise applies only when the type ships INSIDE a managed package and is read FROM a subscriber org.

**When it occurs:** Unmanaged 2GP DX projects, unmanaged orgs, and the packaging org itself. Anyone who reads the Salesforce help article and skips the "managed package" prerequisite makes this mistake.

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

## Gotcha 3: `@NamespaceAccessible` is the (only) correct access modifier for cross-class secret getters in a managed package

**What happens:** A developer wants other classes inside their managed namespace to call `SecretsProvider.getSecret(...)`. They mark the method `public` — but `public` in a managed package only allows callers from the same class file. They switch to `global` — but now any subscriber Apex can call it and exfiltrate the secret. Either choice breaks the threat model.

**When it occurs:** Whenever a managed-package developer assumes Apex access modifiers behave like Java's `public`. They don't — namespace boundaries override class-level visibility.

**How to avoid:** Annotate the method with `@NamespaceAccessible`. This makes it callable from any class inside the same namespace and inaccessible from subscriber code. The annotation also works on classes, properties, constructors, and inner types.

```apex
public class SecretsProvider {
    @NamespaceAccessible
    public static String getSecret(String key) { /* ... */ }
}
```

---

## Gotcha 4: Shield Platform Encryption has indexing and SOQL caveats that surprise teams

**What happens:** A team encrypts `Account.External_Id__c` with Shield, then their integration breaks because case-insensitive search returns no results, `LIKE` queries don't work, ORDER BY orders by ciphertext, and indexed lookups slow down. Some operators (`<`, `>`, `STARTS WITH`) are unsupported on encrypted fields.

**When it occurs:** Most often during the first integration after enabling Shield on a previously-unencrypted field, especially when external systems sync via Bulk API filtering on the now-encrypted column.

**How to avoid:** Read the "Which Salesforce Functions Don't Work with Encrypted Data" help article BEFORE encrypting. For external IDs, prefer hashing or HMAC-ing the value into a separate non-encrypted lookup column rather than encrypting the column itself. Test SOQL filters and report behavior in a sandbox with Shield enabled.

---

## Gotcha 5: `System.debug` of a secret variable lands in the debug log forever

**What happens:** Debug log lines are not purged on demand; they remain available for download by anyone with the View All Data permission until the log expires. A `System.debug('key=' + apiKey)` line written for a single bug investigation leaks the secret to every developer with debug-log access for the next 24 hours and to any Event Monitoring archive indefinitely.

**When it occurs:** During incident triage, when a developer enables a TraceFlag and adds debug statements to figure out why a callout is failing 401.

**How to avoid:** Never `System.debug` a variable whose name matches `*key*`, `*secret*`, `*token*`, `*password*`, `*credential*`. The checker script in this skill flags this. For incident investigation, log a hash of the secret (`EncodingUtil.convertToHex(Crypto.generateDigest('SHA-256', Blob.valueOf(apiKey)))`) so you can compare values without leaking them.
