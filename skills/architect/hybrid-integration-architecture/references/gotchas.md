# Gotchas — Hybrid Integration Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Hyperforce IPs Are Ephemeral — IP Allowlisting Breaks

**What happens:** An org migrates to Hyperforce and the firewall team tries to allowlist the new Salesforce IP ranges for inbound or outbound traffic. The allowlist works briefly, then connectivity intermittently fails as Salesforce rotates IPs.

**Impact:** Integration calls from on-premises systems to Salesforce are sporadically rejected. Outbound calls from Salesforce to on-premises systems fail because the source IP changes. The failures are non-deterministic and hard to diagnose.

**How to avoid:** Salesforce explicitly documents that Hyperforce IP ranges are not stable and are subject to change without notice. Do not use IP allowlisting as an authentication mechanism on Hyperforce orgs. Replace with mTLS (client certificate authentication) or Salesforce Private Connect.

---

## Gotcha 2: Private Connect Requires a Support Case and an Add-On License — Not Self-Serve

**What happens:** An architect designs a solution using Salesforce Private Connect for a Hyperforce org but does not check the provisioning path. The project hits a 6-week delay because the add-on license was not in the contract and the support case to enable it takes several days.

**Impact:** Private Connect is not visible in Setup until the org is opted in via a support case. The customer must purchase the add-on license separately from the main Salesforce contract. Neither step is self-serve.

**How to avoid:** Include Private Connect licensing and the support opt-in process in project planning before architecture sign-off. The support case is filed under "Salesforce Private Connect Setup" — confirm the timeline with Salesforce account team during discovery.

---

## Gotcha 3: Salesforce Has No Native VPN Client — On-Premises Connectivity Requires a Relay

**What happens:** A team assumes Salesforce can join a site-to-site VPN tunnel (IPSec or similar) to reach an on-premises system, similar to how AWS Direct Connect or Azure VPN Gateway can be configured. They discover no such native capability exists.

**Impact:** The integration design must be reworked to use a DMZ relay (MuleSoft, Boomi, or MuleSoft Anypoint Runtime on a DMZ host) that establishes outbound connectivity to both Salesforce and the on-premises system. Rework late in the project cycle.

**How to avoid:** There is no Salesforce-native VPN gateway. All on-premises connectivity from Salesforce requires either (a) an outbound-capable relay in the on-premises or DMZ network, (b) Salesforce Private Connect (AWS PrivateLink only), or (c) exposing the on-premises system over the public internet with strong authentication (mTLS / OAuth).

---

## Gotcha 4: DMZ Relay Encryption Gateways Require Key Management for Tokenization Queries

**What happens:** A team deploys a field-level encryption gateway (DataPower, CipherCloud successor) in the DMZ to tokenize PII before it reaches Salesforce. Reports and SOQL that filter on encrypted fields fail because the ciphertext in Salesforce does not match plaintext filter values.

**Impact:** Encrypted fields are non-searchable by value in SOQL. Reports that filter on those fields return no results. SOQL WHERE clauses using the field must be replaced with deterministic tokenization or the filtering must be moved to the gateway layer.

**How to avoid:** Decide per-field whether the field needs to be searchable. Use deterministic encryption (same plaintext always produces same ciphertext) for fields that must be filtered; use randomized encryption only for fields where filtering is never needed. Document this decision in the integration architecture record.
