# LLM Anti-Patterns — Fit-Gap Analysis Against Org

Common mistakes AI assistants make when generating or advising on fit-gap matrices.
Each entry: what the LLM generates wrong, why it happens, the correct pattern, and a detection hint the consuming agent can use to self-check.

---

## Anti-Pattern 1: Scoring the Matrix Without Probing the Org

**What the LLM generates:** A complete fit-gap table produced from the requirements list alone, with no input on the target org's edition, license SKUs, installed managed packages, or existing automation.

**Why it happens:** LLMs are trained on Salesforce-Help text that describes features as "available in Enterprise and above" — they generalize that to "available in the customer's org" without verifying.

**Correct pattern:**

```
Step 2 of Recommended Workflow:
- Confirm edition (Setup → Company Information)
- List installed managed packages (Setup → Installed Packages)
- Count user license SKUs and Permission Set License SKUs per persona
- Inventory existing flows and triggers on in-scope sObjects

THEN score row 1.
```

**Detection hint:** If the matrix exists but no org-probe summary precedes it, reject and re-run.

---

## Anti-Pattern 2: Calling Apex "Low-Code"

**What the LLM generates:** Rows with a custom Apex trigger or @future callout marked as "Low-Code" because the reviewer reasons "Apex is just declarative-with-extra-steps."

**Why it happens:** Marketing language in Salesforce decks blurs the line. LLMs absorb "low-code platform" as a brand attribute and apply it broadly.

**Correct pattern:**

```
Apex / LWC / external integration → Custom (always).
Flow / Dynamic Forms / formula / validation rules → Low-Code.
```

**Detection hint:** Any row whose `notes` field mentions Apex, LWC, callout, REST, or `@future` must have `tier: Custom`.

---

## Anti-Pattern 3: Ignoring Sandbox vs Production Feature Deltas

**What the LLM generates:** A matrix that assumes a feature is enabled because the demo sandbox has it on.

**Why it happens:** The LLM has seen the feature mentioned in conversation logs about the sandbox and assumes parity.

**Correct pattern:**

```
Probe target = production (or the org that will receive the build).
If only sandbox is accessible, every Standard row dependent on a feature flag carries a `governance` tag pending production confirmation.
```

**Detection hint:** If the probe summary names a sandbox (e.g. "DEV", "UAT", "FullCopy") and the matrix has no `governance` tags, the matrix is suspect.

---

## Anti-Pattern 4: Ignoring Permission Cliffs

**What the LLM generates:** A row marked as Standard for end users when the feature actually requires a Setup-level permission (Customize Application, Manage Knowledge, Modify All Data) for the consuming persona.

**Why it happens:** Salesforce-Help "feature available in Enterprise" is read as "feature usable by all users" — the permission-set requirement is a separate paragraph the LLM skips.

**Correct pattern:**

```
For every Standard row, verify the consuming persona's permission set includes the system permissions and object/field-level access needed.
If end users need Setup access → re-classify as Configuration (permission-set authoring task) at minimum.
```

**Detection hint:** Standard rows with feature names like "Knowledge", "Lightning App Builder edits", "Report subscriptions for others" should be checked for permission-cliff risk.

---

## Anti-Pattern 5: Failing to Chunk by sObject

**What the LLM generates:** A flat list of 80 requirements with no grouping.

**Why it happens:** The LLM treats each row as independent and skips the second-order analysis.

**Correct pattern:**

```
After scoring, group by primary sObject. Surface:
- "Object X has 14 Configuration rows + 6 Low-Code rows" → object-designer + flow-builder workload per object
- "Object Y has 0 Standard rows" → red flag for over-customization
- "Object Z has 8 Custom rows" → trigger consolidation review per `apex/trigger-consolidation`
```

**Detection hint:** If the JSON output is a flat list with no per-sObject summary, the agent skipped this step.

---

## Anti-Pattern 6: Missing the Wrong-Platform Escape Hatch

**What the LLM generates:** A row marked Custom (Apex) for a requirement that genuinely belongs on a different platform — ETL pipelines that should be in MuleSoft, real-time analytics that should be in CRM Analytics or Tableau, OLAP queries that belong in a data warehouse.

**Why it happens:** The LLM's job is to fit work into Salesforce, so it does. The "this is wrong-platform" classification feels like a refusal.

**Correct pattern:**

```
Unfit is a valid, healthy classification. Use it for:
- ETL or large-batch transformations → MuleSoft / iPaaS
- Real-time multi-source analytics → CRM Analytics / Tableau / Data Cloud
- Sub-100ms cross-org sync → middleware
- OLAP-style query patterns → data warehouse + Salesforce Connect

Each Unfit row cites the relevant standards/decision-trees/ branch.
```

**Detection hint:** If the matrix has zero Unfit rows AND any requirement mentions ETL / real-time analytics / cross-system orchestration, the agent missed escape hatches.

---

## Anti-Pattern 7: Conflating "Configuration" and "Low-Code"

**What the LLM generates:** Validation rules and formula fields classified as Configuration; record-triggered Flow without conditional logic classified as Low-Code.

**Why it happens:** The 5-tier rubric is non-obvious — many sources collapse the tiers into "Standard / Customization."

**Correct pattern:**

```
Configuration = point-and-click only. NO formula language, NO Flow, NO validation rule logic.
Low-Code = formula / validation / Flow / Dynamic Forms with conditional logic.
```

**Detection hint:** Any row mentioning "validation rule", "formula", "Flow", or "Dynamic Forms" must be Low-Code at minimum, never Configuration.
