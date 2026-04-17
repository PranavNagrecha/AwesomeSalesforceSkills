# Integration Catalog Builder — Gated Execution Protocol

Five-gate protocol enforced by `scripts/run_builder.py` via `scripts/builder_plugins/integration_catalog.py`.

---

## Gate A — Input readiness

`catalog_name`, `org_alias`, `feature_summary` (≥10 words), and `api_version` are required.

## Gate A.5 — Requirements document

Renders `REQUIREMENTS_TEMPLATE.md` with the target org alias + any Named Credentials referenced.

## Gate B — Ground every symbol

Every Named Credential passed in `named_credentials[]` is a grounding symbol for the REQUIREMENTS doc. Gate B does not hit the org yet — that's Gate C's live oracle.

## Gate C — Build and self-test

**Static check:**
- JSON parses; top-level object with `catalog_version` (`N.M`), `org_alias`, `integrations[]` (non-empty).
- Every integration has `{name, direction ∈ {inbound,outbound,bidirectional}, pattern ∈ {REST, SOAP, Bulk, Streaming, PlatformEvent, CDC, PubSub, SalesforceConnect, MuleSoft, File}, auth ∈ {NamedCredential, OAuth2-ClientCred, OAuth2-AuthCode, OAuth2-JWT, BasicAuth, ApiKey, mTLS, SessionId, None}, owner}`.
- Every integration has `endpoint` OR `callout`.

**Live check:**
- Each `named_credential` referenced by an integration is validated by `sf org list metadata --metadata-type NamedCredential --target-org <alias>`. Any missing NC is a component failure.

Confidence: HIGH iff static green + live green; MEDIUM iff static green + live skipped; LOW otherwise.

## Gate D — Envelope seal

Envelope validates against the shared schema; deliverable kind is `json`.

---

## What this protocol is NOT

- Not a contract tester. The catalog documents integrations; verifying the integrations themselves is `/catalog-integrations` runtime work.
- Not a secrets store. Credentials live in NamedCredential metadata; the catalog references them by name only.
