# Well-Architected Notes — Salesforce Surveys

## Relevant Pillars

- **Security** -- External survey collection runs under the Guest User Profile, which is one of the most sensitive permission contexts in Salesforce. Granting Read and Create on survey objects to the guest user is necessary but must be scoped carefully. The guest user should not have access to any objects or fields beyond what is strictly required for survey submission. Overly broad guest user permissions are a common audit finding.

- **User Experience** -- Surveys are a direct touchpoint with customers and employees. Poor page structure, confusing branching, and broken links create a negative brand impression. The survey experience must be tested from the respondent's perspective, not the admin's. Embedding surveys in Lightning pages for internal users and using personalized invitation links for external users are both patterns that improve completion rates.

- **Scalability** -- The Base tier's 300-response lifetime cap makes surveys non-viable for any org with meaningful external survey volume. Architects must assess response volume projections before committing to a design. The Feedback Management tier decision (Base vs Starter vs Growth) is an architectural choice that constrains or enables the entire survey strategy.

## Architectural Tradeoffs

**Native Surveys vs Third-Party Tools:** Salesforce Surveys provide tight integration with the platform data model -- responses link directly to Contacts, Cases, and Accounts without middleware. However, the native tool has limited question types, page-level-only branching, and no built-in analytics beyond standard reports. Third-party tools offer richer survey logic but require integration work to push responses back into Salesforce. Choose native when the primary goal is CRM-integrated feedback; choose third-party when survey design complexity is the priority.

**Anonymous vs Tracked Responses:** Using generic survey URLs is simpler to distribute but loses all traceability. Creating SurveyInvitation records per recipient adds complexity (Flow or Apex automation) but preserves the response-to-record association that makes survey data actionable. The right choice depends on whether the org needs aggregate sentiment (anonymous is fine) or per-customer feedback trends (tracked is required).

**Feedback Management Tier Selection:** Upgrading from Base to Starter or Growth is a licensing cost. Delaying the decision until the 300-cap is hit causes a production outage for survey collection. Architects should project 12-month response volume and select the tier at design time rather than reacting to cap exhaustion.

## Anti-Patterns

1. **Designing without confirming the response cap** -- Building and launching a survey program on Base tier without checking the 300-response lifetime limit leads to silent failures when the cap is hit. Always confirm the tier and current usage before committing to a design.

2. **Testing surveys only as an authenticated admin** -- Admins have full object access, so surveys always work during internal testing. The guest user experience is fundamentally different. Failing to test as an unauthenticated external user means permission issues are discovered by customers, not by the team.

3. **Treating survey content as deployable metadata** -- Assuming surveys move through change sets or CI/CD pipelines like other Salesforce configuration leads to failed deployments and duplicated manual effort. Survey content is stored as data in SurveyVersion records and must be treated as org-specific configuration.

## Official Sources Used

- Object Reference — sObject behavior and standard object semantics for Survey, SurveyVersion, SurveyInvitation, SurveyResponse, SurveyQuestionResponse, SurveyQuestionScore — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Salesforce Well-Architected Overview — architecture quality framing for security, user experience, and scalability tradeoffs — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Surveys Developer Guide — survey creation, question types, branching, invitations, and guest user configuration — https://developer.salesforce.com/docs/atlas.en-us.surveys.meta/surveys/surveys_intro.htm
- Salesforce Feedback Management Documentation — tier comparison, response limits, licensing — https://help.salesforce.com/s/articleView?id=sf.task_create_a_survey.htm
