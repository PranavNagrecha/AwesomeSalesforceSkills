# Well-Architected Notes — reCAPTCHA and Bot Prevention

## Relevant Pillars

- **Security** -- reCAPTCHA is a direct security control that prevents unauthorized automated access to public-facing data-creation surfaces. Without it, unauthenticated endpoints are open to bot abuse, data poisoning, and resource exhaustion. Server-side verification ensures the control cannot be bypassed by disabling client-side JavaScript.
- **Reliability** -- Bot-generated spam degrades org data quality and can exhaust governor limits (e.g., daily email sends triggered by Case auto-response rules, workflow rule evaluations on mass Lead creation). reCAPTCHA prevents reliability-impacting volume spikes from automated sources.
- **Operational Excellence** -- Layered bot prevention reduces manual triage work. Without reCAPTCHA, support teams waste hours deleting spam cases and leads. Monitoring reCAPTCHA scores and token failure rates provides an early-warning signal for emerging attack patterns.

## Architectural Tradeoffs

1. **Built-in toggle vs. custom implementation** -- the built-in Web-to-Case/Lead toggle is zero-effort but only works for standard generated HTML forms. Any customization (LWC forms, Experience Cloud, APIs) requires the custom Apex verification pattern, which adds maintenance surface but provides score-based control and logging.

2. **reCAPTCHA v2 vs. v3** -- v2 (checkbox or invisible) provides a hard challenge that blocks bots but adds friction for users. v3 (score-based) is invisible to users but requires tuning the score threshold and does not stop sophisticated bots that score above the threshold. The right choice depends on the UX tolerance and threat model of the specific surface.

3. **Single-layer vs. defense-in-depth** -- reCAPTCHA alone stops commodity bots but not targeted attacks. Adding honeypot fields, rate limiting, and email validation increases implementation complexity but is necessary for high-value surfaces (financial forms, registration flows).

## Anti-Patterns

1. **Client-side-only verification** -- checking the reCAPTCHA response only in JavaScript without server-side verification. An attacker can bypass the client entirely by posting directly to the Apex endpoint. Server-side verification via the Google API is mandatory.

2. **Shared keys across environments** -- using the same reCAPTCHA site key and secret in production and all sandboxes. This pollutes analytics, risks deploying test keys to production, and makes key rotation a cross-environment coordination problem.

3. **Set-and-forget score threshold** -- deploying reCAPTCHA v3 with a default threshold and never revisiting it. Bot behavior and user traffic patterns change over time. Without periodic review of score distributions, the threshold drifts out of alignment with actual traffic.

## Official Sources Used

- Salesforce Help: Web-to-Case reCAPTCHA Setup -- configuring the built-in reCAPTCHA toggle for standard web forms
  https://help.salesforce.com/s/articleView?id=sf.setting_up_web-to-case.htm&type=5
- Salesforce Help: Web-to-Lead Setup -- reCAPTCHA requirement for standard lead capture forms
  https://help.salesforce.com/s/articleView?id=sf.setting_up_web-to-lead.htm&type=5
- Salesforce Developer Docs: Headless Identity reCAPTCHA -- v3 requirement for Headless Identity registration and login APIs
  https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/headless_identity_recaptcha.htm
- Salesforce Help: CSP Trusted Sites -- configuring Content Security Policy for third-party scripts in Experience Cloud
  https://help.salesforce.com/s/articleView?id=sf.csp_trusted_sites.htm&type=5
- Salesforce Well-Architected Overview -- architecture quality framing for security and reliability pillars
  https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Security Guide -- org-level security controls and defense-in-depth framing
  https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5
