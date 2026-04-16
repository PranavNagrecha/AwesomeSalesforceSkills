# Examples — MFA Enforcement Strategy

## Example 1: SSO-First Enterprise With Lingering Salesforce Passwords

**Context:** A 4,000-employee company uses Microsoft Entra ID for SAML SSO into Salesforce. Security believes “MFA is done” because Conditional Access requires phishing-resistant MFA at the IdP. A quarterly access review still finds hundreds of active Salesforce passwords for the same employees.

**Problem:** Org-wide Salesforce MFA enforcement is toggled on without removing password login as a realistic path. A subset of users continues to authenticate directly to Salesforce with password only, bypassing the IdP MFA investment and breaking the compliance story.

**Solution:**

1. Treat **channel inventory** as a prerequisite: for each population, record whether the only supported path is SSO or whether Salesforce password remains available.
2. Align IdP policy (MFA strength, session length) with Salesforce session expectations documented for your edition.
3. **Disable or tightly control direct login** for populations intended to be SSO-only, after communications and a pilot.
4. Only then align Salesforce org-wide MFA settings with the remaining populations that truly authenticate locally.

**Why it works:** MFA enforcement is evaluated in the context of **how** the session is established. Closing the weaker channel removes the audit finding that “MFA exists in theory but not on the path the user actually took.”

---

## Example 2: Phased Rollout for a Global Sales Organization

**Context:** Salesforce is revenue-critical. Sales operations fears lockouts during quarter-end. Identity standards still require MFA for all UI access within two quarters.

**Problem:** A single cutover date risks mass failed logins in regions where help desk coverage is thin, and executives resist without a credible support model.

**Solution:**

| Phase | Audience | Duration | Exit criteria |
|---|---|---|---|
| 0 | Identity + Salesforce admins | 2 weeks | Runbook signed; IdP SAML traces clean |
| 1 | IT and finance pilot | 3 weeks | <1% MFA-related incidents; KB articles live |
| 2 | Americas sales | 4 weeks | Registration 98%+; SSO bypass resolved |
| 3 | EMEA/APAC | 4 weeks | Same metrics; localized comms sent |

Pair each phase with **predictable office hours**, **printed recovery steps** for regions with device restrictions, and a **named rollback approver**.

**Why it works:** MFA adoption is a **change management** problem as much as a configuration task. Phasing limits blast radius while preserving a firm end state.

---

## Anti-Pattern: “We Will Enforce MFA and Fix Integrations Later”

**What practitioners do:** Enable org-wide MFA for all users on a Friday evening, plan to triage broken integrations on Monday.

**What goes wrong:** Batch jobs, ETL, and legacy desktop tools that reused personal user sessions or weak automation patterns fail silently or at volume, affecting data freshness and downstream reporting.

**Correct approach:** Run an **integration inventory** in parallel with human MFA rollout; migrate automation to supported OAuth or integration-user patterns; time enforcement after green metrics from a pilot group that includes operational personas.
