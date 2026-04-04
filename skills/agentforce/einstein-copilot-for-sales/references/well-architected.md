# Well-Architected Notes — Einstein Copilot for Sales

## Relevant Pillars

### User Experience

Einstein Sales AI features (Opportunity Scoring, Pipeline Inspection, EAC, email generation) exist entirely to improve the daily experience of sales reps and managers. User Experience is the primary pillar because a misconfigured or partially-working AI feature that surfaces blank score fields, empty insights panels, or broken email sync creates distrust in AI tooling that is very hard to recover from. The sequence of enablement — data readiness check before enablement, model training before user access, EAC exclusion rules before sync — directly protects the user experience from a broken first impression.

Key UX considerations:
- Opportunity Score and score factors should be visible in the places reps work (record page, list view, pipeline view), not buried in Setup.
- Pipeline Inspection AI insights are manager-facing; ensure forecast managers are the rollout cohort, not individual contributors.
- Einstein email composition surfaces inside the email activity composer; do not add a separate entry point — keep AI help in the workflow.

### Operational Excellence

Operational Excellence governs how the org manages and maintains Einstein Sales AI over time:
- **Model retraining cadence:** Opportunity Scoring retrains weekly. Admins should monitor model AUC metrics monthly to detect drift as win rates, deal cycles, or product mix changes.
- **EAC configuration governance:** EAC configuration profiles should be version-controlled as metadata if possible and reviewed when onboarding new sales teams or roles. Proliferation of poorly-scoped profiles leads to missing activity data.
- **License tracking:** Einstein Generative AI licensing is separate from Einstein for Sales. A formal license audit process prevents surprise gaps when new features are requested.
- **Exclusion rule maintenance:** EAC exclusion domain lists require ongoing maintenance as new partner/vendor domains emerge. A stale exclusion list will allow personal or legal email to sync into Salesforce.

---

## Architectural Tradeoffs

### EAC vs. Manual Activity Logging

EAC reduces the manual data entry burden on reps but introduces a reporting gap: EAC-synced activities are not in standard Activity objects. Orgs that need deep activity reporting must accept either (a) EAC + Einstein Activity Capture report types with limitations, or (b) investing in CRM Analytics datasets that include EAC data. There is no configuration that makes EAC data appear in standard Activity report types.

**Tradeoff decision:** If compliance or coaching programs rely on standard activity reports, validate EAC report capabilities in a full-copy sandbox before committing to EAC as the activity capture strategy.

### Opportunity Scoring vs. Custom Scoring Models

Einstein Opportunity Scoring is a managed ML model that Salesforce trains automatically. It requires no data science resources and no model governance. However, it is a black box — admins can see top field weights but cannot inspect the full model. For orgs with complex sales motions (multi-product, partner vs. direct, long vs. short cycle) the managed model may conflate distinct opportunity types.

**Tradeoff decision:** For orgs with meaningfully different opportunity types, consider whether a single managed scoring model serves all segments. Record Type segmentation can help if Einstein Opportunity Scoring supports per-record-type training (verify in current documentation — this capability has evolved across releases). If high accuracy per-segment scoring is critical, a custom CRM Analytics-based scoring model may be required — this is out of scope for this skill.

---

## Anti-Patterns

1. **Enabling all Einstein Sales AI features simultaneously on Day 1** — Enabling EAC, Opportunity Scoring, Pipeline Inspection, email generation, and Relationship Insights all at once without validating data prerequisites for each creates a situation where half the features silently fail (blank scores, empty insights, no relationship connections). Users lose trust in all of them, not just the ones that failed. Enable sequentially: EAC first (it needs time to accumulate history), then Opportunity Scoring (needs 24–72 hours to train), then Pipeline Inspection and Relationship Insights (which depend on the prior two).

2. **Skipping EAC exclusion domain configuration before rollout** — Enabling EAC without configuring exclusion rules will sync all email correspondence — including personal email, legal communications, and HR conversations — into Salesforce records. This is a privacy and compliance risk. Exclusion rules must be a pre-launch gate, not a post-launch cleanup.

3. **Promising generative email drafting without verifying the Einstein Generative AI license** — Building rep training materials, change management, or business cases around AI email composition before confirming the org has the Einstein Generative AI entitlement creates expensive expectation mismatches at go-live.

---

## Official Sources Used

- Einstein for Sales overview — https://help.salesforce.com/s/articleView?id=sf.einstein_sales.htm
- Einstein Opportunity Scoring — https://help.salesforce.com/s/articleView?id=sf.einstein_opp_scoring.htm
- Einstein Activity Capture — https://help.salesforce.com/s/articleView?id=sf.einstein_activity_capture.htm
- Einstein Copilot for Sales (email and copilot features) — https://help.salesforce.com/s/articleView?id=sf.einstein_copilot.htm
- Agentforce Developer Guide — https://developer.salesforce.com/docs/einstein/genai/guide/agentforce.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
