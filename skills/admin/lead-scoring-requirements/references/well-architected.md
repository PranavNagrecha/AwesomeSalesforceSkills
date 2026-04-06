# Well-Architected Notes — Lead Scoring Requirements

## Relevant Pillars

- **Operational Excellence** — The primary pillar. A well-designed scoring model creates a repeatable, documented process for moving leads through the funnel. It includes explicit thresholds, a signed-off SLA, and a feedback loop (recycle tracking, SQL acceptance rate) that enables continuous improvement. Without operational rigor, the model degrades silently as ICP and market conditions evolve.
- **Reliability** — Scoring automation must work correctly at scale. Record-triggered Flows that recalculate scores on every save are a reliability risk at high lead volume. The model must be designed with governor limits in mind: either use before-save Flows for lightweight calculations, or schedule batch recalculation to avoid per-record overhead compounding during bulk operations.
- **Security** — Lead data frequently contains PII (email, phone, company, job title). Field-level security must restrict who can see and edit scoring dimension fields and the `Is_MQL__c` flag. Marketing ops should be able to read scores; only the scoring automation (running Flow user) and admins should be able to write dimension score fields. Sales reps should be read-only on dimension scores to prevent gaming.
- **Performance** — High-frequency record-triggered Flows on the Lead object are a common performance anti-pattern. The scoring model design must explicitly address recalculation frequency and choose a strategy (before-save for creates, scheduled for updates) that does not degrade org performance during list imports or campaign responses.
- **Scalability** — The scoring model field map and automation design should anticipate future dimensions. Adding a new scoring signal (e.g., intent data from a third-party tool) should require adding one numeric field and one Flow element — not redesigning the composite formula. Keeping dimension scores in separate fields (not collapsed into a single computed value) makes the model extensible.

## Architectural Tradeoffs

**Stored Number vs. Formula for Composite Score:** A Formula field for the composite score is zero-maintenance (it always reflects current dimension values) but cannot be used in Flow conditions or Assignment Rules. A stored Number field requires a Flow to maintain it but enables automation routing. The tradeoff is automation reliability vs. maintenance overhead. For any model where the score drives automated routing, the stored Number field is the correct choice.

**Record-Triggered vs. Scheduled Flow for Score Recalculation:** Record-triggered Flow provides real-time scores but creates governor limit risk at scale and fires during bulk loads. Scheduled Flow is safer for high-volume orgs but means scores may be up to 24 hours stale. For most B2B orgs with daily lead volumes under 500, record-triggered is acceptable. Above 500 leads/day or when large list imports are regular, use scheduled recalculation.

**Native Sales Cloud vs. Account Engagement Scoring Engine:** Account Engagement's scoring engine is purpose-built for marketing engagement tracking (email clicks, form fills, page visits) but requires an AE license and is harder to customize for firmographic fit. Native Sales Cloud scoring via Flow is more flexible but requires more implementation effort. The hybrid approach (AE for engagement, CRM Flow for fit, combined in a Salesforce Number field) provides the best of both at the cost of additional sync complexity.

## Anti-Patterns

1. **Single-dimensional MQL threshold** — Defining MQL as a single score threshold with no fit component allows high-engagement non-buyers to flood the sales queue. The correct approach is a two-dimensional model (fit AND engagement) with minimum thresholds on both dimensions before MQL status is granted.

2. **Undocumented handoff SLA** — Implementing the scoring automation without a written, signed-off SLA between marketing and sales creates ambiguity about rep response time expectations and recycle criteria. Without documentation, disputes about lead quality are unresolvable and the model cannot be improved systematically. The SLA is as important as the technical implementation.

3. **Score in a Formula field used for routing** — Using a formula field as the basis for Lead assignment or MQL notification Flows creates silent failures (Flow condition cannot evaluate formula fields at DML time). Always store routing-critical scores in Number fields maintained by automation.

## Official Sources Used

- Salesforce Help — Sample Scoring Calculation Formulas — https://help.salesforce.com/s/articleView?id=sf.leads_scoring_formula.htm
- Salesforce Help — Customize Scoring Rules — https://help.salesforce.com/s/articleView?id=sf.leads_scoring.htm
- Account Engagement Help — Lead Qualification Tips — https://help.salesforce.com/s/articleView?id=sf.pardot_lead_qualification.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
