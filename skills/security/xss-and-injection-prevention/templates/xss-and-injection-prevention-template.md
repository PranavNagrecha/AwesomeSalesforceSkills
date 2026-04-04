# XSS and Injection Prevention — Security Review Template

Use this template when reviewing Visualforce pages, Apex controllers, or LWC components for XSS and injection vulnerabilities.

## Scope

**Component under review:** (Visualforce page / Apex class / LWC component name)

**User-controlled input paths:**
- (list each input: URL param, form field, Apex REST param, stored field from external system)

## Output Context Audit

For each piece of user-controlled data, record where it is rendered:

| Input Variable | Output Context | Current Encoding | Required Encoding | Fixed? |
|---|---|---|---|---|
| `{variable}` | HTML body / JS block / URL / Header | NONE / HTMLENCODE / JSENCODE | JSENCODE / URLENCODE / etc. | [ ] |

## Dynamic SOQL / SOSL Audit

List all `Database.query(` and `Search.query(` calls that use dynamic strings:

| Method | String Contains User Input? | Uses Bind Variable? | Fixed? |
|---|---|---|---|
| `Database.query(...)` | Yes / No | Yes / No | [ ] |

## PageReference Redirect Audit

List all `new PageReference(url)` where the URL is user-derived:

| Location | URL Source | Allowlist Check Present? | Fixed? |
|---|---|---|---|
| `ClassName.methodName` | URL param / field / apex param | Yes / No | [ ] |

## HTTP Header Audit

List all `RestContext.response.headers.put(...)` or `HttpResponse.setHeader(...)` calls with user-derived values:

| Location | Header Name | Value Source | CRLF Stripped? | Fixed? |
|---|---|---|---|---|

## Code Analyzer Results

Run: `sf scanner run --target force-app/ --format table --engine pmd`

Key rules to check:
- [ ] `ApexXSSFromURLParam` — no findings
- [ ] `ApexXSSFromEscapeFalse` — no findings
- [ ] `ApexSOQLInjection` — no findings
- [ ] `ApexOpenRedirect` — no findings

## Final Sign-Off

- [ ] All output contexts have appropriate encoding
- [ ] No dynamic SOQL/SOSL with string concatenation using user input
- [ ] All PageReference redirects validated against allowlist
- [ ] No user input in HTTP headers without CRLF stripping
- [ ] Code Analyzer passes with no XSS/injection findings
