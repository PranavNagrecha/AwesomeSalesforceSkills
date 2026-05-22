# Apex WSDL-to-Apex Patterns — Work Template

Use this template when consuming a third-party SOAP service from Apex via the Setup > Apex Classes > Generate from WSDL tool.

## Scope

**Skill:** `apex-wsdl2apex-patterns`

**Request summary:** (fill in what the user asked for — e.g., "Integrate the Acme Tax SOAP API to compute tax at order commit time")

## Context Gathered

- **Vendor WSDL file location:**
- **WSDL size (bytes):**  (must be < 1 MB for parser)
- **SOAP version in WSDL bindings:**  (only 1.1 supported)
- **Unsupported XSD constructs found** (`xsd:choice`, `xsd:any`, mixed content, external imports, recursive types):
- **Operations consumed by this integration** (only these; trim the rest):
- **Auth model exposed by vendor** (Basic / OAuth / mTLS / SOAP header token):
- **Named Credential planned to wrap the endpoint:**
- **Calling Apex layer** (synchronous controller / Queueable / Batch / @future):
- **p99 vendor latency observed in vendor docs:**  (drives `timeout_x`)
- **Retry / idempotency requirement:**

## Approach

Which pattern from SKILL.md applies?

- [ ] Pattern 1 — Generate, wrap with Named Credential, dispatch from Queueable
- [ ] Pattern 2 — WSDL with custom SOAP header (auth in envelope)
- [ ] Pattern 3 — Mocking outbound SOAP for tests (always required)

**Decision-tree branch consulted:** (link to `standards/decision-trees/integration-pattern-selection.md` if applicable)

## WSDL Pre-Processing Log

Record every edit applied to the vendor WSDL on disk. This file is the input to the next regen.

| Vendor WSDL line(s) | Edit applied | Reason |
|---|---|---|
| | | |

## Checklist

- [ ] WSDL is under 1 MB and uses SOAP 1.1 only
- [ ] No `xsd:choice`, `xsd:any`, or external imports remain
- [ ] Generated stub class is under 1 MB compiled (Save succeeds)
- [ ] Cleaned WSDL is committed to source control alongside the vendor's original
- [ ] `WSDL_README.md` documents every pre-processing edit
- [ ] Named Credential `<Service>_NC` is created with the correct URL and auth
- [ ] Wrapper service class sets `endpoint_x = 'callout:<NC>'` (NEVER a literal URL)
- [ ] Wrapper sets `timeout_x` explicitly (default 10s is rarely correct)
- [ ] Auth headers are NOT set in `inputHttpHeaders_x` when endpoint is a callout NC
- [ ] Two-catch ladder in place: `WebServiceCalloutException` first, then `CalloutException`
- [ ] WebServiceMock test class covers happy path, SOAP fault, and timeout
- [ ] Async surface (Queueable / Batch) chosen if the calling transaction does DML
- [ ] No hand-edits in the generated stub (verify with `grep` for `@TestVisible`, `@AuraEnabled`, `// CUSTOM`)
- [ ] Checker script run against `force-app/`: 0 issues

## Notes

Record any deviations from the standard pattern and why:
