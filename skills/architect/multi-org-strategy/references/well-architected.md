# Well-Architected Alignment — Multi-Org Strategy

This skill maps to the Salesforce Well-Architected Framework across four pillars. Multi-org architecture decisions have the highest blast radius of any architectural choice in a Salesforce implementation — a wrong call here cascades into years of integration debt, user management overhead, and governor limit complexity.

---

## Security

Multi-org topologies multiply the identity and access management surface area. Each additional production org is an independent security boundary with its own:

- User records and permission assignments
- Profile and permission set configuration
- Session security policies (timeout, IP restrictions, MFA enforcement)
- Connected App configurations (OAuth scopes, callback URLs, IP range restrictions)

**WAF guidance applied:**

- Use an external IdP (Okta, Azure AD) as the single source of truth for identity across all orgs. Configure each org as a SAML Service Provider under the same IdP. This ensures MFA enforcement, session policies, and user lifecycle events (deactivation, role changes) are applied consistently across all orgs.
- Connected Apps used for cross-org integration must be scoped to the minimum required OAuth permissions. Avoid the `full` scope on integration Connected Apps.
- Named Credentials must be used to store all cross-org OAuth credentials. Client secrets and tokens must not appear in Apex source, Custom Settings, or Custom Metadata. Named Credentials are encrypted at rest and are not visible in code review or deployment artifacts.
- JWT Bearer flow (RFC 7523) is the correct server-to-server OAuth pattern for automated cross-org callouts. It does not require a user to authorize the connection at runtime and does not require refresh token storage.
- IP range restrictions on Connected Apps limit the callout surface to known network egress points (your integration platform, MuleSoft VPC, or Apex callout IP ranges). Configure these.

---

## Scalability

Cross-org data exchange is bounded by governor limits on both sides of every callout. Scalability in multi-org architectures requires explicit modeling of limit consumption at design time — not after the integration fails in production.

**WAF guidance applied:**

- REST API callouts from Apex consume limits on the calling org (callout count, CPU time, heap) and on the target org (daily API calls, SOQL, DML). Size the integration volume against both org's limit budgets.
- Bulk API 2.0 is the only scalable pattern for cross-org sync of large record volumes. It uses an asynchronous job model that does not consume per-transaction Apex limits on the calling side and uses efficient batch processing on the receiving side. Use it for any sync job that moves more than a few thousand records.
- Salesforce-to-Salesforce does not scale. Each S2S record exchange is a separate API call. At high volumes, S2S exhausts the daily API limit on both orgs. Do not use S2S for new integrations; migrate existing S2S integrations to Bulk API 2.0 or REST API.
- External Objects (Salesforce Connect) scale for low-volume, on-demand lookups. They do not scale for bulk processing or trigger-based access patterns. Design the External Object boundary clearly: display-time lookups only, never in Apex loops or triggers.

---

## Reliability

Multi-org integrations introduce distributed system failure modes that do not exist in single-org architectures. Each cross-org callout is a network call that can fail, timeout, or return unexpected data. The architecture must account for these failure modes explicitly.

**WAF guidance applied:**

- Every cross-org Apex callout must have explicit timeout handling, error logging, and retry logic. A callout that fails silently leaves data out of sync with no alert and no self-healing.
- Use idempotent upsert operations (with an external ID field) rather than insert for cross-org record creation. If a callout succeeds but the response is lost (network error), the retry must not create a duplicate.
- Platform Events can decouple the trigger of a cross-org callout from its execution, enabling reliable retry without tying the original transaction to the callout's success.
- Monitoring: each org's API usage, callout error rates, and Bulk API job completion status should be surfaced in a centralized monitoring view. Integration failures that are invisible until a user reports missing data are an architectural defect, not an operational concern.
- For Salesforce Connect, the OData endpoint (remote org) must be treated as an external dependency. Implement graceful degradation: if the external data source is unavailable, the calling org's page should display a meaningful message rather than a generic error.

---

## Operational Excellence

Multi-org architectures increase operational complexity proportionally with each additional org. Operational discipline must be designed in from the start, not retrofitted.

**WAF guidance applied:**

- Every production org requires its own release pipeline. Changes to shared integration components (Connected Apps, Named Credentials, permission sets for the integration user) must be coordinated across orgs to avoid breaking the integration during deployment windows.
- Custom Metadata Types are the correct home for cross-org routing configuration (endpoint base URLs, environment-specific org identifiers). CMDT records are version-controlled, deployable, and do not require code changes to update — unlike Custom Settings or hard-coded Apex.
- User management across orgs must be automated via SCIM from the IdP. Manual multi-org offboarding is an operational risk. The cost of one missed deactivation (a terminated employee accessing data) outweighs the investment in SCIM configuration.
- Document the multi-org architecture in an Architecture Decision Record (ADR) that captures: the justification for each org, its data domain, its integration touchpoints, its SSO configuration, and its license allocation. Review and update this document at each major change. Multi-org architectures that lack documentation become unmaintainable within 12–18 months.
- Establish a clear sunset plan: if the justification for a satellite org was temporary (M&A transition, regulatory holding pattern), define the trigger conditions for org consolidation and assign an owner to track it.

---

## Official Sources Used

- Salesforce Well-Architected — Org Strategy Decision Guide
  Architecture patterns and tradeoffs for single vs. multiple org decisions
  URL: https://architect.salesforce.com/design/decision-guides/org-strategy

- Apex Developer Guide — Named Credentials
  Named Credential configuration for Apex callouts; JWT Bearer flow for server-to-server OAuth
  URL: https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts_named_credentials.htm

- Salesforce Help — Salesforce to Salesforce Overview
  S2S feature documentation; confirms legacy status and SOAP API usage
  URL: https://help.salesforce.com/s/articleView?id=sf.salesforce_to_salesforce_overview.htm

- Salesforce Help — Salesforce Connect
  External Objects, OData adapter behavior, external query limits, cross-org data access patterns
  URL: https://help.salesforce.com/s/articleView?id=sf.salesforce_connect.htm

- Salesforce Well-Architected Overview
  Overall architecture quality model — trusted, easy, adaptable — and integration pattern framing
  URL: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
