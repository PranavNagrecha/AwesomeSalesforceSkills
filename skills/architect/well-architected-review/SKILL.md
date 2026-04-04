---
name: well-architected-review
description: "Use when conducting a formal Salesforce Well-Architected Framework (WAF) review of an org or solution design. Covers all three pillars: Trusted (security, compliance), Easy (user experience, adoption), and Adaptable (scalability, maintainability). Produces a structured assessment with findings and recommendations. Triggers: well-architected review, WAF assessment, org architecture review, architecture health check, trusted easy adaptable. NOT for deep-dives into individual pillars (use security-architecture-review, limits-and-scalability-planning, or technical-debt-assessment) or for implementation guidance."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Scalability
  - Operational Excellence
  - User Experience
tags:
  - well-architected
  - architect
  - org-assessment
  - trusted-easy-adaptable
  - architecture-review
triggers:
  - "conduct a well-architected review of this org"
  - "WAF assessment for our Salesforce org"
  - "architecture health check before go-live"
  - "trusted easy adaptable review"
  - "org architecture review against Salesforce best practices"
  - "pre-delivery architecture sign-off"
  - "is this org well-architected?"
  - "architecture review for this solution design"
inputs:
  - Org type and Salesforce edition
  - Primary business function(s) supported by the org
  - Key stakeholder concerns or known pain points
  - Scope (full org vs specific solution/cloud)
outputs:
  - Well-Architected review document with findings per pillar
  - Prioritized recommendations with effort and impact ratings
  - Summary scorecard (Red/Amber/Green per pillar)
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

Use this skill when conducting a formal Salesforce Well-Architected Framework (WAF) review against an org or a solution design. It applies all three high-level pillars — Trusted, Easy, and Adaptable — and produces a structured assessment with scored findings, prioritized recommendations, and a summary scorecard. It does not replace pillar-specific deep-dives; it is the entry point that tells you which deep-dives are needed.

---

## Before Starting

- **What is the scope?** A full org WAF review, a specific solution or cloud, or a pre-delivery sign-off? Scope determines how deeply each pillar is examined.
- **Who is the audience?** An executive sponsor needs a scorecard and top-three risks. A delivery team needs actionable findings with remediation owners.
- **What edition and cloud(s) are in scope?** Enterprise Edition unlocks sharing rules and Shield; Unlimited Edition changes license economics. Edition affects what controls are available.
- **Are there regulatory or compliance requirements?** GDPR, HIPAA, PCI-DSS, SOC 2 — these directly shape the Trusted pillar assessment scope.

---

## Modes

### Mode 1: Full Org WAF Review

Use when assessing an existing production org holistically. Suitable for annual architecture reviews, post-merger org assessments, or as a baseline before a major transformation program.

**Pre-review questionnaire (gather before starting):**
- Salesforce edition and clouds licensed
- Approximate user count and user personas
- Org age and last major architectural change
- Number of custom objects, active Flows, Apex classes, and integrations
- Known pain points from stakeholders
- Any recent security incidents or governor limit events

**Review sequence:**

1. **Trusted pillar:** Security model audit (sharing model completeness, OWDs, sharing rules), FLS coverage check in Apex (use of `WITH SECURITY_ENFORCED`, `stripInaccessible`, or `WITH USER_MODE`), authentication strength (MFA enforced, SSO configured), Shield assessment (field audit trail, event monitoring, platform encryption for regulated fields), data classification inventory (what data lives where, is it classified, is sensitive data masked in sandboxes).

2. **Easy pillar:** Lightning page performance review (identify pages with 10+ components, missing lazy loading, synchronous Apex on load), process complexity assessment (count of active Flows, are any redundant, are users doing manual work that should be automated), adoption signal review (field usage, report and dashboard activity, object record counts vs licence count), mobile readiness (mobile navigation configured, key pages mobile-optimised), accessibility compliance (are custom LWC components meeting WCAG 2.1 AA where possible).

3. **Adaptable pillar:** Governor limit headroom scan (daily API usage vs limit, SOQL row limits in peak transactions, heap size in large batch jobs), technical debt level (presence of trigger frameworks, documented architecture decisions, test coverage %, hardcoded IDs), deployment pipeline maturity (sandbox refresh policy, use of scratch orgs, source control, CI/CD pipeline presence), configuration vs code ratio (could logic move from Apex to Flow without sacrificing reliability), dependency management (managed packages with known deprecations, API version currency).

4. **Scoring:** Each finding is rated Red (critical gap — immediate action required), Amber (improvement needed — schedule within the quarter), or Green (good practice — document and maintain).

5. **Output:** Findings report with pillar, area, finding, severity, and recommendation — plus a summary scorecard and a prioritized backlog.

---

### Mode 2: Solution Design WAF Review

Use when reviewing a proposed design before build begins, or before delivery of a new project or feature set into an existing org.

This mode is lighter than a full org review. Focus on the portions of the WAF that the specific solution will affect:

- **Trusted:** Does the solution introduce new data access patterns? Are sharing model implications reviewed? Does any integration callout expose sensitive data over non-TLS connections?
- **Easy:** Is the user journey mapped? Are the proposed page layouts and screen Flows sensible for the target persona? Has the solution been reviewed against mobile usage if the org has mobile users?
- **Adaptable:** What are the governor limit implications of the proposed design at scale? Is the solution using platform features (Flows, standard objects) before reaching for custom Apex or custom objects? Is the deployment approach documented?

Produce a WAF review section in the solution design document itself rather than a separate deliverable.

---

### Mode 3: Pre-Delivery WAF Sign-off

Use immediately before go-live for a project or a significant release. This is a checkpoint, not a full review. Confirm:

- **Trusted:** All Apex classes use enforced sharing. No hardcoded credentials. MFA is enforced for all users in scope. Any Shield requirements are met.
- **Easy:** UAT sign-off covers the key user personas. No critical accessibility blockers. Performance on key pages confirmed in a production-equivalent sandbox.
- **Adaptable:** Test coverage is at or above 85% for new code. No known governor limit breaches in integration testing. Deployment runbook is documented and tested.

Document any items that cannot be met at go-live as accepted risks with a named owner and a target remediation date. Do not withhold sign-off for Amber findings that have an agreed remediation plan; withhold it only for Red findings without a plan.

---

## WAF Pillar Reference

The Salesforce Well-Architected Framework uses three top-level pillars. Each maps to the six internal WAF dimensions used in this repository's scoring model.

| WAF Pillar | Internal Dimensions |
|-----------|-------------------|
| Trusted | Security, Reliability |
| Easy | User Experience |
| Adaptable | Scalability, Performance, Operational Excellence |

### Trusted

Security model completeness covers OWD settings, sharing rules, role hierarchy, and Apex sharing. Every custom object should have a documented OWD justification. Apex that queries or mutates data should enforce FLS using `WITH USER_MODE`, `WITH SECURITY_ENFORCED`, or `stripInaccessible`. Any class using `without sharing` must have a documented reason.

Compliance readiness means understanding what regulated data the org holds and whether appropriate controls are in place. GDPR requires a data map and a right-to-erasure process. HIPAA requires audit logging and access controls on PHI. PCI-DSS prohibits storing cardholder data in standard Salesforce fields without encryption.

Authentication strength means MFA is enforced (not just enabled), SSO is configured where the org has more than a handful of users, and trusted IP ranges are documented and minimal.

Shield considerations apply whenever the org holds regulated or sensitive data. Event Monitoring provides an audit trail for data access. Field Audit Trail extends the standard field history retention window. Platform Encryption encrypts data at rest in Salesforce storage.

### Easy

User experience quality is assessed by examining page performance (Lightning App Builder page load time, number of components per page, synchronous Apex on page load), clarity of error messages, and whether the UI makes the right path the easy path.

Adoption signals include field usage rates (fields with zero or near-zero population may indicate unused features or poor design), record count trends (objects with no records may indicate failed rollouts), and report and dashboard usage (low engagement suggests the org is not supporting decision-making effectively).

Process simplicity asks: are users doing work that could be automated? Are there manual copy-paste steps between Salesforce and other systems? Are approval processes clearly documented and consistently applied?

### Adaptable

Scalability headroom is measured by reviewing peak governor limit consumption. An org running at 80% of its daily API limit or hitting SOQL row limits in production transactions is fragile. Identify the top five governor limit consumption points and document headroom.

Technical debt level is assessed by examining test coverage (target 85%+, never accept below 75%), presence of hardcoded IDs (use Custom Metadata or Custom Settings instead), API version currency of Apex classes and LWC components, and whether architecture decisions are documented.

Deployment pipeline maturity covers whether the team uses source control, whether sandbox refresh is on a documented cadence, whether there is a CI/CD pipeline or at minimum a documented manual deployment checklist, and whether scratch org definitions exist for repeatable environment setup.

---

## Common WAF Anti-Patterns

### Trusted Anti-Patterns
- "View All Data" or "Modify All Data" granted broadly across the user base
- Apex performing DML without FLS checks (`stripInaccessible` missing, `WITH USER_MODE` absent)
- No Shield implementation for orgs holding regulated data (financial, health, or personal data at scale)
- Sharing model never reviewed after org age exceeds three years — OWD and sharing rules designed for a smaller org may over-expose data as the org grows

### Easy Anti-Patterns
- Page layouts with 50+ fields presented to users who need 10
- Custom objects created for a project that ended — now cluttering the data model and confusing admins
- No Lightning page optimisation — all components load synchronously, page takes 8 seconds
- Automation gaps — users told to "copy this ID from one screen and paste it into another" because no one built the junction
- Training investment made at go-live only, never repeated — adoption erodes as the team turns over

### Adaptable Anti-Patterns
- Governor limit usage at 90%+ during peak transactions — one bad data load away from a production outage
- Test coverage at exactly 75% because "that's all Salesforce requires" — provides false confidence
- No sandbox refresh policy — production and sandbox drift until deployments become unpredictable
- Zero documentation of Flow → Apex handoff logic — the next developer does not know why the Flow stops at a certain step and calls a specific Apex action
- Managed packages on deprecated API versions with no upgrade plan

---

## Official Sources Used

- Salesforce Well-Architected Framework Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Well-Architected: Trusted — https://architect.salesforce.com/docs/architect/well-architected/guide/trusted.html
- Salesforce Well-Architected: Easy — https://architect.salesforce.com/docs/architect/well-architected/guide/easy.html
- Salesforce Well-Architected: Adaptable — https://architect.salesforce.com/docs/architect/well-architected/guide/adaptable.html

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

