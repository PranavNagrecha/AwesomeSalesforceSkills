# LLM Anti-Patterns — Cloud-Specific Deployment Architecture

Common mistakes AI coding assistants make when deploying Salesforce cloud-specific components.

## Anti-Pattern 1: Assuming metadata API covers every cloud

**What the LLM generates:** "Just SFDX deploy the whole project — it handles Marketing Cloud too."

**Why it happens:** The model treats Salesforce as one metadata surface.

**Correct pattern:**

```
Metadata API covers Platform + Sales/Service + partial coverage for
newer clouds. Marketing Cloud, Commerce Cloud B2C, and parts of Data
Cloud need their own tooling (MC DevTools, SFCC Build API, Data Cloud
Migration Tool). Build a per-cloud tool map.
```

**Detection hint:** A pipeline with a single `sfdx force:source:deploy` step expected to cover Marketing Cloud content.

---

## Anti-Pattern 2: Deploying OmniScripts before their Integration Procedures

**What the LLM generates:** SFDX deploy of an Industries Data Kit with no ordering; all components in one batch.

**Why it happens:** The model relies on the platform to resolve references and does not know OmniStudio's rules.

**Correct pattern:**

```
OmniStudio order: DataRaptors → Integration Procedures → OmniScripts
→ FlexCards. The OmniStudio Migration Tool handles ordering if used
correctly; raw SFDX needs an explicit sequence. Skipping the order
leaves broken references in deployed components.
```

**Detection hint:** A single-step OmniStudio deploy command with FlexCards and DataRaptors in the same batch.

---

## Anti-Pattern 3: Deploying a Marketing Cloud data extension schema over existing production data

**What the LLM generates:** Runs `mcdev deploy --type dataExtension` pointed at production without checking drift.

**Why it happens:** The model treats data extensions like Salesforce custom objects and underestimates schema deploy impact.

**Correct pattern:**

```
Marketing Cloud data extensions have schema AND data. Schema deploys
overwriting an existing DE can truncate columns. Use compare-before-
deploy tools, back up data, and prefer additive changes over
destructive ones. Drift between environments is common; reconcile
before deploy.
```

**Detection hint:** A pipeline step deploys DE schema to production with no prior backup or compare step.

---

## Anti-Pattern 4: Deploying Agentforce topics without their actions

**What the LLM generates:** A change set with only topic XML; related action classes left in another PR.

**Why it happens:** The model treats topic and action as independently deployable metadata.

**Correct pattern:**

```
An Agentforce topic and the actions it invokes must deploy together.
Separating them leaves the topic pointing at nonexistent actions →
runtime failures. Package topic + actions + prompt templates as one
deployable unit.
```

**Detection hint:** A pipeline PR with a Topic metadata file whose referenced Action classes are missing from the diff.

---

## Anti-Pattern 5: No rollback plan for Marketing Cloud or Commerce Cloud

**What the LLM generates:** "Rollback: redeploy the previous version from Git." For Marketing Cloud journey changes.

**Why it happens:** The model generalizes rollback semantics across clouds.

**Correct pattern:**

```
Marketing Cloud journeys, Commerce Cloud catalog changes, and some
Data Cloud changes are NOT trivially reversible. Rollback plan must
describe: stopping in-flight journeys, replaying previous config,
and data repair if schemas changed. Git-revert is not enough.
```

**Detection hint:** A runbook with "git revert" as the Marketing Cloud rollback plan.
