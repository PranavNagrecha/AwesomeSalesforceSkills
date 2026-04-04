---
name: security-health-check
description: "Use when running, interpreting, or acting on Salesforce Security Health Check results — reading the score, understanding risk categories, evaluating specific settings, creating or importing a custom baseline, querying the Tooling API programmatically, or planning remediation from findings. Triggers: 'security health check score', 'health check failing settings', 'custom baseline', 'remediate health check findings', 'fix risk'. NOT for org hardening implementation, permission model design, or broad baseline config beyond what Health Check directly measures."
category: security
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
triggers:
  - "our security health check score dropped after the last release"
  - "what does a high risk finding in health check mean and how do we fix it"
  - "how do I create a custom baseline for our industry compliance requirements"
  - "can I query health check score programmatically from a pipeline or script"
  - "health check shows failing password policy but we already changed the setting"
  - "what is the difference between informational and low risk in health check"
tags:
  - security-health-check
  - security-score
  - custom-baseline
  - password-policy
  - session-settings
  - tooling-api
inputs:
  - "current Health Check score and list of failing settings"
  - "org type (production, sandbox, scratch) and regulatory or compliance context"
  - "whether a custom baseline is in use and what it overrides"
  - "Tooling API access or Setup UI access"
outputs:
  - "interpretation of score and risk categories with remediation priorities"
  - "step-by-step remediation plan for specific failing settings"
  - "custom baseline design guidance and XML/import workflow"
  - "Tooling API query patterns for automated score monitoring"
  - "completed Health Check review worksheet"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-04
---

# Security Health Check

Use this skill when the question is specifically about reading, interpreting, remediating, or automating the Salesforce Security Health Check tool — the built-in Setup feature that scores an org's security configuration against a baseline standard. This skill covers how the score is computed, what each risk category means, how to fix individual failing settings, how to build a custom baseline, and how to query Health Check data via the Tooling API.

For broader org hardening beyond what Health Check measures (CSP Trusted Sites, CORS, clickjack protections, release updates), use `security/org-hardening-and-baseline-config`.

---

## Before Starting

Gather this context before working on anything in this domain:

- What is the current Health Check score and which risk group are the failing settings in (High Risk, Medium Risk, Low Risk, Informational)?
- Is the org using the default Salesforce baseline or a custom-imported baseline?
- Is the request about the Setup UI, Tooling API queries, or automated pipeline monitoring?
- Are there compliance requirements (HIPAA, PCI-DSS, SOC 2) that warrant a stricter custom baseline?

---

## Core Concepts

### The Score Is a Weighted Compliance Percentage

Security Health Check compares your org's current security settings against a baseline standard and produces a score from 0 to 100. The score is not a simple pass/fail count — it is a weighted calculation where High Risk deviations reduce the score most, followed by Medium Risk, and then Low Risk. Informational findings do not affect the score at all. A setting that is "Meets Standard" contributes positively; a setting that "Does Not Meet Standard" lowers the score proportionally to its risk weight.

The score formula is approximately: `Score = 100% − Σ(deviation weight × risk category weight)`. Because High Risk items carry the most weight, a single High Risk failure can drop the score substantially even if all other settings pass.

### Four Risk Categories

Every setting in Health Check belongs to exactly one risk category:

- **High Risk** — settings whose misconfiguration represents the most serious security exposure. Examples include minimum password length below 8 characters, no password complexity requirement, session timeout set to longer than 12 hours, and permitting all IP ranges without restriction. These must be addressed first.
- **Medium Risk** — settings with meaningful but less immediate exposure. Examples include password expiration set to "never" and maximum invalid login attempts set above 10.
- **Low Risk** — minor configuration gaps that represent incremental hardening. Examples include not requiring a password change on first login and not enforcing password history.
- **Informational** — settings tracked for awareness only. They do not affect the score. Informational items are useful for auditing but remediating them does not improve the numeric score.

### What Settings Are Evaluated

Health Check evaluates settings in the following areas (against the Salesforce standard baseline):

