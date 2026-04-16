# Examples — Hybrid Integration Architecture

## Example 1: On-Premises ERP Integration via DMZ Relay

**Scenario:** A manufacturer runs SAP on-premises behind a corporate firewall. Salesforce Service Cloud needs real-time order status from SAP when a rep opens a case.

**Problem:** The SAP system is on an RFC/BAPI interface inside the corporate network. Opening inbound TCP from the internet to the SAP host is not permitted by the security team. Salesforce has no native VPN client capability.

**Solution:** Deploy MuleSoft Runtime on a host in the corporate DMZ (or on-premises network segment with controlled egress). The DMZ host initiates outbound HTTPS to the MuleSoft Anypoint Platform control plane and to Salesforce. SAP calls stay inbound from the DMZ host only. The DMZ relay acts as a protocol bridge: RFC/BAPI inbound from SAP, HTTPS/REST outbound to Salesforce via MuleSoft API Manager.

**Why it works:** Outbound-only TCP from the DMZ host satisfies firewall policy (no inbound rule required from the internet). MuleSoft's hybrid deployment model is documented in Anypoint Platform: a Runtime Manager agent on the DMZ host polls the control plane for deployment updates and forwards telemetry outbound — no inbound port needed on the DMZ host.

---

## Example 2: Salesforce Private Connect for Regulated Data Residency

**Scenario:** A financial services firm hosts a loan origination system (LOS) in its own AWS VPC in the same region as its Salesforce Hyperforce org. Regulatory requirements prohibit LOS data from traversing the public internet.

**Problem:** Standard REST API calls from Salesforce to the LOS AWS endpoint cross the public internet. IP allowlisting is not viable because Hyperforce does not publish stable static IPs — the IP ranges are ephemeral and change without notice.

**Solution:** Enable Salesforce Private Connect (add-on license required; support case required to opt the org in). Configure a VPC endpoint in the customer AWS account pointing to the Salesforce PrivateLink service endpoint for the org's Hyperforce region. All traffic from Salesforce to the LOS VPC traverses the AWS backbone — never the public internet.

**Why it works:** AWS PrivateLink keeps traffic within the AWS network fabric. Salesforce Private Connect is the only Salesforce-supported mechanism for private network connectivity on Hyperforce. The connection is unidirectional from Salesforce outbound; the customer VPC must expose an NLB (Network Load Balancer) as the PrivateLink target.

---

## Example 3: mTLS Authentication Replacing IP Allowlisting on Hyperforce

**Scenario:** A healthcare org migrating to Hyperforce previously authenticated inbound API calls from their middleware using a static IP allowlist. Post-migration the allowlist breaks because Hyperforce IPs rotate.

**Problem:** The Hyperforce infrastructure documentation explicitly states that IP ranges are not stable and should not be used for authentication. The old allowlist approach becomes unreliable after migration.

**Solution:** Replace IP allowlisting with mutual TLS (mTLS). The middleware presents a client certificate signed by an internal CA. Salesforce Named Credentials or an API Gateway in front of Salesforce validates the client certificate. No IP rule needed because identity is asserted cryptographically.

**Why it works:** mTLS verifies identity regardless of the calling IP address, eliminating the dependency on stable IPs. Salesforce supports client certificate validation via Named Credentials (Salesforce-outbound) and via the Connected App Certificate Pinning feature (inbound OAuth flows). For Hyperforce-specific guidance, Salesforce recommends mTLS or Private Connect as the two supported alternatives to IP allowlisting.
