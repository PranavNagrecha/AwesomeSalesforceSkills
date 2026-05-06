# Well-Architected Notes — Tableau Embedding in Lightning

## Relevant Pillars

- **Security** — RLS is enforced on the Tableau side; the embedding
  pattern is only as secure as the JWT signing key and the identity
  claim. Misconfiguration silently exposes data.
- **Performance** — Embedded vizes add page-load weight (Tableau
  SDK + viz rendering). Each embed adds 1+ seconds to initial
  render; multiple embeds on a single page can become a UX problem.

## Architectural Tradeoffs

- **Tableau Viz LWC vs custom LWC.** Drag-and-drop is simpler;
  custom is required for record-context filters and event handling.
- **JWT vs SAML SSO.** JWT is per-request and supports fine-grained
  identity claims; SAML is org-level and simpler if already in
  place. Most embedded use cases prefer JWT for control over the
  identity claim.
- **Tableau vs CRM Analytics.** Different products. Tableau is more
  flexible analytically and ubiquitous outside Salesforce; CRM
  Analytics integrates more tightly with Salesforce data. Pick by
  the existing analytics investment.

## Anti-Patterns

1. **Anonymous embed of non-public data.**
2. **RLS expressed as a JavaScript filter** rather than as a data-
   source filter using `USERNAME()`.
3. **Long-lived JWTs** (24 hours).
4. **Hardcoded Tableau host URL** in LWC source.
5. **Connected App secret in Apex source.**
6. **Missing CSP Trusted Sites** producing silent empty render.

## Official Sources Used

- Tableau Embedding API v3 — https://help.tableau.com/current/api/embedding_api/en-us/index.html
- Tableau Pulse Embedding — https://help.tableau.com/current/online/en-us/pulse_embed.htm
- Connected Apps with JWT — https://help.tableau.com/current/online/en-us/connected_apps_direct.htm
- CSP Trusted Sites for Lightning Components — https://help.salesforce.com/s/articleView?id=sf.csp_trusted_sites.htm&type=5
- Tableau Viz Lightning Web Component (AppExchange / Setup) — https://help.salesforce.com/s/articleView?id=sf.tableau_viz.htm&type=5
- Salesforce Well-Architected Trustworthy — https://architect.salesforce.com/well-architected/trusted/secure
