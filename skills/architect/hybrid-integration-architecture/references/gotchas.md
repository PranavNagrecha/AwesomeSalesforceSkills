# Gotchas — Hybrid Integration Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.
Each gotcha names its source. Claims that no fetched source confirms carry an inline `UNVERIFIED (date):` marker.

## Gotcha 1: Hyperforce IP Ranges Change and Are Shared, So Allowlisting Is Not Authentication

**What happens:** An org moves to Hyperforce and the firewall team allowlists Salesforce IP ranges. Later, connectivity fails when the ranges change, or a security review points out that the allowlist admits every Salesforce org in the region.

Correction (2026-10-03): earlier text said Hyperforce IP ranges are "not stable", "ephemeral", and "subject to change without notice", and Example 2 said Hyperforce "does not publish stable static IPs". Salesforce publishes a machine-readable list at `https://ip-ranges.salesforce.com/ip-ranges.json`. When fetched on 2026-10-03 it carried a `syncToken`, a `createDate` of 2026-07-06, and IP prefixes for 24 AWS and GCP regions. The ranges are published and versioned, and they change between versions. UNVERIFIED (2026-10-03): which traffic direction each prefix covers, and how much notice precedes a change, are described in Salesforce Help, which this pass could not fetch.

**When it occurs:** Hyperforce migrations, and any design that treats a source-IP check as proof of identity.

**How to avoid:** If an allowlist is required, automate it from the JSON feed and watch the `syncToken` for changes. Never make it the only control: every org hosted in that region egresses from the same prefixes. *Integration Patterns and Practices* (Security Considerations) supports two-way SSL with self-signed or CA-signed certificates, and that or OAuth should carry the identity check.

---

## Gotcha 2: A Private Connect Connection Is Not Working Just Because It Deployed

**What happens:** A team deploys `OutboundNetworkConnection` metadata and expects callouts to flow privately. The Metadata API Developer Guide says the connection is created `Unprovisioned` and moves through `Allocation`, `PendingAcceptance`, `PendingActivation` to `Ready` only after an admin performs a Provision action (and Sync or Teardown later). `PendingAcceptance` waits on the customer to accept the endpoint connection on their AWS endpoint service. The connection type is `AwsPrivateLink` (the only non-internal value), so the far end must be an AWS VPC endpoint service.

UNVERIFIED (2026-10-03): earlier text said Private Connect needs a support case to opt the org in and a separate add-on licence. Licensing and enablement are documented only in Salesforce Help; confirm both with the account team during discovery.

**When it occurs:** Pipelines that deploy network metadata to a new sandbox or production org and move straight to integration testing.

**How to avoid:** Treat provisioning as a runbook step with two owners: the Salesforce admin who runs Provision and checks `status` = `Ready`, and the AWS owner who accepts the connection on the endpoint service named in `AwsVpcEndpointServiceName`. Record the `AwsVpcEndpointId` Salesforce returns. Repeat the step per org, because each org has its own connection.

---

## Gotcha 3: Only Callouts Through a PrivateEndpoint Named Credential Use the Private Path

**What happens:** Private Connect is `Ready`, yet traffic still leaves over the internet. The Metadata API Developer Guide (`NamedCredential`, API 56.0 and later) defines a `PrivateEndpoint` named credential type that "sends traffic through a private connection, bypassing the public internet", and requires it to reference an `OutboundNetworkConnection`. A callout to a raw URL, or through a `SecuredEndpoint` or legacy named credential, is not routed through the connection.

**When it occurs:** Apex written before Private Connect existed, Flow HTTP callouts configured against a different named credential, or a copied named credential that kept the old type.

**How to avoid:** Inventory every callout to the on-premises target and require each to use the `PrivateEndpoint` named credential. Block raw endpoint URLs in code review. Monitor the relay or endpoint service for any traffic arriving from public addresses.

---

## Gotcha 4: Salesforce Has No Native VPN Client — On-Premises Connectivity Requires a Relay

