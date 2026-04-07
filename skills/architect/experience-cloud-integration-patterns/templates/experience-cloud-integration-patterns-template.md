# Experience Cloud Integration Patterns — Decision Template

Use this template when designing or reviewing integrations between an Experience Cloud site and external systems. Fill in each section before beginning implementation.

---

## Scope

**Project / site name:** (name of the Experience Cloud site)

**Site template:** (LWR / Aura / Visualforce-based)

**Request summary:** (what external systems need to connect to this site, and why)

---

## Site Inventory

| Site Name | Template | Domain | Guest Access? | Auth Methods |
|---|---|---|---|---|
| | | | | |

---

## External System Classification

For each external system involved, classify its integration type:

| External System | Type | Protocol | Direction |
|---|---|---|---|
| (e.g., Okta) | SSO / Identity Provider | SAML 2.0 / OIDC / OAuth | Inbound (users authenticate via this system) |
| (e.g., Google Tag Manager) | Third-party script | N/A — script injection | Outbound (events sent from site to GTM) |
| (e.g., Data Cloud) | Behavioral data platform | Web SDK | Outbound (events) + Inbound (profile enrichment) |
| (e.g., external portal) | iFrame host | N/A — HTTP embedding | Inbound (this site embedded in external page) |

---

## SSO / Identity Integration Design

Complete this section for each identity provider integration.

### IdP: (name)

- **Protocol:** SAML 2.0 / OIDC / OAuth 2.0
- **Salesforce role:** SP only / SP + IdP simultaneously
- **Sites enabled on:** (list site names where this SSO config is enabled)
- **ACS URL:** (exported from SAML configuration record)
- **SP Entity ID:** (exported from SAML configuration record — NOT the org entity ID)
- **User provisioning:** JIT provisioning / pre-provisioned / Auth Provider registration handler
- **Registration handler class:** (Apex class name, if OIDC/OAuth)
- **Fallback auth path:** (what happens if the IdP is unavailable)
- **IdP certificate expiry date:** (add to operational calendar)

---

## Script and Widget Injection Plan

Complete this section for each third-party script that must load on the site.

### Site: (site name)

| Script / Vendor | Source URL | Load Location | Injection Mechanism | CSP Directive |
|---|---|---|---|---|
| Google Tag Manager | `https://www.googletagmanager.com/gtm.js?id=GTM-XXX` | Head | Privileged Script Tag (LWR) | `script-src` |
| Intercom | `https://widget.intercom.io/widget/<app_id>` | Head | Privileged Script Tag (LWR) | `script-src` |
| (Aura site example) | `https://vendor.example.com/chat.js` | Head markup | Static resource or head markup (Aura) | N/A |

**Notes on dataLayer / event push architecture:**
(Describe how LWC components will push events to GTM/analytics without needing additional script tags)

---

## Data Cloud Integration

- **Data Cloud provisioned in org?** Yes / No
- **Org-level connection configured?** Yes / No
- **Sites activated in Data Cloud setup?**

| Site Name | Activated? | SDK Script Visible in Page Source? |
|---|---|---|
| | | |

- **Identity signal configuration:** (email hashing enabled? consent gating required?)
- **Event types to capture:** (page views, clicks, form submissions, custom events)

---

## iFrame Embedding Assessment

- **Is any external system attempting to embed this Experience Cloud site in an iFrame?** Yes / No
- **If yes — embedding origin domain:**
- **X-Frame-Options constraint acknowledged?** Yes / No
- **Chosen resolution:**
  - [ ] Redirect flow (no embedding)
  - [ ] JavaScript widget API (no iFrame)
  - [ ] Salesforce Support case opened for trusted-origin exception (domain: ______)
  - [ ] Other (document rationale):

---

## CSP Compliance Checklist

For LWR sites, verify the following directives are satisfied:

- [ ] `script-src` includes all third-party script domains via Privileged Script Tag
- [ ] `connect-src` includes all external API endpoints called from site pages (XHR/fetch)
- [ ] `frame-src` includes any external iFrames embedded within site pages (not the site being embedded — that is `X-Frame-Options`)
- [ ] No `unsafe-inline` or `unsafe-eval` directives introduced by integration work
- [ ] Browser DevTools console shows zero CSP violation errors after integration deployment

---

## Security Review

- [ ] SAML assertions validated server-side; no assertion content logged or stored in browser storage
- [ ] Auth Provider registration handler handles both new-user and existing-user cases; no unhandled exceptions
- [ ] Third-party scripts loaded via Privileged Script Tag reviewed for data access scope (what session data is visible to the script)
- [ ] Data Cloud identity signal transmission reviewed against privacy policy and data residency requirements
- [ ] iFrame `X-Frame-Options` constraint documented and resolution approach approved
- [ ] Session isolation verified: guest user session cannot access authenticated user data

---

## Operational Runbook Notes

- **IdP certificate expiry monitoring:** (how is this tracked?)
- **Multi-site configuration audit frequency:** (how often are Privileged Script Tags and Data Cloud site activations audited for drift?)
- **SSO break-glass procedure:** (how do admins access Salesforce if the IdP is unavailable?)
- **Registration handler deployment process:** (CI/CD pipeline or manual deployment?)

---

## Deviations from Standard Pattern

(Record any deviations from the guidance in SKILL.md and the reason for each)

| Deviation | Justification | Reviewed By |
|---|---|---|
| | | |
