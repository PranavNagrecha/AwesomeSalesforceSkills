# LLM Anti-Patterns — OmniStudio Admin Configuration

Common mistakes AI coding assistants make when generating or advising on OmniStudio admin configuration. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating Permission Set Assignment as the Only Required Step

**What the LLM generates:** "Assign the OmniStudio Admin permission set to your builders and OmniStudio User to your consumers — that's all you need to set up OmniStudio access."

**Why it happens:** LLMs are trained on Salesforce documentation that covers permission sets extensively, but the additional PSL (Permission Set License) requirement is less prominent. The PSL-then-permission-set ordering constraint is a licensing detail that tends to get underweighted in general access-control guidance.

**Correct pattern:**

```
Step 1: Assign OmniStudioPSL Permission Set License to the user account.
Step 2: Confirm PSL is active for the user.
Step 3: Assign OmniStudio Admin (builders) or OmniStudio User (consumers).
Step 4: Verify the user can access the OmniStudio app tab.
```

**Detection hint:** Any response that instructs permission set assignment without mentioning PSL provisioning first should be flagged. Look for guidance that skips directly to "assign permission set" without a prior "assign PSL" step.

---

## Anti-Pattern 2: Claiming Standard Runtime Can Be Reversed Per Component

**What the LLM generates:** "You can enable Standard OmniStudio Runtime to test native components, and revert individual components back to Managed Package Runtime if needed."

**Why it happens:** LLMs often model feature toggles as bidirectional because most Salesforce settings can be reversed. The per-component irreversibility of the Standard Runtime transition is a platform-specific constraint that contradicts the general pattern.

**Correct pattern:**

```
Standard OmniStudio Runtime enablement is ONE-WAY per component.
Once a component is opened and saved in the Standard designer, it 
cannot be reverted to Managed Package Runtime.

Before enabling Standard Runtime in any org, audit all existing 
components and create a complete migration plan. Treat the toggle 
as a migration checkpoint, not a feature flag.
```

**Detection hint:** Any response that implies reversibility ("you can switch back," "revert to managed package," "toggle off per component") is incorrect. Flag guidance that does not explicitly call out the irreversibility.

---

## Anti-Pattern 3: Omitting the Runtime Namespace Field

**What the LLM generates:** A setup guide for OmniStudio that covers enabling Standard Runtime and assigning permission sets, but never mentions the Runtime Namespace field in OmniStudio Settings.

**Why it happens:** The Runtime Namespace field is a less-documented setting that does not appear in most high-level OmniStudio setup overviews. LLMs frequently skip it because it is not covered in the narrative portions of docs that training data tends to capture well.

**Correct pattern:**

```
OmniStudio Settings — required configuration:
  1. Standard OmniStudio Runtime: enabled (for native orgs)
  2. Runtime Namespace: set to the correct value
     - omnistudio  (native / no managed package)
     - vlocity_ins (Insurance and Health Cloud)
     - vlocity_cmt (Communications Cloud)
     - vlocity_ps  (Public Sector Solutions)
  3. Disable Managed Package Runtime: enabled once migration is complete
```

**Detection hint:** Any OmniStudio setup response that does not mention the Runtime Namespace field is incomplete. Flag guides that jump from "enable Standard Runtime" to "assign permissions" without covering namespace configuration.

---

## Anti-Pattern 4: Assuming OmniStudio User Permission Set Is Sufficient for Community Users

**What the LLM generates:** "To allow community users to access OmniScripts, assign the OmniStudio User permission set to the community profile."

**Why it happens:** The standard OmniStudio User permission set is the obvious answer for user-level access. The additional community consumer custom permission requirement is documented in a separate Experience Cloud integration section that LLMs often miss or conflate with the main permission setup.

**Correct pattern:**

```
For Experience Cloud / community user access:
  1. Assign OmniStudioPSL PSL to the community user.
  2. Assign OmniStudio User permission set to the community profile.
  3. Create a new Permission Set with the custom permission 
     "OmniStudio Community User" enabled.
  4. Assign that custom permission set to the community profile 
     or Experience Cloud permission set group.
  
Both the standard OmniStudio User permission set AND the community 
consumer custom permission are required. Neither alone is sufficient.
```

**Detection hint:** Any guidance for community user OmniStudio access that stops at `OmniStudio User` permission set assignment without mentioning a separate community consumer custom permission is incomplete. Flag responses that do not mention custom permissions for community context.

---

## Anti-Pattern 5: Recommending a Fixed Namespace Value Without Org Verification

**What the LLM generates:** "Set the Runtime Namespace to `vlocity_cmt` in OmniStudio Settings." (without checking which namespace is actually installed)

**Why it happens:** LLMs tend to default to a specific example value from training data rather than acknowledging that the correct value is org-dependent. `vlocity_cmt` appears frequently in documentation examples, which biases recommendations toward it regardless of the actual org configuration.

**Correct pattern:**

```
Step 1: Determine the installed namespace before configuring.
  - In Setup > Installed Packages, check which package is installed:
    vlocity_ins, vlocity_cmt, vlocity_ps, or omnistudio (native)
  - If no managed package is installed and Standard Runtime is enabled,
    use: omnistudio

Step 2: Set Runtime Namespace to the value that matches the installed package.

Never hardcode a namespace value without confirming it against the 
actual Installed Packages list in the target org.
```

**Detection hint:** Any response that prescribes a specific namespace value (`vlocity_cmt`, `vlocity_ins`, `omnistudio`) without first instructing the user to verify which package is installed is potentially incorrect. The namespace must always be derived from the actual org state.

---

## Anti-Pattern 6: Ignoring Sandbox Refresh Impact on OmniStudio Settings

**What the LLM generates:** A deployment or environment setup guide that configures OmniStudio Settings once in production and assumes the values will persist correctly in sandbox environments.

**Why it happens:** Most Salesforce custom settings and metadata deploy reliably across environments. LLMs generalize this behavior and do not flag OmniStudio Settings as a configuration category that may require explicit post-refresh verification.

**Correct pattern:**

```
Post-sandbox-refresh OmniStudio checklist:
  1. Log in to the refreshed sandbox.
  2. Navigate to Setup > OmniStudio Settings.
  3. Verify Runtime Namespace value — do not assume it was preserved.
  4. Verify Standard OmniStudio Runtime toggle is in the expected state.
  5. Verify Disable Managed Package Runtime toggle if applicable.
  6. Activate a test component to confirm the configuration is operational.
```

**Detection hint:** Any deployment or sandbox runbook that configures OmniStudio Settings without an explicit post-refresh verification step is incomplete. Flag guides that treat OmniStudio Settings as a set-once configuration.
