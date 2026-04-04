# Gotchas — XSS and Injection Prevention

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Auto-Escaping Does Not Apply Inside Script Blocks

**What happens:** Developers add `{!field}` to a Visualforce page in an HTML body context and see it renders safely. They then use the same syntax inside a `<script>` block — and it does not escape. The JavaScript string receives the raw field value, including any single quotes, angle brackets, or script sequences.

**When it occurs:** Any Visualforce page that passes Apex controller data into a JavaScript context using the `{!expression}` syntax inside `<script>` tags.

**How to avoid:** Always use `{!JSENCODE(expression)}` for any Apex expression that appears inside a JavaScript context. For expressions in HTML attributes that call JavaScript (like `onclick="doSomething('{!field}')"`) use `{!JSINHTMLENCODE(field)}` which applies both JavaScript encoding and HTML attribute encoding.

---

## Gotcha 2: SOSL Queries Are Also Injectable

**What happens:** Developers focus on SOQL injection prevention but use string concatenation in SOSL queries, leaving a parallel injection surface.

**When it occurs:** Dynamic SOSL built with `Search.query('FIND \'' + userInput + '\' IN ALL FIELDS...')`.

**How to avoid:** SOSL does not support bind variables in the `FIND` clause directly via `Database.query()`. The safe approach is to use `String.escapeSingleQuotes()` on the search term combined with validating the input length and character set. For Search.query (the Apex SOSL API), the literal string after FIND can still be controlled — sanitize before building the query string.

---

## Gotcha 3: Rendered Field Values in Aura Components Bypass Locker Service

**What happens:** Aura components that render user data via `component.set('v.innerHtml', userValue)` or via `<lightning:formattedRichText value="{!v.data}">` can execute script tags embedded in the data value if Locker Service is not fully enforced for the component's API version.

**When it occurs:** Older Aura components on API versions before Locker Service enforcement (API v39 or older), or components explicitly disabling Locker via org settings.

**How to avoid:** Sanitize HTML content before setting it as innerHTML. Use `$A.util.escapeHtml()` in Aura or avoid rich text rendering of user-controlled data entirely. In LWC, use `{field}` template bindings which are auto-escaped by the framework.

---

## Gotcha 4: CRLF Injection in HTTP Headers

**What happens:** When Apex code adds user-supplied values to `RestContext.response.headers` or to a `HttpResponse` object without stripping carriage-return/line-feed characters, an attacker can inject additional HTTP headers or split the response body.

**When it occurs:** Any code path where user-supplied strings are placed into HTTP response headers, such as setting a custom `Location` header based on a URL parameter.

**How to avoid:** Reject or strip `\r` and `\n` from any string before placing it into an HTTP header. A simple check: `if (headerValue.contains('\r') || headerValue.contains('\n')) { throw new ... }`.
