# Well-Architected Alignment — Technical Debt Assessment

## Relevant Pillars

### Operational Excellence

The Salesforce Well-Architected Operational Excellence pillar governs maintainability, deployability, and observability — the three qualities that technical debt most directly erodes.

**Maintainability:** Technical debt accumulates when the team cannot confidently change the system. Dead Apex classes, over-complex Flows with 100+ elements, and Workflow Rules that nobody owns are all maintainability liabilities. The team avoids touching them because the blast radius is unknown. A technical debt assessment restores the team's ability to reason about the system by making the hidden complexity visible and bounded.

**Deployability:** Deployment failures caused by stale Apex (broken references, zero coverage dragging org below 75%), hardcoded IDs that differ between sandbox and production, and deprecated metadata are Operational Excellence failures. They are not one-off incidents — they are structural debt that repeats as a failure on every deployment until resolved.

**Observability:** Dead automation that still executes (active Workflow Rules presumed replaced by Flows, Process Builder flows overlapping with Record-Triggered Flows) creates ghost behavior: the system does things that are not visible in the current documentation or the current team's knowledge. Technical debt assessment makes this visible so that observability can be restored.

**WAF Operational Excellence questions applied to technical debt:**
- Can a new developer understand and safely modify the automation on this object? (Automation overlap and complexity debt answer "no.")
- Will the next deployment to this org succeed without manual intervention? (Coverage debt, hardcoded IDs, and broken formula fields answer "no.")
- When something breaks in production, is there enough context to diagnose it quickly? (Dead code and undocumented automation answer "no.")

### Reliability

The Salesforce Well-Architected Reliability pillar governs correct behavior under normal and abnormal conditions. Technical debt undermines reliability through several mechanisms:

**Automation overlap as a reliability failure:** When a Record-Triggered Flow and an Apex trigger both write the same field on the same object, the final value is determined by execution order — and that order can shift if any automation is added, modified, or reordered on the object. This is a latent reliability failure: it works today because the current order produces the desired result, but it will break silently when the order changes. Identifying and resolving overlap is a reliability improvement.

**Governor limit exposure from complexity debt:** Flows with 100+ elements that are approaching the 2,000-element interview limit, and Apex classes that consume significant CPU or SOQL budget, create latent governor limit failures. These classes and flows will pass in sandbox testing (low data volume) and fail in production (full data volume and concurrent transactions). Complexity debt quantification directly predicts governor limit risk.

**Silent failure from dead code:** Apex classes that are present but untested can contain bugs that are dormant until a code path is triggered. Zero-coverage Apex is not just a hygiene issue — it is code whose behavior under failure conditions is entirely unknown.

**WAF Reliability questions applied to technical debt:**
- What happens when two automations both update the same field? (Overlap debt: the answer is non-deterministic.)
- Is the failure observable? (Dead automation: the answer is often "no — the failure is silent.")
- Can the system recover? (Coverage debt: if the error-handling code has 0% coverage, it has never been tested in error conditions.)

---

## Architectural Anti-Patterns Addressed

1. **Automation strata accumulation** — Adding new automation layers without retiring the old ones creates a historical sediment of conflicting behavior. Each layer was correct when written; together they are unreliable. Periodic assessment and cleanup is a reliability practice, not just a housekeeping exercise.

2. **Coverage theater** — An org at exactly 75% coverage that achieves that number by having many small test methods with no assertions has passed the deployment gate but has no actual test reliability. Dead Apex with zero coverage erodes even this floor. Coverage debt assessment distinguishes meaningful tests from coverage-theater.

3. **The "we'll clean it up later" trap** — Inactive Flow versions, unused permission sets, and Process Builder flows left in place after migration are all examples of debt deferred with the intention of returning. The assessment turns "later" into a dated, severity-rated backlog item — giving it a home and an owner.

---

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html — primary authority for Operational Excellence and Reliability pillar definitions and quality framing
- Apex Developer Guide: Code Coverage — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_testing_code_coverage.htm — authoritative source for coverage requirements, deployment thresholds, and how coverage is calculated per class
- Flow Considerations (Salesforce Help) — https://help.salesforce.com/s/articleView?id=sf.flow_considerations.htm — Flow governor limits including the 2,000 Flow version limit, element limits, and callout restrictions that underpin the automation debt findings
- Apex Developer Guide: Order of Execution — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers_order_of_execution.htm — authoritative execution sequence for triggers, Flows, Workflow Rules, and validation rules that underpins automation overlap analysis
