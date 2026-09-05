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
- Metadata API Developer Guide, "Maintaining User References" (api_meta.txt L2705–2719) — sandbox username suffix (`user@acme.com` → `user@acme.com.test`), and the rule that a username missing in the destination org stops the deployment — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (worked-examples.md § 2.3; environment checklist)
- Metadata API Developer Guide, `deployRecentValidation()` (api_meta.txt L4860–4874) — the quick-deploy preconditions: validated for the target environment within the last 10 days, tests passed, 75% coverage — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (worked-examples.md § 5, "Validation before the sign-off, quick deploy after it")
- Metadata API Developer Guide, `ActionOverride.formFactor` and `CompactLayout` (api_meta.txt L39827–39836, L43076–43082) — `Large` = Lightning Experience desktop, `Small` = Salesforce mobile app; compact layouts exclude text area, long text area, rich text area and multi-select picklist — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (gotcha 11)
- Data Loader Guide, Settings reference (salesforce_data_loader.txt L351–360, L379–383) — import batch maximum of 200 records for SOAP API and 10,000 for Bulk API, Bulk API 2.0 sizing batches itself; the Assignment rule setting, which "overrides Owner values in your CSV file" — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_data_loader.pdf (gotcha 7; worked-examples.md UAT-CI-005)
- Bulk API 2.0 ingest job resource (api_asynch.txt L1591–1595) and REST API Assignment Rule Header (api_rest.txt L691–694) — `assignmentRuleId` is optional on a Bulk job, while REST defaults to running the active assignment rules when the header is absent (gotcha 7)
- Apex Developer Guide, "Execution Governors and Limits" (apexdev.txt L19544, L19554, L19579) — 100 SOQL queries / 150 DML statements / 10,000 ms CPU synchronous, 200 / 150 / 60,000 ms asynchronous — the ceilings a bulk UAT case exists to probe — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf (gotcha 8; worked-examples.md § 3)
- `skills/admin/sandbox-strategy/SKILL.md` §§ Sandbox Type Decision Matrix, Type Capacities and Refresh Windows, What Your Org Actually Owns — Full-vs-Partial selection for UAT, the 29-day Full refresh floor, Partial Copy's 5 GB / 10,000-records-per-object cap, and the fact that Enterprise Edition ships zero Full sandboxes (worked-examples.md § 2.1; gotchas 6 and 8)
- `skills/devops/sandbox-data-isolation-gotchas/SKILL.md` § Email Deliverability — What Is and Is Not Controlled Automatically — the three deliverability levels, the `System Email Only` default, and the fact that only `User.Email` gets `.invalid` appended while Contact and Lead emails are copied verbatim (worked-examples.md § 2.2; gotcha 1)
- `skills/admin/change-management-and-deployment/SKILL.md` § The Deploy Contract — `checkOnly` as the validation switch and `rollbackOnError` / `testLevel` as release decisions, which is what makes the UAT window and the quick-deploy window one schedule (worked-examples.md § 5)
- `skills/admin/uat-test-case-design/SKILL.md` §§ The Canonical UAT Case Schema, Permission Setup Discipline, Negative-Path Coverage — the per-case field schema this skill's plan record references rather than restates (worked-examples.md § 3; gotchas 2 and 10)
