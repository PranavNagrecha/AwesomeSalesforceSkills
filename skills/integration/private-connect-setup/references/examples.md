# Examples — Private Connect Setup

## Example 1: Outbound to a data warehouse over a private endpoint

**Context:** Apex and Salesforce Connect reach a Snowflake account hosted in the
customer's own cloud tenancy. The security review rejected public-internet egress for this
traffic.

**Problem:** the team enabled Private Connect, saw the callout keep working, and closed
the finding. It was still traversing the public internet — the Named Credential had never
been repointed, so nothing about the successful callout had changed.

**Prerequisites, checked before any configuration (each can end the project):**

1. The org is on Hyperforce. Confirm the instance in Setup → Company Information and its
   infrastructure on the Salesforce Trust status page.
2. Private Connect is on the contract. It is separately purchased and usage-billed.
3. The region of the endpoint service matches the org's instance region.
4. The partner or platform exposes a PrivateLink-style endpoint service, not just a public
   URL.

**Configuration order — Salesforce is last, not first:**

1. In the cloud account, create the VPC Endpoint Service (AWS) or Private Link Service
   (Azure) fronting the warehouse, and note the service name.
2. Setup → **Private Connect** → add an **Outbound** connection with that service name.
   Salesforce provisions the peering and issues a private DNS name.
3. Accept the pending connection request in the cloud console. Until this is accepted the
   connection sits in a pending state, which reads as a Salesforce fault and is not one.
4. Repoint the Named Credential at the issued private DNS name — the step that actually
   moves the traffic:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<NamedCredential xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Warehouse (Private Connect)</label>
    <namedCredentialType>SecuredEndpoint</namedCredentialType>
    <generatedAuthorizationHeader>false</generatedAuthorizationHeader>
    <parameters>
        <parameterName>Url</parameterName>
        <parameterType>Url</parameterType>
        <parameterValue>https://wh.privatelink.internal.example.com</parameterValue>
    </parameters>
    <parameters>
        <parameterName>ExternalCredential</parameterName>
        <parameterType>Authentication</parameterType>
        <parameterValue>Warehouse_OAuth</parameterValue>
    </parameters>
</NamedCredential>
```

**Why it works:** Private Connect provisions a path; it does not rewrite configuration.
The public hostname continues to resolve and continues to work, so the callout gives no
signal either way — which is exactly why teams believe they have migrated when they have
not. Repointing the Named Credential is the only change that moves traffic, and keeping
the OAuth External Credential unchanged is deliberate: the private path replaces the
route, never the authentication.

---

## Example 2: Proving which path the traffic actually took

**Context:** the migration above is complete and needs sign-off for the audit.

**Problem:** the obvious test asserts a `200` from the callout. That proves reachability,
which was true before the project started. It cannot distinguish the private path from the
public one, so it would pass just as happily against a misconfiguration.

**Solution:** a positive probe from Salesforce, then a negative test on the far side. Only
the second one is evidence.

```apex
@IsTest
private class PrivateConnectProbeTest {
    // Reachability only. Deliberately NOT the acceptance criterion — see below.
    @IsTest
    static void endpointRespondsThroughNamedCredential() {
        Test.setMock(HttpCalloutMock.class, new WarehouseHealthMock(200));
        Test.startTest();
        HttpResponse res = WarehouseGateway.health();
        Test.stopTest();
        Assert.areEqual(200, res.getStatusCode());
    }
}
```

The evidence that satisfies the audit is collected outside Salesforce, in three steps:

1. **Source address.** In the warehouse's access log, confirm requests arrive from the
   endpoint service's private address range rather than from a public egress address.
   This is the single most useful check and takes a minute.
2. **Endpoint service metrics.** Confirm the connection shows accepted connections and
   bytes transferred that correlate with the Salesforce job schedule. Zero bytes on a
   provisioned connection is the signature of anti-pattern 4 — a private link paid for
   and unused.
3. **Negative test.** Remove the public route, or block the public source range at the
   warehouse, and re-run the job. If it still succeeds, the private path is carrying the
   traffic. If it fails, it never was.

**Why it works:** steps 1 and 2 are observations and step 3 is an experiment. The
experiment is what turns "we configured it" into "we verified it", and it is the only one
of the three that cannot be satisfied by a misconfiguration that happens to look right.
Run it in a lower environment first — the negative test is, by construction, an outage if
the answer is no.

**Ongoing:** alert on the endpoint service's connection state, not just on callout errors.
A connection that drops out of the accepted state fails over to the public path silently
in some configurations and hard-fails in others, and neither outcome announces itself in
Salesforce.
