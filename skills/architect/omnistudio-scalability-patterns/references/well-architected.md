# Well-Architected Notes — OmniStudio Scalability Patterns

## Relevant Pillars

### Scalability

This is the primary pillar for this skill. OmniStudio scalability requires explicit architectural decisions at the Integration Procedure level before high-volume portal deployments go live. The platform does not auto-scale around governor limits or concurrent Apex capacity constraints — both require design-time choices.

Key scalability design rules:
- Queueable Chainable must be selected for IP steps that exceed governor limits under load, not applied reactively after incidents
- The 25-concurrent-long-running-Apex limit (requests > 20 seconds) must be a design input for any portal expecting more than 50 concurrent active sessions
- Direct Platform Access (Spring '25+) should be evaluated for all read-heavy Integration Procedures on LWR sites before go-live
- IP-level caching capacity must be sized against peak concurrent request rates for reference data; cache TTL is a scalability parameter, not just a data-freshness preference
- LWR + CDN is a binary prerequisite for Experience Cloud scalability — not optional

### Performance

High-concurrency OmniStudio deployments have a performance dimension distinct from single-session optimization:
- Under concurrency, governor limit consumption per session is additive org-wide, not isolated
- DPA reduces Apex CPU consumption at the session level, which multiplies across hundreds of concurrent sessions into meaningful overall platform headroom
- DataRaptor Extract caching reduces database round-trips org-wide, not just per user

### Reliability

Reliability under high concurrency is primarily threatened by the 25-concurrent-long-running-Apex limit and governor limit violations:
- When the concurrent Apex ceiling is reached, requests do not gracefully degrade — they error. OmniScripts that invoke IPs hitting this ceiling surface as unexplained failures to users
- Governor limit errors in async contexts (fire-and-forget) are harder to surface and may go unmonitored
- MuleSoft escalation criteria should be documented before go-live as a reliability commitment: at what threshold does the team move orchestration out of OmniStudio?

### Operational Excellence

- Monitor concurrent long-running Apex request count in Setup > Apex Jobs during peak portal hours, not just during testing
- Establish alerts on Apex concurrency metrics before go-live
- Include cache TTL review in the release management process — reference data TTLs that made sense at launch may become stale after data model changes
- Document async execution mode choices (fire-and-forget vs. Queueable Chainable) in the integration architecture decision record

## Architectural Tradeoffs

**Queueable Chainable vs. synchronous execution:** Queueable Chainable escapes governor limits but introduces asynchronous latency. The OmniScript UI must handle a polling or callback pattern to surface results. This adds UX complexity and requires error handling for queue depth scenarios (Queueable jobs queue; they do not guarantee immediate execution).

**IP-level caching vs. data freshness:** Higher cache TTLs reduce database load and governor consumption under concurrency. Lower TTLs maintain data accuracy for transactional data. There is no universal correct TTL — it is a business decision, not a technical one.

**OmniStudio Integration Procedures vs. MuleSoft:** Integration Procedures share the Salesforce governor pool. At extreme scale, this is a fundamental architectural constraint that caching and async modes can mitigate but not eliminate. MuleSoft runs on dedicated compute outside the Salesforce governor model. The escalation point is a design decision that should be documented before peak load events, not discovered in production.

**LWR migration cost vs. scalability requirement:** LWR + CDN is mandatory for high-volume portals but migrating an existing Aura site to LWR is a non-trivial effort. The tradeoff must be surfaced during architecture review, not deferred to post-go-live optimization.

## Anti-Patterns

1. **Async mode as a universal fix** — applying fire-and-forget or Queueable Chainable to all Integration Procedures regardless of whether they actually face governor limit pressure. This adds latency and UX complexity without architectural benefit for low-complexity IPs.
2. **Caching user-specific data at the IP level** — enabling IP-level caching on Integration Procedures that return account-specific or user-specific data. This can cause data leakage between users and is a security and compliance risk, not just a data integrity issue.
3. **Deploying a high-volume portal on Aura** — launching an Experience Cloud portal expected to serve hundreds of concurrent users without first migrating to LWR and enabling CDN. Performance degradation under load is predictable and avoidable at design time.

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- OmniStudio Integration Procedures Help — https://help.salesforce.com/s/articleView?id=sf.os_integration_procedures.htm
- OmniStudio Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.omnistudio_dev_guide.meta/omnistudio_dev_guide/
- Salesforce Governor Limits Reference — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_gov_limits.htm
- Experience Cloud LWR Sites — https://help.salesforce.com/s/articleView?id=sf.exp_cloud_lwr_intro.htm
