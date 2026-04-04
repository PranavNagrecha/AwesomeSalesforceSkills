# Well-Architected Notes — Security Health Check

## Relevant Pillars

- **Security** — Security Health Check is a direct expression of the Security pillar. It operationalizes the principle that security configuration must be validated, not assumed. The tool provides a scored, repeatable measure of password policy, session management, and network access control compliance against a known baseline. Using Health Check regularly ensures security posture is measurable and auditable rather than aspirational.

- **Operational Excellence** — Maintaining a Health Check score requires an operational cadence, not a one-time configuration. Post-release reviews, sandbox-refresh checks, and pipeline monitoring gates all represent operational practices that prevent silent drift. Teams that treat Health Check as a quarterly or annual check rather than a continuous process accumulate risk between reviews.

- **Reliability** — Indirectly relevant: security misconfigurations caught by Health Check (such as missing session locks or excessively permissive network access) can contribute to unauthorized access that disrupts service reliability. Maintaining a strong baseline reduces the attack surface that might otherwise lead to account compromise and operational disruption.

## Architectural Tradeoffs

**Default baseline vs. custom baseline:** The Salesforce standard baseline is appropriate for most orgs and represents Salesforce's published best-practice thresholds. Custom baselines allow orgs to align with compliance frameworks (HIPAA, PCI-DSS, SOC 2, FedRAMP) that require stricter controls. The tradeoff is maintenance overhead — a custom baseline XML must be versioned, reviewed after each Salesforce release, and managed as a first-class configuration artifact. Organizations without genuine compliance-framework requirements should prefer the default baseline to avoid the operational burden of baseline governance.

**Manual remediation vs. "Fix It" automation:** The Health Check UI's "Fix It" button provides a fast path to remediation for individual settings. The tradeoff is precision: "Fix It" applies the Salesforce standard value, not a custom baseline's stricter threshold, and does not document the change in a release or change management record. For production orgs or regulated environments, explicit manual remediation with change management documentation is preferable to "Fix It."

**UI-driven review vs. Tooling API monitoring:** The Setup UI provides the clearest, most accessible view of Health Check results. The Tooling API enables automation, historical trending, and pipeline gates, but requires authentication infrastructure (Connected App, OAuth flow) and ongoing maintenance of the monitoring script. Organizations with mature DevOps practices benefit from both: the UI for human review and the API for automated enforcement.

## Anti-Patterns

1. **Score as a proxy for security** — treating the Health Check score as the primary or only measure of org security. A 100% score against the Salesforce standard baseline means password and session settings meet published thresholds; it does not mean the org is broadly hardened. CSP configuration, CORS allowlists, connected app governance, permission model design, and encryption controls are outside the scope of Health Check. Use `security/org-hardening-and-baseline-config` alongside Health Check for a more complete picture.

2. **Baseline softening for score management** — importing a custom baseline that demotes failing settings to Informational or reduces thresholds to values easier to meet. This produces a high score without improving actual security. Any custom baseline deviation from the Salesforce standard should have a documented compliance or business justification, not a score-management rationale.

3. **Set-and-forget mentality** — running Health Check once during an org build or security review and never revisiting it. Salesforce releases can add new settings or tighten thresholds, admin changes can weaken settings, and sandbox refreshes can introduce drift. Health Check is a continuous operational control, not a one-time configuration task.

## Official Sources Used

- Security Health Check — https://help.salesforce.com/s/articleView?id=sf.security_health_check.htm&type=5
- How Is the Health Check Score Calculated? — https://help.salesforce.com/s/articleView?id=xcloud.security_health_check_score.htm&language=en_US&type=5
- Create a Custom Baseline for Health Check — https://help.salesforce.com/s/articleView?id=xcloud.security_custom_baseline_create.htm&language=en_US&type=5
- Custom Baseline File Requirements — https://help.salesforce.com/s/articleView?id=xcloud.security_custom_baseline_file_requirements.htm&language=en_US&type=5
- SecurityHealthCheck Tooling API Object — https://developer.salesforce.com/docs/atlas.en-us.api_tooling.meta/api_tooling/tooling_api_objects_securityhealthcheck.htm
- SecurityHealthCheckRisks Tooling API Object — https://developer.salesforce.com/docs/atlas.en-us.api_tooling.meta/api_tooling/tooling_api_objects_securityhealthcheckrisks.htm
- Salesforce Security Guide — https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
