# Well-Architected Notes — Change Advisory Board Process

## Relevant Pillars

- **Security** — The primary pillar. CAB governance directly enforces Intentional Governance and least-privilege access control principles. Changes to Profiles, Permission Sets, Sharing Rules, and integrations must pass through an approval gate precisely because these changes alter the security posture of the org. The Well-Architected framework principle of "know who can do what and why" depends on controlled, audited change processes.
- **Operational Excellence** — The CAB process is a core Operational Excellence mechanism. The Salesforce Well-Architected framework emphasizes that mature operations require defined change control, deployment runbooks, and post-implementation reviews. A poorly governed change process directly causes unplanned outages and data integrity incidents.
- **Reliability** — Change is the leading cause of production incidents in Salesforce orgs. A structured CAB process with mandatory rollback planning reduces the blast radius of failed deployments and provides the documented procedures necessary for rapid recovery.
- **Performance** — Less directly applicable, but large Flow deployments and sharing rule recalculations triggered by changes can cause performance degradation. The CAB review step is an appropriate place to flag any planned changes that could trigger org-wide sharing recalculations or Apex bulk processing spikes.
- **Scalability** — The CAB process itself must scale with org complexity. A process designed for 10 deployments per month may create a governance bottleneck when the org matures to 50 deployments. The Well-Architected principle of designing for the expected scale applies to governance processes, not just technical architecture.

## Architectural Tradeoffs

**Speed of delivery vs. rigor of review:** A heavier CAB process (weekly board meeting, multi-week advance notice) provides thorough review but slows delivery. A lighter process (async approvals, 24-hour turnaround for Normal changes) maintains speed but requires more discipline from individual approvers. The right balance depends on regulatory context and org change volume. Start with async approvals for Normal changes and synchronous CAB meetings only for changes affecting the security model or external integrations.

**Automated gate vs. procedural enforcement:** An automated pipeline gate (the deployment tool calls the ITSM API) provides hard enforcement but requires ITSM integration effort. A procedural gate (approvers are responsible for verifying tickets before clicking Deploy) is faster to implement but relies on human compliance and will degrade under pressure. For regulated industries, automated gates are non-negotiable. For smaller organizations, procedural enforcement with compensating controls (deployment logs, ITSM audit) is a reasonable starting point.

**Broad CAB scope vs. tiered exemptions:** Including every change type in the CAB process creates overhead that drives teams to either route around the process or classify everything as Standard to avoid it. Tiering (Standard / Normal / Emergency) with clear criteria per tier maintains governance rigor for high-risk changes while keeping the process frictionless for low-risk routine changes.

## Anti-Patterns

1. **Single-Tier CAB (Everything Needs Approval)** — Treating every Salesforce change — including dashboard edits, report updates, and trivial configuration — as requiring full CAB approval. This creates a governance bottleneck that either slows delivery to a crawl or causes teams to route around the process informally. Instead, maintain explicit Standard change pre-authorization for low-risk, repeatable changes so the CAB review budget is reserved for high-risk changes that genuinely need it.

2. **Platform-Internal Approval Process as CAB Gate** — Using a Salesforce Approval Process or a custom `Deployment_Request__c` object as the enforcement mechanism for CAB approvals. This creates a false sense of governance: the Salesforce org cannot gate its own deployment pipeline. A developer with CLI access can deploy to production regardless of any object state inside the org. CAB gates must live in the deployment toolchain and check an external ITSM system.

3. **No Rollback Requirement** — Approving changes through CAB without requiring a documented and tested rollback procedure. When a deployment fails in production, the absence of a rollback plan converts a recoverable incident into an extended outage. The CAB change ticket must require a rollback procedure, and the Normal change review must explicitly confirm that the rollback has been validated in sandbox.

## Official Sources Used

- Salesforce Well-Architected — Intentional Governance: https://architect.salesforce.com/well-architected/easy/intentional
- Salesforce DevOps Center Overview: https://help.salesforce.com/s/articleView?id=sf.devops_center_overview.htm
- Salesforce Help — Getting Started: Governance: Change Management (Article 000388899): https://help.salesforce.com/s/articleView?id=000388899
- Salesforce Trust Calendar (upgrade schedule): https://trust.salesforce.com
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Metadata API Developer Guide: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
