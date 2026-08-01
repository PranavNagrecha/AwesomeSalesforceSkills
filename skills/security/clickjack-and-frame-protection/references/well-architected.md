# Well-Architected Notes — Clickjack and Frame Protection

## Relevant Pillars

| Pillar | How this skill contributes |
|---|---|
| **Security** | Framing policy is the control that stops UI-redress attacks, where the user's own authenticated session is used against them. It costs nothing at runtime and is the cheapest security control in the platform to keep switched on. |
| **Reliability** | The realistic failure is not an attack — it is a partner embed going blank after a domain change or a Setup edit, with no server-side error anywhere. Retest coverage is what makes this reliable, not the setting itself. |
| **Operational Excellence** | Every trusted-domain entry is a standing grant over a whole class of pages. Without an owned, dated register the list only ever grows, and the 512 / 100 / 12 KB ceilings arrive without warning. |

## Architectural Tradeoffs

- **Allow-list versus proxy origin.** Enumerating partner origins is the correct answer at small scale and the wrong answer at large scale: it consumes the documented domain limits, inflates the CSP header toward the 12 KB ceiling, and makes revocation a per-partner task. Past a few dozen origins, one branded proxy origin that fans out on the partner side is the cheaper design, at the cost of a component you now own.
- **Org-wide checkbox versus per-origin entry.** Disabling a Session Settings option is a one-click fix that removes protection from every page of that class. The allow-list is slower, needs an approval, and is scoped. Prefer the slow one; the fast one has no blast-radius limit.
- **Same-origin default versus external-domain allow-list for Experience Cloud.** *Allow framing by the same origin only* is the documented default and needs no maintenance. Moving to *Allow framing of site pages on external domains* unblocks a partner and creates a register somebody must review forever. Make that a deliberate, owned decision.
- **Modern-browser policy versus legacy-browser reality.** A multi-origin allow-list is only expressible in CSP `frame-ancestors`. Browsers that support the legacy `X-Frame-Options` header only cannot receive it, so supporting them means accepting single-origin behaviour rather than pretending the allow-list applies everywhere.
- **Deleting legacy Visualforce versus allow-listing around it.** Removing unused pages is unglamorous and permanently shrinks the framable surface. Leaving them and scoping the allow-list narrowly does not help, because the entry grants framing over the whole class of pages.

## Anti-Patterns

1. Writing `X-Frame-Options` or `Content-Security-Policy` from Apex, Visualforce, or an LWC — the platform emits these headers for its own pages.
2. Selecting *Allow framing by any page* to make a symptom disappear; it is the documented no-protection level.
3. Enabling one of the two Visualforce clickjack options and treating the surface as covered.
4. Diagnosing a Canvas app failure as a Salesforce clickjack problem — Canvas puts the vendor's app in the child frame, not Salesforce.
5. Accepting an Experience Builder preview or a direct page load as evidence that cross-origin framing works.
6. Growing the trusted-domain register without an owner, a review date, or a check against the documented limits.
7. Omitting the cross-origin framing retest from a My Domain or Enhanced Domains change runbook.

## Official Sources Used

- Salesforce Security Guide — Modify Session Security Settings — https://help.salesforce.com/s/articleView?id=xcloud.admin_sessions.htm — used for the four clickjack option labels and their verbatim descriptions, and the Setup path.
- Salesforce Help — Configure Clickjack Protection — https://help.salesforce.com/s/articleView?id=xcloud.security_clickjack_protection_configure.htm — used as the parent topic covering Visualforce pages, trusted domains, and less common browsers.
- Salesforce Help — Specify Trusted Domains for Inline Frames — https://help.salesforce.com/s/articleView?id=xcloud.security_clickjack_specify_iframe_trusted_domains.htm — used for the trusted-domain list, the iframe-type selection, the 512 / 100 domain limits, and the 12 KB CSP header guidance.
- Salesforce Help — Enable Clickjack Protection in Experience Cloud Sites — https://help.salesforce.com/s/articleView?id=experience.networks_clickjack_protection.htm — used for the four Clickjack Protection Levels, the same-origin default, the Experience Builder path, and the rule that mixed Experience Builder / Salesforce Tabs + Visualforce sites need both locations configured.
- Visualforce Developer Guide — Put Visualforce Pages on External Domains — https://developer.salesforce.com/docs/atlas.en-us.pages.meta/pages/pages_quick_start_external_iframe.htm — used for the end-to-end external-framing procedure: enable both Visualforce options, then add the trusted domain with iframe type Visualforce Pages.
- Salesforce Platform Developer Guide — Canvas framework introduction — https://developer.salesforce.com/docs/atlas.en-us.platform_connect.meta/platform_connect/canvas_framework_intro.htm — used to establish the framing direction: Canvas apps are loaded on a Salesforce page in an iframe, so Salesforce is the parent.
- Salesforce Help — Enable Clickjack Protection in Site.com — https://help.salesforce.com/s/articleView?id=platform.siteforce_clickjacking_enable.htm — used to confirm that Salesforce Sites are configured separately again from both surfaces above.
- W3C Content Security Policy Level 2 — `frame-ancestors` directive — https://www.w3.org/TR/CSP2/#directive-frame-ancestors — used for the standards-level rule that `frame-ancestors` is honoured only in an HTTP header and not in a `<meta http-equiv>` element.
