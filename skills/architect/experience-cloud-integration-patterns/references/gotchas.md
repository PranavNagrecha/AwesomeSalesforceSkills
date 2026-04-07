# Gotchas — Experience Cloud Integration Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: SAML Entity ID Is Site-Specific, Not the Org-Level Entity ID

**What happens:** Admins configure SAML SSO and manually copy the org's entity ID from Setup > Company Information or from a previously configured SAML app. They provide this to the external IdP. When users attempt to SSO, Salesforce rejects the assertion with an "invalid audience" or "entity ID mismatch" error.

**When it occurs:** When the SAML SSO configuration is for an Experience Cloud site (as opposed to the main Salesforce org login). Each Experience Cloud site has its own SAML entity ID derived from the site's domain. The org-level entity ID is different and will not match what Salesforce validates against for site-specific assertions.

**How to avoid:** Always export the SP metadata XML directly from the SAML SSO configuration record in Setup (using the "Download Metadata" button), rather than constructing the entity ID manually. Provide the full metadata XML to the external IdP administrator. The ACS URL and entity ID in the exported metadata are the authoritative values for that site.

---

## Gotcha 2: X-Frame-Options Blocks Cross-Origin iFrame Embedding by Default

**What happens:** A third-party web application or a separate internal portal attempts to embed an Experience Cloud site in an iFrame. The browser renders a blank frame or a security error page. Developer tools show a refused-to-display error citing `X-Frame-Options: SAMEORIGIN`.

**When it occurs:** Salesforce sets the `X-Frame-Options: SAMEORIGIN` response header on all Experience Cloud site pages by default. This header instructs browsers to allow framing only from the same origin. There is no Experience Builder toggle or Setup setting to change this to `ALLOWALL` or to specify trusted third-party origins for cross-origin framing. The restriction applies even for sites set to Public access.

**How to avoid:** Design integrations that require external embedding around redirect flows or widget APIs rather than iFrame embedding. If iFrame embedding from specific trusted origins is a hard business requirement, open a Salesforce Support case — Salesforce can apply a trusted-origin exception for specific domains at the infrastructure level, but this is not self-serve. Document this constraint in the integration design before committing to an iFrame-based architecture.

---

## Gotcha 3: Privileged Script Tag Is Per-LWR-Site, Not Org-Wide

**What happens:** An administrator adds a Privileged Script Tag for a GTM container or analytics library to one LWR site and assumes the configuration applies to all sites in the org. The script fails to load on other sites, and the team cannot identify the cause because no error appears in Experience Builder for the other sites.

**When it occurs:** Privileged Script Tag configuration exists independently per LWR site. The setting lives in Experience Builder > Settings > Security for each individual site. There is no org-level Privileged Script Tag configuration that cascades to all sites. Multi-site organizations commonly discover this when rolling out a new marketing tool across their entire portal estate.

**How to avoid:** When deploying third-party scripts to multiple Experience Cloud sites, configure Privileged Script Tag entries for each site individually. For organizations with many sites, consider scripting deployout via the Salesforce CLI and metadata API (NetworkSiteDetail metadata type) rather than clicking through Experience Builder for each site. Document the per-site nature of the setting in runbooks and change management procedures.

---

## Gotcha 4: Data Cloud Web SDK Connector Is Auto-Created at Org Level But Requires Per-Site Activation

**What happens:** An administrator connects Data Cloud to the Salesforce org via the Data Cloud setup wizard. They assume all Experience Cloud sites are now instrumented for behavioral event capture. No events appear in Data Cloud. Investigation reveals the Web SDK JavaScript is not loading on any site.

**When it occurs:** The Data Cloud connection creates a Web SDK connector at the org level, but this connector must be explicitly enabled for each Experience Cloud site. Site activation is a separate step in the Data Cloud site configuration (Data Cloud > Setup > Experience Cloud Sites). Sites that are not activated in this second step receive no SDK injection and emit no events, even though the org-level connection is active.

**How to avoid:** After completing the org-level Data Cloud connection, navigate to Data Cloud > Setup > Experience Cloud Sites and activate each portal site individually. Verify activation by checking the site's page source for the `dw.js` SDK script tag. Add a verification step for Data Cloud site activation to the project go-live checklist for any Experience Cloud deployment.

---

## Gotcha 5: The Org Can Act as Both SP and IdP Simultaneously — These Are Independent Configurations

**What happens:** An enterprise needs Salesforce to accept SAML assertions from a corporate IdP (Okta) for portal login (SP role) AND issue SAML assertions to a separate downstream system like an order management portal (IdP role). The implementation team believes enabling the Salesforce Identity Provider feature will break or interfere with the inbound SAML SSO configuration, so they avoid it. The downstream system integration is then built with a workaround (separate org or manual credential sync).

**When it occurs:** This misconception is common because the two configurations appear in different Setup areas and are not visually linked. Setup > Identity > SAML Single Sign-On Settings manages the SP role (inbound assertions). Setup > Identity > Identity Provider manages the IdP role (outbound assertions). They are entirely independent.

**How to avoid:** Explicitly document both roles in the integration design. Configure them independently:
- **SP role:** SAML SSO configuration record + site Login & Registration setting
- **IdP role:** Enable Identity Provider in Setup, then create a Connected App for the downstream system

Test each role in isolation first, then verify they operate concurrently without conflict. Include a dual-role test case in the SSO acceptance test plan.
