# LLM Anti-Patterns — Integration Security Architecture

Common mistakes AI coding assistants make when generating or advising on Integration Security Architecture.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending IP Allowlisting for Hyperforce-Based Integrations

**What the LLM generates:** "To secure your integration, add the Salesforce IP ranges to your firewall allowlist. You can find the current Salesforce IP addresses in the Salesforce Trust site or in your org's Setup > Network Access page."

**Why it happens:** Training data includes many Salesforce integration guides written for Classic infrastructure where IP allowlisting was a standard and viable approach. The Hyperforce migration is relatively recent, and content describing Hyperforce's dynamic IP behavior is less prevalent in training data than the older Classic guidance.

**Correct pattern:**

```text
For Hyperforce orgs, IP allowlisting is not a reliable authentication mechanism.
Hyperforce IPs are dynamically assigned across cloud infrastructure and are not
published in a stable static list. Use mTLS mutual certificate authentication instead:
- Generate a certificate in Salesforce Certificate and Key Management
- Configure the Named Credential to present the certificate
- Install the certificate as a trusted client cert on the external system
- The external system validates Salesforce's identity by certificate, not source IP
```

**Detection hint:** Look for phrases like "add Salesforce IP ranges to your allowlist," "whitelist Salesforce IPs," or references to `ipRanges` in firewall rules in the context of a Hyperforce integration recommendation.

---

## Anti-Pattern 2: Treating OAuth Signing Certificate and mTLS Client Certificate as the Same Object

**What the LLM generates:** "Configure your certificate in Certificate and Key Management and use it for both the JWT Bearer OAuth flow and the mTLS client certificate in your Named Credential. This keeps things simple with one certificate to manage."

**Why it happens:** Both configurations reference Certificate and Key Management, and both are associated with the same external integration. LLMs pattern-match on "one certificate = one integration" simplification without understanding that the two roles have different CA trust requirements and lifecycle paths.

**Correct pattern:**

```text
OAuth JWT Signing Certificate:
- Purpose: Sign the JWT assertion sent to OAuth token endpoint
- Can be self-signed; OAuth server validates signature, not CA chain
- Configured: Connected App (public cert upload) + External Credential JWT settings

mTLS Client Certificate:
- Purpose: Presented during TLS handshake to remote API endpoint
- Must be issued by CA trusted by remote server's mTLS trust store
- Configured: Named Credential > Client Certificate field
- Often requires CSR submission to external system's CA

These are two distinct certificates. Design, provision, and track them separately.
```

**Detection hint:** Flag any response that says "use the same certificate for" both OAuth JWT and mTLS, or that shows a single certificate alias referenced in both the Connected App signature settings and the Named Credential mTLS settings.

---

## Anti-Pattern 3: Omitting the Explicit Port in Named Credential URLs for mTLS

**What the LLM generates:** `Named Credential URL: https://api.partner.com` with instructions to enable the client certificate option, without specifying that port 8443 must be included in the URL if the mTLS endpoint uses it.

**Why it happens:** LLMs default to standard HTTPS port 443 in URL construction. The requirement to explicitly include `:8443` in Named Credential URLs is a Salesforce-specific platform behavior that is not obvious from general web development knowledge.

**Correct pattern:**

```text
If the remote mTLS endpoint listens on port 8443:
  Named Credential URL: https://api.partner.com:8443/endpoint/path

If the remote mTLS endpoint listens on port 443 (standard HTTPS with mTLS):
  Named Credential URL: https://api.partner.com/endpoint/path

Verify the correct port with the external system before configuring the Named Credential.
Run: openssl s_client -connect api.partner.com:8443
to confirm the TLS handshake and client certificate request on the expected port.
```

**Detection hint:** Any Named Credential URL recommendation for an mTLS endpoint that does not include a port number — check whether the external API documentation specifies a non-443 mTLS listener port.

---

