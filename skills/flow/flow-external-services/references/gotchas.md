# Gotchas — Flow External Services

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Record-Triggered Flows Cannot Make Synchronous Callouts

**What happens:** A record-triggered flow (before-save or after-save) that contains an External Service action or HTTP Callout action throws `System.CalloutException: You have uncommitted work pending` at runtime. The flow terminates and the record save may roll back depending on the flow type.

**When it occurs:** Any time a callout action is placed directly inside the main interview of a record-triggered flow, including callouts in subflows called from a record-triggered flow. The restriction applies regardless of whether the callout itself would succeed.

**How to avoid:** Never place callout actions directly in record-triggered flow interviews. Use one of these async dispatch patterns instead:
- Publish a Platform Event from the record-triggered flow, then subscribe with an autolaunched flow that contains the callout.
- Use a scheduled path on a record-triggered flow (runs asynchronously outside the save transaction).
- Call an `@future` or Queueable Apex method from the record-triggered flow to perform the HTTP request.

---

## Gotcha 2: HTTP Callout Action Does Not Fault on 4xx/5xx HTTP Responses

**What happens:** The built-in HTTP Callout core action returns `Response_Status_Code` as a Number variable regardless of the HTTP response. A `400 Bad Request`, `401 Unauthorized`, or `500 Internal Server Error` from the server results in a successful action execution (no fault). The fault connector only activates on network-level failures (connection timeout, DNS failure, SSL error).

**When it occurs:** Every time an HTTP Callout action is used and the external server returns a non-2xx status. If the developer only wires the fault connector and does not check the status code variable, a failed API call appears to succeed to the flow, and downstream logic (e.g., updating records based on the response) proceeds with bad data.

**How to avoid:** After every HTTP Callout action, add a **Decision** element that checks `{!varStatusCode} >= 400`. Route the `True` outcome to the same error handling path as the fault connector. This ensures both network failures and server-side errors are handled correctly.

---

## Gotcha 3: External Services Spec Validation Silently Drops Unsupported Schema Features

**What happens:** When importing an OpenAPI spec that contains `oneOf`, `anyOf`, `allOf`, recursive `$ref` references, or complex `enum` arrays on request body properties, Salesforce may import the spec successfully (showing no hard error) but silently omit the affected parameters from the generated action signature. At runtime, those fields are simply not available as inputs or outputs in Flow Builder.

**When it occurs:** Especially common with OpenAPI 3.0 specs from modern REST APIs that use discriminator patterns or polymorphic schemas. Also triggered by specs that use `$ref` within `$ref` chains beyond one level of nesting.

**How to avoid:** After registering a spec, immediately open the generated action in Flow Builder and verify every expected input and output field appears. If fields are missing, simplify the spec section that defines them — flatten the schema, remove composition keywords, and re-import. Always test spec imports in a sandbox before building flows that depend on the generated actions.

---

## Gotcha 4: External Credential Permission Set Assignment Is Required at Runtime, Not Just at Setup

**What happens:** The HTTP callout fails with a generic authentication error (`Unauthorized` or `forbidden`) even though the Named Credential is correctly configured and the External Service registration completed without errors. The error message does not mention Permission Sets.

**When it occurs:** The running user (or the automated context, such as a scheduled flow) does not have the Permission Set that is assigned to the External Credential principal. This is checked at callout runtime, not at flow activation. Flows that are tested by an admin (who has the Permission Set) pass fine, then fail for regular users in production.

**How to avoid:** After configuring the External Credential principal, explicitly assign the correct Permission Set(s) to the principal. For automated flows (scheduled, platform-event-triggered), ensure the running user or the automation user context has the Permission Set. Test with a non-admin user before releasing.

---

## Gotcha 5: Named Credential URL Trailing Slash Produces Double-Slash in Path

**What happens:** The concatenated request URL contains `//` (double slash) in the resource path, causing the external server to return `404 Not Found` or route the request incorrectly. For example, `https://api.example.com/` + `/v1/orders` becomes `https://api.example.com//v1/orders`.

**When it occurs:** When the Named Credential's URL field ends with `/` and the HTTP Callout action's Path field (or the spec's path definition) begins with `/`. This is extremely common because it is intuitive to end a base URL with a slash.

**How to avoid:** Always configure the Named Credential URL without a trailing slash (e.g., `https://api.example.com`). Paths in HTTP Callout actions and OpenAPI specs should begin with `/`. This is a Salesforce platform-wide convention, not specific to Flow.

---

## Gotcha 6: Collection Output Variables From External Services Actions Must Be Initialized

**What happens:** If an External Service action returns an array (list) and the output is mapped to a collection variable, and that collection variable has never been initialized in the flow, the loop element that iterates over it either throws an error or silently processes zero items when the response contains data.

**When it occurs:** When flow variables used to receive list outputs from External Service actions are declared but not assigned a default empty collection before the action runs. This is most common in flows built incrementally where variables are added later.

**How to avoid:** Before the External Service action, add an Assignment element that sets the collection variable to an empty collection (or simply declare it — Flow initializes text and primitive collection variables as empty by default). After the action, verify the collection variable is non-null and non-empty in a Decision element before entering the loop.
