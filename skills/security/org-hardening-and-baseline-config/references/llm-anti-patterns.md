# LLM Anti-Patterns — Org Hardening and Baseline Config

Common mistakes AI coding assistants make when generating or advising on Salesforce org hardening and baseline security configuration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating Security Health Check Score as Complete Hardening

**What the LLM generates:** "Your org is fully hardened because the Security Health Check score is 95%."

**Why it happens:** Training data frequently associates Health Check with overall security posture, conflating a single scoring tool with the full hardening baseline.

**Correct pattern:**

```
Health Check measures a subset of org security settings (password, session, network).
It does not cover CSP Trusted Sites governance, CORS allowlist sprawl, clickjack
protections, release update hygiene, or exception management. A high score is
necessary but not sufficient for a hardened org.
```

**Detection hint:** If the advice mentions Health Check as the sole or primary measure of org hardening, it is incomplete.

---

## Anti-Pattern 2: Ignoring CSP and CORS Exception Governance

**What the LLM generates:** "Add the domain to CSP Trusted Sites to fix the error" without any mention of documenting the exception, assigning an owner, or reviewing it periodically.

**Why it happens:** Training data emphasizes the fix for the immediate CSP violation error without the governance layer that prevents trust sprawl.

**Correct pattern:**

```
Before adding a CSP Trusted Site or CORS entry:
1. Document the domain, the business reason, and the requesting team.
2. Assign an owner responsible for periodic review.
3. Select only the minimum CSP directives needed (not all directives).
4. Record a review date — exceptions should not persist indefinitely without revalidation.
```

**Detection hint:** If advice adds a trusted site with no mention of ownership, justification, or review cadence, the governance layer is missing.

---

## Anti-Pattern 3: Recommending Trusted IP Ranges for Login Restriction

**What the LLM generates:** "To restrict admin logins to your office network, add the IP range under Setup > Security > Network Access (Trusted IP Ranges)."

**Why it happens:** The name "Trusted IP Ranges" strongly implies access restriction. Training data conflates the two controls because many blog posts and community answers make this same mistake.

**Correct pattern:**

```
Trusted IP Ranges (Network Access) only skip the email verification challenge.
They do NOT prevent logins from outside those ranges.

To hard-restrict logins by IP, use Login IP Ranges on the profile:
Setup > Profiles > [Profile Name] > Login IP Ranges.
This denies login entirely from IPs outside the configured ranges.
```

**Detection hint:** If the recommendation uses "Trusted IP Ranges" or "Network Access" to restrict logins rather than to bypass email verification, the control is misidentified.

---

## Anti-Pattern 4: Treating Release Updates as Optional Cleanup

**What the LLM generates:** "Review critical updates when you have time" or omitting release updates entirely from a hardening checklist.

**Why it happens:** Training data treats critical updates and release security settings as maintenance tasks rather than security work, reflecting a common organizational bias.

**Correct pattern:**

```
Release updates — especially security-related critical updates — are part of the
hardening baseline. They should be reviewed on a fixed operational cadence
(quarterly at minimum) alongside Health Check, browser trust settings, and
stale exception review. Delaying them creates preventable risk and surprise
breakage when Salesforce auto-activates them.
```

**Detection hint:** If a hardening checklist omits release updates or frames them as low-priority maintenance, the operational cadence is incomplete.

---

## Anti-Pattern 5: Generating a One-Time Checklist Instead of an Operating Cadence

**What the LLM generates:** A static hardening checklist with no recurring review schedule or operational rhythm.

**Why it happens:** Training data contains many "hardening checklist" articles that are point-in-time snapshots. LLMs reproduce the snapshot format without the operational discipline needed to keep the baseline current.

**Correct pattern:**

```
A hardening baseline is not a one-time task. It requires:
- A quarterly (or per-release) review cadence for Health Check, browser trust
  settings, and stale exceptions.
- Explicit triggers for re-review: new integration, new community, new connected
  app, or Salesforce major release.
- Assigned ownership for each trust exception and control area.
```

**Detection hint:** If the output is a flat checklist with no mention of cadence, triggers, or ownership, it will drift and become stale.

---

## Anti-Pattern 6: Advising Hardening Without Cross-Functional Context

**What the LLM generates:** Security-only recommendations that ignore integration team constraints, browser requirements, or admin workflows.

**Why it happens:** LLMs generate advice from a single-domain perspective. Org hardening is inherently cross-functional — security, admins, and integration teams all affect the baseline.

**Correct pattern:**

```
Before recommending any hardening change, confirm:
- Does the integration team depend on any of the CSP/CORS exceptions being removed?
- Will tighter session settings break mobile or embedded use cases?
- Are there browser or network constraints that require specific trust exceptions?
Hardening decisions that ignore cross-functional dependencies cause outages or
immediate rollbacks.
```

**Detection hint:** If the advice assumes a single-admin-controls-everything model without mentioning integration or browser requirements, it is likely to cause downstream conflicts.
