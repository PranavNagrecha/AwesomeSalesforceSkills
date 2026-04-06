# Well-Architected Notes — Omni-Channel Routing Setup

## Relevant Pillars

- **Reliability** — Omni-Channel routing is a real-time customer-facing system. Misconfigured routing rules or missing Service Resources cause work items to sit unrouted, directly impacting customer wait times and SLA compliance. Reliability in this context means: routing chains are complete, no queue is left without a Routing Configuration, and fallback paths exist for all routing failure scenarios.
- **Operational Excellence** — Routing configuration must be maintainable. As teams grow, change, and reorganize, Presence Configurations, queue memberships, and Service Resource skill assignments must be updated without manual error. Well-documented configuration decisions and a structured change process prevent routing degradation over time.
- **Scalability** — Queue-based routing with a flat single-queue structure does not scale to multi-product, multi-tier support operations. Skills-Based Routing and tiered Routing Configurations with priority levels are the patterns that allow the routing architecture to grow with the business without requiring a full redesign.

## Architectural Tradeoffs

**Queue-Based vs Skills-Based Routing**

Queue-based routing is simpler to configure and easier to reason about — the routing engine only needs to know which queue a work item is in and who is in that queue. The tradeoff is that it places the burden of skill matching upstream: items must be pre-sorted into the correct queues by assignment rules or automation before routing. Any miscategorization or new work type requires queue structure changes.

Skills-Based Routing moves skill matching into the routing engine itself. This is more powerful but has more prerequisites (Skills, Service Resources, Routing Rules, skill assignments) and more failure modes (silent fallback when no agent matches). Skills-Based Routing is the right choice when skill matching is the primary driver of routing quality and queue structures would otherwise become too granular to manage.

**Least Active vs Most Available**

Least Active equalizes the number of open items per agent — it does not account for item weight or agent capacity. Most Available uses the remaining capacity percentage, which accounts for channel weight differences. For single-channel deployments with uniform work items, Least Active is adequate. For multi-channel deployments where work items vary in effort, Most Available better reflects actual agent workload and prevents overloading agents who have a heavy case open alongside several chats.

## Anti-Patterns

1. **One Queue for All Work Types** — Placing all work items into a single queue and using a single Routing Configuration removes the ability to prioritize by work type. A high-priority escalation competes equally with a low-priority routine inquiry. As volume grows, this pattern creates unpredictable wait time distributions. The correct approach is separate queues per priority tier with Routing Configuration priority levels set accordingly.

2. **Skipping Fallback Routing Rules in Skills-Based Deployments** — Deploying Skills-Based Routing without fallback criteria means any work item that does not match a routing rule criteria sits in queue indefinitely without alerting supervisors. This silently degrades SLAs for edge cases (null field values, new product lines not yet covered by rules). Every Skills-Based Routing deployment should include a catch-all fallback routing rule entry and a queue monitor alert for items exceeding the expected wait threshold.

3. **Managing Routing via Apex Triggers Instead of Native Routing Configuration** — Some teams use Apex triggers to set Case.OwnerId directly to a user, bypassing Omni-Channel entirely. This prevents Omni-Channel from managing capacity, tracking agent availability, or providing Omni-Channel Supervisor visibility. Routing logic belongs in Routing Configurations and Skills-Based Routing Rules — not in trigger code.

## Official Sources Used

- Omni-Channel Overview — https://help.salesforce.com/s/articleView?id=sf.omnichannel_intro.htm
- Routing Model Options for Omni-Channel — https://help.salesforce.com/s/articleView?id=sf.omnichannel_routing_model_options.htm
- Skills-Based Routing — https://help.salesforce.com/s/articleView?id=sf.omnichannel_skills_based_routing.htm
- Set Up Omni-Channel — https://help.salesforce.com/s/articleView?id=sf.omnichannel_setup.htm
- Service Presence Introduction — https://help.salesforce.com/s/articleView?id=sf.service_presence_intro.htm
- Create Service Channels — https://help.salesforce.com/s/articleView?id=sf.omnichannel_create_service_channel.htm
- Create Routing Configurations — https://help.salesforce.com/s/articleView?id=sf.omnichannel_create_routing_config.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
