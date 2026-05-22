# Gotchas — Apex WSDL-to-Apex Patterns

Non-obvious Salesforce platform behaviors that cause real production problems when generating outbound SOAP stubs from a WSDL.

## Gotcha 1: `xsd:choice` and `xsd:any` reject the entire WSDL

**What happens:** Setup > Apex Classes > Generate from WSDL fails with `Failed to parse wsdl: schema does not support 'choice'` (or `'any'`). No partial class is produced; the entire WSDL is rejected on the first unsupported construct found.

**When it occurs:** The vendor's WSDL contains an XSD union (`xsd:choice`), an "anything goes" element (`xsd:any`), or extensible wildcard attributes (`xsd:anyAttribute`). These are common in legacy Microsoft WCF WSDLs and any service that exposes an extensible payload.

**How to avoid:** Pre-process the WSDL on disk. Convert `xsd:choice` to `xsd:sequence` with each branch marked `minOccurs="0"` (semantics loosen — both branches become legal — but downstream Apex can validate). Replace `xsd:any` with a typed wildcard element (`xsd:string` for a fall-through). Persist the cleaned WSDL to source control with a `WSDL_README.md` documenting which edits were applied so the next regen starts from the cleaned WSDL.

---

## Gotcha 2: 1 MB WSDL limit AND 1 MB generated-class limit are independent

**What happens:** A WSDL under 1 MB parses successfully but the generated Apex class exceeds the 1 MB Apex class size limit. Save fails with `Apex class is too large`. The metadata API deploy of the generated class fails identically.

**When it occurs:** The WSDL declares many complex types with deep nesting (each becomes a static inner class with its own serializer), or declares many operations (each becomes a method with full element parameter classes). A 600 KB WSDL with 50 complex types can balloon to 1.4 MB of Apex.

**How to avoid:** Trim the WSDL to only the operations and types actually consumed. Delete unused `<wsdl:operation>` and `<wsdl:binding>` blocks; walk `<xsd:complexType>` definitions and remove any type only referenced by deleted operations. Iterate until both the WSDL and the generated class are under 1 MB. Preserve the vendor's full WSDL as `*-vendor-FULL.wsdl` for auditability.

---

## Gotcha 3: `endpoint_x` defaults to the WSDL's `<soap:address location>`

**What happens:** The first call from a new wrapper service silently goes to whatever URL the vendor baked into the WSDL — typically a sandbox or developer URL like `https://stage.api.example.com/Service.svc`. The vendor's stage environment processes the request, the call returns success, and the production system never sees the transaction.

**When it occurs:** Anyone who instantiates a generated stub without explicitly setting `endpoint_x`. Developer-tier defaults persist into production deploys.

**How to avoid:** **Always** set `endpoint_x = 'callout:<Named_Credential>'` before invoking any operation method. Code review the wrapper class for this line. Static analysis is feasible — every `new XxxxPort.Yyyy()` should be followed by an assignment to `endpoint_x` referencing `callout:`.

---

## Gotcha 4: SOAP faults raise `WebServiceCalloutException`, not `CalloutException`

**What happens:** A `try / catch (CalloutException e)` block does not catch a SOAP fault. The fault propagates up as `System.WebServiceCalloutException: SOAP Server: ...` and the calling transaction rolls back if not handled elsewhere.

**When it occurs:** Vendor returns HTTP 500 with a SOAP `<faultcode>` / `<faultstring>` body. Every production SOAP service eventually does this for input validation errors, business-rule rejections, or auth failures.

**How to avoid:** Use a two-catch ladder, fault first: `catch (System.WebServiceCalloutException fault)` then `catch (System.CalloutException net)`. The order matters — `WebServiceCalloutException` is a subclass of `CalloutException`, so a broader catch first swallows the fault metadata.

---

## Gotcha 5: `HttpCalloutMock` does NOT intercept wsdl2apex callouts

**What happens:** Test class registers `Test.setMock(HttpCalloutMock.class, mock)` and the test still fails at runtime with `Methods defined as TestMethod do not support Web service callouts`. The compiler does not warn; the failure surfaces only on execution.

**When it occurs:** A developer familiar with REST `Http.send()` testing patterns assumes the same mock applies to SOAP callouts. It does not — wsdl2apex stubs use a separate runtime callout path.

**How to avoid:** Use `Test.setMock(WebServiceMock.class, mock)` for any code path that invokes a generated SOAP stub. The mock implements `WebServiceMock.doInvoke()` and populates the response via the literal key `response.put('response_x', element)`. Mixed REST + SOAP tests need both mocks registered separately.

---

## Gotcha 6: Reserved-word collisions get silently `_x`-suffixed

**What happens:** A WSDL element named `type`, `class`, `return`, or `new` becomes a property named `type_x` (etc.) on the generated class. The vendor documentation references `type`; the developer searches for `type` in the Apex stub and finds nothing.

**When it occurs:** WSDLs from vendors that aren't aware of Apex reserved-word collisions — common for non-Salesforce-targeted SOAP services.

