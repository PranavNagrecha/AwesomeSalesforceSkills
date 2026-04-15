# LLM Anti-Patterns — Data Cloud Identity Resolution

Common mistakes AI coding assistants make when generating or advising on Data Cloud Identity Resolution.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Confusing Data Cloud Identity Resolution with CRM Duplicate Rules

**What the LLM generates:** "To configure identity resolution in Salesforce, go to Setup > Duplicate Management > Duplicate Rules and create a new rule using the Standard Contact matching rule. This will merge duplicate Contact records and create a unified view of the customer."

**Why it happens:** LLMs conflate "identity resolution" (a Data Cloud platform feature for Unified Individuals) with "duplicate management" (a CRM platform feature for deduplicating sObject records). Both involve comparing records and identifying matches, so training data about either topic bleeds into the other. The LLM is also more likely to have seen general Salesforce CRM documentation than Data Cloud-specific content.

**Correct pattern:**

```text
Data Cloud Identity Resolution:
- Operates on DMO records (Individual, Contact Point Email, etc.)
- Produces Unified Individual profiles (NOT CRM record merges)
- Configured in Data Cloud Setup > Identity Resolution
- Uses Match Rules and Reconciliation Rules within an Identity Resolution Ruleset
- Does NOT modify CRM Contact or Account records

CRM Duplicate Management (different feature entirely):
- Operates on CRM sObject records (Contact, Lead, Account)
- Configured in Setup > Duplicate Management > Duplicate Rules
- Uses Matching Rules on standard/custom sObjects
- Can block saves or alert on duplicates
- Does NOT create Unified Individuals
```

**Detection hint:** Any response that mentions "Duplicate Rules", "Matching Rules" (the CRM object), or Setup > Duplicate Management when the user asked about Data Cloud identity resolution is applying the wrong platform feature.

---

## Anti-Pattern 2: Treating Fuzzy Match as Real-Time-Capable

**What the LLM generates:** "For real-time identity resolution as customers browse your website, configure a Fuzzy match rule on Individual > First Name. This will ensure that even as events arrive in real time, customers are correctly unified even if their names vary slightly across systems."

**Why it happens:** The LLM knows that Data Cloud supports real-time resolution and that Fuzzy match exists as a match rule type. It does not know that the real-time resolution code path evaluates only Exact and Exact Normalized match methods. The LLM reasons by feature capability alone and misses the batch-only constraint.

**Correct pattern:**

```text
Real-time resolution path supports:
  - Exact (any field)
  - Exact Normalized (email, phone)

Real-time resolution does NOT evaluate:
  - Fuzzy (first name) — batch-only
  - Full address Normalized — batch-only

If real-time fidelity is required:
  Use Exact or Exact Normalized match rules only.
  Accept that fuzzy name variations will only be resolved on the next batch run.
```

**Detection hint:** Any recommendation to use Fuzzy match in a context where real-time resolution latency is described as a requirement is incorrect.

---

## Anti-Pattern 3: Assuming the Ruleset ID Can Be Changed or Is Cosmetic

**What the LLM generates:** "Don't worry about the 4-character ID when creating the ruleset — you can always rename it later in the ruleset settings. For now, just use 'TEST' to get started."

**Why it happens:** LLMs frequently treat configuration names and IDs as cosmetic and reversible, which is true for most Salesforce metadata (renaming a flow, a field API name with a migration, etc.). The immutability of the Data Cloud identity resolution ruleset ID is a specific platform constraint not widely represented in training data.

**Correct pattern:**

```text
Identity resolution ruleset ID:
- 4-character alphanumeric, assigned at creation time
- CANNOT be changed after the ruleset is saved
- Embedded in activation targets, data actions, and API references
- If the wrong ID was used, the only remediation is:
  1. Delete the ruleset (consuming the slot permanently for that ID)
  2. Recreate with the correct ID (uses the second slot)
- Choose the ID as if it is permanent — because it is.

Naming convention example:
  EMLP → Email Primary
  PHNC → Phone + Compound Name
  CMPS → Compound (Name + Address)
```