- **Password Policies**: minimum length, complexity requirements (alpha/numeric/special characters), maximum age, history enforcement, first-time login change, lockout effective period, maximum invalid attempts.
- **Session Settings**: session timeout value, session security level required at login, require secure connections (HTTPS), lock sessions to the IP from which they originated, require HttpOnly attribute on session cookies.
- **Network Access**: login IP range restrictions, trusted IP ranges.
- **Authentication Settings**: multi-factor authentication enforcement flags, identity confirmation behavior.

The exact set of settings checked can expand with Salesforce releases. Check the current baseline via Setup → Security → Health Check after any major release.

### Custom Baselines Replace the Salesforce Standard

By default, Health Check measures your org against the Salesforce-published standard. Organizations with stricter requirements (financial services, healthcare, government) can replace this with a custom baseline. A custom baseline is an XML file that:

1. Specifies each setting and the threshold your organization requires.
2. Assigns a risk category (High, Medium, Low, Informational) to each setting — you can promote a setting from Low to High, or demote one to Informational to exclude it from scoring.
3. Is imported via Setup → Security → Health Check → Import Baseline.

When a custom baseline is active, the score reflects compliance with your custom thresholds, not the Salesforce defaults. This means a 100% score against a custom baseline is only meaningful if the custom baseline is at least as strict as the Salesforce standard in every category. A custom baseline that relaxes settings to achieve a higher score is an anti-pattern.

### Tooling API Access for Automated Monitoring

Health Check data is queryable via two read-only Tooling API objects: `SecurityHealthCheck` and `SecurityHealthCheckRisks`. This enables automated monitoring in CI/CD pipelines and scheduled health monitoring scripts.

- `SecurityHealthCheck` — returns the overall score for the org. Requires "View Setup and Configuration" permission. Available since API version 37.0.
- `SecurityHealthCheckRisks` — returns individual risk findings: setting name, current org value, standard/baseline value, risk category, and whether the setting meets the standard.

Sample Tooling API SOQL:

```
SELECT Score FROM SecurityHealthCheck
```

```
SELECT SettingName, RiskType, OrgValue, StandardValue, MeetsStandard
FROM SecurityHealthCheckRisks
WHERE MeetsStandard = false
ORDER BY RiskType ASC
```

The Tooling API endpoint is `/services/data/vXX.0/tooling/query/?q=...`. Results can be parsed to enforce a minimum score gate in automated deployment or security review workflows.

---

## Common Patterns

### Mode 1: Run and Baseline an Org's Health Check

**When to use:** First-time review, post-release review, or routine security audit.

**How it works:**
1. Navigate to Setup → Security → Health Check.
2. Note the overall score and the baseline in use (Salesforce Standard or a named custom baseline).
3. Expand each risk group (High Risk first) and record every failing setting with its current value and the required standard value.
4. Use the Health Check Review Worksheet (see template) to capture each finding, its risk tier, and the responsible admin or team.
5. Prioritize remediation: all High Risk items first, then Medium, then Low.

**Why not the alternative:** Skipping structured documentation of findings leads to partial remediation — teams fix the most obvious settings but miss less visible ones. The worksheet creates an audit trail.

### Mode 2: Interpret Score Changes and Custom Baselines

**When to use:** Score unexpectedly dropped after a release or sandbox refresh, or the team needs to align Health Check to a compliance framework.

**How it works — score drop investigation:**
1. Compare the current failing settings against any recent changes (post-release settings drift, sandbox copy behavior).
2. Check whether the baseline itself was changed (a new release may update the Salesforce standard thresholds).
3. Identify whether the drop is a new High Risk failure (large score drop) or an accumulation of Low Risk settings (gradual drift).

**How it works — custom baseline design:**
1. From Setup → Health Check, export the current Salesforce standard baseline as XML.
2. Edit the XML to set `riskType` values and `standardValue` thresholds to match your compliance requirements.
3. Do not relax any setting below the Salesforce default threshold just to improve a score.
4. Import the custom baseline via Setup → Health Check → Import Baseline.
5. Document every deviation from the Salesforce standard and the business justification.

**Why not the alternative:** Manually tracking compliance thresholds outside the tool creates drift and is not auditable.

### Mode 3: Automated Score Monitoring via Tooling API

**When to use:** You want a pipeline check, a scheduled alert, or integration with an external SIEM or monitoring system.

