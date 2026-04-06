# Well-Architected Notes — Customer Effort Scoring

## Relevant Pillars

- **Reliability** — A CX measurement strategy is only reliable if the survey delivery pipeline is fault-tolerant: null-contact guards, opted-out contact checks, and response cap monitoring must all be in place to prevent silent failures that produce unrepresentative or incomplete data.
- **Operational Excellence** — The measurement strategy must be operationally sustainable: clearly owned, governed with a re-send suppression policy, monitored for response rate health, and connected to a defined escalation path for low-score responses. A strategy that produces data nobody acts on is not operationally excellent.
- **User Experience** — CX measurement directly improves user experience by surfacing friction, dissatisfaction, and disloyalty signals before they result in churn. Choosing the right metric (CES for effort, NPS for loyalty, CSAT for interaction quality) is a prerequisite for producing actionable experience improvement intelligence.
- **Performance** — Survey timing directly affects data quality. CES must fire within 60 minutes of case closure to produce valid effort data. A poorly configured Scheduled Path that delays surveys by 24 hours produces data that is not representative of the customer's actual effort experience, undermining the entire measurement program.
- **Security** — Survey invitations sent to opted-out contacts violate email communication preferences and potentially regulatory requirements (GDPR, CAN-SPAM). The `HasOptedOutOfEmail` check is both a data integrity measure and a compliance requirement.

## Architectural Tradeoffs

**Metric depth vs. respondent burden.** The more metrics you collect per interaction, the richer the dataset — but each additional survey lowers response rates for all surveys. The Well-Architected approach is to be intentional: select the single metric that best answers the primary business question per interaction type. For most orgs, that means CES for transactional support interactions and NPS for periodic relationship health measurement.

**Real-time integration vs. batch reporting.** Connecting `SurveyResponse` data to CRM Analytics enables real-time dashboards but requires the Growth or Enterprise Feedback Management license tier and CRM Analytics licensing. For orgs without CRM Analytics, standard report types on `SurveyInvitation` joined to `SurveyResponse` provide adequate operational reporting at no additional license cost. Choose the reporting approach that matches the license investment the org has already made — do not recommend CRM Analytics dashboards to an org on the Starter tier.

**Survey completeness vs. response rate.** Longer surveys produce richer data but lower response rates. A 3-question CES survey (effort question + one follow-up + one NPS tack-on) consistently outperforms a 1-question survey on data richness, but the response rate typically drops by 8–12 percentage points compared to a single-question survey. For orgs with low baseline response rates (under 15%), start with a 1-question survey to establish the baseline, then experiment with a second question after response rate stabilizes.

## Anti-Patterns

1. **Metric shopping — picking a metric based on what produces the best-looking score.** Some orgs try CSAT, find the scores "too low," then switch to NPS, find the NPS "too negative," then move to CES hoping for a better result. This produces no benchmark continuity and no actionable insight. The Well-Architected approach is to select a metric based on the business question it answers, document the selection rationale, and maintain it consistently for at least 6 months to establish a meaningful baseline.

2. **Disconnected measurement — collecting scores but never connecting them to operational data.** A CES score of 2.8 out of 7 is an alarm signal. But without linking that score to the case, the agent, the case type, or the product area, it is impossible to know what to fix. Always design the response-to-case linkage before deploying the survey, not as an afterthought after data has been collected without the linkage field populated.

3. **Ignoring the license cap until it breaks production sends.** Treating the Feedback Management response cap as an infinite resource and only discovering the cap when survey sends silently stop mid-month is a common operational failure. The capacity plan for the measurement program must include a monthly volume projection and a defined monitoring cadence — at minimum, a weekly check of responses consumed vs. cap.

## Official Sources Used

- Salesforce Feedback Management Overview — https://help.salesforce.com/s/articleView?id=sf.feedback_management_overview.htm
- Set Up Customer Feedback Survey — https://help.salesforce.com/s/articleView?id=sf.feedback_management_setup.htm
- Service Insights CSAT Dashboard — https://help.salesforce.com/s/articleView?id=sf.service_insights_csat_dashboard.htm
- Salesforce Surveys Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.surveys.meta/surveys/surveys_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
