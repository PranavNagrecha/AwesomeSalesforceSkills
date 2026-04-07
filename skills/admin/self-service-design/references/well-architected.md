# Well-Architected Notes — Self-Service Design

## Relevant Pillars

- **Easy** — The primary WAF pillar for self-service portal design. A well-designed self-service portal reduces customer effort by surfacing the right answer before the customer needs to ask. Design choices (search prominence, article titles, zero-results handling) directly determine how easy it is for customers to resolve issues without agent involvement. The Salesforce Well-Architected "Easy" pillar emphasizes designing for outcomes — in self-service, the outcome is customer resolution, not portal engagement.

- **Adaptable** — Self-service portals must adapt to changing contact reason distributions. The design must include a measurement loop (deflection rate by contact reason) that feeds back into article authoring priorities. A portal that cannot adapt its article coverage to new product features, policy changes, or emerging issue types degrades in deflection effectiveness over time. The architecture should support an ongoing article quality review cycle, not a one-time launch.

- **Trusted** — Community peer support introduces trust risk: incorrect answers from community members can mislead customers and increase case volume rather than reducing it. The design must include a moderation workflow and a mechanism for promoting verified answers to canonical Knowledge articles. Peer-contributed content without review creates a trust liability. Internal article governance (article review cycles, publication approval) underpins the trusted self-service experience.

## Architectural Tradeoffs

**Article quality vs. portal UX investment:** Most orgs over-invest in portal UX (search bar design, page layout, branding) and under-invest in article quality. The tradeoff is asymmetric: a high-quality article inventory with a mediocre search UX will deflect more cases than a polished UX with a thin or poorly-titled article set. When budget or time is constrained, prioritize article coverage and title quality before UX design work.

**Friction calibration vs. deflection rate:** Adding friction to the case submission flow increases deflection rate up to a point, then produces diminishing returns as abandonment rises. The optimal friction level is the highest friction level that does not cause measurable abandonment spikes. This is empirically determined — it cannot be set from a design document alone. The architecture should include an A/B testing capability or at minimum a phased rollout with abandonment monitoring before full deployment.

**Community peer support vs. moderation cost:** Peer community Q&A scales the effective knowledge base without internal authoring cost, but it introduces a moderation burden that scales with community activity. Orgs that launch community Q&A as a cost-reduction strategy without resourcing moderation create a trust liability that can increase case volume (customers submitting cases to get correct answers after receiving wrong peer advice). Only recommend community Q&A when moderation capacity is committed.

## Anti-Patterns

1. **Launching self-service before the article baseline is established** — Designing portal UX, configuring deflection components, and announcing the portal to customers before verifying that Knowledge articles are published, channel-assigned, and titled with customer-facing language. The result is a portal with good UX and no deflection, because no relevant articles surface in search. The correct sequence is: article coverage first, UX design second, launch third.

2. **Treating all case form exits as deflections** — Using the Case Deflection component metric without instrumenting form abandonment separately. This masks frustrated abandonment (a failure mode) within the deflection rate metric (a success signal), making the portal appear more effective than it is and masking a friction calibration problem. Always separate deflection (customer found an answer) from abandonment (customer gave up).

3. **Launching community Q&A without seeded content and moderation capacity** — Enabling Experience Cloud Q&A as a self-sustaining peer support channel without pre-seeded content, internal advocate coverage, or a moderation workflow. The result is a ghost town that suppresses customer engagement and contributes zero deflection while creating a visible signal that the portal is not actively maintained.

## Official Sources Used

- Deflect Cases with Self-Service — help.salesforce.com — primary authority for Case Deflection component behavior, Help Center template design, and pre-deflection article surfacing mechanics
- Provide a Self-Service Help Center — Salesforce Help — Help Center template configuration and Knowledge search integration in Experience Cloud
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html — architecture quality framing (Easy, Adaptable, Trusted pillars)
- Self-Help Service and Knowledge Scale — Trailhead — deflection model combining Knowledge article surfacing, Help Center UX, and community peer support; Case Deflection component measurement patterns