**How it works:**
1. Authenticate to the Tooling API using a Connected App with the "api" OAuth scope.
2. Query `SecurityHealthCheck` to retrieve the current score.
3. Query `SecurityHealthCheckRisks WHERE MeetsStandard = false` to retrieve failing settings.
4. Parse results and compare against a minimum score threshold or a list of required-passing settings.
5. Emit alerts or fail a deployment gate if the score falls below threshold or a required setting is failing.

**Why not the alternative:** Relying on manual Setup UI reviews creates gaps between reviews. Automated monitoring catches score drops introduced by admin changes between audit cycles.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Score is below 80% with High Risk failures | Fix all High Risk settings first, then Medium | High Risk items carry the heaviest score weight |
| Score is 90%+ but team wants compliance alignment | Design a custom baseline with your framework thresholds | Default baseline may not match your compliance posture |
| Score dropped after sandbox refresh | Check if sandbox copied production password/session settings correctly; sandbox resets some settings to less-strict defaults | Sandbox copy does not always preserve all security settings |
| Informational items make up most of the list | These do not affect the score; triage by real risk, not score impact | Moving items to Informational is a conscious risk acceptance decision |
| Team needs automated monitoring | Use Tooling API SecurityHealthCheck + SecurityHealthCheckRisks with a scheduled job | Provides continuous monitoring without manual UI checks |
| Custom baseline makes the score look artificially high | Audit the baseline against the Salesforce standard; document every relaxed setting | A custom baseline that relaxes defaults is a risk acceptance, not a security improvement |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Overall Health Check score has been recorded with baseline name and review date.
- [ ] All High Risk failing settings have been identified, documented, and a remediation owner assigned.
- [ ] All Medium Risk failing settings have been reviewed and triaged.
- [ ] If a custom baseline is in use, every deviation from the Salesforce standard is documented with a business justification.
- [ ] No custom baseline changes were made solely to improve the numeric score without genuine compliance justification.
- [ ] If Tooling API monitoring is in place, the query and alert thresholds are documented.
- [ ] Informational items have been reviewed for genuine risk even though they don't affect the score.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Sandbox refresh can reset security settings to less-strict defaults** — when a sandbox is created or refreshed from a production org, some session and password settings may revert to Salesforce defaults rather than inheriting the production values. A 100% Health Check score in production does not guarantee any particular score in a freshly-refreshed sandbox. Always run Health Check in a new sandbox before using it for security testing.

2. **Moving a setting to Informational in a custom baseline excludes it from scoring but does not fix it** — administrators sometimes move a failing setting to Informational rather than remediating it, because this improves the numeric score. The setting remains misconfigured; only its contribution to the score is removed. A 100% score against a permissive custom baseline provides no meaningful security assurance.

3. **The Salesforce standard baseline can change between releases** — Salesforce may tighten the standard thresholds for existing settings or add new settings in any major release. A score that was 95% before a Spring/Summer/Winter release can drop immediately after the release without any admin action, simply because a new setting was added and it defaults to a non-compliant state. Post-release Health Check review is a required operational cadence, not optional.

4. **"Fix It" applies the Salesforce standard value, not your custom baseline value** — the Setup UI "Fix It" button next to a failing setting applies the Salesforce standard recommended value. If you are using a custom baseline with stricter thresholds, "Fix It" may set the value to the Salesforce standard rather than your custom requirement. Always verify the resulting value against your baseline after using "Fix It".

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Health Check review worksheet | Scored inventory of all failing settings by risk tier with remediation owners and status |
| Custom baseline design | Annotated XML baseline with deviation justifications and compliance mapping |
| Tooling API query patterns | Ready-to-use SOQL for score retrieval and failing-settings enumeration |
| Remediation plan | Prioritized action list: High Risk first, with specific setting targets and responsible parties |

---

## Related Skills

- `security/org-hardening-and-baseline-config` — use when the question expands beyond what Health Check directly measures (CSP, CORS, clickjack, release updates, browser trust governance).
- `admin/connected-apps-and-auth` — use when the remediation involves authentication settings or OAuth app configuration that Health Check flags.
- `security/platform-encryption` — use when compliance requirements driving a custom baseline also include data-at-rest encryption concerns.
