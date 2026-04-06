# Well-Architected Notes — SLA Design and Escalation Matrix

## Relevant Pillars

### Reliability

SLA design and the escalation matrix are fundamentally a reliability mechanism. A well-designed SLA tier table with correctly mapped milestone thresholds and business hours ensures that every case has a defined, monitored, and enforced commitment window. Cases do not fall through the cracks — the escalation matrix guarantees that the right person is notified before a breach, not after. Reliability is degraded when business hours are misaligned between the entitlement process and escalation rule entries, because the enforcement paths are then running on different clocks.

### Operational Excellence

The escalation matrix document is an operational governance artifact. It makes the intended behavior of the SLA enforcement system explicit, reviewable, and auditable by non-technical stakeholders (support operations managers, account managers, legal). A design without this artifact leaves the enforcement configuration implicit in Salesforce Setup — visible only to admins who know where to look. Operational excellence requires that the SLA design is documented at the level a new support operations manager can understand and act on without a Salesforce login.

### Trustworthiness

Entitlement processes and milestones are visible to customers via the Entitlement and Case Milestone related lists. If a milestone fires incorrectly (wrong tier applied due to ambiguous auto-assignment, or wrong time target due to missing entry criteria), the customer sees inaccurate SLA data. Trustworthiness requires that the tier definition table and auto-assignment logic are designed to eliminate ambiguity — every case must receive the correct entitlement and the correct milestone targets with certainty.

### Security

SLA enforcement inherits the security model of the Case object. Milestone records (CaseMilestone) are child records of Case and respect Case sharing rules. Entitlement records respect Account sharing. Design considerations: ensure that support agents can read their case's milestones (required for SLA awareness), but cannot edit CaseMilestone.CompletionDate (to prevent gaming the SLA clock). Review FLS on the CaseMilestone object as part of the design.

### Scalability

The platform limit of 10 milestones per entitlement process constrains tier design at scale. A design that attempts to track 6+ SLA metrics per case (first response, first resolution, workaround, fix, followup, closure) within a single entitlement process will hit this limit. Design for the 10-milestone ceiling by prioritizing the two most contractually significant milestones per tier-priority combination (typically First Response and Resolution). Use operational escalation rules for secondary tracking rather than adding milestones.

---

## Architectural Tradeoffs

**Tier granularity vs. process complexity:** More tiers (Enterprise, Professional, Basic, Partner, Internal) means more entitlement processes, more milestone configurations, and more escalation rule entries to maintain. Each tier doubles the operational overhead. The Well-Architected principle of "as simple as possible" suggests starting with three tiers maximum and adding tiers only when contractual commitments genuinely differ. Avoid creating a Platinum/Gold/Silver/Bronze/Standard five-tier model if Platinum and Gold have the same response targets.

**Milestone actions vs. escalation rules:** Using milestone actions for both customer-facing SLA notifications and internal operational routing duplicates logic and makes the system harder to change. Keep milestone actions for customer-facing SLA enforcement. Use escalation rules for internal operational safety nets (idle cases, unassigned cases). The two mechanisms complement each other when separated by concern, and conflict when used for the same purpose.

**Business hours granularity:** Configuring one Business Hours record per time zone vs. one per support team creates tradeoffs. Per-time-zone records are simpler but do not account for holidays specific to a regional team. Per-team records are more accurate but multiply maintenance overhead. For most implementations, one record per major operating region (US, EMEA, APAC) is the right balance.

---

## Anti-Patterns

1. **Configuring entitlement processes without a design artifact** — Jumping directly to Setup and entering time values without a tier definition table produces a configuration that cannot be reviewed for correctness, drifts from contractual commitments over time, and cannot be validated during an org audit. The design artifact is not optional documentation — it is the specification.

2. **Using "Default" Business Hours as a shortcut** — The Default record is 24/7 until changed. Referencing it by name in a design gives the false impression that the SLA will honor standard business hours. Always create named Business Hours records with explicit day and time configuration, and verify them in Setup before referencing them in the design.

3. **Attaching the same escalation rule entry to all tiers** — A single escalation rule entry without tier-differentiated criteria will escalate every case at the same time threshold regardless of tier. Enterprise P1 and Basic P4 cases will escalate at the same elapsed time. This is operationally meaningless and floods managers with irrelevant notifications. Design separate escalation rule entries per tier with criteria that match on Entitlement.Name or Account's support tier field.

---

## Official Sources Used

- Salesforce Help: Entitlements Overview — https://help.salesforce.com/s/articleView?id=sf.entitlements_overview.htm
- Salesforce Help: Milestones — https://help.salesforce.com/s/articleView?id=sf.entitlements_milestone_overview.htm
- Salesforce Help: Set Up Entitlement Processes — https://help.salesforce.com/s/articleView?id=sf.entitlements_process_setup.htm
- Salesforce Help: Business Hours — https://help.salesforce.com/s/articleView?id=sf.customize_businesshours.htm
- Salesforce Help: Set Up Case Escalation Rules — https://help.salesforce.com/s/articleView?id=sf.customize_escalation.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/well-architected/overview