**How to avoid:** Maintain a glossary in the wrapper class header that maps vendor element names to generated Apex names for any `_x`-suffixed members. The Apex stub source is searchable for `_x` — running `grep '_x' <Stub>.cls` lists every collision and every HTTP control property in one pass.

---

## Gotcha 7: `timeout_x` default of 10 seconds is too short for most SOAP services

**What happens:** Calls intermittently fail with `System.CalloutException: Read timed out` even when the vendor's API is healthy. Latency spikes from 8 to 12 seconds (within SLA) blow past the default.

**When it occurs:** Wrapper service is written without an explicit `timeout_x` assignment. Many SOAP services routinely respond in 15–30 seconds because the SOAP envelope itself is heavier than REST + JSON.

**How to avoid:** Set `timeout_x` explicitly in every wrapper. A reasonable default is 60000 (60 s); the maximum is 120000 (120 s) — the synchronous transaction governor cap. Budget the timeout against the vendor's p99 latency plus headroom.

---

## Gotcha 8: `inputHttpHeaders_x` Authorization header is silently stripped when endpoint is a Named Credential

**What happens:** A wrapper sets both `endpoint_x = 'callout:My_NC'` and `inputHttpHeaders_x = {'Authorization' => 'Bearer ...'}`. The Named Credential's auth wins; the developer-provided Authorization header is dropped. Authentication appears to work using the wrong credentials, which can manifest as cross-tenant data leakage in multi-tenant vendor APIs.

**When it occurs:** Code copied from a non-NC integration that authenticated by setting the Authorization header inline, then partially refactored to use a Named Credential.

**How to avoid:** Auth headers belong to the Named Credential / External Credential — never in `inputHttpHeaders_x`. Reserve `inputHttpHeaders_x` for non-auth headers (`SOAPAction`, `X-Idempotency-Key`, `X-Trace-Id`). If the vendor requires a custom auth header that the NC cannot produce, escalate to using an Apex-managed token alongside a "No Auth" External Credential.

---

## Gotcha 9: `<wsdl:import>` of external schemas is silently dropped

**What happens:** A WSDL declares `<wsdl:import location="external.xsd"/>` referring to a schema file alongside it. Generate from WSDL completes but the imported types are missing from the generated Apex — operations referencing those types fail to compile.

**When it occurs:** Multi-file WSDL bundles where the vendor ships `Service.wsdl` plus a separate `Types.xsd`. The platform does not fetch imported files.

**How to avoid:** Inline the imported schema into the main WSDL before uploading. Copy the `<xsd:schema>` body from the imported file into the WSDL's own `<wsdl:types>` block; delete the `<wsdl:import>` directive; reconcile any duplicate target namespaces.

---

## Gotcha 10: Stub regeneration after manual WSDL edits silently rebuilds from the original

**What happens:** A developer pre-processes the WSDL once (removes `xsd:choice`, inlines imports), generates the stub, and ships. Six months later, a different developer regenerates the stub from the vendor's original WSDL because the cleaned WSDL is not in source control. The regen fails because the original still has `xsd:choice`; the developer hand-edits the Apex to make it compile; tests pass against the now-divergent stub; production hits the divergence.

**When it occurs:** Cleaned WSDLs aren't committed alongside the generated stub, and there's no runbook describing the pre-processing steps.

**How to avoid:** Commit the cleaned WSDL as `<service>.wsdl` and the vendor's original as `<service>-vendor-FULL.wsdl`. Include a `WSDL_README.md` listing every edit applied (`xsd:choice → xsd:sequence` on line 412, schema inlining on lines 50–95, etc.) so the next regen is deterministic.

---

## Gotcha 11: SOAP 1.2 bindings are not supported

**What happens:** Generate from WSDL fails with `Found more than one soap:binding` or silently selects the first binding (which may be SOAP 1.1 in a dual-binding WSDL). Single-binding SOAP 1.2 WSDLs fail to parse with `Unsupported SOAP version`.

**When it occurs:** Modern services that ship SOAP 1.2 by default (`http://schemas.xmlsoap.org/wsdl/soap12/`).

**How to avoid:** Ask the vendor for a SOAP 1.1 binding (almost all vendors maintain both for backward compat). If only 1.2 is available, abandon wsdl2apex and hand-author the SOAP envelope using `Http.send()` plus XML serialization — the WSDL becomes documentation only.

---

## Gotcha 12: `Database.Stateful` + Queueable wrapping a SOAP callout serializes the stub

**What happens:** A Queueable that holds a stub instance as a member variable fails to enqueue with `System.SerializationException: Not serializable: MyServicePort.Soap`. The stub class is not `Serializable` (generated stubs are stateful and reference platform resources).

**When it occurs:** A wrapper service is captured as a Queueable member variable instead of being instantiated inside `execute()`.

**How to avoid:** Instantiate the stub inside the Queueable's `execute()` method, not in its constructor or as a member field. Pass only primitive / serializable payload data through the Queueable's state.