**What happens:** A team assumes Salesforce can join a site-to-site VPN tunnel (IPSec or similar) to reach an on-premises system, as AWS Direct Connect or an Azure VPN Gateway can. No fetched Salesforce guide documents such a capability. *Integration Patterns and Practices* describes on-premises access through reverse proxies (Apache HTTP, lighttpd, nginx, IBM WebSeal, CA SiteMinder) and encryption gateways instead. (For Government Cloud Plus only, the *Government Cloud* guide documents Salesforce Express Connect as a private route from the customer data center.)

**When it occurs:** Designs drawn by network teams used to IaaS connectivity.

**How to avoid:** Plan one of: (a) a relay in the DMZ or on-premises network with outbound-capable connectivity, (b) Private Connect to an AWS VPC that reaches on-premises over Direct Connect or VPN, or (c) exposing the on-premises service publicly behind strong authentication (two-way SSL or OAuth).

---

## Gotcha 5: Encryption Gateways Break Filtering on Tokenized Fields

**What happens:** A field-level encryption gateway (*Integration Patterns and Practices* lists Salesforce's own, CipherCloud, IBM DataPower and Computer Associates products) tokenizes PII before it reaches Salesforce. Reports and SOQL that filter on those fields return nothing, because the stored ciphertext does not match plaintext filter values.

**When it occurs:** Any field encrypted at the gateway that a report, list view, duplicate rule, or SOQL `WHERE` clause relies on.

**How to avoid:** Decide per field whether it must be searchable. Use the gateway's deterministic mode for fields that must be filtered and randomized mode only where filtering is never needed (vendor behavior UNVERIFIED 2026-10-03; confirm with the gateway vendor). Record the decision per field in the architecture record. If the data only needs protection at rest inside Salesforce, compare with Shield Platform Encryption, which the same guide lists as the cloud-based option.

---

## Gotcha 6: Relay Latency Counts Against Apex Callout Timeouts

**What happens:** A DMZ relay adds authentication, protocol translation, and a hop to an on-premises system. Callouts that were fast in testing start failing under load. The Apex Developer Guide ("Callout Limits and Limitations", "Execution Governors and Limits") sets a default callout timeout of 10 seconds and a maximum cumulative timeout of 120 seconds for all callouts in one transaction.

**When it occurs:** Synchronous callouts from a record page or a before-save context that chain several relay calls, or an on-premises system that slows down at month end.

**How to avoid:** Set explicit per-callout timeouts sized to the relay's measured latency. Keep synchronous paths to one relay call and move multi-call work to Queueable Apex. Make the relay fail fast with a clear error rather than holding the connection.

---

## Gotcha 7: Remote Site Settings Are Not Needed With a Named Credential

**What happens:** Runbooks for relay-based callouts include "add the relay FQDN to Remote Site Settings" alongside a named credential. The Apex Developer Guide ("Invoking Callouts Using Apex") says a callout whose endpoint is a named credential does not need a remote site setting. The extra Remote Site Setting is harmless to the callout but leaves a second, unaudited path: any Apex can call that FQDN directly without the named credential's authentication.

**When it occurs:** Designs copied from pre-named-credential integrations.

**How to avoid:** Drop the Remote Site Setting when every callout uses the named credential. Remove existing ones during the hybrid integration review so raw-URL callouts to the relay fail.

---

## Gotcha 8: WS-Security Is Not Supported in Salesforce Callouts

**What happens:** An on-premises SOAP service requires WS-Security headers. *Integration Patterns and Practices* ("Remote Process Invocation—Request and Reply", Security Considerations) says Salesforce does not support WS-Security, and lists three alternatives: a security or XML gateway that injects the credentials, transport-level two-way SSL with IP restrictions, or hand-built WS-Security headers in WSDL2Apex classes, which it does not recommend.

**When it occurs:** Integrations with older ESB or mainframe-fronting SOAP services.

**How to avoid:** Put the WS-Security injection in the DMZ gateway so Salesforce sends a plain authenticated request, or negotiate two-way SSL with the service owner. Record the choice; the guide's warning about hand-coded headers is maintenance cost on every Salesforce release.
