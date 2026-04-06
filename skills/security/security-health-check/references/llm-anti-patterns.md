# LLM Anti-Patterns — Security Health Check

Common mistakes AI coding assistants make when generating or advising on Salesforce Security Health Check.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Equating a 100% Score with Full Org Security

**What the LLM generates:** "Your org is fully secure because the Health Check score is 100%."

**Why it happens:** Training data treats Health Check as a comprehensive security assessment. In reality, it measures a subset of settings (password, session, network, authentication) and does not cover CSP governance, CORS, sharing model, encryption, or event monitoring.

**Correct pattern:**

```
A 100% Health Check score means the org meets or exceeds the active baseline
for the settings Health Check evaluates. It does NOT indicate:
- Proper CSP Trusted Sites or CORS governance
- Correct sharing model or permission architecture
- Shield encryption or event monitoring configuration
- Release update hygiene or clickjack protections

Health Check is one input to security posture, not a complete assessment.
```

**Detection hint:** If the advice treats a high Health Check score as proof of comprehensive security, it is conflating a subset tool with the full security posture.

---

## Anti-Pattern 2: Relaxing a Custom Baseline to Improve the Score

**What the LLM generates:** "Move the failing setting to Informational in your custom baseline so the score improves."

**Why it happens:** LLMs optimize for the metric (score) rather than the outcome (security). Suggesting a baseline change that improves the number is a common pattern.

**Correct pattern:**

```
A custom baseline should NEVER relax settings below the Salesforce standard
threshold solely to improve the numeric score. Moving a failing setting to
Informational removes it from scoring but does NOT fix the misconfiguration.
A 100% score against a permissive custom baseline provides no meaningful
security assurance. Every deviation from the Salesforce standard must be
documented with a genuine business justification.
```

**Detection hint:** If the advice suggests changing the baseline (rather than fixing the setting) to improve the score, it is score manipulation, not remediation.

---

## Anti-Pattern 3: Using the "Fix It" Button Without Verifying the Result

**What the LLM generates:** "Click the Fix It button next to each failing setting to remediate it."

**Why it happens:** LLMs recommend the simplest UI path. The Fix It button exists and appears to be a one-click solution.

**Correct pattern:**

```
The "Fix It" button applies the SALESFORCE STANDARD baseline value, not your
custom baseline value. If your org uses a custom baseline with stricter
thresholds, "Fix It" may set the value to the Salesforce standard — which is
LESS strict than your custom requirement.

After using "Fix It", always verify:
1. The resulting value matches your custom baseline threshold (if applicable).
2. The change does not conflict with operational requirements (e.g., session
   timeout too short for mobile users).
```

**Detection hint:** If the advice recommends "Fix It" without mentioning that it applies the Salesforce standard (not custom baseline) value, the resulting setting may still fail a custom baseline check.

---

## Anti-Pattern 4: Ignoring Post-Release Score Drops

**What the LLM generates:** Advice that treats the Health Check score as stable across Salesforce releases without mentioning that the standard baseline can change.

**Why it happens:** LLMs generate static configuration advice. They do not model the fact that Salesforce can tighten standard baseline thresholds or add new settings in any major release.

**Correct pattern:**

```
The Salesforce standard baseline can change between releases. A score that was
95% before a Spring/Summer/Winter release can drop immediately after the release
without any admin action. New settings may be added that default to a
non-compliant state.

Post-release Health Check review is a required operational cadence — not
optional maintenance. After every major Salesforce release, re-run Health Check
and investigate any score changes.
```

**Detection hint:** If the advice assumes the Health Check score is stable unless an admin changes something, it misses the release-driven baseline drift.

---

## Anti-Pattern 5: Treating Informational Items as Unimportant

**What the LLM generates:** "Informational items don't affect the score, so you can ignore them."

**Why it happens:** LLMs associate zero score impact with zero risk. Informational items do not affect the numeric score, but they may still represent real security gaps.

**Correct pattern:**

```
Informational items do not affect the Health Check score, but they are tracked
for a reason. They may represent:
- Real risks that Salesforce categorized as informational due to low prevalence
- Settings that should be promoted to a higher risk category in a custom baseline
- Audit-relevant findings that compliance reviewers will still flag

Review Informational items for genuine risk, even though remediating them does
not change the score.
```

**Detection hint:** If the advice dismisses all Informational items as irrelevant because they do not affect the score, real risks may be ignored.

---

## Anti-Pattern 6: Querying the Wrong Tooling API Object for Risk Details

**What the LLM generates:** "Query SecurityHealthCheck to get the list of failing settings."

**Why it happens:** LLMs conflate the two Tooling API objects. `SecurityHealthCheck` returns only the overall score; `SecurityHealthCheckRisks` returns the individual setting details.

**Correct pattern:**

```
Two Tooling API objects serve different purposes:
- SecurityHealthCheck → returns the overall org score (one row)
- SecurityHealthCheckRisks → returns individual risk findings with SettingName,
  RiskType, OrgValue, StandardValue, and MeetsStandard

To get failing settings:
  SELECT SettingName, RiskType, OrgValue, StandardValue, MeetsStandard
  FROM SecurityHealthCheckRisks
  WHERE MeetsStandard = false
  ORDER BY RiskType ASC

Both are read-only Tooling API objects queried via the Tooling API endpoint.
```

**Detection hint:** If the advice queries SecurityHealthCheck expecting individual setting details, it will only receive the score, not the risk findings.
