# LLM Anti-Patterns — Hybrid Integration Architecture

Common mistakes AI coding assistants make when generating or advising on hybrid Salesforce integration architecture.

---

## Anti-Pattern 1: Recommending IP Allowlisting as the Security Control on Hyperforce

**What the LLM generates:** "Add Salesforce's IP ranges to your firewall allowlist so only Salesforce can call your on-premises endpoint."

**Why it happens:** IP allowlisting is a well-known network security pattern and LLMs apply it without checking the Hyperforce IP stability constraint.

**The correct pattern:** Hyperforce IP ranges are ephemeral and not stable. Salesforce documentation explicitly states they should not be used for authentication. Use mTLS (client certificate) or Salesforce Private Connect instead.

**Detection hint:** Any recommendation to allowlist Salesforce IPs for a Hyperforce org is incorrect. The org's Hyperforce status can be confirmed in Setup > Company Information.

---

## Anti-Pattern 2: Suggesting Salesforce Has a Native VPN Client

**What the LLM generates:** "Configure a site-to-site IPSec VPN between Salesforce and your on-premises network to keep traffic private."

**Why it happens:** LLMs are familiar with AWS VPN Gateway and Azure VPN Gateway patterns and apply them to Salesforce without verifying platform capability.

**The correct pattern:** Salesforce does not have a native VPN gateway or IPSec client. On-premises private connectivity requires (a) a DMZ relay host that initiates outbound connections, (b) Salesforce Private Connect (AWS PrivateLink, add-on license), or (c) exposing the on-premises system over the internet with mTLS/OAuth.

**Detection hint:** Any mention of "VPN tunnel" or "IPSec" for Salesforce-to-on-premises connectivity is not achievable natively. The design requires a relay or Private Connect.

---

## Anti-Pattern 3: Treating Private Connect as Self-Serve and Generally Available

**What the LLM generates:** "Enable Salesforce Private Connect in Setup under Network Access to configure your PrivateLink connection."

**Why it happens:** LLMs generate plausible Setup navigation paths without knowing the actual provisioning requirements.

**The correct pattern:** Salesforce Private Connect requires (a) an add-on license purchased separately, and (b) a support case to opt the org in. It is not visible in Setup by default and is not self-serve. Plan 2-4 weeks for the full provisioning cycle.

**Detection hint:** If a response suggests activating Private Connect through Setup without mentioning the license and support case, the provisioning path is incorrect.

---

## Anti-Pattern 4: Confusing In-Transit Encryption Gateway with Shield Platform Encryption

**What the LLM generates:** "Use Salesforce Shield Platform Encryption to encrypt the data while it's in transit between your DMZ and Salesforce."

**Why it happens:** LLMs conflate at-rest field encryption (Shield Platform Encryption) with in-transit network encryption (TLS/mTLS at the network layer or gateway-side tokenization).

**The correct pattern:** Shield Platform Encryption encrypts data at rest in the Salesforce database. It has no role in securing data in transit over the network. In-transit encryption is handled by TLS/mTLS at the network layer. DMZ encryption gateways (DataPower, field-level tokenization proxies) handle pre-ingestion field transformation.

**Detection hint:** Any response that uses "Shield Platform Encryption" to address a transit or network security requirement is applying the wrong tool.

---

## Anti-Pattern 5: Designing DMZ Relay Without HA or Fallback

**What the LLM generates:** "Deploy MuleSoft Runtime on a single DMZ server to relay calls between Salesforce and your on-premises system."

**Why it happens:** LLMs generate minimal working designs without considering the production reliability requirement.

**The correct pattern:** A single-node DMZ relay is a SPOF for all integrations passing through it. Production hybrid designs require: (a) HA relay deployment (minimum two nodes with load balancer), (b) documented fallback behavior for relay failure (queue-based async, circuit breaker), and (c) alert thresholds on relay health.

**Detection hint:** Any hybrid integration design with a single relay node and no HA configuration or fallback plan is not production-grade.

---

## Anti-Pattern 6: Recommending Inbound Port Opening on DMZ Host

**What the LLM generates:** "Open port 443 inbound on your DMZ server so Salesforce can push events to it."

**Why it happens:** LLMs default to server-listener patterns without considering that DMZ hosts can use outbound polling to avoid inbound firewall rules.

**The correct pattern:** The primary pattern for DMZ relay connectivity is outbound-only from the DMZ host. The relay polls Salesforce Platform Events or subscribes to the Streaming API over an outbound persistent connection. MuleSoft Runtime Manager uses an outbound agent connection to the control plane — no inbound port required. Require inbound ports only if the architecture genuinely requires server-push and document the security exception.

**Detection hint:** Any architecture that requires opening inbound TCP from the internet to a DMZ relay host should be questioned — most relay patterns can be redesigned as outbound-initiated from the relay side.