**Detection hint:** Any suggestion to use a temporary, test, or placeholder ID for a Data Cloud identity resolution ruleset is incorrect.

---

## Anti-Pattern 4: Claiming More Than 2 Rulesets Can Be Created in a Single Org

**What the LLM generates:** "For a multi-BU implementation, create one identity resolution ruleset per business unit. You can create as many rulesets as needed and scope each one to the appropriate data space."

**Why it happens:** LLMs generalize from other Salesforce features where per-BU or per-team configurations can scale horizontally (e.g., multiple flows, multiple connected apps, multiple data streams). The 2-ruleset hard limit is a specific Data Cloud platform constraint that is not reflected in most Salesforce configuration documentation.

**Correct pattern:**

```text
Hard org-level limit: 2 identity resolution rulesets per Data Cloud org.

This limit:
  - Counts all rulesets, including auto-created Starter Data Bundle rulesets
  - Cannot be raised by a support case
  - Is not per-data-space or per-BU — it is per org

Multi-BU options within the 2-ruleset limit:
  - Shared ruleset with OR-combined match rules covering both BUs' identity attributes
  - Separate Data Cloud orgs (higher cost and operational complexity)
  - Accept that one BU's identity attributes will not have a dedicated ruleset
```

**Detection hint:** Any recommendation to create more than 2 identity resolution rulesets in a single Data Cloud org, or any claim that the limit is configurable, is incorrect.

---

## Anti-Pattern 5: Recommending Reconciliation Rule Changes as a Low-Risk Fix

**What the LLM generates:** "To fix the incorrect phone number appearing in your Unified Individual profiles, simply update the reconciliation rule for the Phone field from 'Most Recent' to 'Source Priority' and set CRM as rank 1. This will immediately update the affected profiles."

**Why it happens:** LLMs model configuration changes as instant and incremental by default. They do not know that reconciliation rule changes in Data Cloud identity resolution trigger a full re-run rather than an incremental update. The concept of "a configuration change that requires hours-long batch reprocessing before taking effect" is counterintuitive and underrepresented in training data.

**Correct pattern:**

```text
Changing any reconciliation rule on an existing ruleset:
  - Does NOT update existing Unified Individual clusters immediately
  - Triggers a full re-run of the entire ruleset on the next scheduled or manual run
  - Re-run duration: minutes (small orgs) to hours (millions of Individual records)
  - During re-run: downstream segments and activations see stale Unified Individual values

Pre-change checklist:
  1. Estimate re-run duration from the most recent scheduled run's elapsed time
  2. Communicate the maintenance window to downstream teams (segmentation, activation, Agentforce)
  3. Schedule the change during a low-traffic window
  4. Do not make changes during campaign launch windows
```

**Detection hint:** Any suggestion that a reconciliation rule change will "immediately" or "quickly" update existing Unified Individual profiles is incorrect.

---

## Anti-Pattern 6: Applying Normalized Match Type to Fields Not Supported for Normalization

**What the LLM generates:** "Use a Normalized match rule on the Individual > Last Name field to handle inconsistent formatting across sources."

**Why it happens:** The LLM knows that Normalized match is a valid match type in Data Cloud and correctly understands that it pre-processes values before comparison. It does not know that Normalized match is only supported on specific Contact Point DMO fields (Email Address, Phone Number, Address fields) and is not available for Individual DMO fields like First Name or Last Name.

**Correct pattern:**

```text
Normalized match is supported on:
  - Contact Point Email > Email Address (lowercases, trims whitespace)
  - Contact Point Phone > Phone Number (strips formatting, normalizes country code)
  - Contact Point Address > Street, City, State, Postal Code (USPS-style standardization)

Normalized match is NOT supported on:
  - Individual > First Name (use Fuzzy for partial match, or Exact)
  - Individual > Last Name (use Exact)
  - Custom DMO fields (Exact only)

For name fields with formatting inconsistencies across sources:
  Use data prep / transform steps in the data stream mapping to normalize
  values before they reach the Individual DMO, then use Exact match.
```

**Detection hint:** Any recommendation to apply Normalized match type to an Individual DMO field (First Name, Last Name, etc.) is incorrect.
