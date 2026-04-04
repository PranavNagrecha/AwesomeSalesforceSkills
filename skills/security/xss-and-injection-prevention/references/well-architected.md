# Well-Architected Notes — XSS and Injection Prevention

## Relevant Pillars

- **Security** — XSS and injection vulnerabilities are direct security failures. Stored XSS can result in account takeover, data exfiltration, and credential theft at scale. SOQL injection can bypass all sharing model protections and expose records the user should never see. These are among the most severe vulnerability classes in the Salesforce platform.
- **Reliability** — An application that is vulnerable to injection is unreliable: the behavior of any query or page can be modified by external input. Encoding and bind variables make the application's behavior deterministic regardless of input content.
- **Operational Excellence** — Encoding requirements and bind-variable patterns should be enforced by code review checklists and automated scanning (Salesforce Code Analyzer / PMD). Relying on manual review alone is operationally fragile.

## Architectural Tradeoffs

**Defense in depth vs. single layer:** Platform auto-escaping handles HTML body contexts. Relying only on auto-escaping misses JavaScript contexts, URL contexts, and attribute contexts. Explicit encoding in every output context is the defense-in-depth approach and provides redundancy.

**Dynamic SOQL vs. Static SOQL:** Static SOQL is always injection-safe and should be preferred. Dynamic SOQL with bind variables is safe for filter values. Dynamic field names, object names, and clauses (ORDER BY, LIMIT) cannot use bind variables — these must be validated against a whitelist before inclusion.

## Anti-Patterns

1. **Using `{!field}` in JavaScript contexts without JSENCODE** — The auto-escape does not apply. This is the most common XSS pattern in Salesforce development.
2. **Using `String.escapeSingleQuotes()` as the sole SOQL injection defense** — Insufficient. Bind variables are the correct primary defense.
3. **Assuming LWC Lightning Web Security prevents all XSS** — LWS sandboxes cross-component DOM access but does not prevent XSS via `innerHTML` or Apex-returned HTML strings.

## Official Sources Used

- Salesforce Secure Coding Guide — Cross-Site Scripting — https://developer.salesforce.com/docs/atlas.en-us.secure_coding_guide.meta/secure_coding_guide/secure_coding_cross_site_scripting.htm
- Apex Developer Guide — Security Tips for Apex and Visualforce — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/pages_security_tips_xss.htm
- Visualforce Developer Guide — Security Tips — https://developer.salesforce.com/docs/atlas.en-us.pages.meta/pages/pages_security_tips_xss.htm
- Salesforce Security Implementation Guide — https://help.salesforce.com/s/articleView?id=sf.security_overview_applications.htm
