# Well-Architected Notes — AML/KYC Process Architecture

## Relevant Pillars

- **Security (Trusted)** — The most directly applicable pillar. AML/KYC architecture handles regulated personal data and financial crime risk. Key requirements: Named Credentials for vendor authentication (no hardcoded secrets), minimum-necessary access on integration user profiles, field-level security on `PartyProfileRisk` fields to restrict who can read risk ratings, and audit trail design that satisfies regulatory examination. A compliance gap in the security design is not merely a technical debt item — it is a regulatory liability.

- **Reliability** — Screening vendor API availability is outside Salesforce's control. The architecture must be designed to handle vendor timeouts, rate-limit errors (HTTP 429), and service outages without corrupting the `PartyProfileRisk` state or silently skipping screening for a customer. Retry strategy, dead-letter queue design, and fallback behavior (block onboarding if screening cannot complete? Allow with manual review flag?) must be explicitly documented.

- **Operational Excellence** — AML programs require demonstrable operational controls: evidence that every customer was screened, records of every screening decision and any override, and periodic review schedules with SLAs. The architecture must produce an audit trail as a first-class output — not as an afterthought. `PartyProfileRisk.RiskReviewDate` drives periodic review; the operational model must include a process for reviewing the queue of overdue reviews.

- **Performance** — Screening at scale hits Salesforce governor limits quickly. Synchronous callout limits (100 per transaction, 10-second timeout) and batch callout rate limits from screening vendors require the architecture to be designed around throughput from the start. Retrofitting an asynchronous pattern onto a synchronous implementation is a major rework.

- **Adaptability** — Regulatory requirements change: new sanctions lists, updated FATF guidance, changes to PEP criteria. The architecture should isolate the vendor integration contract (the Integration Procedure or Apex callout layer) from the risk scoring logic (the Apex scoring class or CRM Analytics model) so either can be updated independently when regulations or vendor APIs change.

---

## Architectural Tradeoffs

**Synchronous vs. Asynchronous Screening**

The primary tradeoff is between immediacy and scale. Synchronous screening (OmniStudio Integration Procedure in an OmniScript step) gives the agent immediate feedback and a natural decision point before the customer record is activated. It is the right choice for guided onboarding at moderate volume. Asynchronous screening (Batch Apex + Platform Events) is the only viable architecture for portfolio re-screening at scale. The two patterns are not mutually exclusive — an org can use synchronous screening for new onboarding and asynchronous re-screening for the annual review cycle.

**Rule-Based Risk Scoring vs. CRM Analytics Model**

Rule-based Apex scoring is simpler, deterministic, and fully auditable — a regulator can read the scoring logic and understand exactly how a risk rating was produced. CRM Analytics scoring can incorporate more variables and adapt to data patterns, but requires more governance to ensure the model output meets regulatory explainability standards. For most AML programs, rule-based Apex is the correct default unless the institution has a mature data science practice and explicit regulatory approval for model-based risk rating.

**Vendor Managed Package vs. Raw REST Integration**

Some screening vendors (Refinitiv, LexisNexis) offer Salesforce managed packages that install their own objects and workflows. These packages simplify the initial integration but create a dependency on the vendor's object model. If the institution changes vendors, the managed package objects may need migration. A raw REST integration via Integration Procedure or Apex is more portable but requires more implementation effort. Document this tradeoff in the architecture decision record.

---

## Anti-Patterns

1. **Screening on record save via synchronous Flow callout** — Triggers the callout inside the saving transaction, which breaks on bulk operations and makes the record save dependent on vendor API availability. This anti-pattern is common because it seems simple to implement. It creates a brittle architecture that fails silently for bulk imports and produces confusing errors. Always decouple the callout from the save transaction.

2. **Storing vendor API credentials in Custom Metadata or Custom Labels** — Custom Metadata and Custom Labels are accessible to all authenticated users who can query the org's metadata. AML screening vendor credentials stored here are visible to any developer or admin with Apex execution access. Always use Named Credentials with External Credential policies for vendor authentication.

3. **Using FSC Identity Verification as the AML screening mechanism** — Covered in detail in gotchas.md. This is architecturally incorrect and creates a regulatory compliance gap that is invisible in functional testing. It must be explicitly called out in every FSC AML architecture review.

4. **Omitting the audit trail from the architecture** — Designing the screening integration and risk scoring without designing the audit trail simultaneously. Regulators require evidence of every screening decision, every risk rating change, and every manual override. Adding audit trail after the fact typically requires rework of the data model and the orchestration layer. Treat the audit trail as a first-class architectural requirement from day one.

---

## Official Sources Used

- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Integration Patterns Guide — https://architect.salesforce.com/docs/architect/fundamentals/guide/integration-patterns.html
- Financial Services Cloud Developer Guide: Identity Verification — https://developer.salesforce.com/docs/atlas.en-us.financial_services_cloud_object_reference.meta/financial_services_cloud_object_reference/fsc_fields_PartyProfileRisk.htm
- Salesforce Apex Developer Guide: Apex Callouts — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_callouts.htm
- Salesforce Platform Events Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/platform_events_intro.htm
- Named Credentials and External Credentials — https://help.salesforce.com/s/articleView?id=sf.named_credentials_about.htm
- Salesforce Well-Architected: Trusted Pillar — https://architect.salesforce.com/docs/architect/well-architected/guide/trusted.html
