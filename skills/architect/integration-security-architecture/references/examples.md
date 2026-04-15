# Examples — Integration Security Architecture

## Example 1: Hyperforce Migration Breaks IP-Allowlisted ERP Integration

**Context:** A financial services org on Classic Salesforce migrated to Hyperforce as part of an infrastructure upgrade. The org had a legacy outbound integration to an on-premises ERP system where the ERP firewall allowlisted a set of Salesforce IPs that had been stable for several years.

**Problem:** After Hyperforce migration, outbound callouts from Salesforce to the ERP began failing intermittently — sometimes passing, sometimes timing out with no Salesforce-side error. The failure pattern was non-deterministic and initially attributed to the ERP itself. Investigation eventually revealed that Salesforce's egress IPs on Hyperforce were changing as traffic was routed across cloud infrastructure. The ERP firewall was seeing callout attempts from IPs not in its allowlist and silently dropping packets. The allowlist contained IPs that were valid on Classic but were no longer the source IPs on Hyperforce.

**Solution:**

```text
Architecture change:
1. Remove IP-based firewall rule from ERP; replace with mTLS mutual authentication.
2. Generate a dedicated client certificate in Salesforce Certificate and Key Management.
   - Key size: 2048-bit RSA minimum; 4096-bit recommended for long-lived certs.
   - Expiry: 2 years with calendar reminder set at 18 months.
3. Export the Salesforce certificate and install as trusted client cert on the ERP API layer.
4. Update the Named Credential endpoint URL to include explicit port if ERP mTLS listener
   is on 8443: https://erp.internal.example.com:8443/api/v2
5. Configure the Named Credential to present the client certificate on outbound calls.
6. ERP validates Salesforce's certificate on every TLS handshake — no IP dependency.
```

**Why it works:** mTLS authenticates Salesforce's identity by cryptographic proof (the private key held in Salesforce) rather than by network location. Hyperforce IP rotation is irrelevant because the ERP is checking the certificate, not the source IP. The integration works regardless of which cloud infrastructure node routes the egress traffic.

---

## Example 2: API Gateway as Single mTLS Entry Point for Multi-System Integration

**Context:** A manufacturing org had 14 external systems (ERP, WMS, PLM, supplier portals) each needing to call Salesforce APIs. The initial design called for each system to have its own Connected App and its own inbound authentication. Certificate count was projected to reach 38 within two years — uncomfortably close to the 50-cert limit — and the security team wanted a single audit trail for all inbound API traffic.

**Problem:** Per-system direct integration meant: 14 separate Connected Apps with varying OAuth scope configurations; 14 separate certificates to manage and rotate; no centralized logging or rate limiting; risk of scope over-provisioning in Connected Apps configured by individual integration teams.

**Solution:**

```text
Architecture decision:
1. MuleSoft API Gateway placed as the single entry point for all 14 external systems.
2. Each external system authenticates to MuleSoft using its own certificate (managed by
   MuleSoft's certificate store — outside Salesforce's 50-cert limit).
3. MuleSoft authenticates to Salesforce using a single Connected App with a single
   OAuth 2.0 JWT Bearer certificate (one Salesforce certificate consumed).
4. MuleSoft enforces per-system rate limits, payload validation, and audit logging.
5. Salesforce Connected App scopes are set to the minimum required for all integrations
   routed through the gateway.
6. Private Connect established between MuleSoft VPC and Salesforce — inbound traffic from
   gateway never traverses public internet.

Result:
- Salesforce certificate count: 1 (gateway JWT signing cert) instead of 14
- Single Connected App with defined, audited scope
- All inbound integration traffic logged at gateway layer
- Salesforce Private Connect eliminates public API endpoint exposure
```

**Why it works:** The gateway consolidates the authentication surface. Salesforce only needs to trust one identity (the gateway), not 14 external systems. Certificate management for the external systems is delegated to the gateway's certificate store, leaving Salesforce's 50-cert budget largely intact. Private Connect means the Salesforce API endpoint is not reachable from the public internet at all.

---

## Example 3: JWT Bearer OAuth and mTLS — Separate Certificate Configuration

**Context:** A healthcare org integrating with a payer API that required both OAuth 2.0 JWT Bearer authentication and mTLS client certificate presentation on the same outbound callout.

**Problem:** The implementation team used the same certificate for both the JWT signing configuration and the Named Credential's mTLS client certificate setting, reasoning that "one cert is simpler." The OAuth token requests succeeded (JWT signing worked) but mTLS failed because the payer's mTLS trust store expected a certificate issued by a specific intermediate CA — not the self-signed certificate that worked for OAuth JWT signing.

**Solution:**

```text
Certificate inventory (two separate certificates, two separate purposes):

Certificate A — JWT Signing Certificate
- Purpose: Signs the JWT assertion in the OAuth 2.0 JWT Bearer token request
- Configured in: Connected App > Use Digital Signature > upload public cert
- Reference in: JWT Signing Certificate field in External Credential (Named Principal)
- Issued by: Can be self-signed or any CA; payer OAuth server only checks the signature
- Salesforce holds: Private key

Certificate B — mTLS Client Certificate  
- Purpose: Presented to payer's TLS listener during handshake to prove caller identity
- Configured in: Certificate and Key Management (separate entry from Certificate A)
- Reference in: Named Credential endpoint configuration > Client Certificate field
- Issued by: Must be signed by the CA that the payer's mTLS trust store trusts
- Salesforce holds: Private key; payer holds corresponding CA trust anchor

Named Credential URL: https://payer-api.example.com:8443/fhir/r4
(port 8443 explicit — payer mTLS listener does not respond on 443)
```

**Why it works:** The two certificates serve different authentication layers. Certificate A proves the application's OAuth identity to the authorization server. Certificate B proves the TLS client identity to the API endpoint. The payer's systems — OAuth server and API TLS listener — may be run by different teams with different CA trust requirements. Separate certificates allow each to be managed, rotated, and trusted independently.

---

## Anti-Pattern: IP Allowlisting on Hyperforce Orgs

**What practitioners do:** After moving to Hyperforce, teams continue to maintain IP allowlists on external firewalls using Salesforce IP ranges found in documentation or observed in network logs. They may add new IPs as failures occur, creating an expanding allowlist that never stabilizes.

**What goes wrong:** Hyperforce IPs are not stable and are not published in a canonical static list. The allowlist requires continuous manual maintenance. Failures are non-deterministic — the integration works when traffic routes through an allowlisted IP and fails when it routes through a new IP. Production outages occur with no Salesforce-side error (the packet is dropped at the firewall before reaching Salesforce), making root-cause analysis difficult.

**Correct approach:** Replace IP allowlisting with mTLS client certificate authentication. The external system validates Salesforce's identity by certificate, not by source IP. This works regardless of Hyperforce IP rotation and requires zero ongoing maintenance as the integration scales.
