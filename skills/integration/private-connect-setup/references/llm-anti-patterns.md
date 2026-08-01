# LLM Anti-Patterns — Private Connect Setup

Scope: the configuration and verification of Private Connect itself. Where private
networking sits in an overall topology, and whether it is the right answer at all, belongs
to `architect/hybrid-integration-architecture`. This file is about the prerequisites,
the setup order and the failure modes that impersonate network faults.

## Anti-Pattern 1: Recommending Private Connect without checking the prerequisite

Asked "how do we keep this traffic off the public internet", assistants produce Private
Connect setup steps for any org. It is a Hyperforce capability with its own commercial
terms; an org on legacy first-generation infrastructure cannot enable it, and no amount
of configuration will make the Setup node appear.

❌ Open with the configuration steps.
✅ Establish three things first, in this order, because each one can end the
conversation: (1) is the org on Hyperforce; (2) is Private Connect included in the
contract, since it is a separately purchased, usage-billed capability; (3) does the
partner actually expose an endpoint service — AWS PrivateLink or the Azure equivalent. A
partner with only a public URL cannot be reached privately no matter what you configure
on the Salesforce side.

Source: Private Connect overview —
https://help.salesforce.com/s/articleView?id=sf.private_connect_overview.htm

## Anti-Pattern 2: Ignoring direction

Private Connect has an outbound form (Salesforce calls your service) and an inbound form
(your network calls Salesforce). They have different prerequisites, different
configuration and different verification. Assistants blur them because "connect the VPC"
sounds symmetric.

❌ "Set up Private Connect between Salesforce and the VPC."
✅ Name the direction and the initiator. Outbound covers Apex callouts, External Services
and Salesforce Connect reaching your endpoint service. Inbound covers your systems
calling the Salesforce API or an Experience Cloud site. Most requirements need only one,
and configuring both doubles the cost and the review surface for no benefit.

## Anti-Pattern 3: Treating region as a detail

The connection is regional. The Salesforce instance's region and the cloud provider
region hosting the endpoint service must line up, and this is discovered at the point
where the setup step refuses rather than at design time.

❌ Provision the endpoint service wherever the rest of the estate lives, then start on
the Salesforce side.
✅ Determine the org's instance and region first — Setup → Company Information, and the
Salesforce Trust status page for the instance — then provision the endpoint service in
the matching region. Reprovisioning an endpoint service in a different region is a
straightforward change on the cloud side and an awkward one on the contractual side.

## Anti-Pattern 4: Leaving the Named Credential pointed at the public hostname

The most common "it's configured but nothing changed" outcome. Private Connect provisions
private DNS, but nothing rewrites your existing configuration. The Named Credential still
holds the public hostname, so the callout still resolves publicly, still works, and gives
no signal at all that the private path is unused.

**Wrong** — the private link is provisioned and idle:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<NamedCredential xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Partner API</label>
    <endpoint>https://api.partner.example.com</endpoint>
    <generatedAuthorizationHeader>false</generatedAuthorizationHeader>
    <namedCredentialType>SecuredEndpoint</namedCredentialType>
</NamedCredential>
```

**Right** — the endpoint is the private DNS name issued when the connection was
provisioned:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<NamedCredential xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Partner API (Private Connect)</label>
    <endpoint>https://api-partner.privatelink.internal.example.com</endpoint>
    <generatedAuthorizationHeader>false</generatedAuthorizationHeader>
    <namedCredentialType>SecuredEndpoint</namedCredentialType>
    <parameters>
        <parameterName>Url</parameterName>
        <parameterType>Url</parameterType>
        <parameterValue>https://api-partner.privatelink.internal.example.com</parameterValue>
    </parameters>
</NamedCredential>
```

Because the public hostname keeps working, the only reliable check is on the far side:
confirm the request arrived through the endpoint service, not that the callout returned
200.

## Anti-Pattern 5: Assuming the private path replaces the access controls

Private Connect changes the path traffic takes. It does not authenticate anyone, and it
does not remove any other control. Assistants describe it as a security boundary and
teams relax the ones that were doing the actual work.

❌ "Traffic is private now, so we can drop the IP restrictions and simplify the auth."
✅ Private Connect is one control among several and composes with the rest. Network
access restrictions, Connected App policy, certificate authentication and the endpoint
service's own allow-list all continue to apply, and each still has to be configured. The
property you gained is that packets do not traverse the public internet, not that callers
are trusted.

## Anti-Pattern 6: Verifying by calling the endpoint

A successful callout proves reachability, which was never in question — the public route
also works. Assistants generate a probe that asserts `200` and declare the migration
complete, and the private link sits unused and billed.

❌ `Assert.areEqual(200, res.getStatusCode());` as the acceptance test.
✅ Verify on the receiving side, where the two paths are actually distinguishable: the
endpoint service's connection metrics show traffic, and the application's access log shows
the source as the private endpoint rather than a public egress address. Then, as a
negative test, remove the public route or block the public source range and confirm the
callout still succeeds. Only the negative test proves which path is carrying the traffic.

## Anti-Pattern 7: Debugging a name-resolution failure as a firewall problem

The characteristic failure after a partial cutover is a callout that fails intermittently
or resolves to the wrong address, and teams spend days on security-group rules. The
symptom set is narrow enough to diagnose directly.

- `System.CalloutException: Unauthorized endpoint, please check Setup->Security->Remote
  site settings` — nothing to do with Private Connect. The host is not authorised, which
  is a Setup problem regardless of path.
- A callout that succeeds but the partner never sees on the private endpoint — the
  Named Credential still carries the public hostname (anti-pattern 4).
- A callout that times out only from Salesforce while succeeding from your own network —
  the return route. Private Connect provisions the path in; your VPC route tables and
  security groups still have to permit the response back, and this is the step most often
  missed because the outbound half succeeded.
- Setup refusing the connection at creation — region mismatch (anti-pattern 3).
