# Examples — Hybrid Integration Architecture

## Example 1: On-Premises ERP Integration via DMZ Relay

**Scenario:** A manufacturer runs SAP on-premises behind a corporate firewall. Salesforce Service Cloud needs real-time order status from SAP when a rep opens a case.

**Problem:** The SAP system is on an RFC/BAPI interface inside the corporate network. Opening inbound TCP from the internet to the SAP host is not permitted by the security team. Salesforce has no native VPN client capability.

**Solution:** Deploy MuleSoft Runtime on a host in the corporate DMZ (or on-premises network segment with controlled egress). The DMZ host initiates outbound HTTPS to the MuleSoft Anypoint Platform control plane and to Salesforce. SAP calls stay inbound from the DMZ host only. The DMZ relay acts as a protocol bridge: RFC/BAPI inbound from SAP, HTTPS/REST outbound to Salesforce via MuleSoft API Manager.

**Why it works:** Outbound-only TCP from the DMZ host satisfies firewall policy (no inbound rule required from the internet). MuleSoft's hybrid deployment model is documented in Anypoint Platform: a Runtime Manager agent on the DMZ host polls the control plane for deployment updates and forwards telemetry outbound — no inbound port needed on the DMZ host.

---

## Example 2: Salesforce Private Connect for Regulated Data Residency

**Scenario:** A financial services firm hosts a loan origination system (LOS) in its own AWS VPC in the same region as its Salesforce Hyperforce org. Regulatory requirements prohibit LOS data from traversing the public internet.

**Problem:** Standard REST API calls from Salesforce to the LOS AWS endpoint cross the public internet. IP allowlisting is not viable because Hyperforce does not publish stable static IPs — the IP ranges are ephemeral and change without notice. (Correction 2026-10-03: Salesforce publishes versioned per-region prefixes at `ip-ranges.salesforce.com/ip-ranges.json`; the real objection is that those prefixes are shared by every org in the region and change between versions, so an allowlist cannot prove the caller is this org.)

**Solution:** Enable Salesforce Private Connect (add-on license required; support case required to opt the org in; both UNVERIFIED 2026-10-03, Help-only). Correction (2026-10-03): for Salesforce-to-LOS callouts the direction is the reverse of what earlier text said. The customer publishes a VPC endpoint service (behind an NLB) and Salesforce creates the endpoint: the Metadata API `OutboundNetworkConnection` takes the customer's `AwsVpcEndpointServiceName` and `Region`, and Salesforce returns the `AwsVpcEndpointId`. A customer-side VPC endpoint to a Salesforce service is the inbound case (`InboundNetworkConnection`). All traffic from Salesforce to the LOS VPC traverses the AWS backbone — never the public internet.

**Why it works:** AWS PrivateLink keeps traffic within the AWS network fabric. Salesforce Private Connect is the only Salesforce-supported mechanism for private network connectivity on Hyperforce (UNVERIFIED 2026-10-03; Government Cloud Plus also offers Salesforce Express Connect). The connection is unidirectional from Salesforce outbound; the customer VPC must expose an NLB (Network Load Balancer) as the PrivateLink target.

---

## Example 3: mTLS Authentication Replacing IP Allowlisting on Hyperforce

**Scenario:** A healthcare org migrating to Hyperforce previously authenticated inbound API calls from their middleware using a static IP allowlist. Post-migration the allowlist breaks because Hyperforce IPs rotate. (Note 2026-10-03: what breaks on migration is a firewall rule that allowlisted the old Salesforce instance addresses; Salesforce now publishes the Hyperforce prefixes in `ip-ranges.json`, which change between versions.)

**Problem:** The Hyperforce infrastructure documentation explicitly states that IP ranges are not stable and should not be used for authentication. (Correction 2026-10-03: the ranges are published and versioned; see `gotchas.md` Gotcha 1. The authentication point stands because the ranges are shared across orgs.) The old allowlist approach becomes unreliable after migration.

