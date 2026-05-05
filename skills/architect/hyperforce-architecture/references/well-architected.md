# Well-Architected Notes — Hyperforce Architecture

## Relevant Pillars

- **Reliability** — Hyperforce changes the reliability surface in two ways. Platform-level cross-region failover becomes Salesforce-managed within the chosen region's pairing; customer-controllable failover does not. The HA/DR architecture must be re-grounded after migration: any document that assumed First-Gen Salesforce-owned data centers is wrong post-migration. Reliability gains include automatic regional redundancy and faster patching cadence; reliability constraints include reduced visibility into the underlying cloud-provider regions' incidents (the customer sees the Salesforce status page, not the AWS / Azure / GCP regional dashboard directly).
- **Security** — Region selection is a primary input to data-residency posture. Network controls shift: Hyperforce IP ranges are cloud-provider-owned CIDRs; customer firewalls and allowlists must be updated. Private Connect (Hyperforce-only) eliminates public-internet exposure for AWS- or Azure-hosted dependencies, which is an unlock the architecture decision record should call out.
- **Operational Excellence** — The migration itself is an operational-excellence event: pre-migration inventory, post-migration validation, architecture decision record. Post-migration, operational schedules (Data Export, scheduled jobs, sandbox refreshes) may need re-pinning. The discipline of treating it as a project (with named owners and checklists) is the difference between a clean cutover and 8 hours of firefighting.

Performance and Scalability are not central to this skill — Hyperforce's platform-level scaling is invisible to most customer architecture decisions. User-perceived latency may improve (closer cloud-provider region) or worsen (more egress hops if integrations didn't move), but the architecture levers are integration topology, not Hyperforce itself.

## Architectural Tradeoffs

### Single-org single-region vs multi-org multi-region

| Dimension | Single-org single-region | Multi-org multi-region |
|---|---|---|
| Data residency posture | One residency stance globally | Per-org residency to match jurisdictions |
| Cross-region UX | Latency penalty for distant users | Lower latency per region |
| Reporting / aggregation | Unified inside one org | Cross-org via CRM Analytics, Data Cloud, middleware |
| Operational complexity | One org to govern | N orgs to govern; metadata sync needed |
| When to choose | Single market, residency obligations are uniform | Multiple markets with diverging residency obligations |

Hyperforce orgs are single-region by definition. "We have multiple regions" is a multi-org architecture question, not a Hyperforce question. See `architect/multi-org-strategy`.

### Salesforce-initiated vs customer-elected migration

| Dimension | Salesforce-initiated | Customer-elected |
|---|---|---|
| Trigger | Salesforce notification with proposed window | Customer requests via engagement / contract |
| Schedule control | Negotiable within proposed band | Customer sets timeline |
| Migration assistance | Bundled engagement | Negotiated engagement |
| Cost | Included in subscription | May involve professional services |
| Region choice | Default region (Salesforce decides) | Customer chooses |

Most customers experience Salesforce-initiated migrations. Customer-elected is the path for new-region landings and feature-blocked workloads.

### Region pairing for failover

Hyperforce regions pair for cross-region failover. The pairing is Salesforce-managed; customers cannot mix-and-match pairings or trigger failover. Region selection should consider both the primary region (residency, latency) and the pairing region (compliance posture of the failover destination, since customer data may temporarily reside there during a regional event).

For workloads where the failover region's residency posture matters (e.g., EU customer data must not transit to a non-EU region during failover), confirm the pairing meets the obligation before locking in the region.

## Anti-Patterns

1. **Treating Hyperforce migration as a Salesforce-only operational event** — the customer side has more pre-cutover work (IP allowlists, communication, validation plan) than the Salesforce side. Architectures that under-resource the customer's project end up firefighting on cutover day.
2. **Confusing residency with sovereignty** — Hyperforce regions deliver at-rest residency. Sovereignty (legal-process scope) is a separate compliance layer. Architecture decision records that conflate the two ship a compliance gap.
3. **Assuming customer-controllable cross-region failover is available** — Hyperforce manages failover at platform level. Customer architectures that depend on triggered or orchestrated failover need to live in multi-org territory, not single-org.
4. **Sequencing Hyperforce-only features before the migration completes** — Private Connect, regional Data Cloud capabilities, regional Einstein/Agentforce models all gate on Hyperforce. Promising delivery dates that ignore the migration dependency produces stalled projects.

## Official Sources Used

- Hyperforce Overview — https://help.salesforce.com/s/articleView?id=sf.hyperforce_overview.htm&type=5
- What is Hyperforce — https://www.salesforce.com/news/stories/what-is-hyperforce/
- Hyperforce Migration Help — https://help.salesforce.com/s/articleView?id=000389060&type=1
- Salesforce Trust — Hyperforce Status — https://status.salesforce.com
- Hyperforce IP Allowlisting (Knowledge Article) — https://help.salesforce.com/s/articleView?id=000389005&type=1
- Private Connect Setup — https://help.salesforce.com/s/articleView?id=sf.private_connect.htm&type=5
- Salesforce Well-Architected Framework Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Well-Architected — Trusted (residency / compliance) — https://architect.salesforce.com/well-architected/trusted/overview
- Salesforce Government Cloud — https://www.salesforce.com/government/government-cloud-plus/
