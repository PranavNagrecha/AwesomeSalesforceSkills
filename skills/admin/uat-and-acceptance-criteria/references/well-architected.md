# Well-Architected Notes — UAT and Acceptance Criteria

## Relevant Pillars

- **Operational Excellence** — UAT is the quality gate that prevents defective releases from reaching production. Structured test scripts, defect logs, and formal sign-off are the operational artifacts that make releases repeatable, auditable, and improvable. Skipping UAT or running it informally is the leading cause of production incidents and emergency patches in Salesforce orgs.
- **Reliability** — Regression testing ensures that changes to shared components (flows, validation rules, page layouts, profiles) do not silently break previously working features. Without structured regression planning, reliability degrades over time as the org accumulates undetected regressions.
- **Security** — Security defects (FLS errors, sharing rule gaps, profile permission overages) must be classified as P1 severity and block release. UAT that does not test from role-appropriate non-admin profiles cannot detect FLS or sharing defects. The security layer of a Salesforce org is only as good as the UAT coverage of its access model.

## Architectural Tradeoffs

**Manual UAT vs Automated Testing:** UAT test scripts executed by business users are the standard for validating that a built feature meets business acceptance criteria. They are not a substitute for automated Apex tests or Flow tests, and automated tests are not a substitute for UAT. These serve different purposes:
- Automated tests (Apex, Jest, Flow tests) validate technical implementation correctness and catch regression at the code level. They run fast, are repeatable, and should run in CI/CD.
- Manual UAT validates that the feature matches the business user's expectation in the actual UI. It catches usability issues, FLS misconfigurations, page layout gaps, and cross-feature interactions that automated tests cannot simulate.

Both are required for a reliable Salesforce release practice.

**Test Environment Fidelity vs Cost:** Full sandbox refreshes provide the highest environment fidelity for UAT but are expensive (licensed separately, slow to refresh). Partial sandboxes are faster and cheaper but may lack the data volume needed to test sharing at scale. Developer sandboxes require manual data setup but are free. The environment selection decision affects which categories of defects UAT can reliably find.

## Anti-Patterns

1. **Testing from an admin account** — Admins bypass FLS and most sharing restrictions in the UI. A test pass from an admin user does not confirm that the feature works for Sales Reps, Service Agents, or other restricted profiles. Every security-related test case must be executed from a user with the actual production profile, not a system administrator.

2. **Acceptance criteria written as UI preferences, not observable outcomes** — Criteria like "the page should load quickly" or "the form should be user-friendly" cannot be tested and cannot produce a pass/fail result. These criteria drift into production unchecked and become post-launch complaints. Every criterion must be an observable, boolean outcome tied to a specific Salesforce field, button, automation trigger, or access control.

3. **UAT executed by the build team** — The person who built the feature knows the happy path and unconsciously avoids the edge cases they did not account for. Business users find the defects that matter to the business. UAT must be executed by the people who will use the feature in production, not the people who built it.

4. **No regression plan on shared metadata changes** — A change to a Flow that is shared across 5 business processes, or a profile update that affects 3 different record types, carries regression risk across all of those downstream features. Without a regression plan, that risk is invisible until a production incident surfaces it.

## Official Sources Used

- Salesforce Well-Architected Overview — architecture quality framing, Operational Excellence and Reliability pillars — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Trailhead: Business Analyst Certification Preparation — user story and acceptance criteria format, if/then structure — https://trailhead.salesforce.com/en/credentials/businessanalyst
- Salesforce Help: Sandbox Types and Templates — sandbox type selection for test environments — https://help.salesforce.com/s/articleView?id=sf.data_sandbox_environments.htm&type=5
- Salesforce Help: Set Email Deliverability — deliverability settings that affect UAT email testing — https://help.salesforce.com/s/articleView?id=sf.emailadmin_deliverability.htm&type=5