**Solution:** Replace IP allowlisting with mutual TLS (mTLS). The middleware presents a client certificate signed by an internal CA, and an API gateway in front of Salesforce, or Salesforce's own inbound mutual authentication, validates it. Correction (2026-10-03): Named Credentials do not validate inbound client certificates; they are outbound definitions that present Salesforce's certificate to the remote server. No IP rule needed because identity is asserted cryptographically.

**Why it works:** mTLS verifies identity regardless of the calling IP address, eliminating the dependency on stable IPs. Salesforce presents client certificates on outbound callouts through Named Credentials, and *Integration Patterns and Practices* confirms two-way SSL with self-signed or CA-signed certificates. UNVERIFIED (2026-10-03): the earlier reference to a "Connected App Certificate Pinning feature" for inbound flows was not found in any fetched guide. For Hyperforce-specific guidance, Salesforce recommends mTLS or Private Connect as the two supported alternatives to IP allowlisting.

---

## Example 4: Decision Record for Private Callouts From Service Cloud to an On-Premises Claims System

**Context:** An insurer's Service Cloud org (Enterprise Edition, Hyperforce, AWS `eu-central-1`) must look up claim status in an on-premises claims system when an agent opens a Case. The claims API is SOAP with WS-Security, sits in the Frankfurt data center, and reaches the insurer's AWS account over Direct Connect. Security policy forbids claim data on the public internet. Average claims API latency is 1.8 seconds, with 6 seconds at month end.

**Decision record (machine-readable form):**

```yaml
adr: HYB-003
title: Private Connect outbound to an AWS endpoint service fronting the claims gateway
status: accepted
date: 2026-10-03
decision:
  path: Salesforce -> AWS PrivateLink -> insurer VPC (NLB) -> Direct Connect -> DMZ XML gateway -> claims SOAP API
  ws_security: injected by the DMZ XML gateway (Salesforce callouts do not support WS-Security)
  identity: two-way SSL between Salesforce and the gateway; gateway holds the WS-Security credential
rejected:
  - option: public DMZ reverse proxy with an allowlist from ip-ranges.json
    reason: claim data would cross the internet; published prefixes are shared by every org in eu-central-1
  - option: hand-built WS-Security headers in WSDL2Apex classes
    reason: Integration Patterns and Practices does not recommend it (maintenance on every release)
metadata:   # deployable components, by Metadata API type and member name
  OutboundNetworkConnection:
    member: Claims_PrivateLink
    connectionType: AwsPrivateLink
    properties:
      Region: eu-central-1
      AwsVpcEndpointServiceName: com.amazonaws.vpce.eu-central-1.vpce-svc-<insurer-service-id>
    status_after_deploy: Unprovisioned   # admin runs Provision; insurer accepts in AWS; expect Ready
  NamedCredential:
    member: Claims_Private
    namedCredentialType: PrivateEndpoint   # API 56.0+; must reference the OutboundNetworkConnection
    namedCredentialParameters:
      - parameterType: OutboundNetworkConnection   # lookup used when the type is PrivateEndpoint
        outboundNetworkConnection: Claims_PrivateLink
  RemoteSiteSetting: none                  # not needed with a named credential; none allowed for the gateway host
callout_design:
  context: Queueable Apex launched from the Case page action (not synchronous)
  timeout_ms: 15000                        # per callout; transaction cap is 120 s cumulative
  retries: 1, then mark Case.Claim_Lookup_Status__c = 'Unavailable'
runbook:
  per_org_steps: [deploy metadata, Provision, AWS owner accepts endpoint connection, verify status Ready, smoke-test callout]
  owners: {salesforce: Integration admin, aws: Cloud network team}
licences_and_enablement:
  - Private Connect add-on and enablement path to confirm with the account team (Help-only, UNVERIFIED 2026-10-03)
consequences:
  - each sandbox needs its own connection and acceptance before integration tests
  - any callout not using Claims_Private fails at the gateway (no public listener), which is the intended control
```

**Why it works:** the private path is enforced twice, by the named credential type and by the gateway having no public listener. WS-Security lives where the platform says it must (the gateway). The callout runs async with an explicit timeout sized to month-end latency, so agents are not blocked when the claims system slows down.