## Anti-Pattern 4: Ignoring the 50-Certificate Org Limit in Multi-Integration Architecture

**What the LLM generates:** An architecture diagram or integration design where each of 12 external systems has its own dedicated certificate in Salesforce, with no mention of the org-level certificate limit or any consolidation strategy.

**Why it happens:** LLMs generate integration designs based on clean isolation principles (one cert per system) without being aware of the hard 50-certificate platform limit. This limit is not prominently featured in general Salesforce documentation and is underrepresented in training data relative to basic integration patterns.

**Correct pattern:**

```text
Before finalizing a certificate-per-integration design:
1. Check current certificate count: Setup > Certificate and Key Management > count entries
2. Project total: current count + certificates required by proposed design
3. If projected total > 35 (warning threshold before hard limit):
   - Consider API gateway consolidation: one Salesforce cert authenticates to gateway
   - Consider shared certificates for integrations that trust the same external CA
   - Plan certificate retirement for decommissioned integrations
4. Hard limit is 50; there is no support escalation path to raise it
```

**Detection hint:** Multi-integration architecture designs (5+ external systems) that specify a unique certificate per system without any mention of the 50-cert limit or a consolidation strategy.

---

## Anti-Pattern 5: Recommending Salesforce Private Connect Without Confirming Licensing and Enablement Prerequisites

**What the LLM generates:** "For maximum security, use Salesforce Private Connect to establish a private network connection to your AWS VPC. This eliminates public internet exposure. You can configure this in Setup > Salesforce Private Connect."

**Why it happens:** Salesforce Private Connect is the architecturally correct answer for high-sensitivity integrations requiring private network paths. LLMs correctly identify it as the best practice but omit the prerequisite checks: it is not included in standard Salesforce licensing, it requires a support-assisted enablement process, and it is only available for certain cloud regions and Hyperforce deployments.

**Correct pattern:**

```text
Before recommending Salesforce Private Connect:
1. Confirm licensing: Private Connect is an add-on; verify entitlement with Salesforce AE
2. Confirm cloud region compatibility: only certain AWS/Azure regions are supported
3. Confirm the external system operates in a VPC that can establish PrivateLink
4. Account for lead time: enablement requires a Salesforce support case and
   typically takes 2–4 weeks
5. Include Private Connect as a separate project track with its own prerequisites,
   not as a single configuration step within the integration sprint

If Private Connect is not viable, mTLS over public internet with strong
certificate management is the documented alternative.
```

**Detection hint:** Any Private Connect recommendation that does not mention licensing verification, support-assisted enablement, or lead time. Phrases like "configure in Setup" for Private Connect are a red flag — it is not a self-service Setup configuration.

---

## Anti-Pattern 6: Conflating Connected App OAuth Scope with Integration-Level Data Access Control

**What the LLM generates:** A Connected App configuration with `scope: full` or `scope: api` for an inbound integration, reasoning that "the external system needs full access to read and write the required objects."

**Why it happens:** `api` and `full` are the most common scopes shown in documentation examples. LLMs default to broad scopes to avoid troubleshooting narrow-scope failures, which are a common pattern in training data support threads.

**Correct pattern:**

```text
Connected App OAuth scope should be minimal:
- Identify the specific objects and operations the integration requires
- Use object-level scope (e.g., `api` for REST API access) combined with
  profile/permission set restrictions on the running user
- Never grant `full` scope unless the integration explicitly requires
  metadata API and all user permissions
- Scope over-provisioning means a compromised token grants broader access
  than the integration needs — containment blast radius is larger

For inbound integrations: apply IP-range restrictions on the Connected App
for Classic orgs; for Hyperforce, use the Connected App's certificate
validation (mTLS) as the equivalent control.
```

**Detection hint:** Connected App configurations with `scope: full` or `scope: api refresh_token` for a narrowly-scoped integration (e.g., reading Account records for a sync job). Investigate whether the broad scope is justified.
