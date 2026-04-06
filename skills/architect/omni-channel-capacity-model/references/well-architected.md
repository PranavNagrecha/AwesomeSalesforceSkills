# Well-Architected Notes — Omni-Channel Capacity Model

## Relevant Pillars

- **Scalability** — The capacity model must scale with agent headcount, channel additions, and volume growth. Poorly tuned weights or rigid skills matrices break down when volumes increase by 2-3x during seasonal peaks. A well-designed model uses overflow routing and broad secondary skills to absorb spikes without architecture changes.
- **Reliability** — Capacity misconfigurations cause cascading failures: overloaded agents abandon items, queue wait times spike, customers retry creating duplicate cases, and the system enters a death spiral. Reliable capacity design includes buffer capacity, overflow paths, and monitoring thresholds that trigger alerts before queues back up.
- **Operational Excellence** — Capacity models require ongoing tuning. Average handle times change as products evolve, agent skill levels shift with turnover, and seasonal patterns repeat annually. Operational excellence means building dashboards, review cadences, and adjustment procedures into the capacity model from day one rather than treating the initial design as permanent.

## Architectural Tradeoffs

1. **Simplicity vs. precision in channel weights.** Fewer weight tiers (e.g., Light=3, Medium=5, Heavy=10) are easier to communicate and maintain. More granular weights (e.g., Chat=2, Messaging=3, Case=5, Complex Case=7, Voice=10) model reality more accurately but increase configuration surface area and the risk of misconfiguration. Start simple and add granularity only when monitoring data shows the simple model is inadequate.

2. **Specialist depth vs. overflow flexibility.** Deep specialization (many narrow skills, few agents per skill) produces better first-contact resolution for the specific skill but creates bottleneck risk. Broad generalization (fewer skills, more agents per skill) reduces bottleneck risk but may lower resolution quality. The recommended balance is specialist-primary with generalist-overflow: route to specialists first, overflow to cross-trained generalists after a timeout.

3. **Agent autonomy vs. system control.** Giving agents many Presence Status options (Available - Chat Only, Available - Cases Only, Available - All) provides flexibility but complicates capacity planning — if too many agents switch to "Chat Only" during a case volume spike, cases queue up. Restricting statuses to fewer options (Available, Break) simplifies planning but reduces agent ability to manage their own workload. Balance by limiting status options to 3-4 well-defined modes with clear usage guidelines.

## Anti-Patterns

1. **One-size-fits-all capacity** — Setting all Service Channel weights to 1 and relying on tab count to manage load. This treats a phone call the same as a chat message, leading to agent overload and customer dissatisfaction. Use differentiated weights that reflect real effort per channel.

2. **Skills without overflow** — Assigning narrow skills to small agent groups with no secondary routing path. When those agents are unavailable, work items queue indefinitely while generalist agents sit idle. Always pair skill-based primary routing with a timeout-triggered overflow to a broader agent pool.

3. **Set-and-forget capacity tuning** — Deploying a capacity model based on initial estimates and never revisiting it. Handle times, channel mix, and agent proficiency change over time. Without quarterly reviews of capacity metrics (overflow rate, average wait time, agent utilization), the model drifts from reality and service levels degrade.

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Omni-Channel Overview — https://help.salesforce.com/s/articleView?id=sf.omnichannel_intro.htm
- Service Presence Introduction — https://help.salesforce.com/s/articleView?id=sf.service_presence_intro.htm
