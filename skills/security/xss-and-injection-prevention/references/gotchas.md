# Gotchas — XSS and Injection Prevention

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Auto-Escaping Does Not Apply Inside Script Blocks

**What happens:** Developers bind `{!field}` through a standard component such as `<apex:outputText>` and see it renders safely — the component escapes it (apexdev 264 L13439-13442). They then use the same syntax inside a `<script>` block — and it does not escape: a formula outside a Visualforce component is unfiltered (L13480-13483). The JavaScript string receives the raw field value, including any single quotes, angle brackets, or script sequences.

**When it occurs:** Any Visualforce page that passes Apex controller data into a JavaScript context using the `{!expression}` syntax inside `<script>` tags.

**How to avoid:** Always use `{!JSENCODE(expression)}` for any Apex expression that appears inside a JavaScript context. For expressions in HTML attributes that call JavaScript (like `onclick="doSomething('{!field}')"`) use `{!JSINHTMLENCODE(field)}`, which applies `HTMLENCODE` first and then `JSENCODE` (apexdev 264 L13510-13512).

---

## Gotcha 2: SOSL Queries Are Also Injectable

**What happens:** Developers focus on SOQL injection prevention but use string concatenation in SOSL queries, leaving a parallel injection surface.

**When it occurs:** Dynamic SOSL built with `Search.query('FIND \'' + userInput + '\' IN ALL FIELDS...')`.

**How to avoid:** Dynamic SOSL runs through `Search.query` / `Search.find`, not `Database.query()`. The guide's defense is "To prevent SOSL injection, use the escapeSingleQuotes method" (apexdev 264 L11763); combine it with validating the input length and character set. UNVERIFIED (2026-10-20): whether dynamic SOSL accepts bind variables in `FIND` is not stated in the corpus. For Search.query (the Apex SOSL API), the literal string after FIND can still be controlled — sanitize before building the query string.

---

## Gotcha 3: Rendered Field Values in Aura Components Bypass Locker Service

UNVERIFIED (2026-10-20): this heading's claim and the body below — script execution through `formattedRichText`, the API v39 enforcement boundary, `$A.util.escapeHtml()` and LWC template auto-escaping — have no corpus line. The corpus holds only the switches: `lockerServiceNext` (Lightning Web Security for LWC, Locker for Aura) and `lockerServiceAPIVersion` (api_meta 264 L129910-129930).

**What happens:** Aura components that render user data via `component.set('v.innerHtml', userValue)` or via `<lightning:formattedRichText value="{!v.data}">` can execute script tags embedded in the data value if Locker Service is not fully enforced for the component's API version.

**When it occurs:** Older Aura components on API versions before Locker Service enforcement (API v39 or older), or components explicitly disabling Locker via org settings.

**How to avoid:** Sanitize HTML content before setting it as innerHTML. Use `$A.util.escapeHtml()` in Aura or avoid rich text rendering of user-controlled data entirely. In LWC, use `{field}` template bindings which are auto-escaped by the framework.

---

## Gotcha 4: CRLF Injection in HTTP Headers

**What happens:** When Apex code adds user-supplied values to `RestContext.response.headers` (a `Map<String, String>`, apexref 262 L228743-228747) or calls `addHeader(name, value)` (L228840-228845) without stripping carriage-return/line-feed characters, an attacker can inject additional HTTP headers or split the response body. UNVERIFIED (2026-10-20): whether the platform itself rejects CR/LF in header values is not in the corpus; it documents only that `cookie`, `set-cookie` and similar names throw (apexref 262 L228866-228873).

**When it occurs:** Any code path where user-supplied strings are placed into HTTP response headers, such as setting a custom `Location` header based on a URL parameter.

**How to avoid:** Reject or strip `\r` and `\n` from any string before placing it into an HTTP header. A simple check: `if (headerValue.contains('\r') || headerValue.contains('\n')) { throw new ... }`.

---

## Gotcha 5: `escape="false"` turns a safe tag into a raw sink

**What happens:** `<apex:outputText escape="false" value="{!$CurrentPage.parameters.userInput}" />` renders script from the URL; the guide calls this output "vulnerable to XSS attacks" (apexdev 264 L13449-13452).

**When it occurs:** Any tag where a developer disabled escaping to render formatting HTML, usually alongside a rerender that echoes user input (L13487-13499).

**How to avoid:** Keep the default escaping, or wrap the value: `<apex:outputText value=" {!HTMLENCODE(myTextField)}" escape="false"/>` (L13518). The checker flags `escape="false"` tags whose value is not wrapped in an encoding function.
