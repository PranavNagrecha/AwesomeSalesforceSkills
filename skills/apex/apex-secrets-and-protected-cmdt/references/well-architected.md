# Well-Architected Notes — Apex Secrets and Protected CMDT

## Relevant Pillars

- **Security** — Primary pillar. This skill governs storage of credentials, signing keys, encryption keys, and tenant tokens. Wrong storage decisions create direct paths to data exfiltration, replay attacks, and compliance findings (PCI, HIPAA, SOC 2, FedRAMP).
- **Operational Excellence** — Secondary. Every secret needs a rotation procedure, an owner, and a runbook. Secrets without operational ownership become risk debt.
- **Reliability** — Tertiary. A secret rotation that requires a code deploy is fragile; design storage so the rotation is a controlled data update, not a release event.

## Architectural Tradeoffs

| Tradeoff | Decision criteria |
|---|---|
| Named Credential vs Apex-managed secret | Always Named Credential when the secret is used as callout authentication. Apex-managed only when the secret is consumed by an SDK that won't accept platform-injected headers. |
| Protected CMDT vs Protected Custom Setting | CMDT for global, deploy-time-frozen secrets (signing keys); Custom Setting for per-tenant runtime-configurable values (subscriber-supplied API keys). |
| In-org Protected CMDT vs off-platform vault | In-org acceptable when the threat model is "subscribers should not see this." Off-platform required when the threat model is "even our own admins should not see this." |
| Encrypted Custom Field vs Plain Text + access control | Shield encryption when the field holds regulated data at rest. Plain text + sharing controls when the data is reference-only and not regulated. |

## Anti-Patterns

1. **"Protected = secret" without managed-package context** — Engineers read "Protected" in the Salesforce docs and assume it means "encrypted and hidden from everyone." It means "hidden from subscribers of a managed package." In an unmanaged DX project the protection is zero. Always pair the Protected designation with explicit managed-package packaging plans.
2. **Hardcoded "temporary" secrets** — `private static final String API_KEY = 'sk_live_...'` with a "fix before prod" comment. The secret is now in version control, in CI logs, in every developer's clone, and in any compiled artifact. There is no "temporary" — it is permanent the moment it is committed.
3. **Secret-bearing CMDT records committed to source control** — `customMetadata/*.md-meta.xml` files are pulled by `sf project retrieve` and committed alongside code. Without an explicit `.forceignore` rule, the secret value lives in git history.
4. **No rotation procedure** — A secret with no documented rotation owner and cadence is a future incident. Treat rotation runbooks as a deliverable equal to the storage decision.
5. **`System.debug` of secret values** — Debug logs are downloadable artifacts retained for hours and archived for years in Event Monitoring. Logging a secret once leaks it persistently.

## Official Sources Used

- Apex Developer Guide 264 — protected custom settings public outside a managed package, readable by guest user (salesforce_apex_developer_guide.txt L13709-13713); `public` = all Apex in the package (L3661-3663); debug log retention 24 h / 7 days (L38605)
- Metadata API 264 — `Protected` / `PackageProtected` visibility (api_meta.txt L44591-44594)
- Packaging 264 — `@NamespaceAccessible` across same-namespace 2GP packages; `global` across all namespaces (pkg2_dev.txt L17987-17990); sfdx 264 scratch-org shared-namespace exposure (sfdx_dev.txt L18905-18912)
- Apex Reference 262 — protected CMDT behaves as public outside managed package (L170826-170828); `getInstance(developerName)` returns null on no match (L204618-204620); hierarchy `getInstance()` (L205082-205084); Security Guide 262 — Classic encrypted text 175-char limit (salesforce_security_impl_guide.txt L2522)

- Custom Metadata Types — Protect Sensitive Data — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_metadata_security.htm
- Apex Developer Guide — Named Credentials as Callout Endpoints — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_named_credentials.htm
- Metadata API Developer Guide — PlatformEncryptionSettings — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_platformencryptionsettings.htm
- `@NamespaceAccessible` annotation — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_NamespaceAccessible.htm
- Apex Developer Guide — Custom Settings (Protected visibility in managed packages) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_customsettings.htm
- Apex Crypto class reference — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_classes_restful_crypto.htm
- Salesforce Well-Architected — Secure pillar — https://architect.salesforce.com/well-architected/trusted/secure
