# Gotchas — Integration Security Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Hyperforce IPs Are Ephemeral — IP Allowlisting Fails Without Warning

**What happens:** An integration that uses IP-based firewall allowlisting works in testing and for some period in production, then begins failing intermittently. Connection timeouts or `Connection refused` errors appear on the external system's side. There is no Salesforce error log entry because the packet is dropped before reaching Salesforce.

**When it occurs:** Any org on Hyperforce where an external system (ERP firewall, API gateway, on-premises server) has added Salesforce IP addresses to an allowlist. As Hyperforce routes egress traffic across cloud infrastructure, different IP addresses are used. Once a new IP appears that is not on the allowlist, all callouts through that route fail until traffic shifts again.

**How to avoid:** Do not use IP allowlisting as the authentication or access-control mechanism for Hyperforce-based orgs. Use mTLS mutual certificate authentication, which proves identity cryptographically rather than by network location. For inbound traffic to Salesforce, IP allowlisting on the Salesforce side (trusted IP ranges) is a separate concern and is still configurable — the risk is on allowlists maintained by external systems trying to restrict which IPs can reach them.

---

## Gotcha 2: Port 8443 Must Be Explicitly Specified in the Named Credential URL

**What happens:** An outbound Named Credential is configured for an endpoint that uses mTLS on port 8443. The Named Credential URL is set to `https://api.example.com` without specifying the port. Callouts either connect to port 443 (where no mTLS listener exists) and fail with a TLS error, or fail to connect at all. No client certificate is presented because the connection never reaches the mTLS listener.

**When it occurs:** Any Named Credential where the remote API uses a non-standard port for mTLS. Port 8443 is common for mTLS-only endpoints. The error surface is confusing because the failure may appear as a generic `System.CalloutException: IO Exception` with no indication that the wrong port was targeted.

**How to avoid:** Always include the port explicitly in the Named Credential endpoint URL: `https://api.example.com:8443/path`. Confirm the exact port the remote endpoint uses for mTLS by checking the external system's API documentation or by running `openssl s_client -connect api.example.com:8443` from a network-adjacent system to confirm the TLS handshake completes and a client certificate request is issued.

---

## Gotcha 3: The OAuth JWT Signing Certificate and the mTLS Client Certificate Are Separate Objects

**What happens:** A practitioner configures a single certificate to serve dual purposes — as the JWT signing certificate for OAuth 2.0 JWT Bearer flow and as the mTLS client certificate in the Named Credential. One of the two authentication mechanisms fails, often the mTLS presentation, because the receiving system's mTLS trust store requires a certificate from a specific CA that is different from the self-signed certificate acceptable for JWT signing.

**When it occurs:** Integration design with both OAuth 2.0 JWT Bearer token acquisition and mTLS transport-layer authentication on the same callout — common in financial services, healthcare payer APIs, and government integrations. The confusion arises because both certificates are configured in the same general area of Salesforce Setup (Certificate and Key Management) and both are associated with the same external integration.

**How to avoid:** Document two separate certificate objects in the architecture design with explicit purposes:
- **JWT Signing Certificate**: Used to sign the JWT assertion sent to the OAuth token endpoint. Can be self-signed. Configured in: Connected App > Use Digital Signature (public cert uploaded) and External Credential JWT Bearer settings (private key held by Salesforce).
- **mTLS Client Certificate**: Presented during TLS handshake to the API endpoint. Must be issued by a CA trusted by the remote server's mTLS trust store. Configured in: Named Credential's certificate setting.
These certificates may have different issuers, different expiry schedules, and different rotation responsibilities.

---

## Gotcha 4: Hard 50-Certificate Limit Per Org Cannot Be Raised

**What happens:** A new certificate cannot be created or imported because the org has reached the 50-certificate limit in Certificate and Key Management. Integration deployments fail. The error may surface as a deployment error in a CI/CD pipeline if the pipeline attempts to deploy a certificate metadata component.

**When it occurs:** Orgs with many integrations, especially those that have grown over years without a certificate retirement process. Each self-signed certificate generated in Salesforce, each CA-signed certificate imported, and each certificate used for OAuth JWT signing counts toward the 50-cert limit. Certificates from decommissioned integrations that were never deleted remain in the count.

**How to avoid:** Include certificate retirement in integration decommissioning procedures. Periodically audit Certificate and Key Management and remove certificates for retired integrations. Before designing a new integration architecture, confirm current count. If the org is above 35 certificates, recommend either API gateway consolidation (one Salesforce certificate authenticates to the gateway, which manages certificates for all upstream systems) or a formal certificate lifecycle governance process. There is no workaround or support exception for the 50-cert limit.

---

## Gotcha 5: Salesforce Private Connect Is Not Enabled by Default and Has Licensing Requirements

**What happens:** An architecture design specifies Salesforce Private Connect for private network connectivity to a cloud VPC. Implementation begins and the Private Connect setup option is not visible in Setup, or enablement fails. Project timelines slip because the licensing and enablement process was not factored in.

**When it occurs:** When Private Connect is included in an architecture recommendation without confirming that (a) it is licensed, (b) the underlying cloud provider private connectivity (AWS PrivateLink, Azure Private Link) is supported for the org's cloud region, and (c) the enablement process (which requires a support case) has been initiated.

**How to avoid:** Before including Private Connect in an architecture recommendation, verify: licensing entitlement with the Salesforce account team, supported cloud regions and providers for the org's Hyperforce deployment, and the lead time for support-assisted enablement. Flag Private Connect as a prerequisite in the project plan with its own track, not as a configuration step within the integration sprint.

---

## Gotcha 6: Certificate Expiry Is Not Auto-Renewed and Causes Silent Integration Failures

**What happens:** A certificate used for mTLS or OAuth JWT signing expires. Outbound callouts begin failing. Depending on how the external system handles expired client certificates, the failure may appear as a TLS handshake error, a 401 Unauthorized, a connection timeout, or (on some systems) silent packet drop. Certificates in Salesforce do not auto-renew and there is no built-in expiry notification.

**When it occurs:** Typically 1–3 years after initial configuration, when the certificate reaches its expiry date. Common in orgs that configured mTLS at go-live and never established a rotation process. The failure is often sudden — the certificate was valid yesterday, expired at midnight, and all callouts fail at business open.

**How to avoid:** Record every certificate expiry date in a centralized tracking system (Jira, Confluence, a Named Credential inventory sheet) with a 90-day lead alert. Define an owner for each certificate. Include certificate rotation as a step in integration health reviews. When a new certificate is deployed, the Named Credential configuration must be updated to reference the new certificate — deployment of the new cert alone does not update existing Named Credentials pointing to the old one.
