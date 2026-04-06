# LLM Anti-Patterns -- Metadata API Coverage Gaps

Common mistakes AI coding assistants make when advising on Salesforce metadata coverage gaps.
These patterns help the consuming agent self-check its own output.

---

## Anti-Pattern 1: Claiming a metadata type is universally unsupported without checking the API version

**What the LLM generates:** "ForecastingSettings is not supported by Metadata API and must always be configured manually."

**Why it happens:** Training data includes older documentation where the type was unsupported. Support status changes across API versions, but LLMs treat it as static.

**Correct pattern:**

```text
ForecastingSettings has partial support that varies by API version and org configuration.
Check the Metadata Coverage Report for your specific API version at
developer.salesforce.com/docs/metadata-coverage before concluding it is unsupported.
```

**Detection hint:** Absolute statements like "is not supported" or "cannot be deployed" without referencing a specific API version.

---

## Anti-Pattern 2: Suggesting package.xml wildcard retrieval will catch unsupported types

**What the LLM generates:** "Use `<members>*</members>` for the metadata type in package.xml to retrieve all components, including any that might be unsupported."

**Why it happens:** LLMs generalize the wildcard pattern without understanding that unsupported types are not returned by the Metadata API regardless of the query.

**Correct pattern:**

```xml
<!-- Wildcard retrieval only returns SUPPORTED types.
     Unsupported types must be handled via Tooling API,
     manual Setup configuration, or data export. -->
<types>
    <members>*</members>
    <name>CustomObject</name>
</types>
```

**Detection hint:** Suggesting wildcard `*` retrieval as a workaround for unsupported types.

---

## Anti-Pattern 3: Conflating Metadata API support with source tracking support

**What the LLM generates:** "Since CustomSetting is supported by Metadata API, your scratch org source tracking will automatically detect changes to it."

**Why it happens:** LLMs do not distinguish between the four coverage channels (Metadata API, source tracking, unlocked packages, managed packages). Support in one channel does not guarantee support in another.

**Correct pattern:**

```text
Metadata API support and source tracking support are independent.
Check the Metadata Coverage Report for BOTH columns.
CustomSetting is supported by Metadata API but may not be fully
source-tracked depending on the specific sub-type (list vs. hierarchy).
```

**Detection hint:** Phrases like "since it is supported" that infer one channel's support from another's.

---

## Anti-Pattern 4: Recommending the Tooling API as a universal workaround

**What the LLM generates:** "For any unsupported metadata type, use the Tooling API to deploy it programmatically as a workaround."

**Why it happens:** The Tooling API exposes many metadata-like objects, so LLMs overgeneralize it as a full replacement for Metadata API. In reality, many Tooling API objects are read-only or do not support DML operations needed for deployment.

**Correct pattern:**

```text
The Tooling API is a workaround for SOME unsupported types (e.g., FlowDefinition
activation). Verify that the specific Tooling API object supports CREATE or UPDATE
operations before recommending it. Many Tooling API objects are read-only.
For truly unsupported types, manual Setup configuration documented in a
release runbook is the only option.
```

**Detection hint:** Blanket statements like "use the Tooling API to deploy" without specifying the exact object and verifying its DML support.

---

## Anti-Pattern 5: Generating fabricated metadata type names

**What the LLM generates:** "The `OrgSecurityPolicy` metadata type is not supported by Metadata API" or "Use the `DeploymentConfiguration` type in package.xml."

**Why it happens:** LLMs hallucinate plausible-sounding metadata type names that do not exist in the Salesforce platform. These fabricated names waste practitioner time when they search for documentation.

**Correct pattern:**

```text
Only reference metadata type names that appear in the Metadata API Developer Guide
or the Metadata Coverage Report. If unsure whether a type exists, direct the
practitioner to search the Coverage Report rather than guessing.
```

**Detection hint:** Any metadata type name not found in the Metadata API Developer Guide's type reference or the Coverage Report.

---

## Anti-Pattern 6: Advising to remove .forceignore entries to "fix" deployment failures

**What the LLM generates:** "Your deployment is failing because the type is in .forceignore. Remove the entry and redeploy."

**Why it happens:** LLMs pattern-match deployment errors to exclusion patterns without considering that the `.forceignore` entry may exist specifically to prevent deployment of an unsupported type.

**Correct pattern:**

```text
Before removing a .forceignore entry, check WHY it was added.
If the entry excludes an unsupported metadata type, removing it will cause
deployment failures rather than fixing them. Check the Metadata Coverage Report
and the project's release runbook for context on each exclusion.
```

**Detection hint:** Suggesting removal of `.forceignore` entries without checking the type's support status.

---

## Anti-Pattern 7: Omitting the release runbook when recommending exclusion

**What the LLM generates:** "Add ForecastingSettings to .forceignore to fix the deployment error." (No mention of documenting the manual steps.)

**Why it happens:** LLMs optimize for fixing the immediate error without considering the downstream impact. Excluding a type from deployment solves the CI failure but creates silent configuration drift if the manual steps are not documented.

**Correct pattern:**

```text
1. Add ForecastingSettings to .forceignore to prevent deployment failures.
2. Document the manual configuration steps in the release runbook:
   - Setup path: Setup > Forecasts Settings > Configure Forecasting
   - Values to set: [specify]
   - Verification: [specify how to confirm]
   - Owner: [specify who executes this step]
```

**Detection hint:** Recommending `.forceignore` exclusion without a corresponding release runbook entry.
