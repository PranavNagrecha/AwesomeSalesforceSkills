# Well-Architected Notes — Einstein Copilot for Service

## Relevant Pillars

### User Experience

Einstein for Service features exist primarily to reduce agent handle time and improve resolution quality. User Experience is the primary pillar because AI features that surface incorrect case classifications, irrelevant article recommendations, or broken reply suggestions actively harm the agent experience — creating distrust in AI tooling that is very difficult to recover from. The sequencing of enablement — data quality validation before classification model training, article-linking habit before recommendation quality — directly protects the agent experience from a degraded first impression.

Key UX considerations:
- Case Classification suggestions should appear in a component agents can see and act on in their normal case-handling flow. Hidden or hard-to-find AI input is ignored.
- Reply Recommendations must surface quickly during a messaging session. If suggestions appear with noticeable latency, agents will stop looking for them.
- Work Summary and Service Replies should be positioned as agent efficiency tools, not automation that bypasses agent judgment. Agents should be able to edit, reject, or override all AI outputs.
- Einstein Conversation Mining insights are manager-facing and optimization-focused — do not surface them in the agent console.

### Operational Excellence

Operational Excellence governs how the org manages Einstein for Service AI features over time after go-live:
- **Model monitoring:** Case Classification models retrain on a Salesforce-managed schedule. Admins should spot-check classification accuracy monthly, particularly after significant changes to the case intake process or field picklist values.
- **Article base maintenance:** Article Recommendations quality is tied to Knowledge article currency and completeness. A stale or incomplete Knowledge base produces stale recommendations. Schedule Knowledge article reviews as a recurring operational cadence.
- **Training Data refresh for Reply Recommendations:** As agent messaging behaviors evolve, the Training Data corpus ages. Periodically re-run the Training Data job to incorporate recent high-quality agent responses.
- **License tracking:** Einstein Generative AI licensing is separate from Service Cloud Einstein. A formal license audit process prevents surprise gaps when Work Summary or Service Replies are requested by the business.
- **ECM review cadence:** Einstein Conversation Mining insights are only valuable if acted on. Establish a recurring review cadence (monthly or quarterly) where the Service Ops team reviews ECM insights and commits to specific bot or agent workflow improvements.

### Security

Einstein for Service generative AI features (Work Summary, Service Replies) operate on the Einstein Trust Layer. The Trust Layer enforces:
- **Data masking:** Sensitive data fields (PII, payment data) are masked before case content is sent to the LLM, preventing sensitive customer data from appearing in prompts.
- **No data exfiltration:** Salesforce's AI Trust Layer architecture ensures that case content processed by LLMs does not leave Salesforce infrastructure and is not used to train third-party foundation models.
- **Grounding in Knowledge:** Service Replies are grounded in published Knowledge articles, constraining LLM outputs to org-sanctioned content rather than free-form generation.

Admins enabling generative features should review the Einstein Trust Layer configuration before go-live, even if the Trust Layer defaults are acceptable — understanding the default masking rules and audit logging behavior is a security due diligence requirement.

---

## Architectural Tradeoffs

### Case Classification Auto-Populate vs. Suggestion Mode

Einstein Case Classification can be configured to auto-populate fields on case creation or to surface suggestions that agents accept/reject. Auto-populate mode reduces agent effort but eliminates the agent correction feedback loop that improves model accuracy over time. Suggestion mode requires one additional agent click per field but captures agent corrections as training signal and builds trust through transparency.

**Tradeoff decision:** For new implementations, start in suggestion mode. The feedback loop improves model accuracy faster and prevents large-scale routing errors caused by incorrect auto-populated values. Move to auto-populate only after the model has demonstrated consistent accuracy (80%+) over 4–6 weeks of suggestion-mode operation.

### Einstein Auto-Routing vs. Static Omni-Channel Routing Rules

Static Omni-Channel routing rules are deterministic and fully controllable. Einstein Auto-Routing is probabilistic — it performs better as the classification model improves but introduces routing variance in the early model lifecycle. Orgs that need strict SLA compliance and predictable routing behavior may be better served by static rules with incremental AI augmentation rather than full AI-driven routing from day one.

**Tradeoff decision:** Use Einstein Auto-Routing for routing dimensions (e.g., language routing, topic specialty routing) where static rules would require exhaustive maintenance. Keep static rules for the highest-stakes routing paths (e.g., VIP customers, escalation routing) where determinism matters more than efficiency.

### Service Replies Grounding Quality vs. Knowledge Base Investment

Service Replies with Einstein produces AI-drafted responses grounded in Knowledge articles. The quality ceiling of Service Replies is bounded by the quality and coverage of the Knowledge base. Orgs with a thin or outdated Knowledge base will get thin or outdated AI-drafted responses. The feature amplifies whatever quality the Knowledge base already has — it does not compensate for Knowledge gaps.

**Tradeoff decision:** Invest in Knowledge base curation and coverage as a prerequisite for Service Replies enablement, not a follow-up activity. Enabling Service Replies on a weak Knowledge base creates agent distrust (drafts that need heavy editing) and potentially incorrect customer-facing content.

---

## Anti-Patterns

1. **Enabling Auto-Routing simultaneously with Case Classification before the model is validated** — Auto-Routing consumes classification field values in real time. An unvalidated or low-accuracy classification model will produce systematic routing errors at scale. Always validate classification accuracy in suggestion mode before enabling Auto-Routing. See gotchas.md Gotcha 4.

2. **Including Work Summary or Service Replies in project scope without confirming Einstein Generative AI licensing** — These features require a separate license (Einstein 1 Service or Einstein Generative AI add-on). Scoping them without license confirmation creates expectation mismatches at go-live that delay delivery. License confirmation is a day-one project requirement, not a handoff.

3. **Treating Article Recommendation quality as a static outcome of the initial setup** — Recommendation quality is a function of ongoing agent behavior (article linking at case close) and Knowledge base freshness. Orgs that enable Article Recommendations and never revisit them see quality degradation within months. Operational cadences for article maintenance and agent behavior monitoring are required to maintain recommendation value.

4. **Enabling all Einstein for Service features simultaneously on Day 1** — Each feature has its own data prerequisite, training period, and agent adoption requirement. Enabling everything at once means some features will silently fail (insufficient data, missing Training Data job, license gap) while others work correctly. Users cannot distinguish between features that failed due to misconfiguration and features that are working — they distrust all of them. Enable sequentially with a validation gate between each feature.

---

## Official Sources Used

- Einstein for Service overview — https://help.salesforce.com/s/articleView?id=sf.einstein_service.htm
- Einstein Case Classification — https://help.salesforce.com/s/articleView?id=sf.einstein_case_classification.htm
- Einstein Article Recommendations — https://help.salesforce.com/s/articleView?id=sf.einstein_article_recommendations.htm
- Einstein Reply Recommendations — https://help.salesforce.com/s/articleView?id=sf.einstein_reply_recommendations.htm
- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
