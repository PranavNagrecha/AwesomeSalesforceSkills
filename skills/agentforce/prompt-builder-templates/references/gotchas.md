# Gotchas — Prompt Builder Templates

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: Inactive Templates Fail Silently With No User-Facing Error

**What happens:** When a prompt template has no active version, the Einstein button for Field Generation templates disappears from the record page, agent actions bound to the template return no output, and no error message appears anywhere — not in the UI, not in debug logs, and not in event monitoring. From the user's perspective, the feature simply does not exist.

**Why it occurs:** Template activation is a discrete state in Salesforce; an inactive template is treated as if it were never configured. The platform does not surface a "template is inactive" warning in App Builder, on the record page, or in Agentforce agent diagnostics.

**How to avoid:** Build activation state into your deployment checklist. After deploying a template change (or after a sandbox refresh that resets activation state), explicitly navigate to Prompt Builder in Setup and confirm the intended version is active. Do not rely on visual layout inspection to confirm a template is working — the Einstein button renders only when the template is active AND the user has the required permissions. Test with a real record as the final check.

---

## Gotcha 2: Manage Prompt Templates Permission Must Exist in Subscriber Orgs for Packaged Templates

**What happens:** A managed package that includes prompt templates installs successfully in a subscriber org even when no user in that org has the Manage Prompt Templates permission. The templates appear in Setup and in package metadata, but they cannot be invoked. Users see no Einstein buttons, agent actions produce no output, and there is no install-time warning or post-install error.

**Why it occurs:** Salesforce validates package installability independently of the permission assignments needed to use packaged features. The install step confirms metadata integrity, not runtime permission readiness. The Manage Prompt Templates permission is required at invocation time, not at install time.

**How to avoid:** Document the Manage Prompt Templates permission as an explicit post-installation requirement in your package release notes and install guide. Automate the check: after any package install or upgrade, verify that at least one permission set in the subscriber org includes Manage Prompt Templates before marking the deployment complete. The `check_prompt_builder_templates.py` script in this skill's `scripts/` directory scans for this permission assignment in permission set metadata.

---

## Gotcha 3: Flow Grounding Failures Return Empty String, Not an Error

**What happens:** A Template-Triggered Prompt Flow that grounds a prompt template throws a runtime fault (SOQL exception, null variable dereference, governor limit hit). Instead of surfacing an error in the Resolved Prompt or the Generated Response, the merge field that references the flow resolves to an empty string. The LLM receives an incomplete prompt and generates plausible-looking but factually wrong output. This appears as a quality problem, not a system error, and is extremely difficult to trace without independent flow testing.

**Why it occurs:** The platform treats a failed grounding flow as a graceful degradation — the prompt is sent to the LLM without the missing data rather than blocking the request. This design prevents hard failures from blocking all generative AI output, but it makes silent data loss the default error mode.

**How to avoid:** Test every Template-Triggered Prompt Flow independently in Flow Builder using representative test data before binding it to a template. Add fault connectors to all flow paths and route them to a custom platform event or custom log object so failures are observable. After any deployment that modifies grounding flows, re-run Save & Preview in Prompt Builder against a real record and inspect the Resolved Prompt panel to confirm all flow-injected text is present.

---

## Gotcha 4: Apex Capability Type Mismatch Is Silent

**What happens:** An `@InvocableMethod` intended to ground a Flex template is decorated with a `capabilityType` string that does not exactly match the template's API name. The Apex class deploys successfully, the template activates successfully, and preview runs without error — but the Apex data is simply absent from the Resolved Prompt. The LLM generates output without the grounded data, typically producing hallucinated or generic content.

**Why it occurs:** The capability type matching is a runtime binding, not a compile-time or deploy-time validation. Salesforce does not surface a mismatch as a warning in Prompt Builder or in Apex compilation. Common causes: the template was renamed after the Apex was written, the API name was hand-typed with a case error, or the namespace prefix was omitted in a namespaced org.

**How to avoid:** Treat the capability type string as a contractual constant. Define it as a named constant in the Apex class rather than an inline string literal, and document it in the class header comment alongside the template API name. After any template rename, update the Apex capability type and redeploy. Always verify via Save & Preview that the Resolved Prompt contains the Apex-injected text, not just that the preview completes without error.

---

## Gotcha 5: New Custom Objects and Fields Are Invisible in Prompt Builder Until Session Refresh

**What happens:** An admin creates a new custom object or custom field and immediately navigates to Prompt Builder to use the new field as a merge field resource. The Insert Resource panel does not show the new field. The admin assumes a permission issue or a metadata deployment error.

**Why it occurs:** Prompt Builder's resource picker reads available objects and fields from the session cache. Newly created metadata is not reflected until the current admin session is refreshed — the admin must log out and log back in (or open a new private browser window with a fresh session).

**How to avoid:** After creating new custom fields or objects intended for use in a prompt template, log out and log back in before opening Prompt Builder. Include this step explicitly in any runbook or deployment checklist that involves adding new fields to an existing template.
