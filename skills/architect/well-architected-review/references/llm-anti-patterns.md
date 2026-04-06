# LLM Anti-Patterns — Well-Architected Review

Common mistakes AI coding assistants make when generating or advising on Salesforce Well-Architected Framework (WAF) reviews.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using Outdated WAF Pillar Names

**What the LLM generates:** References to AWS-style pillars ("Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization") or pre-2023 Salesforce terminology instead of the current Salesforce Well-Architected Framework pillars.

**Why it happens:** LLMs conflate AWS Well-Architected Framework pillar names with Salesforce's framework. Salesforce rebranded its WAF pillars to Trusted, Easy, and Adaptable, but older training data uses different terminology.

**Correct pattern:**

```text
Current Salesforce Well-Architected Framework (as of Spring '25):

Three pillars:
1. TRUSTED: security, compliance, data protection, identity, privacy
2. EASY: user experience, adoption, accessibility, usability
3. ADAPTABLE: scalability, maintainability, automation, integration readiness

Sub-attributes under each pillar:
- Trusted: Secure, Compliant, Reliable
- Easy: Discoverable, Efficient, Familiar
- Adaptable: Composable, Scalable, Resilient

Reference: https://architect.salesforce.com/well-architected/overview
```

**Detection hint:** Flag WAF reviews that reference "Cost Optimization," "Performance Efficiency," or "Operational Excellence" as pillar names — these are AWS pillars, not Salesforce. Check for "Trusted, Easy, Adaptable" as the correct framework.

---

## Anti-Pattern 2: Producing Generic Checklist Reviews Without Org-Specific Findings

**What the LLM generates:** A boilerplate WAF review that lists general best practices ("enable MFA," "use sharing rules," "implement CI/CD") without referencing specific findings from the actual org being reviewed. The output reads like a Salesforce best-practices blog post rather than an assessment.

**Why it happens:** LLMs generate from pattern completion. Without specific org data provided as context, they produce generic recommendations. Even when org details are provided, LLMs may default to template-style output.

**Correct pattern:**

```text
A WAF review finding must include:
1. Specific observation: "The Account object OWD is Public Read/Write,
   but Account records contain PII fields (SSN__c, Tax_ID__c)."
2. Pillar and sub-attribute: "Trusted > Secure"
3. Risk rating: "High — PII exposure to all authenticated users"
4. Recommendation: "Change Account OWD to Private, create sharing rules
   for the 3 user groups that need cross-team visibility."
5. Effort estimate: "Medium — requires sharing rule creation and testing"

Do NOT produce findings that are not tied to a specific org configuration,
data model, or automation pattern observed in the assessment scope.
```

**Detection hint:** Flag WAF review outputs where every finding uses generic language ("ensure," "consider," "should") without referencing specific objects, fields, automation, or configurations.

---

## Anti-Pattern 3: Scoring All Pillars Without Adequate Evidence

**What the LLM generates:** A complete Red/Amber/Green scorecard for all three pillars based on limited input — for example, generating a "Green" Trusted score based solely on the fact that MFA is enabled, without checking sharing model, FLS, Connected App policies, or Shield configuration.

**Why it happens:** LLMs are completion-oriented and will fill in a scorecard template even when insufficient evidence exists. Generating "Green" is easier than acknowledging gaps.

**Correct pattern:**

```text
WAF scoring rules:
- GREEN: evidence of compliance across all sub-attributes of the pillar,
  validated by specific org configuration checks.
- AMBER: partial compliance with identified gaps that have remediation paths.
- RED: critical gaps that pose immediate risk or block compliance.
- NOT ASSESSED: insufficient data to score this pillar. Request more information.

It is better to score a pillar as "NOT ASSESSED" than to give a misleading
Green based on incomplete evidence.

Minimum evidence per pillar:
- Trusted: OWD review, FLS spot-check, Connected App audit, Shield status
- Easy: user adoption metrics, page layout review, mobile experience check
- Adaptable: automation inventory, code coverage, deployment process review
```

**Detection hint:** Flag WAF scorecards that rate all pillars Green without listing the specific evidence checked for each rating. Check for "NOT ASSESSED" usage — its absence suggests over-confidence.

---

## Anti-Pattern 4: Ignoring the Easy Pillar (User Experience and Adoption)

**What the LLM generates:** WAF reviews that provide detailed Trusted and Adaptable assessments but give only a single sentence to the Easy pillar, such as "The org uses Lightning Experience, so the user experience is modern."

**Why it happens:** LLMs are trained on technical content (security, code, architecture) and have far less training data on Salesforce UX best practices, page layout optimization, mobile adoption, and user onboarding. The Easy pillar gets short-changed because it is less technical.

**Correct pattern:**

```text
Easy pillar review areas:
1. Page layout efficiency: are record pages optimized with Dynamic Forms,
   or do they show 50+ fields in a single column?
2. Navigation: is the App Launcher organized? Are utility bar items useful?
3. Mobile experience: is the Salesforce mobile app configured with mobile
   layouts and actions? Or is the mobile experience a shrunken desktop?
4. Adoption metrics: daily active users, login frequency, feature usage
   (available via Event Monitoring or Login History).
5. In-App Guidance: are walkthroughs or prompts configured for new features?
6. Accessibility: WCAG compliance of custom components, color contrast,
   keyboard navigation.

The Easy pillar is often the most impactful for ROI because poor UX
drives workarounds, shadow IT, and low adoption.
```

**Detection hint:** Flag WAF reviews where the Easy pillar section is less than 20% of the total review length or contains no specific page layout, navigation, or adoption findings.

---

## Anti-Pattern 5: Treating WAF as a One-Time Audit Rather Than a Continuous Practice

**What the LLM generates:** "Conduct the Well-Architected Review, document findings, and implement the remediation backlog" as a one-time project with no follow-up cadence, regression monitoring, or integration into the SDLC.

**Why it happens:** LLMs treat the WAF review as a point-in-time deliverable (like a security audit) rather than a continuous practice. Training data typically shows WAF as a pre-go-live or annual activity.

**Correct pattern:**

```text
WAF should be embedded as a continuous practice:

1. Pre-go-live: full WAF review before each major release
2. Quarterly: lightweight pillar check-ins (30-minute reviews per pillar)
3. Sprint-level: WAF design principles as part of story acceptance criteria
4. Automated: Security Health Check monitoring, code coverage thresholds,
   and sharing model drift detection as CI/CD quality gates
5. Post-incident: WAF-aligned root cause analysis (which pillar was violated?)

Embed WAF sub-attributes into Definition of Done:
- Trusted: FLS enforced, no hard-coded credentials
- Easy: page layout reviewed, mobile tested
- Adaptable: automation documented, no dead code introduced
```

**Detection hint:** Flag WAF review recommendations that end with "implement remediation" without defining a review cadence, automated monitoring, or integration into the development lifecycle.
