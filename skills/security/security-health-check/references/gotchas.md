# Gotchas — Security Health Check

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: Sandbox Refresh Silently Resets Security Settings

**What happens:** After refreshing a sandbox from production, the sandbox Health Check score is lower than production's score. Password policy and session settings in the sandbox do not match the production values even though the refresh is supposed to copy org configuration.

**When it occurs:** Sandbox creation and refresh operations do not guarantee a full copy of all security settings. Some settings — particularly around session security level requirements and network access controls — may revert to Salesforce defaults during the sandbox provisioning process. This is not consistently documented per-setting; the behavior varies by sandbox type (Full, Partial, Developer).

**How to avoid:** After every sandbox refresh, open Setup → Health Check in the sandbox and compare its score and findings against production. Do not assume the sandbox mirrors production's security posture. If you use the sandbox for security testing or compliance validation, remediate Health Check findings in the sandbox explicitly rather than assuming they were inherited from production.

---

## Gotcha 2: The "Fix It" Button Applies the Salesforce Standard, Not Your Custom Baseline

**What happens:** An org using a custom baseline with stricter-than-Salesforce thresholds has a failing setting. An admin clicks "Fix It" next to the setting in the Health Check UI. The setting is remediated — but to the Salesforce standard value, not the custom baseline's stricter requirement. The Health Check score does not improve because the setting still fails against the custom baseline threshold.

**When it occurs:** Any time a custom baseline is active and the admin uses the "Fix It" shortcut. The UI's "Fix It" functionality is tied to the Salesforce standard thresholds, not the imported custom baseline thresholds.

**How to avoid:** When a custom baseline is in use, do not rely on "Fix It" for accurate remediation. Instead, look at the "Your Value" and "Standard Value" columns in the Health Check UI — where "Standard Value" reflects the custom baseline threshold — and manually set the setting to meet or exceed that threshold. Verify the resulting value is correct before trusting the score improvement.

---

## Gotcha 3: Informational Reclassification Does Not Survive a Baseline Re-Import

**What happens:** An admin exports the baseline, demotes a specific setting to Informational, and re-imports it. The setting is excluded from the score as expected. Later, a new version of the custom baseline is imported (for example, because the compliance team updated their requirements). The previously-demoted setting reverts to its original risk category in the new baseline file, which was built from a fresh export.

**When it occurs:** Custom baseline XML files are version-controlled independently of the Setup UI state. If a team maintains multiple versions of a baseline file and imports a version that did not include the Informational overrides, those overrides are lost. There is no in-product merge or diff mechanism for baseline versions.

**How to avoid:** Treat the custom baseline XML as a versioned artifact in source control. Maintain a single "canonical" file that includes all risk category overrides, with inline comments documenting each deviation. Every import should come from the canonical file, not an ad-hoc export. Use a checklist before importing any baseline to confirm all expected Informational overrides are present in the file.

---

## Gotcha 4: The Salesforce Standard Baseline Can Tighten Without Notice Between Releases

**What happens:** An org with a 95% Health Check score has not changed any security settings. After a major Salesforce release activates (Spring, Summer, or Winter), the score drops to 82%. No admin action caused the drop.

**When it occurs:** Salesforce may update the standard baseline thresholds or add new settings to the Health Check evaluation as part of any major release. For example, a release may add a new session cookie security setting that did not previously exist. Because orgs do not proactively configure settings that do not yet exist, the new setting defaults to a non-compliant value. From the Health Check tool's perspective, this is a new failing setting, which reduces the score.

**How to avoid:** Schedule a Health Check review within the first week after each major Salesforce release activates in your production org. Treat Health Check score maintenance as a recurring operational task, not a one-time configuration activity. If you use a custom baseline, also check whether Salesforce updated the standard baseline for any settings your custom baseline inherits — your XML may need updating to reflect new settings.

---

## Gotcha 5: Score Can Be 100% Against a Weaker Custom Baseline While the Org Is Not Secure

**What happens:** A team reports that Health Check score is 100%, implying the org is fully hardened. In reality, a custom baseline was imported that set most password and session thresholds to the minimum values Salesforce accepts, making it trivially easy to pass. Stakeholders interpret 100% as "maximum security" when it actually means "compliant with a minimally-strict custom standard."

**When it occurs:** This happens when custom baselines are used primarily for score management rather than genuine compliance alignment. Because the import mechanism does not warn when a custom baseline is weaker than the Salesforce standard, the resulting score can be misleading.

**How to avoid:** When reviewing or presenting Health Check scores, always disclose which baseline is in use — Salesforce Standard or a named custom baseline. When evaluating a custom baseline, compare every threshold against the Salesforce standard and flag any setting where the custom threshold is more lenient. A meaningful score requires a baseline that is at least as strict as the Salesforce standard in every category.
